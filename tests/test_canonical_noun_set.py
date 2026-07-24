"""Regression tests for the W1 canonical noun set (2026-07-24 hardening pass).

These tests verify invariants, not just field presence. Each test guards a
contract that an unwary caller could otherwise violate:

  - extra="forbid"   : typo / unknown field tripwire
  - strict=True      : no implicit coercion (str -> enum, str -> int, etc.)
  - frozen=True      : instances are immutable; mutation must raise
  - required fields  : domain, units, source_geometry_hash, receipt_hash ...

If any of these tests fail, the canonical noun set is no longer safe to
wire into the W1 gate pipeline. Treat every failure as a contract break.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from geox_mcp.domain.seismic_interpret.models import (
    CoordinateDomain,
    DipBasis,
)


# --- Helpers -----------------------------------------------------------------


def _point(**overrides):
    """Return a complete Point2D dict. Domain is the enum instance, not a
    string, because the canonical models are strict=True."""
    base = {
        "x": 1.0,
        "y": 2.0,
        "domain": CoordinateDomain.TRACE,
        "horizontal_unit": "trace",
        "vertical_unit": "ms",
    }
    base.update(overrides)
    return base


def _polyline():
    pts = [
        _point(point_order=0),
        _point(x=3.0, y=4.0, point_order=1),
        _point(x=5.0, y=6.0, point_order=2),
    ]
    return {"points": pts}


def _fault_kwargs():
    return {
        "fault_id": "F1",
        "polyline": _polyline(),
    }


def _witness_kwargs():
    return {
        "witness_id": "W1",
        "model_or_method": "deterministic_transform",
        "source_geometry_hash": "abc123",
        "derivation": "took the fault polyline and ran K-DIP",
        "structural_style": "extensional_normal",
    }


def _minimal_hypothesis_kwargs():
    return {"hypothesis_id": "H1", "witness": _witness_kwargs()}


# --- extra="forbid" ----------------------------------------------------------


def test_fault_extra_forbid():
    from geox_mcp.domain.seismic_interpret.models import Fault

    Fault(**_fault_kwargs())  # baseline—no extras
    with pytest.raises(ValidationError) as exc:
        Fault(**_fault_kwargs(), regime_priors="high")  # misspelled field
    assert "Extra inputs" in str(exc.value)


def test_horizon_extra_forbid():
    from geox_mcp.domain.seismic_interpret.models import Horizon

    Horizon(horizon_id="H")  # baseline—all geometry optional
    with pytest.raises(ValidationError) as exc:
        Horizon(horizon_id="H", top_depth=100.0)  # invented field
    assert "Extra inputs" in str(exc.value)


def test_hypothesis_extra_forbid():
    from geox_mcp.domain.seismic_interpret.models import Hypothesis

    Hypothesis(**_minimal_hypothesis_kwargs())
    with pytest.raises(ValidationError) as exc:
        Hypothesis(**_minimal_hypothesis_kwargs(), confidence=0.9)
    assert "Extra inputs" in str(exc.value)


# --- frozen=True -------------------------------------------------------------


def test_fault_frozen():
    from geox_mcp.domain.seismic_interpret.models import Fault

    fault = Fault(**_fault_kwargs())
    with pytest.raises(ValidationError) as exc:
        fault.fault_id = "F2"  # type: ignore[misc]
    assert "frozen" in str(exc.value).lower()


def test_canonical_bundle_frozen():
    from geox_mcp.domain.seismic_interpret.models import CanonicalInterpretationBundle

    bundle = CanonicalInterpretationBundle(receipt_hash="h" * 16)
    with pytest.raises(ValidationError) as exc:
        bundle.receipt_hash = "z" * 16  # type: ignore[misc]
    assert "frozen" in str(exc.value).lower()
    with pytest.raises(ValidationError):
        bundle.seal_eligibility = True  # type: ignore[misc]


# --- F7 Humility: no fixed confidence at the type level ----------------------


def test_hypothesis_no_fixed_confidence():
    """Hypothesis MUST default confidence_value to None. The contract forbids
    emitting a fixed confidence at the type level—only attachments carry
    a measured confidence, and only after benchmark calibration is verified.
    """
    from geox_mcp.domain.seismic_interpret.models import Hypothesis

    hyp = Hypothesis(**_minimal_hypothesis_kwargs())
    assert hyp.confidence_value is None
    assert hyp.confidence_basis is None
    # strict mode: a string for confidence_value must NOT be coerced.
    with pytest.raises(ValidationError):
        Hypothesis(**_minimal_hypothesis_kwargs(), confidence_value="not_a_float")


def test_hypothesis_confidence_only_via_attachment():
    """Confidence is the attachment's job, not a top-level field. If a
    benchmark does attach a confidence, it lives in the attachments dict
    alongside a citation. The top-level confidence_value stays None.
    """
    from geox_mcp.domain.seismic_interpret.models import Hypothesis

    hyp = Hypothesis(
        **_minimal_hypothesis_kwargs(),
        attachments={"benchmark_confidence": 0.73, "benchmark_doi": "10.0/xyz"},
    )
    assert hyp.attachments["benchmark_confidence"] == 0.73
    assert hyp.confidence_value is None


# --- GateResult required fields ---------------------------------------------


def test_gate_result_required_fields():
    """These fields are required on every gate (no defaults). Missing any one
    must raise ValidationError so the audit trail is never partial.

    `inputs_used`, `measurement_units`, and `missing_inputs` have defaults
    (empty dict / empty list) on purpose: a gate can record 'no inputs
    used' cleanly. The truly required fields are the six below.
    """
    from geox_mcp.domain.seismic_interpret.models import GateResult

    full = {
        "gate_id": "K-DIP",
        "status": "PASS",
        "inputs_used": {"dip_deg": 45.0},
        "measurement_units": {"dip_deg": "deg"},
        "equation_or_rule": "tan(dip) <= 0.577",
        "threshold_source": "F1_AMANAH_TABLE_2026",
        "reason": "dip within bounds",
        "missing_inputs": [],
        "receipt_hash": "r" * 16,
    }
    GateResult(**full)  # baseline

    no_default_fields = (
        "gate_id",
        "status",
        "equation_or_rule",
        "threshold_source",
        "reason",
        "receipt_hash",
    )
    for missing in no_default_fields:
        kwargs = {k: v for k, v in full.items() if k != missing}
        with pytest.raises(ValidationError) as exc:
            GateResult(**kwargs)
        assert (
            missing in str(exc.value)
            or "field required" in str(exc.value).lower()
        ), f"missing field {missing} should have been raised, got: {exc.value}"


def test_gate_result_inputs_units_parallel():
    """inputs_used and measurement_units are parallel dicts: every key in
    inputs_used has a corresponding unit string. The type does not enforce
    parallelism (it can't, since dicts are open at the type level), but
    the test documents the contract so callers learn it.
    """
    from geox_mcp.domain.seismic_interpret.models import GateResult

    g = GateResult(
        gate_id="K-THROW",
        status="WARN",
        inputs_used={"throw_m": 12.5},
        measurement_units={"throw_m": "m"},
        equation_or_rule="throw_m >= 5",
        threshold_source="regional_prior",
        reason="throw above noise floor",
        missing_inputs=["velocity"],
        receipt_hash="0" * 16,
    )
    assert g.inputs_used["throw_m"] == 12.5
    assert g.measurement_units["throw_m"] == "m"


# --- Fault: three distinct dip fields, three distinct semantic bases ---------


def test_fault_dip_fields_distinct():
    """The three dip fields are NOT aliases—they have different semantics:

      - image_dip_deg          : raw pixel measurement (no VE correction)
      - apparent_section_dip_deg: after azimuth correction only
      - true_subsurface_dip_deg: after VE correction, true 3D dip

    A regression that collapses them into one field would silently mis-label
    the gate verdict. The test asserts all three are independently settable
    and that the test set is not degenerate (image != true).
    """
    from geox_mcp.domain.seismic_interpret.models import Fault

    f = Fault(
        **_fault_kwargs(),
        image_dip_deg=72.0,
        apparent_section_dip_deg=58.0,
        true_subsurface_dip_deg=42.0,
        dip_basis=DipBasis.TRUE_SUBSURFACE,
    )
    assert f.image_dip_deg == 72.0
    assert f.apparent_section_dip_deg == 58.0
    assert f.true_subsurface_dip_deg == 42.0
    assert f.dip_basis is DipBasis.TRUE_SUBSURFACE
    assert f.image_dip_deg != f.true_subsurface_dip_deg


# --- Horizon: three distinct geometry tracks + conversion_basis --------------


def test_horizon_geometries_distinct():
    """A horizon keeps pixel/time/depth geometry as separate optional
    fields. The conversion_basis declares which transform licensed the
    non-pixel tracks. The structural separation prevents a regression
    that overwrites pixel geometry with a time-domain polyline.
    """
    from geox_mcp.domain.seismic_interpret.models import Horizon, Polyline2D

    pixel = Polyline2D(points=[_point()])
    time = Polyline2D(
        points=[_point(x=10.0, y=20.0, domain=CoordinateDomain.TIME_MS)]
    )
    h = Horizon(
        horizon_id="T1",
        pixel_geometry=pixel,
        time_geometry=time,
        conversion_basis="regional_prior",
    )
    assert h.pixel_geometry is not None
    assert h.time_geometry is not None
    assert h.depth_geometry is None
    assert h.conversion_basis == "regional_prior"
    assert h.pixel_geometry is not h.time_geometry


# --- WitnessProvenance: required chain ---------------------------------------


def test_witness_provenance_required_chain():
    """A witness without witness_id, witness_type (defaulted), derivation,
    or source_geometry_hash is a broken witness—it cannot be re-derived.
    """
    from geox_mcp.domain.seismic_interpret.models import WitnessProvenance

    WitnessProvenance(**_witness_kwargs())  # baseline

    for missing in (
        "witness_id",
        "model_or_method",
        "source_geometry_hash",
        "derivation",
        "structural_style",
    ):
        kwargs = {k: v for k, v in _witness_kwargs().items() if k != missing}
        with pytest.raises(ValidationError):
            WitnessProvenance(**kwargs)


# --- CoordinateDomain: every Point2D must declare domain + units -------------


def test_coordinate_domain_declared():
    """Anonymous geometry is rejected. Every Point2D must declare domain,
    horizontal_unit, and vertical_unit. No defaults, no inferred types.
    """
    from geox_mcp.domain.seismic_interpret.models import Point2D

    # Baseline—all three declared.
    Point2D(
        x=1.0,
        y=2.0,
        domain=CoordinateDomain.TRACE,
        horizontal_unit="trace",
        vertical_unit="ms",
    )

    for missing in ("domain", "horizontal_unit", "vertical_unit"):
        kwargs = {
            "x": 1.0,
            "y": 2.0,
            "domain": CoordinateDomain.TRACE,
            "horizontal_unit": "trace",
            "vertical_unit": "ms",
        }
        del kwargs[missing]
        with pytest.raises(ValidationError):
            Point2D(**kwargs)

    # Strict mode: a string for x must NOT be coerced to float.
    with pytest.raises(ValidationError):
        Point2D(
            x="1.0",  # type: ignore[arg-type]
            y=2.0,
            domain=CoordinateDomain.TRACE,
            horizontal_unit="trace",
            vertical_unit="ms",
        )

    # Strict mode: a bare string for the enum field must NOT be coerced.
    with pytest.raises(ValidationError):
        Point2D(
            x=1.0,
            y=2.0,
            domain="trace",  # type: ignore[arg-type]
            horizontal_unit="trace",
            vertical_unit="ms",
        )


# --- Polyline2D: point_order preserved ---------------------------------------


def test_polyline_ordering():
    """Point2D.point_order is the explicit ordering channel. The Polyline
    is a list, so list order is preserved, but the point_order field is
    what makes the order defensible against a careless re-shuffle.
    """
    from geox_mcp.domain.seismic_interpret.models import Polyline2D

    pts = [
        _point(point_order=0),
        _point(x=10.0, y=20.0, point_order=1),
        _point(x=30.0, y=40.0, point_order=2),
    ]
    poly = Polyline2D(points=pts)
    assert [p.point_order for p in poly.points] == [0, 1, 2]
    assert [p.x for p in poly.points] == [1.0, 10.0, 30.0]
    # closed=False by default; mutating it must fail (frozen).
    with pytest.raises(ValidationError):
        poly.closed = True  # type: ignore[misc]
