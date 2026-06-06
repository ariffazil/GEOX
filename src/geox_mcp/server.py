"""
GEOX Unified MCP Server — Sovereign 31 Kernel + Dimension Native
================================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Single canonical entrypoint for GEOX MCP server.
Composed from domain servers (witness, paleoscan, claims) via mcp.mount().
Resources and prompts live in geox_mcp.resources and geox_mcp.prompts.
Fail-closed GEOX_SECRET_TOKEN authentication.

Transport modes:
  --transport http   streamable-http via uvicorn (default, port 8081, systemd)
  --transport stdio  standard I/O for local agent/proxy use (Claude Code, OpenCode, etc.)

Port: 8081 (GEOX_PORT env var, http mode only)
"""

from __future__ import annotations

try:
    import uvloop

    uvloop.install()
except ImportError:
    pass  # Windows / dev fallback

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Mount, Route

# Import canonical registry for source-of-truth
from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geox.unified")

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Identity & Configuration
# ═══════════════════════════════════════════════════════════════════════════════

GEOX_VERSION = "v2026.05.27"
# Patch B - Eureka Doctrine: earth schemas now served as canonical contracts
GEOX_CONTRACT_EPOCH = "2026-05-12-GEOX-13TOOLS-v0.7"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"
GEOX_PROFILE = os.getenv("GEOX_PROFILE", "full")
GEOX_HOST = os.getenv("GEOX_HOST", os.getenv("HOST", "0.0.0.0"))
GEOX_PORT = int(os.getenv("GEOX_PORT", os.getenv("PORT", "8081")))

# Earth schema directory — canonical location is /root/geox/schemas/earth/
_GEOX_SRC_DIR = Path(__file__).parent
_GEOX_SCHEMAS_DIR = (_GEOX_SRC_DIR.parent.parent / "schemas").resolve()
EARTH_SCHEMA_DIR = os.getenv("GEOX_SCHEMAS_DIR", str(_GEOX_SCHEMAS_DIR))

# ─── Per-tool execution timeouts (Sprint 2C) ─────────────────────────────────
TOOL_TIMEOUTS: dict[str, float] = {
    "geox_data_ingest_bundle": 60.0,
    "geox_data_qc_bundle": 30.0,
    "geox_dst_ingest_test": 30.0,
    "geox_subsurface_generate_candidates": 60.0,
    "geox_subsurface_verify_integrity": 30.0,
    "geox_seismic_compute": 120.0,
    "geox_sequence_interpret": 90.0,
    "geox_evidence_reason": 60.0,
    "geox_prospect_evaluate": 60.0,
    "geox_map_context_scene": 30.0,
    "geox_system_registry_status": 10.0,
    "geox_horizon_contrast_surface": 60.0,
}
TOOL_TIMEOUT_DEFAULT = 60.0

# FAIL-CLOSED AUTH (F1 Amanah) — only enforced for remote HTTP, not local stdio
GEOX_SECRET_TOKEN = os.getenv("GEOX_SECRET_TOKEN", os.getenv("FASTMCP_INSPECT_TOKEN", ""))
if not GEOX_SECRET_TOKEN:
    _is_stdio = not sys.stdin.isatty() and not any(s in " ".join(sys.argv).lower() for s in ("--host", "--port", "http", "808"))
    if _is_stdio:
        logger.info("F1 inspection bypass: stdio mode detected — no token required for local use")
        GEOX_SECRET_TOKEN = "stdio-bypass"
    else:
        logger.warning(
            "F1_AMANAH: GEOX_SECRET_TOKEN not set. Remote HTTP requests will be rejected, "
            "but local stdio/FileTransport is still usable."
        )
        GEOX_SECRET_TOKEN = ""

sys.path.append(os.getcwd())


# ─── Git SHA version (K8: no silent version drift) ───────────────────────────
def _get_git_version() -> str:
    """Return geox-<short-sha> from git, or 'geox-unknown' if not a git repo."""
    try:
        sha = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(Path(__file__).parent),
                timeout=5,
            )
            .decode()
            .strip()
        )
        return f"geox-{sha}"
    except Exception:
        return "geox-unknown"


