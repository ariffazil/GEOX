# GEOX Tool Improvement Specification v1
**Status:** FORGE READY — actionable  
**Date:** 2026-04-19  
**Source:** GEOX_Current_Tools_Improvement_Spec.docx (Arif Fazil)  
**Scope:** Improve existing tools only — no new tools, no new external interfaces  
**Claim state vocabulary:** OBSERVED | COMPUTED | INFERRED | HYPOTHESIS | VOID  

---

## Core Doctrine

> GEOX already has the right backbone. The gap is specification discipline, metadata continuity, rendering fidelity, workflow clarity, and governed handoff between existing capabilities.

Every result must carry:
1. **Claim state** — one of: OBSERVED, COMPUTED, INFERRED, HYPOTHESIS, VOID
2. **Provenance tag** — one of: fixture | uploaded | real_survey | user_text | user_image
3. **Limitation statement** — what is missing, not yet QC'd, or not admissible
4. **Human decision point** — where human judgment becomes mandatory

---

## Tool Improvement Matrix

### 1. `geox_seismic_load_volume`

**Current capability:** Ingests SEG-Y or fixture, indexes dimensions, stores sample interval and bounding range.

**Current gap:** Geometry is loaded but not fully formalized as a downstream contract.

**Required improvements:**

| Field | Requirement |
|-------|-------------|
| `sample_interval_ms` | REQUIRED — must be emitted in ms |
| `axis_identity` | REQUIRED — inline_axis, crossline_axis, time_axis declared |
| `inline_range` | REQUIRED — [first, last, step] |
| `crossline_range` | REQUIRED — [first, last, step] |
| `sample_domain` | REQUIRED — "time_ms" or "depth_m" |
| `byte_order` | REQUIRED — "little_endian" or "big_endian" |
| `bounding_box_3d` | REQUIRED — inline/crossline/time or depth corners |
| `provenance` | REQUIRED — one of: fixture, uploaded, real_survey |
| `intake_claim` | REQUIRED — OBSERVED for real_survey, COMPUTED for fixture |
| `survey_name` | REQUIRED if real_survey |
| `ingestion_hash` | REQUIRED — SHA-256 of file header for provenance |

**Admissibility gate:**
- If `provenance == user_image` or `provenance == user_text` → `claim = HYPOTHESIS`, emit `limitation: "Image/text input cannot substitute for seismic ingestion."`
- If `sample_interval_ms` is None → `claim = VOID`, block downstream attributes

**Output schema:**
```json
{
  "tool": "geox_seismic_load_volume",
  "verdict": "SEAL | HOLD | VOID",
  "claim_state": "OBSERVED | COMPUTED | HYPOTHESIS | VOID",
  "provenance": "fixture | uploaded | real_survey",
  "sample_interval_ms": float,
  "axis_identity": {"inline_axis": "str", "crossline_axis": "str", "time_axis": "str"},
  "inline_range": [int, int, int],
  "crossline_range": [int, int, int],
  "sample_domain": "time_ms | depth_m",
  "byte_order": "little_endian | big_endian",
  "bounding_box_3d": {"inline": [min,max], "crossline": [min,max], "z": [min,max]},
  "survey_name": "str | null",
  "ingestion_hash": "str (SHA-256)",
  "limitations": ["str"],
  "vault_receipt": {...}
}
```

---

### 2. `geox_seismic_render_slice`

**Current capability:** Renders inline/crossline/time slices.

**Current gap:** Display behaviour can drift into presentation mode rather than coordinate-faithful mode.

**Required improvements:**

| Field | Requirement |
|-------|-------------|
| `physical_extents` | REQUIRED — inline/crossline range, time or depth range |
| `axis_labels` | REQUIRED — e.g., "Inline (1-based)", "TWT (ms)" |
| `orientation` | REQUIRED — inline | crossline | time_slice | depth_slice |
| `domain_flag` | REQUIRED — "time" | "depth" | "frequency" |
| `display_mode` | REQUIRED — qualitative_display | interpretation_scale | earth_scale_depth_view |
| `volume_id` | REQUIRED — must reference the ingested volume |
| `slice_location` | REQUIRED — actual inline/crossline/time value |
| `provenance` | REQUIRED — links back to geox_seismic_load_volume |
| `claim_state` | REQUIRED — qualitative_display=INFERRED, interpretation_scale=COMPUTED, earth_scale_depth_view=OBSERVED |

**Render must preserve:**
- Coordinate meaning must survive export
- Slice must carry volume_id, orientation, slice_location, domain, and provenance

**Admissibility gate:**
- If volume_id is not in session state → `claim = VOID`, reject render
- If display_mode is not declared → `hold = True`, request display_mode

---

### 3. `geox_seismic_compute_attribute`

