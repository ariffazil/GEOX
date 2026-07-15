from __future__ import annotations

"""
GEOX Argument Sidecar — Every Map Must Be an Argument
═══════════════════════════════════════════════════════════════════════════════

The missing Eureka: GEOX is not a map renderer. GEOX is a geological
argument engine. Every exported map must carry:
  - at least one claim
  - one evidence reference
  - one uncertainty band
  - one rival interpretation

This schema enforces that law.

schema_name:    ArgumentSidecar
schema_version:  argument.v1
source:          Arif Eureka directive 2026-07-01
organ:           GEOX

Governing law:
  No GEOX map may be exported unless every interpreted layer has
  at least one claim, one evidence reference, one uncertainty band,
  and one rival interpretation.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# ENUMS
# ──────────────────────────────────────────────────────────────────────────────


class TruthClass(str, Enum):
    """How grounded is this claim in physical reality?"""

    FACT = "FACT"  # Directly observed, sensor-level
    INTERPRETATION = "INTERPRETATION"  # Derived from multiple observations
    HYPOTHESIS = "HYPOTHESIS"  # Proposed but not yet tested
    SPECULATION = "SPECULATION"  # Low-evidence, high-uncertainty
    SCENARIO = "SCENARIO"  # What-if model, not a truth claim


class ChallengeType(str, Enum):
    """What kind of rival interpretation is this?"""

    GEOPHYSICAL_ARTIFACT = "geophysical_artifact"  # Velocity, migration, acquisition artifact
    STRATIGRAPHIC_ALTERNATIVE = "stratigraphic_alternative"  # Different depositional model
    STRUCTURAL_ALTERNATIVE = "structural_alternative"  # Different fault/fold model
    CHARGE_TIMING = "charge_timing"  # Different migration/charge story
    SEAL_INTEGRITY = "seal_integrity"  # Alternative seal risk
    RESERVOIR_PRESENCE = "reservoir_presence"  # Alternative reservoir model
    DIAGENETIC = "diagenetic"  # Post-depositional alteration risk
    ECONOMIC_ALTERNATIVE = "economic_alternative"  # Different commercial viability
    DATA_QUALITY = "data_quality"  # Input data may be unreliable
    ANALOGUE_MISMATCH = "analogue_mismatch"  # Wrong analogue selected


class ReviewState(str, Enum):
    """Where is this argument in the review pipeline?"""

    DRAFT = "draft"  # Initial argument, not reviewed
    VALIDATED_NOT_SEALED = "validated_not_sealed"  # Reviewed but not final
    CHALLENGED = "challenged"  # Rival has not been resolved
    SEALED = "sealed"  # Irreversibly committed to VAULT999
    VOID = "void"  # Rejected or superseded


# ──────────────────────────────────────────────────────────────────────────────
# CLAIM
# ──────────────────────────────────────────────────────────────────────────────


class GeologicalClaim(BaseModel):
    """A single falsifiable geological assertion.

    Every claim must be:
    - Falsifiable (can be proven wrong)
    - Grounded (has evidence)
    - Uncertain (has honest bounds)
    - Challenged (has at least one rival)
    """

    claim_id: str = Field(
        default_factory=lambda: f"claim-{uuid4().hex[:8]}",
        description="Unique claim identifier",
    )
    claim_text: str = Field(
        description="The geological assertion in plain language",
    )
    truth_class: TruthClass = Field(
        default=TruthClass.INTERPRETATION,
        description="How grounded is this claim",
    )
    layer_id: str = Field(
        default="",
        description="Which map layer this claim is about",
    )
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="References to supporting evidence (wells, seismic, publications)",
    )
    epistemic_label: str = Field(
        default="INT",
        description="OBS | DER | INT | SPEC",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=0.90,  # F7 HUMILITY cap
        description="Confidence in this claim (0-0.90)",
    )
    falsification_test: str = Field(
        default="",
        description="What evidence would prove this claim wrong?",
    )


# ──────────────────────────────────────────────────────────────────────────────
# RIVAL INTERPRETATION
# ──────────────────────────────────────────────────────────────────────────────


class RivalInterpretation(BaseModel):
    """A competing interpretation that could defeat the primary claim.

    GEOX forces rivals before any map becomes trusted.
    """

    rival_id: str = Field(
        default_factory=lambda: f"rival-{uuid4().hex[:8]}",
        description="Unique rival identifier",
    )
    claim_text: str = Field(
        description="The rival geological assertion",
    )
    challenge_type: ChallengeType = Field(
        description="What kind of challenge this is",
    )
    evidence_needed: list[str] = Field(
        default_factory=list,
        description="What evidence would confirm or deny this rival",
    )
    probability: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Estimated probability this rival is correct",
    )
    status: str = Field(
        default="unresolved",
        description="unresolved | supported | refuted | partially_supported",
    )


# ──────────────────────────────────────────────────────────────────────────────
# UNCERTAINTY BAND
# ──────────────────────────────────────────────────────────────────────────────


class UncertaintyBand(BaseModel):
    """Honest uncertainty for a geological claim.

    Not decoration — a blocking gate.
    """

    p10: str = Field(
        default="",
        description="Low estimate / pessimistic case in plain language",
    )
    p50: str = Field(
        default="",
        description="Most likely case",
    )
    p90: str = Field(
        default="",
        description="High estimate / optimistic case",
    )
    dominant_source: str = Field(
        default="unknown",
        description="What contributes most to uncertainty: data | model | assumption | scale",
    )
    major_unknowns: list[str] = Field(
        default_factory=list,
        description="Key variables that are unconstrained",
    )
    blocks_export: bool = Field(
        default=False,
        description="Does this uncertainty block map export?",
    )


# ──────────────────────────────────────────────────────────────────────────────
# ARGUMENT SIDECAR — The full geological argument
# ──────────────────────────────────────────────────────────────────────────────


class ArgumentSidecar(BaseModel):
    """The argument sidecar — attached to every GEOX map export.

    Governing law:
      No GEOX map may be exported unless every interpreted layer has
      at least one claim, one evidence reference, one uncertainty band,
      and one rival interpretation.

    This converts GEOX from "Earth renderer" to "Earth reasoning organ."
    """

    sidecar_id: str = Field(
        default_factory=lambda: f"arg-{uuid4().hex[:12]}",
        description="Unique sidecar identifier",
    )
    artifact_id: str = Field(
        description="ID of the map/artifact this sidecar is attached to",
    )
    scene_plan_id: str = Field(
        default="",
        description="Which scene plan produced this argument",
    )

    # ── Primary claims ────────────────────────────────────────────────────
    primary_claims: list[GeologicalClaim] = Field(
        default_factory=list,
        description="What does this map assert? At least one required.",
    )

    # ── Rival interpretations ─────────────────────────────────────────────
    rival_claims: list[RivalInterpretation] = Field(
        default_factory=list,
        description="Competing interpretations. At least one required.",
    )

    # ── Uncertainty ───────────────────────────────────────────────────────
    uncertainty: UncertaintyBand = Field(
        default_factory=UncertaintyBand,
        description="Honest uncertainty. Not decoration — a blocking gate.",
    )

    # ── Review state ──────────────────────────────────────────────────────
    review_state: ReviewState = Field(
        default=ReviewState.DRAFT,
        description="Where is this argument in the review pipeline?",
    )
    f13_required: bool = Field(
        default=True,
        description="Does this argument require F13 SOVEREIGN approval?",
    )
    human_reviewer: str = Field(
        default="",
        description="Who reviewed this argument (empty = not yet reviewed)",
    )
    review_notes: str = Field(
        default="",
        description="Reviewer's notes or qualifications",
    )

    # ── Export gate ───────────────────────────────────────────────────────
    export_permitted: bool = Field(
        default=False,
        description="Can this map be exported? False until all gates pass.",
    )
    export_block_reason: str = Field(
        default="",
        description="Why export is blocked (empty = permitted)",
    )

    # ── Provenance ────────────────────────────────────────────────────────
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )
    created_by: str = Field(
        default="GEOX",
        description="Who created this argument sidecar",
    )
    constitution_hash: str = Field(
        default="",
        description="Constitutional law version",
    )

    model_config = {
        "json_schema_extra": {"description": ("GEOX Argument Sidecar — every map must be an argument. DITEMPA BUKAN DIBERI")}
    }


# ──────────────────────────────────────────────────────────────────────────────
# VALIDATION — Export gate
# ──────────────────────────────────────────────────────────────────────────────


def validate_argument_for_export(sidecar: ArgumentSidecar) -> tuple[bool, list[str]]:
    """Validate that an argument sidecar meets export requirements.

    Governing law:
      No GEOX map may be exported unless every interpreted layer has
      at least one claim, one evidence reference, one uncertainty band,
      and one rival interpretation.

    Returns:
        (permitted, list_of_block_reasons)
    """
    blocks: list[str] = []

    # Must have at least one primary claim
    if not sidecar.primary_claims:
        blocks.append("No primary claims. Every map must assert something.")

    # Every claim must have evidence
    for claim in sidecar.primary_claims:
        if not claim.evidence_refs:
            blocks.append(f"Claim '{claim.claim_text[:60]}...' has no evidence refs.")

    # Must have at least one rival interpretation
    if not sidecar.rival_claims:
        blocks.append("No rival interpretations. Every claim must have at least one challenger.")

    # Must have uncertainty
    if not sidecar.uncertainty.p10 and not sidecar.uncertainty.p50:
        blocks.append("No uncertainty band. Every claim must declare its uncertainty.")

    # Uncertainty blocking check
    if sidecar.uncertainty.blocks_export:
        blocks.append("Uncertainty explicitly blocks export.")

    # Review state check
    if sidecar.review_state == ReviewState.VOID:
        blocks.append("Argument is VOID.")

    return (len(blocks) == 0, blocks)


# ──────────────────────────────────────────────────────────────────────────────
# BUILDER — Quick argument construction
# ──────────────────────────────────────────────────────────────────────────────


def build_argument_sidecar(
    *,
    artifact_id: str,
    primary_claims: list[dict[str, Any]],
    rival_claims: list[dict[str, Any]],
    uncertainty: dict[str, Any] | None = None,
    scene_plan_id: str = "",
    created_by: str = "GEOX",
) -> ArgumentSidecar:
    """Build an ArgumentSidecar with validation.

    Parameters
    ----------
    artifact_id : str
        ID of the map/artifact.
    primary_claims : list[dict]
        List of claim dicts with at least claim_text.
    rival_claims : list[dict]
        List of rival dicts with at least claim_text and challenge_type.
    uncertainty : dict, optional
        Uncertainty band dict.
    scene_plan_id : str, optional
        Scene plan that produced this argument.
    created_by : str
        Who created this argument.

    Returns
    -------
    ArgumentSidecar
        Validated argument sidecar.

    Raises
    ------
    ValueError
        If no claims or no rivals provided.
    """
    if not primary_claims:
        raise ValueError("At least one primary claim is required.")
    if not rival_claims:
        raise ValueError("At least one rival interpretation is required.")

    claims = [GeologicalClaim(**c) for c in primary_claims]
    rivals = [RivalInterpretation(**r) for r in rival_claims]
    unc = UncertaintyBand(**(uncertainty or {}))

    sidecar = ArgumentSidecar(
        artifact_id=artifact_id,
        scene_plan_id=scene_plan_id,
        primary_claims=claims,
        rival_claims=rivals,
        uncertainty=unc,
        created_by=created_by,
    )

    # Auto-validate export permission
    permitted, blocks = validate_argument_for_export(sidecar)
    sidecar.export_permitted = permitted
    sidecar.export_block_reason = "; ".join(blocks) if blocks else ""

    return sidecar
