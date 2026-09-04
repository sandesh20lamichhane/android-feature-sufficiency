#!/usr/bin/env python
"""Move a superseded run to _archive/. Never delete -- you will want the numbers."""
from __future__ import annotations

import shutil
import sys

from afs.paths import Paths

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: archive_run.py <run_id>")
    paths = Paths.create()
    src = paths.runs / sys.argv[1]
    if not src.exists():
        sys.exit(f"no such run: {src}")
    dest = paths.archive / sys.argv[1]
    shutil.move(str(src), str(dest))
    print(f"archived -> {dest}")
