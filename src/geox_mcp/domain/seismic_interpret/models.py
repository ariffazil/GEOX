"""Pydantic contracts for geox_seismic_interpret (B-final).

Discriminated unions by mode. Request branches: extra=forbid + declared
transport envelope (session_id/actor_id/…) so MCP metadata is retained
and semantic typos (imagepath) still raise loudly.

Output models use extra=allow for findings attachments.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Semantic strictness — unknown fields forbidden (typo tripwire)."""

    model_config = ConfigDict(extra="forbid")


class TransportAwareRequest(StrictModel):
    """Request branch base: declared MCP transport envelope + forbid extras.

    Why not extra=\"ignore\":
      - ignore silently drops session_id/actor_id (handlers never see them)
      - ignore also swallows typos (imagepath → looks like VOID_NO_DATA)

    Why not bare extra=\"allow\":
      - loses the tripwire for misspelled semantic fields

    Declared transport keys pass validation and survive model_dump().
    Unknown semantic keys still raise ValidationError.
    """

    session_id: str | None = None
    actor_id: str | None = None
    trace_id: str | None = None
    source_sha256: str | None = None


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
    """Measurement identity / scale. Missing scale → gates UNMEASURED.

    Chat-minimal keys (bin_spacing_m, velocity_td, VE) enable auto-derive of
    K-DIP / K-THROW / K-VEL / K-RESTORE / K-GROWTH inputs.
    """

    x_axis: AxisSpec | None = None
    vertical_axis: AxisSpec | None = None
    vertical_exaggeration: float | None = None
    polarity: Literal["SEG_NORMAL", "SEG_REVERSE", "UNKNOWN"] = "UNKNOWN"
    phase_degrees: float | None = None
    sample_interval_ms: float | None = None
    sample_rate_ms: float | None = None  # alias of sample_interval_ms
    bin_spacing_m: float | None = None
    velocity_td: list[dict[str, Any]] | None = None  # [{twt_ms, depth_m}, ...]
    velocity_linear_m_s: float | None = None  # synthetic linear T–D helper
    well_tie: dict[str, Any] | None = None  # {cmp, well_ref}
    input_class: Literal["image_only", "segy_slice", "segy_2d", "segy_3d", "unknown"] = "unknown"
    calibrated: bool = False  # explicit flag when axes are trusted
    sha256: str | None = None
    calibration_hash: str | None = None
    crs: str | None = None
    vertical_datum: str | None = None


class EarthConstraints(StrictModel):
    wells: list[dict[str, Any]] = Field(default_factory=list)
    formation_tops: list[dict[str, Any]] = Field(default_factory=list)
    checkshots: list[dict[str, Any]] = Field(default_factory=list)
    velocity_model_ref: str | None = None
    stratigraphic_framework_ref: str | None = None
    structural_regime: Literal["extension", "contraction", "strike_slip", "salt", "unknown"] = "unknown"
    # W3 hardening 2026-07-24: named witness records. The bundle builder
    # reads these directly — they are NOT mutated into fake alternatives.
    witnesses: list[dict[str, Any]] = Field(default_factory=list)


class InterpretRequestFlags(StrictModel):
    horizons: bool = True
    faults: bool = True
    structural_framework: bool = True
    restoration: bool = False
    hypothesis_count: int = Field(default=3, ge=1, le=10)


# ── Mode-discriminated requests ──────────────────────────────────────────────


class HorizonContrastMode(TransportAwareRequest):
    mode: Literal["horizon_contrast"] = "horizon_contrast"
    attribute_data: dict[str, list[float]]
    depth: list[float]
    geological_query: str = "sequence_boundary"
    well_ties: dict[str, float] | None = None
    peak_threshold: float = 1.5
    min_separation_m: float = 20.0
    custom_query: dict[str, float] | None = None
    calibration: Calibration | None = None


