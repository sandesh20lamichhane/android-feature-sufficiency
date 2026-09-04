import numpy as np

from afs.data import make_synthetic
from afs.data.splits import leave_one_family_out, random_split, temporal_split


def test_random_split_disjoint():
    ds = make_synthetic(n=500)
    tr, te = random_split(ds)
    assert len(np.intersect1d(tr, te)) == 0


def test_temporal_split_is_ordered():
    import pandas as pd
    ds = make_synthetic(n=1000)
    tr, te = temporal_split(ds, train_end="2017-01-01")
    fs = pd.to_datetime(pd.Series(ds.first_seen))
    assert fs.iloc[tr].max() < fs.iloc[te].min()


def test_lofo_holds_out_family():
    ds = make_synthetic(n=2000)
    fam, tr, _te = next(leave_one_family_out(ds))
    train_fams = set(np.asarray(ds.family)[tr][ds.labels[tr] == 1])
    assert fam not in train_fams
