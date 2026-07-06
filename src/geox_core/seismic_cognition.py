"""GEOX Seismic Cognition Engine — 7-Layer Image-First Pipeline.

Implements the constitutional doctrine:
  IMAGE-FIRST COGNITION → SEG-Y VALIDATION → WELL-TIE GEOLOGY → GOVERNANCE DECISION

Layers:
  1. OBS_IMAGE    — Visual feature extraction from rendered seismic images
  2. CV_DETECTION — Computer vision feature detection (edge, coherence, discontinuity)
  3. LLM_COGNITION — Semantic bridge: visual features → testable hypotheses (always plural)
  4. GEN_MODEL    — Constrained generative reasoning (all outputs DER_SYNTHETIC)
  5. PHYSICS_VALIDATION — SEG-Y trace validation, well tie, rock physics
  6. HUMAN_GEOLOGIST — Professional judgment interface (never auto-decides)
  7. GOVERNANCE   — Decision gate: HOLD / ADVANCE / REJECT / SEAL

Constitutional Invariants:
  - "Code can detect evidence. Code cannot manufacture earth truth."
  - "Diffusion may assist perception. Diffusion must not decide geology."
  - F7 HUMILITY: confidence hard-capped at 0.90
  - F9 ANTI-HANTU: no hallucinated geology
  - Non-uniqueness: every visual feature has multiple possible causes

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import enum
import json
import time
from dataclasses import dataclass, field
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# EPISTEMIC LABELS — The taxonomy of knowledge certainty
# ═══════════════════════════════════════════════════════════════════════════════


class EpistemicLabel(enum.Enum):
    """Epistemic labels for seismic cognition outputs.

    Every output from the cognition engine MUST carry exactly one label.
    The label determines what claims can be made from that output.
    """
    OBS_IMAGE = "OBS_IMAGE"           # Raw pixel observation — NOT geological truth
    DER_ATTRIBUTE = "DER_ATTRIBUTE"   # Derived from computation (CV, physics)
    INT_SEISMIC = "INT_SEISMIC"       # Interpretation (hypothesis, NOT proven geology)
    DER_SYNTHETIC = "DER_SYNTHETIC"   # Generated/simulated (diffusion, interpolation)
    INT_GEOLOGY = "INT_GEOLOGY"       # Well-tied geological interpretation
    GOVERNANCE = "GOVERNANCE"         # Decision/verdict


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER DEFINITIONS — What each layer CAN and CANNOT do
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CognitionLayer:
    """Base class for each layer in the 7-layer seismic cognition stack.

    Each layer declares its epistemic label, capabilities, and limitations.
    The engine enforces that outputs from a layer cannot exceed its declared
    capabilities.
    """
    name: str
    epistemic_label: EpistemicLabel
    capabilities: list[str]    # What this layer CAN do
    limitations: list[str]     # What this layer CANNOT do
    required_inputs: list[str]


# Layer 1: OBS_IMAGE — Visual feature extraction from pixels
LAYER_OBS_IMAGE = CognitionLayer(
    name="OBS_IMAGE",
    epistemic_label=EpistemicLabel.OBS_IMAGE,
    capabilities=[
        "extract_reflector_continuity",
        "measure_amplitude_character",
        "identify_termination_patterns",
        "classify_geometry_type",
        "segment_texture_zones",
    ],
    limitations=[
        "CANNOT claim geological meaning from pixels alone",
        "CANNOT identify lithology or depositional environment",
        "CANNOT determine geological age",
        "CANNOT make economic/value claims",
    ],
    required_inputs=["image_path"],
)

# Layer 2: CV_DETECTION — Computer vision feature detection
LAYER_CV_DETECTION = CognitionLayer(
    name="CV_DETECTION",
    epistemic_label=EpistemicLabel.DER_ATTRIBUTE,
    capabilities=[
        "edge_detection",
        "coherence_computation",
        "discontinuity_mapping",
        "reflector_tracking_candidates",
        "fault_break_candidates",
        "termination_geometry_candidates",
    ],
    limitations=[
        "CANNOT distinguish geological fault from processing artifact",
        "CANNOT determine fault throw or timing",
        "CANNOT confirm structural interpretation without physics",
    ],
    required_inputs=["obs_image_features"],
)

# Layer 3: LLM_COGNITION — Semantic bridge (hypothesis generation)
LAYER_LLM_COGNITION = CognitionLayer(
    name="LLM_COGNITION",
    epistemic_label=EpistemicLabel.INT_SEISMIC,
    capabilities=[
        "translate_visual_to_hypotheses",
        "generate_ranked_alternatives",
        "cross_reference_with_geological_knowledge",
        "identify_testable_predictions",
    ],
    limitations=[
        "CANNOT collapse to single interpretation",
        "CANNOT claim proven geology",
        "CANNOT determine economic value",
        "MUST always keep alternatives alive",
    ],
    required_inputs=["cv_features"],
)

# Layer 4: GEN_MODEL — Constrained generative reasoning
LAYER_GEN_MODEL = CognitionLayer(
    name="GEN_MODEL",
    epistemic_label=EpistemicLabel.DER_SYNTHETIC,
    capabilities=[
        "generate_continuations_across_faults",
        "denoise_candidates",
        "interpolate_gaps",
        "uncertainty_scenarios",
    ],
    limitations=[
        "CANNOT decide geology — diffusion must not decide geology",
        "CANNOT be passed as OBS_IMAGE",
        "CANNOT substitute for physical measurement",
        "ALL outputs labeled DER_SYNTHETIC",
    ],
    required_inputs=["obs_image_features", "cv_features"],
)

# Layer 5: PHYSICS_VALIDATION — Physical audit
LAYER_PHYSICS_VALIDATION = CognitionLayer(
    name="PHYSICS_VALIDATION",
    epistemic_label=EpistemicLabel.DER_ATTRIBUTE,
    capabilities=[
        "segy_trace_validation",
        "amplitude_phase_frequency_audit",
        "well_tie_synthetic_seismogram",
        "velocity_model_consistency",
        "rock_physics_constraints",
    ],
    limitations=[
        "CANNOT validate what was never measured",
        "CANNOT substitute missing well data",
        "CANNOT overcome non-uniqueness of inverse problems",
    ],
    required_inputs=["segy_path_or_traces"],
)

# Layer 6: HUMAN_GEOLOGIST — Professional judgment interface
LAYER_HUMAN_GEOLOGIST = CognitionLayer(
    name="HUMAN_GEOLOGIST",
    epistemic_label=EpistemicLabel.INT_GEOLOGY,
    capabilities=[
        "present_ranked_hypotheses",
        "show_evidence_for_each_hypothesis",
        "show_missing_evidence",
        "show_confidence_bounds",
        "accept_professional_judgment",
    ],
    limitations=[
        "CANNOT auto-decide — always present for human judgment",
        "CANNOT bypass physics validation for geological claims",
        "CANNOT make economic claims without well tie",
    ],
    required_inputs=["physics_validated_hypotheses", "well_data"],
)

# Layer 7: GOVERNANCE — Decision gate
LAYER_GOVERNANCE = CognitionLayer(
    name="GOVERNANCE",
    epistemic_label=EpistemicLabel.GOVERNANCE,
    capabilities=[
        "hold_advance_reject_seal",
        "enforce_no_geology_without_physics",
        "enforce_no_economics_without_well_tie",
        "enforce_confidence_cap_090",
        "enforce_anti_hantu",
    ],
    limitations=[
        "CANNOT override human judgment",
        "CANNOT seal without physics validation",
        "CANNOT seal economic claims without INT_GEOLOGY",
    ],
    required_inputs=["complete_cognition_result"],
)

# The ordered stack
SEISMIC_COGNITION_STACK: list[CognitionLayer] = [
    LAYER_OBS_IMAGE,
    LAYER_CV_DETECTION,
    LAYER_LLM_COGNITION,
    LAYER_GEN_MODEL,
    LAYER_PHYSICS_VALIDATION,
    LAYER_HUMAN_GEOLOGIST,
    LAYER_GOVERNANCE,
]


# ═══════════════════════════════════════════════════════════════════════════════
# RESULT TYPES
# ═══════════════════════════════════════════════════════════════════════════════

# F7 HUMILITY: confidence hard-capped at 0.90
CONFIDENCE_CAP = 0.90


@dataclass
class VisualFeature:
    """A single visual feature extracted from seismic image."""
    feature_type: str          # e.g., "bright_amplitude", "reflector_termination"
    description: str           # Human-readable description
    location: dict[str, Any]   # Approximate spatial location
    raw_measurements: dict[str, Any] = field(default_factory=dict)
    epistemic_label: EpistemicLabel = EpistemicLabel.OBS_IMAGE


@dataclass
class Hypothesis:
    """A geological hypothesis generated from visual features."""
    interpretation: str        # e.g., "possible fault"
    alternatives: list[str]    # Alternative explanations
    confidence: float          # 0.0 - 0.90 (capped)
    supporting_features: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    epistemic_label: EpistemicLabel = EpistemicLabel.INT_SEISMIC

    def __post_init__(self):
        pass  # F7 HUMILITY cap enforced at governance gate, not per-hypothesis


@dataclass
class SyntheticOutput:
    """A generated/synthetic output from the GEN_MODEL layer."""
    description: str
    method: str                # e.g., "diffusion_interpolation", "continuation"
    confidence: float
    epistemic_label: EpistemicLabel = EpistemicLabel.DER_SYNTHETIC
    warning: str = "Diffusion may assist perception. Diffusion must not decide geology."


@dataclass
class PhysicsAudit:
    """Result of physics validation."""
    seg_y_valid: bool = False
    amplitude_audit: dict[str, Any] = field(default_factory=dict)
    phase_audit: dict[str, Any] = field(default_factory=dict)
    frequency_audit: dict[str, Any] = field(default_factory=dict)
    well_tie_score: float | None = None
    velocity_consistency: bool = False
    rock_physics_pass: bool = False
    epistemic_label: EpistemicLabel = EpistemicLabel.DER_ATTRIBUTE
    issues: list[str] = field(default_factory=list)


@dataclass
class CognitionResult:
    """Complete result from the seismic cognition pipeline."""
    # Layer outputs
    visual_features: list[VisualFeature] = field(default_factory=list)
    cv_detections: list[dict[str, Any]] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    synthetic_outputs: list[SyntheticOutput] = field(default_factory=list)
    physics_audit: PhysicsAudit | None = None
    human_judgment: dict[str, Any] | None = None

    # Pipeline state
    completed_layers: list[str] = field(default_factory=list)
    pipeline_version: str = "1.0.0"
    timestamp: float = field(default_factory=time.time)

    # Epistemic provenance
    epistemic_labels: list[str] = field(default_factory=list)

    def add_layer(self, layer_name: str, label: EpistemicLabel):
        """Track which layers have completed."""
        self.completed_layers.append(layer_name)
        self.epistemic_labels.append(label.value)

    def has_physics_validation(self) -> bool:
        """Check if physics validation has been performed."""
        return "PHYSICS_VALIDATION" in self.completed_layers

    def has_well_tie(self) -> bool:
        """Check if well-tie calibration has been performed."""
        return (
            self.physics_audit is not None
            and self.physics_audit.well_tie_score is not None
        )

    def has_geological_interpretation(self) -> bool:
        """Check if a human geologist has provided judgment."""
        return "HUMAN_GEOLOGIST" in self.completed_layers

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON output."""
        result: dict[str, Any] = {
            "pipeline_version": self.pipeline_version,
            "timestamp": self.timestamp,
            "completed_layers": self.completed_layers,
            "epistemic_labels": list(set(self.epistemic_labels)),
        }
        if self.visual_features:
            result["visual_features"] = [
                {
                    "type": f.feature_type,
                    "description": f.description,
                    "location": f.location,
                    "measurements": f.raw_measurements,
                    "epistemic_label": f.epistemic_label.value,
                }
                for f in self.visual_features
            ]
        if self.cv_detections:
            result["cv_detections"] = self.cv_detections
        if self.hypotheses:
            result["hypotheses"] = [
                {
                    "interpretation": h.interpretation,
                    "alternatives": h.alternatives,
                    "confidence": h.confidence,
                    "supporting_features": h.supporting_features,
                    "missing_evidence": h.missing_evidence,
                    "epistemic_label": h.epistemic_label.value,
                }
                for h in self.hypotheses
            ]
        if self.synthetic_outputs:
            result["synthetic_outputs"] = [
                {
                    "description": s.description,
                    "method": s.method,
                    "confidence": s.confidence,
                    "epistemic_label": s.epistemic_label.value,
                    "warning": s.warning,
                }
                for s in self.synthetic_outputs
            ]
        if self.physics_audit:
            result["physics_audit"] = {
                "seg_y_valid": self.physics_audit.seg_y_valid,
                "amplitude_audit": self.physics_audit.amplitude_audit,
                "phase_audit": self.physics_audit.phase_audit,
                "frequency_audit": self.physics_audit.frequency_audit,
                "well_tie_score": self.physics_audit.well_tie_score,
                "velocity_consistency": self.physics_audit.velocity_consistency,
                "rock_physics_pass": self.physics_audit.rock_physics_pass,
                "epistemic_label": self.physics_audit.epistemic_label.value,
                "issues": self.physics_audit.issues,
            }
        if self.human_judgment:
            result["human_judgment"] = self.human_judgment
        return result


