"""Smoke: boot the gallery, hit every route, step every lite demo."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("FLYDEMOS_SOMA_N", "600")


def main() -> int:
    from fastapi.testclient import TestClient

    from flydemos.app import app
    from flydemos.lite import LiteBrain
    from flydemos.retina import HexRetina, N_COLUMNS

    retina = HexRetina()
    assert retina.n == N_COLUMNS == 892, retina.n

    brain = LiteBrain(retina=retina)
    chase = brain.step_chase(0.4)
    assert chase["vision"]["columns"] == 892
    assert "steer_L" in chase["motor"]["dn"]
    sees = brain.step_sees(0.2)
    assert sees["scene"]["kind"] == "page"
    nose = brain.step_nose(0.1, "cVA", 1.0)
    assert nose["olfaction"]["odour"] == "cVA"
    assert nose["olfaction"]["pc1_hz"] == 222.0
    av = brain.step_avalanche({"u": 0.3, "v": 0.4})
    assert av["neural"]["firing"] >= 0
    learn = brain.step_learning({"kind": "novelty", "view": "scene-a"})
    assert learn["reward_is_model"] is True

    with TestClient(app) as client:
        for path in ("/", "/chase", "/avalanche", "/learning", "/sees", "/nose", "/healthz", "/api/status"):
            r = client.get(path)
            assert r.status_code == 200, (path, r.status_code)
            print(f"  GET {path:16} {r.status_code}")
        st = client.get("/api/status").json()
        assert st["private"] is False
        assert st["counts"]["hex_columns"] == 892
        print(f"  mode {st['label']}")
        with client.websocket_connect("/ws/chase") as ws:
            hello = ws.receive_json()
            assert hello["type"] == "hello"
            assert hello["hex"]["n"] == 892
            frame = ws.receive_json()
            assert frame["type"] == "frame"
            assert "vision" in frame
            print("  ws  /ws/chase        hello+frame")

    print("smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
