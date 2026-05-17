---
id: geox.subsurface.reservoir-dynamics
title: Reservoir Dynamics
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
substrates: [machine-fixed, fluid-sampling, pressure-data]
scales: [well, reservoir, field]
horizons: [medium, long]
inputs: [sw, por, vsh, pressure-data, pvt-data]
outputs: [net-pay, stoiip, giip, flow-capacity, posterior-bands]
depends_on: [geox.subsurface.formation-evaluation]
legal_domain: proprietary
status: active
runtime:
  cache_ttl_sec: 7200
  read_only: true
upstream_dependency: geox.subsurface.formation-evaluation
net_pay_criteria:
  sw_max: 0.4
  por_min: 0.10
  vsh_max: 0.6
---

# subsurface.reservoir-dynamics

Governs fluid mechanics, PVT, material balance reasoning.

## Contract

**Inputs:** sw, por, vsh (from formation-evaluation), pressure-data, pvt-data
**Outputs:** net-pay, stoiip, giip, flow-capacity, posterior-bands (p10/p50/p90)

## Upstream Dependency Enforcement

- **Sw, POR, Vsh MUST come from `geox.subsurface.formation-evaluation`.**
- Validate upstream source before processing.
- If upstream values missing → emit `HOLD: "AWAITING_FORMATION_EVALUATION"`

## Net Pay Flagging Rules

Net pay requires **ALL THREE** conditions simultaneously:

| Parameter | Threshold | Condition |
|-----------|-----------|-----------|
| Sw | < 0.4 | AND |
| POR | > 0.10 | AND |
| Vsh | < 0.6 | ALL THREE |

Single-condition pass is insufficient.

## Output Requirements

**Single-value STOIIP/GIIP outputs are FORBIDDEN.**
Output MUST be probabilistic: `{p10, p50, p90, unit}`.

## Edges

← formation-evaluation
→ basin-charge
→ prospect-risk