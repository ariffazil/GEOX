"""
test_deep_time_physics_flow.py — Earth physics flow consistency tests.

The Earth system has causal chains:
  CO2 → temperature → ice → sea level
  High CO2 → warm → low ice → high sea level
  Low CO2 → cold → high ice → low sea level

These tests verify that the deep-time state variables are physically
consistent with each other — not just individually correct.

Calibration sources:
  - Zachos et al. 2001 (Science) — Cenozoic δ18O compilation
  - Westerhold et al. 2020 (Science) — astronomically tuned stack
  - Holbourn et al. 2014 (EPSL) — middle Miocene climate
  - Rae et al. 2021 (AREPS) — CO2 compilation
  - Miller et al. 2020 (Science Advances) — sea level
  - Pekar & DeConto 2006 (USGS) — ice volume

DITEMPA BUKAN DIBERI — Earth physics is forged, not given.
"""

from __future__ import annotations

import pytest


async def _get_state(age_ma: float) -> dict:
    """Helper: get earth state vector at a given age."""
    from geox_mcp.tools.deep_time_state import geox_deep_time_state

    result = await geox_deep_time_state(age_ma=float(age_ma))
    assert result["execution_status"] == "SUCCESS", f"deep_time_state failed at {age_ma} Ma"
    return result["primary_artifact"]["earth_state_vector"]


def _ice_has_ice(ice_str: str) -> bool:
    """True if ice descriptor indicates presence of significant ice."""
    s = ice_str.lower()
    # Negative indicators — these mean ice-free or minimal ice
    if "ice-free" in s:
        return False
    if "no antarctic" in s:
        return False
    if "no polar ice" in s:
        return False
    # Positive indicators — these mean ice present
    positive = [
        "glaciation",
        "ice sheet",
        "eaismi",
        "glacial",
        "ice age",
        "quasi-permanent",
        "mi-1",
        "oi-1",
        "snowball",
        "dynamic",
        "polar",
        "expansion",
        "reduced antarctic",
    ]
    return any(p in s for p in positive)


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS FLOW 1: CO2 ↔ Temperature coupling
# Higher CO2 should correlate with higher temperature (greenhouse effect)
# ══════════════════════════════════════════════════════════════════════════════


class TestCO2TemperatureCoupling:
    """CO2 and temperature should be positively correlated."""

    @pytest.mark.asyncio
    async def test_eocene_high_co2_high_temp(self):
        """50 Ma (early Eocene hothouse): high CO2 + high temperature."""
        state = await _get_state(50.0)
        co2 = state["atmospheric_co2_ppm"]["value"]
        temp = state["global_temperature_anomaly_c"]["value"]
        assert co2 > 500, f"Eocene CO2={co2} too low (expected >500)"
        assert temp > 5, f"Eocene temp anomaly={temp}°C too low (expected >5)"

    @pytest.mark.asyncio
    async def test_pleistocene_low_co2_low_temp(self):
        """0 Ma (pre-industrial): low CO2 + low temperature anomaly."""
        state = await _get_state(0.0)
        co2 = state["atmospheric_co2_ppm"]["value"]
        temp = state["global_temperature_anomaly_c"]["value"]
        assert co2 < 350, f"Pleistocene CO2={co2} too high (expected <350)"
        assert temp < 2, f"Pleistocene temp anomaly={temp}°C too high (expected <2)"

    @pytest.mark.asyncio
    async def test_mco_warm_interval(self):
        """16 Ma (MCO): should be warmer than 13 Ma (post-MMCT)."""
        state_16 = await _get_state(16.0)
        state_13 = await _get_state(13.0)
        temp_16 = state_16["global_temperature_anomaly_c"]["value"]
        temp_13 = state_13["global_temperature_anomaly_c"]["value"]
        # MCO should be warmer than post-MMCT
        assert temp_16 >= temp_13, f"MCO (16 Ma) temp={temp_16}°C should be >= post-MMCT (13 Ma) temp={temp_13}°C"


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS FLOW 2: Temperature ↔ Ice coupling
# Higher temperature should correlate with less ice
# ══════════════════════════════════════════════════════════════════════════════


