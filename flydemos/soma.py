"""Stylized male Drosophila CNS volume for spike-avalanche lite mode.

When body-annotations.feather is present, measured somaLocation replaces this.
The live flycoinrh feed draws every firing neuron at its measured soma; this
cloud is an anatomical cartoon so the cascade is watchable without the 14 MB
table. It is labelled as such in the UI.
"""

from __future__ import annotations

import os

import numpy as np

N_DISPLAY = int(os.environ.get("FLYDEMOS_SOMA_N", "4800"))


def _blob(rng: np.random.Generator, n: int, mean, cov) -> np.ndarray:
    return rng.multivariate_normal(mean, cov, size=n).astype(np.float32)


def stylized_cns(n: int = N_DISPLAY, seed: int = 7) -> dict:
    rng = np.random.default_rng(seed)
    # Rough proportions of the male CNS: two optic lobes, central brain, VNC.
    n_ol = int(n * 0.34)
    n_cb = int(n * 0.38)
    n_vnc = n - n_ol - n_cb
    n_ol_l, n_ol_r = n_ol // 2, n_ol - n_ol // 2

    ol_l = _blob(rng, n_ol_l, [-1.15, 0.15, 0.35], np.diag([0.10, 0.16, 0.12]))
    ol_r = _blob(rng, n_ol_r, [1.15, 0.15, 0.35], np.diag([0.10, 0.16, 0.12]))
    cb = _blob(rng, n_cb, [0.0, 0.05, 0.25], np.diag([0.22, 0.18, 0.16]))
    # VNC trails posterior ( +Y )
    vnc = _blob(rng, n_vnc, [0.0, 1.35, -0.15], np.diag([0.06, 0.38, 0.05]))
    vnc[:, 0] *= 0.55 + 0.35 * np.clip(1.6 - vnc[:, 1], 0.2, 1.0)

    xyz = np.vstack([ol_l, ol_r, cb, vnc])
    region = np.array(
        (["optic_l"] * n_ol_l)
        + (["optic_r"] * n_ol_r)
        + (["central"] * n_cb)
        + (["vnc"] * n_vnc),
        dtype=object,
    )
    # Normalize to a unit box for the renderer.
    lo, hi = xyz.min(0), xyz.max(0)
    xyz = (xyz - lo) / np.maximum(hi - lo, 1e-6)
    xyz = xyz * 2.0 - 1.0
    return {"xyz": xyz, "region": region, "source": "stylized CNS volume"}


def pack_xyz(xyz: np.ndarray, limit: int = 4000) -> list:
    if len(xyz) > limit:
        idx = np.linspace(0, len(xyz) - 1, limit).astype(int)
        xyz = xyz[idx]
    return [[round(float(a), 4), round(float(b), 4), round(float(c), 4)] for a, b, c in xyz]


class SomaCloud:
    def __init__(self, xyz: np.ndarray, region: np.ndarray | None, source: str):
        self.xyz = np.asarray(xyz, dtype=np.float32)
        self.region = (
            np.asarray(region)
            if region is not None
            else np.array(["unknown"] * len(self.xyz), dtype=object)
        )
        self.source = source
        self.n = len(self.xyz)

    @classmethod
    def lite(cls, n: int = N_DISPLAY) -> "SomaCloud":
        d = stylized_cns(n)
        return cls(d["xyz"], d["region"], d["source"])

    def layout(self, limit: int = 4000) -> dict:
        idx = np.linspace(0, self.n - 1, min(limit, self.n)).astype(int)
        return {
            "n": self.n,
            "source": self.source,
            "xyz": pack_xyz(self.xyz[idx], limit),
            "region": [str(self.region[i]) for i in idx],
        }

    def optic_indices(self, side: str | None = None) -> np.ndarray:
        if side == "L":
            return np.flatnonzero(self.region == "optic_l")
        if side == "R":
            return np.flatnonzero(self.region == "optic_r")
        return np.flatnonzero(np.isin(self.region, ["optic_l", "optic_r"]))
