# Orchestration & Void

Orchestration coordinates multiple agents and systems. The void—where data is missing, contested, or denied—requires special handling.

## Overview

The Orchestration domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `agent_coordination` | Multi-agent task distribution | machine, void |
| `void_detect` | Characterize data denial | void |
| `edge_handle` | Handle boundary conditions | machine, void |
| `fallback_orchestrate` | Degraded-mode operations | machine, void |

## Agent Coordination

Multi-agent systems distribute tasks:
- **Decomposition**: Split strategic → tactical → operational
- **Assignment**: Match tasks to agent capabilities
- **Synchronization**: Share world model state
- **Escalation**: Route to higher authority

### Coordination Patterns

- **Centralized**: Single controller
- **Hierarchical**: Regional controllers
- **Federated**: Peer-to-peer negotiation
- **Market-based**: Auction mechanisms

## Void Detection

The void is not absence—it's information:
- **No-sensor**: Areas without coverage
- **Contested**: Enemy jamming, spoofing
- **Blackout**: Communication loss
- **Unknown**: Unexplored or forgotten

### Void Characterization

- **Type**: Sensor void, comm void, data void
- **Duration**: Temporary or permanent
- **Extent**: Spatial coverage
- **Recovery**: Time to restore

## Edge Case Handling

Edge cases occur at boundaries:
- **Spatial**: Administrative borders
- **Temporal**: Regime transitions
- **Modal**: Sensor mode changes
- **Semantic**: Category transitions

### Handling Strategies

- **Graceful degradation**: Reduce capability
- **Fallback stacking**: Alternative approaches
- **Escalation**: Human review for novel cases
- **Learning**: Capture for future improvement

## Fallback Orchestration

When primary systems fail:
- **Failure modes**: Identified and characterized
- **Available capabilities**: Degraded but functional
- **Mission priority**: What must succeed
- **Risk assessment**: Is fallback safe?

### Fallback Hierarchy

1. Full capability (nominal)
2. Reduced capability (degraded)
3. Minimal capability (emergency)
4. Survival mode (protective only)

## Constitutional Constraints

Orchestration must satisfy:
- **F1 Amanah**: Fallback modes preserve safety
- **F13 Sovereign**: Human authority preserved in degradation
- **F9 Anti-Hantu**: Void is explicit, never hidden

## See Also

- [Sensing & Signals](sensing.md) — Signal acquisition
- [Governance & Policy](governance.md) — Constitutional gate
- [Agent Coordination](../../apps/site/skills/agent_coordination.html) — Skill detail
