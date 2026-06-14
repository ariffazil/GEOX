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

import httpx
import json
import logging
import os
from enum import StrEnum
from typing import Any

from starlette.responses import JSONResponse

logger = logging.getLogger("geox.governance")


class RiskTier(StrEnum):
    READONLY = "readonly"
    C1_ADVISORY = "c1"
    C2_EXECUTE = "c2"
    IRREVERSIBLE = "irreversible"


# ─── GEOX Tool Risk Map ────────────────────────────────────────────────────────
# All entries must match canonical tool names from CANONICAL_PUBLIC_TOOLS
# or LEGACY_ALIAS_MAP in src/geox_mcp/registry.py.

GEOX_RISK_MAP: dict[str, RiskTier] = {
    # READONLY — log only, no kernel call
    "geox_data_ingest_bundle": RiskTier.READONLY,
    "geox_data_qc_bundle": RiskTier.READONLY,
    "geox_dst_ingest_test": RiskTier.READONLY,
    "geox_header_inspect": RiskTier.READONLY,
    "geox_las_inspect": RiskTier.READONLY,
    "geox_seismic_segy_inspect": RiskTier.READONLY,
    "geox_evidence_discover": RiskTier.READONLY,
    "geox_report_to_workflow": RiskTier.C1_ADVISORY,  # P1.3: workflow steps can feed decision pipelines — advisory only
    "geox_subsurface_generate_candidates": RiskTier.READONLY,
    "geox_subsurface_verify_integrity": RiskTier.READONLY,
    "geox_seismic_compute": RiskTier.READONLY,
    "geox_sequence_interpret": RiskTier.READONLY,
    "geox_evidence_reason": RiskTier.READONLY,
    "geox_map_context_scene": RiskTier.READONLY,
    "geox_system_registry_status": RiskTier.READONLY,
    "geox_horizon_contrast_surface": RiskTier.READONLY,
    "geox_coord_transform_tool": RiskTier.READONLY,
    "geox_blockspace_resolution_tool": RiskTier.READONLY,
    "geox_volume_frame_tool": RiskTier.C2_EXECUTE,  # P0.1: readOnlyHint=False, destructiveHint=True — must match tier
    "geox_seismic_compute_attribute_tool": RiskTier.READONLY,
    "geox_fault_stick_ingest_tool": RiskTier.READONLY,
    "geox_attribute_registry_list_tool": RiskTier.READONLY,
    "geox_blend_volume_tool": RiskTier.READONLY,
    "geox_claim_create": RiskTier.READONLY,
    "geox_claim_validate": RiskTier.READONLY,
    "geox_claim_challenge": RiskTier.READONLY,
    "geox_evidence_attach": RiskTier.READONLY,
    "geox_basin_resolve": RiskTier.READONLY,
    "geox_basin_profile": RiskTier.READONLY,
    "geox_query_intake": RiskTier.READONLY,
    "geox_abstraction_guard": RiskTier.READONLY,
    "geox_literature_ingest": RiskTier.READONLY,
    "geox_vision_perceptual_inventory": RiskTier.READONLY,
    "geox_vision_audit": RiskTier.READONLY,
    "geox_vision_calibrate": RiskTier.READONLY,
    "geox_vision_minimax_inference": RiskTier.READONLY,
    "geox_query_macrostrat": RiskTier.READONLY,
    # C1 — kernel pre-check, execute anyway
    "geox_prospect_evaluate": RiskTier.C1_ADVISORY,
    # C2 — SEAL required from arifOS
    "geox_claim_seal": RiskTier.C2_EXECUTE,
    # IRREVERSIBLE — SEAL + ack_irreversible already checked by RT-3
    "geox_segy_export_tool": RiskTier.IRREVERSIBLE,
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
    """Load tool→lane mapping from GEOX.yaml federation contract or fallback."""
    try:
        import yaml
        contract_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "arifOS", "federation", "GEOX.yaml",
        )
        # Also try local path (when running from geox repo directly)
        if not os.path.exists(contract_path):
            contract_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "federation", "GEOX.yaml",
            )
        if os.path.exists(contract_path):
            with open(contract_path) as f:
                contract = yaml.safe_load(f)
            return contract.get("lanes", {}).get("tool_lane_map", {})
    except Exception:
        pass

    # Fallback: lane classification from registry manifest
    try:
        from geox_mcp.registry import GEOX_TOOL_MANIFEST
        return {t["name"]: t.get("lane", "reasoning") for t in GEOX_TOOL_MANIFEST}
    except Exception:
        pass

    # Ultimate fallback: hardcoded lane map
    return {
        "geox_system_registry_status": "discovery",
        "geox_attribute_registry_list_tool": "discovery",
        "geox_basin_resolve": "discovery",
        "geox_query_intake": "discovery",
        "geox_query_macrostrat": "discovery",
        "geox_data_ingest_bundle": "evidence",
        "geox_data_qc_bundle": "evidence",
        "geox_dst_ingest_test": "evidence",
        "geox_header_inspect": "evidence",
        "geox_las_inspect": "evidence",
        "geox_seismic_segy_inspect": "evidence",
        "geox_evidence_discover": "evidence",
        "geox_evidence_attach": "evidence",
        "geox_literature_ingest": "evidence",
        "geox_fault_stick_ingest_tool": "evidence",
        "geox_volume_frame_tool": "evidence",
        "geox_vision_perceptual_inventory": "evidence",
        "geox_vision_calibrate": "evidence",
        "geox_subsurface_generate_candidates": "reasoning",
        "geox_subsurface_verify_integrity": "reasoning",
        "geox_seismic_compute": "reasoning",
        "geox_seismic_compute_attribute_tool": "reasoning",
        "geox_sequence_interpret": "reasoning",
        "geox_evidence_reason": "reasoning",
        "geox_prospect_evaluate": "reasoning",
        "geox_map_context_scene": "reasoning",
        "geox_horizon_contrast_surface": "reasoning",
        "geox_coord_transform_tool": "reasoning",
        "geox_blockspace_resolution_tool": "reasoning",
        "geox_blend_volume_tool": "reasoning",
        "geox_basin_profile": "reasoning",
        "geox_vision_minimax_inference": "reasoning",
        "geox_vision_audit": "reasoning",
        "geox_report_to_workflow": "reasoning",
        "geox_abstraction_guard": "reasoning",
        "geox_claim_create": "judgment",
        "geox_claim_validate": "judgment",
        "geox_claim_challenge": "judgment",
        "geox_claim_seal": "judgment",
        "geox_segy_export_tool": "judgment",
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
    "judgment": True,     # lease required
}

