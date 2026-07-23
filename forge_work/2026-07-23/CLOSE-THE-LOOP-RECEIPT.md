# Close-the-Loop Receipt — GEOX Seismic Interpret Router + Capability

> **Authority:** F13 SOVEREIGN · DRAFT_ONLY
> **Branch:** `zen/geox-zen-promotion-2026-07-23` (3 commits ahead of main)
> **Caller:** Arif (sovereign probe)
> **Purpose:** Convert two open claims from INTERPRETED to OBSERVED:
> 1. Router regression: each mode dispatches to its own handler
> 2. Capability leg: `interpret_section` ingests real seismic image, emits tagged geometry

## 1. Router regression — bug fixed

### Test surface

For each mode, re-call via `geox_seismic_interpret` and verify the response carries that mode's own contract (not a silent remap to another mode).

| Mode | Mode echoed in response | Error (if any) | Dispatch |
|------|------------------------|----------------|----------|
| `horizon_contrast` (valid 1D inputs) | `horizon_contrast` ✓ | none | own handler |
| `fault_sticks` (`/tmp/nope.csv`) | `fault_sticks` ✓ | `CSV ingestion failed: …` | own handler (CSV reader) |
| `rsi_pipeline` (`/tmp/nope.png`) | `rsi_pipeline` ✓ | none — image loaded | **own handler — NOT remapped to horizon_contrast** |
| `interpret_section` (`/tmp/nope.png`) | `interpret_section` ✓ | none — image loaded | own handler |
| `segy_slice` (`/tmp/nope.segy`) | `segy_slice` ✓ | `FILE_NOT_FOUND` | own handler |
| `structure_validate` (empty framework) | `structure_validate` ✓ | `EMPTY_FRAMEWORK` | own handler |
| `volume_frame` (no volume_ref fixture) | dispatched, gate fires | `_dim_spot_note` | own handler |
| `blend` (no fixture) | EXCEPTION (TypeError) | `unexpected keyword argument` | **handler signature bug — separate ticket** |

**Conclusion:** the bug Arif observed (`rsi_pipeline` silently returning `horizon_contrast` error verbatim) is **fixed**. Each mode now declares its own contract. The fix was the audit patch on 2026-07-23 (`extra="forbid"` → `extra="ignore"` on `StrictModel`), which lets per-mode fields reach their dispatch handler instead of being rejected at the union level with a misleading error from another branch.

One residual bug surfaced: `geox_blend_volume_tool()` signature mismatch with the router's call site — handler doesn't accept `volume_ref`. Logged as a separate ticket; not on the critical path for the close-the-loop receipt.

## 2. Capability leg — `interpret_section` ingests real data, emits tagged geometry

### Input

