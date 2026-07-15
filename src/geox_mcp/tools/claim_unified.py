"""
geox_claim — Unified Claim Lifecycle (Phase 2.5)
═══════════════════════════════════════════════════
Absorbs: geox_claim_create, geox_claim_validate, geox_claim_challenge,
         geox_claim_seal, geox_evidence_attach

Modes: create, validate, challenge, seal, attach_evidence

Added Phase 2.5:
  - epistemic_label (OBS/DER/INT/SPEC) — arifOS standard epistemic tag
  - forbidden_uses — list of prohibited applications for the claim
  - source_citation — literature provenance {url, title, authors, publication}
  - category — literature taxonomy (reservoir, stratigraphy, source, etc.)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations
from typing import Any, Literal

# ── Epistemic label type (arifOS standard) ──────────────────────────────────
EpistemicLabel = Literal["OBS", "DER", "INT", "SPEC"]

# ── Literature category taxonomy ────────────────────────────────────────────
LitCategory = Literal[
    "reservoir",
    "stratigraphy",
    "source",
    "structure",
    "seal",
    "charge",
    "trap",
    "thermal",
    "pressure",
    "seismic",
    "geochemistry",
    "petrophysics",
    "general",
]


async def geox_claim(
    mode: Literal["create", "validate", "challenge", "seal", "attach_evidence"] = "create",
    # ── Core claim fields ───────────────────────────────────────────────────
    claim_id: str = "",
    claim_text: str = "",
    claim_type: str = "other",
    truth_class: str = "INTERPRETATION",
    evidence_ids: list[str] | None = None,
    uncertainty_p10: float | None = None,
    uncertainty_p50: float | None = None,
    uncertainty_p90: float | None = None,
    uncertainty_distribution: str = "lognormal",
    alternatives: list[dict[str, Any]] | None = None,
    provenance: str = "GEOX Claim Engine",
    authority: str = "GEOX_CLAIM_WORKER",
    # ── Challenge fields ────────────────────────────────────────────────────
    challenge_text: str = "",
    alternative_claim_text: str = "",
    alternative_evidence_ids: list[str] | None = None,
    challenge_evidence_ids: list[str] | None = None,
    alternative_uncertainty: dict[str, Any] | None = None,
    challenger_provenance: str = "GEOX Claim Engine",
    # ── Seal fields ─────────────────────────────────────────────────────────
    ack_irreversible: bool = False,
    seal_verdict: str = "SEAL",
    voxel_state: dict[str, Any] | None = None,  # H3 fix: required for seal mode
    # ── Evidence fields ─────────────────────────────────────────────────────
    evidence_id: str = "",
    evidence_type: str = "supporting",
    # ── Literature-to-claims extraction fields (Phase 2.5) ──────────────────
    epistemic_label: EpistemicLabel | None = None,
    forbidden_uses: list[str] | None = None,
    source_citation: dict[str, Any] | None = None,
    category: LitCategory | None = None,
    # ── F11/F3 Identity propagation fields ──────────────────────────────────
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Unified claim lifecycle — DRAFT → VALIDATED → SEALED.

    Modes:
      create          - Create a structured interpretation claim
      validate        - Validate claim against 16-field earth_memory_envelope
      challenge       - Challenge existing claim with alternative interpretation
      seal            - Submit validated claim to arifOS for VAULT999 sealing
                       (H3 fix: requires voxel_state for well_constrained check)
      attach_evidence - Attach evidence artifact to existing claim

    Phase 2.5 literature extraction fields (mode=create):
      epistemic_label  — OBS (observed) / DER (derived) / INT (interpreted) / SPEC (speculation)
      forbidden_uses   — List of prohibited applications (e.g. "no site-specific drilling decisions")
      source_citation  — Literature provenance: {url, title, authors, publication}
      category         — Literature taxonomy: reservoir, stratigraphy, source, structure, etc.
    """
    # ── Seal mode: F2 TRUTH gate (H3 fix, ADR-008) ─────────────────────────
    if mode == "seal":
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
                "claim_id": claim_id,
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
                "claim_id": claim_id,
                "well_constrained": False,
                "observation_count": obs_count,
                "forward_model_residual": residual,
                "required_action": (
                    "Either (a) gather more observations to bring obs_count >= 3, "
                    "or (b) improve forward-model fit to bring residual < 0.3, "
                    "then retry seal."
                ),
            }

        from geox_mcp.tools.claims import geox_claim_seal as _impl

        result = await _impl(
            claim_id=claim_id,
            ack_irreversible=ack_irreversible,
            seal_verdict=seal_verdict,
            session_id=session_id,
            actor_id=actor_id,
        )
        if isinstance(result, dict):
            result["well_constrained_check"] = {
                "observation_count": obs_count,
                "forward_model_residual": residual,
                "well_constrained": True,
                "floor_enforced": "F2_TRUTH",
                "adr_reference": "ADR-008",
            }
            result.setdefault("session_id", session_id or "geox-session")
            result.setdefault("actor_id", actor_id or authority or "geox-governed")
        return result

    # ── Validate mode ───────────────────────────────────────────────────────
    if mode == "validate":
        from geox_mcp.tools.claims import geox_claim_validate as _impl

        result = await _impl(claim_id=claim_id, session_id=session_id, actor_id=actor_id)
        if isinstance(result, dict):
            result.setdefault("session_id", session_id or "geox-session")
            result.setdefault("actor_id", actor_id or authority or "geox-governed")
        return result

    # ── Challenge mode ──────────────────────────────────────────────────────
    if mode == "challenge":
        from geox_mcp.tools.claims import geox_claim_challenge as _impl

        result = await _impl(
            claim_id=claim_id,
            challenge_text=challenge_text,
            alternative_claim_text=alternative_claim_text,
            alternative_evidence_ids=alternative_evidence_ids or [],
            challenge_evidence_ids=challenge_evidence_ids,
            alternative_uncertainty=alternative_uncertainty,
            challenger_provenance=challenger_provenance,
            session_id=session_id,
            actor_id=actor_id,
        )
        if isinstance(result, dict):
            result.setdefault("session_id", session_id or "geox-session")
            result.setdefault("actor_id", actor_id or authority or "geox-governed")
        return result

    # ── Attach evidence mode ────────────────────────────────────────────────
    if mode == "attach_evidence":
        from geox_mcp.tools.claims import geox_evidence_attach as _impl

        result = await _impl(
            claim_id=claim_id,
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            provenance=provenance,
            session_id=session_id,
            actor_id=actor_id,
        )
        if isinstance(result, dict):
            result.setdefault("session_id", session_id or "geox-session")
            result.setdefault("actor_id", actor_id or authority or "geox-governed")
        return result

    # ── Default: Create mode ────────────────────────────────────────────────
    # Build extra_metadata from literature-to-claims extraction fields
    lit_metadata: dict[str, Any] = {}
    if epistemic_label is not None:
        lit_metadata["epistemic_label"] = epistemic_label
    if forbidden_uses is not None:
        lit_metadata["forbidden_uses"] = forbidden_uses
    if source_citation is not None:
        lit_metadata["source_citation"] = source_citation
    if category is not None:
        lit_metadata["category"] = category

    from geox_mcp.tools.claims import geox_claim_create as _impl

    result = await _impl(
        claim_text=claim_text,
        claim_type=claim_type,
        truth_class=truth_class,
        evidence_ids=evidence_ids or [],
        uncertainty_p10=uncertainty_p10,
        uncertainty_p50=uncertainty_p50,
        uncertainty_p90=uncertainty_p90,
        uncertainty_distribution=uncertainty_distribution,
        alternatives=alternatives,
        provenance=provenance,
        authority=authority,
        extra_metadata=lit_metadata or None,
        session_id=session_id,
        actor_id=actor_id,
    )
    if isinstance(result, dict):
        result.setdefault("session_id", session_id or "geox-session")
        result.setdefault("actor_id", actor_id or authority or "geox-governed")
    return result
