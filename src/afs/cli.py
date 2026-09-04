"""CLI: `afs-run --experiment 02_reproduce_baseline`."""
from __future__ import annotations

import argparse
import json

from afs.config import resolve_experiment
from afs.paths import Paths
from afs.pipeline.stages import run_experiment


def main() -> None:
    ap = argparse.ArgumentParser(prog="afs-run")
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--scratch", default=None)
    ap.add_argument("--force", action="store_true",
                    help="ignore valid checkpoints and recompute")
    args = ap.parse_args()

    cfg = resolve_experiment(args.experiment)
    paths = Paths.create(args.data_root, args.scratch)
    res = run_experiment(cfg, paths, force=args.force)
    print(json.dumps({k: v for k, v in res.items() if k != "data"},
                     indent=2, default=str))


if __name__ == "__main__":
    main()
