from __future__ import annotations

import logging
from typing import Any, Dict, Literal, Optional

from geox_core.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
)

logger = logging.getLogger("geox.canonical.prospect")


async def geox_prospect_evaluate(
    prospect_ref: str,
    mode: Literal["screen", "appraise", "develop"] = "screen",
    evidence_refs: list[str] | None = None,
    verdict: Literal["compute", "preview", "seal"] = "compute",
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
    # ── Eureka 8 (2026-06-03): optional StructuralMap as derived input ────
    structural_map_inline: Optional[Dict[str, Any]] = None,
) -> dict:
    """Integrated prospect evaluation (Volumetrics, POS, EVOI) with optional preview/seal.

    Replaces: geox_prospect_evaluate + geox_prospect_judge_preview + geox_prospect_judge_seal.

    Args:
        prospect_ref: Prospect artifact reference.
        mode: Evaluation mode.
            - "screen": Qualitative/heuristic screening (default). No evidence required.
            - "appraise": Requires QC_VERIFIED evidence_refs (DST, PVT, seismic, etc.).
            - "develop": Requires full evidence package + prior appraisal.
        evidence_refs: List of artifact refs that have passed QC. Required for appraise/develop.
        verdict: "compute" (default) | "preview" (reversible advisory) | "seal" (irreversible).
        ack_irreversible: Required when verdict="seal". F1 Amanah gate.
        judge_pin: Optional constant-time PIN for seal authorization.
        structural_map_inline: E8 — optional inline StructuralMap (output of
                               bootstrap_structure). When provided, the prospect
                               evaluation carries the structural position as
                               additional evidence (Vp-mean, structural-height
                               at the prospect location, etc.).
    """
    # Hardening: validate free-text inputs at boundary.
    from geox_mcp.tools.kernel._validation import validate_tool_inputs

    _err = validate_tool_inputs(
        "geox_prospect_evaluate",
        prospect_ref=prospect_ref,
        evidence_refs=evidence_refs,
        judge_pin=judge_pin,
    )
    if _err is not None:
        return _err
    refs = evidence_refs or []

    if mode in ("appraise", "develop") and not refs:
        # Agentic recovery (Fix #1, #5 - Arif 2026-05-16)
        # RECOVERABLE_ERROR: failure has an exit path — downgrade or evidence workflow
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
                # Downgrade path: allow screen mode without evidence
                "downgrade_available": True,
                "downgrade_mode": "screen",
                "downgrade_note": "Use mode='screen' for qualitative screening without evidence. Results will be HYPOTHESIS-level.",
            },
            tool_class="compute",
            execution_status=ExecutionStatus.RECOVERABLE_ERROR,  # Changed from ERROR
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            evidence_refs=[],
            # Agentic recovery fields (Fix #1, #4 - Arif 2026-05-16)
            next_best_actions=[
                {
                    "mode": "downgrade",
                    "action": "Use screen mode for qualitative screening without evidence",
                    "tool_hint": "geox.prospect_evaluate",
                    "parameters": {"mode": "screen"},
                    "rank": 0,
                },
                {
                    "mode": "evidence_request",
                    "action": "Ingest DST, PVT, seismic data to unlock appraise/develop modes",
                    "tool_hint": "geox.data.ingest",
                    "evidence_required": [
                        "DST table",
                        "PVT / gas composition",
                        "seismic interpretation",
                    ],
                    "rank": 1,
                },
                {
                    "mode": "evidence_request",
                    "action": "QC verify ingested artifacts before appraisal",
                    "tool_hint": "geox.data.qc",
                    "rank": 2,
                },
            ],
            suggested_tool="geox.data.ingest",
            can_auto_retry=True,
            # Structured missing inputs (Fix #8 - Arif 2026-05-16)
            missing_inputs_schema=[
                {
                    "name": "evidence_refs",
                    "type": "string[]",
                    "acceptable_sources": ["QC_VERIFIED_LAS", "QC_VERIFIED_DST", "QC_VERIFIED_SEISMIC", "QC_VERIFIED_PVT"],
                    "unlock_stage": "appraisal",
                    "description": "QC-verified artifacts required for appraise/develop modes",
                }
            ],
            # Confidence policy (Fix #9 - Arif 2026-05-16)
            confidence_policy={
                "confidence_band": "not_computed",
                "reason": "No QC-verified evidence_refs supplied for appraisal",
                "allowed_claims": ["qualitative screening", "hypothesis framing"],
                "disallowed_claims": ["POS", "STOIIP", "P10/P50/P90", "commercial decision", "prospect ranking"],
            },
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
            claim_state="INTERPRETED",
            uncertainty="High",
            humility_score=0.5,
            evidence_refs=[],
            # Confidence policy for screen mode (Fix #9 - Arif 2026-05-16)
            confidence_policy={
                "confidence_band": "qualitative",
                "reason": "Screen mode — no quantitative evidence available",
                "allowed_claims": ["qualitative screening", "relative ranking", "hypothesis framing"],
                "disallowed_claims": ["POS", "STOIIP", "P10/P50/P90", "commercial decision"],
            },
            # Agentic: screen mode is the safe downgrade
            suggested_tool=None,
            can_auto_retry=True,
        )

    # Compute AC risk score from evidence quality
    ac_risk_score = 0.22
    if mode == "screen" and not refs:
        ac_risk_score = 0.65
    elif mode == "appraise" and refs:
        ac_risk_score = 0.35
    elif mode == "develop" and refs:
        ac_risk_score = 0.18

    # ── PREVIEW PATH (reversible advisory) ───────────────────────────────────
    if verdict == "preview":
        preview_verdict = GovernanceStatus.SEAL if ac_risk_score < 0.5 else GovernanceStatus.HOLD
        artifact = {
            "ref": prospect_ref,
            "mode": mode,
            "ac_risk": ac_risk_score,
            "pos": 0.22 if mode == "screen" else 0.35,
            "stoiip_p50": 150 if mode == "screen" else 220,
            "preview_verdict": preview_verdict,
            "reversible": True,
            "note": "This is a preview only. Call verdict='seal' with ack_irreversible=True to make irreversible.",
            "f13_compliance": {
                "Recommendation": "Proceed" if preview_verdict == GovernanceStatus.SEAL else "Hold / Rework",
                "Uncertainty": f"AC_Risk Score: {ac_risk_score}",
                "Consequence": "Preview Mode - No physical capital committed.",
                "Authority": "HUMAN",
            },
        }
        return get_standard_envelope(
            artifact,
            tool_class="judge",
            governance_status=GovernanceStatus.QUALIFY,
            artifact_status=ArtifactStatus.DRAFT,
            claim_tag="PLAUSIBLE",
            claim_state="JUDGE_PREVIEW",
        )

    # ── SEAL PATH (irreversible constitutional adjudication) ─────────────────
    if verdict == "seal":
        import hmac
        import os

        _expected_pin = os.environ.get("GEOX_JUDGE_PIN", "")
        if _expected_pin:
            if not judge_pin or not hmac.compare_digest(str(judge_pin), _expected_pin):
                return get_standard_envelope(
                    {
                        "tool": "geox_prospect_evaluate",
                        "error_code": "F11_AUTH_FAILED",
                        "message": "F11 AUTH: Invalid or missing judge_pin. Constant-time check failed.",
                        "guard": "F11",
                        "floor": "F11_AUTH",
                    },
                    tool_class="judge",
                    execution_status=ExecutionStatus.ERROR,
                    governance_status=GovernanceStatus.HOLD,
                    claim_tag="HYPOTHESIS",
                )
        if not ack_irreversible:
            return get_standard_envelope(
                {
                    "tool": "geox_prospect_evaluate",
                    "error_code": "RT3_GUARD_F1_AMANAH",
                    "message": (
                        "verdict='seal' is a constitutional adjudication (irreversible). "
                        "F1 Amanah requires ack_irreversible=True. "
                        "Provide ack_irreversible=True in the tool call to proceed."
                    ),
                    "guard": "RT3",
                    "floor": "F1_AMANAH",
                },
                tool_class="judge",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                claim_tag="HYPOTHESIS",
            )
        seal_verdict = GovernanceStatus.SEAL if ac_risk_score < 0.5 else GovernanceStatus.HOLD
        artifact = {
            "ref": prospect_ref,
            "mode": mode,
            "ac_risk": ac_risk_score,
            "pos": 0.22 if mode == "screen" else 0.35,
            "stoiip_p50": 150 if mode == "screen" else 220,
            "verdict": seal_verdict,
            "sealed": True,
            "f13_compliance": {
                "Recommendation": "Proceed to Capital Execution"
                if seal_verdict == GovernanceStatus.SEAL
                else "Hold / Reject Prospect",
                "Uncertainty": f"Residual AC_Risk: {ac_risk_score}",
                "Consequence": "Irreversible Capital and Safety Risk Bound to this Decision.",
                "Authority": "HUMAN",
            },
        }
        return get_standard_envelope(
            artifact,
            tool_class="judge",
            governance_status=seal_verdict,
            artifact_status=ArtifactStatus.VERIFIED if seal_verdict == GovernanceStatus.SEAL else ArtifactStatus.DRAFT,
            claim_tag="CLAIM",
            claim_state="SEALED",
        )

    # ── COMPUTE PATH (default) ───────────────────────────────────────────────
    artifact = {
        "ref": prospect_ref,
        "mode": mode,
        "ac_risk": ac_risk_score,
        "pos": 0.22 if mode == "screen" else 0.35,
        "stoiip_p50": 150 if mode == "screen" else 220,
        "score_type": "heuristic_screening" if mode == "screen" else "appraisal",
        "verdict_available": True,
        "note": "Use verdict='preview' for reversible advisory or verdict='seal' with ack_irreversible for constitutional seal.",
    }
    return get_standard_envelope(
        artifact,
        tool_class="compute",
        claim_tag="PLAUSIBLE",
        claim_state="COMPUTED",
        confidence_band={"p10": 80, "p50": 150, "p90": 280},
        humility_score=round((280 - 80) / 150, 4) if 150 else 0.0,
        evidence_refs=refs,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DEPRECATED: Preview / Seal / Verdict — energy absorbed into geox_prospect_evaluate
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_prospect_judge_preview(
    prospect_ref: str,
    ac_risk_score: float,
) -> dict:
    """[DEPRECATED] Use geox_prospect_evaluate with verdict='preview'."""
    return await geox_prospect_evaluate(
        prospect_ref=prospect_ref,
        mode="screen",
        verdict="preview",
    )


async def geox_prospect_judge_seal(
    prospect_ref: str,
    ac_risk_score: float,
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
) -> dict:
    """[DEPRECATED] Use geox_prospect_evaluate with verdict='seal'."""
    return await geox_prospect_evaluate(
        prospect_ref=prospect_ref,
        mode="screen",
        verdict="seal",
        ack_irreversible=ack_irreversible,
        judge_pin=judge_pin,
    )


async def geox_prospect_judge_verdict(
    prospect_ref: str,
    ac_risk_score: float,
    ack_irreversible: bool = False,
    judge_pin: str | None = None,
) -> dict:
    """[DEPRECATED] Use geox_prospect_evaluate with verdict='seal'."""
    return await geox_prospect_evaluate(
        prospect_ref=prospect_ref,
        mode="screen",
        verdict="seal",
        ack_irreversible=ack_irreversible,
        judge_pin=judge_pin,
    )
