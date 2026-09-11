"""53 olfactory receptor types / 2,635 ORNs.

flycoinrh notes this channel exists and was unused. Ligand affinities for
the classic odours follow the literature; walking-DN bias is demo wiring.
cVA → ORN_DA1 → pC1 at 222 Hz untrained is flycoinrh's measurement that
the pathway works.
"""

from __future__ import annotations

import numpy as np

# 53 receptor types typical of adult Drosophila olfactory / CO2 neurons.
# Counts sum to 2,635. Larger glomeruli get more ORNs.
RECEPTORS: list[tuple[str, int, str]] = [
    ("Or7a", 54, "DA3"),
    ("Or9a", 48, "VM3"),
    ("Or10a", 56, "DL1"),
    ("Or13a", 52, "DC2"),
    ("Or19a", 44, "DC1"),
    ("Or22a", 68, "DM2"),
    ("Or22b", 34, "DM2"),
    ("Or23a", 42, "DA4l"),
    ("Or33a", 40, "DA2"),
    ("Or33b", 46, "DM3"),
    ("Or35a", 50, "VC3"),
    ("Or42a", 76, "VM7d"),
    ("Or42b", 74, "DM1"),
    ("Or43a", 46, "DA4m"),
    ("Or43b", 52, "VM2"),
    ("Or47a", 58, "DM3"),
    ("Or47b", 109, "VA1v"),
    ("Or49a", 38, "DL4"),
    ("Or49b", 44, "VA5"),
    ("Or56a", 50, "DA2"),  # geosmin
    ("Or59b", 64, "DM4"),
    ("Or67a", 48, "DM6"),
    ("Or67b", 46, "VA3"),
    ("Or67c", 54, "VC4"),
    ("Or67d", 78, "DA1"),  # cVA
    ("Or69a", 56, "D"),
    ("Or71a", 42, "VC2"),
    ("Or82a", 40, "VA6"),
    ("Or83c", 46, "DC3"),
    ("Or85a", 44, "DM5"),
    ("Or85b", 48, "VM5d"),
    ("Or85c", 36, "VC5"),
    ("Or85d", 38, "VA4"),
    ("Or85e", 34, "VC1"),
    ("Or85f", 40, "DL6"),
    ("Or88a", 60, "VA1d"),
    ("Or92a", 62, "VA2"),
    ("Or98a", 46, "VM5v"),
    ("Ir8a", 30, "co-rec"),
    ("Ir25a", 32, "co-rec"),
    ("Ir31a", 42, "VL1"),
    ("Ir64a", 54, "DC4"),  # acids
    ("Ir75a", 52, "DL2d"),
    ("Ir75b", 46, "DL2v"),
    ("Ir75c", 44, "VL2a"),
    ("Ir75d", 40, "VL2p"),
    ("Ir76a", 42, "VM4"),
    ("Ir76b", 50, "co-rec"),
    ("Ir84a", 44, "VL2a"),
    ("Ir92a", 38, "VM1"),
    ("Gr21a", 61, "V"),  # CO2
    ("Gr63a", 61, "V"),  # CO2
    ("Or1a", 36, "DL5"),
]

assert len(RECEPTORS) == 53
assert sum(n for _, n, _ in RECEPTORS) == 2635

# Literature-backed primary ligands. Values are relative affinities 0–1.
# Unlisted receptors stay near baseline for that odour.
LIGANDS: dict[str, dict[str, float]] = {
    "cVA": {
        "Or67d": 1.0,
        "Or47b": 0.18,
        "Or88a": 0.12,
        "note": "cis-vaccenyl acetate, DA1 / Or67d. flycoinrh: ORN_DA1 → pC1 222 Hz untrained.",
    },
    "fruit": {
        "Or22a": 0.95,
        "Or22b": 0.55,
        "Or42a": 0.9,
        "Or42b": 1.0,
        "Or59b": 0.45,
        "Or85b": 0.35,
        "Or92a": 0.4,
        "note": "esters / alcohols typical of ripe fruit (Or22a, Or42a/b).",
    },
    "geosmin": {
        "Or56a": 1.0,
        "Or33a": 0.15,
        "note": "harmful microbe odour; Or56a / DA2. Aversive in the animal.",
    },
    "CO2": {
        "Gr21a": 1.0,
        "Gr63a": 1.0,
        "note": "Gr21a + Gr63a, V glomerulus. Aversive.",
    },
    "vinegar": {
        "Ir64a": 1.0,
        "Ir75a": 0.7,
        "Ir75b": 0.55,
        "Ir75c": 0.4,
        "Or42b": 0.25,
        "note": "acids / vinegar; Ir64a DC4 and Ir75s.",
    },
}

