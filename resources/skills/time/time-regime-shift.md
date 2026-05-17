---
id: geox.time.regime-shift
title: Regime Shift
domain: time
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: medium
  human_confirmation: false
substrates: [machine-fixed, environment-field, void]
scales: [site, corridor, district, region]
horizons: [immediate, short, medium]
inputs: [historical-baseline, current-observations, change-indicators]
outputs: [regime-classification, shift-confidence, stability-index]
depends_on: [geox.sensing.observation-qc]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 1800
  read_only: true
---

# time-regime-shift

Distinguish stable baseline, drift, sudden break, and new regime.

## Contract

**Inputs:** historical-baseline, current-observations, change-indicators
**Outputs:** regime-classification, shift-confidence, stability-index

## Behavior

Compare current observations against historical baselines to detect regime shifts. Classify as stable, drifting, broken, or new regime.

## Edges

← sense-observation-qc
- → forecast-branching
- → monitoring-triggers
- → anomaly-detection
