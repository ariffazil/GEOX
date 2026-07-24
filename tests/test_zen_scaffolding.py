"""
🌊 GEOX Zen Scaffolding Tests (PR-A1 through PR-A4)

Coverage for the Phase A scaffolding — classical baseline, ONNX adapter
contract, human correction hook, artifact ingest.
"""

from __future__ import annotations

import numpy as np
import pytest


# ──────────────────────────────────────────────────────────────────────
# PR-A2 — Classical image baseline
# ──────────────────────────────────────────────────────────────────────


def test_structure_tensor_returns_dip_and_coherence():
    from geox_mcp.tools.seismic_classical import structure_tensor

    np.random.seed(0)
    img = np.random.randn(40, 60).astype(np.float32)
    img[20, :] = 1.0
    out = structure_tensor(img, sigma=1.0)
    assert out["dip_rad"].shape == img.shape
    assert out["coherence"].shape == img.shape
    assert (out["coherence"] >= 0).all() and (out["coherence"] <= 1).all()


def test_semblance_coherence_in_unit_range():
    from geox_mcp.tools.seismic_classical import semblance_coherence

    np.random.seed(0)
    img = np.random.randn(40, 60).astype(np.float32)
    out = semblance_coherence(img, window=5)
    assert (out >= 0).all() and (out <= 1).all()


def test_dp_horizon_tracker_walks_columns():
    from geox_mcp.tools.seismic_classical import dp_horizon_tracker

    np.random.seed(0)
    img = np.random.randn(40, 60).astype(np.float32)
    img[20, :] = 1.0
    out = dp_horizon_tracker([(0, 20)], img, dip_penalty=0.5)
    assert out["n_traces_walked"] == img.shape[1]
    assert len(out["points"]) == img.shape[1]


def test_rgt_estimation_monotonic_in_x():
    from geox_mcp.tools.seismic_classical import rgt_estimation

    np.random.seed(0)
    img = np.random.randn(40, 60).astype(np.float32)
    out = rgt_estimation(img, sigma=2.0)
    assert (out["rgt"][:, 1:] >= out["rgt"][:, :-1]).all()


def test_classical_baseline_returns_candidate_geometry():
    from geox_mcp.tools.seismic_classical import classical_baseline

    np.random.seed(0)
    img = np.random.randn(60, 80).astype(np.float32)
    img[20:25, :] += 1.0
    out = classical_baseline(img, n_horizon_levels=3)
    assert out["local_verdict"] == "QUALIFIED_CANDIDATE"
    assert out["seal_authority"] == "arifOS_only"
    assert out["epistemic_label"] == "INT_SEISMIC"
    assert out["artifact_sha256"].startswith("sha256:")


def test_artifact_sha256_stable():
    from geox_mcp.tools.seismic_classical import artifact_sha256

    a = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    assert artifact_sha256(a) == artifact_sha256(a)


# ──────────────────────────────────────────────────────────────────────
# PR-A3 — ONNX adapter contract
# ──────────────────────────────────────────────────────────────────────


def test_onnx_manifest_rejects_noncommercial_license():
    from geox_mcp.tools.seismic_onnx_adapter import OnnxModelAdapter, ModelManifest

    for bad_license in ("CC-BY-NC-4.0", "Research-only", "GPL-3.0"):
        bad = ModelManifest(model_id="bad", revision="v1", license=bad_license)
        with pytest.raises(ValueError):
            OnnxModelAdapter(manifest=bad)


def test_onnx_manifest_accepts_apache():
    from geox_mcp.tools.seismic_onnx_adapter import ModelManifest, OnnxModelAdapter

    m = ModelManifest(model_id="ok", revision="v1", license="Apache-2.0")
    a = OnnxModelAdapter(manifest=m)
    assert a.manifest.license == "Apache-2.0"


def test_onnx_adapter_refuses_to_seal():
    from geox_mcp.tools.seismic_onnx_adapter import ClassicalBaselineAdapter

    a = ClassicalBaselineAdapter()
    refusal = a.refuse_to_seal()
    assert "final_verdict" in refusal["refuses"]
    assert "autonomous_structure_acceptance" in refusal["refuses"]
    assert "capital_forecast" in refusal["refuses"]
    assert len(refusal["promotion_required_benchmarks"]) >= 5


def test_classical_baseline_adapter_proposes_int_seismic():
    from geox_mcp.tools.seismic_onnx_adapter import ClassicalBaselineAdapter

    a = ClassicalBaselineAdapter()
    np.random.seed(0)
    img = np.random.randn(30, 40).astype(np.float32)
    cand = a.propose(img)
    d = cand.to_dict()
    assert d["provenance"]["epistemic_label"] == "INT_SEISMIC"
    assert d["provenance"]["seal_authority"] == "arifOS_only"


# ──────────────────────────────────────────────────────────────────────
# PR-A4 — Human correction hook
# ──────────────────────────────────────────────────────────────────────


