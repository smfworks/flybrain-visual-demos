import { HexEye } from "./hex.js";
import { connectDemo, $ } from "./core.js";

const eye = new HexEye($("hero"));
let rates = null;

connectDemo("chase", {
  onHello(m) {
    eye.layout(m.hex);
    const pill = $("live-mode");
    if (pill) pill.textContent = (m.label || "LITE") + " · private preview";
    $("pip") && $("pip").classList.add("on");
  },
  onFrame(m) {
    if (m.vision) eye.rates(m.vision);
    rates = m.vision;
  },
});

function loop() {
  eye.draw();
  requestAnimationFrame(loop);
}
loop();

fetch("/api/status")
  .then((r) => r.json())
  .then((d) => {
    const el = $("live-mode");
    if (el) el.textContent = `${d.label} · private preview`;
  })
  .catch(() => {});
