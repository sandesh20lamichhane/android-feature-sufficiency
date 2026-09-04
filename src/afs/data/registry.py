"""Dataset loaders.

The real loaders are intentionally left as explicit stubs with the expected
on-disk layout documented. Filling them in is step one of the data audit, and
each one forces a provenance decision that must be recorded in
docs/decisions/ before the loader is considered done.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from afs.data.schema import Dataset
from afs.data.synthetic import make_synthetic


def load_synthetic(raw_root: Path, **kw) -> Dataset:
    return make_synthetic(**kw)


def load_drebin(raw_root: Path, **kw) -> Dataset:
    """Expected: raw/drebin/feature_vectors/<sha256>  (one file per app,
    'type::value' lines) and raw/drebin/sha256_family.csv.

    DECISION REQUIRED before use: Drebin ships malware only. The benign corpus
    is yours to choose and it determines the result. Record the choice, the
    date range you matched, and the market, in docs/decisions/.
    """
    raise NotImplementedError(
        "Implement in notebooks/01_data_audit.ipynb; see docs/decisions/0002."
    )


def load_cicmaldroid(raw_root: Path, **kw) -> Dataset:
    """Expected: raw/cicmaldroid/feature_vectors_static.csv and
    .../feature_vectors_syscalls.csv, joined on sample hash.

    Notes that must reach the paper: not all samples executed successfully in
    the sandbox, so the dynamic subset is smaller and non-randomly so; and the
    Riskware class is definitionally over-permissioned, which structurally
    favours the permissions-only arm. Report with and without it.
    """
    raise NotImplementedError(
        "Implement in notebooks/01_data_audit.ipynb; see docs/decisions/0003."
    )


def load_androzoo(raw_root: Path, **kw) -> Dataset:
    """Expected: raw/androzoo/latest.csv.gz plus a locally extracted feature
    table. Needed for the temporal axis (dex_date) and for a benign corpus with
    known provenance. API key request takes days to weeks -- start it early.
    """
    raise NotImplementedError(
        "Implement in notebooks/01_data_audit.ipynb; see docs/decisions/0004."
    )


DATASETS: dict[str, Callable[..., Dataset]] = {
    "synthetic": load_synthetic,
    "drebin": load_drebin,
    "cicmaldroid": load_cicmaldroid,
    "androzoo": load_androzoo,
}


def load_dataset(name: str, raw_root: str | Path, **kw) -> Dataset:
    if name not in DATASETS:
        raise KeyError(f"unknown dataset {name!r}; have {sorted(DATASETS)}")
    return DATASETS[name](Path(raw_root), **kw)
