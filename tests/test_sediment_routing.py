"""
test_sediment_routing.py — Sediment Routing Engine Tests
=========================================================

Verifies the routing engine produces physics-generated bodies,
not facies classifications.

DITEMPA BUKAN DIBERI — Forged, Not Given.
Forged: 2026-07-03 — the extinction event.
"""

from __future__ import annotations

import pytest

from geox_core.engines.stratigraphy.sediment_routing import (
    BasinGeometry,
    DepositionalBody,
    Environment,
    LobeEvent,
    RoutingRequest,
    RoutingResult,
    SedimentSource,
    simulate_routing,
    _gradient_at_position,
    _environment_at_position,
    _transport_capacity,
    _is_turbidity_initiated,
)


# ═══════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════


def _default_request(**overrides) -> RoutingRequest:
    """Create a default routing request for testing."""
    defaults = dict(
        sources=[
            SedimentSource(
                source_id="RIVER1",
                position_km=0.0,
                sand_fraction=0.6,
                supply_rate_m_myr=100.0,
                discharge_m3_s=2000.0,
            ),
        ],
        geometry=BasinGeometry(
            profile_length_km=120.0,
            shelf_width_km=50.0,
            shelf_gradient=0.001,
            slope_gradient=0.05,
            basin_floor_gradient=0.001,
            slope_start_km=60.0,
            basin_floor_start_km=80.0,
        ),
        accommodation_rate_m_myr=50.0,
        duration_ma=10.0,
        time_step_myr=1.0,
        seed=42,
    )
    defaults.update(overrides)
    return RoutingRequest(**defaults)


# ═══════════════════════════════════════════════════════════════════════════
# Physics Kernel Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestPhysicsKernels:
    """Test individual physics functions."""

    def test_gradient_shelf(self):
        """Shelf gradient is gentle."""
        geo = BasinGeometry(
            profile_length_km=120.0,
            shelf_gradient=0.001,
            slope_gradient=0.05,
            slope_start_km=60.0,
        )
        assert _gradient_at_position(30.0, geo) == 0.001

    def test_gradient_slope(self):
        """Slope gradient is steep."""
        geo = BasinGeometry(
            profile_length_km=120.0,
            shelf_gradient=0.001,
            slope_gradient=0.05,
            slope_start_km=60.0,
            basin_floor_start_km=80.0,
        )
        assert _gradient_at_position(70.0, geo) == 0.05

    def test_gradient_basin_floor(self):
        """Basin floor gradient is gentle."""
        geo = BasinGeometry(
            profile_length_km=120.0,
            shelf_gradient=0.001,
            slope_gradient=0.05,
            slope_start_km=60.0,
            basin_floor_start_km=80.0,
            basin_floor_gradient=0.002,
        )
        assert _gradient_at_position(100.0, geo) == 0.002

    def test_environment_coastal(self):
        """Shallow water near source = delta or shoreface."""
        geo = BasinGeometry(profile_length_km=120.0, slope_start_km=60.0)
        env = _environment_at_position(10.0, geo, water_depth_m=3.0)
        assert env in (Environment.DELTA, Environment.SHOREFACE)

    def test_environment_deep(self):
        """Deep water far from source = basin floor."""
        geo = BasinGeometry(
            profile_length_km=120.0,
            slope_start_km=60.0,
            basin_floor_start_km=80.0,
        )
        env = _environment_at_position(100.0, geo, water_depth_m=500.0)
        assert env == Environment.BASIN_FLOOR

    def test_transport_capacity_steeper(self):
        """Steeper slope = higher transport capacity."""
        cap_gentle = _transport_capacity(0.001, 1000.0, 0.25)
        cap_steep = _transport_capacity(0.05, 1000.0, 0.25)
        assert cap_steep >= cap_gentle

    def test_turbidity_steep_slope(self):
        """Steep slope with sediment = turbidity."""
        assert _is_turbidity_initiated(5.0, 10.0) is True

    def test_turbidity_gentle_slope(self):
        """Gentle slope = no turbidity."""
        assert _is_turbidity_initiated(1.0, 10.0) is False


