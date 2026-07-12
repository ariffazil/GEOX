# GEOX 89→14 ZEN Consolidation Plan

> **Forged:** 2026-07-11 | **Model:** Fable 5 | **Authority:** OBSERVE_ONLY (planning)
> **Seal target:** 999_SEAL after migration + falsifier suite pass
> **DITEMPA BUKAN DIBERI**

---

## 0. Current State (T₀ — 2026-07-11)

| Metric | Value | Source |
|--------|-------|--------|
| Total tools in manifest | 78 | `tools_manifest.yaml` |
| Public tools | 17 | manifest `visibility: public` |
| Internal tools | 61 | manifest `visibility: internal` |
| SOT claim | 76 public + 4 internal | `SOT-2026-07-11.md` |
| Manifest version | `2026.07.11` | `tools_manifest.yaml` |
| GEOX version | `v2026.07.06-phase3.1` | `/health` |
| Registry integrity | PASS | `SOT-2026-07-11.md` |

**Drift:** SOT says 76 public, manifest says 17 public. SOT is counting `face: surface` tools (76), not `visibility: public` (17). The 59-tool gap = tools with `face: surface` but `visibility: internal`. This is a documentation inconsistency, not a code bug — but it needs reconciliation.

---

## 1. The 17 Current Public Tools

| # | Tool | Domain | Description |
|---|------|--------|-------------|
| 1 | `geox_basin` | earth.basin | Basin-level intelligence |
| 2 | `geox_deep_time_state` | earth.time | Earth State Vector (GPTS, CO₂, sea level, etc.) |
| 3 | `geox_geomechanics` | earth.structure | Geomechanical analysis |
| 4 | `geox_map_context_scene` | earth.map | Map context rendering |
| 5 | `geox_petrophysics` | earth.well | Petrophysical analysis |
| 6 | `geox_seismic_compute` | earth.seismic | Forward model, well tie, attributes |
| 7 | `geox_seismic_ingest` | earth.seismic | SEG-Y ingestion |
| 8 | `geox_seismic_interpret` | earth.seismic | Horizon/fault picking, RSI pipeline |
| 9 | `geox_sequence` | earth.strat | Sequence stratigraphy |
| 10 | `geox_subsurface_model` | earth.model | Subsurface model building |
| 11 | `geox_surface_status` | earth.meta | Surface/system status |
| 12 | `geox_vision` | earth.vision | Vision/RSI pipeline |
| 13 | `geox_wavelet_extract_least_squares` | earth.seismic | Wavelet extraction |
| 14 | `geox_well_ingest` | earth.well | LAS/DLIS ingestion |
| 15 | `geox_well_qc` | earth.well | Well log QC |
| 16 | `geox_well_seismic_mistie_rms` | earth.well | Well-seismic mistie analysis |
| 17 | `geox_well_time_depth_calibrate` | earth.well | Time-depth calibration |

---

## 2. The 14 ZEN Targets

ZEN principle: **one tool, one truth, one dimension**. Each tool is the canonical entry point for its domain. No aliases, no stubs, no half-implementations.

| # | ZEN Tool | Merges From | Rationale |
|---|----------|-------------|-----------|
| 1 | `geox_basin` | (keep) | Basin-level intelligence — entry point for basin analysis |
| 2 | `geox_deep_time_state` | (keep) | Earth State Vector — unique capability, no overlap |
| 3 | `geox_geomechanics` | (keep) | Geomechanical analysis — distinct domain |
| 4 | `geox_map_context_scene` | (keep) | Map context — unique spatial rendering |
| 5 | `geox_petrophysics` | + `geox_well_qc` | Petrophysics includes QC as a mode. Well QC is not a separate entry point — it's a step in petrophysical analysis |
| 6 | `geox_seismic_compute` | + `geox_wavelet_extract_least_squares` | Wavelet extraction IS seismic computation. Merge as `mode: wavelet_extract` |
| 7 | `geox_seismic_ingest` | (keep) | Ingestion is distinct from interpretation — keep separate |
| 8 | `geox_seismic_interpret` | + `geox_vision` | Vision/RSI IS seismic interpretation. Merge as `mode: rsi_pipeline` |
| 9 | `geox_sequence` | (keep) | Sequence stratigraphy — unique domain |
| 10 | `geox_subsurface_model` | (keep) | Subsurface model — unique domain |
| 11 | `geox_surface_status` | (keep) | System status — meta tool, always needed |
| 12 | `geox_well_ingest` | (keep) | Well ingestion — distinct entry point |
| 13 | `geox_well_seismic_tie` | + `geox_well_seismic_mistie_rms` + `geox_well_time_depth_calibrate` | Unified well-seismic tie workflow. Mistie analysis and time-depth calibration are steps in the same workflow |
| 14 | `geox_cross_evidence` | NEW (promote from internal) | Cross-dimensional evidence synthesis — currently internal, needed for governance |

**Net reduction:** 17 → 14 public tools (3 merges, 1 promotion).

