"""
Test 5: Ensemble Residual Contracts
=====================================
Verifies that Tool 03 (geox_subsurface_generate_candidates) fulfils the
Blueprint output contract:

  - ensemble present with >= 3 realizations
  - each realization has scenario_tag: MIN / MID / MAX
  - residual has mean_offset and max_deviation keys
  - evidence_density has n_samples and data_quality keys
  - assumptions dict is present with target_class, rock_model, fluid_model, cutoffs
  - humility_score is a float >= 0

Tests are unit-level: they call _inject_ensemble_residual_evidence directly
with a synthetic SUCCESS result so no real LAS artifact is required.

Run: pytest tests/test_ensemble_residual_contracts.py -v
"""

import sys
sys.path.insert(0, ".")

import pytest
from contracts.tools.canonical._helpers import _inject_ensemble_residual_evidence


def _make_success_result(**overrides) -> dict:
    """Minimal SUCCESS result as _compute_subsurface_candidates would produce."""
    base = {
        "execution_status": "SUCCESS",
        "phit_p10": 0.08,
        "phit_p50": 0.15,
        "phit_p90": 0.22,
        "sw_p50": 0.45,
        "k_mean_md": 12.5,
        "n_samples": 1500,
        "uncertainty": {"input_null_pct": {"GR": 0.01, "RHOB": 0.02}},
    }
    base.update(overrides)
    return base


# ensemble presence

def test_ensemble_present():
    result = _inject_ensemble_residual_evidence(_make_success_result(), realizations=3)
    assert "ensemble" in result, "ensemble key missing"
    assert isinstance(result["ensemble"], list)


def test_ensemble_has_three_realizations():
    result = _inject_ensemble_residual_evidence(_make_success_result(), realizations=3)
    assert len(result["ensemble"]) == 3, f"Expected 3 realizations, got {len(result['ensemble'])}"


def test_ensemble_scenario_tags_min_mid_max():
    """Each realization must declare MIN, MID, or MAX scenario_tag."""
    result = _inject_ensemble_residual_evidence(_make_success_result(), realizations=3)
    tags = [r["scenario_tag"] for r in result["ensemble"]]
    assert "MIN" in tags, f"MIN tag missing from ensemble: {tags}"
    assert "MID" in tags, f"MID tag missing from ensemble: {tags}"
    assert "MAX" in tags, f"MAX tag missing from ensemble: {tags}"


def test_ensemble_realization_ids_sequential():
    result = _inject_ensemble_residual_evidence(_make_success_result(), realizations=3)
    ids = [r["realization_id"] for r in result["ensemble"]]
    assert ids == [1, 2, 3], f"Unexpected realization_ids: {ids}"


# residual contract

def test_residual_present():
    result = _inject_ensemble_residual_evidence(_make_success_result())
    assert "residual" in result, "residual key missing"


def test_residual_has_required_keys():
    result = _inject_ensemble_residual_evidence(_make_success_result())
    residual = result["residual"]
    assert "mean_offset" in residual, f"residual missing mean_offset: {residual}"
    assert "max_deviation" in residual, f"residual missing max_deviation: {residual}"


def test_residual_values_are_numeric():
    result = _inject_ensemble_residual_evidence(_make_success_result())
    assert isinstance(result["residual"]["mean_offset"], float)
    assert isinstance(result["residual"]["max_deviation"], float)


# evidence_density contract

def test_evidence_density_present():
    result = _inject_ensemble_residual_evidence(_make_success_result())
    assert "evidence_density" in result, "evidence_density key missing"


def test_evidence_density_has_required_keys():
    result = _inject_ensemble_residual_evidence(_make_success_result())
    ed = result["evidence_density"]
    assert "n_samples" in ed, f"evidence_density missing n_samples: {ed}"
    assert "data_quality" in ed, f"evidence_density missing data_quality: {ed}"


