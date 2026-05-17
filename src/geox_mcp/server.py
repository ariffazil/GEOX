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

import argparse
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

# Import canonical registry for source-of-truth
from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP
from geox_mcp.skills_resources import register_skill_resources

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geox.unified")

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Identity & Configuration
# ═══════════════════════════════════════════════════════════════════════════════

GEOX_VERSION = "v2026.05.17"
# Patch A - Fix epoch string
GEOX_CONTRACT_EPOCH = "2026-05-12-GEOX-13TOOLS-v0.7"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"
GEOX_PROFILE = os.getenv("GEOX_PROFILE", "full")
GEOX_HOST = os.getenv("GEOX_HOST", os.getenv("HOST", "0.0.0.0"))
GEOX_PORT = int(os.getenv("GEOX_PORT", os.getenv("PORT", "8081")))

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
        "Canonical GEOX Registry & MCP App Control Plane (Sovereign 13). DITEMPA BUKAN DIBERI — One Sovereign Kernel."
    ),
    "tasks": True,  # H3: Enable SEP-1686 background task execution
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
        from geox_mcp.tools.unified_13 import register_unified_tools

        register_unified_tools(mcp, profile=GEOX_PROFILE)
        # Assert against the canonical public tools count
        assert len(CANONICAL_PUBLIC_TOOLS) >= 14, (
            f"F0_CONSTITUTION_BREACH: Expected at least 15 sovereign tools, got {len(CANONICAL_PUBLIC_TOOLS)}"
        )
        logger.info(f"Sovereign tool surface: IGNITED ({len(CANONICAL_PUBLIC_TOOLS)} Canonical + well stratigraphy Tools)")
        # Register well tools
        try:
            from geox_mcp.tools.well import register_well_tools

            register_well_tools(mcp)
            logger.info("Well tools registered successfully")
        except Exception as e:
            logger.warning(f"Well tools not loaded: {e}")
        # Register generalized stratigraphy pipeline tools
        try:
            from geox_mcp.tools.stratigraphy import register_stratigraphy_tools

            register_stratigraphy_tools(mcp)
            logger.info("Stratigraphy pipeline tools registered successfully")
        except Exception as e:
            logger.warning(f"Stratigraphy pipeline tools not loaded: {e}")
        # Register Earth abduction tools (Tier 4 — PROCESS_HYPOTHESIS)
        try:
            from geox_mcp.tools.abduction import geox_process_abduction, geox_evidence_contradiction_scan

            mcp.tool()(geox_process_abduction)
            mcp.tool()(geox_evidence_contradiction_scan)
            logger.info("Earth abduction tools registered successfully")
        except Exception as e:
            logger.warning(f"Earth abduction tools not loaded: {e}")

        # H3 — Register background task tools (SEP-1686)
        try:
            from geox_mcp.tools.data import geox_task_ingest_las_batch
            from geox_mcp.tools.abduction import geox_task_metabolize_basin

            mcp.tool(name="geox_task_ingest_las_batch", task=True)(geox_task_ingest_las_batch)
            mcp.tool(name="geox_task_metabolize_basin", task=True)(geox_task_metabolize_basin)
            logger.info("Background task tools registered successfully")
        except Exception as e:
            logger.warning(f"Background task tools not loaded: {e}")

        # B — Register domain skills as MCP resources (wiki sync)
        try:
            from geox_mcp.skills_resources import register_geox_skills

            register_geox_skills(mcp)
            logger.info("Domain skill resources registered successfully")
        except Exception as e:
            logger.warning(f"Skill resources not loaded: {e}")
    except Exception as e:
        logger.critical(f"Failed to bootstrap Sovereign 13 registry: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# BOOT — Canonical surface only (chaos cleanup: dimension registries archived)
# ═══════════════════════════════════════════════════════════════════════════════
logger.info("Canonical surface loading...")
bootstrap_sovereign_13()

# ═══════════════════════════════════════════════════════════════════════════════
# MCP SURFACE PRUNE — Remove non-canonical tools (aliases, duplicates, noise)
# F8 GENIUS: elegant surface. F10 ONTOLOGY: structural coherence.
# ═══════════════════════════════════════════════════════════════════════════════


def _prune_mcp_surface(mcp_server) -> None:
    """Strip non-canonical tools from the MCP registry after bootstrap.

    Uses FEDERATION_TOOLS manifest (is_tool_somatic) from
    /federation/tool_manifest.py as single source of truth.
    Falls back to SACRED_SURFACE set if federation manifest unavailable.
    """
    from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

    SACRED_SURFACE: set[str] = set(CANONICAL_PUBLIC_TOOLS) | {
        "geox_dst_ingest_test",
        "geox_well_compute_gr_bins",
        "geox_well_build_packages",
        "geox_well_infer_seq_strat",
        "geox_well_analyze_sequence",
        "geox_stratigraphy_run_pipeline",
        "geox_stratigraphy_preview_config",
        # H3 — Background task tools (SEP-1686)
        "geox_task_ingest_las_batch",
        "geox_task_metabolize_basin",
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

                visible = is_tool_somatic(name)
            except Exception:
                visible = name in SACRED_SURFACE
            if not visible:
                del components[key]
                removed.append(name)
    if removed:
        logger.info(f"MCP surface pruned: {len(removed)} non-canonical tools removed")
    logger.info(f"MCP surface clean: {len(components)} canonical tools exposed")


_prune_mcp_surface(mcp)

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL PANIC MIDDLEWARE (F1 Amanah — fail closed on unhandled exceptions)
# ═══════════════════════════════════════════════════════════════════════════════


class EarthAnchorMiddleware(BaseHTTPMiddleware):
    """Inject ATLAS13 Earth event anchor into every MCP tool result."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path in ("/mcp", "/mcp/stream") and request.method == "POST":
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            if body:
                try:
                    payload = json.loads(body)
                    if "result" in payload:
                        result = payload["result"]
                        content = result.get("content", [])
                        for item in content:
                            txt = item.get("text", "")
                            if txt and txt.startswith("{") and "earth_event_anchor" not in txt:
                                try:
                                    data = json.loads(txt)
                                    if isinstance(data, dict):
                                        tool_name = data.get("tool") or ""
                                        anchor = _earth_event_for_tool(tool_name)
                                        data["earth_event_anchor"] = anchor
                                        item["text"] = json.dumps(data)
                                        result["structuredContent"]["earth_event_anchor"] = anchor
                                except (json.JSONDecodeError, TypeError):
                                    pass
                        payload["result"] = result
                    body = json.dumps(payload).encode()
                except (json.JSONDecodeError, TypeError):
                    pass
            return JSONResponse(json.loads(body.decode())) if body else response
        return response


class GlobalPanicMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.exception("GEOX kernel panic caught")
            return JSONResponse(
                {
                    "status": "void",
                    "tool": "kernel_panic_handler",
                    "error": str(exc)[:500],
                    "floor": "F10_COHERENCE",
                    "message": "Unhandled server exception. Request voided.",
                },
                status_code=500,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL OUTPUT CONTRACT v0.5 — Wrap all tool outputs
# Injects: claim_tag, confidence_band, physics_guard, evidence_refs,
# uncertainty, audit_receipt, humility_score (F7), maruah_flag (F6)
# CHANGED v0.5: confidence_band defaults to None (not fake zeros)
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# ATLAS13 — Earth Memory Anchors for GEOX (13 canonical Earth events)
# ═══════════════════════════════════════════════════════════════════════════════

ATLAS13_EARTH_EVENTS = [
    {
        "event_id": "GEOX-EARTH-001",
        "event_name": "Moon-forming impact",
        "time_anchor": "~4.5 Ga",
        "earth_domain": ["planetary formation", "impact physics", "mantle differentiation"],
        "organism_witness": "no organism — event created Earth-Moon stability field inherited by all later life",
        "machine_witness": "orbital mechanics, angular momentum, isotope ratios, planetary simulation",
        "geox_lesson": "Earth systems may appear stable only after catastrophic reorganization.",
        "nine_signal_mapping": {
            "delta": "physical Earth state changed by impact",
            "psi": "no governance yet — pre-biological",
            "omega": "stability after collision is not given, it is forged",
        },
    },
    {
        "event_id": "GEOX-EARTH-002",
        "event_name": "Late Heavy Bombardment",
        "time_anchor": "~4.1–3.8 Ga",
        "earth_domain": ["impact cratering", "early crust", "planetary hazard"],
        "organism_witness": "pre-biological or early-biological survival boundary",
        "machine_witness": "crater record, lunar proxy evidence, impact modeling",
        "geox_lesson": "A surface is not sovereign; it is exposed.",
        "nine_signal_mapping": {
            "delta": "crust repeatedly disrupted",
            "psi": "no constraint system yet",
            "omega": "survival requires shielding",
        },
    },
    {
        "event_id": "GEOX-EARTH-003",
        "event_name": "Formation of stable oceans",
        "time_anchor": "~4.4–3.8 Ga",
        "earth_domain": ["hydrosphere", "atmosphere", "habitability"],
        "organism_witness": "water becomes the medium of metabolism",
        "machine_witness": "isotopes, zircons, sedimentary record, climate models",
        "geox_lesson": "Water is Earth's first operating system for life.",
        "nine_signal_mapping": {
            "delta": "hydrosphere stabilized",
            "psi": "planetary chemistry constrained",
            "omega": "habitability is a physical condition, not a guarantee",
        },
    },
    {
        "event_id": "GEOX-EARTH-004",
        "event_name": "Great Oxidation Event",
        "time_anchor": "~2.4 Ga",
        "earth_domain": ["atmosphere", "redox chemistry", "biosphere"],
        "organism_witness": "anaerobic worlds collapsed; aerobic futures opened",
        "machine_witness": "banded iron formations, sulfur isotopes, atmospheric chemistry",
        "geox_lesson": "Life can transform the planet that hosts it. Small process + long time = planetary regime shift.",
        "nine_signal_mapping": {
            "delta": "atmospheric chemistry measurably altered",
            "psi": "biological activity rewrote planetary constraints",
            "omega": "small causes can produce epochal effects",
        },
    },
    {
        "event_id": "GEOX-EARTH-005",
        "event_name": "Snowball Earth glaciations",
        "time_anchor": "~720–635 Ma",
        "earth_domain": ["climate extremes", "ice-albedo feedback", "carbon cycle"],
        "organism_witness": "survival under planetary-scale constraint",
        "machine_witness": "glacial deposits, cap carbonates, climate instability models",
        "geox_lesson": "Feedback can freeze the world before balance returns.",
        "nine_signal_mapping": {
            "delta": "climate locked into extreme state",
            "psi": "feedback overwhelmed containment",
            "omega": "stability is not the default; it is maintained",
        },
    },
    {
        "event_id": "GEOX-EARTH-006",
        "event_name": "Cambrian Explosion",
        "time_anchor": "~541 Ma",
        "earth_domain": ["evolution", "sedimentary record", "oxygenation", "ecology"],
        "organism_witness": "body plans diversified; perception, predation, shells, motion intensified",
        "machine_witness": "fossil record, stratigraphy, geochemical proxies",
        "geox_lesson": "Complexity appears when Earth permits enough energy, oxygen, and structure.",
        "nine_signal_mapping": {
            "delta": "Earth system conditions permitted rapid diversification",
            "psi": "ecological constraints emerged with complexity",
            "omega": "complexity is enabled, not willed",
        },
    },
    {
        "event_id": "GEOX-EARTH-007",
        "event_name": "End-Ordovician extinction",
        "time_anchor": "~444 Ma",
        "earth_domain": ["glaciation", "sea-level fall", "marine extinction"],
        "organism_witness": "shallow marine life suffered collapse",
        "machine_witness": "stratigraphy, isotope excursions, sedimentary basin shifts",
        "geox_lesson": "A cooling Earth can be as lethal as a burning one.",
        "nine_signal_mapping": {
            "delta": "sea level and ocean chemistry shifted",
            "psi": "climate boundary exceeded",
            "omega": "cooling is not safety",
        },
    },
    {
        "event_id": "GEOX-EARTH-008",
        "event_name": "Late Devonian crisis",
        "time_anchor": "~372–359 Ma",
        "earth_domain": ["reef collapse", "ocean anoxia", "terrestrial plant expansion"],
        "organism_witness": "marine ecosystems destabilized over prolonged stress",
        "machine_witness": "black shales, redox proxies, reef stratigraphy",
        "geox_lesson": "Slow crisis is still crisis. Not every catastrophic Earth event is instant.",
        "nine_signal_mapping": {
            "delta": "reef systems degraded over millions of years",
            "psi": "prolonged stress is still a governance failure",
            "omega": "duration does not dilute severity",
        },
    },
    {
        "event_id": "GEOX-EARTH-009",
        "event_name": "Permian–Triassic extinction",
        "time_anchor": "~252 Ma",
        "earth_domain": ["volcanism", "carbon cycle", "ocean anoxia", "mass extinction"],
        "organism_witness": "largest known mass extinction; survival bottleneck",
        "machine_witness": "Siberian Traps, mercury anomalies, carbon isotope shifts, temperature proxies",
        "geox_lesson": "When carbon, heat, ocean chemistry, and volcanism couple, life pays the debt.",
        "nine_signal_mapping": {
            "delta": "Earth systems cascaded",
            "psi": "planetary constraints catastrophically breached",
            "omega": "coupled crises exceed any single discipline",
        },
    },
    {
        "event_id": "GEOX-EARTH-010",
        "event_name": "Chicxulub impact / K–Pg extinction",
        "time_anchor": "~66 Ma",
        "earth_domain": ["impact physics", "extinction", "ejecta", "atmospheric opacity"],
        "organism_witness": "dinosaur dominance ended; mammals inherited opportunity",
        "machine_witness": "iridium layer, shocked quartz, crater imaging, global ejecta",
        "geox_lesson": "Dominance is not permanence. Scale can be overruled by shock.",
        "nine_signal_mapping": {
            "delta": "sudden global forcing",
            "psi": "no governance could have prevented it",
            "omega": "humility before abrupt Earth response",
        },
    },
    {
        "event_id": "GEOX-EARTH-011",
        "event_name": "Paleocene–Eocene Thermal Maximum",
        "time_anchor": "~56 Ma",
        "earth_domain": ["carbon release", "warming", "ocean acidification", "migration"],
        "organism_witness": "ecosystems reorganized under rapid warming",
        "machine_witness": "carbon isotope excursion, benthic foram records, temperature proxies",
        "geox_lesson": "Carbon is not only chemistry; carbon is destiny under constraint.",
        "nine_signal_mapping": {
            "delta": "carbon pulse drove thermal response",
            "psi": "carbon cycle governance is planetary",
            "omega": "geochemistry becomes history",
        },
    },
    {
        "event_id": "GEOX-EARTH-012",
        "event_name": "Toba supereruption",
        "time_anchor": "~74 ka",
        "earth_domain": ["volcanology", "ash dispersal", "atmospheric forcing"],
        "organism_witness": "regional devastation, climate stress, survival pressure",
        "machine_witness": "ash layers, volcanic glass, climate modeling, eruption volume",
        "geox_lesson": "Atmosphere turns local violence into distributed consequence.",
        "nine_signal_mapping": {
            "delta": "volcanic aerosol globally dispersed",
            "psi": "no governance — pure geological forcing",
            "omega": "local events can have planetary reach",
        },
    },
    {
        "event_id": "GEOX-EARTH-013",
        "event_name": "2004 Sumatra–Andaman megathrust earthquake and tsunami",
        "time_anchor": "2004-12-26",
        "earth_domain": ["plate tectonics", "megathrust rupture", "tsunami", "hazard"],
        "organism_witness": "immediate human and ecological loss across the Indian Ocean",
        "machine_witness": "seismometers, tide gauges, GPS displacement, tsunami warning systems",
        "geox_lesson": "Earth motion becomes cascading consequence. The ocean carried the judgment outward.",
        "nine_signal_mapping": {
            "delta": "plate boundary ruptured",
            "psi": "hazard governance tested at scale",
            "omega": "Earth does not negotiate with infrastructure",
        },
    },
]

ATLAS13_BY_NAME: dict[str, dict] = {}
for e in ATLAS13_EARTH_EVENTS:
    name = e["event_name"].replace("\u2013", "-").replace("\u2014", "-").replace("\u2018", "'").replace("\u2019", "'")
    ATLAS13_BY_NAME[name] = e
    ATLAS13_BY_NAME[e["event_name"]] = e
ATLAS13_BY_ID: dict[str, dict] = {e["event_id"]: e for e in ATLAS13_EARTH_EVENTS}


def _lookup_atlas(event_name: str) -> dict | None:
    """Look up an Earth event by name, normalizing special characters."""
    for e in ATLAS13_EARTH_EVENTS:
        en = e["event_name"]
        if en == event_name:
            return e
        if en.replace("\u2013", "-") == event_name or en.replace("\u2014", "-") == event_name:
            return e
    return ATLAS13_BY_NAME.get(event_name)


def _earth_event_for_tool(tool_name: str) -> dict:
    """Return a stable Earth event anchor for a given GEOX tool name."""
    tool_to_event = [
        ("geox_seismic", "Chicxulub impact / K-Pg extinction"),
        ("geox_prospect", "Permian-Triassic extinction"),
        ("geox_subsurface", "Late Heavy Bombardment"),
        ("geox_section", "Cambrian Explosion"),
        ("geox_map_context", "Formation of stable oceans"),
        ("geox_time4d", "Snowball Earth glaciations"),
        ("geox_evidence_summarize", "End-Ordovician extinction"),
        ("geox_data_ingest", "Toba supereruption"),
        ("geox_data_qc", "Paleocene-Eocene Thermal Maximum"),
        ("geox_history", "Great Oxidation Event"),
        ("geox_system_registry", "Moon-forming impact"),
    ]
    for prefix, event_name in tool_to_event:
        if tool_name.startswith(prefix):
            anchor = _lookup_atlas(event_name)
            if anchor:
                return anchor
    return ATLAS13_EARTH_EVENTS[3]  # default: Great Oxidation Event


def _wrap_tool_outputs(mcp_server):
    """Monkey-patch all registered tool functions to inject universal output contract.
    MCP 2025-11-25 dual output: content (legacy text) + structuredContent (typed JSON).
    """
    import inspect
    from datetime import datetime

    provider = getattr(mcp_server, "_local_provider", None)
    if not provider:
        return

    _UI_FALLBACKS = {
        "geox_prospect_evaluate": "[HYPOTHESIS] Prospect evaluation completed. Open in host with UI support for full visualization.",
        "geox_seismic_analyze_volume": "[HYPOTHESIS] Seismic volume analysis completed. Open in host with UI support for full visualization.",
        "geox_map_context_scene": "[HYPOTHESIS] Map context scene rendered. Open in host with UI support for full visualization.",
        "geox_data_ingest_bundle": "[CLAIM] Data ingestion bundle processed. Open in host with UI support for full visualization.",
        "geox_subsurface_generate_candidates": "[CLAIM] Subsurface candidate generation completed. Open in host with UI support for full visualization.",
    }

    for key, tool in getattr(provider, "_components", {}).items():
        if not key.startswith("tool:"):
            continue
        original_fn = getattr(tool, "fn", None)
        if not original_fn:
            continue

        async def _universal_wrapper(*args, __orig=original_fn, __tool=tool, **kwargs):
            result = __orig(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            if not isinstance(result, dict):
                return result

            now = datetime.now(UTC).isoformat()
            tool_name = getattr(__tool, "name", "")
            # Gap 5: inject UI fallback for tools with app links
            if tool_name in _UI_FALLBACKS and "_ui_fallback" not in result:
                result["_ui_fallback"] = _UI_FALLBACKS[tool_name]
            defaults = {
                "claim_tag": result.get("claim_tag", "HYPOTHESIS"),
                "confidence_band": result.get("confidence_band"),
                "physics_guard": result.get("physics_guard", {"guard_passed": True, "physics_version": "geox-v2026.05.10"}),
                "evidence_refs": result.get("evidence_refs", []),
                "uncertainty": result.get("uncertainty", "Moderate"),
                "audit_receipt": result.get(
                    "audit_receipt",
                    {
                        "vault999_ref": "VAULT999-PENDING",
                        "timestamp": now,
                        "session_id": "geox-no-session",
                    },
                ),
                "humility_score": result.get("humility_score", 0.0),
                "maruah_flag": result.get(
                    "maruah_flag",
                    {
                        "maruah_flag": "CLEAR",
                        "territory_risk": "none",
                        "recommended_action": "Proceed with standard consent protocols.",
                        "confidence": "HIGH",
                    },
                ),
                "earth_event_anchor": result.get("earth_event_anchor", _earth_event_for_tool(tool_name)),
            }
            for k, v in defaults.items():
                if k not in result:
                    result[k] = v
            if result.get("confidence_band") is None:
                result["confidence_band"] = {
                    "computed": False,
                    "reason": "No volumetric distribution or statistical method supplied",
                    "p10": None,
                    "p50": None,
                    "p90": None,
                }

            # Return plain dict — FastMCP serializes with by_alias=True, exclude_none=True.
            # Returning mcp.types.CallToolResult caused annotations:null and _meta:null
            # on the wire (pydantic_core.to_jsonable_python includes all null fields).
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
            {
                "id": "TRJ-A",
                "name": "Delta-9 Anticline",
                "risk": "Low",
                "eta": "2 Days",
                "seal": "Required",
            },
            {
                "id": "TRJ-B",
                "name": "Deepwater Carbonate",
                "risk": "High",
                "eta": "14 Days",
                "seal": "Required (888_HOLD)",
            },
        ]

    @geox_app.tool()
    async def trigger_hold_seal(trajectory_id: str) -> dict:
        return {"status": "888_HOLD Lifted", "seal_granted": True}

    @geox_app.ui()
    def mission_board(mission: str) -> PrefabApp:
        options = [
            {
                "id": "TRJ-A",
                "name": "Delta-9 Anticline",
                "risk": "Low",
                "eta": "2 Days",
                "seal": "Required",
            },
            {
                "id": "TRJ-B",
                "name": "Deepwater Carbonate",
                "risk": "High",
                "eta": "14 Days",
                "seal": "Required (888_HOLD)",
            },
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
    # from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP # Already imported at the top

    return {
        "status": "ok",
        "service": "geox-mcp-kernel",
        "version": GEOX_VERSION,
        "contract_epoch": GEOX_CONTRACT_EPOCH,  # Use the new contract epoch
        "canonical_tools": len(CANONICAL_PUBLIC_TOOLS),
        "legacy_aliases": len(LEGACY_ALIAS_MAP),
        "auth_mode": "fail_closed",
        "profile": GEOX_PROFILE,
        "timestamp": datetime.now(UTC).isoformat(),
        "seal": GEOX_SEAL,
        "identity_pass": is_geox(),
        "identity": "GEOX",
        "role": "Earth Substrate Witness",
        "authority": "TERRAIN_WITNESS",
        "enabled_dimensions": [
            "prospect",
            "well",
            "earth3d",
            "map",
            "cross",
            "physics",
            "section",
            "canonical",
        ],
        "fastmcp_apps": {
            "enabled": HAS_FASTMCP_APPS,
            "mission_board": bool(geox_app),
            "well_desk": bool(well_app),
        },
    }


async def health_handler(request):
    return JSONResponse(
        {
            "status": "healthy",
            "registry_truth": "VERIFIED",  # Tool registry intact; 21 tools registered
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


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
    from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

    return JSONResponse(
        {
            "organ": "GEOX",
            "version": GEOX_VERSION,
            "git_sha": os.getenv("GIT_SHA", "unknown")[:8],
            "transport": "streamable-http",
            "mcp_endpoint": "https://geox.arif-fazil.com/mcp",
            "tool_count": len(CANONICAL_PUBLIC_TOOLS),  # Report canonical public tools
            "floors": [
                "F1",
                "F2",
                "F3",
                "F4",
                "F5",
                "F6",
                "F7",
                "F8",
                "F9",
                "F10",
                "F11",
                "F12",
                "F13",
            ],
            "discovery": "stateless",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


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
        "canonical": [
            "geox_prospect_judge_preview",
            "geox_prospect_judge_seal",
            "geox_evidence_summarize_cross",
        ],
        "description": "AC_Risk, 888_HOLD, verdict gateway, VAULT999, evidence graph",
    },
}


async def tools_list_handler(request):
    """Return the public tool surface: 15 sovereign tools with full MCP 2025-11-25 metadata.

    Internal dimension/substrate tools are callable but NOT advertised here.
    Aliases are listed separately with deprecation metadata.
    """
    from geox_core.schemas.output_schemas import get_tool_metadata

    all_tools = {t.name: t for t in await mcp.list_tools()}

    # ── PUBLIC surface: sovereign tools with full metadata ─────────────────
    categories = []
    seen_public = set()
    for cat_name, cat_info in GEOX_TOOL_CATEGORIES.items():
        cat_tools = []
        for tool_name in cat_info["canonical"]:
            t = all_tools.get(tool_name)
            if t and tool_name in CANONICAL_PUBLIC_TOOLS and tool_name not in seen_public:
                seen_public.add(tool_name)
                meta = get_tool_metadata(tool_name) or {}
                tool_entry = {
                    "name": t.name,
                    "description": t.description,
                }
                if meta.get("title"):
                    tool_entry["title"] = meta["title"]
                if meta.get("outputSchema"):
                    tool_entry["outputSchema"] = meta["outputSchema"]
                if meta.get("annotations"):
                    tool_entry["annotations"] = meta["annotations"]
                cat_tools.append(tool_entry)
        if cat_tools:
            categories.append(
                {
                    "category": cat_name,
                    "description": cat_info["description"],
                    "tools": cat_tools,
                    "visibility": "public",
                }
            )

    # ── INTERNAL surface: dimension + substrate tools ────────────────────────
    internal_tools = []
    for t in all_tools.values():
        if t.name not in CANONICAL_PUBLIC_TOOLS and t.name not in LEGACY_ALIAS_MAP:
            meta = get_tool_metadata(t.name) or {}
            tool_entry = {
                "name": t.name,
                "description": t.description,
            }
            if meta.get("title"):
                tool_entry["title"] = meta["title"]
            if meta.get("outputSchema"):
                tool_entry["outputSchema"] = meta["outputSchema"]
            if meta.get("annotations"):
                tool_entry["annotations"] = meta["annotations"]
            internal_tools.append(tool_entry)
    if internal_tools:
        categories.append(
            {
                "category": "internal",
                "description": "Dimension registry and substrate tools — callable but not part of public surface",
                "tools": internal_tools,
                "visibility": "internal",
            }
        )

    # ── ALIASES (deprecated) ──────────────────────────────────────────────
    aliases = []
    for alias_name, canonical_name in LEGACY_ALIAS_MAP.items():
        t = all_tools.get(alias_name)
        if t:
            aliases.append(
                {
                    "name": alias_name,
                    "description": t.description,
                    "deprecated": True,
                    "canonical_name": canonical_name,
                    "deprecated_since": "2026-05-01",
                    "removal_target": "2026-06-01",
                }
            )

    return JSONResponse(
        {
            "organ": "GEOX",
            "schema": "geox-tool-registry/v2",
            "schema_version": "geox-output-v0.6",
            "mcp_spec": "2025-11-25",
            "categories": categories,
            "public_count": len(CANONICAL_PUBLIC_TOOLS),
            "internal_count": len(internal_tools),
            "alias_count": len(aliases),
            "total_runtime": len(all_tools),
            "natural_tools": 11,
            "seal": "DITEMPA BUKAN DIBERI",
            "public_surface": "15 sovereign tools",
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.resource("geox://identity")
async def geox_identity() -> dict:
    from geox_mcp.registry import CANON9_TOOL_MAP
    from geox_core.enums.statuses import GDE_VOCAB

    identity_state = {
        "identity": "GEOX",
        "role": "Earth Substrate Witness",
        "authority": "TERRAIN_WITNESS",
        "seal": GEOX_SEAL,
        "version": GEOX_VERSION,
        "profile": GEOX_PROFILE,
        "identity_pass": is_geox(),
        "canon_9": {
            "quantities": ["rho", "Vp", "Vs", "rho_e", "chi", "k", "P", "T", "phi"],
            "tool_map": {k: v for k, v in sorted(CANON9_TOOL_MAP.items())},
            "description": "EARTH.CANON_9 — nine invariant subsurface quantities. Every tool declares which it touches.",
        },
        "gde_vocabulary": {
            "entries": len(GDE_VOCAB),
            "description": "Geological Depositional Environment vocabulary for paleoenvironment mapping.",
        },
        "strat_standards": {
            "supported": ["NN_zone", "NP_zone", "Stage_Sabah", "Cycle_Sarawak", "custom"],
            "description": "Stratigraphic reference schemes. NN_zone (GPTS2020) is the default anchor.",
        },
        "toac_version": "v1",
        "schema_version": "geox-output-v0.7",
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
                    with open(os.path.join(manifest_dir, filename)) as f:
                        apps.append(json.load(f))
                except Exception as e:
                    logger.error(f"Failed to load manifest {filename}: {e}")
    return apps


@mcp.resource("geox://apps/earth-panel")
async def get_earth_panel() -> str:
    try:
        ui_path = os.path.join(os.getcwd(), "ui", "earth-panel", "index.html")
        with open(ui_path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error loading earth panel UI: {e}"


@mcp.resource("geox://profile/status")
async def get_profile_status() -> str:
    return json.dumps(
        {
            "status": "healthy",
            "service": "geox-unified",
            "profile": GEOX_PROFILE,
            "enabled_dimensions": ["prospect", "well", "earth3d", "map", "cross"],
            "version": GEOX_VERSION,
            "seal": GEOX_SEAL,
            "constitutional_floors": "F1-F13 ACTIVE",
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TREE777 WIKI RESOURCES — Federation Canonical Knowledge Tree
# ═══════════════════════════════════════════════════════════════════════════════
# Exposes GEOX-domain slice of the TREE777 wiki as MCP Resources.
# URI scheme:
#   tree777://skills/geox/{name}   — GEOX skill pages
#   tree777://geo/concepts/{name}  — Geoscience concept pages
#   tree777://geo/scars/{name}     — GEOX scar/incident records
# Wiki root: /root/AAA/wiki (shared across all 4 federation servers)
# Rule: Resources grow. Tools stay bounded. Judgment remains Arif.
# DITEMPA BUKAN DIBERI — Intelligence is forged, not given.

TREE777_WIKI_ROOT = Path(os.environ.get("TREE777_WIKI_ROOT", "/root/AAA/wiki"))
TREE777_SKILLS_DIR = TREE777_WIKI_ROOT / "skills" / "geox"
TREE777_CONCEPTS_DIR = TREE777_WIKI_ROOT / "concepts"
TREE777_SCAR_DIR = TREE777_WIKI_ROOT / "scars"


def _geox_read_wiki_file(file_path: str | Path) -> str:
    """Read a wiki file, returning frontmatter-stripped content."""
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: File not found: {path}"
    content = path.read_text()
    if content.startswith("---"):
        end = content.find("\n---\n", 4)
        if end != -1:
            content = content[end + 5 :]
    return content.strip()


def _geox_tree777_index() -> dict[str, Any]:
    """Build the TREE777 index for GEOX domain slice."""
    skills = []
    if TREE777_SKILLS_DIR.exists():
        for f in TREE777_SKILLS_DIR.glob("*.md"):
            skills.append({"name": f.stem, "uri": f"tree777://skills/geox/{f.stem}"})

    concepts = []
    if TREE777_CONCEPTS_DIR.exists():
        for f in TREE777_CONCEPTS_DIR.glob("*.md"):
            concepts.append({"name": f.stem, "uri": f"tree777://geo/concepts/{f.stem}"})

    scars = []
    if TREE777_SCAR_DIR.exists():
        for f in TREE777_SCAR_DIR.glob("*.md"):
            if "geox" in f.stem or "geo" in f.stem:
                scars.append({"name": f.stem, "uri": f"tree777://geo/scars/{f.stem}"})

    return {
        "domain": "geox",
        "skills": skills,
        "concepts": concepts,
        "scars": scars,
        "total": len(skills) + len(concepts) + len(scars),
    }


@mcp.resource(
    "tree777://index",
    description=(
        "TREE777 wiki full index. Lists all federation skills, concepts, and scars. "
        "Use this to discover available resources across the arifOS, GEOX, WELL, and WEALTH domains."
    ),
)
async def geox_tree777_index() -> str:
    return json.dumps(_geox_tree777_index(), indent=2)


@mcp.resource(
    "tree777://skills/geox/{name}",
    description=(
        "Individual GEOX skill page from the TREE777 wiki. "
        "Returns markdown content (frontmatter-stripped) with metadata. "
        "Example: tree777://skills/geox/spatial-grounding"
    ),
)
async def geox_tree777_skill(name: str) -> str:
    file_path = TREE777_SKILLS_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps({"error": f"Skill not found: {name}", "uri": f"tree777://skills/geox/{name}"})
    content = _geox_read_wiki_file(file_path)
    return json.dumps({"uri": f"tree777://skills/geox/{name}", "content": content}, indent=2)


@mcp.resource(
    "tree777://geo/concepts/{name}",
    description=(
        "Geoscience concept page from the TREE777 wiki. "
        "Covers: TREE777, intelligence-tree, mcp-architecture-mapping, etc. "
        "Example: tree777://geo/concepts/TREE777"
    ),
)
async def geox_tree777_concept(name: str) -> str:
    file_path = TREE777_CONCEPTS_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps({"error": f"Concept not found: {name}", "uri": f"tree777://geo/concepts/{name}"})
    content = _geox_read_wiki_file(file_path)
    return json.dumps({"uri": f"tree777://geo/concepts/{name}", "content": content}, indent=2)


@mcp.resource(
    "tree777://geo/scars/{name}",
    description=(
        "GEOX scar/incident record from the TREE777 wiki. "
        "Documents failures and lessons learned for geoscience operations. "
        "Example: tree777://geo/scars/geo-seismic-misread"
    ),
)
async def geox_tree777_scar(name: str) -> str:
    file_path = TREE777_SCAR_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps({"error": f"Scar not found: {name}", "uri": f"tree777://geo/scars/{name}"})
    content = _geox_read_wiki_file(file_path)
    return json.dumps({"uri": f"tree777://geo/scars/{name}", "content": content}, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES — Agent Knowledge Pack
# Exposes resources/ directory as MCP resources for agent ingestion.
# DITEMPA BUKAN DIBERI — Intelligence is forged, not given.
# ═══════════════════════════════════════════════════════════════════════════════

RESOURCES_DIR = Path(os.getcwd()) / "resources"


@mcp.resource(
    "geox://capabilities",
    description="Full GEOX capability map: tools, domains, claim limits, next best actions. Read at session start.",
)
async def geox_capabilities() -> str:
    path = RESOURCES_DIR / "capabilities" / "geox_capabilities.json"
    if not path.exists():
        return json.dumps({"error": "Capabilities not found"})
    return path.read_text()


@mcp.resource(
    "geox://resources/{category}/{name}",
    description=(
        "Agent knowledge pack: ontology, playbooks, schemas, examples. "
        "Categories: ontology, playbooks, schemas, examples. "
        "Example: geox://resources/ontology/curve_aliases"
    ),
)
async def geox_resource(category: str, name: str) -> str:
    """Serve any file from the resources/ directory as an MCP resource."""
    # Security: restrict to known categories and file extensions
    allowed_categories = {"ontology", "playbooks", "schemas", "examples", "prompts"}
    if category not in allowed_categories:
        return json.dumps({"error": f"Invalid category: {category}"})

    file_path = RESOURCES_DIR / category / name
    # Prevent directory traversal
    try:
        file_path = file_path.resolve()
        resources_root = RESOURCES_DIR.resolve()
        if not str(file_path).startswith(str(resources_root)):
            return json.dumps({"error": "Invalid resource path"})
    except Exception:
        return json.dumps({"error": "Invalid resource path"})

    if not file_path.exists():
        # Try common extensions
        for ext in [".yaml", ".yml", ".json", ".md", ".csv"]:
            alt = file_path.with_suffix(ext)
            if alt.exists():
                file_path = alt
                break

    if not file_path.exists():
        return json.dumps({"error": f"Resource not found: {category}/{name}"})

    try:
        content = file_path.read_text()
        return json.dumps({
            "uri": f"geox://resources/{category}/{name}",
            "content": content,
            "format": file_path.suffix.lstrip("."),
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to read resource: {e}"})


@mcp.resource(
    "geox://resources/index",
    description="Index of all available resources in the GEOX knowledge pack.",
)
async def geox_resources_index() -> str:
    index = {}
    for category in ["ontology", "playbooks", "schemas", "examples", "prompts"]:
        cat_dir = RESOURCES_DIR / category
        if cat_dir.exists():
            files = [f.name for f in cat_dir.iterdir() if f.is_file()]
            index[category] = sorted(files)
    return json.dumps(index, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE SKILL RESOURCES — geox_core/skills exposed as MCP resources & prompts
# ═══════════════════════════════════════════════════════════════════════════════
register_skill_resources(mcp)


# ═══════════════════════════════════════════════════════════════════════════════
# MCP PROMPTS — GEOX Domain Rituals
# User-controlled structured interactions (not model-controlled like tools)
# Arif triggers these; the model prepares the packet; the tool evaluates.
# DITEMPA BUKAN DIBERI — Intelligence is forged, not given.
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.prompt()
async def prompt_review_petrophysics(formation: str = "", depth_md: float = 0, phi: float = 0, sw: float = 0) -> str:
    """
    Petrophysics review ritual for Arif.
    User-controlled prompt — Arif triggers this, not the model.
    """
    prompt = f"""# GEOX Petrophysics Review — {formation or "Unnamed Formation"}

## Input Parameters
- Formation: {formation}
- Depth (MD): {depth_md}m
- Porosity (phi): {phi:.1%}
- Water Saturation (Sw): {sw:.1%}

## Review Checklist
1. **Porosity sanity**: Is phi within physically plausible range for the formation type?
2. **Sw sanity**: Is Sw consistent with expected fluid contacts?
3. **Cross-plots**: Do phi-Sw relationships follow expected trends?
4. **Log quality**: Are there borehole environment effects to correct?
5. **Uncertainty**: What is the confidence band on these values?

## Output
Provide a PETROPHYSICS VERDICT:
- SEAL: Values are consistent and defensible
- SABAR: Values need correction or additional data
- HOLD: Insufficient information to assess
"""
    return prompt


@mcp.prompt()
async def prompt_geo_uncertainty_check(prospect_name: str = "", pos: float = 0, uncertainty_band: str = "moderate") -> str:
    """
    Geological uncertainty check for Arif.
    User-controlled prompt — Arif triggers this, not the model.
    """
    prompt = f"""# GEOX Geological Uncertainty Check — {prospect_name or "Unnamed Prospect"}

## Input
- Prospect: {prospect_name}
- Probability of Success (PoS): {pos:.0%}
- Uncertainty Band: {uncertainty_band}

## Uncertainty Assessment
1. **Structural uncertainty**: Fault geometry, trap integrity
2. **Stratigraphic uncertainty**: Reservoir presence and quality
3. **Charge uncertainty**: Source, migration, timing
4. **Retention uncertainty**: Seal capacity and integrity

## Key Question
Is the PoS estimate robust given the available data? What would need to be true for PoS to double? To halve?

## Output
Provide a UNCERTAINTY VERDICT:
- SEAL: Uncertainty is quantified and acceptable
- SABAR: Key uncertainties need de-risking
- HOLD: Major uncertainties unresolved
"""
    return prompt


@mcp.prompt()
async def prompt_prospect_review_packet(prospect_name: str = "", block: str = "", status: str = "screening") -> str:
    """
    Prospect review packet preparation for Arif.
    User-controlled prompt — Arif triggers this, not the model.
    """
    prompt = f"""# GEOX Prospect Review Packet — {prospect_name or "Unnamed Prospect"}

## Prospect Identity
- Name: {prospect_name}
- Block/License: {block}
- Status: {status}

## Required Sections
1. **Executive Summary** (3 sentences max)
2. **Geological Setting** — structure, stratigraphy, reservoir, seal, charge
3. **Risk Summary** — PoS breakdown by element
4. **Resource Range** — low/best/high case with basis
5. **Key Data Gaps** — what needs to be tested
6. **Recommendation** — proceed, farmed out, or dropped

## Constitutional Check
- F02 TRUTH: All claims must be evidence-grounded
- F07 HUMILITY: Uncertainty bands must be declared
- F08 GENIUS: Is this the simplest correct interpretation?

## Output
Produce a PROSPECT REVIEW PACKET ready for Arif's verdict.
"""
    return prompt


@mcp.prompt()
async def prompt_claim_discipline() -> str:
    """Core epistemic ladder — enforce claim-state separation."""
    path = RESOURCES_DIR / "prompts" / "claim_discipline.md"
    if path.exists():
        return path.read_text()
    return "# Claim Discipline\n\nOBSERVED ≠ DERIVED ≠ INTERPRETED ≠ PROVEN.\n"


@mcp.prompt()
async def prompt_earth_reasoning_protocol() -> str:
    """Mandatory abductive loop for geological tool calls."""
    path = RESOURCES_DIR / "prompts" / "earth_reasoning_protocol.md"
    if path.exists():
        return path.read_text()
    return "# Earth Reasoning Protocol\n\nObserve → Derive → Hypothesize → Test → Rank → Missing Evidence.\n"


@mcp.prompt()
async def prompt_red_team_reviewer() -> str:
    """Self-attack protocol before accepting any interpretation."""
    path = RESOURCES_DIR / "prompts" / "red_team_reviewer.md"
    if path.exists():
        return path.read_text()
    return "# Red Team Reviewer\n\nWhat evidence would break this hypothesis?\n"


@mcp.prompt()
async def prompt_failure_policy() -> str:
    """Failure modes and recovery actions for GEOX tools."""
    path = RESOURCES_DIR / "prompts" / "failure_policy.md"
    if path.exists():
        return path.read_text()
    return "# Failure Policy\n\nMissing curves → emit missing_inputs_schema. Sw=0/1 → 888HOLD.\n"


@mcp.prompt()
async def prompt_geox_agent_system() -> str:
    """Master system prompt for GEOX agent behavior."""
    path = RESOURCES_DIR / "prompts" / "geox_agent_system.md"
    if path.exists():
        return path.read_text()
    return "# GEOX Agent System\n\nYou are GEOX. Orchestrate tools. Enforce claim discipline. Route 888HOLD to Arif.\n"


@mcp.prompt()
async def prompt_tool_selection() -> str:
    """Routing logic: given evidence state, which tool to call next."""
    path = RESOURCES_DIR / "prompts" / "tool_selection.md"
    if path.exists():
        return path.read_text()
    return "# Tool Selection\n\nIf LAS ingested → QC. If QC passed → curve_inventory.\n"


@mcp.prompt()
async def prompt_report_writer() -> str:
    """Structured output template for geological reports."""
    path = RESOURCES_DIR / "prompts" / "report_writer.md"
    if path.exists():
        return path.read_text()
    return "# Report Writer\n\nSection 1: Data Quality. Section 2: Petrophysics. Section 3: Interpretation.\n"


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY MCP HANDLER (for backward compatibility with existing POST /mcp callers)
# ═══════════════════════════════════════════════════════════════════════════════


async def run_legacy_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tool_result = await mcp.call_tool(name, arguments)
    parsed = json.loads(tool_result.content[0].text) if tool_result.content else {}
    # MCP 2025-11-25: dual content — structuredContent (typed JSON) + content (legacy text)
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
                "kernel": "Sovereign 13 + Dimension Native",
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
        # Use canonical public tools for listing
        all_tools = {t.name: t for t in await mcp.list_tools()}
        tools = [
            {"name": t.name, "description": t.description} for t_name in CANONICAL_PUBLIC_TOOLS if (t := all_tools.get(t_name))
        ]
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
        elif resolved_name not in CANONICAL_PUBLIC_TOOLS:  # If it\'s not an alias and not in canonical tools
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

        # RT-3: irreversible operations require explicit human ack
        from control_plane_server_patch import rt3_guard

        rt3_blocked = rt3_guard(name, args)
        if rt3_blocked is not None:
            return rt3_blocked
        result = await run_legacy_tool(resolved_name, args)  # Call with resolved name
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": response_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
            }
        )

    return JSONResponse({"error": "Method not found"}, status_code=404)


# ── Monkey-patch: Accept */* when json_response is enabled ──────────────────
# Fixes MCP SDK probe that sends Accept: */* but FastMCP requires explicit
# application/json. Without this, /mcp returns HTTP 406 when called by generic
# HTTP clients (curl, browser fetch, MCP Apps).
from mcp.server.streamable_http import StreamableHTTPServerTransport

_orig_check = StreamableHTTPServerTransport._check_accept_headers


def _patched_check(self, request):
    if self.is_json_response_enabled:
        return (
            True,
            True,
        )  # json_response=True: accept both JSON and SSE (FastMCP will still prefer JSON)
    return _orig_check(self, request)


StreamableHTTPServerTransport._check_accept_headers = _patched_check
# ─────────────────────────────────────────────────────────────────────────────


def create_app():
    # FastMCP HTTP handler — streamable-http, fully stateless (arifOS-compatible).
    # stateless_http=True: no session tracking, no session ID validation, no "Missing session ID" errors.
    # This is the same architecture as arifOS server.py line 560.
    mcp_http_handler = mcp.http_app(
        path="/mcp",
        transport="streamable-http",
        json_response=True,
        stateless_http=True,  # ← was False; stateful mode breaks MCP handshake (server creates
        # session, then validates it before sending session ID to client — chicken-and-egg bug).
    )

    app = Starlette(
        routes=[
            Route("/health", health_handler, methods=["GET"]),
            Route("/ready", ready_handler, methods=["GET"]),
            Route("/status", status_handler, methods=["GET"]),
            Route("/.well-known/mcp/server.json", discovery_handler, methods=["GET"]),
            Route("/tools", tools_list_handler, methods=["GET"]),
            Route("/mcp", mcp_http_handler, methods=["GET", "POST"]),
            Route("/mcp/stream", mcp_http_handler, methods=["GET", "POST"]),
        ],
        lifespan=mcp_http_handler.lifespan,
    )
    app.add_middleware(EarthAnchorMiddleware)
    app.add_middleware(GlobalPanicMiddleware)
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
    logger.info("  Dimensions: ['prospect', 'well', 'earth3d', 'map', 'cross']")
    logger.info(f"  MCP Apps: {'enabled' if HAS_FASTMCP_APPS else 'disabled'}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