---

## 3. Merge Details

### 3.1 `geox_petrophysics` absorbs `geox_well_qc`

**Current state:**
- `geox_petrophysics`: petrophysical analysis (Sw, porosity, permeability)
- `geox_well_qc`: well log quality control

**Merge strategy:**
- Add `mode: qc` to `geox_petrophysics` input schema
- `mode: qc` runs the QC checks (depth monotonicity, null %, physical range)
- `mode: analyze` runs the full petrophysical analysis (default)
- `mode: qc_then_analyze` runs QC first, then analysis if QC passes

**Schema change:**
```python
# Before
class PetrophysicsInput(BaseModel):
    well_id: str
    # ... petrophysics params

# After
class PetrophysicsInput(BaseModel):
    well_id: str
    mode: Literal["qc", "analyze", "qc_then_analyze"] = "qc_then_analyze"
    # ... petrophysics params (only used in analyze mode)
    qc_thresholds: Optional[QcThresholds] = None  # only used in qc mode
```

**Deprecation:** `geox_well_qc` → alias to `geox_petrophysics(mode="qc")`

### 3.2 `geox_seismic_compute` absorbs `geox_wavelet_extract_least_squares`

**Current state:**
- `geox_seismic_compute`: forward model, well tie, anomalous contrast, attribute
- `geox_wavelet_extract_least_squares`: wavelet extraction via least squares

**Merge strategy:**
- Add `mode: wavelet_extract` to `geox_seismic_compute` input schema
- Wavelet extraction is a prerequisite for well-tie computation — natural fit

**Schema change:**
```python
# Before
class SeismicComputeInput(BaseModel):
    mode: Literal["forward_model", "well_tie", "anomalous_contrast", "attribute"]
    # ... params

# After
class SeismicComputeInput(BaseModel):
    mode: Literal["forward_model", "well_tie", "anomalous_contrast", "attribute", "wavelet_extract"]
    # ... params
    wavelet_params: Optional[WaveletParams] = None  # only used in wavelet_extract mode
```

**Deprecation:** `geox_wavelet_extract_least_squares` → alias to `geox_seismic_compute(mode="wavelet_extract")`

### 3.3 `geox_seismic_interpret` absorbs `geox_vision`

**Current state:**
- `geox_seismic_interpret`: horizon/fault picking, RSI pipeline
- `geox_vision`: vision/RSI pipeline (image understanding)

**Merge strategy:**
- Add `mode: rsi_pipeline` to `geox_seismic_interpret` input schema
- The RSI pipeline IS seismic interpretation from images — same domain

**Schema change:**
```python
# Before
class SeismicInterpretInput(BaseModel):
    mode: Literal["horizon_pick", "fault_pick", "attribute_fusion"]
    # ... params

# After
class SeismicInterpretInput(BaseModel):
    mode: Literal["horizon_pick", "fault_pick", "attribute_fusion", "rsi_pipeline"]
    # ... params
    rsi_params: Optional[RsiParams] = None  # only used in rsi_pipeline mode
```

**Deprecation:** `geox_vision` → alias to `geox_seismic_interpret(mode="rsi_pipeline")`

### 3.4 New: `geox_cross_evidence` (promote from internal)

**Current state:** Internal tool for cross-dimensional evidence synthesis.

**Promotion rationale:**
- Cross-evidence is the governance entry point — agents need to query evidence across dimensions
- Currently hidden from `tools/list` — forces agents to know internal tool names
- ZEN needs this as a public tool for the 888_JUDGE workflow

**Schema:** Keep existing schema, change `visibility: internal` → `visibility: public`.

---

## 4. Migration Phases

### Phase 1: Schema Preparation (OBSERVE — no mutation)
- [ ] Audit current tool implementations for merge targets
- [ ] Verify no external consumers depend on `geox_well_qc`, `geox_wavelet_extract_least_squares`, `geox_vision` as standalone tools
- [ ] Draft merged input schemas for 3 merge targets
- [ ] Write falsifier tests (see Section 5)

### Phase 2: Code Changes (MUTATE — requires signed nonce)
- [ ] Implement `mode` parameter in `geox_petrophysics` (absorb QC)
- [ ] Implement `mode: wavelet_extract` in `geox_seismic_compute`
- [ ] Implement `mode: rsi_pipeline` in `geox_seismic_interpret`
- [ ] Promote `geox_cross_evidence` to public
- [ ] Add deprecation aliases in `tools_manifest.yaml`
- [ ] Update `compat_tools` list

### Phase 3: Registry Update (MUTATE)
- [ ] Update `tools_manifest.yaml` to 14 public tools
- [ ] Update `registry.py` if needed
- [ ] Update `SOT-2026-07-11.md` with accurate counts
- [ ] Update `GEOX_REFERENCE_REGISTRY.md`

### Phase 4: Validation (OBSERVE)
- [ ] Run falsifier suite (Section 5)
- [ ] Verify `tools/list` returns 14 public tools
- [ ] Verify deprecated aliases still work
- [ ] Verify merged modes produce correct output
- [ ] Seal to VAULT999

