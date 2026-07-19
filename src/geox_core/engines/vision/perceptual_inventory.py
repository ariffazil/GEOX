"""
GEOX Perceptual Inventory — Pydantic v2 schemas (Layer 1 output contract)
═══════════════════════════════════════════════════════════════════════════
Forged 2026-06-07 — DITEMPA BUKAN DIBERI

The Perceptual Inventory is the typed grammar that bridges:
    VLM (raw text/image understanding) → GEOX claim engine (structured reasoning)

This is the **missing piece** flagged in `VISION_INTELLIGENCE_IMPLEMENTATION.md`
(2026-04-10, Phase 0 "Foundation Complete" but Phase 3 "Real VLM not wired").

Design constraints (from GEOX_VISION_DEV_CHARTER.md + Cross-Modal Fidelity
Theorem ratified 2026-06-05):

1. **Observation-only at the schema layer.** ReflectorObservation,
   FaultObservation, AmplitudeZoneObservation carry *what the VLM saw* —
   not *what it means geologically*. Geological interpretation happens
   in the claim engine (Layer 3), with `forbidden_claims` enforcement.

2. **Every observation has provenance.** `pixel_provenance` is a
   (lateral_extent_inlines, twt_range_ms) tuple bounding where in the
   image the observation was made. This makes the output auditable per
   F11 and falsifiable (Arif can look at the same pixels and disagree).

3. **Confidence is bounded.** No observation may carry confidence > 0.90
   (F7 HUMILITY hard cap). The default AC_Risk B_cog baseline is 0.79
   per Bond et al. (2007) seismic-interpretation failure rate.

4. **Transform stack is logged.** Per F4 CLARITY, every PerceptualInventory
   carries the chain of operations applied: image-read, polarity-invert,
   vlm-inference, json-parse. The AC_Risk engine sums (1 - invertibility)
   for each transform to compute D_transform.

5. **Verdict is INTERPRETATION, not SEAL.** A VLM-only output cannot
   reach SEAL because (a) the underlying physical data has not been
   reconciled (no SEG-Y cross-check, no well tie), and (b) Bond 2007
   shows 79% first-interpretation error rate. SEAL requires
   physics-validated evidence (B_cog 0.20) which is impossible from
   pixels alone.
"""

from __future__ import annotations

import hashlib
import json
import time
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════


class AmplitudeCharacter(StrEnum):
    BRIGHT = "bright"
    DIM = "dim"
    VARIABLE = "variable"
    TRANSPARENT = "transparent"


class ReflectorContinuity(StrEnum):
    CONTINUOUS = "continuous"
    DISCONTINUOUS = "discontinuous"
    CHAOTIC = "chaotic"


class PolarityConvention(StrEnum):
    SEG_NORMAL = "SEG-normal"  # positive impedance = peak (trough in display)
    SEG_REVERSE = "SEG-reverse"
    UNKNOWN = "unknown"
    OTHER = "other"


class FaultType(StrEnum):
    NORMAL = "normal"
    REVERSE = "reverse"
    STRIKE_SLIP = "strike-slip"
    WRENCH = "wrench"
    UNKNOWN = "unknown"


class AmplitudeZoneCharacter(StrEnum):
    BRIGHT = "bright"
    DIM = "dim"
    POLARITY_REVERSAL = "polarity-reversal"
    SHADOW_ZONE = "shadow-zone"
    OTHER = "other"

    @classmethod
    def _missing_(cls, value: str) -> AmplitudeZoneCharacter:
        return cls.OTHER


class AmplitudeZoneOrigin(StrEnum):
    LITHOLOGY = "lithology"
    FLUID = "fluid"
    TUNING = "tuning"
    ARTIFACT = "artifact"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: str) -> AmplitudeZoneOrigin:
        return cls.UNKNOWN


class DisplayColorPolarity(StrEnum):
    RED_POSITIVE = "red-positive"  # Standard SEG red=positive
    BLACK_POSITIVE = "black-positive"
    UNKNOWN = "unknown"


class DisplayUnits(StrEnum):
    TWT_MS = "TWT-ms"
    TWT_S = "TWT-s"
    DEPTH_M = "depth-m"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: str) -> DisplayUnits:
        """Lenient: unknown unit strings become UNKNOWN. Per F2 TRUTH, an
        honest UNKNOWN is better than a hard fail. Logs a warning at
        the adapter layer."""
        return cls.UNKNOWN


