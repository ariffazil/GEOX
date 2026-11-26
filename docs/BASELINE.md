# GEOX Phase A Baseline (Measured 2026-11-26)

> Branch: `forge/lifecycle-obs` · Epoch: `2026-11-26` · Status: READ-ONLY BASELINE (zero fixes applied yet)
> Evidence class: `[OBS]` measured live on KVM8 (`/root/GEOX` + `http://127.0.0.1:8081`)

## 1. Git & Deployment Identity `[OBS]`

| Metric | Measured Value |
|---|---|
| Source `git rev-parse HEAD` (`/root/GEOX`) | `3f5f4c8ebd4c71986303160fb94b9b358b6ce4fb` (`geox-3f5f4c8eb`) |
| Live `/health` `git_version` (`:8081`) | `geox-3f5f4c8eb` |
| Live `/health` `version` (surface) | `v2026.10.03` |
| Live `/health` `geox_source_drift` (`/opt/geox`) | `drift: true` (`local_head=68fc6da69...` vs `origin_main=3f5f4c8eb...`) |
| Live `/health` `status` / `registry_state` | `degraded` (`cause=DEPENDENCY`, `arifos=degraded`, `F6=unmeasured`) / `PASS` |
| Live runtime process | `/opt/geox/.venv/bin/python3 -m geox_mcp.server --host 127.0.0.1 --port 8081` |

## 2. Structural & Dependency Metrics `[OBS]`

| Metric | Measured Value | Target (Phase C/D) |
|---|---|---|
| `src/geox_mcp/server.py` size | **4,533 lines** (199,596 bytes) | Split into thin routers (<300 lines each) |
| `profile=mcp-app` registrations in `server.py` | **0** (`resourceUri` count = 1) | >=1 production SEP-1865 MCP App |
| `registry.py` files in repo | **6** (`src/geox_mcp/registry.py`, `src/geox_mcp/tools/registry.py`, `contracts/tools/canonical/registry.py`, `geox/egs/registry.py`, `src/geox/egs/registry.py`, `geox_timeseries/registry.py`) | **1** canonical `registry.py` |
| Live `/tools` count (`:8081`) | **29** (duplicates: `[]`) | Freeze at 29 → consolidate to `<=15` |
| Source `@mcp.tool` defs directly in `server.py` | **38** (internal/auxiliary helpers; duplicates: `[]`) | Consolidate / remove phantom surface |
| `pyproject.toml` mandatory dependencies | **52** (optional groups: `dev: 6`, `pinn: 1`, `seismic: 1`, `all: 14`) | **<10** pure/wheel core deps |
| `.venv` installed distributions (`/root/GEOX/.venv`) | **232** packages (`fastmcp==4.1.4`) | Clean `<30s` cold `uvx` install |
| Top-level directories | **48** (includes 5 legacy UI trees: `apps/`, `geox-gui/`, `static/`, `ui/`, `chat/` + twin `geox/` & `src/`) | ONE `src/geox/` + ONE `ui-apps/` |

## 3. Live 29-Tool Surface & Lifecycle Map `[OBS]`

| Lifecycle Stage | Live Tools (`:8081/tools`, N=29) | Known Gap |
|---|---|---|
| **Exploration** | `geox_basin`, `geox_deep_time`, `geox_map`, `geox_spatial`, `geox_seismic_ingest`, `geox_seismic_interpret`, `geox_seismic_compute`, `geox_contrast_metabolize`, `geox_source`, `geox_observe`, `geox_paleobiodb_query`, `geox_prospect` (screen), `geox_glof` | Public F3 SEG-Y end-to-end test |
| **Appraisal** | `geox_well_ingest`, `geox_well_qc`, `geox_petrophysics`, `geox_geomechanics` | Forensic checks: `datum_shift`, `unit_trap`, `sentinel`, `matrix_paradox`, `age_inversion` |
| **Development** | `geox_grid`, `geox_resqml_io`, `geox_model`, `geox_well` | Well-planning / drilling-hazard evidence |
| **Production** | `geox_temporal` | Production-data ingest, history-match hooks |
| **Abandonment** | *(none dedicated — `geox_geomechanics` / `geox_claim` partial)* | P&A / well-integrity / CCS-MRV mode (`geox_integrity` mode) |
| **Cross-cutting** | `geox_surface_status`, `geox_claim`, `geox_calibration_register_witness`, `geox_extract_display_proxy`, `geox_register_native_source`, `geox_extract_native_trace`, `geox_list_registered_sources` | Forecast-vs-actual calibration ledger + persistent EarthGraph |

## 4. Phase B Entry State `[OBS]`

- `~/.geox/telemetry.jsonl`: **not yet emitting**
- `~/.geox/earthgraph.db`: **not yet persisted** (in-memory only; boots empty)
- `src/geox/obs.py`: **not yet created**
