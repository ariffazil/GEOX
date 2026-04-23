# Contracts Analysis — GEOX Agent Forge Work
**Version:** 2026.04.14-AUDIT  
**Seal:** 999_SEAL  
**Scope:** Assessment of the 9 specification documents and 4 code files produced in this forge session.

---

## Executive Summary

The forge session produced a **coherent, enforceable constitutional architecture** for GEOX. The specifications are internally consistent, tightly aligned with the stated mission ("high-stakes Earth decisions under uncertainty without getting deceived by our own tools"), and materially advance the codebase from "collection of geoscience tools" to "governed decision engine."

**Overall grade:** **SEAL with QUALIFY caveats.** The architecture is sound, but 4 enforceability gaps and 2 unresolved contradictions must be addressed before regulatory or safety-critical deployment.

---

## 1. Completeness Assessment

### 1.1 What Is Fully Covered

| Domain | Coverage | Evidence |
|--------|----------|----------|
| **Epistemological architecture** | ✅ Strong | `GEOX_CONSTITUTIONAL_PHYSICS_STACK.md` defines L0–L5; every layer has a clear role and handoff contract. |
| **Risk quantification** | ✅ Strong | `TOAC_AC_RISK_SPEC.md` gives operational formulas for U_phys, D_transform, B_cog, calibration loops, and floor overrides. |
| **Tool taxonomy** | ✅ Strong | `GEOX_ORTHOGONAL_TOOL_SPEC.md` + `GEOX_TOOL_TAXONOMY.md` reduce ~82 overlapping tools to 52 with explicit dimension/stage/nature tags. |
| **Cross-product risk inheritance** | ✅ Strong | `GEOX_INTERPRODUCT_RISK_RULES.md` defines VOID propagation, HOLD propagation, AC_Risk inheritance weights, and cascading 888_HOLD chains. |
| **Hard governance gates** | ✅ Strong | `GEOX_GO_NOGO_RULES.md` establishes 5 non-negotiable rules with explicit metabolic enforcement points. |
| **SEAL enforcement** | ✅ Strong | `GEOX_SEAL_CHECKLIST.md` maps per-dimension metabolizer firing requirements; code implements `can_grant_seal()`. |
| **Product versioning & audit** | ✅ Strong | `GEOX_PRODUCT_VERSIONING.md` defines vault-bound schema with Merkle anchoring and replayability contract. |
| **Physics adapter contract** | ⚠️ Partial | `PHYSICS_ADAPTER_SPEC.md` covers 3 adapters (OpenQuake, MODFLOW, TOUGH2) but is a specification, not an implementation. |

### 1.2 What Is Missing or Under-Specified

1. **Data provenance and lineage at the file level**
   - The specs mention `inputs_hash` and `l0_sources` but do not specify how file URIs are guaranteed to be durable (S3 lifecycle policies, institutional data retention contracts).
   - *Gap severity:* Medium. A vault hash is useless if the underlying files are deleted.

2. **B_cog operational detection**
   - `bias_scenario` is manually selected or context-detected, but no algorithm for `detect_bias_scenario()` is provided.
   - *Gap severity:* High. B_cog is the most manipulable component of AC_Risk. Without automated detection of `executive_pressure` or `single_model_collapse`, operators can game the score.

3. **Human escalation latency and timeout rules**
   - 888_HOLD is defined, but there is no SLA for human response. What happens if arif does not respond within 24h / 7d / 30d?
   - *Gap severity:* Medium. For time-sensitive decisions (earthquake aftershock, dam safety), an indefinite HOLD is equivalent to a silent VOID.

4. **Conflict resolution when floors contradict each other**
   - F6 (water sovereignty) and F8 (regulatory) may demand different actions in a transboundary aquifer. The specs do not define a tie-breaker beyond "888_HOLD."
   - *Gap severity:* Medium. This is a real jurisdictional problem for Malaysia (e.g., Johor–Singapore water issues).

5. **Rollback and suppression of prior product versions**
   - The versioning spec defines `superseded_by` but does not define how clients (GIS tools, planning departments) are notified that a product they previously consumed is now VOID or superseded.
   - *Gap severity:* Medium. Old versions are dangerous if they remain in operational systems.

---

## 2. Consistency & Contradictions

### 2.1 Internal Consistency (High)

