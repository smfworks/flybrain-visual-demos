"""Synthetic stimuli the lite brain looks at.

Chase: a luminous target on a dark field.
Sees: a dark instrument-page (the kind of UI flycoinrh's fly was tuned on).
"""

from __future__ import annotations

import numpy as np


def luminous_target(
    h: int,
    w: int,
    x: float,
    y: float,
    sigma: float = 22.0,
    amp: float = 1.0,
) -> np.ndarray:
    yy, xx = np.ogrid[0:h, 0:w]
    d2 = (xx - x) ** 2 + (yy - y) ** 2
    img = amp * np.exp(-d2 / (2.0 * sigma ** 2))
    # faint floor so L2 is not saturated everywhere
    return np.clip(img.astype(np.float32) + 0.03, 0, 1)


def dark_page(h: int = 400, w: int = 640, t: float = 0.0, cursor=None) -> tuple[np.ndarray, dict]:
    """Dark launchpad-ish texture. Luminance only — the fly has no colour."""
    img = np.full((h, w), 0.045, dtype=np.float32)
    img[0:36, :] = 0.11
    img[36:38, :] = 0.22
    # glowing form cards
    boxes = [
        (70, 48, 220, 36),
        (70, 100, 220, 36),
        (70, 152, 340, 72),
        (70, 248, 140, 40),
        (230, 248, 140, 40),
        (400, 70, 180, 220),
    ]
    scroll = int((np.sin(t * 0.35) * 0.5 + 0.5) * 28)
    scene_boxes = []
    for i, (x, y, bw, bh) in enumerate(boxes):
        y2 = y + scroll
        x0, x1 = max(0, x), min(w, x + bw)
        y0, y1 = max(0, y2), min(h, y2 + bh)
        glow = 0.16 + 0.10 * (0.5 + 0.5 * np.sin(t * 0.8 + i))
        img[y0:y1, x0:x1] = glow
        img[y0:y0 + 2, x0:x1] = min(1.0, glow + 0.35)
        img[y1 - 2 : y1, x0:x1] = min(1.0, glow + 0.12)
        scene_boxes.append(
            {
                "x": x / w,
                "y": y2 / h,
                "w": bw / w,
                "h": bh / h,
                "glow": round(float(glow), 3),
            }
        )
    # body copy as horizontal luminance grain (texture, not letters)
    rng = np.random.default_rng(4)
    text = rng.random((8, w)).astype(np.float32) * 0.08 + 0.05
    for row in range(8):
        yy = 310 + row * 10 + scroll // 2
        if 0 <= yy < h - 2:
            img[yy : yy + 2, 70 : w - 40] = text[row, 70 : w - 40]
    scene = {
        "kind": "page",
        "w": w,
        "h": h,
        "boxes": scene_boxes,
        "scroll": scroll,
        "note": "Dark UI texture. The fly's retina is a luminance map; light mode breaks it.",
    }
    return img, scene


def poke_disk(h: int, w: int, x: float, y: float, sigma: float = 16.0) -> np.ndarray:
    return luminous_target(h, w, x, y, sigma=sigma, amp=1.0)
