"""
GEOX WebMCP Gateway — browser-facing MCP console for Earth Intelligence.

Provides:
  - /webmcp           — WebMCP console HTML page
  - /webmcp/tools     — Tool registry listing
  - /webmcp/call/{t}  — Tool execution via HTTP POST
  - /webmcp/status    — Live GEOX health/status
  - /.well-known/webmcp — WebMCP discovery manifest

This is a lightweight GEOX-specific version, not the full arifOS WebMCP.
Mounted as Starlette routes in server.py's create_app().

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from geox_mcp.surface_manifest import webmcp_categories

logger = logging.getLogger("geox.webmcp")

GEOX_VERSION = os.getenv("GEOX_VERSION", "2026.06.06")
GEOX_SEAL = "DITEMPA BUKAN DIBERI"

TOOL_CATEGORIES: list[dict[str, Any]] = webmcp_categories()

# ── HTML Console Page ──────────────────────────────────────────────────────

_WEBCMP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GEOX WebMCP Console — Earth Intelligence</title>
<style>
  :root { --bg: #0a0a0f; --surface: #12121a; --border: #1e1e2e; --text: #e0e0e0; --accent: #00d4aa; --gold: #d4af37; --red: #e74c3c; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, sans-serif; line-height: 1.6; }
  .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
  header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); flex-wrap: wrap; gap: 0.5rem; }
  h1 { font-size: 1.5rem; }
  h1 span { color: var(--accent); }
  .badge { background: var(--accent); color: #000; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
  .badge.warn { background: var(--gold); }
  .badge.offline { background: var(--red); color: #fff; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
  .card h3 { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 0.5rem; }
  .card .value { font-size: 1.5rem; font-weight: 700; }
  .card .value.green { color: var(--accent); }
  .card .value.gold { color: var(--gold); }
  .flex-row { display: flex; gap: 0.5rem; margin: 1rem 0; align-items: center; flex-wrap: wrap; }
  .flex-row label { font-size: 0.8rem; color: #888; }
  .flex-row input { background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 0.5rem; border-radius: 4px; font-family: monospace; flex: 1; min-width: 120px; }
  .flex-row input::placeholder { color: #555; }
  .cat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.75rem; }
  .cat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem 1rem; }
  .cat-card h4 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--accent); margin-bottom: 0.5rem; }
  .tool-pill { display: inline-block; background: #1a1a2e; color: #ccc; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; margin: 2px; font-family: 'JetBrains Mono', monospace; cursor: pointer; }
  .tool-pill:hover { background: var(--accent); color: #000; }
  #output { background: #000; border: 1px solid var(--border); border-radius: 8px; padding: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; overflow-x: auto; white-space: pre-wrap; margin-top: 1rem; display: none; }
  #tool-form { margin-top: 1rem; }
  #tool-form select, #tool-form textarea, #tool-form button { width: 100%; padding: 0.5rem; margin-bottom: 0.5rem; background: var(--surface); border: 1px solid var(--border); color: var(--text); border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }
  #tool-form button { background: var(--accent); color: #000; font-weight: 600; cursor: pointer; }
  #tool-form button:hover { opacity: 0.9; }
  #tool-form textarea { min-height: 100px; }
  .footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: 0.75rem; color: #666; text-align: center; }
  .flex-row { display: flex; gap: 1rem; align-items: center; margin-bottom: 0.5rem; }
  .loading { opacity: 0.5; pointer-events: none; }
  #map { height: 400px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 1rem; }
  #map-info { font-size: 0.75rem; color: #888; padding: 0.25rem 0; min-height: 1.2rem; }
  #map-info strong { color: var(--accent); }
  .map-section { margin-bottom: 1.5rem; }
  .map-section h3 { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 0.5rem; }
</style>
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" />
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
</head>
<body>
<div class="container">
  <header>
    <h1>GEOX <span>WebMCP</span></h1>
    <span class="badge" id="status-badge">DITEMPA BUKAN DIBERI</span>
  </header>

  <div class="grid">
    <div class="card">
      <h3>Canonical Tools</h3>
      <div class="value green" id="tool-count">—</div>
    </div>
    <div class="card">
      <h3>GEOX Version</h3>
      <div class="value gold" id="geox-version">—</div>
    </div>
  </div>

  <div class="map-section">
    <h3>Interactive Map (MapLibre)</h3>
    <div id="map"></div>
    <div id="map-info"></div>
  </div>

  <div id="tool-form">
    <div class="flex-row" style="gap: 0.75rem;">
      <select id="tool-select" style="flex: 3; background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 0.5rem; border-radius: 4px; font-family: monospace;">
        <option value="">Select a tool...</option>
      </select>
      <button onclick="callTool()" id="call-btn" style="background: var(--accent); color: #000; border: none; padding: 0.5rem 1.2rem; border-radius: 4px; font-weight: 600; cursor: pointer;">Call Tool</button>
    </div>
    <div class="flex-row" style="gap: 0.75rem;">
      <label>Session ID:</label>
      <input type="text" id="session-id" placeholder="optional">
      <label>Actor ID:</label>
      <input type="text" id="actor-id" placeholder="optional">
    </div>
    <textarea id="tool-args" placeholder='Enter tool arguments as JSON, e.g. {"mode": "health"}' style="width: 100%; background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 0.75rem; border-radius: 4px; font-family: monospace; font-size: 0.85rem; min-height: 60px; resize: vertical;"></textarea>
  </div>

  <div id="output" class="card" style="display: none; white-space: pre-wrap; font-family: monospace; font-size: 0.85rem; overflow-x: auto;"></div>

  <h3 style="margin: 1rem 0 0.5rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: #888;">Tool Registry</h3>
  <div class="cat-grid" id="tool-registry"></div>

  <div class="footer">
    GEOX WebMCP &mdash; Earth Intelligence Platform &mdash; <a href="https://geox.arif-fazil.com" style="color: var(--accent);">geox.arif-fazil.com</a>
  </div>
</div>

<script>
const WEBCMP_BASE = '/webmcp';
const MAP_BBOX = [115.5, 4.0, 120.0, 7.5]; // Sabah basin default

let mapLibreMap = null;

async function loadMapContext(bbox, sessionId, actorId) {
  const mapInfo = document.getElementById('map-info');
  mapInfo.innerHTML = 'Loading GEOX scene...';
  try {
    const payload = { arguments: { bbox, mode: 'render_geojson' } };
    if (sessionId) payload.session_id = sessionId;
    if (actorId) payload.actor_id = actorId;
    const res = await fetch(WEBCMP_BASE + '/call/geox_map_context_scene', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.verdict === 'VOID') {
      mapInfo.innerHTML = '<span style="color:var(--red)">Error: ' + (data.error || 'call failed') + '</span>';
      return null;
    }
    // Extract GeoJSON from GEOX evidence envelope
    // WebMCP wraps: data.result = evidence envelope, data.result.result = tool return
    const innerResult = data.result?.result || data.result;
    const geoJson = innerResult?.primary_artifact?.geojson || innerResult;
    if (!geoJson || !geoJson.features) {
      mapInfo.innerHTML = 'No GeoJSON data returned. Try a different bbox.';
      return null;
    }
    const featCount = geoJson.features.length;
    const maruah = innerResult?.primary_artifact?.geojson?.metadata?.maruah_flag;
    // Build feature type summary
    const typeCounts = {};
    geoJson.features.forEach(f => {
      const t = f.properties?.type || 'unknown';
      typeCounts[t] = (typeCounts[t] || 0) + 1;
    });
    const typeSummary = Object.entries(typeCounts).map(([k,v]) => k + '=' + v).join(' ');
    mapInfo.innerHTML = '<strong>Scene loaded:</strong> ' + featCount + ' features [' + typeSummary + ']'
      + (maruah?.maruah_flag ? ' · <span style="color:var(--gold)">' + maruah.maruah_flag + '</span>' : '')
      + ' · <strong>CRS:</strong> ' + (geoJson.metadata?.crs?.properties?.name || 'EPSG:4326')
      + ' · <strong>Basins:</strong> ' + (maruah?.intersected_basins?.join(', ') || 'none');
    return geoJson;
  } catch (e) {
    mapInfo.innerHTML = '<span style="color:var(--red)">Fetch error: ' + e.message + '</span>';
    return null;
  }
}

function initMap(geoJson) {
  if (mapLibreMap) { mapLibreMap.remove(); mapLibreMap = null; }
  mapLibreMap = new maplibregl.Map({
    container: 'map',
    style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    center: [(MAP_BBOX[0] + MAP_BBOX[2]) / 2, (MAP_BBOX[1] + MAP_BBOX[3]) / 2],
    zoom: 5.5,
  });
  mapLibreMap.addControl(new maplibregl.NavigationControl(), 'top-right');

  mapLibreMap.on('load', () => {
    if (!geoJson) return;
    // Add GeoJSON source
    mapLibreMap.addSource('geox-scene', { type: 'geojson', data: geoJson });
    // Fill layer for polygons
    mapLibreMap.addLayer({
      id: 'geox-fill',
      type: 'fill',
      source: 'geox-scene',
      paint: { 'fill-color': ['case', ['==', ['get', 'type'], 'bounding_box'], '#00d4aa', '#d4af37'], 'fill-opacity': 0.15 },
    });
    // Outline layer
    mapLibreMap.addLayer({
      id: 'geox-outline',
      type: 'line',
      source: 'geox-scene',
      paint: { 'line-color': ['case', ['==', ['get', 'type'], 'bounding_box'], '#00d4aa', '#d4af37'], 'line-width': 2 },
    });
    // Fit map to features
    const bounds = new maplibregl.LngLatBounds();
    geoJson.features.forEach(f => {
      if (f.geometry?.type === 'Polygon') {
        f.geometry.coordinates[0].forEach(c => bounds.extend(c));
      }
    });
    if (!bounds.isEmpty()) mapLibreMap.fitBounds(bounds, { padding: 40 });
  });

  // Click handler — show feature info
  mapLibreMap.on('click', 'geox-fill', (e) => {
    const props = e.features?.[0]?.properties || {};
    const mapInfo = document.getElementById('map-info');
    mapInfo.innerHTML = '<strong>Feature:</strong> ' + (props.label || props.type || 'unknown')
      + ' · <strong>Type:</strong> ' + (props.type || '—')
      + (props.maruah_flag ? ' · <span style="color:var(--gold)">MARUAH flagged</span>' : '');
  });

  // Cursor change
  mapLibreMap.on('mouseenter', 'geox-fill', () => { mapLibreMap.getCanvas().style.cursor = 'pointer'; });
  mapLibreMap.on('mouseleave', 'geox-fill', () => { mapLibreMap.getCanvas().style.cursor = ''; });
}

async function init() {
  try {
    const res = await fetch(WEBCMP_BASE + '/status');
    const data = await res.json();
    document.getElementById('tool-count').textContent = data.canonical_tools || '—';
    document.getElementById('geox-version').textContent = data.version || '—';
    document.getElementById('status-badge').textContent = data.seal || 'DITEMPA BUKAN DIBERI';
  } catch(e) {
    document.getElementById('tool-count').textContent = 'offline';
  }

  // Load GEOX map scene
  const sessId = document.getElementById('session-id').value.trim();
  const actId = document.getElementById('actor-id').value.trim();
  const geoJson = await loadMapContext(MAP_BBOX, sessId, actId);
  initMap(geoJson);

  try {
    const res = await fetch(WEBCMP_BASE + '/tools');
    const data = await res.json();
    const registry = document.getElementById('tool-registry');
    const select = document.getElementById('tool-select');

    for (const cat of data.categories || []) {
      const card = document.createElement('div');
      card.className = 'cat-card';
      let toolsHtml = '';
      for (const t of cat.tools || []) {
        toolsHtml += `<span class="tool-pill" onclick="selectTool('${t}')">${t}</span>`;
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        select.appendChild(opt);
      }
      card.innerHTML = '<h4>' + cat.category + '</h4>' + toolsHtml;
      registry.appendChild(card);
    }
  } catch(e) {
    console.error('Failed to load tools', e);
  }
}

function selectTool(name) {
  document.getElementById('tool-select').value = name;
  document.getElementById('tool-args').value = '{"mode": "health"}';
  document.getElementById('tool-args').focus();
}

async function callTool() {
  const name = document.getElementById('tool-select').value;
  if (!name) return;
  let args = {};
  try { args = JSON.parse(document.getElementById('tool-args').value || '{}'); } catch(e) { alert('Invalid JSON args'); return; }

  const sessionId = document.getElementById('session-id').value.trim();
  const actorId = document.getElementById('actor-id').value.trim();

  const output = document.getElementById('output');
  output.style.display = 'block';
  output.textContent = 'Calling ' + name + '...';
  document.getElementById('call-btn').classList.add('loading');

  const payload = { arguments: args };
  if (sessionId) payload.session_id = sessionId;
  if (actorId) payload.actor_id = actorId;

  try {
    const res = await fetch(WEBCMP_BASE + '/call/' + name, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    output.textContent = JSON.stringify(data, null, 2);
  } catch(e) {
    output.textContent = 'Error: ' + e.message;
  } finally {
    document.getElementById('call-btn').classList.remove('loading');
  }
}

init();
</script>
</body>
</html>
"""


