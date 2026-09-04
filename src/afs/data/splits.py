"""Evaluation protocols.

Three protocols, deliberately separate functions rather than a flag, because
they answer different questions and get reported side by side:

  random_split        the standard protocol -- reproduces the known result
  temporal_split      train past / test future; where permissions should decay
  leave_one_family_out generalisation to unseen malware families
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from afs.data.schema import Dataset


def random_split(ds: Dataset, test_size: float = 0.3, seed: int = 0, stratify: bool = True):
    from sklearn.model_selection import train_test_split
    idx = np.arange(len(ds))
    tr, te = train_test_split(
        idx, test_size=test_size, random_state=seed,
        stratify=ds.labels if stratify else None,
    )
    return np.sort(tr), np.sort(te)


def temporal_split(ds: Dataset, train_end: str, test_start: str | None = None,
                   test_end: str | None = None):
    """Strict past/future split on first_seen.

    A gap between train_end and test_start is allowed and encouraged: it
    prevents near-duplicate repackagings straddling the boundary from leaking
    the test set into training.
    """
    if ds.first_seen is None:
        raise ValueError(f"{ds.name} has no first_seen dates; temporal split unavailable")
    fs = pd.to_datetime(pd.Series(ds.first_seen))
    tr = np.where(fs < pd.Timestamp(train_end))[0]
    start = pd.Timestamp(test_start or train_end)
    mask = fs >= start
    if test_end:
        mask &= fs < pd.Timestamp(test_end)
    te = np.where(mask)[0]
    if len(tr) == 0 or len(te) == 0:
        raise ValueError("temporal split produced an empty side; check dates")
    return tr, te


def leave_one_family_out(ds: Dataset, min_size: int = 10):
    """Yield (family, train_idx, test_idx).

    Held-out family's malware goes to test; benign samples are split randomly
    so the test side has both classes. Families below `min_size` are skipped --
    recall on 3 samples is noise, not a result.
    """
    if ds.family is None:
        raise ValueError(f"{ds.name} has no family labels")
    fam = pd.Series(ds.family)
    benign = np.where(ds.labels == 0)[0]
    rng = np.random.default_rng(0)
    b_shuf = rng.permutation(benign)
    b_te, b_tr = b_shuf[: len(b_shuf) // 3], b_shuf[len(b_shuf) // 3:]
    counts = fam[ds.labels == 1].value_counts()
    for f in counts[counts >= min_size].index:
        held = np.where((fam.values == f) & (ds.labels == 1))[0]
        other = np.where((fam.values != f) & (ds.labels == 1))[0]
        yield f, np.sort(np.concatenate([other, b_tr])), np.sort(np.concatenate([held, b_te]))