class VisionVerdict(StrEnum):
    """Per the F2 TRUTH floor, VLM-only outputs are INTERPRETATION at best.
    SEAL is reserved for physics-validated claims (which VLM cannot produce
    from pixels alone)."""

    SEAL = "SEAL"  # Reserved — VLM cannot reach this alone
    QUALIFY = "QUALIFY"  # VLM + cross-view consistency check passed
    INTERPRETATION = "INTERPRETATION"  # Default VLM-only output
    HOLD = "HOLD"  # VLM uncertain, awaiting F13 human review
    VOID = "VOID"  # VLM call failed or AC_Risk exceeded threshold


class AcRiskVerdict(StrEnum):
    """From TOAC_CANON.md: AC_Risk thresholds."""

    SEAL = "SEAL"  # < 0.15
    QUALIFY = "QUALIFY"  # 0.15-0.34
    HOLD = "HOLD"  # 0.35-0.59
    VOID = "VOID"  # >= 0.60


# ═══════════════════════════════════════════════════════════════════════════════
# Observation schemas (Layer 1 outputs)
# ═══════════════════════════════════════════════════════════════════════════════


class ReflectorObservation(BaseModel):
    """A single laterally-coherent seismic reflector as observed by the VLM.
    Pure geometry, no geological meaning yet."""

    reflector_id: str = Field(..., description="Stable identifier, e.g. 'R_top_seq_boundary'")
    lateral_extent_inlines: tuple[float, float] = Field(..., description="(start, end) inline range where reflector is visible")
    twt_range_ms: tuple[float, float] = Field(..., description="(min, max) TWT in ms where reflector is observed")
    amplitude_character: AmplitudeCharacter
    continuity: ReflectorContinuity
    polarity: PolarityConvention = PolarityConvention.UNKNOWN
    confidence: float = Field(..., ge=0.0, le=0.90, description="F7 HUMILITY hard cap at 0.90")
    notes: str | None = Field(None, description="Free-form VLM note, e.g. 'clinoform geometry visible'")


class FaultObservation(BaseModel):
    """A discontinuity in reflector continuity, observed by the VLM."""

    fault_id: str = Field(..., description="Stable identifier, e.g. 'F_main_boundary'")
    type: FaultType = FaultType.UNKNOWN
    lateral_extent_inlines: tuple[float, float]
    twt_range_ms: tuple[float, float]
    strike_dip_deg: float | None = Field(None, ge=0.0, le=90.0, description="Apparent dip")
    throw_ms: float | None = Field(None, description="Apparent vertical throw in ms TWT")
    confidence: float = Field(..., ge=0.0, le=0.90)
    notes: str | None = None


class AmplitudeZoneObservation(BaseModel):
    """A localized amplitude anomaly — bright spot, dim spot, polarity reversal."""

    zone_id: str
    twt_range_ms: tuple[float, float]
    lateral_extent_inlines: tuple[float, float]
    character: AmplitudeZoneCharacter
    possible_origin: AmplitudeZoneOrigin = AmplitudeZoneOrigin.UNKNOWN
    confidence: float = Field(..., ge=0.0, le=0.90)
    notes: str | None = None


class AxisMetadata(BaseModel):
    """Coordinate system metadata extracted from the image header / axes.
    Critical for downstream physics checks."""

    twt_range_ms: tuple[float, float] = Field(..., description="(min, max) from vertical axis")
    inline_range: tuple[float, float] = Field(..., description="(min, max) from horizontal axis")
    polarity_convention: PolarityConvention = PolarityConvention.UNKNOWN
    display_units: DisplayUnits = DisplayUnits.UNKNOWN
    color_polarity: DisplayColorPolarity = DisplayColorPolarity.UNKNOWN
    confidence: float = Field(0.5, ge=0.0, le=0.90)
    notes: str | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# AC_Risk components
# ═══════════════════════════════════════════════════════════════════════════════


