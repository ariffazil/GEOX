# GEOX Unified Roadmap & TODO
**"DITEMPA BUKAN DIBERI" — Forged, Not Given.**

> **Version:** v0.4.1 — April 1, 2026
> **Based on:** Deep research across 9 complement repositories
> **Authority:** 999 SEAL | Floors F1 F4 F7 | Confidence: CLAIM

⚠️ **EXECUTIVE OVERRIDE (April 2026):** 
The primary strategic direction has shifted to prioritizing the **Governed Intelligence Kernel** and **Grounded Evidence Graph** over further UI polish. Please see [STRATEGIC_UPGRADE_PATH_Q2_2026.md](docs/STRATEGIC_UPGRADE_PATH_Q2_2026.md) for the definitive 12-month upgrade plan focusing on State, Memory, Policy, Uncertainty, and Multimodal Observability.

---

## Current Status (Audit v0.4)

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Architecture** | ✅ 4-Plane Stack defined | Governance, Language, Perception, Earth |
| **Pipeline** | ✅ 000-999 implemented | INIT→THINK→EXPLORE→HEART→REASON→AUDIT→SEAL |
| **Governance** | ✅ F1-F13 Floors active | 888 HOLD mechanism |
| **MCP Server** | ⚠️ Functional | stdio/HTTP transports working |
| **Memory** | ⚠️ JSONL default, Qdrant optional | Needs production hardening |
| **CI/CD** | ⚠️ Basic GitHub Actions | Needs coverage threshold |
| **Visualization** | ❌ None | **CRITICAL GAP** |
| **Tri-App Architecture** | 🆕 New | Map + Cross Section + Seismic Section |

---

## 🏛️ Tri-App Architecture (Map + Cross Section + Seismic Section)

GEOX owns the visual semantics, not the LLM. LLM handles intent; GEOX produces deterministic state.

### Three Coordinated Views

| App | Purpose | Data Source | Key Distinction |
|-----|---------|------------|-----------------|
| **Map App** | Geographic context | Basin, coordinates, assets | Spatial overview |
| **Cross Section App** | Interpreted earth model | Wells, tops, faults, stratigraphy | **INTERPRETED** — observed vs inferred |
| **Seismic Section App** | Sensor evidence | Seismic image/line | **OBSERVATIONAL** — raw evidence |

### Critical: Never Merge Cross Section and Seismic Section
- **Geologic Cross Section**: Interpretive earth model product
- **Seismic Section**: Observational sensor image
- Confusing them leads to overclaim and bad UI semantics

### Sync Mode
- Split-screen: Cross Section + Seismic Section
- Shared profile cursor
- Clicking well in cross section highlights well tie in seismic
- Fault selection synced between views
- Distance coordinate synchronized along line

### 888 HOLD Triggers for Cross Section
- Borehole spacing > 10km — continuity claims unreliable
- Unit correlation confidence < 0.6
- Vertical exaggeration > 2x but not disclosed
- Fault geometry not seismic-constrained
- Pinchout/truncation in interpreted zone
- Interval of interest has zero well control

---

## Integration Matrix: Adopt · Borrow · Wrap · Ignore

| Repository | Decision | Rationale |
|------------|----------|-----------|
| `blake365/usgs-quakes-mcp` | **ADOPT** (packaging) | Clean Claude Desktop integration, Smithery config |
| `datalayer/earthdata-mcp-server` | **BORROW** (discovery) | Multi-mode download pattern (manifest→script→download) |
| `datalayer/jupyter-earth-mcp-server` | **IGNORE** | Archived; merged into earthdata-mcp-server |
| `microsoft/seismic-deeplearning` | **BORROW** (ML pipelines) | Segmentation models, SEGY prep; archived but instructive |
| `intel/openseismic` | **IGNORE** | Discontinued May 2024; OpenVINO abandoned |
| `lanl/mtl` | **BORROW** (task taxonomy) | Multi-task: DHR + RGT + Fault; proprietary but inspiring |
| `cigvis` | **ADOPT** (visualization) | **HIGHEST PRIORITY** — 3D seismic rendering, fault/horizon overlays |
| `dougwithseismic/withseismic-mcp` | **ADOPT** (server architecture) | Production TypeScript template, registry pattern |
| `pathintegral-institute/mcp.science` | **BORROW** (ecosystem) | Monorepo structure, `uvx` execution pattern |

