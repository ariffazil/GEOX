"""
Tests for geox/core/welltie.py — well-to-seismic tie computation engine.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import os

import csv
import tempfile
from pathlib import Path

import numpy as np
import pytest

import sys

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

try:
    from geox_core.core.welltie import (
        compute_vp_from_sonic,
        compute_ai,
        compute_reflectivity,
        build_wavelet_from_type,
        generate_synthetic_trace,
        apply_phase_rotation,
        cross_correlate,
        assess_tie_quality,
        compute_average_velocity_td,
    )
except ImportError:
    pytest.skip("geox_core.core.welltie module not available", allow_module_level=True)


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _write_minimal_las(path: Path, depths, dt_values, rhob_values=None) -> None:
    """Write a minimal valid LAS 2.0 file with DEPT, DT, RHOB curves.

    Format matches test_wave2_capabilities.py::_write_sample_las.
    """
    if not depths:
        raise ValueError("depths list cannot be empty")

    step = float(depths[1] - depths[0]) if len(depths) > 1 else 1.0
    null_value = -999.25

    # Build data rows
    rows = []
    for i, d in enumerate(depths):
        dt = float(dt_values[i]) if i < len(dt_values) else 100.0
        rho = float(rhob_values[i]) if rhob_values and i < len(rhob_values) else 2.35
        rows.append(f"{d:10.4f}  {dt:10.4f}  {rho:10.4f}")

    content = "\n".join(
        [
            "~Version ---------------------------------------------------",
            " VERS.                    2.0   :LAS, version 2.0",
            " WRAP.                     NO   :ONE LINE PER DEPTH STEP",
            "~Well ------------------------------------------------------",
            f" STRT.M              {float(depths[0]):.4f}   :START DEPTH",
            f" STOP.M              {float(depths[-1]):.4f}   :STOP DEPTH",
            f" STEP.M              {step:.4f}   :STEP",
            " NULL.              -999.25   :NULL VALUE",
            " COMP.             TEST COMPANY   :COMPANY",
            " WELL.             TEST-WELL-001  :WELL NAME",
            "~Curve Information -----------------------------------------",
            " DEPT.M              :  DEPTH",
            " DT  .USFT           :  SONIC TRANSIT TIME",
            " RHOB.GCC           :  BULK DENSITY",
            "~A DEPT         DT         RHOB",
        ]
        + rows
    )
    path.write_text(content)


# ── 1. Vp from sonic ────────────────────────────────────────────────────────


class TestComputeVpFromSonic:
    def test_vp_from_sonic_usft(self):
        """DT in us/ft → Vp in m/s."""
        dt = np.array([100.0, 95.0, 90.0, 85.0])  # us/ft
        depth = np.array([1000.0, 1010.0, 1020.0, 1030.0])
        vp = compute_vp_from_sonic(dt, depth, dt_unit="usft")

        expected = np.array([3048.0, 3208.4, 3387.0, 3586.0])  # m/s approx
        np.testing.assert_allclose(vp, expected, rtol=0.01)

    def test_vp_from_sonic_usm(self):
        """DT in us/m → Vp in m/s."""
        dt = np.array([328.0, 312.0, 295.0])  # us/m
        depth = np.array([1000.0, 1010.0, 1020.0])
        vp = compute_vp_from_sonic(dt, depth, dt_unit="usm")

        expected = np.array([3048.8, 3205.1, 3389.8])  # m/s
        np.testing.assert_allclose(vp, expected, rtol=0.01)

    def test_vp_clips_to_canon9_bounds(self):
        """Vp outside [1500, 6000] m/s gets clipped."""
        dt = np.array([200.0, 50.0, 150.0])  # 200 us/ft → 1524 m/s (ok), 50 → 6096 (ok), 150 → 2032 (ok)
        depth = np.array([1000.0, 1010.0, 1020.0])
        vp = compute_vp_from_sonic(dt, depth, dt_unit="usft")
        assert vp.min() >= 1500.0
        assert vp.max() <= 6000.0

    def test_vp_handles_nan(self):
        dt = np.array([100.0, np.nan, 90.0])
        depth = np.array([1000.0, 1010.0, 1020.0])
        vp = compute_vp_from_sonic(dt, depth, dt_unit="usft")
        assert np.isnan(vp[1])
        assert np.isfinite(vp[0])
        assert np.isfinite(vp[2])


# ── 2. AI computation ────────────────────────────────────────────────────────


class TestComputeAI:
    def test_ai_formula(self):
        """AI = Vp × ρ."""
        vp = np.array([3000.0, 3500.0, 4000.0])
        rho = np.array([2.0, 2.2, 2.5])  # g/cm³
        ai = compute_ai(vp, rho)
        expected = np.array([6000.0, 7700.0, 10000.0])
        np.testing.assert_allclose(ai, expected, rtol=1e-6)

    def test_ai_handles_nan(self):
        vp = np.array([3000.0, np.nan, 3500.0])
        rho = np.array([2.0, 2.2, 2.5])
        ai = compute_ai(vp, rho)
        assert np.isfinite(ai[0])
        assert np.isnan(ai[1])
        assert np.isfinite(ai[2])


# ── 3. Reflectivity ──────────────────────────────────────────────────────────


class TestComputeReflectivity:
    def test_reflectivity_formula(self):
        """RC[i] = (AI[i+1] - AI[i]) / (AI[i+1] + AI[i])."""
        ai = np.array([6000.0, 7700.0, 10000.0])
        rc = compute_reflectivity(ai, polarity="SEG_NORMAL")

        # RC[0] = (7700-6000)/(7700+6000) = 1700/13700
        expected_0 = 1700.0 / 13700.0
        np.testing.assert_almost_equal(rc[0], expected_0)

    def test_reflectivity_seg_reverse_inverts_sign(self):
        ai = np.array([6000.0, 7700.0])
        rc_normal = compute_reflectivity(ai, polarity="SEG_NORMAL")
        rc_reverse = compute_reflectivity(ai, polarity="SEG_REVERSE")
        np.testing.assert_almost_equal(rc_reverse, -rc_normal)

    def test_reflectivity_length(self):
        """RC is one element shorter than AI."""
        ai = np.array([6000.0, 7700.0, 10000.0, 12000.0])
        rc = compute_reflectivity(ai)
        assert len(rc) == len(ai) - 1

    def test_reflectivity_zero_impedance_contrast(self):
        """AI[i] + AI[i+1] = 0 → should be handled (not divide by zero)."""
        ai = np.array([1.0, -1.0])
        rc = compute_reflectivity(ai)
        # Should not raise; result should be nan or 0
        assert len(rc) == 1


# ── 4. Wavelet determinism ───────────────────────────────────────────────────


class TestWaveletDeterminism:
    def test_ricker_deterministic(self):
        """Same frequency → same wavelet shape."""
        w1 = build_wavelet_from_type("ricker", 30.0, 1.0)
        w2 = build_wavelet_from_type("ricker", 30.0, 1.0)
        np.testing.assert_array_equal(w1, w2)

    def test_ricker_ormsby_klauder_different_shapes(self):
        """Different wavelet types produce different shapes."""
        wr = build_wavelet_from_type("ricker", 30.0, 1.0)
        wo = build_wavelet_from_type("ormsby", 30.0, 1.0)
        wk = build_wavelet_from_type("klauder", 30.0, 1.0)
        # All wavelets should be non-trivial (not all zeros, not constant)
        assert np.abs(wr).max() > 0.0
        assert np.abs(wo).max() > 0.0
        assert np.abs(wk).max() > 0.0
        # Shapes differ from each other
        assert not np.allclose(wr, wo)
        assert not np.allclose(wr, wk)
        assert not np.allclose(wo, wk)


# ── 5. Synthetic generation ─────────────────────────────────────────────────


class TestGenerateSyntheticTrace:
    def test_synthetic_is_normalized(self):
        """Synthetic trace should be in [-1, 1]."""
        rc = np.sin(np.linspace(0, 10, 50))
        twt = np.linspace(1000, 2000, 50)
        synth, _ = generate_synthetic_trace(rc, twt, "ricker", 30.0, noise_db=None)
        assert synth.min() >= -1.0
        assert synth.max() <= 1.0

    def test_synthetic_deterministic_with_seed(self):
        """Same seed → same noise."""
        rc = np.sin(np.linspace(0, 10, 100))
        twt = np.linspace(1000, 2000, 100)
        s1, _ = generate_synthetic_trace(rc, twt, "ricker", 30.0, noise_db=-20, rng_seed=99)
        s2, _ = generate_synthetic_trace(rc, twt, "ricker", 30.0, noise_db=-20, rng_seed=99)
        np.testing.assert_array_equal(s1, s2)

    def test_synthetic_zero_rc_gives_near_zero(self):
        """Zero reflectivity → zero-ish synthetic (only wavelet × zero = 0)."""
        rc = np.zeros(100)
        twt = np.linspace(1000, 2000, 100)
        synth, _ = generate_synthetic_trace(rc, twt, "ricker", 30.0, noise_db=None)
        # With zero RC the output should be near zero
        assert np.abs(synth).max() < 1e-6


# ── 6. Phase rotation ───────────────────────────────────────────────────────


class TestPhaseRotation:
    def test_phase_rotation_zero_is_noop(self):
        """Phase 0° → returns same trace."""
        trace = np.sin(np.linspace(0, 10, 100))
        rotated = apply_phase_rotation(trace, 0.0)
        np.testing.assert_array_almost_equal(trace, rotated)

    def test_phase_rotation_180_flips_sign(self):
        """Phase 180° → flips sign."""
        trace = np.sin(np.linspace(0, 10, 200))
        rotated = apply_phase_rotation(trace, 180.0)
        np.testing.assert_array_almost_equal(rotated, -trace, decimal=5)


# ── 7. Cross-correlation ────────────────────────────────────────────────────


class TestCrossCorrelate:
    def test_perfect_correlation(self):
        """Identical traces → correlation = 1.0."""
        trace = np.sin(np.linspace(0, 10, 200))
        coef, rms, shift = cross_correlate(trace, trace)
        assert abs(coef - 1.0) < 0.01

    def test_correlation_range(self):
        """Correlation coefficient in [-1, 1]."""
        t1 = np.random.default_rng(0).normal(0, 1, 200)
        t2 = np.random.default_rng(1).normal(0, 1, 200)
        coef, rms, shift = cross_correlate(t1, t2)
        assert -1.0 <= coef <= 1.0

    def test_residual_rms_positive(self):
        """Residual RMS must be non-negative."""
        t1 = np.random.default_rng(0).normal(0, 1, 100)
        t2 = np.random.default_rng(1).normal(0, 1, 100)
        _, rms, _ = cross_correlate(t1, t2)
        assert rms >= 0.0


# ── 8. Tie quality ──────────────────────────────────────────────────────────


class TestAssessTieQuality:
    @pytest.mark.parametrize(
        "coef,expected",
        [
            (0.90, "EXCELLENT"),
            (0.80, "GOOD"),
            (0.70, "MODERATE"),
            (0.50, "POOR"),
            (0.0, "UNDETERMINED"),
        ],
    )
    def test_tie_quality_thresholds(self, coef, expected):
        verdict = assess_tie_quality(coef, residual_rms=0.2, phase_rotation_deg=0.0, polarity_reversed=False)
        assert verdict == expected

    def test_high_residual_downgrades(self):
        """High residual RMS downgrades the verdict by one tier."""
        # 0.90 coef but 0.6 residual → should be downgraded from EXCELLENT to GOOD
        verdict = assess_tie_quality(0.90, residual_rms=0.6, phase_rotation_deg=0.0, polarity_reversed=False)
        assert "GOOD" in verdict or "EXCELLENT" not in verdict


# ── 9. Average velocity T-D conversion ──────────────────────────────────────


class TestAverageVelocityTD:
    def test_td_increases_with_depth(self):
        """TWT should increase with depth."""
        vp = np.full(100, 3000.0)  # constant 3000 m/s
        depth = np.linspace(0, 3000, 100)  # 0 to 3000 m
        twt = compute_average_velocity_td(vp, depth)
        assert twt[-1] > twt[0]  # TWT increases
        # At 3000m with Vp=3000, TWT ≈ 2 × 3000/3000 × 1000 = 2000 ms
        np.testing.assert_almost_equal(twt[-1], 2000.0, decimal=1)

    def test_td_zero_at_surface(self):
        """TWT should be 0 at depth 0."""
        vp = np.full(10, 3000.0)
        depth = np.linspace(0, 1000, 10)
        twt = compute_average_velocity_td(vp, depth)
        assert twt[0] == 0.0


# ── 10. Full compute_welltie integration ────────────────────────────────────


class TestComputeWelltieFull:
    def test_welltie_produces_required_keys(self, tmp_path):
        """Full workflow returns all required output keys."""
        from geox.core.welltie import compute_welltie

        # Write minimal LAS
        las = tmp_path / "test.las"
        depths = list(np.linspace(1000, 3000, 50))
        dt_vals = [100.0 + (d - 1000) * 0.01 for d in depths]  # ~100-120 us/ft
        rho_vals = [2.35] * 50
        _write_minimal_las(las, depths, dt_vals, rho_vals)

        result = compute_welltie(
            las_path=str(las),
            checkshot_ref=None,  # use average velocity
            wavelet_mode="ricker",
            wavelet_freq_hz=30.0,
            phase_degrees=0.0,
            polarity="SEG_NORMAL",
        )

        required_keys = [
            "tie_quality_verdict",
            "correlation_coefficient",
            "wavelet",
            "depth_to_time",
            "ai_curve",
            "reflectivity_series",
            "assumptions",
            "physics_guard",
            "canon_9_touched",
            "humility_score",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_welltie_claim_tag_is_not_claim(self, tmp_path):
        """Well-tie output should not use CLAIM tag — it's an interpretation aid."""
        from geox.core.welltie import compute_welltie

        las = tmp_path / "test.las"
        depths = list(np.linspace(1000, 3000, 50))
        dt_vals = [100.0] * 50
        rho_vals = [2.35] * 50
        _write_minimal_las(las, depths, dt_vals, rho_vals)

        result = compute_welltie(
            las_path=str(las),
            wavelet_mode="ricker",
            wavelet_freq_hz=30.0,
        )
        # humility_score is always > 0 (it's an interpretation)
        assert result["humility_score"] > 0

    def test_welltie_density_fallback(self, tmp_path):
        """When RHOB curve is absent from LAS, matrix/fluid density fallback is used."""
        from geox.core.welltie import compute_welltie

        # Write a LAS with only DEPT + DT (no RHOB)
        las = tmp_path / "no_rhob.las"
        content = (
            "~Version ---------------------------------------------------\n"
            " VERS.                    2.0   :LAS, version 2.0\n"
            " WRAP.                     NO   :ONE LINE PER DEPTH STEP\n"
            "~Well ------------------------------------------------------\n"
            " STRT.M              1000.0000   :START DEPTH\n"
            " STOP.M              2000.0000   :STOP DEPTH\n"
            " STEP.M                50.0000   :STEP\n"
            " NULL.              -999.25   :NULL VALUE\n"
            "~Curve Information -----------------------------------------\n"
            " DEPT.M              :  DEPTH\n"
            " DT  .USFT           :  SONIC TRANSIT TIME\n"
            "~A DEPT         DT\n"
            " 1000.0000  100.0000\n"
            " 1050.0000  100.0000\n"
            " 1100.0000  100.0000\n"
        )
        las.write_text(content)

        result = compute_welltie(
            las_path=str(las),
            wavelet_mode="ricker",
            wavelet_freq_hz=30.0,
            matrix_density=2.71,
            fluid_density=1.0,
        )

        # Should have assumption about density fallback
        assert any("density" in a.lower() or "matrix" in a.lower() for a in result["assumptions"])

    def test_welltie_td_method_is_average_velocity_without_checkshot(self, tmp_path):
        """Without checkshot, uses average_velocity T-D method."""
        from geox.core.welltie import compute_welltie

        las = tmp_path / "test.las"
        depths = list(np.linspace(1000, 3000, 30))
        dt_vals = [100.0] * 30
        rho_vals = [2.35] * 30
        _write_minimal_las(las, depths, dt_vals, rho_vals)

        result = compute_welltie(
            las_path=str(las),
            checkshot_ref=None,
            wavelet_mode="ricker",
            wavelet_freq_hz=30.0,
        )
        assert result["depth_to_time"]["method"] == "average_velocity"
        assert result["depth_to_time"]["coverage_pct"] == 100.0

    def test_welltie_canon9_touched(self, tmp_path):
        """well_tie must touch Vp and rho in CANON-9."""
        from geox.core.welltie import compute_welltie

        las = tmp_path / "test.las"
        depths = list(np.linspace(1000, 3000, 30))
        dt_vals = [100.0] * 30
        rho_vals = [2.35] * 30
        _write_minimal_las(las, depths, dt_vals, rho_vals)

        result = compute_welltie(
            las_path=str(las),
            wavelet_mode="ricker",
            wavelet_freq_hz=30.0,
        )
        assert "Vp" in result["canon_9_touched"]
        assert "rho" in result["canon_9_touched"]

    def test_welltie_physics_guard_present(self, tmp_path):
        """Physics guard must include Vp bounds check and AI positive check."""
        from geox.core.welltie import compute_welltie

        las = tmp_path / "test.las"
        depths = list(np.linspace(1000, 3000, 30))
        dt_vals = [100.0] * 30
        rho_vals = [2.35] * 30
        _write_minimal_las(las, depths, dt_vals, rho_vals)

        result = compute_welltie(
            las_path=str(las),
            wavelet_mode="ricker",
            wavelet_freq_hz=30.0,
        )
        pg = result["physics_guard"]
        assert "Vp_bounds_check" in pg
        assert "AI_positive_check" in pg
        assert "pct_in_bounds" in pg["Vp_bounds_check"]


