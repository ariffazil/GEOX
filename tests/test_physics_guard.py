"""
Unit tests for PhysicsGuard.
Tests physics constraint enforcement for subsurface outputs.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from geox.core.physics_guard import PhysicsGuard, PhysicsViolation, ValidationResult


class TestPhysicsGuardValidate:
    """Tests for PhysicsGuard.validate()"""

    def setup_method(self):
        self.guard = PhysicsGuard()

    def test_valid_porosity(self):
        result = self.guard.validate({"porosity": 0.25})
        assert result.status == "PASS"
        assert result.hold is False
        assert len(result.violations) == 0

    def test_valid_sw(self):
        result = self.guard.validate({"sw": 0.3})
        assert result.status == "PASS"

    def test_valid_vsh(self):
        result = self.guard.validate({"vsh": 0.15})
        assert result.status == "PASS"

    def test_porosity_below_min(self):
        result = self.guard.validate({"porosity": 0.01})
        assert result.status == "PHYSICS_VIOLATION"
        assert result.hold is True
        assert len(result.violations) == 1
        assert result.violations[0].parameter == "porosity"
        assert result.violations[0].value == 0.01

    def test_porosity_above_max(self):
        result = self.guard.validate({"porosity": 0.50})
        assert result.status == "PHYSICS_VIOLATION"
        assert result.hold is True

    def test_sw_below_min(self):
        result = self.guard.validate({"sw": -0.1})
        assert result.status == "PHYSICS_VIOLATION"
        assert result.hold is True

    def test_sw_above_max(self):
        result = self.guard.validate({"sw": 1.5})
        assert result.status == "PHYSICS_VIOLATION"
        assert result.hold is True

    def test_vsh_below_min(self):
        result = self.guard.validate({"vsh": -0.05})
        assert result.status == "PHYSICS_VIOLATION"
        assert result.hold is True

    def test_vsh_above_max(self):
        result = self.guard.validate({"vsh": 1.2})
        assert result.status == "PHYSICS_VIOLATION"
        assert result.hold is True

    def test_multiple_violations(self):
        result = self.guard.validate({"porosity": 0.50, "sw": 1.5, "vsh": 1.2})
        assert result.status == "PHYSICS_VIOLATION"
        assert len(result.violations) == 3

    def test_empty_output_passes(self):
        result = self.guard.validate({})
        assert result.status == "PASS"

    def test_por_key_alias(self):
        result = self.guard.validate({"por": 0.20})
        assert result.status == "PASS"


class TestPhysicsGuardPosteriorBreadth:
    """Tests for PhysicsGuard.check_posterior_breadth()"""

    def setup_method(self):
        self.guard = PhysicsGuard(max_posterior_ratio=5.0)

    def test_valid_posterior_breadth(self):
        result = self.guard.check_posterior_breadth(p10=50, p50=100, p90=200)
        assert result.status == "PASS"
        assert result.hold is False
        assert result.posterior_breadth_ratio == 4.0

    def test_boundary_ratio(self):
        result = self.guard.check_posterior_breadth(p10=50, p50=100, p90=250)
        assert result.status == "PASS"
        assert result.posterior_breadth_ratio == 5.0

    def test_excessive_breadth(self):
        result = self.guard.check_posterior_breadth(p10=10, p50=100, p90=600)
        assert result.status == "POSTERIOR_TOO_BROAD"
        assert result.hold is True
        assert result.posterior_breadth_ratio == 60.0
        assert result.posterior_breadth_violation is True

    def test_p10_zero_invalid(self):
        result = self.guard.check_posterior_breadth(p10=0, p50=100, p90=200)
        assert result.status == "INVALID"
        assert result.hold is True

    def test_negative_p10_invalid(self):
        result = self.guard.check_posterior_breadth(p10=-10, p50=100, p90=200)
        assert result.status == "INVALID"
        assert result.hold is True

    def test_custom_max_ratio(self):
        guard = PhysicsGuard(max_posterior_ratio=3.0)
        result = guard.check_posterior_breadth(p10=50, p50=100, p90=200)
        assert result.status == "POSTERIOR_TOO_BROAD"


class TestPhysicsGuardVolumetricOutput:
    """Tests for PhysicsGuard.check_volumetric_output()"""

    def setup_method(self):
        self.guard = PhysicsGuard()

    def test_valid_stoiip(self):
        result = self.guard.check_volumetric_output(
            {"p10": 50, "p50": 100, "p90": 200, "unit": "MMbbl"}
        )
        assert result.status == "PASS"

    def test_missing_p10(self):
        result = self.guard.check_volumetric_output(
            {"p50": 100, "p90": 200}
        )
        assert result.status == "INVALID"
        assert result.hold is True

    def test_missing_p50(self):
        result = self.guard.check_volumetric_output(
            {"p10": 50, "p90": 200}
        )
        assert result.status == "INVALID"

    def test_missing_p90(self):
        result = self.guard.check_volumetric_output(
            {"p10": 50, "p50": 100}
        )
        assert result.status == "INVALID"

    def test_excessive_breadth_stoiip(self):
        result = self.guard.check_volumetric_output(
            {"p10": 10, "p50": 100, "p90": 700}
        )
        assert result.status == "POSTERIOR_TOO_BROAD"
        assert result.hold is True


class TestPhysicsGuardNetPay:
    """Tests for PhysicsGuard.check_net_pay()"""

    def setup_method(self):
        self.guard = PhysicsGuard()

    def test_valid_net_pay(self):
        result = self.guard.check_net_pay(sw=0.25, por=0.18, vsh=0.20)
        assert result.status == "PASS"

    def test_sw_above_cutoff(self):
        result = self.guard.check_net_pay(sw=0.50, por=0.18, vsh=0.20)
        assert result.status == "NET_PAY_NOT_MET"
        assert result.hold is True

    def test_por_below_cutoff(self):
        result = self.guard.check_net_pay(sw=0.25, por=0.05, vsh=0.20)
        assert result.status == "NET_PAY_NOT_MET"
        assert result.hold is True

    def test_vsh_above_cutoff(self):
        result = self.guard.check_net_pay(sw=0.25, por=0.18, vsh=0.70)
        assert result.status == "NET_PAY_NOT_MET"
        assert result.hold is True

    def test_all_criteria_fail(self):
        result = self.guard.check_net_pay(sw=0.50, por=0.05, vsh=0.70)
        assert result.status == "NET_PAY_NOT_MET"
        assert len(result.violations) == 3

    def test_custom_cutoffs(self):
        result = self.guard.check_net_pay(
            sw=0.35, por=0.12, vsh=0.50,
            sw_cutoff=0.3, por_cutoff=0.15, vsh_cutoff=0.4
        )
        assert result.status == "NET_PAY_NOT_MET"
        assert len(result.violations) == 3


class TestPhysicsGuardChargeTiming:
    """Tests for PhysicsGuard.check_charge_timing()"""

    def setup_method(self):
        self.guard = PhysicsGuard()

    def test_valid_timing_charge_before_trap(self):
        result = self.guard.check_charge_timing(charge_ma=50, trap_ma=60)
        assert result.status == "PASS"

    def test_valid_timing_simultaneous(self):
        result = self.guard.check_charge_timing(charge_ma=60, trap_ma=60)
        assert result.status == "PASS"

    def test_timing_violation_charge_after_trap(self):
        result = self.guard.check_charge_timing(charge_ma=70, trap_ma=60)
        assert result.status == "TIMING_VIOLATION"
        assert result.hold is True
        assert "CHARGE_BEFORE_TRAP_VIOLATION" in result.reason


class TestPhysicsGuardProspectInput:
    """Tests for PhysicsGuard.validate_prospect_input()"""

    def setup_method(self):
        self.guard = PhysicsGuard()

    def test_valid_prospect(self):
        result = self.guard.validate_prospect_input({
            "porosity": 0.25,
            "sw": 0.30,
            "vsh": 0.15,
            "stoiip": {"p10": 50, "p50": 100, "p90": 200}
        })
        assert result.status == "PASS"

    def test_prospect_with_violation(self):
        result = self.guard.validate_prospect_input({
            "porosity": 0.50,
            "stoiip": {"p10": 50, "p50": 100, "p90": 200}
        })
        assert result.status == "PHYSICS_VIOLATION"

    def test_prospect_with_broad_posterior(self):
        result = self.guard.validate_prospect_input({
            "stoiip": {"p10": 10, "p50": 100, "p90": 700}
        })
        assert result.status == "PHYSICS_VIOLATION"
        assert result.posterior_breadth_violation is True


class TestValidationResult:
    """Tests for ValidationResult.to_dict()"""

    def test_pass_result(self):
        result = ValidationResult(status="PASS")
        d = result.to_dict()
        assert d["status"] == "PASS"
        assert "violations" not in d
        assert "hold" not in d

    def test_violation_result(self):
        violation = PhysicsViolation(
            parameter="porosity",
            value=0.50,
            min_bound=0.02,
            max_bound=0.45
        )
        result = ValidationResult(
            status="PHYSICS_VIOLATION",
            violations=[violation],
            hold=True,
            reason="Physical bounds exceeded"
        )
        d = result.to_dict()
        assert d["status"] == "PHYSICS_VIOLATION"
        assert d["hold"] is True
        assert len(d["violations"]) == 1
        assert d["violations"][0]["parameter"] == "porosity"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
