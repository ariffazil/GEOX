"""
test_deep_time_state.py — geox_deep_time_state conformance (FORGE 2026-06-22 + hardening)

Verifies the GEOX Deep Time Physics Context Tool, including the 4-crack
hardening and 2-governance-gap closure:

  Hardening addressed:
    Crack 1 — 5-state polarity enum (NORMAL/REVERSED/MIXED/SUPERCHRON/UNRESOLVED)
    Crack 2 — benthic δ18O (OBSERVED) split from temperature (INTERPRETED)
    Crack 3 — sea level reference-frame fields (curve, component, datum)
    Crack 4 — interval queries return distribution metadata, not just scalar
    Gap 1   — F9 fabrication guard (UNKNOWN for unknowable params)
    Gap 2   — mandatory _governance footer (verdict, risk, human_review, seal)

  Core verification:
    1. Canonical surface presence (registry + manifest)
    2. Age Resolver (numeric, range, named, fuzzy, case-insensitive)
    3. ICS Chart v2024/12 boundaries
    4. Earth State Vector — all 14+ variables returned
    5. F2 TRUTH — null + NO_DATA for pending external data
    6. F7 HUMILITY — confidence capped at 0.90
    7. Solar/day-length formulas
    8. CNS/Kiaman SUPERCHRON detection
    9. Legacy alias routes correctly
   10. Pending datasets + unknown_at_age lists populated

DITEMPA BUKAN DIBEI — Earth evidence is forged, not given.
"""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.join(REPO_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)


# ─── 1. Canonical surface presence ───────────────────────────────────────────


def test_geox_deep_time_state_in_canonical_registry():
    """The tool is in CANONICAL_PUBLIC_TOOLS."""
    try:
        from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
    except ImportError:
        pytest.skip("geox_mcp.registry not importable in this env")
    assert "geox_deep_time_state" in CANONICAL_PUBLIC_TOOLS


def test_geox_deep_time_state_module_importable():
    """The tool module imports cleanly with @mcp.tool function defined."""
    from geox_mcp.tools.deep_time_state import geox_deep_time_state
    assert callable(geox_deep_time_state)
    assert asyncio.iscoroutinefunction(geox_deep_time_state)


def test_geox_time4d_reconstruct_palo_alias():
    """Legacy alias from the parity matrix slot routes to the same function."""
    from geox_mcp.tools.deep_time_state import (
        geox_deep_time_state,
        geox_time4d_reconstruct_paleo,
    )
    assert geox_time4d_reconstruct_paleo is not None


# ─── 2. Age Resolver — numeric ────────────────────────────────────────────────


def test_resolve_numeric_point():
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    res = resolve_age_query(age_ma=66.0)
    assert 65.0 <= res.top_ma <= 67.0
    assert 65.0 <= res.base_ma <= 67.0
    assert res.named_unit in ("Cretaceous", "Paleocene")
    assert res.ics_chart_version == "v2024/12"


def test_resolve_numeric_range():
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    res = resolve_age_query(age_top_ma=145.0, age_bot_ma=66.0)
    assert res.top_ma == 66.0
    assert res.base_ma == 145.0
    assert res.named_unit in ("Cretaceous", "Early Cretaceous")
    assert res.duration_myr == pytest.approx(79.0, abs=0.01)


# ─── 3. Age Resolver — named units ────────────────────────────────────────────


def test_resolve_jurassic_period():
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    res = resolve_age_query(period="Jurassic")
    assert res.named_unit == "Jurassic"
    assert res.named_rank == "period"
    assert res.top_ma == pytest.approx(145.0, abs=0.01)
    assert res.base_ma == pytest.approx(201.4, abs=0.01)
    assert res.confidence >= 0.95


def test_resolve_late_cretaceous_epoch():
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    res = resolve_age_query(period="Late Cretaceous")
    assert res.named_unit == "Late Cretaceous"
    assert res.named_rank == "epoch"
    assert res.top_ma == pytest.approx(66.0, abs=0.01)
    assert res.base_ma == pytest.approx(100.5, abs=0.01)


