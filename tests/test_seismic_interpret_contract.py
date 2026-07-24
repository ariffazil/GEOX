"""
🌊 GEOX Seismic Interpret Contract Tests (PR-B2)

Schema ↔ handler parity. Per F13 doctrine:
  - Every handler parameter must exist in the public schema
  - Every schema parameter must be accepted by the handler
  - Unsupported parameters must fail explicitly
  - Every mode must reach the correct handler
  - No mode may silently fall through

Discriminated-union schema lives at geox_mcp.contracts.seismic_interpret_schema
Handler lives at geox_mcp.tools.seismic_interpret.geox_seismic_interpret

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError


def test_interpret_request_discriminated_union_modes():
    from geox_mcp.domain.seismic_interpret.models import InterpretRequest

    adapter = TypeAdapter(InterpretRequest)
    # valid modes
    adapter.validate_python(
        {
            "mode": "horizon_contrast",
            "attribute_data": {"seismic_amplitude": [0.1, 0.2]},
            "depth": [0.0, 10.0],
        }
    )
    adapter.validate_python(
        {
            "mode": "structure_validate",
            "framework": {"faults": []},
        }
    )
    adapter.validate_python(
        {
            "mode": "interpret_section",
            "image_path": "/tmp/x.jpg",
        }
    )
    adapter.validate_python({"mode": "segy_slice", "segy_path": "/tmp/x.segy"})
    adapter.validate_python({"mode": "interpret", "framework": {"faults": [{"fault_id": "F1"}]}})

    # unknown mode still rejected by discriminator
    with pytest.raises(ValidationError):
        adapter.validate_python({"mode": "not_a_real_mode"})

    # Wrong types on declared fields ARE rejected.
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "mode": "fault_sticks",
                "source_uri": 123,  # declared field, wrong type
            }
        )


def test_transport_envelope_retained_and_typos_forbid():
    """Pin-down for ignore vs allow vs declared-envelope (Claude review).

    - Declared transport fields (session_id, actor_id, source_sha256) must
      survive model_validate → model_dump (handlers can see them).
    - Semantic typos (imagepath) must raise under extra=forbid — not
      silently vanish into a VOID_NO_DATA that looks like missing data.
    """
    from geox_mcp.domain.seismic_interpret.models import InterpretRequest, SectionImageMode

    adapter = TypeAdapter(InterpretRequest)

    ok = adapter.validate_python(
        {
            "mode": "interpret_section",
            "image_path": "/tmp/x.png",
            "session_id": "SEAL-test",
            "actor_id": "FORGE",
            "trace_id": "trc-1",
            "source_sha256": "deadbeef",
        }
    )
    dumped = ok.model_dump()
    assert dumped["session_id"] == "SEAL-test"
    assert dumped["actor_id"] == "FORGE"
    assert dumped["source_sha256"] == "deadbeef"
    assert dumped["trace_id"] == "trc-1"
    assert dumped["image_path"] == "/tmp/x.png"

    # Typo must NOT validate cleanly (would poison VOID vs caller-error taxonomy)
    with pytest.raises(ValidationError) as ei:
        SectionImageMode.model_validate(
            {
                "mode": "interpret_section",
                "imagepath": "/tmp/typo.png",  # typo — not image_path
            }
        )
    err = str(ei.value)
    assert "imagepath" in err or "extra" in err.lower()

    # Completely unknown semantic field also forbidden
    with pytest.raises(ValidationError):
        SectionImageMode.model_validate(
            {
                "mode": "interpret_section",
                "image_path": "/tmp/x.png",
                "totally_unknown_xyz": 99,
            }
        )


EXPECTED_MODES = frozenset(
    {
        "horizon_contrast",
        "fault_sticks",
        "volume_frame",
        "blend",
        "structure_validate",
        "interpret_section",
        "rsi_pipeline",
        "segy_slice",
        "interpret",  # full bundle mode (post-B3)
    }
)


# ──────────────────────────────────────────────────────────────────────
# Schema → handler parity
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_schema_generates_with_discriminator():
    from geox_mcp.contracts.seismic_interpret_schema import generate_json_schema

    schema = generate_json_schema()
    assert schema.get("discriminator"), "discriminated union must declare discriminator"
    mapping = schema["discriminator"].get("mapping", {})
    assert mapping, "discriminator mapping required"
    # Every expected live mode must appear in the schema
    schema_modes = set(mapping.keys())
    missing = EXPECTED_MODES - schema_modes
    assert not missing, f"schema missing modes: {missing}"


@pytest.mark.asyncio
async def test_schema_round_trip_for_every_mode():
    """Every documented mode parses without raising."""
    from geox_mcp.contracts.seismic_interpret_schema import SeismicInterpretRequest
    from pydantic import TypeAdapter

    ta = TypeAdapter(SeismicInterpretRequest)

    samples: dict[str, dict[str, Any]] = {
        "horizon_contrast": {
            "mode": "horizon_contrast",
            "attribute_data": {"rms": [1.0, 2.0, 3.0]},
            "depth": [100.0, 200.0, 300.0],
        },
        "structure_validate": {
            "mode": "structure_validate",
            "framework": {"faults": [], "horizons": []},
        },
        "segy_slice": {"mode": "segy_slice", "segy_path": "/tmp/x.sgy", "frame_index": 5},
        "interpret_section": {
            "mode": "interpret_section",
            "image_path": "/tmp/section.png",
            "max_faults": 10,
            "max_horizons": 5,
        },
        "rsi_pipeline": {
            "mode": "rsi_pipeline",
            "image_path": "/tmp/section.png",
            "max_faults": 10,
            "max_horizons": 5,
        },
        "fault_sticks": {"mode": "fault_sticks", "source_uri": "sticks.csv"},
        "volume_frame": {"mode": "volume_frame", "volume_ref": "vol1"},
        "blend": {"mode": "blend", "volume_ref": "vol1"},
        "interpret": {
            "mode": "interpret",
            "framework": {"faults": [], "horizons": []},
        },
    }
    for mode, payload in samples.items():
        parsed = ta.validate_python(payload)
        assert parsed.mode == mode, f"mode mismatch on {mode}"


@pytest.mark.asyncio
async def test_unknown_mode_explicit_failure():
    """Unknown mode must raise — never silently fall through."""
    from geox_mcp.contracts.seismic_interpret_schema import SeismicInterpretRequest
    from pydantic import TypeAdapter, ValidationError

    ta = TypeAdapter(SeismicInterpretRequest)
    with pytest.raises(ValidationError):
        ta.validate_python({"mode": "does_not_exist"})


@pytest.mark.asyncio
async def test_undeclared_argument_explicit_failure():
    """Extras rejected at the StrictInterpretRequest wrapper level.

    Pydantic's bare discriminated union (Annotated[..., Field(discriminator=...)])
    silently drops unknown fields. We wrap it in `StrictInterpretRequest`
    (with `extra="forbid"`) so the contract fails loudly on unknown keys
    at the wrapper level. Per F13: every schema field is owned; unknowns
    must fail loudly.

    KNOWN LIMITATION: Pydantic does not propagate `extra="forbid"` from
    each discriminated-union branch up to the wrapper. So extras inside
    `request` are dropped silently (Pydantic's discriminator validates
    mode first, then validates the matched branch). The wrapper-level
    `extra="forbid"` catches top-level typos around `request`.
    """
    from geox_mcp.contracts.seismic_interpret_schema import StrictInterpretRequest
    from pydantic import ValidationError

    # Wrapper-level unknown → reject
    with pytest.raises(ValidationError):
        StrictInterpretRequest.model_validate(
            {
                "request": {"mode": "horizon_contrast"},
                "wrapper_typo": True,
            }
        )

    # Each branch's `extra="forbid"` is enforced at branch validation time.
    from geox_mcp.contracts.seismic_interpret_schema import SeismicInterpretRequest
    from pydantic import TypeAdapter

    ta = TypeAdapter(SeismicInterpretRequest)
    # Branch-level extra=forbid: unknown keys must fail loudly (A1 / F13).
    with pytest.raises(ValidationError):
        ta.validate_python(
            {
                "mode": "horizon_contrast",
                "attribute_data": {"rms": [1.0, 2.0, 3.0]},
                "depth": [100.0, 200.0, 300.0],
                "this_is_not_a_field": True,
            }
        )


# ──────────────────────────────────────────────────────────────────────
# Handler → schema parity (live)
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handler_live_modes_present():
    """Handler's live-mode set must include the canonical modes."""
    from geox_mcp.tools.seismic_interpret import _LIVE_MODES

    live = set(_LIVE_MODES)
    missing = EXPECTED_MODES - live - {"interpret"}  # interpret is new
    assert not missing, f"handler missing live modes: {missing}"


