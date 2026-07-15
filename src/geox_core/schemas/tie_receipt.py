"""
GEOX Tie Receipt Schema — Seismic-to-Well Tie Evidence Envelope
═══════════════════════════════════════════════════════════════════════════════════

The receipt tells the system what it is allowed to believe.

Every seismic-to-well tie produces a receipt — not just a correlation score,
but a full evidence envelope covering: data inputs, calibration quality,
error classification, rock physics status, decision permission, and uncertainty.

This is the metabolizer's memory. Without it, a tie is a picture.
With it, a tie is governance evidence.

Schema:   TieReceipt
Version:  1.0.0
Domain:   NATURAL_LAW
Organ:    GEOX
Floor:    F2 (truth), F7 (humility), F9 (anti-hantu), F11 (audit)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# ENUMS
# ──────────────────────────────────────────────────────────────────────────────


class ConfidenceLevel(str, Enum):
    """Confidence in a specific measurement or calibration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResidualClass(str, Enum):
    """Classified error from synthetic-vs-seismic mismatch.

    The metabolizer's core output: what kind of wrongness remains.
    """

    TIME_DEPTH_ERROR = "time_depth_error"  # Wrong velocity model
    WAVELET_ERROR = "wavelet_error"  # Wrong source shape/phase
    LOG_CONDITIONING_ERROR = "log_conditioning_error"  # Bad sonic/density, washout, invasion
    CHECKSHOT_VSP_ERROR = "checkshot_vsp_error"  # Bad depth-time calibration
    PROCESSING_ERROR = "processing_error"  # Migration, phase, statics, multiples
    STRATIGRAPHIC_ERROR = "stratigraphic_error"  # Wrong horizon pick/correlation
    ROCK_PHYSICS_ERROR = "rock_physics_error"  # Wrong elastic-fluid-lithology link
    SCALE_ERROR = "scale_error"  # Well cm/m vs seismic tens of meters
    LATERAL_HETEROGENEITY = "lateral_heterogeneity"  # Well local, seismic spatial
    FLUID_PRESSURE_ERROR = "fluid_pressure_error"  # HC/brine/gas/overpressure misunderstood
    STRUCTURAL_ERROR = "structural_error"  # Faults, dip, migration effects
    GOVERNANCE_ERROR = "governance_error"  # Decision promoted beyond evidence
    GOOD_TIE = "good_tie"  # Residual within acceptable range
    UNEXPLAINED = "unexplained"  # Residual not yet classified


class DecisionPermission(str, Enum):
    """Whether the tie supports downstream decision-making."""

    PROCEED = "PROCEED"  # Tie supports confidence in downstream interpretation
    HOLD = "HOLD"  # Tie has issues that block certain decisions
    VOID = "VOID"  # Tie is unreliable; no decisions permitted


class WaveletSource(str, Enum):
    """Where the wavelet came from."""

    EXTRACTED = "extracted"  # Extracted from seismic data
    STATISTICAL = "statistical"  # Statistical estimate (auto-correlation)
    ASSUMED = "assumed"  # Assumed Ricker/Ormsby/etc.
    WELL_DERIVED = "well_derived"  # Derived from well-seismic match


class LogQuality(str, Enum):
    """Quality flag for individual well log curves."""

    GOOD = "good"
    DEGRADED = "degraded"  # Some washout, invasion, or environmental effects
    POOR = "poor"  # Significant borehole condition issues
    ABSENT = "absent"  # Curve not available


class LithologySeparability(str, Enum):
    """Can rock physics distinguish lithology classes in this dataset?"""

    LOW = "low"  # Overlapping elastic properties
    MEDIUM = "medium"  # Partial separation with uncertainty
    HIGH = "high"  # Clean separation in impedance/VP/VS space


# ──────────────────────────────────────────────────────────────────────────────
# SUB-MODELS
# ──────────────────────────────────────────────────────────────────────────────


