# GEOX Production Gap Tracker — Conveyor Belt Blueprint

> **Created:** 2026-07-02 | **Updated:** 2026-07-02
> **Owner:** Arif (F13 SOVEREIGN) | **Executor:** OpenCode (FORGE)
> **Source:** ChatGPT architecture audit + OpenCode live-state verification
> **Verdict:** YELLOW (72%) → target GREEN (95%)

This is the single-source tracker for GEOX production readiness.
Each layer is a station on the conveyor belt. Data enters at Layer A,
exits at Layer H as a structured, challengeable, auditable claim.

No data reaches arifOS without passing through every station.

---

## Layer A: Data Ingest

**Mission:** Turn raw earth files into canonical artifact records.

| Format | Status | Tool | Notes |
|--------|--------|------|-------|
| LAS | ✅ LIVE | `geox_well_ingest` | Core well log format |
| DLIS | ❌ MISSING | — | Digital Log Interchange Standard |
| LIS | ❌ MISSING | — | Older Schlumberger format |
| CSV logs | ✅ LIVE | `geox_well_ingest` (mode) | Via ingest module |
| SEG-Y | ✅ LIVE | `geox_seismic_ingest` | Seismic volumes |
| SEG-D | ❌ MISSING | — | Field seismic format |
| GeoTIFF | ❌ MISSING | — | Raster images |
| GeoJSON | ✅ LIVE | `geox_map_layers_list` | Map layers |
| Shapefile | ❌ MISSING | — | Standard GIS vector |
| KML/KMZ | ❌ MISSING | — | Google Earth format |
| NetCDF | ❌ MISSING | — | Climate/grids |
| Zarr | ❌ MISSING | — | Cloud-native arrays |
| Petrel exports | ❌ MISSING | — | Schlumberger E&P |
| Kingdom exports | ❌ MISSING | — | IHS Markit E&P |
| RESQML | ❌ MISSING | — | RESQML standard |
| WITSML | ❌ MISSING | — | Wellsite data |
| Core photos | ❌ MISSING | — | Image ingest |
| Thin-section | ❌ MISSING | — | Microscopy images |
| XRD/XRF/ICP-MS | ❌ MISSING | — | Geochemistry tables |
| Well reports | ❌ MISSING | — | PDF/document ingest |
| Mud logs | ❌ MISSING | — | Cuttings descriptions |
| Completion reports | ❌ MISSING | — | Well completion data |
| Production data | ❌ MISSING | — | Production time series |
| Pressure data | ❌ MISSING | — | DST/RFT pressure |
| Temperature data | ❌ MISSING | — | BHT/temperature logs |
| DEM/LiDAR | ❌ MISSING | — | Elevation data |

**Coverage:** 4/26 formats (15%)

**Required artifact record per ingest:**
```
artifact_id: GEOX-ART-...
source_type: LAS | SEGY | GEOTIFF | REPORT | IMAGE | TABLE
source_uri: ...
checksum: sha256:...
coordinate_reference_system: ...
depth_reference: ...
unit_system: ...
null_policy: ...
ingest_time: ...
provenance: ...
quality_status: PASS | WARN | FAIL
```

**Priority:** HIGH — everything downstream depends on clean ingest.
**Effort:** Medium per format (GDAL/OGR wrapper covers many).

---

## Layer B: Quality Control

**Mission:** No earth data enters interpretation until checked.

