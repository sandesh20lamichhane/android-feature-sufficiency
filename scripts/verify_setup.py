#!/usr/bin/env python
"""Pre-flight check. Run before any long job."""
from __future__ import annotations

import shutil
import sys

from afs.paths import Paths
from afs.utils import git_dirty, git_sha


def main() -> int:
    ok = True
    print(f"git sha : {git_sha()}")
    if git_dirty():
        print("  WARN  working tree dirty -- commit before any run you intend to cite")
    paths = Paths.create()
    print(f"data root: {paths.data_root}")
    for d in (paths.raw, paths.runs, paths.records):
        print(f"  {'OK ' if d.exists() else 'MISS'} {d}")
        ok &= d.exists()
    free_gb = shutil.disk_usage(paths.data_root).free / 1e9
    print(f"free space: {free_gb:.1f} GB")
    if free_gb < 20:
        print("  WARN  under 20 GB. Feature matrices + evasion shards run to tens of GB.")
    for mod in ("numpy", "pandas", "sklearn", "lightgbm", "pyarrow"):
        try:
            print(f"  OK  {mod} {__import__(mod).__version__}")
        except Exception:
            print(f"  MISS {mod}")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
