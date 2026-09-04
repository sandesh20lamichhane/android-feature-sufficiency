"""Stage-level checkpointing.

Usage pattern throughout the pipeline:

    store = CheckpointStore(run_dir)
    art = store.artifact("features", cfg, inputs={"raw": raw_hash}, ext=".parquet")
    if art.valid:
        X = pd.read_parquet(art.path)
    else:
        X = build_features(...)
        art.commit(lambda p: X.to_parquet(p))

The artifact path is keyed on a hash of (stage, resolved config, input
hashes), so changing a config value produces a *different file* rather than
silently reusing the old one.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from afs.checkpoint.atomic import atomic_path
from afs.checkpoint.manifest import Manifest
from afs.utils.hashing import hash_obj, short
from afs.utils.logs import get_logger

log = get_logger(__name__)


class StaleCheckpoint(RuntimeError):
    pass


@dataclass
class Artifact:
    path: Path
    manifest: Manifest
    valid: bool

    def commit(self, writer: Callable[[Path], None]) -> Path:
        """Write via `writer(tmp_path)`, rename atomically, drop the manifest."""
        with atomic_path(self.path, suffix=self.path.suffix) as tmp:
            writer(tmp)
        self.manifest.save(self.path)
        log.info("committed %s", self.path.name)
        return self.path


class CheckpointStore:
    def __init__(self, root: str | Path, seed: int | None = None, run_id: str | None = None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.seed = seed
        self.run_id = run_id

    def artifact(
        self,
        stage: str,
        config: dict[str, Any],
        inputs: dict[str, str] | None = None,
        ext: str = ".parquet",
        force: bool = False,
    ) -> Artifact:
        cfg_hash = hash_obj(config)
        man = Manifest(
            stage=stage,
            config=config,
            config_hash=cfg_hash,
            input_hashes=inputs or {},
            seed=self.seed,
            run_id=self.run_id,
        )
        fname = f"{stage}__{short(man.key(), 12)}{ext}"
        path = self.root / fname

        valid = False
        if path.exists() and not force:
            on_disk = Manifest.load(path)
            if on_disk is None:
                log.warning("%s has no manifest -- treating as stale", fname)
            elif on_disk.matches(man):
                valid = True
                log.info("reusing checkpoint %s", fname)
            else:
                log.warning("manifest mismatch for %s -- recomputing", fname)
        return Artifact(path=path, manifest=man, valid=valid)
