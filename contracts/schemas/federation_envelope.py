from __future__ import annotations

"""
Federation Metabolism Spine — Canonical FederationEnvelope
═══════════════════════════════════════════════════════════════════════════════

The blood packet every organ must use to talk to every other organ.

schema_name:    FederationEnvelope
schema_version:  federation.v1
source:          arifOS Federation Metabolism Spine (Arif directive 2026-07-01)
organ:           CROSS-ORGAN — shared by arifOS, AAA, A-FORGE, GEOX, WEALTH, WELL, VAULT999

The loop:
  sense → route → deliberate → execute → measure → seal → learn

Hard rules:
  - No organ may output free-form truth without envelope.
  - No execution may occur without reversibility class.
  - No SEAL may be displayed unless VAULT999/arifOS actually sealed it.
  - No repo may claim sovereignty.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# FEDERATION ENUMS — Shared across all organs
# ──────────────────────────────────────────────────────────────────────────────


class OrganID(str, Enum):
    """Which organ produced or receives this envelope."""

    ARIFOS = "arifOS"
    AAA = "AAA"
    A_FORGE = "A-FORGE"
    GEOX = "GEOX"
    WEALTH = "WEALTH"
    WELL = "WELL"
    VAULT999 = "VAULT999"


class AutonomyBand(str, Enum):
    """What level of autonomous action is permitted for this envelope.

    Maps to the A-R-I-F operating roles and T1/T2/T3 tiers.
    """

    OBSERVE = "OBSERVE"  # Read-only, no side effects
    SUGGEST = "SUGGEST"  # Advisory, no mutation
    SIMULATE = "SIMULATE"  # What-if, no persistence
    DRAFT = "DRAFT"  # Proposed action, not executed
    QUEUE = "QUEUE"  # Ready for execution, awaiting approval
    EXECUTE_REVERSIBLE = "EXECUTE_REVERSIBLE"  # Can be undone
    EXECUTE_HIGH_IMPACT = "EXECUTE_HIGH_IMPACT"  # Significant but reversible
    IRREVERSIBLE = "IRREVERSIBLE"  # Cannot be undone — requires F13


class ReversibilityClass(str, Enum):
    """How reversible is the proposed action?"""

    FULL = "FULL"  # Completely undoable (git revert, delete temp file)
    PARTIAL = "PARTIAL"  # Undoable with effort (deploy rollback, data restore)
    NONE = "NONE"  # Cannot be undone (vault seal, external comms, money)


class RiskClass(str, Enum):
    """Constitutional risk tier for this envelope."""

    LOW = "LOW"  # Standard operations, no floor checks needed
    MEDIUM = "MEDIUM"  # F1 AMANAH + F4 CLARITY
    HIGH = "HIGH"  # F1 + F4 + F7 HUMILITY + F11 AUDIT
    CRITICAL = "CRITICAL"  # All floors + F13 SOVEREIGN required


class ExecutionStatus(str, Enum):
    """Where is this envelope in the metabolic loop?"""

    SENSED = "SENSED"  # Evidence gathered (GEOX/WEALTH/WELL output)
    ROUTED = "ROUTED"  # Intent routed to correct organ (AAA/arifOS)
    DELIBERATING = "DELIBERATING"  # Under constitutional review (arifOS judge)
    APPROVED = "APPROVED"  # Judge returned SEAL
    EXECUTING = "EXECUTING"  # A-FORGE running the action
    MEASURED = "MEASURED"  # Result computed
    SEALED = "SEALED"  # VAULT999 receipt written
    LEARNED = "LEARNED"  # Feedback loop closed
    HOLD = "HOLD"  # Governance pause — requires 888_JUDGE
    VOID = "VOID"  # Rejected or invalidated


class MetabolicPhase(str, Enum):
    """Which phase of the metabolic loop is this envelope in?"""

    SENSE = "sense"
    ROUTE = "route"
    DELIBERATE = "deliberate"
    EXECUTE = "execute"
    MEASURE = "measure"
    SEAL = "seal"
    LEARN = "learn"


# ──────────────────────────────────────────────────────────────────────────────
# EVIDENCE LAYER — What grounds this envelope
# ──────────────────────────────────────────────────────────────────────────────


class EvidenceLayer(BaseModel):
    """Evidence grounding for this envelope.

    Every envelope must declare what evidence it rests on.
    No evidence → the envelope is advisory-only at best.
    """

    evidence_type: str = Field(
        description="Type of evidence: seismic, well_log, petrophysical, financial, biometric, constitutional"
    )
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="References to evidence artifacts (file paths, vault IDs, claim IDs)",
    )
    epistemic_label: str = Field(
        default="OBS",
        description="OBS (observed) | DER (derived) | INT (interpreted) | SPEC (speculation)",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in the evidence (0-1). F7 HUMILITY: cap at 0.90.",
    )
    uncertainty_range: tuple[float, float] = Field(
        default=(0.0, 1.0),
        description="Honest range of confidence",
    )
    major_unknowns: list[str] = Field(
        default_factory=list,
        description="What key variables are unconstrained",
    )
    freshness_utc: str = Field(
        default="",
        description="When this evidence was collected/validated",
    )


# ──────────────────────────────────────────────────────────────────────────────
# FLOOR CHECKS — Constitutional compliance
# ──────────────────────────────────────────────────────────────────────────────


class FloorCheck(BaseModel):
    """A single constitutional floor check result."""

    floor_id: str = Field(description="F1-F13 floor identifier")
    floor_name: str = Field(description="Human-readable floor name")
    passed: bool = Field(default=True)
    reason: str = Field(default="", description="Why it passed or failed")
    evidence: str = Field(default="", description="Evidence supporting the check")


# ──────────────────────────────────────────────────────────────────────────────
# FEDERATION ENVELOPE — The blood packet
# ──────────────────────────────────────────────────────────────────────────────


class FederationEnvelope(BaseModel):
    """
    The canonical federation envelope — the blood packet every organ must use.

    This is the ONE object that flows through the entire metabolic loop:
      sense → route → deliberate → execute → measure → seal → learn

    Every organ wraps its output in this envelope. Every organ reads it
    to understand what came before and what must come next.

    No organ may output free-form truth without this envelope.
    """

    # ── Identity ──────────────────────────────────────────────────────────
    envelope_id: str = Field(
        default_factory=lambda: f"env-{uuid4().hex[:12]}",
        description="Unique envelope identifier",
    )
    trace_id: str = Field(description="End-to-end trace ID — propagates through entire metabolic loop")
    actor_id: str = Field(description="Who initiated this metabolic cycle (human or agent ID)")
    session_id: str | None = Field(
        default=None,
        description="Governed session ID from arifOS session_init",
    )

    # ── Organ routing ─────────────────────────────────────────────────────
    organ_origin: OrganID = Field(description="Which organ produced this envelope")
    organ_target: OrganID | None = Field(
        default=None,
        description="Which organ should receive this next (null = arifOS routes)",
    )
    organ_chain: list[OrganID] = Field(
        default_factory=list,
        description="Which organs have touched this envelope so far",
    )

    # ── Intent ────────────────────────────────────────────────────────────
    intent: str = Field(description="What this metabolic cycle is trying to achieve")
    metabolic_phase: MetabolicPhase = Field(
        default=MetabolicPhase.SENSE,
        description="Which phase of the metabolic loop",
    )

    # ── Evidence ──────────────────────────────────────────────────────────
    evidence_layer: EvidenceLayer = Field(
        default_factory=lambda: EvidenceLayer(evidence_type="unknown"),
        description="What grounds this envelope",
    )

    # ── Governance ────────────────────────────────────────────────────────
    autonomy_band: AutonomyBand = Field(
        default=AutonomyBand.OBSERVE,
        description="What level of autonomous action is permitted",
    )
    reversibility_class: ReversibilityClass = Field(
        default=ReversibilityClass.FULL,
        description="How reversible is the proposed action",
    )
    risk_class: RiskClass = Field(
        default=RiskClass.LOW,
        description="Constitutional risk tier",
    )
    required_floor_checks: list[FloorCheck] = Field(
        default_factory=list,
        description="Constitutional floor checks required and their results",
    )
    f13_required: bool = Field(
        default=False,
        description="Does this envelope require F13 SOVEREIGN approval?",
    )

    # ── Action ────────────────────────────────────────────────────────────
    proposed_action: str = Field(
        default="",
        description="What action is proposed (empty = observation only)",
    )
    execution_status: ExecutionStatus = Field(
        default=ExecutionStatus.SENSED,
        description="Where is this envelope in the metabolic loop",
    )

    # ── Measurement ───────────────────────────────────────────────────────
    measurement_result: dict[str, Any] = Field(
        default_factory=dict,
        description="Computed result from the organ's processing",
    )
    measurement_summary: str = Field(
        default="",
        description="Human-readable summary of the measurement",
    )

    # ── Vault ─────────────────────────────────────────────────────────────
    vault_receipt_reference: str = Field(
        default="",
        description="VAULT999 receipt ID if this envelope was sealed",
    )

    # ── Organ-specific payload ────────────────────────────────────────────
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Organ-specific data (MetabolicOutput for GEOX, WealthInput for WEALTH, etc.)",
    )

    # ── Cross-organ handoff ───────────────────────────────────────────────
    handoff_reason: str = Field(
        default="",
        description="Why this envelope is being passed to the next organ",
    )
    blocked_organs: list[OrganID] = Field(
        default_factory=list,
        description="Organs that should NOT receive this envelope",
    )

    # ── Provenance ────────────────────────────────────────────────────────
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC timestamp of this envelope",
    )
    constitution_hash: str = Field(
        default="",
        description="Constitutional law version",
    )
    parent_envelope_id: str | None = Field(
        default=None,
        description="Previous envelope in the metabolic chain (for tracing)",
    )

    model_config = {
        "json_schema_extra": {
            "description": (
                "Federation Metabolism Spine — the blood packet. "
                "sense → route → deliberate → execute → measure → seal → learn. "
                "DITEMPA BUKAN DIBERI"
            )
        }
    }


# ──────────────────────────────────────────────────────────────────────────────
# BUILDER — Quick envelope construction
# ──────────────────────────────────────────────────────────────────────────────


def build_federation_envelope(
    *,
    trace_id: str,
    actor_id: str,
    organ_origin: OrganID,
    intent: str,
    metabolic_phase: MetabolicPhase = MetabolicPhase.SENSE,
    evidence_type: str = "unknown",
    evidence_refs: list[str] | None = None,
    epistemic_label: str = "OBS",
    confidence: float = 0.5,
    autonomy_band: AutonomyBand = AutonomyBand.OBSERVE,
    reversibility_class: ReversibilityClass = ReversibilityClass.FULL,
    risk_class: RiskClass = RiskClass.LOW,
    proposed_action: str = "",
    execution_status: ExecutionStatus = ExecutionStatus.SENSED,
    measurement_result: dict[str, Any] | None = None,
    measurement_summary: str = "",
    organ_target: OrganID | None = None,
    handoff_reason: str = "",
    payload: dict[str, Any] | None = None,
    session_id: str | None = None,
    parent_envelope_id: str | None = None,
    f13_required: bool = False,
    required_floor_checks: list[FloorCheck] | None = None,
) -> FederationEnvelope:
    """Build a FederationEnvelope with sensible defaults."""
    return FederationEnvelope(
        trace_id=trace_id,
        actor_id=actor_id,
        organ_origin=organ_origin,
        intent=intent,
        metabolic_phase=metabolic_phase,
        evidence_layer=EvidenceLayer(
            evidence_type=evidence_type,
            evidence_refs=evidence_refs or [],
            epistemic_label=epistemic_label,
            confidence=min(confidence, 0.90),  # F7 HUMILITY cap
        ),
        autonomy_band=autonomy_band,
        reversibility_class=reversibility_class,
        risk_class=risk_class,
        proposed_action=proposed_action,
        execution_status=execution_status,
        measurement_result=measurement_result or {},
        measurement_summary=measurement_summary,
        organ_target=organ_target,
        handoff_reason=handoff_reason,
        payload=payload or {},
        session_id=session_id,
        parent_envelope_id=parent_envelope_id,
        f13_required=f13_required,
        required_floor_checks=required_floor_checks or [],
    )


# ──────────────────────────────────────────────────────────────────────────────
# GEOFX → FEDERATION ENVELOPE ADAPTER
# ──────────────────────────────────────────────────────────────────────────────


def geox_to_federation_envelope(
    tool_name: str,
    tool_output: dict[str, Any],
    *,
    trace_id: str,
    actor_id: str,
    intent: str,
    session_id: str | None = None,
    organ_target: OrganID | None = None,
    handoff_reason: str = "",
    parent_envelope_id: str | None = None,
) -> FederationEnvelope:
    """Wrap a GEOX tool output in a FederationEnvelope.

    This is the GEOX metabolic adapter: takes any GEOX tool output
    and wraps it in the canonical federation envelope so arifOS,
    WEALTH, WELL, and A-FORGE can read it uniformly.

    Parameters
    ----------
    tool_name : str
        Canonical GEOX tool name.
    tool_output : dict
        Raw tool output from GEOX MCP.
    trace_id : str
        End-to-end trace ID.
    actor_id : str
        Who initiated this metabolic cycle.
    intent : str
        What this metabolic cycle is trying to achieve.
    session_id : str, optional
        Governed session ID.
    organ_target : OrganID, optional
        Which organ should receive this next.
    handoff_reason : str, optional
        Why this envelope is being passed.

    Returns
    -------
    FederationEnvelope
        Canonical envelope wrapping the GEOX output.
    """
    # Extract claim_state from tool output
    claim_state = tool_output.get("claim_state", "HYPOTHESIS")

    # Map GEOX claim state to execution status
    _CLAIM_TO_STATUS = {
        "NO_VALID_EVIDENCE": ExecutionStatus.VOID,
        "INGESTED": ExecutionStatus.SENSED,
        "QC_VERIFIED": ExecutionStatus.SENSED,
        "INTERPRETED": ExecutionStatus.MEASURED,
        "DERIVED_CANDIDATE": ExecutionStatus.MEASURED,
        "SEALED": ExecutionStatus.SEALED,
        "JUDGE_PREVIEW": ExecutionStatus.DELIBERATING,
        "888_HOLD": ExecutionStatus.HOLD,
        "VOID": ExecutionStatus.VOID,
        # MetabolicOutput states
        "OBSERVED": ExecutionStatus.SENSED,
        "HYPOTHESIS": ExecutionStatus.MEASURED,
        "QUALIFIED": ExecutionStatus.MEASURED,
        "VERIFIED": ExecutionStatus.MEASURED,
        "HOLD": ExecutionStatus.HOLD,
    }
    execution_status = _CLAIM_TO_STATUS.get(claim_state, ExecutionStatus.SENSED)

    # Extract epistemic label from provenance
    provenance = tool_output.get("provenance", {})
    claim_tag = tool_output.get("claim_tag", "")

    # Map perception class to epistemic label
    perception_class = tool_output.get("perception_class", "")
    _PERCEPTION_TO_EPISTEMIC = {
        "MEASURED": "OBS",
        "DERIVED": "DER",
        "CORROBORATED": "DER",
        "HYPOTHESIS": "INT",
        "DISPLAY": "INT",
    }
    epistemic_label = _PERCEPTION_TO_EPISTEMIC.get(perception_class, "OBS")

    # Extract confidence
    confidence = tool_output.get("humility_score", 0.5)
    if isinstance(confidence, (int, float)):
        confidence = max(0.0, min(0.90, 1.0 - confidence))  # Invert humility → confidence, cap 0.90
    else:
        confidence = 0.5

    # Extract evidence refs
    evidence_refs = tool_output.get("evidence_refs", [])

    # Determine risk class based on tool
    _TOOL_RISK = {
        "geox_well_ingest": RiskClass.LOW,
        "geox_well_qc": RiskClass.LOW,
        "geox_well_desurvey": RiskClass.LOW,
        "geox_petrophysics": RiskClass.MEDIUM,
        "geox_sequence": RiskClass.MEDIUM,
        "geox_seismic_ingest": RiskClass.LOW,
        "geox_seismic_compute": RiskClass.MEDIUM,
        "geox_seismic_interpret": RiskClass.MEDIUM,
        "geox_vision": RiskClass.MEDIUM,
        "geox_subsurface_model": RiskClass.HIGH,
        "geox_geomechanics": RiskClass.MEDIUM,
        "geox_basin": RiskClass.LOW,
        "geox_deep_time_state": RiskClass.LOW,
        "geox_atlas": RiskClass.LOW,
        "geox_claim": RiskClass.HIGH,
        "geox_evidence": RiskClass.MEDIUM,
        "geox_prospect": RiskClass.HIGH,
        "geox_doctrine": RiskClass.HIGH,
        "geox_surface_status": RiskClass.LOW,
    }
    risk_class = _TOOL_RISK.get(tool_name, RiskClass.MEDIUM)

    # Determine autonomy band
    if execution_status == ExecutionStatus.HOLD:
        autonomy_band = AutonomyBand.OBSERVE
    elif risk_class == RiskClass.HIGH:
        autonomy_band = AutonomyBand.DRAFT
    elif risk_class == RiskClass.CRITICAL:
        autonomy_band = AutonomyBand.QUEUE
    else:
        autonomy_band = AutonomyBand.SUGGEST

    # F13 required for high-risk or prospect-level tools
    f13_required = risk_class in (RiskClass.HIGH, RiskClass.CRITICAL)

    # Build evidence layer
    evidence_type = "unknown"
    if "seismic" in tool_name:
        evidence_type = "seismic"
    elif "well" in tool_name or "petro" in tool_name:
        evidence_type = "well_log"
    elif "prospect" in tool_name:
        evidence_type = "petrophysical"
    elif "basin" in tool_name:
        evidence_type = "geological"
    elif "claim" in tool_name:
        evidence_type = "constitutional"
    elif "evidence" in tool_name:
        evidence_type = "multi_modal"

    # Build measurement summary
    summary_parts = [f"GEOX {tool_name} → {claim_state}"]
    if tool_output.get("qc_passed") is not None:
        summary_parts.append(f"QC: {'PASS' if tool_output['qc_passed'] else 'FAIL'}")
    if tool_output.get("primary_artifact", {}).get("well_id"):
        summary_parts.append(f"Well: {tool_output['primary_artifact']['well_id']}")

    return build_federation_envelope(
        trace_id=trace_id,
        actor_id=actor_id,
        organ_origin=OrganID.GEOX,
        intent=intent,
        metabolic_phase=MetabolicPhase.SENSE,
        evidence_type=evidence_type,
        evidence_refs=evidence_refs,
        epistemic_label=epistemic_label,
        confidence=confidence,
        autonomy_band=autonomy_band,
        reversibility_class=ReversibilityClass.FULL,
        risk_class=risk_class,
        proposed_action=f"geox_{tool_name}_result",
        execution_status=execution_status,
        measurement_result=tool_output,
        measurement_summary=" | ".join(summary_parts),
        organ_target=organ_target,
        handoff_reason=handoff_reason,
        payload={
            "tool_name": tool_name,
            "claim_state": claim_state,
            "claim_tag": claim_tag,
            "perception_class": perception_class,
            "provenance": provenance,
        },
        session_id=session_id,
        parent_envelope_id=parent_envelope_id,
        f13_required=f13_required,
    )
