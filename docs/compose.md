# Docker Compose

The shipped [`docker-compose.yml`](../docker-compose.yml) builds the existing
[`Dockerfile`](../Dockerfile) and serves the **lite** gallery. Lite needs no
connectome download.

```bash
docker compose up --build
```

The app listens on `0.0.0.0:4747` inside the container (`PORT=4747`). Open
[http://127.0.0.1:4747](http://127.0.0.1:4747). Live public host:
[https://flybrain.aionasmfworks.com](https://flybrain.aionasmfworks.com).

Health:

```bash
curl -fsS http://127.0.0.1:4747/
curl -fsS http://127.0.0.1:4747/healthz
```

`/healthz` returns `{"ok": true, "mode": "lite"|"anatomy"|"full"}`.

## Modes

| mode | what you need | image extras |
|---|---|---|
| **LITE** (default compose) | nothing | shipped `requirements.txt` |
| **ANATOMY** | 14 MB `body-annotations.feather` | `pandas` + `pyarrow` |
| **FULL BRAIN** | flycoinrh checkout + `graph.npz` (~1.1 GB) | `pandas` + `pyarrow` + `scipy` (flysim) |

The signed graph is **not** SMF-owned. It is CC-BY HHMI Janelia FlyEM /
Cambridge Connectomics Group / Google Research. Fetch it with
`python scripts/fetch_connectome.py` on the host; do not bake the 1.1 GB
file into the image.

The shipped Docker image is lite-only. Anatomy and full-brain need extra
Python packages that the Dockerfile does not install. Either `pip install`
them in a derived image, or run those modes from a venv on the host
(`python -m flydemos`) as in the README.

## Mounting annotations (anatomy)

After `python scripts/fetch_connectome.py --annotations-only`:

```yaml
services:
  flybrain:
    build: .
    ports:
      - "4747:4747"
    environment:
      PORT: "4747"
      FLY_ANNOTATIONS: /data/body-annotations.feather
    volumes:
      - ./data/body-annotations.feather:/data/body-annotations.feather:ro
```

`FLY_ANNOTATIONS` is an optional override. If unset, the app also looks at
`./data/body-annotations.feather` and `$FLYCOINRH_ROOT/data/body-annotations.feather`.

## Mounting the graph (full brain)

After `python scripts/fetch_connectome.py --full` (or an existing flycoinrh
checkout that already has `build/graph.npz`):

```yaml
services:
  flybrain:
    build: .
    ports:
      - "4747:4747"
    environment:
      PORT: "4747"
      FLYCOINRH_ROOT: /flycoinrh
      FLY_GRAPH: /data/graph.npz
      FLY_ANNOTATIONS: /data/body-annotations.feather
    volumes:
      - ./vendor/flycoinrh:/flycoinrh:ro
      - ./build/graph.npz:/data/graph.npz:ro
      - ./data/body-annotations.feather:/data/body-annotations.feather:ro
```

`FLYCOINRH_ROOT` must contain `flysim.py` (and usually `build/graph.npz`).
`FLY_GRAPH` overrides the npz path. Full mode also needs flysim's scientific
stack (`pandas`, `pyarrow`, `scipy`) in the image — the lite Dockerfile does
not include them.

Do not rewrite this as SMF-owned connectome infrastructure. The gallery
loads upstream files; it does not replace flycoinrh.