Across all 9 documents, the following invariants hold without contradiction:
- **AC_Risk thresholds:** `< 0.15 = SEAL`, `0.15–0.34 = QUALIFY`, `0.35–0.59 = HOLD`, `≥ 0.60 = VOID`
- **Metabolic stage mapping:** `observe = 111`, `interpret = 333`, `compute = 222/333`, `verify = 555`, `judge = 888`, `audit = 888/999`
- **888_HOLD mandatory dimensions:** HAZARD, HYDRO, CCS, Resource Volumetrics, Geotechnical
- **SEAL universal preconditions:** AC_Risk < 0.15, vault anchor, runtime health, lineage audit

### 2.2 Detected Contradictions / Ambiguities

#### Contradiction A: SEAL ceiling vs. 888_HOLD mandatory list
**Location:** `GEOX_SEAL_CHECKLIST.md` vs. `GEOX_GO_NOGO_RULES.md`

- `GEOX_SEAL_CHECKLIST.md` says for HAZARD: "SEAL ceiling: QUALIFY for public maps; SEAL only for internal scenario studies."
- `GEOX_GO_NOGO_RULES.md` says Rule 5: 888_HOLD is mandatory for HAZARD public maps.

**Issue:** If public HAZARD maps are mandatory 888_HOLD, they can never achieve SEAL (because 888_HOLD means the verdict is at best HOLD pending approval). But the SEAL checklist says "SEAL ceiling: QUALIFY" — implying public maps can at most be QUALIFY, not even reach the HOLD gate.

**Resolution:** The intent is clear (public maps should not be SEAL), but the phrasing is contradictory. Should read: "Public HAZARD maps: maximum verdict QUALIFY; internal studies may reach SEAL if all checklists pass." Remove the reference to 888_HOLD for public maps since they are capped below it.

*Verdict:* **Cosmetic contradiction.** Intent is unambiguous in practice.

---

#### Contradiction B: `geox_vision_review` in SEAL checklist vs. Orthogonal Spec
**Location:** `GEOX_SEAL_CHECKLIST.md` (SECTION dimension) vs. `GEOX_ORTHOGONAL_TOOL_SPEC.md`

- SEAL checklist says SECTION requires `geox_vision_review` (or `section_audit_transform_chain` F9 check).
- Orthogonal spec deprecates `geox_vision_review` to `section_audit_transform_chain` (F9 check).

**Issue:** The SEAL checklist references a deprecated tool name.

**Resolution:** Update SEAL checklist to use canonical name: `section_audit_transform_chain` with F9 flag.

*Verdict:* **Cosmetic contradiction.** Easy fix.

---

#### Contradiction C: D_transform scale in TOAC spec vs. code
**Location:** `TOAC_AC_RISK_SPEC.md` §3.3 vs. `geox/core/ac_risk.py` `compute_ac_risk()`

- The spec defines `D_transform ∈ [1.0, 3.0]` as a multiplicative distortion factor.
- But `GEOX_INTERPRODUCT_RISK_RULES.md` §3 and `geox/core/ac_risk.py` use `D_transform` directly in `AC_Risk = U_phys × D_transform × B_cog`.

**Issue:** If D_transform is capped at 3.0, U_phys at 1.0, and B_cog at 1.0, AC_Risk maxes at 3.0 — but AC_Risk is supposed to be capped at 1.0. The code does `min(1.0, ...)` so the math works, but the intermediate D_transform value can exceed the conceptual range of "risk contribution."

Wait — this is **not a contradiction**. D_transform is a multiplier on the *raw* physical signal, not a probability. The capping at 1.0 happens at the AC_Risk level. But it creates a **modeling ambiguity**: a D_transform of 2.5 with U_phys = 0.30 gives AC_Risk = 0.525 (HOLD). A D_transform of 2.5 with U_phys = 0.10 gives AC_Risk = 0.175 (QUALIFY). The transform distortion is therefore not independently meaningful; it only matters in combination with U_phys.

*Verdict:* **Not a contradiction, but a potential user confusion.** The spec should clarify that D_transform is not a standalone risk score.

---

#### Contradiction D: Calibration misprediction threshold
**Location:** `TOAC_AC_RISK_SPEC.md` §5.3 vs. `geox/core/ac_risk.py` `evaluate_verdict()`

- Spec says: `misprediction_ratio > 2.0` → auto-downgrade one band.
- Code says: `calibration_misprediction_ratio is not None and calibration_misprediction_ratio > 2.0` → downgrade.

**Issue:** The spec does not define what happens at exactly `2.0`. The code uses `> 2.0` (strict inequality), which matches the spec, but the boundary case is undefined.