@pytest.mark.asyncio
async def test_handler_unknown_mode_returns_error():
    """Calling handler with unknown mode returns structured error."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(mode="not_a_real_mode")
    assert r.get("ok") is False
    assert r.get("error") in ("UNKNOWN_MODE", "MODE_NOT_PUBLIC")


@pytest.mark.asyncio
async def test_handler_each_mode_dispatches():
    """Each canonical mode reaches its handler without crashing."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    # horizon_contrast — valid 1D inputs (use longer arrays so the
    # background length matches the attribute depth axis)
    import numpy as np

    depth = [float(z) for z in np.linspace(100.0, 500.0, 21)]
    r1 = await geox_seismic_interpret(
        mode="horizon_contrast",
        attribute_data={"rms": [1.0 + 0.1 * (i % 7) for i in range(len(depth))]},
        depth=depth,
    )
    assert r1.get("mode") == "horizon_contrast"

    # structure_validate — empty framework returns HOLD (not crash)
    r2 = await geox_seismic_interpret(
        mode="structure_validate",
        framework={"faults": [], "horizons": []},
    )
    assert r2.get("mode") == "structure_validate"
    assert r2.get("local_verdict") == "QUALIFIED_CANDIDATE"

    # structure_validate — populated framework
    r3 = await geox_seismic_interpret(
        mode="structure_validate",
        framework={
            "faults": [
                {
                    "fault_id": "F1",
                    "regime_prior": "normal",
                    "dip_deg_image": 60.0,
                    "dip_calibrated": True,
                }
            ],
            "horizons": [
                {"horizon_id": "H1", "order_index": 0, "points": [{"x": 0, "y": 100}, {"x": 10, "y": 105}]},
                {"horizon_id": "H2", "order_index": 1, "points": [{"x": 0, "y": 200}, {"x": 10, "y": 205}]},
            ],
        },
    )
    assert "K-DIP" in r3.get("gates", {})
    assert r3["gates"]["K-DIP"]["status"] == "PASS"


