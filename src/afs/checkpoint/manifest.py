"""Sidecar manifests.

Every artifact gets a `<name>.manifest.json` recording exactly what produced
it. This turns "is this checkpoint still valid?" from a judgement call into a
comparison, which is what makes stale-artifact bugs impossible rather than
merely unlikely.
"""
from __future__ import annotations

import json
import platform
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from afs.checkpoint.atomic import atomic_write_text
from afs.utils.gitinfo import git_dirty, git_sha


def _lib_versions() -> dict[str, str]:
    out: dict[str, str] = {"python": platform.python_version()}
    for mod in ("numpy", "pandas", "scipy", "sklearn", "lightgbm", "pyarrow"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:
            out[mod] = "absent"
    return out


@dataclass
class Manifest:
    stage: str
    config: dict[str, Any]
    config_hash: str
    input_hashes: dict[str, str] = field(default_factory=dict)
    git_sha: str = field(default_factory=git_sha)
    git_dirty: bool = field(default_factory=git_dirty)
    seed: int | None = None
    run_id: str | None = None
    libs: dict[str, str] = field(default_factory=_lib_versions)
    created_utc: str = field(
        default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    extra: dict[str, Any] = field(default_factory=dict)

    # ---- identity ----------------------------------------------------
    def key(self) -> str:
        """The fields that determine whether a cached artifact is reusable.

        Deliberately excludes git_sha: a pure refactor should not invalidate
        every feature matrix on disk. If a code change alters semantics, bump
        the stage version in the config instead.
        """
        from afs.utils.hashing import hash_obj
        return hash_obj(
            {"stage": self.stage, "config": self.config_hash, "inputs": self.input_hashes}
        )

    # ---- io ----------------------------------------------------------
    @staticmethod
    def path_for(artifact: str | Path) -> Path:
        return Path(str(artifact) + ".manifest.json")

    def save(self, artifact: str | Path) -> Path:
        p = self.path_for(artifact)
        atomic_write_text(p, json.dumps(asdict(self), indent=2, sort_keys=True))
        return p

    @classmethod
    def load(cls, artifact: str | Path) -> Manifest | None:
        p = cls.path_for(artifact)
        if not p.exists():
            return None
        try:
            return cls(**json.loads(p.read_text()))
        except Exception:
            return None

    def matches(self, other: Manifest) -> bool:
        return self.key() == other.key()
