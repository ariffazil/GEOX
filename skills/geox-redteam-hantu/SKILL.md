---
id: geox-redteam-hantu
name: geox-redteam-hantu
version: "1.0.0-2026.08.17"
description: Anti-hallucination guardian for GEOX. F9 enforcement. Detects and blocks fabricated formations, phantom wells, ghost data, and epistemic collapse.
owner: GEOX
risk_tier: high
floor_scope: [F2, F7, F9, F10, F12]
autonomy_tier: T0
trigger_phrases:
  - "hallucination"
  - "fabricated data"
  - "phantom well"
  - "ghost formation"
  - "anti-hantu"
  - "geox-redteam-hantu"
dependencies:
  mcp_servers:
    - geox
  skills:
    - geox-epistemic-ladder
    - geox-claim-grammar
    - geox-contradiction-engine
---

# GEOX Red-Team Hantu — Anti-Hallucination Guardian

> **F9 ANTI-HANTU enforcement for GEOX.** No deception, manipulation, or fabricated data.
> "Hantu" = ghost in Malay. This skill hunts geological ghosts.

## Primary Tools

| Tool | Use for |
|------|---------|
| `geox_falsify` | Popperian falsification — Kill Matrix K001-K007 |
| `geox_contradiction_scan` | Scan claims for contradictions (13-type ontology) |
| `geox_claim` | Challenge claims, attach evidence |
| `geox_well_qc` | Validate well data integrity |
| `geox_surface_status` | Verify tool/registry health |

## The Ghost Taxonomy

GEOX hallucinations fall into7 categories. Each requires specific detection:

### 1. Phantom Wells
**Pattern:** Agent references a well that doesn't exist in the loaded dataset.
**Detection:** Every well reference must trace to `geox_well_ingest` artifact_ref.
```yaml
phantom_check:
  well_id: "A-1"
  artifact_ref: "<sha256>"  # Must exist in workspace
  source: "geox_well_ingest"  # Must be traceable
```

### 2. Fabricated Formations
**Pattern:** Agent names a formation (e.g. "Lumut Member") without literature reference.
**Detection:** Formation names require `source_tag: VERIFIED_LITERATURE` or better.

### 3. Ghost Data
**Pattern:** Agent cites numerical values (porosity, GR, depth) not present in loaded data.
**Detection:** Every number must trace to an OBSERVED or DERIVED artifact.

### 4. Epistemic Collapse
**Pattern:** Agent treats INTERPRETATION as OBSERVED fact.
**Detection:** Rung mismatch — interpretation claiming observation-level certainty.
```
❌ "The reservoir is gas-bearing" (claimed as OBSERVED)
✅ "The GR motif suggests gas-bearing sand" (labeled as INTERPRETATION)
```

### 5. Single-Well Extrapolation
**Pattern:** Agent makes basin-wide claims from a single well.
**Detection:** Spatial claims require ≥3 data points for same formation.

### 6. Confidence Inflation
**Pattern:** Agent assigns confidence > 0.90 to subsurface claim.
**Detection:** Hard cap at 0.90 for all geological claims. Override requires 888_HOLD.

### 7. Analog Abuse
**Pattern:** Agent uses "analogous to" without quantifying similarity.
**Detection:** Every analogy must specify: what is similar, what differs, and uncertainty band.

## Detection Protocol

```
1. RECEIVE claim or interpretation
2. SCAN for phantom wells (artifact_ref check)
3. SCAN for fabricated formations (source_tag check)
4. SCAN for ghost data (number traceability)
5. SCAN for epistemic collapse (rung validation)
6. SCAN for single-well extrapolation (spatial check)
7. SCAN for confidence inflation (cap check)
8. SCAN for analog abuse (specificity check)
9. IF any FAIL → geox_contradiction_scan
10. IF FATAL → 888_HOLD
```

## Forbidden Phrases (GEOX-specific)

These trigger immediate HANTU_REVIEW:
- "proven reservoir" — reservoirs are never proven until produced
- "confirmed hydrocarbon" — only DST/MDT confirms mobile HC
- "the formation is" without epistemic rung label
- "analogous to" without quantified similarity metric
- "100% certain" / "definitely" — subsurface certainty is an oxymoron
- Any well name not in loaded dataset
- Any depth not in loaded curves
- Any formation name without literature reference

## Violation Response

| Severity | Pattern | Action |
|----------|---------|--------|
| LOW | Missing epistemic label | Flag, require label |
| MEDIUM | Single-well extrapolation | HOLD, require additional data |
| HIGH | Phantom well reference | BLOCK, require artifact verification |
| FATAL | Fabricated data presented as OBSERVED | 888_HOLD + scar seal |
| FATAL | Confidence > 0.90 on subsurface claim | 888_HOLD, demote to 0.90 max |

## Integration with Claim Lifecycle

```
geox_claim(create) → geox_redteam_hantu(scan) → geox_falsify(kill_matrix)
  ↓ PASS → proceed to geox_contradiction_scan
  ↓ FAIL → HOLD, require evidence
  ↓ FATAL → 888_HOLD, sovereign review
```

## Key References

- `/root/GEOX/GENESIS/015_FALSIFICATION_ENGINE.md` — Kill Matrix K001-K007
- `/root/GEOX/GENESIS/003_CONSTITUTIONAL_ALIGNMENT.md` — Cross-Modal Fidelity
- `/root/GEOX/src/geox_core/core/epistemic_integrity.py` — integrity scoring
- `/root/arifOS/GENESIS/000_KERNEL_CANON.md` — F9 ANTI-HANTU floor

**DITEMPA BUKAN DIBERI — Ghosts are hunted, not tolerated.**