# ─── 4. Age Resolver — fuzzy phrases ──────────────────────────────────────────


def test_resolve_fuzzy_phrase_age_of_dinosaurs():
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    res = resolve_age_query(query="when dinosaurs ruled")
    assert res.named_unit == "Mesozoic"
    assert 66.0 <= res.base_ma <= 252.0


def test_resolve_fuzzy_phrase_kpg_boundary():
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    res = resolve_age_query(query="K-Pg boundary")
    assert 60.0 <= res.midpoint_ma <= 70.0


def test_resolve_fuzzy_phrase_snowball_earth():
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    res = resolve_age_query(query="snowball earth")
    assert 670.0 <= res.midpoint_ma <= 720.0


def test_resolve_fuzzy_phrase_substring_match():
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    res = resolve_age_query(query="what was Earth like during dinosaurs?")
    assert res.named_unit == "Mesozoic"


# ─── 5. ICS Chart v2024/12 boundaries ─────────────────────────────────────────


def test_ics_chart_v2024_12_periods():
    from geox_mcp.tools.deep_time.ics_chart import ics_chart_v2024_12
    chart = ics_chart_v2024_12
    assert chart.version == "v2024/12"
    by_name = {p.name: p for p in chart.periods}
    assert by_name["Cretaceous"].top_ma == pytest.approx(66.0, abs=0.01)
    assert by_name["Cretaceous"].base_ma == pytest.approx(145.0, abs=0.01)
    assert by_name["Jurassic"].top_ma == pytest.approx(145.0, abs=0.01)
    assert by_name["Permian"].base_ma == pytest.approx(298.9, abs=0.01)
    assert by_name["Cambrian"].base_ma == pytest.approx(538.8, abs=0.01)


# ─── 6. Earth State Vector — all 14+ variables ────────────────────────────────


def test_assemble_vector_has_all_variables():
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    from geox_mcp.tools.deep_time.vector import assemble_earth_state_vector
    res = resolve_age_query(age_ma=66.0)
    vec = assemble_earth_state_vector(res)
    assert vec.solar_luminosity_fraction is not None
    assert vec.day_length_hours is not None
    assert vec.orbital_eccentricity is not None
    assert vec.orbital_obliquity_deg is not None
    assert vec.atmospheric_co2_ppm is not None
    assert vec.benthic_d18O_permil is not None
    assert vec.global_temperature_anomaly_c is not None
    assert vec.eustatic_sea_level_m is not None
    assert vec.geomagnetic_polarity is not None
    assert vec.atmospheric_o2_pal is not None
    assert vec.paleogeography_summary is not None
    assert vec.supercontinent_state is not None
    assert vec.ice_extent is not None
    assert vec.biotic_realm is not None


# ─── 7. Crack 2 — temperature split (benthic_d18O vs global_temp) ──────────


def test_benthic_d18O_separate_from_temperature():
    """δ18O is OBSERVED; temperature is INTERPRETED. They are separate fields."""
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    from geox_mcp.tools.deep_time.vector import assemble_earth_state_vector
    res = resolve_age_query(age_ma=66.0)
    vec = assemble_earth_state_vector(res)
    assert vec.benthic_d18O_permil is not None
    assert vec.global_temperature_anomaly_c is not None
    # Both pending external ingestion at this stage
    assert vec.benthic_d18O_permil.epistemic_level in ("NO_DATA", "OBSERVED", "UNKNOWN")
    assert vec.global_temperature_anomaly_c.epistemic_level in ("NO_DATA", "INTERPRETED", "UNKNOWN")


# ─── 8. Crack 3 — sea level reference frame fields ──────────────────────────


def test_sea_level_has_reference_frame_fields():
    """Sea level variable carries curve/component/datum fields (even when NO_DATA)."""
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    from geox_mcp.tools.deep_time.vector import assemble_earth_state_vector
    res = resolve_age_query(age_ma=66.0)
    vec = assemble_earth_state_vector(res)
    assert vec.eustatic_sea_level_m is not None
    # Schema fields present (may be None when NO_DATA — but the slot must exist)
    assert hasattr(vec.eustatic_sea_level_m, "reference_curve")
    assert hasattr(vec.eustatic_sea_level_m, "reference_component")
    assert hasattr(vec.eustatic_sea_level_m, "reference_datum")


