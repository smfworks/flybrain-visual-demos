"""Gallery server: static demos + websocket telemetry."""

from __future__ import annotations

import asyncio
import json
import time

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import paths
from .adapter import describe, load_brain

WEB = paths.WEB
DEMOS = ("chase", "avalanche", "learning", "sees", "nose")

BRAIN = None
STATE = {
    "t0": time.time(),
    "pointer": {},
    "odour": None,
    "conc": 1.0,
    "clients": {d: set() for d in DEMOS},
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    brain()
    task = asyncio.create_task(_broadcast_loop())
    yield
    task.cancel()


app = FastAPI(title="flybrain visual demos", docs_url=None, redoc_url=None, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(WEB / "static")), name="static")


def brain():
    global BRAIN
    if BRAIN is None:
        BRAIN = load_brain()
    return BRAIN


def _page(name: str) -> FileResponse:
    path = WEB / name
    if not path.is_file():
        return JSONResponse({"error": "missing"}, status_code=404)
    return FileResponse(path, media_type="text/html")


@app.get("/")
def index():
    return _page("index.html")


@app.get("/chase")
def chase_page():
    return _page("chase.html")


@app.get("/avalanche")
def avalanche_page():
    return _page("avalanche.html")


@app.get("/learning")
def learning_page():
    return _page("learning.html")


@app.get("/sees")
def sees_page():
    return _page("sees.html")


@app.get("/nose")
def nose_page():
    return _page("nose.html")


@app.get("/api/status")
def api_status():
    b = brain()
    d = describe(b)
    d["uptime_s"] = int(time.time() - STATE["t0"])
    d["demos"] = list(DEMOS)
    return d


@app.get("/api/layout")
def api_layout():
    b = brain()
    return {
        "hex": b.retina.layout(),
        "soma": b.cloud.layout(),
        "olfaction": b.antenna.layout(),
        "honesty": describe(b),
    }


@app.get("/healthz")
def healthz():
    return {"ok": True, "mode": brain().mode}


@app.websocket("/ws/{demo}")
async def ws_demo(ws: WebSocket, demo: str):
    if demo not in DEMOS:
        await ws.close(code=4404)
        return
    await ws.accept()
    STATE["clients"][demo].add(ws)
    b = brain()
    hello = {
        "type": "hello",
        "demo": demo,
        **describe(b),
        "hex": b.retina.layout(),
        "soma": b.cloud.layout() if demo == "avalanche" else None,
        "olfaction": b.antenna.layout() if demo == "nose" else None,
    }
    await ws.send_text(json.dumps(hello))
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            await _handle(demo, msg)
    except WebSocketDisconnect:
        STATE["clients"][demo].discard(ws)
    except Exception:
        STATE["clients"][demo].discard(ws)


async def _handle(demo: str, msg: dict) -> None:
    b = brain()
    kind = msg.get("type")
    if kind == "pointer":
        STATE["pointer"][demo] = {
            "x": float(msg.get("x", 0.5)),
            "y": float(msg.get("y", 0.5)),
        }
    elif kind == "poke" and demo == "avalanche":
        frame = b.step_avalanche({"u": float(msg.get("u", 0.5)), "v": float(msg.get("v", 0.5))})
        await _send(demo, {"type": "frame", **frame})
    elif kind == "odour" and demo == "nose":
        STATE["odour"] = msg.get("id")
        STATE["conc"] = float(msg.get("concentration", 1.0))
    elif kind == "learn" and demo == "learning":
        frame = b.step_learning(
            {"kind": msg.get("kind", "reward"), "view": msg.get("view", "scene-a")}
        )
        await _send(demo, {"type": "frame", **frame})
    elif kind == "reset":
        if demo == "learning":
            await _send(demo, {"type": "frame", **b.step_learning({"kind": "reset"})})
        elif demo == "avalanche":
            b.cascade.reset()
            await _send(demo, {"type": "frame", **b.step_avalanche()})
        else:
            b.reset_cursor()
            STATE["pointer"].pop(demo, None)


async def _send(demo: str, payload: dict) -> None:
    dead = []
    blob = json.dumps(payload)
    for ws in list(STATE["clients"][demo]):
        try:
            await ws.send_text(blob)
        except Exception:
            dead.append(ws)
    for ws in dead:
        STATE["clients"][demo].discard(ws)


async def _broadcast_loop() -> None:
    t = 0.0
    while True:
        await asyncio.sleep(0.05)
        t += 0.05
        b = brain()
        # chase
        if STATE["clients"]["chase"]:
            ptr = STATE["pointer"].get("chase")
            frame = b.step_chase(t, ptr)
            await _send("chase", {"type": "frame", **frame})
        if STATE["clients"]["sees"]:
            frame = b.step_sees(t)
            await _send("sees", {"type": "frame", **frame})
        if STATE["clients"]["nose"]:
            frame = b.step_nose(t, STATE["odour"], STATE["conc"])
            await _send("nose", {"type": "frame", **frame})
        if STATE["clients"]["avalanche"]:
            frame = b.step_avalanche()
            await _send("avalanche", {"type": "frame", **frame})
        if STATE["clients"]["learning"] and int(round(t * 20)) % 5 == 0:
            frame = b.step_learning()
            await _send("learning", {"type": "frame", **frame})


def main() -> None:
    import uvicorn

    uvicorn.run(
        "flydemos.app:app",
        host="0.0.0.0",
        port=int(__import__("os").environ.get("PORT", "4747")),
        reload=False,
    )


if __name__ == "__main__":
    main()
