---
id: geox.hazards.multi-risk-escalation
title: Multi-Risk Escalation
domain: hazards
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: high
  human_confirmation: true
substrates: [human, machine-fixed, environment-field]
scales: [site, corridor, district, region]
horizons: [immediate, short]
inputs: [rainfall-data, terrain-data, load-data, crowding-data, infrastructure-weakness]
outputs: [escalation-bands, risk-composite, priority-areas]
depends_on: [geox.hazards.anomaly-detection, geox.water.floodplain-and-flow, geox.infrastructure.capacity-and-failure]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 600
  read_only: false
---

# hazard-multi-risk-escalation

Combine rain, terrain, load, crowding, and infrastructure weakness into escalation bands.

## Contract

**Inputs:** rainfall-data, terrain-data, load-data, crowding-data, infrastructure-weakness
**Outputs:** escalation-bands, risk-composite, priority-areas

## Behavior

Combine multiple hazard drivers into unified escalation bands. Rank priority areas for response and compute composite risk scores.

## Edges

← hazard-anomaly-detection
← water-floodplain-and-flow
← infra-capacity-and-failure
- → human-in-loop-888
