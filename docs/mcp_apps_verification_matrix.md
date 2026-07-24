# GEOX MCP Apps Verification Matrix

> **SOT date:** 2026-07-24 · **Live tools:** 32 · **Host shell WellDesk:** `p0-viz.html`  
> **Truth rule:** `resources/read` + readiness tests beat this table.  
> Labels: `READY` = host-usable now · `PARTIAL` = HTML serves, flow incomplete · `PLANNED` · `DEPRECATED`

## Primary host apps (MCP iframe)

| Widget URI | Backing tool(s) | HTML on disk | Host bridge | Epistemic | Status |
|---|---|---|---|---|---|
| `ui://geox/well-desk` | `geox_well_desk`, `geox_petrophysics`, `geox_well_ingest`, `geox_well_qc`, `geox_lem_predict` | `apps/well-desk/p0-viz.html` | SEP-1865 `ui/initialize` | SYNTHETIC badge | **READY** (P0+) |
| `ui://geox/basin-explorer` | `geox_basin`, `geox_basin_backstrip`, … | `static/gui/basin_explorer/index.html` | tool meta | — | **READY** |
| `ui://geox/judge-console` | `geox_falsify`, `geox_evidence`, … | `apps/judge-console/index.html` | tool meta | — | **READY** |
| `ui://geox/earth-map` | map chain | `apps/workbench-v1.html` | tool meta | — | **READY** |
| `ui://geox/prospect-studio` | `geox_prospect` | `apps/prospect-ui/index.html` | tool meta | — | **READY** |
| `ui://geox/risk-console` | `geox_claim`, … | `apps/judge-console/index.html` | tool meta | — | **READY** |
| `ui://geox/visual-hub` | visual tools + workspace | `apps/geox-mcp-visual/index.html` | tool meta | — | **READY** |
| `ui://geox/seismic-vision` | seismic ingest/interpret | `static/gui/seismic_viewer/index.html` | tool meta | — | **READY** |
| `ui://geox/earth-volume` | subsurface / deep time | `apps/earth-volume/index.html` | tool meta | — | **READY** |
| `ui://geox/geoprobe` | geomechanics / prospect | `apps/prospect-ui/index.html` | tool meta | — | **READY** |
| `ui://geox/catalog` | `geox_surface_status` | `apps/site/catalog.html` | tool meta | — | **READY** |

## Public browser URLs (Caddy `/var/www/html/geox`)

| URL | Serves | Status |
|---|---|---|
| `https://geox.arif-fazil.com/apps/well-desk/index.html` | Full modular WellDesk | **READY** (deployed 2026-07-24) |
| `https://geox.arif-fazil.com/apps/well-desk/p0-viz.html` | Host shell twin | **READY** |
| MCP `ui://geox/well-desk` | **p0-viz only** (not multi-file index) | **READY** for host |

## Gate tests

```bash
cd /root/GEOX && PYTHONPATH=src pytest tests/test_mcp_apps_readiness.py -q
# Target: 0 failed (expect 32 tools, all UI-bound)
```

## Explicit non-goals / residual

| Item | Status |
|---|---|
| Real LAS hydrate into p0-viz tracks | PARTIAL — needs tool-result curves |
| `generate` vaulted evidence_refs | OPEN |
| ChatGPT live visual QA re-run | DEFERRED |
| Multi-file `index.html` inside MCP iframe | NOT supported (relative scripts / CSP) |

## Deprecated / planned

| ID | Status |
|---|---|
| attribute-audit | DEPRECATED |
| georeference-map | DEPRECATED |
| seismic-vision-review | DEPRECATED |
| analog-digitizer | PLANNED |

---

*Rewritten 2026-07-24 after F2 audit — prior "all READY" matrix overclaimed 33-tool surface.*
