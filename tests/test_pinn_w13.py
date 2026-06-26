"""Tests for W13+ Phase C — PINN seismic inversion."""

from __future__ import annotations

import math

import pytest

from geox_core.seismic.pinn_inversion import (
    SeismicInversionRequest,
    pinn_invert,
    recursive_impedance,
)


class TestRecursiveImpedance:
    def test_zero_reflectivity_returns_constant(self):
        import numpy as np
        r = np.zeros(10)
        ai = recursive_impedance(r, 5e6)
        assert len(ai) == 11
        assert all(math.isclose(v, 5e6, rel_tol=1e-9) for v in ai)

    def test_positive_reflectivity_increases_impedance(self):
        import numpy as np
        r = np.full(5, 0.1)  # R = +0.1 every interface
        ai = recursive_impedance(r, 1e6)
        # Each step: AI' = AI · (1+0.1)/(1-0.1) = AI · 1.222
        for i in range(1, len(ai)):
            assert ai[i] > ai[i - 1]

    def test_r_near_one_does_not_blow_up(self):
        import numpy as np
        r = np.array([0.99])
        ai = recursive_impedance(r, 1e6)
        assert math.isfinite(ai[1])


class TestPinnInvert:
    def test_empty_reflectivity_returns_error(self):
        r = pinn_invert(SeismicInversionRequest(reflectivity=()))
        assert r["ok"] is False

    def test_constant_reflectivity_produces_smooth_profile(self):
        reflectivity = (0.05, 0.05, 0.05, 0.05)
        r = pinn_invert(SeismicInversionRequest(reflectivity=reflectivity))
        assert r["ok"] is True
        assert len(r["ai_kg_ms2"]) == 5
        # PINN constraint: Vp clipped to bounds, density from Gardner
        for vp in r["vp_m_s"]:
            assert 1500 <= vp <= 6000
        for rho in r["rho_kg_m3"]:
            assert 1000 <= rho <= 5000

    def test_impedance_hash_deterministic(self):
        reflectivity = (0.01, 0.02, 0.01)
        r1 = pinn_invert(SeismicInversionRequest(reflectivity=reflectivity))
        r2 = pinn_invert(SeismicInversionRequest(reflectivity=reflectivity))
        assert r1["impedance_hash"] == r2["impedance_hash"]

    def test_with_resistivity_uses_faust(self):
        # Resistivity profile that should push Faust velocity higher at depth
        resistivity = (5.0, 8.0, 12.0, 18.0, 25.0)
        reflectivity = (0.02, 0.03, 0.02, 0.01)
        r = pinn_invert(SeismicInversionRequest(
            reflectivity=reflectivity,
            resistivity_ohm_m=resistivity,
            depth_top_m=1000.0,
        ))
        assert r["ok"] is True
        # VP should increase with depth (Faust trend)
        vps = r["vp_m_s"]
        assert vps[-1] >= vps[0]  # weakly monotonically non-decreasing

    def test_residual_rms_bounded(self):
        r = pinn_invert(SeismicInversionRequest(reflectivity=(0.1, 0.1, 0.1)))
        assert 0.0 <= r["residual_rms"] < 1.0

    def test_godel_wall_known(self):
        r = pinn_invert(SeismicInversionRequest(reflectivity=(0.05, 0.05)))
        assert r["godel_wall"]["state"] == "KNOWN"
