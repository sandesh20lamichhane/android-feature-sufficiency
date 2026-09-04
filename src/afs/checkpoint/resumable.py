"""Within-run resumable loops.

This is the layer that actually rescues you from a Colab disconnect. The two
expensive loops in this project -- evasion cost over thousands of samples x
four feature sets, and leave-one-family-out over Drebin's 179 families -- are
embarrassingly resumable: one independent result per item.

Results append to sharded parquet as they complete. On restart the loop reads
back which item ids are already done and skips them, so a disconnect costs one
item rather than the whole run.

Drive notes baked in here:
  * shard_size batches rows so you write a few hundred at a time, not one file
    per item (Drive collapses under many small files and enforces a file-count
    quota).
  * `local_scratch` keeps the hot path on /content and syncs to Drive every
    `sync_every` shards; local disk is far faster and you only lose the last
    interval.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Sequence

import pandas as pd

from afs.checkpoint.atomic import atomic_path
from afs.utils.logs import get_logger

log = get_logger(__name__)


class ResumableLoop:
    def __init__(
        self,
        out_dir: str | Path,
        id_field: str = "item_id",
        shard_size: int = 250,
        local_scratch: str | Path | None = None,
        sync_every: int = 4,
    ):
        self.final_dir = Path(out_dir)
        self.final_dir.mkdir(parents=True, exist_ok=True)
        self.id_field = id_field
        self.shard_size = shard_size
        self.sync_every = sync_every
        self.work_dir = Path(local_scratch) if local_scratch else self.final_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self._buf: list[dict[str, Any]] = []
        self._shards_since_sync = 0

    # ---- state -------------------------------------------------------
    def _shard_paths(self) -> list[Path]:
        seen = {p.name: p for p in self.final_dir.glob("part-*.parquet")}
        if self.work_dir != self.final_dir:
            seen.update({p.name: p for p in self.work_dir.glob("part-*.parquet")})
        return sorted(seen.values(), key=lambda p: p.name)

    def completed_ids(self) -> set:
        done: set = set()
        for p in self._shard_paths():
            try:
                done.update(pd.read_parquet(p, columns=[self.id_field])[self.id_field].tolist())
            except Exception:
                log.warning("unreadable shard %s -- ignoring (will recompute)", p.name)
        return done

    def results(self) -> pd.DataFrame:
        parts = [pd.read_parquet(p) for p in self._shard_paths()]
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

    # ---- writing -----------------------------------------------------
    def _next_shard_name(self) -> str:
        return f"part-{len(self._shard_paths()):05d}.parquet"

    def _flush(self, force: bool = False) -> None:
        if not self._buf or (len(self._buf) < self.shard_size and not force):
            return
        name = self._next_shard_name()
        target = self.work_dir / name
        df = pd.DataFrame(self._buf)
        with atomic_path(target, suffix=".parquet") as tmp:
            df.to_parquet(tmp, index=False)
        self._buf.clear()
        self._shards_since_sync += 1
        if self.work_dir != self.final_dir and (
            force or self._shards_since_sync >= self.sync_every
        ):
            self.sync()

    def sync(self) -> None:
        """Copy local scratch shards to the durable (Drive) directory."""
        if self.work_dir == self.final_dir:
            return
        for p in sorted(self.work_dir.glob("part-*.parquet")):
            dest = self.final_dir / p.name
            if not dest.exists():
                with atomic_path(dest, suffix=".parquet") as tmp:
                    shutil.copyfile(p, tmp)
        self._shards_since_sync = 0
        log.info("synced shards -> %s", self.final_dir)

    # ---- driver ------------------------------------------------------
    def run(
        self,
        items: Sequence[Any],
        fn: Callable[[Any], dict[str, Any] | None],
        key: Callable[[Any], Any] | None = None,
        progress: bool = True,
    ) -> pd.DataFrame:
        key = key or (lambda x: x)
        done = self.completed_ids()
        todo = [it for it in items if key(it) not in done]
        log.info("resumable: %d done, %d remaining", len(done), len(todo))

        it: Iterable = todo
        if progress:
            try:
                from tqdm.auto import tqdm
                it = tqdm(todo, desc=self.final_dir.name)
            except Exception:
                pass

        try:
            for item in it:
                rec = fn(item)
                if rec is None:
                    continue
                rec.setdefault(self.id_field, key(item))
                self._buf.append(rec)
                self._flush()
        finally:
            # Always persist partial progress, including on KeyboardInterrupt
            # or a Colab timeout that raises on the next cell.
            self._flush(force=True)
        return self.results()
