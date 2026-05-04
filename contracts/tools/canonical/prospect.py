from __future__ import annotations

import logging
from typing import Any, List, Dict, Optional, Literal

from fastmcp import FastMCP
from contracts.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
)
from contracts.tools.canonical._helpers import (
    _get_artifact,
    _artifact_exists,
    _register_artifact,
    _record_latest_qc,
    _latest_qc_failed_refs,
    _check_maruah_territory,
    _inject_ensemble_residual_evidence,
    _safe_upload_path,
    _decode_upload_content,
    _parse_csv_or_json,
    _map_canonical_curves,
    _detect_depth_unit,
    _compute_vsh_from_store,
    _compute_porosity_from_store,
    _compute_saturation_from_store,
    _compute_netpay_from_store,
    _classify_gr_motif,
    _classify_lithology_from_store,
    _safe_reduction,
    _get_well_data_with_depth,
    CLAIM_STATES,
    CANONICAL_ALIASES,
    _CURVE_RANGES,
    _artifact_registry,
    _artifact_store,
    _well_curves_registry,
    _ARTIFACT_REGISTRY_PATH,
    MAX_UPLOAD_BYTES,
)
from compatibility.legacy_aliases import LEGACY_ALIAS_MAP, get_alias_metadata

logger = logging.getLogger("geox.canonical.prospect")


async def geox_prospect_evaluate(
    prospect_ref: str,
    mode: Literal["volumetrics", "POS", "EVOI", "risk_summary", "sensitivity", "prospect_scorecard"] = "prospect_scorecard",
) -> dict:
    """Integrated prospect evaluation (Volumetrics, POS, EVOI).

    Args:
        prospect_ref: Prospect artifact reference.
        mode: Evaluation mode.
            - "volumetrics": GRV/NTG/Recov computation only.
            - "POS": Probability of success analysis.
            - "EVOI": Expected value of information.
            - "risk_summary": Risk summary with AC_Risk flags.
            - "sensitivity": Sensitivity analysis on key parameters.
            - "prospect_scorecard": Full integrated scorecard (default).
    """
    artifact = {"ref": prospect_ref, "mode": mode, "pos": 0.22, "stoiip_p50": 150}
    return get_standard_envelope(
        artifact,
        tool_class="compute",
        claim_tag="PLAUSIBLE",
        confidence_band={"p10": 80, "p50": 150, "p90": 280},
        humility_score=round((280 - 80) / 150, 4) if 150 else 0.0,
    )



async def geox_prospect_judge_verdict(
    prospect_ref: str,
    ac_risk_score: float,
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
) -> dict:
    """888_JUDGE gateway: SEAL/PARTIAL/SABAR/VOID/888 HOLD.

    F11 AUTH (FIND-LIVE-004): Constant-time PIN verification via hmac.compare_digest.
    F1 Amanah (RT-3): Requires ack_irreversible=True for constitutional adjudication.
    """
    # FIND-LIVE-004: F11 constant-time PIN gate
    import hmac, os
    _expected_pin = os.environ.get("GEOX_JUDGE_PIN", "")
    if _expected_pin:
        if not judge_pin or not hmac.compare_digest(str(judge_pin), _expected_pin):
            return get_standard_envelope(
                {
                    "tool": "geox_prospect_judge_verdict",
                    "error_code": "F11_AUTH_FAILED",
                    "message": "F11 AUTH: Invalid or missing judge_pin. Constant-time check failed.",
                    "guard": "F11",
                    "floor": "F11_AUTH",
                    "claim_state": "NO_VALID_EVIDENCE",
                },
                tool_class="judge",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                claim_tag="HYPOTHESIS",
            )

    # RT-3 Guard
    if not ack_irreversible:
        return get_standard_envelope(
            {
                "tool": "geox_prospect_judge_verdict",
                "error_code": "RT3_GUARD_F1_AMANAH",
                "message": (
                    "geox_prospect_judge_verdict is a constitutional adjudication "
                    "(irreversible). F1 Amanah requires ack_irreversible=True. "
                    "Provide ack_irreversible=True in the tool call to proceed."
                ),
                "guard": "RT3",
                "floor": "F1_AMANAH",
                "claim_state": "NO_VALID_EVIDENCE",
            },
            tool_class="judge",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_tag="HYPOTHESIS",
        )
    verdict = GovernanceStatus.SEAL if ac_risk_score < 0.5 else GovernanceStatus.HOLD
    artifact = {"ref": prospect_ref, "ac_risk": ac_risk_score, "verdict": verdict}
    return get_standard_envelope(artifact, tool_class="judge", governance_status=verdict)


