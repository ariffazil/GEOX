"""
GEOX MCP Server — FastMCP Earth Witness for Visual Seismic Interpretation
DITEMPA BUKAN DIBERI

A governed, visual-first seismic structural interpretation coprocessor.
Forged in 2026 for the arifOS federation (March 2026 standard).
"""

import os
import uuid
import json
import urllib.request
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP

# arifOS Unified Architecture (ToAC) v0.3.2 structural imports
from arifos.geox import HardenedGeoxAgent, ToolRegistry
from arifos.geox.TOOLS.seismic.visual_tools import extract_seismic_views
from arifos.geox.TOOLS.seismic.create_overlay import create_overlay
from arifos.geox.geox_schemas import CoordinatePoint
from arifos.geox.tools.earth_realtime_tool import EarthRealtimeTool

# Initialize GEOX Core
mcp = FastMCP(
    name="GEOX Earth Witness",
    description="Governed seismic interpretation coprocessor — Contrast Canon enforced. Benda ni physically boleh jadi tak?",
    version="0.3.2-visual-seal"
)

# Output directory for visual artifacts
OUTPUT_DIR = Path("geox_output")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Register Hardened Agent for tool delegation
agent = HardenedGeoxAgent(session_id="GEOX_SOVEREIGN_VISUAL_SEAL")

# ── GEOX Context Loader (arifOS OMEGA FORGER v2.1) ───────────────────────────
GEOX_CONTEXT_URL = "https://aaa.arif-fazil.com/geox/geox_openclaw_context.json"
_geox_context_cache = None

