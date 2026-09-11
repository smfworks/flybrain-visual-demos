import { fitCanvas } from "./core.js";

export class CnsVolume {
  constructor(canvas) {
    this.c = canvas;
    this.g = canvas.getContext("2d");
    this.xyz = [];
    this.region = [];
    this.spikes = [];
    this.angle = 0.55;
  }
  layout(soma) {
    if (!soma) return;
    this.xyz = soma.xyz || [];
    this.region = soma.region || [];
  }
  setSpikes(pts) {
    this.spikes = pts || [];
  }
  draw() {
    const c = this.c, g = this.g;
    const d = fitCanvas(c);
    const W = c.width, H = c.height;
    g.fillStyle = "#020307";
    g.fillRect(0, 0, W, H);
    this.angle += 0.006;
    const ca = Math.cos(this.angle), sa = Math.sin(this.angle);
    const s = 0.46 * Math.min(W, H);
    const project = (x, y, z) => {
      const xr = x * ca - y * sa;
      const yr = x * sa + y * ca;
      return [W * 0.5 + xr * s, H * 0.46 + (z * 0.78 - yr * 0.22) * s, yr];
    };
    const depth = [];
    for (let i = 0; i < this.xyz.length; i++) {
      const [x, y, z] = this.xyz[i];
      const p = project(x, y, z);
      depth.push([p[2], p[0], p[1], this.region[i] || "central", 0]);
    }
    for (const sp of this.spikes) {
      const p = project(sp[0], sp[1], sp[2]);
      depth.push([p[2], p[0], p[1], "spike", sp[3] == null ? 1 : sp[3]]);
    }
    depth.sort((a, b) => a[0] - b[0]);
    for (const [, x, y, reg, glow] of depth) {
      if (reg === "spike") {
        const a = 0.35 + 0.65 * glow;
        g.fillStyle = `rgba(111,220,166,${a})`;
        const sz = (2.4 + 3.2 * glow) * d;
        g.beginPath();
        g.arc(x, y, sz, 0, 7);
        g.fill();
        g.fillStyle = `rgba(111,220,166,${0.12 * glow})`;
        g.beginPath();
        g.arc(x, y, 10 * d * glow, 0, 7);
        g.fill();
      } else {
        const col =
          reg === "optic_l" || reg === "optic_r"
            ? "rgba(125,234,255,0.55)"
            : reg === "vnc"
            ? "rgba(240,188,95,0.5)"
            : "rgba(210,224,234,0.38)";
        g.fillStyle = col;
        g.fillRect(x, y, 1.85 * d, 1.85 * d);
      }
    }
  }
}
