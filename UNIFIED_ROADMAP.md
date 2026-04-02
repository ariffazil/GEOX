# GEOX Unified Roadmap & TODO

**"DITEMPA BUKAN DIBERI" — Forged, Not Given.**

> **Version:** v0.5.0 — April 2, 2026  
> **Status:** ✅ DEPLOYED TO HORIZON  
> **Authority:** 999 SEAL | Floors F1 F4 F7 | Confidence: CLAIM

---

## Current Status (v0.5.0)

| Dimension | Status | Notes |
|-----------|--------|-------|
| **MCP Server** | ✅ DEPLOYED | FastMCP Horizon: `geoxarifOS.fastmcp.app` |
| **Compatibility** | ✅ 2.x/3.x | ToolResult shim for version detection |
| **E2E Tests** | ✅ 7/7 Passing | Full MCP compliance validation |
| **Documentation** | ✅ Complete | Connection guides + manifesto + landing page |
| **CI/CD** | ✅ GitHub Actions | Auto-test on push |
| **Packaging** | ⚠️ Needs PyPI | Install from source only |
| **Visualization** | ❌ None | **CRITICAL GAP** — cigvis pending |
| **Real Data** | ❌ Mock only | Macrostrat API integration pending |

---

## 🎉 Forge 0: Deployment Complete (April 2026)

### MCP Server Deployment ✅
- [x] FastMCP 2.x/3.x compatibility layer with ToolResult shim
- [x] 6 MCP tools with health endpoints
- [x] E2E test suite (`test_e2e_mcp.py`) — 7 tests passing
- [x] FastMCP Horizon deployment: `https://geoxarifOS.fastmcp.app/mcp`
- [x] Static landing page: `https://geoxarifOS.fastmcp.app/`
- [x] Connection guides for ChatGPT, Claude, Cursor, Kimi, Gemini, VS Code
- [x] Founder manifesto published

### Key Deliverables
| File | Purpose |
|------|---------|
| `geox_mcp_server.py` | Main MCP server with version detection |
| `test_e2e_mcp.py` | E2E test suite |
| `CONNECT_TO_GEOX.md` | Platform connection guides |
| `MANIFESTO.md` | Founder's thesis |
| `geox-gui/public/index.html` | Polished landing page |
| `geox-gui/public/manifesto.html` | Styled manifesto |

---

## 🔨 Forge 1: Real Data Integration (May 2026)

### 1.1 Macrostrat API Integration
**Priority: HIGHEST**

- [ ] Real `MacrostratTool` with API v2
- [ ] F2 Truth Anchor for spatial queries
- [ ] CC-BY-4.0 attribution in reports
- [ ] Cache layer for stratigraphic columns
- [ ] Unit correlation confidence scoring
- [ ] 888 HOLD triggers for sparse well control

```python
# Target API
geox_verify_geospatial(lat=4.5, lon=114.2)
→ Province: Malay Basin
→ Stratigraphy: ["Miocene", "Pliocene"]
→ Confidence: 0.87
→ Source: Macrostrat v2
```

### 1.2 EarthData Discovery
**Priority: MEDIUM**

- [ ] `EarthDataDiscoveryTool` for NASA Earthdata
- [ ] Copernicus Open Access Hub integration
- [ ] Multi-mode: manifest → script → download
- [ ] OAuth2 authentication flow
- [ ] F1 Amanah: Download reversibility

### 1.3 SEG-Y Support
**Priority: MEDIUM**

- [ ] Add `segyio` to dependencies
- [ ] `SegyIngestTool` for 2D/3D SEG-Y import
- [ ] Header parsing and validation
- [ ] Dutch F3 demo dataset
- [ ] F4 Clarity: Explicit data bounds

---

## 🔨 Forge 2: Visualization Layer (June 2026)

**Decision: ADOPT from `cigvis`**

### 2.1 cigvis Integration
- [ ] Add `cigvis>=0.2.0` to dependencies
- [ ] `SeismicVisualizationTool` implementation
- [ ] 2D seismic section rendering
- [ ] 3D volume visualization with overlays
- [ ] Well log trajectory plots
- [ ] Multi-backend: vispy (desktop), viser (web)

### 2.2 MCP Visualization Tools
- [ ] `geox_render_inline` — Inline section
- [ ] `geox_render_timeslice` — Time slice
- [ ] `geox_render_3d` — 3D volume
- [ ] `geox_render_cross_section` — Geologic interpretation

### 2.3 Tri-App Architecture
**Never merge Cross Section and Seismic Section**

| App | Type | Data | Purpose |
|-----|------|------|---------|
| **Map App** | Overview | Basin, coordinates | Geographic context |
| **Cross Section** | INTERPRETED | Wells, tops, faults | Earth model |
| **Seismic Section** | OBSERVATIONAL | Raw seismic | Sensor evidence |

- [ ] Sync mode: split-screen + shared cursor
- [ ] Well tie highlighting
- [ ] Fault selection sync
- [ ] Distance coordinate synchronization

---

## 🔨 Forge 3: Seismic ML Pipeline (Q3 2026)

**Decision: BORROW from `microsoft/seismic-deeplearning` + `lanl/mtl`**

### 3.1 Seismic ML Tools
- [ ] `SeismicMLTool` with PyTorch backend
- [ ] Fault detection (location, dip, strike)
- [ ] Salt identification
- [ ] Facies classification
- [ ] YACS-style configuration

