---
id: geox.orchestration.multi-agent-decomposition
title: Multi-Agent Decomposition
domain: orchestration
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: true
  mcp_tool: false
risk:
  class: medium
  human_confirmation: false
substrates: [human, machine-fixed, machine-mobile]
scales: [corridor, district, region]
horizons: [short, medium]
inputs: [strategic-task, agent-capabilities, current-load]
outputs: [task-decomposition, agent-assignments, coordination-plan]
depends_on: [geox.orchestration.world-model-sync, geox.time.forecast-branching]
legal_domain: civil
status: draft
runtime:
  cache_ttl_sec: 1800
  read_only: false
---

# orch-multi-agent-decomposition

Split strategic, tactical, and operational tasks across specialist agents.

## Contract

**Inputs:** strategic-task, agent-capabilities, current-load
**Outputs:** task-decomposition, agent-assignments, coordination-plan

## Behavior

Decompose complex tasks into sub-tasks assignable to specialist agents. Generate coordination plans for inter-agent communication.

## Edges

← world-model-sync
← forecast-branching
