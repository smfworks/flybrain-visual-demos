"""KC → MBON depression theater.

Same rule as fruitflydev/flycoinrh mushroom.py: eligibility trace on Kenyon
cells, then dopamine depresses the addressed compartment. No potentiation.
Reward vs punishment side split is the documented one (MBON01/02/03 vs
MBON04/10/11) matching PAM vs PPL1 input.

Synapse counts match the measurement: 44,042 KC→MBON, 27,939 reward-side,
14,349 punish-side. In lite mode the synapses are a stand-in population with
those sizes — not the connectome's actual edges. When the real graph is
loaded, MushroomBody from flycoinrh is used instead.
"""

from __future__ import annotations

import numpy as np

N_SYN = 44_042
N_REWARD = 27_939
N_PUNISH = 14_349
# remainder: PAM ≈ PPL1, unassigned in the split
N_KC = 2_000


class MushroomTheater:
    def __init__(self, lr: float = 0.06, floor: float = 0.25, recover: float = 0.0008,
                 trace_decay: float = 0.55, seed: int = 11):
        rng = np.random.default_rng(seed)
        self.lr = lr
        self.floor = floor
        self.recover = recover
        self.trace_decay = trace_decay
        self.n = N_SYN
        self.pre = rng.integers(0, N_KC, size=N_SYN, dtype=np.int32)
        side = np.zeros(N_SYN, dtype=np.int8)
        side[:N_REWARD] = 1
        side[N_REWARD : N_REWARD + N_PUNISH] = -1
        # shuffle so compartments are mixed in index space
        perm = rng.permutation(N_SYN)
        self.side = side[perm]
        self.pre = self.pre[perm]
        self.gain = np.ones(N_SYN, dtype=np.float32)
        self.trace = np.zeros(N_SYN, dtype=np.float32)
        self.events = {"reward": 0, "punish": 0, "novelty": 0}
        # A "view" is a stable random subset of KCs — one odour/scene identity.
        self.views: dict[str, np.ndarray] = {}
        self.current_view = "scene-a"
        self._view(self.current_view, rng)
        self.source = "lite stand-in population (counts from flycoinrh measurement)"

    def _view(self, name: str, rng: np.random.Generator | None = None) -> np.ndarray:
        if name not in self.views:
            rng = rng or np.random.default_rng(sum(name.encode()) % (2**31))
            k = int(N_KC * 0.10)
            self.views[name] = rng.choice(N_KC, size=k, replace=False)
        return self.views[name]

    def observe(self, view: str | None = None, fired_kc: np.ndarray | None = None) -> None:
        self.trace *= self.trace_decay
        if fired_kc is None:
            view = view or self.current_view
            fired_kc = self._view(view)
        active = np.zeros(N_KC, dtype=bool)
        active[np.asarray(fired_kc, dtype=np.int32)] = True
        self.trace[active[self.pre]] = 1.0

    def dopamine(self, valence: int, amount: float = 1.0, novelty: bool = False) -> int:
        want = 1 if valence > 0 else -1
        hit = (self.side == want) & (self.trace > 0.05)
        if not hit.any():
            return 0
        self.gain[hit] *= (1.0 - self.lr * amount * self.trace[hit])
        np.clip(self.gain, self.floor, 1.0, out=self.gain)
        key = "reward" if want > 0 else "punish"
        self.events[key] += 1
        if novelty:
            self.events["novelty"] += 1
        return int(hit.sum())

    def forget(self) -> None:
        if len(self.gain):
            self.gain += (1.0 - self.gain) * self.recover

    def encounter(self, kind: str = "reward", view: str = "scene-a") -> dict:
        """One rewarded/punished/novelty encounter with a view."""
        self.current_view = view
        self.observe(view)
        novelty = kind == "novelty"
        if kind in ("reward", "novelty"):
            hit = self.dopamine(+1, novelty=novelty)
        elif kind == "punish":
            hit = self.dopamine(-1)
        else:
            hit = 0
        self.forget()
        out = self.stats()
        out["hit"] = hit
        out["kind"] = kind
        out["view"] = view
        out["reward_is_model"] = True
        if novelty:
            out["note"] = (
                "Novelty stood in for reward — a modelling choice, not sugar."
            )
        return out

    def stats(self) -> dict:
        rew = self.side == 1
        pun = self.side == -1
        mean_r = float(self.gain[rew].mean()) if rew.any() else 1.0
        mean_p = float(self.gain[pun].mean()) if pun.any() else 1.0
        return {
            "synapses": int(len(self.gain)),
            "reward_side": int(rew.sum()),
            "punish_side": int(pun.sum()),
            "depressed": int((self.gain < 0.995).sum()),
            "mean_gain": round(float(self.gain.mean()), 4),
            "min_gain": round(float(self.gain.min()), 4),
            "reward_gain": round(mean_r, 4),
            "punish_gain": round(mean_p, 4),
            "reward_delta_pct": round((mean_r - 1.0) * 100.0, 2),
            "punish_delta_pct": round((mean_p - 1.0) * 100.0, 2),
            "rewards": self.events["reward"],
            "punishments": self.events["punish"],
            "novelty": self.events["novelty"],
            "documented": {"reward_pct": -6.0, "punish_pct": -0.9, "encounters": 20},
            "source": self.source,
        }

    def sparkline(self, bins: int = 48) -> dict:
        """Histogram of gains per compartment, for the theater bars."""
        def hist(mask):
            h, _ = np.histogram(self.gain[mask], bins=bins, range=(self.floor, 1.0))
            return h.astype(int).tolist()

        rew = self.side == 1
        pun = self.side == -1
        kc = np.zeros(N_KC, dtype=np.float32)
        # mean outgoing gain per KC (reward-side)
        for i in np.flatnonzero(rew)[:: max(1, int(rew.sum() / 400))]:
            kc[self.pre[i]] = self.gain[i]
        return {
            "reward": hist(rew),
            "punish": hist(pun),
            "kc": [round(float(x), 3) for x in kc[:: max(1, N_KC // 80)]],
        }

    def reset(self) -> None:
        self.gain[:] = 1.0
        self.trace[:] = 0.0
        self.events = {"reward": 0, "punish": 0, "novelty": 0}