class StructureValidateMode(TransportAwareRequest):
    mode: Literal["structure_validate"] = "structure_validate"
    framework: dict[str, Any] | None = None
    faults: list[dict[str, Any]] | None = None
    horizons: list[dict[str, Any]] | None = None
    calibration: Calibration | None = None
    earth_constraints: EarthConstraints | None = None
    request: InterpretRequestFlags | None = None
    claim_text: str = ""


class SectionImageMode(TransportAwareRequest):
    mode: Literal["interpret_section", "rsi_pipeline", "section_image", "classical_section"] = "interpret_section"
    image_path: str | None = None
    image_data: str | None = None  # base64 / data-URL from chat clients (≤2MB decoded)
    artifact_ref: str | None = None
    source_uri: str | None = None
    max_faults: int = 20
    max_horizons: int = 12
    calibration: Calibration | None = None
    earth_constraints: EarthConstraints | None = None
    request: InterpretRequestFlags | None = None


class SegySliceMode(TransportAwareRequest):
    mode: Literal["segy_slice", "segy_2d"] = "segy_slice"
    segy_path: str | None = None
    source_uri: str | None = None
    volume_ref: str | None = None
    frame_index: int = 0
    orientation: str = "inline"
    calibration: Calibration | None = None


class FaultSticksMode(TransportAwareRequest):
    mode: Literal["fault_sticks"] = "fault_sticks"
    source_uri: str = ""
    source_type: str = "csv"


class VolumeFrameMode(TransportAwareRequest):
    mode: Literal["volume_frame"] = "volume_frame"
    action: str = "get"
    volume_ref: str = ""
    frame_index: int = 0
    orientation: str = "inline"
    provenance: str = "fixture"
    image_data: str | None = None


class BlendMode(TransportAwareRequest):
    mode: Literal["blend"] = "blend"
    blend_mode: str = "alpha"
    volume_ref: str = ""
    provenance: str = "fixture"


class InterpretBundleMode(TransportAwareRequest):
    """Full propose→validate→compare loop emitting interpretation_bundle."""

    mode: Literal["interpret"] = "interpret"
    artifact_ref: str | None = None
    artifact_type: Literal["section_image", "segy_2d", "segy_3d", "interpreted_section", "framework"] = "framework"
    image_path: str | None = None
    image_data: str | None = None  # base64 / data-URL from chat clients
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


class GateResultModel(BaseModel):
    """Output gate receipt — `extra="allow"` so handlers can attach findings."""

    model_config = ConfigDict(extra="allow")  # allow findings etc.
    gate_id: str
    status: Literal["PASS", "WARN", "KILL", "UNMEASURED"]
    equation: str = ""
    receipt_hash: str = ""
    reason: str = ""


class HypothesisModel(StrictModel):
    model_config = ConfigDict(extra="allow")
    hypothesis_id: str
    witness_id: str | None = None
    witness_type: str | None = None
    model_or_method: str = ""
    derivation: str = ""
    horizons: list[dict[str, Any]] = Field(default_factory=list)
    faults: list[dict[str, Any]] = Field(default_factory=list)
    fault_blocks: list[dict[str, Any]] = Field(default_factory=list)
    structural_style: str = "unknown"
    kinematic_claims: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    status: str | None = None
    hypothesis_status: str | None = None
    evidence_coverage: float | None = None
    calibration_status: str | None = None
    confidence_value: float | None = None
    confidence_basis: str | None = None
    epistemic_class: Literal["OBSERVATION", "DERIVATION", "INTERPRETATION", "SPECULATION"] = "INTERPRETATION"
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    physics_gates: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    unresolved_measurements: list[str] = Field(default_factory=list)
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


# ═══ Canonical noun set (W1, hardening pass 2026-07-24) ═══
# Sibling block to existing classes. DO NOT modify or rename existing models;
# these classes are additive sidecars used by the W1 hardening pass and are
# referenced by /root/forge_work/2026-07-24-GEOX-HARDENING/canonical_noun_schemas.json.
# Existing InterpretationBundle / GateResultModel / HypothesisModel / etc. are
# untouched; this block introduces CanonicalInterpretationBundle (distinct name)
# to avoid shadowing the live InterpretationBundle used by bundle.py and the
# geox_seismic_interpret tool.

