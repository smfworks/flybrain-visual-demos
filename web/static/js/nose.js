import { $, connectDemo, setMode, makeGauges, paintGauges, DN_ROWS, fitCanvas } from "./core.js";
import { HexEye } from "./hex.js";
import { FlyCursor } from "./fly.js";

const eye = new HexEye($("retina"));
const fly = new FlyCursor();
const gauges = makeGauges($("cells"), DN_ROWS);
let send = () => {};
let olf = null;
let particles = [];
let odour = null;

connectDemo("nose", {
  onHello(m, s) {
    send = s;
    setMode(m);
    eye.layout(m.hex);
    const host = $("odours");
    const odours = (m.olfaction && m.olfaction.odours) || {};
    host.innerHTML = "";
    const none = document.createElement("button");
    none.className = "ghost";
    none.textContent = "clear air";
    none.onclick = () => { odour = null; send({ type: "odour", id: "none" }); };
    host.appendChild(none);
    for (const id of Object.keys(odours)) {
      const b = document.createElement("button");
      b.textContent = odours[id].name;
      b.title = odours[id].bias;
      b.onclick = () => {
        odour = id;
        send({ type: "odour", id, concentration: 1 });
      };
      host.appendChild(b);
    }
  },
  onFrame(m) {
    if (m.vision) eye.rates(m.vision);
    if (m.motor) paintGauges(gauges, m.motor.dn);
    if (m.cursor) fly.set(m.cursor.x, m.cursor.y);
    if (m.trail) fly.trail = m.trail;
    if (m.target) fly.target = m.target;
    olf = m.olfaction;
    if (olf) {
      $("peak").textContent = `${olf.peak}  ${olf.peak_hz} Hz`;
      $("mean").textContent = olf.mean_hz + " Hz";
      $("pc1").textContent = olf.pc1_hz ? olf.pc1_hz + " Hz" : "—";
      $("odour-name").textContent = olf.odour || "clear air";
      $("olf-note").textContent = olf.note || "No odour. Spontaneous ORN rates only.";
      paintTiles(olf.tiles);
    }
  },
});

function paintTiles(tiles) {
  const c = $("al");
  const g = c.getContext("2d");
  fitCanvas(c);
  g.fillStyle = "#05070c";
  g.fillRect(0, 0, c.width, c.height);
  if (!tiles) return;
  const mx = Math.max(20, ...tiles.map((t) => t.hz));
  for (const t of tiles) {
    const x = t.u * c.width, y = t.v * c.height;
    const a = Math.min(1, t.hz / mx);
    g.fillStyle = `rgba(196,167,255,${0.12 + a * 0.85})`;
    g.beginPath();
    g.arc(x, y, 7 + a * 10, 0, 7);
    g.fill();
  }
}

function stepPlume() {
  const c = $("plume");
  const g = c.getContext("2d");
  fitCanvas(c);
  g.fillStyle = "rgba(3,5,8,0.22)";
  g.fillRect(0, 0, c.width, c.height);
  if (odour) {
    for (let i = 0; i < 6; i++) {
      particles.push({
        x: 0.08 + Math.random() * 0.04,
        y: 0.45 + (Math.random() - 0.5) * 0.28,
        vx: 0.004 + Math.random() * 0.008,
        vy: (Math.random() - 0.5) * 0.004,
        a: 0.4 + Math.random() * 0.5,
      });
    }
  }
  particles = particles.filter((p) => p.x < 1.1 && p.a > 0.02);
  const col = odour === "geosmin" || odour === "CO2" ? [255, 139, 122] : odour === "cVA" ? [240, 188, 95] : [125, 234, 255];
  for (const p of particles) {
    p.x += p.vx;
    p.y += p.vy + Math.sin(p.x * 12) * 0.0015;
    p.a *= 0.992;
    g.fillStyle = `rgba(${col[0]},${col[1]},${col[2]},${p.a})`;
    g.beginPath();
    g.arc(p.x * c.width, p.y * c.height, 2.4, 0, 7);
    g.fill();
  }
  fly.draw(c, { showTarget: false, showTrail: true });
}

function loop() {
  stepPlume();
  eye.draw();
  requestAnimationFrame(loop);
}
loop();
