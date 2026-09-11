"""Descending-neuron decode — FlyPilot's published equations.

    turn  = (DNa02_R − DNa02_L) / 450
    fwd   = mean(DNa01_L, DNa01_R) / 450
    back  = MDN / 450
    stop  = DNp09 / 450
    speed = clip(fwd − back, −1, 1) * (1 − clip(stop, 0, 1))
    dx    = clip(turn, −1, 1) * 90
    dy    = −speed * 90          # forward walking moves up the page
    click = DNp09 ≥ 330 Hz and speed < 0.25
"""

from __future__ import annotations

import numpy as np

TURN_SCALE = 450.0
STEP_PX = 90.0
CLICK_HZ = 330.0


def decode(hz: dict) -> dict:
    steer_l = float(hz.get("steer_L", 0.0))
    steer_r = float(hz.get("steer_R", 0.0))
    fwd_l = float(hz.get("fwd_L", 0.0))
    fwd_r = float(hz.get("fwd_R", 0.0))
    back_hz = float(hz.get("back", 0.0))
    stop_hz = float(hz.get("stop", 0.0))

    turn = (steer_r - steer_l) / TURN_SCALE
    fwd = (fwd_l + fwd_r) / 2.0 / TURN_SCALE
    back = back_hz / TURN_SCALE
    stop = stop_hz / TURN_SCALE
    speed = float(np.clip(fwd - back, -1, 1) * (1.0 - np.clip(stop, 0, 1)))
    dx = float(np.clip(turn, -1, 1) * STEP_PX)
    dy = float(-speed * STEP_PX)
    click = bool(stop_hz >= CLICK_HZ and speed < 0.25)
    return {
        "turn": float(turn),
        "forward": float(max(0.0, speed)),
        "reverse": float(max(0.0, back)),
        "stop": float(stop),
        "turn_l": float(max(0.0, -turn)),
        "turn_r": float(max(0.0, turn)),
        "dx": dx,
        "dy": dy,
        "click": click,
        "speed": speed,
    }


def pool_from_retina(on_rate: np.ndarray, u: np.ndarray, v: np.ndarray) -> dict:
    """Reduced spatial pooling. Not the 10.2M-synapse graph.

    Brightness-weighted centroid of L1 → DNa02 L/R asymmetry (phototaxis-like).
    Mean ON rate → DNa01. Dark-field OFF does not drive steering here.
    """
    w = np.asarray(on_rate, dtype=np.float32)
    mass = float(w.sum()) + 1e-6
    cu = float((u * w).sum() / mass)
    cv = float((v * w).sum() / mass)
    intensity = float(np.clip(w.mean() / 180.0, 0, 1))
    # Keep a floor so a dim field still produces a readable gauge.
    drive = 0.22 + 0.78 * intensity
    steer_r = max(0.0, (cu - 0.5) * 2.0) * TURN_SCALE * drive
    steer_l = max(0.0, (0.5 - cu) * 2.0) * TURN_SCALE * drive
    # Target below gaze (cv > 0.5 in image coords) → less forward; above → more.
    fwd = (0.35 + 0.65 * intensity) * 240.0
    fwd *= float(np.clip(1.15 - 0.5 * (cv - 0.5), 0.45, 1.25))
    return {
        "steer_L": float(steer_l),
        "steer_R": float(steer_r),
        "fwd_L": float(fwd),
        "fwd_R": float(fwd),
        "back": 0.0,
        "stop": float(max(0.0, 40.0 * intensity * (1.0 - abs(cu - 0.5) * 3.0))),
        "click": 0.0,
        "centroid_u": cu,
        "centroid_v": cv,
        "intensity": intensity,
    }


def apply_olfactory_bias(hz: dict, bias: dict) -> dict:
    """Invented DN bias from ORN rates — labelled as demo wiring."""
    out = dict(hz)
    out["steer_L"] = float(out.get("steer_L", 0) + bias.get("steer_L", 0))
    out["steer_R"] = float(out.get("steer_R", 0) + bias.get("steer_R", 0))
    out["fwd_L"] = float(out.get("fwd_L", 0) + bias.get("fwd", 0))
    out["fwd_R"] = float(out.get("fwd_R", 0) + bias.get("fwd", 0))
    out["back"] = float(out.get("back", 0) + bias.get("back", 0))
    out["stop"] = float(out.get("stop", 0) + bias.get("stop", 0))
    return out
