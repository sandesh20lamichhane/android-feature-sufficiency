"""What an attacker can actually change, and at what price.

The central claim of the study is that two models with indistinguishable clean
accuracy can demand wildly different attacker effort. That claim is only as
good as this cost model, so it is explicit, configurable, and reported in the
paper rather than buried.

Direction matters as much as cost. Adding a manifest permission is free and
breaks nothing. Removing a permission the app genuinely needs breaks
functionality. Removing a *live* API call removes behaviour the malware exists
to perform. So each feature carries an add-cost and a remove-cost.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from afs.features.sets import FEATURE_SETS


@dataclass
class FeasibilityModel:
    add_cost: np.ndarray      # per-feature cost of 0 -> 1
    remove_cost: np.ndarray   # per-feature cost of 1 -> 0 (inf = infeasible)
    names: list[str]

    def cost_vector(self, x: np.ndarray) -> np.ndarray:
        """Cost of flipping each coordinate of x, given its current value."""
        return np.where(x > 0, self.remove_cost, self.add_cost)


def default_feasibility(columns: list[str], feature_set: str,
                        remove_penalty: float = 4.0) -> FeasibilityModel:
    """Per-column costs derived from the feature-set cost model.

    remove_penalty encodes that deletion is harder than insertion. For sets
    marked additive_only, removal is treated as infeasible (inf), which is the
    conservative choice -- it can only make evasion look *harder*, so it cannot
    manufacture the result we are hoping to find.
    """
    fs = FEATURE_SETS[feature_set]
    n = len(columns)
    add = np.full(n, fs.attacker_cost, dtype=float)
    # Per-prefix refinement: a column's cost follows the narrowest set it
    # belongs to, so 'api::' columns inside S keep their high cost even though
    # S also contains cheap manifest columns.
    for i, c in enumerate(columns):
        for key in ("P", "M", "S", "D"):
            cand = FEATURE_SETS[key]
            if any(str(c).startswith(p) for p in cand.prefixes):
                add[i] = min(add[i], cand.attacker_cost) if key == "P" else add[i]
        if str(c).startswith(("api::", "opcode::", "url::")):
            add[i] = FEATURE_SETS["S"].attacker_cost
        elif str(c).startswith(("syscall::", "binder::", "composite::")):
            add[i] = FEATURE_SETS["D"].attacker_cost
        elif str(c).startswith("perm::"):
            add[i] = FEATURE_SETS["P"].attacker_cost
    rem = np.where(
        np.array([str(c).startswith(("api::", "opcode::", "syscall::",
                                     "binder::", "composite::")) for c in columns]),
        np.inf, add * remove_penalty,
    )
    return FeasibilityModel(add_cost=add, remove_cost=rem, names=list(columns))
