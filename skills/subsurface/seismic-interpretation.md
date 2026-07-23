---
id: geox.subsurface.seismic-interpretation
title: Seismic Interpretation
domain: subsurface
version: 0.1.0
surface:
  site: true
  mcp_resource: true
  mcp_prompt: false
  mcp_tool: true
risk:
  class: high
  human_confirmation: false
substrates: [machine-fixed, seismic-acquisition]
scales: [line, volume, field, basin]
horizons: [medium, long]
inputs: [seismic-volumes, horizon-interpretations, amplitude-attributes]
outputs: [depth-uncertainty, amplitude-anomaly, dhi-flag, posterior-bands]
depends_on: []
legal_domain: proprietary
status: active
runtime:
  cache_ttl_sec: 86400
  read_only: true
key_principle: "Seismic is inverted physics — not photography. The mapping seismic → geology is many-to-one (non-injective)."
---

# subsurface.seismic-interpretation

Governs reasoning over seismic volumes, horizon picking, amplitude attribute analysis.

## Contract

**Inputs:** seismic-volumes, horizon-interpretations, amplitude-attributes
**Outputs:** depth-uncertainty, amplitude-anomaly, dhi-flag, posterior-bands (p10/p50/p90)

## Key Principle

**Seismic is inverted physics — not photography.** The mapping seismic → geology is many-to-one (non-injective). Never collapse the posterior to a single horizon. Always carry at least P10/P50/P90 depth uncertainty.

## Forge SOT (2026-07-23)

**Canonical doctrine:** `docs/SEISMIC_SECTION_INTERPRET_ZEN.md`  
Loop: measure → propose (INT/SPEC) → K*/G* gates → falsify → receipt → arifOS SEAL?  
Live modes: `structure_validate`, `interpret_section`, `segy_slice` on `geox_seismic_interpret`.  
Gates: `docs/SEISMIC_FAULT_PHYSICS_GATES_K_SPEC.md` · `docs/SEISMIC_STRUCTURAL_VALIDATION_GATES_G0_G10.md`.  
Vision/ML proposes only — never authority. image_only = INT_SEISMIC forever.

## Constraints

1. **Never collapse posterior to single horizon.** Always carry P10/P50/P90 depth uncertainty.
2. **Acquisition footprint bias** must be flagged if detected.
3. **Amplitude anomalies** require corroborating rock physics evidence before emitting DHI (direct hydrocarbon indicator).

## Refusal Logic

- If only seismic evidence exists with no well control → emit `confidence_band: "VERY_BROAD"`, `recommendation: "HOLD — no well calibration"`
- DHI claims require rock physics corroboration; otherwise emit `HOLD`

## Edges

- → formation-evaluation
- → reservoir-dynamics
- → prospect-risk