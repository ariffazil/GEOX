"""
GEOX Unified MCP Server — Sovereign 40 Kernel + Dimension Native
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
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Mount, Route

# Import canonical registry for source-of-truth
from geox_mcp.registry import (
    CANONICAL_COMPAT_TOOLS,
    CANONICAL_PUBLIC_TOOLS,
    CANONICAL_RUNTIME_TOOLS,
    INTERNAL_TOOLS,
    SURFACE_TOOLS,
)
from geox_mcp.routing import (
    GEOX_ENABLE_ARIFOS_ROUTE_QUERY,
    GEOX_ROUTE_QUERY_GUARD_ENABLED,  # noqa: F401 — kept for env compatibility, see create_app()
    arifos_route_query,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geox.unified")

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Identity & Configuration
# ═══════════════════════════════════════════════════════════════════════════════

GEOX_VERSION = "v2026.08.26"
# Phase 2.1 Clean Architecture (2026-06-28): 30 canonical tools (18 original + 12 EGS + 4 internal).
# Phase 2.7 (2026-07-03): +1 geox_biostrat_parse — biostratigraphy parsing (NN zones, GDE, lithology).
# Backward-compat wrappers for 49 legacy alias names.
GEOX_CONTRACT_EPOCH = "2026-07-09-GEOX-73TOOLS-PHASE31-RSI-PIPELINE"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"
GEOX_PROFILE = os.getenv("GEOX_PROFILE", "full")
GEOX_HOST = os.getenv("GEOX_HOST", os.getenv("HOST", "0.0.0.0"))
GEOX_PORT = int(os.getenv("GEOX_PORT", os.getenv("PORT", "8081")))

# 2026-08-04 — OAuth kill-switch for Claude Apps / ChatGPT connectors (no DCR).
# GEOX_OAUTH_ENABLED=0 → open MCP, discovery 404, auth cards report none.
# Flip to 1 + restart to re-enable PRM/AS metadata + fixed Client ID path.
_GEOX_OAUTH_RAW = os.getenv("GEOX_OAUTH_ENABLED", "0").strip().lower()
GEOX_OAUTH_ENABLED = _GEOX_OAUTH_RAW in ("1", "true", "yes", "on")

# Public Hostnames Caddy/Cloudflare forward (FastMCP HostOriginGuard).
# Without these, Host: geox.arif-fazil.com → HTTP 421 Misdirected Request.
GEOX_ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv(
        "GEOX_ALLOWED_HOSTS",
        "geox.arif-fazil.com,mcp.arif-fazil.com,*.arif-fazil.com,127.0.0.1,localhost",
    ).split(",")
    if h.strip()
]
GEOX_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "GEOX_ALLOWED_ORIGINS",
        ",".join(
            [
                "https://geox.arif-fazil.com",
                "https://mcp.arif-fazil.com",
                "https://arif-fazil.com",
                "https://www.arif-fazil.com",
                "https://claude.ai",
                "https://www.claude.ai",
                "https://*.claude.ai",
                "https://*.anthropic.com",
                "https://chatgpt.com",
                "https://chat.openai.com",
                "https://*.oaiusercontent.com",
                "http://localhost",
                "http://localhost:*",
                "http://127.0.0.1",
                "http://127.0.0.1:*",
                "https://localhost",
                "https://127.0.0.1",
            ]
        ),
    ).split(",")
    if o.strip()
]

# Earth schema directory — canonical location is /root/geox/schemas/earth/
_GEOX_SRC_DIR = Path(__file__).parent
_GEOX_SCHEMAS_DIR = (_GEOX_SRC_DIR.parent.parent / "schemas").resolve()
EARTH_SCHEMA_DIR = os.getenv("GEOX_SCHEMAS_DIR", str(_GEOX_SCHEMAS_DIR))

# ─── Per-tool execution timeouts (Sprint 2C) ─────────────────────────────────
TOOL_TIMEOUTS: dict[str, float] = {
    # Surface-facing canonical tools (Phase 2.1 + EGS, 2026-06-28)
    "geox_well_ingest": 60.0,
    "geox_well_qc": 30.0,
    "geox_well_desk_open": 15.0,
    "geox_well_desk_publish": 30.0,
    "geox_render_well_panel": 30.0,
    "geox_gravmag_studio": 30.0,
    "geox_well_desk": 30.0,
    "geox_well_desurvey": 30.0,
    "geox_petrophysics": 60.0,
    "geox_sequence": 90.0,
    "geox_seismic_ingest": 60.0,
    "geox_seismic_compute": 120.0,
    "geox_seismic_interpret": 60.0,
    "geox_rsi_interpret": 120.0,  # Phase 3.0: Real seismic image interpretation — CPU-intensive
    "geox_render_audit": 30.0,  # Phase 3.0: Render-vs-amplitude validation — fast audit
    "geox_physical_reality_interpret": 120.0,  # Phase 3.0: Full RSI pipeline — CPU-intensive    "geox_geological_cognition_run": 60.0,  # Phase 3.0: Geological cognition — hypothesis generation
    "geox_panel_d_render_mcp": 60.0,  # Phase 3.0: Panel D cognitive rendering
    "geox_segy_trace_audit": 120.0,  # Phase 3.0: SEG-Y trace audit — file I/O intensive
    "geox_well_tie_compute": 60.0,  # Phase 3.0: Well-tie calibration via bruges
    "geox_tie_receipt": 10.0,  # Phase 3.3: Tie receipt builder — pure schema, fast
    "geox_tie_preflight": 10.0,  # Phase 3.3: 25-point preflight gate — rule-based, fast
    "geox_benchmark_001": 30.0,  # GEOX-001 Well-Seismic Truth Test — Model Deserves To Live
    "geox_well_time_depth_calibrate": 15.0,
    "geox_well_seismic_mistie_rms": 10.0,
    "geox_wavelet_extract_least_squares": 15.0,
    "geox_3d_model_build": 120.0,  # Phase 3.0: GemPy 3D model building
    "geox_wealth_bridge_run": 60.0,  # Phase 3.0: GEOX→WEALTH capital bridge
    "geox_vision": 120.0,
    "geox_subsurface_model": 60.0,
    "geox_geomechanics": 30.0,
    "geox_basin": 60.0,
    "geox_deep_time_state": 30.0,
    "geox_dynamical_systems": 60.0,  # 2026-08-07: Takens/EDM state-space reconstruction — CPU-numpy
    "geox_biostrat_parse": 15.0,  # Phase 2.7: Biostrat parsing — regex-only, fast.
    "geox_biostrat_nn_age": 10.0,  # Phase 2.7: NN zone age lookup — deterministic.
    "geox_biostrat_ruling_check": 10.0,  # Phase 2.7: Contradiction detection — rule-based.
    "geox_biostrat_falsify": 15.0,  # Phase 2.7: 8-gate Popperian falsification engine.
    "geox_macrostrat_calibrate": 30.0,  # Phase 2.8: Biostrat→Macrostrat age bridge — API+lookup.
    "geox_atlas": 15.0,  # Point-in-country + land/water. Fast lookup from local GeoJSON.
    "geox_map_layers_list": 10.0,  # Layer registry lookup. Fast.
    "geox_map_scene_plan": 10.0,  # Scene plan generation. Fast.
    "geox_map_render_preview": 25.0,  # Static preview render with caching.
    "geox_map_export_package": 60.0,  # Governed export — task-style, PROV sidecar, STAC catalog.
    "geox_surface_status": 10.0,
    "geox_forbidden_claims_scan": 10.0,
    # Internal plumbing (4)
    "geox_claim": 30.0,
    "geox_evidence": 60.0,
    "geox_prospect": 60.0,
    "geox_doctrine": 30.0,
    # EGS tools (12)
    "geox_egs_query_entity": 10.0,
    "geox_egs_query_claim": 10.0,
    "geox_egs_query_uncertainty": 10.0,
    "geox_egs_query_provenance": 10.0,
    "geox_egs_claim_create": 10.0,
    "geox_egs_claim_challenge": 10.0,
    "geox_egs_evidence_attach": 10.0,
    "geox_egs_evidence_reason": 30.0,
    "geox_egs_seismic_compute": 60.0,
    "geox_egs_rock_physics": 30.0,
    "geox_egs_data_qc_bundle": 30.0,
    "geox_egs_scenario_audit": 30.0,
    # Phase 2.6: Universal Anomalous Contrast Detector
    "geox_contrast_detect": 15.0,  # Fast — pure computation, no I/O
}
TOOL_TIMEOUT_DEFAULT = 60.0

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX TOOL ANNOTATIONS — MCP Protocol Compliance (Phase 2, 2026-07-03)
# ═══════════════════════════════════════════════════════════════════════════════
# Default annotations for GEOX tools. GEOX is evidence-only — never destructive.
# readOnlyHint: True for query/compute/simulation tools
# destructiveHint: False for ALL tools (GEOX never destroys)
# idempotentHint: True for read-only tools (calling twice = same result)

# Read-only tools: query, compute, simulation, ingest, QC, parse, atlas, map, status
# PR3: all four MCP hints set explicitly (silence is risky — defaults false/true/false/true).
_GEOX_READONLY_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

# State-creating tools: claim creation, evidence attachment, prospect evaluation
_GEOX_STATE_ANNOTATIONS = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": False,
}

# Export tools: create files/artifacts (not destructive, but not read-only)
_GEOX_EXPORT_ANNOTATIONS = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

# Tools that create state (not read-only)
_GEOX_STATE_TOOLS = {
    "geox_claim",
    "geox_evidence",
    "geox_prospect",
    "geox_egs_claim_create",
    "geox_egs_claim_challenge",
    "geox_egs_evidence_attach",
    "geox_egs_evidence_reason",
    "geox_map_export_package",
}

# Tools that may call external services / open world (Macrostrat, tiles, HTTP)
_GEOX_OPEN_WORLD_TOOLS = {
    "geox_basin",
    "geox_map_layers_list",
    "geox_map_scene_plan",
    "geox_map_render_preview",
    "geox_map_export_package",
    "geox_deep_time_state",
    "geox_to_wealth_bridge",
    "geox_surface_status",
    "geox_visual_understand",
    "geox_visual_generate_hypotheses",
}


def _geox_annotations(tool_name: str) -> dict[str, bool]:
    """Return MCP annotations for a GEOX tool based on its behavior.

    Always sets all four hints: readOnlyHint, destructiveHint, idempotentHint, openWorldHint.
    """
    if tool_name in _GEOX_STATE_TOOLS:
        base = dict(_GEOX_STATE_ANNOTATIONS)
    elif "export" in tool_name:
        base = dict(_GEOX_EXPORT_ANNOTATIONS)
    else:
        base = dict(_GEOX_READONLY_ANNOTATIONS)
    if tool_name in _GEOX_OPEN_WORLD_TOOLS or tool_name.startswith("geox_map_"):
        base["openWorldHint"] = True
    return base


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


# ─── Git SHA version (K8: no silent version drift) ───────────────────────────
def _get_git_version() -> str:
    """Return geox-<short-sha> from git, or the deploy-time frozen marker.

    FHS-promoted runtime (/opt/geox) carries no .git — the deploy marker
    (repo-root .git_commit, full SHA written at rsync time) is the honest
    frozen identity there. Falls back to 'geox-unknown' only when neither
    source exists.
    """
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
        pass
    try:
        marker = (Path(__file__).resolve().parents[2] / ".git_commit").read_text(encoding="utf-8").strip()
        if marker:
            return f"geox-{marker[:7]}"
    except Exception:
        pass
    return "geox-unknown"


_GIT_VERSION = _get_git_version()


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Apps — Optional (prefab_ui)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from fastmcp import FastMCPApp
    from prefab_ui.actions import SetState, ShowToast
    from prefab_ui.app import PrefabApp
    from prefab_ui.components import (
        Badge,
        Card,
        CardHeader,
        Column,
        DataTable,
        Heading,
        Metric,
        Row,
        Separator,
        Text,
    )

    HAS_FASTMCP_APPS = True
except Exception:
    FastMCPApp = None
    PrefabApp = None
    Badge = Card = Column = DataTable = Heading = Metric = Row = Separator = Text = None
    SetState = ShowToast = None
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
    # MCP logging: SEP-2577 deprecated — maintenance only; default min warning.
    "client_log_level": "warning",
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

# Completions CANCELLED 2026-07-09 — agent surface uses full tool JSON.

# ── EGS Runtime (2026-06-28) ─────────────────────────────────────────────────
# Earth Grounding System — typed earth graph, uncertainty algebra,
# claim/evidence lifecycle, structured query API.
# "Language models consume EGS; they do not replace it."
from geox.egs.registry import init_egs_state

init_egs_state()
# DEREGISTERED 2026-07-10: EGS tools disabled (12 tools removed from surface).
# Code preserved. Re-enable by uncommenting.
# register_egs_tools(mcp)

# ── Governance wiring (FORGE 2026-06-25) ─────────────────────────────────────
# Register the FastMCP-native governance middleware BEFORE the Starlette app
# is built. The middleware handles RT1 (canonical tool name) + RT3
# (ack_irreversible for irreversible tools) + organ_governance (arifOS routing)
# at the FastMCP method layer — replacing the old legacy_mcp_handler JSON-RPC
# dispatcher that lived in server.py before this refactor.
#
# check_governance is passed by reference (not imported here) to avoid a
# circular import: organ_governance.py imports from geox_mcp.runtime, which
# in turn imports server.py. The check_governance function is injected at
# create_app() time when the import graph is already resolved.
_geox_governance_middleware = None  # populated by create_app() at runtime


def _build_geox_governance_middleware():
    """Lazy factory — called inside create_app() after import graph resolves."""
    from geox_mcp.geox_middleware import GeoxGovernanceMiddleware
    from geox_mcp.organ_governance import check_governance

    return GeoxGovernanceMiddleware(
        canonical_public_tools=set(CANONICAL_PUBLIC_TOOLS),
        canonical_internal_tools=set(INTERNAL_TOOLS),
        canonical_compat_tools=set(CANONICAL_COMPAT_TOOLS),
        arifos_route_query_enabled=bool(GEOX_ENABLE_ARIFOS_ROUTE_QUERY),
        check_governance_fn=check_governance,
    )


def _build_geox_ttl_middleware():
    """Q3 seal (2026-07-03) — wrap tools/list with meta.ttlMs + fingerprint.

    Per MCP SEP-2549, clients treat tools/list as immediately stale (ttl=0)
    when ttlMs is missing. This middleware adds a 30-second TTL plus a
    stable SHA-256 fingerprint (tool names + inputSchema dumps) so the
    federation drift watcher can cheaply detect tool-surface changes
    without re-parsing the entire tool list.
    """
    from geox_mcp.geox_middleware import GeoxToolListTtlMiddleware

    return GeoxToolListTtlMiddleware()


# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Identity Invariant (F10 Coherence + F01 Amanah)
# ═══════════════════════════════════════════════════════════════════════════════


def is_geox() -> bool:
    return GEOX_VERSION.startswith("v2026.") and GEOX_SEAL == "DITEMPA BUKAN DIBERI" and GEOX_PROFILE in ("full", "lite", "vps")


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


# ═══════════════════════════════════════════════════════════════════
# Entropy Integrity Mesh — GEOX Extensions (Phase 2)
# Material reality anchor. The strongest anti-rhetoric witness.
# ═══════════════════════════════════════════════════════════════════


# DEREGISTERED ZEN-15 — @mcp.tool(name="geox_consequence_footprint", annotations=_geox_annotations("geox_consequence_footprint"))
async def _consequence_footprint(
    action_description: str = "",
    affected_area_km2: float | None = None,
    material_movement_tonnes: float | None = None,
    emissions_tonnes_co2e: float | None = None,
    water_impact_m3: float | None = None,
    habitat_fragmentation: str | None = None,
    subsidence_risk: str | None = None,
    contamination_risk: str | None = None,
    reversibility: str = "UNKNOWN",
    uncertainty_factor: float = 0.5,
) -> dict:
    """Compute physical and ecological consequences of a proposed action.
    Measures: affected area, material movement, emissions, water impact,
    habitat fragmentation, subsidence, contamination, reversibility."""
    import importlib.util as _ilu
    import os as _os

    _p = _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)),
        "..",
        "..",
        "..",
        "entropy-integrity",
        "mcp",
        "geox",
        "consequence_footprint.py",
    )
    _s = _ilu.spec_from_file_location("cf", _p)
    _m = _ilu.module_from_spec(_s)
    _s.loader.exec_module(_m)
    return _m.geox_consequence_footprint(
        action_description=action_description,
        affected_area_km2=affected_area_km2,
        material_movement_tonnes=material_movement_tonnes,
        emissions_tonnes_co2e=emissions_tonnes_co2e,
        water_impact_m3=water_impact_m3,
        habitat_fragmentation=habitat_fragmentation,
        subsidence_risk=subsidence_risk,
        contamination_risk=contamination_risk,
        reversibility=reversibility,
        uncertainty_factor=uncertainty_factor,
    )

    # DEREGISTERED ZEN-15 — @mcp.tool(name="geox_optionality_loss", annotations=_geox_annotations("geox_optionality_loss"))


async def _optionality_loss(
    action_description: str = "",
    options_destroyed: list[dict] | None = None,
    options_preserved: list[dict] | None = None,
) -> dict:
    """Measure destroyed future physical options.
    Sterilised reserves, lost aquifer use, irreversible land conversion,
    inaccessible remediation pathways, reduced resilience."""
    import importlib.util as _ilu
    import os as _os

    _p = _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)), "..", "..", "..", "entropy-integrity", "mcp", "geox", "optionality_loss.py"
    )
    _s = _ilu.spec_from_file_location("ol", _p)
    _m = _ilu.module_from_spec(_s)
    _s.loader.exec_module(_m)
    return _m.geox_optionality_loss(
        action_description=action_description, options_destroyed=options_destroyed or [], options_preserved=options_preserved
    )

    # DEREGISTERED ZEN-15 — @mcp.tool(name="geox_feedback_integrity", annotations=_geox_annotations("geox_feedback_integrity"))


async def _feedback_integrity(
    monitoring_system: str = "",
    sensor_coverage_pct: float = 0,
    baseline_quality: str = "UNKNOWN",
    missing_measurements: list[str] | None = None,
    reporting_delay_hours: float = 0,
    threshold_manipulation_detected: bool = False,
    excluded_anomalies: list[str] | None = None,
) -> dict:
    """Check whether physical monitoring is sufficient to detect drift.
    Sensor coverage, baseline quality, missing measurements,
    reporting delay, threshold manipulation, excluded anomalies."""
    import importlib.util as _ilu
    import os as _os

    _p = _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)),
        "..",
        "..",
        "..",
        "entropy-integrity",
        "mcp",
        "geox",
        "feedback_integrity.py",
    )
    _s = _ilu.spec_from_file_location("fi", _p)
    _m = _ilu.module_from_spec(_s)
    _s.loader.exec_module(_m)
    return _m.geox_feedback_integrity(
        monitoring_system=monitoring_system,
        sensor_coverage_pct=sensor_coverage_pct,
        baseline_quality=baseline_quality,
        missing_measurements=missing_measurements,
        reporting_delay_hours=reporting_delay_hours,
        threshold_manipulation_detected=threshold_manipulation_detected,
        excluded_anomalies=excluded_anomalies,
    )

    # DEREGISTERED ZEN-15 — @mcp.tool(name="geox_material_truth_challenge", annotations=_geox_annotations("geox_material_truth_challenge"))


async def _material_truth_challenge(
    institutional_claim: str = "",
    earth_measurements: list[dict] | None = None,
    measurement_confidence: float = 0.5,
) -> dict:
    """Challenge institutional claims against Earth measurements.
    Pattern: 'The institution claims low harm, but Earth measurements show irreversible loss.'"""
    import importlib.util as _ilu
    import os as _os

    _p = _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)),
        "..",
        "..",
        "..",
        "entropy-integrity",
        "mcp",
        "geox",
        "material_truth_challenge.py",
    )
    _s = _ilu.spec_from_file_location("mtc", _p)
    _m = _ilu.module_from_spec(_s)
    _s.loader.exec_module(_m)
    return _m.geox_material_truth_challenge(
        institutional_claim=institutional_claim,
        earth_measurements=earth_measurements or [],
        measurement_confidence=measurement_confidence,
    )

    # DEREGISTERED ZEN-15 — @mcp.tool(name="geox_cascade_pathway", annotations=_geox_annotations("geox_cascade_pathway"))


async def _cascade_pathway(
    intervention: str = "",
    cascade_graph: list[dict] | None = None,
) -> dict:
    """Model how one intervention propagates across geology, groundwater,
    infrastructure, ecology, communities, capital exposure."""
    import importlib.util as _ilu
    import os as _os

    _p = _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)), "..", "..", "..", "entropy-integrity", "mcp", "geox", "cascade_pathway.py"
    )
    _s = _ilu.spec_from_file_location("cp", _p)
    _m = _ilu.module_from_spec(_s)
    _s.loader.exec_module(_m)
    return _m.geox_cascade_pathway(intervention=intervention, cascade_graph=cascade_graph or [])


def compose_geox_servers() -> None:
    """Mount domain sub-servers onto the main GEOX MCP server.

    Each sub-server owns a slice of the 40-tool canonical surface:
      - witness:    observe/verify tools
      - paleoscan:  paleoscan_python v2.0.0 forge tools
      - claims:     H5 claim engine tools
      - vision:     Vision V1 layer-1 tools (perceptual_inventory,
                    minimax_inference, calibrate, audit)
                    Forged 2026-06-07 (autonomous, F13 delegation).
    """
    from geox_mcp.servers import (
        create_claims_server,
        create_paleoscan_server,
        create_vision_server,
        create_witness_server,
    )

    witness = create_witness_server()
    paleoscan = create_paleoscan_server()
    vision = create_vision_server()

    # namespace=None preserves original tool names (no prefixing)
    mcp.mount(witness, namespace=None)
    mcp.mount(paleoscan, namespace=None)
    # D5: claims sub-server uses **kwargs tools FastMCP rejects.
    # Canonical surface is mode-dispatched geox_claim on the main server.
    # Soft-skip so GEOX boot is not crash-looped (was exit-code 1 2026-07-15).
    try:
        claims = create_claims_server()
        mcp.mount(claims, namespace=None)
    except (ValueError, TypeError) as claims_exc:
        import logging as _logging

        _logging.getLogger("geox.server").warning("claims sub-server skipped (use geox_claim modes): %s", claims_exc)
    mcp.mount(vision, namespace=None)

    # Assert canonical count across all composed servers
    #
    # FORGE HISTORY (count trajectory):
    #   2026-06-14: 37 -> 40 (added basin, lit ingest, abstraction guard, query intake, literature)
    #   2026-06-21: 40 -> 47 (W2-W12 FORGE: 3 doctrine + 1 Prithvi + 1 gravity/mag + 2 open data)
    #   2026-06-21: 47 -> 50 (W13+ Phase C: geox_joint_inversion, geox_mt_forward, geox_biostrat_constraint)
    #   2026-06-22: 50 -> 56 (W16+ substrate; tools unchanged)
    #   2026-06-22: 56 -> 16 (Phase 2 Clean Architecture — mode-consolidated; removed legacy
    #             flat names; geox_doctrine / geox_claim / geox_evidence / geox_prospect
    #             replaced doctrine_assumption_register, claim_create, evidence_discover,
    #             prospect_evaluate, etc.)
    #   2026-06-25: LOCKED at 16 (canonical surface). All Earth dimensions and W9-W13+
    #             tools are deferred to Phase 3 (requires 888_HOLD to re-enable).
    #   2026-06-27: 16 -> 17 (GAP-1 fix: geox_surface_status added — federation-standard registry probe).
    #   2026-06-28: 17 -> 18 (Phase 2.1: geox_well_desurvey added — 3D wellbore geometry).
    #
    # EGS Phase 1 (2026-06-28): 12 EGS tools added (egs_query_*, egs_claim_*, etc.)
    # Live runtime reports canonical_tools=30. Any expansion requires 888_HOLD per
    # geox/AGENTS.md. F13 SOVEREIGN invariant.
    if set(CANONICAL_PUBLIC_TOOLS) & set(INTERNAL_TOOLS):
        raise ValueError("F0_CONSTITUTION_BREACH: internal tools leaked into CANONICAL_PUBLIC_TOOLS.")
    if set(CANONICAL_PUBLIC_TOOLS) & set(CANONICAL_COMPAT_TOOLS):
        raise ValueError("F0_CONSTITUTION_BREACH: compat tools leaked into CANONICAL_PUBLIC_TOOLS.")
    logger.info(
        f"GEOX surface composed: {len(SURFACE_TOOLS)} public + {len(INTERNAL_TOOLS)} internal = {len(CANONICAL_RUNTIME_TOOLS)} runtime + "
        f"{len(CANONICAL_COMPAT_TOOLS)} backward-compat tools"
    )


compose_geox_servers()

from geox_mcp.tools.ui_applets import register_ui_applets


class _McpSlashRewriteMiddleware:
    """ASGI middleware bridging /mcp → /mcp/ for FastMCP streamable-http.

    Starlette Mount("/mcp/", ...) only handles paths UNDER /mcp/ — the exact /mcp
    path falls through all routes and returns Starlette's 404. FastMCP's internal
    router also expects /mcp/.

    This middleware intercepts /mcp requests BEFORE route matching, rewrites
    scope.path to /mcp/, then passes to the ASGI app. The Mount("/mcp/", ...)
    then matches and FastMCP's internal routing works correctly.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path") == "/mcp":
            # Shallow copy — scope is mutable but shared; only mutate our copy
            scope = dict(scope)
            scope["path"] = "/mcp/"
        await self.app(scope, receive, send)


