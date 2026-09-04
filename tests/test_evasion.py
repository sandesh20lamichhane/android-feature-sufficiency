import numpy as np
from afs.attack.evasion_cost import linear_evasion_cost
from afs.attack.feasibility import default_feasibility


def test_cheap_features_evade_cheaper():
    cols = [f"perm::{i}" for i in range(20)] + [f"api::{i}" for i in range(20)]
    feas = default_feasibility(cols, "S")
    # Permissions cost 1.0 to add, api features cost 8.0.
    assert feas.add_cost[0] < feas.add_cost[25]
    # Live API calls cannot be removed at all.
    assert not np.isfinite(feas.remove_cost[25])


def test_evasion_reduces_score_below_threshold():
    n = 30
    cols = [f"perm::{i}" for i in range(n)]
    feas = default_feasibility(cols, "P")
    w = np.ones(n)
    x = np.ones(n)
    r = linear_evasion_cost(x, w, 0.0, threshold=5.0, feas=feas)
    assert r["evaded"]
    assert w @ (x - 0) - r["n_flips"] <= 5.0


def test_already_benign_costs_nothing():
    cols = [f"perm::{i}" for i in range(5)]
    feas = default_feasibility(cols, "P")
    r = linear_evasion_cost(np.zeros(5), np.ones(5), 0.0, 1.0, feas)
    assert r["already_benign"] and r["cost"] == 0.0