| QC Check | Status | Location | Notes |
|----------|--------|----------|-------|
| Null density | ⚠️ PER-TOOL | `geox_well_qc` | Per-curve, not unified |
| Curve coverage | ⚠️ PER-TOOL | `geox_well_qc` | Checks which curves exist |
| Depth step irregularity | ⚠️ PER-TOOL | `geox_well_qc` | |
| Unit sanity | ❌ MISSING | — | No unit validation |
| Duplicate depths | ⚠️ PER-TOOL | `geox_well_qc` | |
| Depth gaps | ⚠️ PER-TOOL | `geox_well_qc` | |
| Spikes | ❌ MISSING | — | No spike detection |
| Tool calibration risk | ❌ MISSING | — | |
| Curve alias resolution | ❌ MISSING | — | |
| Coordinate validity | ⚠️ PER-TOOL | `geox_atlas` | Land/water only |
| Datum mismatch | ❌ MISSING | — | |
| CRS mismatch | ❌ MISSING | — | |
| Well trajectory mismatch | ✅ LIVE | `geox_well_desurvey` | |
| Seismic sample rate | ⚠️ PER-TOOL | `geox_seismic_ingest` | |
| SEG-Y header consistency | ⚠️ PER-TOOL | `geox_seismic_ingest` | |
| Trace count consistency | ⚠️ PER-TOOL | `geox_seismic_ingest` | |
| Image georeference | ❌ MISSING | — | |

**Gap:** No unified `geox_qc_run` that gates all downstream compute.
Each tool does its own QC. No canonical PASS/WARN/FAIL record.

**Required output:**
```yaml
qc_status: PASS | WARN | FAIL
confidence: high | medium | low
fatal_issues: [...]
warnings: [...]
usable_for: [...]
not_usable_for: [...]
```

**Priority:** HIGH — QC gate prevents garbage-in-garbage-out.
**Effort:** Medium — wrap existing per-tool QC into unified runner.

---

## Layer C: Domain Compute

**Mission:** Canonical compute families. Bounded transforms, no AI.

### Petrophysics

| Tool | Status | Notes |
|------|--------|-------|
| `geox_petrophysics` (unified) | ✅ LIVE | Mode-based: SP, GR, density-neutron, resistivity |
| `geox_gr_vshale` | ⚠️ INLINE | Inside unified tool |
| `geox_porosity_density` | ⚠️ INLINE | Inside unified tool |
| `geox_porosity_neutron_density` | ⚠️ INLINE | Inside unified tool |
| `geox_porosity_sonic` | ❌ MISSING | Wyllie/time-average |
| `geox_rw_temperature_correct` | ❌ MISSING | Rw correction |
| `geox_archie_sw` | ❌ MISSING | Archie water saturation |
| `geox_dual_water_sw` | ❌ MISSING | Dual-water model |
| `geox_indonesia_sw` | ❌ MISSING | Indonesia equation |
| `geox_net_pay_cutoff` | ❌ MISSING | Net pay from cutoffs |
| `geox_fluid_contact_pick` | ❌ MISSING | OWC/GOC picking |
| `geox_pressure_gradient` | ❌ MISSING | Pressure analysis |
| `geox_pay_summary` | ❌ MISSING | Pay zone summary |

### Seismic

| Tool | Status | Notes |
|------|--------|-------|
| `geox_seismic_ingest` | ✅ LIVE | SEG-Y read |
| `geox_seismic_compute` | ✅ LIVE | Synthetic, well-tie, attributes |
| `geox_seismic_interpret` | ✅ LIVE | Horizon contrast, faults, frames |
| `geox_segy_ingest` | ⚠️ INLINE | Via seismic_ingest |
| `geox_volume_qc` | ❌ MISSING | Volume QC |
| `geox_attribute_amplitude` | ⚠️ INLINE | Via seismic_compute |
| `geox_attribute_coherence` | ❌ MISSING | |
| `geox_attribute_variance` | ❌ MISSING | |
| `geox_attribute_sweetness` | ❌ MISSING | |
| `geox_frequency_decomposition` | ❌ MISSING | |
| `geox_rgb_blend` | ❌ MISSING | |
| `geox_horizon_pick` | ❌ MISSING | Auto/semi-auto horizon picking |
| `geox_fault_stick_ingest` | ❌ MISSING | |
| `geox_fault_surface_build` | ❌ MISSING | |
| `geox_time_depth_convert` | ❌ MISSING | Checkshot/VSP anchoring |

### Structural Geology

