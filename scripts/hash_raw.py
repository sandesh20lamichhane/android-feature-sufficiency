#!/usr/bin/env python
"""Checksum raw/ and write docs/raw_checksums.json (a record -> goes in git)."""
from __future__ import annotations

import json
from pathlib import Path

from afs.paths import Paths
from afs.utils.hashing import hash_file

if __name__ == "__main__":
    paths = Paths.create()
    man = {str(p.relative_to(paths.raw)): hash_file(p)
           for p in sorted(paths.raw.rglob("*")) if p.is_file()}
    out = Path("docs/raw_checksums.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(man, indent=2, sort_keys=True))
    print(f"hashed {len(man)} files -> {out}")