**Current capability:** Computes amplitude, variance, sweetness, coherence, envelope, freq_avg.

**Current gap:** Attribute meaning is not strongly tied to windowing, units, and slice provenance in the output contract.

**Required improvements:**

| Field | Requirement |
|-------|-------------|
| `attribute` | REQUIRED — exact name: amplitude \| variance \| sweetness \| coherence \| envelope \| freq_avg |
| `window_samples` | REQUIRED — window size in samples |
| `window_center_ms` | REQUIRED — window centre in ms |
| `units` | REQUIRED — physical units of output |
| `value_range` | REQUIRED — [min, max] of computed values |
| `statistics` | REQUIRED — {mean, std, p10, p90, count} |
| `source_slice_identity` | REQUIRED — volume_id + orientation + slice_index |
| `claim_state` | REQUIRED — always COMPUTED (attributes are derived) |
| `slice_provenance` | REQUIRED — reference to geox_seismic_load_volume intake |
| `limitation` | REQUIRED — what this attribute can and cannot tell the interpreter |

**Must emit limitation statement, e.g.:**
```
"limitation": "Coherence measures lateral discontinuity. It cannot distinguish fault from facies change without structural control."
```

---

### 4. `geox_well_load_bundle`

**Current capability:** Loads fixture or LAS-backed well context.

**Current gap:** Well identity and log coverage are not yet packaged as a formal witness summary.

**Required improvements:**

| Field | Requirement |
|-------|-------------|
| `loaded_curves` | REQUIRED — list of curve mnemonics successfully loaded |
| `depth_range` | REQUIRED — [top_md_m, bottom_md_m] |
| `missing_channels` | REQUIRED — list of expected curves NOT found in bundle |
| `source_type` | REQUIRED — fixture \| LAS \| user_upload |
| `suitability` | REQUIRED — one of: decision_ready \| screening_only \| void |
| `well_id` | REQUIRED |
| ` permit` | REQUIRED |
| `spud_date` | if available |
| `total_depth_m` | if available |
| `claim_state` | REQUIRED — OBSERVED for LAS, COMPUTED for fixture |
| `qc_prerequisite_met` | bool — true if bundle can proceed to geox_well_qc_logs |

**Admissibility gate:**
- If `suitability == void` → block petrophysics, emit human decision point
- If `missing_channels` includes a required curve → emit `hold = True`

---

### 5. `geox_well_qc_logs`

**Current capability:** Performs log QC.

**Current gap:** QC findings need structured severity and actionability.

**Required improvements:**

| Field | Requirement |
|-------|-------------|
| `qc_overall` | REQUIRED — PASS \| WARN \| FAIL |
| `curve_results` | REQUIRED — per-curve: {mnemonic, status, issues[]} |
| `issues` | REQUIRED — categorized: spike \| gap \| null_zone \| unit_ambiguity \| cross_curve_inconsistency |
| `spike_threshold` | REQUIRED — declared threshold used |
| `gap_threshold_m` | REQUIRED — declared threshold used |
| `null_zone_flags` | REQUIRED — depth intervals with null values |
| `unit_ambiguity_depths` | REQUIRED — depth intervals where GR units unclear |
| `claim_state` | REQUIRED — PASS=OBSERVED, WARN=COMPUTED, FAIL=HYPOTHESIS |

**Per-curve issue schema:**
```json
{
  "mnemonic": "GR",
  "status": "PASS | WARN | FAIL",
  "issues": [
    {"type": "spike", "depth_m": 1850.5, "value": 180.2, "threshold": 150.0},
    {"type": "gap", "depth_m": [2100.0, 2150.0]},
    {"type": "null_zone", "depth_m": [1900.0, 1950.0]},
    {"type": "unit_ambiguity", "depth_m": [2200.0, 2250.0], "suspected_unit": "API | gAPI"}
  ]
}
```

---

### 6. `geox_well_compute_petrophysics`

**Current capability:** Runs petrophysical computations under constrained memory rules.

**Current gap:** Outputs need stronger traceability from inputs to model assumptions.

**Required improvements:**

| Field | Requirement |
|-------|-------------|
| `saturation_model` | REQUIRED — Archie \| Indonesia \| any model name |
| `required_curves_present` | REQUIRED — list of curves used |
| `required_curves_absent` | REQUIRED — list of curves needed but not loaded |
| `applied_defaults` | REQUIRED — dict of which parameters were defaulted |
| `interval_coverage` | REQUIRED — {top_md: float, bottom_md: float, net_m: float} |
| `confidence_limitations` | REQUIRED — narrative of what limits confidence |
| `phi_eff_range` | REQUIRED — [min, max] effective porosity as fraction |
| `sw_range` | REQUIRED — [min, max] water saturation as fraction |
| `claim_state` | REQUIRED — HYPOTHESIS if required curves absent |
| `prerequisite_qc_state` | REQUIRED — reference to geox_well_qc_logs output |

