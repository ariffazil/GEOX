"""
GEOX Metabolic Output Schemas — Canonical-Copy of arifOS metabolic.v1
════════════════════════════════════════════════════════════════════════════════════════

CANONICAL-COPY NOTICE
─────────────────────
This file is a canonical copy of the arifOS Universal Metabolic Contract.

schema_name:    MetabolicOutput
schema_version:  metabolic.v1
source_commit:   3c64960e (arifOS)
contract_hash:   a5826a9eb1182c4f212fda1baa55ff9f
organ:           GEOX
adoption_status: PHASE_1

Do NOT fork the meaning. Do NOT modify enum values or field names.
If you need changes, propose them to arifOS first.

The loop:
  witness → decode → contrast → meaning → constraint → model update → judgment

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────────────────────
# METABOLIC ENUMS — Do not modify
# ──────────────────────────────────────────────────────────────────────────────


class ClaimState(StrEnum):
    """Where does this claim sit in the evidence lifecycle?

    Maps directly to Eureka 10 metabolic output contract.
    """

    OBSERVED = "OBSERVED"  # Raw witness received — not yet interpreted
    HYPOTHESIS = "HYPOTHESIS"  # Anomaly detected, meaning proposed
    QUALIFIED = "QUALIFIED"  # Meaning tested, constraints checked
    VERIFIED = "VERIFIED"  # Cross-witness confirmed
    SEALED = "SEALED"  # Irreversible — human ratified + vault entry
    HOLD = "HOLD"  # Governance pause — requires 888_JUDGE


class WitnessType(StrEnum):
    """What category of evidence is this witness?

    Eureka 1: Reality is never directly held. Maps are not Earth.
    """

    MAP = "map"
    SEISMIC = "seismic"
    FILING = "filing"
    REPORT = "report"
    IMAGE = "image"
    LOG = "log"
    TESTIMONY = "testimony"
    SENSOR = "sensor"
    DOCUMENT = "document"
    SIGNAL = "signal"


class ModelTarget(StrEnum):
    """Which domain model does this witness update?"""

    EARTH = "Earth"
    WEALTH = "Wealth"
    INSTITUTION = "Institution"
    BODY = "Body"
    CASE = "Case"
    SYSTEM = "System"


class OrganType(StrEnum):
    """Which organ processes this witness."""

    GEOX = "GEOX"  # Earth metabolism
    WEALTH = "WEALTH"  # Capital/institution metabolism
    WELL = "WELL"  # Body/human-readiness metabolism
    INSTX = "INSTX"  # Institution model
    ARIFOS = "arifOS"  # Constitutional kernel + routing


class ContrastSeverity(StrEnum):
    """How significant is the anomalous contrast?"""

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AbstractionUse(StrEnum):
    """How can an abstraction be safely used?"""

    HEURISTIC = "heuristic"  # Starting point for investigation only
    HYPOTHESIS = "hypothesis"  # Testable claim under development
    VERIFIED_MODEL = "verified_model"  # Physically/logically confirmed


class ConfidenceLevel(StrEnum):
    """
    Shared confidence language across all organs.

    Rules:
      No evidence       → UNKNOWN / HOLD
      Weak evidence     → HYPOTHESIS
      Cross-checked    → QUALIFIED
      Primary-source   → VERIFIED
      Human authority  → SEALED
    """

    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERIFIED = "VERIFIED"
    SEALED = "SEALED"


class WitnessStatus(StrEnum):
    """
    Lifecycle stage of a witness through the metabolic pipeline.

    Eureka 10 §1: Universal witness schema.
    """

    RAW = "RAW"
    DECODED = "DECODED"
    INTERPRETED = "INTERPRETED"
    VERIFIED = "VERIFIED"
    CONTESTED = "CONTESTED"


class StalenessRisk(StrEnum):
    """How likely is this evidence to be stale?"""

    LOW = "LOW"  # Static evidence (geology, legal structure)
    MODERATE = "MODERATE"  # Slowly changing (company filings, reserves)
    HIGH = "HIGH"  # Rapidly changing (market prices, production numbers)


# ──────────────────────────────────────────────────────────────────────────────
# WITNESS LAYER
# ──────────────────────────────────────────────────────────────────────────────


class Witness(BaseModel):
    """A single piece of evidence — ingested, classified, not yet interpreted.

    Eureka 1: Reality is never directly held. Maps are not Earth.
    """

    witness_id: str = Field(description="Unique identifier for this witness")
    witness_type: WitnessType = Field(description="Category of evidence")
    source_uri: str = Field(default="", description="Where this evidence came from")
    raw_content: Any = Field(default=None, description="Raw evidence payload")
    ingested_at: str = Field(description="UTC timestamp of ingestion")
    session_id: str | None = Field(default=None, description="Session binding")
    provenance: str = Field(default="", description="Origin chain: who observed, how transmitted, any transforms")


# ──────────────────────────────────────────────────────────────────────────────
# DECODED ENTITY LAYER
# ──────────────────────────────────────────────────────────────────────────────


class DecodedEntity(BaseModel):
    """A discrete object extracted from the witness."""

    entity_id: str = Field(description="Unique decoded entity ID")
    entity_type: str = Field(description="Type: horizon, fault, anomaly, filing, ratio...")
    detected_at_depth: str | None = Field(
        default=None,
        description="Depth reference: MD, TVD, TVDSS — or temporal for non-spatial",
    )
    detected_value: Any = Field(default=None, description="The measured/detected value")
    detection_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in detection (separate from meaning confidence!)",
    )
    perception_class: str = Field(
        default="MEASURED",
        description="MEASURED | DERIVED | DISPLAY | CORROBORATED | HYPOTHESIS",
    )
    evidence_tag: str = Field(
        default="UNKNOWN",
        description="EVIDENCE_DIRECT | EVIDENCE_MULTI_ZONE | INTERPRET_FROM_LITHOLOGY...",
    )


# ──────────────────────────────────────────────────────────────────────────────
# ANOMALOUS CONTRAST LAYER
# ──────────────────────────────────────────────────────────────────────────────


class AnomalousContrast(BaseModel):
    """A deviation from expected background.

    Eureka 3: Contrast is the birth of hypothesis.

    In GEOX: bright spot ≠ gas automatically (could be tuning/lithology/artifact)
    """

    contrast_id: str = Field(description="Unique contrast ID, e.g. AC-001")
    contrast_domain: Literal["earth", "wealth", "institution", "health", "law", "system"] = Field(
        default="earth", description="Which domain context"
    )
    background_expectation: str = Field(description="What the model expected before this witness")
    observed_deviation: str = Field(description="What was actually observed that differs")
    candidate_causes: list[str] = Field(default_factory=list, description="Possible explanations for the contrast")
    false_positive_risks: list[str] = Field(default_factory=list, description="Known ways this contrast could be spurious")
    required_verification: list[str] = Field(default_factory=list, description="What tests are needed before treating as real")
    severity: ContrastSeverity = Field(default=ContrastSeverity.MODERATE)


# ──────────────────────────────────────────────────────────────────────────────
# MEANING LAYER
# ──────────────────────────────────────────────────────────────────────────────


class CandidateMeaning(BaseModel):
    """Possible interpretations of a decoded entity.

    Eureka 6: Meaning is harder than perception.
    """

    meaning_id: str = Field(description="Unique meaning ID")
    decoded_entity_id: str = Field(description="Which entity this meaning applies to")
    possible_meanings: list[str] = Field(default_factory=list, description="Differential interpretations — never just one")
    primary_interpretation: str = Field(default="", description="Most likely meaning given current evidence")
    meaning_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in primary interpretation (separate from detection!)",
    )
    meaning_confidence_band: tuple[float, float] = Field(default=(0.0, 1.0), description="F07 HUMILITY: uncertainty range")
    tests_needed_before_claim: list[str] = Field(
        default_factory=list, description="What evidence would confirm or deny this interpretation"
    )
    ruling_out: list[str] = Field(default_factory=list, description="What other interpretations have been ruled out")


# ──────────────────────────────────────────────────────────────────────────────
# CONSTRAINT LAYER
# ──────────────────────────────────────────────────────────────────────────────


class ConstraintCheck(BaseModel):
    """A single constraint verified against the candidate meaning.

    Eureka 7: Abstraction without guard becomes hallucination.
    """

    constraint_id: str = Field(description="Which constraint was checked")
    constraint_type: str = Field(description="physics | law | ethics | financial | constitutional")
    rule_invoked: str = Field(description="Which rule or law is being applied")
    check_passed: bool = Field(default=False, description="Did the candidate meaning pass this constraint?")
    failure_reason: str = Field(default="", description="If check failed, why")
    evidence_required: list[str] = Field(default_factory=list, description="What evidence was used to verify this constraint")


# ──────────────────────────────────────────────────────────────────────────────
# MODEL UPDATE LAYER
# ──────────────────────────────────────────────────────────────────────────────


class ModelUpdate(BaseModel):
    """A proposed update to a Large Domain Model.

    Eureka 4: GEOX should not produce "a map." It should update a Large Earth Model.

    This is the real memory — not the output, but the updated state.
    """

    model_id: str = Field(description="Which model is being updated")
    model_type: Literal[
        "LargeEarthModel",
        "LargeWealthModel",
        "LargeInstitutionModel",
        "LargeBodyModel",
        "LargeSystemModel",
    ] = Field(default="LargeEarthModel", description="Domain model classification")
    state_before: dict[str, Any] = Field(default_factory=dict, description="Model state before this witness was applied")
    incoming_witnesses: list[str] = Field(default_factory=list, description="Which witness IDs contributed to this update")
    proposed_updates: list[dict[str, Any]] = Field(default_factory=list, description="Specific field-level changes proposed")
    constraints_checked: list[str] = Field(
        default_factory=list, description="Which constraints were verified before accepting update"
    )
    state_after: dict[str, Any] = Field(default_factory=dict, description="Model state after this witness was applied")
    confidence_delta: float = Field(default=0.0, description="Change in model confidence from this update")
    audit_receipt: str = Field(default="", description="VAULT reference for this model update")


# ──────────────────────────────────────────────────────────────────────────────
# ABSTRACTION GUARD
# ──────────────────────────────────────────────────────────────────────────────


class AbstractionGuard(BaseModel):
    """Guard against metaphor being used as proof.

    Eureka 7: Analogy is powerful but dangerous.

    metaphor → literal claim → evidence needed → allowed status
    """

    metaphor: str = Field(description="The figurative language or abstraction being guarded")
    literal_claim: str = Field(description="What the metaphor translates to as a testable claim")
    evidence_required: list[str] = Field(default_factory=list, description="What evidence is needed to support this claim")
    allowed_use: AbstractionUse = Field(
        default=AbstractionUse.HEURISTIC,
        description="How this abstraction can legitimately be used",
    )
    misuse_risk: str = Field(default="", description="Known risks if this metaphor is over-extended")
    violations: list[str] = Field(
        default_factory=list,
        description="If metaphor was misused as proof, what was violated",
    )


# ──────────────────────────────────────────────────────────────────────────────
# UNCERTAINTY LAYER — F07 HUMILITY
# ──────────────────────────────────────────────────────────────────────────────


class UncertaintyBand(BaseModel):
    """Uncertainty quantification for this metabolic output.

    F07 HUMILITY: Confidence must be labeled honestly. No fake certainty.
    """

    omega_0: float = Field(default=0.05, ge=0.0, le=1.0, description="Base uncertainty (Ω₀)")
    uncertainty_range: tuple[float, float] = Field(default=(0.0, 1.0), description="Honest range of confidence")
    major_unknowns: list[str] = Field(default_factory=list, description="What key variables are unconstrained")
    key_missing_evidence: list[str] = Field(default_factory=list, description="What evidence would most reduce uncertainty")
    claim_too_certain_flag: bool = Field(default=False, description="Was the model tempted to overclaim?")


# ──────────────────────────────────────────────────────────────────────────────
# EVIDENCE FRESHNESS — Eureka 10 §8
# ──────────────────────────────────────────────────────────────────────────────


class EvidenceFreshness(BaseModel):
    """Evidence freshness tracking — prevents stale intelligence from guiding action.

    Eureka 10 §8: Evidence freshness and decay.
    """

    as_of: str = Field(description="UTC timestamp when evidence was collected")
    expires_after_seconds: int | None = Field(default=None, description="Seconds after which this evidence is considered stale")
    staleness_risk: StalenessRisk = Field(default=StalenessRisk.MODERATE, description="Likely rate of evidence decay")
    requires_refresh: bool = Field(default=False, description="Should this evidence be re-fetched before use?")
    refresh_recommendation: str = Field(default="", description="Human-readable recommendation for refresh")


# ──────────────────────────────────────────────────────────────────────────────
# CROSS-ORGAN HANDOFF — Eureka 10 §4
# ──────────────────────────────────────────────────────────────────────────────


class CrossOrganHandoff(BaseModel):
    """Formal handoff packet when one organ passes work to another.

    Example chain:
      GEOX (finds resource significance)
        → WEALTH (evaluates capital consequence)
        → WELL (checks Arif readiness)
        → arifOS (judges route)
        → VAULT (seals)
    """

    next_best_organ: OrganType = Field(default=OrganType.ARIFOS, description="Which organ should receive this next")
    handoff_reason: str = Field(default="", description="Why this organ? What can it add that this organ cannot?")
    handoff_payload: dict[str, Any] = Field(default_factory=dict, description="Structured data to pass to the next organ")
    blocked_organs: list[OrganType] = Field(
        default_factory=list,
        description="Which organs should NOT receive this (conflict, capture risk)",
    )
    blocked_reason: str = Field(default="", description="Why each blocked organ was excluded")
    confidence_at_handoff: ConfidenceLevel = Field(default=ConfidenceLevel.MODERATE, description="Confidence level at handoff")


# ──────────────────────────────────────────────────────────────────────────────
# ORGAN CONFLICT — Eureka 10 §9
# ──────────────────────────────────────────────────────────────────────────────


class OrganConflict(BaseModel):
    """Record of a conflict between organ conclusions.

    Eureka 10 §9: Conflict scanner.

    Example:
      GEOX:  asset is technically strategic
      WEALTH: deal structure is economically defensible
      arifOS: governance transparency is insufficient
      WELL:   public action readiness is low

    Result: PARTIAL / HOLD — not a forced conclusion.
    """

    conflict_id: str = Field(description="Unique conflict identifier")
    organ_a: OrganType = Field(description="First organ in conflict")
    organ_a_conclusion: str = Field(description="What organ A concluded")
    organ_b: OrganType = Field(description="Second organ in conflict")
    organ_b_conclusion: str = Field(description="What organ B concluded")
    conflict_domain: str = Field(default="", description="earth | wealth | governance | health | law | system")
    resolution_status: Literal["OPEN", "PARTIAL", "RESOLVED", "ESCALATED"] = Field(
        default="OPEN", description="Current resolution state"
    )
    partial_flag: bool = Field(
        default=False,
        description="True if this conflict means output should be PARTIAL not FORCED",
    )
    recommended_action: str = Field(default="", description="What should happen given this conflict")


# ──────────────────────────────────────────────────────────────────────────────
# METABOLIC OUTPUT — The universal contract
# ──────────────────────────────────────────────────────────────────────────────


class MetabolicOutput(BaseModel):
    """
    Universal metabolic output contract for all organs.

    schema_name:      MetabolicOutput
    schema_version:   metabolic.v1
    source_commit:    3c64960e (arifOS)
    contract_hash:    a5826a9eb1182c4f212fda1baa55ff9f
    organ:           GEOX
    adoption_status:  PHASE_1

    The loop:
      witness → meaning → verification → model update → judgment

    Every organ (GEOX, WEALTH, WELL, arifOS) must output this structure.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    organ: OrganType = Field(default=OrganType.GEOX, description="Which organ produced this output")
    tool_name: str = Field(default="", description="Which MCP tool generated this output")
    session_id: str | None = Field(default=None)

    # ── Witness layer ──────────────────────────────────────────────────────────
    witnesses_ingested: list[Witness] = Field(default_factory=list, description="Raw evidence received in this metabolic cycle")
    witness_type: WitnessType | None = Field(default=None, description="Primary witness category")
    witness_status: WitnessStatus = Field(
        default=WitnessStatus.RAW,
        description="Lifecycle stage: RAW → DECODED → INTERPRETED → VERIFIED → CONTESTED",
    )

    # ── Decoded layer ─────────────────────────────────────────────────────────
    decoded_entities: list[DecodedEntity] = Field(default_factory=list, description="Objects extracted from witnesses")

    # ── Contrast layer ────────────────────────────────────────────────────────
    anomalous_contrasts: list[AnomalousContrast] = Field(default_factory=list, description="Deviations from expected background")

    # ── Meaning layer ─────────────────────────────────────────────────────────
    candidate_meanings: list[CandidateMeaning] = Field(
        default_factory=list, description="Possible interpretations (never a single claim)"
    )

    # ── Constraint layer ──────────────────────────────────────────────────────
    constraints_checked: list[ConstraintCheck] = Field(default_factory=list, description="Rules, physics, law, ethics verified")

    # ── Model update layer ───────────────────────────────────────────────────
    model_updates: list[ModelUpdate] = Field(default_factory=list, description="Proposed state changes to domain models")
    model_target: ModelTarget = Field(default=ModelTarget.EARTH, description="Which domain model was updated")

    # ── Abstraction guard ────────────────────────────────────────────────────
    abstraction_guard: AbstractionGuard | None = Field(
        default=None, description="If metaphors were used, guard against hallucination"
    )

    # ── Uncertainty ───────────────────────────────────────────────────────────
    uncertainty: UncertaintyBand = Field(default_factory=UncertaintyBand, description="Honest uncertainty quantification (F07)")

    # ── Evidence freshness ────────────────────────────────────────────────────
    evidence_freshness: EvidenceFreshness | None = Field(
        default=None, description="Evidence expiry and staleness tracking (Eureka 10 §8)"
    )

    # ── Required next steps ──────────────────────────────────────────────────
    required_next_tests: list[str] = Field(default_factory=list, description="What tests would most improve confidence")
    next_best_tool: str = Field(default="", description="Which tool should be called next to advance understanding")

    # ── Cross-organ handoff ─────────────────────────────────────────────────
    cross_organ_handoff: CrossOrganHandoff | None = Field(
        default=None,
        description="Formal handoff packet to next organ (Eureka 10 §4)",
    )

    # ── Claim state ───────────────────────────────────────────────────────────
    claim_state: ClaimState = Field(default=ClaimState.HYPOTHESIS, description="Where does this sit in the evidence lifecycle?")

    # ── Conflict flags ────────────────────────────────────────────────────────
    conflict_flags: list[OrganConflict] = Field(
        default_factory=list,
        description="Detected disagreements between organ conclusions (Eureka 10 §9)",
    )

    # ── Confidence level (shared policy) ─────────────────────────────────────
    confidence_level: ConfidenceLevel = Field(
        default=ConfidenceLevel.MODERATE,
        description=("Shared confidence language: UNKNOWN/LOW/MODERATE/HIGH/VERIFIED/SEALED (Eureka 10 §7)"),
    )

    # ── Audit ────────────────────────────────────────────────────────────────
    audit_receipt: str = Field(default="", description="VAULT reference for this metabolic cycle")

    # ── SOVEREIGNTY BOUNDARY (Eureka 8) ─────────────────────────────────────
    # AI proposes. Tools compute. Memory records. Constraints guard. Arif judges.
    recommendation_only: bool = Field(default=True, description="AI proposes only — has not been ratified by human")
    execution_authorized: bool = Field(
        default=False, description="Has a human authorized execution? False until F13 ratification."
    )
    human_final_authority: str = Field(default="Arif", description="Who has final say on this output?")
    requires_888_judge: bool = Field(default=False, description="Does this output require 888_JUDGE before action?")

    # ── Provenance ──────────────────────────────────────────────────────────
    timestamp_utc: str = Field(description="UTC timestamp of this output")
    domain_law: str = Field(default="NATURAL_LAW", description="GEOX domain law: NATURAL_LAW (kuasa alam)")
    physics_manifest_hash: str = Field(default="", description="SHA-256 hash of GEOX Physics Manifest")

    class Config:
        json_schema_extra = {
            "description": (
                "Governed Witness Metabolism Output — "
                "Intelligence is not answer generation. "
                "Intelligence is governed witness metabolism. "
                "DITEMPA BUKAN DIBERI"
            )
        }


