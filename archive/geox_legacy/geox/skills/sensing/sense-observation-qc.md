---
id: geox.sensing.observation-qc
title: Observation QC
domain: sensing
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: medium
  human_confirmation: false
substrates: [human, machine-fixed, machine-mobile, orbital, environment-field, void]
scales: [site, corridor, district, region]
horizons: [immediate, short]
inputs: [normalized-observations, calibration-data, trust-indicators]
outputs: [qc-scores, freshness-rating, contamination-flags]
depends_on: [geox.sensing.observation-intake]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 300
  read_only: true
---

# sense-observation-qc

Score freshness, calibration, trust, resolution, and likely contamination.

## Contract

**Inputs:** normalized-observations, calibration-data, trust-indicators
**Outputs:** qc-scores, freshness-rating, contamination-flags

## Behavior

Evaluate each normalized observation for quality. Flag stale readings, calibration drift, low trust, and possible contamination or spoofing.

## Edges

← sense-observation-intake
← sense-signal-classification
- → time-regime-shift