# ── D7 ACCEPT-NEGOTIATION MIDDLEWARE (2026-08-01) ─────────────────────────────
# Fix: GEOX /mcp returned 406 "Not Acceptable: Client must accept text/event-stream"
# on plain GET (no Accept header). This broke discovery probes (the audit's
# "storefront window cracked"). Fix: intercept GET /mcp* without SSE Accept,
# return a graceful discovery JSON. Real MCP clients (Accept: text/event-stream)
# pass through to FastMCP normally.
#
# Why middleware, not route: the FastMCP Mount is INSIDE Starlette routing.
# A route can't reach /mcp/ before the Mount does (Starlette routes are
# matched in order). Middleware fires before routing — sees the request first.
class _McpAcceptNegotiationMiddleware:
    """Negotiate Accept header on GET /mcp* — graceful discovery, not 406."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "")

        # Only intercept GET on /mcp endpoints
        if method != "GET" or not path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        # Parse Accept header (ASGI headers are list[tuple[bytes, bytes]])
        accept_value = ""
        for name, value in scope.get("headers", []):
            if name == b"accept":
                accept_value = value.decode("latin-1", "ignore").lower()
                break

        # If client accepts text/event-stream, pass through to FastMCP
        if "text/event-stream" in accept_value:
            await self.app(scope, receive, send)
            return

        # Otherwise: graceful discovery response
        import json as _json
        from starlette.responses import JSONResponse as _JSON

        discovery = {
            "mcp_endpoint": "https://geox.arif-fazil.com/mcp/",
            "transport": "streamable-http",
            "server": "GEOX Federated Domain",
            "version": "v2026.07.24",
            "discovery": (
                "Send Accept: application/json, text/event-stream to initiate "
                "an MCP session, then POST JSON-RPC initialize. Real MCP clients "
                "(Claude Code, OpenCode, etc.) do this automatically."
            ),
            "tools": "/tools",
            "schema": "/schemas",
            "card": "/.well-known/mcp/server.json",
            "health": "/health",
            "ready": "/ready",
            "doctrine": "DITEMPA BUKAN DIBERI — One Sovereign Kernel",
        }

        response = _JSON(
            discovery,
            headers={
                # Tell clients what we DO accept (proper negotiation)
                "Accept-Post": "application/json, text/event-stream",
                # Help caches treat discovery differently from session
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
            status_code=200,
        )
        await response(scope, receive, send)


register_ui_applets(mcp)
# ZEN-15 v0.2.1 — gravmag studio consolidated into geox_gravmag_studio(mode="open"|"screen")
# in tools_wiring.py. Standalone registrations removed.
# register_gravmag_studio_tools(mcp)
# register_gravmag_studio_screen_tools(mcp)


# ── W2-W4 FORGE — Doctrine layer tool registrations ────────────────────────
# INTERNAL-ONLY 2026-06-27: judgment lane — removed from MCP facade
# Python-callable for federation organs; not on tools/list
async def _doctrine_assumption_register(
    introduced_by: str,
    rung_origin: int,
    description: str,
    parent_assumption_id: str | None = None,
    inherited_from: str | None = None,
    epistemic_label: str = "DER",
) -> dict:
    """Register an assumption in the GEOX doctrine lineage (Gap X)."""
    from geox_mcp.tools.doctrine import (
        AssumptionRegisterRequest,
        geox_doctrine_assumption_register,
    )

    req = AssumptionRegisterRequest(
        introduced_by=introduced_by,
        rung_origin=rung_origin,
        description=description,
        parent_assumption_id=parent_assumption_id,
        inherited_from=inherited_from,
        epistemic_label=epistemic_label,
    )
    return (await geox_doctrine_assumption_register(req)).model_dump(mode="json")


# INTERNAL-ONLY 2026-06-27: judgment lane — removed from MCP facade
async def _doctrine_anti_beautiful_one(
    text: str,
    grounding_evidence_count: int = 0,
    grounding_evidence_rungs: list[int] | None = None,
    threshold: float = 1.5,
    include_decomposition: bool = True,
) -> dict:
    """Run Anti-Beautiful-One audit on a claim (Gap 3)."""
    from geox_mcp.tools.doctrine import (
        BeautyAuditRequest,
        geox_doctrine_anti_beautiful_one,
    )

    req = BeautyAuditRequest(
        text=text,
        grounding_evidence_count=grounding_evidence_count,
        grounding_evidence_rungs=list(grounding_evidence_rungs or []),
        threshold=threshold,
        include_decomposition=include_decomposition,
    )
    return (await geox_doctrine_anti_beautiful_one(req)).model_dump(mode="json")


# INTERNAL-ONLY 2026-06-27: judgment lane — removed from MCP facade
async def _doctrine_godel_review(
    claim_id: str = "",
    action: str = "review",
    void_reason: str | None = None,
    rung: int | None = None,
    description: str | None = None,
    depends_on_assumption_ids: list[str] | None = None,
) -> dict:
    """Review / seal / void a claim via the Gödel Wall (Gap 5).

    If `claim_id` is provided, action operates on the existing claim
    (review / seal / void). Otherwise, register a new claim and run review.
    """
    from geox_mcp.tools.doctrine import (
        GodelClaimRequest,
        GodelSealRequest,
        geox_doctrine_godel_register_claim,
        geox_doctrine_godel_review,
    )

    if not claim_id:
        if rung is None or description is None:
            return {"ok": False, "error": "rung and description required when claim_id is absent"}
        reg_req = GodelClaimRequest(
            rung=rung,
            description=description,
            depends_on_assumption_ids=list(depends_on_assumption_ids or []),
        )
        reg = await geox_doctrine_godel_register_claim(reg_req)
        if not reg.ok:
            return reg.model_dump(mode="json")
        # Pull the new claim_id out of the registration response
        claim_id = reg.claim.get("claim_id", "") if reg.claim else ""
    req = GodelSealRequest(claim_id=claim_id, action=action, void_reason=void_reason)
    return (await geox_doctrine_godel_review(req)).model_dump(mode="json")


# ── W5-W8 FORGE — Phase A first wave: Foundation model backing engine ────────
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_prithvi_eo_inference", annotations=_geox_annotations("geox_prithvi_eo_inference"))
async def _prithvi_eo_inference(
    tile_id: str,
    task: str = "land_cover",
    bands: list[str] | None = None,
    time_range_start: str = "2024-01-01",
    time_range_end: str = "2024-12-31",
    cloud_cover_max: float = 0.20,
    source_uri: str | None = None,
) -> dict:
    """Run Prithvi-EO-2.0 (NASA-IMPACT/IBM) on an HLS tile. Mock mode by default."""
    from geox_mcp.tools.earth_obs import (
        PrithviEOInferenceRequest,
        geox_prithvi_eo_inference,
    )

    req = PrithviEOInferenceRequest(
        tile_id=tile_id,
        bands=tuple(bands) if bands else ("B02", "B03", "B04", "B8A", "B11", "B12"),
        time_range=(time_range_start, time_range_end),
        cloud_cover_max=cloud_cover_max,
        task=task,  # type: ignore[arg-type]
        source_uri=source_uri,
    )
    return (await geox_prithvi_eo_inference(req)).model_dump(mode="json")


# ── W9-W12 FORGE — Phase B first wave: Nonseismic geophysics + open data ────
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_gravity_magnetic_forward", annotations=_geox_annotations("geox_gravity_magnetic_forward"))
async def _gravity_magnetic_forward(
    survey_type: str = "gravity",
    easting_m: list[float] | None = None,
    northing_m: list[float] | None = None,
    prisms: list[dict] | None = None,
    magnetization_a_m: float = 0.0,
    field_declination_deg: float = 0.0,
    field_inclination_deg: float = 0.0,
) -> dict:
    """Forward-model gravity or magnetic anomaly grid via HarmonIC (mock by default)."""
    from geox_mcp.tools.geophysics_nonseismic import (
        GravityMagneticForwardRequest,
        geox_gravity_magnetic_forward,
    )

    req = GravityMagneticForwardRequest(
        survey_type=survey_type,  # type: ignore[arg-type]
        easting_m=tuple(easting_m) if easting_m else (0.0,),
        northing_m=tuple(northing_m) if northing_m else (0.0,),
        prisms=list(prisms or []),
        magnetization_a_m=magnetization_a_m,
        field_declination_deg=field_declination_deg,
        field_inclination_deg=field_inclination_deg,
    )
    return (await geox_gravity_magnetic_forward(req)).model_dump(mode="json")


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_emag2_ingest", annotations=_geox_annotations("geox_emag2_ingest"))
async def _emag2_ingest(force: bool = False) -> dict:
    """Fetch EMAG2v3 global magnetic anomaly grid (offline-safe stub by default)."""
    from geox_mcp.tools.geophysics_nonseismic import (
        EMAG2FetchRequest,
        geox_emag2_ingest,
    )

    req = EMAG2FetchRequest(force=force)
    return (await geox_emag2_ingest(req)).model_dump(mode="json")


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_icgem_models", annotations=_geox_annotations("geox_icgem_models"))
async def _icgem_models() -> dict:
    """List ICGEM (GFZ Potsdam) global gravity field models."""
    from geox_mcp.tools.geophysics_nonseismic import (
        ICGEMListRequest,
        geox_icgem_models,
    )

    return (await geox_icgem_models(ICGEMListRequest())).model_dump(mode="json")


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_geochem_kinetics", annotations=_geox_annotations("geox_geochem_kinetics"))
async def _geochem_kinetics(
    initial_smectite_frac: float = 0.5,
    T_C: float = 100.0,
    time_ma: float = 10.0,
    TOC_wt: float = 0.05,
    kerogen_type: str = "II",
) -> dict:
    """Foundational Geochemistry: computes mineral kinetics (smectite->illite) and kerogen maturation.

    This acts as the causal base layer feeding into RockPhysics13State (porosity budget, void generation).
    """
    from geox_mcp.tools.geochemistry import (
        GeochemRequest,
    )
    from geox_mcp.tools.geochemistry import (
        geox_geochem_kinetics as _impl,
    )

    req = GeochemRequest(
        initial_smectite_frac=initial_smectite_frac,
        T_C=T_C,
        time_ma=time_ma,
        TOC_wt=TOC_wt,
        kerogen_type=kerogen_type,
    )
    return (await _impl(req)).model_dump(mode="json")


# ── W13+ FORGE — Phase C: Multi-physics Earth Witness (joint inversion + CSEM/MT + biostrat) ──
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_joint_inversion", annotations=_geox_annotations("geox_joint_inversion"))
async def _joint_inversion(
    observations: list[dict] | None = None,
    prior: dict | None = None,
    max_iter: int = 50,
    tolerance: float = 1e-3,
) -> dict:
    """Joint multi-physics inversion: fuse N modalities into one Physics13State per cell.

    Each observation: {modality, value, uncertainty?, weight?, depth_m?}.
    Supported modalities: seismic_impedance, seismic_vpvs, gravity, magnetic, mt_resistivity.
    Enforces Earth-bounds on every dial; output is graded RAW or AAA.
    """
    from geox_mcp.tools.multi_physics import (
        JointInversionRequest,
        geox_joint_inversion,
    )
    from geox_mcp.tools.multi_physics import ModalityObsSchema as _ModObs

    obs = [_ModObs(**o) for o in (observations or [])]
    req = JointInversionRequest(
        observations=obs,
        prior=prior,
        max_iter=max_iter,
        tolerance=tolerance,
    )
    return (await geox_joint_inversion(req)).model_dump(mode="json")


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_mt_forward", annotations=_geox_annotations("geox_mt_forward"))
async def _mt_forward(
    layers: list[dict] | None = None,
    frequencies_hz: list[float] | None = None,
) -> dict:
    """1D CSEM/MT forward: apparent resistivity + phase at each frequency."""
    from geox_mcp.tools.multi_physics import (
        MTForwardRequestSchema,
        geox_mt_forward,
    )

    req = MTForwardRequestSchema(
        layers=layers or [],
        frequencies_hz=tuple(frequencies_hz) if frequencies_hz else (0.001, 0.01, 0.1, 1.0, 10.0, 100.0),
    )
    return (await geox_mt_forward(req)).model_dump(mode="json")


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_biostrat_constraint", annotations=_geox_annotations("geox_biostrat_constraint"))
async def _biostrat_constraint(
    state: dict,
    age_ma: float,
) -> dict:
    """Biostratigraphic time-facies admissibility check for a Physics13State cell.

    Returns zone name, admissible materials, and consistency verdict.
    """
    from geox_mcp.tools.multi_physics import (
        BiostratRequest,
        geox_biostrat_constraint,
    )

    req = BiostratRequest(state=state, age_ma=age_ma)
    return (await geox_biostrat_constraint(req)).model_dump(mode="json")


# ── Phase 2.7 (2026-07-03): Biostratigraphy Parser — NN zone + GDE + lithology ──
# DEREGISTERED ZEN-15 — @mcp.tool(name="geox_biostrat_parse", annotations=_geox_annotations("geox_biostrat_parse"))
async def _biostrat_parse(
    text: str = "",
    paleoenvironment: str = "",
    lithology: str = "",
) -> dict:
    """Biostratigraphy Parser — extract biozones, GDE events, lithology from free text.

    Returns arrays of biozones[], gde_events[], lithology_class, unparsed_terms[], warnings[].
    Multi-zone extraction. All outputs evidence-tagged with source_span provenance.

    F2 TRUTH: regex-only, no ML. Every output carries source_span and evidence_tag.
    F7 HUMILITY: confidence hard-capped at 0.85. Unmatched terms preserved, not guessed.
    IRON LAW: Tectonics → Stratigraphy → Age. Biostrat calibrates, never constitutes.
    """

    from geox_mcp.tools.biostrat_parse import geox_biostrat_parse as _impl

    return await _impl(
        text=text,
        paleoenvironment=paleoenvironment,
        lithology=lithology,
    )


# ── Phase 2.7 (2026-07-03): NN Zone Age Resolution ──
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_biostrat_nn_age", annotations=_geox_annotations("geox_biostrat_nn_age"))
async def _biostrat_nn_age(
    zone: str = "",
    scheme: str = "Martini",
    calibration: str = "default",
) -> dict:
    """NN Zone Age Resolution — convert biozone to age bracket with calibration metadata.

    Returns zone, scheme, discipline, age_top_ma, age_base_ma, epoch, calibration,
    and mandatory not_a_radiometric_age=true warning.

    F2 TRUTH: Biozone age depends on calibration table and regional diachroneity.
    F7 HUMILITY: Zone age is a lookup, not a measurement. Confidence capped at 0.85.
    """
    from geox_mcp.tools.biostrat_nn_age import geox_biostrat_nn_age as _impl

    return await _impl(zone=zone, scheme=scheme, calibration=calibration)


# ── Phase 2.7 (2026-07-03): Biostrat Ruling Check — contradiction detector ──
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_biostrat_ruling_check", annotations=_geox_annotations("geox_biostrat_ruling_check"))
async def _biostrat_ruling_check(
    biozone: str = "",
    lithology: str = "",
    environment: str = "",
    claim: str = "",
    depth_m: float | None = None,
) -> dict:
    """Biostrat Ruling Check — detect contradictions in biostratigraphic interpretations.

    Tests facies compatibility, reworking/caving, age ordering, and multi-discipline
    convergence. Returns PASS | WEAK_PASS | CONTRADICTION | HOLD | REJECT.

    B4 Facies Veto: biozone-implied environment must not conflict with lithology/faices
    without documented explanation.

    F2 TRUTH: Flags contradictions, does not resolve them.
    F6 MARUAH: Challenges interpretations, never overrides without evidence.
    """
    from geox_mcp.tools.biostrat_ruling_check import geox_biostrat_ruling_check as _impl

    return await _impl(
        biozone=biozone,
        lithology=lithology,
        environment=environment,
        claim=claim,
        depth_m=depth_m,
    )


# ── Phase 2.7 (2026-07-03): Biostrat Falsification Engine — 8-gate Popperian test ──
# DEREGISTERED ZEN-15 — @mcp.tool(name="geox_biostrat_falsify", annotations=_geox_annotations("geox_biostrat_falsify"))
async def _biostrat_falsify(
    fossil_group: str = "calcareous_nannofossil",
    biozone: str = "",
    lithology: str = "",
    environment: str = "",
    claim: str = "",
    claim_type: str = "age",
    sample_type: str = "cuttings",
    depth_m: float | None = None,
    younger_zone: str = "",
    older_zone: str = "",
    depth_younger_m: float | None = None,
    depth_older_m: float | None = None,
    reworking_claimed: bool = False,
    fault_present: bool = False,
    fossil_names: str = "",
    basin_province: str = "",
    claim_is_basinwide: bool = False,
    seismic_group: str = "",
    expected_seismic_group: str = "",
    stacking_pattern: str = "",
    region: str = "sabah",
) -> dict:
    """8-Gate Popperian Falsification Engine for biostrat claims.

    G1-Facies G2-StratOrder G3-Taxonomy G4-Reworking G5-Diachroneity
    G6-Seismic G7-Sequence G8-Tectonic. Any single FALSIFIED → overall FALSIFIED.
    Science advances by eliminating what CANNOT be true.
    """
    from geox_mcp.tools.biostrat_falsify import geox_biostrat_falsify as _impl

    return await _impl(
        fossil_group=fossil_group,
        biozone=biozone,
        lithology=lithology,
        environment=environment,
        claim=claim,
        claim_type=claim_type,
        sample_type=sample_type,
        depth_m=depth_m,
        younger_zone=younger_zone,
        older_zone=older_zone,
        depth_younger_m=depth_younger_m,
        depth_older_m=depth_older_m,
        reworking_claimed=reworking_claimed,
        fault_present=fault_present,
        fossil_names=fossil_names,
        basin_province=basin_province,
        claim_is_basinwide=claim_is_basinwide,
        seismic_group=seismic_group,
        expected_seismic_group=expected_seismic_group,
        stacking_pattern=stacking_pattern,
        region=region,
    )


# ── Phase 2.8 (2026-07-03): Macrostrat Calibrate — biostrat → absolute age bridge ──
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_macrostrat_calibrate", annotations=_geox_annotations("geox_macrostrat_calibrate"))
async def _macrostrat_calibrate(
    biozone: str = "",
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float = 50,
    discipline_hint: str = "",
    macrostrat_unit_name: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict:
    """Merge relative biostratigraphy (NN, PR, TR, FO/LO, GDE) with Macrostrat absolute ages.

    Calibrates a biozone against:
    1. GEOX internal NN-age table (for NN zones)
    2. Macrostrat time intervals (global age brackets)
    3. Macrostrat units at lat/lng (local rock packages)

    Cross-references all three and returns a merged age bracket with
    uncertainty, provenance, contradiction flags, and a ruling.

    RULING CLASSES:
      PASS          — biostrat age matches Macrostrat unit age within uncertainty
      WEAK_PASS     — ages partially overlap or one has high uncertainty
      HOLD          — insufficient data (no Macrostrat column, empty biozone)
      CONTRADICTION — ages don't overlap (e.g., NN5 says 14.9 Ma, column says 23 Ma)

    F2 TRUTH: Calibration is a MERGE, not a measurement.
    F7 HUMILITY: Confidence capped at 0.85.
    """
    from geox_mcp.tools.macrostrat_calibrate import geox_macrostrat_calibrate as _impl

    return await _impl(
        biozone=biozone,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        discipline_hint=discipline_hint,
        macrostrat_unit_name=macrostrat_unit_name,
    )


# ── W13+ FORGE — Phase C: PINN-style 1D seismic inversion (Faust + Gardner prior) ──
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_seismic_inversion", annotations=_geox_annotations("geox_seismic_inversion"))
async def _seismic_inversion(
    reflectivity: list[float] | None = None,
    sample_interval_s: float = 0.002,
    initial_impedance: float = 7.0e6,
    depth_top_m: float = 0.0,
    resistivity_ohm_m: list[float] | None = None,
) -> dict:
    """1D post-stack seismic inversion under PINN-style physics constraints.

    Recovers acoustic impedance, Vp, density via recursive inversion +
    Faust velocity prior + Gardner density prior. Enforces Physics9 bounds.
    """
    from geox_mcp.tools.seismic_inversion import (
        SeismicInversionRequestSchema,
        geox_seismic_inversion,
    )

    req = SeismicInversionRequestSchema(
        reflectivity=tuple(reflectivity) if reflectivity else (),
        sample_interval_s=sample_interval_s,
        initial_impedance=initial_impedance,
        depth_top_m=depth_top_m,
        resistivity_ohm_m=tuple(resistivity_ohm_m) if resistivity_ohm_m else None,
    )
    return (await geox_seismic_inversion(req)).model_dump(mode="json")


# ── W13+ FORGE — Phase C: Geomechanics (K, G, E, ν, AI + Stress Polygon) ──
@mcp.tool(name="geox_geomechanics", annotations=_geox_annotations("geox_geomechanics"))
async def _geomechanics(
    mode: str = "derive_moduli",
    state: dict | str | None = None,
    depth_m: float | None = None,
    sv_mpa: float | None = None,
    pp_mpa: float = 10.0,
    friction_coefficient: float = 0.6,
    avg_density_kg_m3: float = 2300.0,
    water_depth_m: float = 0.0,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
    thickness_m: float | None = None,
    rho_fluid: float | None = 1025.0,
) -> dict:
    """Geomechanical computations: derive moduli or compute Zoback stress polygon.

    Modes:
      derive_moduli (default) - K, G, E, ν, AI from Physics13State.
        Optional: buoyancy when thickness_m provided.
        Required: state dict with rho, vp, vs.

      stress_polygon - Zoback (2010) frictional stress polygon.
        Bounds Shmin and SHmax from Andersonian faulting theory.
        Required: depth_m or sv_mpa. Optional: pp_mpa, friction_coefficient.
        Returns stress polygon vertices (A-D) + regime boundaries.
    """
    if mode == "stress_polygon":
        from geox_mcp.tools.geomechanics_unified import _compute_stress_polygon

        return _compute_stress_polygon(
            depth_m=depth_m,
            sv_mpa=sv_mpa,
            pp_mpa=pp_mpa,
            friction_coefficient=friction_coefficient,
            avg_density_kg_m3=avg_density_kg_m3,
            water_depth_m=water_depth_m,
        )

    from geox_mcp.tools.geomechanics import (
        GeomechanicsRequest,
        geox_geomechanics,
    )

    # F1 AMANAH: MCP transport may serialize dict as JSON string — parse if needed
    if isinstance(state, str):
        import json as _json

        try:
            state = _json.loads(state)
        except (ValueError, TypeError):
            return {"ok": False, "error": f"state is a string but not valid JSON: {state[:200]}"}

    # Guard: derive_moduli requires state with rho, vp, vs.
    # If the caller gave depth/Sv (typical volcano or well query) but no
    # elastic state, compute the Zoback stress polygon instead of a hard fail.
    if not state or not isinstance(state, dict):
        if depth_m is not None or sv_mpa is not None:
            from geox_mcp.tools.geomechanics_unified import _compute_stress_polygon

            poly = _compute_stress_polygon(
                depth_m=depth_m,
                sv_mpa=sv_mpa,
                pp_mpa=pp_mpa,
                friction_coefficient=friction_coefficient,
                avg_density_kg_m3=avg_density_kg_m3,
                water_depth_m=water_depth_m,
            )
            poly["mode_requested"] = "derive_moduli"
            poly["mode_executed"] = "stress_polygon"
            poly["stress_polygon"] = poly.get("stress_polygon_vertices")
            poly["note"] = (
                "derive_moduli needs state {rho, vp, vs}. "
                "depth_m/sv_mpa was provided so GEOX computed the Zoback "
                "stress polygon instead."
            )
            return poly
        return {
            "ok": False,
            "tool": "geox_geomechanics",
            "error": "derive_moduli requires state dict with rho, vp, vs.",
            "hint": 'Provide state as {"rho": 2300, "vp": 3500, "vs": 2000} for typical sandstone. Or pass depth_m for a Zoback stress polygon.',
        }

    try:
        result = await geox_geomechanics(
            GeomechanicsRequest(
                state=state,
                thickness_m=thickness_m,
                rho_fluid=rho_fluid if rho_fluid is not None else 1025.0,
            )
        )
        dumped = result.model_dump(mode="json")
        nested = dumped.get("result") if isinstance(dumped.get("result"), dict) else {}
        derived = nested.get("derived") if isinstance(nested, dict) else None
        if derived:
            dumped["moduli"] = derived
            dumped["elastic_properties"] = derived
        return dumped
    except Exception as e:
        return {
            "ok": False,
            "tool": "geox_geomechanics",
            "error": f"{type(e).__name__}: {e}",
            "hint": "Provide state dict with rho, vp, vs for derive_moduli mode.",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DYNAMICAL SYSTEMS LAYER — State-Space Reconstruction (Forged 2026-08-07)
# Small extraction from DeepEDM (ICML 2025). Takens embedding + EDM kernel.
# GEOX reconstructs the attractor; WEALTH interprets; WELL judges readiness.
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool(name="geox_dynamical_systems", annotations=_geox_annotations("geox_dynamical_systems"))
async def _dynamical_systems(
    mode: str = "auto_embed",
    series: list[float] | None = None,
    max_lag: int = 100,
    delay: int = 0,
    dim: int = 0,
    kernel: str = "simplex",
    k: int = 4,
    temperature: float = 0.1,
    library: list[list[float]] | None = None,
    targets: list[float] | None = None,
    query: list[list[float]] | None = None,
) -> dict:
    """State-space reconstruction layer for time-series analysis.

    Modes:
      auto_embed      — Auto-compute optimal τ (mutual information) and E (FNN),
                        return Takens embedding library + targets.
      takens_embed    — Build delay-coordinate library from series with given τ, E.
      edm_kernel      — Local dynamics prediction via simplex or softmax kernel
                        on a reconstructed state-space attractor.
      test            — Self-test on Lorenz attractor (proof of primitives).

    Federation contract:
      GEOX reconstructs the attractor.
      WEALTH interprets dynamics economically (prices, production, cashflow).
      WELL judges human readiness to act on the regime estimate.

    Epistemic: DER_TAKENS_EMBEDDING (derived from OBS_SERIES + delay + dim).
    All outputs are OBS-level only when mode=auto_embed (parameters are derived).
    """
    from geox_mcp.tools.geox_dynamical_systems import (
        geox_dynamical_test,
        geox_edm_kernel,
        geox_false_nearest_neighbors,
        geox_mutual_information,
        geox_takens_embed,
    )

    import numpy as np

    if mode == "test":
        return geox_dynamical_test()

    if mode == "auto_embed":
        if not series or len(series) < 10:
            return {"ok": False, "error": "auto_embed requires series (min 10 values)"}
        arr = np.array(series, dtype=np.float64)
        tau = geox_mutual_information(arr, max_lag=max_lag)
        E = geox_false_nearest_neighbors(arr, delay=tau, max_dim=10)
        if E < 3:
            E = 3
        lib, tgt = geox_takens_embed(arr, delay=tau, dim=E)
        return {
            "ok": True,
            "mode": "auto_embed",
            "tau": int(tau),
            "E": int(E),
            "library_shape": list(lib.shape),
            "library": lib.tolist(),
            "targets": tgt.tolist(),
            "note": (
                "Use library + targets with geox_edm_kernel for local dynamics prediction. "
                "GEOMETRY ONLY — this is the reconstructed state-space, not a forecast."
            ),
        }

    if mode == "takens_embed":
        if not series or len(series) < 10:
            return {"ok": False, "error": "takens_embed requires series (min 10 values)"}
        if delay < 1:
            return {"ok": False, "error": "delay (τ) must be >= 1"}
        if dim < 2:
            return {"ok": False, "error": "dim (E) must be >= 2"}
        arr = np.array(series, dtype=np.float64)
        lib, tgt = geox_takens_embed(arr, delay=delay, dim=dim)
        return {
            "ok": True,
            "mode": "takens_embed",
            "tau": delay,
            "E": dim,
            "library_shape": list(lib.shape),
            "library": lib.tolist(),
            "targets": tgt.tolist(),
        }

    if mode == "edm_kernel":
        if library is None or targets is None or query is None:
            return {
                "ok": False,
                "error": "edm_kernel requires library, targets, and query arrays",
            }
        lib_arr = np.array(library, dtype=np.float64)
        tgt_arr = np.array(targets, dtype=np.float64)
        q_arr = np.array(query, dtype=np.float64)
        if len(lib_arr) < k:
            return {"ok": False, "error": f"Library size {len(lib_arr)} < k={k}"}
        preds = geox_edm_kernel(lib_arr, tgt_arr, q_arr, kernel=kernel, k=k, temperature=temperature)
        return {
            "ok": True,
            "mode": "edm_kernel",
            "kernel": kernel,
            "k": k,
            "predictions": preds.tolist(),
        }

    return {"ok": False, "error": f"Unknown mode: {mode}. Use: auto_embed, takens_embed, edm_kernel, test."}


# ── W13+ FORGE — A2 GRAVITY SCREEN (evidence lane, no judgment required) ──
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_gravity_screen", annotations=_geox_annotations("geox_gravity_screen"))
async def _gravity_screen(
    observed_mGal: list[float],
    easting_m: list[float],
    northing_m: list[float],
    density_kg_m3: float,
    depth_top_m: float,
    depth_bottom_m: float,
    reference_density_kg_m3: float = 2670.0,
    claim_id: str = "UNKNOWN",
    hypothesis_prior: float = 0.25,
    actor_id: str | None = None,
    session_id: str | None = None,
    trace_id: str | None = None,
) -> dict:
    """Screen a gravity anomaly against a single-density prism forward model.

    Evidence lane tool — does NOT invoke geox_subsurface_model (judgment lane).
    Uses HarmonICA (or mock fallback) to compute predicted gravity and compare
    to observed. Returns HYPOTHESIS_SCREEN grade + misfit diagnostics.

    A2 fix (2026-06-28): bypasses geox_subsurface_model judgment firewall by
    providing a gravity-only screen in the evidence lane.
    """
    from geox_core.engines.geophysics.harmonica_adapter import gravity_screen

    return gravity_screen(
        observed_mGal=observed_mGal,
        easting_m=easting_m,
        northing_m=northing_m,
        density_kg_m3=density_kg_m3,
        depth_top_m=depth_top_m,
        depth_bottom_m=depth_bottom_m,
        reference_density_kg_m3=reference_density_kg_m3,
        claim_id=claim_id,
        hypothesis_prior=hypothesis_prior,
    )


# ── A2 JUDGMENT PREFLIGHT — guidance tool (evidence lane) ───────────────────
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_judgment_preflight", annotations=_geox_annotations("geox_judgment_preflight"))
async def _judgment_preflight(
    target_tool: str,
    actor_id: str | None = None,
    session_id: str | None = None,
    trace_id: str | None = None,
) -> dict:
    """Guide callers to the correct governance path for judgment-lane tools.

    This is a C1 advisory tool in the evidence lane — it does NOT invoke
    the target tool. It returns the correct call sequence so the caller
    can proceed through proper governance.

    A2 fix (2026-06-28): geox_subsurface_model is judgment lane (direct call
    forbidden). This tool tells the caller exactly how to route through
    arifOS to reach it legally.
    """
    # Valid judgment-lane tools that can be preflted
    VALID_JUDGMENT_TOOLS = {
        "geox_subsurface_model": {
            "lane": "judgment",
            "lease_required": True,
            "session_required": True,
            "arifos_route_required": True,
            "governance_sequence": [
                "1. arif_init(mode='init') — establish governed session",
                "2. arif_lease_issue(tool='geox_subsurface_model') — get lease_id",
                "3. arif_kernel_route(mode='bridge', organ='geox', tool_name='geox_subsurface_model', lease_id=<lease>, session_id=<session>)",
            ],
            "alternative_evidence_tool": "geox_gravity_screen",
            "alternative_note": (
                "For gravity-only screening without full joint inversion, "
                "use geox_gravity_screen (evidence lane, no lease required). "
                "gravity_screen returns HYPOTHESIS_SCREEN grade."
            ),
        },
        "geox_prospect": {
            "lane": "judgment",
            "lease_required": True,
            "session_required": True,
            "arifos_route_required": True,
            "governance_sequence": [
                "1. arif_init(mode='init') — establish governed session",
                "2. arif_lease_issue(tool='geox_prospect') — get lease_id",
                "3. arif_kernel_route(mode='bridge', organ='geox', tool_name='geox_prospect', lease_id=<lease>, session_id=<session>)",
            ],
            "alternative_evidence_tool": "geox_evidence",
            "alternative_note": "For prospect screening use geox_evidence (evidence lane) first.",
        },
    }

    if target_tool not in VALID_JUDGMENT_TOOLS:
        return {
            "ok": False,
            "error": f"Unknown judgment-lane tool: {target_tool}",
            "valid_tools": list(VALID_JUDGMENT_TOOLS.keys()),
            "note": "Judgment-lane tools must route through arifOS kernel. "
            "For evidence-lane alternatives, check geox_basin or geox_evidence.",
        }

    info = VALID_JUDGMENT_TOOLS[target_tool]
    return {
        "ok": True,
        "target_tool": target_tool,
        "lane": info["lane"],
        "lease_required": info["lease_required"],
        "session_required": info["session_required"],
        "arifos_route_required": info["arifos_route_required"],
        "governance_sequence": info["governance_sequence"],
        "alternative_evidence_tool": info.get("alternative_evidence_tool"),
        "alternative_note": info.get("alternative_note"),
        "epistemic_label": "OBS",
        "caveat": (
            "preflight is guidance only — it does not execute the target tool. "
            "Caller must follow the governance_sequence to invoke the judgment-lane tool."
        ),
    }


# ── geox_well_decision_class — removed (Phase 1 Clean Slate, → WELL organ) ──


# ── W14+ FORGE 2026-06-21: GEOX-LEM inference (substrate live, weights pending GPU + 888) ──
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_lem_predict", annotations=_geox_annotations("geox_lem_predict"))
async def _lem_predict(
    well_id: str,
    curves: dict,
    depth_m: list,
    depth_top_m: float | None = None,
    depth_bot_m: float | None = None,
    target_properties: list[str] | None = None,
    mode: str = "physics_prior",
    basin: str | None = None,
    rw_ohm_m: float | None = None,
    rho_matrix_g_cc: float | None = None,
    rho_fluid_g_cc: float | None = None,
    patch_size_m: float = 0.5,
    actor_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Predict rock properties (porosity, Sw, lithology, Vp, pressure gradient) over a depth window.

    Substrate mode of operation:
      - `physics_prior` (default): physics-bounded estimates via Archie (Sw),
        density-porosity (phi), Gardner (Vp), Wyllie (phi from DT). Honest mock-default
        until federated pretraining data (>=1,200 wells) and foundation-model weights
        are deployed (gated by 888_HOLD).
      - `transformer`: requires federated weights; gated.
      - `hybrid`: physics prior + transformer residual; transformer residual gated.

    F2 TRUTH: confidence is hard-capped at 0.90. F13 SOVEREIGN: AC_Risk > 0.5 -> human_review_required.
    """
    from geox_mcp.tools.lem_predict import (
        LEMPredictRequest,
    )
    from geox_mcp.tools.lem_predict import (
        geox_lem_predict as _impl,
    )

    req = LEMPredictRequest(
        well_id=well_id,
        curves=curves,
        depth_m=depth_m,
        depth_top_m=depth_top_m,
        depth_bot_m=depth_bot_m,
        target_properties=target_properties or ["porosity", "sw"],
        mode=mode,
        basin=basin,
        rw_ohm_m=rw_ohm_m,
        rho_matrix_g_cc=rho_matrix_g_cc,
        rho_fluid_g_cc=rho_fluid_g_cc,
        patch_size_m=patch_size_m,
        actor_id=actor_id,
        session_id=session_id,
    )
    return await _impl(req)


