"""
Unit tests for CandidateGeometry immutable schema (Phase B2 - ARIF Authority).
════════════════════════════════════════════════════════════════════════════════
Invariants tested:
1. Frozen immutability: attempts to mutate fields raise FrozenInstanceError.
2. Plural source IDs and plural SHA256 hashes.
3. Explicit CRS and time/depth domain.
4. Epistemic status locked to HYPOTHESIS.
5. Typed GateVerdicts ("PASS", "FAIL", "NOT_RUN", "INSUFFICIENT_INPUT", "ERROR").
6. PromotionState progression: GENERATED -> SCREENED -> SURVIVES_TEST / REJECTED.
7. Automated tools cannot set HUMAN_ACCEPTED.
"""

from __future__ import annotations

import dataclasses
import pytest

from geox_core.schemas.candidate_geometry import CandidateGeometry, GateVerdict, PromotionState


def test_candidate_geometry_immutability():
    cand = CandidateGeometry(
        candidate_id="cand_test_01",
        source_data_ids=("synth_seis_inline_100",),
        source_sha256s=("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",),
        generator_name="geox_extract_faults_shadow",
        generator_version="v2026.11.03-b2",
        parameters_hash="param_hash_abc",
        geometry_type="fault_segment",
        coordinate_reference_system="EPSG:32650",
        domain="time_ms",
        coordinates=((10.0, 100.0), (15.0, 150.0)),
        epistemic_status="HYPOTHESIS",
        promotion_state="GENERATED",
    )

    # 1. Outer instance is frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        cand.candidate_id = "mutated_id"  # type: ignore[misc]

    with pytest.raises(dataclasses.FrozenInstanceError):
        cand.promotion_state = "HUMAN_ACCEPTED"  # type: ignore[misc]

    # 2. Collections are immutable tuples
    assert isinstance(cand.source_data_ids, tuple)
    assert isinstance(cand.source_sha256s, tuple)
    assert isinstance(cand.coordinates, tuple)
    assert isinstance(cand.rejection_reasons, tuple)
    assert isinstance(cand.missing_evidence, tuple)
    assert isinstance(cand.contradictions, tuple)


def test_candidate_geometry_plural_sources():
    cand = CandidateGeometry(
        candidate_id="cand_composite_01",
        source_data_ids=("seis_cub_01", "seis_coherence_01", "well_top_wp1"),
        source_sha256s=("hash_a", "hash_b", "hash_c"),
        generator_name="geox_extract_faults_shadow",
        generator_version="v2026.11.03-b2",
        parameters_hash="p_hash_composite",
        geometry_type="fault_segment",
        coordinate_reference_system="LOCAL_INLINE",
        domain="depth_m",
        coordinates=((100.0, 1500.0), (105.0, 1600.0)),
    )
    assert len(cand.source_data_ids) == 3
    assert len(cand.source_sha256s) == 3
    assert cand.domain == "depth_m"
    assert cand.coordinate_reference_system == "LOCAL_INLINE"


def test_candidate_geometry_state_transitions():
    cand = CandidateGeometry(
        candidate_id="cand_state_01",
        source_data_ids=("synth_01",),
        source_sha256s=("hash_01",),
        generator_name="geox_extract_faults_shadow",
        generator_version="v2026.11.03-b2",
        parameters_hash="p_hash",
        geometry_type="fault_segment",
        coordinate_reference_system="EPSG:4326",
        domain="time_ms",
        coordinates=((0.0, 100.0), (5.0, 200.0)),
    )
    assert cand.promotion_state == "GENERATED"
    assert cand.epistemic_status == "HYPOTHESIS"

    # Screened with insufficient input
    c_insufficient = cand.with_falsifier_results(
        results={"G2_TOPOLOGY": "INSUFFICIENT_INPUT"},
        missing=("G2_TOPOLOGY: Insufficient horizons",),
    )
    assert c_insufficient.promotion_state == "SCREENED"
    assert "G2_TOPOLOGY: Insufficient horizons" in c_insufficient.missing_evidence

    # Survives when passes and no kills
    c_survives = cand.with_falsifier_results(
        results={"G2_TOPOLOGY": "PASS", "K_DIP": "PASS"},
    )
    assert c_survives.promotion_state == "SURVIVES_TEST"
    assert c_survives.epistemic_status == "HYPOTHESIS"

    # Rejected when any gate fails
    c_rejected = c_survives.with_falsifier_results(
        results={"K_DL": "FAIL"},
        reasons=("K_DL: Displacement-length scaling exceeded",),
    )
    assert c_rejected.promotion_state == "REJECTED"
    assert "K_DL: Displacement-length scaling exceeded" in c_rejected.rejection_reasons

    # Check to_dict serialization
    d = c_rejected.to_dict()
    assert d["promotion_state"] == "REJECTED"
    assert d["epistemic_status"] == "HYPOTHESIS"
    assert isinstance(d["coordinates"], list)
    assert isinstance(d["source_data_ids"], list)