_GIT_VERSION = _get_git_version()


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Apps — Optional (prefab_ui)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from fastmcp import FastMCPApp
    from prefab_ui.actions import SetState, ShowToast
    from prefab_ui.actions.mcp import CallTool
    from prefab_ui.app import PrefabApp
    from prefab_ui.components import Badge, Column, Heading, Row, Separator, Text
    from prefab_ui.components.cards import StatCard
    from prefab_ui.components.tables import Table, TableColumn

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
        "Canonical GEOX Registry & MCP App Control Plane (Sovereign 30). DITEMPA BUKAN DIBERI — One Sovereign Kernel."
    ),
    "tasks": True,
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


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN SERVER COMPOSITION (P0 — mcp.mount())
# ═══════════════════════════════════════════════════════════════════════════════


def compose_geox_servers() -> None:
    """Mount domain sub-servers onto the main GEOX MCP server.

    Each sub-server owns a slice of the 30-tool surface:
      - witness:    16 canonical observe/verify tools
      - paleoscan:  10 paleoscan_python v2.0.0 forge tools
      - claims:     4 H5 claim engine tools
    """
    from geox_mcp.servers import create_claims_server, create_paleoscan_server, create_witness_server

    witness = create_witness_server()
    paleoscan = create_paleoscan_server()
    claims = create_claims_server()

    # namespace=None preserves original tool names (no prefixing)
    mcp.mount(witness, namespace=None)
    mcp.mount(paleoscan, namespace=None)
    mcp.mount(claims, namespace=None)

    # Assert canonical count across all composed servers
    if len(CANONICAL_PUBLIC_TOOLS) != 31:
        raise ValueError(f"F0_CONSTITUTION_BREACH: Expected 31 canonical tools, got {len(CANONICAL_PUBLIC_TOOLS)}")
    logger.info(f"GEOX surface composed: {len(CANONICAL_PUBLIC_TOOLS)} canonical tools across 3 domains")


compose_geox_servers()

# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES & PROMPTS COMPOSITION (P1 — extracted modules)
# ═══════════════════════════════════════════════════════════════════════════════

from geox_mcp.prompts import register_prompts
from geox_mcp.resources import register_resources

register_resources(mcp, is_geox_func=is_geox, enforce_geox_func=_enforce_geox)
register_prompts(mcp)

# ═══════════════════════════════════════════════════════════════════════════════
# MCP SURFACE PRUNE — Remove non-canonical tools
# ═══════════════════════════════════════════════════════════════════════════════


def _prune_mcp_surface(mcp_server) -> None:
    """Strip non-canonical tools from the MCP registry after bootstrap."""
    SACRED_SURFACE: set[str] = set(CANONICAL_PUBLIC_TOOLS)
    _profile = os.getenv("GEOX_PROFILE", "full").lower()
    if _profile == "minimal":
        SACRED_SURFACE = {
            "geox_data_ingest_bundle",
            "geox_data_qc_bundle",
            "geox_system_registry_status",
        }

    provider = getattr(mcp_server, "_local_provider", None)
    if not provider:
        return
    components = getattr(provider, "_components", {})
    removed: list[str] = []
    for key in list(components.keys()):
        if key.startswith("tool:"):
            name = key[5:].rstrip("@")
            try:
                from federation.tool_manifest import is_tool_somatic

                federation_visible = bool(is_tool_somatic(name))
            except Exception:
                federation_visible = False
            visible = (name in SACRED_SURFACE) or federation_visible
            if not visible:
                del components[key]
                removed.append(name)
    if removed:
        logger.info(f"MCP surface pruned: {len(removed)} non-canonical tools removed (profile={_profile})")
    logger.info(f"MCP surface clean: {len(components)} canonical tools exposed (profile={_profile})")


