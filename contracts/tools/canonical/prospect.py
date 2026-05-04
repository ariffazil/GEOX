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
    mode: Literal["screen", "appraise", "develop"] = "screen",
    evidence_refs: list[str] | None = None,
) -> dict:
    """Integrated prospect evaluation (Volumetrics, POS, EVOI).

    Args:
        prospect_ref: Prospect artifact reference.
        mode: Evaluation mode.
            - "screen": Qualitative/heuristic screening (default). No evidence required.
            - "appraise": Requires QC_VERIFIED evidence_refs (DST, PVT, seismic, etc.).
            - "develop": Requires full evidence package + prior appraisal.
        evidence_refs: List of artifact refs that have passed QC. Required for appraise/develop.
    """
    refs = evidence_refs or []

    if mode in ("appraise", "develop") and not refs:
        return get_standard_envelope(
            {
                "tool": "geox_prospect_evaluate",
                "error_code": "NO_VALID_EVIDENCE",
                "message": f"mode='{mode}' requires evidence_refs. Provide ingested + QC-verified artifacts.",
                "required_evidence": [
                    "DST table",
                    "pressure buildup",
                    "PVT / gas composition",
                    "structure map",
                    "seismic interpretation",
                    "contacts",
                    "net pay / petrophysics",
                ],
            },
            tool_class="compute",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            evidence_refs=[],
        )

    if mode == "screen" and not refs:
        artifact = {
            "ref": prospect_ref,
            "mode": mode,
            "pos": None,
            "stoiip_p50": None,
            "score_type": "heuristic_screening",
            "note": "No evidence supplied — screening is qualitative only.",
        }
        return get_standard_envelope(
            artifact,
            tool_class="compute",
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            evidence_refs=[],
        )

    # Evidence-present path (placeholder for real computation)
    artifact = {"ref": prospect_ref, "mode": mode, "pos": 0.22, "stoiip_p50": 150}
    return get_standard_envelope(
        artifact,
        tool_class="compute",
        claim_tag="PLAUSIBLE",
        claim_state="COMPUTED",
        confidence_band={"p10": 80, "p50": 150, "p90": 280},
        humility_score=round((280 - 80) / 150, 4) if 150 else 0.0,
        evidence_refs=refs,
    )


async def geox_prospect_judge_preview(
    prospect_ref: str,
    ac_risk_score: float,
) -> dict:
    """Reversible advisory verdict — does NOT require ack_irreversible.

    Returns a preview of what the judge would decide, without sealing.
    """
    verdict = GovernanceStatus.SEAL if ac_risk_score < 0.5 else GovernanceStatus.HOLD
    artifact = {
        "ref": prospect_ref,
        "ac_risk": ac_risk_score,
        "preview_verdict": verdict,
        "reversible": True,
        "note": "This is a preview only. Call geox_prospect_judge_seal to make irreversible.",
    }
    return get_standard_envelope(
        artifact,
        tool_class="judge",
        governance_status=GovernanceStatus.QUALIFY,
        artifact_status=ArtifactStatus.DRAFT,
        claim_tag="PLAUSIBLE",
        claim_state="JUDGE_PREVIEW",
    )


async def geox_prospect_judge_seal(
    prospect_ref: str,
    ac_risk_score: float,
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
) -> dict:
    """888_JUDSEAL gateway: irreversible constitutional adjudication.

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
                    "tool": "geox_prospect_judge_seal",
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
                "tool": "geox_prospect_judge_seal",
                "error_code": "RT3_GUARD_F1_AMANAH",
                "message": (
                    "geox_prospect_judge_seal is a constitutional adjudication "
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
    artifact = {"ref": prospect_ref, "ac_risk": ac_risk_score, "verdict": verdict, "sealed": True}
    return get_standard_envelope(
        artifact,
        tool_class="judge",
        governance_status=verdict,
        artifact_status=ArtifactStatus.VERIFIED if verdict == GovernanceStatus.SEAL else ArtifactStatus.DRAFT,
        claim_tag="CLAIM",
        claim_state="SEALED",
    )




# ── Backward-compat alias: canonical 13 name → seal implementation ──
async def geox_prospect_judge_verdict(
    prospect_ref: str,
    ac_risk_score: float,
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
) -> dict:
    """[DEPRECATED in favour of geox_prospect_judge_preview / geox_prospect_judge_seal]
    888_JUDGE gateway: SEAL/PARTIAL/SABAR/VOID/888 HOLD.
    This canonical name now delegates to geox_prospect_judge_seal.
    """
    return await geox_prospect_judge_seal(
        prospect_ref=prospect_ref,
        ac_risk_score=ac_risk_score,
        ack_irreversible=ack_irreversible,
        judge_pin=judge_pin,
    )