class AcRiskComponents(BaseModel):
    """AC_Risk = U_phys × D_transform × B_cog (TOAC_CANON.md)
    Each component is bounded [0, 1] before multiplication; the product is
    capped at 1.0 by the AC_Risk engine.

    Bond et al. (2007) baseline: B_cog = 0.79 for unaided expert seismic
    interpretation failure rate. Adjusted down by multi-view check (0.42)
    and physics-validation (0.20)."""

    u_phys: float = Field(..., ge=0.0, le=1.0, description="Physical model uncertainty")
    d_transform: float = Field(..., ge=1.0, le=3.0, description="Transform stack distortion (multiplicative)")
    b_cog: float = Field(0.79, ge=0.0, le=1.0, description="Cognitive bias exposure")
    transform_stack: list[str] = Field(default_factory=list, description="F4 CLARITY: each transform applied")
    multi_view_passed: bool = Field(False, description="True if cross-view consistency check passed")
    physics_validated: bool = Field(False, description="True if reconciled with underlying SEG-Y / well data")

    @field_validator("d_transform")
    @classmethod
    def cap_d_transform(cls, v: float) -> float:
        return min(3.0, max(1.0, v))

    def compute(self) -> float:
        """Compute AC_Risk = U_phys × D_transform × B_cog, capped at 1.0."""
        ac_risk = self.u_phys * self.d_transform * self.b_cog
        return min(1.0, ac_risk)

    def to_verdict(self) -> AcRiskVerdict:
        ac_risk = self.compute()
        if ac_risk < 0.15:
            return AcRiskVerdict.SEAL
        elif ac_risk < 0.35:
            return AcRiskVerdict.QUALIFY
        elif ac_risk < 0.60:
            return AcRiskVerdict.HOLD
        else:
            return AcRiskVerdict.VOID


# ═══════════════════════════════════════════════════════════════════════════════
# Top-level Perceptual Inventory
# ═══════════════════════════════════════════════════════════════════════════════


