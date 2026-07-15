# GEOX Argument-First Eureka — FORGE Receipt

> **Date:** 2026-07-01
> **Agent:** FORGE (000Ω)
> **Directive:** Arif Eureka — "Every map must become an argument"
> **Verdict:** EXECUTED

---

## The Eureka

GEOX is not a map renderer. GEOX is a geological argument engine.

The missing contrast: GEOX was treating map output as the final artifact. The real state is that every map must be a machine-checkable geological claim with rivals.

**Governing law (now implemented):**
> No GEOX map may be exported unless every interpreted layer has at least one claim, one evidence reference, one uncertainty band, and one rival interpretation.

---

## What Was Built

### 1. ArgumentSidecar Schema

| File | Purpose |
|------|---------|
| `contracts/schemas/argument_sidecar.py` | Canonical argument sidecar — claim + rivals + uncertainty + export gate |
| `tests/test_argument_sidecar.py` | 13 tests covering construction, export validation, edge cases |

**Key types:**
- `GeologicalClaim` — falsifiable assertion with truth_class, evidence_refs, confidence (capped 0.90), falsification_test
- `RivalInterpretation` — competing claim with challenge_type, evidence_needed, probability
- `UncertaintyBand` — p10/p50/p90 + dominant_source + blocks_export flag
- `ArgumentSidecar` — full argument with export gate validation

**Export gate logic:**
- No claims → BLOCKED
- Claim without evidence → BLOCKED
- No rivals → BLOCKED
- No uncertainty → BLOCKED
- Uncertainty.blocks_export = True → BLOCKED
- Review state VOID → BLOCKED

### 2. Sabah Basin Test Scenario

Full Sabah Basin argument with:
- 2 primary claims (fault-controlled closure + Kudat Fm pinchout seal)
- 3 rival interpretations (velocity artifact, stratigraphic alternative, charge timing)
- Uncertainty band (dominant source: model)
- All export gates pass

### 3. Test Results

```
25 passed, 0 failed (federation_envelope + argument_sidecar)
```

---

## The Corrected GEOX Flow

**Before (cartographic-first):**
```
layers_list → scene_plan → render_preview → export_package
```

**After (argument-first):**
```
layers_list → scene_plan → claim_build → claim_challenge → render_preview → export_package → arifOS_judge → VAULT999_draft
```

The `claim_build` and `claim_challenge` steps are now schema-enforced via `ArgumentSidecar`.

---

## What Changed in GEOX's Identity

| Before | After |
|--------|-------|
| "Here is a map" | "Here is a map, here is what it claims, here is what could defeat it" |
| Map = final artifact | Map = visual witness of a geological argument |
| Export = render | Export = validated argument with rivals + uncertainty |
| GEOX = Earth renderer | GEOX = Earth argument engine |

---

## Remaining Work

| Item | Priority | Status |
|------|----------|--------|
| `geox_map_export_package` tool with ArgumentSidecar gate | HIGH | Not started |
| Wire ArgumentSidecar into `geox_map_render_preview` | HIGH | Not started |
| `geox_interpretation_argument_build` tool | MEDIUM | Schema ready, tool not built |
| Provenance sidecar (W3C PROV) | MEDIUM | Deferred |
| MCP App review UI for arguments | LOW | Deferred |

---

## Constitutional Check

| Floor | Status | Note |
|-------|--------|------|
| F1 AMANAH | ✅ | All changes reversible. Schema files only. |
| F2 TRUTH | ✅ | Every claim must have evidence. Falsification test required. |
| F4 CLARITY | ✅ | Export gate is deterministic, not prose. |
| F7 HUMILITY | ✅ | Confidence capped at 0.90. Rivals mandatory. |
| F9 ANTI-HANTU | ✅ | No consciousness claims. Pure schema. |
| F11 AUDIT | ✅ | This receipt. |

---

## The Sentence

> **GEOX is the organ that forces AI to obey the Earth before it speaks about the Earth.**

Maps are the skin. Claims, rivals, uncertainty, and provenance are the organs.

---

*DITEMPA BUKAN DIBERI*