# ── Route Handlers ─────────────────────────────────────────────────────────


async def webmcp_index(request: Request) -> HTMLResponse:
    """Serve the WebMCP console HTML page."""
    return HTMLResponse(content=_WEBCMP_HTML)


async def webmcp_manifest(request: Request) -> JSONResponse:
    """WebMCP discovery manifest."""
    return JSONResponse(
        {
            "schema_version": "1.0",
            "service": "GEOX WebMCP",
            "version": GEOX_VERSION,
            "seal": GEOX_SEAL,
            "site": {"name": "GEOX Earth Intelligence", "url": "https://geox.arif-fazil.com"},
            "apis": {"declarative": True, "imperative": True},
            "endpoints": {
                "console": "/webmcp",
                "tools": "/webmcp/tools",
                "call": "/webmcp/call/{tool_name}",
                "status": "/webmcp/status",
            },
        }
    )


async def webmcp_tools(request: Request) -> JSONResponse:
    """Return the tool registry with categories."""
    return JSONResponse(
        {
            "categories": TOOL_CATEGORIES,
            "total_tools": sum(len(c["tools"]) for c in TOOL_CATEGORIES),
            "seal": GEOX_SEAL,
        }
    )


async def webmcp_status(request: Request) -> JSONResponse:
    """Return GEOX runtime status for the WebMCP console."""
    return JSONResponse(
        {
            "status": "healthy",
            "service": "geox-unified",
            "version": GEOX_VERSION,
            "canonical_tools": sum(len(c["tools"]) for c in TOOL_CATEGORIES),
            "profile": os.getenv("GEOX_PROFILE", "full"),
            "seal": GEOX_SEAL,
            "endpoints": {
                "mcp": "https://geox.arif-fazil.com/mcp",
                "webmcp": "https://geox.arif-fazil.com/webmcp",
            },
        }
    )


