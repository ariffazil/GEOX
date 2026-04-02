# GEOX TODO — Active Tasks

**DITEMPA BUKAN DIBERI** | Version 0.5.0 | Status: DEPLOYED

---

## 🎯 Current Sprint: Deployment & Distribution

### MCP Server Deployment
- [x] FastMCP 2.x/3.x compatibility layer
- [x] E2E test suite (7/7 tests passing)
- [x] Deploy to FastMCP Horizon
- [x] Connection guides for all platforms
- [x] Landing page + manifesto
- [ ] Custom domain mapping (optional)
- [ ] Usage analytics dashboard

### Distribution & Discovery
- [x] Smithery.ai configuration
- [x] GitHub repository public
- [x] README with badges
- [ ] PyPI release (`pip install arifos-geox`)
- [ ] mcp-get registry submission
- [ ] Awesome MCP Servers list

---

## 🔨 Next Forge: Real Data Integration

### Macrostrat API (Priority: HIGH)
- [ ] Real `MacrostratTool` with API v2
- [ ] F2 Truth Anchor for spatial queries
- [ ] CC-BY-4.0 attribution handling
- [ ] Cache layer for stratigraphic data
- [ ] Unit correlation confidence scoring

### EarthData Discovery (Priority: MEDIUM)
- [ ] NASA Earthdata integration
- [ ] Copernicus Open Access Hub
- [ ] Multi-mode: manifest → script → download
- [ ] OAuth2 authentication flow

### SEG-Y Support (Priority: MEDIUM)
- [ ] Add `segyio` dependency
- [ ] `SegyIngestTool` for 2D/3D import
- [ ] Dutch F3 demo dataset
- [ ] Header parsing and validation

---

## 🎨 Visualization Layer

### cigvis Integration (Priority: HIGH)
- [ ] Add `cigvis>=0.2.0` to dependencies
- [ ] 2D seismic section rendering
- [ ] 3D volume visualization
- [ ] Fault and horizon overlays
- [ ] Well log trajectory plots

### Tri-App Architecture
- [ ] Map App — Geographic context
- [ ] Cross Section App — Interpreted earth model
- [ ] Seismic Section App — Raw observational data
- [ ] Sync mode: split-screen with shared cursor
- [ ] 888 HOLD triggers for cross sections

---

## 🤖 ML Pipeline

### Seismic ML (Priority: MEDIUM)
- [ ] Fault detection model (PyTorch)
- [ ] Salt identification
- [ ] Facies classification
- [ ] YACS-style configuration
- [ ] ONNX export support

### Foundation Models
- [ ] TerraFM integration (NASA)
- [ ] Prithvi-EO-2.0 (IBM/NASA)
- [ ] Embedding cache in Qdrant
- [ ] Multi-task inference heads

---

## 🏛️ Constitutional Hardening

### Floor Implementation
- [x] F1 AMANAH — Reversibility checks
- [x] F2 TRUTH — Evidence anchoring
- [x] F4 CLARITY — Units and metadata
- [ ] F7 HUMILITY — Uncertainty propagation
- [ ] F9 ANTI-HANTU — No phantom data
- [ ] F13 SOVEREIGN — Human review UI

### Audit & Tracing
- [ ] VAULT999 integration
- [ ] Session telemetry
- [ ] Decision lineage
- [ ] Model cards registry

---

## 📚 Documentation

### Guides
- [x] Connection guide (all platforms)
- [x] Manifesto (founder's thesis)
- [ ] API reference (auto-generated)
- [ ] Tutorial: First prospect evaluation
- [ ] Tutorial: Seismic interpretation
- [ ] Best practices guide

### Examples
- [ ] Malay Basin demo (updated)
- [ ] North Sea case study
- [ ] Gulf of Mexico walkthrough
- [ ] Jupyter notebook tutorials

---

## 🔧 Infrastructure

### CI/CD
- [x] GitHub Actions workflow
- [x] Ruff linting
- [ ] MyPy strict mode
- [ ] pytest coverage >80%
- [ ] Automated PyPI releases

### Testing
- [x] E2E MCP tests
- [ ] Integration tests (real APIs)
- [ ] Visualization regression tests
- [ ] Load/performance tests

---

## 📊 Success Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| MCP Server | ✅ Deployed | Stable | 🟢 |
| Test Coverage | ~60% | 80% | 🟡 |
| Real Data Sources | 0 | 3+ | 🔴 |
| Visualization | None | cigvis | 🔴 |
| Documentation | Good | Excellent | 🟡 |
| PyPI Installs | 0 | 100+ | 🔴 |

---

## 🗓️ Timeline

| Phase | Focus | ETA |
|-------|-------|-----|
| **0.5.x** | Stabilization, docs, distribution | April 2026 |
| **0.6.0** | Macrostrat + real data | May 2026 |
| **0.7.0** | Visualization (cigvis) | June 2026 |
| **0.8.0** | ML pipeline | Q3 2026 |
| **1.0.0** | Production hardened | Q4 2026 |

---

## 🐛 Known Issues

| Issue | Severity | Status |
|-------|----------|--------|
| FastMCP 3.x ToolResult import | Medium | ✅ Fixed |
| No real geological data yet | High | 🔴 Planned |
| Visualization missing | High | 🔴 Planned |
| Tests need more coverage | Medium | 🟡 In Progress |

---

*Last Updated: April 2, 2026*  
*Seal: DITEMPA BUKAN DIBERI*