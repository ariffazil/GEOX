"""
geox_claim — Unified Claim Lifecycle (Phase 2)
═══════════════════════════════════════════════
Absorbs: geox_claim_create, geox_claim_validate, geox_claim_challenge,
         geox_claim_seal, geox_evidence_attach

Modes: create, validate, challenge, seal, attach_evidence

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations
from typing import Any, Literal

async def geox_claim(
    mode: Literal["create", "validate", "challenge", "seal", "attach_evidence"] = "create",
    claim_id: str = "",
    challenge_text: str = "",
    alternative_claim_text: str = "",
    alternative_evidence_ids: list[str] | None = None,
    challenge_evidence_ids: list[str] | None = None,
    alternative_uncertainty: dict[str, Any] | None = None,
    challenger_provenance: str = "GEOX Claim Engine",
    ack_irreversible: bool = False,
    seal_verdict: str = "SEAL",
    evidence_id: str = "",
    evidence_type: str = "supporting",
    provenance: str = "GEOX Claim Engine",
    claim_text: str = "",
    claim_type: str = "other",
    truth_class: str = "INTERPRETATION",
    evidence_ids: list[str] | None = None,
    uncertainty_p10: float | None = None,
    uncertainty_p50: float | None = None,
    uncertainty_p90: float | None = None,
    uncertainty_distribution: str = "lognormal",
    alternatives: list[dict[str, Any]] | None = None,
    authority: str = "GEOX_CLAIM_WORKER",
    voxel_state: dict[str, Any] | None = None,  # H3 fix: required for seal mode
) -> dict[str, Any]:
    """Unified claim lifecycle — DRAFT → VALIDATED → SEALED.

    Modes:
      create          - Create a structured interpretation claim
      validate        - Validate claim against 16-field earth_memory_envelope
      challenge       - Challenge existing claim with alternative interpretation
      seal            - Submit validated claim to arifOS for VAULT999 sealing
                       (H3 fix: requires voxel_state for well_constrained check)
      attach_evidence - Attach evidence artifact to existing claim
    """
    kwargs = locals().copy()
    if mode == "validate":
        from geox_mcp.tools.claims import geox_claim_validate as _impl
        return await _impl(claim_id=kwargs.get("claim_id", ""))

    if mode == "challenge":
        from geox_mcp.tools.claims import geox_claim_challenge as _impl
        return await _impl(
            claim_id=kwargs.get("claim_id", ""),
            challenge_text=kwargs.get("challenge_text", ""),
            alternative_claim_text=kwargs.get("alternative_claim_text", ""),
            alternative_evidence_ids=kwargs.get("alternative_evidence_ids", []),
            challenge_evidence_ids=kwargs.get("challenge_evidence_ids"),
            alternative_uncertainty=kwargs.get("alternative_uncertainty"),
            challenger_provenance=kwargs.get("challenger_provenance", "GEOX Claim Engine"),
        )

    if mode == "seal":
        # ── H3 fix (2026-06-22): F2 TRUTH at system level ────────────────────
        # Per ADR-008, well_constrained check (obs_count >= 3 AND residual < 0.3)
        # is the system-level gate before any seal. Caller must pass `voxel_state`
        # dict with `observation_count` and `forward_model_residual` fields.
        voxel_state = kwargs.get("voxel_state")
        if not voxel_state:
            return {
                "status": "HOLD",
                "governance_status": "HOLD",
                "error_code": "F2_TRUTH_VOXEL_REQUIRED",
                "message": (
                    "Seal requires a voxel_state dict with observation_count and "
                    "forward_model_residual fields. Per ADR-008, well_constrained "
                    "check (obs_count >= 3 AND residual < 0.3) is the system-level "
                    "F2 TRUTH gate. Provide voxel_state to proceed."
                ),
                "floor": "F2_TRUTH",
                "guard": "RT3",
                "claim_id": kwargs.get("claim_id", ""),
                "required_action": "Pass voxel_state={observation_count: int, forward_model_residual: float, ...} to geox_claim(mode='seal').",
            }

        obs_count = int(voxel_state.get("observation_count", 0))
        residual = float(voxel_state.get("forward_model_residual", 1.0))
        well_constrained = (obs_count >= 3) and (residual < 0.3)

        if not well_constrained:
            return {
                "status": "HOLD",
                "governance_status": "HOLD",
                "error_code": "F2_TRUTH_NOT_WELL_CONSTRAINED",
                "message": (
                    f"Voxel is not well_constrained. "
                    f"observation_count={obs_count} (need >= 3), "
                    f"forward_model_residual={residual:.4f} (need < 0.3). "
                    f"Per ADR-008, this seal is held until the underlying voxel "
                    f"is sufficiently constrained by observations and forward-model fit."
                ),
                "floor": "F2_TRUTH",
                "guard": "RT3",
                "claim_id": kwargs.get("claim_id", ""),
                "well_constrained": False,
                "observation_count": obs_count,
                "forward_model_residual": residual,
                "required_action": (
                    "Either (a) gather more observations to bring obs_count >= 3, "
                    "or (b) improve forward-model fit to bring residual < 0.3, "
                    "then retry seal."
                ),
            }

        # well_constrained=True → proceed to underlying seal implementation
        from geox_mcp.tools.claims import geox_claim_seal as _impl
        result = await _impl(
            claim_id=kwargs.get("claim_id", ""),
            ack_irreversible=kwargs.get("ack_irreversible", False),
            seal_verdict=kwargs.get("seal_verdict", "SEAL"),
        )
        # Annotate the result with the well_constrained proof (F11 AUDIT)
        if isinstance(result, dict):
            result["well_constrained_check"] = {
                "observation_count": obs_count,
                "forward_model_residual": residual,
                "well_constrained": True,
                "floor_enforced": "F2_TRUTH",
                "adr_reference": "ADR-008",
            }
        return result

    if mode == "attach_evidence":
        from geox_mcp.tools.claims import geox_evidence_attach as _impl
        return await _impl(
            claim_id=kwargs.get("claim_id", ""),
            evidence_id=kwargs.get("evidence_id", ""),
            evidence_type=kwargs.get("evidence_type", "supporting"),
            provenance=kwargs.get("provenance", "GEOX Claim Engine"),
        )

    # Default: create
    from geox_mcp.tools.claims import geox_claim_create as _impl
    return await _impl(
        claim_text=kwargs.get("claim_text", ""),
        claim_type=kwargs.get("claim_type", "other"),
        truth_class=kwargs.get("truth_class", "INTERPRETATION"),
        evidence_ids=kwargs.get("evidence_ids", []),
        uncertainty_p10=kwargs.get("uncertainty_p10"),
        uncertainty_p50=kwargs.get("uncertainty_p50"),
        uncertainty_p90=kwargs.get("uncertainty_p90"),
        uncertainty_distribution=kwargs.get("uncertainty_distribution", "lognormal"),
        alternatives=kwargs.get("alternatives"),
        provenance=kwargs.get("provenance", "GEOX Claim Engine"),
        authority=kwargs.get("authority", "GEOX_CLAIM_WORKER"),
    )
