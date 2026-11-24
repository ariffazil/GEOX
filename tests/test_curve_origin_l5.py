"""Law L5 / L10 — curve origin separation.

These pin the invariant that was missing before 2026-11-24: the QC path built one
``raw_curves`` dict from every LAS curve, so a *computed* curve satisfied a
completeness requirement meant for a *measured* one.

Two properties matter and both are asserted here:

1. a mnemonic can never produce better than LOW-confidence provenance;
2. inventory completeness and physical (measured) completeness are distinct, and
   a computed curve satisfies only the first.
"""

from __future__ import annotations

import pytest

from geox_core.curve_origin import (
    CurveOrigin,
    classify_curve_origin,
    measure_completeness,
)


@pytest.mark.parametrize(
    "mnemonic,expected",
    [
        ("GR", CurveOrigin.MEASURED.value),
        ("RHOB", CurveOrigin.MEASURED.value),
        ("NPHI", CurveOrigin.MEASURED.value),
        ("VSH", CurveOrigin.COMPUTED.value),
        ("PHIE", CurveOrigin.COMPUTED.value),
        ("PERM", CurveOrigin.COMPUTED.value),
        ("RHOB_INTERP", CurveOrigin.INTERPRETED.value),
        ("GR_SPLICE", CurveOrigin.SPLICED.value),
        ("DT_SYNTH", CurveOrigin.RECONSTRUCTED.value),
    ],
)
def test_origin_classification(mnemonic, expected):
    assert classify_curve_origin(mnemonic)["origin"] == expected


def test_token_beats_exact_match():
    """RHOB is measured; RHOB_INTERP is not — the suffix must win."""
    assert classify_curve_origin("RHOB")["origin"] == CurveOrigin.MEASURED.value
    assert classify_curve_origin("RHOB_INTERP")["origin"] == CurveOrigin.INTERPRETED.value


def test_tvd_is_not_a_measurement():
    """TVD is derived from deviation. Only MD along the borehole is measured."""
    assert classify_curve_origin("MD")["origin"] == CurveOrigin.MEASURED.value
    assert classify_curve_origin("TVD")["origin"] == CurveOrigin.COMPUTED.value
    assert classify_curve_origin("TVDSS")["origin"] == CurveOrigin.COMPUTED.value


def test_unknown_stays_unknown():
    result = classify_curve_origin("ZZZ9")
    assert result["origin"] == CurveOrigin.UNKNOWN.value
    assert result["origin_basis"] == "unknown"
    assert result["origin_confidence"] == "unknown"


@pytest.mark.parametrize("mnemonic", ["GR", "VSH", "RHOB_INTERP", "GR_SPLICE", "DT_SYNTH", "ZZZ9", ""])
def test_every_classification_carries_basis_and_confidence(mnemonic):
    result = classify_curve_origin(mnemonic)
    assert set(result) == {"origin", "origin_basis", "origin_confidence"}
    # A mnemonic match may never claim provenance better than LOW.
    assert result["origin_confidence"] in {"low", "unknown"}
    if result["origin"] != CurveOrigin.UNKNOWN.value:
        assert result["origin_basis"] == "mnemonic_pattern"


def test_computed_curve_does_not_satisfy_physical_completeness():
    """The defect this whole module exists to prevent, stated as an assertion."""
    present = {"RHOB": CurveOrigin.COMPUTED.value, "GR": CurveOrigin.MEASURED.value}
    result = measure_completeness(present, total_canonical=10)

    assert result["inventory_count"] == 2
    assert result["measured_count"] == 1
    assert result["measured_curves"] == ["GR"]
    assert result["inventory_only_curves"] == ["RHOB"]
    assert result["completeness_inventory_score"] == 0.2
    assert result["completeness_measured_score"] == 0.1


def test_unknown_curve_stays_in_inventory_but_not_in_physical_measure():
    present = {"ZZZ9": CurveOrigin.UNKNOWN.value}
    result = measure_completeness(present, total_canonical=10)

    assert result["inventory_count"] == 1, "an unknown curve must not vanish"
    assert result["measured_count"] == 0, "unknown must not count as measured"
    assert result["inventory_only_curves"] == ["ZZZ9"]


def test_zero_denominator_is_safe():
    assert measure_completeness({}, total_canonical=0)["completeness_measured_score"] == 0.0