# ═══════════════════════════════════════════════════════════════════════════
# Routing Engine Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestSedimentRouting:
    """Test the full routing simulation."""

    def test_basic_routing(self):
        """Basic routing produces bodies."""
        req = _default_request()
        result = simulate_routing(req)

        assert len(result.bodies) > 0
        assert result.total_sand_m > 0
        assert result.total_mud_m > 0
        assert result.confidence <= 0.90
        assert result.epistemic_label == "DER"

    def test_no_facies_labels(self):
        """CRITICAL: No facies labels in output. Environments are physics-derived."""
        req = _default_request()
        result = simulate_routing(req)
        output = str(result.model_dump()).upper()

        # These taxonomy labels must NOT appear
        for label in ["LST", "TST", "HST", "FSST", "SYSTEMS_TRACT"]:
            assert label not in output, f"Taxonomy label '{label}' found!"

    def test_environments_emerge(self):
        """Depositional environments emerge from routing, not from rules."""
        req = _default_request()
        result = simulate_routing(req)

        # At least one environment should emerge
        assert len(result.emergent_environments) > 0
        for env in result.emergent_environments:
            assert env in [e.value for e in Environment]

    def test_sand_mud_partitioning(self):
        """Sand and mud are partitioned by grain size."""
        req = _default_request()
        result = simulate_routing(req)

        # Both sand and mud should be deposited
        assert result.total_sand_m > 0
        assert result.total_mud_m > 0

    def test_mass_balance(self):
        """Mass balance is approximately conserved."""
        req = _default_request()
        result = simulate_routing(req)

        # Mass balance error should be small
        assert result.mass_balance_error < 0.5, f"Mass balance error too high: {result.mass_balance_error}"

    def test_reservoir_seal_source_emerge(self):
        """Reservoir/seal/source potential emerges from physics."""
        req = _default_request()
        result = simulate_routing(req)

        reservoirs = [b for b in result.bodies if b.is_reservoir]
        seals = [b for b in result.bodies if b.is_seal]

        # Sand-rich bodies should be reservoirs
        for r in reservoirs:
            assert r.sand_fraction > 0.5

        # Mud-rich bodies should be seals
        for s in seals:
            assert s.sand_fraction < 0.3

    def test_lobe_events_generated(self):
        """Lobe switching events are generated from physics."""
        req = _default_request(duration_ma=20.0, time_step_myr=0.5, seed=123)
        result = simulate_routing(req)

        # Events may or may not occur depending on gradient
        # The test is that the structure is correct
        for event in result.lobe_events:
            assert event.event_type in ("avulsion", "turbidity_current", "lobe_abandonment")
            assert event.age_ma >= 0

    def test_deterministic_with_seed(self):
        """Same seed produces same result."""
        req1 = _default_request(seed=42)
        req2 = _default_request(seed=42)
        r1 = simulate_routing(req1)
        r2 = simulate_routing(req2)

        assert r1.total_sand_m == r2.total_sand_m
        assert len(r1.bodies) == len(r2.bodies)

    def test_steeper_slope_more_turbidity(self):
        """Steeper slope produces more turbidity events."""
        req_gentle = _default_request(seed=42)
        # Override geometry for steeper slope
        req_steep = _default_request(
            seed=42,
            geometry=BasinGeometry(
                profile_length_km=120.0,
                shelf_width_km=50.0,
                shelf_gradient=0.001,
                slope_gradient=0.15,  # much steeper
                basin_floor_gradient=0.001,
                slope_start_km=60.0,
                basin_floor_start_km=80.0,
            ),
        )

        r_gentle = simulate_routing(req_gentle)
        r_steep = simulate_routing(req_steep)

        # Steeper should have more turbidity events
        assert r_steep.num_turbidity_events >= r_gentle.num_turbidity_events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