class LogStatus(BaseModel):
    """Quality status of a single well log curve used in the tie."""

    curve_name: str = Field(description="LAS curve mnemonic (e.g. DT, RHOB, GR, RT)")
    quality: LogQuality = Field(description="Quality assessment")
    null_pct: float = Field(default=0.0, ge=0.0, le=100.0, description="Percentage of null values")
    environmental_corrections: list[str] = Field(
        default_factory=list,
        description="Corrections applied (e.g. borehole, invasion, mud weight)",
    )
    notes: str = Field(default="", description="Any known issues with this curve")


class TimeDepthControl(BaseModel):
    """Quality of the time-depth relationship used for the tie."""

    checkshot_present: bool = Field(default=False, description="Was checkshot data available?")
    vsp_present: bool = Field(default=False, description="Was VSP data available?")
    checkshot_count: int = Field(default=0, ge=0, description="Number of checkshot points")
    drift_max_ms: float | None = Field(
        default=None,
        description="Maximum checkshot drift in ms (Physics9 invariant #9: curvature threshold)",
    )
    confidence: ConfidenceLevel = Field(description="Overall time-depth calibration confidence")
    notes: str = Field(default="", description="Known issues with time-depth control")


class WaveletInfo(BaseModel):
    """Wavelet used for synthetic seismogram generation."""

    source: WaveletSource = Field(description="How the wavelet was obtained")
    phase_degrees: float | None = Field(default=None, description="Phase angle in degrees")
    frequency_hz: float | None = Field(default=None, description="Dominant frequency")
    phase_confidence: ConfidenceLevel = Field(description="Confidence in phase estimate")
    notes: str = Field(default="", description="Wavelet-related caveats")


class TieQuality(BaseModel):
    """Measured quality of the synthetic-to-seismic match."""

    correlation_window: str = Field(
        default="",
        description="Depth/time interval over which correlation was measured",
    )
    correlation_score: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Cross-correlation coefficient (Physics9 #7: r >= 0.70 for PASS)",
    )
    residual_class: ResidualClass = Field(description="Classified error type")
    residual_description: str = Field(
        default="",
        description="Human-readable explanation of the residual",
    )
    residual_severity: str = Field(
        default="low",
        description="low | medium | high | critical",
    )


class RockPhysicsStatus(BaseModel):
    """Rock physics assessment for the tied interval."""

    lithology_separability: LithologySeparability = Field(description="Can elastic properties distinguish lithology?")
    fluid_separability: LithologySeparability = Field(description="Can elastic properties distinguish fluid type?")
    impedance_overlap_risk: bool = Field(default=False, description="Do sand and shale impedance ranges overlap?")
    tuning_thickness_m: float | None = Field(
        default=None,
        description="Estimated tuning thickness in meters (if computed)",
    )
    notes: str = Field(default="", description="Rock physics caveats")


class InversionPermission(BaseModel):
    """Whether seismic inversion is permitted given tie quality."""

    allowed: bool = Field(description="Is inversion permitted?")
    constraints: list[str] = Field(
        default_factory=list,
        description="Specific constraints on inversion (e.g. 'low-frequency prior uncertain')",
    )
    inversion_type_recommended: str = Field(
        default="",
        description="Recommended inversion type (acoustic, elastic, stochastic, geostatistical)",
    )


class UncertaintyAssessment(BaseModel):
    """Uncertainty state for key interpretation variables."""

    depth: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    fluid: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    thickness: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    lateral_continuity: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    structural_trap: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    major_unknowns: list[str] = Field(
        default_factory=list,
        description="Key unconstrained variables",
    )


# ──────────────────────────────────────────────────────────────────────────────
# TIE RECEIPT — The complete evidence envelope
# ──────────────────────────────────────────────────────────────────────────────


