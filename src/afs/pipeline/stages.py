"""Orchestration. Every stage checkpoints; every long loop resumes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from afs.attack.evasion_cost import greedy_evasion_cost, linear_evasion_cost
from afs.attack.feasibility import default_feasibility
from afs.checkpoint import CheckpointStore, ResumableLoop
from afs.checkpoint.atomic import atomic_write_text
from afs.data import load_dataset
from afs.data.splits import random_split, temporal_split
from afs.eval.metrics import full_report, paired_bootstrap_diff, threshold_at_fpr, tpr_at_fpr
from afs.features.sets import build_matrix
from afs.models.registry import build_model, decision_scores, linear_weights
from afs.paths import Paths, make_run_id
from afs.utils import get_logger, git_dirty, set_seed

log = get_logger("afs.pipeline")


def _get_split(ds, cfg: dict):
    proto = cfg.get("protocol", "random")
    if proto == "random":
        return random_split(ds, cfg.get("test_size", 0.3), cfg.get("seed", 0))
    if proto == "temporal":
        return temporal_split(ds, cfg["train_end"], cfg.get("test_start"), cfg.get("test_end"))
    raise KeyError(f"unknown protocol {proto!r}")


def run_experiment(cfg: dict, paths: Paths | None = None,
                   force: bool = False) -> dict[str, Any]:
    paths = paths or Paths.create()
    seed = cfg.get("seed", 0)
    set_seed(seed)
    run_id = make_run_id(cfg)
    run_dir = paths.run_dir(run_id)
    log.info("run_id=%s", run_id)
    if git_dirty():
        log.warning("working tree is DIRTY -- recorded git sha will not fully "
                    "describe this result. Commit before any run you intend to cite.")

    atomic_write_text(run_dir / "config.json", json.dumps(cfg, indent=2, sort_keys=True))
    store = CheckpointStore(run_dir / "checkpoints", seed=seed, run_id=run_id)

    # ---- stage 1: data -------------------------------------------------
    dcfg = cfg["data"]
    ds = load_dataset(dcfg["_name"], paths.raw, **dcfg.get("params", {}))
    summary = ds.summary()
    atomic_write_text(run_dir / "data_summary.json", json.dumps(summary, indent=2, default=str))
    log.info("dataset: %s", {k: v for k, v in summary.items() if k != "roc"})

    tr, te = _get_split(ds, cfg.get("split", {"protocol": "random", "seed": seed}))
    y_tr, y_te = ds.labels[tr], ds.labels[te]

    results: dict[str, Any] = {"run_id": run_id, "data": summary,
                               "n_train": len(tr), "n_test": len(te), "arms": {}}
    score_cache: dict[str, np.ndarray] = {}

    # ---- stage 2: one arm per (feature set x model) ---------------------
    for fs_name in cfg["feature_sets"]:
        X, cols = build_matrix(ds.features, fs_name)
        for m_name, m_spec in cfg["models"].items():
            arm = f"{fs_name}::{m_name}"
            arm_cfg = {"feature_set": fs_name, "model": m_spec, "seed": seed,
                       "split": cfg.get("split"), "data": dcfg}

            model_art = store.artifact("model", arm_cfg, ext=".joblib", force=force)
            if model_art.valid:
                model = joblib.load(model_art.path)
            else:
                model = build_model(m_spec)
                model.fit(X[tr], y_tr)
                model_art.commit(lambda p, m=model: joblib.dump(m, p))

            scores = decision_scores(model, X[te])
            score_cache[arm] = scores
            rep = full_report(y_te, scores)
            results["arms"][arm] = {"n_features": len(cols),
                                    **{k: v for k, v in rep.items() if k != "roc"}}
            log.info("%-18s auc=%.4f  tpr@1e-3=%.4f", arm, rep["roc_auc"],
                     rep["tpr@fpr=0.001"])

            # ---- stage 3: evasion cost (resumable) -----------------------
            if cfg.get("evasion", {}).get("enabled", False):
                results["arms"][arm]["evasion"] = _evasion(
                    cfg, run_dir, paths, run_id, arm, model, X, te, y_te,
                    scores, cols, fs_name,
                )

    # ---- stage 4: paired differences between feature sets ---------------
    base = cfg.get("baseline_arm")
    if base and base in score_cache:
        results["vs_baseline"] = {}
        for arm, sc in score_cache.items():
            if arm == base:
                continue
            results["vs_baseline"][arm] = {
                f"tpr@{f:g}": paired_bootstrap_diff(
                    y_te, score_cache[base], sc,
                    lambda yt, s, f=f: tpr_at_fpr(yt, s, f),
                    n_boot=cfg.get("n_boot", 500), seed=seed)
                for f in (0.01, 0.001)
            }

    atomic_write_text(run_dir / "metrics.json", json.dumps(results, indent=2, default=str))
    log.info("wrote %s", run_dir / "metrics.json")
    return results


def _evasion(cfg, run_dir, paths, run_id, arm, model, X, te, y_te, scores,
             cols, fs_name) -> dict[str, Any]:
    ecfg = cfg["evasion"]
    target_fpr = ecfg.get("threshold_fpr", 0.01)
    thr = threshold_at_fpr(y_te, scores, target_fpr)
    feas = default_feasibility(cols, fs_name, ecfg.get("remove_penalty", 4.0))

    mal = te[y_te == 1]
    cap = ecfg.get("max_samples")
    if cap and len(mal) > cap:
        mal = np.random.default_rng(cfg.get("seed", 0)).choice(mal, cap, replace=False)

    try:
        w, b = linear_weights(model)
        mode = "linear"
    except TypeError:
        w = b = None
        mode = "greedy"

    loop = ResumableLoop(
        out_dir=run_dir / "partial" / f"evasion__{arm.replace('::', '__')}",
        id_field="sample_idx",
        shard_size=ecfg.get("shard_size", 250),
        local_scratch=paths.scratch_dir(run_id, f"evasion_{arm.replace('::', '__')}"),
    )

    def work(i: int) -> dict[str, Any]:
        x = X[i]
        if mode == "linear":
            r = linear_evasion_cost(x, w, b, thr, feas,
                                    max_flips=ecfg.get("max_flips", 200))
        else:
            r = greedy_evasion_cost(x, lambda A: decision_scores(model, A), thr, feas,
                                    max_flips=ecfg.get("max_flips", 50))
        return {"sample_idx": int(i), "cost": r["cost"], "n_flips": r["n_flips"],
                "evaded": bool(r.get("evaded", False)),
                "already_benign": bool(r.get("already_benign", False))}

    df = loop.run(list(mal), work, key=lambda i: int(i))
    loop.sync()
    if df.empty:
        return {"mode": mode, "n": 0}

    attacked = df[~df["already_benign"]]
    finite = attacked[np.isfinite(attacked["cost"])]
    return {
        "mode": mode,
        "threshold_fpr": target_fpr,
        "n_attacked": int(len(attacked)),
        "evasion_rate": float(attacked["evaded"].mean()) if len(attacked) else float("nan"),
        "median_cost": float(finite["cost"].median()) if len(finite) else float("nan"),
        "median_flips": float(finite["n_flips"].median()) if len(finite) else float("nan"),
        "p10_cost": float(finite["cost"].quantile(0.10)) if len(finite) else float("nan"),
    }
