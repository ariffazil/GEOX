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
