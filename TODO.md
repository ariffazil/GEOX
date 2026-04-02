# GEOX TODO — Active Tasks

**DITEMPA BUKAN DIBERI** | Version 0.5.0 | Status: DEPLOYED

---

## 🚨 AUDIT RESPONSE: Protocol Stability (CRITICAL)

**External Audit Date:** April 3, 2026  
**Status:** Findings Acknowledged | Action Required  
**Full Report:** [AUDIT_2026-04-03_EXTERNAL.md](AUDIT_2026-04-03_EXTERNAL.md)  
**Response:** [RESPONSE_TO_AUDIT.md](RESPONSE_TO_AUDIT.md)

### Critical Findings (Fix Before Any Sale)

#### arifOS: Transport Instability 🔴
- [ ] **Fix transport/content-type negotiation** — Eliminate HTTP 424 errors
- [ ] **Define canonical entrypoint** — Reduce 20+ surfaces to 5 primary endpoints
- [ ] **Unified API envelope** — Standardize request/response schema
- [ ] **Error taxonomy** — Structured JSON, no HTML leakage
- [ ] **SSE/HTTP hardening** — Protocol negotiation stable

**Impact:** -30% valuation ($600K–$900K) if not fixed  
**Timeline:** 60-90 days  
**Owner:** arifOS

#### GEOX: Execution Maturity 🔴
- [ ] **Project/session object model** — Move from atomic tools to object graph
- [ ] **Well-log ingestion API** — LAS/DLIS support
- [ ] **cigvis 3D visualization** — Replace text fallback
- [ ] **Evidence graph schema** — Explicit ledger, not implicit

**Impact:** -20% valuation ($300K–$600K) if not fixed  
**Timeline:** 90 days  
**Owner:** GEOX

### Immediate Actions (Next 7 Days)
- [ ] Inventory all arifOS entry points
- [ ] Document current transport failures
- [ ] Create canonical envelope specification
- [ ] Inventory GEOX object model gaps
- [ ] Research cigvis integration path

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

---

## 💰 Strategic Valuation & Commercial Path

> **Analysis Date:** April 2026  
> **Point Estimate:** $2.0M – $2.5M combined (GEOX + arifOS)

### Current Valuation Matrix

| Asset | As-Is | Worst Case | Stretch |
|-------|-------|------------|---------|
| **GEOX** | $400K – $900K | $100K – $250K | $1.2M – $1.5M |
| **arifOS** | $800K – $1.8M | $250K – $600K | $2.5M – $3.5M |
| **Combined** | **$1.5M – $3.0M** | **$400K – $900K** | **$4.0M – $5.5M** |

### Key Metrics

| Metric | GEOX | arifOS |
|--------|------|--------|
| Commits | 50 | 163 |
| Codebase | 34K LOC | 149K LOC |
| Containers | 1 (MCP) | 16 (Full stack) |
| License | AGPL-3.0 | AGPL-3.0 |
| Deployment | ✅ FastMCP Horizon | ✅ Production Docker |

### The AGPL Reality

**Cannot close-source existing code.** Public AGPL code remains free forever.

**Can sell:**
- ✅ Future proprietary branch rights (Enterprise Edition)
- ✅ Trademarks / domains / brand
- ✅ Deployment know-how / runbooks
- ✅ Founder transition (6-12 months)
- ✅ Hosted control plane IP

### Strategic Options

| Path | Timeline | Target Value | Probability |
|------|----------|--------------|-------------|
| **Fire Sale** | 30 days | $600K – $1.2M | High |
| **Structured Sale** | 6-12 months | $2.5M – $5.0M | Medium |
| **Build & Raise** | 2-3 years | $10M – $50M | Low (70% fail) |

### Recommended Actions (Valuation Focus)

#### Immediate (Next 30 Days)
- [ ] **IP Hygiene Audit** — Verify 100% personal ownership, no employer conflicts
- [ ] **Trademark Filing** — "GEOX", "arifOS", "DITEMPA BUKAN DIBERI"
- [ ] **Domain Acquisition** — geox.earth, arifos.com (if available)
- [ ] **Enterprise Branch Setup** — Private repo for future proprietary code

#### Short Term (3-6 Months) — **HIGHEST ROI**
- [ ] **cigvis Integration** — 3D seismic visualization (+$500K perceived value)
- [ ] **Macrostrat Live Data** — Real geological API integration
- [ ] **Land One Pilot** — Target: $10K/month with O&G or mining firm
- [ ] **Design Partner LOI** — Non-binding letter from major (Shell, Petronas, etc.)

#### Medium Term (6-12 Months)
- [ ] **Revenue Target** — $50K ARR minimum
- [ ] **Case Studies** — 2-3 documented customer successes
- [ ] **Team Expansion** — Hire geoscientist + engineer
- [ ] **Seed Round** — $2M on $8M+ pre-money (if not selling)

### Valuation Toxins to Avoid

| Risk | Impact | Mitigation |
|------|--------|------------|
| Unclear IP ownership | -40% valuation | Get employer waivers NOW |
| No visualization | -30% valuation | Prioritize cigvis |
| No paid pilot | -50% valuation | Land one customer |
| AGPL confusion | Deal killer | Structure as "future rights" sale |

### Decision Matrix

**IF you need cash NOW:**
→ Sell structured package: Future rights + brand + transition. Target: $1.5M

**IF you can wait 6 months:**
→ Add cigvis + land pilot. Target: $3M – $5M

**IF you want maximum value:**
→ Build 2 years, reach $100K ARR, Series A at $25M+. Risk: 70% failure rate

---

*Last Updated: April 3, 2026*  
*Valuation Authority: Forensic audit complete*  
*Seal: DITEMPA BUKAN DIBERI*