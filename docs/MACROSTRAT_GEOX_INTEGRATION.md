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

@macrostrat.tool(
    output_schema=GEOX_CLAIM_ENVELOPE_SCHEMA,
    app=AppConfig(resourceUri="ui://geox/workbench-v1.html"),
)
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
        return {
            "content": [{"type": "text", "text": f"Found {len(r.json().get('data', []))} units"}],
            "structuredContent": stamp_claim_envelope(r.json()),
        }

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

### 4.1 Resource Registration

All GEOX MCP App Views use a single fixed `ui://` resource with a pinned MIME type:

```python
# src/geox_mcp/apps/workbench.py
MCP_APPS_RESOURCE_MIME = "text/html;profile=mcp-app"  # pin, don't guess

@mcp.resource(
    "ui://geox/workbench-v1.html",
    mime_type=MCP_APPS_RESOURCE_MIME,
    app=AppConfig(
        resourceUri="ui://geox/workbench-v1.html",
        visibility=["app", "model"],
    ),
)
def geox_workbench() -> str:
    return read_bundle("apps/workbench-v1.html")
```

Tool registration via `register_tools_on_server()` passes `AppConfig` centrally:

```python
_WITNESS_APPS = {
    name: AppConfig(
        resourceUri="ui://geox/workbench-v1.html",
        visibility=["app", "model"],
    )
    for name in (
        "geox_map_context_scene",
        "geox_seismic_compute",
        "geox_horizon_contrast_surface",
        "geox_subsurface_generate_candidates",
        "geox_prospect_evaluate",
    )
}
```

**MIME constant:** `text/html;profile=mcp-app` matches the value exported by
`@modelcontextprotocol/ext-apps → RESOURCE_MIME_TYPE`. FastMCP (Python) does not
expose this constant, so it is hard-coded centrally in `workbench.py`.

### 4.2 Tool Metadata (structuredContent channel)

Every GEOX governed tool returns BOTH channels — LLM-readable text and GUI-ready structured:

```python
@mcp.tool(
    name="geox_query_macrostrat",
    output_schema=GEOX_CLAIM_ENVELOPE_SCHEMA,
    app=AppConfig(resourceUri="ui://geox/workbench-v1.html"),
)
async def geox_query_macrostrat(
    lat: float, lng: float
) -> dict:
    """Query Macrostrat and return a governed claim envelope."""
    raw = await _fetch_macrostrat(lat, lng)
    envelope = stamp_claim_envelope(raw)  # F2 TRUTH, F11 AUDIT
    return {
        # LLM channel — prose summary
        "content": [{"type": "text", "text": format_summary(envelope)}],
        # GUI channel — full governed envelope for workbench
        "structuredContent": envelope,
    }
```

**Rule:** `content` is for the LLM. `structuredContent` is for the GUI workbench.
Both travel in the same JSON-RPC response. The host delivers `structuredContent`
to the workbench via `ui/notifications/tool-result`.

### 4.3 Handshake Contract (exact sequence)

```
Workbench                     Host
   │                           │
   ├── ui/initialize ────────► │  {appInfo, appCapabilities, protocolVersion: "2026-01-26"}
   │                           │
   │ ◄── ui/notifications/ ───┤  {appInfo, protocolVersion}
   │     initialized           │
   │                           │
   │     [tools/call] ───────► │  User or model initiates a GEOX tool call
   │                           │
   │ ◄── ui/notifications/ ───┤  {name, structuredContent, content}
   │     tool-result           │
   │                           │
   │     [tools/call] ───────► │  Workbench calls back (e.g. macrostrat_units)
   │                           │  → server injects SCT, never crosses iframe
   │ ◄── ui/notifications/ ───┤
   │     tool-result           │  ← provenance badges updated on every result
```

**Critical GEOX governance rule:** Every `tool-result` must update the workbench's
provenance badges (reason_code, epistemic rung, staleness). Model-initiated tool
calls are first-class events — the workbench must react to them, not only to user clicks.

### 4.4 Dual Session Layers (must never conflate)

| Layer | What | Scope | Crosses iframe? |
|-------|------|-------|-----------------|
| `transport_session` | MCP transport session ID (UUID) | Host-level, stateless | ✅ yes — HTTP header |
| `sct` | GEOX constitutional session (sct_v1) | Server-level, governance | ❌ never |
| `actor_id` | Operator identity | Server-level, audit | ❌ never |

**Invariants:**
- `sct` must **never** cross the iframe boundary.
- `sct` must **never** appear in transport headers.
- `sct` is injected server-side per tool call via the GEOX governed envelope.
- The workbench passes `actor_id` and `session_id` via `tools/call` arguments,
  but the server derives `sct` from its internal session store — never from the UI.

### 4.5 Origin Pinning (security)

The workbench JavaScript must not use wildcard origins:

```javascript
// ✅ Correct — pin the host origin
const HOST_ORIGIN = "https://geox.arif-fazil.com";

function postRpc(method, params) {
    window.parent.postMessage(
        { jsonrpc: "2.0", ... },
        HOST_ORIGIN
    );
}
```