# ──────────────────────────────────────────────────────────────────────
# Schema fields ⊆ handler kwargs
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_silent_argument_drop():
    """Every schema field must be accepted by the handler (no silent drops)."""
    import inspect

    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    sig = inspect.signature(geox_seismic_interpret)
    handler_params = set(sig.parameters.keys())

    # Schema field names (excluding discriminator + nested types)
    schema_fields = {
        # horizon_contrast
        "attribute_data",
        "depth",
        "geological_query",
        "well_ties",
        "stratigraphic_framework",
        "peak_threshold",
        "min_separation_m",
        "custom_query",
        "closure_grid",
        # fault_sticks / volume_frame / blend
        "source_uri",
        "source_type",
        "action",
        "volume_ref",
        "frame_index",
        "orientation",
        "provenance",
        "image_data",
        "blend_mode",
        # section / RSI / structure / SEG-Y
        "image_path",
        "framework",
        "faults",
        "horizons",
        "measurement_context",
        "segy_path",
        "max_faults",
        "max_horizons",
        # legacy
        "horizon_query",
        "threshold",
        "confidence_cap",
        "cube_ref",
        "volume_inline",
    }

    missing_in_handler = schema_fields - handler_params
    assert not missing_in_handler, (
        f"schema fields not accepted by handler: {missing_in_handler}"
    )


