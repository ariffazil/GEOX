"""
GEOX Earth Witness — Canonical EarthObservationPacket Pydantic v2 Schema
═══════════════════════════════════════════════════════════════════════════
Authority: ARIFOS::GEOX::EARTH_WITNESS_SLICE::v1
Canon: F1-F13 Constitutional Discipline · Invariant I1-I9

Enforces:
I1 Image != Specimen != Measurement != Earth.
I2 Vision output is EVIDENCE only for visible features; everything else INTERPRET/HYPOTHESIS.
I3 No hydrocarbon/fluid claim from image alone. Amplitude != hydrocarbon. Impedance != lithology.
I4 No fossil age from morphology alone; requires taxon candidate + PBDB range + expert flag.
I5 Missing diagnostic input -> INPUT_REQUIRED, never guessed.
I6 Every output carries: claim_tag, confidence, provenance (artifact sha256), limitations[].
I7 basin_profile = context only; must never raise confidence.
I8 No confidential/PETRONAS data to any external model. Demo = public/synthetic only.
I9 Max local verdict = QUALIFIED_CANDIDATE / PARTIAL. Only arifOS issues SEAL.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# ── Modality & Domain Types ────────────────────────────────────────────────

ObservationModality = Literal[
    "rock",
    "outcrop",
    "core",
    "thin_section",
    "fossil",
    "seismic_display",
    "map",
    "section",
    "unknown",
]

DomainClass = Literal["time", "depth", "na"]

EpistemicClaimTag = Literal["EVIDENCE", "INTERPRET", "HYPOTHESIS", "UNKNOWN"]

ObservationState = Literal[
    "DRAFT",
    "INPUT_REQUIRED",
    "REVIEW_PENDING",
    "QUALIFIED_CANDIDATE",
]

LocalVerdict = Literal[
    "QUALIFIED_CANDIDATE",
    "PARTIAL",
    "SABAR",
    "HOLD",
    "VOID",
]


# ── Sub-Schemas ─────────────────────────────────────────────────────────────

class ArtifactMetadata(BaseModel):
    id: str
    sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    media_type: str
    original_uri: str | None = None
    source_actor: str
    captured_at: str


class ScaleMetadata(BaseModel):
    value: float
    unit: str
    pixel_per_unit: float | None = None
    is_calibrated: bool = False


class OrientationMetadata(BaseModel):
    strike: float | None = None
    dip: float | None = None
    facing: str | None = None
    is_way_up_known: bool = False


class DisplayTransformMetadata(BaseModel):
    polarity: str | None = None
    color_map: str | None = None
    gain: float | None = None
    has_enhancement: bool = False


class ObservationContext(BaseModel):
    modality: ObservationModality
    subject_class: str | None = None
    scale: ScaleMetadata | None = None
    orientation: OrientationMetadata | None = None
    crs: str | None = None
    domain: DomainClass = "na"
    display_transform: DisplayTransformMetadata | None = None
    acquisition_metadata: dict[str, Any] = Field(default_factory=dict)


class VisibleFeature(BaseModel):
    feature_id: str
    label: str
    category: str
    bounding_box: list[float] | None = None
    description: str | None = None
    confidence: float = Field(..., ge=0.0, le=0.90)

    @field_validator("confidence")
    @classmethod
    def cap_confidence(cls, v: float) -> float:
        # F5 HUMILITY / F7 hard cap at 0.90
        return min(v, 0.90)


class OcrText(BaseModel):
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    location: str | None = None


class Measurement(BaseModel):
    metric: str
    value: float
    unit: str
    method: str
    uncertainty: float


class ObservationsBlock(BaseModel):
    visible_features: list[VisibleFeature] = Field(default_factory=list)
    ocr_text: list[OcrText] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    annotations: list[str] = Field(default_factory=list)


class Hypothesis(BaseModel):
    hypothesis_id: str
    label: str
    supporting: list[str] = Field(default_factory=list)
    conflicting: list[str] = Field(default_factory=list)
    falsifiers: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=0.90)

    @field_validator("confidence")
    @classmethod
    def cap_confidence(cls, v: float) -> float:
        return min(v, 0.90)


class HumanTestRequest(BaseModel):
    test_name: str
    purpose: str
    discriminates: list[str] = Field(default_factory=list)


class LimitationsBlock(BaseModel):
    image_cannot_determine: list[str] = Field(
        default_factory=list,
        description="Explicit enumeration of what physical parameters pixels cannot observe (F9 Anti-Hantu Honesty Gate)",
    )
    missing_metadata: list[str] = Field(default_factory=list)
    requested_human_tests: list[HumanTestRequest] = Field(default_factory=list)
    requested_instrument_data: list[str] = Field(default_factory=list)


class ProvenanceRecord(BaseModel):
    step: str
    agent_id: str
    model_id: str | None = None
    timestamp: str
    hash: str | None = None


class EpistemicBlock(BaseModel):
    claim_tag: EpistemicClaimTag = "INTERPRET"
    confidence: float = Field(..., ge=0.0, le=0.90)
    state: ObservationState = "DRAFT"
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    verdict: LocalVerdict | None = None

    @field_validator("confidence")
    @classmethod
    def cap_confidence(cls, v: float) -> float:
        return min(v, 0.90)


# ── The Canonical Root Packet ───────────────────────────────────────────────

class EarthObservationPacket(BaseModel):
    """Canonical multimodal Earth observation packet enforcing invariant Image != Specimen != Measurement != Earth."""
    schema_version: Literal["earth_observation_packet.v1"] = "earth_observation_packet.v1"
    packet_id: str
    artifact: ArtifactMetadata
    context: ObservationContext
    observations: ObservationsBlock
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    limitations: LimitationsBlock
    epistemic: EpistemicBlock

    @model_validator(mode="after")
    def enforce_invariants(self) -> EarthObservationPacket:
        # Invariant I3: No hydrocarbon claim from image alone
        for hyp in self.hypotheses:
            label_lower = hyp.label.lower()
            if any(term in label_lower for term in ["hydrocarbon", "oil leg", "gas pay", "direct hydrocarbon indicator", "dhi confirmed"]):
                # Downgrade or force INPUT_REQUIRED
                if self.epistemic.claim_tag == "EVIDENCE":
                    self.epistemic.claim_tag = "HYPOTHESIS"
                if "Fluid cannot be confirmed from image alone (Amplitude != Hydrocarbon)" not in self.limitations.image_cannot_determine:
                    self.limitations.image_cannot_determine.append(
                        "Fluid cannot be confirmed from image alone (Amplitude != Hydrocarbon). Requires AVO or well tie."
                    )
                if self.epistemic.state != "INPUT_REQUIRED":
                    self.epistemic.state = "INPUT_REQUIRED"

        # Invariant I4: No fossil age from morphology alone without PBDB validation
        if self.context.modality == "fossil":
            if "Absolute age cannot be determined from morphology alone" not in self.limitations.image_cannot_determine:
                self.limitations.image_cannot_determine.append(
                    "Absolute age cannot be determined from morphology alone. Requires PBDB biozone range validation."
                )

        # Invariant I5: Missing diagnostic scale bar on hand specimen / outcrop
        if self.context.modality in ["rock", "outcrop", "core", "thin_section"]:
            if self.context.scale is None or not self.context.scale.is_calibrated:
                if "Diagnostic physical scale bar is missing" not in self.limitations.missing_metadata:
                    self.limitations.missing_metadata.append("Diagnostic physical scale bar is missing")
                if self.epistemic.state == "DRAFT":
                    self.epistemic.state = "INPUT_REQUIRED"

        # Invariant I9: Local verdict must never exceed QUALIFIED_CANDIDATE
        if self.epistemic.verdict == "SEAL":  # type: ignore
            self.epistemic.verdict = "QUALIFIED_CANDIDATE"

        return self
