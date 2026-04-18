"""
Multi-model petrophysical saturation ensemble for GEOX Wave 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np

from geox.core.governed_output import classify_claim_tag, make_vault_receipt
from geox.core.physics_guard import PhysicsGuard


@dataclass
class EnsembleModelResult:
    name: str
    sw: float
    physics_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "sw": round(self.sw, 4),
            "physics_status": self.physics_status,
        }


@dataclass
class PetroEnsembleResult:
    models: list[EnsembleModelResult]
    mean: float
    p10: float
    p50: float
    p90: float
    disagreement_band: float
    hold_enforced: bool
    claim_tag: str
    physics_validation: dict[str, Any]
    vault_receipt: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "models": [model.to_dict() for model in self.models],
            "mean": round(self.mean, 4),
            "p10": round(self.p10, 4),
            "p50": round(self.p50, 4),
            "p90": round(self.p90, 4),
            "disagreement_band": round(self.disagreement_band, 4),
            "hold_enforced": self.hold_enforced,
            "claim_tag": self.claim_tag,
            "physics_validation": self.physics_validation,
            "vault_receipt": self.vault_receipt,
        }


class PetroEnsemble:
    """Compute Archie, Indonesia, and Simandoux saturation estimates."""

    def __init__(self, guard: PhysicsGuard | None = None) -> None:
        self.guard = guard or PhysicsGuard()

    @staticmethod
    def _clamp_sw(value: float) -> float:
        return max(0.0, min(1.0, value))

    def _archie(self, rt: float, phi: float, rw: float, a: float, m: float, n: float) -> float:
        water_term = max((a * rw) / max((phi**m) * rt, 1e-9), 1e-9)
        return self._clamp_sw(water_term ** (1.0 / n))

    def _indonesia(
        self,
        rt: float,
        phi: float,
        rw: float,
        vsh: float,
        a: float,
        m: float,
        n: float,
        rsh: float,
    ) -> float:
        shale_term = (vsh ** max(0.01, (1.0 - vsh))) / sqrt(max(rsh, 1e-6))
        clean_term = sqrt(max(phi**m / max(a * rw, 1e-9), 1e-9))
        conductivity = max((1.0 / sqrt(max(rt, 1e-9))) - shale_term, 0.0)
        return self._clamp_sw((conductivity / max(clean_term, 1e-9)) ** (2.0 / n))

    def _simandoux(
        self,
        rt: float,
        phi: float,
        rw: float,
        vsh: float,
        a: float,
        m: float,
        n: float,
        rsh: float,
    ) -> float:
        shale_conductivity = vsh / max(rsh, 1e-6)
        water_conductivity = max((1.0 / max(rt, 1e-9)) - shale_conductivity, 0.0)
        saturation_term = max((water_conductivity * a * rw) / max(phi**m, 1e-9), 1e-9)
        return self._clamp_sw(saturation_term ** (1.0 / n))

    def compute_sw_ensemble(
        self,
        rt: float,
        phi: float,
        rw: float,
        vsh: float,
        temp: float,
        a: float = 1.0,
        m: float = 2.0,
        n: float = 2.0,
        rsh: float | None = None,
    ) -> PetroEnsembleResult:
        """Compute the three canonical Sw models and summarize their spread."""
        effective_rsh = rsh if rsh is not None else max(rw * (5.0 + temp / 100.0), 1.5)
        models = [
            EnsembleModelResult("archie", self._archie(rt, phi, rw, a, m, n), "PASS"),
            EnsembleModelResult("indonesia", self._indonesia(rt, phi, rw, vsh, a, m, n, effective_rsh), "PASS"),
            EnsembleModelResult("simandoux", self._simandoux(rt, phi, rw, vsh, a, m, n, effective_rsh), "PASS"),
        ]

        validations: dict[str, Any] = {}
        invalid_models: list[str] = []
        for model in models:
            validation = self.guard.validate({"sw": model.sw, "porosity": phi, "vsh": vsh})
            validations[model.name] = validation.to_dict()
            if validation.hold:
                model.physics_status = validation.status
                invalid_models.append(model.name)

        values = np.array([model.sw for model in models], dtype=float)
        p10, p50, p90 = np.percentile(values, [10, 50, 90])
        disagreement_band = float(p90 - p10)
        hold_enforced = disagreement_band > 0.20 or bool(invalid_models)
        confidence = max(0.0, 1.0 - disagreement_band - 0.1 * len(invalid_models))
        claim_tag = classify_claim_tag(confidence, hold_enforced=hold_enforced)
        payload = {
            "mean": float(values.mean()),
            "p10": float(p10),
            "p50": float(p50),
            "p90": float(p90),
            "disagreement_band": disagreement_band,
            "invalid_models": invalid_models,
        }
        return PetroEnsembleResult(
            models=models,
            mean=float(values.mean()),
            p10=float(p10),
            p50=float(p50),
            p90=float(p90),
            disagreement_band=disagreement_band,
            hold_enforced=hold_enforced,
            claim_tag=claim_tag,
            physics_validation=validations,
            vault_receipt=make_vault_receipt("geox_compute_sw_ensemble", payload, verdict="HOLD" if hold_enforced else "SEAL"),
        )