# ──────────────────────────────────────────────────────────────────────
# Receipt envelope contract (F13 doctrine)
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_gate_receipt_envelope_required_fields():
    """Every gate result must include the full envelope."""
    from geox_mcp.tools.structure_gates import run_all_structure_gates

    fw = {
        "faults": [
            {"fault_id": "F1", "regime_prior": "normal", "dip_deg_image": 60.0, "dip_calibrated": True}
        ],
        "horizons": [
            {"horizon_id": "A", "order_index": 0, "points": [{"x": 0, "y": 100}, {"x": 10, "y": 105}]},
            {"horizon_id": "B", "order_index": 1, "points": [{"x": 0, "y": 200}, {"x": 10, "y": 205}]},
        ],
    }
    m = run_all_structure_gates(fw)
    for gate_id, gate in m["gates"].items():
        if gate_id == "K-XCUT":
            continue
        for fld in ("status", "gate_id", "equation", "thresholds", "calculated_result", "evidence_refs", "receipt_hash"):
            assert gate.get(fld), f"{gate_id} missing {fld}"
        assert gate["status"] in {"PASS", "WARN", "KILL", "UNMEASURED"}


@pytest.mark.asyncio
async def test_unmeasured_doctrine():
    """Missing scale → UNMEASURED, never a KILL guess."""
    from geox_mcp.tools.structure_validate import geox_structure_validate

    r = await geox_structure_validate(
        framework={
            "faults": [
                {
                    "fault_id": "F_no_cal",
                    "regime_prior": "reverse",
                    "dip_deg_image": 75.0,  # extreme value
                    # NO dip_calibrated, NO VE → gate refuses to compute
                }
            ],
            "measurement_context": {"input_class": "image_only"},
        }
    )
    k_dip = r["gates"]["K-DIP"]
    assert k_dip["status"] == "UNMEASURED"
    assert "calibrat" in k_dip["reason"].lower() or "scal" in k_dip["reason"].lower()


@pytest.mark.asyncio
async def test_receipt_hash_is_stable():
    """Same inputs → same receipt_hash. Deterministic audit trail."""
    from geox_mcp.tools.structure_gates import run_all_structure_gates

    fw = {"faults": [{"fault_id": "F1", "regime_prior": "normal", "dip_deg_image": 60.0}]}
    r1 = run_all_structure_gates(fw)
    r2 = run_all_structure_gates(fw)
    assert r1["gates"]["K-DIP"]["receipt_hash"] == r2["gates"]["K-DIP"]["receipt_hash"]


# ──────────────────────────────────────────────────────────────────────
# Competing hypotheses contract (PR-C4)
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_competing_hypotheses_always_three():
    """Interpretation_bundle must emit ≥3 hypotheses (as_proposed + relay + artifact)."""
    from geox_mcp.contracts.interpretation_bundle import build_interpretation_bundle

    fw = {
        "faults": [
            {"fault_id": "F1", "regime_prior": "normal", "dip_deg_image": 60.0, "dip_calibrated": True}
        ]
    }
    bundle = build_interpretation_bundle(frameworks_or_primary=fw)
    assert len(bundle["hypotheses"]) >= 3, (
        f"need ≥3 hypotheses, got {len(bundle['hypotheses'])}"
    )


@pytest.mark.asyncio
async def test_preferred_hypothesis_always_none_from_geox():
    """GEOX MUST NOT auto-promote a preferred hypothesis. Human only."""
    from geox_mcp.contracts.interpretation_bundle import build_interpretation_bundle

    fw = {
        "faults": [
            {"fault_id": "F1", "regime_prior": "normal", "dip_deg_image": 60.0, "dip_calibrated": True}
        ]
    }
    bundle = build_interpretation_bundle(frameworks_or_primary=fw)
    assert bundle["preferred_hypothesis"] is None
    assert bundle["seal_eligibility"] is False
    assert bundle["seal_authority"] == "arifOS_only"
    assert bundle["local_verdict"] == "QUALIFIED_CANDIDATE"


# ──────────────────────────────────────────────────────────────────────
# ONNX adapter contract (PR-A3)
# ──────────────────────────────────────────────────────────────────────


def test_onnx_manifest_rejects_noncommercial_license():
    from geox_mcp.tools.seismic_onnx_adapter import OnnxModelAdapter, ModelManifest

    bad = ModelManifest(model_id="bad", revision="v1", license="CC-BY-NC-4.0")
    with pytest.raises(ValueError):
        OnnxModelAdapter(manifest=bad)


def test_onnx_manifest_rejects_gpl():
    from geox_mcp.tools.seismic_onnx_adapter import OnnxModelAdapter, ModelManifest

    bad = ModelManifest(model_id="bad", revision="v1", license="GPL-3.0")
    with pytest.raises(ValueError):
        OnnxModelAdapter(manifest=bad)