Inside a sandboxed iframe, `*` is technically safe, but GEOX controls both ends.
Pin the origin for zero-cost defense-in-depth against origin-spoofing attacks.

### 4.6 Strategic Note — Host Agnosticism

> ChatGPT implements the open MCP Apps standard.

This means the GEOX workbench runs identically in ChatGPT, Claude, VS Code,
and any compliant MCP Apps host. Governance stays server-side. The constitutional
physics layer (`sct`, `F1-F13`, `888_HOLD`) is portable across vendors.
This is the architecture GEOX was designed for — "physics not prompts."

---

## 5. Implementation Priority

| Priority | Item | Effort | Dependencies |
|---|---|---|---|---|
| P0 | `macrostrat-mcp` adapter server | 1 day | FastMCP, httpx |
| P1 | Register adapter in A-FORGE registry | 1 hr | A-FORGE affordances.yaml |
| P2 | Integrate macrostrat_units into `geox_basin` stratigraphy mode | 4 hr | GEOX basin engine |
| P3 | Integrate Macrostrat map tiles into `geox_map_scene_plan` | 4 hr | GEOX map tools |
| P4 | GEOX Basin Panel MCP App (HTML + JS) | 2 days | MapLibre, Chart.js |
| P5 | Full double-iframe with UI hydration | 3 days | MCP Apps SDK |

### Completed (2026-07-11)

| Item | Component | Commit |
|------|-----------|--------|
| Single fixed `ui://` workbench resource | `resources/__init__.py` | `71ad29d0` |
| `AppConfig` wiring via `register_tools_on_server(apps=...)` | `_register.py` + `witness.py` | `71ad29d0` |
| 5 visual tools bound to unified workbench | `witness.py` | `71ad29d0` |
| StructuredContent channel on governed envelopes | Blueprint §4.2 | Documentation |
| Interactive map vertical slice (WebMCP) | `webmcp.py` | `71ad29d0` |
| Origin pinning, handshake contract, dual-session rules | Blueprint §4.3–4.5 | Documentation |

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

---

## Appendix A — MCP Apps Contract (4 Deltas)

These four binding rules govern all GEOX MCP App View interactions. Derived from Alpic MCP Apps analysis + FastMCP 3.4.2 runtime.

### Δ1 — MIME Type Constant

Pin the MIME type to a single constant — never inline:

```python
# src/geox_mcp/apps/workbench.py
MCP_APPS_RESOURCE_MIME = "text/html;profile=mcp-app"  # verified against @modelcontextprotocol/ext-apps

@mcp.resource("ui://geox/workbench-v1.html", mime_type=MCP_APPS_RESOURCE_MIME, ...)
```

### Δ2 — Handshake Sequence

Exact lifecycle, not generic:

```
Workbench boots
  → ui/initialize {appInfo: {name, version}, appCapabilities: {}, protocolVersion: "2026-01-26"}
Host responds
  → ui/notifications/initialized {}
Workbench ready.
Host calls GEOX tool
  → tools/call {name, arguments}
GEOX returns result
  → ui/notifications/tool-result {content, structuredContent}
Workbench renders structuredContent, updates provenance badges (rung, staleness, MARUAH)
```

Every `tool-result` **must** update provenance badges — not just display data.

### Δ3 — `structuredContent` Channel

GUI reads `structuredContent`, not `content[0].text`:

```python
# GEOX governed envelope — returns BOTH channels
return {
    "content": [{"type": "text", "text": summary_for_llm}],
    "structuredContent": stamp_claim_envelope(evidence, rung, risk),
}
```

The tool must declare `outputSchema` so the Host knows `structuredContent` is valid:

```python
@mcp.tool(
    name="macrostrat_units",
    outputSchema=GEOX_CLAIM_ENVELOPE_SCHEMA,
    app=AppConfig(resourceUri="ui://geox/workbench-v1.html"),
)
```

- LLM channel → prose summary  
- GUI channel → full governed envelope with evidence, claims, rung, MARUAH flags  
- Schema contract → prevents silent drift between channels

### Δ4 — Two Session Layers

| Layer | Identifier | Scope | Boundary |
|-------|-----------|-------|----------|
| MCP transport | `mcp-session-id` | Stateless, host-level HTTP | Headers only, never in workbench iframe |
| GEOX constitutional | `sct_v1` | Server-side governance, lineage, SEAL | Server-injected per tool call, never crosses iframe |

**Rule:** `sct` must never appear in `postMessage`. `sct` must never appear in transport headers. `sct` is injected server-side per tool call via `register_tools_on_server(apps=...)` → `kwargs["app"]`.

### Security: Origin Pinning

Workbench JS must pin the host origin — never use `"*"`:

```javascript
// apps/workbench-v1.html
const HOST_ORIGIN = "https://geox.arif-fazil.com";  // or window.location.origin
window.parent.postMessage(msg, HOST_ORIGIN);
```

### Host Portability

ChatGPT, Claude, VS Code, and any MCP Apps-compliant host all follow the same protocol. Governance stays server-side — no vendor-specific branches in workbench code.

