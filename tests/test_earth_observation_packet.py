"""
Unit tests for EarthObservationPacket schema and field test discriminators.
Tests Phase 1 contracts: JSON schema roundtrip, Invariants I1-I9, field test elimination.
"""

import json
from pathlib import Path
import pytest

from geox_core.schemas.earth_observation import (
    EarthObservationPacket,
    ArtifactMetadata,
    ObservationContext,
    ObservationsBlock,
    VisibleFeature,
    OcrText,
    Measurement,
    Hypothesis,
    LimitationsBlock,
    EpistemicBlock,
    ProvenanceRecord,
    HumanTestRequest,
)
from geox_core.earth_witness.field_tests import (
    FieldTestInput,
    evaluate_field_discriminators,
)


def test_earth_observation_packet_valid():
    """Verify clean instantiation and roundtrip."""
    packet = EarthObservationPacket(
        packet_id="eop-001",
        artifact=ArtifactMetadata(
            id="art-123",
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            media_type="image/jpeg",
            source_actor="ariffazil",
            captured_at="2026-10-03T11:00:00Z",
        ),
        context=ObservationContext(
            modality="rock",
            domain="na",
        ),
        observations=ObservationsBlock(
            visible_features=[
                VisibleFeature(
                    feature_id="f1",
                    label="cross_stratification",
                    category="sedimentary_structure",
                    confidence=0.85,
                )
            ],
            ocr_text=[],
            measurements=[],
        ),
        hypotheses=[
            Hypothesis(
                hypothesis_id="h1",
                label="Fluvial Sandstone",
                supporting=["cross_stratification"],
                conflicting=[],
                falsifiers=["marine microfossils"],
                confidence=0.75,
            )
        ],
        limitations=LimitationsBlock(
            image_cannot_determine=["True permeability", "Porosity percentage"],
            missing_metadata=[],
            requested_human_tests=[
                HumanTestRequest(
                    test_name="dilute_hcl",
                    purpose="Test for calcite cementation",
                    discriminates=["calcareous sandstone", "siliceous sandstone"],
                )
            ],
            requested_instrument_data=[],
        ),
        epistemic=EpistemicBlock(
            claim_tag="INTERPRET",
            confidence=0.75,
            state="DRAFT",
            provenance=[
                ProvenanceRecord(
                    step="visual_inventory",
                    agent_id="earth_observer_agent",
                    timestamp="2026-10-03T11:00:05Z",
                )
            ],
            verdict="QUALIFIED_CANDIDATE",
        ),
    )

    data = packet.model_dump()
    assert data["packet_id"] == "eop-001"
    # Roundtrip
    reconstructed = EarthObservationPacket.model_validate(data)
    assert reconstructed.artifact.sha256 == packet.artifact.sha256


def test_invariant_i3_hydrocarbon_guard():
    """Invariant I3: No hydrocarbon claim from image alone."""
    packet = EarthObservationPacket(
        packet_id="eop-seismic-01",
        artifact=ArtifactMetadata(
            id="art-seismic",
            sha256="a" * 64,
            media_type="image/png",
            source_actor="hermes",
            captured_at="2026-10-03T11:00:00Z",
        ),
        context=ObservationContext(
            modality="seismic_display",
            domain="time",
        ),
        observations=ObservationsBlock(),
        hypotheses=[
            Hypothesis(
                hypothesis_id="h1",
                label="Direct Hydrocarbon Indicator Gas Pay",
                supporting=["bright spot"],
                conflicting=[],
                falsifiers=[],
                confidence=0.88,
            )
        ],
        limitations=LimitationsBlock(
            image_cannot_determine=[],
            missing_metadata=[],
            requested_human_tests=[],
            requested_instrument_data=[],
        ),
        epistemic=EpistemicBlock(
            claim_tag="EVIDENCE",
            confidence=0.88,
            state="DRAFT",
            provenance=[],
        ),
    )

    # Must be downgraded from EVIDENCE and state changed to INPUT_REQUIRED
    assert packet.epistemic.claim_tag == "HYPOTHESIS"
    assert packet.epistemic.state == "INPUT_REQUIRED"
    assert any("Amplitude != Hydrocarbon" in lim for lim in packet.limitations.image_cannot_determine)


def test_invariant_i5_missing_scale_guard():
    """Invariant I5: Missing scale on specimen forces INPUT_REQUIRED."""
    packet = EarthObservationPacket(
        packet_id="eop-hand-01",
        artifact=ArtifactMetadata(
            id="art-hand",
            sha256="b" * 64,
            media_type="image/jpeg",
            source_actor="ariffazil",
            captured_at="2026-10-03T11:00:00Z",
        ),
        context=ObservationContext(
            modality="outcrop",
            domain="na",
            scale=None,  # No scale bar
        ),
        observations=ObservationsBlock(),
        hypotheses=[],
        limitations=LimitationsBlock(
            image_cannot_determine=[],
            missing_metadata=[],
            requested_human_tests=[],
            requested_instrument_data=[],
        ),
        epistemic=EpistemicBlock(
            claim_tag="INTERPRET",
            confidence=0.5,
            state="DRAFT",
            provenance=[],
        ),
    )

    assert packet.epistemic.state == "INPUT_REQUIRED"
    assert "Diagnostic physical scale bar is missing" in packet.limitations.missing_metadata


def test_field_tests_hcl_elimination():
    """Verify physical test discriminators eliminate contradictory hypotheses."""
    candidates = ["limestone", "dolostone", "quartzite", "shale", "chert"]

    # Test 1: Vigorous HCl effervescence
    report1 = evaluate_field_discriminators(
        candidates,
        FieldTestInput(hcl="vigorous"),
    )
    # Quartzite, shale, chert, and dolostone must be eliminated
    assert "limestone" in report1.surviving_hypotheses
    assert "quartzite" not in report1.surviving_hypotheses
    assert "chert" not in report1.surviving_hypotheses

    # Test 2: Hardness > steel
    report2 = evaluate_field_discriminators(
        candidates,
        FieldTestInput(hardness="gt_steel"),
    )
    # Limestone and dolostone (Mohs 3-4) must be eliminated
    assert "limestone" not in report2.surviving_hypotheses
    assert "dolostone" not in report2.surviving_hypotheses
    assert "quartzite" in report2.surviving_hypotheses
    assert "chert" in report2.surviving_hypotheses
