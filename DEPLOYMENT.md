# Deployment — GEOX (Earth Sciences)

## Live VPS (KVM8) — this is how GEOX actually runs

- Unit: `geox-mcp.service`
- Runtime: `/opt/geox`
- Source: `/root/GEOX` (`github.com/ariffazil/GEOX`)
- Bind: `127.0.0.1:8081`
- Entry: `/opt/geox/.venv/bin/python3 -m geox_mcp.server --host 127.0.0.1 --port 8081`

```bash
# After gitwrap on /root/GEOX:
git -C /opt/geox fetch origin
git -C /opt/geox reset --hard origin/main
systemctl restart geox-mcp.service
curl -sf http://127.0.0.1:8081/health
```

Do not treat Docker Compose as the live path on this host.

### Deploy verification — TWO checks, not one

`/drift` only compares the runtime with **its own build** — `drift_count=0` never proves
the runtime is current. Always check both:

```bash
# 1. surface parity (live == its build's canonical)
curl -sf http://127.0.0.1:8081/drift | python3 -m json.tool | grep -E "drift_count|gap_count|\"ok\""

# 2. runtime vs intended source commit (the honest lag signal)
curl -sf http://127.0.0.1:8081/health | python3 -c "import json,sys; print(json.load(sys.stdin)['git_version'])"
git -C /root/GEOX rev-parse --short main

# 3. README status snapshot (host-side; needs the live organ)
cd /root/GEOX && PYTHONPATH=src python3 scripts/generate_readme_status.py
```

`git_version` equal to the intended deploy commit = current. A feature-branch runtime
ahead of `main` is lag-by-design until the branch merges; `main` is only truthful after a
deploy from `main`.

### Rollback

```bash
git -C /opt/geox reset --hard <previous-good-sha>
systemctl restart geox-mcp.service
curl -sf http://127.0.0.1:8081/health   # git_version must show the rollback sha
```

### Operational map (infra detail — the public README intentionally omits this)

| Thing | Value |
|---|---|
| Source repo | `/root/GEOX` → `github.com/ariffazil/GEOX` |
| Runtime | `/opt/geox` (FHS git clone; source ≠ runtime until deploy) |
| Process | `/opt/geox/.venv/bin/python3 -m geox_mcp.server --host 127.0.0.1 --port 8081` |
| Unit | `geox-mcp.service` (systemd; drop-ins: mesh-hosts, stateless, zz-sandbox) |
| Public ingress | Caddy `geox.arif-fazil.com` → `/var/www/html/geox` SPA + `/mcp` proxy; auth `P3_AUTH_LITE` (`/root/GEOX/oauth/static_clients.yaml`) |
| Earth Witness chat (local only) | `/root/GEOX/chat/` → `uvicorn chat.server:app --host 127.0.0.1 --port 8765` — NOT publicly exposed; Gate 6 Class-B pending |
| Federation topology SOT | `/root/AAA/federation/organs.yaml` (machine) + `/root/AAA/docs/ORGAN.md` (human); live `/health` beats both |

## Prerequisites (portable / Docker)

- Docker 24+ and Docker Compose v2
- 8 CPU cores, 16GB RAM (seismic processing is compute-intensive)
- Ports: `8081` (GEOX organ)

## Quick Start (Docker — not KVM8 live)

```bash
git clone https://github.com/ariffazil/GEOX.git
cd GEOX
docker compose up -d

# Verify
curl http://localhost:8081/health
```

## Docker Compose

```yaml
services:
  geox:
    image: arifazil/geox:latest
    ports:
      - "8081:8081"
    volumes:
      - geox-data:/var/lib/geox
      - ./seismic-data:/data/seismic:ro
    environment:
      - GEOX_MODEL_PATH=/var/lib/geox/models
    restart: unless-stopped

volumes:
  geox-data:
```

## Domain Capabilities

- Seismic interpretation (SEG-Y processing)
- Petrophysics analysis
- Basin modeling
- GLOF cascade analysis
- Paleobiology queries (PaleoDB integration)
- Spatial-temporal earth reasoning

## Data Requirements

GEOX can operate in two modes:
1. **Query mode** — uses public data sources (PaleoDB, USGS, etc.)
2. **Analysis mode** — requires user-provided seismic/well data (SEG-Y, LAS files)
