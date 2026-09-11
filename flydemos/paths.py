"""Where this repo, optional flycoinrh checkout, and connectome files live."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DATA = Path(os.environ.get("FLYDEMOS_DATA", ROOT / "data"))
BUILD = Path(os.environ.get("FLYDEMOS_BUILD", ROOT / "build"))


def flycoinrh_root() -> Path | None:
    """Return a flycoinrh checkout that has flysim.py, or None."""
    env = os.environ.get("FLYCOINRH_ROOT")
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.extend(
        [
            ROOT / "vendor" / "flycoinrh",
            ROOT.parent / "flycoinrh",
            Path.home() / "src" / "flycoinrh",
            Path.home() / "flycoinrh",
        ]
    )
    for path in candidates:
        if (path / "flysim.py").is_file():
            return path
    return None


def graph_path() -> Path | None:
    root = flycoinrh_root()
    env = os.environ.get("FLY_GRAPH")
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.append(BUILD / "graph.npz")
    if root:
        candidates.append(root / "build" / "graph.npz")
    for path in candidates:
        if path.is_file():
            return path
    return None


def annotations_path() -> Path | None:
    root = flycoinrh_root()
    env = os.environ.get("FLY_ANNOTATIONS")
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.append(DATA / "body-annotations.feather")
    if root:
        candidates.append(root / "data" / "body-annotations.feather")
    for path in candidates:
        if path.is_file():
            return path
    return None
