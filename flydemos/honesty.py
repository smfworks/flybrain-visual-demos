"""Measured vs invented — the same distinction flycoinrh is careful about."""

COUNTS = {
    "neurons": 165_122,
    "synapses": 10_228_000,
    "hex_columns": 892,
    "orns": 2_635,
    "receptor_types": 53,
    "kc_mbon_synapses": 44_042,
    "reward_side": 27_939,
    "punish_side": 14_349,
}

MODES = {
    "lite": {
        "id": "lite",
        "label": "LITE",
        "blurb": (
            "Reduced visuomotor model. Hex sampling and descending-neuron "
            "decode match flycoinrh. The 165,122-cell LIF network is not running."
        ),
    },
    "anatomy": {
        "id": "anatomy",
        "label": "ANATOMY",
        "blurb": (
            "Measured hex columns and soma coordinates from FlyEM annotations, "
            "with the reduced dynamics. Load graph.npz for the real LIF brain."
        ),
    },
    "full": {
        "id": "full",
        "label": "FULL BRAIN",
        "blurb": (
            "FlyBrain.run over the signed connectome. L1/L2 drive and DN "
            "readouts come from FlyPilot.step(detail=True)."
        ),
    },
}

COPY = {
    "connectome": (
        "165,122 neurons and 10,228,000 signed synapses from the male "
        "Drosophila CNS EM volume (CC-BY Janelia FlyEM / Cambridge / Google). "
        "This preview does not own that data."
    ),
    "retina": (
        "892 retinotopic hex columns into L1 (ON) and L2 (OFF), the lamina "
        "cells directly postsynaptic to photoreceptors R1–R6. Sampling uses "
        "the same axial-hex → unit-square math as fruitflydev/flycoinrh FlyEye."
    ),
    "motor": (
        "DNa02 left vs right steers (cursor x). DNa01 drives forward (cursor y). "
        "MDN reverses. DNp09 stops / clicks. Decode equations are FlyPilot's: "
        "turn = (R−L)/450, speed from DNa01−MDN gated by DNp09, dx/dy × 90 px."
    ),
    "lite_mapping": (
        "Lite mode does not claim the 10.2M-synapse graph is running. L1/L2 "
        "rates are real samples of the stimulus. Descending-neuron Hz are a "
        "reduced spatial pooling of those columns (brightness centroid → DNa02 "
        "L/R, peak ON luminance → DNa01), then decoded with FlyPilot's equations. "
        "Lite demos use a wide FOV so the target stays in the mosaic; flycoinrh's "
        "launchpad used a tight 300×210 window. When graph.npz is present, "
        "FlyPilot.step replaces the pooling."
    ),
    "learning": (
        "The circuit, the KC→MBON site, and depression-not-potentiation are "
        "measured. The reward signal is not: a fly is rewarded by sugar, not by "
        "a demo event. Novelty standing in for reward is a modelling choice. "
        "flycoinrh measured −6.0% mean gain on reward-side MBONs vs −0.9% on "
        "punishment-side after twenty rewarded encounters with one view."
    ),
    "olfaction": (
        "2,635 ORNs across 53 receptor types sit in the connectome unused by "
        "flycoinrh. cVA through ORN_DA1 drives pC1 at 222 Hz untrained — the "
        "pathway works. Classic ligand affinities (cVA–Or67d, CO2–Gr21a/Gr63a, "
        "geosmin–Or56a) follow the literature. Lite ORN counts partition the "
        "measured 2,635 across 53 types (not a per-receptor census). Biasing "
        "walking DNs from ORN rates is demo wiring, not a measured motor mapping."
    ),
    "soma": (
        "On the live flycoinrh feed, every dot is a neuron at its measured soma "
        "coordinate. Lite mode uses a stylized CNS volume unless "
        "body-annotations.feather is loaded. Idle fly-shaped scatters are "
        "decoration; these demos are not that."
    ),
    "private": (
        "Private preview — not published. Simulation approach after "
        "fruitflydev/flycoinrh, Shiu et al. 2024 and Lappalainen et al. 2024. "
        "Not affiliated with them, nor with pons or Robinhood."
    ),
}


def payload(mode: str, extras: dict | None = None) -> dict:
    info = MODES.get(mode, MODES["lite"])
    out = {
        "mode": info["id"],
        "label": info["label"],
        "blurb": info["blurb"],
        "counts": COUNTS,
        "copy": COPY,
        "credit": "fruitflydev/flycoinrh",
        "connectome": "CC-BY HHMI Janelia FlyEM, Cambridge Connectomics Group, Google Research",
        "private": True,
    }
    if extras:
        out.update(extras)
    return out