### Decision Definitions
- **ADOPT**: Direct integration into GEOX architecture
- **BORROW**: Extract patterns/ideas, do not copy code directly
- **WRAP**: Create adapters to use existing functionality
- **IGNORE**: Do not use; archived, irrelevant, or substitutes exist

---

## 🌍 Forge 3: Open Earth Integration (STRATEGIC)
Standardize GEOX on open engines and data models to close the visualization gap.

### 3.1 Core Engines
- [ ] Integrate **CesiumJS** for high-precision WGS84 3D globe visualization.
- [ ] Integrate **MapLibre GL JS** for GPU-accelerated 2D mapping.
- [ ] Use **TerriaJS** as the catalog-driven UI shell.

### 3.2 Data Standards & Infra
- [ ] Implement **STAC** for geospatial asset discovery.
- [ ] Standardize on **Cloud Optimized GeoTIFF (COG)** for raster/seismic delivery.
- [ ] Deploy **Martin** (Vector Tiles) and **TiTiler** (Raster) serving layers.
- [ ] Migrate spatial metadata to **PostGIS**.

### 3.3 Canonical Earth Sourcing
- [ ] Wire **OpenStreetMap (via Protomaps)** as the primary basemap.
- [ ] Set **Copernicus DEM** as the global terrain source.
- [ ] Automate **Macrostrat** API integration for geologic maps.

## 🔨 Forge 1: Foundation Hardening (COMPLETED)

### 1.1 Packaging & Installation ✅
- [x] `pip install -e .` works via `uv`
- [x] CLI entry point resolves at `/root/arifOS/.venv/bin/geox`
- [x] Health check functional

### 1.2 Smithery.ai Integration ✅
- [x] `transport: stdio` for Claude Desktop
- [x] All 10 MCP tools documented
- [x] Installation via `pip install arifos-geox`

### 1.3 Canonical State Schemas ✅
- [x] `GeoXIntent` — Normalized user intent
- [x] `GeoXAssetContext` — Asset and spatial context
- [x] `GeoXDisplayState` — Viewer state
- [x] `GeoXAnalysisState` — Observations, interpretations
- [x] `GeoXAuditState` — Hold status, scope flags
- [x] `GeoXUiState` — Combined UI state
- [x] `GeoXCrossSectionState` — Geologic cross section
- [x] `GeoXSeismicSectionState` — Seismic section
- [x] `GeoXTriAppState` — Container for all three apps
- [x] `CrossSectionHoldTriggers` — 888 HOLD triggers
- [x] `ToolOutputEnvelope` — Standard tool contract

### 1.4 Tests ✅
- [x] 179 tests passing
- [x] `ruff` clean (after auto-fix)
- [x] `mypy` on canonical_state.py: 0 errors

---

## 🔨 Forge 2: Visualization Gap (HIGHEST PRIORITY)

**Decision: ADOPT from `cigvis`**

### 2.1 Integrate cigvis
- [ ] Add `cigvis>=0.2.0` to dependencies
- [ ] Implement `SeismicVisualizationTool`
- [ ] 2D/3D seismic volume rendering
- [ ] Fault and horizon overlays
- [ ] Well log trajectory visualization

### 2.2 MCP Visualization Tools
- [ ] `geox_render_inline` — Inline section rendering
- [ ] `geox_render_timeslice` — Time slice rendering
- [ ] `geox_render_3d` — 3D volume with overlays
- [ ] Multi-backend: vispy (desktop), viser (web), plotly (Jupyter)

### 2.3 Cross Section App
- [ ] `geox_open_cross_section`
- [ ] `geox_cross_section_build_model`
- [ ] `geox_cross_section_get_uncertainty_zones`
- [ ] Profile line selection in map

---

## 🔨 Forge 3: Real Data Integration

