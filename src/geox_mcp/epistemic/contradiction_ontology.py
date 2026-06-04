"""
epistemic/contradiction_ontology.py — GEOX Contradiction Ontology
============================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Formal taxonomy of contradiction types for GEOX.
Not all contradictions are equal — this module provides
typed contradiction classification with severity and resolution paths.

Contradiction types:
  - MEASUREMENT_CONFLICT    : Two calibrated measurements disagree
  - DATUM_CONFLICT          : Depth/time reference frame mismatch
  - MODEL_PHYSICS_VIOLATION: Model output violates Physics9 constraints
  - INTERPRETATION_OBSERVATION_MISMATCH: Interpretation contradicts measurement
  - MODEL_MEASUREMENT_MISMATCH: Model prediction contradicts observation
  - JUDGMENT_EVIDENCE_CONFLICT: Judgment exceeds evidentiary basis
  - NARRATIVE_OVERRUN       : Story exceeds grounding
  - CROSS_MODAL_CONFLICT    : Same Earth object contradicts across modalities
  - MISSING_GROUNDING        : Claim has no lower-rung support
  - BEAUTIFUL_ONE_DRIFT     : Rhetorical coherence exceeds evidence
  - CIRCULAR_REASONING       : Claim assumes itself
  - UNKNOWN                  : Cannot determine contradiction class
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ContradictionType(StrEnum):
    MEASUREMENT_CONFLICT = "MEASUREMENT_CONFLICT"
    DATUM_CONFLICT = "DATUM_CONFLICT"
    MODEL_PHYSICS_VIOLATION = "MODEL_PHYSICS_VIOLATION"
    INTERPRETATION_OBSERVATION_MISMATCH = "INTERPRETATION_OBSERVATION_MISMATCH"
    MODEL_MEASUREMENT_MISMATCH = "MODEL_MEASUREMENT_MISMATCH"
    JUDGMENT_EVIDENCE_CONFLICT = "JUDGMENT_EVIDENCE_CONFLICT"
    NARRATIVE_OVERRUN = "NARRATIVE_OVERRUN"
    CROSS_MODAL_CONFLICT = "CROSS_MODAL_CONFLICT"
    MISSING_GROUNDING = "MISSING_GROUNDING"
    BEAUTIFUL_ONE_DRIFT = "BEAUTIFUL_ONE_DRIFT"
    CIRCULAR_REASONING = "CIRCULAR_REASONING"
    UNKNOWN = "UNKNOWN"


class ContradictionSeverity(StrEnum):
    """How severe is this contradiction for the reasoning chain."""

    FATAL = "fatal"  # Claim must be VOIDed immediately
    HIGH = "high"  # Requires 888_HOLD before proceeding
    MEDIUM = "medium"  # Must be surfaced and acknowledged
    LOW = "low"  # Flag for awareness, not blocking
    NEGLIGIBLE = "negligible"  # Minor inconsistency, note only


class ResolutionPath(StrEnum):
    """How this contradiction type should be resolved."""

    VOID = "void"  # Claim is void — cannot proceed
    HOLD = "hold"  # 888_HOLD — requires sovereign decision
    DEMOTE = "demote"  # Push claim to lower rung
    ESCALATE = "escalate"  # Surface to higher authority
    RETRY = "retry"  # Re-run with corrected inputs
    SUSPEND = "suspend"  # Hold in limbo — await new evidence
    IGNORE = "ignore"  # Log and continue (only for NEGLIGIBLE)


# ─── Severity + Resolution map ────────────────────────────────────────────────

CONTRADICTION_SEVERITY: dict[ContradictionType, ContradictionSeverity] = {
    ContradictionType.MEASUREMENT_CONFLICT: ContradictionSeverity.HIGH,
    ContradictionType.DATUM_CONFLICT: ContradictionSeverity.HIGH,
    ContradictionType.MODEL_PHYSICS_VIOLATION: ContradictionSeverity.FATAL,
    ContradictionType.INTERPRETATION_OBSERVATION_MISMATCH: ContradictionSeverity.HIGH,
    ContradictionType.MODEL_MEASUREMENT_MISMATCH: ContradictionSeverity.HIGH,
    ContradictionType.JUDGMENT_EVIDENCE_CONFLICT: ContradictionSeverity.MEDIUM,
    ContradictionType.NARRATIVE_OVERRUN: ContradictionSeverity.MEDIUM,
    ContradictionType.CROSS_MODAL_CONFLICT: ContradictionSeverity.HIGH,
    ContradictionType.MISSING_GROUNDING: ContradictionSeverity.HIGH,
    ContradictionType.BEAUTIFUL_ONE_DRIFT: ContradictionSeverity.MEDIUM,
    ContradictionType.CIRCULAR_REASONING: ContradictionSeverity.FATAL,
    ContradictionType.UNKNOWN: ContradictionSeverity.MEDIUM,
}

CONTRADICTION_RESOLUTION: dict[ContradictionType, ResolutionPath] = {
    ContradictionType.MEASUREMENT_CONFLICT: ResolutionPath.HOLD,
    ContradictionType.DATUM_CONFLICT: ResolutionPath.HOLD,
    ContradictionType.MODEL_PHYSICS_VIOLATION: ResolutionPath.VOID,
    ContradictionType.INTERPRETATION_OBSERVATION_MISMATCH: ResolutionPath.DEMOTE,
    ContradictionType.MODEL_MEASUREMENT_MISMATCH: ResolutionPath.VOID,
    ContradictionType.JUDGMENT_EVIDENCE_CONFLICT: ResolutionPath.DEMOTE,
    ContradictionType.NARRATIVE_OVERRUN: ResolutionPath.DEMOTE,
    ContradictionType.CROSS_MODAL_CONFLICT: ResolutionPath.HOLD,
    ContradictionType.MISSING_GROUNDING: ResolutionPath.SUSPEND,
    ContradictionType.BEAUTIFUL_ONE_DRIFT: ResolutionPath.DEMOTE,
    ContradictionType.CIRCULAR_REASONING: ResolutionPath.VOID,
    ContradictionType.UNKNOWN: ResolutionPath.ESCALATE,
}


@dataclass
class ContradictionRecord:
    """
    A single contradiction record in the GEOX contradiction ontology.

    Captures the full context of a detected contradiction for
    audit, resolution tracking, and cascade analysis.
    """

    contradiction_id: str
    contradiction_type: ContradictionType
    severity: ContradictionSeverity
    resolution_path: ResolutionPath

    # Who is contradicting whom
    claim_a: str
    claim_a_rung: int
    claim_a_tool: str
    claim_b: str
    claim_b_rung: int
    claim_b_tool: str

    # What won (lower rung wins by iron law)
    winning_claim: str
    winning_rung: int
    losing_claim: str
    losing_rung: int

    # Resolution
    verdict: str  # VOID | FLAG | HOLD | DEMOTE
    resolution_notes: str = ""
    resolved_at: datetime | None = None

    # Cascade
    assumption_ids_affected: list[str] = field(default_factory=list)
    downstream_tools_affected: list[str] = field(default_factory=list)

    # Context
    session_id: str = ""
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)

    def is_fatal(self) -> bool:
        return self.severity == ContradictionSeverity.FATAL

    def requires_hold(self) -> bool:
        return self.severity in (
            ContradictionSeverity.FATAL,
            ContradictionSeverity.HIGH,
        )

    def to_dict(self) -> dict:
        return {
            "contradiction_id": self.contradiction_id,
            "contradiction_type": self.contradiction_type.value,
            "severity": self.severity.value,
            "resolution_path": self.resolution_path.value,
            "claim_a": self.claim_a,
            "claim_a_rung": self.claim_a_rung,
            "claim_a_tool": self.claim_a_tool,
            "claim_b": self.claim_b,
            "claim_b_rung": self.claim_b_rung,
            "claim_b_tool": self.claim_b_tool,
            "winning_claim": self.winning_claim,
            "winning_rung": self.winning_rung,
            "losing_claim": self.losing_claim,
            "losing_rung": self.losing_rung,
            "verdict": self.verdict,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "assumption_ids_affected": self.assumption_ids_affected,
            "downstream_tools_affected": self.downstream_tools_affected,
            "session_id": self.session_id,
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata,
        }


def classify_contradiction(
    claim_a_rung: int,
    claim_b_rung: int,
    claim_a_type: str,
    claim_b_type: str,
    has_physics_violation: bool = False,
    has_circular_ref: bool = False,
    beauty_score: float | None = None,
    has_missing_grounding: bool = False,
) -> ContradictionType:
    """
    Classify a detected contradiction into its proper type.

    Called by the iron law validator and by contradiction detection
    in geox_evidence_reason and geox_subsurface_verify_integrity.
    """
    # Circular reasoning is always FATAL
    if has_circular_ref:
        return ContradictionType.CIRCULAR_REASONING

    # Physics violation
    if has_physics_violation:
        return ContradictionType.MODEL_PHYSICS_VIOLATION

    # Beauty drift
    if beauty_score is not None and beauty_score > 2.0:
        return ContradictionType.BEAUTIFUL_ONE_DRIFT

    # Missing grounding
    if has_missing_grounding:
        return ContradictionType.MISSING_GROUNDING

    # Both are Rung 2 measurements
    if claim_a_rung == 2 and claim_b_rung == 2:
        return ContradictionType.MEASUREMENT_CONFLICT

    # Rung 3 vs Rung 2: model vs measurement
    if {claim_a_rung, claim_b_rung} == {2, 3}:
        # Higher rung (3) is the model, lower (2) is measurement
        higher_rung = max(claim_a_rung, claim_b_rung)
        if higher_rung == 3:
            return ContradictionType.MODEL_MEASUREMENT_MISMATCH

    # Rung 4 interpretation vs Rung 2 measurement
    if 4 in {claim_a_rung, claim_b_rung} and 2 in {claim_a_rung, claim_b_rung}:
        return ContradictionType.INTERPRETATION_OBSERVATION_MISMATCH

    # Cross-modal conflict (same rung, different modality)
    if claim_a_rung == claim_b_rung and claim_a_type != claim_b_type:
        return ContradictionType.CROSS_MODAL_CONFLICT

    # Datum conflict (depth reference)
    if "datum" in claim_a_type.lower() or "datum" in claim_b_type.lower():
        return ContradictionType.DATUM_CONFLICT

    # Narrative overrun (Rung 7 vs anything below)
    if 7 in {claim_a_rung, claim_b_rung}:
        return ContradictionType.NARRATIVE_OVERRUN

    # Judgment vs evidence (Rung 6 vs lower)
    if 6 in {claim_a_rung, claim_b_rung} and min(claim_a_rung, claim_b_rung) < 6:
        return ContradictionType.JUDGMENT_EVIDENCE_CONFLICT

    return ContradictionType.UNKNOWN


def get_contradiction_record(
    contradiction_type: ContradictionType,
    claim_a: str,
    claim_a_rung: int,
    claim_a_tool: str,
    claim_b: str,
    claim_b_rung: int,
    claim_b_tool: str,
    session_id: str,
    contradiction_id: str | None = None,
    **kwargs,
) -> ContradictionRecord:
    """
    Factory: build a fully classified ContradictionRecord.

    Automatically sets severity and resolution_path from the type.
    Determines winning/losing claim by iron law (lower rung wins).
    """
    import uuid

    # Iron law: lower rung wins
    if claim_a_rung <= claim_b_rung:
        winning_claim = claim_a
        winning_rung = claim_a_rung
        losing_claim = claim_b
        losing_rung = claim_b_rung
    else:
        winning_claim = claim_b
        winning_rung = claim_b_rung
        losing_claim = claim_a
        losing_rung = claim_a_rung

    severity = CONTRADICTION_SEVERITY.get(contradiction_type, ContradictionSeverity.MEDIUM)
    resolution_path = CONTRADICTION_RESOLUTION.get(contradiction_type, ResolutionPath.ESCALATE)

    # Verdict based on severity
    if severity == ContradictionSeverity.FATAL:
        verdict = "VOID"
    elif severity == ContradictionSeverity.HIGH:
        verdict = "HOLD"
    elif severity == ContradictionSeverity.MEDIUM:
        verdict = "FLAG"
    else:
        verdict = "IGNORE"

    return ContradictionRecord(
        contradiction_id=contradiction_id or str(uuid.uuid4())[:12],
        contradiction_type=contradiction_type,
        severity=severity,
        resolution_path=resolution_path,
        claim_a=claim_a,
        claim_a_rung=claim_a_rung,
        claim_a_tool=claim_a_tool,
        claim_b=claim_b,
        claim_b_rung=claim_b_rung,
        claim_b_tool=claim_b_tool,
        winning_claim=winning_claim,
        winning_rung=winning_rung,
        losing_claim=losing_claim,
        losing_rung=losing_rung,
        verdict=verdict,
        session_id=session_id,
        **kwargs,
    )
