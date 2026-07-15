# GEOX MCP Apps & GUI Readiness Analysis

> **DITEMPA BUKAN DIBERI**
> Forged: 2026-07-10 | Classification: FULL_AUDIT

---

## Hybrid Surface Classification

| Category | Count | Includes |
|----------|-------|----------|
| **Canonical** | 40 | Well pipeline, seismic, basin, prospect, simulation, maps |
| **Diagnostic** | 21 | Health, AI/vision, audit, benchmark |
| **Legacy** | 8 | Superseded aliases (3d_model, wealth_bridge, well_tie) |
| **Internal** | 12 | EGS evidence governance system |
| **Phantom** | 0 | None detected |

**Hybrid surface = 61 tools** (40 canonical + 21 diagnostic). Legacy/internal hidden from public MCP surface.

---

## MCP Apps Readiness Matrix

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Apps exist | ✅ | 12+ apps in `apps/` (well-desk, seismic, basin, prospect-ui, etc.) |
| Apps served via HTTPS | ✅ | `geox.arif-fazil.com/apps/well-desk/` → 200 OK |
| App implements SEP-1865 | ✅ | `MCPBridge.js` has full `ui/initialize`, `tools/call`, `ui/update-model-context` |
| App has manifest | ✅ | `manifest.json` with schema v1.0, resource_uri, capabilities |
| FastMCP installed | ✅ | 3.4.2 |
| `_meta.ui.resourceUri` on tools | ❌ | No tool registers `_meta` with `ui.resourceUri` |
| `ui://` resource handler | ✅ partial | Legacy seismic viewer has pattern but no active FastMCP handler |
| MCP endpoint reachable | ✅ | Port 8081, health passes |

**Result: MCP Apps ready at the app layer, missing only FastMCP-side wiring.**

---

## MCP GUI Readiness Matrix

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Web GUI exists | ✅ | `geox-gui/` — React/Vite/Cesium/D3/MapLibre |
| GUI served via HTTPS | ✅ | `geox.arif-fazil.com` returns 200 |
| GUI has operator dashboard | ✅ | Well-desk dashboard, geox-dashboard.html |
| GUI links to MCP Apps | ✅ | apps/ directory has manifest linking to geox.arif-fazil.com |
| GUI published as MCP App | ❌ | No `apps.json` manifest for agent discovery |
| Operator console exists | ❌ | No single-entry operator console linking all apps |

**Result: GUI functional but not agent-discoverable. Missing operator console.**

---

## What's Needed for "Enterprise Ready"

### Phase A — Surface Alignment (today)
1. Write `tools.json` with canonical+diagnostic lists
2. Update `.well-known/agent.json` with `tools_manifest` + `apps_manifest` links
3. Update `llms.txt` with canonical tool list

### Phase B — MCP Apps Wiring (1 session)
1. Add `_meta.ui.resourceUri` to well tools (well_ingest, petrophysics, sequence)
2. Register `ui://well-desk/index.html` resource handler on FastMCP
3. Write `apps.json` manifest
4. Serve apps from unified base path

### Phase C — Operator Console (1 session)
1. Build minimal HTML dashboard: tool list, health, links to each MCP App
2. Add to `apps.json`
3. Wire seismic viewer and basin explorer same pattern

---

## File Changes Required

| File | Action |
|------|--------|
| `tools.json` | **Create** — canonical+diagnostic classification |
| `.well-known/agent.json` | **Update** — add tools_manifest, apps_manifest |
| `llms.txt` | **Update** — canonical tool list, app links |
| `apps.json` | **Create** — MCP Apps manifest |
| `geox_mcp/server.py` | **Update** — add `_meta.ui.resourceUri` + `ui://` handler |
| `geox-gui/operator-console.html` | **Create** — minimal operator dashboard |

---

## Testing Protocol

1. `tools/list` via FastMCP → matches `tools.json`
2. `HTTP GET` each app URL → 200 + non-empty
3. Well pipeline round-trip: ingest → QC → petrophysics → well-desk app renders same well ID
4. MCP Inspector validates `_meta.ui.resourceUri` is present on canonical tools

---

## Summary

GEOX is **functionally complete** for MCP Apps. The apps exist, the protocol is implemented, the GUI is live. The gap is three FastMCP-side changes and two discovery files. Estimate: **2-3 hours** to close.

Proceed: **Phase A → Phase B → Phase C**.