**Degrade gracefully:**
- If required curves are absent → compute with defaults, declare defaults, emit `hold = True`

---

### 7. `geox_time4d_verify_timing`

**Current capability:** Checks trap-charge timing relationships.

**Current gap:** Timing logic can be misread without scenario framing.

**Required improvements:**

| Field | Requirement |
|-------|-------------|
| `verdict` | REQUIRED — SCREENING_PASS \| SCREENING_HOLD \| SCREENING_FAIL |
| `burial_carrier_context` | REQUIRED — what assumed burial path / carrier type was used |
| `assumptions` | REQUIRED — list of specific geological assumptions made |
| `reversal_conditions` | REQUIRED — under what conditions would the conclusion flip? |
| `claim_state` | REQUIRED — HYPOTHESIS for screening, INFERRED if multiple independent lines agree |
| `scenario_used` | REQUIRED — which geological scenario was applied |
| `limitation` | REQUIRED — "Screening outcome only. Not a replacement for structural or stratigraphic proof." |

---

### 8. `geox_prospect_evaluate` + `arifos_judge_prospect`

**Current capability:** Evaluates prospects with governed risk logic.

**Current gap:** Geological state and governance state can blur if not explicitly separated.

**Required improvements:**

| Field | Requirement |
|-------|-------------|
| `geology_summary` | REQUIRED — what is the structural/stratigraphic picture? |
| `ambiguity_summary` | REQUIRED — what are the 3 top ambiguities? |
| `governance_flags` | REQUIRED — {f1_hold, f2_confidence, f13_approval_required} |
| `hold_status` | REQUIRED — 888_HOLD if any threshold breached |
| `human_decision_point` | REQUIRED — the exact point where human judgment is required, declared explicitly |
| `ac_risk_score` | REQUIRED — numeric with threshold reference |
| `claim_state` | REQUIRED — CLAIM if f2_confidence >= 0.99, PLAUSIBLE if >= 0.65, HYPOTHESIS otherwise |
| `evidence_chain_complete` | bool — true if all 6 workflow stages have been completed |

---

## Workflow Contract — Stage Gates

```
Stage A: Intake → geox_seismic_load_volume OR geox_well_load_bundle
         Gate: claim_state must be OBSERVED or COMPUTED before proceeding

Stage B: QC → geox_well_qc_logs + metadata from Stage A
         Gate: qc_overall must be PASS or WARN before petrophysics

Stage C: Seismic interpretation → geox_seismic_render_slice + geox_seismic_compute_attribute
         Gate: volume_id must be from Stage A, display_mode must be declared

Stage D: Rock and reservoir → geox_well_compute_petrophysics
         Gate: prerequisite curves present, qc_prerequisite_met == true

Stage E: Petroleum system timing → geox_time4d_verify_timing
         Gate: screening only, not final verdict

Stage F: Governed prospect review → geox_prospect_evaluate + arifos_judge_prospect
         Gate: all prior stages complete, 888_HOLD if f13_approval_required
```

---

## Behavioural Non-Negotiables

1. **No image-only as seismic** — image intake must emit HYPOTHESIS, not imply attribute computation
2. **No coordinate loss** — rendered slices must carry orientation, domain, and scale
3. **No anonymous attributes** — every attribute panel must show name, slice identity, provenance
4. **No score without uncertainty** — governance outputs must expose ambiguity and hold conditions
5. **No silent failure** — well workflows must declare missing curves, not proceed past them
6. **No discovery-as-reasoning** — metadata tools remain descriptive, non-interpretive

---

## Implementation Priority

| Priority | Tools | Action |
|----------|-------|--------|
| P1 | geox_seismic_load_volume | Add missing required fields to output schema |
| P1 | geox_well_load_bundle | Add witness summary fields |
| P1 | geox_well_qc_logs | Add structured severity + curve-level issues |
| P2 | geox_seismic_compute_attribute | Add window metadata + limitation statement |
| P2 | geox_prospect_evaluate | Separate geological vs governance state |
| P3 | geox_seismic_render_slice | Declare display_mode + physical extents |
| P3 | geox_time4d_verify_timing | Add reversal_conditions + scenario framing |

---

## Verification Checklist

After implementation, each tool must pass:

- [ ] Output has no missing required fields
- [ ] Provenance tag is always present and accurate
- [ ] Claim state is correctly classified
- [ ] Limitation statement is present for every computed/hypothesized output
- [ ] Human decision point is exposed where required
- [ ] All stage gates enforce the workflow contract
- [ ] VAULT999 receipt is emitted for every tool call

---

*DITEMPA BUKAN DIBERI — Forged, Not Given*
