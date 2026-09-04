import numpy as np

from afs.eval.metrics import full_report, paired_bootstrap_diff, tpr_at_fpr


def _data(seed=0, sep=2.0, n=4000):
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < 0.3).astype(int)
    s = rng.normal(sep * y, 1.0)
    return y, s


def test_tpr_monotone_in_fpr():
    y, s = _data()
    a = tpr_at_fpr(y, s, 0.001)
    b = tpr_at_fpr(y, s, 0.01)
    c = tpr_at_fpr(y, s, 0.1)
    assert a <= b <= c


def test_perfect_separation():
    y = np.array([0] * 50 + [1] * 50)
    s = np.array([0.0] * 50 + [1.0] * 50)
    assert tpr_at_fpr(y, s, 0.01) == 1.0


def test_report_has_low_fpr_keys():
    y, s = _data()
    r = full_report(y, s)
    assert "tpr@fpr=0.001" in r and "roc_auc" in r


def test_paired_diff_detects_real_gap():
    y, weak = _data(sep=1.0)
    rng = np.random.default_rng(1)
    strong = weak + 1.5 * y + rng.normal(0, 0.1, len(y))
    d = paired_bootstrap_diff(y, weak, strong,
                              lambda yt, sc: tpr_at_fpr(yt, sc, 0.01), n_boot=200)
    assert d["diff"] > 0 and d["significant"]
