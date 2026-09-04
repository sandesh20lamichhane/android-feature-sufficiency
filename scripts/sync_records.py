#!/usr/bin/env python
"""Copy run records (small, textual, NOT regenerable) from Drive into the repo.

Artifacts stay in Drive. Records go in git, so the repo alone tells you what
ran, when, on which commit, with which config, and what came out.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from afs.paths import Paths

RECORDS = ("metrics.json", "config.json", "data_summary.json")

if __name__ == "__main__":
    paths = Paths.create()
    dest_root = Path("paper/tables/runs")
    n = 0
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for run in sorted(paths.runs.iterdir()):
        if not run.is_dir() or (only and run.name != only):
            continue
        for f in RECORDS:
            src = run / f
            if src.exists():
                dest = dest_root / run.name / f
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest)
                n += 1
    print(f"copied {n} record files -> {dest_root}")
    print("now: git add -A && git commit -m 'run records' && git push")