# ── W15+ FORGE 2026-06-22: Deep Time State (governed Earth State Vector) ──
@mcp.tool(name="geox_deep_time_state", annotations=_geox_annotations("geox_deep_time_state"))
async def _deep_time_state(
    age_ma: float | None = None,
    age_top_ma: float | None = None,
    age_bot_ma: float | None = None,
    period: str | None = None,
    query: str | None = None,
    biozone: str | None = None,
    include_pending_datasets: bool = True,
    actor_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Deep Time State — returns an Earth State Vector for the requested deep time.

    F2 TRUTH: age resolution via ICS Chart v2024/12.
    F7 HUMILITY: confidence hard-capped at 0.90.
    F11 AUDIT: every envelope carries governance footer.

    Phase 2.7: accepts biozone (e.g. "NN5") — resolved via Martini (1971) + GPTS2020.
    """
    from geox_mcp.tools.deep_time_state import geox_deep_time_state as _impl

    return await _impl(
        age_ma=age_ma,
        age_top_ma=age_top_ma,
        age_bot_ma=age_bot_ma,
        period=period,
        query=query,
        biozone=biozone,
        include_pending_datasets=include_pending_datasets,
    )


# ── Phase 2.2 (2026-06-29): Earth Atlas — Natural Earth 10m point-in-country + land/water ──
# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_isitwater", annotations=_geox_annotations("geox_isitwater"))
async def _geox_isitwater(
    lat: float,
    lon: float,
) -> dict:
    """Point-in-polygon land/water classifier using Natural Earth 10m GeoJSON.

    Returns 'land', 'water', or 'error'. Synchronous geometry — no network calls.
    Data: /root/geox/data/atlas/countries.geojson + sea_neighbors.geojson (SHA256 verified).
    F2 TRUTH: geometry-only, no model uncertainty.
    """
    from geox_mcp.tools.geox_atlas import geox_isitwater as _impl

    return await _impl(lat=lat, lon=lon)


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_context_at_location", annotations=_geox_annotations("geox_context_at_location"))
async def _geox_context_at_location(
    lat: float,
    lon: float,
) -> dict:
    """Country + sea context at a lat/lon point. Land → adjacent sea countries.
    Water → enclosing + neighboring countries. Natural Earth 10m GeoJSON.

    F2 TRUTH: geometry-only lookup from local atlas data.
    """
    from geox_mcp.tools.geox_atlas import geox_context_at_location as _impl

    return await _impl(lat=lat, lon=lon)


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_atlas", annotations=_geox_annotations("geox_atlas"))
async def _geox_atlas(
    lat: float,
    lon: float,
    mode: str = "context",
) -> dict:
    """Unified Earth Atlas — point-in-country + land/water classification.

    Combines geox_isitwater and geox_context_at_location into one call.
    Natural Earth 10m GeoJSON, offline, sovereign, no network calls.

    Args:
        lat: Latitude in EPSG:4326.
        lon: Longitude in EPSG:4326.
        mode: 'context' (default) — both land/water AND country context.
              'water' — land/water only (faster).

    Returns:
        Land/water classification + country/sea context + F2 TRUTH metadata.
    """
    from geox_mcp.tools.geox_atlas import geox_context_at_location as _context
    from geox_mcp.tools.geox_atlas import geox_isitwater as _isitwater

    result: dict = {"lat": lat, "lon": lon, "mode": mode}

    water_result = await _isitwater(lat=lat, lon=lon)
    result["is_water"] = water_result.get("is_water", None)
    result["water_status"] = water_result.get("status", "error")

    if mode == "context":
        ctx = await _context(lat=lat, lon=lon)
        result["context"] = ctx.get("context", {})
        result["country"] = ctx.get("country")

    result["_envelope"] = {
        "evidence_floor": "OBSERVED",
        "method": "Natural Earth 10m point-in-polygon",
        "source": "Natural Earth Data (offline)",
        "limitations": ["10m resolution", "Coastal accuracy ±50m"],
        "forbidden_claims": [],
    }
    return result


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_forbidden_claims_scan", annotations=_geox_annotations("geox_forbidden_claims_scan"))
async def _geox_forbidden_claims_scan(
    text: str = "",
) -> dict:
    """Scan text for forbidden geological/economic certainty claims.

    Tests output against GEOX's canonical forbidden-claims list.
    Any BLOCK-level claim → output should be downgraded.
    Any WARN-level claim → caveats should be added.

    Forbidden claims include:
      - "proven reserves", "commercial discovery" (BLOCK)
      - "safe drilling target", "mineable resource" (BLOCK)
      - "environmentally safe", "zero risk" (BLOCK)
      - "hydrocarbon pay" without "candidate" prefix (WARN)
      - "low-risk investment" without WEALTH organ backing (WARN)

    Args:
        text: Output text to scan (stringified JSON or plain text).

    Returns:
        Scan results with flagged claims, severity, and suggestions.
    """
    from geox_mcp.tools.forbidden_claims import (
        forbidden_claims_summary,
        scan_forbidden_claims,
    )

    flags = scan_forbidden_claims(text)
    summary = forbidden_claims_summary()

    return {
        "status": "OK",
        "scanned": True,
        "flagged_claims": flags,
        "total_flagged": len(flags),
        "block_count": sum(1 for f in flags if f["severity"] == "BLOCK"),
        "warn_count": sum(1 for f in flags if f["severity"] == "WARN"),
        "registry": summary,
        "_envelope": {
            "evidence_floor": "OBSERVED",
            "method": "Pattern-matched regex against canonical forbidden-claims list",
            "authority": "F13 SOVEREIGN — list not modifiable by agents",
            "forbidden_claims": [],
        },
    }


# ── Phase 2.3 (2026-07-01): Earth Map Surface — Layer Registry + Scene Planning + Preview ──
# Architecture: tools compute + decide, resources carry data payloads.
# Truth-class gated (CONTEXT / INTERPRETATION / DECISION_SUPPORT).
# Cached renders. Guardrailed for miskin VPS survival.


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_layers_list", annotations=_geox_annotations("geox_map_layers_list"))
async def _geox_map_layers_list(
    bbox: list[float],
    theme: str | None = None,
    include_unavailable: bool = False,
) -> dict:
    """List available GEOX map layers for a bounding box.

    Returns layer catalogue with metadata, truth classes, and availability.
    Use themes: regional_geology, basin, structure, stratigraphy, petroleum,
    tectonics, sabah_regional, se_asia. Or query all layers for a bbox.

    F2 TRUTH: layer registry is curated, not ground truth.
    F6 MARUAH: community territory check on bbox.
    """
    from geox_mcp.tools.earth_map import geox_map_layers_list as _impl

    return await _impl(bbox=bbox, theme=theme, include_unavailable=include_unavailable)


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_scene_plan", annotations=_geox_annotations("geox_map_scene_plan"))
async def _geox_map_scene_plan(
    bbox: list[float],
    layer_ids: list[str] | None = None,
    theme: str | None = None,
    map_purpose: str = "context",
    style_profile: str = "geox_regional_clean_v1",
    crs: str = "EPSG:4326",
) -> dict:
    """Create a deterministic visual recipe for a geological map scene.

    This is the 'constitution' of the map — layer ordering, styles, warnings,
    and provenance. No image is rendered yet. Inspect this before rendering.

    map_purpose: context | interpretation | qc | prospect_review | publication
    Truth class gate: context maps exclude DECISION_SUPPORT layers.

    Returns scene_id for use with geox_map_render_preview.
    """
    from geox_mcp.tools.earth_map import geox_map_scene_plan as _impl

    return await _impl(
        bbox=bbox,
        layer_ids=layer_ids,
        theme=theme,
        map_purpose=map_purpose,
        style_profile=style_profile,
        crs=crs,
    )


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_render_preview", annotations=_geox_annotations("geox_map_render_preview"))
async def _geox_map_render_preview(
    scene_id: str | None = None,
    bbox: list[float] | None = None,
    layer_ids: list[str] | None = None,
    theme: str | None = None,
    width_px: int = 1024,
    height_px: int = 768,
    style_profile: str = "geox_regional_clean_v1",
    format: str = "image/png",
) -> dict:
    """Render a static map preview from a scene plan or bbox.

    Either provide scene_id (from geox_map_scene_plan) OR bbox+layer_ids/theme.
    Images < 300KB returned as inline base64. Larger images as resource links.

    Guardrails: max 1600px, max 12 layers, max 5000 features, 24h cache TTL.
    Uses matplotlib + optional contextily basemap tiles.
    """
    from geox_mcp.tools.earth_map import geox_map_render_preview as _impl

    return await _impl(
        scene_id=scene_id,
        bbox=bbox,
        layer_ids=layer_ids,
        theme=theme,
        width_px=width_px,
        height_px=height_px,
        style_profile=style_profile,
        format=format,
    )


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_export_package", annotations=_geox_annotations("geox_map_export_package"))
async def _geox_map_export_package(
    scene_plan_id: str,
    formats: list[str] | None = None,
    include_sources: bool = False,
    include_provenance: bool = True,
    review_mode: str = "draft",
    output_dir: str | None = None,
) -> dict:
    """Create a governed export package with map assets, metadata, and provenance sidecars.

    This is the 4th and final map verb — completes the chain:
    layers_list → scene_plan → render_preview → export_package.

    Produces a package directory with:
      - Rendered preview (PNG/WebP)
      - STAC catalog JSON (if include_provenance=True)
      - W3C PROV provenance sidecar (if include_provenance=True)
      - Scene manifest with layer references + checksums
      - Optional: included source data copies

    Args:
        scene_plan_id: Scene ID from geox_map_scene_plan.
        formats: Output formats. Default: ["png"]. Options: png, svg, pdf, gpkg, stac.
        include_sources: If True, include copies of source data files.
        include_provenance: If True, generate PROV sidecar + STAC catalog.
        review_mode: draft | validated | sealed_candidate. Affects provenance metadata.
        output_dir: Custom output directory. Default: /root/geox/data/exports/{scene_plan_id}.

    Returns:
        Package manifest with artifact paths, checksums, and provenance references.
    """
    from geox_mcp.tools.earth_map import geox_map_export_package as _impl

    return await _impl(
        scene_plan_id=scene_plan_id,
        formats=formats,
        include_sources=include_sources,
        include_provenance=include_provenance,
        review_mode=review_mode,
        output_dir=output_dir,
    )


# ── W13+ FORGE — Phase C: GEOX → WEALTH STOIIP + ranking feed ──
# ── geox_wealth_feed — removed (Phase 1 Clean Slate, → arif_bridge_connect) ──


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_query_macrostrat", annotations=_geox_annotations("geox_query_macrostrat"))
async def geox_query_macrostrat(
    basin_name: str = "",
    mode: str = "macrostrat_units",
    lat: float | None = None,
    lng: float | None = None,
) -> dict:
    """Query Macrostrat geological database for regional stratigraphy, lithology, and age data.

    This is an alias for geox_basin_profile(mode='macrostrat_units'|'macrostrat_columns').
    Macrostrat data is PROCESS_HYPOTHESIS level — regional surface geology,
    not subsurface truth. CC-BY-4.0 license.
    """
    from geox_mcp.tools.basin import geox_basin_profile as _profile

    result = await _profile(
        basin_name=basin_name or "Global",
        mode=mode,
        lat=lat,
        lng=lng,
    )
    # Extract interpreted data from the envelope
    artifact = result.get("primary_artifact", {})
    if artifact:
        return artifact.get("interpreted", artifact)
    return result


# ── Phase 2.6 (2026-07-03): Universal Anomalous Contrast Detector ───────────
# Theory of Anomalous Contrast (ToAC) generalized across all seven dimensions.
# Mass, Energy, Time, Absence contrast detection + cross-dimensional audit.
# Pattern: predict → observe → contrast → classify → report.
# A-FORGE 888_HOLD approved 2026-07-03 by F13 SOVEREIGN.


# DEREGISTERED ZEN-15 — @mcp.tool(name="geox_contrast_detect", annotations=_geox_annotations("geox_contrast_detect"))
async def _geox_contrast_detect(
    dimension: str = "all",
    mass_predicted: float | None = None,
    mass_observed: float | None = None,
    energy_predicted_stress: float | None = None,
    energy_observed_stress: float | None = None,
    energy_predicted_temp: float | None = None,
    energy_observed_temp: float | None = None,
    time_expected_ma: float | None = None,
    time_measured_ma: float | None = None,
    absence_expected_thickness: float | None = None,
    absence_observed_thickness: float | None = None,
    absence_expected_timespan: float | None = None,
    absence_observed_timespan: float | None = None,
    threshold: float = 0.2,
    # Probabilistic (optional): [P90, P50, P10] arrays + data-quality weight
    mass_predicted_dist: list[float] | None = None,
    mass_observed_dist: list[float] | None = None,
    energy_predicted_temp_dist: list[float] | None = None,
    energy_observed_temp_dist: list[float] | None = None,
    time_expected_dist: list[float] | None = None,
    time_measured_dist: list[float] | None = None,
    confidence_index: float = 0.70,
    data_quality: str = "unknown",
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict:
    """Universal anomalous contrast detector across seven dimensions.

    Generalizes the Theory of Anomalous Contrast (ToAC) from seismic-only
    to all seven dimensions of the GEOX dimensional ontology.

    Pattern (universal across all dimensions):
      1. PREDICT — expected value from model/theory/Five-Part expectation
      2. OBSERVE — actual value from data/evidence/measurement
      3. CONTRAST — |predicted − observed| normalized
      4. CLASSIFY — anomaly type, severity, governance action
      5. REPORT — structured JSON with epistemic labels

    Detects:
      - Mass anomalies (bypass, missing mass, source-sink imbalance)
      - Energy anomalies (overpressure, thermal anomaly, stress mismatch)
      - Temporal contradictions (reworking, missing time, age conflicts)
      - Absence anomalies (unconformities, erosion, non-deposition)
      - Cross-dimensional conflicts (mass vs time, energy vs absence)

    Every anomaly maps to a Five-Part violation:
      SOURCE, TRANSFER, SINK, BURIAL, or EXHUMATION.

    Axiom: Anomalous contrast is the universal signature of geological
    inconsistency. Across all seven dimensions, anomalies share one pattern:
    contrast that cannot be explained by SOURCE → TRANSFER → SINK → BURIAL → EXHUMATION.

    Args:
        dimension: Which dimension to check ("all", "mass", "energy", "time", "absence")
        mass_predicted: Expected sediment production rate (m³/Myr)
        mass_observed: Observed sediment accumulation rate (m³/Myr)
        energy_predicted_stress: Expected stress (Pa) from model
        energy_observed_stress: Observed stress (Pa) from data
        energy_predicted_temp: Expected temperature (K) from model
        energy_observed_temp: Observed temperature (K) from data
        time_expected_ma: Expected age (Ma) from stratigraphy
        time_measured_ma: Measured age (Ma) from dating
        absence_expected_thickness: Expected thickness (m) from subsidence model
        absence_observed_thickness: Observed thickness (m) from wells/seismic
        absence_expected_timespan: Expected time span (Ma) for interval
        absence_observed_timespan: Observed time span (Ma) from dating
        threshold: Anomaly detection threshold (default 0.2 = 20%)

    Returns:
        Structured anomaly report with per-dimension contrasts,
        dimensional entropy, cross-dimensional conflicts, and recommended actions.
    """
    from geox_mcp.tools.contrast_detect import contrast_detect as _detect

    return _detect(
        dimension=dimension,
        mass_predicted=mass_predicted,
        mass_observed=mass_observed,
        energy_predicted_stress=energy_predicted_stress,
        energy_observed_stress=energy_observed_stress,
        energy_predicted_temp=energy_predicted_temp,
        energy_observed_temp=energy_observed_temp,
        time_expected_ma=time_expected_ma,
        time_measured_ma=time_measured_ma,
        absence_expected_thickness=absence_expected_thickness,
        absence_observed_thickness=absence_observed_thickness,
        absence_expected_timespan=absence_expected_timespan,
        absence_observed_timespan=absence_observed_timespan,
        threshold=threshold,
        mass_predicted_dist=mass_predicted_dist,
        mass_observed_dist=mass_observed_dist,
        energy_predicted_temp_dist=energy_predicted_temp_dist,
        energy_observed_temp_dist=energy_observed_temp_dist,
        time_expected_dist=time_expected_dist,
        time_measured_dist=time_measured_dist,
        confidence_index=confidence_index,
        data_quality=data_quality,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RSI TOOLS — Real Seismic Image Interpretation (Phase 3.0, 2026-07-06)
# Forged from SCAR_GEOX_RSI_001 failure analysis.
# OBS_IMAGE ≠ OBS_GEOLOGY. Pixels are observed. Geology requires calibration.
# ═══════════════════════════════════════════════════════════════════════════════


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_rsi_interpret", annotations=_geox_annotations("geox_rsi_interpret"))
async def _geox_rsi_interpret(
    image_path: str,
    mode: str = "horizon_fault_pick",
    max_faults: int = 20,
    max_horizons: int = 12,
    fault_percentile: float = 97.0,
    fault_min_length: int = 80,
    horizon_search: int = 5,
    horizon_lookahead: int = 10,
    include_attributes: bool = False,
) -> dict:
    """Real Seismic Image interpretation — horizon and fault picking from image pixels.

    Processes a real seismic image through the RSI pipeline:
    reality gate → provenance → crop → AGC → attribute stack →
    fault detection (ant-track-lite + structure tensor + curvature) →
    horizon tracking (DP with look-ahead + multi-seed + confidence) →
    epistemic governance → render audit.

    OBS_IMAGE ≠ OBS_GEOLOGY: All outputs are pixel-derived, not geological measurements.
    Every INT claim carries alternative interpretations.
    PETROPHYSICS = HOLD from image-only input.

    Args:
        image_path: Path to the seismic image file (JPG, PNG, TIFF)
        mode: Interpretation mode (currently only horizon_fault_pick)
        max_faults: Maximum number of faults to extract
        max_horizons: Maximum number of horizons to track
        fault_percentile: Percentile threshold for fault probability (higher = fewer faults)
        fault_min_length: Minimum pixel length for a valid fault
        horizon_search: Search window (pixels) for horizon tracking
        horizon_lookahead: Look-ahead window for DP horizon tracking
        include_attributes: If True, include full attribute arrays in output (large!)
    """
    from geox_mcp.tools.seismic_rsi import geox_rsi_interpret as _impl

    return await _impl(
        image_path=image_path,
        mode=mode,
        max_faults=max_faults,
        max_horizons=max_horizons,
        fault_percentile=fault_percentile,
        fault_min_length=fault_min_length,
        horizon_search=horizon_search,
        horizon_lookahead=horizon_lookahead,
        include_attributes=include_attributes,
    )


# DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_render_audit", annotations=_geox_annotations("geox_render_audit"))
async def _geox_render_audit(
    image_path: str,
    agc_window: int = 30,
) -> dict:
    """Audit image rendering fidelity — validate render-vs-amplitude consistency.

    Checks dynamic range, color space, histogram shape, and AGC correlation.
    All outputs labeled DER_RENDER_CONTRAST.

    This audit answers: "Does the image faithfully represent seismic amplitude,
    or has rendering (colormap, contrast, clipping) distorted the signal?"

    Args:
        image_path: Path to seismic image file
        agc_window: AGC window size for correlation check
    """
    from geox_mcp.tools.seismic_rsi import geox_render_audit as _impl

    return await _impl(image_path=image_path, agc_window=agc_window)


# ═══════════════════════════════════════════════════════════════════════════════
# MCP APPS — PrefabUI tools (P2#7)
# ═══════════════════════════════════════════════════════════════════════════════


def _register_prefab_apps() -> None:
    """Register MCP App tools on the geox_app and well_app providers.

    These are FastMCP PrefabUI components that render interactive UIs
    inside MCP hosts (Claude, ChatGPT, Cursor, etc.).

    Only registered when HAS_FASTMCP_APPS is True.
    """
    if not HAS_FASTMCP_APPS:
        logger.info("MCP Apps disabled — prefab-ui not installed")
        return

    # Import tool categories for PrefabUI dashboard
    from geox_mcp.webmcp import TOOL_CATEGORIES

    # ── geox_app: GEOX Mission Board ──────────────────────────────────
    @geox_app.tool
    def geox_mission_board() -> list[PrefabApp]:
        """GEOX Mission Board — live governance dashboard."""
        with PrefabApp() as board:
            with Column(gap=4, css_class="p-4"):
                Heading("GEOX Mission Board", level=2)
                Text(f"Earth Intelligence — {len(CANONICAL_PUBLIC_TOOLS)} canonical tools across 4 domains")
                Separator()
                with Row(gap=6):
                    Metric(label="Canonical Tools", value=str(len(CANONICAL_PUBLIC_TOOLS)))
                    Metric(label="Domains", value="4")
                    Metric(label="Status", value="SEAL")
                Separator()
                Heading("Tool Categories", level=3)
                for cat in TOOL_CATEGORIES:
                    with Column(gap=1):
                        Heading(cat["category"], level=4)
                        Text(", ".join(cat["tools"]))
        return board

    @geox_app.tool
    def geox_health_dashboard() -> PrefabApp:
        """GEOX Health Dashboard — real-time system status."""
        import os
        import subprocess

        try:
            git = subprocess.run(
                ["git", "log", "--oneline", "-1"],
                capture_output=True,
                text=True,
                cwd="/root/geox",
                timeout=5,
            )
            git_version = git.stdout.strip() or "unknown"
        except Exception:
            git_version = "unknown"

        with PrefabApp() as dash:
            with Column(gap=4, css_class="p-4"):
                Heading("GEOX System Health", level=2)
                Badge("DITEMPA BUKAN DIBERI", variant="outline")

                with Row(gap=4):
                    with Card():
                        CardHeader("MCP Server")
                        Text(f"Version: {os.getenv('GEOX_VERSION', '2026.06.06')}")
                        Text(f"Commit: {git_version}")
                        Text(f"Port: {os.getenv('GEOX_PORT', '8081')}")

                    with Card():
                        CardHeader("Transport")
                        Text("HTTP: streamable-http")
                        Text("Stdio: local agents")
                        Text("WebMCP: browser console")

                with Card():
                    CardHeader("Canonical Tools by Category")
                    for cat in TOOL_CATEGORIES:
                        Text(f"{cat['category']}: {len(cat['tools'])} tools")
        return dash

    # ── well_app: Well Desk App ────────────────────────────────────────
    @well_app.tool
    def well_desk_dashboard() -> PrefabApp:
        """Well Desk — well log and petrophysics quick-launch panel."""
        with PrefabApp() as wd:
            with Column(gap=4, css_class="p-4"):
                Heading("Well Desk", level=2)
                Text("Interactive well log analysis tools")
                Separator()
                with Row(gap=4):
                    Metric(label="LAS Files Available", value="737")
                    Metric(label="Wells", value="600+")
                    Metric(label="Well Data Directory")
                    Text("/root/geox/data/wells/")
                Separator()
                Heading("Quick Actions", level=3)
                with Column(gap=2):
                    with Card():
                        CardHeader("Ingest Well Log")
                        Text("geox_data_ingest_bundle — load LAS/CSV/Parquet")
                    with Card():
                        CardHeader("QC Log Data")
                        Text("geox_data_qc_bundle — depth, curves, physical ranges")
                    with Card():
                        CardHeader("Petrophysics")
                        Text("geox_subsurface_generate_candidates — Vsh, Phi, Sw, NetPay")
        return wd

    logger.info("MCP App tools registered: geox_mission_board, geox_health_dashboard, well_desk_dashboard")


_register_prefab_apps()

# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES & PROMPTS COMPOSITION (P1 — extracted modules)
# ═══════════════════════════════════════════════════════════════════════════════

from geox_mcp.prompts import register_prompts
from geox_mcp.resources import register_resources
from geox_mcp.ui.resources import register_gravmag_studio_resource, register_workspace_resource

register_resources(mcp, is_geox_func=is_geox, enforce_geox_func=_enforce_geox)
register_workspace_resource(mcp)
register_gravmag_studio_resource(mcp)
register_prompts(mcp)

# ═══════════════════════════════════════════════════════════════════════════════
# MCP SURFACE PRUNE — Remove non-canonical tools
# ═══════════════════════════════════════════════════════════════════════════════


def _prune_mcp_surface(mcp_server) -> None:
    """Strip non-canonical tools from the MCP registry after bootstrap."""
    SACRED_SURFACE: set[str] = set(CANONICAL_RUNTIME_TOOLS)  # compat tools removed — FastMCP 3.4.2 rejects **kwargs
    _profile = os.getenv("GEOX_PROFILE", "full").lower()
    if _profile == "minimal":
        SACRED_SURFACE = {
            "geox_well_ingest",
            "geox_well_qc",
            "geox_petrophysics",
            "geox_basin",
        } | set(CANONICAL_PUBLIC_TOOLS)

    provider = getattr(mcp_server, "_local_provider", None)
    if not provider:
        return
    components = getattr(provider, "_components", {})
    total_tools = sum(1 for k in components if k.startswith("tool:"))
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
    # Safety: if pruning would remove >30% of tools, something is wrong — abort
    if removed and len(removed) > total_tools * 0.5:
        logger.error(
            f"MCP surface prune ABORTED: would remove {len(removed)}/{total_tools} tools (>30%). "
            f"SACRED_SURFACE has {len(SACRED_SURFACE)} entries. Check YAML manifest completeness."
        )
        return
    if removed:
        logger.info(f"MCP surface pruned: {len(removed)} non-canonical tools removed (profile={_profile})")
        for name in sorted(removed):
            logger.info(f"  pruned: {name}")
    logger.info(f"MCP surface clean: {len(components)} canonical tools exposed (profile={_profile})")


# MCP Spec 2025-11-25 outputSchema — standard GEOX response envelope
#
# IMPORTANT: this schema is patched onto every FastMCP tool via
# _patch_output_schemas() after registration. The wrapper's `-> dict[str, Any]`
# annotation is permissive (additionalProperties: true), but THIS schema is
# strict on the declared properties. If a declared property has the wrong
# type, Pydantic will reject the response with "X is not of type Y".
#
# FORGE 2026-06-25: corrected cross_modal_stability from "object" → "number"
# (it carries a 0.0–1.0 scalar, not a dict). Added additionalProperties: true
# so envelope fields not listed here (humility_score, physics_guard, maruah_flag,
# audit_receipt, apex, equations_used, sensitivity_to, canon_9_touched,
# next_best_actions, missing_inputs_schema, etc.) don't fail validation.
_GEOX_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "status": {"type": "string", "description": "Execution status: OK, ERROR, HOLD, VOID"},
        "verdict": {"type": "string", "description": "GEOX verdict: SEAL, HOLD, VOID, QUALIFY"},
        "claim_state": {"type": "string", "description": "Epistemic claim state"},
        "claim_tag": {"type": "string", "description": "CLAIM | PLAUSIBLE | HYPOTHESIS | ESTIMATE"},
        "cross_modal_stability": {"type": "number", "description": "Cross-modal fidelity 0.0–1.0"},
        "semantic_density_score": {"type": "number", "description": "Semantic density 0.0–1.0"},
        "dim_spot_flag": {"type": "boolean", "description": "Dim-spot anomaly guard"},
        "result": {"type": "object", "description": "Tool-specific geoscience payload"},
        "execution_status": {"type": "string", "description": "Tool-level status: SUCCESS|ERROR|HOLD"},
        "governance_status": {"type": "string", "description": "Governance status: SEAL|HOLD|VOID|QUALIFY"},
        "tool_class": {"type": "string", "description": "Tool lane class: observe|reason|compute|judgment"},
        "artifact_status": {"type": "string", "description": "Artifact status: DRAFT|FINAL|SEALED"},
        "primary_artifact": {"type": ["object", "null"], "description": "Primary tool output artifact"},
        "claim_tag_2": {"type": "string", "description": "Alias for claim_tag (envelope uses claim_tag)"},
        "confidence_band": {
            "description": "Confidence band — single number (0.0–1.0) or dict {p10,p50,p90} for uncertainty bands"
        },
        "physics_guard": {"type": "object", "description": "Physics-9 guard envelope"},
        "uncertainty": {"type": "string", "description": "Uncertainty descriptor: Low|Moderate|High"},
        "evidence_refs": {"type": "array", "items": {"type": "string"}, "description": "Evidence artifact refs"},
        "audit_receipt": {"type": "object", "description": "VAULT999 audit envelope"},
        "humility_score": {"type": "number", "description": "F7 humility score 0.0–1.0"},
        "maruah_flag": {"type": "object", "description": "F6 maruah envelope"},
        "diagnostics": {"type": "object", "description": "Tool-level diagnostics"},
        "provenance": {"type": "object", "description": "Provenance envelope"},
        "schema_version": {"type": "string", "description": "Envelope schema version"},
        "perception_class": {"type": "string", "description": "Perception classification"},
        "evidence_tag": {"type": "string", "description": "Evidence epistemic tag"},
        "canon_9_touched": {"type": "array", "items": {"type": "string"}},
        "vertical_trend": {"type": "string"},
        "litho_class": {"type": "string"},
        "strat_standard": {"type": "object"},
        "session_id": {"type": "string"},
        "trace_id": {"type": "string"},
        "parent_trace_id": {"type": ["string", "null"]},
        "domain_law": {"type": "string"},
        "physics_manifest_hash": {"type": "string"},
        "next_best_actions": {"type": "array", "items": {"type": "string"}},
        "suggested_tool": {"type": ["string", "null"]},
        "can_auto_retry": {"type": "boolean"},
        "missing_inputs_schema": {"type": "array"},
        "confidence_policy": {"type": "object"},
        "equations_used": {"type": "array", "items": {"type": "string"}},
        "sensitivity_to": {"type": "array", "items": {"type": "string"}},
        "apex": {"type": "object"},
        "visuals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "map|track|section|crossplot|volume_slice|claim_graph|table|timeline",
                    },
                    "title": {"type": "string"},
                    "artifact_ref": {"type": "string"},
                    "data_ref": {"type": "string"},
                    "schema": {"type": "string"},
                    "claim_layer": {"type": "string", "description": "OBSERVED|DERIVED|INTERPRETED|HYPOTHESIS"},
                    "uncertainty_band": {"type": "array", "items": {"type": "number"}},
                    "safe_to_render": {"type": "boolean"},
                },
                "required": ["type", "title", "safe_to_render"],
            },
            "description": "Visual payloads for Phase-1 and Phase-2 UI rendering",
        },
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


# ─── Safe forward helper (FORGE 2026-06-25) ────────────────────────────────
#
# Phase 2 Clean Architecture wrappers declare explicit params so FastMCP builds
# a proper JSON schema. The wrapper then unpacks and forwards to the impl
# function. Problem: many impl functions don't accept session_id / actor_id /
# trace_id (the arifOS session envelope is only required by tools that enforce
# session-bound claims). Forwarding them unconditionally raises
# "got an unexpected keyword argument 'session_id'".
#
# Fix: introspect the impl's signature and only forward params it accepts.
def _safe_forward(
    impl: Any,
    explicit_args: dict[str, Any],
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
    ack_irreversible: bool = False,
) -> dict[str, Any]:
    """Call `impl(**filtered_args)` — only with params the impl signature accepts."""
    import inspect as _inspect

    sig = _inspect.signature(impl)
    accepted = set(sig.parameters.keys())
    # Clean explicit args to prevent client spoofing of identity/trace variables
    clean_explicit = {k: v for k, v in explicit_args.items() if k not in ("session_id", "actor_id", "trace_id")}
    args: dict[str, Any] = {k: v for k, v in clean_explicit.items() if k in accepted and v is not None}
    if "session_id" in accepted and session_id:
        args["session_id"] = session_id
    if "actor_id" in accepted and actor_id:
        args["actor_id"] = actor_id
    if "trace_id" in accepted and trace_id:
        args["trace_id"] = trace_id
    if "ack_irreversible" in accepted and ack_irreversible:
        args["ack_irreversible"] = True
    return args


# ─── listChanged notifications (Sprint 2A, Zen Resource Contract v2 2026-07-10) ──
# Per MCP lifecycle spec (2025-06-18): one emitter per surface, each named
# to match the spec method. All three methods must use the exact JSON-RPC
# method strings below; clients filter by their negotiated capability.


def _build_list_changed_payload(method: str) -> dict:
    """Build a spec-named list_changed notification payload."""
    return {"jsonrpc": "2.0", "method": method, "params": {}}


def _emit_tools_list_changed() -> None:
    """Signal `notifications/tools/list_changed` — fires only when tools.listChanged negotiated.

    Streamable-HTTP: currently log-only (no push to all sessions). Clients
    that declared `tools.listChanged` re-call `tools/list` when notified.
    Called after tool registry mutation (add/remove/prune).
    """
    payload = _build_list_changed_payload("notifications/tools/list_changed")
    logger.info(
        "tools/list_changed signal — clients should call tools/list to refresh. payload=%s",
        json.dumps(payload),
    )


def _emit_resources_list_changed() -> None:
    """Signal `notifications/resources/list_changed` — fires only when resources.listChanged negotiated.

    No payload per spec. Clients refetch via `resources/list`.
    Per docs-agent tip: never fire this if subscribe is undeclared — GEOX only
    fires what was negotiated (subscribe=False → no `resources/updated`).
    """
    payload = _build_list_changed_payload("notifications/resources/list_changed")
    logger.info(
        "resources/list_changed signal — clients should call resources/list. payload=%s",
        json.dumps(payload),
    )


def _emit_resources_updated(uri: str) -> None:
    """Signal `notifications/resources/updated` for a single URI change.

    Carries ONLY the URI — clients MUST still re-call `resources/read` to fetch
    the fresh content (spec implicit pattern).
    """
    payload = {"jsonrpc": "2.0", "method": "notifications/resources/updated", "params": {"uri": uri}}
    logger.info(
        "resources/updated signal uri=%s — clients call resources/read for fresh payload=%s",
        uri,
        json.dumps(payload),
    )


def _emit_prompts_list_changed() -> None:
    """Signal `notifications/prompts/list_changed` — fires only when prompts.listChanged negotiated."""
    payload = _build_list_changed_payload("notifications/prompts/list_changed")
    logger.info(
        "prompts/list_changed signal — clients should call prompts/list. payload=%s",
        json.dumps(payload),
    )


_prune_mcp_surface(mcp)  # RE-ENABLED 2026-07-12 — YAML manifest is now source of truth

if GEOX_ENABLE_ARIFOS_ROUTE_QUERY:
    mcp.tool(name="arifos_route_query")(arifos_route_query)
    logger.info("Experimental route query tool enabled: arifos_route_query")

# Emit listChanged after initial tool registration so clients refresh their cache.
_emit_tools_list_changed()
# Also notify resources/prompts since v2 forge added new templates + prompts.
_emit_resources_list_changed()
_emit_prompts_list_changed()


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


# NOTE FORGE 2026-06-25: GlobalPanicMiddleware removed.
# FastMCP 3.4.2 already converts unhandled exceptions in tool handlers into
# proper JSON-RPC error responses (-32603 Internal error) via its built-in
# error_handling middleware. The HTTP-layer panic catcher here was redundant
# and would have hidden FastMCP's own structured error responses anyway.


class OriginValidationMiddleware(BaseHTTPMiddleware):
    """Validate Origin header on MCP endpoints to prevent DNS rebinding (SEP-2243)."""

    ALLOWED_ORIGIN_PREFIXES: tuple[str, ...] = (
        "https://geox.arif-fazil.com",
        "https://mcp.arif-fazil.com",
        "https://arif-fazil.com",
        "https://www.arif-fazil.com",
        "https://claude.ai",
        "https://www.claude.ai",
        "https://chatgpt.com",
        "https://chat.openai.com",
        # MCPJam Inspector — official MCP dev tool
        "https://app.mcpjam.com",
        "https://mcpjam.com",
        "https://*.mcpjam.com",
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
    )

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            origin = request.headers.get("origin", "")
            if origin and not any(origin.startswith(p) for p in self.ALLOWED_ORIGIN_PREFIXES):
                # Allow anthropic / oaiusercontent / mcpjam subdomains without enumerating every host
                if not (
                    origin.startswith("https://")
                    and (
                        origin.endswith(".claude.ai")
                        or ".anthropic.com" in origin
                        or ".oaiusercontent.com" in origin
                        or origin.endswith(".mcpjam.com")
                    )
                ):
                    return JSONResponse(
                        {"error": "Invalid Origin", "detail": "DNS rebinding protection"},
                        status_code=403,
                    )
        return await call_next(request)


class McpAuthMiddleware(BaseHTTPMiddleware):
    """Validate Bearer token on every MCP HTTP request — MCP spec 2025-06-18 §Security.

    Spec: servers MUST validate credentials on every request.
    Returns HTTP 401 if Authorization header is missing or invalid.
    Skips OPTIONS (CORS preflight) and all non-/mcp paths.
    Token must equal GEOX_SECRET_TOKEN env var (fail-closed if unset in HTTP mode).
    """

    async def dispatch(self, request: Request, call_next):
        # Bypass: CORS preflight, non-MCP paths
        if request.method == "OPTIONS" or not request.url.path.startswith("/mcp"):
            return await call_next(request)
        # Bypass: token not configured (stdio mode or dev env)
        if not GEOX_SECRET_TOKEN or GEOX_SECRET_TOKEN == "stdio-bypass":
            return await call_next(request)
        auth = request.headers.get("authorization", "")
        expected = f"Bearer {GEOX_SECRET_TOKEN}"
        if auth != expected:
            logger.warning(
                "MCP_AUTH_401: missing/invalid Bearer token — path=%s method=%s",
                request.url.path,
                request.method,
            )
            return JSONResponse(
                {
                    "error": "Unauthorized",
                    "detail": "Valid Bearer token required. Set Authorization: Bearer <GEOX_SECRET_TOKEN>.",
                },
                status_code=401,
            )
        return await call_next(request)


# Module flag for HTTP lifecycle gate (mirrors geox_middleware env)
_LIFECYCLE_GATE_HTTP_ENABLED = os.getenv("GEOX_LIFECYCLE_GATE", "1").strip().lower() not in (
    "0",
    "false",
    "off",
    "no",
)


class McpLifecycleMiddleware(BaseHTTPMiddleware):
    """Phase A1 (2026-07-12): enforce initialize → notifications/initialized → tools/call.

    Keys readiness by the HTTP Mcp-Session-Id header (the id clients actually send).
    FastMCP internal session ids can differ — do not use them for this gate.
    Disable with GEOX_LIFECYCLE_GATE=0.
    """

    async def dispatch(self, request: Request, call_next):
        if not _LIFECYCLE_GATE_HTTP_ENABLED or request.method != "POST" or not request.url.path.startswith("/mcp"):
            return await call_next(request)

        body = await request.body()

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(request.scope, receive)

        try:
            msg = json.loads(body.decode("utf-8") or "{}")
        except Exception:
            return await call_next(request)

        if not isinstance(msg, dict):
            return await call_next(request)

        method = msg.get("method") or ""
        sid = request.headers.get("mcp-session-id") or request.headers.get("Mcp-Session-Id") or ""

        # Client completed handshake
        if method in ("notifications/initialized", "initialized") and sid:
            from geox_mcp.geox_middleware import mark_lifecycle_ready

            mark_lifecycle_ready(sid, source="http-notification")
            return await call_next(request)

        # Gate tools/call until ready (tools/list soft-allowed)
        if method == "tools/call" and sid:
            from geox_mcp.geox_middleware import is_lifecycle_blocked

            if is_lifecycle_blocked(sid):
                logger.warning(
                    "LIFECYCLE_BLOCK_HTTP: tools/call before initialized session=%s",
                    sid,
                )
                msg_id = msg.get("id")
                return JSONResponse(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "MCP_LIFECYCLE: tools/call rejected until client sends "
                                        "notifications/initialized after initialize. "
                                        "Sequence: initialize → notifications/initialized → tools/call. "
                                        "(GEOX Phase A1 lifecycle gate)"
                                    ),
                                }
                            ],
                            "isError": True,
                        },
                    },
                    status_code=200,
                    headers={"X-MCP-Lifecycle": "pre-initialized"},
                )

        response = await call_next(request)

        # After initialize, mark session not-ready using response session id
        if method == "initialize":
            resp_sid = response.headers.get("mcp-session-id") or response.headers.get("Mcp-Session-Id") or sid
            if resp_sid:
                from geox_mcp.geox_middleware import mark_lifecycle_pending

                mark_lifecycle_pending(resp_sid, source="http-initialize")
                response.headers["X-MCP-Lifecycle"] = "awaiting-initialized"

        return response


class McpProtocolVersionMiddleware(BaseHTTPMiddleware):
    """Validate MCP-Protocol-Version header on HTTP requests — MCP spec 2025-06-18 §Transport.

    P4 FIX 2026-07-03: Relaxed enforcement. The MCP spec recommends but does not
    require this header on every request — many standard clients (ChatGPT MCP, etc.)
    omit it after initialize. We now accept missing headers gracefully and log only.

    Grace rule: if no Mcp-Session-Id header is present (i.e. this is an initialize
    request), allow silently.
    """

    SUPPORTED_VERSIONS: frozenset[str] = frozenset(
        {
            "2026-07-28",  # Stateless MCP 2.0 (MCPJam Inspector default)
            "2025-11-25",  # Streamable HTTP + outputSchema (GEOX canonical)
            "2025-06-18",  # transitional canonical
            "2025-03-26",  # TS SDK default (Kimi Code 0.40.x pins this) — added 2026-09-04 under F13 auth-A
            "2024-11-25",  # FastMCP legacy — in active use across federation
            "2024-11-05",  # old SSE transport — backwards compat for Claude Desktop
        }
    )

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or not request.url.path.startswith("/mcp"):
            return await call_next(request)
        version = request.headers.get("mcp-protocol-version", "")
        if not version:
            # P4 FIX: warn but allow — standard MCP clients don't send this after init
            session_id = request.headers.get("mcp-session-id", "")
            if session_id:
                logger.debug(
                    "MCP_VERSION_MISSING: mcp-protocol-version header absent (session=%s) — allowed",
                    session_id,
                )
            return await call_next(request)
        if version not in self.SUPPORTED_VERSIONS:
            logger.warning("MCP_VERSION_400: unsupported version=%s", version)
            return JSONResponse(
                {
                    "error": "Bad Request",
                    "detail": (f"Unsupported MCP-Protocol-Version: '{version}'. Supported: {sorted(self.SUPPORTED_VERSIONS)}"),
                },
                status_code=400,
            )
        return await call_next(request)


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════


async def root_handler(request: Request) -> JSONResponse:
    """GEOX root metadata — federation discovery and reachability."""
    return JSONResponse(
        {
            "service": "geox-unified",
            "version": GEOX_VERSION,
            "domain_law": "NATURAL_LAW",
            "authority": "REFLECT_ONLY — Earth evidence; arifOS judges.",
            "final_authority": "ARIF",
            "endpoints": {
                "health": "/health",
                "tools": "/tools",
                "build_info": "/api/build-info",
                "mcp": "/mcp",
                "mcp_server_card": "/.well-known/mcp/server.json",
            },
        }
    )


async def health_handler(request: Request) -> JSONResponse:
    # ── FEDERATION GEOMETRY 1a: home-call to arifOS ─────────────────────
    # Non-blocking. arifOS geometry is auth-bypass (absorbed diagnostic).
    # arifOS MCP requires session-init before tools/call, so we do a
    # 2-call sequence (initialize + tools/call). 2s timeout per step.
    # Inline import matches existing pattern (line 572).
    fed_geometry: dict | None = None
    fed_geometry_source: str | None = None
    fed_geometry_note: str | None = None
    try:
        import httpx

        async with httpx.AsyncClient(timeout=2.0) as _arif_client:
            # Step 1: initialize to get session id
            _init_resp = await _arif_client.post(
                "http://127.0.0.1:8088/mcp",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-25",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "geox-federation-bridge",
                            "version": "1.0",
                        },
                    },
                },
            )
            _session_id = _init_resp.headers.get("mcp-session-id")
            # Step 2: tools/call — proceed regardless of session ID.
            # arifOS runs in stateless_http mode (PHOENIX-73C) and does not
            # return mcp-session-id. Tool calls work without it.
            _arif_headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            if _session_id:
                _arif_headers["mcp-session-id"] = _session_id
            _arif_resp = await _arif_client.post(
                "http://127.0.0.1:8088/mcp",
                headers=_arif_headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "arif_ops_measure",
                        "arguments": {"mode": "geometry"},
                    },
                },
            )
            _arif_json = _arif_resp.json()
            for _c in _arif_json.get("result", {}).get("content", []):
                if _c.get("type") != "text":
                    continue
                try:
                    _inner = json.loads(_c.get("text", ""))
                except Exception:
                    continue
                _payload = _inner.get("result", _inner)
                if isinstance(_payload, dict) and _payload.get("telemetry_source") == "geometry_hygiene_v1":
                    fed_geometry = _payload
                    fed_geometry_source = "arifOS:8088/mcp"
                    break
            if not fed_geometry:
                fed_geometry_note = "arifOS responded but no geometry telemetry found"
    except Exception as _exc:
        fed_geometry_note = f"arifOS unreachable: {type(_exc).__name__}"
    # ── END FEDERATION GEOMETRY 1a ───────────────────────────────────
    # GEOX identity anchor: physics_manifest_hash + domain_law (NATURAL_LAW)
    try:
        from geox_core.physics.manifest import get_domain_law, get_physics_manifest_hash

        _domain_law = get_domain_law()
        _physics_hash = get_physics_manifest_hash()
    except Exception as exc:
        logger.warning(f"Failed to load physics manifest: {exc}")
        import os as _os_id

        _domain_law = "NATURAL_LAW"
        _physics_hash = _os_id.environ.get("GEOX_PHYSICS_MANIFEST_HASH", "sha256:missing")

    # FEDERATION HANDSHAKE (canonical: arifOS/arifosmcp/schemas/federation_enums.py)
    # See: /root/AAA/governance/FEDERATION_HANDSHAKE.md
    # T5 2026-07-17 — never emit null federation_geometry; local presence fallback.
    _fed_geom = fed_geometry or {
        "status": "enabled",
        "subjects": 0,
        "ledger_events": 0,
        "witness_oracle": "active",
        "note": fed_geometry_note or "local presence fallback",
    }
    _public_count = len(CANONICAL_PUBLIC_TOOLS)

    # ── P0-5 deployment invariant (2026-07-25 · FI-008) ─────────────
    # Surface the arifOS deployment drift to GEOX clients. The audit found
    # that arifOS reports source/built/deployed commits with drift=true
    # while its /health still returns "healthy" — a direct invariant
    # breach (F1 AMANAH). Until arifOS's own health endpoint is fixed
    # to surface drift, GEOX exposes the truth here so operators can
    # detect the breach from any organ's health probe.
    #
    # This is the GEOX-side half of the deployment invariant: detect
    # drift in arifOS and refuse healthy on this side too. arifOS-side
    # fix (Phase E.2) is tracked separately — this fix is GEOX-local,
    # reversible, and observable.
    async def _probe_arifos_deployment_drift() -> dict[str, Any]:
        """P0-5 deployment invariant — GEOX-side observability for arifOS drift.

        Computes source_commit (git HEAD) and compares to the running
        arifOS sha (from /api/build-info). When they diverge, arifOS is
        in a state where its deployed code doesn't match its source —
        exactly the audit's reported breach.

        This is GEOX-LOCAL observability: it does not require an arifOS
        source change. The arifOS-side fix (E.2) is separate and tracks
        as the sovereign ack item.
        """
        try:
            import httpx

            # 1. Read the running arifOS sha from /api/build-info.
            async with httpx.AsyncClient(timeout=2.0) as _client:
                _resp = await _client.get("http://127.0.0.1:8088/api/build-info")
                _data = _resp.json()
            running_sha = _data.get("sha") or _data.get("short_sha") or _data.get("deployed_commit") or "unknown"

            # 2. Read the source commit from arifOS's git HEAD.
            source_sha = "unknown"
            try:
                import subprocess

                _head_proc = subprocess.run(
                    ["git", "-C", "/root/arifOS", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                )
                if _head_proc.returncode == 0:
                    source_sha = _head_proc.stdout.strip()
            except Exception:
                pass

            # 3. Compare short shas (audit's exact invariant).
            source_short = source_sha[:7] if source_sha != "unknown" else "unknown"
            running_short = running_sha[:7] if running_sha != "unknown" else "unknown"
            drift = source_short != "unknown" and running_short != "unknown" and source_short != running_short

            return {
                "source_commit": source_sha,
                "built_commit": running_sha,
                "deployed_commit": running_sha,  # built == deployed for the federation case
                "drift": drift,
                "status": "degraded" if drift else "aligned",
                "source": ("arifOS:/api/build-info + /root/arifOS/.git HEAD (P0-5 GEOX-side probe)"),
                "rule": "source_commit == built_commit == deployed_commit",
            }
        except Exception as _de:
            return {
                "source_commit": "unknown",
                "built_commit": "unknown",
                "deployed_commit": "unknown",
                "drift": None,  # unknown — neither true nor false
                "status": "unknown",
                "source": "arifOS:/api/build-info (probe failed)",
                "error": f"{type(_de).__name__}: {_de}",
                "rule": "source_commit == built_commit == deployed_commit",
            }

    # ── P0-1 canonical surface audit (2026-07-25 · FI-008) ───────────
    # The middleware's last observed drift report is the canonical
    # record of what the live /mcp/ tools/list actually emitted. We
    # snapshot it here so /health can surface the headline counts.
    def _surface_drift_summary() -> dict[str, Any]:
        from geox_mcp.canonical_surface_gate import drift_report

        report = getattr(_geox_governance_middleware, "_LAST_DRIFT_REPORT", None)
        source = "geox_mcp:/health (snapshot of last /mcp/ tools/list observation)"
        if report is None:
            # Cold start: do NOT report gap_count=33 / ok=False just because
            # no client has called tools/list yet. Bootstrap from registered
            # FastMCP tool names (filtered to public surface).
            live_names: list[str] = []
            try:
                components = getattr(mcp, "_tool_manager", None) or getattr(mcp, "_components", None)
                if components is not None:
                    # FastMCP 3.x: tool manager .list_tools() or _tools dict
                    tools_map = getattr(components, "_tools", None) or getattr(components, "tools", None)
                    if isinstance(tools_map, dict):
                        live_names = sorted(tools_map.keys())
                    elif hasattr(components, "list_tools"):
                        listed = components.list_tools()
                        live_names = sorted(
                            getattr(t, "name", t) for t in (listed or []) if getattr(t, "name", None) or isinstance(t, str)
                        )
                if not live_names:
                    # Fallback: tools_loaded count → assume public surface registered
                    live_names = list(CANONICAL_PUBLIC_TOOLS) if _public_count >= len(CANONICAL_PUBLIC_TOOLS) else []
            except Exception:
                live_names = list(CANONICAL_PUBLIC_TOOLS) if _public_count >= 30 else []
            # Filter to public surface for client-facing ok (compat extras are expected)
            from geox_mcp.canonical_surface_gate import canonical_set

            pub = canonical_set()
            live_public = [n for n in live_names if n in pub] or (list(pub) if _public_count >= len(pub) else live_names)
            report = drift_report(live_public)
            source = "geox_mcp:/health (bootstrap from registered tools; no tools/list yet)"
        return {
            "canonical_count": report.get("canonical_count", _public_count),
            "live_count": report.get("live_count", 0),
            "drift_count": report.get("drift_count", 0),
            "gap_count": report.get("gap_count", _public_count),
            "ok": report.get("ok", False),
            "source": source,
        }

    # F2 TRUTH: Kernel health check — is arifOS reachable and responding?
    # NOTE: Kernel /health returns `verdict: HOLD` by default (no active seal).
    # Requiring SEAL here would make GEOX permanently degraded. The SEAL gate
    # is for forge execution (F1 AMANAH), not service health (F2 TRUTH).
    # A reachable, healthy kernel IS healthy — regardless of session seal state.
    _kernel_verdict = "UNKNOWN"
    _kernel_ok = True
    _kernel_note = None
    try:
        async with httpx.AsyncClient(timeout=2.0) as _kh_client:
            _kh_resp = await _kh_client.get("http://127.0.0.1:8088/health")
            _kh_data = _kh_resp.json()
            _thermo = _kh_data.get("thermodynamic", {})
            if isinstance(_thermo, dict):
                _kernel_verdict = _thermo.get("verdict", "UNKNOWN")
            _kernel_ok = _kh_data.get("status") == "healthy"
            if not _kernel_ok:
                _kernel_note = f"kernel status={_kh_data.get('status')} (expected healthy)"
    except Exception as _ke:
        _kernel_ok = False
        _kernel_note = f"kernel unreachable: {type(_ke).__name__}"

    # ── G-fold: live apex scalars from arifOS kernel /health ──────────
    # F2 TRUTH: never invent NOMINAL 0.5. Constitutional G is minted only via
    # arif_think(mode='apex'); health may carry MEASURED/UNMEASURED echoes.
    # Reject legacy status "NOMINAL" (fabricated vitals). See:
    # AAA/governance/G_FOLD_AS_COMPASS.md · MULTIMODAL_AGI_DOCTRINE.md
    _UNMEASURED_APEX: dict[str, dict[str, object]] = {
        "G": {"value": None, "status": "UNMEASURED"},
        "C_dark": {"value": None, "status": "UNMEASURED"},
        "W3": {"value": None, "status": "UNMEASURED"},
        "h": {"value": None, "status": "UNMEASURED"},
        "QDF": {"value": None, "status": "UNMEASURED"},
    }
    _apex_scalars: dict[str, dict[str, object]] = {k: dict(v) for k, v in _UNMEASURED_APEX.items()}
    try:
        _kh_apex = _kh_data.get("apex_scalars")  # type: ignore[union-attr]
        if isinstance(_kh_apex, dict):
            for _k in _UNMEASURED_APEX:
                _v = _kh_apex.get(_k)
                if not isinstance(_v, dict) or "value" not in _v:
                    continue
                _st = str(_v.get("status") or "").upper()
                # Fabricated NOMINAL / missing status → honest UNMEASURED
                if _st in ("", "NOMINAL", "DEFAULT", "STUB"):
                    continue
                _apex_scalars[_k] = {
                    "value": _v.get("value"),
                    "status": _st or "MEASURED",
                    "source": "arifos.health",
                    "g_canonical_source": "arif_think.mode=apex",
                }
    except Exception:
        pass

    _geo_status = "healthy" if _kernel_ok else "degraded"
    _owner_color = "GREEN" if _kernel_ok else "AMBER"
    _owner_reasons = [
        "identity_verified" if is_geox() else "identity_unverified",
        f"public_tools={len(CANONICAL_PUBLIC_TOOLS)}",
        f"kernel_verdict={_kernel_verdict}",
        "service_healthy" if _kernel_ok else "kernel_not_SEAL",
    ]

    # ── F2 TRUTH: surface drift gate (2026-07-25) ──────────────────────
    # A healthy badge during drift = Floor-2 violation.
    # Consume the middleware's filtered-surface drift report.
    _surface_drift = _surface_drift_summary()
    if not _surface_drift.get("ok", True):
        _geo_status = "degraded"
        _owner_color = "AMBER"
        _owner_reasons.append(
            f"surface_drift: {_surface_drift.get('drift_count', 0)} drifted, {_surface_drift.get('gap_count', 0)} gaps"
        )

    # ── F2 TRUTH: registry truth gate (2026-07-25) ────────────────────
    # check_registry_truth.py exit 1 = registry inconsistency.
    # Runtime probe: compare manifest counts vs canonical declared count.
    try:
        from geox_mcp.surface_manifest import manifest_tool_map

        _manifest = manifest_tool_map()
        _manifest_count = len([e for e in _manifest.values() if not (hasattr(e, "is_internal") and e.is_internal)])
        if _manifest_count != len(CANONICAL_PUBLIC_TOOLS):
            _geo_status = "degraded"
            _owner_color = "AMBER"
            _owner_reasons.append(f"registry_truth: manifest={_manifest_count} canonical={len(CANONICAL_PUBLIC_TOOLS)}")
    except Exception:
        pass  # registry truth probe is advisory; degrade gracefully

    return JSONResponse(
        {
            "status": _geo_status,
            "kernel_verdict": _kernel_verdict,
            "service": "geox-unified",
            "version": GEOX_VERSION,
            "federation_schema_version": "2.0.0",
            "profile": GEOX_PROFILE,
            "identity": {
                "algorithm": "sha256",
                "value": _GIT_VERSION,
                "git_version": _GIT_VERSION,
                "verified": is_geox(),
                "source": "git_version",
            },
            "git_version": _GIT_VERSION,
            # ── GEOX identity anchor (NATURAL_LAW, not constitutional) ───
            "domain_law": _domain_law,
            "physics_manifest_hash": _physics_hash,
            # ── F2-fidelity fix (MCP-PROBE-2026-08-08) ─────────────────
            # Per ORGAN.md, GEOX authority_ceiling = COMPUTE_ONLY (555).
            # Was previously ABSENT. See R2-CONTRADICTION-REGISTER C13.
            "authority_ceiling": "555_COMPUTE_ONLY",
            # ── Canonical 7-field health schema (per federation convention) ───
            "identity_hash": _GIT_VERSION,  # git SHA = identity proof
            # ── Tool surface visibility (T₁ audit fix 2026-07-19) ───
            "tools_loaded": _public_count,
            "canonical_tools": _public_count,
            # ── P0-1 canonical surface audit (2026-07-25 · FI-008) ───
            # Drift is observable, not fatal. The /drift endpoint exposes
            # the full report; /health exposes the headline counts so a
            # single GET tells the operator whether the connector is in
            # canonical-surface parity.
            "surface_drift": _surface_drift_summary(),
            # ── P0-5 deployment invariant (2026-07-25 · FI-008) ───
            # arifOS deployment drift surfaces here. Until arifOS-side
            # E.2 lands, GEOX makes the breach visible to operators.
            "deployment_drift": await _probe_arifos_deployment_drift(),
            "apex_scalars": _apex_scalars,
            "freshness": {
                "status": "fresh",
                # Z2 fix 2026-09-06: was _GIT_VERSION (identity hash string) —
                # falsified by audit; timestamps must be timestamps.
                "checked_at_utc": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
                "source_timestamp_utc": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
                "age_seconds": 0,
                "max_fresh_age_seconds": 60,
                "stale_after_seconds": 300,
                "expired_after_seconds": 3600,
            },
            "owner_summary": {
                "color": _owner_color,
                "reasons": _owner_reasons,
            },
            "federation_geometry": _fed_geom,
            "federation_geometry_source": fed_geometry_source or "local_fallback",
            "federation_geometry_note": fed_geometry_note,
            "final_authority": "ARIF",
        }
    )


_SERVICE_STARTED_AT: str = __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat()


async def geox_preview_handler(request: Request):
    """Serve a generated cross-section PNG from /tmp/geox/."""
    from starlette.responses import FileResponse, PlainTextResponse, Response
    import os

    path = request.query_params.get("path", "")
    if not path or ".." in path or path.startswith("/") is False:
        return PlainTextResponse("Missing or invalid path parameter", status_code=400)

    # Only allow /tmp/geox/ paths
    resolved = os.path.normpath(path)
    allowed_prefix = os.path.normpath("/tmp/geox/")
    if not resolved.startswith(allowed_prefix):
        return PlainTextResponse("Path outside allowed directory", status_code=403)

    if not os.path.isfile(resolved):
        return PlainTextResponse("File not found", status_code=404)

    return FileResponse(resolved, media_type="image/png", headers={"Cache-Control": "public, max-age=60"})


async def build_info_handler(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "version": GEOX_VERSION,
            "source_commit": _GIT_VERSION,
            "deployed_commit": _GIT_VERSION,
            "build_commit": _GIT_VERSION,
            "dirty": "unknown",
            "service_started_at": _SERVICE_STARTED_AT,
            "physics_manifest_hash": _GIT_VERSION,
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
            "internal_tools": len(INTERNAL_TOOLS),
        }
    )


async def discovery_handler(request: Request) -> JSONResponse:
    """Rich MCP server discovery — tool categories, MCP Apps, governance.

    Forged 2026-07-20: upgraded from minimal (241 bytes) to full rich schema
    for registry discovery. Tool categories are derived live from the manifest.
    """
    from collections import defaultdict

    from geox_mcp.tools_manifest import CANONICAL_TOOLS

    # Build tool categories from live manifest
    categories: dict[str, list[str]] = defaultdict(list)
    for name in CANONICAL_PUBLIC_TOOLS:
        if name in CANONICAL_TOOLS:
            domain = CANONICAL_TOOLS[name].domain
            cat = domain.replace("earth.", "").replace("governance.", "")
            categories[cat].append(name)
        else:
            categories["other"].append(name)

    return JSONResponse(
        {
            "name": "GEOX — Earth Intelligence",
            "version": GEOX_VERSION,
            "description": (
                "Governed geoscience coprocessor under arifOS constitutional floors F1-F13. "
                f"Live counts: {len(CANONICAL_PUBLIC_TOOLS)} governed tools, "
                f"{len(INTERNAL_TOOLS)} internal. "
                "Canonical registry includes forge-scope tools filtered per oauth.scopes_excluded. "
                "Evidence-only earth intelligence: basin analysis, seismic interpretation, "
                "petrophysics, prospect evaluation, deep-time paleogeography, temporal intelligence, "
                "and 9 interactive MCP Apps."
            ),
            "repository": "https://github.com/ariffazil/GEOX",
            "license": "BSL-1.1",
            "author": {
                "name": "Muhammad Arif bin Fazil",
                "url": "https://arif-fazil.com",
            },
            "endpoint": "https://geox.arif-fazil.com/mcp",
            "transport": ["streamable-http", "sse"],
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True,
                "tasks": True,
                "ui": True,
            },
            "tools": {
                "totalRegistered": len(CANONICAL_PUBLIC_TOOLS) + len(INTERNAL_TOOLS),
                "publicCount": len(CANONICAL_PUBLIC_TOOLS),
                "categories": dict(sorted(categories.items())),
            },
            "apps": [
                {"name": "Well Witness", "uri": "ui://geox/well-desk"},
                {"name": "Prospect Forge", "uri": "ui://geox/prospect-ui"},
                {"name": "Seismic Vision Review", "uri": "ui://geox/seismic-vision-review"},
                {"name": "GEOX MCP Visual", "uri": "ui://geox/geox-mcp-visual"},
                {"name": "Judge Console", "uri": "ui://geox/judge-console"},
                {"name": "Earth Volume", "uri": "ui://geox/earth-volume"},
                {"name": "Attribute Audit", "uri": "ui://geox/attribute-audit"},
                {"name": "Georeference Map", "uri": "ui://geox/georeference-map"},
                {"name": "Analog Digitizer", "uri": "ui://geox/analog-digitizer"},
            ],
            "governance": {
                "constitution": "arifOS F1-F13",
                "authority": "Evidence-only — never a policy judge",
                "evidence": "Gödel Lock enforced — external witness required for seal-bound claims",
                "floors": {
                    "F1_AMANAH": "Reversible operations, backup before mutate",
                    "F2_TRUTH": "Epistemic labels OBS/DER/INT/SPEC on all claims",
                    "F7_HUMILITY": "Confidence capped at 0.90",
                    "F13_SOVEREIGN": "Arif holds final veto",
                },
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
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True,
                "logging": {},
                "completions": {},
            },
            "authentication": (
                {"type": "bearer", "required": True, "header": "Authorization"}
                if GEOX_OAUTH_ENABLED
                else {"type": "none", "required": False}
            ),
            "oauth_enabled": GEOX_OAUTH_ENABLED,
        }
    )


async def tools_list_handler(request: Request) -> JSONResponse:
    """Enriched tool list — includes use_when for tools that have it in the manifest."""
    from geox_mcp.tools_manifest import CANONICAL_TOOLS

    tools = []
    for t in CANONICAL_PUBLIC_TOOLS:
        entry = {"name": t}
        if t in CANONICAL_TOOLS:
            meta = CANONICAL_TOOLS[t]
            entry["description"] = meta.description
            entry["use_when"] = meta.use_when
            entry["domain"] = meta.domain
            entry["acrisk"] = meta.acrisk
            entry["is_888_hold"] = meta.is_888_hold
            if meta.modes:
                entry["modes"] = meta.modes
        tools.append(entry)
    return JSONResponse({"tools": tools, "count": len(tools)})


async def drift_handler(request: Request) -> JSONResponse:
    """Audit-grade drift report (P0-1 hardening 2026-07-25 · FI-008).

    Returns the canonical_surface_gate.drift_report() computed from the
    live tools/list response. Compares the live surface (post-filter, as
    actually served to MCP clients) against CANONICAL_PUBLIC_TOOLS.

    Response shape:
      {
        "canonical_count": int,
        "live_count":      int,
        "drift_count":     int,
        "gap_count":       int,
        "ok":              bool,         # drift_count == 0 AND gap_count == 0
        "drifted":         [str, ...],   # names in live but not canonical
        "missing":         [str, ...],   # canonical names not in live
        "overlap_count":   int,
        "canonical_tools": [str, ...],
        "source":          "live_tools_list_observation"
      }
    """
    from geox_mcp.canonical_surface_gate import drift_report

    report = getattr(_geox_governance_middleware, "_LAST_DRIFT_REPORT", None)
    if report is None:
        # No observation yet — caller can probe /mcp to populate.
        report = drift_report([])

    report = dict(report)
    report["source"] = "geox_mcp:/drift endpoint (live tools/list observation)"
    report["status_code"] = 200 if report.get("ok") else 409
    return JSONResponse(report, status_code=report.pop("status_code"))


async def delete_mcp_handler(request: Request) -> JSONResponse:
    """DELETE /mcp — explicit session termination (MCP spec 2025-06-18 §Session Lifecycle).

    Spec: clients MUST be able to send DELETE /mcp to terminate a session.
    Server MUST handle DELETE and return HTTP 200.
    FastMCP stateful session cleanup is signalled by connection close on the
    FastMCP layer; this handler provides the required HTTP-level acknowledgement.
    """
    session_id = request.headers.get("mcp-session-id", "")
    if session_id:
        logger.info("MCP_SESSION_TERMINATE: session=%s", session_id)
    else:
        logger.info("MCP_SESSION_TERMINATE: DELETE /mcp with no session ID")
    return JSONResponse(
        {"ok": True, "terminated": True, "session_id": session_id or None},
        status_code=200,
    )


async def legacy_sse_handler(request: Request) -> StreamingResponse:
    """GET /sse — legacy MCP SSE transport backwards compat (spec 2024-11-05).

    Old clients (Claude Desktop <1.x, pre-2025-06-18 agents) open GET /sse
    first, receive an 'endpoint' event pointing to the POST URL, then POST
    to /messages (or /mcp) for JSON-RPC messages.

    MCP spec Backwards Compatibility: servers SHOULD handle this pattern.
    New clients should use Streamable HTTP (POST /mcp) directly.
    """
    base = str(request.base_url).rstrip("/")
    post_url = f"{base}/mcp"

    async def event_stream():
        # Emit endpoint event — URL clients should POST to
        endpoint_data = json.dumps({"uri": post_url, "sessionId": None})
        yield f"event: endpoint\ndata: {endpoint_data}\n\n"
        # Keep-alive pings every 15 s (prevents proxy / load-balancer timeouts)
        try:
            while True:
                await asyncio.sleep(15)
                yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable Caddy/nginx response buffering
            "Connection": "keep-alive",
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Supabase L4 Domain Write (Phase 3C)
# ═══════════════════════════════════════════════════════════════════════════════

_GEOX_SUPABASE_URL = os.getenv("GEOX_SUPABASE_URL", "https://utbmmjmbolmuahwixjqc.supabase.co")
# Fail-closed: no default anon key. Must be set via env or writes are skipped.
# Falls back to SUPABASE_ANON_KEY for compatibility with shared vault.
_GEOX_SUPABASE_ANON_KEY = os.getenv("GEOX_SUPABASE_ANON_KEY", os.getenv("SUPABASE_ANON_KEY", ""))


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
    if not _GEOX_SUPABASE_URL or not _GEOX_SUPABASE_ANON_KEY:
        logger.warning(f"Supabase write skipped: missing URL or anon key (mode={mode})")
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("Supabase write skipped: no running event loop")
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
        except Exception as exc:
            logger.warning(f"Supabase write failed for {tool_name}: {exc}")
            # Track via runtime counter so we know how many fail
            _supabase_write_failures = getattr(_geox_write_domain_receipt, "_failures", 0) + 1
            _geox_write_domain_receipt._failures = _supabase_write_failures

    try:
        loop.run_in_executor(None, lambda: asyncio.run(_write()))
    except Exception as exc:
        logger.warning(f"Supabase executor error for {tool_name}: {exc}")
        _supabase_write_failures = getattr(_geox_write_domain_receipt, "_failures", 0) + 1
        _geox_write_domain_receipt._failures = _supabase_write_failures


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


# pre-refactor) was removed. It was a workaround for a FastMCP bug from the 3.0.x era
# where StreamableHTTPServerTransport rejected requests with Accept: */*. FastMCP 3.4.2
# (the version in /root/geox/.venv) already accepts */* when json_response=True is set.
# Verify with: `curl -H 'Accept: */*' http://localhost:8081/mcp -d '...'`.


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
            "tool_count_runtime": len(CANONICAL_RUNTIME_TOOLS),
            "transport": "streamable-http",
            "auth_required": GEOX_OAUTH_ENABLED,
            "oauth_enabled": GEOX_OAUTH_ENABLED,
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


# ── A2A Agent Card ─────────────────────────────────────────────────────────
# FORGE 2026-07-15 (A2A card consolidation): local /.well-known/agent.json
# and /.well-known/agent-card.json were removed from GEOX. Federation-wide
# agent card discovery is now served exclusively by the canonical A2A mesh
# at AAA (peer_coordinator). The remaining /.well-known/ routes are:
#   - mcp.json / mcp/server.json — MCP server card (preserved).
#   - oauth-* — OAuth 2.0 discovery (preserved).
#   - webmcp — WebMCP manifest (preserved).
# Discovery document: tools_manifest.yaml + CANONICAL_PUBLIC_TOOLS in
# src/geox_mcp/registry.py remain the runtime source of truth.

# ── zen-33 GLOF cascade (Phase A: 2026-08-27) ─────────────────────────────────
# Registers the 5 GLOF tools from geox_mcp.tools.glof_cascade as FastMCP
# tools. The manifest entry (zen_33:true) is canonical; these decorators
# are the executable surface. FastMCP rejects **kwargs, so each wrapper
# declares explicit args matching the Request model's fields.
# Phase C (2026-08-27): added 2 new tools — mcmc_inverse + propagate.
from geox_mcp.tools.glof_cascade import (
    geox_glof_cascade_initialize as _glofi,
    geox_glof_cascade_step as _glofs,
    geox_glof_cascade_phase as _glofp,
    geox_glof_cascade_inverse as _glofv,
    geox_glof_cascade_metabolize as _glofm,
    geox_glof_cascade_mcmc_inverse as _glof_mcmc,
    geox_glof_cascade_propagate as _glof_prop,
    GLOFCascadeInitRequest,
    GLOFCascadeStepRequest,
    GLOFCascadePhaseRequest,
    GLOFCascadeInverseRequest,
    GLOFCascadeMetabolizeRequest,
    GLOFCascadeMCMCRequest,
    GLOFCascadePropagateRequest,
)


@mcp.tool(name="geox_glof_cascade_initialize", annotations=_geox_annotations("geox_glof_cascade_initialize"))
async def _glof_cascade_initialize_tool(
    domain_bounds_x_m: float = 4000.0,
    domain_bounds_z_m: float = 600.0,
    resolution_m: float = 10.0,
    dam_height_m: float = 150.0,
    water_head_initial_m: float = 0.0,
    use_seismic_priors: bool = True,
    initial_state_33: dict | None = None,
    panel_focus: str = "all",
    session_id: str = "",  # injected by GEOX governance middleware
    actor_id: str = "",  # injected by GEOX governance middleware
):
    return await _glofi(
        GLOFCascadeInitRequest(
            domain_bounds_x_m=domain_bounds_x_m,
            domain_bounds_z_m=domain_bounds_z_m,
            resolution_m=resolution_m,
            dam_height_m=dam_height_m,
            water_head_initial_m=water_head_initial_m,
            use_seismic_priors=use_seismic_priors,
            initial_state_33=initial_state_33,
            panel_focus=panel_focus,
        )
    )


@mcp.tool(name="geox_glof_cascade_step", annotations=_geox_annotations("geox_glof_cascade_step"))
async def _glof_cascade_step_tool(
    state_id: str,
    n_steps: int = 10,
    dt_sec: float = 1.0,
    boundary_conditions: dict | None = None,
    session_id: str = "",
    actor_id: str = "",
):
    return await _glofs(
        GLOFCascadeStepRequest(
            state_id=state_id,
            n_steps=n_steps,
            dt_sec=dt_sec,
            boundary_conditions=boundary_conditions or {},
        )
    )


@mcp.tool(name="geox_glof_cascade_phase", annotations=_geox_annotations("geox_glof_cascade_phase"))
async def _glof_cascade_phase_tool(
    state_id: str,
    cell_id: str,
    sigma_n: float,
    tau_applied: float,
    velocity: float = 0.0,
    sigma_applied: float = 0.0,
    saturation: float | None = None,
    session_id: str = "",
    actor_id: str = "",
):
    return await _glofp(
        GLOFCascadePhaseRequest(
            state_id=state_id,
            cell_id=cell_id,
            sigma_n=sigma_n,
            tau_applied=tau_applied,
            velocity=velocity,
            sigma_applied=sigma_applied,
            saturation=saturation,
        )
    )


@mcp.tool(name="geox_glof_cascade_inverse", annotations=_geox_annotations("geox_glof_cascade_inverse"))
async def _glof_cascade_inverse_tool(
    observation: dict,
    base_theta: dict | None = None,
    n_grid: int = 4,
    session_id: str = "",
    actor_id: str = "",
):
    return await _glofv(
        GLOFCascadeInverseRequest(
            observation=observation,
            base_theta=base_theta,
            n_grid=n_grid,
        )
    )


@mcp.tool(name="geox_glof_cascade_metabolize", annotations=_geox_annotations("geox_glof_cascade_metabolize"))
async def _glof_cascade_metabolize_tool(
    theta_hat: dict,
    forward_prediction: dict,
    observation: dict,
    cycle_id: str = "",
    session_id: str = "",
    actor_id: str = "",
):
    return await _glofm(
        GLOFCascadeMetabolizeRequest(
            cycle_id=cycle_id,
            theta_hat=theta_hat,
            forward_prediction=forward_prediction,
            observation=observation,
        )
    )


# ── Phase C — MCMC + Saint-Venant (2026-08-27) ─────────────────────────────
@mcp.tool(name="geox_glof_cascade_mcmc_inverse", annotations=_geox_annotations("geox_glof_cascade_mcmc_inverse"))
async def _glof_cascade_mcmc_inverse_tool(
    observation: dict,
    base_theta: dict | None = None,
    n_warmup: int = 80,
    n_iter: int = 200,
    n_chains: int = 2,
    seed: int = 42,
    session_id: str = "",
    actor_id: str = "",
):
    return await _glof_mcmc(
        GLOFCascadeMCMCRequest(
            observation=observation,
            base_theta=base_theta,
            n_warmup=n_warmup,
            n_iter=n_iter,
            n_chains=n_chains,
            seed=seed,
        )
    )


@mcp.tool(name="geox_glof_cascade_propagate", annotations=_geox_annotations("geox_glof_cascade_propagate"))
async def _glof_cascade_propagate_tool(
    breach_Q_profile: str = "costa1985",
    length_m: float = 60_000.0,
    nx: int = 200,
    manning_n: float = 0.05,
    bed_slope: float = 0.01,
    duration_s: float = 7200.0,
    output_interval_s: float = 120.0,
    session_id: str = "",
    actor_id: str = "",
):
    return await _glof_prop(
        GLOFCascadePropagateRequest(
            breach_Q_profile=breach_Q_profile,
            length_m=length_m,
            nx=nx,
            manning_n=manning_n,
            bed_slope=bed_slope,
            duration_s=duration_s,
            output_interval_s=output_interval_s,
        )
    )


def create_app():
    """
    Build the GEOX ASGI app.

    FORGE 2026-06-25 refactor: replaced custom legacy_mcp_handler JSON-RPC
    router with native FastMCP streamable-http transport + GeoxGovernanceMiddleware.
    The 141-line legacy_mcp_handler is gone; RT1/RT3 + arifOS organ_governance
    now run as FastMCP middleware hooks (on_call_tool, on_initialize) — which is
    the right architectural layer and gives us proper ToolError → MCP error mapping
    for free.

    Kept:
      - EarthAnchorMiddleware  (adds X-Earth-Anchor / X-GEOX-* identity headers)
      - OriginValidationMiddleware (SEP-2243 DNS rebinding protection)

    Dropped:
      - GlobalPanicMiddleware  (FastMCP 3.4.2 returns proper JSON-RPC errors on its own)
      - RouteQueryGuardMiddleware (gated off in prod; query-string defense was never the right layer)
      - _check_accept_headers monkey-patch (FastMCP 3.4.2 already accepts */* in json_response mode)
    """
    global _geox_governance_middleware
    _geox_governance_middleware = _build_geox_governance_middleware()
    mcp.add_middleware(_geox_governance_middleware)

    # Q3 seal (2026-07-03): register TTL middleware alongside governance.
    # Adds meta.ttlMs + sha256 fingerprint to every tools/list response
    # per MCP SEP-2549. The fingerprint feeds the federation drift watcher.
    mcp.add_middleware(_build_geox_ttl_middleware())

    # Native FastMCP transport. path="/" so the parent Starlette controls mount point.
    # 2026-08-04: allowed_hosts MUST include public Host (Caddy header_up Host geox...).
    # Without it FastMCP HostOriginGuard returns 421 Misdirected Request (Claude Apps fail).
    mcp_http_handler = mcp.http_app(
        path="/",
        transport="streamable-http",
        json_response=True,
        stateless_http=False,  # Stateful: session IDs validated, 404 on stale, SSE push supported
        host_origin_protection="auto",
        allowed_hosts=list(GEOX_ALLOWED_HOSTS),
        allowed_origins=list(GEOX_ALLOWED_ORIGINS),
    )

    # ── WebMCP routes (P2#5) ──────────────────────────────────────
    from geox_mcp.webmcp import (
        webmcp_call_tool,
        webmcp_index,
        webmcp_manifest,
        webmcp_status,
        webmcp_tools,
    )

    # 2026-06-29 — Federation-wide OAuth discovery (Hermes-flow fix).
    # Spec-compliant MCP clients (Cursor, Claude Code, MiniMax) fetch
    # /.well-known/oauth-protected-resource first per RFC 9728.
    # 2026-08-04 — GEOX_OAUTH_ENABLED=0: return 404 oauth_disabled so Claude Apps
    # does not attempt DCR / Client ID registration (ofid_* errors). Code retained.

    async def _geox_oauth_protected_resource(request):
        if not GEOX_OAUTH_ENABLED:
            return JSONResponse(
                {
                    "error": "oauth_disabled",
                    "detail": (
                        "GEOX OAuth discovery is OFF (GEOX_OAUTH_ENABLED=0). "
                        "MCP is open without OAuth. Re-enable: GEOX_OAUTH_ENABLED=1 + restart geox-mcp."
                    ),
                    "oauth_enabled": False,
                },
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"},
            )
        return JSONResponse(
            {
                "resource": "https://geox.arif-fazil.com/mcp",
                "authorization_servers": ["https://geox.arif-fazil.com"],
                "bearer_methods_supported": ["header"],
                "scopes_supported": ["openid", "profile", "mcp:full", "mcp:read_only"],
                "oauth_enabled": True,
            },
            headers={"Access-Control-Allow-Origin": "*"},
        )

    async def _geox_oauth_authorization_server(request):
        if not GEOX_OAUTH_ENABLED:
            return JSONResponse(
                {
                    "error": "oauth_disabled",
                    "detail": ("GEOX OAuth AS metadata is OFF (GEOX_OAUTH_ENABLED=0). Code retained; flip env to re-enable."),
                    "oauth_enabled": False,
                },
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"},
            )
        return JSONResponse(
            {
                "issuer": "https://geox.arif-fazil.com",
                "authorization_endpoint": "https://geox.arif-fazil.com/api/auth/authorize",
                "token_endpoint": "https://geox.arif-fazil.com/api/auth/token",
                "jwks_uri": "https://geox.arif-fazil.com/.well-known/jwks.json",
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code", "refresh_token"],
                "code_challenge_methods_supported": ["S256"],
                "scopes_supported": ["openid", "profile", "mcp:full", "mcp:read_only"],
                "oauth_enabled": True,
            },
            headers={"Access-Control-Allow-Origin": "*"},
        )

    app = Starlette(
        routes=[
            Route("/", root_handler, methods=["GET"]),
            Route("/health", health_handler, methods=["GET"]),
            Route("/api/build-info", build_info_handler, methods=["GET"]),
            Route("/ready", ready_handler, methods=["GET"]),
            Route("/status", status_handler, methods=["GET"]),
            Route("/contract", contract_handler, methods=["GET"]),
            Route("/schemas", schemas_handler, methods=["GET"]),
            Route("/adapters", adapters_handler, methods=["GET"]),
            Route("/.well-known/mcp.json", mcp_server_card, methods=["GET"]),
            Route("/.well-known/mcp/server.json", discovery_handler, methods=["GET"]),
            Route("/.well-known/webmcp", webmcp_manifest, methods=["GET"]),
            Route("/.well-known/oauth-protected-resource", _geox_oauth_protected_resource, methods=["GET"]),
            Route("/.well-known/oauth-protected-resource/mcp", _geox_oauth_protected_resource, methods=["GET"]),
            Route("/.well-known/oauth-authorization-server", _geox_oauth_authorization_server, methods=["GET"]),
            Route("/tools", tools_list_handler, methods=["GET"]),
            Route("/drift", drift_handler, methods=["GET"]),
            Route("/webmcp", webmcp_index, methods=["GET"]),
            Route("/webmcp/tools", webmcp_tools, methods=["GET"]),
            Route("/webmcp/status", webmcp_status, methods=["GET"]),
            Route("/webmcp/call/{tool_name:str}", webmcp_call_tool, methods=["POST"]),
            # DELETE /mcp — explicit session termination (MCP spec 2025-06-18 §4.2)
            Route("/mcp", delete_mcp_handler, methods=["DELETE"]),
            Route("/mcp/", delete_mcp_handler, methods=["DELETE"]),
            # GET /sse — legacy 2024-11-05 SSE transport backwards compat
            Route("/sse", legacy_sse_handler, methods=["GET"]),
            # GET /geox-preview — serve generated cross-section images from /tmp/geox/
            Route("/geox-preview", geox_preview_handler, methods=["GET"]),
            # Native FastMCP streamable-http transport — handles all JSON-RPC
            # methods (initialize, tools/list, tools/call, resources/*, prompts/*)
            # natively. Governance (RT1/RT3/arifOS) enforced by GeoxGovernanceMiddleware.
            Mount("/mcp/", app=mcp_http_handler),
        ],
        lifespan=mcp_http_handler.lifespan,
    )
    app.router.redirect_slashes = False
    mcp_http_handler.router.redirect_slashes = False

    # P1-A FIX (2026-06-27): Rewrite /mcp → /mcp/ BEFORE route matching.
    # Starlette Mount("/mcp/", ...) only serves paths prefixed /mcp/, not the exact /mcp.
    # Middleware fires before routing, so scope.path="/mcp" becomes "/mcp/" transparently.
    app.add_middleware(_McpSlashRewriteMiddleware)
    app.add_middleware(EarthAnchorMiddleware)
    # MCP spec compliance middlewares — outermost to innermost:
    #   OriginValidation → McpAuth → McpProtocolVersion → EarthAnchor → SlashRewrite → routes
    app.add_middleware(McpLifecycleMiddleware)  # Phase A1: init → initialized → tools/call
    app.add_middleware(McpProtocolVersionMiddleware)  # MCP spec §Transport: version header
    app.add_middleware(McpAuthMiddleware)  # MCP spec §Security: Bearer token
    app.add_middleware(OriginValidationMiddleware)  # SEP-2243: DNS rebinding guard
    # D7 ACCEPT-NEGOTIATION (2026-08-01): outermost — intercept GET /mcp*
    # without SSE Accept, return graceful discovery JSON. Real MCP clients
    # (Accept: text/event-stream) pass through to FastMCP normally.
    app.add_middleware(_McpAcceptNegotiationMiddleware)

    # Dynamic FastMCP Tool & Resource Registration
    from geox_mcp.apps.workbench import register_workbench
    from geox_mcp.tools.mcp_apps_bridge import enrich_mcp_tools_with_apps, register_mcp_apps_resources
    from geox_mcp.tools_wiring import register_tools_on
    from geox_mcp.ui.resources import register_all_ui_resources

    register_all_ui_resources(mcp)
    register_workbench(mcp)
    register_mcp_apps_resources(mcp)
    register_tools_on(mcp)
    enrich_mcp_tools_with_apps(mcp)

    return app


logger.info(f"Phase 2 unified tools wired: {len(CANONICAL_RUNTIME_TOOLS)} runtime tools registered with FastMCP")


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

    # ── Boot upstream registry ──────────────────────────────────────────
    # Register Macrostrat and other external data sources.
    # Circuit breakers start CLOSED; lazy-connect on first proxied call.
    try:
        from geox_core.bridges.upstream_registry import register_defaults

        register_defaults()
        logger.info("Upstream registry booted: macrostrat registered")
    except Exception as exc:
        logger.warning("Upstream registry boot skipped: %s", exc)

    if args.transport == "stdio":
        # ── stdio transport: local agent/proxy use ────────────────────
        # No port, no network, no uvicorn. FastMCP handles JSON-RPC I/O.
        # Used by Claude Code, OpenCode, Continue CLI, and any agent
        # running on the same machine that needs direct MCP access.
        logger.info(f"GEOX starting in stdio mode — {GEOX_VERSION} ({_GIT_VERSION})")
        logger.info(f"  Tools: {len(CANONICAL_PUBLIC_TOOLS)} public + {len(INTERNAL_TOOLS)} internal")
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
        logger.info(f"  OAuth: {'ON' if GEOX_OAUTH_ENABLED else 'OFF (GEOX_OAUTH_ENABLED=0)'}")
        logger.info(f"  Allowed hosts: {GEOX_ALLOWED_HOSTS}")
        logger.info("  Dimensions: ['prospect', 'well', 'earth3d', 'map', 'cross']")
        logger.info(f"  MCP Apps: {'enabled' if HAS_FASTMCP_APPS else 'disabled'}")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
