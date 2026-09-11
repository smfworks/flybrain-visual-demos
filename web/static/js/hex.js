import { fitCanvas } from "./core.js";

function hexPath(ctx, x, y, r) {
  ctx.beginPath();
  for (let i = 0; i < 6; i++) {
    const a = Math.PI / 6 + i * (Math.PI / 3);
    const px = x + r * Math.cos(a);
    const py = y + r * Math.sin(a);
    i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
  }
  ctx.closePath();
}

export class HexEye {
  constructor(canvas) {
    this.c = canvas;
    this.g = canvas.getContext("2d");
    this.h1 = [];
    this.h2 = [];
    this.on = [];
    this.off = [];
    this.source = "";
  }
  layout(hex) {
    if (!hex) return;
    this.h1 = hex.h1;
    this.h2 = hex.h2;
    this.source = hex.source || "";
    this.on = new Array(hex.n).fill(0);
    this.off = new Array(hex.n).fill(0);
  }
  rates(vision) {
    if (!vision) return;
    if (vision.on) this.on = vision.on;
    if (vision.off) this.off = vision.off;
  }
  draw({ accent = null, poke = null } = {}) {
    const c = this.c, g = this.g;
    const d = fitCanvas(c);
    const W = c.width, H = c.height;
    g.fillStyle = "#030508";
    g.fillRect(0, 0, W, H);
    if (!this.h1.length) return;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    const xy = [];
    for (let i = 0; i < this.h1.length; i++) {
      const x = this.h1[i] + 0.5 * this.h2[i];
      const y = this.h2[i] * Math.sqrt(3) / 2;
      xy.push([x, y]);
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
    const pad = 18 * d;
    const sx = (W - pad * 2) / (maxX - minX + 1e-6);
    const sy = (H - pad * 2) / (maxY - minY + 1e-6);
    const s = Math.min(sx, sy);
    const ox = (W - (maxX - minX) * s) / 2;
    const oy = (H - (maxY - minY) * s) / 2;
    const r = s * 0.54;

    for (let i = 0; i < xy.length; i++) {
      const px = ox + (xy[i][0] - minX) * s;
      const py = oy + (xy[i][1] - minY) * s;
      const on = (this.on[i] || 0) / 100;
      const off = (this.off[i] || 0) / 100;
      const a = Math.max(0.04, Math.min(1, on * 0.95 + off * 0.12));
      g.fillStyle = `rgba(125,234,255,${a.toFixed(3)})`;
      hexPath(g, px, py, r);
      g.fill();
      if (on > 0.55) {
        g.fillStyle = `rgba(234,244,250,${((on - 0.55) * 0.9).toFixed(3)})`;
        hexPath(g, px, py, r * 0.38);
        g.fill();
      }
    }
    if (accent) {
      const ax = ox + (accent.x * (maxX - minX)) * s; // unused
      void ax;
    }
    if (poke) {
      g.strokeStyle = "rgba(240,188,95,0.85)";
      g.lineWidth = 1.4 * d;
      g.beginPath();
      g.arc(poke.x * W, poke.y * H, 16 * d, 0, 7);
      g.stroke();
    }
  }

  hit(ev) {
    const r = this.c.getBoundingClientRect();
    return {
      u: (ev.clientX - r.left) / r.width,
      v: (ev.clientY - r.top) / r.height,
    };
  }
}
