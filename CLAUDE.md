# CLAUDE.md — GEOX Agent Instructions

> **GEOX is the earth intelligence organ of the arifOS federation.**
> Physics9-governed subsurface evidence. Evidence-only. Never decides alone.
> **DITEMPA BUKAN DIBERI — Forged, Not Given.**

---

## What you are working in

GEOX provides 33 MCP tools for geoscience evidence: well ingest, petrophysics, seismic, prospect evaluation, and vision interpretation. All outputs carry `cross_modal_stability`, `semantic_density_score`, and `dim_spot_flag`.

## Build / run / test

```bash
cd /root/geox
pip install -e ".[dev]"                              # or: uv sync --frozen
PYTHONPATH=src pytest tests/ -q --tb=short          # 229+ tests
PYTHONPATH=src python scripts/smoke_test.py         # smoke test
make lint && make format                             # ruff + mypy
python server.py                                    # start on :8081
systemctl restart geox-mcp                         # redeploy
curl -s http://localhost:8081/health               # health check
```

## Architecture

```
src/geox_core/   ← physics truth (NOT agent-facing)
    engines/petrophysics/   ← PINN, Archie, Sw, net-pay
    engines/seismic/        ← AC risk, synthetic, well-tie
    ac_risk.py              ← Anomalous Contrast Risk (564 lines)
    pinn.py                 ← Physics-Informed Neural Net (389 lines)

src/geox_mcp/    ← agent surface (tools, contracts, resources)
    tools/                  ← all 33 public tools
    contracts/              ← tool specs
    servers/                ← server bootstrap

GENESIS/         ← constitutional charter + Cross-Modal Fidelity Theorem
tests/           ← 60+ files, Nobel-grade physics locks (33/33)
apps/            ← welldesk, seismic_vision, earth_volume, judge_console
```

## The 33-tool canonical surface (key tools)

`geox_basin_profile` · `geox_claim_create` · `geox_claim_validate` · `geox_claim_seal` · `geox_prospect_evaluate` · `geox_data_ingest_bundle` · `geox_data_qc_bundle` · `geox_sequence_interpret` · `geox_seismic_compute` · `geox_horizon_contrast_surface` · `geox_subsurface_generate_candidates` · `geox_subsurface_verify_integrity` · `geox_vision_minimax_inference`

## Physics9 invariants (never violate)

1. All outputs carry epistemic tag: FACT / INTERPRETATION / SPECULATION
2. `overall_confidence` hard-capped at 0.90 (F5 HUMILITY)
3. `AC_Risk > 0.5` → `human_review_required = True` (F13)
4. SEAL verdict reserved for `physics_validated = True` (F9 ANTI-HANTU)
5. Claim state: `DRAFT → VALIDATED → SEALED` — no skipping

## Conventions

- `src/geox_core/` is physics truth — no agent-facing logic here.
- `src/geox_mcp/` is the agent surface — all new tools go here.
- PYTHONPATH=src required for all test and run commands.
- Line length: 130. Python target: 3.11.
- `pytest-asyncio` mode = auto.
- Latest release tag: `v2026.06.07`
- REPO= commit trailer: `REPO=geox` | Tags: `vYYYY.MM.DD`
