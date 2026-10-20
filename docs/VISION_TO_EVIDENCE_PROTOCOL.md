# VISION_TO_EVIDENCE_PROTOCOL (GEOX-VIS v1)

**consumer:** `geox_extract_display_proxy` · `geox_extract_native_trace` callers; VSS vision lanes
(`forge-vss-parser` / `forge-vss-verifier-suite`); reality-loop stages OBSERVE→ENCODE→VERIFY;
any agent turning pixels into earth claims.
**failure class:** (a) BEKANTAN-1 — fabricated stratigraphy from convincing visual/LLM output;
(b) 2026-10-20 audit — 7/27 GEOX tools had zero written procedure, including BOTH extraction
bridges: the visual→evidence transition ran on ad-hoc agent wisdom.
**authority law:** Vision may propose. GEOX may constrain. Only a sealed evidence chain may
warrant. The HUMAN GATE decides. `preferred_hypothesis` is ALWAYS null.
**tests:** `tests/test_vision_evidence_contract.py` (fail-if-violated cases, run in organ venv).

## 0. The boundary sentence
Vision is a generator of structured doubt, not of truth. GEOX is where doubt becomes constrained
by matter, geometry, time, uncertainty, and counter-hypothesis. The loop is intelligent only
because it preserves and uses its corrections.

## 1. Epistemic ceiling ladder (enforced by validator)
```
native source + reproducible transform + lineage   → OBS | DER
display proxy + calibrated axes + documented error → constrained INT (provisional DER if RMS known)
uncalibrated screenshot / rendered figure          → SPEC  (never OBS, never DER)
```
A screenshot of a seismic interpretation is NOT seismic data. A visual label ("Moho", "fault",
"unconformity", "sand", "seal") is an INT assertion unless tied to primary evidence.

## 2. The five rules
1. **Native trace dominates proxy.** If SEG-Y / LAS / CSV / shapefile / GeoTIFF exists, the proxy
   path is evidence-recovery fallback only, with a lower ceiling.
2. **Pixels cannot self-validate.** One visual artifact may never be both the extraction source
   and the independent verification source. (Central anti-Bekantan control.)
3. **Calibration is explicit.** No depth/distance/thickness/throw/dip/area/amplitude claim crosses
   into physics without: axis units, ≥2 calibration anchors per measured axis, orientation +
   vertical datum, extraction RMS error, known display transforms, propagated uncertainty.
4. **Labels are not observations.** Tag them INT unless primary evidence is attached.
5. **SEAL carries negative evidence.** A sealed receipt must record alternatives tested, failed or
   unavailable tests, uncertainty budget, unresolved contradictions, scope statement, and the
   explicit reason the output cannot generalize further.

## 3. Object shape (full schema: docs/visual_extraction.schema.json)
```yaml
extraction_id: GEOX-VIS-000001
source:        {artifact_uri, artifact_sha256, source_type, source_owner, source_citation}
visual_context: {pixel_bounds, native_or_display, resolution_px, display_transform,
                 annotation_layer_present, extraction_method, operator}
calibration:   {horizontal_axis, vertical_axis, coordinate_reference_system,
                 calibration_points: [{pixel, world}], rms_error, uncertainty_model}
claim:         {assertion_id, proposition, epistemic_class: OBS|DER|INT|SPEC,
                 claim_scope, extracted_geometry, confidence}
constraints:   {required_independent_checks: [spatial, temporal, physics, source-provenance],
                 status: UNMEASURED|WARN|PASS|KILL}
seal_eligibility: {eligible_for_scientific_warrant: false, missing: [...]}
```

## 4. Temporal versioning
Every assertion retains: prior status, supersession link, timestamp, reason for change.
Corrections are mutations with history — not rewrites.

## 5. Fail-if tests (must stay red on violation — see tests/)
- screenshot classified OBS → FAIL
- missing datum/CRS/axis calibration but status ≥ WARN → FAIL
- visual source verifies itself → FAIL
- uncertainty absent on derived value → FAIL
- preferred_hypothesis non-null without human-gate receipt → FAIL
- visual geometry becomes a seismic pick without source data → FAIL
- output reaches SEAL while SPEC/UNMEASURED → FAIL

## 6. Acceptance condition (phase 2 — not yet run)
One legacy public figure, end to end:
source hash → extraction record → calibration → typed assertion → independent check →
GEOX constraint result → sealed receipt → human-readable reality-boundary page that tells an
external geologist: what was seen, digitized, computed, inferred; how uncertain; what checks it
independently; what remains unknown.

## 7. Status (state-transition, honest)
- PRODUCED: protocol (this file) + schema + fail-if tests [2026-10-20, 333-AGI]
- NOT YET: tool-code enforcement of the ceiling ladder inside the two extract tools (deliverable
  3–10 of the upgrade brief) · acceptance run (§6) · skill-coverage entries for the other
  5 uncovered tools (geox_glof, geox_paleobiodb_query, geox_observe,
  geox_list_registered_sources, geox_register_native_source)