LANE_REQUIRES_ARIFOS_ROUTE: dict[str, bool] = {
    "discovery": False,
    "evidence": False,
    "reasoning": False,   # direct or routed — both acceptable
    "judgment": True,      # MUST route through arifOS kernel
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


def _check_lane_enforcement(
    tool_name: str,
    session_id: str | None = None,
    actor_id: str | None = None,
    lease_id: str | None = None,
    is_direct_call: bool = True,
) -> tuple[str, JSONResponse | None]:
    """Lane-based authority enforcement (Federation Contract §3).

    Returns:
      ("SEAL", None) if the call is authorized for this lane.
      ("HOLD", JSONResponse) if lane enforcement blocks the call.
    """
    if ASSET_MODE == "sandbox":
        return "SEAL", None

    lane = _get_lane(tool_name)

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
                        "fix": "Route through arifOS: arif_kernel_route(mode=bridge, organ=geox, tool_name='{tool}')".format(tool=tool_name),
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

    lane = _get_lane(tool_name)

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

    # ═══ STEP 1: LANE ENFORCEMENT (Federation Contract §3) ═══════════
    lane_verdict, lane_error = _check_lane_enforcement(
        tool_name=tool_name,
        session_id=session_id,
        actor_id=actor_id,
        lease_id=lease_id,
        is_direct_call=is_direct_call,
    )
    if lane_verdict == "HOLD":
        return lane_verdict, lane_error

    risk_tier = GEOX_RISK_MAP.get(tool_name, RiskTier.C1_ADVISORY)

    # ═══ STEP 2: IDENTITY PROPAGATION (P0.1 — lane-aware) ══════════
    id_verdict, id_error = _check_identity_propagation(tool_name, session_id, actor_id)
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
