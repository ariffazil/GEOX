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

logger = logging.getLogger("geox.webmcp")

GEOX_VERSION = os.getenv("GEOX_VERSION", "2026.06.06")
GEOX_SEAL = "DITEMPA BUKAN DIBERI"

# ── Canonical tool categories for display ──────────────────────────────────
TOOL_CATEGORIES: list[dict[str, Any]] = [
    {
        "category": "Data Ingest & QC",
        "tools": [
            "geox_data_ingest_bundle", "geox_data_qc_bundle",
            "geox_header_inspect", "geox_las_inspect",
            "geox_seismic_segy_inspect", "geox_dst_ingest_test",
        ],
    },
    {
        "category": "Evidence & Reasoning",
        "tools": [
            "geox_evidence_discover", "geox_evidence_reason",
            "geox_evidence_attach", "geox_report_to_workflow",
        ],
    },
    {
        "category": "Subsurface & Petrophysics",
        "tools": [
            "geox_subsurface_generate_candidates",
            "geox_subsurface_verify_integrity",
        ],
    },
    {
        "category": "Seismic Physics",
        "tools": [
            "geox_seismic_compute", "geox_seismic_compute_attribute_tool",
            "geox_volume_frame_tool", "geox_blend_volume_tool",
            "geox_segy_export_tool",
            "geox_fault_stick_ingest_tool",
            "geox_attribute_registry_list_tool",
        ],
    },
    {
        "category": "Horizon & Structure",
        "tools": [
            "geox_horizon_contrast_surface", "geox_coord_transform_tool",
            "geox_blockspace_resolution_tool",
        ],
    },
    {
        "category": "Sequence Stratigraphy",
        "tools": ["geox_sequence_interpret"],
    },
    {
        "category": "Basin & Prospect",
        "tools": [
            "geox_basin_resolve", "geox_basin_profile",
            "geox_prospect_evaluate", "geox_query_intake",
            "geox_literature_ingest",
        ],
    },
    {
        "category": "Macrostrat (Global Geology)",
        "tools": [
            "geox_basin_profile (mode='macrostrat_units')",
            "geox_basin_profile (mode='macrostrat_columns')",
        ],
    },
    {
        "category": "Claim Engine",
        "tools": [
            "geox_claim_create", "geox_claim_validate",
            "geox_claim_challenge", "geox_claim_seal",
        ],
    },
    {
        "category": "Governance & Registry",
        "tools": [
            "geox_system_registry_status", "geox_abstraction_guard",
            "geox_map_context_scene",
        ],
    },
    {
        "category": "Vision V1 (Layer 1)",
        "tools": [
            "geox_vision_perceptual_inventory",
            "geox_vision_minimax_inference",
            "geox_vision_calibrate",
            "geox_vision_audit",
        ],
    },
]

# ── HTML Console Page ──────────────────────────────────────────────────────

_WEBCMP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GEOX WebMCP Console</title>
<style>
  :root { --bg: #0a0a0f; --surface: #12121a; --border: #1e1e2e; --text: #e0e0e0; --accent: #00d4aa; --gold: #d4af37; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, sans-serif; line-height: 1.6; }
  .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
  header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
  h1 { font-size: 1.5rem; }
  h1 span { color: var(--accent); }
  .badge { background: var(--accent); color: #000; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
  .card h3 { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 0.5rem; }
  .card .value { font-size: 1.5rem; font-weight: 700; }
  .card .value.green { color: var(--accent); }
  .card .value.gold { color: var(--gold); }
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
</style>
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

  <div id="tool-form">
    <div class="flex-row">
      <select id="tool-select" style="flex: 2;"><option value="">Select a tool...</option></select>
      <button onclick="callTool()" id="call-btn">Call Tool</button>
    </div>
    <textarea id="tool-args" placeholder='{"mode": "health"}'></textarea>
  </div>

  <div id="output"></div>

  <h3 style="margin: 1rem 0 0.5rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: #888;">Tool Registry</h3>
  <div class="cat-grid" id="tool-registry"></div>

  <div class="footer">
    GEOX WebMCP &mdash; Earth Intelligence Platform &mdash; <a href="https://geox.arif-fazil.com" style="color: var(--accent);">geox.arif-fazil.com</a>
  </div>
</div>

<script>
const WEBCMP_BASE = '/webmcp';

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

  const output = document.getElementById('output');
  output.style.display = 'block';
  output.textContent = 'Calling ' + name + '...';
  document.getElementById('call-btn').classList.add('loading');

  try {
    const res = await fetch(WEBCMP_BASE + '/call/' + name, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ arguments: args }),
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
    return JSONResponse({
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
    })


async def webmcp_tools(request: Request) -> JSONResponse:
    """Return the tool registry with categories."""
    return JSONResponse({
        "categories": TOOL_CATEGORIES,
        "total_tools": sum(len(c["tools"]) for c in TOOL_CATEGORIES),
        "seal": GEOX_SEAL,
    })


async def webmcp_status(request: Request) -> JSONResponse:
    """Return GEOX runtime status for the WebMCP console."""
    return JSONResponse({
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
    })


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

    # Call the tool through MCP (delegated to FastMCP)
    try:
        # Lazy import to avoid circular dependency
        from geox_mcp.server import mcp as geox_mcp_instance

        result = await geox_mcp_instance.call_tool(tool_name, arguments)
        parsed = json.loads(result.content[0].text) if result.content else {}
        return JSONResponse({
            "verdict": "SEAL",
            "tool": tool_name,
            "result": parsed,
        })
    except Exception as e:
        logger.exception(f"WebMCP tool call failed: {tool_name}")
        return JSONResponse({
            "verdict": "VOID",
            "tool": tool_name,
            "error": str(e),
        }, status_code=500)