| Tool | Status | Notes |
|------|--------|-------|
| `geox_geomechanics` | ✅ LIVE | K, G, E, ν, AI |
| `geox_fault_interpret` | ⚠️ INLINE | Via seismic_interpret |
| `geox_throw_estimate` | ❌ MISSING | |
| `geox_dip_azimuth` | ❌ MISSING | |
| `geox_fracture_density` | ❌ MISSING | |
| `geox_stress_regime` | ❌ MISSING | |
| `geox_trap_closure` | ❌ MISSING | |
| `geox_spill_point` | ❌ MISSING | |
| `geox_column_height` | ❌ MISSING | |

### Stratigraphy

| Tool | Status | Notes |
|------|--------|-------|
| `geox_sequence` | ✅ LIVE | Sequence stratigraphy, correlation |
| `geox_sequence_pick` | ⚠️ INLINE | Via sequence tool |
| `geox_systems_tract_classify` | ❌ MISSING | |
| `geox_facies_interpret` | ❌ MISSING | |
| `geox_channel_detect` | ❌ MISSING | |
| `geox_lobe_detect` | ❌ MISSING | |
| `geox_depositional_environment` | ❌ MISSING | |
| `geox_correlation_panel` | ❌ MISSING | |

### Basin

| Tool | Status | Notes |
|------|--------|-------|
| `geox_basin` | ✅ LIVE | Profile, resolve, macrostrat, deep_time |
| `geox_deep_time_state` | ✅ LIVE | Earth state vectors |
| `geox_subsurface_model` | ✅ LIVE | Joint inversion, gravity/mag, MT |

**Compute coverage:** ~30% of requested families.

**Priority:** MEDIUM — existing tools cover core workflows.
**Effort:** Large — each new tool needs bounded transforms + tests.

---

## Layer D: Claim Engine

**Mission:** Every GEOX output is a structured claim, not loose prose.

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| Claim creation | ✅ LIVE | `geox_egs_claim_create` | Typed claims with confidence |
| Claim types | ✅ LIVE | EGS models | reservoir, structural, stratigraphic |
| Truth classes | ✅ LIVE | EGS | FACT, INTERPRETATION, SPECULATION |
| Evidence binding | ✅ LIVE | `geox_egs_evidence_attach` | |
| Method binding | ⚠️ PARTIAL | — | No explicit method_ids field |
| Uncertainty (p10/p50/p90) | ⚠️ PARTIAL | EGS | Available but not enforced |
| Limitations field | ⚠️ PARTIAL | — | Export warnings, not per-claim |
| Alternatives field | ⚠️ PARTIAL | `geox_egs_scenario_audit` | Not mandatory |
| Authority field | ✅ LIVE | EGS | Agent authority tracking |
| State machine | ✅ LIVE | `claim_state_machine.yaml` | DRAFT → CHALLENGED → VALIDATED → SEALED |

**Gap:** Claims work but limitations, alternatives, and uncertainty are not mandatory fields.

**Priority:** HIGH — this is the core output format.
**Effort:** Low — add required fields to claim schema.

---

## Layer E: Challenge Engine

**Mission:** Every major claim must be challenged by at least one alternative.

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| Claim challenge | ✅ LIVE | `geox_egs_claim_challenge` | Can challenge any claim |
| Evidence attach | ✅ LIVE | `geox_egs_evidence_attach` | Supporting + contradictory |
| Evidence reason | ✅ LIVE | `geox_egs_evidence_reason` | Synthesize/grade evidence |
| Scenario audit | ✅ LIVE | `geox_egs_scenario_audit` | Alternative interpretations |
| **Mandatory challenge gate** | ❌ MISSING | — | Challenge NOT required before HIGH/CRITICAL claims |
| Counter-evidence requirement | ❌ MISSING | — | No forced counter-evidence for decisions |

**Gap:** Challenge is available but not mandatory. A claim can go from DRAFT to SEALED without challenge.

**Fix:** Add `challenge_required: true` to HIGH/CRITICAL claim creation.
**Priority:** HIGH — civilizational safety.
**Effort:** Medium — add gate logic to EGS claim state machine.

---

## Layer F: Uncertainty Layer

