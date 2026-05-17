---
id: geox.subsurface.basin-charge
title: Basin Charge
domain: subsurface
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: critical
  human_confirmation: true
substrates: [machine-fixed, geochemical, thermal-history]
scales: [basin, play, prospect]
horizons: [long]
inputs: [source-rock-data, thermal-maturity, migration-pathways, trap-age]
outputs: [charge-timing, maturity-window, migration-adequacy, hold-flag]
depends_on: [geox.subsurface.reservoir-dynamics]
legal_domain: proprietary
status: active
runtime:
  cache_ttl_sec: 86400
  read_only: true
timing_validation: geox_time4d_verify_timing
maturity_windows:
  oil: [0.6, 1.3]
  gas: 1.3
---

# subsurface.basin-charge

Governs thermal maturity, source rock evaluation, hydrocarbon migration pathway reasoning.

## Contract

**Inputs:** source-rock-data, thermal-maturity, migration-pathways, trap-age
**Outputs:** charge-timing, maturity-window, migration-adequacy, hold-flag

## Charge Timing Validation

- **CRITICAL:** Charge timing MUST be verified against trap formation age.
- Delegates to `geox_time4d_verify_timing` tool.
- If `charge_ma > trap_ma` → `CHARGE_BEFORE_TRAP_VIOLATION` → `{"status": "TIMING_VIOLATION", "hold": true}`

## Maturity Windows

| Phase | Ro Range | Action |
|-------|----------|--------|
| Oil | 0.6% – 1.3% | Normal |
| Gas | > 1.3% | Normal |
| Under-mature | < 0.6% | Flag warning |
| Over-mature | > 3.0% | Flag warning |

## Refusal Logic

- If charge_ma > trap_ma → `TIMING_VIOLATION`, `hold: true`
- If source rock maturity outside window → `MATURITY_WARNING`

## Edges

← reservoir-dynamics
→ prospect-risk