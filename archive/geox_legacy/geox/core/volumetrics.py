"""
Probabilistic volumetrics for GEOX Wave 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from geox.core.governed_output import classify_claim_tag, make_vault_receipt
from geox.core.physics_guard import PhysicsGuard


@dataclass
class TriangularDist:
    min: float
    ml: float
    max: float

    def to_spec(self) -> dict[str, float]:
        return {"min": self.min, "ml": self.ml, "max": self.max}


@dataclass
class LognormalDist:
    mean: float
    stddev: float

    def to_spec(self) -> dict[str, float | str]:
        return {"mean": self.mean, "stddev": self.stddev, "kind": "lognormal"}


@dataclass
class VolumeDistribution:
    p10: float
    p50: float
    p90: float
    mean: float
    stdev: float
    valid_draws: int
    rejected_draws: int
    hold_enforced: bool
    claim_tag: str
    tornado: dict[str, float]
    vault_receipt: dict[str, Any]
    physics_validation: dict[str, Any]

    @property
    def n_valid(self) -> int:
        return self.valid_draws

    @property
    def n_draws(self) -> int:
        return self.valid_draws + self.rejected_draws

    @property
    def posterior_ratio(self) -> float:
        return self.p90 / max(self.p10, 1e-9)

    @property
    def tornado_data(self) -> list[dict[str, float | str]]:
        rows = [
            {"parameter": key, "impact": value, "abs_impact": abs(value)}
            for key, value in self.tornado.items()
        ]
        return sorted(rows, key=lambda row: float(row["abs_impact"]), reverse=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "p10": round(self.p10, 4),
            "p50": round(self.p50, 4),
            "p90": round(self.p90, 4),
            "mean": round(self.mean, 4),
            "stdev": round(self.stdev, 4),
            "valid_draws": self.valid_draws,
            "rejected_draws": self.rejected_draws,
            "n_valid": self.n_valid,
            "n_draws": self.n_draws,
            "posterior_ratio": round(self.posterior_ratio, 4),
            "hold_enforced": self.hold_enforced,
            "claim_tag": self.claim_tag,
            "tornado": {key: round(value, 4) for key, value in self.tornado.items()},
            "tornado_data": self.tornado_data,
            "vault_receipt": self.vault_receipt,
            "physics_validation": self.physics_validation,
        }


class ProbabilisticVolumetrics:
    """Monte Carlo HCPV calculator with PhysicsGuard validation."""

    def __init__(
        self,
        guard: PhysicsGuard | None = None,
        draws: int = 10_000,
        seed: int = 7,
        n_draws: int | None = None,
    ) -> None:
        self.guard = guard or PhysicsGuard()
        self.draws = n_draws if n_draws is not None else draws
        self.rng = np.random.default_rng(seed)

    def _sample_distribution(self, spec: float | dict[str, float]) -> np.ndarray:
        if hasattr(spec, "to_spec"):
            spec = spec.to_spec()
        if isinstance(spec, (int, float)):
            return np.full(self.draws, float(spec), dtype=float)
        if {"min", "ml", "max"}.issubset(spec):
            return self.rng.triangular(spec["min"], spec["ml"], spec["max"], self.draws)
        if {"mean", "stddev"}.issubset(spec):
            samples = self.rng.normal(spec["mean"], spec["stddev"], self.draws)
            if spec.get("kind") == "lognormal":
                samples = np.exp(samples)
            return samples
        raise ValueError(f"Unsupported distribution spec: {spec}")

    def compute_hcpv(
        self,
        grv_dist: float | dict[str, float],
        ntg_dist: float | dict[str, float],
        phi_dist: float | dict[str, float],
        sw_dist: float | dict[str, float],
        fvf_dist: float | dict[str, float] | None = None,
        fvf: float | None = None,
    ) -> VolumeDistribution:
        grv = self._sample_distribution(grv_dist)
        ntg = self._sample_distribution(ntg_dist)
        phi = self._sample_distribution(phi_dist)
        sw = self._sample_distribution(sw_dist)
        fvf_spec = fvf if fvf is not None else fvf_dist
        if fvf_spec is None:
            fvf_spec = 1.0
        fvf = np.maximum(self._sample_distribution(fvf_spec), 1e-6)

        hcpv_samples: list[float] = []
        rejected_draws = 0
        first_violation: dict[str, Any] | None = None
        for idx in range(self.draws):
            validation = self.guard.validate({"porosity": float(phi[idx]), "sw": float(sw[idx])})
            if validation.hold or ntg[idx] < 0.0 or ntg[idx] > 1.0:
                rejected_draws += 1
                if first_violation is None:
                    first_violation = validation.to_dict()
                continue
            hcpv_samples.append(float(grv[idx] * ntg[idx] * phi[idx] * (1.0 - sw[idx]) / fvf[idx]))

        if not hcpv_samples:
            raise ValueError("No valid Monte Carlo draws survived PhysicsGuard validation")

        samples = np.array(hcpv_samples, dtype=float)
        p10, p50, p90 = np.percentile(samples, [10, 50, 90])
        posterior = self.guard.check_volumetric_output({"p10": float(p10), "p50": float(p50), "p90": float(p90)})
        hold_enforced = posterior.hold
        tornado = {
            "grv": float(np.std(grv) / max(np.mean(grv), 1e-6)),
            "ntg": float(np.std(ntg) / max(np.mean(ntg), 1e-6)),
            "phi": float(np.std(phi) / max(np.mean(phi), 1e-6)),
            "sw": float(np.std(sw) / max(np.mean(sw), 1e-6)),
            "fvf": float(np.std(fvf) / max(np.mean(fvf), 1e-6)),
        }
        confidence = max(0.0, 1.0 - min((float(p90) / max(float(p10), 1e-6)) / 10.0, 1.0))
        payload = {
            "p10": float(p10),
            "p50": float(p50),
            "p90": float(p90),
            "mean": float(samples.mean()),
            "ratio": float(p90 / max(p10, 1e-6)),
        }
        return VolumeDistribution(
            p10=float(p10),
            p50=float(p50),
            p90=float(p90),
            mean=float(samples.mean()),
            stdev=float(samples.std()),
            valid_draws=len(hcpv_samples),
            rejected_draws=rejected_draws,
            hold_enforced=hold_enforced,
            claim_tag=classify_claim_tag(confidence, hold_enforced=hold_enforced),
            tornado=tornado,
            vault_receipt=make_vault_receipt(
                "geox_compute_volume_probabilistic",
                payload,
                verdict="HOLD" if hold_enforced else "SEAL",
            ),
            physics_validation={
                "posterior": posterior.to_dict(),
                "first_violation": first_violation,
            },
        )
