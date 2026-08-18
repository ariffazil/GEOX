---
id: geox-epistemic-ladder
name: geox-epistemic-ladder
version: "1.1.0-2026.08.17"
description: Epistemic rungs — OBSERVED → DERIVED → INTERPRETED → HYPOTHESIS → EARTHMODEL → DECISIONSUPPORT → HUMAN JUDGMENT. Prevents category errors.
owner: GEOX
risk_tier: high
floor_scope: [F2, F4, F7, F9, F11]
autonomy_tier: T1
trigger_phrases:
  - "epistemic ladder"
  - "observed vs derived"
  - "confidence rung"
  - "epistemic rung"
  - "geox-epistemic-ladder"
dependencies:
  mcp_servers:
    - geox
  skills:
    - geox-claim-grammar
---

# GEOX Epistemic Ladder Skill

The epistemic ladder prevents **category errors** — treating an interpretation as a fact, or a hypothesis as a proven model. Every geological claim must be tagged at its correct rung.

## Primary Tools

| Tool | Use for |
|------|---------|
| `geox_claim` | Claims carry epistemic rung in their structure |
| `geox_falsify` | Falsification respects rung hierarchy |
| `geox_contradiction_scan` | Contradiction severity depends on rung mismatch |
| `geox_petrophysics` | DERIVED rung — bounded transforms from OBSERVED |
| `geox_seismic_interpret` | INTERPRETED_LOCAL through EARTHMODEL rungs |
| `geox_prospect` | DECISIONSUPPORT rung — formal recommendation |

## The 7-Rung Ladder

| Rung | Label | What It Means | Example |
|------|-------|---------------|---------|
| 1 | **OBSERVED** | Direct sensor reading. The only rung that is "true" in the physical sense. | GR = 85 API at 2450m MD |
| 2 | **DERIVED** | Computed from OBSERVED via bounded, validated transform. | Porosity = 0.18 from density log using ρma=2.65 |
| 3 | **INTERPRETED_LOCAL** | Single-well geological interpretation. Expert pattern match on curves. | "Shale-prone interval, coarsening-upward motif" |
| 4 | **PROCESS_HYPOTHESIS** | A depositional/environmental process is hypothesized. | "Mouth bar deposit in delta front" |
| 5 | **EARTHMODEL** | Multiple wells + seismic integrated into consistent 3D/4D narrative. | "NW-SE progradational clinoform set" |
| 6 | **DECISIONSUPPORT** | Formal recommendation with quantified uncertainty and risk. | "Drill Well-X: P50 12MMbo, ACRisk 0.42" |
| 7 | **HUMAN JUDGMENT** | Human (Arif) makes final decision after reviewing all evidence. | 888_HOLD verdict: SEAL / SABAR / VOID |

## Iron Rule

**Lower-rung observation ALWAYS beats higher-rung interpretation.**

- A DERIVED porosity of 0.22 is MORE TRUE than an EARTHMODEL that says 0.18.
- A PROCESS_HYPOTHESIS must be challenged if it conflicts with OBSERVED data.
- HUMAN JUDGMENT can override any rung, but only after viewing all evidence.

## Forbidden Moves

| Move | Why It's Forbidden |
|------|-------------------|
| INTERPRETED → CLAIM without evidence chain | Skips uncertainty |
| EARTHMODEL → FACT | Models are never facts |
| Single well → Basin-wide conclusion | Spatial extrapolation without data |
| "Bright spot = gas" without fluid substitution modeling | AVO classes I-IV can mimic HC |
| Correlation without chronostratigraphic constraint | Time-transgressive surfaces |

## Detection Rules

When scanning code/outputs:
- If a string says "the reservoir" without `EpistemicRung` — flag it
- If a number has no uncertainty band (P10/P50/P90) and is INTERPRETED+ — flag it
- If a single well log is labeled EARTHMODEL — flag it
- If HUMAN_JUDGMENT appears without `888_HOLD` or Arif's signature — flag it
- If any rung ≥ 4 is used without documenting `evidence_for`, `evidence_against`, `missing_tests` — flag it

## Key References

- `/root/GEOX/src/geox_core/core/epistemic_integrity.py` — pLDDT-equivalent integrity scoring
- `/root/GEOX/src/geox_core/schemas/output_schemas.py` — TOOL_RUNG_MAP
- `/root/GEOX/GENESIS/003_CONSTITUTIONAL_ALIGNMENT.md` — Cross-Modal Fidelity Theorem

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