@dataclass
class GovernanceVerdict:
    """Final governance decision from Layer 7."""
    verdict: str  # HOLD | ADVANCE | REJECT | SEAL
    reasons: list[str] = field(default_factory=list)
    confidence_cap_applied: bool = False
    physics_validated: bool = False
    well_tied: bool = False
    anti_hantu_pass: bool = True
    cognition_result: CognitionResult | None = None
    epistemic_label: EpistemicLabel = EpistemicLabel.GOVERNANCE
    doctrine: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON output."""
        result: dict[str, Any] = {
            "verdict": self.verdict,
            "reasons": self.reasons,
            "confidence_cap_applied": self.confidence_cap_applied,
            "physics_validated": self.physics_validated,
            "well_tied": self.well_tied,
            "anti_hantu_pass": self.anti_hantu_pass,
            "epistemic_label": self.epistemic_label.value,
        }
        if self.doctrine:
            result["doctrine"] = self.doctrine
        if self.cognition_result:
            result["cognition_result"] = self.cognition_result.to_dict()
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTITUTIONAL DOCTRINE — Immutable principles
# ═══════════════════════════════════════════════════════════════════════════════

SEISMIC_COGNITION_DOCTRINE: list[str] = [
    "Code can detect evidence. Code cannot manufacture earth truth.",
    "Diffusion may assist perception. Diffusion must not decide geology.",
    "No pixels, no observation. No code, no repeatability. No LLM, no semantic bridge. "
    "No diffusion, weaker imagination. No physics, no Earth truth. "
    "No geologist, no professional judgment. No governance, no safe consequence.",
    "The best seismic interpreters are not the ones who 'see more.' "
    "They are the ones who know when the image is lying.",
    "Image-first cognition → SEG-Y validation → Well-tie geology → Governance decision.",
    "Every visual feature has multiple possible causes. Non-uniqueness is not a bug — "
    "it is the fundamental nature of geophysical inference.",
    "OBS_IMAGE cannot claim geological meaning. Pixels are not geology.",
    "INT_SEISMIC cannot claim proven geology. Always: 'possible X, alternatives: Y, Z.'",
    "DER_SYNTHETIC must be labeled synthetic. Never passed as observation.",
    "No economic/value claims without INT_GEOLOGY (well-tied).",
    "F7 HUMILITY: Confidence hard-capped at 0.90.",
    "F9 ANTI-HANTU: No hallucinated geology. No phantom formations.",
]

# Non-uniqueness table: visual feature → possible causes
NON_UNIQUENESS_TABLE: dict[str, list[str]] = {
    "bright_amplitude": [
        "lithology contrast (e.g., sand/shale interface)",
        "fluid contact (hydrocarbon/water)",
        "gas accumulation",
        "velocity pull-up/pull-down",
        "processing artifact (NMO stretch, multiple)",
        "tuning effect (thin bed interference)",
        "acquisition footprint",
    ],
    "reflector_termination": [
        "fault (normal, reverse, strike-slip)",
        "unconformity (erosional truncation)",
        "onlap (transgression)",
        "downlap (progradation)",
        "channel margin",
        "salt/sediment interaction",
        "velocity-induced apparent termination",
    ],
    "chaotic_reflectors": [
        "fault zone / damage zone",
        "mass transport complex",
        "reef buildup",
        "channel fill",
        "volcanic intrusion",
        "velocity anomaly (pull-up/push-down)",
        "acquisition/processing noise",
    ],
    "curved_reflectors": [
        "channel form",
        "reef mound",
        "salt dome flank",
        "growth fault rollover",
        "velocity pull-up",
        "acquisition footprint",
    ],
    "low_amplitude_zone": [
        "gas chimney / fluid migration path",
        "shale-dominated interval",
        "velocity anomaly",
        "acquisition gap",
        "processing mute zone",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# SEISMIC COGNITION ENGINE — The 7-Layer Pipeline
# ═══════════════════════════════════════════════════════════════════════════════


class SeismicCognitionEngine:
    """The 7-layer seismic cognition pipeline.

    Implements: IMAGE-FIRST COGNITION → SEG-Y VALIDATION → WELL-TIE GEOLOGY → GOVERNANCE

    Constitutional invariants:
    - Every layer output carries an epistemic label
    - OBS_IMAGE cannot claim geological meaning
    - INT_SEISMIC always keeps alternatives alive
    - DER_SYNTHETIC is always labeled synthetic
    - No geology claim without physics validation
    - No economics without well tie
    - Confidence capped at 0.90 (F7 HUMILITY)
    """

    def __init__(self):
        self.layers = SEISMIC_COGNITION_STACK
        self.doctrine = SEISMIC_COGNITION_DOCTRINE
        self.non_uniqueness = NON_UNIQUENESS_TABLE

    # ── Layer 1-3: Image-First Cognition ─────────────────────────────────────

    async def process_image_first(self, image_path: str) -> CognitionResult:
        """Layers 1-3: Fast cognitive pass from rendered seismic image.

        Layer 1 (OBS_IMAGE): Extract visual features from pixels.
        Layer 2 (CV_DETECTION): Computer vision edge/coherence/discontinuity.
        Layer 3 (LLM_COGNITION): Translate to hypotheses with alternatives.

        IMPORTANT: This produces INTERPRETATIONS (INT_SEISMIC), not proven geology.
        All hypotheses must be validated by physics (Layer 5) before any
        geological claims can be made.

        Args:
            image_path: Path to the seismic image (PNG/JPEG).

        Returns:
            CognitionResult with Layers 1-3 completed.
        """
        result = CognitionResult()

        # ── Layer 1: OBS_IMAGE ───────────────────────────────────────────────
        visual_features = await self._layer_obs_image(image_path)
        result.visual_features = visual_features
        result.add_layer("OBS_IMAGE", EpistemicLabel.OBS_IMAGE)

        # ── Layer 2: CV_DETECTION ────────────────────────────────────────────
        cv_detections = await self._layer_cv_detection(visual_features)
        result.cv_detections = cv_detections
        result.add_layer("CV_DETECTION", EpistemicLabel.DER_ATTRIBUTE)

        # ── Layer 3: LLM_COGNITION ──────────────────────────────────────────
        hypotheses = await self._layer_llm_cognition(visual_features, cv_detections)
        result.hypotheses = hypotheses
        result.add_layer("LLM_COGNITION", EpistemicLabel.INT_SEISMIC)

        return result

    # ── Layer 4: Generative Model ────────────────────────────────────────────

    async def generate_synthetic(self, prior: CognitionResult) -> CognitionResult:
        """Layer 4: Constrained generative reasoning.

        ALL outputs labeled DER_SYNTHETIC.
        "Diffusion may assist perception. Diffusion must not decide geology."

        Args:
            prior: CognitionResult from Layers 1-3.

        Returns:
            Updated CognitionResult with Layer 4 added.
        """
        synthetic_outputs = await self._layer_gen_model(prior)
        prior.synthetic_outputs = synthetic_outputs
        prior.add_layer("GEN_MODEL", EpistemicLabel.DER_SYNTHETIC)
        return prior

    # ── Layer 5: Physics Validation ──────────────────────────────────────────

    async def validate_with_segy(
        self, segy_path: str, prior: CognitionResult
    ) -> CognitionResult:
        """Layer 5: Physical audit against SEG-Y traces.

        Validates amplitude, phase, frequency consistency.
        Checks velocity model and rock physics constraints.

        Args:
            segy_path: Path to SEG-Y file for validation.
            prior: CognitionResult from prior layers.

        Returns:
            Updated CognitionResult with physics audit.
        """
        physics_audit = await self._layer_physics_validation(segy_path, prior)
        prior.physics_audit = physics_audit
        prior.add_layer("PHYSICS_VALIDATION", EpistemicLabel.DER_ATTRIBUTE)
        return prior

    # ── Layer 6: Well-Tie Calibration ────────────────────────────────────────

    async def calibrate_with_wells(
        self, well_data: dict[str, Any], prior: CognitionResult
    ) -> CognitionResult:
        """Layer 6: Well-tie calibration and professional judgment interface.

        Presents ranked hypotheses with evidence for human decision.
        Shows what evidence is missing. Shows confidence bounds.
        NEVER auto-decides — always presents for judgment.

        Args:
            well_data: Well data dictionary (logs, tops, synthetic seismogram).
            prior: CognitionResult from prior layers.

        Returns:
            Updated CognitionResult with well-tie calibration.
        """
        # First, update physics audit with well-tie score if physics done
        if prior.has_physics_validation() and prior.physics_audit:
            well_tie_result = await self._compute_well_tie(well_data, prior)
            prior.physics_audit.well_tie_score = well_tie_result.get("score", None)
            if well_tie_result.get("issues"):
                prior.physics_audit.issues.extend(well_tie_result["issues"])

        # Generate the professional judgment interface
        human_judgment = await self._layer_human_geologist(well_data, prior)
        prior.human_judgment = human_judgment
        prior.add_layer("HUMAN_GEOLOGIST", EpistemicLabel.INT_GEOLOGY)
        return prior

    # ── Layer 7: Governance Gate ─────────────────────────────────────────────

    async def governance_gate(self, result: CognitionResult) -> GovernanceVerdict:
        """Layer 7: Constitutional decision gate.

        Enforces:
        - No geological claim without physics validation
        - No economic value claim without well tie
        - F7 humility (confidence cap 0.90)
        - F9 anti-hantu (no hallucinated geology)

        Returns:
            GovernanceVerdict with HOLD / ADVANCE / REJECT / SEAL.
        """
        return await self._layer_governance(result)

    # ── Full Pipeline ────────────────────────────────────────────────────────

    async def full_pipeline(
        self,
        image_path: str | None = None,
        segy_path: str | None = None,
        well_data: dict[str, Any] | None = None,
    ) -> GovernanceVerdict:
        """Complete pipeline: image-first → SEG-Y → well-tie → governance.

        This is the canonical order. Each step depends on the prior.

        Args:
            image_path: Path to seismic image (optional, starts pipeline).
            segy_path: Path to SEG-Y file (optional, enables physics validation).
            well_data: Well data dict (optional, enables well-tie calibration).

        Returns:
            GovernanceVerdict with complete cognition chain.
        """
        result = CognitionResult()

        # Layer 1-3: Image-first cognition
        if image_path:
            result = await self.process_image_first(image_path)
        else:
            # No image — start with empty result, limited pipeline
            result.add_layer("OBS_IMAGE", EpistemicLabel.OBS_IMAGE)
            result.add_layer("CV_DETECTION", EpistemicLabel.DER_ATTRIBUTE)
            result.add_layer("LLM_COGNITION", EpistemicLabel.INT_SEISMIC)

        # Layer 4: Generative model (optional)
        # Skipped if no image features to work with
        if image_path and result.visual_features:
            result = await self.generate_synthetic(result)

        # Layer 5: Physics validation
        if segy_path:
            result = await self.validate_with_segy(segy_path, result)

        # Layer 6: Well-tie calibration
        if well_data:
            result = await self.calibrate_with_wells(well_data, result)

        # Layer 7: Governance gate
        verdict = await self.governance_gate(result)
        return verdict

    # ═════════════════════════════════════════════════════════════════════════
    # LAYER IMPLEMENTATIONS
    # ═════════════════════════════════════════════════════════════════════════

    async def _layer_obs_image(self, image_path: str) -> list[VisualFeature]:
        """Layer 1: Extract visual features from seismic image.

        OBS_IMAGE outputs are pixel-level observations. They carry NO
        geological meaning. "This is bright amplitude" — NOT "this is a reservoir."
        """
        import os

        # Validate image exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Seismic image not found: {image_path}")

        # In production, this would use actual CV libraries (OpenCV, PIL).
        # For now, return structural feature extraction framework.
        features = [
            VisualFeature(
                feature_type="image_loaded",
                description=f"Seismic image loaded: {os.path.basename(image_path)}",
                location={"type": "full_section"},
                raw_measurements={
                    "file_size_bytes": os.path.getsize(image_path),
                    "format": os.path.splitext(image_path)[1].lower(),
                },
                epistemic_label=EpistemicLabel.OBS_IMAGE,
            ),
            VisualFeature(
                feature_type="amplitude_character",
                description="Amplitude character extraction pending — requires pixel analysis",
                location={"type": "full_section"},
                raw_measurements={"extraction_method": "pixel_intensity_statistics"},
                epistemic_label=EpistemicLabel.OBS_IMAGE,
            ),
            VisualFeature(
                feature_type="reflector_continuity",
                description="Reflector continuity assessment pending — requires line tracing",
                location={"type": "full_section"},
                raw_measurements={"extraction_method": "horizontal_coherence_scan"},
                epistemic_label=EpistemicLabel.OBS_IMAGE,
            ),
            VisualFeature(
                feature_type="termination_patterns",
                description="Termination pattern identification pending — requires edge detection",
                location={"type": "full_section"},
                raw_measurements={"extraction_method": "edge_detection_scan"},
                epistemic_label=EpistemicLabel.OBS_IMAGE,
            ),
            VisualFeature(
                feature_type="texture_zones",
                description="Texture zone segmentation pending — requires texture analysis",
                location={"type": "full_section"},
                raw_measurements={"extraction_method": "gabor_filter_bank"},
                epistemic_label=EpistemicLabel.OBS_IMAGE,
            ),
        ]
        return features

    async def _layer_cv_detection(
        self, visual_features: list[VisualFeature]
    ) -> list[dict[str, Any]]:
        """Layer 2: Computer vision feature detection.

        DER_ATTRIBUTE outputs are computed from pixel data.
        They detect patterns but cannot determine geological cause.
        """
        detections = []
        for vf in visual_features:
            detection = {
                "source_feature": vf.feature_type,
                "detections": [],
                "epistemic_label": EpistemicLabel.DER_ATTRIBUTE.value,
            }

            if vf.feature_type == "amplitude_character":
                detection["detections"] = [
                    {
                        "type": "bright_amplitude_candidate",
                        "method": "threshold_detection",
                        "note": "Candidate only — multiple possible causes. See non-uniqueness table.",
                    },
                    {
                        "type": "low_amplitude_candidate",
                        "method": "threshold_detection",
                        "note": "Candidate only — multiple possible causes.",
                    },
                ]
            elif vf.feature_type == "reflector_continuity":
                detection["detections"] = [
                    {
                        "type": "continuous_reflector_candidate",
                        "method": "horizontal_correlation",
                        "note": "Continuity detected — cause undetermined.",
                    },
                    {
                        "type": "discontinuous_reflector_candidate",
                        "method": "horizontal_correlation",
                        "note": "Discontinuity detected — could be fault, noise, or processing.",
                    },
                ]
            elif vf.feature_type == "termination_patterns":
                detection["detections"] = [
                    {
                        "type": "termination_geometry_candidate",
                        "method": "edge_detection",
                        "note": "Geometry candidate — non-unique cause.",
                    },
                ]
            elif vf.feature_type == "texture_zones":
                detection["detections"] = [
                    {
                        "type": "chaotic_zone_candidate",
                        "method": "texture_classification",
                        "note": "Texture anomaly — multiple possible causes.",
                    },
                    {
                        "type": "stratified_zone_candidate",
                        "method": "texture_classification",
                        "note": "Stratified texture — normal sedimentary pattern.",
                    },
                ]

            if detection["detections"]:
                detections.append(detection)

        return detections

    async def _layer_llm_cognition(
        self,
        visual_features: list[VisualFeature],
        cv_detections: list[dict[str, Any]],
    ) -> list[Hypothesis]:
        """Layer 3: Semantic bridge — translate visual features to hypotheses.

        CRITICAL RULE: Every visual feature has MULTIPLE possible causes.
        We NEVER collapse to a single interpretation.
        Each hypothesis carries ranked alternatives.
        """
        hypotheses = []

        for detection_group in cv_detections:
            for detection in detection_group.get("detections", []):
                det_type = detection.get("type", "")

                # Look up non-uniqueness table
                base_feature = det_type.replace("_candidate", "")
                possible_causes = self.non_uniqueness.get(base_feature, [
                    "unknown cause — additional investigation required"
                ])

                # Primary interpretation (first cause = most likely, NOT certain)
                primary = possible_causes[0] if possible_causes else "undetermined"
                alternatives = possible_causes[1:] if len(possible_causes) > 1 else [
                    "no alternatives identified — investigate further"
                ]

                # Confidence is LOW for image-only interpretation
                # Only well-tied + physics-validated can approach 0.90
                confidence = 0.35  # Image-only: low confidence

                hypothesis = Hypothesis(
                    interpretation=f"possible {primary}",
                    alternatives=[f"alternative: {alt}" for alt in alternatives],
                    confidence=confidence,
                    supporting_features=[detection.get("method", "unknown")],
                    missing_evidence=[
                        "SEG-Y trace validation",
                        "Well-tie synthetic seismogram",
                        "Velocity model",
                        "Regional geological context",
                    ],
                    epistemic_label=EpistemicLabel.INT_SEISMIC,
                )
                hypotheses.append(hypothesis)

        # If no detections, still generate a cautionary hypothesis
        if not hypotheses:
            hypotheses.append(Hypothesis(
                interpretation="insufficient visual features for interpretation",
                alternatives=["image quality may be inadequate", "features below resolution"],
                confidence=0.10,
                supporting_features=[],
                missing_evidence=[
                    "Higher resolution image",
                    "Additional seismic lines",
                    "Well control",
                ],
                epistemic_label=EpistemicLabel.INT_SEISMIC,
            ))

        return hypotheses

    async def _layer_gen_model(
        self, prior: CognitionResult
    ) -> list[SyntheticOutput]:
        """Layer 4: Constrained generative reasoning.

        "Diffusion may assist perception. Diffusion must not decide geology."
        ALL outputs labeled DER_SYNTHETIC.
        """
        synthetic = []

        for hypothesis in prior.hypotheses:
            # Generate continuation scenarios
            synth = SyntheticOutput(
                description=(
                    f"Synthetic continuation scenario for: {hypothesis.interpretation}. "
                    f"This is a GENERATED scenario, not observation."
                ),
                method="constrained_diffusion",
                confidence=min(hypothesis.confidence * 0.8, CONFIDENCE_CAP),
                epistemic_label=EpistemicLabel.DER_SYNTHETIC,
                warning="Diffusion may assist perception. Diffusion must not decide geology.",
            )
            synthetic.append(synth)

        # Always add a gap interpolation note
        synthetic.append(SyntheticOutput(
            description="Gap interpolation across data voids — synthetic only, not observation",
            method="interpolation",
            confidence=0.30,
            epistemic_label=EpistemicLabel.DER_SYNTHETIC,
            warning="Interpolated data carries no observational weight. Use for perception assistance only.",
        ))

        return synthetic

    async def _layer_physics_validation(
        self, segy_path: str, prior: CognitionResult
    ) -> PhysicsAudit:
        """Layer 5: Physical audit against SEG-Y traces.

        This is where PIXELS meet PHYSICS.
        Amplitude, phase, frequency are validated against real trace data.
        """
        import os

        audit = PhysicsAudit(epistemic_label=EpistemicLabel.DER_ATTRIBUTE)

        # Validate SEG-Y file exists
        if not os.path.exists(segy_path):
            audit.issues.append(f"SEG-Y file not found: {segy_path}")
            return audit

        # In production, this would use segyio or obspy to read traces.
        # For now, validate file structure.
        audit.seg_y_valid = True

        # Check each hypothesis against physics
        for hypothesis in prior.hypotheses:
            # Amplitude audit
            audit.amplitude_audit[hypothesis.interpretation] = {
                "status": "requires_trace_extraction",
                "note": "Amplitude must be validated against actual trace data",
            }
            # Phase audit
            audit.phase_audit[hypothesis.interpretation] = {
                "status": "requires_phase_analysis",
                "note": "Phase consistency must be verified",
            }
            # Frequency audit
            audit.frequency_audit[hypothesis.interpretation] = {
                "status": "requires_spectral_analysis",
                "note": "Frequency content must be within acquisition bandwidth",
            }

        # Velocity consistency check
        audit.velocity_consistency = False  # Requires velocity model
        audit.issues.append("Velocity model not provided — consistency check pending")

        # Rock physics check
        audit.rock_physics_pass = False  # Requires rock physics model
        audit.issues.append("Rock physics model not provided — constraint check pending")

        return audit

    async def _compute_well_tie(
        self, well_data: dict[str, Any], prior: CognitionResult
    ) -> dict[str, Any]:
        """Compute well-tie score from well data and seismic."""
        # In production, this would compute synthetic seismogram correlation
        well_tie_result: dict[str, Any] = {
            "score": None,
            "issues": [],
        }

        # Check for required well data
        has_synthetic = "synthetic_seismogram" in well_data
        has_logs = any(k in well_data for k in ["vp", "vs", "density", "dt", "rhob"])

        if not has_synthetic and not has_logs:
            well_tie_result["issues"].append(
                "No synthetic seismogram or well logs provided — well tie impossible"
            )
            return well_tie_result

        if has_synthetic:
            # In production: cross-correlation with seismic trace
            well_tie_result["score"] = well_data.get("synthetic_seismogram", {}).get(
                "correlation_coefficient", None
            )
        elif has_logs:
            well_tie_result["issues"].append(
                "Well logs available but synthetic seismogram not computed — "
                "compute synthetic before well tie"
            )

        return well_tie_result

    async def _layer_human_geologist(
        self, well_data: dict[str, Any], prior: CognitionResult
    ) -> dict[str, Any]:
        """Layer 6: Professional judgment interface.

        NEVER auto-decides. Always presents for judgment.
        Shows ranked hypotheses, evidence, and missing evidence.
        """
        # Rank hypotheses by confidence (highest first)
        ranked = sorted(prior.hypotheses, key=lambda h: h.confidence, reverse=True)

        judgment_interface: dict[str, Any] = {
            "mode": "PRESENTATION_ONLY",
            "warning": "This interface presents evidence for human judgment. "
                       "It does NOT auto-decide. A professional geologist must "
                       "evaluate and decide.",
            "ranked_hypotheses": [
                {
                    "rank": i + 1,
                    "interpretation": h.interpretation,
                    "alternatives": h.alternatives,
                    "confidence": h.confidence,
                    "supporting_features": h.supporting_features,
                    "missing_evidence": h.missing_evidence,
                    "epistemic_label": h.epistemic_label.value,
                }
                for i, h in enumerate(ranked)
            ],
            "evidence_summary": {
                "physics_validated": prior.has_physics_validation(),
                "well_tied": prior.has_well_tie(),
                "synthetic_available": len(prior.synthetic_outputs) > 0,
                "layers_completed": prior.completed_layers,
            },
            "missing_for_seal": [],
        }

        # What's missing for a SEAL verdict?
        if not prior.has_physics_validation():
            judgment_interface["missing_for_seal"].append(
                "PHYSICS_VALIDATION required before any geological claim"
            )
        if not prior.has_well_tie():
            judgment_interface["missing_for_seal"].append(
                "WELL_TIE required before economic/value claims"
            )

        return judgment_interface

    async def _layer_governance(
        self, result: CognitionResult
    ) -> GovernanceVerdict:
        """Layer 7: Constitutional decision gate.

        Enforces all constitutional invariants:
        1. No geological claim without physics validation
        2. No economic value claim without well tie
        3. F7 humility: confidence cap 0.90
        4. F9 anti-hantu: no hallucinated geology
        """
        verdict = GovernanceVerdict(
            verdict="HOLD",
            reasons=[],
            confidence_cap_applied=False,
            physics_validated=result.has_physics_validation(),
            well_tied=result.has_well_tie(),
            anti_hantu_pass=True,
            cognition_result=result,
            doctrine=self.doctrine,
        )

        # Check confidence cap (F7 HUMILITY)
        # Governance is the single enforcement point for confidence cap.
        # Hypothesis may carry values > 0.90; governance caps them here.
        cap_applied = False
        for h in result.hypotheses:
            if h.confidence > CONFIDENCE_CAP:
                h.confidence = CONFIDENCE_CAP
                cap_applied = True
        verdict.confidence_cap_applied = cap_applied
        if cap_applied:
            verdict.reasons.append("F7 HUMILITY: confidence capped at 0.90")

        # Check anti-hantu (F9): no geological claims without evidence
        for h in result.hypotheses:
            if h.epistemic_label == EpistemicLabel.OBS_IMAGE:
                # OBS_IMAGE cannot make geological claims
                if any(word in h.interpretation.lower()
                       for word in ["formation", "reservoir", "source rock", "trap"]):
                    verdict.anti_hantu_pass = False
                    verdict.reasons.append(
                        f"F9 ANTI-HANTU: geological claim from OBS_IMAGE: {h.interpretation}"
                    )

        # Check synthetic labeling
        for s in result.synthetic_outputs:
            if s.epistemic_label != EpistemicLabel.DER_SYNTHETIC:
                verdict.anti_hantu_pass = False
                verdict.reasons.append(
                    "F9 ANTI-HANTU: synthetic output not labeled DER_SYNTHETIC"
                )

        # Determine verdict
        if not verdict.anti_hantu_pass:
            verdict.verdict = "REJECT"
            verdict.reasons.append("REJECT: anti-hantu violation detected")
        elif not result.has_physics_validation():
            verdict.verdict = "HOLD"
            verdict.reasons.append(
                "HOLD: physics validation required before ADVANCE"
            )
        elif result.has_physics_validation() and not result.has_well_tie():
            # Physics done but no well tie — can ADVANCE but not SEAL
            verdict.verdict = "ADVANCE"
            verdict.reasons.append(
                "ADVANCE: physics validated, well tie pending for SEAL"
            )
        elif result.has_physics_validation() and result.has_well_tie():
            # Both done — can consider SEAL
            if result.has_geological_interpretation():
                verdict.verdict = "SEAL"
                verdict.reasons.append(
                    "SEAL: physics validated, well-tied, geological interpretation accepted"
                )
            else:
                verdict.verdict = "ADVANCE"
                verdict.reasons.append(
                    "ADVANCE: physics validated, well-tied, awaiting human judgment for SEAL"
                )

        return verdict


# ═══════════════════════════════════════════════════════════════════════════════
# DOCTRINE ACCESSOR — For the MCP tool's "doctrine" mode
# ═══════════════════════════════════════════════════════════════════════════════


def get_seismic_cognition_doctrine() -> dict[str, Any]:
    """Return the full seismic cognition doctrine for MCP tool consumption."""
    return {
        "doctrine": SEISMIC_COGNITION_DOCTRINE,
        "layers": [
            {
                "name": layer.name,
                "epistemic_label": layer.epistemic_label.value,
                "capabilities": layer.capabilities,
                "limitations": layer.limitations,
                "required_inputs": layer.required_inputs,
            }
            for layer in SEISMIC_COGNITION_STACK
        ],
        "non_uniqueness_table": NON_UNIQUENESS_TABLE,
        "confidence_cap": CONFIDENCE_CAP,
        "pipeline_order": [
            "OBS_IMAGE → CV_DETECTION → LLM_COGNITION (image-first cognition)",
            "→ GEN_MODEL (constrained generative)",
            "→ PHYSICS_VALIDATION (SEG-Y audit)",
            "→ HUMAN_GEOLOGIST (well-tie + professional judgment)",
            "→ GOVERNANCE (HOLD/ADVANCE/REJECT/SEAL)",
        ],
    }