class TestTemperatureIceCoupling:
    """Temperature and ice should be negatively correlated."""

    @pytest.mark.asyncio
    async def test_eocene_warm_ice_free(self):
        """50 Ma (warm Eocene): should be ice-free."""
        state = await _get_state(50.0)
        temp = state["global_temperature_anomaly_c"]["value"]
        ice = str(state["ice_extent"]["value"])
        assert temp > 5, f"Eocene temp={temp}°C too low"
        assert not _ice_has_ice(ice), f"Eocene should be ice-free. Got: {ice}"

    @pytest.mark.asyncio
    async def test_pleistocene_cold_has_ice(self):
        """0 Ma (cold Pleistocene): should have ice sheets."""
        state = await _get_state(0.0)
        ice = str(state["ice_extent"]["value"])
        assert _ice_has_ice(ice), f"Pleistocene should have ice. Got: {ice}"

    @pytest.mark.asyncio
    async def test_13Ma_cold_has_ice(self):
        """13 Ma (post-MMCT cooling): should have Antarctic ice."""
        state = await _get_state(13.0)
        ice = str(state["ice_extent"]["value"])
        assert _ice_has_ice(ice), f"13 Ma should have ice (post-MMCT). Got: {ice}"


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS FLOW 3: Ice ↔ Sea level coupling
# More ice should correlate with lower sea level (glacial eustasy)
# ══════════════════════════════════════════════════════════════════════════════


class TestIceSeaLevelCoupling:
    """Ice and sea level should be negatively correlated."""

    @pytest.mark.asyncio
    async def test_eocene_ice_free_high_sea_level(self):
        """50 Ma (ice-free): sea level should be higher than present."""
        state = await _get_state(50.0)
        ice = str(state["ice_extent"]["value"])
        sl = state["eustatic_sea_level_m"]["value"]
        assert not _ice_has_ice(ice), f"50 Ma should be ice-free. Got: {ice}"
        # Ice-free world should have higher sea level
        assert sl is None or sl > 0, f"50 Ma sea level={sl} should be >0 in ice-free world"

    @pytest.mark.asyncio
    async def test_pleistocene_has_ice_lower_sea_level(self):
        """0 Ma (glacial): sea level should be lower than Eocene."""
        state_0 = await _get_state(0.0)
        state_50 = await _get_state(50.0)
        sl_0 = state_0["eustatic_sea_level_m"]["value"]
        sl_50 = state_50["eustatic_sea_level_m"]["value"]
        if sl_0 is not None and sl_50 is not None:
            assert sl_50 > sl_0, f"Eocene (50 Ma) sea level={sl_50}m should be > Pleistocene (0 Ma)={sl_0}m"


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS FLOW 4: Boundary transitions
# Key geological boundaries should show step changes
# ══════════════════════════════════════════════════════════════════════════════


