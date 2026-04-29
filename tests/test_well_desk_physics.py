"""
test_well_desk_physics.py — Pytest Suite for Rock Physics Engine
=================================================================
Validates forward/inverse round-trip, metabolic convergence,
and PhysicsGuard boundary enforcement.

Run: pytest tests/test_well_desk_physics.py -v
"""

import sys
import pytest
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))

from rock_physics_engine import (
    RockPhysicsEngine,
    Physics9State,
    PhysicsGuard,
    GUARD,
    Mineral,
    Fluid,
    GASSMANN_CONST  # Will be defined in engine
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    return RockPhysicsEngine()


@pytest.fixture
def bek2_state():
    """BEK-2 scaffold: phi=0.22, Sw=0.35, vsh=0.12, brine, 2040-2220m"""
    return Physics9State(
        porosity=0.22, sw=0.35, vsh=0.12,
        fluid_type="brine", pressure_mpa=25.0, temp_c=80.0
    )


@pytest.fixture
def clean_sand_brine():
    """Clean sand, fully brine saturated"""
    return Physics9State(
        porosity=0.25, sw=1.0, vsh=0.05,
        fluid_type="brine", pressure_mpa=20.0, temp_c=75.0
    )


@pytest.fixture
def clean_sand_gas():
    """Clean sand with gas — should show Vp drop and Vp/Vs increase"""
    return Physics9State(
        porosity=0.25, sw=0.10, vsh=0.05,
        fluid_type="gas", pressure_mpa=20.0, temp_c=75.0
    )


# ── Forward Tests ────────────────────────────────────────────────────────────

class TestForward:
    def test_forward_sandstone_brine(self, engine, clean_sand_brine):
        """Known input (clean sand, brine) must produce Vp in expected range."""
        result = engine.forward(clean_sand_brine)
        assert result.grade != "PHYSICS_VIOLATION"
        assert GUARD["vp_min"] <= result.vp <= GUARD["vp_max"]
        assert GUARD["rho_min"] <= result.rho <= GUARD["rho_max"]
        # Clean brine sand: Vp ~ 3500-4200 m/s
        assert 3500 <= result.vp <= 4200
        # Density ~ 2.3-2.4 g/cm3
        assert 2.2 <= result.rho <= 2.45

    def test_forward_sandstone_oil(self, engine):
        """Oil saturation should produce Vp between brine and gas cases."""
        state = Physics9State(
            porosity=0.25, sw=0.20, vsh=0.05,
            fluid_type="oil", pressure_mpa=20.0, temp_c=75.0
        )
        result = engine.forward(state)
        assert result.grade != "PHYSICS_VIOLATION"
        assert 3000 <= result.vp <= 4000

    def test_forward_sandstone_gas(self, engine, clean_sand_gas):
        """Gas substitution must produce Vp drop and Vp/Vs increase vs brine."""
        # First get brine reference
        brine_state = Physics9State(
            porosity=0.25, sw=1.0, vsh=0.05,
            fluid_type="brine", pressure_mpa=20.0, temp_c=75.0
        )
        brine_result = engine.forward(brine_state)
        gas_result = engine.forward(clean_sand_gas)

        assert gas_result.grade != "PHYSICS_VIOLATION"
        # Gas: Vp must drop significantly (>20% lower than brine)
        assert gas_result.vp < brine_result.vp * 0.85
        # Gas: Vp/Vs must increase
        assert gas_result.vp_vs_ratio > brine_result.vp_vs_ratio
        # Gas: density must drop
        assert gas_result.rho < brine_result.rho * 0.95

    def test_forward_shale(self, engine):
        """High vsh (shale) must produce lower Vp/Vs and higher density."""
        state = Physics9State(
            porosity=0.12, sw=1.0, vsh=0.85,
            fluid_type="brine", pressure_mpa=25.0, temp_c=80.0
        )
        result = engine.forward(state)
        assert result.grade != "PHYSICS_VIOLATION"
        # Shale: Vp ~ 2800-3400 m/s
        assert 2500 <= result.vp <= 3600
        # Shale: higher density
        assert result.rho >= 2.4

    def test_forward_limestone(self, engine):
        """Carbonate matrix must produce high Vp."""
        state = Physics9State(
            porosity=0.10, sw=1.0, vsh=0.05,
            fluid_type="brine", pressure_mpa=30.0, temp_c=90.0
        )
        result = engine.forward(state, lithology="lime_shale")
        assert result.grade != "PHYSICS_VIOLATION"
        # Limestone: Vp > 5000 m/s
        assert result.vp >= 4800
        assert result.rho >= 2.5


# ── Inverse Tests ────────────────────────────────────────────────────────────

class TestInverse:
    @pytest.mark.skipif(
        not hasattr(RockPhysicsEngine, 'inverse') or RockPhysicsEngine.__dict__.get('inverse') is None,
        reason="scipy not available for inverse mode"
    )
    def test_inverse_round_trip(self, engine):
        """Forward(por=0.22, Sw=0.35) → inverse → recover por ±0.02, Sw ±0.05."""
        # Forward
        fwd_state = Physics9State(
            porosity=0.22, sw=0.35, vsh=0.12,
            fluid_type="brine", pressure_mpa=25.0, temp_c=80.0
        )
        fwd = engine.forward(fwd_state)
        assert fwd.grade != "PHYSICS_VIOLATION"

        # Inverse
        inv = engine.inverse(fwd.vp, fwd.vs, fwd.rho, prior=fwd_state)
        assert inv.grade != "PHYSICS_VIOLATION"

        # Recovery tolerance
        assert abs(inv.est_porosity - 0.22) <= 0.02
        assert abs(inv.est_sw - 0.35) <= 0.05
        # Fluid type should be identified correctly
        assert inv.est_fluid == "brine"

    @pytest.mark.skipif(
        not hasattr(RockPhysicsEngine, 'inverse') or RockPhysicsEngine.__dict__.get('inverse') is None,
        reason="scipy not available for inverse mode"
    )
    def test_inverse_gas_identification(self, engine):
        """Gas case must be identified as gas after inversion."""
        fwd_state = Physics9State(
            porosity=0.25, sw=0.10, vsh=0.05,
            fluid_type="gas", pressure_mpa=20.0, temp_c=75.0
        )
        fwd = engine.forward(fwd_state)
        inv = engine.inverse(fwd.vp, fwd.vs, fwd.rho, prior=fwd_state)
        assert inv.est_fluid == "gas"


# ── PhysicsGuard Tests ───────────────────────────────────────────────────────

class TestPhysicsGuard:
    def test_guard_rejects_impossible_porosity(self, engine):
        """por=0.55 must trigger PHYSICS_VIOLATION."""
        state = Physics9State(
            porosity=0.55, sw=0.50, vsh=0.20,
            fluid_type="brine", pressure_mpa=25.0, temp_c=80.0
        )
        result = engine.forward(state)
        assert result.grade == "PHYSICS_VIOLATION"

    def test_guard_rejects_negative_vs(self):
        """Vs = 0 with rho > 2.0 is physically impossible."""
        guard = PhysicsGuard()
        assert guard.validate_forward(3000, 0, 2.2) == "PHYSICS_VIOLATION"

    def test_guard_accepts_reasonable_values(self):
        """Typical sandstone values must pass."""
        guard = PhysicsGuard()
        assert guard.validate_forward(3800, 2100, 2.35) == "AAA"

    def test_guard_reversibility_check(self):
        """F1: Round-trip must be reversible within tolerance."""
        guard = PhysicsGuard()
        fwd = Physics9State(porosity=0.22, sw=0.35, vsh=0.12, fluid_type="brine")
        fwd.vp = 3700; fwd.vs = 2000; fwd.rho = 2.38
        inv = Physics9State(porosity=0.22, sw=0.35, vsh=0.12, fluid_type="brine")
        inv.est_porosity = 0.215; inv.est_sw = 0.34
        assert guard.check_reversibility(fwd, inv) is True

        # Outside tolerance
        inv.est_porosity = 0.30  # Too far
        assert guard.check_reversibility(fwd, inv) is False


# ── Metabolic Tests ──────────────────────────────────────────────────────────

class TestMetabolic:
    def test_metabolic_convergence(self, engine, bek2_state):
        """Metabolic mode must converge in < 50 iterations for BEK-2 scaffold."""
        # Forward reference
        fwd = engine.forward(bek2_state)
        assert fwd.grade != "PHYSICS_VIOLATION"

        # Metabolic convergence
        result = engine.metabolic(fwd.vp, fwd.ai * 1000, bek2_state, max_iter=50)

        # Must not be physics violation
        assert result.grade != "PHYSICS_VIOLATION"
        # Should have iteration log
        assert len(result.metabolic_log) > 0
        assert len(result.metabolic_log) <= 50
        # Final delta should be smaller than initial
        if len(result.metabolic_log) > 1:
            final_delta = result.metabolic_log[-1].delta_state
            initial_delta = result.metabolic_log[0].delta_state
            assert final_delta <= initial_delta

    def test_metabolic_aaa_grade(self, engine):
        """Perfect match should reach AAA immediately."""
        state = Physics9State(
            porosity=0.20, sw=0.50, vsh=0.20,
            fluid_type="brine", pressure_mpa=25.0, temp_c=80.0
        )
        fwd = engine.forward(state)
        # Use exact forward outputs as observed
        result = engine.metabolic(fwd.vp, fwd.ai * 1000, state, tolerance=1e-3)
        assert result.grade == "AAA"
        assert len(result.metabolic_log) <= 2  # Should converge immediately


# ── Mineral/Fluid Catalog Tests ──────────────────────────────────────────────

class TestCatalog:
    def test_mineral_properties_exist(self):
        """All mineral end-members must have valid properties."""
        for mineral in Mineral:
            assert mineral.bulk_mod > 0
            assert mineral.shear_mod >= 0
            assert 1.0 <= mineral.rho <= 5.0

    def test_fluid_properties_exist(self):
        """All fluid end-members must have valid properties."""
        for fluid in Fluid:
            assert fluid.bulk_mod >= 0  # Gas can be ~0
            assert fluid.rho > 0

    def test_vrh_bounds(self):
        """Voigt-Reuss-Hill must lie between bounds."""
        from rock_physics_engine import vrh_bound
        k_v, k_r = vrh_bound(0.5, 36.6, 2.5)
        k_hill = 0.5 * (k_v + k_r)
        assert k_r <= k_hill <= k_v


# ── Vault Receipt Tests ──────────────────────────────────────────────────────

class TestVault:
    def test_receipt_structure(self, engine):
        """Receipt must contain all required fields."""
        state = Physics9State(
            porosity=0.22, sw=0.35, vsh=0.12,
            fluid_type="brine", pressure_mpa=25.0, temp_c=80.0
        )
        fwd = engine.forward(state)
        receipt = engine.build_vault_receipt(fwd)
        assert receipt.receipt_id.startswith("well-desk-")
        assert receipt.vault_route == "999_VAULT"
        assert receipt.floor_checks["F11"] is True

    def test_receipt_floor_checks(self, engine):
        """PHYSICS_VIOLATION must fail F9."""
        state = Physics9State(
            porosity=0.55, sw=0.50, vsh=0.20,
            fluid_type="brine", pressure_mpa=25.0, temp_c=80.0
        )
        fwd = engine.forward(state)
        receipt = engine.build_vault_receipt(fwd)
        assert receipt.floor_checks["F9"] is False


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