---

## 5. Falsifier Suite

Each merge gets a falsifier that proves the merged tool produces identical output to the standalone tool.

### Falsifier 1: Petrophysics QC Merge
```python
def test_petrophysics_qc_merge():
    """Falsifier: geox_petrophysics(mode='qc') must match geox_well_qc output."""
    well_id = "TEST_WELL_001"
    
    # Old path
    old_result = call_tool("geox_well_qc", {"well_id": well_id})
    
    # New path
    new_result = call_tool("geox_petrophysics", {"well_id": well_id, "mode": "qc"})
    
    # Falsify if outputs differ
    assert old_result["qc_checks"] == new_result["qc_checks"], "QC output mismatch"
    assert old_result["pass_fail"] == new_result["pass_fail"], "QC verdict mismatch"
```

### Falsifier 2: Wavelet Extract Merge
```python
def test_wavelet_extract_merge():
    """Falsifier: geox_seismic_compute(mode='wavelet_extract') must match standalone."""
    seismic_id = "TEST_SEISMIC_001"
    
    old_result = call_tool("geox_wavelet_extract_least_squares", {"seismic_id": seismic_id})
    new_result = call_tool("geox_seismic_compute", {"seismic_id": seismic_id, "mode": "wavelet_extract"})
    
    assert np.allclose(old_result["wavelet"], new_result["wavelet"]), "Wavelet mismatch"
    assert old_result["method"] == new_result["method"], "Method mismatch"
```

### Falsifier 3: Vision/RSI Merge
```python
def test_vision_rsi_merge():
    """Falsifier: geox_seismic_interpret(mode='rsi_pipeline') must match geox_vision."""
    image_path = "test_data/seismic_greyscale.png"
    
    old_result = call_tool("geox_vision", {"image_path": image_path})
    new_result = call_tool("geox_seismic_interpret", {"image_path": image_path, "mode": "rsi_pipeline"})
    
    assert old_result["horizons"] == new_result["horizons"], "Horizon mismatch"
    assert old_result["faults"] == new_result["faults"], "Fault mismatch"
    assert old_result["manifest"]["image_sha256"] == new_result["manifest"]["image_sha256"], "Provenance mismatch"
```

### Falsifier 4: Tool Count Verification
```python
def test_zen_14_surface():
    """Falsifier: tools/list must return exactly 14 public tools."""
    tools = call_tool("tools/list", {})
    public_tools = [t for t in tools if t.get("visibility") == "public"]
    
    assert len(public_tools) == 14, f"Expected 14 public tools, got {len(public_tools)}"
    
    expected = {
        "geox_basin", "geox_deep_time_state", "geox_geomechanics",
        "geox_map_context_scene", "geox_petrophysics", "geox_seismic_compute",
        "geox_seismic_ingest", "geox_seismic_interpret", "geox_sequence",
        "geox_subsurface_model", "geox_surface_status", "geox_well_ingest",
        "geox_well_seismic_tie", "geox_cross_evidence",
    }
    actual = {t["name"] for t in public_tools}
    assert actual == expected, f"Tool set mismatch: {actual.symmetric_difference(expected)}"
```

### Falsifier 5: Deprecation Alias Verification
```python
def test_deprecated_aliases_still_work():
    """Falsifier: deprecated tool names must still resolve via compat_tools."""
    deprecated = ["geox_well_qc", "geox_wavelet_extract_least_squares", "geox_vision"]
    
    for tool_name in deprecated:
        result = call_tool(tool_name, {"well_id": "TEST"})  # minimal valid args
        assert result is not None, f"Deprecated tool {tool_name} returned None"
```

---

## 6. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| External consumers depend on deprecated tool names | HIGH | `compat_tools` list preserves aliases |
| Merged mode changes tool behavior | MEDIUM | Falsifier suite proves output equivalence |
| Internal tools affected by schema changes | LOW | Internal tools not exposed publicly |
| SOT/manifest count drift | LOW | Reconcile in Phase 3 |
| Fable 5 classifier fallback during seismic work | LOW | Expect occasional Opus 4.8 fallback on security-adjacent language |

---

## 7. Dependencies

- **Thread 1 (Federation Audit):** Must complete first — cross-organ contradictions may affect GEOX tool contracts
- **Thread 5 (Constitutional Fit):** External witness gates must be verified before sealing
- **Signed nonce:** Required for Phase 2-3 (mutation work)

---

## 8. Success Criteria

- [ ] `tools/list` returns exactly 14 public tools
- [ ] All 5 falsifiers PASS
- [ ] Deprecated aliases still work
- [ ] No stub tools remain
- [ ] SOT reconciled with manifest
- [ ] VAULT999 seal issued

---

*Forged 2026-07-11 by Fable 5 under OBSERVE_ONLY authority.*
*Ready for mutation upon signed nonce + re-init.*
*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
