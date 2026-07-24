"""Strict Pydantic seismic noun set (MASTER FORGE W1).

Section · SectionRef · AxisCalibration · Point2D · Polyline2D · Horizon · Fault
FaultCutoff · Hypothesis · WitnessProvenance · GateResult · InterpretationBundle
CompactInterpretationResult · RenderArtifact

Core geometry: extra=forbid, strict=True, frozen=True.
No true-depth from image pixels or TWT alone.
Vendor extensions: attachments only — never extra=allow on core contracts.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictFrozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class CoordinateDomain(str, Enum):
    PIXEL = "pixel"
    TRACE = "trace"
    CDP = "cdp"
    DISTANCE_M = "distance_m"
    TIME_MS = "time_ms"
    DEPTH_M = "depth_m"


class EpistemicLabel(str, Enum):
    OBS = "OBS"  # observed
    DER = "DER"  # derived
    INT = "INT"  # interpreted
    SPEC = "SPEC"  # speculative


class HypothesisStatus(str, Enum):
    UNTESTED = "UNTESTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    SURVIVES_CURRENT_TESTS = "SURVIVES_CURRENT_TESTS"
    REJECTED = "REJECTED"


class CalibrationStatus(str, Enum):
    UNCALIBRATED = "UNCALIBRATED"
    PARTIAL = "PARTIAL"
    CALIBRATED = "CALIBRATED"


class GateStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    KILL = "KILL"
    UNMEASURED = "UNMEASURED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FaultKinematicStatus(str, Enum):
    UNTESTED = "UNTESTED"
    NORMAL = "NORMAL"
    REVERSE = "REVERSE"
    STRIKE_SLIP = "STRIKE_SLIP"
    REACTIVATED = "REACTIVATED"
    INCONCLUSIVE = "INCONCLUSIVE"


class Point2D(StrictFrozen):
    x: float
    y: float
    domain: CoordinateDomain = CoordinateDomain.PIXEL
    horizontal_unit: str = "pixel"
    vertical_unit: str = "pixel"
    epistemic: EpistemicLabel = EpistemicLabel.SPEC
    source_section: str | None = None
    source_hash: str | None = None
    order_index: int = 0


class Polyline2D(StrictFrozen):
    points: tuple[Point2D, ...]
    domain: CoordinateDomain = CoordinateDomain.PIXEL
    horizontal_unit: str = "pixel"
    vertical_unit: str = "pixel"
    source_section: str | None = None
    source_hash: str | None = None
    epistemic: EpistemicLabel = EpistemicLabel.SPEC
    ordered: bool = True

    @field_validator("points")
    @classmethod
    def _min_points(cls, v: tuple[Point2D, ...]) -> tuple[Point2D, ...]:
        if len(v) < 2:
            raise ValueError("Polyline2D requires ≥2 points")
        return v


class AxisCalibration(StrictFrozen):
    """Earth-physics scale. Must be explicit — never silent workspace inherit."""

    horizontal_unit: str = "trace"  # trace | cdp | m
    vertical_unit: str = "ms"  # ms | m
    domain: Literal["time", "depth"] = "time"
    vertical_exaggeration: float | None = None
    bin_spacing_m: float | None = None
    sample_interval_ms: float | None = None
    section_azimuth_deg: float | None = None
    polarity_convention: Literal["SEG_NORMAL", "SEG_REVERSE", "UNKNOWN"] = "UNKNOWN"
    datum: str | None = None
    crs: str | None = None
    velocity_td: tuple[dict[str, float], ...] | None = None  # [{twt_ms, depth_m}]
    velocity_linear_m_s: float | None = None
    well_tie: dict[str, Any] | None = None
    calibration_hash: str | None = None
    calibrated: bool = False
    bound: bool = False  # visible calibration receipt bound


class Section(StrictFrozen):
    section_id: str
    source_hash: str
    input_class: Literal["image_only", "segy_slice", "segy_2d", "segy_3d", "unknown"] = "unknown"
    domain: Literal["time", "depth"] = "time"
    axis_calibration: AxisCalibration | None = None
    image_path: str | None = None
    attachments: dict[str, Any] = Field(default_factory=dict)


class SectionRef(StrictFrozen):
    section_id: str
    source_hash: str


class Fault(StrictFrozen):
    fault_id: str
    geometry: Polyline2D
    # Dip family — never invent true dip from image alone
    image_dip_deg: float | None = None
    apparent_section_dip_deg: float | None = None
    true_subsurface_dip_deg: float | None = None
    dip_basis: Literal["image_pixel", "section_apparent", "true_subsurface", "unknown"] | None = None
    dip_direction: str | None = None
    fault_strike_deg: float | None = None
    section_azimuth_deg: float | None = None
    kinematic_claim: str | None = None  # claim only
    kinematic_status: FaultKinematicStatus = FaultKinematicStatus.UNTESTED
    regime_prior: str | None = None
    throw_profile: tuple[float, ...] | None = None
    max_displacement: float | None = None
    length_m: float | None = None
    artifact: bool = False
    witness_id: str | None = None
    attachments: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _no_true_dip_without_basis(self) -> Fault:
        if self.true_subsurface_dip_deg is not None:
            if self.dip_basis not in ("true_subsurface",):
                # allow if dip_basis explicitly true_subsurface
                if self.dip_basis != "true_subsurface":
                    raise ValueError(
                        "true_subsurface_dip_deg requires dip_basis='true_subsurface' "
                        "(need scale+azimuth+strike/T–D — not image pixels alone)"
                    )
        return self


class Horizon(StrictFrozen):
    horizon_id: str
    pixel_geometry: Polyline2D | None = None
    time_geometry: Polyline2D | None = None
    depth_geometry: Polyline2D | None = None
    conversion_basis: Literal["checkshot", "vsp", "velocity_model", "regional_prior", "none", None] | None = None
    order_index: int = 0
    witness_id: str | None = None
    attachments: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _depth_requires_basis(self) -> Horizon:
        if self.depth_geometry is not None:
            if self.conversion_basis in (None, "none"):
                raise ValueError(
                    "depth_geometry requires conversion_basis in "
                    "{checkshot,vsp,velocity_model,regional_prior} — never from TWT alone"
                )
            if self.conversion_basis == "regional_prior":
                # allowed but SPEC
                pass
        return self


class FaultCutoff(StrictFrozen):
    """CutoffPair — hanging-wall / footwall sense (discrimination chain)."""

    horizon_id: str
    fault_id: str
    hw_twt: float | None = None
    fw_twt: float | None = None
    hw_depth_m: float | None = None
    fw_depth_m: float | None = None
    sense: Literal["normal_slip", "reverse_slip", "ambiguous", "unmeasured"] = "unmeasured"
    throw_ms: float | None = None
    throw_m: float | None = None
    fault_cmp: float | None = None
    epistemic: EpistemicLabel = EpistemicLabel.DER


class WitnessProvenance(StrictFrozen):
    witness_id: str
    witness_type: Literal[
        "classical_cv",
        "vlm",
        "human",
        "geological_transform",
        "empty_conceptual",
        "independent_model",
        "primary",
    ]
    model_or_method: str = ""
    prompt_hash: str | None = None
    source_geometry_hash: str | None = None
    derivation: str = ""


class GateResult(StrictFrozen):
    gate_id: str
    status: GateStatus
    inputs_used: tuple[str, ...] = ()
    measurement_units: str = ""
    equation_or_rule: str = ""
    threshold_source: str = ""
    reason: str = ""
    missing_inputs: tuple[str, ...] = ()
    receipt_hash: str | None = None
    findings: tuple[dict[str, Any], ...] = ()


class Hypothesis(StrictFrozen):
    hypothesis_id: str
    witness: WitnessProvenance
    structural_style: str = "unknown"
    kinematic_claims: tuple[str, ...] = ()
    faults: tuple[Fault, ...] = ()
    horizons: tuple[Horizon, ...] = ()
    cutoffs: tuple[FaultCutoff, ...] = ()
    supporting_evidence: tuple[str, ...] = ()
    contradicting_evidence: tuple[str, ...] = ()
    unresolved_measurements: tuple[str, ...] = ()
    gate_results: tuple[GateResult, ...] = ()
    status: HypothesisStatus = HypothesisStatus.UNTESTED
    evidence_coverage: float = 0.0  # measured_applicable / applicable — NOT probability
    calibration_status: CalibrationStatus = CalibrationStatus.UNCALIBRATED
    confidence_value: float | None = None  # null unless benchmark_calibrated
    confidence_basis: str | None = None
    combined_gate_verdict: str | None = None
    render_ref: str | None = None
    attachments: dict[str, Any] = Field(default_factory=dict)


class RenderArtifact(StrictFrozen):
    render_ref: str
    render_hash: str
    source_hash: str
    format: Literal["png", "svg"] = "png"
    hypothesis_id: str | None = None
    style_version: str = "geox_render_v1"
    path: str | None = None


class CompactHypothesisSummary(StrictFrozen):
    hypothesis_id: str
    status: HypothesisStatus
    gate_summary: dict[str, int] = Field(default_factory=dict)
    render_ref: str | None = None
    witness_type: str | None = None


class CompactInterpretationResult(StrictFrozen):
    status: str = "OK"
    local_verdict: Literal["QUALIFIED_CANDIDATE"] = "QUALIFIED_CANDIDATE"
    seal_authority: Literal["arifOS_only"] = "arifOS_only"
    preferred_hypothesis: None = None
    input_class: str
    calibration_status: CalibrationStatus = CalibrationStatus.UNCALIBRATED
    hypotheses: tuple[CompactHypothesisSummary, ...] = ()
    detail_ref: str | None = None
    receipt_hash: str | None = None
    render_refs: tuple[str, ...] = ()


class InterpretationBundle(StrictFrozen):
    """Full detail bundle — stored behind detail_ref, not default MCP payload."""

    observations: dict[str, Any] = Field(default_factory=dict)
    hypotheses: tuple[Hypothesis, ...] = ()
    preferred_hypothesis: None = None
    limitations: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    local_verdict: Literal["QUALIFIED_CANDIDATE"] = "QUALIFIED_CANDIDATE"
    seal_authority: Literal["arifOS_only"] = "arifOS_only"
    seal_eligibility: bool = False
    renders: tuple[RenderArtifact, ...] = ()
    cutoffs: tuple[FaultCutoff, ...] = ()
    section: SectionRef | None = None


def schema_snapshot() -> dict[str, Any]:
    """Stable JSON schemas for core nouns."""
    models = {
        "Point2D": Point2D,
        "Polyline2D": Polyline2D,
        "AxisCalibration": AxisCalibration,
        "Section": Section,
        "SectionRef": SectionRef,
        "Fault": Fault,
        "Horizon": Horizon,
        "FaultCutoff": FaultCutoff,
        "WitnessProvenance": WitnessProvenance,
        "GateResult": GateResult,
        "Hypothesis": Hypothesis,
        "RenderArtifact": RenderArtifact,
        "CompactInterpretationResult": CompactInterpretationResult,
        "InterpretationBundle": InterpretationBundle,
    }
    return {k: v.model_json_schema() for k, v in models.items()}
