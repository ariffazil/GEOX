# GEOX MCP Audit — Final Report
**Date:** 2026-06-29
**Auditor:** FORGE (A-FORGE)
**Scope:** `/root/geox/src/geox_mcp/server.py`, `registry.py`, `resources/__init__.py`, `prompts/__init__.py`
**MCP Spec Reference:** modelcontextprotocol.io/specification/2025-06-18

---

## Executive Summary

GEOX MCP server is **operationally healthy** — all 6 federation organs alive, 45 MCP tools registered, 57 resources wired, 10 prompts defined. However, there are **7 spec violations and 4 implementation gaps** that need fixing.

| Category | Count | Severity |
|----------|-------|----------|
| MCP Spec Violations | 7 | HIGH |
| Implementation Gaps | 4 | MEDIUM |
| Tool Naming Inconsistencies | 3 | LOW |
| Documentation Issues | 2 | LOW |

---

## 1. CANONICAL vs MCP TOOL GAP

**Finding:** Confusion between canonical surface (what GEOX *should* expose) and actual MCP decorators (what GEOX *does* expose).

```
MCP @mcp.tool decorators:     45 tools
Registry canonical total:     79 tool names in registry.py
Phase 2.1 canonical surface:  30 tools (26 surface + 4 internal)
Phase 2.1 live surface:       26 tools (14 surface + 12 EGS via register_egs_tools)
```

**19 MCP-only tools** (in decorators, NOT in Phase 2.1 canonical surface):
```
geox_bathymetry_ingest       geox_heatflow_query        geox_satellite_catalog
geox_climate_reanalysis      geox_hydrology_query       geox_space_weather
geox_earthquake_catalog      geox_judgment_preflight    geox_stress_query
geox_erddap_query            geox_ocean_query           geox_uk_petroleum_query
geox_geochem_query           geox_paleomag_query
geox_geology_map_query       geox_plate_reconstruct
geox_gravity_change_query    geox_relief_ingest
geox_gravity_screen
```

**Assessment:** These 19 tools are legitimate GEOX operations (earth data ingestion, catalog queries) but were not part of the Phase 2.1 canonical surface definition. They are **not spec violations** — they work, they're just not in the canonical "public API" list. Recommend: update `registry.py` canonical comments to clarify that these are "extended domain tools" outside the 30-tool canonical surface, OR promote them to canonical surface.

**53 canonical-only tools** (in registry.py, NOT in MCP decorators):
- Internal plumbing tool names (not exposed via MCP)
- Deprecated EGS tool names (e.g., `geox_egs_seismic_compute` → use `geox_seismic_compute`)
- Planned/unimplemented stubs (e.g., `geox_doctrine_*`)
- Sub-tool names wrapped by mode-based entry points (e.g., `geox_basin_profile` → `geox_basin(mode='profile')`)

**Not a problem** — these are internal or deprecated.

---

## 2. CRITICAL: 9 Resource Templates Using `mcp.resource()` Instead of `mcp.resource_template()`

**MCP Spec:** URIs with `{param}` placeholders MUST use `mcp.resource_template()`. Static URIs use `mcp.resource()`.

**Current state in `resources/__init__.py`:** All 9 templates use `mcp.resource()` — **spec violation**.

| URI | Handler |
|-----|---------|
| `tree777://skills/geox/{name}` | `geox_tree777_skill` |
| `tree777://geo/concepts/{name}` | `geox_tree777_concept` |
| `tree777://geo/scars/{name}` | `geox_tree777_scar` |
| `geox://resources/{category}/{name}` | `geox_resource` |
| `geox://render/surfaces/{surface_id}` | `geox_render_surface` |
| `geox://render/cubes/{volume_id}/{orientation}/{slice_index}` | `geox_render_cube_slice` |
| `geox://render/payload-schema/{_version}` | `geox_render_payload_schema` |
| `geox://render/cubes/{cube_id}/manifest` | `geox_cube_manifest` |
| `geox://render/cubes/{cube_id}/lod/{lod}/brick/{ix}/{iy}/{iz}` | `geox_cube_brick` |

**Fix required:**
```python
# WRONG (current)
mcp.resource("geox://render/surfaces/{surface_id}", description=...)(geox_render_surface)

# CORRECT (per MCP spec)
mcp.resource_template("geox://render/surfaces/{surface_id}", description=...)(geox_render_surface)
```

**Impact:** MCP clients expecting template URI behavior may get incorrect routing or unable to resolve parameterized URIs.

---

## 3. CRITICAL: `geox_query_macrostrat` Missing `description=` in Decorator

**MCP Spec:** All tools MUST have a `description` field in their decorator for client discovery.

**Current:**
```python
@mcp.tool(name="geox_query_macrostrat")  # MISSING description=
async def geox_query_macrostrat(
    basin_name: str = "",
    mode: str = "macrostrat_units",
    ...
```

**All other 44 tools** have `description` fields. This is the only one missing.

---

## 4. HIGH: 10 Prompts Not Registered with MCP

**File:** `src/geox_mcp/prompts/__init__.py` (361 lines, 17,397 bytes)

**Current state:** 10 prompt string constants defined:
```
GEOX_SENSE_PROMPT           GEOX_INTERPRET_PROMPT        GEOX_RED_TEAM_REVIEWER_PROMPT
GEOX_QC_PROMPT              GEOX_UI_EXPLAIN_PANEL_PROMPT  GEOX_REPORT_WRITER_PROMPT
GEOX_LITERATURE_TO_CLAIMS_PROMPT  GEOX_BASIN_SCREEN_PROMPT  GEOX_ABSTRACTION_GUARD_PROMPT
```

**Problem:** `prompts/__init__.py` is imported in `server.py` but prompt constants are **never registered** with the MCP server. `prompts/__init__.py` has **zero** `@mcp.prompt` decorators — they're just Python string constants.

