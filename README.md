<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
federation_release: v2026.08.25
last_verified: 2026-08-25T04:30:00Z
live_commit: 6fa76d02
tools_live: 19 (canonical, live-witnessed via :8081/health)
apps_registered: 18
authority_ceiling: 555_COMPUTE_ONLY
truth_rule: live :8081/health + tools/list beat any static count in prose
-->

# GEOX — Earth Intelligence Engine

## Physics-grounded geological intelligence for exploration, hazard assessment, and earth science.

GEOX is an AI-powered earth science platform that transforms subsurface data — seismic, wells, basin models — into auditable geological evidence. Every claim is traceable, every uncertainty is visible, and every result separates observation from interpretation.

**Licensed under the Business Source License 1.1 (BSL-1.1).** Production use requires a license from the author.

---

## The Problem

Traditional earth science workflows are slow, siloed, and dependent on scarce domain expertise. A senior geologist's intuition about seismic patterns, reservoir quality, or basin maturity cannot scale. GEOX encodes this expertise into a system that can:

- Process seismic data and interpret structures at machine speed
- Run petrophysical analysis across well logs consistently
- Model basin evolution and charge systems quantitatively
- Assess geohazards (GLOF, fault activation) with physics-grounded reasoning
- Query paleobiological databases with spatial-temporal context

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      GEOX Earth Intelligence                 │
│  Port :8081  ·  MCP Interface  ·  19 Tools  ·  18 Apps     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │   Seismic    │  │Petrophysics  │  │   Basin Modeling   │ │
│  │ Interpret    │  │  Net Pay     │  │   Charge System    │ │
│  │   Compute    │  │  Quality     │  │   Volumetrics      │ │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬──────────┘ │
│         │                 │                     │           │
│  ┌──────▼─────────────────▼─────────────────────▼──────────┐│
│  │           GEOX Witness Layer (Δ·Ω·Ψ)                     ││
│  │  OBS (Observed) → DER (Derived) → INT (Interpreted)     ││
│  └──────────────────────────┬──────────────────────────────┘│
│                             │                               │
│  ┌──────────────┐  ┌───────▼───────┐  ┌──────────────────┐ │
│  │  Paleobiology │  │ Spatial-Temp  │  │  Geohazard/GLOF  │ │
│  │  (PaleoDB)   │  │   Reasoning   │  │   Cascade Model  │ │
│  └──────────────┘  └───────────────┘  └──────────────────┘ │
│                                                              │
└──────────────────────────┬───────────────────────────────────┘
                           │ MCP
                    ┌──────▼──────┐
                    │  arifOS FED  │
                    │  :7080 MCP   │
                    └─────────────┘
```

---

## Quick Start

### Docker

```bash
git clone https://github.com/arif-fazil/GEOX.git
cd GEOX
docker compose up -d

# Verify
curl http://localhost:8081/health
curl http://localhost:8081/tools/list
```

### Local Development

```bash
cd GEOX
pip install -e .
python -m geox.server --port 8081
```

---

## Domain Capabilities

### Seismic Interpretation
- SEG-Y processing and visualization
- Structural validation gates (G0–G10)
- Fault analysis and geomechanics
- Seismic attribute computation

### Petrophysics
- Well log analysis (LAS format)
- Net pay determination
- Porosity, permeability, saturation
- Rock physics transforms

### Basin Modeling
- Charge system analysis
- Thermal history modeling
- Migration pathway analysis
- STOIIP / GIIP volumetrics

### Geohazard Assessment
- GLOF (Glacial Lake Outburst Flood) cascade analysis
- Fault activation risk
- Landslide and subsidence modeling
- Real-time hazard monitoring

### Paleobiology
- PaleoDB integration for fossil record queries
- Biostratigraphic correlation
- Paleoenvironmental reconstruction

### Spatial-Temporal Reasoning
- Geological time-scale aware analysis
- Multi-scale spatial reasoning
- Provenance tracking for all claims

---

## Epistemic Transparency

Every GEOX output carries an epistemic label:

| Label | Meaning |
|-------|---------|
| **OBS** | Directly observed from data |
| **DER** | Derived via known physical laws |
| **INT** | Interpreted (expert-level inference) |
| **SPEC** | Speculative (hypothesis, needs validation) |

This is not a feature — it is a requirement. In exploration, the cost of confusing speculation with observation can be hundreds of millions of dollars.

---

## MCP Interface

GEOX exposes 19 canonical tools via MCP (Model Context Protocol):

`geox_basin` · `geox_geomechanics` · `geox_glof_cascade_*` · `geox_map` · `geox_model` · `geox_paleobiodb_query` · `geox_petrophysics` · `geox_prospect` · `geox_seismic_*` · `geox_source` · `geox_spatial` · `geox_temporal` · `geox_well_*`

Full tool list: `curl http://localhost:8081/tools/list`

---

## Use Cases

| Industry | Application | Value |
|----------|-------------|-------|
| Oil & Gas | Prospect evaluation | Reduce dry well risk |
| Mining | Resource estimation | Faster target generation |
| Geological Survey | Regional assessment | Scale expert analysis |
| Insurance | Geohazard modeling | Quantify exposure |
| Academia | Research reproducibility | Open, auditable earth science |

---

## Federation Role

GEOX is the earth witness in the arifOS federation. It computes geological evidence — it never adjudicates. All outputs flow through the arifOS constitutional kernel (F1–F13) before becoming sealed decisions.

**Sister Repos:**
- [arifOS](https://github.com/arif-fazil/arifOS) — Constitutional kernel (judgment)
- [AAA](https://github.com/arif-fazil/AAA) — Intelligence routing
- [A-FORGE](https://github.com/arif-fazil/A-FORGE) — Execution engine
- [WEALTH](https://github.com/arif-fazil/WEALTH) — Capital management
- [WELL](https://github.com/arif-fazil/WELL) — Biometric monitoring
- [arifFlow](https://github.com/arif-fazil/arifFlow) — Workflow orchestration

---

## Documentation

- [Full Technical README](docs/README-FULL.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Earth Intelligence Core Design](docs/ARCHITECTURE-EARTH-OS.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Changelog](CHANGELOG.md)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## License

**Business Source License 1.1 (BSL-1.1)**

Licensed under the BSL-1.1 with production use restrictions. Non-production, evaluation, testing, personal development, and academic research use is permitted. For production licensing, contact arifbfazil@gmail.com.

See [LICENSE](LICENSE) for the full text.

---

**DITEMPA BUKAN DIBERI** — Forged, Not Given.