### 3.1 Macrostrat Integration
- [ ] Real `MacrostratTool` with API v2
- [ ] F2 Truth Anchor for spatial queries
- [ ] CC-BY-4.0 attribution in reports

### 3.2 EarthData Discovery
- [ ] `EarthDataDiscoveryTool` for NASA Earthdata/Copernicus
- [ ] Multi-mode: manifest → script → download
- [ ] OAuth authentication

### 3.3 SEG-Y Reader
- [ ] Add `segypy` or `segyio` to dependencies
- [ ] `SegyIngestTool` for 2D/3D SEG-Y import
- [ ] Dutch F3 dataset support

---

## 🔨 Forge 4: Seismic ML Pipeline

**Decision: BORROW from `microsoft/seismic-deeplearning` + `lanl/mtl`**

### 4.1 Seismic ML Tools
- [ ] `SeismicMLTool` with fault detection, salt ID, facies
- [ ] YACS-style config for model swapping
- [ ] PyTorch backend (NOT OpenVINO)

### 4.2 Multi-Task Inference
- [ ] DHR: Denoised High-Resolution image
- [ ] RGT: Relative Geological Time volume
- [ ] Fault: Fault attributes (location, dip, strike)

### 4.3 Model Backend
| Model | Backend | Status |
|-------|---------|--------|
| Fault detection | PyTorch | Implement |
| Salt identification | PyTorch | Implement |
| Facies classification | PyTorch | Implement |
| Intel OpenVINO | ~~Deprecated~~ | **DO NOT USE** |

---

## 🗺️ Long-Term Roadmap (Months 6-24)

### Phase 2: Perception & Memory (Months 6-9)
- [ ] LEM Integration (TerraFM or Prithvi-EO-2.0)
- [ ] Qdrant production hardening
- [ ] Schema-first synthesis

### Phase 3: Geology Adaptation (Months 9-18)
- [ ] Constraint Graph (Chronostratigraphy ordering)
- [ ] Alignment Pipeline (Macrostrat × EO tiles)
- [ ] Multi-Task Heads

### Phase 4: Verification & Governance (Months 18-24)
- [ ] Benchmark Harness (GEO-Bench, Copernicus-Bench)
- [ ] Model Registry + Model Cards
- [ ] F13 Sovereign Dashboard

---

## 🛡️ Constitutional Floor Mapping

| Floor | Forge 1 | Forge 2 | Forge 3 | Forge 4 |
|-------|---------|---------|---------|---------|
| F1 Amanah | Reversibility checks | Dual-memory audit | ML lineage | Full provenance |
| F2 Truth | Canonical schemas | cigvis rendering | Fault/RGT inference | Benchmark validation |
| F4 Clarity | Units in quantities | Embedding metadata | Multi-task outputs | Uncertainty propagation |
| F7 Humility | API timeout handling | Visualization uncertainty | Model uncertainty | Calibrated confidence |
| F9 Anti-Hantu | No phantom data | Real SEG-Y reader | Real ML models | Benchmark checks |
| F13 Sovereign | Smithery integration | 888 HOLD on viz | HOLD on ML | Human review UI |

---

## ⚠️ Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| cigvis API changes | Low | Medium | Pin version, adapter pattern |
| LEM backend unavailable | Medium | High | Mock fallback, pluggable |
| Archived ML repos | High | Low | Use as reference only |
| Macrostrat API changes | Medium | Medium | Version pinning |
| OpenVINO avoidance | Done | N/A | Use ONNX/TensorRT |

---

## ✅ Success Metrics

| Metric | Current | Target (Forge 2) |
|--------|---------|-----------------|
| CI Pipeline | ✅ 179 tests | ✅ 80%+ coverage |
| Visualization | ❌ None | ✅ cigvis rendering |
| Real Data | ❌ Mock only | ✅ Macrostrat real |
| Smithery Integration | ✅ Config exists | ✅ Auto-updates |

---

*Ditempa Bukan Diberi* [ΔΩΨ | 888 | 999]
*Updated: April 1, 2026*
*Status: FORGE-1 COMPLETE | FORGE-2 READY