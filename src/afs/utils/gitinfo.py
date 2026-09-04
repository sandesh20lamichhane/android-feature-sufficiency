"""Git provenance. Every artifact records the commit that produced it."""
from __future__ import annotations

import subprocess


def _run(args: list[str]) -> str | None:
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def git_sha(short_form: bool = True) -> str:
    sha = _run(["git", "rev-parse", "HEAD"])
    if not sha:
        return "nogit"
    return sha[:10] if short_form else sha


def git_dirty() -> bool:
    """True if the working tree has uncommitted changes.

    A dirty tree means the recorded SHA does not fully describe the code that
    produced a result. The pipeline warns loudly rather than blocking.
    """
    out = _run(["git", "status", "--porcelain"])
    return bool(out) if out is not None else False