# ──────────────────────────────────────────────────────────────────────────────
# METABOLIC CYCLE — Full witness → judgment loop record
# ──────────────────────────────────────────────────────────────────────────────


class MetabolicCycle(BaseModel):
    """Complete record of one full metabolic cycle."""

    cycle_id: str = Field(description="Unique cycle identifier")
    organ: OrganType = Field(default=OrganType.GEOX)
    session_id: str | None = None

    # Steps in order
    witness_ingest: list[Witness] = Field(default_factory=list)
    visual_decode: list[DecodedEntity] = Field(default_factory=list)
    anomalous_contrast: list[AnomalousContrast] = Field(default_factory=list)
    meaning_generate: list[CandidateMeaning] = Field(default_factory=list)
    constraint_verify: list[ConstraintCheck] = Field(default_factory=list)
    model_update: list[ModelUpdate] = Field(default_factory=list)

    # Final state
    final_output: MetabolicOutput | None = None
    claim_state: ClaimState = ClaimState.HYPOTHESIS

    # Sovereignty
    recommendation_only: bool = True
    execution_authorized: bool = False
    human_final_authority: str = "Arif"
    requires_888_judge: bool = False

    # Audit
    timestamp_utc: str = ""
    total_steps: int = 0


# ──────────────────────────────────────────────────────────────────────────────
# METABOLIC OUTPUT BUILDER — GEOX Phase 1 adoption helper
# ──────────────────────────────────────────────────────────────────────────────
# NOT a canonical-copy section — this builder lives in GEOX only.
# It constructs MetabolicOutput dicts for GEOX tool envelopes.
#
# canonical-copy notice:
#   schema_name:    MetabolicOutput
#   schema_version:  metabolic.v1
#   source_commit:   3c64960e (arifOS)
#   contract_hash:   a5826a9eb1182c4f212fda1baa55ff9f
#   organ:           GEOX
#   adoption_status: PHASE_1
#
# DITEMPA BUKAN DIBERI — Forged, Not Given


