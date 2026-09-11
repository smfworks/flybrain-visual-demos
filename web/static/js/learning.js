import { $, connectDemo, setMode, fitCanvas } from "./core.js";

let spark = { reward: [], punish: [], kc: [] };
let send = () => {};

connectDemo("learning", {
  onHello(m, s) {
    send = s;
    setMode(m);
  },
  onFrame(m) {
    const st = m.stats || {};
    $("r-delta").textContent = (st.reward_delta_pct ?? 0).toFixed(1) + "%";
    $("p-delta").textContent = (st.punish_delta_pct ?? 0).toFixed(1) + "%";
    $("r-gain").textContent = st.reward_gain ?? "1.000";
    $("p-gain").textContent = st.punish_gain ?? "1.000";
    $("n-syn").textContent = (st.synapses || 0).toLocaleString();
    $("n-dep").textContent = (st.depressed || 0).toLocaleString();
    $("n-rew").textContent = (st.rewards || 0).toLocaleString();
    $("n-pun").textContent = (st.punishments || 0).toLocaleString();
    $("n-nov").textContent = (st.novelty || 0).toLocaleString();
    if (m.spark) spark = m.spark;
    const note = $("event-note");
    if (note && st.note) note.textContent = st.note;
    else if (note && m.reward_is_model) {
      note.textContent = "Reward signal is a modelling choice when novelty is used — not sugar.";
    }
  },
});

$("btn-rew")?.addEventListener("click", () => send({ type: "learn", kind: "reward", view: "scene-a" }));
$("btn-nov")?.addEventListener("click", () => send({ type: "learn", kind: "novelty", view: "scene-a" }));
$("btn-pun")?.addEventListener("click", () => send({ type: "learn", kind: "punish", view: "scene-b" }));
$("btn-20")?.addEventListener("click", async () => {
  for (let i = 0; i < 20; i++) {
    send({ type: "learn", kind: "novelty", view: "scene-a" });
    await new Promise((r) => setTimeout(r, 90));
  }
});
$("btn-reset")?.addEventListener("click", () => send({ type: "reset" }));

function paintHist(c, hist, color) {
  const g = c.getContext("2d");
  const d = fitCanvas(c);
  g.fillStyle = "#080b10";
  g.fillRect(0, 0, c.width, c.height);
  if (!hist || !hist.length) return;
  const mx = Math.max(1, ...hist);
  const w = c.width / hist.length;
  hist.forEach((v, i) => {
    const h = (v / mx) * (c.height - 4);
    g.fillStyle = color;
    g.fillRect(i * w + 0.5, c.height - h, Math.max(1, w - 1), h);
  });
  void d;
}

function paintKc(c, kc) {
  const g = c.getContext("2d");
  fitCanvas(c);
  g.fillStyle = "#05070c";
  g.fillRect(0, 0, c.width, c.height);
  if (!kc) return;
  const n = kc.length;
  const cols = 16;
  const rows = Math.ceil(n / cols);
  const w = c.width / cols, h = c.height / rows;
  kc.forEach((v, i) => {
    const x = (i % cols) * w, y = Math.floor(i / cols) * h;
    const gnn = 0.25 + 0.75 * v;
    g.fillStyle = `rgba(196,167,255,${gnn})`;
    g.fillRect(x + 1, y + 1, w - 2, h - 2);
  });
}

function loop() {
  paintHist($("h-rew"), spark.reward, "rgba(240,188,95,0.85)");
  paintHist($("h-pun"), spark.punish, "rgba(125,234,255,0.7)");
  paintKc($("kc"), spark.kc);
  requestAnimationFrame(loop);
}
loop();
