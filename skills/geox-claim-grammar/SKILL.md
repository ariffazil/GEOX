---
id: geox-claim-grammar
name: geox-claim-grammar
version: "1.2.0-2026.08.17"
description: Geological claim structure — evidence_for, evidence_against, missing_tests, Location First enforcement. Every geological claim follows this grammar.
owner: GEOX
risk_tier: high
floor_scope: [F1, F2, F3, F4, F7, F9, F11]
autonomy_tier: T1
trigger_phrases:
  - "geological claim"
  - "claim grammar"
  - "evidence for"
  - "evidence against"
  - "claim structure"
  - "geox-claim-grammar"
dependencies:
  mcp_servers:
    - geox
  skills:
    - geox-epistemic-ladder
    - geox-contradiction-engine
---

# GEOX Claim Grammar Skill

Every geological claim in GEOX follows a strict grammar. This prevents narrative drift, epistemic collapse, and single-hypothesis bias.

## Primary Tools

| Tool | Use for |
|------|---------|
| `geox_claim` | Create/validate/challenge/seal/attach geological claims |
| `geox_falsify` | Popperian falsification — Kill Matrix K001-K007 |
| `geox_contradiction_scan` | Scan claims for contradictions (13-type ontology) |
| `geox_evidence` | Evidence lifecycle: attach, discover, summarize, cross-reference |
| `geox_evidence_synthesize` | Mode-driven evidence synthesis: discover, synthesize, abduct, contradict |

## Claim Structure

Every geological statement must be expressible as:

```yaml
claim:
  text: "<specific, falsifiable statement>"
  rung: OBSERVED | DERIVED | INTERPRETED_LOCAL | PROCESS_HYPOTHESIS | EARTHMODEL | DECISIONSUPPORT
  evidence_for:
    - artifact_ref: <sha256 of source data>
      weight: 0.0-1.0
    - ...
  evidence_against:
    - artifact_ref: <sha256 of contradicting data>
      weight: 0.0-1.0
    - ...
  missing_tests:
    - "What data would prove this wrong?"
    - ...
  acrisk: 0.0-1.0
  alternatives:
    - description: "Mouth bar deposit"
      support: ["grain_size_trend", "bioturbation_index"]
    - description: "Distributary channel fill"
      support: ["scour_base", "fining_upward"]
```

## Location First — Positional Accuracy Enforcement

Every location-bearing claim MUST include:

```yaml
claim:
  coordinates:
    lat: <decimal_degrees_north>
    lon: <decimal_degrees_east>
    crs: "EPSG:4326"  # WGS84 — mandatory
  positional_accuracy_m: <number>  # REQUIRED. Radius of confidence in meters.
  source_tag: "VERIFIED_SURVEY" | "VERIFIED_LITERATURE" | "ESTIMATED" | "UNKNOWN"
  source_reference: "<DOI / URL / publication reference>"  # Required for VERIFIED_LITERATURE
```

### Source Tags and Their Meaning

| Tag | Meaning | Confidence Cap | Examples |
|-----|---------|---------------|----------|
| `VERIFIED_SURVEY` | Direct GPS measurement or survey-grade coordinates | 0.95 | Well location from deviation survey, seismic bin grid, field GPS |
| `VERIFIED_LITERATURE` | Published coordinate from peer-reviewed source | 0.85 | Morley 2023 Figure 1, published map |
| `ESTIMATED` | Inferred from map, description, or regional context | 0.60 | "~5 km from town", "from regional map at 1:250k scale" |
| `UNKNOWN` | No source — recalled, guessed, or unverified | 0.30 | "I think it's around here", "from memory" |

### Rule: No UNKNOWN Coordinates in Decision-Support Claims

- For DECISIONSUPPORT rung claims: ESTIMATED or better required. UNKNOWN = automatic HOLD.
- For INTERPRETED_LOCAL and above: ESTIMATED or better. UNKNOWN must carry explicit caveat.
- For any location claim: `source_tag` is MANDATORY.

## Claim Types

| Type | Template | Example |
|------|----------|---------|
| FACT | `<property>` = `<value>` at `<location>` | GR = 85 API at 2450.5m MD in Well A-1 |
| INTERPRETATION | `<observation>` suggests `<process>` | "The coarsening-upward GR motif suggests a mouth bar deposit" |
| SPECULATION | `<analogy>` implies `<possibility>` | "By analogy with Well B-2, the sand may extend 500m updip" |
| COMPARISON | `<A>` is similar to `<B>` in `<aspect>` | "This GR motif matches Well C-3's mouth bar pattern" |
| CHALLENGE | `<claim>` is questioned because `<evidence>` | "The 'mouth bar' interpretation is contradicted by density curve" |

## Multi-Hypothesis Mandate

**No single hypothesis may be presented without alternatives.**

For every INTERPRETED_LOCAL or higher claim, at minimum:
- The primary hypothesis
- At least one alternative hypothesis
- Evidence supporting each
- What test would distinguish them

## Forbidden Phrases

These trigger immediate RED-TEAM review:
- "proven reservoir" — A reservoir is never "proven" until produced
- "confirmed hydrocarbon" — Only DST/MDT can confirm mobile HC
- "100% confidence" — Not possible in subsurface
- "certain" / "definitely" — Subsurface certainty is an oxymoron
- "proven shoreface" — Even well-known systems have local variability
- "analogous to" without quantifying similarity
- "by analogy" without bounding the uncertainty

## Violation Response

| Level | Example | Action |
|-------|---------|--------|
| Minor | Single hypothesis without alternative | Add contradiction scan |
| Medium | Claim without evidence_for | Reject, require data refs |
| Major | Forbidden phrase ("proven") | Block, red-team review |
| Critical | Claim contradicts OBSERVED data | 888_HOLD escalation |

## Key References

- `/root/GEOX/src/geox_mcp/tools/claims.py` — claim_create, claim_validate, claim_challenge
- `/root/GEOX/src/geox_mcp/tools/evidence_reason.py` — abduct, contradict, full synthesis
- `/root/GEOX/src/geox_core/governance/geox_invariants.yaml` — constitutional claim invariants

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