class TieReceipt(BaseModel):
    """Seismic-to-well tie evidence envelope.

    This receipt tells the system what it is allowed to believe.
    The receipt matters more than the image of the tie.

    schema:   TieReceipt
    version:  1.0.0
    domain:   NATURAL_LAW
    organ:    GEOX
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    well_name: str = Field(description="Well identifier")
    seismic_volume: str = Field(default="", description="Seismic volume name/ID")
    tie_id: str = Field(default="", description="Unique tie receipt ID")
    session_id: str | None = Field(default=None, description="Governed session ID")

    # ── Conventions ──────────────────────────────────────────────────────────
    polarity_convention: str = Field(
        default="",
        description="SEG_NORMAL or SEG_REVERSE",
    )
    phase_convention: str = Field(
        default="",
        description="Zero-phase, minimum-phase, or mixed",
    )
    seismic_datum: str = Field(default="", description="Seismic datum (e.g. MSL, KB)")
    well_datum: str = Field(default="", description="Well datum (e.g. KB, MSL)")
    depth_basis: str = Field(default="MD", description="MD, TVD, or TVDSS")

    # ── Data inputs ──────────────────────────────────────────────────────────
    logs_used: list[str] = Field(
        default_factory=list,
        description="Which log curves were used (e.g. sonic, density, GR, resistivity)",
    )
    log_status: list[LogStatus] = Field(
        default_factory=list,
        description="Quality status of each log curve",
    )

    # ── Calibration ─────────────────────────────────────────────────────────
    time_depth_control: TimeDepthControl = Field(
        default_factory=lambda: TimeDepthControl(confidence=ConfidenceLevel.LOW),
        description="Time-depth calibration quality",
    )
    wavelet: WaveletInfo = Field(
        default_factory=lambda: WaveletInfo(source=WaveletSource.ASSUMED, phase_confidence=ConfidenceLevel.LOW),
        description="Wavelet used for synthetic",
    )

    # ── Tie quality ─────────────────────────────────────────────────────────
    tie_quality: TieQuality = Field(
        default_factory=lambda: TieQuality(residual_class=ResidualClass.UNEXPLAINED),
        description="Measured synthetic-to-seismic match quality",
    )

    # ── Geological markers ───────────────────────────────────────────────────
    geological_markers: list[str] = Field(
        default_factory=list,
        description="Key horizons tied (e.g. top_reservoir, base_reservoir, seal)",
    )

    # ── Rock physics ─────────────────────────────────────────────────────────
    rock_physics_status: RockPhysicsStatus = Field(
        default_factory=lambda: RockPhysicsStatus(
            lithology_separability=LithologySeparability.LOW,
            fluid_separability=LithologySeparability.LOW,
        ),
        description="Rock physics assessment for the tied interval",
    )

    # ── Inversion permission ────────────────────────────────────────────────
    inversion_permission: InversionPermission = Field(
        default_factory=lambda: InversionPermission(allowed=False, constraints=["tie quality insufficient"]),
        description="Whether seismic inversion is permitted",
    )

    # ── Decision permission ─────────────────────────────────────────────────
    decision_permission: DecisionPermission = Field(
        default=DecisionPermission.HOLD,
        description="Whether the tie supports downstream decisions",
    )
    decision_reason: str = Field(
        default="",
        description="Plain-language reason for decision permission status",
    )

    # ── Uncertainty ─────────────────────────────────────────────────────────
    uncertainty: UncertaintyAssessment = Field(
        default_factory=UncertaintyAssessment,
        description="Uncertainty state for key interpretation variables",
    )

    # ── Anti-hantu ──────────────────────────────────────────────────────────
    anti_hantu_flags: list[str] = Field(
        default_factory=list,
        description="Specific anti-hantu warnings (e.g. 'amplitude ≠ hydrocarbon', 'inversion ≠ truth')",
    )

    # ── Provenance ──────────────────────────────────────────────────────────
    timestamp_utc: str = Field(description="UTC timestamp of receipt creation")
    domain_law: str = Field(default="NATURAL_LAW", description="GEOX domain law")
    physics_manifest_hash: str = Field(default="", description="SHA-256 of GEOX Physics Manifest")

    class Config:
        json_schema_extra = {
            "description": (
                "Seismic-to-well tie evidence envelope — "
                "The receipt tells the system what it is allowed to believe. "
                "DITEMPA BUKAN DIBERI"
            )
        }


# ──────────────────────────────────────────────────────────────────────────────
# BUILDER — Construct a TieReceipt from tool outputs
# ──────────────────────────────────────────────────────────────────────────────


def build_tie_receipt(
    well_name: str,
    *,
    seismic_volume: str = "",
    session_id: str | None = None,
    polarity_convention: str = "",
    phase_convention: str = "",
    seismic_datum: str = "",
    well_datum: str = "",
    depth_basis: str = "MD",
    logs_used: list[str] | None = None,
    log_status: list[dict[str, Any]] | None = None,
    time_depth_control: dict[str, Any] | None = None,
    wavelet: dict[str, Any] | None = None,
    tie_quality: dict[str, Any] | None = None,
    geological_markers: list[str] | None = None,
    rock_physics_status: dict[str, Any] | None = None,
    inversion_permission: dict[str, Any] | None = None,
    decision_permission: str = "HOLD",
    decision_reason: str = "",
    uncertainty: dict[str, Any] | None = None,
    anti_hantu_flags: list[str] | None = None,
) -> dict[str, Any]:
    """Build a TieReceipt dict from component data."""
    from datetime import UTC, datetime

    now = datetime.now(UTC).isoformat()

    # Auto-derive anti-hantu flags if not provided
    if anti_hantu_flags is None:
        anti_hantu_flags = [
            "amplitude is not hydrocarbon",
            "impedance is not lithology",
            "inversion is not truth",
            "tie is not validation unless residuals are explained",
        ]

    # Auto-derive decision permission from tie quality
    if tie_quality and tie_quality.get("residual_class") == "good_tie":
        if decision_permission == "HOLD":
            decision_permission = "PROCEED"
            if not decision_reason:
                decision_reason = "Residual within acceptable range; tie supports downstream interpretation"

    receipt = TieReceipt(
        well_name=well_name,
        seismic_volume=seismic_volume,
        tie_id=f"tie-{well_name}-{int(datetime.now(UTC).timestamp())}",
        session_id=session_id,
        polarity_convention=polarity_convention,
        phase_convention=phase_convention,
        seismic_datum=seismic_datum,
        well_datum=well_datum,
        depth_basis=depth_basis,
        logs_used=logs_used or [],
        log_status=[LogStatus(**ls) for ls in log_status] if log_status else [],
        time_depth_control=TimeDepthControl(**time_depth_control)
        if time_depth_control
        else TimeDepthControl(confidence=ConfidenceLevel.LOW),
        wavelet=WaveletInfo(**wavelet)
        if wavelet
        else WaveletInfo(source=WaveletSource.ASSUMED, phase_confidence=ConfidenceLevel.LOW),
        tie_quality=TieQuality(**tie_quality) if tie_quality else TieQuality(residual_class=ResidualClass.UNEXPLAINED),
        geological_markers=geological_markers or [],
        rock_physics_status=RockPhysicsStatus(**rock_physics_status)
        if rock_physics_status
        else RockPhysicsStatus(lithology_separability=LithologySeparability.LOW, fluid_separability=LithologySeparability.LOW),
        inversion_permission=InversionPermission(**inversion_permission)
        if inversion_permission
        else InversionPermission(allowed=False),
        decision_permission=DecisionPermission(decision_permission),
        decision_reason=decision_reason,
        uncertainty=UncertaintyAssessment(**uncertainty) if uncertainty else UncertaintyAssessment(),
        anti_hantu_flags=anti_hantu_flags,
        timestamp_utc=now,
        domain_law="NATURAL_LAW",
    )

    return receipt.model_dump()
