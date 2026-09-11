from fastapi.testclient import TestClient

from flydemos.app import app

PAGES = ["/", "/chase", "/avalanche", "/learning", "/sees", "/nose"]


def test_pages_boot():
    with TestClient(app) as client:
        for p in PAGES:
            r = client.get(p)
            assert r.status_code == 200, p
            assert b"private" in r.content.lower() or p != "/"
        st = client.get("/api/status").json()
        assert st["private"] is True
        assert st["credit"] == "fruitflydev/flycoinrh"
        assert "CC-BY" in st["connectome"]
        assert st["counts"]["neurons"] == 165122
        h = client.get("/healthz").json()
        assert h["ok"] is True


def test_chase_websocket_frame():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/chase") as ws:
            hello = ws.receive_json()
            assert hello["type"] == "hello"
            assert hello["hex"]["n"] == 892
            frame = ws.receive_json()
            assert frame["demo"] == "chase"
            assert "motor" in frame
            assert "vision" in frame
