---
id: geox.time.forecast-branching
title: Forecast Branching
domain: time
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: true
  mcp_tool: true
risk:
  class: medium
  human_confirmation: false
substrates: [machine-fixed, machine-mobile]
scales: [site, corridor, district, region]
horizons: [short, medium, long]
inputs: [base-forecast, assumption-sets, scenario-seeds]
outputs: [scenario-tree, branch-probabilities, key-uncertainties]
depends_on: [geox.time.regime-shift, geox.atmosphere.weather-state]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 7200
  read_only: false
---

# time-forecast-branching

Branch future states into scenario trees with assumptions.

## Contract

**Inputs:** base-forecast, assumption-sets, scenario-seeds
**Outputs:** scenario-tree, branch-probabilities, key-uncertainties

## Behavior

Generate probabilistic scenario trees from base forecasts. Identify key uncertainties and compute branch probabilities.

## Edges

← time-regime-shift
← atmo-weather-state
- → monitoring-triggers
- → multi-agent-decomposition
