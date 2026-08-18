---
id: geox-contradiction-engine
name: geox-contradiction-engine
version: "1.1.0-2026.08.17"
description: Multi-hypothesis contradiction scanner. Flags conflicting evidence across7 contradiction types. Every interpretation must list alternatives.
owner: GEOX
risk_tier: high
floor_scope: [F2, F4, F7, F9, F11]
autonomy_tier: T1
trigger_phrases:
  - "contradiction"
  - "conflicting evidence"
  - "alternative hypothesis"
  - "geox-contradiction-engine"
dependencies:
  mcp_servers:
    - geox
  skills:
    - geox-claim-grammar
    - geox-epistemic-ladder
---

# GEOX Contradiction Engine Skill

Conflicting evidence must be surfaced, not suppressed. This skill defines the contradiction detection patterns for the GEOX organ.

## Primary Tools

| Tool | Use for |
|------|---------|
| `geox_contradiction_scan` | Scan claims for contradictions (13-type ontology). Classifies severity FATAL/HIGH/MEDIUM/LOW |
| `geox_falsify` | Popperian falsification — Kill Matrix K001-K007 |
| `geox_claim` | Create/validate/challenge geological claims |
| `geox_evidence_synthesize` | Mode-driven synthesis: discover, synthesize, abduct, contradict |

## Core Pattern

Every interpretation must list alternatives. Every alternative must list what evidence would support it vs the primary claim.

```yaml
claim: "Reservoir is gas-bearing at 2142-2168 m TVDSS"
alternatives:
  - "Low-density shale (GR low but density also low)"
  - "Coal (high resistivity but very low density)"
  - "Tuning artifact (amplitude high but below tuning thickness)"
```

## Contradiction Types

| Type | Example | Detection |
|------|---------|-----------|
| **Evidence gap** | High Sw but seismic DHI present | Mismatch between log and seismic evidence |
| **Physics violation** | Porosity > 0.45 without explanation | Exceeds CANON-9 bounds |
| **Single-well certainty** | Regional interpretation from 1 well | <3 wells for basin-scale claim |
| **Uncalibrated pressure** | Fluid gradient without DST/MDT | Pressure claim missing calibration ref |
| **Temporal drift** | Claim based on 2020 data, 2025 well contradicts | Newer evidence supersedes older |
| **Modal contradiction** | Seismic says flat spot, logs say water | Cross-modality evidence conflict |
| **Epistemic collapse** | "Bright spot = hydrocarbon" | Skips AVO, rock physics, fluid analysis |

## Required Fields for Every Claim

Beyond standard fields, every claim should carry:

```yaml
contradiction_scan:
  status: PASS | WARN | FAIL
  contradictions_found: []
  alternatives_evaluated: 2
  missing_evidence: ["DST in zone X"]
```

## Enforcement

- Every INTERPRETATION or higher claim must list at least 1 alternative
- Every claim must pass contradiction scan before reaching SEAL
- Contradictions are not failures — they are intellectual honesty
- A claim with no alternatives is a weak claim
- FATAL contradictions → 888_HOLD (never autonomous seal)

## Tool Usage

```python
# Scan a claim for contradictions
result = await geox_contradiction_scan(
    claim_id="claim-001",
)

# Challenge a claim with alternative
result = await geox_claim(
    claim_id="claim-001",
    challenge_text="No DST evidence for gas interpretation",
    alternative_claim_text="Interval may be low-density shale, not gas sand",
    alternative_evidence_ids=["las:A1_GR", "las:A1_RHOB"],
)

# Falsify via Kill Matrix
result = await geox_falsify(
    claim_text="Reservoir is gas-bearing at 2142-2168 m",
)
```

## Key References

- `/root/GEOX/GENESIS/015_FALSIFICATION_ENGINE.md` — Kill Matrix K001-K007
- `/root/GEOX/GENESIS/017_EARTHOS_CONSTITUTION.md` — Cross-Modal Fidelity Theorem

**DITEMPA BUKAN DIBERI — Built, not assumed.**
