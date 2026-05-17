---
id: geox.sensing.observation-intake
title: Observation Intake
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
substrates: [human, machine-fixed, machine-mobile, orbital, environment-field]
scales: [site, corridor, district, region]
horizons: [immediate, short]
inputs: [raw-reports, sensor-streams, satellite-feed, api-data, field-notes]
outputs: [normalized-observations, schema-compliant-records]
depends_on: []
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 300
  read_only: false
---

# sense-observation-intake

Normalize reports from human, sensor, satellite, API, log, and field notes into one observation schema.

## Contract

**Inputs:** raw-reports, sensor-streams, satellite-feed, api-data, field-notes
**Outputs:** normalized-observations, schema-compliant-records

## Behavior

Ingest heterogeneous observation sources and emit canonical records tagged with provenance, timestamp, coordinate reference, and confidence indicators.

## Edges

- → sense-signal-classification
- → sense-observation-qc
