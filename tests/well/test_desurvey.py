"""Golden tests for geox_core.engines.well.desurvey_core.

Six tests covering the canonical scenarios from GEOX-ADAPT-001-r1 §GOLDEN TESTS.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import pytest

# Ensure src/ is importable
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from geox_core.engines.well.desurvey_core import desurvey  # noqa: E402

# Tolerance constants
TOL_TIGHT_M = 0.01
TOL_TVD_M = 0.5
TOL_LATERAL_M = 1.0
TOL_AZI_DEG = 0.001

# Default collar at origin (RTM-Malaya projected, in metres)
RTM_ORIGIN = {"x_collar": 0.0, "y_collar": 0.0, "z_collar": 0.0, "ground_elev": 0.0}


# ─── Test 1 — Vertical well (sanity) ──────────────────────────────────────
def test_1_vertical_well():
    """Vertical well: TVD == MD, X==0, Y==0, closure_error==0."""
    survey = [
        {"md": 0.0, "inc": 0.0, "azi": 0.0},
        {"md": 1500.0, "inc": 0.0, "azi": 0.0},
        {"md": 3000.0, "inc": 0.0, "azi": 0.0},
    ]
    result = desurvey(
        well_id="VERT-1",
        collar=RTM_ORIGIN,
        survey=survey,
        method="minimum_curvature",
        declination_deg=0.0,
        kb_elevation_m=25.0,
    )
    assert result["scheme"] == "geox.desurvey.v1"
    assert result["well_id"] == "VERT-1"
    assert result["method"] == "minimum_curvature"

    # Last row should be at MD=3000
    last = result["rows"][-1]
    assert last["md_m"] == pytest.approx(3000.0, abs=1e-6)
    assert last["tvd_m"] == pytest.approx(3000.0, abs=TOL_TIGHT_M)
    assert last["tvdss_m"] == pytest.approx(3000.0 - 25.0, abs=TOL_TIGHT_M)
    assert last["x_m"] == pytest.approx(0.0, abs=TOL_TIGHT_M)
    assert last["y_m"] == pytest.approx(0.0, abs=TOL_TIGHT_M)

    # QC
    qc = result["qc_report"]
    assert qc["closure_error_m"] == 0.0
    assert qc["lateral_departure_m"] == pytest.approx(0.0, abs=TOL_TIGHT_M)
    assert qc["kb_elevation_m_used"] == 25.0

    # Claim envelope
    assert result["claim_envelope"]["tag"] == "CLAIM"
    assert result["claim_envelope"]["acr"] < 0.30


# ─── Test 2 — Straight inclined well ──────────────────────────────────────
def test_2_straight_inclined_well():
    """Straight inclined at 30° azimuth East.
    Expected: TVD ≈ MD*cos(30°), lateral X (easting) ≈ MD*sin(30°).
    """
    survey = [
        {"md": 0.0, "inc": 30.0, "azi": 90.0},
        {"md": 1000.0, "inc": 30.0, "azi": 90.0},
    ]
    result = desurvey(
        well_id="INCL-30E",
        collar=RTM_ORIGIN,
        survey=survey,
        method="minimum_curvature",
        declination_deg=0.0,
        kb_elevation_m=30.0,
    )

    last = result["rows"][-1]
    expected_tvd = 1000.0 * math.cos(math.radians(30.0))
    expected_easting = 1000.0 * math.sin(math.radians(30.0))

    assert last["tvd_m"] == pytest.approx(expected_tvd, abs=TOL_TVD_M)
    # Convention (matches pyproj always_xy=True): x_m = easting, y_m = northing.
    # For azi=90° (East), northing ≈ 0 and easting ≈ 500.
    assert last["x_m"] == pytest.approx(expected_easting, abs=TOL_LATERAL_M)
    assert last["y_m"] == pytest.approx(0.0, abs=TOL_TIGHT_M)
    assert result["claim_envelope"]["tag"] == "CLAIM"


# ─── Test 3 — Build-and-hold horizontal ───────────────────────────────────
def test_3_build_and_hold_horizontal():
    """Kickoff at 500m, build 3°/30m to 90°, hold to 2000m MD.

    For a 3°/30m build rate from inc=0 at 500m to inc=90:
      Build section length: 90° / (3°/30m) = 900m of MD (from 500 to 1400m MD)
      Hold section: 1400m to 2000m MD = 600m at inc=90°

    Expected: TVD at TD ≈ 500 (vertical) + build integral + hold(0)
    Build integral: integral of cos(inc) where inc goes 0→90 linearly,
    integrated over the 900m build. Result: 900 * (2/π) * 1 ≈ 573m of TVD in build.
    Hold section: TVD contribution = 600 * cos(90°) = 0.
    Total TVD at TD ≈ 500 + 573 ≈ 1073m. (Analytic check via wellpathpy.)
    Lateral X at TD = build integral of sin(inc) + 600*sin(90°)
                    = 900*(2/π) + 600 ≈ 573 + 600 ≈ 1173m
    """
    survey = [
        {"md": 0.0, "inc": 0.0, "azi": 0.0},
        {"md": 500.0, "inc": 0.0, "azi": 90.0},  # vertical section ends
        {"md": 1400.0, "inc": 90.0, "azi": 90.0},  # build section ends
        {"md": 2000.0, "inc": 90.0, "azi": 90.0},  # hold section ends
    ]
    result = desurvey(
        well_id="HORIZ-1",
        collar=RTM_ORIGIN,
        survey=survey,
        method="minimum_curvature",
        declination_deg=0.0,
        kb_elevation_m=20.0,
    )

    last = result["rows"][-1]
    # Tolerance ±2% of TD for build-hold math
    # wellpathpy minimum_curvature is more accurate than analytic build estimate
    assert last["tvd_m"] == pytest.approx(1073.0, abs=15.0), f"expected TVD ≈ 1073m, got {last['tvd_m']}"
    # Lateral at TD (north + east components combined)
    qc = result["qc_report"]
    # Lateral ≈ 1173m for azi=90, with build contribution
    assert qc["lateral_departure_m"] == pytest.approx(1173.0, abs=20.0), (
        f"expected lateral ≈ 1173m, got {qc['lateral_departure_m']}"
    )

    assert result["claim_envelope"]["tag"] == "CLAIM"


# ─── Test 4 — Magnetic declination application ────────────────────────────
def test_4_magnetic_declination_application():
    """Declination of -3° applied to magnetic azi 45° → true azi 42°.

    F2 TRUTH: declination must be explicit. Test that it actually applies.
    """
    survey = [
        {"md": 0.0, "inc": 10.0, "azi": 45.0},  # magnetic
        {"md": 500.0, "inc": 10.0, "azi": 45.0},  # magnetic
    ]
    result = desurvey(
        well_id="DECL-1",
        collar=RTM_ORIGIN,
        survey=survey,
        method="minimum_curvature",
        declination_deg=-3.0,  # West (East Malaysia offshore ≈ -1 to -3)
        kb_elevation_m=15.0,
    )

    last = result["rows"][-1]
    # azi_true = 45 + (-3) = 42°
    assert last["azi_true_deg"] == pytest.approx(42.0, abs=TOL_AZI_DEG), f"expected azi_true 42°, got {last['azi_true_deg']}"

    # QC should report declination applied
    assert result["qc_report"]["magnetic_declination_applied_deg"] == -3.0

    # Tag should be CLAIM (clean data, declination declared, no gaps)
    assert result["claim_envelope"]["tag"] == "CLAIM"


# ─── Test 5 — Survey gap detection (inc-aware) ───────────────────────────
def test_5_survey_gap_escalates_estimate():
    """Survey with a real gap on a deviated well (inc > 5°).
    Gap 1000→2000 = 1000m between stations. With inc=30° at both ends,
    the gap is inc-eligible and should be flagged.

    Expect: survey_gap_intervals populated, acr elevated, geometry self-consistent.
    Note: with the gap decoupled from tag, this case stays CLAIM but
    acr rises (gap penalty only).
    """
    survey = [
        {"md": 0.0, "inc": 30.0, "azi": 90.0},
        {"md": 500.0, "inc": 30.0, "azi": 90.0},
        {"md": 1000.0, "inc": 30.0, "azi": 90.0},
        {"md": 2000.0, "inc": 30.0, "azi": 90.0},  # ← gap from 1000m to 2000m
        {"md": 2500.0, "inc": 30.0, "azi": 90.0},
    ]
    result = desurvey(
        well_id="GAP-1",
        collar=RTM_ORIGIN,
        survey=survey,
        method="minimum_curvature",
        declination_deg=0.0,
        kb_elevation_m=10.0,
        step_size_m=10.0,
    )

    # Should produce output up to MD=2500m (last survey station)
    assert result["rows"][-1]["md_m"] == pytest.approx(2500.0, abs=1e-6)

    # Gap intervals: 1000→2000 (1000m, inc=30° at both ends → flagged)
    gaps = result["qc_report"]["survey_gap_intervals"]
    flagged = [g for g in gaps if abs(g["to_md_m"] - g["from_md_m"] - 1000.0) < 1.0]
    assert len(flagged) >= 1, f"expected gap from 1000→2000 to be flagged, got {gaps}"

    # ACRisk should be elevated by gap penalty (baseline 0.18 + 0.05 = 0.23)
    assert result["claim_envelope"]["acr"] > 0.22, f"expected elevated acr due to gap, got {result['claim_envelope']['acr']}"

    # Tag is CLAIM (gap penalty lives in ACR, not tag — per decoupled logic)
    # The geometry is still self-consistent (constant inc, constant azi).
    assert result["claim_envelope"]["tag"] == "CLAIM"


# ─── Test 6 — KB missing escalates appropriately ──────────────────────────
def test_6_kb_missing_escalates():
    """All data clean but kb_elevation_m omitted.
    Expect: tvdss_m == null, kb_elevation_m_used == null,
            acr += 0.10, tag=PLAUSIBLE.
    """
    survey = [
        {"md": 0.0, "inc": 0.0, "azi": 0.0},
        {"md": 1000.0, "inc": 0.0, "azi": 0.0},
    ]
    result = desurvey(
        well_id="NO-KB-1",
        collar=RTM_ORIGIN,
        survey=survey,
        method="minimum_curvature",
        declination_deg=0.0,
        kb_elevation_m=None,  # ← missing
    )

    # tvdss_m should be None in all rows
    for row in result["rows"]:
        assert row["tvdss_m"] is None, f"expected tvdss_m=None when kb missing, got {row['tvdss_m']}"

    # QC should reflect kb not used
    assert result["qc_report"]["kb_elevation_m_used"] is None
    assert result["qc_report"]["total_depth_tvdss_m"] is None

    # ACRisk should include KB missing penalty (0.18 baseline + 0.10)
    assert result["claim_envelope"]["acr"] == pytest.approx(0.28, abs=0.01), (
        f"expected acr ≈ 0.28 (baseline 0.18 + KB missing 0.10), got {result['claim_envelope']['acr']}"
    )

    # "missing" should mention KB
    assert any("kb_elevation_m" in m for m in result["claim_envelope"]["missing"])

    # Tag — with no kb, cannot be CLAIM. PLAUSIBLE expected (clean otherwise)
    assert result["claim_envelope"]["tag"] == "PLAUSIBLE", (
        f"expected PLAUSIBLE (no KB, otherwise clean), got {result['claim_envelope']['tag']}"
    )


# ─── Bonus: tangential method sanity ──────────────────────────────────────
def test_bonus_tangential_method():
    """Tangential method via balanced_tan should produce close-to-minimum-curvature
    result for a smooth well. Verify method selection works."""
    survey = [
        {"md": 0.0, "inc": 0.0, "azi": 90.0},
        {"md": 500.0, "inc": 30.0, "azi": 90.0},
        {"md": 1000.0, "inc": 30.0, "azi": 90.0},
    ]
    result = desurvey(
        well_id="TAN-1",
        collar=RTM_ORIGIN,
        survey=survey,
        method="tangential",
        declination_deg=0.0,
        kb_elevation_m=10.0,
    )

    assert result["method"] == "tangential"
    assert result["claim_envelope"]["tag"] == "CLAIM"
    # Tangential slightly underestimates TVD vs minimum curvature
    # (it's the older, simpler method). Should be in same ballpark.
    last = result["rows"][-1]
    assert 800.0 < last["tvd_m"] < 950.0, f"tangential TVD out of expected range, got {last['tvd_m']}"


# ─── Bonus: validation failures ───────────────────────────────────────────
class TestValidationFailures:
    """Failure modes per card §FAILURE MODES."""

    def test_missing_well_id(self):
        with pytest.raises(ValueError, match="well_id required"):
            desurvey("", RTM_ORIGIN, [{"md": 0, "inc": 0, "azi": 0}], "minimum_curvature")

    def test_missing_collar(self):
        with pytest.raises(ValueError, match="collar required"):
            desurvey("X", {}, [{"md": 0, "inc": 0, "azi": 0}], "minimum_curvature")

    def test_insufficient_survey_stations(self):
        with pytest.raises(ValueError, match="≥2 stations"):
            desurvey("X", RTM_ORIGIN, [{"md": 0, "inc": 0, "azi": 0}], "minimum_curvature")

    def test_non_monotonic_survey(self):
        with pytest.raises(ValueError, match="not monotonic"):
            desurvey(
                "X",
                RTM_ORIGIN,
                [
                    {"md": 100.0, "inc": 0, "azi": 0},
                    {"md": 50.0, "inc": 0, "azi": 0},
                ],
                "minimum_curvature",
            )

    def test_unsupported_method(self):
        with pytest.raises(ValueError, match="unsupported method"):
            bad_method: Any = "magic_method"
            desurvey("X", RTM_ORIGIN, [{"md": 0, "inc": 0, "azi": 0}, {"md": 100, "inc": 0, "azi": 0}], bad_method)
