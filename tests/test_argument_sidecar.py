"""
Test: GEOX Argument Sidecar — Every Map Must Be an Argument
═══════════════════════════════════════════════════════════════════════════════

Tests the governing law:
  No GEOX map may be exported unless every interpreted layer has
  at least one claim, one evidence reference, one uncertainty band,
  and one rival interpretation.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import pytest

from contracts.schemas.argument_sidecar import (
    ArgumentSidecar,
    ChallengeType,
    GeologicalClaim,
    ReviewState,
    RivalInterpretation,
    TruthClass,
    UncertaintyBand,
    build_argument_sidecar,
    validate_argument_for_export,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _sabah_structural_claims() -> list[dict]:
    """Sabah Basin structural interpretation claims."""
    return [
        {
            "claim_text": "The mapped closure is primarily fault-controlled by NW-SE trending thrust faults.",
            "truth_class": "INTERPRETATION",
            "layer_id": "faults.interpreted.main",
            "evidence_refs": [
                "seismic:SABAH-3D-2024:inline-1250",
                "well:SN-1:tops",
                "fault_polygon:fp-001",
            ],
            "epistemic_label": "INT",
            "confidence": 0.65,
            "falsification_test": "Depth conversion sensitivity analysis; if closure vanishes with alternative velocity model, the claim fails.",
        },
        {
            "claim_text": "Stratigraphic pinchout of Kudat Fm sandstones provides the primary reservoir seal.",
            "truth_class": "INTERPRETATION",
            "layer_id": "stratigraphy.kudat_fm",
            "evidence_refs": [
                "well:SN-1:core_description",
                "seismic:SABAH-3D-2024:amplitude_extraction",
            ],
            "epistemic_label": "INT",
            "confidence": 0.55,
            "falsification_test": "Facies model from additional well control; if sandstone extends beyond mapped pinchout, the claim fails.",
        },
    ]


def _sabah_rival_claims() -> list[dict]:
    """Rival interpretations for Sabah Basin structure."""
    return [
        {
            "claim_text": "Closure may be velocity pull-up rather than genuine structural relief.",
            "challenge_type": "geophysical_artifact",
            "evidence_needed": [
                "velocity_model_qc",
                "depth_conversion_sensitivity",
                "well_tie_quality_check",
            ],
            "probability": 0.25,
            "status": "unresolved",
        },
        {
            "claim_text": "Feature may be a stratigraphic pinchout rather than fault-controlled closure.",
            "challenge_type": "stratigraphic_alternative",
            "evidence_needed": [
                "facies_model_from_well_control",
                "amplitude_extraction_wider_area",
                "analogue_field_comparison",
            ],
            "probability": 0.30,
            "status": "unresolved",
        },
        {
            "claim_text": "Charge timing may be synchronous with trap formation, making preservation uncertain.",
            "challenge_type": "charge_timing",
            "evidence_needed": [
                "burial_history_model",
                "maturity_vro_tmax_data",
                "migration_pathway_analysis",
            ],
            "probability": 0.20,
            "status": "unresolved",
        },
    ]


def _sabah_uncertainty() -> dict:
    """Uncertainty band for Sabah Basin interpretation."""
    return {
        "p10": "Low closure confidence — velocity model uncertain, sparse well control",
        "p50": "Moderate closure confidence — seismic geometry supports structure but depth conversion carries risk",
        "p90": "High closure confidence if velocity model validated by additional well tie",
        "dominant_source": "model",
        "major_unknowns": [
            "Velocity model below Kudat Fm",
            "Fault seal capacity",
            "Charge timing relative to trap formation",
        ],
        "blocks_export": False,
    }


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestGeologicalClaim:
    """Test claim construction and validation."""

    def test_claim_has_required_fields(self):
        """Claim has all required fields."""
        claim = GeologicalClaim(
            claim_text="The closure is fault-controlled.",
            truth_class=TruthClass.INTERPRETATION,
            evidence_refs=["seismic:001", "well:SN-1"],
            confidence=0.65,
        )
        assert claim.claim_id.startswith("claim-")
        assert claim.truth_class == TruthClass.INTERPRETATION
        assert len(claim.evidence_refs) == 2
        assert claim.confidence == 0.65

    def test_claim_confidence_capped_at_090(self):
        """F7 HUMILITY: confidence cannot exceed 0.90."""
        # Pydantic will reject values > 0.90 due to le=0.90
        with pytest.raises(Exception):
            GeologicalClaim(
                claim_text="Test claim",
                confidence=0.95,
            )


class TestRivalInterpretation:
    """Test rival construction."""

    def test_rival_has_required_fields(self):
        """Rival has all required fields."""
        rival = RivalInterpretation(
            claim_text="Closure may be velocity artifact.",
            challenge_type=ChallengeType.GEOPHYSICAL_ARTIFACT,
            evidence_needed=["velocity_model_qc"],
            probability=0.25,
        )
        assert rival.rival_id.startswith("rival-")
        assert rival.challenge_type == ChallengeType.GEOPHYSICAL_ARTIFACT
        assert rival.status == "unresolved"


class TestArgumentSidecar:
    """Test full argument sidecar construction."""

    def test_build_valid_sabah_argument(self):
        """Sabah Basin argument passes all export gates."""
        sidecar = build_argument_sidecar(
            artifact_id="sab-basin-structural-scene-v1",
            primary_claims=_sabah_structural_claims(),
            rival_claims=_sabah_rival_claims(),
            uncertainty=_sabah_uncertainty(),
            scene_plan_id="scene-structural-sabah-v5",
        )

        assert len(sidecar.primary_claims) == 2
        assert len(sidecar.rival_claims) == 3
        assert sidecar.uncertainty.dominant_source == "model"
        assert sidecar.export_permitted is True
        assert sidecar.export_block_reason == ""
        assert sidecar.review_state == ReviewState.DRAFT

    def test_no_claims_blocks_export(self):
        """No claims = export blocked."""
        sidecar = ArgumentSidecar(
            artifact_id="test-001",
            primary_claims=[],
            rival_claims=[
                RivalInterpretation(
                    claim_text="Test rival",
                    challenge_type=ChallengeType.DATA_QUALITY,
                )
            ],
        )
        permitted, blocks = validate_argument_for_export(sidecar)
        assert permitted is False
        assert any("No primary claims" in b for b in blocks)

    def test_no_rivals_blocks_export(self):
        """No rivals = export blocked."""
        sidecar = ArgumentSidecar(
            artifact_id="test-002",
            primary_claims=[GeologicalClaim(claim_text="Test claim")],
            rival_claims=[],
        )
        permitted, blocks = validate_argument_for_export(sidecar)
        assert permitted is False
        assert any("No rival interpretations" in b for b in blocks)

    def test_claim_without_evidence_blocks_export(self):
        """Claim without evidence refs = export blocked."""
        sidecar = ArgumentSidecar(
            artifact_id="test-003",
            primary_claims=[
                GeologicalClaim(
                    claim_text="Test claim with no evidence",
                    evidence_refs=[],
                )
            ],
            rival_claims=[
                RivalInterpretation(
                    claim_text="Test rival",
                    challenge_type=ChallengeType.DATA_QUALITY,
                )
            ],
        )
        permitted, blocks = validate_argument_for_export(sidecar)
        assert permitted is False
        assert any("no evidence refs" in b for b in blocks)

    def test_uncertainty_blocks_export(self):
        """Uncertainty.blocks_export = True blocks export."""
        sidecar = ArgumentSidecar(
            artifact_id="test-004",
            primary_claims=[
                GeologicalClaim(
                    claim_text="Test claim",
                    evidence_refs=["evidence:001"],
                )
            ],
            rival_claims=[
                RivalInterpretation(
                    claim_text="Test rival",
                    challenge_type=ChallengeType.DATA_QUALITY,
                )
            ],
            uncertainty=UncertaintyBand(
                p10="Very uncertain",
                p50="Still uncertain",
                blocks_export=True,
            ),
        )
        permitted, blocks = validate_argument_for_export(sidecar)
        assert permitted is False
        assert any("Uncertainty explicitly blocks" in b for b in blocks)

    def test_void_review_state_blocks_export(self):
        """VOID review state = export blocked."""
        sidecar = ArgumentSidecar(
            artifact_id="test-005",
            primary_claims=[
                GeologicalClaim(
                    claim_text="Test claim",
                    evidence_refs=["evidence:001"],
                )
            ],
            rival_claims=[
                RivalInterpretation(
                    claim_text="Test rival",
                    challenge_type=ChallengeType.DATA_QUALITY,
                )
            ],
            uncertainty=UncertaintyBand(p10="Low", p50="Mid"),
            review_state=ReviewState.VOID,
        )
        permitted, blocks = validate_argument_for_export(sidecar)
        assert permitted is False
        assert any("VOID" in b for b in blocks)


class TestArgumentBuilder:
    """Test the build_argument_sidecar helper."""

    def test_builder_validates_claims_required(self):
        """Builder rejects empty claims."""
        with pytest.raises(ValueError, match="At least one primary claim"):
            build_argument_sidecar(
                artifact_id="test",
                primary_claims=[],
                rival_claims=[{"claim_text": "rival", "challenge_type": "data_quality"}],
            )

    def test_builder_validates_rivals_required(self):
        """Builder rejects empty rivals."""
        with pytest.raises(ValueError, match="At least one rival"):
            build_argument_sidecar(
                artifact_id="test",
                primary_claims=[{"claim_text": "claim"}],
                rival_claims=[],
            )

    def test_builder_auto_validates_export(self):
        """Builder auto-validates export permission."""
        sidecar = build_argument_sidecar(
            artifact_id="test-auto",
            primary_claims=[
                {
                    "claim_text": "Test claim",
                    "evidence_refs": ["evidence:001"],
                }
            ],
            rival_claims=[
                {
                    "claim_text": "Test rival",
                    "challenge_type": "data_quality",
                }
            ],
            uncertainty={"p10": "Low", "p50": "Mid"},
        )
        assert sidecar.export_permitted is True

    def test_sidecar_serialization_roundtrip(self):
        """Sidecar survives JSON serialization."""
        sidecar = build_argument_sidecar(
            artifact_id="test-roundtrip",
            primary_claims=[
                {
                    "claim_text": "Serialization test claim",
                    "evidence_refs": ["evidence:001"],
                    "truth_class": "INTERPRETATION",
                }
            ],
            rival_claims=[
                {
                    "claim_text": "Serialization test rival",
                    "challenge_type": "geophysical_artifact",
                }
            ],
        )
        json_str = sidecar.model_dump_json()
        sidecar2 = ArgumentSidecar.model_validate_json(json_str)
        assert sidecar2.artifact_id == sidecar.artifact_id
        assert len(sidecar2.primary_claims) == 1
        assert len(sidecar2.rival_claims) == 1
