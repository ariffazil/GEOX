# GEOX MCP Apps — Host-Agnostic Geoscience Platform

> **Version:** v1.0.0-draft · **Status:** 🔐 SEALED ✅  
> **Motto:** *DITEMPA BUKAN DIBERI* — Forged, not given.

---

## 1. Overview
GEOX is an application system designed to surface high-fidelity geological and geophysical capabilities directly within AI workflows. It enables interactive 3D seismic viewing, basin exploration, and well context analysis inside hosts like **Microsoft Copilot**, **ChatGPT**, and **Claude**.

### The Earth Witness Mandate

GEOX is the **Earth Witness organ** in the arifOS constitutional federation. It serves as the **reality gatekeeper** for all geoscience operations: every reasoning output, every structural interpretation, and every subsurface decision must be:

- ✅ **Physically possible** (thermodynamics, rock mechanics)
- ✅ **Geospatially grounded** (verified coordinates, CRS, jurisdiction)
- ✅ **Consistent with world-state evidence** (seismic, well data, outcrops)
- ✅ **Petrophysically grounded in well logs** before pay/prospect verdicts.

> *GEOX prevents AI from making physically impossible claims about the Earth by enforcing constitutional verification on every geoscience output.*

---

## 2. Core Features

- **Host-Agnostic UI**: Build once (Web Shell), render in ChatGPT (Iframe), Copilot (Adaptive Card/Link), or standalone.
- **Physical Grounding**: Every claim is verified by the **Theory of Anomalous Contrast (ToAC)**.
- **Hardened Governance**: Mandatory **888_HOLD** triggers for unphysical results (e.g., $Sw > 1.0$).
- **MCP Native**: Plugs into any host supporting the Model Context Protocol.

---

## 3. Architecture Snapshot
GEOX follows a **Sovereign Core** pattern where the domain logic and UI are isolated from AI-specific vendor SDKs using **Host Adapters**.

Refer to [LLM_WIKI.md](LLM_WIKI.md) for deep technical specifications and the `wiki/` directory for theoretical foundations.

---

## 4. Repo Structure
- `/arifos/geox/physics/`: Core petrophysical and geophysical models (Archie, Simandoux, Indonesia).
- `/arifos/geox/apps/`: App manifests and logic.
- `/arifos/geox/adapters/`: Host-specific translation layers (OpenAI, Copilot).
- `/geox-gui/`: React/TypeScript microfrontend source.
- `/wiki/`: Deep architectural and geological knowledge base (ToAC, RATLAS, 13 Floors).

---

## 5. Quickstart
1. **Requirements**: Python 3.10+, Node.js 18+.
2. **Install**: `pip install -e .` & `cd geox-gui && npm install`.
3. **Run MCP Server**: `python geox_mcp_server.py`.
4. **Dev GUI**: `cd geox-gui && npm run dev`.

---

## 6. Current Host Targets
- **Claude Desktop**: Full L4 support (Native MCP Apps).
- **Microsoft Copilot**: L2 (Adaptive Cards) + L4 (External Deep Links).
- **ChatGPT Apps**: L3/L4 support (via OpenAI Apps SDK Adapter).

---

## 7. Documentation Map
| File | Purpose |
| :--- | :--- |
| **LLM_WIKI.md** | Canonical architecture, contracts, and internal memory. |
| **CHANGELOG.md** | Reverse chronological list of notable changes. |
| **TODO.md** | Actionable task queue for the current sprint. |
| **ROADMAP.md** | Strategic phases and milestones. |

---

**Policy:** *DITEMPA BUKAN DIBERI* - All changes must honor the F1-F13 Constitutional Floors.
