# GEOX — Earth Intelligence & Governed World Model

> **Status:** OPERATIONAL | **Organ:** FIELD (γ) | **Authority:** arifOS
> **Domain:** `geox.arif-fazil.com`

## 🏛️ What this repo is

The geoscientific domain coprocessor for the arifOS federation. GEOX prepares earth evidence — petrophysics, well log analysis, formation evaluation, and geophysical calculations — through a governed FastMCP surface. All evidence passes through the F3 WITNESS floor before being presented to the reasoning kernel.

**GEOX owns the FIELD — the empirical grounding layer for earth sciences within the federation.**

## 📦 Ownership

- **Owns**: Well log processing (lasio, welly), petrophysical calculations, formation evaluation, geophysical evidence preparation.
- **Does NOT own**: Constitutional judgment (arifOS), economic logic (WEALTH).

## 🏗️ Current Structure

```
GEOX/
├── server.py                 # Unified FastMCP server (15 tools)
├── contracts/              # Pydantic schemas, tool contracts, parity matrices
├── control_plane/         # API routing, FastMCP canonical server
├── execution_plane/       # Calculation engines, VPS server
├── services/             # Evidence store, geo fabric, governance judge
├── geox/                 # Modern dimension-native: core/, dimensions/, apps/, ingest/, skills/
├── arifos/               # Legacy domain logic: THEORY/, ENGINE/, TOOLS/, GOVERNANCE/
│   ├── THEORY/          # Formation evaluation, capillary pressure, SW analysis
│   ├── ENGINE/          # Calculation engine
│   ├── TOOLS/           # Domain tools
│   └── GOVERNANCE/     # F3 WITNESS enforcement
├── compatibility/       # Legacy alias bridge
├── tests/               # pytest suite with shared fixtures (conftest.py)
├── docs/               # Architecture and domain specs
└── apps/               # Micro-frontend manifests
```

## 🚀 Verified Commands

```bash
# Install
pip install -e ".[dev]"

# Run canonical MCP server
python server.py

# Test
pytest tests/ -q

# Lint
ruff check server.py geox/
ruff format geox/
mypy server.py geox/
```

## 🔗 Federation Loop

- [arifOS](https://github.com/ariffazil/arifOS) — Kernel (constitutional judgment, F3 WITNESS enforcement)
- [WEALTH](https://github.com/ariffazil/wealth) — Capital (economic constraints on field development)

---

*Last Verified: 2026.05.16 | 999 SEAL ALIVE*