**MCP Spec:** `prompts/list` must return all available prompts. Without registration, MCP clients cannot discover GEOX prompts.

**Note:** The 3 canonical prompts (`GEOX_SENSE_PROMPT`, `GEOX_QC_PROMPT`, `GEOX_INTERPRET_PROMPT`) are referenced in the file header but not registered. The file header says they should be the 3 domain prompts for Earth evidence.

---

## 5. MEDIUM: Missing Utility Protocol Implementations

Per MCP spec (2025-06-18), these features should be implemented:

| Feature | Status | Notes |
|---------|--------|-------|
| `ping` handler | ❌ Missing | No `mcp.add_method("ping", ...)` |
| `progressToken` on slow tools | ❌ Missing | No tool uses progressToken. Slow tools: `geox_basin`, `geox_seismic_ingest`, `geox_deep_time_state`, `geox_subsurface_model` |
| `notifications/cancelled` handler | ❌ Missing | No cancellation handling |
| `elicitation/create` | ❌ Missing | Available but not wired |
| `sampling/createMessage` | ❌ Missing | Available but not wired |
| `roots/list` handler | ❌ Missing | Available but not wired |
| Pagination on `resources/list` | ✅ Implemented | `cursor` keyword found |

**Slow tools that need `progressToken`:**
- `geox_basin` — basin profiling, macrostrat, deep time (can take 10+ seconds)
- `geox_seismic_ingest` — SEG-Y loading
- `geox_deep_time_state` — Earth State Vector computation
- `geox_subsurface_model` — joint inversion, gravity/mag

---

## 6. LOW: `geox_query_macrostrat` Docstring Notes `alias` But Has No Explicit Handler

The tool docstring says:
> "This is an alias for `geox_basin_profile(mode='macrostrat_units'|'macrostrat_columns')`"

But `geox_basin_profile` is not a standalone MCP tool — it's a mode of `geox_basin`. This is **documentation inconsistency**, not a bug. The alias works because it maps to the correct `geox_basin` mode internally.

---

## 7. LOW: 57 Resources Registered, But Only 4 Are Static (No Templates)

Of the 57 `mcp.resource()` registrations:
- **4 static resources** (`geox://reality/context`, `geox://identity`, `geox://registry/apps`, `geox://profile/status`)
- **9 template resources** (using `{param}`) — all 9 are **spec violations** (should be `mcp.resource_template()`)
- **44 schema-index resources** (e.g., `geox://earthquake/usgs_summary`) — these return a URI string, not live data. Per MCP docs: "Schema index" resources returning just a URI may be acceptable, but the pattern is unusual.

**Schema-index resources** (44 URIs like `geox://stratigraphy/macrostrat_units`) return a string like `"geox://stratigraphy/macrostrat_units"` — the resource URI itself. This is degenerate — the client already knows the URI. These appear to be **documentation/index resources** rather than live data resources. Consider:
1. Returning actual schema data (JSON schema object) instead of the URI string
2. Converting to `prompts` if they're meant to guide LLM behavior
3. Removing if redundant with `resources/list` index

---

## 8. Implementation Verification

```
✅ arifos:8088          alive
✅ aforge:7071          alive
✅ aaa:3001             alive
✅ geox:8081            alive (v2026.06.22-phase2, geox-5f5c20ff)
✅ wealth:18082         alive
✅ well:18083           alive
```

**GEOX server.py (2665 lines):**
- 45 `@mcp.tool` decorators confirmed
- `register_resources(mcp)` called at line ~1022
- `register_egs_tools(mcp)` called at line ~1005
- 0 `@mcp.prompt` decorators
- 0 `@mcp.resource_template` decorators (correct for static resources, but wrong for 9 templates)
- 57 `mcp.resource()` registrations (4 static + 9 template violations + 44 schema-index)
- Prompts module imported but not registered with MCP

---

## 9. Recommended Fixes (Priority Order)

### P0 (Spec Violations — Fix Immediately)
1. **Fix 9 resource templates** — change `mcp.resource(uri with {param})` → `mcp.resource_template(uri with {param})` in `resources/__init__.py`
2. **Add `description=` to `geox_query_macrostrat`** decorator

### P1 (Functional Gaps)
3. **Register 10 prompts with MCP** — add `@mcp.prompt` decorators in `prompts/__init__.py` OR register programmatically in `server.py`
4. **Add `progressToken` to slow tools** — `geox_basin`, `geox_seismic_ingest`, `geox_deep_time_state`, `geox_subsurface_model`

### P2 (Protocol Completeness)
5. **Add `ping` handler** — `mcp.add_method("ping", handler)`
6. **Add cancellation handler** — `mcp.add_method("notifications/cancelled", handler)`
7. **Consider adding `roots/list`** — scope file access for well/seismic data

### P3 (Documentation)
8. **Clarify 19 MCP-only tools** — update `registry.py` comments to explain these are "extended domain" tools outside the 30-tool canonical surface
9. **Review 44 schema-index resources** — determine if they should return live schema data instead of URI strings

---

## 10. Evidence

- `server.py` line count: 2665
- `registry.py` line count: ~500
- `resources/__init__.py`: 1619 lines, 65,781 bytes
- `prompts/__init__.py`: 361 lines, 17,397 bytes
- MCP decorator count: 45 `@mcp.tool`, 0 `@mcp.prompt`, 0 `@mcp.resource_template`
- Resource registration count: 57 `mcp.resource()` calls (4 static + 9 template violations + 44 schema-index)
- Tool naming gap: 19 MCP-only, 53 canonical-only (internal/deprecated/stub)

---

**DITEMPA BUKAN DIBERI** — Audit complete. Evidence forged, not given.