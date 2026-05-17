---
id: geox.subsurface.prospect-risk
title: Prospect Risk
domain: subsurface
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: critical
  human_confirmation: true
substrates: [machine-fixed, geological-assessment]
scales: [prospect, lead, play]
horizons: [medium, long]
inputs: [reservoir-assessment, trap-assessment, seal-assessment, charge-assessment, retention-assessment]
outputs: [pos, component-probabilities, coupling-flags, posterior-breadth, hold-flag]
depends_on:
  - geox.subsurface.reservoir-dynamics
  - geox.subsurface.basin-charge
legal_domain: proprietary
status: active
runtime:
  cache_ttl_sec: 3600
  read_only: true
independence_model: explicit
pos_formula: "P(reservoir) × P(trap) × P(seal) × P(charge) × P(retention)"
---

# subsurface.prospect-risk

Governs PoS (Probability of Success) computation.

## Contract

**Inputs:** reservoir-assessment, trap-assessment, seal-assessment, charge-assessment, retention-assessment
**Outputs:** pos, component-probabilities, coupling-flags, posterior-breadth, hold-flag

## PoS Formula

```
PoS = P(reservoir) × P(trap) × P(seal) × P(charge) × P(retention)
```

## Independence Enforcement

Each component MUST be assessed independently.

**Coupling Detection:** If geological coupling is detected between any two components (e.g., same depositional system controls both seal and reservoir):

```json
{
  "coupling_detected": true,
  "components": ["seal", "reservoir"],
  "pos_correction": "REQUIRED"
}
```

**Coupled PoS without correction → REJECT output.**

## Output Schema

```json
{
  "pos": float,
  "components": {
    "reservoir": {"p": float, "confidence": "HIGH|MEDIUM|LOW"},
    "trap": {"p": float, "confidence": "HIGH|MEDIUM|LOW"},
    "seal": {"p": float, "confidence": "HIGH|MEDIUM|LOW"},
    "charge": {"p": float, "confidence": "HIGH|MEDIUM|LOW"},
    "retention": {"p": float, "confidence": "HIGH|MEDIUM|LOW"}
  },
  "coupling_flags": [],
  "posterior_breadth": float,
  "hold": bool
}
```

## Posterior Breadth

- `posterior_breadth` = ratio of P90/P10 across components
- If breadth > 5.0 → `hold: true`

## Edges

← reservoir-dynamics
← basin-charge
→ posterior-integrity
→ wealth-capital-allocation