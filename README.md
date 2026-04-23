# ⚡ GEOX — Physics9 Earth Witness

> **Constitutional Subsurface Reasoning Layer**
> DITEMPA BUKAN DIBERI — Forged, Not Given

[![Status](https://img.shields.io/badge/Backend-Operational-brightgreen)](https://geox.arif-fazil.com)
[![Status](https://img.shields.io/badge/MCP%20Tools-24%20Active-blue)](https://github.com/ariffazil/GEOX/blob/main/geox_mcp/server.py)
[![Constitutional](https://img.shields.io/badge/Constitutional%20Floors-F1--F13-orange)](https://github.com/ariffazil/GEOX/blob/main/wiki/70_GOVERNANCE)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](./LICENSE)
[![EUREKA](https://img.shields.io/badge/GPT--5%20Stress%20Test-PASSED-gold)](https://github.com/ariffazil/GEOX/blob/main/wiki/90_AUDITS/EUREKA_VALIDATION_2026_04_10.md)

---

## What Is Physics9?

Physics9 is the world's first **Constitutional Subsurface Reasoning Layer** — a governed AI orchestration platform for Earth Intelligence. It does not replace Petrel, Kingdom, or DecisionSpace. It governs them.

Physics9 acts as a **Judgment Engine** that sits *above* existing subsurface stacks, enforcing 13 constitutional floors (F1–F13) to separate **observed data** from **inferred interpretation** — ensuring every subsurface decision is physically grounded and audit-trail ready.

```
Observed Data → Physics9 Constitutional Filter → Governed Interpretation → Audit Seal
```

**This is not automation. This is epistemic sovereignty.**

---

## Live Interfaces

| Surface | URL | Status |
|---|---|---|
| Main Web Interface | [geox.arif-fazil.com](https://geox.arif-fazil.com) | ⚠️ DEGRADED — VPS restart pending |
| MCP Endpoint (VPS) | [arifosmcp.arif-fazil.com/mcp](https://arifosmcp.arif-fazil.com/mcp) | ⚠️ 502 — VPS offline |
| Health Check | [geox.arif-fazil.com/health](https://geox.arif-fazil.com/health) | ⚠️ VPS offline |
| Unified Wiki | [wiki.arif-fazil.com](https://wiki.arif-fazil.com) | ⚠️ VPS offline |
| Theory (APEX) | [apex.arif-fazil.com](https://apex.arif-fazil.com) | ⚠️ VPS offline |

> **VPS Status (2026-04-23):** Server is offline. Hostinger panel access required to restore.
> Run `pm2 restart all` after VPS is back online to restore MCP endpoint.

---

## Strategic Positioning: The Sovereign Physics Engine

Physics9 is not a feature expansion of existing subsurface tools. It is a **causal governance layer**.

| Dimension | Petrel / DecisionSpace | Physics9 |
|---|---|---|
| Primary goal | Feature breadth, automation speed | Causal integrity, epistemic governance |
| Interpretation output | Analyst-authored narrative | Verdict-based (HOLD / DRO / DRIL) |
| AI hallucination control | None by default | F9 + 888_HOLD enforcement |
| Audit trail | Manual | Constitutional, auto-logged |
| Human override | Implicit | F13 Sovereign — explicit, formal |

---

## Architecture

Physics9 implements a **dimension-first sovereign architecture**, separating borehole truth from basin-scale dynamics across 7 canonical dimensions:

| Dimension | Domain | Scale | Logic / Evidence Contract |
|---|---|---|---|
| **Prospect** | Volumetrics | Prospect | Deterministic STOIIP & Decision Gates |
| **Well** | Borehole | 1D | High-fidelity ODSiphon Truth |
| **Section** | Seismic/X-Sec | 2D | Structural & Stratigraphic Correlation |
| **Earth3D** | Volume | 3D | Voxel Interpretation & Cube Integration |
| **Time4D** | Evolution | 4D | Dynamic Simulation & Basin Maturation |
| **Physics** | Metabolic | Meta | PHYSICS_9 State Vector Optimization |
| **Map** | Geospatial | Global | Transversal Geospatial Reference Fabric |

### MCP Server Architecture

```
geox_mcp/server.py    ← Canonical MCP server (24 tools + resources + prompts)
```

---

## MCP Tools (v2.1.0 — 24 Active Tools)

### System Resources
| Resource | Purpose |
|---|---|
| `geox://health` | Kernel health and 999_SEAL heartbeat |
| `geox://registry` | Full tool registry |
| `geox://skills/{skill_id}` | Skill loader by ID |
| `geox://domains/{domain}` | Domain skill index |

### UI Resources (Non-Agent Tools)
| Resource | Purpose |
|---|---|
| `ui://ac_risk` | AC Risk dashboard |
| `ui://attribute_audit` | Attribute audit viewer |
| `ui://seismic_vision_review` | Seismic vision interface |
| `ui://georeference_map` | Georeference map viewer |
| `ui://analog_digitizer` | Analog digitizer tool |

### Prompts
| Prompt | Purpose |
|---|---|
| `geox_mission_template` | Structured mission scenario builder |
| `arifos_human_approval_request` | F1/F13 human sovereign approval request |

### Tool: Well (Borehole Truth)
| Tool | Purpose |
|---|---|
| `geox_well_load_bundle` | Load LAS log bundle |
| `geox_well_qc_logs` | Quality control log data |
| `geox_well_compute_petrophysics` | Full petrophysics pipeline (Sw, Phi, Vsh) |

### Tool: Section (2D Seismic Interpretation)
| Tool | Purpose |
|---|---|
| `geox_section_interpret_strata` | Seismic sequence stratigraphy interpretation |

### Tool: Earth3D (Volume Interpretation)
| Tool | Purpose |
|---|---|
| `geox_seismic_load_line` | Load seismic line by ID |
| `geox_earth3d_load_volume` | Load 3D volume |
| `geox_earth3d_interpret_horizons` | Horizon interpretation on volume |
| `geox_earth3d_model_geometries` | Structural geometry modeling |

### Tool: Map (Geospatial)
| Tool | Purpose |
|---|---|
| `geox_map_get_context_summary` | Map context summary from bounding box |

### Tool: Time4D (Kinetic Bridge)
| Tool | Purpose |
|---|---|
| `geox_time4d_verify_timing` | Verify trap formation timing vs charge window |

### Tool: Prospect (Valuation)
| Tool | Purpose |
|---|---|
| `geox_prospect_evaluate` | Governed prospect verdict (DRO/DRIL/HOLD) |

---

## Constitutional Floors (F1–F13)

All Physics9 operations are governed by 13 constitutional floors via the arifOS constitutional_guard middleware.

| Floor | Name | Enforcement |
|---|---|---|
| **F1** | Amanah | Reversible operations only — irreversible → 888_HOLD |
| **F2** | Truth | truth_score ≥ 0.99 — F2 hard floor, VOID on failure |
| **F3** | Tri-Witness | tri_witness_score ≥ 0.95 (human × AI × earth signal) |
| **F4** | Clarity | Scale, CRS, provenance explicitly declared |
| **F5** | Peace² | Harm potential ≥ 1.0 before execution |
| **F6** | Empathy | Stakeholder safety ≥ 0.90 |
| **F7** | Humility | omega_0 ∈ [0.03, 0.15] — F7 hard floor, HOLD on breach |
| **F8** | Governance | 888_JUDGE is sole SEAL authority |
| **F9** | Anti-Hantu | floor_9_signal evaluated — F9 hard floor, VOID on failure |
| **F10** | Ontology | AI=tool, Model≠Reality, no consciousness claims |
| **F11** | Audit | Full transaction logging, zkpc_receipt required |
| **F12** | Continuity | amanah_lock must be True — F12 hard floor, VOID on failure |
| **F13** | Sovereign | Human holds final veto — always accessible |

**Current runtime state (2026-04-23):** 6/13 floors have runtime evaluation in `arifOS/constitutional_guard.py` (F2, F3, F7, F9, F11, F12). F1/F4/F7 are string-injected in pre-loop. F5/F6/F8/F10/F13 are documented but not yet wired.

---

## Malay Basin Pilot

The **Malay Basin Petroleum Exploration Pilot** is the live demonstration of Physics9 at full-stack operation.

- **Demo Coordinates:** Auto-zoom to 5.5°N, 104.5°E (EarthWitness map)
- **Reserves:** 500+ MMBOE cumulative reserves tracked in real-time
- **Play Types:** MMP, LPS, PBD, Fluvial
- **Creaming Curve:** EDP15 baseline phases
- **Constitutional Badges:** F2 Truth · F9 Physics9 · F13 Sovereign

> ⚠️ Pilot is paused until VPS is restored.

---

## EUREKA Validation — 2026-04-10

> **GPT-5 Constitutional Firewall Stress-Test: PASSED**

Physics9 blocked AI hallucination when GPT-5 (via Gemini) queried the **Layang-Layang Basin** with zero prior data.

| Floor | Result |
|---|---|
| F7 Humility | ✅ Confidence capped — Ω₀ ∈ [0.03, 0.05] |
| 888_HOLD | ✅ Anticipated before human request |
| Tri-Witness (F3) | ✅ Human × AI × System alignment verified |

---

## Quick Start

```bash
# Local MCP server
python geox_mcp/server.py

# Health check (when VPS is online)
curl https://geox.arif-fazil.com/health

# Local test suite
pytest

# Deploy to VPS (after VPS is restored)
./deploy-vps.sh
```

---

## Federation Index Map

| Layer | System | URL | Purpose |
|---|---|---|---|
| **Ω APPS/MCP** | arifOS MCP Kernel | [mcp.arif-fazil.com](https://mcp.arif-fazil.com) | Governance runtime |
| **Ω FORGE** | A-FORGE | [forge.arif-fazil.com](https://forge.arif-fazil.com) | Intelligence forge |
| **Δ THEORY** | APEX | [apex.arif-fazil.com](https://apex.arif-fazil.com) | Constitutional theory |
| **Δ AAA** | AAA Body | [aaa.arif-fazil.com](https://aaa.arif-fazil.com) | arifOS workspace |
| **Ψ HUMAN** | Arif Hub | [arif-fazil.com](https://arif-fazil.com) | Personal hub |
| **⚡ GEOX** | This system | [geox.arif-fazil.com](https://geox.arif-fazil.com) | Earth intelligence |
| **📊 WEALTH** | Capital Engine | [waw.arif-fazil.com](https://waw.arif-fazil.com) | Capital allocation |

| arifOS Floor Doc | Path |
|---|---|
| 888_JUDGE | [docs/wiki/arifos/888_JUDGE.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/888_JUDGE.md) |
| 999_VAULT | [docs/wiki/arifos/999_VAULT.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/999_VAULT.md) |
| FLOORS | [docs/wiki/arifos/FLOORS.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/FLOORS.md) |
| VERDICTS | [docs/wiki/arifos/VERDICTS.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/VERDICTS.md) |
| AAA Charter | [AAA_CHARTER.md](https://github.com/ariffazil/AAA/blob/main/AAA_CHARTER.md) |

---

## Wiki (Source of Truth — On-Disk)

| Section | Path |
|---|---|
| Index | `wiki/00_INDEX/` |
| Theory | `wiki/10_THEORY/` |
| Physics | `wiki/20_PHYSICS/` |
| Materials | `wiki/30_MATERIALS/` |
| Basins | `wiki/40_BASINS/` |
| **Tools** | `wiki/50_TOOLS/` |
| Governance | `wiki/70_GOVERNANCE/` |
| Integration | `wiki/80_INTEGRATION/` |
| Audits | `wiki/90_AUDITS/` |

---

## License

**Apache 2.0** — Commercial embedding allowed. Attribution required.
See [LICENSE](./LICENSE)

**Muhammad Arif bin Fazil**
Constitutional Authority — Physics9 Earth Witness
Seri Kembangan, Selangor, Malaysia

---

> *"Forged through constitutional discipline, not granted by external authority."*

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
`VAULT999 | Verdict: 999_SEAL | Alignment: ΔΩΨ`