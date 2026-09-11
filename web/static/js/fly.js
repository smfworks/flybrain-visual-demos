import { fitCanvas } from "./core.js";

export class FlyCursor {
  constructor() {
    this.x = 0.5;
    this.y = 0.5;
    this.tx = 0.5;
    this.ty = 0.5;
    this.wing = 0;
    this.trail = [];
    this.target = null;
  }
  set(x, y) {
    this.tx = x;
    this.ty = y;
  }
  draw(c, { showTarget = true, showTrail = true } = {}) {
    const g = c.getContext("2d");
    const d = fitCanvas(c);
    const W = c.width, H = c.height;
    this.x += (this.tx - this.x) * 0.22;
    this.y += (this.ty - this.y) * 0.22;
    this.wing += 0.55;

    if (showTrail && this.trail.length > 1) {
      g.beginPath();
      this.trail.forEach((p, i) => {
        const x = p[0] * W, y = p[1] * H;
        i ? g.lineTo(x, y) : g.moveTo(x, y);
      });
      g.strokeStyle = "rgba(125,234,255,0.28)";
      g.lineWidth = 1.4 * d;
      g.stroke();
    }

    if (showTarget && this.target) {
      const x = this.target.x * W, y = this.target.y * H;
      const glow = g.createRadialGradient(x, y, 2 * d, x, y, 48 * d);
      glow.addColorStop(0, "rgba(240,188,95,0.95)");
      glow.addColorStop(0.25, "rgba(240,188,95,0.35)");
      glow.addColorStop(1, "rgba(240,188,95,0)");
      g.fillStyle = glow;
      g.beginPath();
      g.arc(x, y, 48 * d, 0, 7);
      g.fill();
    }

    const x = this.x * W, y = this.y * H, s = Math.min(W, H) * 0.028;
    g.save();
    g.translate(x, y);
    g.fillStyle = "rgba(125,234,255,0.92)";
    g.beginPath();
    g.ellipse(0, 0, s * 0.62, s * 0.42, 0, 0, 7);
    g.fill();
    g.beginPath();
    g.ellipse(s * 0.62, -s * 0.06, s * 0.30, s * 0.28, 0, 0, 7);
    g.fill();
    g.fillStyle = "rgba(125,234,255,0.34)";
    for (const sgn of [1, -1]) {
      g.beginPath();
      g.ellipse(
        -s * 0.22,
        sgn * (s * 0.42 + Math.abs(Math.sin(this.wing)) * s * 0.16),
        s * 0.72,
        s * 0.20,
        sgn * 0.5,
        0,
        7
      );
      g.fill();
    }
    g.restore();
  }
}

export function clearField(c, color = "#030508") {
  const g = c.getContext("2d");
  fitCanvas(c);
  g.fillStyle = color;
  g.fillRect(0, 0, c.width, c.height);
}