*Verdict:* **Minor ambiguity.** Recommend adding `≥ 2.0` in both spec and code to avoid edge-case gaming.

---

## 3. Enforceability Assessment

### 3.1 Code-Backed Enforcement (Strong)

The following rules are **already enforced in code**:

| Rule | Code Location | Mechanism |
|------|---------------|-----------|
| AC_Risk computation | `geox/core/ac_risk.py` `compute_ac_risk()` | Returns verdict based on inputs |
| Floor overrides | `geox/core/ac_risk.py` `evaluate_verdict()` | F1, F2, F7, F9, F13 hard-coded |
| SEAL checklist | `geox/core/tool_registry.py` `can_grant_seal()` | Boolean gate with failure list |
| Cross-product mandatory HOLD | `geox/core/tool_registry.py` `MANDATORY_888HOLD_DIMENSIONS` | Set-based check |
| Upstream verdict inheritance | `geox/core/ac_risk.py` `evaluate_verdict()` | `upstream_verdicts` parameter |
| Tool taxonomy | `geox/core/tool_registry.py` `ToolMetadata` | `dimension`, `stage`, `nature` fields |
| MCP resource exposure | `control_plane/fastmcp/server.py` | Three new `geox://registry/*` resources |

### 3.2 Specification-Only Enforcement (Medium Risk)

The following rules exist in specs but have **no automated enforcement yet**:

| Rule | Document | Gap |
|------|----------|-----|
| Temporal validity inheritance | `GEOX_INTERPRODUCT_RISK_RULES.md` §5 | No code checks `valid_until` dates |
| Calibration event registry | `TOAC_AC_RISK_SPEC.md` §5.4 | Registry exists in `ac_risk.py` but no periodic job to process vault events |
| B_cog detection from user context | `TOAC_AC_RISK_SPEC.md` §4 | `detect_bias_scenario()` is not implemented |
| Physics adapter thin-wrapper contract | `PHYSICS_ADAPTER_SPEC.md` | No adapter implementations exist |
| Cross-product dependency graph | `GEOX_INTERPRODUCT_RISK_RULES.md` §5 | JSON registry is documented but not loaded into `tool_registry.py` |
| Product versioning envelope | `GEOX_PRODUCT_VERSIONING.md` | Schema defined but not validated at runtime |

### 3.3 Unenforceable by Code (Governance Layer)

These require human or institutional process:
- **Sovereign veto (F13):** Code can route to 888_HOLD, but only a human can approve.
- **Data provider QC flags:** Code can store `qc_flag: passed`, but only the provider can truthfully set it.
- **Regulatory mapping (F8):** Code can flag "regulatory filing," but jurisdiction-specific law is outside the system.

*Assessment:* This is correct. These are **governance boundaries**, not implementation gaps. The system correctly routes them to human authority.

---

## 4. Mission Alignment

### 4.1 Alignment with "High-Stakes Earth Decisions Under Uncertainty"

**Grade: A-**

The specifications directly address the three failure modes of high-stakes geoscience:

1. **Over-interpretation (pattern fitting without physics)** → Blocked by Rule 2 (physics verification before interpretation) and F9 Anti-Hantu checks.
2. **Optimistic cascade (downstream products ignoring upstream uncertainty)** → Blocked by Rule 3 (cross-product risk inheritance) and explicit inheritance weights.
3. **Unvalidated models influencing public safety** → Blocked by Rule 5 (mandatory 888_HOLD for HAZARD/HYDRO/CCS) and calibration loop penalties.

### 4.2 Alignment with "Without Getting Deceived by Our Own Tools"

**Grade: A-**

The architecture treats AI/VLM, math transforms, and physics engines as **sources of distortion**, not oracles:
- Every transform is logged and scored (`D_transform`)
- Every AI interpretation is flagged for hallucination review (`section_audit_transform_chain` F9 check)
- Every model that has mispredicted before is penalized (`U_phys` adjustment)
- Every product that could affect cities or water requires human sign-off (F13)

**Remaining vulnerability:** B_cog is manually specified. A malicious or careless operator could set `bias_scenario = "physics_validated"` when no such validation exists, artificially lowering AC_Risk. This is the **single largest attack surface** in the current design.

---

## 5. Gaps Requiring Next Forge Session

### Priority 1: B_cog Operationalization
**File target:** `geox/core/bias_detector.py` (new)

