"""
organ_governance.py — GEOX arifOS Governance Integration
========================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

GEOX-specific governance module that:
   1. Defines risk tier for all GEOX tools
   2. Calls arifOS kernel for C2+/IRREVERSIBLE tools
   3. Returns (verdict, error_response_or_None) tuple

Used by geox_mcp/server.py after RT-3 guard check.

arifOS kernel endpoint: http://arifosmcp:8088/mcp

FAIL-CLOSED: If arifOS kernel is unreachable or session is unbound,
defaults to HOLD. No guessing, no bypass.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from enum import StrEnum
from typing import Any

import httpx
from starlette.responses import JSONResponse

from geox_mcp.session_enforcement import validate_session

logger = logging.getLogger("geox.governance")


class RiskTier(StrEnum):
    READONLY = "readonly"
    C1_ADVISORY = "c1"
    C2_EXECUTE = "c2"
    IRREVERSIBLE = "irreversible"


# ─── GEOX Tool Risk Map ────────────────────────────────────────────────────────
# All entries must match canonical tool names from CANONICAL_PUBLIC_TOOLS
# in src/geox_mcp/registry.py (Phase 2 Clean Architecture — 16 tools).
#
# Old compat tool names (geox_data_ingest_bundle, geox_claim_seal, etc.)
# are NOT listed here — they are accepted by the middleware for backward
# compat but the risk map only governs canonical tools.

GEOX_RISK_MAP: dict[str, RiskTier] = {
    # ── WELL DOMAIN (4) ──
    "geox_well_ingest": RiskTier.READONLY,
    "geox_well_qc": RiskTier.READONLY,
    "geox_well_desk_open": RiskTier.READONLY,
    "geox_petrophysics": RiskTier.READONLY,
    "geox_sequence": RiskTier.READONLY,
    # ── SEISMIC DOMAIN ──
    "geox_seismic_ingest": RiskTier.READONLY,
    "geox_seismic_compute": RiskTier.READONLY,
    "geox_seismic_interpret": RiskTier.READONLY,
    "geox_vision": RiskTier.READONLY,
    "geox_tie_receipt": RiskTier.READONLY,
    "geox_tie_preflight": RiskTier.READONLY,
    "geox_benchmark_001": RiskTier.C1_ADVISORY,  # GEOX-001 truth test — advisory verdict only
    "geox_well_time_depth_calibrate": RiskTier.READONLY,
    "geox_well_seismic_mistie_rms": RiskTier.READONLY,
    "geox_wavelet_extract_least_squares": RiskTier.READONLY,
    # ── MODEL DOMAIN (2) ──
    "geox_subsurface_model": RiskTier.C1_ADVISORY,  # joint inversion → advisory
    "geox_geomechanics": RiskTier.READONLY,
    # ── BASIN DOMAIN (2) ──
    "geox_basin": RiskTier.READONLY,
    "geox_deep_time_state": RiskTier.READONLY,
    # ── GOVERNANCE DOMAIN (2) ──
    "geox_claim": RiskTier.C2_EXECUTE,  # mode="seal" → requires arifOS SEAL
    "geox_evidence": RiskTier.READONLY,
    # ── EVALUATION DOMAIN (1) ──
    "geox_prospect": RiskTier.C1_ADVISORY,  # mode="seal" → C2
    # ── DOCTRINE DOMAIN (1) ──
    "geox_doctrine": RiskTier.READONLY,
    # ── VISUAL/DESK DOMAIN ──
    "geox_well_desk_publish": RiskTier.C2_EXECUTE,
    "geox_render_well_panel": RiskTier.READONLY,
    # ── ZEN-15 CANONICAL (2026-07-13) ──
    "geox_gravmag_studio": RiskTier.READONLY,
    "geox_well_desk": RiskTier.READONLY,  # mode="publish" → C2 (inherits from well_desk_publish)
    "geox_contrast_detect": RiskTier.READONLY,
    "geox_basin_backstrip": RiskTier.READONLY,
    "geox_sediment_mass_balance": RiskTier.READONLY,
    "geox_thermal_maturity_history": RiskTier.READONLY,
    "geox_map_context_scene": RiskTier.READONLY,
    "geox_biostrat_parse": RiskTier.READONLY,
    "geox_biostrat_falsify": RiskTier.READONLY,
    "geox_falsify": RiskTier.READONLY,
    "geox_consequence_footprint": RiskTier.READONLY,
    "geox_optionality_loss": RiskTier.READONLY,
    "geox_feedback_integrity": RiskTier.READONLY,
    "geox_material_truth_challenge": RiskTier.READONLY,
    "geox_cascade_pathway": RiskTier.READONLY,
    "geox_gravmag_studio_open": RiskTier.READONLY,
    "geox_gravmag_studio_screen": RiskTier.READONLY,
    # ── PHASE 2 PROMOTIONS (2026-07-19) ──
    "geox_map_export_package": RiskTier.READONLY,
    "geox_seismic_cognition": RiskTier.READONLY,
    "geox_visual_understand": RiskTier.READONLY,
    "geox_visual_generate_hypotheses": RiskTier.READONLY,
    "geox_simulate_accommodation": RiskTier.READONLY,
    "geox_simulate_sequences": RiskTier.READONLY,
}


# ─── arifOS Kernel Client ──────────────────────────────────────────────────────

ARIFOS_KERNEL_URL = os.getenv("ARIFOS_KERNEL_URL", "http://127.0.0.1:8088")
_ARIFOS_KERNEL_TOKEN = os.getenv("ARIFOS_KERNEL_TOKEN", "")


# Cached MCP session for kernel calls (initialize → initialized → tools/call)
_kernel_mcp_session_id: str | None = None


async def _call_arif_kernel(tool_name: str, params: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    """Call arifOS MCP kernel asynchronously. FAIL-CLOSED on error — returns error dict.

    D5: complete MCP lifecycle (initialize → notifications/initialized → tools/call)
    so streamable-HTTP kernel gates do not reject bare tools/call.
    """
    global _kernel_mcp_session_id

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": params},
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if _ARIFOS_KERNEL_TOKEN:
        headers["Authorization"] = f"Bearer {_ARIFOS_KERNEL_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Ensure MCP session + lifecycle
            if not _kernel_mcp_session_id:
                init = await client.post(
                    f"{ARIFOS_KERNEL_URL}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": 0,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-03-26",
                            "capabilities": {},
                            "clientInfo": {"name": "geox-organ-governance", "version": "1.0"},
                        },
                    },
                    headers=headers,
                )
                sid = init.headers.get("mcp-session-id") or init.headers.get("Mcp-Session-Id")
                if sid:
                    _kernel_mcp_session_id = sid.strip()
                    headers["Mcp-Session-Id"] = _kernel_mcp_session_id
                    await client.post(
                        f"{ARIFOS_KERNEL_URL}/mcp",
                        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                        headers=headers,
                    )
            else:
                headers["Mcp-Session-Id"] = _kernel_mcp_session_id

            resp = await client.post(f"{ARIFOS_KERNEL_URL}/mcp", json=payload, headers=headers)
            # Session expiry → one retry with fresh lifecycle
            if resp.status_code in (400, 404) and "session" in resp.text.lower():
                _kernel_mcp_session_id = None
                return await _call_arif_kernel(tool_name, params, timeout=timeout)

            resp.raise_for_status()
            # SSE or JSON
            ctype = resp.headers.get("content-type", "")
            if "text/event-stream" in ctype:
                result = None
                for line in resp.text.splitlines():
                    if line.startswith("data:"):
                        result = json.loads(line[5:].strip())
                        break
                if result is None:
                    return {"status": "ERROR", "error": "empty SSE from kernel"}
            else:
                result = resp.json()
            rpc_result = result.get("result", {"status": "ERROR", "error": "no result in response"})
            if isinstance(rpc_result, dict) and "content" in rpc_result and isinstance(rpc_result["content"], list):
                for item in rpc_result["content"]:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "").strip()
                        if text.startswith("KERNEL_DENY") or text.startswith("ERROR") or text.startswith("HOLD"):
                            return {"status": "ERROR", "error": text}
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, dict):
                                return parsed
                        except Exception:
                            pass
                        return {"status": "OK", "text": text}
            return rpc_result
    except Exception as exc:
        logger.error(f"arifOS kernel call failed: {exc}")
        return {"status": "ERROR", "error": str(exc)}


# ─── Governance Check ─────────────────────────────────────────────────────────


# ─── FOUR-LANE TOOL CLASSIFICATION (Federation Contract §3) ────────────────────
# Loaded from GEOX.yaml federation contract; fallback to inline heuristics.
# Lane determines authority gating: discovery(no session) → evidence(no session)
# → reasoning(session required) → judgment(session+lease+arifOS judge required)


def _load_lane_map() -> dict[str, str]:
    """Load tool→lane mapping from registry manifest (single source of truth).

    Priority: registry.py GEOX_TOOL_MANIFEST > compat lane map > hardcoded fallback.
    The old GEOX.yaml federation contract is NOT loaded — it had stale
    40-tool entries that caused the split-brain. Registry manifest is the
    only authoritative lane source.
    """
    # Priority 1: registry manifest (authoritative) + backward-compat tools
    try:
        from geox_mcp.registry import GEOX_TOOL_MANIFEST

        lane_map = {t["name"]: t.get("lane", "reasoning") for t in GEOX_TOOL_MANIFEST}
        # Priority 2: backward-compat tools (CANONICAL_COMPAT_TOOLS) — all 49 missing
        # from GEOX_TOOL_MANIFEST, defaulting to "reasoning" which incorrectly
        # required sessions. Fixed by assigning correct lanes per tool function.
        # discovery = read-only, no session required
        # evidence = data/state ops, no session required
        # reasoning = compute, session recommended
        # judgment = arifOS-gated, session+lease required
        lane_map.update(
            {
                # ── DISCOVERY (read-only, no session) ──────────────────────────
                "geox_las_inspect": "discovery",  # LAS metadata read
                "geox_seismic_inspect": "discovery",  # seismic metadata read
                "geox_seismic_segy_inspect": "discovery",  # SEG-Y header read
                "geox_header_inspect": "discovery",  # generic header read
                "geox_tops_inspect": "discovery",  # formation tops read
                "geox_deviation_survey_inspect": "discovery",  # deviation survey read
                "geox_basin_profile": "discovery",  # basin profiling
                "geox_basin_resolve": "discovery",  # basin resolution
                "geox_query_intake": "discovery",  # intake query
                "geox_query_macrostrat": "discovery",  # Macrostrat lookup
                "geox_macrostrat_calibrate": "discovery",  # Phase 2.8: biostrat→Ma bridge — read-only API+lookup, no session needed
                "geox_coord_transform_tool": "discovery",  # pure math, no state
                "geox_blockspace_resolution_tool": "discovery",  # pure math, no state
                "geox_attribute_registry_list_tool": "discovery",  # registry read
                "geox_evidence_discover": "discovery",  # evidence search
                "geox_surface_status": "discovery",  # P0 fix #120 — health probe, no session needed
                # ── CONTRAST DETECTION (pure computation, no session) ───────────
                "geox_contrast_detect": "discovery",  # universal contrast detector — read-only computation
                # ── BIOSTRAT (read-only parse/lookup, no session) ───────────────
                "geox_biostrat_parse": "discovery",  # text parsing — pure regex
                "geox_biostrat_nn_age": "discovery",  # NN zone age lookup — table read
                "geox_biostrat_ruling_check": "discovery",  # contradiction check — read-only
                "geox_biostrat_falsify": "discovery",  # 8-gate falsification — read-only
                "geox_falsify": "discovery",  # Popperian falsification engine — read-only compute, no session
                # ── MAP TOOLS (read-only render/plan, no session) ───────────────
                "geox_map_layers_list": "discovery",  # layer registry read
                "geox_map_scene_plan": "discovery",  # scene planning — pure computation
                "geox_map_render_preview": "discovery",  # preview render — read-only
                "geox_map_export_package": "discovery",  # Phase 2 promotion — governed map export, read-only
                # ── SEISMIC TIE / COGNITION TOOLS (Phase 2 promotion) ────────────
                "geox_tie_preflight": "discovery",  # well tie preflight — read-only compute
                "geox_tie_receipt": "discovery",  # well tie receipt — read-only
                "geox_wavelet_extract_least_squares": "discovery",  # wavelet extraction — pure math
                "geox_seismic_cognition": "discovery",  # seismic cognition — read-only compute
                # ── VISION TOOLS (Phase 2 promotion) ─────────────────────────────
                "geox_visual_understand": "discovery",  # visual understanding — read-only
                "geox_visual_generate_hypotheses": "discovery",  # hypothesis generation — read-only
                # ── STRATIGRAPHIC SIMULATION (Phase 2 promotion) ─────────────────
                "geox_simulate_accommodation": "discovery",  # accommodation simulation — pure compute
                "geox_simulate_sequences": "discovery",  # sequence simulation — pure compute
                # ═══ STRIKE 3 FIX (2026-06-30): 3 missing aliases ═══════════════
                "geox_dst_ingest_test": "evidence",  # DST test data ingest
                "geox_sequence_interpret": "reasoning",  # sequence interpretation (compute-bound, session OK)
                "geox_evidence_reason": "evidence",  # evidence reasoning (data op, no session)
                # ── EVIDENCE (data ops, no session required) ────────────────────
                "geox_data_ingest_bundle": "evidence",  # data ingestion
                "geox_data_qc_bundle": "evidence",  # QC operations
                "geox_claim_create": "evidence",  # claim creation (alias: egs_claim_create)
                "geox_claim_challenge": "evidence",  # claim challenge (alias: egs_claim_challenge)
                "geox_evidence_attach": "evidence",  # attach evidence (alias: egs_evidence_attach)
                "geox_literature_ingest": "evidence",  # literature ingestion
                "geox_biostrat_constraint": "evidence",  # biostrat data
                "geox_icgem_models": "evidence",  # ICGEM model ingestion
                "geox_emag2_ingest": "evidence",  # EMAG2 data ingest
                "geox_mt_forward": "evidence",  # MT forward model ingest
                "geox_gravity_magnetic_forward": "evidence",  # gravity/mag ingest
                "geox_fault_stick_ingest_tool": "evidence",  # fault data ingest
                "geox_map_context_scene": "evidence",  # scene/map data
                "geox_blend_volume_tool": "evidence",  # volume blending (data mutation)
                "geox_horizon_contrast_surface": "evidence",  # surface creation
                "geox_subsurface_generate_candidates": "evidence",  # candidate generation
                "geox_subsurface_verify_integrity": "evidence",  # integrity check
                # ── REASONING (compute, session recommended) ───────────────────
                "geox_joint_inversion": "reasoning",  # joint inversion compute
                "geox_prithvi_eo_inference": "reasoning",  # foundation model inference
                "geox_lem_predict": "reasoning",  # LEM prediction
                "geox_seismic_inversion": "reasoning",  # seismic inversion
                "geox_seismic_compute_attribute_tool": "reasoning",  # seismic attribute compute
                "geox_vision_minimax_inference": "reasoning",  # minimax vision inference
                "geox_vision_calibrate": "reasoning",  # vision calibration
                "geox_vision_audit": "reasoning",  # vision audit
                "geox_vision_perceptual_inventory": "reasoning",  # perceptual inventory
                # ── JUDGMENT (arifOS-gated, session+lease required) ───────────
                "geox_claim_seal": "judgment",  # irreversible seal (alias: geox_claim mode=seal)
                "geox_prospect_evaluate": "judgment",  # prospect eval (alias: geox_prospect)
                "geox_claim_validate": "judgment",  # claim validation
                "geox_doctrine_anti_beautiful_one": "judgment",  # doctrine check
                "geox_doctrine_assumption_register": "judgment",  # assumption register
                "geox_doctrine_godel_review": "judgment",  # Gödel review
                "geox_abstraction_guard": "judgment",  # abstraction safety guard
                "geox_segy_export_tool": "judgment",  # irreversible SEG-Y export
                "geox_volume_frame_tool": "judgment",  # irreversible volume write
                "geox_well_desk_publish": "judgment",  # C2_EXECUTE — image publish + vault seal
            }
        )
        return lane_map
    except Exception:
        pass

    # Priority 3: hardcoded fallback for canonical tools (Phase 2)
    return {
        # WELL DOMAIN
        "geox_well_ingest": "evidence",
        "geox_well_qc": "evidence",
        "geox_petrophysics": "reasoning",
        "geox_sequence": "reasoning",
        # SEISMIC DOMAIN
        "geox_seismic_ingest": "evidence",
        "geox_seismic_compute": "evidence",  # FIX: was "reasoning" — compute-only, no session state needed
        "geox_seismic_interpret": "reasoning",
        "geox_vision": "reasoning",
        # MODEL DOMAIN
        "geox_subsurface_model": "judgment",
        "geox_geomechanics": "reasoning",
        # BASIN DOMAIN
        "geox_basin": "discovery",
        "geox_deep_time_state": "discovery",
        # GOVERNANCE DOMAIN
        "geox_claim": "judgment",
        "geox_evidence": "evidence",
        # EVALUATION DOMAIN
        "geox_prospect": "judgment",
        # DOCTRINE DOMAIN
        "geox_doctrine": "judgment",
        # ── DISCOVERY (backward-compat, no session) ─────────────────────
        "geox_las_inspect": "discovery",
        "geox_coord_transform_tool": "discovery",
        "geox_blockspace_resolution_tool": "discovery",
        "geox_attribute_registry_list_tool": "discovery",
        # ── EVIDENCE (backward-compat, no session) ────────────────────
        "geox_data_ingest_bundle": "evidence",
        "geox_data_qc_bundle": "evidence",
        "geox_claim_create": "evidence",
        "geox_evidence_attach": "evidence",
        # ── JUDGMENT (backward-compat, arifOS-gated) ─────────────────
        "geox_claim_seal": "judgment",
        "geox_prospect_evaluate": "judgment",
        "geox_segy_export_tool": "judgment",
        "geox_volume_frame_tool": "judgment",
    }


GEOX_LANE_MAP: dict[str, str] = _load_lane_map()

# Lane authority requirements
# ─── 2026-07-25: GEOX GOVERNANCE HARDENING ─────────────────────────────
# Per F13 SOVEREIGN directive: force every GEOX call through the arifOS
# gateway. The SCT token IS the gateway proof — arifOS is the sole issuer.
# ALL lanes now require session (SCT); receipt generation is mandatory.
# Discovery tools remain callable IF carrying valid SCT from arifOS.
LANE_REQUIRES_SESSION: dict[str, bool] = {
    "discovery": True,  # HARDENED: SCT required — "force through arifOS gateway"
    "evidence": True,  # HARDENED: SCT required
    "reasoning": True,
    "judgment": True,
}

LANE_REQUIRES_LEASE: dict[str, bool] = {
    "discovery": False,
    "evidence": False,
    "reasoning": False,  # session recommended, lease optional
    "judgment": True,  # lease required
}

LANE_REQUIRES_ARIFOS_ROUTE: dict[str, bool] = {
    "discovery": False,
    "evidence": False,
    "reasoning": False,  # direct or routed — both acceptable
    "judgment": True,  # MUST route through arifOS kernel
}

# ─── 2026-07-25 P0-2: AUTHORITY GATING ──────────────────────────────────
# Maps risk tiers to minimum SCT authority level required for execution.
# OBSERVE_ONLY sessions cannot mutate or commit irreversible changes.
MIN_AUTHORITY_FOR_TIER: dict[str, str] = {
    "readonly": "OBSERVE_ONLY",
    "c1": "OBSERVE_ONLY",
    "c2": "OPERATOR",
    "irreversible": "LIMITED_MUTATE",
}

# Tools that actually write to disk or mutate state, even if the risk map
# classifies them conservatively. These require at minimum OPERATOR authority
# regardless of their nominal risk tier.
MUTATION_TOOLS: set[str] = {
    "geox_well_ingest",  # writes LAS files to /data/geox_las/
    "geox_seismic_ingest",  # writes SEG-Y data to disk
    "geox_well_desk",  # mode=publish writes rendered panels
    "geox_map_export_package",  # exports map packages to disk
    "geox_claim",  # mode=seal writes immutable claims
    "geox_prospect",  # mode=seal writes sealed evaluations
    "geox_subsection_model",  # model building mutates workspace state
}

# Authority rank ordering (from session_enforcement.AUTHORITY_LEVELS)
_AUTHORITY_RANK = {
    "OBSERVE_ONLY": 0,
    "OPERATOR": 1,
    "LIMITED_MUTATE": 2,
    "FULL": 3,
    "SOVEREIGN": 4,
}


def _effective_min_authority(tool_name: str, risk_tier_str: str) -> str:
    """Determine the minimum authority level for a tool call.

    Returns the higher of: the tier-based minimum, or OPERATOR if the tool
    is in MUTATION_TOOLS and explicitly writes state.
    """
    tier_auth = MIN_AUTHORITY_FOR_TIER.get(risk_tier_str, "OBSERVE_ONLY")
    if tool_name in MUTATION_TOOLS:
        mutation_auth = "OPERATOR"
        if _AUTHORITY_RANK.get(mutation_auth, 0) > _AUTHORITY_RANK.get(tier_auth, 0):
            return mutation_auth
    return tier_auth


def _check_authority_gate(
    tool_name: str,
    risk_tier_str: str,
    session_authority: str | None,
    actor_id: str,
) -> tuple[str, JSONResponse | None]:
    """P0-2: Reject calls where session authority < minimum required.

    This is the enforcement that prevents OBSERVE_ONLY sessions from
    writing files, exporting data, or sealing claims — the gap that
    the 2026-07-25 audit identified as critical.

    Returns ("TRANSPORT_OK", None) if authority is sufficient.
    Returns ("HOLD", JSONResponse) if authority is insufficient.
    """
    if not session_authority:
        # No authority claim — treat as OBSERVE_ONLY (safest default)
        session_authority = "OBSERVE_ONLY"

    required = _effective_min_authority(tool_name, risk_tier_str)
    session_rank = _AUTHORITY_RANK.get(session_authority, -1)
    required_rank = _AUTHORITY_RANK.get(required, 0)

    if session_rank >= required_rank:
        logger.debug(
            f"AUTH_GATE: {tool_name} [{risk_tier_str}] → PASS "
            f"(session={session_authority}[{session_rank}] >= required={required}[{required_rank}])"
        )
        return "TRANSPORT_OK", None

    logger.warning(
        f"AUTH_GATE: {tool_name} [{risk_tier_str}] → BLOCKED "
        f"(session={session_authority}[{session_rank}] < required={required}[{required_rank}])"
    )
    error_response = JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32003,
                "message": "INSUFFICIENT_AUTHORITY",
                "data": {
                    "guard": "AUTHORITY_GATE",
                    "verdict": "HOLD",
                    "tool": tool_name,
                    "risk_tier": risk_tier_str,
                    "session_authority": session_authority,
                    "required_authority": required,
                    "actor_id": actor_id,
                    "reason": (
                        f"Tool '{tool_name}' requires {required} authority. "
                        f"Session only has {session_authority}. "
                        f"Re-initialize with arif_init(mode='init') and request higher authority."
                    ),
                    "fix": "Call arif_init(mode='init', requested_authority='OPERATOR') for write access.",
                },
            },
        },
        status_code=403,
    )
    return "HOLD", error_response


LANE_DIRECT_CALL_FORBIDDEN_MESSAGE: dict[str, str] = {
    "judgment": (
        "JUDGMENT_LANE_DIRECT_CALL: Tool '{tool}' is classified as JUDGMENT lane. "
        "Judgment lane tools MUST be called through arif_kernel_route(mode=bridge, organ=geox). "
        "Direct agent-to-GEOX calls for judgment tools are forbidden per Federation Contract §7. "
        "Route through arifOS: arif_init → arif_lease_issue → arif_kernel_route(mode=bridge, organ=geox, tool_name='{tool}')"
    ),
}


# ─── Identity Propagation Gate (P0.1 + Lane Enforcement) ──────────────────────
# Lane-aware identity enforcement:
#   - Discovery/Evidence: no session or identity required
#   - Reasoning: session_id required (actor_id recommended)
#   - Judgment: session_id + lease_id + MUST route through arifOS (reject direct calls)
# Sandbox mode bypasses all checks.

ASSET_MODE = os.getenv("GEOX_ASSET_MODE", "production")  # production | sandbox | demo


def _get_lane(tool_name: str) -> str:
    """Get the lane classification for a tool.

    Default is "discovery" (no session required) per P0 fix #120.
    Previously defaulted to "reasoning" which silently session-gated
    any unregistered tool — including health probes.
    """
    return GEOX_LANE_MAP.get(tool_name, "discovery")


# ─── Mode-Based Lane Overrides ───────────────────────────────────────────────
# Some tools have mode-based authority: non-seal modes are evidence-lane,
# seal modes require judgment routing. This dict maps (tool_name, mode_value)
# to the override lane. If a match is found, it overrides the default lane
# from GEOX_LANE_MAP.
#
# FIX 2026-07-06: geox_claim non-seal modes (create, validate, challenge,
# attach, query, list) are evidence-lane operations. Only seal mode requires
# judgment routing through arifOS.

_MODE_LANE_OVERRIDES: dict[tuple[str, str], str] = {
    ("geox_claim", "create"): "evidence",
    ("geox_claim", "validate"): "evidence",
    ("geox_claim", "challenge"): "evidence",
    ("geox_claim", "attach"): "evidence",
    ("geox_claim", "query"): "evidence",
    ("geox_claim", "list"): "evidence",
    ("geox_prospect", "compute"): "evidence",
    ("geox_prospect", "screen"): "evidence",
    ("geox_prospect", "rank"): "evidence",
}


def _get_effective_lane(tool_name: str, arguments: dict[str, Any] | None = None) -> str:
    """Get the effective lane for a tool call, considering mode-based overrides."""
    if arguments:
        # Check both flat and nested arguments — some tools wrap in `arguments` dict
        mode = arguments.get("mode") or arguments.get("action")
        if not mode and isinstance(arguments.get("arguments"), dict):
            mode = arguments["arguments"].get("mode") or arguments["arguments"].get("action")
        if mode:
            override = _MODE_LANE_OVERRIDES.get((tool_name, str(mode)))
            if override:
                return override
    return _get_lane(tool_name)


# ─── ARTIFACT-ID & RECEIPT GENERATION (2026-07-25 Hardening) ─────────────


# ═══ FIVE-LAYER EVIDENCE ENVELOPE (P0-6 · 2026-07-25) ═══════════════════
# Per the 2026-07-25 GEOX audit: "transport success is not evidence success."
# This envelope separates five independent dimensions so no tool can claim
# SUCCESS when it only means "the HTTP call arrived."
#
# Rules (from the audit's required architecture correction):
#   1. transport_status=OK        → call arrived (HTTP 200 =/= evidence)
#   2. execution_status=COMPLETED  → code ran (no exceptions =/= correct)
#   3. artifact_status=CREATED     → state changed (write =/= valid write)
#   4. verification_status=VERIFIED → independent read-back confirmed
#   5. governance_verdict          → authority decision (SEAL/HOLD/VOID)
#
# Final task success is impossible unless required acceptance fields are
# non-empty. An observe-only session must make state-changing tools
# uncallable — not merely discouraged.

EVIDENCE_ENVELOPE_SCHEMA_VERSION = "1.0.0"


def build_evidence_envelope(
    tool_name: str,
    transport_status: str = "OK",
    execution_status: str = "PENDING",
    artifact_status: str = "NONE",
    verification_status: str = "UNVERIFIED",
    governance_verdict: str = "HOLD",
    claim_state: str = "COMPUTED",
    artifact_id: str = "",
    session_id: str = "",
    actor_id: str = "",
    content_sha256: str = "",
    is_error: bool = False,
    error_detail: str = "",
) -> dict[str, Any]:
    """Build the canonical five-layer evidence envelope for a GEOX operation.

    This envelope is injected into every GEOX response by the middleware.
    It replaces the ambiguous single-field 'status' pattern where SUCCESS,
    HOLD, HYPOTHESIS, and UNKNOWN could coexist in one response.

    The five layers are independent — transport can succeed while execution
    fails, execution can complete while verification is pending, etc.

    Args:
        transport_status: "OK" | "ERROR" | "TIMEOUT"
        execution_status: "COMPLETED" | "FAILED" | "PENDING" | "REJECTED"
        artifact_status: "CREATED" | "MODIFIED" | "DELETED" | "NONE"
        verification_status: "VERIFIED" | "PENDING" | "UNVERIFIED" | "FAILED"
        governance_verdict: "SEAL" | "HOLD" | "SABAR" | "VOID" | "ADVISORY"
        claim_state: "OBSERVED" | "DERIVED" | "INTERPRETED" | "SPECULATIVE" | "COMPUTED"
    """
    import time as _env_time

    return {
        "_envelope": {
            "schema": "geox-evidence-envelope",
            "version": EVIDENCE_ENVELOPE_SCHEMA_VERSION,
            "transport_status": transport_status,
            "execution_status": execution_status,
            "artifact_status": artifact_status,
            "verification_status": verification_status,
            "governance_verdict": governance_verdict,
            "claim_state": claim_state,
        },
        "_identity": {
            "artifact_id": artifact_id,
            "session_id": session_id,
            "actor_id": actor_id,
            "tool": tool_name,
            "timestamp_utc": _env_time.strftime("%Y-%m-%dT%H:%M:%SZ", _env_time.gmtime()),
        },
        "_receipt": {
            "content_sha256": content_sha256,
            "is_error": is_error,
            "error_detail": error_detail[:200] if error_detail else "",
            "vault999_status": "PENDING",
        },
    }


def evidence_envelope_success(tool_name: str, **kwargs) -> dict[str, Any]:
    """Shortcut: build a SUCCESS envelope where all layers pass."""
    return build_evidence_envelope(
        tool_name=tool_name,
        transport_status="OK",
        execution_status="COMPLETED",
        governance_verdict="SEAL",
        **kwargs,
    )


def evidence_envelope_hold(tool_name: str, reason: str, **kwargs) -> dict[str, Any]:
    """Shortcut: build a HOLD envelope (blocked at governance layer)."""
    return build_evidence_envelope(
        tool_name=tool_name,
        transport_status="OK",
        execution_status="REJECTED",
        governance_verdict="HOLD",
        error_detail=reason,
        **kwargs,
    )


# One canonical artifact-ID format for ALL GEOX operations.
# Format: geox:{session_short}:{tool_name}:{content_hash}
# Every GEOX call in production mode generates a receipt sealed to VAULT999.


def generate_artifact_id(
    tool_name: str,
    session_id: str | None = None,
    arguments: dict[str, Any] | None = None,
) -> str:
    """Generate canonical GEOX artifact-ID.

    Format: geox:{session_short}:{tool_name}:{content_hash}

    The content_hash is a SHA256 of (tool_name + session_id + sorted args + timestamp),
    providing a stable, reproducible identifier that binds the operation to its
    session, tool, and parameters.
    """
    session_short = (session_id or "nosession")[:16]
    payload = f"{tool_name}|{session_id or 'nosession'}|{json.dumps(arguments or {}, sort_keys=True, default=str)}|{time.time()}"
    content_hash = hashlib.sha256(payload.encode()).hexdigest()[:12]
    return f"geox:{session_short}:{tool_name}:{content_hash}"


async def seal_geox_receipt(
    tool_name: str,
    artifact_id: str,
    session_id: str | None,
    actor_id: str | None,
    verdict: str,
    result_summary: str = "",
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal a GEOX operation receipt to VAULT999 via A-FORGE forge_vault.

    This is the permanent audit trail required by F11 AUDITABILITY and the
    F13 SOVEREIGN directive (2026-07-25). Every GEOX call in production mode
    produces a receipt. Failures are logged but do not block the operation —
    the receipt is evidence, not a gate.
    """
    receipt = {
        "artifact_id": artifact_id,
        "tool": tool_name,
        "session_id": session_id,
        "actor_id": actor_id,
        "verdict": verdict,
        "summary": result_summary[:500] if result_summary else "",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # Write to A-FORGE forge_vault for VAULT999 sealing
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            vault_resp = await client.post(
                "http://127.0.0.1:7072/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "forge_vault",
                        "arguments": {
                            "mode": "write",
                            "name": f"geox-{artifact_id}",
                            "category": "geox.operation",
                            "value": json.dumps(receipt),
                            "actor_id": actor_id or "geox-organ",
                            "session_id": session_id or "",
                        },
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            if vault_resp.status_code == 200:
                receipt["vault_status"] = "sealed"
                logger.info(f"RECEIPT: {artifact_id} → VAULT999 sealed")
            else:
                receipt["vault_status"] = f"error_http_{vault_resp.status_code}"
                logger.warning(f"RECEIPT: {artifact_id} → VAULT999 write failed: {vault_resp.status_code}")
    except Exception as exc:
        receipt["vault_status"] = f"error_{type(exc).__name__}"
        logger.warning(f"RECEIPT: {artifact_id} → VAULT999 unreachable: {exc}")

    # Also append to local receipt ledger (fallback, read by vault999-writer)
    try:
        ledger_path = "/root/.local/share/arifos/geox_receipt_ledger.jsonl"
        os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
        with open(ledger_path, "a") as f:
            f.write(json.dumps(receipt) + "\n")
    except Exception as exc:
        logger.warning(f"RECEIPT: local ledger write failed: {exc}")

    return receipt


def _check_lane_enforcement(
    tool_name: str,
    session_id: str | None = None,
    actor_id: str | None = None,
    lease_id: str | None = None,
    is_direct_call: bool = True,
    arguments: dict[str, Any] | None = None,
) -> tuple[str, JSONResponse | None]:
    """Lane-based authority enforcement (Federation Contract §3).

    Returns:
      ("TRANSPORT_OK", None) if the call is authorized for this lane (not constitutional SEAL).
      ("HOLD", JSONResponse) if lane enforcement blocks the call.
    """
    if ASSET_MODE == "sandbox":
        return "TRANSPORT_OK", None

    lane = _get_effective_lane(tool_name, arguments)

    # ── JUDGMENT LANE: MUST route through arifOS ──────────────────────
    if LANE_REQUIRES_ARIFOS_ROUTE.get(lane, False) and is_direct_call:
        reason = LANE_DIRECT_CALL_FORBIDDEN_MESSAGE.get(lane, "").format(tool=tool_name)
        logger.warning(f"LANE: {tool_name} [{lane}] → BLOCKED (direct call forbidden)")
        error_response = JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32007,
                    "message": "JUDGMENT_LANE_DIRECT_CALL_FORBIDDEN",
                    "data": {
                        "guard": "LANE_ENFORCEMENT",
                        "verdict": "HOLD",
                        "tool": tool_name,
                        "lane": lane,
                        "reason": reason,
                        "fix": f"Route through arifOS: arif_kernel_route(mode=bridge, organ=geox, tool_name='{tool_name}')",
                    },
                },
            },
            status_code=428,
        )
        return "HOLD", error_response

    # ── REASONING / JUDGMENT LANE: session required ──────────────────
    if LANE_REQUIRES_SESSION.get(lane, False):
        if not session_id or session_id in ("anonymous", "null", "None", ""):
            reason = f"Tool '{tool_name}' is in {lane} lane — session_id required"
            logger.warning(f"LANE: {tool_name} [{lane}] → HOLD (no session)")
            error_response = JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32003,
                        "message": "SESSION_REQUIRED",
                        "data": {
                            "guard": "LANE_ENFORCEMENT",
                            "verdict": "HOLD",
                            "tool": tool_name,
                            "lane": lane,
                            "reason": reason,
                            "fix": "Call arif_init(mode=init) first to establish governed session.",
                        },
                    },
                },
                status_code=423,
            )
            return "HOLD", error_response

    # ── JUDGMENT LANE: lease required ────────────────────────────────
    if LANE_REQUIRES_LEASE.get(lane, False):
        if not lease_id or lease_id in ("anonymous", "null", "None", ""):
            reason = f"Tool '{tool_name}' is in {lane} lane — lease_id required"
            logger.warning(f"LANE: {tool_name} [{lane}] → HOLD (no lease)")
            error_response = JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32003,
                        "message": "LEASE_REQUIRED",
                        "data": {
                            "guard": "LANE_ENFORCEMENT",
                            "verdict": "HOLD",
                            "tool": tool_name,
                            "lane": lane,
                            "reason": reason,
                            "fix": "Call arif_lease_issue first, then pass lease_id in arguments.",
                        },
                    },
                },
                status_code=423,
            )
            return "HOLD", error_response

    # ── DISCOVERY / EVIDENCE LANE: always allowed ───────────────────
    logger.info(f"LANE: {tool_name} [{lane}] → ALLOWED")
    return "TRANSPORT_OK", None


