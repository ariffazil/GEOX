# GEOX Real Well Data

## Available on this host (2026-07-09)

| Well | Path | Status | Notes |
|------|------|--------|-------|
| **15/9-19 (Q15 North Sea)** | `q15_15_9_19/q15_15_9_19.las` | **REAL LAS** | Sonic (AC), density (DEN), GR, NEU, RDEP + petro curves. Danish North Sea sector. |
| Q15 DAK petro | `q15_15_9_19/q15_dak_petro.las` | REAL LAS | Companion petrophysics product |
| Volve 15/9-19 validation | `../geox_las/CHATGPT_VALIDATION_VOLVE_15_9_19.las` | REAL LAS | Validation suite |

## Not on this host

| Dataset | Status |
|---------|--------|
| **Petronas proprietary LAS / SEG-Y / checkshot** | **ABSENT** — no licensed Petronas borehole/seismic files found under `/root` |
| Malay Basin field checkshot/VSP tables | ABSENT as digital tables (docs only under `docs/petronas/`) |
| Mini SEG-Y cubes for Malay prospects | ABSENT |

## Honest rule (F2)

- Do **not** claim Petronas well-tie calibration until real Petronas LAS + checkshot + seismic extract are ingested.
- Use Q15/Volve for **real-LAS** well-tie physics tests (GEOX-001 path).
- Synthetic fixtures remain under `tests/fixtures/geox_001/` for regression PROCEED/HOLD/KILL cases only.

## GEOX-001 wiring

```bash
# Synthetic regression (default demo)
PYTHONPATH=src python -m geox_core.benchmarks.geox_001_well_seismic_truth --scenario mistie_hold

# Real LAS path (Q15) — checkshot/horizon still scenario-derived until field tables arrive
PYTHONPATH=src python -c "
from geox_core.benchmarks.geox_001_well_seismic_truth import run_geox_001_real_las
print(run_geox_001_real_las()['killer_output']['verdict'])
"
```
