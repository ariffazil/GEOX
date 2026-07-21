# 🔥 GEOX Earth OS — Architecture v1.0

> **DITEMPA BUKAN DIBERI** — The OS is forged, not given.
> **Architect:** Muhammad Arif bin Fazil (F13 SOVEREIGN) · **Forged:** 2026-07-21
> **Status:** H1 ACTIVE, H2-H8 PLANNED

---

## 0. THE SHIFT

```
BEFORE (MCP GUI)                    AFTER (Earth OS)
─────────────────                   ─────────────────
Tool → MCP → UI → App              Agent → Workspace → State → Evidence → Review → Decision
(button)                            (operating environment)
```

GEOX stopped being "an MCP server with UIs" at 27/30 tools enriched with `_meta.ui.resourceUri`.
What remains is the transformation into an **Earth-native intelligence operating environment.**

---

## 1. HORIZONS MAP

| Horizon | Name | Status | Effort | Depends On |
|---------|------|--------|--------|------------|
| **H1** | P0-P8: GUI Completion | ✅ 90% DONE | ~2 weeks | — |
| **H2** | Workspace Memory | 🔨 IN PROGRESS | ~1 week | H1 |
| **H3** | Knowledge Graph | 📋 PLANNED | ~2 weeks | H2 |
| **H4** | Earth Twin | 📋 PLANNED | ~4 weeks | H3 |
| **H5** | QQQ Runtime | 📋 PLANNED | ~3 weeks | H3 |
| **H6** | Agent Society | 📋 PLANNED | ~3 weeks | H5 |
| **H7** | AAA Mission Control | 📋 PLANNED | ~2 weeks | H2, H5 |
| **H8** | Earth OS Convergence | 📋 PLANNED | ~2 weeks | H2-H7 |

---

## 2. HORIZON 1 — GUI Completion (P0-P8)

### Done This Session
- ✅ `mcp-ui-server` v1.0.0 installed in GEOX .venv
- ✅ 3 broken external URLs fixed (seismic_viewer, basin_explorer, well_desk)
- ✅ Tool enrichment: 7 → 27 tools with `_meta.ui.resourceUri`
- ✅ All 11 GEOX app URLs return HTTP 200
- ✅ Bridge now uses `mcp-ui-server` SDK for proper resource creation

### Remaining
| P# | Item | Est. |
|----|------|------|
| P1 | Wire workspace into tool handlers | 3 days |
| P2 | Evidence visualization components | 3 days |
| P3 | GEOX Flow: tool chain DAG | 5 days |
| P4 | Earth Workspace unified container | 5 days |
| P5 | Agent visibility in cockpit | 1 day |
| P6 | QQQ path-ranking UI | 3 days |
| P7 | AAA AppRenderer integration | 3 days |
| P8 | CSP hardening + fallback HTML + load testing | 2 days |

---

## 3. HORIZON 2 — Workspace Memory

### What It Is
Persistent session state so that "Kinabalu Basin" entered once flows through all subsequent tools.

### Architecture
```
┌─────────────────────────────────────────┐
│          GeoxWorkspace                   │
│  ┌─────────────────────────────────┐    │
│  │ Geological Context              │    │
│  │  basin, play, well_id, field    │    │
│  ├─────────────────────────────────┤    │
│  │ Tool History (last 50 calls)    │    │
│  ├─────────────────────────────────┤    │
│  │ Evidence Stack                  │    │
│  ├─────────────────────────────────┤    │
│  │ Active Apps & Agent Activity    │    │
│  ├─────────────────────────────────┤    │
│  │ H3 Relations (knowledge graph)  │    │
│  ├─────────────────────────────────┤    │
│  │ H5 Hypotheses (QQQ paths)       │    │
│  └─────────────────────────────────┘    │
│                                         │
│  inject_params() — auto-fills tool args │
│  get_context_banner() — UI display      │
│  record_tool_call() — audit trail       │
└─────────────────────────────────────────┘
         │
         ▼
  WorkspaceStore (JSON filesystem)
         │
         ▼
  Future: Supabase → VAULT999 sealed
```

### Implemented
- ✅ `GeoxWorkspace` Pydantic model at `src/geox_mcp/state/workspace.py`
- ✅ `WorkspaceStore` JSON file persistence
- ✅ `inject_params()` auto-fill
- ❌ NOT YET wired into tool handlers (P1)

