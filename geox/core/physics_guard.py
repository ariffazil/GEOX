"""
PhysicsGuard — Upstream physics constraint checker.

Runs BEFORE 888_HOLD queue.
Physically impossible outputs never reach human review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PhysicsViolation:
    parameter: str
    value: float
    min_bound: float
    max_bound: float
    severity: str = "CRITICAL"


@dataclass
class ValidationResult:
    status: str
    violations: list[PhysicsViolation] = field(default_factory=list)
    hold: bool = False
    posterior_breadth_violation: bool = False
    posterior_breadth_ratio: Optional[float] = None
    reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"status": self.status}
        if self.violations:
            result["violations"] = [
                {
                    "parameter": v.parameter,
                    "value": v.value,
                    "min_bound": v.min_bound,
                    "max_bound": v.max_bound,
                    "severity": v.severity,
                }
                for v in self.violations
            ]
        if self.hold:
            result["hold"] = True
        if self.posterior_breadth_violation:
            result["posterior_breadth_violation"] = True
        if self.posterior_breadth_ratio is not None:
            result["posterior_breadth_ratio"] = self.posterior_breadth_ratio
        if self.reason:
            result["reason"] = self.reason
        return result


class PhysicsGuard:
    """
    Upstream physics constraint checker.
    Runs BEFORE 888_HOLD queue.
    Physically impossible outputs never reach human review.
    """

    BOUNDS: dict[str, tuple[float, float]] = {
        "porosity": (0.02, 0.45),
        "sw": (0.0, 1.0),
        "vsh": (0.0, 1.0),
    }

    RO_BOUNDS: dict[str, tuple[float, float]] = {
        "ro_oil_window": (0.6, 1.3),
        "ro_gas_floor": (1.3, 5.0),
    }

    def __init__(self, max_posterior_ratio: float = 5.0) -> None:
        self.max_posterior_ratio = max_posterior_ratio

    def validate(self, output: dict[str, Any]) -> ValidationResult:
        """
        Returns output unchanged if valid.
        Returns {"status": "PHYSICS_VIOLATION", "violations": [...], "hold": True}
        if any bound is breached.
        """
        violations: list[PhysicsViolation] = []

        if "porosity" in output or "por" in output:
            por = output.get("porosity") or output.get("por")
            if por is not None:
                violations.extend(self._check_bounds("porosity", por))

        if "sw" in output:
            violations.extend(self._check_bounds("sw", output["sw"]))

        if "vsh" in output:
            violations.extend(self._check_bounds("vsh", output["vsh"]))

        if "ro" in output:
            ro = output["ro"]
            if ro is not None:
                violations.extend(self._check_ro_bounds(ro))

        if violations:
            return ValidationResult(
                status="PHYSICS_VIOLATION",
                violations=violations,
                hold=True,
                reason="Physical bounds exceeded",
            )

        return ValidationResult(status="PASS")

    def _check_bounds(
        self, param: str, value: float
    ) -> list[PhysicsViolation]:
        violations: list[PhysicsViolation] = []
        if param in self.BOUNDS:
            min_b, max_b = self.BOUNDS[param]
            if value < min_b or value > max_b:
                violations.append(
                    PhysicsViolation(
                        parameter=param,
                        value=value,
                        min_bound=min_b,
                        max_bound=max_b,
                        severity="CRITICAL",
                    )
                )
        return violations

    def _check_ro_bounds(self, ro: float) -> list[PhysicsViolation]:
        violations: list[PhysicsViolation] = []
        oil_min, oil_max = self.RO_BOUNDS["ro_oil_window"]
        gas_min, gas_max = self.RO_BOUNDS["ro_gas_floor"]

        if ro < oil_min or (ro > oil_max and ro < gas_min):
            violations.append(
                PhysicsViolation(
                    parameter="ro",
                    value=ro,
                    min_bound=oil_min,
                    max_bound=gas_max,
                    severity="WARNING",
                )
            )
        return violations

    def check_posterior_breadth(
        self, p10: float, p50: float, p90: float, max_ratio: Optional[float] = None
    ) -> ValidationResult:
        """
        Returns {"hold": True, "reason": "POSTERIOR_TOO_BROAD"}
        if P90/P10 > max_ratio.

        Args:
            p10: 10th percentile (P10)
            p50: 50th percentile (P50)
            p90: 90th percentile (P90)
            max_ratio: Maximum allowed P90/P10 ratio. Defaults to self.max_posterior_ratio.

        Returns:
            ValidationResult with status and hold flag
        """
        if max_ratio is None:
            max_ratio = self.max_posterior_ratio

        if p10 <= 0:
            return ValidationResult(
                status="INVALID",
                hold=True,
                reason="P10 must be > 0 for ratio calculation",
            )

        ratio = p90 / p10

        if ratio > max_ratio:
            return ValidationResult(
                status="POSTERIOR_TOO_BROAD",
                hold=True,
                posterior_breadth_violation=True,
                posterior_breadth_ratio=ratio,
                reason=f"POSTERIOR_TOO_BROAD: P90/P10 = {ratio:.2f} > {max_ratio}",
            )

        return ValidationResult(
            status="PASS",
            posterior_breadth_ratio=ratio,
        )

    def check_volumetric_output(
        self, stoiip: dict[str, Any], max_ratio: Optional[float] = None
    ) -> ValidationResult:
        """
        Check a volumetric output dict with p10/p50/p90 values.

        Args:
            stoiip: Dict with keys "p10", "p50", "p90", and optionally "unit"

        Returns:
            ValidationResult with posterior breadth check
        """
        if not all(k in stoiip for k in ("p10", "p50", "p90")):
            return ValidationResult(
                status="INVALID",
                hold=True,
                reason="Volumetric output requires p10, p50, p90",
            )

        return self.check_posterior_breadth(
            p10=stoiip["p10"],
            p50=stoiip["p50"],
            p90=stoiip["p90"],
            max_ratio=max_ratio,
        )

    def check_net_pay(
        self, sw: float, por: float, vsh: float,
        sw_cutoff: float = 0.4,
        por_cutoff: float = 0.10,
        vsh_cutoff: float = 0.6
    ) -> ValidationResult:
        """
        Validate net pay criteria: Sw < Sw_cutoff AND POR > POR_cutoff AND Vsh < Vsh_cutoff.

        All three conditions must be met simultaneously for net pay.

        Args:
            sw: Water saturation
            por: Porosity
            vsh: Shale volume
            sw_cutoff: Maximum Sw for net pay (default 0.4)
            por_cutoff: Minimum POR for net pay (default 0.10)
            vsh_cutoff: Maximum Vsh for net pay (default 0.6)

        Returns:
            ValidationResult with net pay status
        """
        violations: list[PhysicsViolation] = []

        if sw >= sw_cutoff:
            violations.append(
                PhysicsViolation(
                    parameter="sw",
                    value=sw,
                    min_bound=0.0,
                    max_bound=sw_cutoff,
                    severity="CRITICAL",
                )
            )

        if por <= por_cutoff:
            violations.append(
                PhysicsViolation(
                    parameter="por",
                    value=por,
                    min_bound=por_cutoff,
                    max_bound=1.0,
                    severity="CRITICAL",
                )
            )

        if vsh >= vsh_cutoff:
            violations.append(
                PhysicsViolation(
                    parameter="vsh",
                    value=vsh,
                    min_bound=0.0,
                    max_bound=vsh_cutoff,
                    severity="CRITICAL",
                )
            )

        if violations:
            return ValidationResult(
                status="NET_PAY_NOT_MET",
                violations=violations,
                hold=True,
                reason="Net pay requires Sw < Sw_cutoff AND POR > POR_cutoff AND Vsh < Vsh_cutoff",
            )

        return ValidationResult(status="PASS")

    def check_charge_timing(
        self, charge_ma: float, trap_ma: float
    ) -> ValidationResult:
        """
        Validate charge timing: charge_ma must be <= trap_ma.

        Charge must occur BEFORE or SIMULTANEOUS with trap formation.

        Args:
            charge_ma: Charge timing in millions of years ago
            trap_ma: Trap formation timing in millions of years ago

        Returns:
            ValidationResult with timing status
        """
        if charge_ma > trap_ma:
            return ValidationResult(
                status="TIMING_VIOLATION",
                hold=True,
                reason=f"CHARGE_BEFORE_TRAP_VIOLATION: charge_ma ({charge_ma}) > trap_ma ({trap_ma})",
            )

        return ValidationResult(status="PASS")

    def validate_prospect_input(
        self, prospect: dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a complete prospect input dict.

        Args:
            prospect: Dict with keys like por, sw, vsh, stoiip (p10/p50/p90), etc.

        Returns:
            ValidationResult with all violations
        """
        all_violations: list[PhysicsViolation] = []
        posterior_breadth_violation = False
        posterior_breadth_ratio: Optional[float] = None
        reasons: list[str] = []

        if any(k in prospect for k in ("porosity", "por", "sw", "vsh")):
            basic_result = self.validate(prospect)
            if basic_result.violations:
                all_violations.extend(basic_result.violations)

        if "stoiip" in prospect and isinstance(prospect["stoiip"], dict):
            stoiip_result = self.check_volumetric_output(prospect["stoiip"])
            if stoiip_result.hold:
                posterior_breadth_violation = stoiip_result.posterior_breadth_violation
                posterior_breadth_ratio = stoiip_result.posterior_breadth_ratio
                if stoiip_result.reason:
                    reasons.append(stoiip_result.reason)

        if all_violations or reasons:
            return ValidationResult(
                status="PHYSICS_VIOLATION",
                violations=all_violations,
                hold=True,
                posterior_breadth_violation=posterior_breadth_violation,
                posterior_breadth_ratio=posterior_breadth_ratio,
                reason="; ".join(reasons) if reasons else "Physical bounds exceeded",
            )

        return ValidationResult(status="PASS")
