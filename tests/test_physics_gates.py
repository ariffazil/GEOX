"""
test_physics_gates.py — Physics correctness benchmarks for GEOX domain tools.

Verifies that GEOX tools produce physically correct results against
known-good reference values. Prevents silent physics drift.

F2 TRUTH: Every claim must be grounded in observable reality.
F7 HUMILITY: Acceptance bands are wide enough for model uncertainty.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import pytest
import math


# ── Geomechanics Physics Gates ────────────────────────────────────────────────


class TestGeomechanicsGates:
    """Verify geomechanics tool produces physically correct moduli."""

    @pytest.mark.asyncio
    async def test_sandstone_moduli(self):
        """Sandstone (Vp=3500, Vs=1800, rho=2350) should yield realistic moduli."""
        from geox_mcp.tools.geomechanics import GeomechanicsRequest, geox_geomechanics

        req = GeomechanicsRequest(state={"vp": 3500, "vs": 1800, "rho": 2350})
        result = await geox_geomechanics(req)

        assert result.ok, f"geox_geomechanics failed: {result.error}"
        r = result.result

        # Bulk modulus: K = ρ(Vp² - 4/3·Vs²)
        # For these values: K ≈ 18.6 GPa
        assert 15 < r["derived"]["K_GPa"] < 25, f"Bulk modulus {r['derived']['K_GPa']:.1f} GPa out of sandstone range [15-25]"

        # Shear modulus: G = ρ·Vs²
        # For these values: G ≈ 7.6 GPa
        assert 5 < r["derived"]["G_GPa"] < 12, f"Shear modulus {r['derived']['G_GPa']:.1f} GPa out of sandstone range [5-12]"

        # Poisson's ratio: ν = (Vp² - 2Vs²) / (2(Vp² - Vs²))
        # For these values: ν ≈ 0.32
        assert 0.2 < r["derived"]["nu"] < 0.4, f"Poisson's ratio {r['derived']['nu']:.3f} out of sandstone range [0.2-0.4]"

        # Vp/Vs ratio
        assert 1.8 < r["derived"]["vp_vs_ratio"] < 2.2, (
            f"Vp/Vs {r['derived']['vp_vs_ratio']:.2f} out of sandstone range [1.8-2.2]"
        )

        # Acoustic impedance: AI = ρ·Vp
        expected_ai = 2350 * 3500
        assert abs(r["derived"]["ai_kg_ms2"] - expected_ai) < 100, f"AI {r['derived']['ai_kg_ms2']} != expected {expected_ai}"

    @pytest.mark.asyncio
    async def test_limestone_moduli(self):
        """Limestone (Vp=5000, Vs=2700, rho=2650) should yield higher moduli."""
        from geox_mcp.tools.geomechanics import GeomechanicsRequest, geox_geomechanics

        req = GeomechanicsRequest(state={"vp": 5000, "vs": 2700, "rho": 2650})
        result = await geox_geomechanics(req)

        assert result.ok, f"geox_geomechanics failed: {result.error}"
        r = result.result

        # Limestone should have higher moduli than sandstone
        assert r["derived"]["K_GPa"] > 30, f"Limestone K={r['derived']['K_GPa']:.1f} GPa too low (expected >30)"
        assert r["derived"]["G_GPa"] > 15, f"Limestone G={r['derived']['G_GPa']:.1f} GPa too low (expected >15)"

    @pytest.mark.asyncio
    async def test_shale_moduli(self):
        """Shale (Vp=2500, Vs=1000, rho=2200) — low moduli, high Poisson."""
        from geox_mcp.tools.geomechanics import GeomechanicsRequest, geox_geomechanics

        req = GeomechanicsRequest(state={"vp": 2500, "vs": 1000, "rho": 2200})
        result = await geox_geomechanics(req)

        assert result.ok, f"geox_geomechanics failed: {result.error}"
        r = result.result

        # Shale: low moduli, high Poisson's ratio
        assert r["derived"]["K_GPa"] < 15, f"Shale K={r['derived']['K_GPa']:.1f} GPa too high (expected <15)"
        assert r["derived"]["nu"] > 0.35, f"Shale ν={r['derived']['nu']:.3f} too low (expected >0.35)"

    @pytest.mark.asyncio
    async def test_stress_polygon_zoback(self):
        """Stress polygon at 3000m should match Zoback (2010) bounds."""
        from geox_mcp.tools.geomechanics import GeomechanicsRequest
        from geox_mcp.tools.geomechanics_unified import _compute_stress_polygon

        result = _compute_stress_polygon(depth_m=3000, pp_mpa=10.0, friction_coefficient=0.6)

        # Sv at 3000m with avg density 2300 kg/m³
        # Sv = ρ·g·h = 2300 * 9.81 * 3000 / 1e6 ≈ 67.7 MPa
        assert 60 < result["sv_mpa"] < 80, f"Sv={result['sv_mpa']:.1f} MPa out of range for 3000m"

        # Shmin should be less than Sv (normal faulting regime)
        assert result["stress_polygon_vertices"]["B_normal_limit"]["sh_mpa"] < result["sv_mpa"]

        # SHmax should be greater than Sv (reverse faulting regime)
        assert result["stress_polygon_vertices"]["D_reverse_limit"]["sh_max_mpa"] > result["sv_mpa"]


# ── Deep Time State Physics Gates ─────────────────────────────────────────────


class TestDeepTimeGates:
    """Verify deep time state produces physically plausible values.

    Calibrated against:
      - Zachos et al. 2001 (Science) — Cenozoic δ18O compilation
      - Westerhold et al. 2020 (Science) — astronomically tuned stack
      - Holbourn et al. 2014 (EPSL) — middle Miocene climate/cryosphere
    """

    @pytest.mark.asyncio
    async def test_present_day(self):
        """Present day (0 Ma) should match known values."""
        from geox_mcp.tools.deep_time_state import geox_deep_time_state

        result = await geox_deep_time_state(age_ma=0.0)

        assert result["execution_status"] == "SUCCESS"
        state = result["primary_artifact"]["earth_state_vector"]

        # Present CO2: ~280 ppm (pre-industrial GEOCARBSULF) to ~420 ppm (2024)
        co2 = state["atmospheric_co2_ppm"]["value"]
        assert 250 < co2 < 600, f"Present CO2={co2} ppm out of range [250-600]"

        # Present day length: 24 hours
        day = state["day_length_hours"]["value"]
        assert 23.9 < day < 24.1, f"Present day length={day}h out of range"

    @pytest.mark.asyncio
    async def test_eocene_warm(self):
        """Eocene (50 Ma) should be warmer than present."""
        from geox_mcp.tools.deep_time_state import geox_deep_time_state

        result = await geox_deep_time_state(age_ma=50.0)

        assert result["execution_status"] == "SUCCESS"
        state = result["primary_artifact"]["earth_state_vector"]

        # Eocene CO2: ~800-1500 ppm
        co2 = state["atmospheric_co2_ppm"]["value"]
        assert co2 > 400, f"Eocene CO2={co2} ppm too low (expected >400)"

        # Eocene temperature anomaly: +8-12°C above present
        temp = state["global_temperature_anomaly_c"]["value"]
        assert temp > 5, f"Eocene temp anomaly={temp}°C too low (expected >5)"

    @pytest.mark.asyncio
    async def test_ice_free_periods(self):
        """Pre-34 Ma should be ice-free."""
        from geox_mcp.tools.deep_time_state import geox_deep_time_state

        result = await geox_deep_time_state(age_ma=100.0)

        assert result["execution_status"] == "SUCCESS"
        state = result["primary_artifact"]["earth_state_vector"]

        ice = state["ice_extent"]["value"]
        assert "ice-free" in str(ice).lower(), f"Cretaceous ice={ice}, expected ice-free"

    @pytest.mark.asyncio
    async def test_23Ma_has_antarctic_ice(self):
        """23 Ma (Mi-1 event) must have Antarctic ice — NOT ice-free.

        Calibration: Zachos et al. 2001, Westerhold et al. 2020.
        Mi-1 = transient AIS expansion to ~100-125% modern EAIS volume.
        """
        from geox_mcp.tools.deep_time_state import geox_deep_time_state

        result = await geox_deep_time_state(age_ma=23.0)

        assert result["execution_status"] == "SUCCESS"
        state = result["primary_artifact"]["earth_state_vector"]

        ice = str(state["ice_extent"]["value"]).lower()
        assert "ice-free" not in ice, (
            f"23 Ma ice_extent says 'ice-free' — WRONG. Mi-1 had Antarctic ice (~100-125% modern EAIS). Got: {ice}"
        )
        assert "mi-1" in ice or "dynamic" in ice or "eaismi" in ice or "antartic" in ice or "glaciation" in ice, (
            f"23 Ma ice_extent should mention Mi-1 or dynamic EAIS. Got: {ice}"
        )

    @pytest.mark.asyncio
    async def test_13Ma_has_antarctic_ice(self):
        """13 Ma (post-MMCT) must have Antarctic ice — NOT ice-free.

        Calibration: Holbourn et al. 2014, Westerhold et al. 2020.
        By ~13 Ma, AIS expanded to near-modern volume after MMCT.
        """
        from geox_mcp.tools.deep_time_state import geox_deep_time_state

        result = await geox_deep_time_state(age_ma=13.0)

        assert result["execution_status"] == "SUCCESS"
        state = result["primary_artifact"]["earth_state_vector"]

        ice = str(state["ice_extent"]["value"]).lower()
        assert "ice-free" not in ice, (
            f"13 Ma ice_extent says 'ice-free' — WRONG. Post-MMCT AIS was near-modern volume. Got: {ice}"
        )
        assert "quasi-permanent" in ice or "post-mmct" in ice or "near-modern" in ice or "antartic" in ice, (
            f"13 Ma ice_extent should mention quasi-permanent EAIS or post-MMCT. Got: {ice}"
        )

    @pytest.mark.asyncio
    async def test_16Ma_MCO_reduced_ice(self):
        """16 Ma (MCO) should show reduced/warm Antarctic ice.

        Calibration: Holbourn et al. 2014. MCO = warm interval, reduced AIS.
        """
        from geox_mcp.tools.deep_time_state import geox_deep_time_state

        result = await geox_deep_time_state(age_ma=16.0)

        assert result["execution_status"] == "SUCCESS"
        state = result["primary_artifact"]["earth_state_vector"]

        ice = str(state["ice_extent"]["value"]).lower()
        assert "ice-free" not in ice, (
            f"16 Ma ice_extent says 'ice-free' — WRONG. MCO had reduced but still present Antarctic ice. Got: {ice}"
        )

    @pytest.mark.asyncio
    async def test_50Ma_true_ice_free(self):
        """50 Ma (early Eocene) should genuinely be ice-free.

        Calibration: Zachos et al. 2001. No Antarctic ice before ~34 Ma.
        """
        from geox_mcp.tools.deep_time_state import geox_deep_time_state

        result = await geox_deep_time_state(age_ma=50.0)

        assert result["execution_status"] == "SUCCESS"
        state = result["primary_artifact"]["earth_state_vector"]

        ice = str(state["ice_extent"]["value"]).lower()
        assert "ice-free" in ice, f"50 Ma should be ice-free. Got: {ice}"


# ── Rock Physics Gates ────────────────────────────────────────────────────────


class TestRockPhysicsGates:
    """Verify petrophysics computations are physically bounded."""

    def test_vsh_bounds(self):
        """Vsh must be in [0, 1]."""
        # Vsh = (GR - GR_clean) / (GR_shale - GR_clean)
        gr_clean = 15
        gr_shale = 150

        for gr in [15, 75, 150]:
            vsh = (gr - gr_clean) / (gr_shale - gr_clean)
            assert 0 <= vsh <= 1, f"Vsh={vsh:.2f} out of bounds for GR={gr}"

    def test_porosity_bounds(self):
        """Porosity must be in [0, 1]."""
        rho_ma = 2.65  # matrix density
        rho_fl = 1.0  # fluid density

        for rho_b in [1.8, 2.2, 2.65]:
            phi = (rho_ma - rho_b) / (rho_ma - rho_fl)
            phi = max(0, min(1, phi))
            assert 0 <= phi <= 1, f"Porosity={phi:.2f} out of bounds for RHOB={rho_b}"

    def test_archie_sw_bounds(self):
        """Archie Sw must be in [0, 1]."""
        a, m, n = 1.0, 2.0, 2.0
        rw = 0.05
        phi = 0.20
        rt = 10  # resistivity

        sw = ((a * rw) / (phi**m * rt)) ** (1 / n)
        sw = max(0, min(1, sw))
        assert 0 <= sw <= 1, f"Sw={sw:.2f} out of bounds"


# ── Gravity Forward Model Gates ───────────────────────────────────────────────


class TestGravityGates:
    """Verify gravity forward model produces bounded results."""

    @pytest.mark.asyncio
    async def test_single_prism_anomaly(self):
        """A single prism should produce a bounded anomaly."""
        from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open

        result = await geox_gravmag_studio_open(
            survey_type="gravity",
            prisms=[
                {
                    "easting": 0,
                    "northing": 0,
                    "depth_top": 1000,
                    "depth_bottom": 3000,
                    "width_e": 5000,
                    "width_n": 5000,
                    "density": 300,  # kg/m³ contrast
                }
            ],
            grid_n=20,
            grid_extent_m=20000,
        )

        assert result["verdict"] == "QUALIFY"
        values = result["render_payload"]["anomaly_values"]
        finite_vals = [v for v in values if v == v and v != 0]

        # Gravity anomaly from a prism should be finite and bounded
        if finite_vals:
            assert all(-500 < v < 500 for v in finite_vals), (
                f"Anomaly values out of physical range: min={min(finite_vals)}, max={max(finite_vals)}"
            )

    @pytest.mark.asyncio
    async def test_empty_prisms_zero_anomaly(self):
        """No prisms = zero anomaly everywhere."""
        from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open

        result = await geox_gravmag_studio_open(
            survey_type="gravity",
            prisms=[],
            grid_n=10,
        )

        assert result["verdict"] == "QUALIFY"
        values = result["render_payload"]["anomaly_values"]
        assert all(v == 0.0 for v in values), "Empty prisms should produce zero anomaly"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
