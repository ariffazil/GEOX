"""
geox_core.physics.guards — Upstream Physics Constraint Checker

Runs BEFORE 888_HOLD queue.
Physically impossible outputs never reach human review.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from geox_core.core.epistemic_integrity import EpistemicIntegrity, EpistemicResult


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
    posterior_breadth_ratio: float | None = None
    reason: str | None = None
    epistemic_integrity: EpistemicResult | None = None

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
        if self.epistemic_integrity:
            result["epistemic_integrity"] = self.epistemic_integrity.to_dict()
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

    # ── Multi-Physics Bounds (Phase C: Seismic Inversion / Gravity / Magnetics / EM) ──

    GRAVITY_BOUNDS: dict[str, tuple[float, float]] = {
        "density_kg_m3": (1000, 5000),
        "density_contrast_kg_m3": (-2000, 2000),
        "bouguer_anomaly_mgal": (-200, 200),
    }

    MAGNETICS_BOUNDS: dict[str, tuple[float, float]] = {
        "susceptibility_si": (0, 0.1),
        "total_field_anomaly_nt": (-5000, 5000),
        "inclination_deg": (-90, 90),
    }

    EM_BOUNDS: dict[str, tuple[float, float]] = {
        "resistivity_ohmm": (0.01, 1e6),
        "apparent_resistivity_ohmm": (0.01, 1e6),
        "phase_deg": (-180, 180),
    }

    SEISMIC_INVERSION_BOUNDS: dict[str, tuple[float, float]] = {
        "acoustic_impedance_kg_m2s": (1e4, 1e8),
        "inversion_correlation": (0.0, 1.0),
    }

    def __init__(self, max_posterior_ratio: float = 5.0) -> None:
        self.max_posterior_ratio = max_posterior_ratio
        self.epistemic = EpistemicIntegrity()

    # ─── Core Bounds Validation ─────────────────────────────────────────────

    def validate(self, output: dict[str, Any]) -> ValidationResult:
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

    def _check_bounds(self, param: str, value: float) -> list[PhysicsViolation]:
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

    # ─── Posterior Breadth ──────────────────────────────────────────────────

    def check_posterior_breadth(
        self,
        p10: float,
        p50: float,
        p90: float,
        max_ratio: float | None = None,
    ) -> ValidationResult:
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
        return ValidationResult(status="PASS", posterior_breadth_ratio=ratio)

    def check_volumetric_output(self, stoiip: dict[str, Any], max_ratio: float | None = None) -> ValidationResult:
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

    # ─── Net Pay ────────────────────────────────────────────────────────────

    def check_net_pay(
        self,
        sw: float,
        por: float,
        vsh: float,
        sw_cutoff: float = 0.4,
        por_cutoff: float = 0.10,
        vsh_cutoff: float = 0.6,
    ) -> ValidationResult:
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

    # ─── Timing ─────────────────────────────────────────────────────────────

    def check_charge_timing(self, charge_ma: float, trap_ma: float) -> ValidationResult:
        if charge_ma > trap_ma:
            return ValidationResult(
                status="TIMING_VIOLATION",
                hold=True,
                reason=(f"CHARGE_BEFORE_TRAP_VIOLATION: charge_ma ({charge_ma}) > trap_ma ({trap_ma})"),
            )
        return ValidationResult(status="PASS")

    # ─── Well-Tie Integrity ─────────────────────────────────────────────────

    def check_tie_correlation(self, r_tie: float, threshold: float = 0.70) -> str:
        if r_tie < threshold:
            return "HOLD"
        return "QUALIFY"

    # ─── Velocity Sanity (Stretch/Squeeze Guard) ────────────────────────────

    def validate_velocity_sanity(self, v_stretched: np.ndarray, z_depth: np.ndarray) -> ValidationResult:
        violations: list[PhysicsViolation] = []

        if np.any(v_stretched > 5500.0) or np.any(v_stretched < 1480.0):
            violations.append(
                PhysicsViolation(
                    parameter="velocity_absolute",
                    value=float(np.max(v_stretched) if np.any(v_stretched > 5500.0) else np.min(v_stretched)),
                    min_bound=1480.0,
                    max_bound=5500.0,
                    severity="CRITICAL",
                )
            )

        dv_dz = np.abs(np.diff(v_stretched) / np.diff(z_depth))
        if np.any(dv_dz > 50.0):
            violations.append(
                PhysicsViolation(
                    parameter="velocity_gradient_acceleration",
                    value=float(np.max(dv_dz)),
                    min_bound=0.0,
                    max_bound=50.0,
                    severity="CRITICAL",
                )
            )

        if violations:
            return ValidationResult(
                status="PHYSICS_VIOLATION",
                violations=violations,
                hold=True,
                reason="Unphysical velocity stretch/squeeze detected.",
            )
        return ValidationResult(status="PASS")

    # ─── Multi-Physics Validation (Phase C) ────────────────────────────────

    def validate_gravity(self, output: dict[str, Any]) -> ValidationResult:
        """Validate gravity forward model output against physical bounds."""
        violations: list[PhysicsViolation] = []
        for param, (lo, hi) in self.GRAVITY_BOUNDS.items():
            val = output.get(param)
            if val is not None and isinstance(val, (int, float)):
                if val < lo or val > hi:
                    violations.append(PhysicsViolation(
                        parameter=param, value=float(val),
                        min_bound=lo, max_bound=hi, severity="CRITICAL",
                    ))
        if violations:
            return ValidationResult(
                status="PHYSICS_VIOLATION", violations=violations, hold=True,
                reason="Gravity bounds exceeded",
            )
        return ValidationResult(status="PASS")

    def validate_magnetics(self, output: dict[str, Any]) -> ValidationResult:
        """Validate magnetics forward model output against physical bounds."""
        violations: list[PhysicsViolation] = []
        for param, (lo, hi) in self.MAGNETICS_BOUNDS.items():
            val = output.get(param)
            if val is not None and isinstance(val, (int, float)):
                if val < lo or val > hi:
                    violations.append(PhysicsViolation(
                        parameter=param, value=float(val),
                        min_bound=lo, max_bound=hi, severity="CRITICAL",
                    ))
        if violations:
            return ValidationResult(
                status="PHYSICS_VIOLATION", violations=violations, hold=True,
                reason="Magnetics bounds exceeded",
            )
        return ValidationResult(status="PASS")

    def validate_em(self, output: dict[str, Any]) -> ValidationResult:
        """Validate EM forward model output against physical bounds."""
        violations: list[PhysicsViolation] = []
        for param, (lo, hi) in self.EM_BOUNDS.items():
            val = output.get(param)
            if val is not None and isinstance(val, (int, float)):
                if val < lo or val > hi:
                    violations.append(PhysicsViolation(
                        parameter=param, value=float(val),
                        min_bound=lo, max_bound=hi, severity="CRITICAL",
                    ))
        if violations:
            return ValidationResult(
                status="PHYSICS_VIOLATION", violations=violations, hold=True,
                reason="EM bounds exceeded",
            )
        return ValidationResult(status="PASS")

    def validate_seismic_inversion(self, output: dict[str, Any]) -> ValidationResult:
        """Validate seismic inversion output against physical bounds."""
        violations: list[PhysicsViolation] = []
        for param, (lo, hi) in self.SEISMIC_INVERSION_BOUNDS.items():
            val = output.get(param)
            if val is not None and isinstance(val, (int, float)):
                if val < lo or val > hi:
                    violations.append(PhysicsViolation(
                        parameter=param, value=float(val),
                        min_bound=lo, max_bound=hi, severity="CRITICAL",
                    ))
        if violations:
            return ValidationResult(
                status="PHYSICS_VIOLATION", violations=violations, hold=True,
                reason="Seismic inversion bounds exceeded",
            )
        return ValidationResult(status="PASS")

    def validate_physics9_state(self, state: dict[str, Any]) -> ValidationResult:
        """Validate a complete Physics9State against all bounds."""
        violations: list[PhysicsViolation] = []
        bounds = {
            "rho": (1000, 5000),
            "vp": (1500, 7000),
            "vs": (500, 4000),
            "rho_e": (0.01, 1e6),
            "chi": (0, 0.1),
            "k": (0.1, 10),
            "P": (1e5, 1e9),
            "T": (200, 600),
            "phi": (0.01, 0.45),
        }
        for param, (lo, hi) in bounds.items():
            val = state.get(param)
            if val is not None:
                if val < lo or val > hi:
                    violations.append(PhysicsViolation(
                        parameter=param, value=float(val),
                        min_bound=lo, max_bound=hi, severity="CRITICAL",
                    ))
        if violations:
            return ValidationResult(
                status="PHYSICS_VIOLATION", violations=violations, hold=True,
                reason="Physics9State bounds exceeded",
            )
        return ValidationResult(status="PASS")

    # ─── Drift Sanity (Checkshot Quality) ───────────────────────────────────

    def validate_drift_sanity(
        self,
        drift_ms: np.ndarray,
        z_depth: np.ndarray,
        threshold_curvature: float = 0.5,
    ) -> ValidationResult:
        d_drift_dz = np.diff(drift_ms) / np.diff(z_depth)
        d2_drift_dz2 = np.abs(np.diff(d_drift_dz) / np.diff(z_depth[:-1]))

        if np.any(d2_drift_dz2 > threshold_curvature):
            return ValidationResult(
                status="DRIFT_VIOLATION",
                hold=True,
                reason=(
                    f"Drift curve curvature {np.max(d2_drift_dz2):.4f} exceeds threshold "
                    f"{threshold_curvature}. Checkshot quality audit required."
                ),
                violations=[
                    PhysicsViolation(
                        parameter="drift_curvature",
                        value=float(np.max(d2_drift_dz2)),
                        min_bound=0.0,
                        max_bound=threshold_curvature,
                        severity="CRITICAL",
                    )
                ],
            )
        return ValidationResult(status="PASS")

    # ─── Prospect Composite ─────────────────────────────────────────────────

    def validate_prospect_input(self, prospect: dict[str, Any]) -> ValidationResult:
        all_violations: list[PhysicsViolation] = []
        posterior_breadth_violation = False
        posterior_breadth_ratio: float | None = None
        reasons: list[str] = []
        epistemic_result: EpistemicResult | None = None

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

        stoiip_data = prospect.get("stoiip", {})
        epistemic_result = self.epistemic.compute_integrity(
            outputs=stoiip_data if isinstance(stoiip_data, dict) else {},
            well_density=prospect.get("well_density", 0.0),
            model_lineage=prospect.get("model_lineage", ["unknown"]),
            pos_components=prospect.get("pos_components"),
        )

        if epistemic_result.hold:
            reasons.append(epistemic_result.recommendation)

        if all_violations or reasons or epistemic_result.hold:
            status = "PHYSICS_VIOLATION" if all_violations or posterior_breadth_violation else "EPISTEMIC_VIOLATION"
            return ValidationResult(
                status=status,
                violations=all_violations,
                hold=True,
                posterior_breadth_violation=posterior_breadth_violation,
                posterior_breadth_ratio=posterior_breadth_ratio,
                reason="; ".join(reasons) if reasons else "Physical/Epistemic violation",
                epistemic_integrity=epistemic_result,
            )

        return ValidationResult(status="PASS", epistemic_integrity=epistemic_result)
