---
id: geox.subsurface.posterior-integrity
title: Posterior Integrity
domain: subsurface
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: critical
  human_confirmation: false
substrates: [machine-fixed]
scales: [prospect, lead, play, basin]
horizons: [short, medium, long]
inputs: [all-subsurface-outputs, well-density, model-lineage]
outputs: [integrity-score, posterior-breadth, evidence-density, model-lineage-hash, recommendation]
depends_on:
  - geox.subsurface.formation-evaluation
  - geox.subsurface.seismic-interpretation
  - geox.subsurface.reservoir-dynamics
  - geox.subsurface.basin-charge
  - geox.subsurface.prospect-risk
legal_domain: proprietary
status: active
runtime:
  cache_ttl_sec: 1800
  read_only: true
integrity_thresholds:
  auto_hold: 0.3
  warning: 0.6
  pass: 0.6
analogy: "AlphaFold pLDDT equivalent for GEOX"
---

# subsurface.posterior-integrity

Governs epistemic integrity scoring for all subsurface outputs. **This is the AlphaFold pLDDT equivalent for GEOX.**

## Contract

**Inputs:** all-subsurface-outputs, well-density (wells/100km²), model-lineage
**Outputs:** integrity-score, posterior-breadth, evidence-density, model-lineage-hash, recommendation

## Integrity Score Computation

For every horizon, volumetric, and seal probability emitted:

| Metric | Formula | Purpose |
|--------|---------|---------|
| `posterior_breadth` | P90 / P10 | Measures uncertainty spread |
| `evidence_density` | wells / 100km² in study area | Data confidence |
| `model_lineage_hash` | Hash of interpretation run ID | Correlation tracking |

**Integrity Score Formula:**

```
integrity_score = f(evidence_density, posterior_breadth, model_lineage_diversity)
```

## Threshold Actions

| Integrity Score | Classification | Action |
|-----------------|---------------|--------|
| < 0.3 | **AUTO_HOLD** | Do NOT pass to WEALTH |
| 0.3 – 0.6 | **PLAUSIBLE** | Pass with warning |
| > 0.6 | **CLAIM** | Pass to WEALTH normally |

## Requirement

**This score MUST be attached to every output that flows downstream to WEALTH.**

## Model Lineage Hash

`model_lineage_hash` identifies which interpretation run produced the output. This enables:
- Tracking which prospects share the same AI interpretation
- Detecting correlated epistemic risk in portfolio
- Preventing one flawed model from infecting 10 wells

## Refusal Logic

- `integrity_score < 0.3` → `recommendation: "HOLD"`, do not pass to WEALTH
- Any output with single-value volumetrics (no p10/p50/p90) → `HOLD`

## Edges

← all subsurface skills
→ wealth-capital-allocation (ONLY if integrity_score >= 0.3)