**Mission:** Make uncertainty visible on every output.

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| Measurement uncertainty | ⚠️ PARTIAL | EGS | Per-entity, not per-tool |
| Depth uncertainty | ⚠️ PARTIAL | `geox_well_desurvey` | TVD uncertainty only |
| Coordinate uncertainty | ❌ MISSING | — | |
| Unit uncertainty | ❌ MISSING | — | |
| Method uncertainty | ❌ MISSING | — | |
| Interpreter uncertainty | ❌ MISSING | — | |
| Model uncertainty | ⚠️ PARTIAL | `geox_subsurface_model` | Inversion uncertainty |
| Economic sensitivity | ⚠️ PARTIAL | WEALTH bridge | Not in GEOX directly |
| Data absence uncertainty | ❌ MISSING | — | "Unknown because not measured" |
| **Enforcement** | ❌ MISSING | — | Uncertainty is optional, not structural |

**Gap:** Uncertainty tracking exists in EGS but is not enforced on tool outputs.
A tool can return results without any uncertainty field.

**Fix:** Add `uncertainty_required: true` to COMPUTE-class tools. Empty uncertainty = WARN.
**Priority:** MEDIUM.
**Effort:** Medium.

---

## Layer G: Reproducibility Layer

**Mission:** Every output must be reproducible from declared inputs.

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| PROV sidecar | ✅ LIVE | `earth_map.py:_build_prov_sidecar` | On exports only |
| STAC catalog | ✅ LIVE | `earth_map.py:_build_stac_catalog` | On exports only |
| Artifact envelope | ✅ CONTRACT | `contracts/artifact_envelope.py` | Not yet stamped on tools |
| Checksum recording | ✅ PARTIAL | Export packages | Not on individual tool returns |
| Parameter set recording | ❌ MISSING | — | No parameter_set field |
| Tool version recording | ✅ PARTIAL | `_envelope` contract | Not yet integrated |
| Random seed recording | ❌ MISSING | — | |
| Runtime environment | ❌ MISSING | — | |
| `geox_receipt_create` | ❌ MISSING | — | Unified receipt wrapper |

**Gap:** PROV sidecar exists for exports. Artifact envelope contract exists.
Neither is stamped on the 35 tool returns.

**Fix:** Integrate `stamp_envelope()` into all tool returns. 1 line per tool.
**Priority:** HIGH — reproducibility is the certification backbone.
**Effort:** Low — mechanical integration.

---

## Layer H: Safety & Authority

**Mission:** Classify every action by risk. Block unsafe actions.

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| 888_HOLD on claims | ✅ LIVE | `geox_claim`, `geox_prospect` | require 888_HOLD |
| Truth class gating | ✅ LIVE | Map tools | DECISION_SUPPORT excluded from context |
| Affordance contracts | ✅ LIVE | `geox_surface_status` | action_class, mutation, irreversibility |
| Risk bands (GREEN→BLACK) | ❌ MISSING | — | No risk color classification |
| Forbidden claims list | ❌ MISSING | — | No BLOCKED_TERMS for "proven reserves" etc. |
| Evidence floor classifier | ❌ MISSING | — | L1/L2/L3/L4 not on outputs |
| BLACK actions (illegal/fraud) | ❌ MISSING | — | No BLACK classification |
| Dry-run mode | ❌ MISSING | — | No preview before mutation |

**Gap:** Governance exists via 888_HOLD and affordances but no color-coded risk bands,
no forbidden-claims list, no evidence floors, no dry-run.

**Priority:** HIGH — civilizational safety.
**Effort:** Low (risk bands) to Medium (forbidden-claims classifier).

---

## Layer Z: Protocol & Integration