Implement heuristic detection for at least these scenarios:
- `executive_pressure`: deadline < model validation time estimate
- `single_model_collapse`: number of candidate models reduced from >3 to 1 without new physical constraint
- `ai_vision_only`: transform stack contains `vlm_inference` or `ai_segmentation` with no `physics_verify_parameters` in the chain
- `multi_interpreter`: evidence of ≥3 distinct interpreter signatures in product metadata

**Why P1:** Without this, AC_Risk is gameable.

---

### Priority 2: Dependency Graph Registry in Code
**File target:** `geox/core/tool_registry.py`

Load the JSON dependency registry from `GEOX_INTERPRODUCT_RISK_RULES.md` §5 into a queryable data structure and wire `can_grant_seal()` to check upstream product verdicts from the vault.

**Why P2:** Currently, cross-product inheritance is a spec-only rule.

---

### Priority 3: Calibration Job Scheduler
**File target:** `geox/jobs/calibration_sync.py` (new)

A periodic task (daily/weekly) that:
1. Queries VAULT999 for prediction records with elapsed forecast horizons
2. Compares against new observation records
3. Computes misprediction ratios
4. Updates `_CALIBRATION_REGISTRY` in `geox/core/ac_risk.py`

**Why P3:** The calibration loop is structurally defined but not operationally closed.

---

### Priority 4: Product Schema Validator
**File target:** `geox/core/product_validator.py` (new)

A runtime validator that checks every tool output against `GEOX_PRODUCT_VERSIONING.md` schema before it can be vaulted. Fails fast with `GEOX_400_VALIDATION` if required fields are missing.

**Why P4:** Prevents "almost-SEAL" products from entering the vault with incomplete metadata.

---

### Priority 5: 888_HOLD Timeout & Escalation Policy
**File target:** `GEOX_GO_NOGO_RULES.md` (amendment)

Define explicit behavior for unreviewed HOLD tickets:
- `t < 24h`: HOLD remains active
- `24h ≤ t < 7d`: Auto-escalate notification to secondary sovereign
- `t ≥ 7d`: For non-life-safety products, downgrade to VOID (safe default). For life-safety products (HAZARD evacuation), maintain HOLD and escalate to institutional emergency contact.

**Why P5:** Prevents silent indefinite HOLDs that paralyze decision-making.

---

## 6. Risk Analysis of the Specifications Themselves

### 6.1 What Could Make This Contract Fail in Court or Arbitration?

1. **Vagueness in "reasonable" or "moderate" language**
   - The spec uses terms like "moderate uncertainty" and "standard exploration context" in U_phys interpretation. These are not legally precise.
   - *Fix:* Replace qualitative bands with quantitative thresholds where possible.

2. **Reliance on undocumented institutional knowledge**
   - The `bias_scenario` enum includes culturally specific concepts (e.g., "executive pressure" understood within PETRONAS context).
   - *Fix:* Add explicit definitions in an appendix.

3. **No dispute resolution mechanism**
   - If two sovereign authorities disagree on a HOLD resolution, the specs do not define arbitration.
   - *Fix:* Out-of-scope for GEOX; this is an arifOS governance question. Correctly deferred.

### 6.2 What Makes This Contract Defensible?

1. **Every rule has an enforcement point (metabolic stage) and a violation consequence (VOID/HOLD).**
2. **Every product is tamper-evident (Merkle chain).**
3. **The calibration loop creates a duty-of-care feedback mechanism.**
4. **The 888_HOLD gate creates an explicit audit trail of human judgment.**

These are the four pillars of defensible AI governance: **traceability, tamper-evidence, continuous improvement, and human override.**

---

## 7. Final Verdict

| Criterion | Grade | Notes |
|-----------|-------|-------|
| **Completeness** | B+ | 5 gaps identified; none are fatal. |
| **Consistency** | A- | 2 cosmetic contradictions, 1 minor ambiguity. |
| **Enforceability** | B+ | Strong code coverage for core rules; 6 spec-only rules remain. |
| **Mission Alignment** | A- | Directly addresses over-interpretation, optimistic cascade, and unvalidated models. |
| **Legal Defensibility** | B+ | Merkle anchoring and human override provide strong defenses; some vague language remains. |

**Composite Verdict:** **QUALIFY → SEAL pending resolution of P1 (B_cog operationalization) and Contradiction A (SEAL ceiling wording).**

> The architecture is correct. The next forge session should not add more documents. It should implement the enforcement gaps.

---

**Sealed:** 2026-04-14T06:15:00Z  
**Analyst:** Kimi Code CLI (AF-FORGE VPS)  
**DITEMPA BUKAN DIBERI**
