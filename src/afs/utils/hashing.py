"""Deterministic hashing of configs and files.

Checkpoint validity depends entirely on these being stable across sessions,
so everything is canonicalised before hashing: dict keys sorted, floats via
repr, and no reliance on Python's salted builtin hash().
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _canonical(obj[k]) for k in sorted(obj)}
    if isinstance(obj, (list, tuple)):
        return [_canonical(v) for v in obj]
    if isinstance(obj, set):
        return sorted(_canonical(v) for v in obj)
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, float):
        return repr(obj)
    return obj


def hash_obj(obj: Any) -> str:
    """Stable SHA-256 of any JSON-able object."""
    blob = json.dumps(_canonical(obj), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def hash_file(path: str | Path, chunk: int = 1 << 20) -> str:
    """SHA-256 of a file. Used for raw-data integrity manifests."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def short(digest: str, n: int = 10) -> str:
    return digest[:n]