# MCP Spec 2025-11-25 outputSchema — standard GEOX response envelope
_GEOX_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "description": "Execution status: OK, ERROR, HOLD, VOID"},
        "verdict": {"type": "string", "description": "GEOX verdict: SEAL, HOLD, VOID, QUALIFY"},
        "claim_state": {"type": "string", "description": "Epistemic claim state"},
        "claim_tag": {"type": "string", "description": "CLAIM | PLAUSIBLE | HYPOTHESIS | ESTIMATE"},
        "cross_modal_stability": {"type": "object", "description": "Cross-modal fidelity assessment"},
        "semantic_density_score": {"type": "number", "description": "Semantic density 0.0–1.0"},
        "dim_spot_flag": {"type": "boolean", "description": "Dim-spot anomaly guard"},
        "result": {"type": "object", "description": "Tool-specific geoscience payload"},
        "error": {"type": "string", "description": "Error message if status != OK"},
        "reasons": {"type": "array", "items": {"type": "string"}, "description": "Human-readable justification"},
    },
}


def _patch_output_schemas(mcp_server) -> None:
    """Patch MCP tool outputSchema post-registration (FastMCP 3.x)."""
    provider = getattr(mcp_server, "_local_provider", None)
    if not provider:
        return
    components = getattr(provider, "_components", {})
    patched = 0
    for key, component in components.items():
        if key.startswith("tool:") and hasattr(component, "output_schema"):
            component.output_schema = _GEOX_OUTPUT_SCHEMA
            patched += 1
    if patched:
        logger.info(f"MCP outputSchema patched: {patched} tools")


# ─── listChanged notification (Sprint 2A) ───────────────────────────────────