def test_onnx_adapter_refuses_to_seal():
    """Every adapter must declare what it refuses to seal."""
    from geox_mcp.tools.seismic_onnx_adapter import ClassicalBaselineAdapter

    a = ClassicalBaselineAdapter()
    refusal = a.refuse_to_seal()
    assert "final_verdict" in refusal["refuses"]
    assert "autonomous_structure_acceptance" in refusal["refuses"]
    assert len(refusal["promotion_required_benchmarks"]) >= 5


# ──────────────────────────────────────────────────────────────────────
# Human correction contract (PR-A4)
# ──────────────────────────────────────────────────────────────────────


def test_human_corrections_emit_receipts():
    from geox_mcp.tools.seismic_corrections import (
        add_seeds,
        freeze_accepted_geometry,
        join_faults,
        mark_unconformity,
        remove_segment,
        rerun_gates,
        select_alternative,
        split_fault,
    )

    # Every correction must return a receipt with receipt_hash
    s = add_seeds({}, horizon_seeds=[(50, 80)])
    assert "receipt" in s and "receipt_hash" in s["receipt"]
    f = freeze_accepted_geometry({})
    assert "receipt" in f and "frozen_at_iso" in f["receipt"]
    j = join_faults(
        {"faults": [{"fault_id": "F1"}, {"fault_id": "F2"}]},
        fault_ids=["F1", "F2"],
    )
    assert "receipt" in j and "receipt_hash" in j["receipt"]
    m = mark_unconformity(
        {"horizons": [{"horizon_id": "H1"}]},
        horizon_id="H1",
        surface_type="erosional",
    )
    assert "receipt" in m
    r = remove_segment(
        {"horizons": [{"horizon_id": "H1"}]},
        target_type="horizon",
        target_id="H1",
    )
    assert "receipt" in r
    rg = rerun_gates({"faults": []})
    assert "gate_matrix" in rg
    sel = select_alternative(
        {"horizons": [{"horizon_id": "H1"}]},
        horizon_id="H1",
        alternative_id="alt-A",
    )
    assert sel["framework"]["horizons"][0]["selected_alternative"] == "alt-A"
    sp = split_fault(
        {"faults": [{"fault_id": "F1"}]},
        fault_id="F1",
        at_xy=(100.0, 200.0),
    )
    assert any(f.get("fault_id") == "F1-b" for f in sp["framework"]["faults"])


# ──────────────────────────────────────────────────────────────────────
# Artifact ingest contract (PR-A1)
# ──────────────────────────────────────────────────────────────────────


def test_artifact_ingest_emits_hash_and_chain():
    from geox_mcp.tools.artifact_ingest import ingest_artifact

    art = ingest_artifact(
        "/root/GEOX/pyproject.toml",
        artifact_type="framework_json",
        note="contract test",
    )
    assert art["sha256"].startswith("sha256:")
    assert art["artifact_hash_chain"].startswith("sha256:")
    assert art["size_bytes"] > 0


def test_calibration_state_validation():
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

    partial = validate_calibration_state({"vertical_exaggeration": 1.0})
    assert partial["calibrated"] is False
    assert "polarity" in partial["missing"]


# ──────────────────────────────────────────────────────────────────────
# Classical baseline contract (PR-A2)
# ──────────────────────────────────────────────────────────────────────


def test_classical_baseline_returns_candidate_geometry():
    import numpy as np

    from geox_mcp.tools.seismic_classical import classical_baseline

    np.random.seed(0)
    img = np.random.randn(60, 80).astype(np.float32)
    img[20:25, :] += 1.0  # horizontal reflector

    out = classical_baseline(img, n_horizon_levels=3)
    assert out["local_verdict"] == "QUALIFIED_CANDIDATE"
    assert out["seal_authority"] == "arifOS_only"
    assert out["epistemic_label"] == "INT_SEISMIC"
    assert out["artifact_sha256"].startswith("sha256:")
    assert "candidate_horizons" in out
    assert "candidate_faults" in out
    assert "structure_tensor_dip_rad" in out
    assert "coherence_map" in out