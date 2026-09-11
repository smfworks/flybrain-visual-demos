from flydemos.lite import LiteBrain
from flydemos.mushroom_lite import MushroomTheater, N_PUNISH, N_REWARD, N_SYN
from flydemos.olfaction import RECEPTORS, Antenna


def test_chase_steers_toward_light():
    b = LiteBrain()
    b.cx, b.cy = 320, 200
    b.set_target(0.85, 0.5)
    frame = b.step_chase(0.0, {"x": 0.85, "y": 0.5})
    # target on the right → DNa02 R should dominate in the reduced mapping
    assert frame["motor"]["dn"]["steer_R"] > frame["motor"]["dn"]["steer_L"]
    assert frame["vision"]["columns"] == 892


def test_mushroom_counts_and_depression_direction():
    mb = MushroomTheater()
    st = mb.stats()
    assert st["synapses"] == N_SYN == 44042
    assert st["reward_side"] == N_REWARD == 27939
    assert st["punish_side"] == N_PUNISH == 14349
    for _ in range(20):
        mb.encounter("novelty", "scene-a")
    st = mb.stats()
    # reward compartment addressed; punish should barely move
    assert st["reward_delta_pct"] < -2.0
    assert st["punish_delta_pct"] > -2.0
    assert st["novelty"] == 20
    assert st["rewards"] == 20


def test_orn_inventory():
    assert len(RECEPTORS) == 53
    assert sum(n for _, n, _ in RECEPTORS) == 2635
    a = Antenna()
    out = a.step()
    a.set_odour("cVA", 1.0)
    hot = a.step()
    assert hot["peak"] == "Or67d"
    assert hot["pc1_hz"] == 222.0
    assert hot["bias_invented"] is True
    assert hot["peak_hz"] > out["peak_hz"]