def test_add_seeds_appends_and_returns_receipt():
    from geox_mcp.tools.seismic_corrections import add_seeds

    out = add_seeds({}, horizon_seeds=[(10, 20)], fault_seeds=[(30, 40)])
    assert "receipt" in out
    assert out["receipt"]["correction"] == "add_seeds"
    assert out["receipt"]["n_horizon_seeds"] == 1
    assert out["receipt"]["n_fault_seeds"] == 1
    assert "receipt_hash" in out["receipt"]
    assert any(h.get("horizon_id", "").startswith("H-seed-") for h in out["framework"]["horizons"])
    assert any(f.get("fault_id", "").startswith("F-seed-") for f in out["framework"]["faults"])


def test_remove_segment_filters_by_type():
    from geox_mcp.tools.seismic_corrections import remove_segment

    fw = {"horizons": [{"horizon_id": "H1"}, {"horizon_id": "H2"}]}
    out = remove_segment(fw, target_type="horizon", target_id="H1")
    assert len(out["framework"]["horizons"]) == 1
    assert out["framework"]["horizons"][0]["horizon_id"] == "H2"


def test_join_faults_links_two_into_one():
    from geox_mcp.tools.seismic_corrections import join_faults

    fw = {"faults": [{"fault_id": "F1"}, {"fault_id": "F2"}]}
    out = join_faults(fw, fault_ids=["F1", "F2"])
    assert len(out["framework"]["faults"]) == 1
    assert "F2" in out["framework"]["faults"][0].get("merged_from", [])


def test_split_fault_dups_with_ab_suffix():
    from geox_mcp.tools.seismic_corrections import split_fault

    fw = {"faults": [{"fault_id": "F1"}]}
    out = split_fault(fw, fault_id="F1", at_xy=(100.0, 200.0))
    ids = [f["fault_id"] for f in out["framework"]["faults"]]
    assert "F1-a" in ids
    assert "F1-b" in ids


def test_mark_unconformity_sets_relation():
    from geox_mcp.tools.seismic_corrections import mark_unconformity

    fw = {"horizons": [{"horizon_id": "H1"}]}
    out = mark_unconformity(fw, horizon_id="H1", surface_type="erosional")
    h = out["framework"]["horizons"][0]
    assert h["relations"]["surface_type"] == "erosional"
    assert h["relations"]["truncates_below"] is True


def test_select_alternative_records_choice():
    from geox_mcp.tools.seismic_corrections import select_alternative

    fw = {"horizons": [{"horizon_id": "H1"}]}
    out = select_alternative(fw, horizon_id="H1", alternative_id="alt-A")
    assert out["framework"]["horizons"][0]["selected_alternative"] == "alt-A"


def test_freeze_accepted_geometry_marks_eligibility():
    from geox_mcp.tools.seismic_corrections import freeze_accepted_geometry

    out = freeze_accepted_geometry({"foo": "bar"})
    assert out["framework"]["provenance"]["seal_eligible"] is True
    assert out["framework"]["provenance"]["accepted_by"] == "human_interpreter"
    assert "frozen_at_iso" in out["framework"]["provenance"]


def test_rerun_gates_calls_matrix():
    from geox_mcp.tools.seismic_corrections import rerun_gates

    out = rerun_gates(
        {
            "faults": [
                {"fault_id": "F1", "regime_prior": "normal", "dip_deg_image": 60.0, "dip_calibrated": True}
            ]
        }
    )
    assert "gate_matrix" in out
    assert "combined_verdict" in out["receipt"]


# ──────────────────────────────────────────────────────────────────────
# PR-A1 — Artifact ingest
# ──────────────────────────────────────────────────────────────────────


def test_artifact_ingest_emits_hash_and_chain():
    from geox_mcp.tools.artifact_ingest import ingest_artifact

    art = ingest_artifact(
        "/root/GEOX/pyproject.toml",
        artifact_type="framework_json",
        note="zen scaffolding test",
    )
    assert art["sha256"].startswith("sha256:")
    assert art["artifact_hash_chain"].startswith("sha256:")
    assert art["size_bytes"] > 0
    assert art["artifact_type"] == "framework_json"


def test_artifact_ingest_handles_missing_file():
    from geox_mcp.tools.artifact_ingest import ingest_artifact

    art = ingest_artifact("/does/not/exist.png", artifact_type="section_image")
    assert art["sha256"] == "sha256:unresolved"
    assert art["size_bytes"] == 0


def test_calibration_state_full():
    from geox_mcp.tools.artifact_ingest import validate_calibration_state

    full = validate_calibration_state(
        {
            "x_axis": {"type": "trace"},
            "vertical_axis": {"type": "time_ms"},
            "vertical_exaggeration": 1.0,
            "polarity": "SEG_NORMAL",
            "phase_degrees": 0.0,
        }
    )
    assert full["calibrated"] is True
    assert full["missing"] == []


def test_calibration_state_partial_missing():
    from geox_mcp.tools.artifact_ingest import validate_calibration_state

    partial = validate_calibration_state({"vertical_exaggeration": 2.0})
    assert partial["calibrated"] is False
    assert "polarity" in partial["missing"]
    assert "phase_degrees" in partial["missing"]


def test_calibration_state_empty():
    from geox_mcp.tools.artifact_ingest import validate_calibration_state

    empty = validate_calibration_state(None)
    assert empty["calibrated"] is False
    assert empty["missing"] == ["all"]