#!/usr/bin/env python3
"""Fetch the public FlyEM male CNS files and optionally build graph.npz.

The connectome is CC-BY (Janelia FlyEM / Cambridge / Google). It is not in
this git repo (~1.1 GB weights). This script is the documented path onto disk.

Usage:
  python scripts/fetch_connectome.py --annotations-only
  python scripts/fetch_connectome.py --full
  python scripts/fetch_connectome.py --clone-flycoinrh

Environment:
  FLYCOINRH_ROOT   existing checkout of fruitflydev/flycoinrh
  FLYDEMOS_DATA    where feather files go (default ./data)
  FLYDEMOS_BUILD   where graph.npz goes (default ./build)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__import__("os").environ.get("FLYDEMOS_DATA", ROOT / "data"))
BUILD = Path(__import__("os").environ.get("FLYDEMOS_BUILD", ROOT / "build"))
VENDOR = ROOT / "vendor" / "flycoinrh"

BASE = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/"
FILES = {
    "annotations": (
        "body-annotations-male-cns-v1.0-minconf-0.5.feather",
        "body-annotations.feather",
        "14 MB — hex columns + soma coordinates",
    ),
    "nt": (
        "body-neurotransmitters-male-cns-v1.0.feather",
        "body-neurotransmitters.feather",
        "42 MB — consensus neurotransmitter per body",
    ),
    "weights": (
        "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
        "connectome-weights.feather",
        "1.1 GB — synapse counts",
    ),
}
FLYCOINRH = "https://github.com/fruitflydev/flycoinrh.git"


def download(url: str, dest: Path, label: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"exists  {dest} ({dest.stat().st_size:,} bytes)")
        return
    print(f"get     {label}")
    print(f"        {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")

    def hook(count, block, total):
        if total <= 0:
            return
        got = count * block
        pct = min(100, got * 100 / total)
        print(f"\r        {pct:5.1f}%  {got/1e6:,.1f} / {total/1e6:,.1f} MB", end="", flush=True)

    urllib.request.urlretrieve(url, tmp, hook)
    print()
    tmp.replace(dest)


def clone_flycoinrh(dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if (dest / "flysim.py").is_file():
        print(f"exists  {dest}")
        return
    print(f"clone   {FLYCOINRH} → {dest}")
    subprocess.check_call(["git", "clone", "--depth", "1", FLYCOINRH, str(dest)])


def build_graph(flycoinrh: Path) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    data_dst = flycoinrh / "data"
    data_dst.mkdir(exist_ok=True)
    for _, dest_name, _ in FILES.values():
        src = DATA / dest_name
        dst = data_dst / dest_name
        if src.exists() and not dst.exists():
            try:
                dst.symlink_to(src.resolve())
            except OSError:
                shutil.copy2(src, dst)
    print("build   graph.npz via flycoinrh/build_graph.py")
    subprocess.check_call([sys.executable, str(flycoinrh / "build_graph.py")], cwd=str(flycoinrh))
    src = flycoinrh / "build" / "graph.npz"
    BUILD.mkdir(exist_ok=True)
    if src.exists():
        shutil.copy2(src, BUILD / "graph.npz")
        print(f"wrote   {BUILD / 'graph.npz'}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--annotations-only", action="store_true", help="14 MB: real hex + somata")
    p.add_argument("--full", action="store_true", help="annotations + NT + 1.1 GB weights + graph")
    p.add_argument("--clone-flycoinrh", action="store_true", help="shallow clone into vendor/")
    args = p.parse_args()
    if not (args.annotations_only or args.full or args.clone_flycoinrh):
        args.annotations_only = True

    if args.clone_flycoinrh or args.full:
        clone_flycoinrh(VENDOR)

    want = ["annotations"]
    if args.full:
        want = ["annotations", "nt", "weights"]
    for key in want:
        remote, dest_name, label = FILES[key]
        download(BASE + remote, DATA / dest_name, label)

    if args.full:
        root = Path(__import__("os").environ["FLYCOINRH_ROOT"]) if "FLYCOINRH_ROOT" in __import__("os").environ else VENDOR
        if not (root / "flysim.py").is_file():
            clone_flycoinrh(VENDOR)
            root = VENDOR
        build_graph(root)
        print()
        print("Full-brain mode: restart the gallery with")
        print(f"  FLYCOINRH_ROOT={root}")
        print("  python -m flydemos")
    else:
        print()
        print("Anatomy files on disk. Restart the gallery to pick them up.")
        print("For the 165,122-cell LIF network:  python scripts/fetch_connectome.py --full")


if __name__ == "__main__":
    main()
