"""Canonical in-memory representation.

Every loader returns this, so downstream code never knows which dataset it is
looking at. `provenance` is not optional decoration -- benign-set provenance is
the single most attackable part of this study's design, so the source of every
sample travels with it and lands in the paper.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class SampleProvenance:
    """Where a sample came from. Reported per split in the paper."""
    source: str           # e.g. "drebin", "androzoo", "cicmaldroid"
    market: str | None = None       # "google_play", "third_party", "unknown"
    label_origin: str | None = None  # "vt>=4", "drebin_ground_truth", ...
    collected: str | None = None     # ISO date or range


@dataclass
class Dataset:
    name: str
    features: pd.DataFrame          # rows = samples, cols = raw feature names
    labels: np.ndarray              # 1 = malware, 0 = benign
    sample_ids: np.ndarray
    family: np.ndarray | None = None      # Drebin: 179 families
    first_seen: np.ndarray | None = None  # datetime64 for temporal splits
    provenance: dict[str, SampleProvenance] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        n = len(self.features)
        if len(self.labels) != n or len(self.sample_ids) != n:
            raise ValueError("features/labels/sample_ids length mismatch")

    def __len__(self) -> int:
        return len(self.features)

    def summary(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "name": self.name,
            "n_samples": len(self),
            "n_features": self.features.shape[1],
            "n_malware": int(self.labels.sum()),
            "n_benign": int((self.labels == 0).sum()),
            "prevalence": float(self.labels.mean()),
        }
        if self.family is not None:
            out["n_families"] = int(pd.Series(self.family).nunique())
        if self.first_seen is not None:
            fs = pd.Series(self.first_seen).dropna()
            if len(fs):
                out["date_range"] = [str(fs.min()), str(fs.max())]
        # Provenance split -- the number reviewers will look for first.
        if self.provenance:
            src = pd.Series([p.source for p in self.provenance.values()])
            out["provenance_sources"] = src.value_counts().to_dict()
        return out
