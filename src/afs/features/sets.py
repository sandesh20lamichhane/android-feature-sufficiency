"""Nested feature sets P < M < S, plus D.

  P  requested permissions only          (manifest)
  M  full manifest: P + intents + hardware + components
  S  M + static code features (restricted/suspicious API calls, opcodes, URLs)
  D  dynamic behaviour (syscalls, binder calls) -- CICMalDroid only

Nesting matters: because P is a strict subset of M and M of S, any accuracy
difference is attributable to the added features rather than to a different
representation. `attacker_cost` is the per-modification cost used by the
evasion analysis and is the point of the whole study -- a permission is free
to add, an API call sequence is not.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class FeatureSet:
    name: str
    prefixes: tuple[str, ...]
    description: str
    attacker_cost: float = 1.0   # relative cost of one feature modification
    additive_only: bool = False  # True if attacker can add but not remove
    notes: str = ""

    def select(self, columns) -> list[str]:
        return [c for c in columns if any(str(c).startswith(p) for p in self.prefixes)]


FEATURE_SETS: dict[str, FeatureSet] = {
    "P": FeatureSet(
        "P", ("perm::",),
        "Requested permissions from the manifest.",
        attacker_cost=1.0, additive_only=False,
        notes=("Free to modify: adding a permission needs no code change and "
               "breaks no functionality. Post-Android-6.0 a declared "
               "permission is not a held permission."),
    ),
    "M": FeatureSet(
        "M", ("perm::", "intent::", "hardware::", "component::"),
        "Full manifest.",
        attacker_cost=1.5,
        notes="Component names are renameable; intents are near-free to add.",
    ),
    "S": FeatureSet(
        "S", ("perm::", "intent::", "hardware::", "component::",
              "api::", "opcode::", "url::"),
        "Manifest + static code features.",
        attacker_cost=8.0, additive_only=True,
        notes=("Removing a real API call means removing functionality. Adding "
               "dead-code calls is cheaper than removing live ones, hence "
               "additive_only."),
    ),
    "D": FeatureSet(
        "D", ("syscall::", "binder::", "composite::"),
        "Dynamic behaviour from sandbox execution (CICMalDroid).",
        attacker_cost=20.0, additive_only=True,
        notes=("Changing observed runtime behaviour requires re-engineering "
               "the payload, or sandbox evasion -- which is itself detectable."),
    ),
}


def build_matrix(features: pd.DataFrame, feature_set: str) -> tuple[np.ndarray, list[str]]:
    fs = FEATURE_SETS[feature_set]
    cols = fs.select(features.columns)
    if not cols:
        raise ValueError(
            f"feature set {feature_set!r} matched no columns "
            f"(prefixes {fs.prefixes}); check the loader's column naming"
        )
    return features[cols].to_numpy(dtype=np.float32), cols