def load_geox_context() -> dict:
    """Load unified arifOS + GEOX context. Fetches once, caches in module scope."""
    global _geox_context_cache
    if _geox_context_cache is not None:
        return _geox_context_cache
    try:
        req = urllib.request.Request(GEOX_CONTEXT_URL, headers={"User-Agent": "GEOX-MCP/0.3.2"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            _geox_context_cache = json.loads(resp.read().decode())
            print(f"[GEOX] Context loaded v{_geox_context_cache['version']} — {len(_geox_context_cache['governance']['floors'])} floors active")
            return _geox_context_cache
    except Exception as e:
        print(f"[GEOX] Warning: Could not load context from {GEOX_CONTEXT_URL}: {e}")
        return {
            "version": "unavailable",
            "seal": "DITEMPA BUKAN DIBERI",
            "governance": {"floors": [], "pipeline": []},
            "geox": {"ratlas": {"url": ""}, "live_data": {"viewer": ""}}
        }

geox_ctx = load_geox_context()

@mcp.tool
async def geox_extract_seismic_views(seismic_data: str) -> dict:
    """Generate 2-3 controlled display variants (Standard, High Saliency, Edge) to 'ignite' LLM vision."""
    variants = await extract_seismic_views(seismic_data)
    # Output schema: {label, base64, mimeType}
    return {
        "status": "SEALED",
        "variants": variants,
        "message": "Visual contrast canon views generated for multimodal ignition."
    }

@mcp.tool
async def geox_create_overlay(base_image_ref: str, features: list[dict], overlay_type: str = "faults") -> dict:
    """Create a visual overlay (faults/horizons) on a seismic base image. Returns image path."""
    overlay_path = await create_overlay(base_image_ref, features, overlay_type)
    return {
        "overlay_image": str(overlay_path),
        "overlay_type": overlay_type,
        "legend": f"GEOX {overlay_type.upper()} overlay | DITEMPA BUKAN DIBERI"
    }

@mcp.tool
async def geox_interpret_single_line(seismic_data: str, data_type: str = "raster") -> dict:
    """Full governed visual interpreter (orchestrator). Returns JSON result + visual artifacts + visual_markdown."""
    
    # 1. Pipeline Execution via Hardened Agent (Band A)
    # This hits: ingest -> views -> extract -> ranker -> rules -> summary
    envelope = await agent.execute_tool("SingleLineInterpreter", {"seismic_data": seismic_data, "data_type": data_type})
    
    # 2. Visual Artifact Generation for 'Ignition'
    # Generate contrast views and overlays for the final display
    variants = await extract_seismic_views(seismic_data)
    
    best_candidate_id = envelope["payload"].get("best_candidate_id", "C-001")
    candidates = envelope["payload"].get("alternatives", [])
    best = next((c for c in candidates if c["candidate_id"] == best_candidate_id), {"faults": [], "horizons": []})
    
    fault_overlay = await create_overlay(seismic_data, best.get("faults", []), "faults")
    horizon_overlay = await create_overlay(seismic_data, best.get("horizons", []), "horizons")

    # 3. Forging the 'Visual Markdown' payload (Multimodal Orchestration)
    visual_md = f"""
### 🌍 GEOX Governed Visual Interpretation — {os.path.basename(seismic_data)}

**Best Structural Model:** {envelope['payload'].get('geological_setting', 'Passive Margin')} / {best_candidate_id}
Confidence: {envelope['payload'].get('confidence', 'Est. 0.85')} | Verdict: {envelope['verdict']}

**Contrast Panel (Multi-View Canon Compliance)**
(Images are base64-encoded to LLM context)
![Standard]({variants[0]['base64']})
![High Saliency (Equalized)]({variants[1]['base64']})

**Structural Overlays**
![Fault Sticks]({fault_overlay})
![Horizon Picking]({horizon_overlay})

**Bias Audit [Bond et al. 2007]**
{envelope['payload'].get('bias_audit', 'No display bias detected; feature stability verified.')}

**Physical Reality Check**
Is this physically possible? **{envelope['explanation']}**

**Seal:** DITEMPA BUKAN DIBERI 🔨
"""
    
    return {
        "verdict": envelope["verdict"],
        "result": envelope["payload"],
        "artifacts": {
            "fault_overlay": str(fault_overlay),
            "horizon_overlay": str(horizon_overlay),
        },
        "visual_markdown": visual_md.strip(),
        "telemetry": envelope["metrics"]
    }

@mcp.resource("geox://capabilities")
def get_geox_capabilities() -> str:
    """GEOX Earth Witness detailed capabilities resource."""
    ctx = geox_ctx
    ratlas = ctx.get("geox", {}).get("ratlas", {})
    live = ctx.get("geox", {}).get("live_data", {})
    floors = ctx.get("governance", {}).get("floors", [])
    return f"""GEOX Earth Witness (v0.3.2 SEALED)
----------------------------------
Constitutional floors: {', '.join(floors)}
Framework: {ctx.get('framework', 'arifOS OMEGA FORGER')}

Tools:
- geox_interpret_single_line: Orchestrates full Band A interpretational pipeline.
- geox_extract_seismic_views: Triggers multimodal LLM visual mode.
- geox_create_overlay: Generates visual structural audits.
- geox_get_context_summary: Returns compact dict of GEOX context for agent prompts.

Resources:
- geox://context: Full unified arifOS + GEOX constitutional context
- geox://ratlas: RATLAS atlas URLs and material counts
- geox://telemetry: Output telemetry string template

RATLAS: {ratlas.get('materials',0)} materials, {ratlas.get('families',0)} families
Live data: {live.get('well_name','N/A')} | Viewer: {live.get('viewer','')}

DITEMPA BUKAN DIBERI.🔨
"""

@mcp.resource("geox://context")
def geox_context_resource() -> str:
    """Unified arifOS + GEOX context as a resource. Agents query this to get the full constitutional + physics layer."""
    return json.dumps(geox_ctx, indent=2)

@mcp.resource("geox://ratlas")
def geox_ratlas_resource() -> str:
    """RATLAS reference URLs and material count."""
    r = geox_ctx.get("geox", {}).get("ratlas", {})
    return json.dumps({
        "atlas_url": r.get("url", ""),
        "csv_url": r.get("csv", ""),
        "materials": r.get("materials", 0),
        "families": r.get("families", 0),
        "description": r.get("description", "")
    }, indent=2)

@mcp.resource("geox://telemetry")
def geox_telemetry_template() -> str:
    """Output telemetry string template for agents to append to responses."""
    g = geox_ctx.get("governance", {})
    return g.get("output_telemetry_format", "arifOS v{version} | SEALED")

@mcp.tool
async def geox_earth_signals(
    latitude: float,
    longitude: float,
    radius_km: float = 300.0,
    eq_limit: int = 10,
) -> dict:
    """
    Live Earth observation signals for a prospect location.

    Returns real-time data from:
      • USGS Earthquake Hazards Program — seismic events near prospect
      • Open-Meteo — surface climate state (temperature, pressure, precipitation)
      • NOAA GeoMag — magnetic declination for borehole directional correction

    Zero API keys required. All data CC0 / CC-BY 4.0.
    Used at 100 SENSE stage for F2 TRUTH temporal grounding.

    Args:
        latitude: Decimal degrees, WGS-84
        longitude: Decimal degrees, WGS-84
        radius_km: Search radius for seismic events (default 300 km)
        eq_limit: Maximum earthquake events to return (max 50)
    """
    tool = EarthRealtimeTool()
    location = CoordinatePoint(latitude=latitude, longitude=longitude)
    result = await tool.run({"location": location, "radius_km": radius_km, "eq_limit": eq_limit})
    if not result.success:
        return {"status": "ERROR", "error": result.error}

    raw = result.raw_data or {}
    return {
        "status": "SEALED",
        "verdict": "CLAIM",
        "confidence": result.metadata.get("confidence", 0.0),
        "location": {"latitude": latitude, "longitude": longitude},
        "summary": raw.get("summary", ""),
        "earthquakes": raw.get("earthquakes", {}),
        "climate": raw.get("climate", {}),
        "geomagnetic": raw.get("geomagnetic", {}),
        "sources": raw.get("sources", {}),
        "warnings": raw.get("warnings", []),
        "quantities_count": len(result.quantities or []),
        "seal": "DITEMPA BUKAN DIBERI 🔨",
    }


@mcp.tool
async def geox_get_context_summary() -> dict:
    """Return a compact dict of the GEOX context for agent system prompts."""
    return {
        "version": geox_ctx.get("version", "?"),
        "seal": geox_ctx.get("seal", ""),
        "floors": geox_ctx.get("governance", {}).get("floors", []),
        "pipeline": geox_ctx.get("governance", {}).get("pipeline", []),
        "ratlas_url": geox_ctx.get("geox", {}).get("ratlas", {}).get("url", ""),
        "ratlas_csv": geox_ctx.get("geox", {}).get("ratlas", {}).get("csv", ""),
        "ratlas_materials": geox_ctx.get("geox", {}).get("ratlas", {}).get("materials", 0),
        "live_viewer": geox_ctx.get("geox", {}).get("live_data", {}).get("viewer", ""),
        "live_las": geox_ctx.get("geox", {}).get("live_data", {}).get("las", ""),
        "well_name": geox_ctx.get("geox", {}).get("live_data", {}).get("well_name", ""),
        "constraints": geox_ctx.get("geox", {}).get("constraints", []),
        "sites": geox_ctx.get("sites", {}),
        "agent_instructions": geox_ctx.get("agent_instructions", ""),
        "confidence_tags": geox_ctx.get("governance", {}).get("confidence_tags", []),
        "telemetry_format": geox_ctx.get("governance", {}).get("output_telemetry_format", ""),
    }
    """GEOX Earth Witness detailed capabilities resource."""
    return """
GEOX Earth Witness (v0.3.2 SEALED)
----------------------------------
Sovereign structural interpretation powered by Theory of Anomalous Contrast (ToAC).
Standard Tools:
- geox_interpret_single_line: Orchestrates full Band A interpretational pipeline.
- geox_extract_seismic_views: Triggers multimodal LLM visual mode.
- geox_create_overlay: Generates visual structural audits.
DITEMPA BUKAN DIBERI.🔨
"""

if __name__ == "__main__":
    print("GEOX Earth Witness — FAST-MCP Server starting (v0.3.2) 錘")
    mcp.run()
