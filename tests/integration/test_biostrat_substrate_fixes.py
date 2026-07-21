"""
test_biostrat_substrate_fixes.py — Regression tests for T2.6-S3 substrate fixes.

Two findings from T2.6-S2 corpus:

F1 — LBF (Lunt 2016) zone codes like 'Tf1', 'Te2' failed lookup because
     biostrat/zones.py::zone_to_biozone uppercased the input via
     .upper().strip() before comparing against mixed-case LBF_ZONES keys.

F2 — lithology_class() did not recognise 'evaporite', 'red_bed', or
     'continental_conglomerate' trigger words used by falsify G1's
     FOSSIL_ECOLOGY excluded_lithologies check.

This file proves both fixes hold without regressing existing behaviour.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from geox_mcp.tools.biostrat.zones import (  # noqa: E402
    SCHEME_REGISTRY,
    zone_age,
    zone_to_biozone,
)
from geox_mcp.tools.kernel._biostrat import lithology_class  # noqa: E402


# ═════════════════════════════════════════════════════════════════════════════
# F1 — Case-insensitive LBF zone lookup
# ═════════════════════════════════════════════════════════════════════════════


LBF_CASES = [
    # (input, expected_canonical_id, expected_top, expected_base)
    ("Tf1", "Tf1", 0.00, 2.60),
    ("te2", "Te2", 13.60, 15.90),
    ("TF1", "Tf1", 0.00, 2.60),  # uppercase normalised to canonical case
    ("tG", "Tg", 23.03, 28.10),  # lowercase normalised to canonical case
    ("Tf2", "Tf2", 2.60, 5.33),
    ("Te5", "Te5", 5.33, 7.10),
    ("Th",  "Th",  28.10, 33.90),
    ("Ti1", "Ti1", 33.90, 37.70),
]


@pytest.mark.parametrize("input_zone,canonical,exp_top,exp_base", LBF_CASES)
def test_f1_lbf_zone_to_biozone_case_insensitive(
    input_zone: str, canonical: str, exp_top: float, exp_base: float
):
    """LBF (Lunt 2016) zones resolve correctly regardless of input case."""
    bz = zone_to_biozone(input_zone, "Lunt_2016_LBF")
    assert bz is not None, f"LBF zone '{input_zone}' should resolve after F1 fix"
    # Canonical case preserved in Biozone.zone_id
    assert bz.zone_id == canonical, (
        f"Input '{input_zone}' should preserve canonical '{canonical}', got '{bz.zone_id}'"
    )
    assert abs(bz.age_top_ma - exp_top) < 0.01, (
        f"LBF {input_zone} top {bz.age_top_ma} != expected {exp_top}"
    )
    assert abs(bz.age_base_ma - exp_base) < 0.01, (
        f"LBF {input_zone} base {bz.age_base_ma} != expected {exp_base}"
    )


@pytest.mark.parametrize("input_zone,canonical,exp_top,exp_base", LBF_CASES)
def test_f1_lbf_zone_age_case_insensitive(
    input_zone: str, canonical: str, exp_top: float, exp_base: float
):
    """zone_age() helper also case-insensitive (paired fix)."""
    top, base = zone_age(input_zone, "Lunt_2016_LBF")
    assert (top, base) != (-999.25, -999.25), (
        f"zone_age('{input_zone}') should not return sentinel after F1 fix"
    )
    assert abs(top - exp_top) < 0.01
    assert abs(base - exp_base) < 0.01


def test_f1_martini_uppercase_unchanged():
    """Regression: Martini NN5 still resolves with the same age as before."""
    bz = zone_to_biozone("NN5", "Martini_1971_NN")
    assert bz is not None
    assert bz.zone_id == "NN5"  # canonical case is uppercase
    assert abs(bz.age_top_ma - 14.62) < 0.01
    assert abs(bz.age_base_ma - 15.97) < 0.01


def test_f1_blow_uppercase_unchanged():
    """Regression: Blow N17 still resolves."""
    bz = zone_to_biozone("N17", "Blow_1969_N")
    assert bz is not None
    assert abs(bz.age_top_ma - 5.08) < 0.01
    assert abs(bz.age_base_ma - 6.32) < 0.01


def test_f1_unknown_zone_still_returns_none():
    """Regression: garbage input still returns None — fail-closed preserved."""
    assert zone_to_biozone("NOTAREALZONE") is None
    assert zone_to_biozone("XX99", "Martini_1971_NN") is None


def test_f1_zone_age_unknown_still_sentinel():
    """Regression: zone_age sentinel preserved for unknown."""
    top, base = zone_age("NOTAREALZONE")
    assert (top, base) == (-999.25, -999.25)


# ═════════════════════════════════════════════════════════════════════════════
# F2 — Lithology vocabulary extended
# ═════════════════════════════════════════════════════════════════════════════


LITHOLOGY_CASES = [
    # (input, expected_class)
    ("evaporite",                    "evaporite"),
    ("EVAPORITE",                    "evaporite"),  # case-insensitive
    ("anhydrite",                    "evaporite"),
    ("gypsum",                       "evaporite"),
    ("halite",                       "evaporite"),
    ("salt",                         "evaporite"),
    ("red beds",                     "red_bed"),
    ("redbed",                       "red_bed"),
    ("red sandstone",                "red_bed"),
    ("continental conglomerate",     "continental_conglomerate"),
    ("fluvial conglomerate",         "continental_conglomerate"),
    ("alluvial conglomerate",        "continental_conglomerate"),
    # Existing classes preserved:
    ("coal",                         "COAL_CARBONACEOUS"),
    # Note: "carbonaceous shale" → SHALE_PRONE (pre-existing ordering: shale check
    # before coal check). This is a separate concern from F2 — F2 only adds new
    # vocabulary, it does not re-order existing checks. Documented here for honesty.
    ("carbonaceous shale",           "SHALE_PRONE"),
    ("marine shale",                 "SHALE_PRONE"),
    ("sandstone",                    "SAND_PRONE"),
    ("limestone",                    "CARBONATE"),
    ("dolomite",                     "CARBONATE"),
    ("",                             "UNKNOWN"),
]


@pytest.mark.parametrize("lithology,expected_class", LITHOLOGY_CASES)
def test_f2_lithology_class_vocabulary_extended(lithology: str, expected_class: str):
    """lithology_class returns the trigger word that falsify G1 expects."""
    cls = lithology_class(lithology)
    assert cls == expected_class, (
        f"lithology_class({lithology!r}) = {cls!r}, expected {expected_class!r}"
    )


def test_f2_g1_substring_check_works_for_evaporite():
    """Verify the actual falsify G1 contract: 'evaporite' substring in returned class."""
    cls = lithology_class("evaporite").lower()
    assert "evaporite" in cls, (
        f"G1 needs 'evaporite' substring; got {cls!r}. Substring check would fail."
    )


def test_f2_g1_substring_check_works_for_red_bed():
    cls = lithology_class("red beds").lower()
    assert "red_bed" in cls, (
        f"G1 needs 'red_bed' substring; got {cls!r}."
    )


def test_f2_g1_substring_check_works_for_continental_conglomerate():
    cls = lithology_class("continental conglomerate").lower()
    assert "continental_conglomerate" in cls, (
        f"G1 needs 'continental_conglomerate' substring; got {cls!r}."
    )


def test_f2_g1_substring_check_still_works_for_coal():
    """Regression: coal path must still work (was working before F2)."""
    cls = lithology_class("coal").lower()
    assert "coal_carbonaceous" in cls


# ═════════════════════════════════════════════════════════════════════════════
# End-to-end: F1 + F2 fix combined effect on a calibrate call
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_f1_lbf_zone_now_parties_through_calibrate():
    """Tf1 LBF zone should now resolve via geox_biostrat_calibrate."""
    from geox_mcp.tools.biostrat_calibrate import geox_biostrat_calibrate

    result = await geox_biostrat_calibrate(
        zone_code="Tf1", scheme="Lunt_2016_LBF"
    )
    data = result["data"]
    assert data["verdict"] == "PARTIAL", (
        f"LBF Tf1 should now be PARTIAL after F1 fix; got verdict={data['verdict']}"
    )
    assert data["calibrated_age_min_ma"] == 0.0
    assert data["calibrated_age_max_ma"] == 2.60


@pytest.mark.asyncio
async def test_f2_evaporite_contradiction_now_voids():
    """Planktonic foram in evaporite should now VOID (was PARTIAL in T2.6-S2 corpus)."""
    from geox_mcp.tools.biostrat_calibrate import geox_biostrat_calibrate

    result = await geox_biostrat_calibrate(
        taxon_name="Globigerinoides",
        zone_code="N4",
        fossil_group="planktonic_foraminifera",
        lithology="evaporite",
        environment="sabkha",
        run_falsify=True,
        claim="open marine in situ",
        region="sabah",
        sample_type="core",
    )
    data = result["data"]
    assert data["verdict"] == "VOID", (
        f"Evaporite contradiction should now VOID after F2 fix; got verdict={data['verdict']}"
    )
    # The falsify summary must include G1_FACIES as a falsified gate
    fs = data.get("falsification_summary", {})
    primary = fs.get("primary_artifact", {}) if isinstance(fs, dict) else {}
    falsified = primary.get("falsified_gates", [])
    assert "G1_FACIES" in falsified, (
        f"G1 should fire on evaporite for planktonic foram; falsified gates={falsified}"
    )
