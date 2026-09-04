"""Filesystem layout. Single place that knows where things live.

Records (manifests, metrics, decision docs) are small, textual, and NOT
regenerable -- git is their source of truth and Drive holds a mirror.
Artifacts (matrices, models, shards) are large and regenerable -- Drive only,
never git.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from afs.utils.gitinfo import git_sha
from afs.utils.hashing import hash_obj, short

DEFAULT_DATA_ROOT = os.environ.get("AFS_DATA_ROOT", str(Path.home() / "afs-data"))
DEFAULT_SCRATCH = os.environ.get("AFS_SCRATCH", "/content/afs-scratch")


@dataclass
class Paths:
    data_root: Path
    scratch: Path | None = None

    @classmethod
    def create(cls, data_root: str | Path | None = None, scratch: str | Path | None = None):
        p = cls(Path(data_root or DEFAULT_DATA_ROOT), Path(scratch) if scratch else None)
        for d in (p.raw, p.interim, p.processed, p.runs, p.records, p.cache, p.archive):
            d.mkdir(parents=True, exist_ok=True)
        if p.scratch:
            p.scratch.mkdir(parents=True, exist_ok=True)
        return p

    # Immutable after download. Every stage reads from here, writes elsewhere.
    @property
    def raw(self) -> Path: return self.data_root / "raw"
    @property
    def interim(self) -> Path: return self.data_root / "interim"
    @property
    def processed(self) -> Path: return self.data_root / "processed"
    @property
    def runs(self) -> Path: return self.data_root / "runs"
    @property
    def records(self) -> Path: return self.data_root / "records"
    @property
    def cache(self) -> Path: return self.data_root / "cache"
    # Superseded runs move here. Never delete -- you will want the old numbers.
    @property
    def archive(self) -> Path: return self.data_root / "_archive"

    def run_dir(self, run_id: str) -> Path:
        d = self.runs / run_id
        (d / "checkpoints").mkdir(parents=True, exist_ok=True)
        (d / "partial").mkdir(parents=True, exist_ok=True)
        (d / "logs").mkdir(parents=True, exist_ok=True)
        return d

    def scratch_dir(self, run_id: str, name: str) -> Path | None:
        if not self.scratch:
            return None
        d = self.scratch / run_id / name
        d.mkdir(parents=True, exist_ok=True)
        return d


def make_run_id(config: dict) -> str:
    """YYYYMMDD-<git sha>-<config hash>. Never reuse; new config = new run."""
    return f"{time.strftime('%Y%m%d')}-{git_sha()}-{short(hash_obj(config), 8)}"