from datetime import UTC, datetime


def build_metabolic_output(
    tool_name: str,
    primary_artifact: dict[str, Any],
    *,
    witness_type: WitnessType | None = None,
    claim_state: ClaimState | None = None,
    confidence_level: ConfidenceLevel | None = None,
    witness_status: WitnessStatus = WitnessStatus.RAW,
    decoded_entities: list[Any] | None = None,
    anomalous_contrasts: list[Any] | None = None,
    candidate_meanings: list[Any] | None = None,
    constraints_checked: list[Any] | None = None,
    model_updates: list[Any] | None = None,
    required_next_tests: list[str] | None = None,
    next_best_tool: str = "",
    evidence_freshness_as_of: str | None = None,
    cross_organ_handoff: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Build a MetabolicOutput dict for a GEOX tool envelope.

    This is the Phase 1 adoption bridge: each GEOX tool return is wrapped
    with the universal metabolic contract so arifOS can read it uniformly.

    Parameters
    ----------
    tool_name : str
        Canonical GEOX tool name, e.g. "geox_data_ingest_bundle".
    primary_artifact : dict
        The tool's primary_artifact dict (from get_standard_envelope).
    witness_type : WitnessType, optional
        Primary evidence category. If None, inferred from tool_name.
    claim_state : ClaimState, optional
        Where this output sits in the evidence lifecycle.
        If None, inferred from tool_name.
    confidence_level : ConfidenceLevel, optional
        Shared confidence language. If None, inferred from claim_state.
    witness_status : WitnessStatus, default WitnessStatus.RAW
        Lifecycle stage of the primary witness.
    decoded_entities : list, optional
        List of DecodedEntity dicts.
    anomalous_contrasts : list, optional
        List of AnomalousContrast dicts.
    candidate_meanings : list, optional
        List of CandidateMeaning dicts.
    constraints_checked : list, optional
        List of ConstraintCheck dicts.
    model_updates : list, optional
        List of ModelUpdate dicts.
    required_next_tests : list[str], optional
        What tests would most improve confidence.
    next_best_tool : str, optional
        Which GEOX tool should be called next.
    evidence_freshness_as_of : str, optional
        UTC timestamp of when evidence was collected.
        Defaults to current UTC time.
    cross_organ_handoff : dict, optional
        CrossOrganHandoff dict. If None, no handoff.
    session_id : str, optional
        Governed session ID.

    Returns
    -------
    dict
        A MetabolicOutput-compatible dict to inject into the envelope
        under the key "metabolic".
    """
    # ── Defaults per tool ───────────────────────────────────────────────────
    _INGEST_DEFAULTS = {
        "witness_type": WitnessType.LOG,
        "claim_state": ClaimState.OBSERVED,
        "confidence_level": ConfidenceLevel.LOW,
        "witness_status": WitnessStatus.RAW,
        "next_best_tool": "geox_data_qc_bundle",
        "required_next_tests": [
            "QC header check",
            "Depth monotonicity check",
            "Canonical curves completeness check",
        ],
    }
    _QC_DEFAULTS = {
        "witness_type": WitnessType.LOG,
        "claim_state": ClaimState.VERIFIED,
        "confidence_level": ConfidenceLevel.MODERATE,
        "witness_status": WitnessStatus.DECODED,
        "next_best_tool": "geox_subsurface_generate_candidates",
        "required_next_tests": [],
    }
    _SUBSURFACE_DEFAULTS = {
        "witness_type": WitnessType.SIGNAL,
        "claim_state": ClaimState.HYPOTHESIS,
        "confidence_level": ConfidenceLevel.LOW,
        "witness_status": WitnessStatus.INTERPRETED,
        "next_best_tool": "geox_seismic_analyze_volume",
        "required_next_tests": [
            "Cross-validate with analog data",
            "Petrophysical cutoff sensitivity analysis",
        ],
    }
    _SEISMIC_DEFAULTS = {
        "witness_type": WitnessType.SEISMIC,
        "claim_state": ClaimState.HYPOTHESIS,
        "confidence_level": ConfidenceLevel.MODERATE,
        "witness_status": WitnessStatus.INTERPRETED,
        "next_best_tool": "geox_subsurface_generate_candidates",
        "required_next_tests": [
            "Well-to-seismic tie",
            "Amplitude-vs-offset analysis",
        ],
    }

    _TOOL_DEFAULTS = {
        "geox_data_ingest_bundle": _INGEST_DEFAULTS,
        "geox_data_qc_bundle": _QC_DEFAULTS,
        "geox_subsurface_generate_candidates": _SUBSURFACE_DEFAULTS,
        "geox_seismic_analyze_volume": _SEISMIC_DEFAULTS,
    }

    defaults = _TOOL_DEFAULTS.get(tool_name, {})

    # Resolve claim_state → confidence_level mapping if not provided
    _CLAIM_TO_CONFIDENCE = {
        ClaimState.OBSERVED: ConfidenceLevel.LOW,
        ClaimState.HYPOTHESIS: ConfidenceLevel.LOW,
        ClaimState.QUALIFIED: ConfidenceLevel.MODERATE,
        ClaimState.VERIFIED: ConfidenceLevel.HIGH,
        ClaimState.SEALED: ConfidenceLevel.VERIFIED,
        ClaimState.HOLD: ConfidenceLevel.UNKNOWN,
    }

    resolved_claim_state = claim_state or defaults.get("claim_state", ClaimState.HYPOTHESIS)
    resolved_confidence = (
        confidence_level
        or defaults.get("confidence_level")
        or _CLAIM_TO_CONFIDENCE.get(resolved_claim_state, ConfidenceLevel.MODERATE)
    )
    resolved_witness_type = witness_type or defaults.get("witness_type")
    resolved_witness_status = witness_status
    resolved_next_best_tool = next_best_tool or defaults.get("next_best_tool", "")
    resolved_required_tests = required_next_tests if required_next_tests is not None else defaults.get("required_next_tests", [])

    # ── Evidence freshness ─────────────────────────────────────────────────
    freshness_as_of = evidence_freshness_as_of or datetime.now(UTC).isoformat()
    evidence_freshness = {
        "as_of": freshness_as_of,
        "expires_after_seconds": None,  # Geological data is effectively static
        "staleness_risk": StalenessRisk.LOW.value,
        "requires_refresh": False,
        "refresh_recommendation": (
            "Re-ingest only if a new version of this file is suspected or if the geological interpretation changes significantly."
        ),
    }

    # ── Uncertainty ────────────────────────────────────────────────────────
    uncertainty = {
        "omega_0": 0.05,
        "uncertainty_range": [0.0, 1.0],
        "major_unknowns": [],
        "key_missing_evidence": [],
        "claim_too_certain_flag": False,
    }

    # ── Uncertainty range by confidence ──────────────────────────────────
    if resolved_confidence == ConfidenceLevel.LOW:
        uncertainty["uncertainty_range"] = [0.0, 0.5]
        uncertainty["major_unknowns"] = ["Evidence not cross-checked"]
    elif resolved_confidence == ConfidenceLevel.MODERATE:
        uncertainty["uncertainty_range"] = [0.3, 0.7]
    elif resolved_confidence == ConfidenceLevel.HIGH:
        uncertainty["uncertainty_range"] = [0.6, 0.9]

    # ── Cross-organ handoff ───────────────────────────────────────────────
    if cross_organ_handoff is not None:
        handoff = cross_organ_handoff
    else:
        # Default GEOX handoff: after ingest/QC → subsurface reasoning
        handoff = {
            "next_best_organ": OrganType.GEOX.value,
            "handoff_reason": ("GEOX subsurface tools can refine the interpretation with physics-based petrophysical analysis."),
            "handoff_payload": {
                "artifact_ref": primary_artifact.get("artifact_ref", ""),
                "well_id": primary_artifact.get("well_id", ""),
                "source_type": primary_artifact.get("source_type", ""),
            },
            "blocked_organs": [],
            "blocked_reason": "",
            "confidence_at_handoff": resolved_confidence.value,
        }

    # ── Build MetabolicOutput dict ────────────────────────────────────────
    now = datetime.now(UTC).isoformat()

    metabolic = {
        # Identity
        "organ": OrganType.GEOX.value,
        "tool_name": tool_name,
        "session_id": session_id,
        # Witness layer
        "witness_type": resolved_witness_type.value if resolved_witness_type else None,
        "witness_status": resolved_witness_status.value,
        "witnesses_ingested": [],
        # Decoded layer
        "decoded_entities": decoded_entities or [],
        # Contrast layer
        "anomalous_contrasts": anomalous_contrasts or [],
        # Meaning layer
        "candidate_meanings": candidate_meanings or [],
        # Constraint layer
        "constraints_checked": constraints_checked or [],
        # Model update layer
        "model_updates": model_updates or [],
        "model_target": ModelTarget.EARTH.value,
        # Uncertainty
        "uncertainty": uncertainty,
        # Evidence freshness
        "evidence_freshness": evidence_freshness,
        # Next steps
        "required_next_tests": resolved_required_tests,
        "next_best_tool": resolved_next_best_tool,
        # Cross-organ handoff
        "cross_organ_handoff": handoff,
        # Claim state
        "claim_state": resolved_claim_state.value,
        # Conflict flags
        "conflict_flags": [],
        # Confidence level
        "confidence_level": resolved_confidence.value,
        # Audit
        "audit_receipt": primary_artifact.get("vault_receipt", {}),
        # Sovereignty boundary
        "recommendation_only": True,
        "execution_authorized": False,
        "human_final_authority": "Arif",
        "requires_888_judge": False,
        # Provenance
        "timestamp_utc": now,
        "domain_law": "NATURAL_LAW",
        "physics_manifest_hash": "",
    }

    return metabolic
