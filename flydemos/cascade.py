"""Lite spike cascade through a stylized CNS.

Not the 10.2M-synapse graph. A poke into the visual field injects the optic
lobe; activity spreads along region adjacencies with a leaky threshold.
When FlyBrain is loaded, adapter.py runs the real LIF instead.
"""

from __future__ import annotations

import numpy as np

from .soma import SomaCloud

# Hop kernel: from → to, weight
EDGES = {
    "optic_l": (("optic_l", 0.42), ("central", 0.28), ("optic_r", 0.04)),
    "optic_r": (("optic_r", 0.42), ("central", 0.28), ("optic_l", 0.04)),
    "central": (("central", 0.38), ("vnc", 0.22), ("optic_l", 0.06), ("optic_r", 0.06)),
    "vnc": (("vnc", 0.40), ("central", 0.10)),
}


class Cascade:
    def __init__(self, cloud: SomaCloud, seed: int = 5):
        self.cloud = cloud
        self.v = np.zeros(cloud.n, dtype=np.float32)
        self.refr = np.zeros(cloud.n, dtype=np.int32)
        rng = np.random.default_rng(seed)
        # Each cell samples a handful of neighbors in the same / adjacent region.
        self.nbrs = self._wire(rng)
        self.ever = np.zeros(cloud.n, dtype=bool)
        self.glow = np.zeros(cloud.n, dtype=np.float32)
        self.t = 0
        self.last_fired: np.ndarray = np.array([], dtype=np.int32)

    def _wire(self, rng: np.random.Generator) -> list[np.ndarray]:
        by = {r: np.flatnonzero(self.cloud.region == r) for r in EDGES}
        nbrs = []
        for i, r in enumerate(self.cloud.region):
            targets = []
            weights = []
            for dest, w in EDGES.get(str(r), ()):
                pool = by.get(dest)
                if pool is None or len(pool) == 0:
                    continue
                k = 6 if dest == r else 3
                pick = rng.choice(pool, size=min(k, len(pool)), replace=False)
                targets.extend(pick.tolist())
                weights.extend([w / k] * len(pick))
            if not targets:
                nbrs.append((np.array([i], dtype=np.int32), np.array([0.2], dtype=np.float32)))
            else:
                nbrs.append(
                    (
                        np.array(targets, dtype=np.int32),
                        np.array(weights, dtype=np.float32),
                    )
                )
        return nbrs

    def poke(self, u: float, v: float, amp: float = 2.8) -> int:
        """Map a retina poke to the nearer optic lobe and inject."""
        side = "L" if u < 0.5 else "R"
        idx = self.cloud.optic_indices(side)
        if len(idx) == 0:
            idx = np.arange(self.cloud.n)
        # Prefer cells whose x matches poke laterality and y matches v.
        xyz = self.cloud.xyz[idx]
        # xyz in [-1,1]; x laterality, y posterior
        du = xyz[:, 0] - (u * 2 - 1)
        dv = xyz[:, 2] - (v * 2 - 1)
        d = du * du + dv * dv
        take = idx[np.argsort(d)[: max(80, len(idx) // 10)]]
        self.v[take] += 3.4
        self.glow[take] = np.maximum(self.glow[take], 0.85)
        return int(len(take))

    def step(self) -> dict:
        self.t += 1
        self.v *= 0.88
        self.glow *= 0.93
        self.refr = np.maximum(self.refr - 1, 0)
        fired = np.flatnonzero((self.v > 0.72) & (self.refr <= 0))
        self.last_fired = fired.astype(np.int32)
        if len(fired):
            self.ever[fired] = True
            self.glow[fired] = 1.0
            self.refr[fired] = 2
            self.v[fired] = 0.0
            inject = np.zeros_like(self.v)
            for i in fired:
                tgt, _w = self.nbrs[int(i)]
                inject[tgt] += 0.78
            self.v += inject
        vis = self.cloud.optic_indices()
        mot = np.flatnonzero(self.cloud.region == "vnc")
        return {
            "firing": int(len(fired)),
            "ever": int(self.ever.sum()),
            "visual": int(np.isin(fired, vis).sum()) if len(fired) else 0,
            "motor": int(np.isin(fired, mot).sum()) if len(fired) else 0,
            "spikes_per_sec": float(len(fired) / 0.02),
            "mean_mv": float(-52.0 + 8.0 * self.v.mean()),
        }

    def scatter(self, limit: int = 1200) -> list:
        idx = np.flatnonzero(self.glow > 0.08)
        if len(idx) == 0:
            return []
        if len(idx) > limit:
            idx = idx[np.linspace(0, len(idx) - 1, limit).astype(int)]
        pts = []
        xyz = self.cloud.xyz
        for i in idx:
            x, y, z = xyz[int(i)]
            pts.append(
                [
                    round(float(x), 3),
                    round(float(y), 3),
                    round(float(z), 3),
                    round(float(self.glow[int(i)]), 3),
                ]
            )
        return pts

    def reset(self) -> None:
        self.v[:] = 0
        self.refr[:] = 0
        self.ever[:] = False
        self.glow[:] = 0
        self.last_fired = np.array([], dtype=np.int32)
        self.t = 0