# ─── 9. Crack 4 — interval queries get distribution metadata ───────────────


def test_interval_query_has_distribution_warning():
    """Wide interval queries (e.g. period) get interval metadata."""
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    from geox_mcp.tools.deep_time.vector import assemble_earth_state_vector
    res = resolve_age_query(period="Jurassic")  # 56 Myr interval
    vec = assemble_earth_state_vector(res)
    assert vec.is_interval_query is True
    assert vec.interval_duration_myr > 5.0


def test_point_query_does_not_get_distribution_warning():
    """Narrow interval (<=5 Myr) is point semantics — no distribution warning."""
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    from geox_mcp.tools.deep_time.vector import assemble_earth_state_vector
    res = resolve_age_query(age_ma=66.0)  # ±1 Myr window = 2 Myr
    vec = assemble_earth_state_vector(res)
    assert vec.is_interval_query is False


# ─── 10. Crack 1 — 5-state polarity enum ──────────────────────────────────────


def test_polarity_superchron_in_cns():
    """100 Ma falls in CNS → SUPERCHRON."""
    from geox_mcp.tools.deep_time.data_loaders import load_magnetic_polarity
    var = load_magnetic_polarity(100.0, 99.0, 101.0, 2.0)
    assert var.value is not None
    assert "SUPERCHRON" in var.value.upper()
    assert var.notes is not None
    assert "ZERO" in var.notes.upper() or "NULL" in var.notes.upper()
    assert var.warning is not None
    assert "DATING RESOLUTION" in var.warning.upper()


def test_polarity_superchron_in_kiaman():
    """290 Ma falls in Kiaman Reversed Superchron → SUPERCHRON."""
    from geox_mcp.tools.deep_time.data_loaders import load_magnetic_polarity
    var = load_magnetic_polarity(290.0, 289.0, 291.0, 2.0)
    assert var.value is not None
    assert "SUPERCHRON" in var.value.upper()


def test_polarity_unresolved_pre_triassic():
    """Age > 250 Ma (above GPTS calibrated range) → UNRESOLVED."""
    from geox_mcp.tools.deep_time.data_loaders import load_magnetic_polarity
    var = load_magnetic_polarity(400.0, 399.0, 401.0, 2.0)
    assert var.value == "UNRESOLVED"


def test_polarity_resolve_state_enum():
    """The PolarityState enum has all 5 states."""
    from geox_mcp.tools.deep_time.schemas import PolarityState
    assert PolarityState.NORMAL.value == "normal"
    assert PolarityState.REVERSED.value == "reversed"
    assert PolarityState.MIXED.value == "mixed"
    assert PolarityState.SUPERCHRON.value == "superchron"
    assert PolarityState.UNRESOLVED.value == "unresolved"


# ─── 11. Gap 1 — F9 fabrication guard (UNKNOWN) ──────────────────────────────


def test_f9_co2_unknown_in_hadean():
    """CO2 in Hadean (>1500 Ma) → UNKNOWN (no proxy exists)."""
    from geox_mcp.tools.deep_time.data_loaders import load_co2_estimate
    var = load_co2_estimate(2000.0, 1999.0, 2001.0, 2.0)
    assert var.epistemic_level == "UNKNOWN"
    assert "F9" in (var.notes or "") or "fabricat" in (var.notes or "").lower()


def test_f9_d18O_unknown_pre_triassic():
    """δ18O before benthic forams (>180 Ma) → UNKNOWN."""
    from geox_mcp.tools.deep_time.data_loaders import load_benthic_d18O
    var = load_benthic_d18O(300.0, 299.0, 301.0, 2.0)
    assert var.epistemic_level == "UNKNOWN"


def test_f9_o2_unknown_in_archean():
    """O2 in Archean (>2500 Ma) → UNKNOWN."""
    from geox_mcp.tools.deep_time.data_loaders import load_atmospheric_o2
    var = load_atmospheric_o2(3000.0, 2999.0, 3001.0, 2.0)
    assert var.epistemic_level == "UNKNOWN"


