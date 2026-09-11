"""Lite closed loop: stimulus → hex retina → reduced DN pooling → cursor.

When the real graph is present, FullBrain in adapter.py replaces step().
"""

from __future__ import annotations

import math

import numpy as np

from . import motor, scenes
from .cascade import Cascade
from .mushroom_lite import MushroomTheater
from .olfaction import Antenna
from .retina import HexRetina
from .soma import SomaCloud


class LiteBrain:
    def __init__(self, retina: HexRetina | None = None, cloud: SomaCloud | None = None):
        self.retina = retina or HexRetina()
        self.cloud = cloud or SomaCloud.lite()
        self.antenna = Antenna()
        self.mb = MushroomTheater()
        self.cascade = Cascade(self.cloud)
        self.mode = "lite"
        self.field_w = 640
        self.field_h = 400
        self.cx = self.field_w / 2
        self.cy = self.field_h / 2
        self.target = {"x": 0.62, "y": 0.38}
        self.trail: list[list[float]] = []
        self.sees_t = 0.0
        self.last_img: np.ndarray | None = None
        self.last_hz: dict = {}
        self.last_drive: dict | None = None
        self.last_out: dict = {}
        self.steps = 0
        self.pokes = 0
        self.mapping = "reduced spatial pooling of L1 columns → DNa02/DNa01"

    def status(self) -> dict:
        return {
            "mode": self.mode,
            "neurons_simulated": self.retina.n * 2,  # L1 + L2
            "hex_columns": self.retina.n,
            "hex_source": self.retina.source,
            "soma_source": self.cloud.source,
            "mapping": self.mapping,
            "graph": False,
        }

    def set_target(self, x: float, y: float) -> None:
        self.target["x"] = float(np.clip(x, 0.03, 0.97))
        self.target["y"] = float(np.clip(y, 0.03, 0.97))

    def wander_target(self, t: float) -> None:
        self.target["x"] = 0.5 + 0.34 * math.sin(t * 0.55)
        self.target["y"] = 0.5 + 0.28 * math.sin(t * 0.37 + 0.6)

    def _chase_img(self) -> np.ndarray:
        return scenes.luminous_target(
            self.field_h,
            self.field_w,
            self.target["x"] * self.field_w,
            self.target["y"] * self.field_h,
            sigma=32.0,
        )

    def _step_vision(self, img: np.ndarray) -> tuple[dict, dict, dict]:
        drive = self.retina.look(img, self.cx, self.cy)
        hz = motor.pool_from_retina(drive["on"], self.retina.u, self.retina.v)
        out = motor.decode(hz)
        self.last_drive = drive
        self.last_hz = hz
        self.last_out = out
        self.last_img = img
        return drive, hz, out

    def _move(self, out: dict) -> None:
        dx, dy = out["dx"] * 0.45, out["dy"] * 0.45
        if self.cy < 48 and dy < 0:
            dy *= 0.15
        if self.cy > self.field_h - 48 and dy > 0:
            dy *= 0.15
        if self.cx < 48 and dx < 0:
            dx *= 0.15
        if self.cx > self.field_w - 48 and dx > 0:
            dx *= 0.15
        self.cx = float(np.clip(self.cx + dx, 24, self.field_w - 24))
        self.cy = float(np.clip(self.cy + dy, 24, self.field_h - 24))
        nx, ny = self.cx / self.field_w, self.cy / self.field_h
        self.trail.append([round(nx, 4), round(ny, 4)])
        if len(self.trail) > 180:
            self.trail = self.trail[-180:]
        self.steps += 1

    def _vision_pack(self, drive: dict) -> dict:
        on, off = drive["on"], drive["off"]
        return {
            "on_hz": round(float(on.mean()), 1),
            "off_hz": round(float(off.mean()), 1),
            "columns": self.retina.n,
            "on": [int(np.clip(x / 1.8, 0, 100)) for x in on],
            "off": [int(np.clip(x / 1.08, 0, 100)) for x in off],
        }

    def _motor_pack(self, hz: dict, out: dict) -> dict:
        return {
            "dn": {
                "steer_L": round(float(hz.get("steer_L", 0)), 1),
                "steer_R": round(float(hz.get("steer_R", 0)), 1),
                "fwd_L": round(float(hz.get("fwd_L", 0)), 1),
                "fwd_R": round(float(hz.get("fwd_R", 0)), 1),
                "back": round(float(hz.get("back", 0)), 1),
                "stop": round(float(hz.get("stop", 0)), 1),
            },
            "out": {
                "turn_l": round(out["turn_l"], 3),
                "turn_r": round(out["turn_r"], 3),
                "forward": round(out["forward"], 3),
                "reverse": round(out["reverse"], 3),
                "click": round(float(out["stop"]), 3),
            },
            "dx": round(out["dx"], 2),
            "dy": round(out["dy"], 2),
            "clicked": bool(out["click"]),
        }

    def step_chase(self, t: float, pointer: dict | None = None) -> dict:
        if pointer:
            self.set_target(pointer["x"], pointer["y"])
        else:
            self.wander_target(t)
        img = self._chase_img()
        drive, hz, out = self._step_vision(img)
        self._move(out)
        return {
            "demo": "chase",
            "t": round(t, 3),
            "target": {k: round(v, 4) for k, v in self.target.items()},
            "cursor": {
                "x": round(self.cx / self.field_w, 4),
                "y": round(self.cy / self.field_h, 4),
            },
            "trail": self.trail[-80:],
            "vision": self._vision_pack(drive),
            "motor": self._motor_pack(hz, out),
            "mapping": self.mapping,
            "steps": self.steps,
        }

    def step_sees(self, t: float) -> dict:
        self.sees_t = t
        img, scene = scenes.dark_page(self.field_h, self.field_w, t)
        drive, hz, out = self._step_vision(img)
        self._move(out)
        return {
            "demo": "sees",
            "t": round(t, 3),
            "scene": scene,
            "cursor": {
                "x": round(self.cx / self.field_w, 4),
                "y": round(self.cy / self.field_h, 4),
            },
            "trail": self.trail[-80:],
            "vision": self._vision_pack(drive),
            "motor": self._motor_pack(hz, out),
            "mapping": self.mapping,
            "note": "Split readouts: stimulus texture → 892-hex mosaic → DN gauges → cursor.",
        }

    def step_nose(self, t: float, odour: str | None = None, conc: float | None = None) -> dict:
        if odour is not None:
            self.antenna.set_odour(odour if odour not in ("", "none") else None, conc or 1.0)
        elif conc is not None and self.antenna.odour:
            self.antenna.set_odour(self.antenna.odour, conc)
        self.wander_target(t * 0.4)
        img = self._chase_img()
        drive, hz, out = self._step_vision(img)
        olf = self.antenna.step(0.05)
        hz = motor.apply_olfactory_bias(hz, olf["bias"])
        out = motor.decode(hz)
        self.last_hz, self.last_out = hz, out
        self._move(out)
        return {
            "demo": "nose",
            "t": round(t, 3),
            "target": {k: round(v, 4) for k, v in self.target.items()},
            "cursor": {
                "x": round(self.cx / self.field_w, 4),
                "y": round(self.cy / self.field_h, 4),
            },
            "trail": self.trail[-80:],
            "vision": self._vision_pack(drive),
            "motor": self._motor_pack(hz, out),
            "olfaction": olf,
            "mapping": self.mapping,
        }

    def step_avalanche(self, poke: dict | None = None) -> dict:
        injected = 0
        if poke:
            u, v = float(poke["u"]), float(poke["v"])
            injected = self.cascade.poke(u, v)
            # also flash the retina
            img = scenes.poke_disk(
                self.field_h,
                self.field_w,
                u * self.field_w,
                v * self.field_h,
                sigma=20,
            )
            self.last_drive = self.retina.look(img, self.cx, self.cy)
            self.pokes += 1
        info = self.cascade.step()
        drive = self.last_drive or {
            "on": np.zeros(self.retina.n, np.float32),
            "off": np.zeros(self.retina.n, np.float32),
        }
        return {
            "demo": "avalanche",
            "injected": injected,
            "pokes": self.pokes,
            "neural": {
                **info,
                "scatter": self.cascade.scatter(),
                "vision": self._vision_pack(drive) if self.last_drive is not None else None,
            },
            "soma_source": self.cloud.source,
            "note": (
                "Lite cascade on a stylized CNS. Not the 10.2M-synapse graph. "
                "Measured somata used when annotations are loaded; FlyPilot detail "
                "readouts when graph.npz is present."
            ),
        }

    def step_learning(self, event: dict | None = None) -> dict:
        stats = self.mb.stats()
        if event:
            kind = event.get("kind", "reward")
            view = event.get("view", "scene-a")
            if kind == "reset":
                self.mb.reset()
                stats = self.mb.stats()
            else:
                stats = self.mb.encounter(kind, view)
        return {
            "demo": "learning",
            "stats": stats,
            "spark": self.mb.sparkline(),
            "view": self.mb.current_view,
            "reward_is_model": True,
        }

    def reset_cursor(self) -> None:
        self.cx = self.field_w / 2
        self.cy = self.field_h / 2
        self.trail.clear()
        self.steps = 0