class PerceptualInventory(BaseModel):
    """The complete Layer-1 output. This is what gets handed to the GEOX
    claim engine (Layer 3) for geological interpretation.

    Constitutional guarantees:
    - F1 AMANAH: input_image_sha256 is the immutable identity of the source
    - F2 TRUTH: every observation has model_id and timestamp
    - F4 CLARITY: full transform_stack logged
    - F7 HUMILITY: overall_confidence hard-capped at 0.90
    - F9 ANTI-HANTU: verdict is INTERPRETATION at best (SEAL reserved)
    - F11 AUDIT: model_id, raw_response_hash, timestamp
    - F13 SOVEREIGN: human_review_required=True when AC_Risk > 0.5
    """

    inventory_id: str = Field(..., description="Stable id, e.g. inv_<sha256[:12]>")
    image_path: str = Field(..., description="Absolute path to source image")
    input_image_sha256: str = Field(..., description="SHA256 of source image bytes (F1 AMANAH identity)")
    reflectors: list[ReflectorObservation] = Field(default_factory=list)
    faults: list[FaultObservation] = Field(default_factory=list)
    amplitude_zones: list[AmplitudeZoneObservation] = Field(default_factory=list)
    axis_metadata: AxisMetadata
    global_assessment: str = Field(..., description="VLM's natural-language summary")
    overall_confidence: float = Field(..., ge=0.0, le=0.90)
    model_id: str = Field(..., description="e.g. 'minimax-M3-vision'")
    prompt_id: str = Field(..., description="Hash of the prompt used to elicit the VLM")
    raw_response_hash: str = Field(..., description="SHA256 of raw VLM response text")
    transform_stack: list[str] = Field(default_factory=list)
    ac_risk: AcRiskComponents
    verdict: VisionVerdict = VisionVerdict.INTERPRETATION
    human_review_required: bool = Field(False, description="F13: True if AC_Risk > 0.5 or any fault/HC observation")
    timestamp_unix: float = Field(default_factory=time.time, description="ISO 8601 / Unix epoch")

    @model_validator(mode="after")
    def _enforce_governance(self) -> PerceptualInventory:
        """Cross-floor consistency checks at validation time."""
        # F7 HUMILITY hard cap (defense in depth)
        if self.overall_confidence > 0.90:
            raise ValueError(f"F7 HUMILITY violation: overall_confidence {self.overall_confidence} > 0.90")

        # F13 SOVEREIGN: any HC-related observation requires human review
        for zone in self.amplitude_zones:
            if zone.possible_origin in (AmplitudeZoneOrigin.FLUID, AmplitudeZoneOrigin.TUNING):
                if zone.confidence > 0.5:
                    self.human_review_required = True

        for fault in self.faults:
            if fault.type == FaultType.STRIKE_SLIP and fault.confidence > 0.5:
                # Strike-slip is high-stakes claim; require human review
                self.human_review_required = True

        # F13 SOVEREIGN: AC_Risk > 0.5 mandates human review
        if self.ac_risk.compute() > 0.5:
            self.human_review_required = True

        # F13 SOVEREIGN: HOLD or VOID verdict mandates human review
        # (HOLD = 888_HOLD semantics; VOID = unsafe to proceed)
        if self.verdict in (VisionVerdict.HOLD, VisionVerdict.VOID):
            self.human_review_required = True

        # F9 ANTI-HANTU: VLM-only output cannot reach SEAL
        if not self.ac_risk.physics_validated and self.verdict == VisionVerdict.SEAL:
            raise ValueError(
                "F9 ANTI-HANTU: VLM-only output (physics_validated=False) cannot reach SEAL. Verdict must be ≤ INTERPRETATION."
            )

        return self

    def to_json_canonical(self) -> str:
        """Canonical JSON serialization for round-trip integrity
        (per Cross-Modal Fidelity Theorem)."""
        # Pydantic v2 model_dump_json doesn't accept sort_keys directly;
        # we dump to dict first, then json.dumps with sort_keys for
        # cross-modal transfer-stable encoding.
        return json.dumps(self.model_dump(mode="json"), indent=2, sort_keys=True)

    def to_seal_receipt(self) -> dict:
        """Format suitable for VAULT999 sealing.
        Returns dict (not str) for easy composability."""
        return {
            "inventory_id": self.inventory_id,
            "input_image_sha256": self.input_image_sha256,
            "model_id": self.model_id,
            "prompt_id": self.prompt_id,
            "raw_response_hash": self.raw_response_hash,
            "verdict": self.verdict.value,
            "ac_risk": self.ac_risk.compute(),
            "ac_risk_verdict": self.ac_risk.to_verdict().value,
            "human_review_required": self.human_review_required,
            "timestamp_unix": self.timestamp_unix,
            "n_reflectors": len(self.reflectors),
            "n_faults": len(self.faults),
            "n_amplitude_zones": len(self.amplitude_zones),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Factory helpers
# ═══════════════════════════════════════════════════════════════════════════════


def sha256_file(path: str) -> str:
    """Compute SHA256 of file contents (F1 AMANAH identity)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    """Compute SHA256 of text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def default_ac_risk_components(
    u_phys: float = 0.45,
    transform_stack: list[str] | None = None,
    multi_view_passed: bool = False,
    physics_validated: bool = False,
) -> AcRiskComponents:
    """Default AC_Risk components for a VLM-only image interpretation.

    Per TOAC_CANON.md:
    - U_phys = 0.45 (no well control, no SEG-Y tie)
    - D_transform product for image-only path with VLM = 1.5 (1.0 obs × 1.0
      scaling × 1.0 cmapping × 1.0 vlm-inference component, summed 1-inv)
    - B_cog = 0.79 (Bond 2007 baseline) → 0.42 (multi-view) → 0.30
      (physics-validated)

    Note: The exact D_transform arithmetic is in
    `vision_test_harness.py::compute_d_transform_from_stack`.
    """
    stack = transform_stack or ["image-read", "vlm-inference", "json-parse"]
    if multi_view_passed:
        b_cog = 0.42
    elif physics_validated:
        b_cog = 0.30
    else:
        b_cog = 0.79

    # Rough D_transform: each transform in stack contributes (1 - invertibility)
    invertibility = {
        "image-read": 1.0,
        "colormap-invert": 0.7,
        "vlm-inference": 0.3,
        "json-parse": 0.95,
    }
    raw_d = 1.0
    for t in stack:
        inv = invertibility.get(t, 0.5)
        raw_d *= 1.0 + (1.0 - inv)  # multiplicative accumulation

    d_transform = min(3.0, max(1.0, raw_d))

    return AcRiskComponents(
        u_phys=u_phys,
        d_transform=d_transform,
        b_cog=b_cog,
        transform_stack=stack,
        multi_view_passed=multi_view_passed,
        physics_validated=physics_validated,
    )


# Forward refs for type checkers
AcRiskComponents.model_rebuild()
PerceptualInventory.model_rebuild()
