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

import json
import logging
import os
from enum import StrEnum
from typing import Any

import httpx
from starlette.responses import JSONResponse

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
}


# ─── arifOS Kernel Client ──────────────────────────────────────────────────────

ARIFOS_KERNEL_URL = os.getenv("ARIFOS_KERNEL_URL", "http://127.0.0.1:8088")
_ARIFOS_KERNEL_TOKEN = os.getenv("ARIFOS_KERNEL_TOKEN", "")


async def _call_arif_kernel(tool_name: str, params: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    """Call arifOS MCP kernel asynchronously. FAIL-CLOSED on error — returns error dict."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": params},
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if _ARIFOS_KERNEL_TOKEN:
        headers["Authorization"] = f"Bearer {_ARIFOS_KERNEL_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{ARIFOS_KERNEL_URL}/mcp", json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            return result.get("result", {"status": "ERROR", "error": "no result in response"})
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
                # ── CONTRAST DETECTION (pure computation, no session) ───────────
                "geox_contrast_detect": "discovery",  # universal contrast detector — read-only computation
                # ── BIOSTRAT (read-only parse/lookup, no session) ───────────────
                "geox_biostrat_parse": "discovery",  # text parsing — pure regex
                "geox_biostrat_nn_age": "discovery",  # NN zone age lookup — table read
                "geox_biostrat_ruling_check": "discovery",  # contradiction check — read-only
                "geox_biostrat_falsify": "discovery",  # 8-gate falsification — read-only
                # ── MAP TOOLS (read-only render/plan, no session) ───────────────
                "geox_map_layers_list": "discovery",  # layer registry read
                "geox_map_scene_plan": "discovery",  # scene planning — pure computation
                "geox_map_render_preview": "discovery",  # preview render — read-only
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
LANE_REQUIRES_SESSION: dict[str, bool] = {
    "discovery": False,
    "evidence": False,
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

LANE_DIRECT_CALL_FORBIDDEN_MESSAGE: dict[str, str] = {
    "judgment": (
        "JUDGMENT_LANE_DIRECT_CALL: Tool '{tool}' is classified as JUDGMENT lane. "
        "Judgment lane tools MUST be called through arif_kernel_route(mode=bridge, organ=geox). "
        "Direct agent-to-GEOX calls for judgment tools are forbidden per Federation Contract §7. "
        "Route through arifOS: arif_session_init → arif_lease_issue → arif_kernel_route(mode=bridge, organ=geox, tool_name='{tool}')"
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
    """Get the lane classification for a tool."""
    return GEOX_LANE_MAP.get(tool_name, "reasoning")


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
      ("SEAL", None) if the call is authorized for this lane.
      ("HOLD", JSONResponse) if lane enforcement blocks the call.
    """
    if ASSET_MODE == "sandbox":
        return "SEAL", None

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
                            "fix": "Call arif_session_init first to establish governed session.",
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
    return "SEAL", None


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
      ("SEAL", None) if identity is valid and bound, or lane-exempt.
      ("HOLD", JSONResponse) if identity is missing for governed lanes.
    """
    if ASSET_MODE == "sandbox":
        logger.info(f"GOV: {tool_name} [SANDBOX] → identity check bypassed")
        return "SEAL", None

    lane = _get_effective_lane(tool_name, arguments)

    # Discovery and Evidence lanes: no identity required
    if lane in ("discovery", "evidence"):
        return "SEAL", None

    # Reasoning/Judgment lanes: identity check (supplementary to lane enforcement)
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
                        "fix": "Pass actor_id from arifOS session. Call arif_session_init first.",
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
                        "fix": "Call arif_session_init first to establish governed session.",
                    },
                },
            },
            status_code=423,
        )
        return "HOLD", error_response

    return "SEAL", None


async def check_governance(
    tool_name: str,
    arguments: dict[str, Any],
    session_id: str | None = None,
    actor_id: str = "geox-governed",
    fail_closed: bool = True,
    is_direct_call: bool = True,
) -> tuple[str, JSONResponse | None]:
    """
    Check governance for a GEOX tool call.

    Returns: (verdict, error_response_or_None)
      - ("SEAL", None) → proceed with execution
      - ("ADVISORY", None) → proceed (kernel noted the call)
      - ("HOLD", dict) → blocked, return dict as JSON error response
      - ("VOID", dict) → rejected, return dict as JSON error response

    Applied after RT-3 guard (which checks ack_irreversible).

    Enforcement order:
      1. LANE ENFORCEMENT (Federation Contract §3):
         - Judgment lane: BLOCK direct calls → must route through arifOS
         - Reasoning/Judgment: require session_id
         - Judgment: require lease_id
         - Discovery/Evidence: always allowed
      2. IDENTITY PROPAGATION (P0.1):
         - Discovery/Evidence lanes: exempt
         - Reasoning/Judgment: require actor_id + session_id
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
        return lane_verdict, lane_error

    risk_tier = GEOX_RISK_MAP.get(tool_name, RiskTier.C1_ADVISORY)

    # ═══ STEP 2: IDENTITY PROPAGATION (P0.1 — lane-aware) ══════════
    id_verdict, id_error = _check_identity_propagation(tool_name, session_id, actor_id, arguments)
    if id_verdict == "HOLD":
        return id_verdict, id_error

    # READONLY — log and proceed
    if risk_tier == RiskTier.READONLY:
        logger.info(f"GOV: {tool_name} [READONLY] → SEAL (log only)")
        return "SEAL", None

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
        kernel_result = await _call_arif_kernel("arif_judge_deliberate", judge_params)
        verdict = kernel_result.get("verdict", "ADVISORY")
        logger.info(f"GOV: {tool_name} [C1] → {verdict} (proceeding anyway)")
        return verdict, None

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

    kernel_result = await _call_arif_kernel("arif_judge_deliberate", judge_params)

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
                    "arifOS: session not bound. C2/IRREVERSIBLE tools require "
                    "a governed session (arif_session_init) before execution."
                )
        else:
            reason = f"Unexpected kernel response: {str(kernel_result)[:100]}"
            logger.warning(f"GOV: {tool_name} [{risk_tier.value}] → unexpected kernel response")

    if verdict == "SEAL":
        logger.info(f"GOV: {tool_name} [{risk_tier.value}] → SEAL ✅")
        return "SEAL", None

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
    return verdict, error_response
