---
id: geox.subsurface.formation-evaluation
title: Formation Evaluation
domain: subsurface
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: high
  human_confirmation: false
substrates: [machine-fixed, wireline, while-drilling]
scales: [sample, log, bed, field]
horizons: [short, medium, long]
inputs: [wireline-logs, core-data, seismic-velocity]
outputs: [vsh, por, sw, pay-flag, posterior-bands]
depends_on: []
legal_domain: proprietary
status: active
runtime:
  cache_ttl_sec: 3600
  read_only: true
physics_constraints:
  porosity: [0.02, 0.45]
  sw: [0.0, 1.0]
  vsh: [0.0, 1.0]
  posterior_max_ratio: 5.0
---

# subsurface.formation-evaluation

Petrophysical interpretation of well logs. Governs Vsh, POR, Sw computation via physics-grounded Archie / Indonesia / Simandoux models.

## Contract

**Inputs:** wireline-logs, core-data, seismic-velocity
**Outputs:** vsh, por, sw, pay-flag, posterior-bands (p10/p50/p90)

## Physics Constraints (MUST BE ENFORCED, NOT ADVISORY)

| Parameter | Min | Max | Violation Action |
|-----------|-----|-----|-----------------|
| Porosity  | 0.02 | 0.45 | REJECT → `{"status": "PHYSICS_VIOLATION", "hold": true}` |
| Sw        | 0.0  | 1.0  | REJECT → `{"status": "PHYSICS_VIOLATION", "hold": true}` |
| Vsh       | 0.0  | 1.0  | REJECT → `{"status": "PHYSICS_VIOLATION", "hold": true}` |

## Uncertainty Requirements

All outputs MUST carry p10/p50/p90 bands. Single-value outputs are FORBIDDEN.

## Refusal Logic

- If posterior P90/P10 ratio > 5.0 → emit `HOLD` instead of single value
- If any physics bound breached → emit `PHYSICS_VIOLATION` with `hold: true`

## Edges

- → reservoir-dynamics
- → prospect-risk