**Mission:** MCP compliance, A2A readiness, CI/CD health.

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| MCP initialize | ✅ PASS | `:8081/mcp` | JSON-RPC 2025-11-25 |
| tools/list | ✅ PASS | 33 tools | 2 missing (atlas, doctrine) |
| tools/call | ✅ PASS | Tested | Full schema coverage |
| Input schemas | ✅ 100% | 33/33 tools | |
| Output schemas | ✅ 100% | 33/33 tools | |
| Health endpoint | ✅ PASS | `/health` | Version, identity, domain law |
| Session transport | ✅ PASS | Streamable HTTP | Mcp-Session-Id lifecycle |
| MCP-Protocol-Version | ✅ DOCUMENTED | FastMCP 3.4.2 | Required after initialize |
| A2A Agent Cards | ❌ MISSING | — | No `/.well-known/agent.json` |
| MCP Inspector pass | ❌ NOT TESTED | — | |
| OpenTelemetry traces | ❌ MISSING | — | |
| CI publish-image | ⚠️ STALE | `.github/workflows/publish-image.yml` | Uses correct Dockerfile |
| CI Azure deploy | ❌ STALE | — | Remove if unused |
| Version stamp | ⚠️ STALE | `server.py` | Says phase2.3, should be phase2.4 |

---

## Conveyor Belt — The Integration Fix

The conveyor belt is the missing piece. Currently GEOX has stations but no belt.

**Required flow:**
```
Raw data
  → [A] Ingest → artifact record with checksum
  → [B] QC → PASS/WARN/FAIL with usable_for
  → [C] Compute → bounded transform with parameters
  → [D] Claim → structured claim with truth_class + uncertainty
  → [E] Challenge → at least one alternative for HIGH/CRITICAL
  → [F] Uncertainty → p10/p50/p90 or "unknown because..."
  → [G] Reproducibility → receipt with checksums + params + version
  → [H] Safety → risk band + evidence floor + authority check
  → arifOS decision route
```

**The one-line fix for each gap:**

| Gap | Fix | Line |
|-----|-----|------|
| Ingest coverage | `from osgeo import ogr; ds = ogr.Open(path)` | GDAL/OGR wrapper |
| Unified QC | `geox_qc_run(file_path) → QCRecord` | New tool, calls per-domain QC |
| Petrophysics compute | `geox_archie_sw(phi, rw, rt, a, m, n)` | Bounded transform |
| Challenge gate | `if risk >= HIGH: require_challenge(claim_id)` | Gate in claim state machine |
| Uncertainty enforcement | `if not uncertainty: result["warnings"].append(...)` | Schema validation |
| Reproducibility | `return stamp_envelope(result, source_refs)` | 1 line per tool |
| Risk bands | `GEOX_TOOL_MANIFEST[name]["risk_band"] = "YELLOW"` | Registry field |
| A2A Agent Cards | `/.well-known/agent.json` per organ | Static file + route |
| CI fixes | Delete stale workflows | Git rm |
| Version stamp | `_VERSION = "v2026.07.02-phase2.4"` | server.py line 1 |

---

## Priority Stack (what to build first)

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 🔴 P0 | Stamp `_envelope` on 35 tools | 1 day | Reproducibility backbone |
| 🔴 P0 | Fix 1 test failure | 1 hour | CI green |
| 🟠 P1 | Unified `geox_qc_run` | 2 days | QC gate for all data |
| 🟠 P1 | Challenge gate on HIGH/CRITICAL | 2 days | Civilizational safety |
| 🟠 P1 | Forbidden-claims classifier | 2 days | Civilizational safety |
| 🟡 P2 | Risk bands on tool manifest | 1 day | Safety classification |
| 🟡 P2 | Evidence floor labels | 2 days | L1/L2/L3/L4 on outputs |
| 🟡 P2 | Petrophysics: Archie, net pay | 3 days | Compute coverage |
| 🟢 P3 | Shapefile/KML/NetCDF ingest | 3 days | Format coverage |
| 🟢 P3 | A2A Agent Cards | 3 days | Interoperability |
| 🟢 P3 | MCP Inspector pass | 1 day | Standards compliance |

**Total estimated effort for P0+P1:** ~8 days of focused work.
**Total estimated effort for P0+P1+P2:** ~15 days.
**Total estimated effort for all:** ~25 days.

---

*DITEMPA BUKAN DIBERI — The conveyor belt is the next Phase.*
