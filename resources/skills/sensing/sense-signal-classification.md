---
id: geox.sensing.signal-classification
title: Signal Classification
domain: sensing
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: low
  human_confirmation: false
substrates: [machine-fixed, machine-mobile, orbital, environment-field]
scales: [site, corridor, district]
horizons: [immediate]
inputs: [signal-data, frequency-data, sensor-metadata]
outputs: [signal-type, source-class, confidence-band]
depends_on: [geox.sensing.observation-intake]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 600
  read_only: true
---

# sense-signal-classification

Classify source type: optical, RF, GNSS, seismic, thermal, acoustic, symbolic.

## Contract

**Inputs:** signal-data, frequency-data, sensor-metadata
**Outputs:** signal-type, source-class, confidence-band

## Behavior

Given a signal observation, determine the physical modality and emitter class to route downstream processing correctly.

## Edges

← sense-observation-intake
- → sense-observation-qc
