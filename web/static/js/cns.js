import { fitCanvas } from "./core.js";

export class CnsVolume {
  constructor(canvas) {
    this.c = canvas;
    this.g = canvas.getContext("2d");
    this.xyz = [];
    this.region = [];
    this.spikes = [];
    this.angle = 0.4;
    this.idle = true;
  }
  layout(soma) {
    if (!soma) return;
    this.xyz = soma.xyz || [];
    this.region = soma.region || [];
  }
  setSpikes(pts) {
    this.spikes = pts || [];
    this.idle = false;
  }
  draw() {
    const c = this.c, g = this.g;
    const d = fitCanvas(c);
    const W = c.width, H = c.height;
    g.fillStyle = "#020307";
    g.fillRect(0, 0, W, H);
    this.angle += 0.0045;
    const ca = Math.cos(this.angle), sa = Math.sin(this.angle);
    const project = (x, y, z) => {
      const xr = x * ca - y * sa;
      const yr = x * sa + y * ca;
      const s = 0.42 * Math.min(W, H);
      return [W * 0.5 + xr * s, H * 0.48 + (z * 0.72 - yr * 0.18) * s, yr];
    };
    const depth = [];
    for (let i = 0; i < this.xyz.length; i++) {
      const [x, y, z] = this.xyz[i];
      const p = project(x, y, z);
      depth.push([p[2], p[0], p[1], this.region[i] || "central", false]);
    }
    const spikeSet = this.spikes;
    for (const s of spikeSet) {
      const p = project(s[0], s[1], s[2]);
      depth.push([p[2], p[0], p[1], "spike", true]);
    }
    depth.sort((a, b) => a[0] - b[0]);
    for (const [, x, y, reg, spike] of depth) {
      if (spike) {
        g.fillStyle = "rgba(111,220,166,0.95)";
        g.fillRect(x, y, 2.2 * d, 2.2 * d);
        g.fillStyle = "rgba(111,220,166,0.18)";
        g.beginPath();
        g.arc(x, y, 6.5 * d, 0, 7);
        g.fill();
      } else {
        const col =
          reg === "optic_l" || reg === "optic_r"
            ? "rgba(125,234,255,0.16)"
            : reg === "vnc"
            ? "rgba(240,188,95,0.12)"
            : "rgba(226,234,241,0.08)";
        g.fillStyle = col;
        g.fillRect(x, y, 1.15 * d, 1.15 * d);
      }
    }
  }
}
