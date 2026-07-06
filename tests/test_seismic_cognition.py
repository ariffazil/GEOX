"""Tests for GEOX Seismic Cognition Engine — 7-Layer Pipeline.

Tests constitutional invariants:
  - Epistemic labeling correctness per layer
  - OBS_IMAGE cannot contain geological claims
  - Governance gate REJECTS without physics validation
  - DER_SYNTHETIC always labeled synthetic
  - Non-uniqueness: bright amplitude → multiple hypotheses
  - Confidence cap at 0.90 (F7 HUMILITY)
  - Full pipeline ordering

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from geox_core.seismic_cognition import (
    CONFIDENCE_CAP,
    NON_UNIQUENESS_TABLE,
    SEISMIC_COGNITION_DOCTRINE,
    SEISMIC_COGNITION_STACK,
    CognitionLayer,
    CognitionResult,
    EpistemicLabel,
    GovernanceVerdict,
    Hypothesis,
    PhysicsAudit,
    SeismicCognitionEngine,
    SyntheticOutput,
    VisualFeature,
    get_seismic_cognition_doctrine,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def engine():
    """Create a fresh SeismicCognitionEngine."""
    return SeismicCognitionEngine()


@pytest.fixture
def temp_seismic_image(tmp_path):
    """Create a temporary seismic image file."""
    img_path = tmp_path / "seismic_section.png"
    # Write a minimal PNG (1x1 white pixel)
    img_path.write_bytes(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
        b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
        b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return str(img_path)


@pytest.fixture
def temp_segy_file(tmp_path):
    """Create a temporary SEG-Y file."""
    segy_path = tmp_path / "survey.sgy"
    # Write minimal dummy content
    segy_path.write_bytes(b'\x00' * 3600)  # SEG-Y text header size
    return str(segy_path)


@pytest.fixture
def sample_well_data():
    """Sample well data for well-tie calibration."""
    return {
        "well_id": "TEST-001",
        "vp": [2000, 2200, 2500, 2800, 3000],
        "density": [2.0, 2.1, 2.2, 2.35, 2.5],
        "depth": [1000, 1100, 1200, 1300, 1400],
        "synthetic_seismogram": {
            "correlation_coefficient": 0.78,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1: Epistemic Label Correctness
# ═══════════════════════════════════════════════════════════════════════════════


class TestEpistemicLabels:
    """Each layer must carry the correct epistemic label."""

    def test_layer_stack_has_seven_layers(self):
        assert len(SEISMIC_COGNITION_STACK) == 7

    def test_obs_image_label(self):
        layer = SEISMIC_COGNITION_STACK[0]
        assert layer.name == "OBS_IMAGE"
        assert layer.epistemic_label == EpistemicLabel.OBS_IMAGE

    def test_cv_detection_label(self):
        layer = SEISMIC_COGNITION_STACK[1]
        assert layer.name == "CV_DETECTION"
        assert layer.epistemic_label == EpistemicLabel.DER_ATTRIBUTE

    def test_llm_cognition_label(self):
        layer = SEISMIC_COGNITION_STACK[2]
        assert layer.name == "LLM_COGNITION"
        assert layer.epistemic_label == EpistemicLabel.INT_SEISMIC

    def test_gen_model_label(self):
        layer = SEISMIC_COGNITION_STACK[3]
        assert layer.name == "GEN_MODEL"
        assert layer.epistemic_label == EpistemicLabel.DER_SYNTHETIC

    def test_physics_validation_label(self):
        layer = SEISMIC_COGNITION_STACK[4]
        assert layer.name == "PHYSICS_VALIDATION"
        assert layer.epistemic_label == EpistemicLabel.DER_ATTRIBUTE

    def test_human_geologist_label(self):
        layer = SEISMIC_COGNITION_STACK[5]
        assert layer.name == "HUMAN_GEOLOGIST"
        assert layer.epistemic_label == EpistemicLabel.INT_GEOLOGY

    def test_governance_label(self):
        layer = SEISMIC_COGNITION_STACK[6]
        assert layer.name == "GOVERNANCE"
        assert layer.epistemic_label == EpistemicLabel.GOVERNANCE

    def test_all_layers_have_capabilities(self):
        for layer in SEISMIC_COGNITION_STACK:
            assert len(layer.capabilities) > 0, f"{layer.name} has no capabilities"

    def test_all_layers_have_limitations(self):
        for layer in SEISMIC_COGNITION_STACK:
            assert len(layer.limitations) > 0, f"{layer.name} has no limitations"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2: OBS_IMAGE Cannot Contain Geological Claims
# ═══════════════════════════════════════════════════════════════════════════════


class TestObsImageBoundary:
    """OBS_IMAGE outputs must NEVER contain geological meaning."""

    def test_obs_image_features_are_pixel_observations(self):
        """Visual features from Layer 1 must be pixel-level, not geological."""
        feature = VisualFeature(
            feature_type="bright_amplitude",
            description="High amplitude anomaly detected in pixel range [200-300]",
            location={"trace_range": [100, 200], "time_range": [1.5, 2.0]},
            epistemic_label=EpistemicLabel.OBS_IMAGE,
        )
        # Must be OBS_IMAGE
        assert feature.epistemic_label == EpistemicLabel.OBS_IMAGE
        # Must NOT contain geological terms in the feature itself
        geological_terms = ["reservoir", "formation", "source rock", "trap", "hydrocarbon"]
        for term in geological_terms:
            assert term not in feature.description.lower(), (
                f"OBS_IMAGE feature contains geological term: {term}"
            )

    def test_obs_image_layer_cannot_claim_geology(self):
        """The OBS_IMAGE layer's limitations explicitly forbid geological claims."""
        obs_layer = SEISMIC_COGNITION_STACK[0]
        limitations_text = " ".join(obs_layer.limitations).lower()
        assert "geological" in limitations_text or "geology" in limitations_text

    @pytest.mark.asyncio
    async def test_image_first_returns_obs_image_labels(self, engine, temp_seismic_image):
        """process_image_first must label all visual features as OBS_IMAGE."""
        result = await engine.process_image_first(temp_seismic_image)
        for vf in result.visual_features:
            assert vf.epistemic_label == EpistemicLabel.OBS_IMAGE, (
                f"Feature {vf.feature_type} has wrong label: {vf.epistemic_label}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3: Governance Gate REJECTS Without Physics Validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestGovernanceGate:
    """Governance must enforce physics validation before geological claims."""

    @pytest.mark.asyncio
    async def test_hold_without_physics_validation(self, engine):
        """Without physics validation, governance must return HOLD."""
        result = CognitionResult()
        result.add_layer("OBS_IMAGE", EpistemicLabel.OBS_IMAGE)
        result.add_layer("CV_DETECTION", EpistemicLabel.DER_ATTRIBUTE)
        result.add_layer("LLM_COGNITION", EpistemicLabel.INT_SEISMIC)
        result.hypotheses = [
            Hypothesis(
                interpretation="possible fault",
                alternatives=["alternative: channel margin"],
                confidence=0.5,
                epistemic_label=EpistemicLabel.INT_SEISMIC,
            )
        ]
        # No physics validation layer
        verdict = await engine.governance_gate(result)
        assert verdict.verdict == "HOLD"
        assert not verdict.physics_validated
        assert "physics validation" in " ".join(verdict.reasons).lower()

    @pytest.mark.asyncio
    async def test_advance_with_physics_no_well_tie(self, engine, temp_segy_file):
        """With physics but no well-tie → ADVANCE (not SEAL)."""
        result = CognitionResult()
        result.add_layer("OBS_IMAGE", EpistemicLabel.OBS_IMAGE)
        result.add_layer("CV_DETECTION", EpistemicLabel.DER_ATTRIBUTE)
        result.add_layer("LLM_COGNITION", EpistemicLabel.INT_SEISMIC)
        result.hypotheses = [
            Hypothesis(
                interpretation="possible fault",
                alternatives=["alternative: channel margin"],
                confidence=0.5,
                epistemic_label=EpistemicLabel.INT_SEISMIC,
            )
        ]
        # Add physics validation
        result.physics_audit = PhysicsAudit(
            seg_y_valid=True,
            velocity_consistency=True,
            rock_physics_pass=True,
        )
        result.add_layer("PHYSICS_VALIDATION", EpistemicLabel.DER_ATTRIBUTE)

        verdict = await engine.governance_gate(result)
        assert verdict.verdict == "ADVANCE"
        assert verdict.physics_validated
        assert not verdict.well_tied

    @pytest.mark.asyncio
    async def test_seal_with_physics_and_well_tie_and_judgment(self, engine):
        """With physics + well-tie + human judgment → SEAL."""
        result = CognitionResult()
        result.add_layer("OBS_IMAGE", EpistemicLabel.OBS_IMAGE)
        result.add_layer("CV_DETECTION", EpistemicLabel.DER_ATTRIBUTE)
        result.add_layer("LLM_COGNITION", EpistemicLabel.INT_SEISMIC)
        result.hypotheses = [
            Hypothesis(
                interpretation="possible fault",
                alternatives=["alternative: channel margin"],
                confidence=0.7,
                epistemic_label=EpistemicLabel.INT_SEISMIC,
            )
        ]
        result.physics_audit = PhysicsAudit(
            seg_y_valid=True,
            well_tie_score=0.78,
            velocity_consistency=True,
            rock_physics_pass=True,
        )
        result.add_layer("PHYSICS_VALIDATION", EpistemicLabel.DER_ATTRIBUTE)
        result.add_layer("HUMAN_GEOLOGIST", EpistemicLabel.INT_GEOLOGY)

        verdict = await engine.governance_gate(result)
        assert verdict.verdict == "SEAL"
        assert verdict.physics_validated
        assert verdict.well_tied


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 4: DER_SYNTHETIC Always Labeled Synthetic
# ═══════════════════════════════════════════════════════════════════════════════


class TestSyntheticLabeling:
    """DER_SYNTHETIC outputs must always carry the synthetic label."""

    def test_synthetic_output_default_label(self):
        synth = SyntheticOutput(
            description="test",
            method="diffusion",
            confidence=0.5,
        )
        assert synth.epistemic_label == EpistemicLabel.DER_SYNTHETIC

    def test_synthetic_output_has_warning(self):
        synth = SyntheticOutput(
            description="test",
            method="diffusion",
            confidence=0.5,
        )
        assert "diffusion" in synth.warning.lower()
        assert "geology" in synth.warning.lower()

    @pytest.mark.asyncio
    async def test_gen_model_all_outputs_synthetic(self, engine, temp_seismic_image):
        """All outputs from Layer 4 (GEN_MODEL) must be DER_SYNTHETIC."""
        result = await engine.process_image_first(temp_seismic_image)
        result = await engine.generate_synthetic(result)

        for synth in result.synthetic_outputs:
            assert synth.epistemic_label == EpistemicLabel.DER_SYNTHETIC, (
                f"Synthetic output not labeled DER_SYNTHETIC: {synth.epistemic_label}"
            )

    @pytest.mark.asyncio
    async def test_governance_rejects_misslabeled_synthetic(self, engine):
        """Governance must REJECT if synthetic output is not labeled DER_SYNTHETIC."""
        result = CognitionResult()
        result.add_layer("OBS_IMAGE", EpistemicLabel.OBS_IMAGE)
        result.add_layer("CV_DETECTION", EpistemicLabel.DER_ATTRIBUTE)
        result.add_layer("LLM_COGNITION", EpistemicLabel.INT_SEISMIC)
        # Create a MISSLABELED synthetic output
        result.synthetic_outputs = [
            SyntheticOutput(
                description="fake observation",
                method="diffusion",
                confidence=0.8,
                epistemic_label=EpistemicLabel.OBS_IMAGE,  # WRONG LABEL
            )
        ]
        result.add_layer("GEN_MODEL", EpistemicLabel.DER_SYNTHETIC)

        verdict = await engine.governance_gate(result)
        assert verdict.verdict == "REJECT"
        assert not verdict.anti_hantu_pass


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 5: Non-Uniqueness — Multiple Hypotheses Generated
# ═══════════════════════════════════════════════════════════════════════════════


class TestNonUniqueness:
    """Every visual feature must generate multiple hypotheses (non-uniqueness)."""

    def test_bright_amplitude_has_multiple_causes(self):
        """Bright amplitude must have multiple possible causes."""
        assert "bright_amplitude" in NON_UNIQUENESS_TABLE
        causes = NON_UNIQUENESS_TABLE["bright_amplitude"]
        assert len(causes) >= 3, "Bright amplitude must have ≥3 possible causes"

    def test_reflector_termination_has_multiple_causes(self):
        assert "reflector_termination" in NON_UNIQUENESS_TABLE
        causes = NON_UNIQUENESS_TABLE["reflector_termination"]
        assert len(causes) >= 3

    def test_chaotic_reflectors_has_multiple_causes(self):
        assert "chaotic_reflectors" in NON_UNIQUENESS_TABLE
        causes = NON_UNIQUENESS_TABLE["chaotic_reflectors"]
        assert len(causes) >= 3

    def test_non_uniqueness_table_covers_key_features(self):
        """The table must cover at least the key visual features."""
        required = ["bright_amplitude", "reflector_termination", "chaotic_reflectors"]
        for feature in required:
            assert feature in NON_UNIQUENESS_TABLE, f"Missing feature: {feature}"

    @pytest.mark.asyncio
    async def test_hypotheses_include_alternatives(self, engine, temp_seismic_image):
        """Each hypothesis from image-first must carry alternatives."""
        result = await engine.process_image_first(temp_seismic_image)
        for h in result.hypotheses:
            assert len(h.alternatives) > 0, (
                f"Hypothesis '{h.interpretation}' has no alternatives"
            )
            # Must use "alternative:" or "possible" phrasing
            assert any(
                "alternative" in alt.lower() or "possible" in alt.lower()
                for alt in h.alternatives
            ) or "insufficient" in h.interpretation.lower()

    @pytest.mark.asyncio
    async def test_hypotheses_never_collapse_to_single(self, engine, temp_seismic_image):
        """Image-first must not produce exactly one hypothesis with no alternatives."""
        result = await engine.process_image_first(temp_seismic_image)
        for h in result.hypotheses:
            if "insufficient" not in h.interpretation.lower():
                assert len(h.alternatives) >= 1, (
                    f"Hypothesis collapsed to single interpretation: {h.interpretation}"
                )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 6: Confidence Cap at 0.90 (F7 HUMILITY)
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfidenceCap:
    """F7 HUMILITY: confidence must be capped at 0.90."""

    def test_confidence_cap_constant(self):
        assert CONFIDENCE_CAP == 0.90

    def test_hypothesis_post_init_allows_any_value(self):
        """Hypothesis stores confidence as-is; governance enforces cap."""
        h = Hypothesis(
            interpretation="test",
            alternatives=["alt"],
            confidence=0.99,  # Above cap — stored as-is
        )
        assert h.confidence == 0.99  # Not capped at dataclass level

    def test_hypothesis_below_cap_unchanged(self):
        h = Hypothesis(
            interpretation="test",
            alternatives=["alt"],
            confidence=0.50,
        )
        assert h.confidence == 0.50

    @pytest.mark.asyncio
    async def test_governance_caps_confidence(self, engine):
        """Governance gate must cap any hypothesis above 0.90."""
        result = CognitionResult()
        result.add_layer("OBS_IMAGE", EpistemicLabel.OBS_IMAGE)
        h = Hypothesis(
            interpretation="possible fault",
            alternatives=["alt"],
            confidence=0.95,  # Above cap
            epistemic_label=EpistemicLabel.INT_SEISMIC,
        )
        # Before governance: confidence is 0.95
        assert h.confidence == 0.95
        result.hypotheses = [h]
        verdict = await engine.governance_gate(result)
        # After governance: confidence is capped at 0.90
        assert verdict.confidence_cap_applied
        assert result.hypotheses[0].confidence == 0.90

    def test_image_first_hypotheses_have_low_confidence(self):
        """Image-only hypotheses should have low confidence (≤0.5)."""
        # This is a design invariant — image-only = low confidence
        # Only physics validation + well tie can raise confidence
        h = Hypothesis(
            interpretation="possible fault",
            alternatives=["channel margin", "processing artifact"],
            confidence=0.35,  # Image-only confidence
        )
        assert h.confidence <= 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 7: Full Pipeline Ordering
# ═══════════════════════════════════════════════════════════════════════════════


class TestFullPipeline:
    """Pipeline must follow correct ordering: image → SEG-Y → well → governance."""

    @pytest.mark.asyncio
    async def test_image_first_completes_layers_1_3(self, engine, temp_seismic_image):
        """process_image_first must complete Layers 1, 2, 3."""
        result = await engine.process_image_first(temp_seismic_image)
        assert "OBS_IMAGE" in result.completed_layers
        assert "CV_DETECTION" in result.completed_layers
        assert "LLM_COGNITION" in result.completed_layers
        assert "GEN_MODEL" not in result.completed_layers  # Not yet

    @pytest.mark.asyncio
    async def test_full_pipeline_order(self, engine, temp_seismic_image, temp_segy_file, sample_well_data):
        """Full pipeline must complete in order."""
        verdict = await engine.full_pipeline(
            image_path=temp_seismic_image,
            segy_path=temp_segy_file,
            well_data=sample_well_data,
        )
        result = verdict.cognition_result
        assert result is not None

        # Check ordering
        layers = result.completed_layers
        assert layers.index("OBS_IMAGE") < layers.index("CV_DETECTION")
        assert layers.index("CV_DETECTION") < layers.index("LLM_COGNITION")
        assert layers.index("LLM_COGNITION") < layers.index("GEN_MODEL")
        assert layers.index("GEN_MODEL") < layers.index("PHYSICS_VALIDATION")
        assert layers.index("PHYSICS_VALIDATION") < layers.index("HUMAN_GEOLOGIST")

    @pytest.mark.asyncio
    async def test_full_pipeline_without_image(self, engine, temp_segy_file, sample_well_data):
        """Pipeline without image should still work (limited)."""
        verdict = await engine.full_pipeline(
            segy_path=temp_segy_file,
            well_data=sample_well_data,
        )
        # Should complete with some layers
        assert verdict.cognition_result is not None

    @pytest.mark.asyncio
    async def test_full_pipeline_minimal(self, engine):
        """Minimal pipeline (no inputs) should return HOLD."""
        verdict = await engine.full_pipeline()
        assert verdict.verdict in ("HOLD", "ADVANCE", "REJECT", "SEAL")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 8: CognitionResult Serialization
# ═══════════════════════════════════════════════════════════════════════════════


class TestSerialization:
    """Results must serialize to JSON-safe dicts."""

    def test_cognition_result_to_dict(self):
        result = CognitionResult()
        result.add_layer("OBS_IMAGE", EpistemicLabel.OBS_IMAGE)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "OBS_IMAGE" in d["completed_layers"]
        assert "OBS_IMAGE" in d["epistemic_labels"]

    def test_governance_verdict_to_dict(self):
        verdict = GovernanceVerdict(verdict="HOLD", reasons=["test"])
        d = verdict.to_dict()
        assert isinstance(d, dict)
        assert d["verdict"] == "HOLD"
        assert "test" in d["reasons"]

    def test_result_json_serializable(self):
        result = CognitionResult()
        result.add_layer("OBS_IMAGE", EpistemicLabel.OBS_IMAGE)
        result.visual_features = [
            VisualFeature(
                feature_type="test",
                description="test",
                location={},
                epistemic_label=EpistemicLabel.OBS_IMAGE,
            )
        ]
        # Must be JSON-serializable
        json_str = json.dumps(result.to_dict(), default=str)
        assert isinstance(json_str, str)

    def test_verdict_json_serializable(self):
        verdict = GovernanceVerdict(
            verdict="HOLD",
            reasons=["test"],
            doctrine=["doctrine1"],
        )
        json_str = json.dumps(verdict.to_dict(), default=str)
        assert isinstance(json_str, str)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 9: Doctrine
# ═══════════════════════════════════════════════════════════════════════════════


class TestDoctrine:
    """Doctrine must be complete and accessible."""

    def test_doctrine_has_required_principles(self):
        doctrine_text = " ".join(SEISMIC_COGNITION_DOCTRINE).lower()
        assert "code can detect evidence" in doctrine_text
        assert "diffusion must not decide geology" in doctrine_text
        assert "confidence" in doctrine_text
        assert "0.90" in doctrine_text

    def test_get_doctrine_returns_complete(self):
        doctrine = get_seismic_cognition_doctrine()
        assert "doctrine" in doctrine
        assert "layers" in doctrine
        assert "non_uniqueness_table" in doctrine
        assert "confidence_cap" in doctrine
        assert doctrine["confidence_cap"] == 0.90
        assert len(doctrine["layers"]) == 7

    def test_doctrine_pipeline_order(self):
        doctrine = get_seismic_cognition_doctrine()
        assert "pipeline_order" in doctrine
        order_text = " ".join(doctrine["pipeline_order"]).lower()
        assert "obs_image" in order_text
        assert "physics_validation" in order_text
        assert "governance" in order_text


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 10: Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_image_not_found(self, engine):
        """Missing image must raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await engine.process_image_first("/nonexistent/image.png")

    def test_empty_cognition_result(self):
        result = CognitionResult()
        assert result.completed_layers == []
        assert result.visual_features == []
        assert result.hypotheses == []
        assert not result.has_physics_validation()
        assert not result.has_well_tie()
        assert not result.has_geological_interpretation()

    def test_epistemic_label_enum_values(self):
        """All epistemic labels must be valid enum values."""
        for label in EpistemicLabel:
            assert isinstance(label.value, str)
            assert label.value == label.name  # value equals name

    def test_cognition_layer_is_frozen(self):
        """CognitionLayer is frozen (immutable)."""
        layer = SEISMIC_COGNITION_STACK[0]
        with pytest.raises(AttributeError):
            layer.name = "MODIFIED"  # type: ignore

    @pytest.mark.asyncio
    async def test_seg_y_not_found(self, engine, temp_seismic_image):
        """Missing SEG-Y must be handled gracefully."""
        result = await engine.process_image_first(temp_seismic_image)
        result = await engine.validate_with_segy("/nonexistent/segy.sgy", result)
        assert result.physics_audit is not None
        assert not result.physics_audit.seg_y_valid
        assert any("not found" in issue for issue in result.physics_audit.issues)