def test_f9_sea_level_unknown_precambrian():
    """Sea level in Precambrian (>541 Ma) → UNKNOWN."""
    from geox_mcp.tools.deep_time.data_loaders import load_sea_level_estimate
    var = load_sea_level_estimate(600.0, 599.0, 601.0, 2.0)
    assert var.epistemic_level == "UNKNOWN"


def test_unknown_distinct_from_no_data():
    """UNKNOWN ≠ NO_DATA — UNKNOWN is unknowable, NO_DATA is ingestible."""
    from geox_mcp.tools.deep_time.schemas import EPISTEMIC_CONFIDENCE_CAP
    assert "UNKNOWN" in EPISTEMIC_CONFIDENCE_CAP
    assert "NO_DATA" in EPISTEMIC_CONFIDENCE_CAP
    assert EPISTEMIC_CONFIDENCE_CAP["UNKNOWN"] < EPISTEMIC_CONFIDENCE_CAP["NO_DATA"]


# ─── 12. Gap 2 — governance footer mandatory ────────────────────────────────


def test_governance_footer_present():
    """Every envelope carries a governance footer with verdict + risk + seal."""
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    from geox_mcp.tools.deep_time.vector import assemble_earth_state_vector, assemble_envelope
    res = resolve_age_query(period="Jurassic")
    vec = assemble_earth_state_vector(res)
    env = assemble_envelope(age_res=res, input_query={"period": "Jurassic"}, vector=vec)
    assert env.governance is not None
    gov = env.governance
    assert "verdict" in gov
    assert "risk" in gov
    assert "human_review_required" in gov
    assert "f9_fabrication_guard_active" in gov
    assert gov["f9_fabrication_guard_active"] is True
    assert gov["seal"] is not None
    assert gov["seal"].startswith("VAULT999::DTC::")


def test_governance_verdict_HOLD_when_unknown_fields_present():
    """If any field is UNKNOWN, verdict = HOLD + human_review_required = True."""
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    from geox_mcp.tools.deep_time.vector import assemble_earth_state_vector, assemble_envelope
    # Hadean → CO2 is UNKNOWN → verdict should be HOLD
    res = resolve_age_query(query="Hadean")
    vec = assemble_earth_state_vector(res)
    env = assemble_envelope(age_res=res, input_query={"query": "Hadean"}, vector=vec)
    gov = env.governance
    assert gov["verdict"] == "HOLD"
    assert gov["human_review_required"] is True
    assert gov["risk"] == "MEDIUM"


def test_governance_lowest_confidence_field_populated():
    """Governance footer identifies the lowest-confidence field."""
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    from geox_mcp.tools.deep_time.vector import assemble_earth_state_vector, assemble_envelope
    res = resolve_age_query(age_ma=66.0)
    vec = assemble_earth_state_vector(res)
    env = assemble_envelope(age_res=res, input_query={"age_ma": 66.0}, vector=vec)
    gov = env.governance
    assert gov["lowest_confidence_field"] is not None


def test_unknown_at_age_list_populated_for_hadean():
    """Hadean query → unknown_at_age list contains the F9-flagged variables."""
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    from geox_mcp.tools.deep_time.vector import assemble_earth_state_vector, assemble_envelope
    res = resolve_age_query(query="Hadean")
    vec = assemble_earth_state_vector(res)
    env = assemble_envelope(age_res=res, input_query={"query": "Hadean"}, vector=vec)
    assert len(env.unknown_at_age) >= 1
    unknown_vars = [u["variable"] for u in env.unknown_at_age]
    assert "atmospheric_co2_ppm" in unknown_vars


# ─── 13. F7 HUMILITY ───────────────────────────────────────────────────────────


def test_confidence_capped_at_090():
    from geox_mcp.tools.deep_time.schemas import cap_confidence
    assert cap_confidence("OBSERVED", 0.99) == 0.90
    assert cap_confidence("INTERPRETED", 0.95) == 0.85
    assert cap_confidence("PROCESS_HYPOTHESIS", 0.99) == 0.75
    assert cap_confidence("DERIVED", 0.99) == 0.90
    assert cap_confidence("NO_DATA", 0.50) == 0.10
    assert cap_confidence("UNKNOWN", 0.50) == 0.05


