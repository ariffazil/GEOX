# Deployment — GEOX (Earth Sciences)

## Prerequisites

- Docker 24+ and Docker Compose v2
- 8 CPU cores, 16GB RAM (seismic processing is compute-intensive)
- Ports: `8081` (GEOX organ)

## Quick Start

```bash
git clone https://github.com/arif-fazil/GEOX.git
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
