"""Synthetic dataset with the structure of the real problem.

Exists so the full pipeline -- checkpointing, splits, low-FPR metrics, evasion
cost -- can be verified end to end before any real data arrives, and so CI has
something to run. It deliberately bakes in the effect under study: permission
features are strongly but *cheaply* predictive, code features are weaker per
feature but expensive to modify, and the permission signal decays over time.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from afs.data.schema import Dataset, SampleProvenance

FAMILIES = [f"fam{i:03d}" for i in range(20)]


def make_synthetic(
    n: int = 4000,
    n_perm: int = 60,
    n_code: int = 300,
    prevalence: float = 0.3,
    drift: float = 0.6,
    seed: int = 0,
) -> Dataset:
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < prevalence).astype(int)
    t = rng.random(n)  # normalised time, 0 = earliest
    # Permission signal decays with time -> mimics the era artifact.
    perm_strength = 1.0 - drift * t
    P = rng.random((n, n_perm)) < (0.08 + 0.55 * y[:, None] * perm_strength[:, None])
    C = rng.random((n, n_code)) < (0.05 + 0.10 * y[:, None])
    cols = [f"perm::{i}" for i in range(n_perm)] + [f"api::{i}" for i in range(n_code)]
    X = pd.DataFrame(np.hstack([P, C]).astype(np.uint8), columns=cols)
    ids = np.array([f"syn{i:07d}" for i in range(n)])
    fam = np.where(y == 1, rng.choice(FAMILIES, n), "benign")
    dates = pd.to_datetime("2015-01-01") + pd.to_timedelta((t * 1800).astype(int), unit="D")
    prov = {
        i: SampleProvenance(
            source="synthetic",
            market="google_play" if lab == 0 else "third_party",
            label_origin="simulated",
        )
        for i, lab in zip(ids, y)
    }
    return Dataset(
        name="synthetic", features=X, labels=y, sample_ids=ids,
        family=fam, first_seen=dates.values, provenance=prov,
        meta={"synthetic": True, "drift": drift, "seed": seed},
    )