def test_evidence_density_data_quality_levels():
    """data_quality must be HIGH / MEDIUM / LOW."""
    for n_samples, expected_quality in [(2000, "HIGH"), (500, "MEDIUM"), (10, "LOW")]:
        result = _inject_ensemble_residual_evidence(
            _make_success_result(n_samples=n_samples)
        )
        q = result["evidence_density"]["data_quality"]
        assert q == expected_quality, (
            f"n_samples={n_samples}: expected {expected_quality}, got {q}"
        )


# assumptions contract

def test_assumptions_present():
    """assumptions is a Blueprint 888 HOLD blocker -- must exist."""
    result = _inject_ensemble_residual_evidence(
        _make_success_result(),
        assumptions={"target_class": "petrophysics", "rock_model": "linear", "fluid_model": "archie", "cutoffs": {}},
    )
    assert "assumptions" in result, "assumptions key missing -- 888 HOLD BLOCKER"


def test_assumptions_not_none_when_passed():
    assumptions_in = {
        "target_class": "petrophysics",
        "rock_model": "linear",
        "fluid_model": "archie",
        "cutoffs": {"vsh": 0.5, "phi": 0.1, "sw": 0.6, "rt": 2.0},
    }
    result = _inject_ensemble_residual_evidence(
        _make_success_result(), assumptions=assumptions_in
    )
    assert result["assumptions"] == assumptions_in


def test_assumptions_default_empty_dict_when_none():
    """If no assumptions passed, result must still carry an empty dict -- not absent."""
    result = _inject_ensemble_residual_evidence(_make_success_result())
    assert "assumptions" in result
    assert isinstance(result["assumptions"], dict)


def test_assumptions_has_core_keys_when_passed_from_wrapper():
    """Simulate the wrapper call: assumptions carry target_class, rock_model, fluid_model, cutoffs."""
    assumptions = {
        "target_class": "porosity",
        "rock_model": "neutron_density",
        "fluid_model": "archie",
        "cutoffs": {"vsh": 0.4, "phi": 0.08, "sw": 0.65, "rt": 1.5},
    }
    result = _inject_ensemble_residual_evidence(
        _make_success_result(), assumptions=assumptions
    )
    a = result["assumptions"]
    for key in ("target_class", "rock_model", "fluid_model", "cutoffs"):
        assert key in a, f"assumptions missing key: {key}"


# humility_score contract

def test_humility_score_present():
    result = _inject_ensemble_residual_evidence(_make_success_result())
    assert "humility_score" in result


def test_humility_score_is_float():
    result = _inject_ensemble_residual_evidence(_make_success_result())
    assert isinstance(result["humility_score"], float)


def test_humility_score_formula():
    """humility = (p90 - p10) / p50 -- must match hand calculation."""
    r = _inject_ensemble_residual_evidence(
        _make_success_result(phit_p10=0.08, phit_p50=0.15, phit_p90=0.22)
    )
    expected = round(abs(0.22 - 0.08) / abs(0.15), 4)
    assert r["humility_score"] == expected, (
        f"Expected humility_score={expected}, got {r['humility_score']}"
    )


def test_humility_score_non_negative():
    result = _inject_ensemble_residual_evidence(_make_success_result())
    assert result["humility_score"] >= 0.0


# non-SUCCESS passthrough

def test_error_result_not_mutated():
    """_inject_ensemble_residual_evidence must be a no-op for non-SUCCESS results."""
    error_result = {"execution_status": "ERROR", "error_code": "EVIDENCE_REF_NOT_FOUND"}
    result = _inject_ensemble_residual_evidence(error_result)
    assert "ensemble" not in result, "ensemble must not be injected into ERROR result"
    assert "assumptions" not in result


def test_hold_result_not_mutated():
    hold_result = {"execution_status": "HOLD", "error_code": "QC_FAILED_HUMAN_REVIEW_REQUIRED"}
    result = _inject_ensemble_residual_evidence(hold_result)
    assert "ensemble" not in result


if __name__ == "__main__":
    import pytest as _pytest
    _pytest.main([__file__, "-v"])
