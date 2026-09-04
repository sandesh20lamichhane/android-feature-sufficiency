"""Atomic writes.

Google Drive has no atomic write. A disconnect mid-write leaves a truncated
parquet that often reads as valid until it doesn't. Everything here writes to
a temp name in the same directory, fsyncs, then renames -- rename is close
enough to atomic on Drive's FUSE mount to prevent torn artifacts.
"""
from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path
from typing import Iterator


@contextlib.contextmanager
def atomic_path(target: str | Path, suffix: str = "") -> Iterator[Path]:
    """Yield a temp path; rename onto `target` only if the block succeeds."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), prefix=".tmp_", suffix=suffix)
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        yield tmp_path
        os.replace(tmp_path, target)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def atomic_write_bytes(target: str | Path, data: bytes) -> None:
    with atomic_path(target) as tmp:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())


def atomic_write_text(target: str | Path, text: str, encoding: str = "utf-8") -> None:
    atomic_write_bytes(target, text.encode(encoding))
