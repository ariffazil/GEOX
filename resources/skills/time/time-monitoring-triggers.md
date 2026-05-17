---
id: geox.time.monitoring-triggers
title: Monitoring Triggers
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
substrates: [machine-fixed, machine-mobile, human]
scales: [site, corridor, district, region]
horizons: [immediate, short]
inputs: [watchlist, threshold-settings, current-observations]
outputs: [trigger-alerts, replan-recommendations, attention-flags]
depends_on: [geox.time.regime-shift, geox.sensing.observation-qc]
legal_domain: public
status: draft
runtime:
  cache_ttl_sec: 300
  read_only: false
---

# time-monitoring-triggers

Define what to watch and when to replan.

## Contract

**Inputs:** watchlist, threshold-settings, current-observations
**Outputs:** trigger-alerts, replan-recommendations, attention-flags

## Behavior

Evaluate current observations against watchlist thresholds. Generate trigger alerts and replan recommendations when thresholds are breached.

## Edges

← time-regime-shift
← sense-observation-qc
- → route-viability
- → anomaly-detection
