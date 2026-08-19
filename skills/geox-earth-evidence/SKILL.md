---
id: geox-earth-evidence
name: geox-earth-evidence
version: "1.1.0-2026.08.17"
description: GEOX evidence discipline — artifact refs, uncertainty bands, GEOX→WEALTH handoff protocol. Earth intelligence, not Earth certainty.
owner: GEOX
risk_tier: high
floor_scope: [F1, F2, F3, F4, F7, F9, F11]
autonomy_tier: T1
trigger_phrases:
  - "geox evidence"
  - "subsurface evidence"
  - "seismic evidence"
  - "well log evidence"
  - "petrophysics evidence"
  - "basin evidence"
  - "geox-earth-evidence"
dependencies:
  mcp_servers:
    - geox
    - arifos
    - wealth
  skills:
    - geox-claim-grammar
    - geox-epistemic-ladder
---

# geox-earth-evidence — EARTH EVIDENCE SKILL

> **DITEMPA BUKAN DIBERI.** Earth intelligence, not Earth certainty.
> **Skill type:** Domain cognition — geological reasoning without policy claims.

## Primary Tools

| Tool | Use for |
|------|---------|
| `geox_basin` | Basin profile, stratigraphy, scene |
| `geox_well_ingest` | Load LAS, SEG-Y, DST, deviation, tops |
| `geox_well_qc` | QC depth, curves, completeness |
| `geox_petrophysics` | Vsh, porosity, Sw, perm, net pay, LEM |
| `geox_seismic_compute` | Synthetic, well tie, time-depth anchor |
| `geox_sequence` | Sequence stratigraphy, correlation |
| `geox_prospect` | Volumetrics, POS, EVOI, risk assessment |
| `geox_claim` | Create/validate/challenge geological claims |
| `geox_geomechanics` | K, G, E, ν, AI from Physics9State |
| `geox_evidence` | Discover, synthesize, abduct, contradict |
| `geox_evidence_synthesize` | Mode-driven evidence synthesis |
| `geox_workspace` | Set basin/play/well once; every tool inherits |

## Evidence Discipline

### Artifact references, not raw paths

```
✅ GOOD: artifact_ref = "geox://wells/north_malacca_cdp_2024"
❌ BAD:  artifact_ref = "/data/seismic/stack_mukah_2023.sgy"
```

### Uncertainty language (mandatory)

| Confidence | Language |
|-----------|---------|
| 0.85–0.90 | "High confidence" — multiple independent lines of evidence |
| 0.70–0.84 | "Moderate confidence" — single dataset, some analog support |
| 0.50–0.69 | "Low confidence" — regional analog, limited data |
| < 0.50 | "Hypothesis" — needs test |

## Geological Claim Grammar

Every GEOX claim must carry:
```
evidence_for: [...]
evidence_against: [...]
missing_tests: [...]
ACRisk: HIGH | MEDIUM | LOW
```

No single-hypothesis geology without contradiction scan.

## GEOX → WEALTH Handoff

```
1. geox_prospect() → returns G_factor, risk, volume estimates
2. capital_primitive() → uses GEOX inputs for EVOI
3. wealth_judge_handoff() → submit to arifOS
```

Never submit capital decisions to WEALTH without GEOX evidence first.

## Anti-Patterns

- ❌ Using raw file paths as artifact references
- ❌ Claiming > 0.90 confidence on single-well interpretation
- ❌ Bypassing contradiction scan
- ❌ Submitting to WEALTH without GEOX evidence first
- ❌ Making policy claims (GEOX computes, arifOS judges)

## Pre-Flight Check

```bash
curl -sf http://localhost:8081/health && echo "✅ GEOX" || echo "❌ GEOX DOWN"
```

If GEOX is DOWN → do not call geox_* tools. Return GEOX_UNAVAILABLE.

**DITEMPA BUKAN DIBERI — Earth evidence, not Earth authority.**
