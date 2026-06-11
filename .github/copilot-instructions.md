# GEOX — Earth Intelligence Organ

GEOX is the **earth evidence layer** of the arifOS federation. It connects AI agents to subsurface evidence — well logs, petrophysics, seismic, prospect evaluation — under Physics9 constraints. It observes. It computes. It never decides alone.

## Repo identity

- **Path:** `/root/geox`
- **Port:** 8081 | **Domain:** `geox.arif-fazil.com/mcp`
- **Systemd:** `geox-mcp.service`
- **Language:** Python 3.11

## Build, test, run

```bash
pip install -e ".[dev]"              # or: uv sync --frozen
PYTHONPATH=src pytest tests/ -q --tb=short   # 60+ test files, 229+ pass
make lint && make format             # ruff + mypy
make smoke                           # PYTHONPATH=src python scripts/smoke_test.py
python server.py                     # FastMCP server on :8081

# Redeploy
make build && systemctl restart geox-mcp
```

## Key directories

| Path | Role |
|------|------|
| `src/geox_core/` | Truth engine (NOT agent-facing): physics, petrophysics, seismic |
| `src/geox_core/engines/petrophysics/` | PINN, Archie, Sw, net-pay |
| `src/geox_core/engines/seismic/` | AC risk, synthetic, well-tie |
| `src/geox_core/ac_risk.py` | Anomalous Contrast Risk engine (564 lines) |
| `src/geox_core/pinn.py` | Physics-Informed Neural Net (389 lines) |
| `src/geox_mcp/` | MCP surface (agent-facing): tools, contracts, resources |
| `GENESIS/` | Constitutional charter + Cross-Modal Fidelity Theorem |
| `tests/` | 60+ files including Nobel-grade physics locks (33/33) |
| `apps/` | Standalone apps: welldesk, seismic_vision, earth_volume |

## Canonical MCP surface (33 tools)

Core: `geox_basin_profile`, `geox_claim_create`, `geox_prospect_evaluate`, `geox_data_ingest_bundle`, `geox_sequence_interpret`, `geox_seismic_compute`, `geox_subsurface_generate_candidates`, `geox_horizon_contrast_surface`, `geox_vision_minimax_inference`

## Physics9 constraints

All outputs carry epistemic tags (FACT/INTERPRETATION/SPECULATION) and cross-modal stability scores. Never assert CLAIM without verified evidence. `AC_Risk > 0.5` → F13 human review required.

## Conventions

- `src/geox_core/` is the physics truth — do NOT add agent-facing logic here.
- `src/geox_mcp/` is the agent surface — all tools go here.
- PYTHONPATH=src required for all test/run commands.
- Line length: 130. Target: py311.
- REPO= commit trailer: `REPO=geox`
- Tags: `vYYYY.MM.DD` only (latest: `v2026.06.07`).
