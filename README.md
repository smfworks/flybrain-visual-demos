# flybrain-visual-demos

Private preview — **not published**. A gallery of highly visual demos on the
digital fruit-fly brain, in the instrument-panel spirit of
[flybrain.online](https://flybrain.online) / [fruitflydev/flycoinrh](https://github.com/fruitflydev/flycoinrh).

This repo does **not** own the connectome. 165,122 neurons and 10,228,000
signed synapses were measured from a male *Drosophila melanogaster* by EM
(CC-BY HHMI Janelia FlyEM, Cambridge Connectomics Group, Google Research).
The simulation approach follows flycoinrh (LIF, 892-hex L1/L2, DNa02 / DNa01 /
MDN / DNp09, KC→MBON depression). MIT covers **new code here only**.

## Five demos

| route | what you see | what is real |
|---|---|---|
| `/chase` | Luminous target, hex retina, fly-cursor | L1/L2 sampling math + FlyPilot DN decode. Lite pooling until the graph is loaded. |
| `/avalanche` | Click the eye; spikes in the CNS volume | FlyPilot-style firing / spikes/sec / membrane when `graph.npz` is present. Else a labelled lite cascade on a stylized (or measured) volume. |
| `/learning` | Reward vs punish MBON compartments | Depression-not-potentiation, synapse counts, the −6% / −0.9% measurement. **Reward/novelty is a modelling choice.** |
| `/sees` | Page texture → mosaic → DN gauges → path | Same pipeline as chase, four labelled readouts. |
| `/nose` | Plume, 53 receptor types, walk bias | 2,635 ORNs / 53 types unused in flycoinrh. cVA→ORN_DA1→pC1 222 Hz is their measurement. DN bias from ORNs is demo wiring. |

## Run locally (lite — immediate)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m flydemos
```

Open [http://127.0.0.1:4747](http://127.0.0.1:4747). No 1.1 GB download.
Lite mode samples the stimulus through 892 hex columns with flycoinrh's
FlyEye math, pools L1 onto DNa02/DNa01 (phototaxis-like, **labelled**), and
decodes the cursor with FlyPilot's equations. Impressive without pretending
to be 165,122 LIF neurons.

`PORT` overrides the default `4747`.

## Full-brain mode

The signed graph is ~1.1 GB and is **not in git**.

```bash
# 14 MB annotations only → real hex columns + soma coordinates, still lite dynamics
python scripts/fetch_connectome.py --annotations-only

# clone flycoinrh, fetch weights, build graph.npz
python scripts/fetch_connectome.py --full
# then:
export FLYCOINRH_ROOT=$PWD/vendor/flycoinrh
pip install pandas pyarrow scipy   # flysim dependencies
python -m flydemos
```

Or point at an existing checkout:

```bash
export FLYCOINRH_ROOT=/path/to/flycoinrh   # must contain flysim.py and build/graph.npz
export FLY_GRAPH=/path/to/graph.npz        # optional override
export FLY_ANNOTATIONS=/path/to/body-annotations.feather
python -m flydemos
```

Public data (no account, no key), from flycoinrh's README:

```
https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/
  body-annotations-male-cns-v1.0-minconf-0.5.feather      14 MB
  body-neurotransmitters-male-cns-v1.0.feather            42 MB
  connectome-weights-male-cns-v1.0-minconf-0.5.feather   1.1 GB
```

When `graph.npz` loads, demos call `FlyBrain.run` / the FlyPilot decode.
They do **not** keep drawing fake particles and calling them neurons.

Mode pill: **LITE** (constructed lattice) · **ANATOMY** (measured hex/somata,
reduced dynamics) · **FULL BRAIN** (165,122 LIF cells).

## Tests / smoke

```bash
pip install -r requirements.txt
python -m pytest tests -q
python scripts/smoke.py
```

Smoke boots the gallery, hits every route, and steps each lite demo.

## Honesty (match flycoinrh)

- Wiring and cell identities are measurements. Synaptic *efficacy* is not
  (gains stay free in the LIF).
- Lite descending-neuron Hz are a reduced mapping, not the connectome graph.
- Mushroom-body **reward is not real**. Novelty ≠ sugar.
- Olfactory motor bias is invented; the unused ORN channel and cVA→pC1 222 Hz
  are not.
- Idle fly-shaped scatters on flybrain.online are decoration. These demos are
  not that: avalanche dots are either measured somata or a labelled cartoon.

## Credits

Connectome © HHMI Janelia FlyEM, Cambridge Connectomics Group, Google Research
(CC-BY 4.0). Approach after [fruitflydev/flycoinrh](https://github.com/fruitflydev/flycoinrh),
Shiu et al. 2024, Lappalainen et al. 2024. Not affiliated with them, nor with
pons or Robinhood.

New code: MIT. Keep the CC-BY attribution wherever the connectome goes.
