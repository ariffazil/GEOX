"""Tectonic event ontology — schema for event classes and transitions.

The fundamental unit of tectonic reasoning in GEOX.
A restoration computes geometry differences.
An event schema interprets those differences as tectonic consequences.

TECT-001: Observation ≠ Explanation.
TECT-006: Basin evolution is event sequence, not geometry sequence.

Forged: 2026-09-14
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Event Classes — what can happen in a basin
# ═══════════════════════════════════════════════════════════════════════════


class TectonicEventClass(StrEnum):
    """Canonical tectonic event classes.

    Not exhaustive — UnknownEvent is always valid.
    New classes may be proposed but require evidence and F13 ratification.
    """

    RIFT_PULSE = "rift_pulse"
    SAG_PHASE = "sag_phase"
    STRIKE_SLIP_PHASE = "strike_slip_phase"
    COMPRESSION_PHASE = "compression_phase"
    INVERSION_PHASE = "inversion_phase"
    CARBONATE_FACTORY_ON = "carbonate_factory_on"
    CARBONATE_FACTORY_OFF = "carbonate_factory_off"
    BREAKUP_PHASE = "breakup_phase"
    THERMAL_RELAXATION = "thermal_relaxation"
    COLLISION_ONSET = "collision_onset"
    SLAB_BREAKOFF = "slab_breakoff"
    GRAVITY_DEFORMATION = "gravity_deformation"
    MUD_EXPULSION = "mud_expulsion"
    SUBSIDENCE_REGIME_CHANGE = "subsidence_regime_change"
    STRESS_ROTATION = "stress_rotation"
    FAULT_REACTIVATION = "fault_reactivation"
    UNKNOWN_EVENT = "unknown_event"


class StressRegime(StrEnum):
    """Andersonian stress classification."""

    EXTENSIONAL = "extensional"
    STRIKE_SLIP = "strike_slip"
    COMPRESSIVE = "compressive"
    TRANSTENSIONAL = "transtensional"
    TRANSPRESSIVE = "transpressive"
    UNKNOWN = "unknown"


class ConfidenceLevel(StrEnum):
    """Epistemic confidence for tectonic interpretations."""

    CONFIRMED = "confirmed"  # Cross-cutting, unconformity, definitive evidence
    PROBABLE = "probable"  # Multiple independent lines of evidence
    PLAUSIBLE = "plausible"  # Consistent with evidence, not uniquely determined
    SPECULATIVE = "speculative"  # Possible but weakly constrained
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════════════
# Core Schemas
# ═══════════════════════════════════════════════════════════════════════════


class TectonicEvent(BaseModel):
    """A single tectonic event in a basin's history.

    TECT-006: Basin evolution is event sequence, not geometry sequence.
    """

    event_id: str = Field(..., description="Unique event identifier")
    event_class: TectonicEventClass = Field(..., description="Canonical event class")
    name: str = Field(..., description="Human-readable event name")
    age_range_ma: tuple[float, float] = Field(
        ..., description="(older, younger) age bounds in Ma"
    )
    stress_regime: StressRegime = Field(
        default=StressRegime.UNKNOWN, description="Stress regime during this event"
    )
    stress_orientation_deg: float | None = Field(
        default=None,
        ge=0.0,
        lt=360.0,
        description="Shmax or σ1 azimuth (degrees clockwise from N)",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Evidence supporting this event (cross-cutting, biostrat, etc.)",
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.UNKNOWN,
        description="Epistemic confidence in this event's existence and timing",
    )
    kinematics: dict[str, Any] = Field(
        default_factory=dict,
        description="Kinematic parameters (slip rate, displacement vector, etc.)",
    )
    associated_faults: list[str] = Field(
        default_factory=list,
        description="Fault IDs associated with this event",
    )
    notes: str = Field(default="")


class EventTransition(BaseModel):
    """A transition between two tectonic events.

    TECT-009: The diagnostic signal is the transition, not the value.
    """

    from_event_id: str = Field(..., description="Source event ID")
    to_event_id: str = Field(..., description="Target event ID")
    transition_type: str = Field(
        ...,
        description=(
            "Type of transition: stress_rotation, regime_change, "
            "reactivation, onset, cessation"
        ),
    )
    signal: str = Field(
        ...,
        description="What observable signal marks this transition",
    )
    observation: str = Field(
        ...,
        description="What can be observed in the data (geometry, unconformity, etc.)",
    )
    age_ma: float | None = Field(
        default=None, description="Best estimate of transition age (Ma)"
    )
    age_uncertainty_ma: float | None = Field(
        default=None, description="Uncertainty on transition age (Ma)"
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.UNKNOWN,
        description="Confidence that this transition occurred",
    )


class TectonicScenario(BaseModel):
    """A complete tectonic scenario for a basin.

    TECT-007: Restoration products support multiple hypotheses.
    TECT-008: Interpretation must preserve ambiguity.
    """

    scenario_id: str = Field(..., description="Unique scenario identifier")
    basin_name: str = Field(..., description="Basin this scenario applies to")
    events: list[TectonicEvent] = Field(
        ..., description="Ordered sequence of tectonic events"
    )
    transitions: list[EventTransition] = Field(
        default_factory=list, description="Transitions between events"
    )
    probability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relative probability of this scenario (across competing scenarios)",
    )
    competing_scenarios: list[str] = Field(
        default_factory=list,
        description="IDs of other scenarios that explain the same observations",
    )
    evidence_for: list[str] = Field(
        default_factory=list, description="Evidence that supports this scenario"
    )
    evidence_against: list[str] = Field(
        default_factory=list, description="Evidence that challenges this scenario"
    )
    falsification_criteria: list[str] = Field(
        default_factory=list,
        description="What evidence would falsify this scenario",
    )
    assumptions: list[str] = Field(
        default_factory=list, description="Key assumptions in this scenario"
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Source of this scenario (literature, interpreter, model)",
    )


class RestorationObservation(BaseModel):
    """A restoration product framed as an observation, not an explanation.

    TECT-001: Observation ≠ Explanation.
    TECT-007: Products support multiple hypotheses.
    """

    observation_id: str = Field(..., description="Unique observation identifier")
    product_type: str = Field(
        ...,
        description=(
            "Type of restoration product: accommodation, subsidence, "
            "fill_ratio, thickness, uncertainty"
        ),
    )
    value: float | None = Field(default=None, description="Numeric value if scalar")
    grid_ref: str | None = Field(
        default=None, description="Reference to grid file if spatial"
    )
    restoration_scenario_id: str = Field(
        ..., description="ID of the restoration scenario that produced this"
    )
    source_state: str = Field(
        ..., description="Present-day or restored state description"
    )
    target_state: str = Field(
        ..., description="The other state used in differencing"
    )
    equation: str = Field(
        ..., description="The computation that produced this product"
    )
    sign_convention: str = Field(
        ..., description="Z convention used (positive=up, positive=down, etc.)"
    )
    units: str = Field(..., description="Units of the value/grid")
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions that went into this computation",
    )
    uncertainty: dict[str, Any] = Field(
        default_factory=dict,
        description="Uncertainty envelope (numerical, spatial, geological)",
    )
    tectonic_hypotheses: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Competing tectonic explanations for this observation. "
            "Each has: hypothesis, probability, evidence_for, evidence_against"
        ),
    )
    anomaly_flags: list[str] = Field(
        default_factory=list,
        description="Anomaly flags (e.g., fill_ratio_gt_1, extrapolation_beyond_calibrated)",
    )
    requires_diagnostic_review: bool = Field(
        default=False,
        description="True if observation triggered a diagnostic guard",
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Full provenance chain from input data to this observation",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Diagnostic Guard — EUREKA-03 (fill_ratio > 1)
# ═══════════════════════════════════════════════════════════════════════════


class DiagnosticChecklist(BaseModel):
    """Diagnostic checklist for anomalous observations.

    TECT-001: An observation is not an explanation.
    fill_ratio > 1 triggers this — never FAULT_ACTIVITY_CONFIRMED.
    """

    observation_id: str = Field(..., description="Observation that triggered this")
    anomaly_type: str = Field(
        ..., description="Type of anomaly (e.g., fill_ratio_gt_1)"
    )
    possible_causes: list[dict[str, str]] = Field(
        ...,
        description=(
            "Each cause has: cause, test, evidence_required, priority. "
            "Must test ALL before invoking tectonic explanation."
        ),
    )
    tectonic_explanation: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Tectonic explanation (e.g., fault_activity) — ONLY after all "
            "non-tectonic causes have been tested and excluded"
        ),
    )
    status: str = Field(
        default="PENDING_DIAGNOSTIC",
        description="Status: PENDING_DIAGNOSTIC | DIAGNOSED | ESCALATED",
    )


# Default diagnostic checklist for fill_ratio > 1
FILL_RATIO_GT1_CHECKLIST = [
    {
        "cause": "reversed_subtraction_order",
        "test": "Verify sign convention and subtraction order",
        "evidence_required": "Source and target state labels, sign convention declaration",
        "priority": "1 (test first)",
    },
    {
        "cause": "inconsistent_restoration_ages",
        "test": "Verify ages of both restoration states are correct and internally consistent",
        "evidence_required": "Age assignments, biostrat calibration, unconformity evidence",
        "priority": "2",
    },
    {
        "cause": "mismatched_surface_extents",
        "test": "Verify both surfaces cover the same geographic area",
        "evidence_required": "Grid extents, clip boundaries, null cell distribution",
        "priority": "3",
    },
    {
        "cause": "unit_or_datum_mismatch",
        "test": "Verify CRS, XY units, Z units, datum, and polarity match",
        "evidence_required": "CRS metadata, unit declarations, datum reference",
        "priority": "4",
    },
    {
        "cause": "erosion_or_hiatus",
        "test": "Check for unconformity surfaces or erosion between restoration states",
        "evidence_required": "Biostrat gaps, seismic onlap/downlap, missing section",
        "priority": "5",
    },
    {
        "cause": "compaction_model_mismatch",
        "test": "Verify compaction curve is appropriate for lithology and depth range",
        "evidence_required": "Compaction curve name, measured depth limit, extrapolation interval",
        "priority": "6",
    },
    {
        "cause": "interpolation_artefact",
        "test": "Check grid interpolation method and cell size relative to data density",
        "evidence_required": "Interpolation method, cell size, data point density map",
        "priority": "7",
    },
    {
        "cause": "missing_structural_displacement",
        "test": "Check for faults with displacement not represented in the restoration",
        "evidence_required": "Fault map, throw estimates, displacement profiles",
        "priority": "8",
    },
    {
        "cause": "inappropriate_facies_or_lithology_assumption",
        "test": "Verify lithology assignment is appropriate for the depositional setting",
        "evidence_required": "Facies map, well lithology logs, analogue data",
        "priority": "9",
    },
    {
        "cause": "fault_activity",
        "test": "Only after ALL above causes are excluded",
        "evidence_required": "Independent structural evidence (seismic, gravity, stress)",
        "priority": "10 (last resort)",
    },
]


__all__ = [
    "TectonicEventClass",
    "StressRegime",
    "ConfidenceLevel",
    "TectonicEvent",
    "EventTransition",
    "TectonicScenario",
    "RestorationObservation",
    "DiagnosticChecklist",
    "FILL_RATIO_GT1_CHECKLIST",
]
