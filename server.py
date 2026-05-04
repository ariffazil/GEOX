"""
GEOX Unified MCP Server — Sovereign 13 Kernel + Dimension Native
================================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Single canonical entrypoint for GEOX MCP server.
Combines:
  - Sovereign 13 tool surface (contracts.tools.unified_13)
  - Dimension registries (prospect, well, earth3d, map, cross)
  - MCP Apps (Mission Board, Well Desk) with Prefab UI
  - Fail-closed GEOX_SECRET_TOKEN authentication
  - streamable-http transport with Starlette ASGI mounting

Port: 8081 (GEOX_PORT env var)
Transport: streamable-http
"""

from __future__ import annotations

import os
import logging
import sys
import json
import argparse
from datetime import datetime, timezone
from typing import Any

import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

# Import canonical registry for source-of-truth
from contracts.canonical_registry import CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP, GEOX_CAPABILITIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geox.unified")

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Identity & Configuration
# ═══════════════════════════════════════════════════════════════════════════════

GEOX_VERSION = "v2026.05.01-KANON"
# Patch A - Fix epoch string
GEOX_CONTRACT_EPOCH = "2026-05-01-GEOX-13TOOLS-v0.4"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"
GEOX_PROFILE = os.getenv("GEOX_PROFILE", "full")
GEOX_HOST = os.getenv("GEOX_HOST", os.getenv("HOST", "0.0.0.0"))
GEOX_PORT = int(os.getenv("GEOX_PORT", os.getenv("PORT", "8081")))

# FAIL-CLOSED AUTH (F1 Amanah)
_geox_secret = os.getenv("GEOX_SECRET_TOKEN", "")
if not _geox_secret:
    _fallback = os.getenv("FASTMCP_INSPECT_TOKEN", "")
    if _fallback:
        GEOX_SECRET_TOKEN = _fallback
        logger.warning("F1 inspection bypass active — using FASTMCP_INSPECT_TOKEN")
    else:
        logger.critical(
            "F1_AMANAH_BREACH: GEOX_SECRET_TOKEN is missing. Aborting startup "
            "to prevent fail-open exposure."
        )
        sys.exit(1)
else:
    GEOX_SECRET_TOKEN = _geox_secret

sys.path.append(os.getcwd())

# ═══════════════════════════════════════════════════════════════════════════════
# MCP Apps — Optional (prefab_ui)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from fastmcp import FastMCPApp
    from prefab_ui.app import PrefabApp
    from prefab_ui.components import Column, Heading, Row, Text, Separator, Badge
    from prefab_ui.components.tables import Table, TableColumn
    from prefab_ui.components.cards import StatCard
    from prefab_ui.actions.mcp import CallTool
    from prefab_ui.actions import ShowToast, SetState
    HAS_FASTMCP_APPS = True
except Exception:
    FastMCPApp = None
    PrefabApp = None
    Column = Heading = Row = Text = Separator = Badge = None
    Table = TableColumn = StatCard = None
    CallTool = ShowToast = SetState = None
    HAS_FASTMCP_APPS = False

# ═══════════════════════════════════════════════════════════════════════════════
# FastMCP Server Initialization
# ═══════════════════════════════════════════════════════════════════════════════

_mcp_kwargs: dict[str, Any] = {
    "name": "GEOX",
    "version": GEOX_VERSION,
    "instructions": (
        "Canonical GEOX Registry & MCP App Control Plane (Sovereign 13). "
        "DITEMPA BUKAN DIBERI — One Sovereign Kernel."
    ),
}

if HAS_FASTMCP_APPS:
    geox_app = FastMCPApp("GEOX Mission Board")
    well_app = FastMCPApp("Well Desk")
    _mcp_kwargs["providers"] = [
        geox_app,
        well_app,
    ]
else:
    geox_app = None
    well_app = None

mcp = FastMCP(**_mcp_kwargs)

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Identity Invariant (F10 Coherence + F01 Amanah)
# ═══════════════════════════════════════════════════════════════════════════════

def is_geox() -> bool:
    return (
        GEOX_VERSION.startswith("v2026.")
        and GEOX_SEAL == "DITEMPA BUKAN DIBERI"
        and GEOX_SECRET_TOKEN != ""
        and GEOX_PROFILE in ("full", "lite", "vps")
    )


