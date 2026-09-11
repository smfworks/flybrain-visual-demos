import { $, connectDemo, setMode, makeGauges, paintGauges, DN_ROWS } from "./core.js";
import { HexEye } from "./hex.js";
import { FlyCursor, clearField } from "./fly.js";

const field = $("field");
const retina = $("retina");
const eye = new HexEye(retina);
const fly = new FlyCursor();
const gauges = makeGauges($("cells"), DN_ROWS);
let send = () => {};
let dragging = false;

connectDemo("chase", {
  onHello(m, s) {
    send = s;
    setMode(m);
    eye.layout(m.hex);
    $("hex-src").textContent = m.hex.source;
    $("map-note").textContent = m.blurb;
  },
  onFrame(m) {
    if (m.vision) {
      eye.rates(m.vision);
      $("on-hz").textContent = m.vision.on_hz + " Hz";
      $("off-hz").textContent = m.vision.off_hz + " Hz";
      $("n-cols").textContent = m.vision.columns.toLocaleString();
    }
    if (m.motor) paintGauges(gauges, m.motor.dn);
    if (m.cursor) fly.set(m.cursor.x, m.cursor.y);
    if (m.trail) fly.trail = m.trail;
    if (m.target) fly.target = m.target;
    $("steps").textContent = (m.steps || 0).toLocaleString();
  },
});

function pointer(ev) {
  const r = field.getBoundingClientRect();
  const x = (ev.clientX - r.left) / r.width;
  const y = (ev.clientY - r.top) / r.height;
  send({ type: "pointer", x, y });
}
field.addEventListener("pointerdown", (e) => { dragging = true; pointer(e); field.setPointerCapture(e.pointerId); });
field.addEventListener("pointermove", (e) => { if (dragging) pointer(e); });
field.addEventListener("pointerup", () => { dragging = false; });
$("reset")?.addEventListener("click", () => send({ type: "reset" }));

function loop() {
  clearField(field, "#05070c");
  fly.draw(field);
  eye.draw();
  requestAnimationFrame(loop);
}
loop();