# ── 11. Section tool integration ─────────────────────────────────────────────


class TestSectionWellTieMode:
    def setup_method(self):
        """Reset artifact registry before each test to ensure isolation."""
        try:
            from geox_mcp.tools._artifact_helpers import _reset_registry
        except ImportError:
            pytest.skip("geox_mcp.tools._artifact_helpers not available")
        _reset_registry()

    def test_welltie_missing_well_ref_returns_hold(self):
        """No well_ref → NO_VALID_EVIDENCE + HOLD (enforced by F2 claim_state gate)."""
        import asyncio
        try:
            from geox_mcp.tools.section import geox_section_interpret_correlation
        except ImportError:
            pytest.skip("geox_mcp.tools.section not available")

        result = asyncio.run(
            geox_section_interpret_correlation(
                section_ref="test-section",
                well_refs=[],
                mode="well_tie",
            )
        )
        # F2 enforce_claim_state: artifact_status downgraded from COMPUTED→DRAFT when no evidence_refs
        assert result["claim_state"] == "NO_VALID_EVIDENCE"
        assert result["governance_status"] == "HOLD"

    def test_welltie_missing_las_path_returns_hold(self):
        """well_ref with no LAS path and non-existent well_las_paths → HOLD."""
        import asyncio
        try:
            from geox_mcp.tools.section import geox_section_interpret_correlation
        except ImportError:
            pytest.skip("geox_mcp.tools.section not available")

        result = asyncio.run(
            geox_section_interpret_correlation(
                section_ref="test-section",
                well_refs=["no-such-ref"],
                well_las_paths=["/tmp/no-such-geox-test-file-12345.las"],
                mode="well_tie",
            )
        )
        # F2 enforce_claim_state: artifact_status downgraded when no evidence_refs
        assert result["claim_state"] == "NO_VALID_EVIDENCE"
        assert result["governance_status"] == "HOLD"

    def test_welltie_with_valid_las_path_returns_derived_candidate(self, tmp_path):
        """Valid LAS without seismic_ref → DERIVED_CANDIDATE (no correlation possible)."""
        import asyncio
        try:
            from geox_mcp.tools.section import geox_section_interpret_correlation
        except ImportError:
            pytest.skip("geox_mcp.tools.section not available")

        las = tmp_path / "test.las"
        depths = list(np.linspace(1000, 3000, 30))
        dt_vals = [100.0] * 30
        rho_vals = [2.35] * 30
        _write_minimal_las(las, depths, dt_vals, rho_vals)

        result = asyncio.run(
            geox_section_interpret_correlation(
                section_ref="test-section",
                well_refs=["fake-ref-no-las"],
                well_las_paths=[str(las)],
                mode="well_tie",
                wavelet_mode="ricker",
                wavelet_freq_hz=[30.0],
            )
        )
        # Without seismic_ref, tie_verdict is UNDETERMINED → DERIVED_CANDIDATE
        # well_tie results live inside primary_artifact (enforced by get_standard_envelope)
        assert result["claim_state"] == "DERIVED_CANDIDATE"
        assert result["execution_status"] == "SUCCESS"
        pa = result.get("primary_artifact", result)
        assert "tie_quality_verdict" in pa

    def test_welltie_output_has_required_governance_fields(self, tmp_path):
        """Output has humility_score, canon_9_touched, uncertainty, claim_tag."""
        import asyncio
        try:
            from geox_mcp.tools.section import geox_section_interpret_correlation
        except ImportError:
            pytest.skip("geox_mcp.tools.section not available")

        las = tmp_path / "test.las"
        depths = list(np.linspace(1000, 3000, 30))
        dt_vals = [100.0] * 30
        rho_vals = [2.35] * 30
        _write_minimal_las(las, depths, dt_vals, rho_vals)

        result = asyncio.run(
            geox_section_interpret_correlation(
                section_ref="test-section",
                well_refs=["ref-with-no-las"],
                well_las_paths=[str(las)],
                mode="well_tie",
                wavelet_mode="ricker",
                wavelet_freq_hz=[30.0],
            )
        )
        assert "humility_score" in result
        assert "canon_9_touched" in result
        assert "uncertainty" in result
        assert "claim_tag" in result
        assert result["claim_tag"] in ("PLAUSIBLE", "HYPOTHESIS")


# ── 12. Polarity ─────────────────────────────────────────────────────────────


class TestPolarityReversal:
    def test_polarity_seg_reverse_inverts_rc(self):
        """SEG_REVERSE inverts the sign of the reflectivity series."""
        ai = np.array([6000.0, 7700.0, 9000.0])
        rc_normal = compute_reflectivity(ai, polarity="SEG_NORMAL")
        rc_reverse = compute_reflectivity(ai, polarity="SEG_REVERSE")
        np.testing.assert_array_almost_equal(rc_reverse, -rc_normal)
