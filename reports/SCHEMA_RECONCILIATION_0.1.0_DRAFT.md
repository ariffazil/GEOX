# SCHEMA_RECONCILIATION_0.1.0_DRAFT.md — GATE B

**Status:** DRAFT — not frozen. Pending human acceptance of version, field semantics, vocabulary mapping.
**Goal:** prevent a fourth parallel claim vocabulary. Map the THREE observed vocabularies onto FIVE orthogonal dimensions.

---

## 1. The three observed vocabularies (OBS, 2026-10-14)

| # | Vocabulary | Source | Status |
|---|---|---|---|
| V1 | Mission RULE-04 | GEOX AAA FORGE INIT v2 (Arif) | directive |
| V2 | Locked ClaimState | `src/geox_core/schemas/claim_envelope.py` | NO_STATIC_CONSUMER_FOUND, broken under pydantic>=2.14 (`_internal` field) |
| V3 | Live claim envelope | `src/geox_mcp/tools/claims.py::_build_claim_envelope` + `contracts/claim_state_machine.yaml` | LIVE, consumed by `auto_mint.py`, `claim_explanation_guard.py`, `geox_claim_seal` |

V3 is the authoritative live vocabulary. V2 is locked but has no static importer. V1 is the mission directive.

---

## 2. Five orthogonal dimensions (target)

| Dimension | Values | Producer | Consumer | Owner |
|---|---|---|---|---|
| `epistemic_class` | OBSERVED / COMPUTED / INTERPRETED_LOCAL / HYPOTHESIS | GEOX engine | bundle output | mission |
| `lifecycle_state` | NO_VALID_EVIDENCE / INGESTED / QC_VERIFIED / INTERPRETED / DERIVED_CANDIDATE | GEOX claim worker | `geox_claim` | GEOX |
| `explanation_class` | MEASURED / MECHANISM / PATTERN / NARRATIVE / UNCLASSIFIED | claim_kernel/v1 | `claim_explanation_guard.py` (seal gate) | GEOX |
| `authority_ceiling` | QUALIFIED_CANDIDATE (constant) | GEOX | arifOS | arifOS |
| `constitutional_verdict` | SEALED / SABAR / VOID / HOLD (null default) | **arifOS only** | VAULT999 | arifOS |

---

## 3. Value-by-value mapping

### 3.1 epistemic_class (V1 mission ↔ V3 truth_class + epistemic_label)

| Mission value | V3 truth_class | V3 epistemic_label | Mapping | Loss |
|---|---|---|---|---|
| OBSERVED | FACT | OBS | OBSERVED → OBS (direct measurement) | lossy (V1 collapses "measured-fact" vs "asserted-certainty") |
| COMPUTED | — | DER | COMPUTED → DER (deterministic transform) | lossless (derived) |
| INTERPRETED_LOCAL | INTERPRETATION | INT | INTERPRETED_LOCAL → INT | lossless |
| HYPOTHESIS | SPECULATION | SPEC/HYPOTHESIS | HYPOTHESIS → SPEC/HYPOTHESIS | lossy (V3 splits speculation vs multi-hypothesis) |

**Unresolved contradiction (OQ-1):** mission FORBIDDEN includes `FACT`, but V3 `truth_class`
uses `FACT` as a valid *measured* class. Two senses: assertion-of-certainty (forbidden)
vs measured-fact (allowed). Needs Arif/888 ruling before `epistemic_class` can be forced
one-to-one onto V3.

### 3.2 lifecycle_state (V2 locked ↔ V3 claim_state ↔ state-machine)

- V3 `claim_state` (LIVE): DRAFT / VALIDATED / REVIEWED / SEALED / VOID.
- V2 `ClaimState` (locked): NO_VALID_EVIDENCE / INGESTED / QC_VERIFIED / INTERPRETED / DERIVED_CANDIDATE / SEALED / JUDGE_PREVIEW / HOLD / VOID.
- `contracts/claim_state_machine.yaml` (LIVE SOT): 9 states, 8 transitions, 9 error codes.

V2 CONFLATES lifecycle (INGESTED→QC_VERIFIED) with verdict (SEALED/VOID/HOLD/JUDGE_PREVIEW).
Target `lifecycle_state` keeps ONLY the pipeline stage values (NO_VALID_EVIDENCE … DERIVED_CANDIDATE);
verdicts move to `constitutional_verdict`. Mapping is **lossy by design** (separation is the fix).

**Unresolved contradiction (OQ-2):** V3 lifecycle (DRAFT→VALIDATED→REVIEWED→SEALED) is a
*governance/review* ladder; V2 lifecycle (INGESTED→QC_VERIFIED→DERIVED_CANDIDATE) is a
*processing* ladder. These are two different axes. The bundle schemas currently use the
V2 processing ladder for `lifecycle_state`. Whether the bundle should instead track the
V3 governance ladder is open.

### 3.3 explanation_class (LIVE, active consumers — PRESERVE)

- MEASURED / MECHANISM / PATTERN are action-eligible (may be sealed).
- NARRATIVE / UNCLASSIFIED are publishable but NOT action-eligible (cannot be approved/sealed).
- Guarded transitions: REVIEW_PENDING|CHALLENGED → APPROVED_INTERPRETATION, and
  APPROVED_INTERPRETATION → SEALED, both require action-eligible explanation_class.
- **Preserved verbatim** in bundle_common (`ExplanationClass`, `ACTION_ELIGIBLE_EXPLANATION`).

### 3.4 authority_ceiling — constant, lossless

`QUALIFIED_CANDIDATE`. GEOX never exceeds. No mapping needed.

### 3.5 constitutional_verdict — null default, owner arifOS

`SEALED / SABAR / VOID / HOLD`. GEOX never sets it. Mapping lossless.

---

## 4. claim_envelope.py consumer classification

Probes (OBS):
- `grep "claim_envelope" src/` → references in `upstream_registry.py:10` (doctrine mention),
  `claims.py::_build_claim_envelope` (independent builder, NOT importing the module),
  `desurvey_core.py` (dict key `claim_envelope`), my 3 schema files.
- `grep "import claim_envelope"` → **0 static imports**.
- `SOURCES.txt` → packaged (egg-info lists it).

**Classification: NO_STATIC_CONSUMER_FOUND.** (NOT dormant/dead/safe-to-retire.)
Dynamic consumers (registry loading, plugin discovery, string import) not yet excluded —
a full dependency graph is required before any fix/retire decision.

---

## 5. Open questions → ARIF / 888

| ID | Question | Required from |
|---|---|---|
| OQ-1 | "FACT" forbidden (mission) vs valid truth_class (V3). Same or different sense? | Arif / 888 |
| OQ-2 | Which lifecycle ladder governs bundles — V2 processing or V3 governance? | 888 |
| OQ-3 | claim_envelope.py: NO_STATIC_CONSUMER_FOUND + broken + IMMUTABLE → fix, retire, or leave? (needs full dep graph first) | 888 |
| OQ-4 | V1 epistemic_class vs V3 truth_class+epistemic_label: one axis renamed, or two axes? | 888 |

---

## 6. Schema test results (GATE B task 4)

`scripts/verify_bundle_schemas.py` — **10/10 PASS** (2026-10-14, venv pydantic 2.14.0):
1. JSON round-trip · 2. forbidden claim rejection · 3. fewer-than-three hypotheses rejection ·
4. non-null preferred rejection · 5. missing provenance rejection · 6. backward compatibility ·
7. cross-schema shared vocabulary · 8. pydantic version · 9/9b. unknown enum rejection.
