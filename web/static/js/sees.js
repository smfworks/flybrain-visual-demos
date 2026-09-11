import { $, connectDemo, setMode, makeGauges, paintGauges, DN_ROWS, fitCanvas } from "./core.js";
import { HexEye } from "./hex.js";
import { FlyCursor } from "./fly.js";

const eye = new HexEye($("retina"));
const fly = new FlyCursor();
const gauges = makeGauges($("cells"), DN_ROWS);
let scene = null;
let pageC = $("page");
let pathC = $("path");

connectDemo("sees", {
  onHello(m) {
    setMode(m);
    eye.layout(m.hex);
  },
  onFrame(m) {
    if (m.scene) scene = m.scene;
    if (m.vision) {
      eye.rates(m.vision);
      $("on-hz").textContent = m.vision.on_hz + " Hz";
      $("off-hz").textContent = m.vision.off_hz + " Hz";
    }
    if (m.motor) paintGauges(gauges, m.motor.dn);
    if (m.cursor) fly.set(m.cursor.x, m.cursor.y);
    if (m.trail) fly.trail = m.trail;
  },
});

function drawPage(c, scene, fly) {
  const g = c.getContext("2d");
  fitCanvas(c);
  const W = c.width, H = c.height;
  g.fillStyle = "#07090e";
  g.fillRect(0, 0, W, H);
  g.fillStyle = "#121820";
  g.fillRect(0, 0, W, H * 0.09);
  g.fillStyle = "rgba(125,234,255,0.35)";
  g.fillRect(0, H * 0.09, W, 2);
  if (scene && scene.boxes) {
    for (const b of scene.boxes) {
      const x = b.x * W, y = b.y * H, w = b.w * W, h = b.h * H;
      g.fillStyle = `rgba(125,234,255,${0.08 + b.glow})`;
      g.fillRect(x, y, w, h);
      g.strokeStyle = "rgba(125,234,255,0.35)";
      g.strokeRect(x + 0.5, y + 0.5, w, h);
    }
  }
  fly.target = null;
  fly.draw(c, { showTarget: false, showTrail: true });
}

function drawPath(c, trail, cur) {
  const g = c.getContext("2d");
  fitCanvas(c);
  g.fillStyle = "#05070c";
  g.fillRect(0, 0, c.width, c.height);
  if (trail && trail.length > 1) {
    g.beginPath();
    trail.forEach((p, i) => {
      const x = p[0] * c.width, y = p[1] * c.height;
      i ? g.lineTo(x, y) : g.moveTo(x, y);
    });
    g.strokeStyle = "rgba(125,234,255,0.55)";
    g.lineWidth = 2;
    g.stroke();
  }
  if (cur) {
    g.fillStyle = "#7deaff";
    g.beginPath();
    g.arc(cur.x * c.width, cur.y * c.height, 4, 0, 7);
    g.fill();
  }
}

function loop() {
  drawPage(pageC, scene, fly);
  eye.draw();
  drawPath(pathC, fly.trail, { x: fly.x, y: fly.y });
  requestAnimationFrame(loop);
}
loop();
