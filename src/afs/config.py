"""YAML config composition.

An experiment config names its data / features / model / eval components; this
module resolves them into one dict. The *resolved* dict is what gets hashed for
checkpoint keys, so a change anywhere in the tree invalidates exactly the
artifacts that depend on it.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

CONFIG_ROOT = Path(__file__).resolve().parents[2] / "configs"


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_yaml(path: str | Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_component(kind: str, name: str, root: Path | None = None) -> dict:
    root = root or CONFIG_ROOT
    return load_yaml(root / kind / f"{name}.yaml")


def resolve_experiment(name: str, root: Path | None = None, overrides: dict | None = None) -> dict:
    """Compose configs/experiments/<name>.yaml into a fully resolved dict."""
    root = root or CONFIG_ROOT
    exp = load_yaml(root / "experiments" / f"{name}.yaml")
    resolved: dict[str, Any] = {"experiment": name}
    for kind in ("data", "features", "models"):
        ref = exp.get(kind)
        if isinstance(ref, str):
            resolved[kind] = load_component(kind, ref, root)
            resolved[kind]["_name"] = ref
        elif isinstance(ref, list):
            resolved[kind] = {}
            for r in ref:
                resolved[kind][r] = load_component(kind, r, root)
        elif isinstance(ref, dict):
            resolved[kind] = ref
    for k, v in exp.items():
        if k not in ("data", "features", "models"):
            resolved[k] = v
    if overrides:
        resolved = _deep_merge(resolved, overrides)
    return resolved
