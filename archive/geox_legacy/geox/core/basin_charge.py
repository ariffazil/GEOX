"""
Basin charge simulation for GEOX Wave 2 — Improved v2
DITEMPA BUKAN DIBERI

Improvement spec applied to geox_time4d_verify_timing:
  - verdict: screening | probable | improbable | void
  - burial_carrier_context: scenario_used, charge_age_ma, trap_age_ma
  - assumptions: TTI_window, migration_efficiency_assumption, seal_capacity_assumption
  - reversal_conditions: conditions under which the conclusion flips
  - claim_state: OBSERVED | COMPUTED | HYPOTHESIS | VOID
  - limitations: what limits confidence
  - vault_receipt

geox_simulate_basin_charge (internal engine) updated to support the improved tool.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import log10
from typing import Any

from geox.core.governed_output import classify_claim_tag, make_vault_receipt
from geox.core.physics_guard import PhysicsGuard


class ClaimTag(str):
    OBSERVED = "OBSERVED"
    COMPUTED = "COMPUTED"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"
    VOID = "VOID"


@dataclass
class BasinChargeResult:
    """Output schema for geox_simulate_basin_charge — v2."""
    tool: str = "geox_simulate_basin_charge"
    tti: float = 0.0
    easy_ro: float = 0.0
    migration_distance_km: float = 0.0
    charge_probability: float = 0.0
    seal_integrity_estimate: float = 0.0
    charge_age_ma: float = 0.0
    hold_enforced: bool = False
    claim_tag: str = ""
    timing_validation: dict = field(default_factory=dict)
    vault_receipt: dict = field(default_factory=dict)

    @property
    def maturity_window(self) -> str:
        if self.easy_ro < 0.5:
            return "IMMATURE"
        if self.easy_ro < 1.3:
            return "OIL_WINDOW"
        if self.easy_ro < 2.0:
            return "GAS_WINDOW"
        return "OVERMATURE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "tti": round(self.tti, 4),
            "easy_ro": round(self.easy_ro, 4),
            "migration_distance_km": round(self.migration_distance_km, 4),
            "charge_probability": round(self.charge_probability, 4),
            "seal_integrity_estimate": round(self.seal_integrity_estimate, 4),
            "charge_age_ma": round(self.charge_age_ma, 4),
            "hold_enforced": self.hold_enforced,
            "claim_tag": self.claim_tag,
            "timing_validation": self.timing_validation,
            "vault_receipt": self.vault_receipt,
        }


@dataclass
class TimingVerificationResult:
    """Output schema for geox_time4d_verify_timing — v2."""
    tool: str = "geox_time4d_verify_timing"
    # Verdict
    verdict: str = "void"  # screening | probable | improbable | void
    claim_state: str = ClaimTag.UNKNOWN
    # Evidence
    basin_charge_result: dict = field(default_factory=dict)
    charge_age_ma: float = 0.0
    trap_age_ma: float = 0.0
    charge_trap_age_diff_my: float = 0.0
    migration_window_my: float = 0.0
    # Context
    scenario_used: str = ""
    burial_carrier_assumptions: dict = field(default_factory=dict)
    assumptions: dict = field(default_factory=dict)
    # Reversal conditions
    reversal_conditions: list[str] = field(default_factory=list)
    reversal_scenarios: dict = field(default_factory=dict)
    # Limitations
    limitations: list[str] = field(default_factory=list)
    human_decision_point: str = ""
    # Vault
    vault_receipt: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "verdict": self.verdict,
            "claim_state": self.claim_state,
            "basin_charge_result": self.basin_charge_result,
            "charge_age_ma": round(self.charge_age_ma, 4),
            "trap_age_ma": round(self.trap_age_ma, 4),
            "charge_trap_age_diff_my": round(self.charge_trap_age_diff_my, 4),
            "migration_window_my": round(self.migration_window_my, 4),
            "scenario_used": self.scenario_used,
            "burial_carrier_assumptions": self.burial_carrier_assumptions,
            "assumptions": self.assumptions,
            "reversal_conditions": self.reversal_conditions,
            "reversal_scenarios": {k: round(v, 4) if isinstance(v, float) else v
                                   for k, v in self.reversal_scenarios.items()},
            "limitations": self.limitations,
            "human_decision_point": self.human_decision_point,
            "vault_receipt": self.vault_receipt,
        }


class BasinChargeSimulator:
    """Run a simplified Lopatin/Easy%Ro charge workflow — v2."""

    # Threshold for screening vs improbable
    CHARGE_PROBABILITY_SCREEN = 0.50

    def __init__(self, guard: PhysicsGuard | None = None) -> None:
        self.guard = guard or PhysicsGuard()

    def _normalize_burial(self, burial_history: list[dict[str, float]]) -> list[dict[str, float]]:
        normalized: list[dict[str, float]] = []
        for step in burial_history:
            if "temperature_c" in step and "duration_ma" in step:
                normalized.append(dict(step))
                continue
            age_start = float(step.get("age_ma_start", step.get("age_start_ma", 0.0)))
            age_end = float(step.get("age_ma_end", step.get("age_end_ma", 0.0)))
            temp_start = float(step.get("temp_start_c", step.get("temperature_c", 20.0)))
            temp_end = float(step.get("temp_end_c", step.get("temperature_c", temp_start)))
            normalized.append(
                {
                    "age_ma": max(age_start, age_end),
                    "duration_ma": abs(age_start - age_end),
                    "temperature_c": (temp_start + temp_end) / 2.0,
                }
            )
        return normalized

    def compute_tti(self, burial_history: list[dict[str, float]]) -> float:
        burial_history = self._normalize_burial(burial_history)
        tti = 0.0
        for step in burial_history:
            temp_c = step["temperature_c"]
            duration_ma = step["duration_ma"]
            tti += duration_ma * (2.0 ** ((temp_c - 100.0) / 10.0))
        return max(tti, 0.0)

    def compute_easy_ro(self, tti: float) -> float:
        if tti <= 0.0:
            return 0.2
        return max(0.2, min(3.5, 0.42 + 0.23 * log10(tti + 1.0)))

    def _get_charge_age(self, burial_history: list[dict[str, float]]) -> float:
        """Age at which source rock reached >= 90°C (main expulsion threshold)."""
        ages = [step.get("age_ma", 0.0) for step in burial_history if step.get("temperature_c", 0) >= 90.0]
        return max(ages) if ages else 0.0

    def _derive_reversal_conditions(
        self,
        charge_age_ma: float,
        trap_age_ma: float,
        migration_window_my: float,
        buoyancy_pressure_mpa: float,
        seal_capacity_mpa: float,
    ) -> tuple[list[str], dict]:
        """Derive conditions that would flip the verdict."""
        conditions: list[str] = []
        scenarios: dict = {}

        # Condition 1: trap significantly younger than charge
        if charge_age_ma > 0 and trap_age_ma < charge_age_ma - 10.0:
            conditions.append(f"Trap age ({trap_age_ma} Ma) is >10 Ma younger than charge window — charge may have dissipated before trap formation")

        # Condition 2: migration window too short
        if migration_window_my < 5.0:
            conditions.append(f"Migration window ({migration_window_my:.1f} Ma) < 5 Ma — insufficient for effective migration")
            scenarios["short_migration"] = {"migration_window_my": 2.0, "charge_probability_change": -0.20}

        # Condition 3: seal capacity exceeded
        if buoyancy_pressure_mpa > seal_capacity_mpa:
            conditions.append(f"Buoyancy ({buoyancy_pressure_mpa} MPa) exceeds seal capacity ({seal_capacity_mpa} MPa) — leakage risk")
            scenarios["seal_breach"] = {"buoyancy_pressure_mpa": seal_capacity_mpa * 1.2, "charge_probability_change": -0.15}

        # Condition 4: very low maturity
        if charge_age_ma < 20.0:
            conditions.append(f"Immature source (charge age {charge_age_ma:.0f} Ma) — if charge age is actually older/more mature, verdict improves")

        return conditions, scenarios

    def verify_timing(
        self,
        burial_history: list[dict[str, float]],
        trap_age_ma: float,
        carrier_permeability_md: float,
        buoyancy_pressure_mpa: float,
        seal_capacity_mpa: float,
        fault_density: float = 0.1,
    ) -> TimingVerificationResult:
        """
        burial_history = self._normalize_burial(burial_history)
        Full geox_time4d_verify_timing output — v2 spec.
        Returns verdict, scenario context, reversal conditions, claim state.
        """
        # Compute charge metrics
        tti = self.compute_tti(burial_history)
        easy_ro = self.compute_easy_ro(tti)
        charge_age_ma = self._get_charge_age(burial_history)
        migration_distance_km = max(0.0, buoyancy_pressure_mpa * max(carrier_permeability_md, 1.0) / 1000.0)
        migration_window_my = max(0.0, charge_age_ma - trap_age_ma)
        charge_trap_age_diff_my = abs(charge_age_ma - trap_age_ma)

        # Physics
        maturity_factor = max(0.0, min(1.0, (easy_ro - 0.5) / 0.8))
        migration_factor = max(0.0, min(1.0, migration_distance_km / 25.0))
        seal_integrity = max(0.0, min(1.0, (seal_capacity_mpa / max(buoyancy_pressure_mpa, 1e-6)) - fault_density * 0.25))
        charge_probability = max(0.0, min(1.0, 0.45 * maturity_factor + 0.3 * migration_factor + 0.25 * seal_integrity))

        # Timing validation
        timing_validation = self.guard.check_charge_timing(charge_age_ma, trap_age_ma)

        # Reversal conditions
        reversal_conditions, reversal_scenarios = self._derive_reversal_conditions(
            charge_age_ma, trap_age_ma, migration_window_my,
            buoyancy_pressure_mpa, seal_capacity_mpa,
        )

        # Verdict mapping
        if charge_age_ma == 0 or trap_age_ma == 0:
            verdict = "void"
            claim_state = ClaimTag.VOID
        elif charge_probability >= 0.65:
            verdict = "probable"
            claim_state = ClaimTag.COMPUTED
        elif charge_probability >= self.CHARGE_PROBABILITY_SCREEN:
            verdict = "screening"
            claim_state = ClaimTag.COMPUTED
        else:
            verdict = "improbable"
            claim_state = ClaimTag.HYPOTHESIS

        hold_enforced = timing_validation.hold or charge_probability < 0.30

        # Burial/carrier context
        burial_carrier_assumptions = {
            "scenario_used": "standard_burial",
            "carrier_permeability_md": carrier_permeability_md,
            "buoyancy_pressure_mpa": buoyancy_pressure_mpa,
            "seal_capacity_mpa": seal_capacity_mpa,
            "fault_density": fault_density,
            "migration_distance_km": round(migration_distance_km, 4),
            "seal_integrity_estimate": round(seal_integrity, 4),
        }

        assumptions = {
            "TTI_window": f"computed from {len(burial_history)} burial steps",
            "migration_efficiency_assumption": "simplified buoyancy-driven vertical migration",
            "seal_capacity_assumption": "static seal capacity vs buoyancy pressure comparison",
        }

        limitations = []
        if charge_age_ma == 0:
            limitations.append("No burial step reached 90°C — source maturity unconstrained")
        if migration_window_my < 0:
            limitations.append(f"Trap age ({trap_age_ma} Ma) is younger than charge age ({charge_age_ma} Ma) — structural timing may be reversed")
        if fault_density > 0.3:
            limitations.append("High fault density (>0.3) increases leakage risk — not fully captured in seal_integrity_estimate")
        if not reversal_conditions:
            limitations.append("Few reversal conditions identified — result is relatively robust within stated assumptions")

        human_decision_point = ""
        if hold_enforced:
            human_decision_point = (
                "888_HOLD: Charge timing is uncertain or unfavourable. "
                "Do not use for decision without human review of burial history, trap age, and seal integrity."
            )
        elif verdict == "improbable":
            human_decision_point = (
                "Verdict is improbable — confirm trap age and burial history before ruling out prospect. "
                "Reversal conditions may apply if new geological data emerges."
            )

        # Basin charge result
        basin_result = {
            "tti": round(tti, 4),
            "easy_ro": round(easy_ro, 4),
            "charge_probability": round(charge_probability, 4),
            "migration_distance_km": round(migration_distance_km, 4),
            "seal_integrity_estimate": round(seal_integrity, 4),
        }

        payload = {
            "verdict": verdict,
            "charge_age_ma": round(charge_age_ma, 4),
            "trap_age_ma": round(trap_age_ma, 4),
            "charge_probability": round(charge_probability, 4),
        }

        return TimingVerificationResult(
            tool="geox_time4d_verify_timing",
            verdict=verdict,
            claim_state=claim_state,
            basin_charge_result=basin_result,
            charge_age_ma=charge_age_ma,
            trap_age_ma=trap_age_ma,
            charge_trap_age_diff_my=charge_trap_age_diff_my,
            migration_window_my=migration_window_my,
            scenario_used="standard_burial",
            burial_carrier_assumptions=burial_carrier_assumptions,
            assumptions=assumptions,
            reversal_conditions=reversal_conditions,
            reversal_scenarios=reversal_scenarios,
            limitations=limitations,
            human_decision_point=human_decision_point,
            vault_receipt=make_vault_receipt("geox_time4d_verify_timing", payload, verdict="HOLD" if hold_enforced else "SEAL"),
        )

    def simulate(
        self,
        burial_history: list[dict[str, float]],
        trap_age_ma: float = 70.0,
        carrier_permeability_md: float = 100.0,
        buoyancy_pressure_mpa: float = 10.0,
        seal_capacity_mpa: float = 25.0,
        fault_density: float = 0.1,
    ) -> BasinChargeResult:
        """Legacy simulate() — delegates to verify_timing for full output."""
        full = self.verify_timing(
            burial_history=burial_history,
            trap_age_ma=trap_age_ma,
            carrier_permeability_md=carrier_permeability_md,
            buoyancy_pressure_mpa=buoyancy_pressure_mpa,
            seal_capacity_mpa=seal_capacity_mpa,
            fault_density=fault_density,
        )
        charge_prob = full.basin_charge_result.get("charge_probability", 0.0)
        return BasinChargeResult(
            tti=full.basin_charge_result.get("tti", 0.0),
            easy_ro=full.basin_charge_result.get("easy_ro", 0.0),
            migration_distance_km=full.basin_charge_result.get("migration_distance_km", 0.0),
            charge_probability=charge_prob,
            seal_integrity_estimate=full.basin_charge_result.get("seal_integrity_estimate", 0.0),
            charge_age_ma=full.charge_age_ma,
            hold_enforced=full.verdict == "improbable",
            claim_tag={
                ClaimTag.OBSERVED: "CLAIM",
                ClaimTag.COMPUTED: "ESTIMATE",
                ClaimTag.HYPOTHESIS: "HYPOTHESIS",
                ClaimTag.UNKNOWN: "UNKNOWN",
                ClaimTag.VOID: "UNKNOWN",
            }.get(full.claim_state, "UNKNOWN"),
            timing_validation={},
            vault_receipt=full.vault_receipt,
        )


def compute_tti(burial_history: list[dict[str, float]]) -> float:
    return BasinChargeSimulator().compute_tti(burial_history)


def compute_easy_ro(burial_history: list[dict[str, float]] | float) -> float:
    simulator = BasinChargeSimulator()
    tti = burial_history if isinstance(burial_history, (int, float)) else simulator.compute_tti(burial_history)
    return simulator.compute_easy_ro(float(tti))


class BasinCharge(BasinChargeSimulator):
    """Compatibility name for Wave2 tests and older callers."""