def _check_identity_propagation(
    tool_name: str,
    session_id: str | None = None,
    actor_id: str | None = None,
    arguments: dict[str, Any] | None = None,
) -> tuple[str, JSONResponse | None]:
    """P0.1: Reject anonymous tool calls in production mode.

    NOTE: Identity check is now lane-aware. Discovery/Evidence lane tools
    are exempt from identity requirements. Reasoning/Judgment lane tools
    are checked by _check_lane_enforcement instead.

    Returns:
      ("TRANSPORT_OK", None) if identity is valid and bound, or lane-exempt.
      ("HOLD", JSONResponse) if identity is missing for governed lanes.
    """
    if ASSET_MODE == "sandbox":
        logger.info(f"GOV: {tool_name} [SANDBOX] → identity check bypassed")
        return "TRANSPORT_OK", None

    lane = _get_effective_lane(tool_name, arguments)

    # Discovery and Evidence lanes may be genuinely anonymous. Once a caller
    # supplies either identity field, however, that is an identity claim and
    # must be verified. Never let forged credentials silently downgrade to
    # anonymous access while full content is returned.
    identity_claimed = bool(
        (session_id and session_id not in ("anonymous", "null", "None"))
        or (actor_id and actor_id not in ("anonymous", "null", "None", "geox-governed"))
    )
    if lane in ("discovery", "evidence") and not identity_claimed:
        return "TRANSPORT_OK", None

    # Governed lanes and claimed identities: require a complete, bound pair.
    # actor_id must be present and not null/anonymous
    if not actor_id or actor_id in ("anonymous", "null", "None", ""):
        reason = f"actor_id is '{actor_id}' — {lane} lane tools require actor identity"
        logger.warning(f"GOV: {tool_name} [{lane}] → HOLD_IDENTITY_REQUIRED: {reason}")
        error_response = JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32003,
                    "message": "HOLD_IDENTITY_REQUIRED",
                    "data": {
                        "guard": "P0_IDENTITY_PROPAGATION",
                        "verdict": "HOLD",
                        "tool": tool_name,
                        "lane": lane,
                        "reason": reason,
                        "fix": "Pass actor_id from arifOS session. Call arif_init(mode=init) first.",
                    },
                },
            },
            status_code=423,
        )
        return "HOLD", error_response

    # session_id must be present and not null/anonymous
    if not session_id or session_id in ("anonymous", "null", "None", ""):
        reason = f"session_id is '{session_id}' — {lane} lane tools require governed session"
        logger.warning(f"GOV: {tool_name} [{lane}] → HOLD_IDENTITY_REQUIRED: {reason}")
        error_response = JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32003,
                    "message": "HOLD_IDENTITY_REQUIRED",
                    "data": {
                        "guard": "P0_IDENTITY_PROPAGATION",
                        "verdict": "HOLD",
                        "tool": tool_name,
                        "lane": lane,
                        "reason": reason,
                        "fix": "Call arif_init(mode=init) first to establish governed session.",
                    },
                },
            },
            status_code=423,
        )
        return "HOLD", error_response

    # SESSION BINDING VALIDATION — verify session_id against arifOS kernel.
    # Previous code only checked string presence; any non-empty string passed.
    # Now we validate the session is actually real and bound.
    validation = validate_session(session_id, actor_id, required_authority="OBSERVE_ONLY")
    if not validation.ok:
        reason = f"Session validation failed: {validation.error_code} — {validation.error_message}"
        logger.warning(f"GOV: {tool_name} [{lane}] → HOLD_SESSION_INVALID: {reason}")
        error_response = JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32003,
                    "message": "SESSION_INVALID",
                    "data": {
                        "guard": "SESSION_BINDING",
                        "verdict": "HOLD",
                        "tool": tool_name,
                        "lane": lane,
                        "error_code": validation.error_code,
                        "reason": reason,
                        "fix": "Call arif_init(mode=init) to get a valid session_id, then pass it to GEOX tools.",
                    },
                },
            },
            status_code=423,
        )
        return "HOLD", error_response

    # Replace capability material with canonical claims before tool execution.
    # A signed SCT is proof, not a receipt identifier; never echo the raw token.
    claims = validation.session if isinstance(validation.session, dict) else {}
    canonical_session_id = claims.get("sid") or claims.get("session_id") or session_id
    canonical_actor_id = validation.actor or actor_id
    if isinstance(arguments, dict):
        arguments["session_id"] = canonical_session_id
        arguments["actor_id"] = canonical_actor_id

    return "TRANSPORT_OK", None


