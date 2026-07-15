"""
WAJIB #2 (Claude-fable review 2026-07-13): regression suite for the
`_inject_ensemble_residual_evidence` type-guard on `uncertainty`.

The original bug:
    "null_pct": result.get("uncertainty", {}).get("input_null_pct", {})
crashes with `AttributeError: 'str' object has no attribute 'get'` whenever
`uncertainty` is a string band (e.g. "MEDIUM") instead of a dict. This file
replays every observed shape — dict, string band, scalar float/int/bool,
None, missing key — plus a Hypothesis property test that generates random
shapes to ensure no future regression.

Sealed: 2026-07-14 by FORGE (000Ω) under F13 sovereign "yolo afk".
"""

from __future__ import annotations

import pytest

from geox_mcp.tools.kernel._evidence import _inject_ensemble_residual_evidence


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic regression — replays yesterday's exact crash + canonical cases
# ─────────────────────────────────────────────────────────────────────────────


def test_string_band_does_not_crash():
    """The bug. uncertainty='MEDIUM' used to AttributeError on .get()."""
    r = {
        "execution_status": "SUCCESS",
        "phit_p50": 0.22,
        "sw_p50": 0.30,
        "n_samples": 500,
        "uncertainty": "MEDIUM",
    }
    out = _inject_ensemble_residual_evidence(r)
    np = out["evidence_density"]["null_pct"]
    assert np["band"] == "MEDIUM"
    assert np["input_null_pct"] is None
    assert np["warning"] == "uncertainty_was_string_band"


def test_dict_uncertainty_passes_through():
    """Canonical case — dict with input_null_pct preserved verbatim."""
    inner = {"GR": 0.05, "NPHI": 0.02}
    r = {
        "execution_status": "SUCCESS",
        "phit_p50": 0.22,
        "n_samples": 1500,
        "uncertainty": {"input_null_pct": inner},
    }
    out = _inject_ensemble_residual_evidence(r)
    assert out["evidence_density"]["null_pct"] == inner


def test_float_scalar_uncertainty():
    """geox_candidates emits `uncertainty=0.12` (float) — must not crash."""
    r = {
        "execution_status": "SUCCESS",
        "phit_p50": 0.22,
        "n_samples": 50,
        "uncertainty": 0.12,
    }
    out = _inject_ensemble_residual_evidence(r)
    assert out["evidence_density"]["null_pct"]["scalar"] == 0.12


def test_none_uncertainty_yields_empty_dict():
    r = {
        "execution_status": "SUCCESS",
        "phit_p50": 0.22,
        "n_samples": 100,
        "uncertainty": None,
    }
    out = _inject_ensemble_residual_evidence(r)
    assert out["evidence_density"]["null_pct"] == {}


def test_missing_uncertainty_key_yields_empty_dict():
    r = {"execution_status": "SUCCESS", "phit_p50": 0.22, "n_samples": 100}
    out = _inject_ensemble_residual_evidence(r)
    assert out["evidence_density"]["null_pct"] == {}


def test_non_success_status_bypasses_injection():
    """FATAL / ERROR must NOT receive evidence_density — they fail honestly."""
    r = {"execution_status": "FATAL", "uncertainty": "MEDIUM"}
    out = _inject_ensemble_residual_evidence(r)
    assert "evidence_density" not in out
    assert "ensemble" not in out


def test_bool_uncertainty_handled():
    """Edge: bool is a subclass of int — must not crash."""
    r = {"execution_status": "SUCCESS", "phit_p50": 0.22, "n_samples": 100, "uncertainty": True}
    out = _inject_ensemble_residual_evidence(r)
    assert out["evidence_density"]["null_pct"]["scalar"] is True


def test_string_band_with_real_meaning():
    """A non-'MEDIUM' band string still preserves provenance."""
    r = {"execution_status": "SUCCESS", "phit_p50": 0.18, "n_samples": 250, "uncertainty": "HIGH+"}
    out = _inject_ensemble_residual_evidence(r)
    assert out["evidence_density"]["null_pct"]["band"] == "HIGH+"


# ─────────────────────────────────────────────────────────────────────────────
# Property-based fuzzing — the class of bug this regression guards against
# ─────────────────────────────────────────────────────────────────────────────

try:
    import hypothesis  # noqa: F401
    from hypothesis import given, settings, strategies as st

    _HYPOTHESIS_AVAILABLE = True
except ImportError:  # property-based tests skipped if hypothesis missing
    _HYPOTHESIS_AVAILABLE = False
    given = None
    settings = None
    st = None


# Anything JSON-serialisable that *could* be passed as `uncertainty`
uncertainty_st = st.one_of(
    st.none(),
    st.booleans(),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    st.integers(min_value=0, max_value=100),
    st.text(min_size=1, max_size=16),
    st.dictionaries(
        keys=st.sampled_from(["input_null_pct", "p10", "p50", "p90", "band"]),
        values=st.one_of(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            st.text(max_size=8),
            st.dictionaries(
                keys=st.sampled_from(["GR", "NPHI", "RHOB", "RT", "DT"]),
                values=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
                max_size=3,
            ),
        ),
        max_size=3,
    ),
)


@pytest.mark.skipif(not _HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
@given(uncertainty=uncertainty_st, n_samples=st.integers(min_value=0, max_value=5000))
@settings(max_examples=200, deadline=None)
def test_property_uncertainty_never_crashes(uncertainty, n_samples):
    """Whatever shape `uncertainty` takes, _inject_ensemble_residual_evidence
    must not raise. The whole point of the type guard is fail-safe degradation."""
    r = {
        "execution_status": "SUCCESS",
        "phit_p50": 0.22,
        "n_samples": n_samples,
        "uncertainty": uncertainty,
    }
    out = _inject_ensemble_residual_evidence(r)
    # Invariants — output must always have these keys when SUCCESS
    assert "ensemble" in out
    assert "residual" in out
    assert "evidence_density" in out
    assert "humility_score" in out
    # null_pct must always be a dict (the type guard's contract)
    assert isinstance(out["evidence_density"]["null_pct"], dict)
