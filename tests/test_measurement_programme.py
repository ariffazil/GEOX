"""WP-B acceptance tests — geox_measurement_programme (BRIEF §3 WP-B)."""

import pytest

from geox_mcp.tools.measurement_programme import geox_measurement_programme


def _appraisal_carbonate():
    return geox_measurement_programme(
        well_type="appraisal",
        basin="Sarawak (Central Luconia)",
        lithology="carbonate",
        play_type="carbonate build-up",
        water_depth=1000,
        target_depth=3200,
        mud_system="WBM",
        core_planned=True,
    )


def test_four_part_output_no_fabricated_cost():
    r = _appraisal_carbonate()
    assert r["status"] == "OK"
    assert r["analysis_list"], "analysis list present"
    assert any(a["sample_arithmetic"] for g in r["analysis_list"] for a in g["analyses"])
    assert r["cut_list"], "cut list present"
    assert r["epistemic"]["label"] == "DERIVED"
    assert "OMITTED" in r["epistemic"]["cost"], "no fabricated cost"


def test_determinism():
    a = _appraisal_carbonate()
    b = _appraisal_carbonate()
    assert a == b, "identical input -> identical output"


def test_exploration_vs_appraisal_distinction():
    e = geox_measurement_programme(well_type="exploration", lithology="clastic")
    a = geox_measurement_programme(well_type="appraisal", lithology="clastic")
    assert e["analysis_count"] != a["analysis_count"], "well type must change the programme"


def test_carbonate_suite_conditional():
    carb = _appraisal_carbonate()
    clast = geox_measurement_programme(well_type="appraisal", lithology="clastic")
    carb_disciplines = [g["discipline"] for g in carb["analysis_list"]]
    clast_disciplines = [g["discipline"] for g in clast["analysis_list"]]
    assert any("Carbonate" in d for d in carb_disciplines)
    assert not any("Carbonate" in d for d in clast_disciplines)


def test_invalid_well_type():
    r = geox_measurement_programme(well_type="wildcat")
    assert r["status"] == "INVALID"
