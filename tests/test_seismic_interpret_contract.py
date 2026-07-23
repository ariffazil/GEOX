"""
B-final contract tests — schema ↔ handler parity for geox_seismic_interpret.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import inspect

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

    # unknown mode
    with pytest.raises(ValidationError):
        adapter.validate_python({"mode": "not_a_real_mode"})

    # extra field forbidden on branch
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "mode": "fault_sticks",
                "source_uri": "x",
                "totally_unknown_param": 1,
            }
        )


def test_json_schema_generated_from_models():
    from geox_mcp.domain.seismic_interpret.models import (
        bundle_json_schema,
        interpret_request_json_schema,
    )

    req = interpret_request_json_schema()
    assert "oneOf" in req or "$defs" in req or "anyOf" in req
    # discriminator presence (pydantic may encode differently)
    raw = str(req)
    assert "horizon_contrast" in raw
    assert "structure_validate" in raw
    assert "interpret" in raw

    bundle = bundle_json_schema()
    props = bundle.get("properties") or {}
    assert "hypotheses" in props
    assert "preferred_hypothesis" in props
    assert "local_verdict" in props
    assert "seal_authority" in props


def test_handler_params_include_contract_fields():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    sig = inspect.signature(geox_seismic_interpret)
    names = set(sig.parameters)
    required_surface = {
        "mode",
        "attribute_data",
        "depth",
        "image_path",
        "framework",
        "faults",
        "horizons",
        "calibration",
        "earth_constraints",
        "request",
        "segy_path",
        "emit_bundle",
        "artifact_ref",
    }
    missing = required_surface - names
    assert not missing, f"handler missing contract fields: {missing}"


@pytest.mark.asyncio
async def test_unknown_mode_explicit_failure():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(mode="totally_fake_mode")
    assert r.get("ok") is False
    assert r.get("error") in ("UNKNOWN_MODE", "MODE_NOT_PUBLIC")
    assert "live_modes" in r
    assert "horizon_contrast" in r["live_modes"]
    assert "interpret" in r["live_modes"] or "structure_validate" in r["live_modes"]


@pytest.mark.asyncio
async def test_undeclared_mode_does_not_fall_through_to_horizon_error():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(mode="vision")
    assert r.get("error") == "MODE_NOT_PUBLIC"
    assert "attribute_data" not in (r.get("message") or "").lower()


@pytest.mark.asyncio
async def test_preferred_hypothesis_always_null_from_geox():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(
        mode="structure_validate",
        framework={
            "faults": [
                {
                    "fault_id": "F1",
                    "regime_prior": "normal",
                    "dip_deg_subsurface": 60.0,
                    "tip_taper": "ok",
                    "throw_profile": [5, 40, 6],
                }
            ]
        },
    )
    assert r.get("preferred_hypothesis") is None
    bundle = r.get("interpretation_bundle")
    if isinstance(bundle, dict):
        assert bundle.get("preferred_hypothesis") is None
        assert bundle.get("seal_eligibility") is False
