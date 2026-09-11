from flydemos.motor import decode
from flydemos.retina import HexRetina, N_COLUMNS, axial_disk


def test_hex_count():
    h1, h2 = axial_disk()
    assert len(h1) == N_COLUMNS == 892
    # unique columns
    assert len(set(zip(h1.tolist(), h2.tolist()))) == 892


def test_look_on_off():
    eye = HexRetina()
    import numpy as np

    img = np.ones((200, 300), dtype=np.float32)
    d = eye.look(img, 150, 100)
    assert d["on"].mean() == 180.0
    assert d["off"].mean() == 0.0  # 1 - 1 = 0
    img0 = np.zeros((200, 300), dtype=np.float32)
    d0 = eye.look(img0, 150, 100)
    assert d0["on"].mean() == 0.0
    assert abs(d0["off"].mean() - 108.0) < 1e-3  # 180 * 0.6


def test_flypilot_decode_equations():
    out = decode(
        {
            "steer_L": 0.0,
            "steer_R": 450.0,
            "fwd_L": 450.0,
            "fwd_R": 450.0,
            "back": 0.0,
            "stop": 0.0,
        }
    )
    assert abs(out["turn"] - 1.0) < 1e-6
    assert abs(out["dx"] - 90.0) < 1e-6
    assert abs(out["dy"] - (-90.0)) < 1e-6
    click = decode(
        {
            "steer_L": 0,
            "steer_R": 0,
            "fwd_L": 0,
            "fwd_R": 0,
            "back": 0,
            "stop": 330,
        }
    )
    assert click["click"] is True
