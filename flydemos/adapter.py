"""Choose lite / anatomy / full-brain backends.

Full brain requires flycoinrh's flysim.FlyBrain and build/graph.npz.
Anatomy (measured hex + somata, reduced dynamics) needs only the 14 MB
annotations table. Lite runs immediately with no download.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from . import honesty, paths
from .lite import LiteBrain
from .retina import HexRetina
from .soma import SomaCloud


def _try_annotations() -> dict | None:
    p = paths.annotations_path()
    if p is None:
        return None
    try:
        import pandas as pd
    except ImportError:
        return None
    try:
        a = pd.read_feather(p).drop_duplicates("bodyId").set_index("bodyId")
        return {"path": p, "table": a}
    except Exception:
        return None


def retina_from_annotations(ann) -> HexRetina | None:
    try:
        h1 = ann["assignedOlHex1"]
        h2 = ann["assignedOlHex2"]
        types = ann.get("type", ann.get("t"))
        if types is None:
            return None
        has = ~(h1.isna() | h2.isna())
        l1 = has & (types.astype(str) == "L1")
        if int(l1.sum()) < 100:
            return None
        # unique columns
        cols = (
            ann.loc[l1, ["assignedOlHex1", "assignedOlHex2"]]
            .dropna()
            .drop_duplicates()
        )
        hh1 = cols["assignedOlHex1"].to_numpy(dtype=np.int32)
        hh2 = cols["assignedOlHex2"].to_numpy(dtype=np.int32)
        return HexRetina(hh1, hh2, source=f"measured assignedOlHex ({len(hh1)} L1 columns)")
    except Exception:
        return None


def cloud_from_annotations(ann, limit: int = 8000) -> SomaCloud | None:
    try:
        loc = ann["somaLocation"]
        pts = []
        regions = []
        types = ann.get("type", ann.get("t"))
        super_c = ann.get("superclass")
        for i, v in enumerate(loc.to_numpy()):
            if isinstance(v, (list, tuple, np.ndarray)) and len(v) >= 3:
                pts.append((float(v[0]), float(v[1]), float(v[2])))
                t = ""
                if types is not None:
                    t = str(types.iloc[i]) if hasattr(types, "iloc") else ""
                sc = ""
                if super_c is not None:
                    sc = str(super_c.iloc[i]) if hasattr(super_c, "iloc") else ""
                name = (sc + " " + t).lower()
                if "optic" in name or t in {"L1", "L2", "R1-6", "T4", "T5", "Mi1"}:
                    # laterality from x
                    regions.append("optic_l" if pts[-1][0] < 0 else "optic_r")
                elif "descending" in name or t.startswith("DN") or t.startswith("MDN"):
                    regions.append("vnc")
                else:
                    regions.append("central")
        if len(pts) < 200:
            return None
        xyz = np.array(pts, dtype=np.float32)
        if len(xyz) > limit:
            idx = np.linspace(0, len(xyz) - 1, limit).astype(int)
            xyz = xyz[idx]
            regions = [regions[i] for i in idx]
        lo, hi = xyz.min(0), xyz.max(0)
        xyz = (xyz - lo) / np.maximum(hi - lo, 1e-6)
        xyz = xyz * 2.0 - 1.0
        return SomaCloud(xyz, np.array(regions, dtype=object), source="measured somaLocation")
    except Exception:
        return None


class FullBrain(LiteBrain):
    """Drive demos from flysim.FlyBrain.run when the graph is on disk."""

    def __init__(self, graph: Path, flycoinrh: Path, retina: HexRetina, cloud: SomaCloud, fb):
        super().__init__(retina=retina, cloud=cloud)
        self.fb = fb
        self.mode = "full"
        self.mapping = "FlyBrain.run — 165,122 LIF neurons, signed synapses"
        self.graph_file = graph
        self.flycoinrh = flycoinrh
        types = np.asarray(fb.types).astype(str)
        self.on_idx = np.flatnonzero(types == "L1")
        self.off_idx = np.flatnonzero(types == "L2")
        # Motor populations, matching FlyPilot names.
        self.motor_sel = self._motor_indices(fb, flycoinrh)
        self._seed = 0
        self.pilot = None
        try:
            import os

            old = os.getcwd()
            os.chdir(str(flycoinrh))
            try:
                from flyeye import FlyPilot  # type: ignore

                self.pilot = FlyPilot(fb, sim_steps=60)
            finally:
                os.chdir(old)
        except Exception as exc:
            print(f"[flydemos] FlyPilot unavailable ({exc}); using FlyBrain.run + hex look", flush=True)

    def _motor_indices(self, fb, root: Path) -> dict:
        side = None
        ann_p = paths.annotations_path()
        if ann_p is not None:
            try:
                import pandas as pd

                a = pd.read_feather(ann_p).drop_duplicates("bodyId").set_index("bodyId")
                side = a["somaSide"].reindex(fb.bodies).fillna("").to_numpy().astype(str)
            except Exception:
                side = None

        def dn(t, s=None):
            sel = fb.where(type_re=rf"^{t}$")
            if s and side is not None:
                sel = np.array([i for i in sel if side[i] == s], dtype=np.int64)
            return sel

        return {
            "steer_L": dn("DNa02", "L"),
            "steer_R": dn("DNa02", "R"),
            "fwd_L": dn("DNa01", "L"),
            "fwd_R": dn("DNa01", "R"),
            "back": dn("MDN"),
            "stop": dn("DNp09"),
        }

    def status(self) -> dict:
        st = super().status()
        st.update(
            {
                "mode": "full",
                "neurons_simulated": int(self.fb.n),
                "graph": True,
                "graph_path": str(self.graph_file),
            }
        )
        return st

    def _step_vision(self, img: np.ndarray):
        from . import motor as motor_mod

        drive_rates = self.retina.look(img, self.cx, self.cy)
        self._seed += 1
        if self.pilot is not None:
            dx, dy, click, hz, info = self.pilot.step(
                img, self.cx, self.cy, seed=self._seed, detail=True
            )
            out = motor_mod.decode(hz)
            out["dx"], out["dy"], out["click"] = float(dx), float(dy), bool(click)
            self.last_drive = drive_rates
            self.last_hz = hz
            self.last_out = out
            self.last_img = img
            self._last_full_info = info
            return drive_rates, hz, out

        drive = {}
        if len(self.on_idx):
            drive[tuple(self.on_idx)] = np.resize(drive_rates["on"], len(self.on_idx))
        if len(self.off_idx):
            drive[tuple(self.off_idx)] = np.resize(drive_rates["off"], len(self.off_idx))
        rec = {k: v for k, v in self.motor_sel.items() if len(v)}
        result = self.fb.run(
            drive, steps=60, record=rec, seed=self._seed, spike_log=False
        )
        hz = {k: float(np.mean(result[k])) if k in result else 0.0 for k in self.motor_sel}
        for k in self.motor_sel:
            hz.setdefault(k, 0.0)
        out = motor_mod.decode(hz)
        self.last_drive = drive_rates
        self.last_hz = hz
        self.last_out = out
        self.last_img = img
        fired = result.get("_fired")
        self._last_full_info = {
            "firing": int(len(fired)) if fired is not None else 0,
            "spikes_per_sec": float(result.get("_spikes_per_sec", 0.0)),
            "mean_mv": float(result.get("_mean_mv", 0.0)),
            "visual": int(np.isin(self.on_idx, fired).sum() + np.isin(self.off_idx, fired).sum())
            if fired is not None
            else 0,
            "motor": int(sum(np.isin(v, fired).sum() for v in self.motor_sel.values() if len(v)))
            if fired is not None
            else 0,
            "fired": fired,
        }
        return drive_rates, hz, out

    def step_avalanche(self, poke: dict | None = None) -> dict:
        from . import scenes

        if poke:
            u, v = float(poke["u"]), float(poke["v"])
            img = scenes.poke_disk(self.field_h, self.field_w, u * self.field_w, v * self.field_h)
            drive_rates = self.retina.look(img, u * self.field_w, v * self.field_h)
            drive = {}
            if len(self.on_idx):
                drive[tuple(self.on_idx)] = np.resize(drive_rates["on"] * 1.8, len(self.on_idx))
            if len(self.off_idx):
                drive[tuple(self.off_idx)] = np.resize(drive_rates["off"], len(self.off_idx))
            self._seed += 1
            rec = {k: v for k, v in self.motor_sel.items() if len(v)}
            result = self.fb.run(drive, steps=80, record=rec, seed=self._seed)
            fired = result.get("_fired")
            scatter = []
            if fired is not None and len(fired):
                # Map fired indices into the display cloud by wrapping.
                n = self.cloud.n
                take = fired[:900] if len(fired) > 900 else fired
                for i in take:
                    x, y, z = self.cloud.xyz[int(i) % n]
                    scatter.append([round(float(x), 3), round(float(y), 3), round(float(z), 3)])
            self.pokes += 1
            self.last_drive = drive_rates
            return {
                "demo": "avalanche",
                "injected": int(len(self.on_idx)),
                "pokes": self.pokes,
                "neural": {
                    "firing": int(len(fired)) if fired is not None else 0,
                    "ever": int(len(fired)) if fired is not None else 0,
                    "visual": int(np.isin(self.on_idx, fired).sum()) if fired is not None else 0,
                    "motor": 0,
                    "spikes_per_sec": float(result.get("_spikes_per_sec", 0.0)),
                    "mean_mv": float(result.get("_mean_mv", 0.0)),
                    "scatter": scatter,
                    "vision": self._vision_pack(drive_rates),
                },
                "soma_source": self.cloud.source,
                "note": "FlyBrain.run detail readout. Spikes at soma coordinates (measured if annotations loaded).",
            }
        return super().step_avalanche(poke)


def load_brain() -> LiteBrain:
    ann_pack = _try_annotations()
    retina = HexRetina()
    cloud = SomaCloud.lite()
    anatomy = False
    if ann_pack is not None:
        r = retina_from_annotations(ann_pack["table"])
        c = cloud_from_annotations(ann_pack["table"])
        if r is not None:
            retina = r
            anatomy = True
        if c is not None:
            cloud = c
            anatomy = True

    graph = paths.graph_path()
    root = paths.flycoinrh_root()
    if graph is not None and root is not None:
        try:
            sys.path.insert(0, str(root))
            from flysim import FlyBrain  # type: ignore

            fb = FlyBrain(graph)
            brain = FullBrain(graph, root, retina, cloud, fb)
            return brain
        except Exception as exc:
            print(f"[flydemos] full brain failed, falling back: {exc}", flush=True)

    brain = LiteBrain(retina=retina, cloud=cloud)
    if anatomy:
        brain.mode = "anatomy"
        brain.mapping = (
            "measured hex/somata; reduced L1 pooling → DNa02/DNa01 (graph.npz not loaded)"
        )
    return brain


def describe(brain: LiteBrain) -> dict:
    st = brain.status()
    return honesty.payload(st["mode"], extras={"status": st})
