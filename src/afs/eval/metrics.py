"""Metrics, weighted toward the low-FPR regime.

Aggregate accuracy is the wrong instrument for this study: when both arms sit
at 97-99%, "the gap is tiny" is a statement about the metric, not the features.
A store-scale scanner operates at 0.1% FPR or below, so TPR-at-fixed-FPR is the
headline number and accuracy is reported only for comparability with prior work.

Differences between feature sets are reported with a *paired* bootstrap over
the same test samples, because the arms are evaluated on identical data and an
unpaired CI would badly overstate the uncertainty of the difference.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    roc_auc_score,
    roc_curve,
)

DEFAULT_FPRS = (0.10, 0.01, 0.001, 0.0001)


def threshold_at_fpr(y_true: np.ndarray, scores: np.ndarray, target_fpr: float) -> float:
    """Score threshold achieving at most `target_fpr` on this data.

    Uses the benign score distribution directly rather than interpolating the
    ROC, so the returned threshold is achievable rather than notional.
    """
    neg = scores[y_true == 0]
    if len(neg) == 0:
        return float("inf")
    # If fewer benign samples than 1/target_fpr, the estimate is unstable.
    return float(np.quantile(neg, 1.0 - target_fpr))


def tpr_at_fpr(y_true: np.ndarray, scores: np.ndarray, target_fpr: float) -> float:
    thr = threshold_at_fpr(y_true, scores, target_fpr)
    pos = scores[y_true == 1]
    return float((pos >= thr).mean()) if len(pos) else float("nan")


def fpr_resolution_warning(y_true: np.ndarray, target_fpr: float) -> str | None:
    """Flag when the benign set is too small to resolve the requested FPR."""
    n_neg = int((y_true == 0).sum())
    needed = int(np.ceil(10 / target_fpr))
    if n_neg < needed:
        return (f"only {n_neg} benign samples; resolving FPR={target_fpr:g} "
                f"reliably wants >~{needed}. Treat as an upper bound.")
    return None


def full_report(y_true: np.ndarray, scores: np.ndarray,
                fprs: tuple[float, ...] = DEFAULT_FPRS) -> dict[str, Any]:
    y_true = np.asarray(y_true)
    scores = np.asarray(scores, dtype=float)
    yhat = (scores >= np.quantile(scores, 1 - y_true.mean())).astype(int)
    rep: dict[str, Any] = {
        "n": len(y_true),
        "n_pos": int(y_true.sum()),
        "n_neg": int((y_true == 0).sum()),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "pr_auc": float(average_precision_score(y_true, scores)),
        "accuracy": float(accuracy_score(y_true, yhat)),
        "f1": float(f1_score(y_true, yhat, zero_division=0)),
    }
    for f in fprs:
        rep[f"tpr@fpr={f:g}"] = tpr_at_fpr(y_true, scores, f)
        w = fpr_resolution_warning(y_true, f)
        if w:
            rep.setdefault("warnings", []).append(w)
    fpr, tpr, _ = roc_curve(y_true, scores)
    rep["roc"] = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
    return rep


def bootstrap_ci(y_true, scores, stat_fn, n_boot: int = 1000,
                 alpha: float = 0.05, seed: int = 0) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    y_true, scores = np.asarray(y_true), np.asarray(scores)
    n = len(y_true)
    point = stat_fn(y_true, scores)
    vals = np.empty(n_boot)
    for b in range(n_boot):
        i = rng.integers(0, n, n)
        vals[b] = stat_fn(y_true[i], scores[i])
    lo, hi = np.nanquantile(vals, [alpha / 2, 1 - alpha / 2])
    return float(point), float(lo), float(hi)


def paired_bootstrap_diff(y_true, scores_a, scores_b, stat_fn,
                          n_boot: int = 1000, alpha: float = 0.05,
                          seed: int = 0) -> dict[str, float]:
    """CI for stat(B) - stat(A) resampling test *samples*, not predictions.

    This is the number that decides the paper: if the interval for the
    difference straddles zero, the extra features bought nothing at that
    operating point, and saying so is the finding.
    """
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    a, b = np.asarray(scores_a), np.asarray(scores_b)
    n = len(y_true)
    point = stat_fn(y_true, b) - stat_fn(y_true, a)
    vals = np.empty(n_boot)
    for k in range(n_boot):
        i = rng.integers(0, n, n)
        vals[k] = stat_fn(y_true[i], b[i]) - stat_fn(y_true[i], a[i])
    lo, hi = np.nanquantile(vals, [alpha / 2, 1 - alpha / 2])
    return {"diff": float(point), "lo": float(lo), "hi": float(hi),
            "significant": bool(lo > 0 or hi < 0)}
