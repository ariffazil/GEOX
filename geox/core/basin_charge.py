"""
Basin charge simulation utilities for GEOX Wave 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log10
from typing import Any

from geox.core.governed_output import classify_claim_tag, make_vault_receipt
from geox.core.physics_guard import PhysicsGuard


@dataclass
class BasinChargeResult:
    tti: float
    easy_ro: float
    migration_distance_km: float
    charge_probability: float
    seal_integrity_estimate: float
    hold_enforced: bool
    claim_tag: str
    timing_validation: dict[str, Any]
    vault_receipt: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tti": round(self.tti, 4),
            "easy_ro": round(self.easy_ro, 4),
            "migration_distance_km": round(self.migration_distance_km, 4),
            "charge_probability": round(self.charge_probability, 4),
            "seal_integrity_estimate": round(self.seal_integrity_estimate, 4),
            "hold_enforced": self.hold_enforced,
            "claim_tag": self.claim_tag,
            "timing_validation": self.timing_validation,
            "vault_receipt": self.vault_receipt,
        }


class BasinChargeSimulator:
    """Run a simplified Lopatin/Easy%Ro charge workflow."""

    def __init__(self, guard: PhysicsGuard | None = None) -> None:
        self.guard = guard or PhysicsGuard()

    def compute_tti(self, burial_history: list[dict[str, float]]) -> float:
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

    def simulate(
        self,
        burial_history: list[dict[str, float]],
        trap_age_ma: float,
        carrier_permeability_md: float,
        buoyancy_pressure_mpa: float,
        seal_capacity_mpa: float,
        fault_density: float = 0.1,
    ) -> BasinChargeResult:
        tti = self.compute_tti(burial_history)
        easy_ro = self.compute_easy_ro(tti)
        charge_age_ma = max(step["age_ma"] for step in burial_history if step["temperature_c"] >= 90.0)
        timing_validation = self.guard.check_charge_timing(charge_age_ma, trap_age_ma)
        migration_distance_km = max(0.0, buoyancy_pressure_mpa * max(carrier_permeability_md, 1.0) / 1000.0)
        maturity_factor = max(0.0, min(1.0, (easy_ro - 0.5) / 0.8))
        migration_factor = max(0.0, min(1.0, migration_distance_km / 25.0))
        seal_integrity = max(0.0, min(1.0, (seal_capacity_mpa / max(buoyancy_pressure_mpa, 1e-6)) - fault_density * 0.25))
        charge_probability = max(0.0, min(1.0, 0.45 * maturity_factor + 0.3 * migration_factor + 0.25 * seal_integrity))
        hold_enforced = timing_validation.hold
        confidence = max(0.0, min(1.0, charge_probability * seal_integrity))
        payload = {
            "tti": tti,
            "easy_ro": easy_ro,
            "migration_distance_km": migration_distance_km,
            "charge_probability": charge_probability,
        }
        return BasinChargeResult(
            tti=tti,
            easy_ro=easy_ro,
            migration_distance_km=migration_distance_km,
            charge_probability=charge_probability,
            seal_integrity_estimate=seal_integrity,
            hold_enforced=hold_enforced,
            claim_tag=classify_claim_tag(confidence, hold_enforced=hold_enforced),
            timing_validation=timing_validation.to_dict(),
            vault_receipt=make_vault_receipt("geox_simulate_basin_charge", payload, verdict="HOLD" if hold_enforced else "SEAL"),
        )