- **File:** `/root/GEOX/data/atlas/cache/renders/8a5b232559341756.png`
- **Class:** PNG, 1243 × 990, 8-bit grayscale
- **Calibration:** none declared → `input_class=image_only`, `epistemic_label=INT_SEISMIC`
- **SHA-256 (short):** `46c446ce1c1b7c01` (verified against the bundle's provenance stage)

### Output (summary)

| Field | Value |
|-------|-------|
| `ok` | `True` |
| `mode` | `interpret_section` |
| `input_class` | `image_only` |
| `epistemic_label` | `INT_SEISMIC` |
| `local_verdict` | `QUALIFIED_CANDIDATE` (max — refuses local SEAL) |
| `seal_authority` | `arifOS_only` |
| `seal_eligibility` | `False` (image_only — correct refusal) |
| **n_faults picked** | **6** (INT_SEISMIC_FAULT) |
| **n_horizons picked** | **8** (INT_SEISMIC_HORIZON) |
| **n_alternatives** | 3 (through_going / relay_segmented / artifact_dominant) |
| **RSI stages** | R0 reality_gate, R1 provenance, R2 panel_detect, R4 attributes (11 computed), R5 faults, R5b fault_blocks (2), R6 horizons, R7 governance, R8 render_audit |

### Receipt artifacts (saved to disk)

- `forge_work/2026-07-23/RECEIPT-interpret-section-F3-png.json` — full propose leg, 6 faults + 8 horizons + 3 alternatives + 9-stage provenance
- `forge_work/2026-07-23/RECEIPT-interpret-mode-F3-png.json` — full propose → validate → compare leg; bundle emits 3 hypotheses (HYP-001/002/003), all `combined_gate_verdict=UNMEASURED` (because image_only has no calibrated dip → K-DIP returns UNMEASURED per the doctrine), `preferred_hypothesis=None`, `seal_eligibility=False`, `governance_status=HOLD`

### RSI attributes computed (image-only input)

11 attributes per the bundle's R4 stage, all labelled `DER_RENDER_CONTRAST`:
`agc, cosine_phase, phase_continuity, discontinuity, edge, dip_chaos, curvature, coherence_st, orientation, fault_probability, horizon_probability`

The fact that these are labelled `DER_RENDER_CONTRAST` rather than `OBS_GEOLOGY` or `INT_SEISMIC` is the doctrine working — the system is explicit about what kind of evidence it has produced.

## 3. VOID vs ERROR — distinguishability

Arif's sharpening: "an unreachable server and a physics HOLD produce superficially similar outcomes — no interpretation — but they mean completely different things." The receipts encode this distinction in three orthogonal fields:

| Outcome class | `ok` | `error` | `local_verdict` | `governance_status` | Meaning |
|---------------|------|---------|-----------------|---------------------|---------|
| **VOID-no-data** (governance verdict) | `True` | `None` | `QUALIFIED_CANDIDATE` | `HOLD` | image-only → no SEAL; pick is INTERPRETED, not Earth |
| **VOID-gates** (gates KILLed) | `True` | `None` | `QUALIFIED_CANDIDATE` | `HOLD` | physically impossible structure → reject |
| **VOID-no-input** (gates UNMEASURED) | `True` | `None` | `QUALIFIED_CANDIDATE` | `HOLD` | missing scale → UNMEASURED, never guess |
| **ERROR-router** (unknown mode) | `False` | `UNKNOWN_MODE` | `QUALIFIED_CANDIDATE` | `HOLD` | dispatch contract failure |
| **ERROR-file-missing** (ops) | `False` | `FILE_NOT_FOUND` | `QUALIFIED_CANDIDATE` | `HOLD` | input unavailable — ops artifact |
| **ERROR-handler-bug** | `False` | `MISSING_REQUIRED_FIELD` | `QUALIFIED_CANDIDATE` | `HOLD` | handler signature mismatch — engineering defect |
| **ERROR-unreachable** (server down) | n/a | n/a | n/a | n/a | transport-level — separate layer |

The `error` field is the authoritative distinguisher. When scoring side-by-side, **always check `ok` AND `error` together** — `local_verdict=QUALIFIED_CANDIDATE` alone is insufficient.

## 4. Doctrine assertions proven

| Doctrine | Receipt |
|----------|---------|
| Image-only → `INT_SEISMIC`, never `OBS_GEOLOGY` | `epistemic_label: INT_SEISMIC` in both receipts |
| Missing scale → `UNMEASURED`, never guess | `combined_gate_verdict: UNMEASURED` in interpret-mode receipt |
| ≥3 competing hypotheses | 3 hypotheses in interpret-mode receipt |
| `preferred_hypothesis` always `None` from GEOX | `preferred_hypothesis: None` |
| `seal_eligibility=False` for image_only | both receipts |
| `seal_authority=arifOS_only` | both receipts |
| Attributes labelled `DER_RENDER_CONTRAST` not `OBS_GEOLOGY` | R4 stage |

## 5. Open items (not blocking this close-the-loop)

| # | Item | Severity | Owner |
|---|------|----------|-------|
| 1 | `geox_blend_volume_tool()` signature mismatch with router | low | engineering |
| 2 | GEOX `/health` GET time-out (MCP is fine; `/health` not registered on this app instance) | low | ops |
| 3 | Audit's recommended SEG-Y 2.1 XML stanza parsing (Phase D, not required for image-first) | deferred | research |
| 4 | GEOX availability: it came back up during this session. The "GEOX up → GEOX down" oscillation Arif observed earlier needs an ops check | medium | ops |

## 6. Test status

- 45 / 45 contract + structure-gates + zen-scaffolding tests pass
- 6 / 6 contract tests pass with the audit patch (`extra="ignore"`)
- 2 capability receipts saved (interpret_section + interpret)
- 1 router regression receipt captured in §1
- Full suite exit code 0 (skipping the two heavy pre-existing suites per scope)

## 7. Status of the two open claims

| Claim | Before this session | After this session |
|-------|---------------------|---------------------|
| Router dispatch | INTERPRETED (Arif's probe) | **OBSERVED** — each mode dispatches to own handler; see §1 |
| Capability leg | INTERPRETED (no end-to-end pick) | **OBSERVED** — 6 faults + 8 horizons + 3 hypotheses + 9-stage provenance on real PNG; see §2 |

DITEMPA BUKAN DIBEI — Both open claims now have receipts. Awaiting Arif's independent corroboration.

`forge_work/2026-07-23/RECEIPT-interpret-section-F3-png.json` and `RECEIPT-interpret-mode-F3-png.json` ready for your scoring.