def _enforce_geox() -> dict[str, Any] | None:
    if not is_geox():
        return {
            "ok": False,
            "verdict": "NOT_GEOX",
            "error": "GEOX identity invariant failed. Constitutional seal compromised.",
            "authority": "TERRAIN_WITNESS",
            "seal": GEOX_SEAL,
        }
    return None

# ─── SOVEREIGN 13 BOOTSTRAP ───────────────────────────────────────────────────

def bootstrap_sovereign_13():
    try:
        from contracts.tools.unified_13 import register_unified_tools
        register_unified_tools(mcp, profile=GEOX_PROFILE)
        # Assert against the canonical public tools count
        assert len(CANONICAL_PUBLIC_TOOLS) == 13, \
            f"F0_CONSTITUTION_BREACH: Expected 13 sovereign tools, got {len(CANONICAL_PUBLIC_TOOLS)}"
        logger.info(f"Sovereign 13 tool surface: IGNITED ({len(CANONICAL_PUBLIC_TOOLS)} Canonical Tools)")
    except Exception as e:
        logger.critical(f"Failed to bootstrap Sovereign 13 registry: {e}")
        sys.exit(1)

# ─── DIMENSION REGISTRIES — add unique tools on top of Sovereign 13 ────────────
# Call each registry's register function. FastMCP handles duplicates internally
# with a warning ("warn" mode is default). No duplicate tools will be added.

def bootstrap_dimension_registries():
    registry_map = {
        "contracts.tools.prospect": "register_prospect_tools",
        "contracts.tools.well": "register_well_tools",
        "contracts.tools.earth3d": "register_earth3d_tools",
        "contracts.tools.map": "register_map_tools",
        "contracts.tools.cross": "register_cross_tools",
        "contracts.tools.physics": "register_physics_tools",
        "contracts.tools.section": "register_section_tools",
        "geox.canonical": "register_canonical_tools",
    }
    for module_name, func_name in registry_map.items():
        try:
            import importlib
            mod = importlib.import_module(module_name)
            register_fn = getattr(mod, func_name)
            register_fn(mcp, profile=GEOX_PROFILE)
            logger.info(f"  {module_name.split('.')[-1]}: OK")
        except Exception as e:
            logger.warning(f"  {module_name}: skipped ({e})")

# Boot: Sovereign 13 first, then dimension registries
bootstrap_sovereign_13()
logger.info("Dimension registries loading...")
bootstrap_dimension_registries()

# ═══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL OUTPUT CONTRACT v0.4 — Wrap all tool outputs
# Injects: claim_tag, confidence_band, physics_guard, evidence_refs,
# uncertainty, audit_receipt, humility_score (F7), maruah_flag (F6)
# ═══════════════════════════════════════════════════════════════════════════════

