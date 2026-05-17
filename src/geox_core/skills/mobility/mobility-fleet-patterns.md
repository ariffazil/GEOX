---
id: geox.mobility.fleet-patterns
title: Fleet Patterns
domain: mobility
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: low
  human_confirmation: false
substrates: [machine-mobile, orbital, infrastructure]
scales: [district, region, maritime]
horizons: [short, medium]
inputs: [position-reports, ais-data, vehicle-tracking, schedule-data]
outputs: [movement-signatures, pattern-clusters, anomaly-alerts]
depends_on: [geox.geodesy.position-fix-fusion, geox.mobility.route-viability]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 1800
  read_only: true
---

# mobility-fleet-patterns

Repeated movement signatures from vessels, vehicles, aircraft, or mixed fleets.

## Contract

**Inputs:** position-reports, ais-data, vehicle-tracking, schedule-data
**Outputs:** movement-signatures, pattern-clusters, anomaly-alerts

## Behavior

Detect and characterize repeated movement patterns in fleet data. Cluster similar routes and flag deviations for anomaly alerting.

## Edges

← geo-position-fix-fusion
← mobility-route-viability
