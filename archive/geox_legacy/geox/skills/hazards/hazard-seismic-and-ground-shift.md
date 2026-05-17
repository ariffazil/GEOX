---
id: geox.hazards.seismic-and-ground-shift
title: Seismic and Ground Shift
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
substrates: [environment-field, orbital, infrastructure]
scales: [site, corridor, district]
horizons: [immediate, short]
inputs: [seismic-data, gps-deformation, ground-level, structural-monitoring]
outputs: [ground-motion, subsidence-rate, uplift-report, structural-implications]
depends_on: [geox.sensing.signal-classification, geox.geodesy.position-fix-fusion]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 300
  read_only: true
---

# hazard-seismic-and-ground-shift

Ground motion, subsidence, uplift, seabed disturbance, and structural implication.

## Contract

**Inputs:** seismic-data, gps-deformation, ground-level, structural-monitoring
**Outputs:** ground-motion, subsidence-rate, uplift-report, structural-implications

## Behavior

Process seismic and geodetic data to assess ground motion and deformation. Estimate structural implications and alert thresholds.

## Edges

← sense-signal-classification
← geo-position-fix-fusion
- → multi-risk-escalation
