# GEOX Earth Witness

> **DITEMPA BUKAN DIBERI** — *Forged, Not Given*  
> **Constitutional Geoscience Platform v0.5.0**

[![Seal](https://img.shields.io/badge/SEAL-DITEMPA%20BUKAN%20DIBERI-gold)](./wiki/90_AUDITS/999_SEAL.md)
[![Version](https://img.shields.io/badge/version-0.5.0-blue)](./CHANGELOG.md)
[![Status](https://img.shields.io/badge/status-🟡%20PARTIAL-yellow)](./DEPLOYMENT_STATUS.md)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

**Live URL:** https://geox.arif-fazil.com

GEOX is a constitutional geoscience platform that uses multi-agent architecture and tri-witness consensus to deliver verified geological interpretations. Built with Python/FastMCP backend and React/TypeScript frontend, it enforces 13 constitutional floors (F1-F13) including 888_HOLD safety vetoes.

---

## 🚀 Quick Start

### Access the Live Platform
```bash
# Visit the main interface
curl https://geox.arif-fazil.com

# Health check
curl https://geox.arif-fazil.com/health
# Output: OK

# MCP endpoint (use with FastMCP CLI)
fastmcp list https://geox.arif-fazil.com/mcp
```

### Connect Claude Desktop
```json
{
  "mcpServers": {
    "geox": {
      "command": "fastmcp",
      "args": ["run", "https://geox.arif-fazil.com/mcp"]
    }
  }
}
```

### Run Locally
```bash
# Clone and setup
git clone https://github.com/Ariffazil/GEOX.git
cd GEOX

# Backend (requires uv)
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
python geox_mcp_server.py

# Frontend (requires node)
cd geox-gui
npm install
npm run dev
```

---

## 🏛️ Architecture

### Host-Agnostic Design
GEOX implements a three-layer architecture that separates domain logic from transport adapters:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOST PLATFORMS                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Claude      │  │ Copilot     │  │ Custom      │  │ FastMCP Horizon     │ │
│  │ Desktop     │  │ Studio      │  │ MCP Client  │  │ Cloud               │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                │                    │            │
└─────────┼────────────────┼────────────────┼────────────────────┼────────────┘
          │                │                │                    │
          ▼                ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TRANSPORT ADAPTERS (Adapters)                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐ │
│  │ FastMCP Adapter  │  │ Copilot Adapter  │  │ OpenAI Adapter (planned)   │ │
│  │ (SSE/HTTP)       │  │ (Teams/365)      │  │                            │ │
│  └─────────┬────────┘  └─────────┬────────┘  └─────────────┬──────────────┘ │
│            │                     │                         │                │
└────────────┼─────────────────────┼─────────────────────────┼────────────────┘
             │                     │                         │
             ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CORE DOMAIN (Host-Agnostic)                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Tool Logic (12+ tools: seismic, petrophysics, pilot demo)            │  │
│  │  Type Contracts (Pydantic models for all data structures)             │  │
│  │  App Manifest (JSON Schema for host integration)                      │  │
│  │  UI Event Bus (JSON-RPC bridge for React frontend)                    │  │
│  │  Constitutional Services (F1-F13 enforcement)                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
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
| Backend (VPS) | ✅ Operational | MCP Server v0.5.0 responding |
| Frontend (VPS) | 🟡 Pending | Needs Docker rebuild |
| Horizon Cloud | 🟡 Building | numpy fix committed |
| MCP Tools | ✅ 13 tools | All phases implemented |
| Malay Basin Pilot | ✅ Backend ready | GUI needs refresh |

**Next Actions:**
1. Force rebuild VPS Docker image (includes latest GUI)
2. Push numpy fix to trigger Horizon rebuild
3. Verify Pilot tab visibility in production

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
