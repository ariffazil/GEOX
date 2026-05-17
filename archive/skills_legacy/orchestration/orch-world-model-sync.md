---
id: geox.orchestration.world-model-sync
title: World Model Sync
domain: orchestration
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: high
  human_confirmation: false
substrates: [machine-fixed, machine-mobile, infrastructure, orbital]
scales: [site, corridor, district, region, nation]
horizons: [immediate, short]
inputs: [agent-states, sensor-updates, map-versions, mission-state]
outputs: [synced-world-model, conflict-report, consistency-score]
depends_on: [geox.sensing.observation-intake, geox.time.monitoring-triggers]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 60
  read_only: false
---

# orch-world-model-sync

Maintain shared state across agents, maps, sensors, and mission layers.

## Contract

**Inputs:** agent-states, sensor-updates, map-versions, mission-state
**Outputs:** synced-world-model, conflict-report, consistency-score

## Behavior

Synchronize world model state across all agent nodes. Detect conflicts, compute consistency scores, and propagate updates.

## Edges

← sense-observation-intake
← time-monitoring-triggers
- → multi-agent-decomposition
- → void-and-data-denial