ODOUR_META = {
    "cVA": {
        "name": "cVA",
        "full": "cis-vaccenyl acetate",
        "kind": "pheromone",
        "pc1_hz": 222,
        "bias": "arousal · slight turn (demo wiring). pC1 222 Hz is measured.",
    },
    "fruit": {
        "name": "fruit",
        "full": "ripe-fruit esters",
        "kind": "food",
        "pc1_hz": None,
        "bias": "forward drive (demo wiring)",
    },
    "geosmin": {
        "name": "geosmin",
        "full": "geosmin",
        "kind": "aversive",
        "pc1_hz": None,
        "bias": "stop / reverse (demo wiring)",
    },
    "CO2": {
        "name": "CO2",
        "full": "carbon dioxide",
        "kind": "aversive",
        "pc1_hz": None,
        "bias": "turn away (demo wiring)",
    },
    "vinegar": {
        "name": "vinegar",
        "full": "acetic acid / vinegar",
        "kind": "food-acid",
        "pc1_hz": None,
        "bias": "approach, then hover (demo wiring)",
    },
}


class Antenna:
    def __init__(self, seed: int = 3):
        self.names = [r[0] for r in RECEPTORS]
        self.counts = np.array([r[1] for r in RECEPTORS], dtype=np.int32)
        self.glomeruli = [r[2] for r in RECEPTORS]
        self.index = {n: i for i, n in enumerate(self.names)}
        self.n_orns = int(self.counts.sum())
        self.hz = np.full(len(self.names), 8.0, dtype=np.float32)  # spontaneous
        self.odour = None
        self.concentration = 0.0
        rng = np.random.default_rng(seed)
        # Glomerulus map: two antennal lobes as jittered disks.
        ang = np.linspace(0, 2 * np.pi, len(self.names), endpoint=False)
        jitter = rng.normal(0, 0.08, size=len(self.names))
        self.u = 0.50 + 0.38 * np.cos(ang + jitter) * np.where(
            np.arange(len(self.names)) % 2 == 0, 1.0, 0.55
        )
        self.v = 0.50 + 0.34 * np.sin(ang + jitter * 0.7)
        self.u = np.clip(self.u, 0.06, 0.94)
        self.v = np.clip(self.v, 0.08, 0.92)

    def layout(self) -> dict:
        return {
            "n_types": len(self.names),
            "n_orns": self.n_orns,
            "receptors": [
                {
                    "name": n,
                    "n": int(c),
                    "glomerulus": g,
                    "u": round(float(u), 3),
                    "v": round(float(v), 3),
                }
                for n, c, g, u, v in zip(
                    self.names, self.counts, self.glomeruli, self.u, self.v
                )
            ],
            "odours": ODOUR_META,
        }

    def set_odour(self, name: str | None, concentration: float = 1.0) -> None:
        self.odour = name if name in LIGANDS else None
        self.concentration = float(np.clip(concentration, 0, 1.4))

    def step(self, dt: float = 0.05) -> dict:
        target = np.full(len(self.names), 8.0, dtype=np.float32)
        affinities = {}
        if self.odour:
            spec = {k: v for k, v in LIGANDS[self.odour].items() if k != "note"}
            for rec, aff in spec.items():
                i = self.index.get(rec)
                if i is None:
                    continue
                target[i] = 8.0 + 220.0 * aff * self.concentration
                affinities[rec] = aff
            # faint cross-talk so the lobe feels alive
            target += 6.0 * self.concentration * 0.04
        # leak toward target
        self.hz += (target - self.hz) * min(1.0, dt * 6.0)
        self.hz = np.clip(self.hz + np.random.default_rng().normal(0, 1.2, self.hz.shape), 0, 260)
        return self.readout(affinities)

    def readout(self, affinities: dict | None = None) -> dict:
        peak_i = int(np.argmax(self.hz))
        bias = {"steer_L": 0.0, "steer_R": 0.0, "fwd": 0.0, "back": 0.0, "stop": 0.0}
        if self.odour == "cVA":
            # Arousal: a little of both steer (search) + forward. Demo wiring.
            bias["fwd"] = 90.0 * self.concentration
            bias["steer_R"] = 40.0 * self.concentration
        elif self.odour == "fruit":
            bias["fwd"] = 160.0 * self.concentration
        elif self.odour == "geosmin":
            bias["back"] = 140.0 * self.concentration
            bias["stop"] = 80.0 * self.concentration
        elif self.odour == "CO2":
            bias["steer_L"] = 180.0 * self.concentration
            bias["fwd"] = -40.0 * self.concentration
        elif self.odour == "vinegar":
            bias["fwd"] = 70.0 * self.concentration
            bias["stop"] = 30.0 * self.concentration
        tiles = [
            {
                "name": n,
                "hz": round(float(h), 1),
                "n": int(c),
                "glomerulus": g,
                "u": round(float(u), 3),
                "v": round(float(v), 3),
            }
            for n, h, c, g, u, v in zip(
                self.names, self.hz, self.counts, self.glomeruli, self.u, self.v
            )
        ]
        return {
            "odour": self.odour,
            "concentration": round(self.concentration, 3),
            "mean_hz": round(float(self.hz.mean()), 1),
            "peak": self.names[peak_i],
            "peak_hz": round(float(self.hz[peak_i]), 1),
            "pc1_hz": 222.0 if self.odour == "cVA" else None,
            "tiles": tiles,
            "bias": bias,
            "affinities": affinities or {},
            "note": LIGANDS.get(self.odour, {}).get("note") if self.odour else None,
            "bias_invented": True,
        }
