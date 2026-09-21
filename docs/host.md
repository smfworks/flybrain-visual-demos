# Public host

The live gallery is **[https://flybrain.aionasmfworks.com](https://flybrain.aionasmfworks.com)**.
This note is how that kind of host is meant to run. No secrets or credentials
are required for lite mode.

## Bind address

`python -m flydemos` and the Docker image both bind **`0.0.0.0`** on
`PORT` (default `4747`). That is the right bind for a reverse proxy in front
of the gallery. Do not publish the raw port to the internet if a proxy already
terminates TLS.

## Option A — Docker Compose (lite)

From a checkout such as `/opt/flybrain-visual-demos`:

```bash
cd /opt/flybrain-visual-demos
docker compose up --build -d
```

See [compose.md](compose.md). Compose is enough for the public lite host.

A systemd wrapper around compose, if you want the unit to own the process:

```ini
[Unit]
Description=SMF Works flybrain visual demos (compose)
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/flybrain-visual-demos
ExecStart=/usr/bin/docker compose up --build -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

## Option B — systemd + venv

A sample unit lives at [`deploy/flybrain-visual-demos.service`](../deploy/flybrain-visual-demos.service).
Paths are placeholders (`/opt/flybrain-visual-demos`). Edit them before enabling.

User session:

```bash
mkdir -p ~/.config/systemd/user
cp deploy/flybrain-visual-demos.service ~/.config/systemd/user/
# edit WorkingDirectory / ExecStart paths
systemctl --user daemon-reload
systemctl --user enable --now flybrain-visual-demos
systemctl --user status flybrain-visual-demos
```

System-wide: copy the same file to `/etc/systemd/system/`, set `User=` /
`Group=` as you prefer, and use `systemctl` (not `--user`). Change
`WantedBy=default.target` to `WantedBy=multi-user.target` for a machine boot
install.

## Reverse proxy

Put TLS and the public name on a reverse proxy; keep uvicorn on localhost or
a private port.

Caddy sketch:

```
flybrain.aionasmfworks.com {
    reverse_proxy 127.0.0.1:4747
}
```

nginx sketch:

```
server {
    listen 443 ssl;
    server_name flybrain.aionasmfworks.com;
    # ssl_certificate / ssl_certificate_key — your existing cert paths

    location / {
        proxy_pass http://127.0.0.1:4747;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

The `Upgrade` / `Connection` headers matter: several demos use `/ws/{demo}`.

## Health check

```bash
curl -fsS https://flybrain.aionasmfworks.com/
curl -fsS https://flybrain.aionasmfworks.com/healthz
```

Locally, the same paths on `http://127.0.0.1:4747`. `/healthz` is JSON
`{"ok": true, "mode": ...}` and does not require the 1.1 GB graph.

## Honesty on the host

Lite is the intended public default. Loading `graph.npz` on the public host
is an operator choice, not a requirement. Connectome files stay CC-BY
(Janelia FlyEM / Cambridge / Google). The simulation approach follows
fruitflydev/flycoinrh. SMF Works ships the gallery; it does not own the
upstream brain.