---

## 4. HORIZON 3 — Knowledge Graph

### What It Is
Instead of 30 disconnected tools, GEOX understands geological relationships:
```
Group H
 ├─ Nuri-1 (well)
 ├─ Malikai (field)
 ├─ Kikeh (field)
 ├─ Pagasa (formation)
 ├─ North Sabah Wedge (structure)
 └─ Stage III inversion (event)
```

### Architecture
```
geox_well_ingest("Nuri-1")
    ↓
workspace.relations["Group H"] = ["Nuri-1", "Malikai", "Kikeh"]
    ↓
geox_basin("Sabah")
    ↓
relations extended: plays, wells, papers, horizons, risks
    ↓
UI renders graph: click Group H → reveals all connected entities
```

### Implementation Path
1. Extend `GeoxWorkspace.relations` (field already exists)
2. Add `extract_relations()` to key tools (basin, well, prospect)
3. Build knowledge graph viewer in cockpit
4. Link to VAULT999 sealed claims

---

## 5. HORIZON 4 — Earth Twin

### What It Is
A time-slider for geological history. Watch subsidence, faulting, inversion, and charge through deep time.

```
Sabah Basin
 ├─ 15 Ma: Rifting, fluvial-lacustrine
 ├─ 10 Ma: Carbonate platforms
 ├─  8 Ma: Stage II inversion
 ├─  5 Ma: Stage III inversion, clastic influx
 └─  0 Ma: Present configuration
```

### Architecture
```
geox_deep_time_state(age_ma=15)
    ↓
geox_basin_backstrip(well_ref="Nuri-1")
    ↓
geox_thermal_maturity_history(well_ref="Nuri-1")
    ↓
Render: 3D block diagram with time slider (CesiumJS)
```

### Dependencies
- `geox_deep_time_state` (Phase Zen)
- `geox_basin_backstrip` (resurrected 2026-07-16)
- `geox_thermal_maturity_history` (resurrected 2026-07-16)
- CesiumJS in earth-volume app

---

## 6. HORIZON 5 — QQQ Runtime

### What It Is
The ARIF differentiator. Not "Question → Answer" but "Question → Paths → Alternatives → Contradictions → Evidence Ranking → Decision."

```
Question: "What caused Group H structure?"
    ↓
Path A: Gravity sliding (confidence 62%)
  ✓ Onlap geometry on seismic
  ✓ Toe-thrust in downdip section
  ✗ No detachment in deep seismic

Path B: Wrench tectonics (confidence 24%)
  ✓ Flower structures mapped
  ✗ No regional strike-slip evidence

Path C: Inversion (confidence 14%)
  ✓ Angular unconformity at 8 Ma
  ✗ No thick syn-rift sequence

Contradictions: Path A vs B — both have structural support
Verdict: HOLD for additional seismic
```

### Implementation Path
1. Leverage existing `geox_falsify` (Kill Matrix K001-K007)
2. Leverage existing `geox_contradiction_scan` (13-type ontology)
3. Build QQQ path-ranking engine
4. Render as decision matrix in cockpit

---

## 7. HORIZON 6 — Agent Society

### What It Is
Specialist agents that challenge each other:
```
ATLAS    → gathers evidence (basin, wells, maps)
SEISMIC  → tests structural hypotheses
PETRO    → tests reservoir quality
BASIN    → tests charge and migration
JUDGE    → challenges all claims
```

### Architecture
```
Human question
    ↓
AAA dispatches to agent swarm
    ↓
Agents run independently, cross-referencing workspace
    ↓
JUDGE agent receives all evidence
    ↓
Synthesizes: contradictions, confidence, HOLD triggers
    ↓
Human reviews multi-agent output
```

### Dependencies
- A-FORGE parallel orchestration (`forge_parallel`)
- arifOS `arif_judge` for constitutional verdict
- Workspace shared state (H2)

---

## 8. HORIZON 7 — AAA Mission Control

### What It Is
AAA transforms from cockpit dashboard into mission control:
```
AAA knows:
  • Active basin (from workspace)
  • Active agents (ATLAS, SEISMIC, PETRO, BASIN, JUDGE)
  • Active workflows (GEOX Flows from P3)
  • Active evidence (evidence stack from H2)
  • Active QQQ hypotheses (from H5)
```

