---
id: geox.water.floodplain-and-flow
title: Floodplain and Flow
domain: water
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: high
  human_confirmation: true
substrates: [human, machine-fixed, machine-mobile, environment-field]
scales: [site, corridor, district]
horizons: [immediate, short]
inputs: [water-levels, terrain-data, infrastructure-data, rainfall-nowcast]
outputs: [flood-spread, bottleneck-report, overtopping-risk, inundation-sequence]
depends_on: [geox.water.hydrology-basics, geox.terrain.drainage-structure]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 900
  read_only: false
---

# water-floodplain-and-flow

Flood spread plausibility, bottlenecks, overtopping, backflow, and inundation sequence.

## Contract

**Inputs:** water-levels, terrain-data, infrastructure-data, rainfall-nowcast
**Outputs:** flood-spread, bottleneck-report, overtopping-risk, inundation-sequence

## Behavior

Model flood propagation across terrain and infrastructure. Identify bottlenecks, overtopping points, and generate inundation sequences.

## Edges

← water-hydrology-basics
← terrain-drainage-structure
- → hazard-multi-risk-escalation