from enum import Enum


class CoordinateDomain(str, Enum):
    PIXEL = "pixel"
    TRACE = "trace"
    CDP = "cdp"
    DISTANCE_M = "distance_m"
    TIME_MS = "time_ms"
    DEPTH_M = "depth_m"


class GeometryOrigin(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    INTERPRETED = "interpreted"
    SPECULATIVE = "speculative"


class Point2D(BaseModel):
    """A single point with explicit coordinate domain + units.

    Invariant: every Point2D must declare domain AND horizontal_unit AND
    vertical_unit. Anonymous geometry is rejected — never defaulted to
    "unknown". This is the contract that prevents unit drift across
    pixel→time→depth conversions.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    x: float
    y: float
    domain: CoordinateDomain
    horizontal_unit: str
    vertical_unit: str
    source_section: str | None = None
    source_hash: str | None = None
    point_order: int | None = None
    origin: GeometryOrigin = GeometryOrigin.OBSERVED


class Polyline2D(BaseModel):
    """Ordered polyline. point_order on each Point2D preserves the sequence."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    points: list[Point2D]
    closed: bool = False
    source_section: str | None = None
    source_hash: str | None = None
    origin: GeometryOrigin = GeometryOrigin.OBSERVED


class SectionRef(BaseModel):
    """Pointer to a section (image, segy slice, or volume frame).

    `source_uri` is required; `source_hash` is optional but recommended so
    later provenance can attest to the exact bytes that produced the
    geometry. inline_min/max and xline_min/max are populated when the
    section is a sub-volume of a 3D segy.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    section_id: str
    source_uri: str
    source_hash: str | None = None
    source_type: Literal["png", "jpg", "svg", "segy", "unknown"] = "unknown"
    inline_min: int | None = None
    inline_max: int | None = None
    xline_min: int | None = None
    xline_max: int | None = None


class AxisCalibration(BaseModel):
    """Axis calibration wrapper. Reuses the existing AxisSpec from this module.

    `calibrated` is the explicit flag that physics gates check before they
    trust a measurement. `sha256` covers the input bytes; `calibration_hash`
    covers the calibration params themselves.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    horizontal: AxisSpec
    vertical: AxisSpec
    vertical_exaggeration: float | None = None
    section_azimuth_deg: float | None = None
    calibrated: bool = False
    sha256: str | None = None
    calibration_hash: str | None = None


class DipBasis(str, Enum):
    PIXEL = "pixel"
    APPARENT_SECTION = "apparent_section"
    TRUE_SUBSURFACE = "true_subsurface"


class Fault(BaseModel):
    """A fault interpretation. Dip fields are intentionally distinct by basis.

    - image_dip_deg: dip as measured in the raw image pixels (no VE correction)
    - apparent_section_dip_deg: dip after cosine-of-azimuth correction (still
      affected by vertical exaggeration)
    - true_subsurface_dip_deg: dip after VE correction, true 3D dip

    `dip_basis` declares which field is authoritative. `kinematic_status` is a
    four-valued epistemic trail (OBSERVED → SPECULATIVE) that prevents
    interpreting a model output as a definitive slip sense.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    fault_id: str
    polyline: Polyline2D
    image_dip_deg: float | None = None
    apparent_section_dip_deg: float | None = None
    true_subsurface_dip_deg: float | None = None
    dip_basis: DipBasis = DipBasis.PIXEL
    dip_direction: str | None = None
    fault_strike_deg: float | None = None
    section_azimuth_deg: float | None = None
    kinematic_claim: Literal["normal", "reverse", "strike_slip", "unknown"] = "unknown"
    kinematic_status: Literal["OBSERVED", "DERIVED", "INTERPRETED", "SPECULATIVE"] = "SPECULATIVE"
    regime_prior: str | None = None
    reactivation_evidence: bool = False
    throw_profile_m: list[float] | None = None
    tip_taper: Literal["ok", "fail", "unknown"] = "unknown"
    attachments: dict[str, Any] = Field(default_factory=dict)


class Horizon(BaseModel):
    """A horizon interpretation with three distinct geometry tracks.

    - pixel_geometry: image-space coordinates (always available)
    - time_geometry: TWT coordinates (requires time calibration)
    - depth_geometry: depth coordinates (requires velocity model)

    `conversion_basis` declares how pixel→time→depth was produced. The
    three geometries are deliberately separate fields so the gate system
    can reject a conversion that has no basis.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    horizon_id: str
    pixel_geometry: Polyline2D | None = None
    time_geometry: Polyline2D | None = None
    depth_geometry: Polyline2D | None = None
    conversion_basis: Literal["none", "regional_prior", "checkshot", "vsp", "velocity_model"] = "none"
    attachments: dict[str, Any] = Field(default_factory=dict)


class FaultCutoff(BaseModel):
    """Hanging-wall / footwall cutoff at a Horizon × Fault intersection (P2).

    `domain` records which vertical axis the cutoff values live in.
    `measured=False` means the cutoff is interpolated, not picked.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    fault_id: str
    horizon_id: str
    hanging_wall_value: float | None = None
    footwall_value: float | None = None
    throw_m: float | None = None
    throw_ms: float | None = None
    domain: CoordinateDomain
    measured: bool = False


class WitnessProvenance(BaseModel):
    """Provenance for a single competing-hypothesis witness.

    Tri-witness doctrine: every hypothesis must carry explicit witness info
    (independent model / classical CV / human / deterministic transform).
    `derivation` is the human-readable recipe; `source_geometry_hash` is the
    hash of the geometry that fed the witness. The two together let an
    auditor re-derive the claim.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    witness_id: str
    witness_type: Literal["independent_model", "classical_cv", "human_supplied", "deterministic_transform", "empty_conceptual"] = "empty_conceptual"
    model_or_method: str
    prompt_hash: str | None = None
    source_geometry_hash: str
    derivation: str
    structural_style: str
    kinematic_claims: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    unresolved_measurements: list[str] = Field(default_factory=list)
    attachments: dict[str, Any] = Field(default_factory=dict)


class HypothesisStatus(str, Enum):
    UNTESTED = "UNTESTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    SURVIVES_CURRENT_TESTS = "SURVIVES_CURRENT_TESTS"
    REJECTED = "REJECTED"


class CalibrationStatus(str, Enum):
    UNCALIBRATED = "UNCALIBRATED"
    PARTIAL = "PARTIAL"
    CALIBRATED = "CALIBRATED"


class GateResult(BaseModel):
    """A gate receipt. All inputs used, units, and the equation or rule are
    required so that any future audit can re-run the gate exactly.

    `inputs_used` and `measurement_units` keys must be parallel arrays — the
    regression test enforces this. `receipt_hash` chain-anchoors the gate
    to the rest of the bundle.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    gate_id: str
    status: Literal["PASS", "WARN", "KILL", "UNMEASURED", "NOT_APPLICABLE"]
    inputs_used: dict[str, Any] = Field(default_factory=dict)
    measurement_units: dict[str, str] = Field(default_factory=dict)
    equation_or_rule: str
    threshold_source: str
    reason: str
    missing_inputs: list[str] = Field(default_factory=list)
    receipt_hash: str


class RenderStyleVersion(BaseModel):
    """Hash-pinned palette + matplotlib version. Reproducible renders."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    style_id: str
    palette_version: str
    matplotlib_version: str


class RenderArtifact(BaseModel):
    """A rendered figure with provenance hash chain.

    The hashes (render_hash, source_hash, canonical_geometry_hash,
    annotations_hash) form a tape that lets any render be re-derived later.
    `honest_banner` is the W1 gate that requires every render to declare
    its asset — calibration status, witness, hypothesis id.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    render_ref: str
    render_hash: str
    source_hash: str
    canonical_geometry_hash: str
    annotations_hash: str
    style_version: RenderStyleVersion
    bytes: int
    hypothesis_id: str
    image_format: Literal["png", "svg", "both"]
    honest_banner: str


class CompactInterpretationResult(BaseModel):
    """Compact default — physics lives behind detail_ref. Renders cleanly as
    a one-shot JSON receipt for chat clients.

    `seal_authority` is hard-pinned to "arifOS_only" by the contract; GEOX
    never seals — it only emits qualified candidates.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    status: Literal["OK", "OK_HOLD", "HOLD", "VOID"] = "OK"
    local_verdict: Literal["QUALIFIED_CANDIDATE"] = "QUALIFIED_CANDIDATE"
    input_class: Literal["image_only", "segy_slice", "segy_2d", "segy_3d", "unknown"] = "unknown"
    calibration_status: CalibrationStatus = CalibrationStatus.UNCALIBRATED
    hypotheses: list[dict[str, Any]]
    preferred_hypothesis: str | None = None
    detail_ref: str
    receipt_hash: str
    seal_authority: Literal["arifOS_only"] = "arifOS_only"
    gate_summary: dict[str, int] = Field(default_factory=dict)


class CanonicalInterpretationBundle(BaseModel):
    """Full canonical bundle. Distinct name from the live `InterpretationBundle`
    (which is `extra="allow"` and used by the B-final handler) — this is the
    hardened W1 contract with strict, frozen, extra-forbid defaults.

    Hypotheses contains fully-typed Hypothesis objects, not loose dicts.
    `seal_eligibility` is False until a human ratifies it; arifOS is the
    only authority that can flip it to True.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    section: SectionRef | None = None
    calibration: AxisCalibration | None = None
    horizons: list[Horizon] = Field(default_factory=list)
    faults: list[Fault] = Field(default_factory=list)
    fault_cutoffs: list[FaultCutoff] = Field(default_factory=list)
    hypotheses: list["Hypothesis"] = Field(default_factory=list)
    gate_results: list[GateResult] = Field(default_factory=list)
    render_artifacts: list[RenderArtifact] = Field(default_factory=list)
    preferred_hypothesis: str | None = None
    local_verdict: Literal["QUALIFIED_CANDIDATE"] = "QUALIFIED_CANDIDATE"
    seal_authority: Literal["arifOS_only"] = "arifOS_only"
    seal_eligibility: bool = False
    receipt_hash: str


class Hypothesis(BaseModel):
    """A single competing structural hypothesis.

    `confidence_value` defaults to None on construction — the contract
    forbids emitting a fixed confidence at the type level. Confidence is
    only attached via the `attachments` bucket, and only after a benchmark
    calibration is verified. This is the structural expression of F7
    (Humility).
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    hypothesis_id: str
    witness: WitnessProvenance
    faults: list[Fault] = Field(default_factory=list)
    horizons: list[Horizon] = Field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.UNTESTED
    evidence_coverage_measured: int = 0
    evidence_coverage_applicable: int = 0
    calibration_status: CalibrationStatus = CalibrationStatus.UNCALIBRATED
    confidence_value: float | None = None
    confidence_basis: str | None = None
    gate_results: list[GateResult] = Field(default_factory=list)
    attachments: dict[str, Any] = Field(default_factory=dict)


# Resolve the forward reference in CanonicalInterpretationBundle.hypotheses.
# With `from __future__ import annotations` all annotations are strings, so
# Pydantic resolves them lazily — model_rebuild() makes the link explicit
# and surfaces any mistake at import time rather than at first use.
CanonicalInterpretationBundle.model_rebuild()
