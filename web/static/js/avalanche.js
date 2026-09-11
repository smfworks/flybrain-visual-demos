import { $, connectDemo, setMode } from "./core.js";
import { HexEye } from "./hex.js";
import { CnsVolume } from "./cns.js";

const eye = new HexEye($("retina"));
const vol = new CnsVolume($("cns"));
let send = () => {};

connectDemo("avalanche", {
  onHello(m, s) {
    send = s;
    setMode(m);
    eye.layout(m.hex);
    vol.layout(m.soma);
    $("soma-src").textContent = (m.soma && m.soma.source) || "—";
  },
  onFrame(m) {
    const n = m.neural || {};
    if (n.vision) eye.rates(n.vision);
    if (n.scatter) vol.setSpikes(n.scatter);
    $("n-fire").textContent = (n.firing || 0).toLocaleString();
    $("n-ever").textContent = (n.ever || 0).toLocaleString();
    $("n-spk").textContent = Math.round(n.spikes_per_sec || 0).toLocaleString();
    $("n-vis").textContent = (n.visual || 0).toLocaleString();
    $("n-mot").textContent = (n.motor || 0).toLocaleString();
    if (n.mean_mv != null) $("n-mv").textContent = n.mean_mv.toFixed(1) + " mV";
    $("pokes").textContent = (m.pokes || 0).toLocaleString();
  },
});

function poke(ev, canvas) {
  const r = canvas.getBoundingClientRect();
  send({
    type: "poke",
    u: (ev.clientX - r.left) / r.width,
    v: (ev.clientY - r.top) / r.height,
  });
}
$("retina").addEventListener("pointerdown", (e) => poke(e, $("retina")));
$("cns").addEventListener("pointerdown", (e) => poke(e, $("cns")));
$("reset")?.addEventListener("click", () => send({ type: "reset" }));

function loop() {
  eye.draw();
  vol.draw();
  requestAnimationFrame(loop);
}
loop();
