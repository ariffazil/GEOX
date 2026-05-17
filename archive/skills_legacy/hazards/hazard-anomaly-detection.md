---
id: geox.hazards.anomaly-detection
title: Anomaly Detection
domain: hazards
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: medium
  human_confirmation: false
substrates: [machine-fixed, machine-mobile, orbital, environment-field, void]
scales: [site, corridor, district, region]
horizons: [immediate]
inputs: [baseline-data, sensor-streams, movement-data, environmental-readings]
outputs: [anomaly-alerts, deviation-scores, pattern-match]
depends_on: [geox.sensing.observation-qc, geox.time.regime-shift]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 300
  read_only: true
---

# hazard-anomaly-detection

Detect out-of-family signals across movement, environment, or infrastructure state.

## Contract

**Inputs:** baseline-data, sensor-streams, movement-data, environmental-readings
**Outputs:** anomaly-alerts, deviation-scores, pattern-match

## Behavior

Monitor all input streams against learned baselines. Detect statistical anomalies and pattern deviations with confidence scoring.

## Edges

← sense-observation-qc
← time-regime-shift
- → seismic-and-ground-shift
- → multi-risk-escalation