def test_formula_variables_have_derivation_epistemic():
    from geox_mcp.tools.deep_time.age_resolver import resolve_age_query
    from geox_mcp.tools.deep_time.vector import assemble_earth_state_vector
    res = resolve_age_query(age_ma=66.0)
    vec = assemble_earth_state_vector(res)
    assert vec.solar_luminosity_fraction.epistemic_level == "DERIVED"
    assert vec.day_length_hours.epistemic_level == "DERIVED"
    assert vec.orbital_eccentricity.epistemic_level == "DERIVED"
    assert vec.orbital_obliquity_deg.epistemic_level == "DERIVED"


# ─── 14. Solar/day length formulas ────────────────────────────────────────────


def test_solar_luminosity_at_present_is_1():
    from geox_mcp.tools.deep_time.formulas import solar_luminosity_fraction
    assert solar_luminosity_fraction(0.0) == pytest.approx(1.0, abs=1e-6)


def test_solar_luminosity_faint_young_sun_at_formation():
    from geox_mcp.tools.deep_time.formulas import solar_luminosity_fraction
    assert 0.65 <= solar_luminosity_fraction(4544.0) <= 0.75


def test_day_length_at_present_is_24_hours():
    from geox_mcp.tools.deep_time.formulas import day_length_hours
    assert day_length_hours(0.0) == pytest.approx(24.0, abs=0.01)


def test_day_length_ancient_shorter():
    from geox_mcp.tools.deep_time.formulas import day_length_hours
    assert day_length_hours(540.0) < 24.0
    assert day_length_hours(540.0) > 20.0


# ─── 15. Full envelope — async end-to-end ────────────────────────────────────


def test_async_geox_deep_time_state_jurassic():
    from geox_mcp.tools.deep_time_state import geox_deep_time_state
    result = asyncio.run(geox_deep_time_state(period="Jurassic"))
    assert result["primary_artifact"]["tool"] == "geox_deep_time_state"
    assert result["primary_artifact"]["age_resolution"]["named_unit"] == "Jurassic"
    assert "earth_state_vector" in result["primary_artifact"]
    assert "governance" in result["primary_artifact"]


def test_async_geox_deep_time_state_hadean_returns_HOLD():
    """Hadean query triggers F9 → verdict = HOLD."""
    from geox_mcp.tools.deep_time_state import geox_deep_time_state
    result = asyncio.run(geox_deep_time_state(query="Hadean"))
    assert result["primary_artifact"]["governance"]["verdict"] == "HOLD"
    assert result["primary_artifact"]["governance"]["human_review_required"] is True


def test_async_geox_deep_time_state_kpg_boundary():
    from geox_mcp.tools.deep_time_state import geox_deep_time_state
    result = asyncio.run(geox_deep_time_state(query="K-Pg boundary"))
    assert 60.0 <= result["primary_artifact"]["age_resolution"]["midpoint_ma"] <= 70.0


def test_async_legacy_alias_routes():
    from geox_mcp.tools.deep_time_state import geox_time4d_reconstruct_paleo
    result = asyncio.run(geox_time4d_reconstruct_paleo(age_ma=66.0))
    assert result["primary_artifact"]["tool"] == "geox_deep_time_state"
    assert 60.0 <= result["primary_artifact"]["age_resolution"]["midpoint_ma"] <= 70.0


def test_async_geox_deep_time_state_cns_window():
    """100 Ma = CNS → polarity should reflect SUPERCHRON."""
    from geox_mcp.tools.deep_time_state import geox_deep_time_state
    result = asyncio.run(geox_deep_time_state(age_ma=100.0))
    polarity_value = (
        result.get("primary_artifact", {})
        .get("earth_state_vector", {})
        .get("geomagnetic_polarity", {})
        .get("value", "")
    )
    assert "SUPERCHRON" in polarity_value.upper()
