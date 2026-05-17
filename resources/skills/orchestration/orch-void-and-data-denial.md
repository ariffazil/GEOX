---
id: geox.orchestration.void-and-data-denial
title: Void and Data Denial
domain: orchestration
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: true
  mcp_tool: false
risk:
  class: high
  human_confirmation: true
substrates: [void, machine-fixed, machine-mobile, environment-field]
scales: [site, corridor, district, region]
horizons: [immediate, short, medium]
inputs: [sensor-coverage, contested-areas, blackout-zones, spoofing-indicators]
outputs: [void-map, confidence-gaps, denial-regions]
depends_on: [geox.sensing.observation-qc, geox.orchestration.world-model-sync]
legal_domain: international
status: draft
runtime:
  cache_ttl_sec: 600
  read_only: true
---

# orch-void-and-data-denial

Represent unknown space explicitly: no-sensor, contested data, blackout, spoofing, or silence.

## Contract

**Inputs:** sensor-coverage, contested-areas, blackout-zones, spoofing-indicators
**Outputs:** void-map, confidence-gaps, denial-regions

## Behavior

Map regions of sensor denial, contested data, and spoofing. Maintain explicit void representations in the world model.

## Edges

← sense-observation-qc
← world-model-sync
