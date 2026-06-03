"""
organ_governance.py — GEOX arifOS Governance Integration
========================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

GEOX-specific governance module that:
  1. Defines risk tier for all GEOX tools
  2. Calls arifOS kernel for C2+/IRREVERSIBLE tools
  3. Returns (verdict, error_response_or_None) tuple

Used by geox_mcp/server.py after RT-3 guard check.

arifOS kernel endpoint: http://arifosmcp:8080/mcp

FAIL-CLOSED: If arifOS kernel is unreachable or session is unbound,
defaults to HOLD. No guessing, no bypass.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from enum import StrEnum
from typing import Any, Optional

from starlette.responses import JSONResponse

logger = logging.getLogger("geox.governance")


class RiskTier(StrEnum):
    READONLY = "readonly"
    C1_ADVISORY = "c1"
    C2_EXECUTE = "c2"
    IRREVERSIBLE = "irreversible"


# ─── GEOX Tool Risk Map ────────────────────────────────────────────────────────

GEOX_RISK_MAP: dict[str, RiskTier] = {
    # READONLY — log only, no kernel call
    "geox_well_analyze_sequence": RiskTier.READONLY,
    "geox_well_compute_gr_bins": RiskTier.READONLY,
    "geox_well_build_packages": RiskTier.READONLY,
    "geox_well_infer_seq_strat": RiskTier.READONLY,
    "geox_section_interpret_correlation": RiskTier.READONLY,
    "geox_map_context_scene": RiskTier.READONLY,
    "geox_bundle_security_audit": RiskTier.READONLY,
    "geox_data_qc_bundle": RiskTier.READONLY,
    "geox_forward_model_synthetic": RiskTier.READONLY,
    "geox_seismic_well_tie_compute": RiskTier.READONLY,
    "geox_time_depth_anchor": RiskTier.READONLY,
    "geox_process_abduction": RiskTier.READONLY,
    "geox_subsurface_verify_integrity": RiskTier.READONLY,
    "geox_evidence_contradiction_scan": RiskTier.READONLY,
    "geox_evidence_summarize_cross": RiskTier.READONLY,
    "geox_resource_registry_status": RiskTier.READONLY,
    "geox_contradiction_registry_status": RiskTier.READONLY,
    "geox_test_receipt_status": RiskTier.READONLY,
    "geox_mcp_health_check": RiskTier.READONLY,
    "geox_anomalous_contrast_detector": RiskTier.READONLY,
    "geox_vision_time_to_depth": RiskTier.READONLY,
    "geox_time4d_analyze_system": RiskTier.READONLY,
    "geox_subsurface_generate_candidates": RiskTier.READONLY,
    "geox_stratigraphy_preview_config": RiskTier.READONLY,
    # C1 — kernel pre-check, execute anyway
    "geox_prospect_evaluate": RiskTier.C1_ADVISORY,
    "geox_prospect_judge_preview": RiskTier.C1_ADVISORY,
    # C2 — SEAL required from arifOS
    "geox_task_metabolize_basin": RiskTier.C2_EXECUTE,
    "geox_task_ingest_las_batch": RiskTier.C2_EXECUTE,
    "geox_stratigraphy_run_pipeline": RiskTier.C2_EXECUTE,
    # IRREVERSIBLE — SEAL + ack_irreversible already checked by RT-3
    "geox_prospect_judge_seal": RiskTier.IRREVERSIBLE,
}


# ─── arifOS Kernel Client ──────────────────────────────────────────────────────

ARIFOS_KERNEL_URL = os.getenv("ARIFOS_KERNEL_URL", "http://arifosmcp:8080")
_ARIFOS_KERNEL_TOKEN = os.getenv("ARIFOS_KERNEL_TOKEN", "")


def _call_arif_kernel(tool_name: str, params: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    """Call arifOS MCP kernel. FAIL-CLOSED on error — returns error dict."""
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": params},
        }
    ).encode()

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if _ARIFOS_KERNEL_TOKEN:
        headers["Authorization"] = f"Bearer {_ARIFOS_KERNEL_TOKEN}"

    req = urllib.request.Request(
        f"{ARIFOS_KERNEL_URL}/mcp",
        data=payload,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
            return result.get("result", {"status": "ERROR", "error": "no result in response"})
    except Exception as exc:
        logger.error(f"arifOS kernel call failed: {exc}")
        return {"status": "ERROR", "error": str(exc)}


# ─── Governance Check ─────────────────────────────────────────────────────────


def check_governance(
    tool_name: str,
    arguments: dict[str, Any],
    session_id: Optional[str] = None,
    actor_id: str = "geox-governed",
    fail_closed: bool = True,
) -> tuple[str, Optional[JSONResponse]]:
    """
    Check governance for a GEOX tool call.

    Returns: (verdict, error_response_or_None)
      - ("SEAL", None) → proceed with execution
      - ("ADVISORY", None) → proceed (kernel noted the call)
      - ("HOLD", dict) → blocked, return dict as JSON error response
      - ("VOID", dict) → rejected, return dict as JSON error response

    Applied after RT-3 guard (which checks ack_irreversible).

    fail_closed=True: If kernel unreachable or session unbound → HOLD
    fail_closed=False: Allow pass-through (for C1 advisory tools)
    """
    risk_tier = GEOX_RISK_MAP.get(tool_name, RiskTier.C1_ADVISORY)

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
        kernel_result = _call_arif_kernel("arif_judge_deliberate", judge_params)
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

    kernel_result = _call_arif_kernel("arif_judge_deliberate", judge_params)

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