async def check_governance(
    tool_name: str,
    arguments: dict[str, Any],
    session_id: str | None = None,
    actor_id: str = "anonymous",
    fail_closed: bool = True,
    is_direct_call: bool = True,
) -> tuple[str, JSONResponse | None, str]:
    """
    Check governance for a GEOX tool call.

    Returns: (verdict, error_response_or_None, artifact_id)
      - ("TRANSPORT_OK", None, artifact_id) → proceed with execution
      - ("ADVISORY", None, artifact_id) → proceed (kernel noted the call)
      - ("HOLD", JSONResponse, "") → blocked
      - ("VOID", JSONResponse, "") → rejected

    HARDENED 2026-07-25 per F13 SOVEREIGN directive:
      - ALL lanes require session (SCT from arifOS gateway)
      - Every call generates a canonical artifact-ID and VAULT999 receipt
      - Direct calls without valid SCT are rejected in production mode

    Enforcement order:
      1. LANE ENFORCEMENT (Federation Contract §3):
         - Judgment lane: BLOCK direct calls → must route through arifOS
         - ALL lanes: require valid session (SCT) in production mode
         - Judgment: require lease_id
      2. IDENTITY PROPAGATION (P0.1):
         - ALL lanes: require actor_id + session_id
         - Sandbox mode bypasses all checks
      3. RISK TIER (C1/C2/IRREVERSIBLE):
         - Calls arifOS kernel for governed tools

    fail_closed=True: If kernel unreachable or session unbound → HOLD
    fail_closed=False: Allow pass-through (for C1 advisory tools)
    """
    # Extract lane-enforcement fields from arguments
    lease_id = arguments.get("lease_id") if arguments else None
    # session_id from arguments takes precedence over parameter
    if arguments and arguments.get("session_id"):
        session_id = arguments.get("session_id")
    if arguments and arguments.get("actor_id"):
        actor_id = arguments.get("actor_id")
    # Also check nested arguments (wrapper pattern: arguments.arguments)
    if arguments and isinstance(arguments.get("arguments"), dict):
        inner = arguments["arguments"]
        if inner.get("lease_id"):
            lease_id = inner["lease_id"]
        if inner.get("session_id"):
            session_id = inner["session_id"]
        if inner.get("actor_id"):
            actor_id = inner["actor_id"]

    # ═══ STEP 1: LANE ENFORCEMENT (Federation Contract §3) ═══════════
    lane_verdict, lane_error = _check_lane_enforcement(
        tool_name=tool_name,
        session_id=session_id,
        actor_id=actor_id,
        lease_id=lease_id,
        is_direct_call=is_direct_call,
        arguments=arguments,
    )
    if lane_verdict == "HOLD":
        return lane_verdict, lane_error, ""

    risk_tier = GEOX_RISK_MAP.get(tool_name, RiskTier.C1_ADVISORY)
    # D5: geox_claim is mode-dispatched — only seal is C2/judgment; create is evidence
    if tool_name == "geox_claim" and arguments:
        effective = arguments
        if isinstance(arguments.get("arguments"), dict):
            effective = arguments["arguments"]
        mode = str(effective.get("mode") or effective.get("action") or "create").lower()
        if mode in ("create", "validate", "challenge", "attach", "attach_evidence", "query", "list"):
            risk_tier = RiskTier.C1_ADVISORY
        elif mode == "seal":
            risk_tier = RiskTier.IRREVERSIBLE

    # ═══ STEP 2: IDENTITY PROPAGATION (P0.1 — lane-aware) ══════════
    id_verdict, id_error = _check_identity_propagation(tool_name, session_id, actor_id, arguments)
    if id_verdict == "HOLD":
        return id_verdict, id_error, ""

    # ═══ STEP 2.5: AUTHORITY GATING (P0.2 — 2026-07-25) ═════════════
    # OBSERVE_ONLY sessions cannot mutate. Validate the session's
    # authority level against the tool's minimum required authority.
    risk_tier_str = risk_tier.value if isinstance(risk_tier, RiskTier) else str(risk_tier)
    auth_validation = validate_session(session_id, actor_id, required_authority="OBSERVE_ONLY")
    session_authority = auth_validation.authority if auth_validation.ok else "OBSERVE_ONLY"
    auth_verdict, auth_error = _check_authority_gate(
        tool_name=tool_name,
        risk_tier_str=risk_tier_str,
        session_authority=session_authority,
        actor_id=actor_id or "anonymous",
    )
    if auth_verdict == "HOLD":
        return auth_verdict, auth_error, ""

    # ═══ ARTIFACT-ID + RECEIPT (2026-07-25 Hardening) ═══════════════
    artifact_id = generate_artifact_id(tool_name, session_id, arguments)

    # READONLY — log and proceed
    if risk_tier == RiskTier.READONLY:
        logger.info(f"GOV: {tool_name} [READONLY] → SEAL artifact_id={artifact_id}")
        # Fire-and-forget: seal receipt (don't block on VAULT999 latency)
        import asyncio as _asyncio

        _asyncio.ensure_future(seal_geox_receipt(tool_name, artifact_id, session_id, actor_id, "TRANSPORT_OK", "", arguments))
        return "TRANSPORT_OK", None, artifact_id

    # C1 ADVISORY — call kernel but proceed regardless
    if risk_tier == RiskTier.C1_ADVISORY:
        candidate = {
            "action": f"GEOX_ORGAN:{tool_name}",
            "description": f"GEOX organ tool '{tool_name}' [C1 ADVISORY]",
            "actor_id": actor_id,
            "organ": "GEOX",
            "tool": tool_name,
            "risk_tier": risk_tier.value,
        }
        judge_params = {
            "mode": "judge",
            "candidate": json.dumps(candidate),
            "session_id": session_id,
            "actor_id": actor_id,
        }
        logger.info(f"GOV: {tool_name} [C1] → calling arifOS (advisory)...")
        kernel_result = await _call_arif_kernel("arif_judge", judge_params)
        verdict = kernel_result.get("verdict", "ADVISORY")
        logger.info(f"GOV: {tool_name} [C1] → {verdict} (proceeding anyway)")
        return verdict, None, artifact_id

    # C2 / IRREVERSIBLE — SEAL required
    # Build candidate for arifOS judgment
    candidate = {
        "action": f"GEOX_ORGAN:{tool_name}",
        "description": (
            f"GEOX organ tool '{tool_name}' with risk tier {risk_tier.value}. SEAL required from arifOS kernel before execution."
        ),
        "actor_id": actor_id,
        "organ": "GEOX",
        "tool": tool_name,
        "risk_tier": risk_tier.value,
        "arguments_keys": list(arguments.keys()),
    }

    judge_params = {
        "mode": "judge",
        "candidate": json.dumps(candidate),
        "session_id": session_id,
        "actor_id": actor_id,
    }

    logger.info(f"GOV: {tool_name} [{risk_tier.value}] → calling arifOS kernel...")

    kernel_result = await _call_arif_kernel("arif_judge", judge_params)

    verdict = "HOLD"  # fail-closed default
    reason = "arifOS kernel unreachable or session unbound — fail-closed"

    if isinstance(kernel_result, dict):
        kernel_status = kernel_result.get("status", "")

        # Kernel error — fail closed
        if kernel_status == "ERROR":
            reason = f"arifOS kernel error: {kernel_result.get('error', 'unknown')}"
            logger.warning(f"GOV: {tool_name} [{risk_tier.value}] → HOLD (kernel error): {reason}")

        # Valid response — extract verdict
        elif "verdict" in kernel_result:
            verdict = kernel_result.get("verdict", "HOLD")
            judgment = kernel_result.get("judgment", {})
            reason = judgment.get("reason", kernel_result.get("reason", "No reason provided"))

            # Session unbound — fail closed for IRREVERSIBLE/C2
            session_bound = kernel_result.get("session_bound", True)
            if not session_bound and risk_tier in (RiskTier.C2_EXECUTE, RiskTier.IRREVERSIBLE):
                verdict = "HOLD"
                reason = (
                    "arifOS: session not bound. C2/IRREVERSIBLE tools require a governed session (arif_init) before execution."
                )
        else:
            reason = f"Unexpected kernel response: {str(kernel_result)[:100]}"
            logger.warning(f"GOV: {tool_name} [{risk_tier.value}] → unexpected kernel response")

    # TRANSPORT_OK = execution permitted. Constitutional SEAL is arifOS-only (never this layer).
    if verdict in ("SEAL", "TRANSPORT_OK", "ALLOW", "PROCEED"):
        logger.info(
            f"GOV: {tool_name} [{risk_tier.value}] → TRANSPORT_OK "
            f"(kernel_verdict={verdict}; SEAL word reserved for constitutional seal) "
            f"artifact_id={artifact_id}"
        )
        import asyncio as _asyncio2

        _asyncio2.ensure_future(seal_geox_receipt(tool_name, artifact_id, session_id, actor_id, verdict, "", arguments))
        return "TRANSPORT_OK", None, artifact_id

    # HOLD or VOID — block execution (fail-closed)
    error_msg = f"arifOS {verdict}: {reason}"
    logger.warning(f"GOV: {tool_name} [{risk_tier.value}] → {verdict} 🚫 {error_msg}")

    error_response = JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32003 if verdict == "HOLD" else -32004,
                "message": error_msg,
                "data": {
                    "guard": "ORGAN_GOVERNANCE",
                    "verdict": verdict,
                    "tool": tool_name,
                    "risk_tier": risk_tier.value,
                    "reason": reason,
                },
            },
        },
        status_code=423 if verdict == "HOLD" else 403,
    )
    return verdict, error_response, ""
