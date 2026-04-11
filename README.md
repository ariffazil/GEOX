# GEOX Earth Witness

> **DITEMPA BUKAN DIBERI** — *Forged, Not Given*  
> **Constitutional Geoscience Platform v2026.04.11**

[![Seal](https://img.shields.io/badge/SEAL-DITEMPA%20BUKAN%20DIBERI-gold)](./wiki/90_AUDITS/999_SEAL.md)
[![Version](https://img.shields.io/badge/version-2026.04.11-blue)](./CHANGELOG.md)
[![Status](https://img.shields.io/badge/status-🟢%20ACTIVE-green)](./DEPLOYMENT_STATUS.md)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

**Verified Live URLs:**
- 🌐 https://geox.arif-fazil.com — Main web interface
- 🔧 http://localhost:8000 — MCP endpoint (VPS direct)
- ✅ Status: HTTP 200 verified 2026-04-11

GEOX is the world's first **Constitutional Subsurface Reasoning Layer**—a governed AI orchestration platform for Earth Intelligence. Built with a Python/FastMCP backend and a React/TypeScript frontend, it acts as a **Judgment Engine** that sits above existing subsurface stacks (like Petrel, Kingdom, or DecisionSpace). GEOX enforces 13 constitutional floors (F1-F13) to separate observed data from inferred interpretation, ensuring subsurface decisions are physically grounded and audit## 🎯 Strategic Positioning: The Sovereign Physics Engine

Unlike traditional subsurface OS environments (Petrel, DecisionSpace) which focus on feature breadth and automation speed, GEOX is built for **Causal Integrity**.

- **Not a Petrel Clone:** GEOX provides the **Sovereign Logic Layer** that validates interpretations through deterministic physics.
- **Epistemic Governance:** Uses formal verdict semantics (`HOLD`, `PASS`, `FAIL`) to manage interpretation risk and prevent AI hallucinations (hantu).
- **Physics Copilot:** A dimension-first engine that enforces thermodynamic and physical constraints (**EARTH.PHYSICS_9**) across the interpretative lifecycle.

---

## 🏛️ Architecture

GEOX implements a dimension-first sovereign architecture, separating borehole truth from basin-scale hydration:

| Layer | Domain | Scale | Logic |
|-------|--------|-------|-------|
| `bridge` | Governance | Global | Seal, Sync, Audit |
| `prospect` | Mapping | 2D/3D | Volumetrics (STOIIP) |
| `dim1` | Borehole | 1D | Log Synthesis / MD-Scaling |
| `dim2` | Seismic | 2D | Structural Analysis / DHI |
| `dim3` | Basin | 3D | Stratigraphy / Macrostrat |
| `physics9` | Metabolizer | Meta | CANON_9 State Vector |

---

## 🛠️ Sovereign MCP Tools (v1.9)

### Bridge & Governance
| Tool | Purpose | Status |
|------|---------|--------|
| `bridge.sync_state` | Synchronize UI with the 888_JUDGE scene. | ACTIVE |
| `bridge.interpret_causal_scene` | Structured synthesis of multiple witnesses. | ACTIVE |
| `bridge.audit_policy_violation` | Formally audit breach of F2/F8/F9 floors. | ACTIVE |
| `bridge.check_operator_legality` | Constitutional pre-flight on physical operations. | ACTIVE |

### Dimensional Kernels
| Tool | Purpose | Scale |
|------|---------|-------|
| `prospect.compute_stoiip` | Deterministic volumetric integration. | Prospect |
| `dim1.borehole_synthesis` | 1D Truth extraction via ODSiphon. | Borehole |
| `dim2.seismic_interpret` | 2D Structural/DHI interpretation logic. | Seismic |
| `dim3.basin_regional` | 3D Basin-scale stratigraphy & play context. | Basin |
| `physics9.verify_state` | Validate thermodynamic equilibrium (F2_PHYSICS). | Meta |

### System
| Tool | Purpose |
|------|---------|
| `geox_health` | Kernel health and 999_SEAL heartbeat. |
��───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Core Domain:** `arifos/geox/tools/core.py` — Pure business logic, no transport dependencies
- **FastMCP Adapter:** `arifos/geox/tools/adapters/fastmcp_adapter.py` — SSE/HTTP transport
- **Copilot Adapter:** `arifos/geox/adapters/copilot_adapter.py` — Microsoft Teams integration
- **UI Event Bus:** `arifos/geox/ui_bridge/src/event_bus.ts` — TypeScript JSON-RPC bridge

---

## 🛠️ MCP Tools (13 Available)

### Foundation (Phase A)
| Tool | Purpose |
|------|---------|
| `geox_load_seismic_line` | Visual mode ignition with P wave analysis |
| `geox_build_structural_candidates` | Inverse modelling constraints |
| `geox_evaluate_prospect` | Governed prospect verdicts (DRO/DRIL/HOLD) |
| `geox_feasibility_check` | Physical possibility firewall |
| `geox_verify_geospatial` | CRS & jurisdiction verification |
| `geox_calculate_saturation` | Monte Carlo Sw calculations |
| `geox_query_memory` | Geological memory retrieval |

### Physics Engine (Phase B)
| Tool | Purpose |
|------|---------|
| `geox_select_sw_model` | SW model admissibility from log QC |
| `geox_compute_petrophysics` | Full petrophysics property pipeline |
| `geox_validate_cutoffs` | Apply CutoffPolicy schema |
| `geox_petrophysical_hold_check` | Trigger 888_HOLD on floor violations |

### Demo
| Tool | Purpose |
|------|---------|
| `geox_malay_basin_pilot` | Malay Basin petroleum exploration data |

### System
| Tool | Purpose |
|------|---------|
| `geox_health` | Server health & constitutional status |

---

## 🌍 Malay Basin Pilot

The **Malay Basin Petroleum Exploration Pilot** is the live demonstration of GEOX capabilities:

- **Backend:** `arifos/geox/resources/malay_basin_pilot.py`
- **GUI:** `geox-gui/src/components/MalayBasinPilotDashboard.tsx`
- **Live:** https://geox.arif-fazil.com (click "Pilot" tab)

**Features:**
- Real-time exploration metrics (500+ MMBOE cumulative reserves)
- Play type distribution (MMP, LPS, PBD, Fluvial)
- Creaming curve phases (EDP15 baseline)
- Integration with EarthWitness map (auto-zoom to 5.5°N, 104.5°E)
- Constitutional badges (F2 Truth, F9 Anti-Hantu, F13 Sovereign)

---

## ⚖️ Constitutional Floors (F1-F13)

All GEOX operations are governed by 13 constitutional floors:

| Floor | Name | Description |
|-------|------|-------------|
| F1 | Amanah | Reversible, audited operations |
| F2 | Truth | Verdict-based outputs (HOLD/DRO/DRIL) |
| F3 | Tri-Witness | Human × AI × System consensus |
| F4 | Clarity | Zero entropy, 5-line decisions |
| F5 | Peace | Non-adversarial reasoning |
| F6 | Empathy | Care envelope for stakeholders |
| F7 | Humility | Confidence caps at 0.90 |
| F8 | Genius | Multiplicative wisdom (G = A×P×X×E²) |
| F9 | Anti-Hantu | Ghost pattern detection |
| F10 | Ontology | Knowledge graph grounded |
| F11 | Audit | Transaction logging |
| F12 | Injection | Input sanitization |
| F13 | Sovereign | Human emergency override |

**Enforcement:** 888_HOLD triggers on any floor violation.

---

## 📚 Documentation

### Wiki (Source of Truth)
The [wiki/](./wiki) directory contains the canonical documentation:

| Section | Purpose |
|---------|---------|
| [00_INDEX](./wiki/00_INDEX) | Gateway & quickstart |
| [10_THEORY](./wiki/10_THEORY) | Theory of Anomalous Contrast, foundations |
| [20_PHYSICS](./wiki/20_PHYSICS) | Earth Canon 9, physical laws |
| [30_MATERIALS](./wiki/30_MATERIALS) | RATLAS, geological materials |
| [40_BASINS](./wiki/40_BASINS) | Regional geology (Malay Basin, etc.) |
| [50_TOOLS](./wiki/50_TOOLS) | Complete tool documentation |
| [70_GOVERNANCE](./wiki/70_GOVERNANCE) | Constitutional enforcement |
| [80_INTEGRATION](./wiki/80_INTEGRATION) | Architecture & deployment |
| [90_AUDITS](./wiki/90_AUDITS) | Historical seals & logs |

### Key Documents
- [Agent Initialization Protocol](./wiki/00_INDEX/Agent_Initialization_Protocol.md)
- [GEOX Manifesto](./wiki/00_INDEX/MANIFESTO.md)
- [Theory of Anomalous Contrast](./wiki/10_THEORY/Theory_of_Anomalous_Contrast.md)
- [Earth Canon 9](./wiki/20_PHYSICS/EARTH_CANON_9.md)
- [MCP Apps Architecture](./wiki/80_INTEGRATION/GEOX_MCP_APPS_ARCHITECTURE.md)
- [FASTMCP CLI Guide](./wiki/80_INTEGRATION/FASTMCP_CLI_GUIDE.md)

---

## 🧪 Testing

```bash
# Run all tests
pytest

# MCP server test
python test_mcp_server.py

# End-to-end test
python test_e2e_mcp.py

# Health check
curl https://geox.arif-fazil.com/health
```

---

## 🚢 Deployment

### VPS (Production)
```bash
# Deploy to VPS
./deploy-vps.sh

# Force rebuild (use when GUI needs refresh)
./deploy-vps.sh --force-rebuild
```

### Horizon (FastMCP Cloud)
```bash
# Automatic deployment on push to main
# URL: https://geoxarifOS.fastmcp.app/mcp
git push origin main
```

### Local Development
```bash
# Backend
python geox_mcp_server.py

# Frontend
cd geox-gui && npm run dev
```

---

## 📊 Current Status

| Aspect | Status | Notes |
|--------|--------|-------|
| Backend (VPS) | ✅ Operational | MCP Server v2026.04.10 responding |
| Frontend (VPS) | ✅ Operational | Landing page + Cockpit live |
| Landing Page | ✅ Complete | Clean entry point, not crammed cockpit |
| Well Log Viewer | ✅ Complete | LogDock with petrophysics (Canvas/D3) |
| Seismic Engine | ✅ Ignited | Synthetic Physics active |
| MCP Tools | ✅ 13 tools | All phases implemented |
| Malay Basin Pilot | ✅ Full Stack | Live at geox.arif-fazil.com |
| **Constitutional Firewall** | **🆕 EUREKA** | **GPT-5 stress-test PASSED** |

### 🎉 EUREKA-LEVEL Validation (2026-04-10)

**GPT-5 Constitutional Firewall Stress-Test: PASSED**

The GEOX system successfully blocked hallucination when GPT-5 (via Gemini) queried the Layang-Layang Basin with zero prior data:

- ✅ **F7 Humility Enforced** — Confidence capped at Ω₀ ∈ [0.03, 0.05]
- ✅ **888_HOLD Anticipated** — AI acknowledged constraints before human request
- ✅ **Tri-Witness Consensus** — Human × AI × System alignment verified

**Evidence:** [`wiki/90_AUDITS/EUREKA_VALIDATION_2026_04_10.md`](wiki/90_AUDITS/EUREKA_VALIDATION_2026_04_10.md)

**Next Actions:**
1. Tune Ω₀ parameters for deepwater frontier zones
2. Deploy built `dist/` to VPS
3. Connect LogDock to MCP backend for live LAS data
4. Build Seismic Viewer (WebGL)

---

## 🏗️ Project Structure

```
GEOX/
├── arifos/                      # Constitutional architecture
│   └── geox/
│       ├── tools/
│       │   ├── core.py          # Domain logic (host-agnostic)
│       │   └── adapters/
│       │       └── fastmcp_adapter.py
│       ├── contracts/
│       │   ├── types.py         # Pydantic models
│       │   └── app_manifest.py  # App interface schema
│       ├── ui_bridge/
│       │   └── src/
│       │       └── event_bus.ts # TypeScript JSON-RPC
│       ├── adapters/
│       │   └── copilot_adapter.py
│       └── resources/
│           └── malay_basin_pilot.py
├── geox-gui/                    # React/TypeScript frontend
│   └── src/
│       └── components/
│           ├── LandingPage/        # Clean entry point (NEW)
│           ├── LogDock/            # Well log viewer (NEW)
│           ├── MalayBasinPilotDashboard.tsx
│           ├── EarthWitness.tsx
│           └── MainLayout.tsx
├── wiki/                        # Ω-Wiki documentation
│   ├── 00_INDEX/
│   ├── 10_THEORY/
│   ├── 20_PHYSICS/
│   ├── 30_MATERIALS/
│   ├── 40_BASINS/
│   ├── 50_TOOLS/
│   ├── 70_GOVERNANCE/
│   ├── 80_INTEGRATION/
│   └── 90_AUDITS/
├── tests/                       # Test suite
├── geox_mcp_server.py           # FastMCP server entry
├── fastmcp.json                 # CLI configuration
├── pyproject.toml               # Python dependencies
├── Dockerfile                   # Container build
└── docker-compose.yml           # VPS orchestration
```

---

## 📜 License

MIT License — See [LICENSE](./LICENSE)

---

## 👤 Author

**Muhammad Arif bin Fazil**  
Constitutional Authority for GEOX Earth Witness  
DITEMPA BUKAN DIBERI — *Forged, Not Given*

---

*"Forged through constitutional discipline, not granted by external authority."*

---

## 🏛️ Trinity Ecosystem — Live Links

| Ring | Domain | Realm | Status |
|------|--------|-------|--------|
| **Ring 1** | [arif-fazil.com](https://arif-fazil.com) | **THE SOUL** | ✅ LIVE |
| **Ring 2** | [arifos.arif-fazil.com](https://arifos.arif-fazil.com) | **THE MIND** | ✅ LIVE |
| **Ring 3** | [aaa.arif-fazil.com](https://aaa.arif-fazil.com) | **THE BODY** | ✅ LIVE |

### 🌐 Documentation & Interface
- **Theory (APEX):** [https://apex.arif-fazil.com](https://apex.arif-fazil.com)
- **Unified Wiki:** [https://wiki.arif-fazil.com](https://wiki.arif-fazil.com)
- **Spatial (GEOX):** [https://geox.arif-fazil.com](https://geox.arif-fazil.com)
- **Control Portal:** [https://forge.arif-fazil.com](https://forge.arif-fazil.com)
- **Agent Workspace:** [https://waw.arif-fazil.com](https://waw.arif-fazil.com)

### ⚡ arifOS MCP Endpoints
- **MCP Server:** [https://arifosmcp.arif-fazil.com/mcp](https://arifosmcp.arif-fazil.com/mcp)
- **Health:** [https://arifosmcp.arif-fazil.com/health](https://arifosmcp.arif-fazil.com/health)
- **Tools:** [https://arifosmcp.arif-fazil.com/tools](https://arifosmcp.arif-fazil.com/tools)

**Seal:** VAULT999 | **Verdict:** 999_SEAL | **Alignment:** ΔΩΨ