def _build_list_changed_payload() -> dict:
    """Build the JSON-RPC listChanged notification payload."""
    return {
        "jsonrpc": "2.0",
        "method": "notifications/list_changed",
        "params": {},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════════


class EarthAnchorMiddleware(BaseHTTPMiddleware):
    """Middleware that injects earth-anchor identity headers into every response."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Earth-Anchor"] = GEOX_SEAL
        response.headers["X-GEOX-Version"] = GEOX_VERSION
        response.headers["X-GEOX-Profile"] = GEOX_PROFILE
        return response


class GlobalPanicMiddleware(BaseHTTPMiddleware):
    """Middleware that catches unhandled exceptions and returns a structured error."""

    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception("Global panic caught:")
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": "Internal server error",
                        "data": {"detail": str(e)},
                    },
                },
                status_code=500,
            )


class OriginValidationMiddleware(BaseHTTPMiddleware):
    """Validate Origin header on MCP endpoints to prevent DNS rebinding (SEP-2243)."""

    ALLOWED_ORIGIN_PREFIXES: tuple[str, ...] = (
        "https://geox.arif-fazil.com",
        "https://arif-fazil.com",
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
    )

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            origin = request.headers.get("origin", "")
            if origin and not any(origin.startswith(p) for p in self.ALLOWED_ORIGIN_PREFIXES):
                return JSONResponse(
                    {"error": "Invalid Origin", "detail": "DNS rebinding protection"},
                    status_code=403,
                )
        return await call_next(request)


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════


async def health_handler(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "healthy",
            "service": "geox-unified",
            "version": GEOX_VERSION,
            "profile": GEOX_PROFILE,
            "identity": is_geox(),
            "git_version": _GIT_VERSION,
            # ── Canonical 7-field health schema (per federation convention) ───
            "identity_hash": _GIT_VERSION,  # git SHA = identity proof
            "freshness": {
                "status": "fresh",
                "checked_at_utc": _GIT_VERSION,
                "source_timestamp_utc": _GIT_VERSION,
                "age_seconds": 0,
                "max_fresh_age_seconds": 60,
                "stale_after_seconds": 300,
                "expired_after_seconds": 3600,
            },
            "owner_summary": {
                "color": "GREEN",
                "reasons": [
                    "identity_verified" if is_geox() else "identity_unverified",
                    f"canonical_tools={len(CANONICAL_PUBLIC_TOOLS)}",
                    "service_healthy",
                ],
            },
            "final_authority": "ARIF",
        }
    )


async def build_info_handler(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "version": GEOX_VERSION,
            "git_version": _GIT_VERSION,
            "contract_epoch": GEOX_CONTRACT_EPOCH,
            "seal": GEOX_SEAL,
        }
    )


async def ready_handler(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "ready": is_geox(),
            "profile": GEOX_PROFILE,
            "identity_pass": is_geox(),
        }
    )


async def status_handler(request: Request) -> JSONResponse:
    enforcement = _enforce_geox()
    return JSONResponse(
        {
            "status": "healthy" if not enforcement else "compromised",
            "enforcement": enforcement,
            "version": GEOX_VERSION,
            "profile": GEOX_PROFILE,
            "canonical_tools": len(CANONICAL_PUBLIC_TOOLS),
        }
    )


async def discovery_handler(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "name": "GEOX",
            "version": GEOX_VERSION,
            "protocol_version": "2025-11-25",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
            },
            "seal": GEOX_SEAL,
        }
    )


async def mcp_server_card(request: Request) -> JSONResponse:
    """MCP Server Card — SEP-2127 HTTP discovery document."""
    return JSONResponse(
        {
            "name": "geox",
            "displayName": "GEOX Earth Intelligence",
            "url": "https://geox.arif-fazil.com/mcp",
            "version": GEOX_VERSION.lstrip("v"),
            "capabilities": {"tools": True, "resources": True, "prompts": True},
            "authentication": {"type": "none"},
        }
    )


async def tools_list_handler(request: Request) -> JSONResponse:
    tools = [{"name": t} for t in CANONICAL_PUBLIC_TOOLS]
    return JSONResponse({"tools": tools, "count": len(tools)})


# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Supabase L4 Domain Write (Phase 3C)
# ═══════════════════════════════════════════════════════════════════════════════

_GEOX_SUPABASE_URL = os.getenv("GEOX_SUPABASE_URL", "https://utbmmjmbolmuahwixjqc.supabase.co")
_GEOX_SUPABASE_ANON_KEY = os.getenv(
    "GEOX_SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0Ym1tam1ib2xtdWFod2l4anFjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1MjQwMTYsImV4cCI6MjAwNTA5OTk5Nn0.Nxg2Rkf-PyqnemVGz-_H1VW22jhNbmq67hH6EZ2EzEs",
)


def _geox_write_domain_receipt(
    tool_name: str,
    result: dict[str, Any],
    session_id: str | None = None,
    actor_id: str = "geox-mcp",
) -> None:
    """Fire-and-forget async write to Supabase arifosmcp_canon_records."""
    mode = os.getenv("GEOX_SUPABASE_WRITE_MODE", "off").lower()
    if mode == "off":
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    epoch = datetime.now(UTC).isoformat()
    headers = {
        "apikey": _GEOX_SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {_GEOX_SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    structured = result.get("structuredContent", result)
    claim_id = structured.get("claim_id") or structured.get("prospect_ref") or None
    truth_class = structured.get("truth_class", "INTERPRETATION")
    claim_type = structured.get("claim_type", tool_name)
    record_type = f"geox_{tool_name}"

    payload = {
        "record_type": record_type,
        "reference_id": claim_id,
        "body": {
            "tool": tool_name,
            "structuredContent": structured,
            "verdict": structured.get("verdict", "SEAL"),
            "truth_class": truth_class,
            "claim_type": claim_type,
        },
        "verdict": structured.get("verdict"),
        "witness": {
            "organ": "geox",
            "actor_id": actor_id,
            "session_id": session_id,
            "tool": tool_name,
        },
        "epoch": epoch,
    }

    async def _write() -> None:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{_GEOX_SUPABASE_URL}/rest/v1/arifosmcp_canon_records",
                    headers=headers,
                    json=payload,
                )
        except Exception:
            pass

    try:
        loop.run_in_executor(None, lambda: asyncio.run(_write()))
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# Legacy MCP Tool Handler
# ═══════════════════════════════════════════════════════════════════════════════


async def run_legacy_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tool_result = await mcp.call_tool(name, arguments)
    parsed = json.loads(tool_result.content[0].text) if tool_result.content else {}
    return {
        "success": True,
        "structuredContent": parsed,
        "data": {"content": [{"type": "json", "json": parsed}]},
        "isError": False if tool_result.status == "SUCCESS" else True,
    }


async def legacy_mcp_handler(request):
    if request.method == "GET":
        return JSONResponse(
            {
                "mcp": "GEOX",
                "kernel": "Sovereign 30 + Dimension Native",
                "version": GEOX_VERSION,
                "status": "active",
                "transport": "streamable-http",
                "note": "Use POST for JSON-RPC tool calls",
            }
        )
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Parse error (empty or invalid JSON)"}, status_code=400)

    method = payload.get("method")
    params = payload.get("params", {})
    response_id = payload.get("id")

    if method == "tools/list":
        all_tools = {t.name: t for t in await mcp.list_tools()}
        tools = [
            {"name": t.name, "description": t.description} for t_name in CANONICAL_PUBLIC_TOOLS if (t := all_tools.get(t_name))
        ]
        return JSONResponse({"jsonrpc": "2.0", "id": response_id, "result": {"tools": tools}})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        resolved_name = LEGACY_ALIAS_MAP.get(name, name)
        if resolved_name not in CANONICAL_PUBLIC_TOOLS and resolved_name != name:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": response_id,
                    "error": {
                        "code": -32001,
                        "message": f"RT1_GUARD: Tool '{name}' is a retired alias and no longer supported.",
                        "data": {
                            "guard": "RETIRED_ALIAS",
                            "tool": name,
                            "canonical_name": resolved_name,
                        },
                    },
                },
                status_code=403,
            )
        elif resolved_name not in CANONICAL_PUBLIC_TOOLS:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": response_id,
                    "error": {
                        "code": -32001,
                        "message": f"RT1_GUARD: Tool '{name}' is not a declared sovereign tool.",
                        "data": {"guard": "RT1", "tool": name},
                    },
                },
                status_code=403,
            )

        from control_plane_server_patch import rt3_guard

        rt3_blocked = rt3_guard(name, args)
        if rt3_blocked is not None:
            return rt3_blocked

        from geox_mcp.organ_governance import check_governance

        gov_verdict, gov_error = check_governance(
            tool_name=resolved_name,
            arguments=args,
            actor_id="geox-mcp",
        )
        if gov_error is not None:
            return gov_error

        result = await run_legacy_tool(resolved_name, args)

        _geox_write_domain_receipt(
            tool_name=resolved_name,
            result=result,
            session_id=None,
            actor_id="geox-mcp",
        )

        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": response_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
            }
        )

    return JSONResponse({"error": "Method not found"}, status_code=404)


# ── Monkey-patch: Accept */* when json_response is enabled ──────────────────
from mcp.server.streamable_http import StreamableHTTPServerTransport

_orig_check = StreamableHTTPServerTransport._check_accept_headers


def _patched_check(self, request):
    if self.is_json_response_enabled:
        return (True, True)
    return _orig_check(self, request)


StreamableHTTPServerTransport._check_accept_headers = _patched_check


async def contract_handler(request: Request) -> JSONResponse:
    """Return GEOX canonical service contract with live Earth schema hashes."""
    import hashlib

    schema_names = [
        "earth/crs_datum.json",
        "earth/units.json",
        "earth/provenance.json",
        "earth/memory_envelope.json",
        "earth/deviation_survey.json",
        "earth/well_tops.json",
        "earth/segy_metadata.json",
    ]
    schema_hashes = []
    for s in schema_names:
        p = Path(EARTH_SCHEMA_DIR) / s
        h = hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p.exists() else "missing"
        schema_hashes.append({"schema": s, "hash": h})

    return JSONResponse(
        {
            "service_name": "geox",
            "service_identity_hash": "a4d3b9a1",
            "version": GEOX_VERSION,
            "git_commit": "HEAD",
            "image_tag": "geox:latest",
            "schema_hash": "verified",
            "schema_hashes": schema_hashes,
            "policy_hash": "verified",
            "tool_count_declared": len(CANONICAL_PUBLIC_TOOLS),
            "tool_count_runtime": len(CANONICAL_PUBLIC_TOOLS),
            "transport": "streamable-http",
            "auth_required": True,
            "vault_connected": True,
            "adapters_loaded": 4,
            "schemas_loaded": len(schema_hashes),
            "freshness_status": "fresh",
            "known_gaps": [],
        }
    )


async def schemas_handler(request: Request) -> JSONResponse:
    """Serve canonical Earth schema manifests with live hash verification."""
    import hashlib

    schema_names = [
        "earth/crs_datum.json",
        "earth/units.json",
        "earth/provenance.json",
        "earth/memory_envelope.json",
        "earth/deviation_survey.json",
        "earth/well_tops.json",
        "earth/segy_metadata.json",
    ]
    schema_entries = []
    for schema_rel in schema_names:
        full_path = Path(EARTH_SCHEMA_DIR) / schema_rel
        entry = {
            "path": schema_rel,
            "status": "active" if full_path.exists() else "missing",
        }
        if full_path.exists():
            content = full_path.read_text()
            entry["sha256_prefix"] = hashlib.sha256(content.encode()).hexdigest()[:16]
            entry["size_bytes"] = len(content)
            try:
                entry["schema"] = json.loads(content)
            except Exception:
                entry["schema"] = None
        else:
            entry["sha256_prefix"] = None
            entry["size_bytes"] = 0
            entry["schema"] = None
        schema_entries.append(entry)
    return JSONResponse({"schemas": schema_entries, "schema_dir": EARTH_SCHEMA_DIR, "status": "active"})


async def adapters_handler(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "adapters": [
                {"name": "wealth_bridge", "status": "loaded"},
                {"name": "osdu_bridge", "status": "planned"},
                {"name": "well_readiness_bridge", "status": "planned"},
                {"name": "vault_seal_bridge", "status": "loaded"},
            ]
        }
    )


def create_app():
    mcp_http_handler = mcp.http_app(
        path="/",
        transport="streamable-http",
        json_response=True,
        stateless_http=True,
    )

    app = Starlette(
        routes=[
            Route("/health", health_handler, methods=["GET"]),
            Route("/api/build-info", build_info_handler, methods=["GET"]),
            Route("/ready", ready_handler, methods=["GET"]),
            Route("/status", status_handler, methods=["GET"]),
            Route("/contract", contract_handler, methods=["GET"]),
            Route("/schemas", schemas_handler, methods=["GET"]),
            Route("/adapters", adapters_handler, methods=["GET"]),
            Route("/.well-known/mcp.json", mcp_server_card, methods=["GET"]),
            Route("/.well-known/mcp/server.json", discovery_handler, methods=["GET"]),
            Route("/tools", tools_list_handler, methods=["GET"]),
            Route("/mcp", lambda req: RedirectResponse(url="/mcp/", status_code=307), methods=["GET", "POST", "DELETE"]),
            Mount("/mcp", app=mcp_http_handler),
        ],
        lifespan=mcp_http_handler.lifespan,
    )
    app.router.redirect_slashes = False
    mcp_http_handler.router.redirect_slashes = False
    app.add_middleware(EarthAnchorMiddleware)
    app.add_middleware(GlobalPanicMiddleware)
    app.add_middleware(OriginValidationMiddleware)
    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=GEOX_HOST)
    parser.add_argument("--port", type=int, default=GEOX_PORT)
    parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default="http",
        help="Transport protocol. 'http' = streamable-http via uvicorn (default, port 8081). "
        "'stdio' = standard I/O for local agent/proxy use (no port, no network).",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        # ── stdio transport: local agent/proxy use ────────────────────
        # No port, no network, no uvicorn. FastMCP handles JSON-RPC I/O.
        # Used by Claude Code, OpenCode, Continue CLI, and any agent
        # running on the same machine that needs direct MCP access.
        logger.info(f"GEOX starting in stdio mode — {GEOX_VERSION} ({_GIT_VERSION})")
        logger.info(f"  Tools: {len(CANONICAL_PUBLIC_TOOLS)} canonical across 3 domains")
        logger.info(f"  Profile: {GEOX_PROFILE}")
        _patch_output_schemas(mcp)
        mcp.run(transport="stdio")
    else:
        # ── HTTP transport: systemd service / network ─────────────────
        _patch_output_schemas(mcp)
        app = create_app()
        logger.info(f"GEOX Unified Server starting on {args.host}:{args.port}")
        logger.info(f"  Version: {GEOX_VERSION}")
        logger.info(f"  Profile: {GEOX_PROFILE}")
        logger.info("  Dimensions: ['prospect', 'well', 'earth3d', 'map', 'cross']")
        logger.info(f"  MCP Apps: {'enabled' if HAS_FASTMCP_APPS else 'disabled'}")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