class TestBoundaryTransitions:
    """Key geological boundaries should show physically correct transitions."""

    @pytest.mark.asyncio
    async def test_oi1_boundary_at_34Ma(self):
        """Oi-1 (34 Ma): transition from ice-free to glaciated."""
        state_before = await _get_state(35.0)  # ice-free Eocene
        state_after = await _get_state(33.9)  # Oi-1 glaciation
        ice_before = str(state_before["ice_extent"]["value"])
        ice_after = str(state_after["ice_extent"]["value"])
        # Before Oi-1 should be ice-free
        assert not _ice_has_ice(ice_before), f"35 Ma should be ice-free. Got: {ice_before}"
        # After Oi-1 should have ice
        assert _ice_has_ice(ice_after), f"33.9 Ma should have ice (Oi-1). Got: {ice_after}"

    @pytest.mark.asyncio
    async def test_mmct_boundary_at_14Ma(self):
        """MMCT (14 Ma): ice should increase across the transition."""
        state_before = await _get_state(15.0)  # MCO — reduced ice
        state_after = await _get_state(13.0)  # post-MMCT — expanded ice
        ice_before = str(state_before["ice_extent"]["value"])
        ice_after = str(state_after["ice_extent"]["value"])
        # Both should have ice (Antarctic ice existed since 34 Ma)
        assert _ice_has_ice(ice_before), f"15 Ma should have ice. Got: {ice_before}"
        assert _ice_has_ice(ice_after), f"13 Ma should have ice. Got: {ice_after}"
        # Post-MMCT should describe larger/more stable ice
        assert "quasi-permanent" in ice_after.lower() or "near-modern" in ice_after.lower() or "post-mmct" in ice_after.lower(), (
            f"13 Ma should describe stable post-MMCT ice. Got: {ice_after}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS FLOW 5: Full Earth State Vector consistency
# All variables at a given age should be mutually consistent
# ══════════════════════════════════════════════════════════════════════════════


class TestFullStateConsistency:
    """All variables at a given age should be mutually consistent."""

    @pytest.mark.asyncio
    async def test_23Ma_mi1_consistency(self):
        """23 Ma (Mi-1): CO2 moderate, temperature warm, ice expanded, sea level low."""
        state = await _get_state(23.0)

        co2 = state["atmospheric_co2_ppm"]["value"]
        temp = state["global_temperature_anomaly_c"]["value"]
        ice = str(state["ice_extent"]["value"])
        sl = state["eustatic_sea_level_m"]["value"]

        # Mi-1: ice expanded
        assert _ice_has_ice(ice), f"23 Ma Mi-1 should have ice. Got: {ice}"

        # Mi-1: CO2 should be moderate (not extreme)
        if co2 is not None:
            assert 100 < co2 < 800, f"23 Ma CO2={co2} out of plausible range"

        # Mi-1: temperature should be warmer than present
        if temp is not None:
            assert temp > 0, f"23 Ma temp anomaly={temp}°C should be >0 (warmer than present)"

    @pytest.mark.asyncio
    async def test_50Ma_hothouse_consistency(self):
        """50 Ma (Eocene hothouse): high CO2, hot, ice-free, high sea level."""
        state = await _get_state(50.0)

        co2 = state["atmospheric_co2_ppm"]["value"]
        temp = state["global_temperature_anomaly_c"]["value"]
        ice = str(state["ice_extent"]["value"])

        # Hothouse: ice-free
        assert not _ice_has_ice(ice), f"50 Ma should be ice-free. Got: {ice}"

        # Hothouse: high CO2
        if co2 is not None:
            assert co2 > 500, f"50 Ma CO2={co2} should be >500 (hothouse)"

        # Hothouse: high temperature
        if temp is not None:
            assert temp > 5, f"50 Ma temp anomaly={temp}°C should be >5 (hothouse)"

    @pytest.mark.asyncio
    async def test_present_day_consistency(self):
        """0 Ma (pre-industrial): low CO2, cool, has ice, moderate sea level."""
        state = await _get_state(0.0)

        co2 = state["atmospheric_co2_ppm"]["value"]
        temp = state["global_temperature_anomaly_c"]["value"]
        ice = str(state["ice_extent"]["value"])

        # Pre-industrial: has ice
        assert _ice_has_ice(ice), f"0 Ma should have ice. Got: {ice}"

        # Pre-industrial: low CO2
        if co2 is not None:
            assert co2 < 350, f"0 Ma CO2={co2} should be <350 (pre-industrial)"

        # Pre-industrial: near-zero temperature anomaly
        if temp is not None:
            assert -2 < temp < 2, f"0 Ma temp anomaly={temp}°C should be near zero"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
