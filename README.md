# Tailscale Control UI

A small local web interface for viewing and toggling this machine's Tailscale exit-node advertising.

## Run

Requires Python 3.12+, Tailscale, and a local user authorized to change Tailscale settings.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8094
```

Open http://127.0.0.1:8094. Optionally set `SERVICE_URL` to your own private serving URL.

The app has no built-in authentication or cross-site request protection. Keep it on localhost, or behind a trusted access-controlled private proxy; do not publish the running service on the public internet. Actions change the current host's network routing advertisement. This repository contains source only and no tailnet identity or deployment configuration.

Run tests with `pytest`.
