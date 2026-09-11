export const $ = (id) => document.getElementById(id);

export function fitCanvas(c, maxDpr = 2) {
  const r = c.getBoundingClientRect();
  const d = Math.min(window.devicePixelRatio || 1, maxDpr);
  const w = Math.max(2, Math.floor(r.width * d));
  const h = Math.max(2, Math.floor(r.height * d));
  if (c.width !== w || c.height !== h) {
    c.width = w;
    c.height = h;
  }
  return d;
}

export function connectDemo(name, { onHello, onFrame } = {}) {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  let ws, tries = 0;
  const send = (obj) => {
    if (ws && ws.readyState === 1) ws.send(JSON.stringify(obj));
  };
  function open() {
    ws = new WebSocket(`${proto}//${location.host}/ws/${name}`);
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.type === "hello") onHello && onHello(m, send);
      else if (m.type === "frame") onFrame && onFrame(m, send);
    };
    ws.onopen = () => { tries = 0; };
    ws.onclose = () => {
      tries += 1;
      setTimeout(open, Math.min(4000, 400 * tries));
    };
  }
  open();
  return { send, get ws() { return ws; } };
}

export function setMode(hello) {
  const pill = $("mode");
  const pip = $("pip");
  const label = $("mode-label");
  if (label) label.textContent = hello.label || hello.mode || "LITE";
  if (pip) pip.classList.add("on");
  if (pill) {
    pill.classList.toggle("cyan", hello.mode === "full");
    pill.classList.toggle("amber", hello.mode !== "full");
  }
  const blurb = $("mode-blurb");
  if (blurb) blurb.textContent = hello.blurb || "";
}

export function makeGauges(host, rows) {
  const map = {};
  host.innerHTML = "";
  for (const [key, name, kind] of rows) {
    const el = document.createElement("div");
    el.className = "cell";
    el.innerHTML = `<span class="nm"></span><span class="bar2"><span class="fill ${kind || ""}"></span></span><span class="hz">0</span>`;
    el.querySelector(".nm").textContent = name;
    host.appendChild(el);
    map[key] = { fill: el.querySelector(".fill"), hz: el.querySelector(".hz") };
  }
  return map;
}

export function paintGauges(map, dn, scale = 4.5) {
  if (!dn) return;
  for (const k of Object.keys(map)) {
    const v = dn[k] || 0;
    map[k].hz.textContent = Number(v).toFixed(0);
    map[k].fill.style.width = Math.min(100, Math.abs(v) / scale) + "%";
  }
}

export const DN_ROWS = [
  ["steer_L", "DNa02 L", ""],
  ["steer_R", "DNa02 R", ""],
  ["fwd_L", "DNa01 L", "live"],
  ["fwd_R", "DNa01 R", "live"],
  ["back", "MDN", "amber"],
  ["stop", "DNp09", "red"],
];
