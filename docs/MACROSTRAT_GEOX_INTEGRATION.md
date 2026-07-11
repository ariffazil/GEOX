# Macrostrat → GEOX Integration Map

> **Forged:** 2026-07-11  
> **Status:** Blueprint — not implemented  
> **MCP Adapter + GEOX Integration Strategy**

---

## 1. Macrostrat API Surface (v2)

| REST Endpoint | Purpose | MCP Tool Name |
|---|---|---|
| `/units` | Stratigraphic units by location/name | `macrostrat_units` |
| `/columns` | Column locations, groups, areas | `macrostrat_columns` |
| `/sections` | Gap-bound packages | `macrostrat_sections` |
| `/geologic_units/map` | Geologic map units at location | `macrostrat_geologic_map` |
| `/geologic_units/map/legend` | Map legend data | `macrostrat_map_legend` |
| `/defs/lithologies` | Lithology dictionaries | `macrostrat_lithologies` |
| `/defs/intervals` | Time interval definitions | `macrostrat_intervals` |
| `/defs/columns` | Column definitions | `macrostrat_column_defs` |
| `/age_model` | Column age-depth models | `macrostrat_age_model` |
| `/fossils` | Paleobiology collections | `macrostrat_fossils` |
| `/paleogeography` | Plate-tectonic paleogeography | `macrostrat_paleogeography` |
| `/measurements` | Geochemical measurements | `macrostrat_measurements` |

---

## 2. Adapter Architecture

```
┌─────────────┐     MCP JSON-RPC      ┌──────────────────┐     REST/HTTPS      ┌─────────────┐
│  GEOX MCP   │ ◄──────────────────► │  macrostrat-mcp   │ ────────────────► │  Macrostrat  │
│  (existing) │     tools/call        │  (adapter server) │    api/v2/*       │  API (live)  │
└──────┬──────┘                      └──────────────────┘                    └─────────────┘
       │                                                                                        
       │ GEOX internal (Python import)
       ▼
┌──────────────────┐
│  GEOX Basin      │
│  Panel / Map     │
│  Rendering       │
└──────────────────┘
```

### Adapter Server (FastMCP, Python, 200 lines)

```python
from fastmcp import FastMCP
import httpx

macrostrat = FastMCP("macrostrat-mcp")
BASE = "https://macrostrat.org/api/v2"

@macrostrat.tool()
async def macrostrat_units(
    lat: float | None = None,
    lng: float | None = None,
    col_id: int | None = None,
    strat_name: str | None = None,
    age: int | None = None,
    response: str = "json",
) -> dict:
    """Search Macrostrat stratigraphic units by location, column, or name."""
    params = {"format": "json"}
    if lat is not None and lng is not None:
        params["lat"] = lat; params["lng"] = lng
    if col_id: params["col_id"] = col_id
    if strat_name: params["strat_name"] = strat_name
    if age: params["age"] = age
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/units", params=params)
        return r.json()

# ... same pattern for all 12 endpoints
```

---

## 3. GEOX Integration Matrix

| Macrostrat Data | GEOX Tool That Uses It | GEOX Domain | Interactive Panel |
|---|---|---|---|
| Stratigraphic units | `geox_basin` (stratigraphy mode) | Basin analysis | Basin strat column viewer |
| Column locations | `geox_map_scene_plan` | Map layers | Map overlay of column points |
| Geologic map tiles | `geox_map_render_preview` | Map rendering | Geologic basemap layer |
| Age-depth models | `geox_deep_time_state` | Deep time | Age-depth correlation panel |
| Lithology defs | `geox_biostrat_falsify` | Biostratigraphy | Lithology legend overlay |
| Paleogeography | `geox_basin` (plate mode) | Basin reconstruction | Plate reconstruction overlay |
| Geologic map legend | `geox_map_export_package` | Map export | Legend in exported packages |
| Column sections | `geox_sequence` | Sequence stratigraphy | Column correlation panel |

---

## 4. MCP App UI Resource (GEOX Basin Panel)

```yaml
resources:
  - name: "geox_basin_panel"
    uri: "ui/basin-panel.html"
    mimeType: "text/html;profile=mcp-app"
    _meta:
      ui:
        domain: "geox"
        csp:
          connect_domains: ["geox.arif-fazil.com", "macrostrat.org"]
          resource_domains: ["geox.arif-fazil.com"]
```

The GEOX Basin Panel MCP App renders:
1. **Map** — MapLibre with Macrostrat geologic basemap overlay
2. **Strat column** — Interactive column viewer from Macrostrat units
3. **Age-depth** — Chart from Macrostrat age model
4. **Correlation** — Side-by-side column comparison

### UI Hydration Flow

```
1. User asks "show Malay Basin stratigraphy"
2. GEOX calls macrostrat_units(lat=5.5, lng=114.5)
3. GEOX calls geox_basin(mode="profile", name="Malay Basin")
4. GEOX tool returns _meta with ui_resource = "geox://resources/basin/..."
5. MCP Host opens iframe → GEOX Basin Panel
6. Panel receives tool-input notification with Macrostrat data
7. Panel renders interactive strat column + map overlay
8. User clicks a unit → Panel calls macrostrat_units(col_id=x)
9. Panel opens external link to Macrostrat column page
```

---

## 5. Implementation Priority

| Priority | Item | Effort | Dependencies |
|---|---|---|---|
| P0 | `macrostrat-mcp` adapter server | 1 day | FastMCP, httpx |
| P1 | Register adapter in A-FORGE registry | 1 hr | A-FORGE affordances.yaml |
| P2 | Integrate macrostrat_units into `geox_basin` stratigraphy mode | 4 hr | GEOX basin engine |
| P3 | Integrate Macrostrat map tiles into `geox_map_scene_plan` | 4 hr | GEOX map tools |
| P4 | GEOX Basin Panel MCP App (HTML + JS) | 2 days | MapLibre, Chart.js |
| P5 | Full double-iframe with UI hydration | 3 days | MCP Apps SDK |

---

## 6. GEOX + Macrostrat: What This Enables

| Before | After |
|--------|-------|
| GEOX has Sabah/East Malaysia data only | GEOX gets global stratigraphy + columns + lithology |
| Basin panel shows empty background | Basin panel shows Macrostrat geologic basemap |
| Manual strat lookup | Auto-populated column data from lat/lng |
| No age-depth defaults | Macrostrat age model as prior |
| No lithology standards | Macrostrat lithology dictionary |
| No global correlation | Correlation with 80k+ Macrostrat columns |
| Static PDF export | Interactive column correlation |

**CC-BY 4.0 license** — Macrostrat data must be attributed. No usage restrictions.

