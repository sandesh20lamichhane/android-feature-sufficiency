"""Minimum attacker cost to flip a malware sample to benign.

For a linear model this is close to a closed form: to reduce the score we flip
the coordinates with the best score-reduction-per-unit-cost ratio, cheapest
first, until the decision crosses the threshold. That greedy order is optimal
for the linear case because each flip's contribution is independent and
additive -- there is no interaction term to reorder.

For tree ensembles no such structure exists, so `greedy_evasion_cost` does the
same thing empirically: re-score after each candidate flip and take the best
marginal move. It is an upper bound on true minimum cost, which is the safe
direction -- it can only understate how evadable the model is.

Reported per feature set, this is the paper's headline: equal accuracy,
unequal security.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from afs.attack.feasibility import FeasibilityModel


def linear_evasion_cost(x: np.ndarray, w: np.ndarray, b: float, threshold: float,
                        feas: FeasibilityModel, max_flips: int = 200) -> dict[str, Any]:
    """Cheapest set of flips taking w.x + b below `threshold`."""
    x = x.astype(float).copy()
    score = float(w @ x + b)
    need = score - threshold
    if need <= 0:
        return {"already_benign": True, "cost": 0.0, "n_flips": 0, "flips": []}

    # Flipping coordinate i changes the score by (new - old) * w[i].
    new_val = np.where(x > 0, 0.0, 1.0)
    delta = (new_val - x) * w                    # negative = helpful
    cost = feas.cost_vector(x)
    useful = (delta < 0) & np.isfinite(cost) & (cost > 0)
    if not useful.any():
        return {"already_benign": False, "cost": float("inf"), "n_flips": 0,
                "flips": [], "evaded": False}

    idx = np.where(useful)[0]
    efficiency = (-delta[idx]) / cost[idx]       # score drop per unit cost
    order = idx[np.argsort(-efficiency)]

    total, drop, flips = 0.0, 0.0, []
    for i in order[:max_flips]:
        total += float(cost[i])
        drop += float(-delta[i])
        flips.append({"feature": feas.names[i], "cost": float(cost[i]),
                      "direction": "remove" if x[i] > 0 else "add"})
        if drop >= need:
            return {"already_benign": False, "cost": total, "n_flips": len(flips),
                    "flips": flips, "evaded": True}
    return {"already_benign": False, "cost": float("inf"), "n_flips": len(flips),
            "flips": flips, "evaded": False}


def greedy_evasion_cost(x: np.ndarray, score_fn, threshold: float,
                        feas: FeasibilityModel, max_flips: int = 50,
                        candidate_k: int = 400) -> dict[str, Any]:
    """Model-agnostic greedy attack. Upper-bounds the true minimum cost."""
    x = x.astype(float).copy()
    if float(score_fn(x[None, :])[0]) < threshold:
        return {"already_benign": True, "cost": 0.0, "n_flips": 0, "flips": []}

    cost = feas.cost_vector(x)
    feasible = np.where(np.isfinite(cost) & (cost > 0))[0]
    total, flips = 0.0, []

    for _ in range(max_flips):
        cur = float(score_fn(x[None, :])[0])
        if cur < threshold:
            return {"already_benign": False, "cost": total, "n_flips": len(flips),
                    "flips": flips, "evaded": True}
        # Score the cheapest candidates first to keep this tractable.
        cand = feasible[np.argsort(cost[feasible])[:candidate_k]]
        trials = np.repeat(x[None, :], len(cand), axis=0)
        trials[np.arange(len(cand)), cand] = 1.0 - trials[np.arange(len(cand)), cand]
        gains = cur - score_fn(trials)
        eff = gains / cost[cand]
        best = int(np.argmax(eff))
        if gains[best] <= 0:
            break
        i = int(cand[best])
        flips.append({"feature": feas.names[i], "cost": float(cost[i]),
                      "direction": "remove" if x[i] > 0 else "add"})
        total += float(cost[i])
        x[i] = 1.0 - x[i]
        cost[i] = np.inf  # don't flip the same feature twice
        feasible = feasible[feasible != i]

    return {"already_benign": False, "cost": float("inf"), "n_flips": len(flips),
            "flips": flips, "evaded": False}
