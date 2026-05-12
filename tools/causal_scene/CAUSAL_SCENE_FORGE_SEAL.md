# Causal Scene — v2 Dimension-Native Ontology

> **SEAL: 2026-05-12**  
> **Forge origin:** `A-FORGE/geox_schemas.py` (progenitor, 600 lines)  
> **Canonical home:** `geox/tools/causal_scene/`  
> **Motto:** DITEMPA BUKAN DIBERI

---

## The Eureka Gap

The canonical GEOX v1 (`contracts/schemas/output_schemas.py`) uses a **dict-based claim_state model** — 16 tool output schemas described as JSON dictionaries. Each tool returns `claim_state` (INGESTED → QC_VERIFIED → INTERPRETED → DERIVED_CANDIDATE → SEALED) with provenance and depth_basis blocks. The model is **flat, stateless, and tool-centric**.

The A-FORGE progenitor (`geox_schemas.py`) introduces a **Pydantic-native, witness-centric ontology** that v1 completely lacks:

| Concept | v1 (current GEOX) | v2 (progenitor, now here) |
|---|---|---|
| **World model** | Tool output → claim_state | Causal Scene with 4 witness kinds |
| **Evidence types** | Single `primary_artifact` dict | Manifold, Truth, Claim, Texture |
| **Spatial support** | None (depth_basis only) | Discriminated union: grid/stick/track/pointset/volume |
| **Governance** | None separate from tool logic | FloorPolicy, IntentEnvelope, PolicyBand, VerdictCode |
| **Judgment** | claim_state progression only | ContrastVerdict with metrics, links, policy_evaluations |
| **UI** | JSON blob per tool | CausalSceneUISummary + Physics9Item (React-ready) |
| **Thermo** | Not present | ThermoVolume (P/T ranges) |
| **D2T** | Not present | D2TCalibration (depth-to-time tie quality) |

---

## What Was Extracted (and What Wasn't)

**Extracted to this directory:** Only the **architectural concepts** missing from v1. Not the full 600-line file — that would be shallow copy.

**Not extracted (for a reason):**
- `ManifoldWitness` / `TruthWitness` / `ClaimWitness` / `TextureWitness` — these require the full domain model to be useful. Extraction deferred until v2 implementation phase.
- `WitnessBase` — coupled to the entire class hierarchy. Extraction requires deciding inheritance strategy.
- `SurveyBounds`, `MarkerObservation`, `LogCurveRef` — well-specific models. GEOX v1 already has well tools; these need integration planning.

---

## Next Forge Steps

1. **Phase 1** (now): forge seal + extraction of gap analysis
2. **Phase 2**: implement `SupportGeometry` discriminated union as Pydantic models in `contracts/schemas/`
3. **Phase 3**: implement `PolicyBand` + `PolicyEvaluation` as governance primitives
4. **Phase 4**: implement `ContrastOperatorSpec` as tool contract validator
5. **Phase 5**: implement `CausalSceneUISummary` as React payload contract
6. **Phase 6**: clean up A-FORGE root (remove GEOX artifacts)