### Architecture
```tsx
// AAA Cockpit — GeoxMissionControl.tsx
import { AppRenderer } from '@mcp-ui/client';

function GeoxMissionControl({ workspace, mcpClient }) {
  return (
    <div className="mission-control">
      <ContextBanner basin={workspace.basin} play={workspace.play} />
      <AgentStatusPanel agents={workspace.agent_activity} />
      <div className="workbench">
        <AppRenderer
          client={mcpClient}
          toolName={activeTool}
          sandbox={{ url: sandboxProxyUrl }}
          toolInput={workspace}
        />
      </div>
      <EvidencePanel stack={workspace.evidence_stack} />
      <QQQPanel hypotheses={workspace.hypotheses} />
    </div>
  );
}
```

---

## 9. HORIZON 8 — Earth OS Convergence

### What It Is
The synthesis of H2-H7 into a single continuous environment:

```
Human enters: "Why is Group H here?"
    ↓
AAA Mission Control (H7) dispatches
    ↓
Agent Society (H6) debates
    ↓
QQQ Runtime (H5) ranks paths
    ↓
Knowledge Graph (H3) reveals relationships
    ↓
Earth Twin (H4) shows time evolution
    ↓
Workspace Memory (H2) persists everything
    ↓
Human sees:
  • Maps (MapLibre via earth-map)
  • Seismic (Cesium via seismic-vision)
  • Wells (WellDesk)
  • Papers (evidence console)
  • Hypotheses (QQQ matrix)
  • Contradictions (falsification dashboard)
  • Risks (prospect studio)
  • Agent debate (agent status panel)
  
All connected. All persistent. All governed.
```

---

## 10. CURRENT STATE — JULY 21, 2026

```
GEOX MCP Apps (H1)    ████████░░ 90%  27/30 tools have UI, 11/11 app URLs live
GEOX Workbench (H2)   ████░░░░░░ 40%  Workspace model built, not yet wired
GEOX Earth OS (H3-H8) ██░░░░░░░░ 20%  Architecture defined, graph model started
```

### Key Files
| File | Purpose |
|------|---------|
| `src/geox_mcp/tools/mcp_apps_bridge.py` | MCP Apps bridge (SEP-1865) — 11 apps, 27 tool enrichments |
| `src/geox_mcp/state/workspace.py` | H2 workspace state — persistent session memory |
| `src/geox_mcp/server.py` | Unified MCP server (3305 lines, 30 tools) |
| `src/geox_mcp/ui/resources.py` | UI resource registration (workspace, gravmag studio) |
| `src/geox_mcp/apps/workbench.py` | Earth workbench registration |
| `/root/GEOX/apps/workbench-v1.html` | Interactive MapLibre map |

### Key URLs
| App | URL | Status |
|-----|-----|--------|
| WellDesk | `https://geox.arif-fazil.com/cockpit/well_context_desk/` | ✅ 200 |
| Seismic Vision | `https://geox.arif-fazil.com/cockpit/seismic_viewer/` | ✅ 200 |
| Earth Volume | `https://geox.arif-fazil.com/apps/earth-volume/` | ✅ 200 |
| Judge Console | `https://geox.arif-fazil.com/apps/judge-console/` | ✅ 200 |
| Basin Explorer | `https://geox.arif-fazil.com/cockpit/basin_explorer/` | ✅ 200 |
| Earth Map | `https://geox.arif-fazil.com/earth` | ✅ 200 |
| Prospect Studio | `https://geox.arif-fazil.com/apps/prospect-ui/` | ✅ 200 |
| Visual Hub | `https://geox.arif-fazil.com/apps/geox-mcp-visual/` | ✅ 200 |
| Catalog | `https://geox.arif-fazil.com/apps/site/catalog.html` | ✅ 200 |

---

## 11. NEXT FORGE SESSION

1. **P1**: Wire `GeoxWorkspace` into GEOX tool handlers (inject_params)
2. **P2**: Build evidence card visualization component
3. **H3**: Seed knowledge graph from existing basin/well data
4. **P7**: Install `@mcp-ui/client` in AAA and wire first `AppRenderer`

---

*Architecture sealed: 2026-07-21 by FORGE (000Ω) under F13 SOVEREIGN direction.*
*DITEMPA BUKAN DIBERI — The Earth OS is forged, not given.*
