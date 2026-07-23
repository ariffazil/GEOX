"""Pydantic contracts for geox_seismic_interpret (B-final).

Discriminated unions by mode. extra=forbid per branch.
interpretation_bundle is the single semantic output envelope.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


# ── Calibration ──────────────────────────────────────────────────────────────


class AxisSpec(StrictModel):
    type: Literal[
        "trace",
        "cdp",
        "distance_m",
        "inline",
        "crossline",
        "time_ms",
        "depth_m",
        "pixel",
        "unknown",
    ] = "unknown"
    values: list[float] | None = None
    unit: str | None = None


class Calibration(StrictModel):
    """Measurement identity / scale. Missing scale → gates UNMEASURED."""

    x_axis: AxisSpec | None = None
    vertical_axis: AxisSpec | None = None
    vertical_exaggeration: float | None = None
    polarity: Literal["SEG_NORMAL", "SEG_REVERSE", "UNKNOWN"] = "UNKNOWN"
    phase_degrees: float | None = None
    sample_interval_ms: float | None = None
    input_class: Literal["image_only", "segy_slice", "segy_2d", "segy_3d", "unknown"] = "unknown"
    calibrated: bool = False  # explicit flag when axes are trusted
    sha256: str | None = None
    crs: str | None = None
    vertical_datum: str | None = None


class EarthConstraints(StrictModel):
    wells: list[dict[str, Any]] = Field(default_factory=list)
    formation_tops: list[dict[str, Any]] = Field(default_factory=list)
    checkshots: list[dict[str, Any]] = Field(default_factory=list)
    velocity_model_ref: str | None = None
    stratigraphic_framework_ref: str | None = None
    structural_regime: Literal[
        "extension", "contraction", "strike_slip", "salt", "unknown"
    ] = "unknown"


class InterpretRequestFlags(StrictModel):
    horizons: bool = True
    faults: bool = True
    structural_framework: bool = True
    restoration: bool = False
    hypothesis_count: int = Field(default=3, ge=1, le=10)


# ── Mode-discriminated requests ──────────────────────────────────────────────


class HorizonContrastMode(StrictModel):
    mode: Literal["horizon_contrast"] = "horizon_contrast"
    attribute_data: dict[str, list[float]]
    depth: list[float]
    geological_query: str = "sequence_boundary"
    well_ties: dict[str, float] | None = None
    peak_threshold: float = 1.5
    min_separation_m: float = 20.0
    custom_query: dict[str, float] | None = None
    calibration: Calibration | None = None


class StructureValidateMode(StrictModel):
    mode: Literal["structure_validate"] = "structure_validate"
    framework: dict[str, Any] | None = None
    faults: list[dict[str, Any]] | None = None
    horizons: list[dict[str, Any]] | None = None
    calibration: Calibration | None = None
    earth_constraints: EarthConstraints | None = None
    request: InterpretRequestFlags | None = None
    claim_text: str = ""


class SectionImageMode(StrictModel):
    mode: Literal["interpret_section", "rsi_pipeline", "section_image"] = "interpret_section"
    image_path: str | None = None
    artifact_ref: str | None = None
    source_uri: str | None = None
    max_faults: int = 20
    max_horizons: int = 12
    calibration: Calibration | None = None
    earth_constraints: EarthConstraints | None = None
    request: InterpretRequestFlags | None = None


class SegySliceMode(StrictModel):
    mode: Literal["segy_slice", "segy_2d"] = "segy_slice"
    segy_path: str | None = None
    source_uri: str | None = None
    volume_ref: str | None = None
    frame_index: int = 0
    orientation: str = "inline"
    calibration: Calibration | None = None


class FaultSticksMode(StrictModel):
    mode: Literal["fault_sticks"] = "fault_sticks"
    source_uri: str = ""
    source_type: str = "csv"


class VolumeFrameMode(StrictModel):
    mode: Literal["volume_frame"] = "volume_frame"
    action: str = "get"
    volume_ref: str = ""
    frame_index: int = 0
    orientation: str = "inline"
    provenance: str = "fixture"
    image_data: str | None = None


class BlendMode(StrictModel):
    mode: Literal["blend"] = "blend"
    blend_mode: str = "alpha"
    volume_ref: str = ""
    provenance: str = "fixture"


class InterpretBundleMode(StrictModel):
    """Full propose→validate→compare loop emitting interpretation_bundle."""

    mode: Literal["interpret"] = "interpret"
    artifact_ref: str | None = None
    artifact_type: Literal[
        "section_image", "segy_2d", "segy_3d", "interpreted_section", "framework"
    ] = "framework"
    image_path: str | None = None
    segy_path: str | None = None
    framework: dict[str, Any] | None = None
    faults: list[dict[str, Any]] | None = None
    horizons: list[dict[str, Any]] | None = None
    calibration: Calibration | None = None
    earth_constraints: EarthConstraints | None = None
    request: InterpretRequestFlags = Field(default_factory=InterpretRequestFlags)


InterpretRequest = Annotated[
    HorizonContrastMode
    | StructureValidateMode
    | SectionImageMode
    | SegySliceMode
    | FaultSticksMode
    | VolumeFrameMode
    | BlendMode
    | InterpretBundleMode,
    Field(discriminator="mode"),
]


# ── Output bundle ────────────────────────────────────────────────────────────


class GateResultModel(StrictModel):
    model_config = ConfigDict(extra="allow")  # allow findings etc.
    gate_id: str
    status: Literal["PASS", "WARN", "KILL", "UNMEASURED"]
    equation: str = ""
    receipt_hash: str = ""
    reason: str = ""


class HypothesisModel(StrictModel):
    model_config = ConfigDict(extra="allow")
    hypothesis_id: str
    horizons: list[dict[str, Any]] = Field(default_factory=list)
    faults: list[dict[str, Any]] = Field(default_factory=list)
    fault_blocks: list[dict[str, Any]] = Field(default_factory=list)
    structural_style: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    epistemic_class: Literal[
        "OBSERVATION", "DERIVATION", "INTERPRETATION", "SPECULATION"
    ] = "INTERPRETATION"
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    physics_gates: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    combined_gate_verdict: str | None = None


class LimitationsModel(StrictModel):
    missing_scale: bool = False
    missing_velocity: bool = True
    image_only: bool = False
    unmeasured_gates: list[str] = Field(default_factory=list)


class ProvenanceModel(StrictModel):
    model_config = ConfigDict(extra="allow")
    input_hash: str | None = None
    model_revision: str = "geox-seismic-interpret-b-final"
    algorithm_versions: dict[str, str] = Field(default_factory=dict)
    parameter_hash: str | None = None
    tool: str = "geox_seismic_interpret"


class InterpretationBundle(StrictModel):
    """Single semantic output — not a 'correct Earth model'."""

    model_config = ConfigDict(extra="allow")
    observations: dict[str, Any] = Field(default_factory=dict)
    hypotheses: list[HypothesisModel] = Field(default_factory=list)
    preferred_hypothesis: str | None = None  # always null unless human sets
    limitations: LimitationsModel = Field(default_factory=LimitationsModel)
    provenance: ProvenanceModel = Field(default_factory=ProvenanceModel)
    local_verdict: Literal["QUALIFIED_CANDIDATE"] = "QUALIFIED_CANDIDATE"
    seal_authority: Literal["arifOS_only"] = "arifOS_only"
    seal_eligibility: bool = False
    governance_status: str = "HOLD"


def interpret_request_json_schema() -> dict[str, Any]:
    """JSON Schema for the discriminated InterpretRequest union."""
    # Pydantic v2: use TypeAdapter for Annotated unions
    from pydantic import TypeAdapter

    return TypeAdapter(InterpretRequest).json_schema()


def bundle_json_schema() -> dict[str, Any]:
    return InterpretationBundle.model_json_schema()