### 3.2 Multi-Task Inference
| Task | Output | Use Case |
|------|--------|----------|
| DHR | Denoised High-Resolution image | Quality improvement |
| RGT | Relative Geological Time volume | Chronostratigraphy |
| Fault | Fault attributes | Structural interpretation |

### 3.3 Model Backend
- PyTorch (primary)
- ONNX export support
- **DO NOT USE OpenVINO** (discontinued)

---

## 🔨 Forge 4: Distribution & Growth (Ongoing)

### 4.1 Package Distribution
- [ ] PyPI release: `pip install arifos-geox`
- [ ] mcp-get registry submission
- [ ] Smithery.ai auto-update
- [ ] conda-forge package

### 4.2 Community
- [ ] Awesome MCP Servers list
- [ ] Hacker News launch
- [ ] Reddit r/geology, r/geophysics
- [ ] LinkedIn technical posts
- [ ] Conference talks (AAPG, SEG, EAGE)

### 4.3 Documentation
- [ ] API reference (auto-generated)
- [ ] Tutorial: First prospect evaluation
- [ ] Tutorial: Seismic interpretation workflow
- [ ] Video walkthroughs
- [ ] Case study library

---

## 🗺️ Long-Term Roadmap (2026-2027)

### Phase 1: Foundation (COMPLETE)
- ✅ MCP server architecture
- ✅ Constitutional governance (F1-F13)
- ✅ E2E testing framework
- ✅ Deployment pipeline

### Phase 2: Real Data (Q2 2026)
- Macrostrat integration
- EarthData discovery
- SEG-Y support
- Basic visualization

### Phase 3: Perception & ML (Q3 2026)
- cigvis full integration
- Seismic ML pipeline
- LEM integration (TerraFM)
- Qdrant production hardening

### Phase 4: Verification & Scale (Q4 2026)
- GEO-Bench benchmark harness
- Model registry + Model Cards
- F13 Sovereign Dashboard
- Enterprise features

### Phase 5: Ecosystem (2027)
- Plugin architecture
- Third-party tool integration
- Industry partnerships
- Open source foundation

---

## 🏛️ Integration Matrix: Adopt · Borrow · Wrap · Ignore

| Repository | Decision | Rationale | Status |
|------------|----------|-----------|--------|
| `cigvis` | **ADOPT** | 3D seismic rendering — HIGHEST PRIORITY | Pending |
| `macrostrat/macrostrat-api` | **ADOPT** | Real geological data — CRITICAL | Pending |
| `nasa/earthdata` | **WRAP** | Satellite imagery discovery | Planned |
| `microsoft/seismic-deeplearning` | **BORROW** | ML pipeline patterns | Reference |
| `lanl/mtl` | **BORROW** | Multi-task taxonomy | Reference |
| `blake365/usgs-quakes-mcp` | **BORROW** | Packaging patterns | Studied |
| `intel/openseismic` | **IGNORE** | Discontinued May 2024 | Avoided |

---

## 🛡️ Constitutional Floor Mapping

| Floor | Forge 0 | Forge 1 | Forge 2 | Forge 3 |
|-------|---------|---------|---------|---------|
| F1 Amanah | ✅ Reversibility | Download audit | Viz reversibility | ML lineage |
| F2 Truth | ✅ Schema anchor | Macrostrat real | cigvis rendering | Benchmark validation |
| F4 Clarity | ✅ Units explicit | Data bounds | Embedding metadata | Uncertainty propagation |
| F7 Humility | ✅ API timeout | Sparse data | Viz uncertainty | Model calibration |
| F9 Anti-Hantu | ✅ No phantom | Real data only | Real SEG-Y | Real ML models |
| F13 Sovereign | ✅ MCP governance | Human review | HOLD on viz | Full dashboard |

---

## ⚠️ Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| FastMCP API changes | Low | Medium | Version pinning, shim layer ✅ |
| Macrostrat API limits | Medium | Medium | Cache layer, rate limiting |
| cigvis integration complexity | Medium | High | Phased approach, PoC first |
| ML model availability | Medium | Medium | Multiple backends, mock fallbacks |
| User adoption | Medium | High | Documentation, tutorials, community |

---

## ✅ Success Metrics

| Metric | v0.4.x | v0.5.0 (Current) | v0.6.0 Target |
|--------|--------|------------------|---------------|
| MCP Server | ⚠️ Local | ✅ **DEPLOYED** | Stable |
| Test Coverage | 60% | 60% | 80% |
| Real Data Sources | 0 | 0 | 2+ |
| Visualization | None | None | cigvis 2D |
| PyPI Installs | N/A | N/A | 100+ |
| Active Users | 0 | 0 | 10+ |

---

## 🎯 Immediate Next Actions

1. **PyPI Release** — Enable `pip install arifos-geox`
2. **Macrostrat Integration** — Real geological data
3. **cigvis PoC** — Prove visualization pipeline
4. **Tutorial Content** — Lower barrier to entry
5. **Community Outreach** — HN, Reddit, LinkedIn

---

*Ditempa Bukan Diberi* [ΔΩΨ | 888 | 999]  
*Updated: April 2, 2026*  
*Status: FORGE-0 COMPLETE | FORGE-1 READY*