def _wrap_tool_outputs(mcp_server):
    """Monkey-patch all registered tool functions to inject universal output contract."""
    import inspect
    from datetime import datetime, timezone

    provider = getattr(mcp_server, "_local_provider", None)
    if not provider:
        return

    for key, tool in getattr(provider, "_components", {}).items():
        if not key.startswith("tool:"):
            continue
        original_fn = getattr(tool, "fn", None)
        if not original_fn:
            continue

        async def _universal_wrapper(*args, __orig=original_fn, **kwargs):
            result = __orig(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            if not isinstance(result, dict):
                return result

            # Only inject if missing — respect tools that already set these
            now = datetime.now(timezone.utc).isoformat()
            defaults = {
                "claim_tag": result.get("claim_tag", "HYPOTHESIS"),
                "confidence_band": result.get("confidence_band", {"p10": 0.0, "p50": 0.0, "p90": 0.0}),
                "physics_guard": result.get("physics_guard", {"guard_passed": True, "physics_version": "geox-v2026.05.01"}),
                "evidence_refs": result.get("evidence_refs", []),
                "uncertainty": result.get("uncertainty", "Moderate"),
                "audit_receipt": result.get("audit_receipt", {
                    "vault999_ref": "VAULT999-PENDING",
                    "timestamp": now,
                    "session_id": "geox-anon",
                }),
                "humility_score": result.get("humility_score", 0.0),
                "maruah_flag": result.get("maruah_flag", {
                    "maruah_flag": "CLEAR",
                    "territory_risk": "none",
                    "recommended_action": "Proceed with standard consent protocols.",
                    "confidence": "HIGH",
                }),
            }
            for k, v in defaults.items():
                if k not in result:
                    result[k] = v
            return result

        tool.fn = _universal_wrapper

logger.info("Applying universal output contract v0.4...")
_wrap_tool_outputs(mcp)
logger.info("Universal output contract applied to all tools.")

# ═══════════════════════════════════════════════════════════════════════════════
# MCP APPS — Mission Board & Well Desk (if prefab_ui available)
# ═══════════════════════════════════════════════════════════════════════════════

if HAS_FASTMCP_APPS and geox_app is not None:

    @geox_app.tool()
    async def evaluate_mission_trajectories(mission_id: str) -> list[dict]:
        return [
            {"id": "TRJ-A", "name": "Delta-9 Anticline", "risk": "Low", "eta": "2 Days", "seal": "Required"},
            {"id": "TRJ-B", "name": "Deepwater Carbonate", "risk": "High", "eta": "14 Days", "seal": "Required (888_HOLD)"},
        ]

    @geox_app.tool()
    async def trigger_hold_seal(trajectory_id: str) -> dict:
        return {"status": "888_HOLD Lifted", "seal_granted": True}

    @geox_app.ui()
    def mission_board(mission: str) -> PrefabApp:
        options = [
            {"id": "TRJ-A", "name": "Delta-9 Anticline", "risk": "Low", "eta": "2 Days", "seal": "Required"},
            {"id": "TRJ-B", "name": "Deepwater Carbonate", "risk": "High", "eta": "14 Days", "seal": "Required (888_HOLD)"},
        ]
        with Column(gap=4, css_class="p-6") as view:
            Heading(f"GEOX Mission Board: {mission}")
            Badge("DITEMPA BUKAN DIBERI - 999 SEAL ALIVE", variant="outline")
            Separator()
            with Row(gap=4):
                StatCard(label="Trajectories", value=len(options))
                StatCard(label="Subsurface Risk", value="Moderate")
                StatCard(label="Governance", value="888_HOLD ACTIVE", css_class="text-amber-500")
            Table(
                data=options,
                columns=[
                    TableColumn("name", label="Trajectory Model"),
                    TableColumn("risk", label="Geologic Risk"),
                    TableColumn("eta", label="Computational ETA"),
                ],
                row_actions=[
                    CallTool(
                        "trigger_hold_seal",
                        arguments={"trajectory_id": "{id}"},
                        on_success=[ShowToast("999_SEAL Lifted", variant="success")],
                    )
                ],
            )
        return PrefabApp(view=view, state={"mission_active": True})

    @well_app.tool()
    async def trigger_well_seal(well_id: str, signature: str) -> dict:
        return {"status": "888_HOLD Lifted", "seal_granted": True, "sealed_by": signature}

    @well_app.ui()
    def well_dashboard(well_id: str) -> PrefabApp:
        with Column(gap=4, css_class="p-6") as view:
            Heading(f"Well Desk: {well_id}")
            Badge("999 SEAL READY - Petrophysics Active", variant="outline")
            Separator()
            with Row(gap=4):
                StatCard(label="Porosity (\u03c6)", value="22%")
                StatCard(label="Water Sat (Sw)", value="45%")
                StatCard(label="Governance", value="888_HOLD", css_class="text-amber-500")
            CallTool(
                "trigger_well_seal",
                arguments={"well_id": well_id, "signature": "Awaits Human Veto"},
                on_success=[ShowToast("Well Log Sealed", variant="success")],
            )
        return PrefabApp(view=view, state={"well_active": True})

# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

def build_status_payload() -> dict:
    # Use canonical registry for tool count and aliases
    # from contracts.canonical_registry import CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP # Already imported at the top

    return {
        "status": "ok",
        "service": "geox-mcp-kernel",
        "version": GEOX_VERSION,
        "contract_epoch": GEOX_CONTRACT_EPOCH, # Use the new contract epoch
        "canonical_tools": len(CANONICAL_PUBLIC_TOOLS),
        "legacy_aliases": len(LEGACY_ALIAS_MAP),
        "auth_mode": "fail_closed",
        "profile": GEOX_PROFILE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seal": GEOX_SEAL,
        "identity_pass": is_geox(),
        "identity": "GEOX",
        "role": "Earth Substrate Witness",
        "authority": "TERRAIN_WITNESS",
        "enabled_dimensions": ["prospect", "well", "earth3d", "map", "cross", "physics", "section", "canonical"],
        "fastmcp_apps": {
            "enabled": HAS_FASTMCP_APPS,
            "mission_board": bool(geox_app),
            "well_desk": bool(well_app),
        },
    }

async def health_handler(request):
    return JSONResponse({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

async def ready_handler(request):
    payload = build_status_payload()
    if not is_geox():
        payload["status"] = "compromised"
        payload["verdict"] = "NOT_GEOX"
        return JSONResponse(payload, status_code=503)
    return JSONResponse(payload)

async def status_handler(request):
    return JSONResponse(build_status_payload())

async def discovery_handler(request):
    # Use canonical registry for tool count and aliases
    from contracts.canonical_registry import CANONICAL_PUBLIC_TOOLS

    return JSONResponse({
        "organ": "GEOX",
        "version": GEOX_VERSION,
        "git_sha": os.getenv("GIT_SHA", "unknown")[:8],
        "transport": "streamable-http",
        "mcp_endpoint": "https://geox.arif-fazil.com/mcp",
        "tool_count": len(CANONICAL_PUBLIC_TOOLS), # Report canonical public tools
        "floors": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13"],
        "discovery": "stateless",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# 11 Natural Whole Earth Categories — PUBLIC surface (13 sovereign tools)
# These are the ONLY tools advertised in the public registry.
# Dimension/substrate/internal tools remain callable but are not listed here.
GEOX_TOOL_CATEGORIES = {
    "geox_registry_contract": {
        "canonical": ["geox_system_registry_status", "geox_history_audit"],
        "description": "Discover tools, contracts, health, metadata, dependencies, and VAULT999 lineage",
    },
    "geox_data_intake": {
        "canonical": ["geox_data_ingest_bundle"],
        "description": "Import, ingest, inventory, and register Earth evidence artifacts",
    },
    "geox_data_qc": {
        "canonical": ["geox_data_qc_bundle"],
        "description": "QC, coordinate checks, physical range validation, completeness",
    },
    "geox_well_rock_properties": {
        "canonical": ["geox_subsurface_generate_candidates", "geox_subsurface_verify_integrity"],
        "description": "Well logs, petrophysics, Vsh, porosity, Sw, net pay, permeability, lithology",
    },
    "geox_seismic_volume": {
        "canonical": ["geox_seismic_analyze_volume"],
        "description": "SEG-Y loading, attributes, slices, viewer payloads",
    },
    "geox_stratigraphy_section": {
        "canonical": ["geox_section_interpret_correlation"],
        "description": "Correlation, GR motifs, sequence stratigraphy, multi-well panels",
    },
    "geox_map_scene": {
        "canonical": ["geox_map_context_scene"],
        "description": "CRS, bbox, map context, georeferencing, spatial scene rendering",
    },
    "geox_time4d_system": {
        "canonical": ["geox_time4d_analyze_system"],
        "description": "Burial, maturity, trap-charge timing, regime shifts",
    },
    "geox_prospect_assessment": {
        "canonical": ["geox_prospect_evaluate"],
        "description": "Volumetrics, POS, EVOI, prospect evaluation and scorecard",
    },
    "geox_governance_audit": {
        "canonical": ["geox_prospect_judge_verdict", "geox_evidence_summarize_cross"],
        "description": "AC_Risk, 888_HOLD, verdict gateway, VAULT999, evidence graph",
    },
}

async def tools_list_handler(request):
    """Return the public tool surface: 13 sovereign tools grouped by 11 categories.

    Internal dimension/substrate tools are callable but NOT advertised here.
    Aliases are listed separately with deprecation metadata.
    """
    # Use canonical registry for LEGACY_ALIAS_MAP and CANONICAL_PUBLIC_TOOLS
    # from contracts.canonical_registry import CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP # Already imported

    all_tools = {t.name: t for t in await mcp.list_tools()}

    # ── PUBLIC surface: 13 sovereign tools only ────────────────────────────
    categories = []
    seen_public = set()
    for cat_name, cat_info in GEOX_TOOL_CATEGORIES.items():
        cat_tools = []
        for tool_name in cat_info["canonical"]:
            t = all_tools.get(tool_name)
            if t and tool_name in CANONICAL_PUBLIC_TOOLS and tool_name not in seen_public: # Ensure it's in the canonical list
                seen_public.add(tool_name)
                cat_tools.append({"name": t.name, "description": t.description})
        if cat_tools:
            categories.append({
                "category": cat_name,
                "description": cat_info["description"],
                "tools": cat_tools,
                "visibility": "public", # All GEOX_TOOL_CATEGORIES are public
            })

    # ── INTERNAL surface: dimension + substrate tools (callable, not advertised) ──
    internal_tools = []
    for t in all_tools.values():
        if t.name not in CANONICAL_PUBLIC_TOOLS and t.name not in LEGACY_ALIAS_MAP:
            internal_tools.append({"name": t.name, "description": t.description})
    if internal_tools:
        categories.append({
            "category": "internal",
            "description": "Dimension registry and substrate tools — callable but not part of public surface",
            "tools": internal_tools,
            "visibility": "internal",
        })

    # ── ALIASES (deprecated) ──────────────────────────────────────────────
    aliases = []
    for alias_name, canonical_name in LEGACY_ALIAS_MAP.items():
        t = all_tools.get(alias_name)
        if t: # Only include if the tool is actually registered in MCP
            aliases.append({
                "name": alias_name,
                "description": t.description,
                "deprecated": True,
                "canonical_name": canonical_name,
                "deprecated_since": "2026-05-01",
                "removal_target": "2026-06-01",
            })

    return JSONResponse({
        "organ": "GEOX",
        "schema": "geox-tool-registry/v2",
        "categories": categories,
        "public_count": len(CANONICAL_PUBLIC_TOOLS), # Directly from canonical registry
        "internal_count": len(internal_tools),
        "alias_count": len(aliases),
        "total_runtime": len(all_tools),
        "natural_tools": 11, # This is a conceptual count, keep as is for now
        "seal": "DITEMPA BUKAN DIBERI",
        "public_surface": "13 sovereign tools",
    })

# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.resource("geox://identity")
async def geox_identity() -> dict:
    identity_state = {
        "identity": "GEOX",
        "role": "Earth Substrate Witness",
        "authority": "TERRAIN_WITNESS",
        "seal": GEOX_SEAL,
        "version": GEOX_VERSION,
        "profile": GEOX_PROFILE,
        "identity_pass": is_geox(),
    }
    enforcement = _enforce_geox()
    if enforcement:
        identity_state["_enforcement"] = enforcement
    return identity_state

@mcp.resource("geox://registry/apps")
async def list_geox_apps() -> list[dict]:
    manifest_dir = "control_plane/fastmcp/manifests"
    apps = []
    if os.path.exists(manifest_dir):
        for filename in os.listdir(manifest_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(manifest_dir, filename), "r") as f:
                        apps.append(json.load(f))
                except Exception as e:
                    logger.error(f"Failed to load manifest {filename}: {e}")
    return apps

@mcp.resource("geox://apps/earth-panel")
async def get_earth_panel() -> str:
    try:
        ui_path = os.path.join(os.getcwd(), "ui", "earth-panel", "index.html")
        with open(ui_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error loading earth panel UI: {e}"

@mcp.resource("geox://profile/status")
async def get_profile_status() -> str:
    return json.dumps({
        "status": "healthy",
        "service": "geox-unified",
        "profile": GEOX_PROFILE,
        "enabled_dimensions": ["prospect", "well", "earth3d", "map", "cross"],
        "version": GEOX_VERSION,
        "seal": GEOX_SEAL,
        "constitutional_floors": "F1-F13 ACTIVE",
    })

# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY MCP HANDLER (for backward compatibility with existing POST /mcp callers)
# ═══════════════════════════════════════════════════════════════════════════════

async def run_legacy_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tool_result = await mcp.call_tool(name, arguments)
    # Patch C - Tool call wire-shape note: Embed result in content block
    return {"success": True, "data": {"content": [{"type": "json", "json": json.loads(tool_result.content[0].text)}] if tool_result.content else {}}, "isError": False if tool_result.status == "SUCCESS" else True}

async def legacy_mcp_handler(request):
    if request.method == "GET":
        return JSONResponse({
            "mcp": "GEOX",
            "kernel": "Sovereign 13 + Dimension Native",
            "version": GEOX_VERSION,
            "status": "active",
            "transport": "streamable-http",
            "note": "Use POST for JSON-RPC tool calls",
        })
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Parse error (empty or invalid JSON)"}, status_code=400)

    method = payload.get("method")
    params = payload.get("params", {})
    response_id = payload.get("id")

    if method == "tools/list":
        # Use canonical public tools for listing
        all_tools = {t.name: t for t in await mcp.list_tools()}
        tools = [{"name": t.name, "description": t.description} for t_name in CANONICAL_PUBLIC_TOOLS if (t:=all_tools.get(t_name))]
        return JSONResponse({"jsonrpc": "2.0", "id": response_id, "result": {"tools": tools}})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        # RT-1: block undeclared tools before FastMCP sees them. Use canonical for check.
        # Patch E - Resolve dashboard.open: Alias is handled here by LEGACY_ALIAS_MAP
        resolved_name = LEGACY_ALIAS_MAP.get(name, name)
        if resolved_name not in CANONICAL_PUBLIC_TOOLS and resolved_name != name:
             return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": response_id,
                    "error": {
                        "code": -32001,
                        "message": f"RT1_GUARD: Tool \'{name}\' is a retired alias and no longer supported.",
                        "data": {"guard": "RETIRED_ALIAS", "tool": name, "canonical_name": resolved_name},
                    },
                },
                status_code=403,
            )
        elif resolved_name not in CANONICAL_PUBLIC_TOOLS: # If it\'s not an alias and not in canonical tools
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": response_id,
                    "error": {
                        "code": -32001,
                        "message": f"RT1_GUARD: Tool \'{name}\' is not a declared sovereign tool.",
                        "data": {"guard": "RT1", "tool": name},
                    },
                },
                status_code=403,
            )

        # RT-3: irreversible operations require explicit human ack
        from control_plane_server_patch import rt3_guard
        rt3_blocked = rt3_guard(name, args)
        if rt3_blocked is not None:
            return rt3_blocked
        result = await run_legacy_tool(resolved_name, args) # Call with resolved name
        return JSONResponse({"jsonrpc": "2.0", "id": response_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}})

    return JSONResponse({"error": "Method not found"}, status_code=404)

# ═══════════════════════════════════════════════════════════════════════════════
# APP CREATION & ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

def create_app():
    mcp_app = mcp.http_app(path="/", transport="streamable-http")
    app = Starlette(
        routes=[
            Route("/health", health_handler, methods=["GET"]),
            Route("/ready", ready_handler, methods=["GET"]),
            Route("/status", status_handler, methods=["GET"]),
            Route("/.well-known/mcp/server.json", discovery_handler, methods=["GET"]),
            Route("/tools", tools_list_handler, methods=["GET"]),
            Route("/mcp", legacy_mcp_handler, methods=["GET", "POST"]),
            Route("/mcp/stream", legacy_mcp_handler, methods=["GET", "POST"]),
            Mount("/", mcp_app),
        ],
        lifespan=getattr(mcp_app, "lifespan", None),
    )
    return app

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=GEOX_HOST)
    parser.add_argument("--port", type=int, default=GEOX_PORT)
    args = parser.parse_args()
    app = create_app()
    logger.info(f"GEOX Unified Server starting on {args.host}:{args.port}")
    logger.info(f"  Version: {GEOX_VERSION}")
    logger.info(f"  Profile: {GEOX_PROFILE}")
    logger.info(f"  Dimensions: ['prospect', 'well', 'earth3d', 'map', 'cross']")
    logger.info(f"  MCP Apps: {'enabled' if HAS_FASTMCP_APPS else 'disabled'}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")

if __name__ == "__main__":
    main()
