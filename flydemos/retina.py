"""892 retinotopic hex columns, sampled the way flycoinrh's FlyEye samples them.

Axial hex (h1, h2) → Cartesian:

    x = h1 + 0.5 * h2
    y = h2 * √3 / 2

then min-max to the unit square. L1 carries light increments (ON), L2 light
decrements (OFF). Peak ON drive is 180 Hz; OFF is 0.6 × that.

The constructed lattice is a filled hex disk of exactly 892 columns — the
headline number — not the measured assignedOlHex1/2 values. Those replace
this layout when body-annotations.feather is present.
"""

from __future__ import annotations

import numpy as np

N_COLUMNS = 892
ON_HZ = 180.0
OFF_SCALE = 0.6


def axial_disk(n: int = N_COLUMNS) -> tuple[np.ndarray, np.ndarray]:
    """Filled hexagon in axial coordinates, cube-distance rings."""
    cells: list[tuple[int, int]] = []
    radius = 0
    while len(cells) < n:
        for q in range(-radius, radius + 1):
            r1 = max(-radius, -q - radius)
            r2 = min(radius, -q + radius)
            for r in range(r1, r2 + 1):
                if max(abs(q), abs(r), abs(-q - r)) == radius:
                    cells.append((q, r))
                    if len(cells) >= n:
                        h1, h2 = np.array(cells[:n], dtype=np.int32).T
                        return h1, h2
        radius += 1
    h1, h2 = np.array(cells[:n], dtype=np.int32).T
    return h1, h2


def axial_to_xy(h1: np.ndarray, h2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = h1.astype(np.float32) + 0.5 * h2.astype(np.float32)
    y = h2.astype(np.float32) * (np.sqrt(3.0) / 2.0)
    return x, y


def to_uv(
    h1: np.ndarray, h2: np.ndarray
) -> tuple[np.ndarray, np.ndarray, float, float, float, float]:
    x, y = axial_to_xy(h1, h2)
    x0, x1 = float(x.min()), float(x.max())
    y0, y1 = float(y.min()), float(y.max())
    u = np.clip((x - x0) / (x1 - x0 + 1e-9), 0, 1)
    v = np.clip((y - y0) / (y1 - y0 + 1e-9), 0, 1)
    return u, v, x0, x1, y0, y1


class HexRetina:
    """L1/L2 mosaic. Constructed lattice, or measured hex assignments."""

    def __init__(
        self,
        h1: np.ndarray | None = None,
        h2: np.ndarray | None = None,
        source: str = "constructed lattice",
    ):
        if h1 is None or h2 is None:
            h1, h2 = axial_disk(N_COLUMNS)
        self.h1 = np.asarray(h1, dtype=np.int32)
        self.h2 = np.asarray(h2, dtype=np.int32)
        if len(self.h1) != len(self.h2):
            raise ValueError("h1/h2 length mismatch")
        self.n = int(len(self.h1))
        self.source = source
        self.u, self.v, self.x0, self.x1, self.y0, self.y1 = to_uv(self.h1, self.h2)
        self.on_uv = (self.u, self.v)
        self.off_uv = (self.u, self.v)

    def layout(self) -> dict:
        return {
            "n": self.n,
            "source": self.source,
            "h1": self.h1.tolist(),
            "h2": self.h2.tolist(),
            "u": [round(float(x), 4) for x in self.u],
            "v": [round(float(x), 4) for x in self.v],
        }

    def look(
        self,
        img: np.ndarray,
        cx: float,
        cy: float,
        fov_w: float = 300,
        fov_h: float = 210,
        max_hz: float = ON_HZ,
    ) -> dict[str, np.ndarray]:
        """Sample `img` (H×W luminance 0–1) around the cursor. Same as FlyEye.look."""
        H, W = img.shape[:2]

        def sample(uv):
            u, v = uv
            px = np.clip((cx - fov_w / 2 + u * fov_w).astype(int), 0, W - 1)
            py = np.clip((cy - fov_h / 2 + v * fov_h).astype(int), 0, H - 1)
            return img[py, px].astype(np.float32)

        lum_on = sample(self.on_uv)
        lum_off = sample(self.off_uv)
        return {
            "on": np.clip(lum_on, 0, 1) * max_hz,
            "off": np.clip(1.0 - lum_off, 0, 1) * max_hz * OFF_SCALE,
        }

    def pack_cols(self, on_rate: np.ndarray, off_rate: np.ndarray, step: int = 1) -> list:
        cols = []
        for i in range(0, self.n, step):
            cols.append(
                [
                    round(float(self.u[i]), 3),
                    round(float(self.v[i]), 3),
                    round(float(on_rate[i]) / ON_HZ, 3),
                    round(float(off_rate[i]) / (ON_HZ * OFF_SCALE), 3),
                    int(self.h1[i]),
                    int(self.h2[i]),
                ]
            )
        return cols
