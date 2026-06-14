# GEOX Quickstart — 15 Minutes to Running Locally

> **GEOX** is the earth intelligence organ of the arifOS federation. It connects AI agents to subsurface evidence — well logs, petrophysics, seismic data, and prospect evaluation — and enforces constitutional rules that prevent the AI from overstating confidence, skipping evidence, or making irreversible drilling decisions without human approval. It observes. It computes. It never decides alone.

---

## What You'll Have

A running FastMCP server on `http://localhost:8081` exposing 39 geoscience tools.

## Prerequisites

- Python 3.11+
- pip

## Quickstart

```bash
# 1. Clone
git clone https://github.com/ariffazil/geox.git
cd geox

# 2. Install (editable, with dev extras for tools)
pip install -e ".[dev]"

# 3. Start the server
python server.py
```

**That's it.** The server starts on `http://localhost:8081`.

## Verify

```bash
# Health check
curl http://localhost:8081/health | python3 -m json.tool

# Expected: {"status": "healthy", "service": "geox-unified"}

# List tools (40 canonical tools)
curl -s http://localhost:8081/tools | python3 -m json.tool | head -30

# System registry status
curl -s http://localhost:8081/system/registry | python3 -m json.tool
```

## Quick Test

```bash
# Compute a synthetic seismogram (forward model)
curl -s -X POST http://localhost:8081/call \
  -H "Content-Type: application/json" \
  -d '{"tool":"geox_seismic_compute","args":{"mode":"synthetic","vp":[2500,2800,3200,3500],"rho":[2.2,2.3,2.4,2.5],"depth":[500,600,700,800],"wavelet_type":"ricker","wavelet_freq":25}}' \
  | python3 -m json.tool | head -30
```

## Key Tools

| Tool | What It Does |
|------|-------------|
| `geox_data_ingest_bundle` | Ingest LAS, CSV, SEG-Y, structural data |
| `geox_data_qc_bundle` | Quality control — depth monotonicity, null %, physical range checks |
| `geox_seismic_compute` | Forward modeling, well ties, time-depth anchoring |
| `geox_prospect_evaluate` | Volumetrics, probability of success, EVOI |
| `geox_subsurface_generate_candidates` | Ensemble petrophysics/structure/flattening |
| `geox_sequence_interpret` | Sequence stratigraphy — single well, project, correlation |
| `geox_claim_create` | Create structured Earth interpretation claims with provenance |
| `geox_claim_challenge` | Multi-discipline self-argument — geology vs geomechanics vs drilling |

## What You Need for Real Data

GEOX works with synthetic fixtures out of the box — no real data required for testing. For real-world use:

1. Place LAS files in `data/geox_las/`  
2. Run `geox_data_ingest_bundle(source_uri="data/geox_las/your_well.las")`
3. Run `geox_data_qc_bundle(artifact_ref="<returned_id>", artifact_type="well_log")`
4. Use the verified artifact in downstream tools

## Common Issues

- **ImportError: lasio/welly/striplog** → Run `pip install lasio welly striplog`
- **Port 8081 in use** → Set `GEOX_PORT=8082` before starting
- **SEG-Y support requires segyio** → `pip install segyio` for seismic file support

## Next Steps

- Read the [arifOS Constitution](https://github.com/ariffazil/arifOS/blob/main/docs/CONSTITUTION.md)
- Set up [WEALTH](https://github.com/ariffazil/wealth) for capital intelligence
- Set up [WELL](https://github.com/ariffazil/well) for human readiness
- Read the [Glossary](https://github.com/ariffazil/arifOS/blob/main/docs/GLOSSARY.md)
- Read the [GENESIS Charter](GENESIS/000_MANIFESTO.md) for the founding doctrine

---

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