async def webmcp_call_tool(request: Request) -> JSONResponse:
    """Execute a GEOX MCP tool via WebMCP."""
    tool_name = request.path_params.get("tool_name", "")
    if not tool_name:
        return JSONResponse({"error": "No tool name specified"}, status_code=400)

    # Validate tool is in canonical list
    all_tools = {t for cat in TOOL_CATEGORIES for t in cat["tools"]}
    if tool_name not in all_tools:
        return JSONResponse({"error": f"Unknown tool: {tool_name}", "canonical_tools": sorted(all_tools)}, status_code=404)

    try:
        body = await request.json()
    except Exception:
        body = {}

    arguments = body.get("arguments", {})

    # Inject session/authority from request headers into tool call
    session_id = body.get("session_id") or request.headers.get("X-Session-Id")
    actor_id = body.get("actor_id") or request.headers.get("X-Actor-Id")
    if session_id and "session_id" not in arguments:
        arguments["session_id"] = session_id
    if actor_id and "actor_id" not in arguments:
        arguments["actor_id"] = actor_id

    # Call the tool through MCP (delegated to FastMCP)
    try:
        # Lazy import to avoid circular dependency
        from geox_mcp.server import mcp as geox_mcp_instance

        result = await geox_mcp_instance.call_tool(tool_name, arguments)
        parsed = json.loads(result.content[0].text) if result.content else {}
        return JSONResponse(
            {
                "verdict": "SEAL",
                "tool": tool_name,
                "session_id": session_id or "",
                "actor_id": actor_id or "",
                "result": parsed,
            }
        )
    except Exception as e:
        logger.exception(f"WebMCP tool call failed: {tool_name}")
        return JSONResponse(
            {
                "verdict": "VOID",
                "tool": tool_name,
                "error": str(e),
            },
            status_code=500,
        )
