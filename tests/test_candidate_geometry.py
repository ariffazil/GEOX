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


def test_single_canonical_candidate_geometry_definition():
    """Verify that CandidateGeometry in seismic_onnx_adapter is identical to geox_core.schemas."""
    from geox_core.schemas.candidate_geometry import CandidateGeometry as CoreCandidateGeometry
    from geox_mcp.tools.seismic_onnx_adapter import CandidateGeometry as AdapterCandidateGeometry

    assert CoreCandidateGeometry is AdapterCandidateGeometry
    assert CoreCandidateGeometry.__module__ == "geox_core.schemas.candidate_geometry"


def test_no_import_shadowing():
    """Verify that importing CandidateGeometry from either path lands on the exact same class."""
    import sys

    # Reload check
    mod_core = sys.modules.get("geox_core.schemas.candidate_geometry")
    mod_adapter = sys.modules.get("geox_mcp.tools.seismic_onnx_adapter")

    assert getattr(mod_core, "CandidateGeometry") is getattr(mod_adapter, "CandidateGeometry")


def test_onnx_adapter_returns_canonical_candidate_geometry():
    """Verify that ClassicalBaselineAdapter proposes legacy bundle and migrates cleanly to canonical."""
    import numpy as np
    from geox_core.schemas.candidate_geometry import CandidateGeometry
    from geox_mcp.tools.seismic_onnx_adapter import (
        ClassicalBaselineAdapter,
        LegacyOnnxCandidateGeometry,
    )

    adapter = ClassicalBaselineAdapter()
    np.random.seed(42)
    fake_img = np.random.randn(30, 40).astype(np.float32)

    # 1. propose() returns LegacyOnnxCandidateGeometry
    legacy_bundle = adapter.propose(fake_img)
    assert isinstance(legacy_bundle, LegacyOnnxCandidateGeometry)
    d = legacy_bundle.to_dict()
    assert d["provenance"]["epistemic_label"] == "INT_SEISMIC"

    # 2. propose_canonical() returns list of canonical CandidateGeometry
    canonical_list = adapter.propose_canonical(fake_img)
    assert isinstance(canonical_list, list)
    for item in canonical_list:
        assert isinstance(item, CandidateGeometry)
        assert item.epistemic_status == "HYPOTHESIS"
        assert item.promotion_state == "GENERATED"


def test_legacy_payload_migration_or_rejection():
    """Verify that LegacyOnnxCandidateGeometry converts correctly to canonical and rejects corrupt points."""
    from geox_core.schemas.candidate_geometry import CandidateGeometry
    from geox_mcp.tools.seismic_onnx_adapter import LegacyOnnxCandidateGeometry

    legacy = LegacyOnnxCandidateGeometry(
        horizons=[
            {"id": "H_leg_1", "points": [[0.0, 50.0], [10.0, 55.0]]},
            {"id": "H_corrupt", "points": "invalid_points_format"},  # Should be skipped safely
        ],
        faults=[
            {"id": "F_leg_1", "points": [[5.0, 40.0], [5.0, 90.0]]},
        ],
        provenance={"source": "legacy_onnx_test_run"},
    )

    canonical_items = legacy.to_canonical(crs="EPSG:4326", domain="depth_m")
    assert len(canonical_items) == 2  # 1 valid horizon + 1 valid fault

    fault_item = next(x for x in canonical_items if x.geometry_type == "fault_segment")
    assert fault_item.candidate_id == "F_leg_1"
    assert fault_item.domain == "depth_m"
    assert fault_item.coordinate_reference_system == "EPSG:4326"
    assert fault_item.epistemic_status == "HYPOTHESIS"
    assert fault_item.promotion_state == "GENERATED"


def test_candidate_serialization_roundtrip():
    """Verify roundtrip conversion between CandidateGeometry dataclass and dictionary."""
    from geox_core.schemas.candidate_geometry import CandidateGeometry

    cand = CandidateGeometry(
        candidate_id="cand_rt_01",
        source_data_ids=("src_1", "src_2"),
        source_sha256s=("sha_1", "sha_2"),
        generator_name="geox_test",
        generator_version="v1.0",
        parameters_hash="param_123",
        geometry_type="closure_outline",
        coordinate_reference_system="EPSG:32650",
        domain="time_ms",
        coordinates=((1.0, 2.0), (3.0, 4.0), (1.0, 2.0)),
        epistemic_status="HYPOTHESIS",
        promotion_state="SCREENED",
        falsifier_results={"G2_TOPOLOGY": "PASS", "K_DIP": "INSUFFICIENT_INPUT"},
        rejection_reasons=(),
        missing_evidence=("K_DIP: missing checkshot",),
        contradictions=(),
    )

    payload = cand.to_dict()
    assert payload["candidate_id"] == "cand_rt_01"
    assert payload["source_data_ids"] == ["src_1", "src_2"]
    assert payload["falsifier_results"]["G2_TOPOLOGY"] == "PASS"

    # Reconstruct from dict
    cand_reconstructed = CandidateGeometry(
        candidate_id=payload["candidate_id"],
        source_data_ids=tuple(payload["source_data_ids"]),
        source_sha256s=tuple(payload["source_sha256s"]),
        generator_name=payload["generator_name"],
        generator_version=payload["generator_version"],
        parameters_hash=payload["parameters_hash"],
        geometry_type=payload["geometry_type"],
        coordinate_reference_system=payload["coordinate_reference_system"],
        domain=payload["domain"],
        coordinates=tuple(tuple(p) for p in payload["coordinates"]),
        epistemic_status=payload["epistemic_status"],
        promotion_state=payload["promotion_state"],
        falsifier_results=dict(payload["falsifier_results"]),
        rejection_reasons=tuple(payload["rejection_reasons"]),
        missing_evidence=tuple(payload["missing_evidence"]),
        contradictions=tuple(payload["contradictions"]),
    )

    assert cand == cand_reconstructed

