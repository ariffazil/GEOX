"""
Multi-model petrophysical saturation ensemble for GEOX Wave 2 — Improved v2
DITEMPA BUKAN DIBERI

Improvement spec applied:
  - Required output: saturation model, required_curves_present/absent,
    applied_defaults, interval_coverage, confidence_limitations,
    prerequisite_qc_state, claim_state, vault_receipt

Every output carries:
  - claim_state: OBSERVED | COMPUTED | HYPOTHESIS | VOID
  - provenance: trace from QC input to model output
  - limitations: what limits confidence
  - human_decision_point: where human judgment is required
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Any, Optional

import numpy as np

from geox.core.governed_output import classify_claim_tag, make_vault_receipt
from geox.core.physics_guard import PhysicsGuard


class ClaimTag(str):
    OBSERVED = "OBSERVED"
    COMPUTED = "COMPUTED"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"
    VOID = "VOID"


@dataclass
class EnsembleModelResult:
    name: str
    sw: float
    physics_status: str
    is_defaulted: bool = False
    defaulted_params: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "name": self.name,
            "sw": round(self.sw, 4),
            "physics_status": self.physics_status,
            "is_defaulted": self.is_defaulted,
        }
        if self.defaulted_params:
            d["defaulted_params"] = self.defaulted_params
        return d


@dataclass
class PetroEnsembleResult:
    """Output schema for geox_well_compute_petrophysics — v2."""
    tool: str = "geox_well_compute_petrophysics"
    # Required per spec
    saturation_model: str = ""          # Archie | Indonesia | Simandoux
    required_curves_present: list[str] = field(default_factory=list)
    required_curves_absent: list[str] = field(default_factory=list)
    applied_defaults: dict = field(default_factory=dict)
    interval_coverage: dict = field(default_factory=dict)  # {top_md, bottom_md, net_m}
    confidence_limitations: list[str] = field(default_factory=list)
    prerequisite_qc_state: str = ""      # reference to geox_well_qc_logs output
    # Computed values
    models: list[EnsembleModelResult] = field(default_factory=list)
    mean: float = 0.0
    p10: float = 0.0
    p50: float = 0.0
    p90: float = 0.0
    disagreement_band: float = 0.0
    phi_eff_range: list[float] = field(default_factory=list)
    sw_range: list[float] = field(default_factory=list)
    # Governance
    hold_enforced: bool = False
    claim_state: str = ClaimTag.UNKNOWN
    limitations: list[str] = field(default_factory=list)
    human_decision_point: str = ""
    vault_receipt: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "saturation_model": self.saturation_model,
            "required_curves_present": self.required_curves_present,
            "required_curves_absent": self.required_curves_absent,
            "applied_defaults": self.applied_defaults,
            "interval_coverage": self.interval_coverage,
            "confidence_limitations": self.confidence_limitations,
            "prerequisite_qc_state": self.prerequisite_qc_state,
            "models": [m.to_dict() for m in self.models],
            "mean": round(self.mean, 4),
            "p10": round(self.p10, 4),
            "p50": round(self.p50, 4),
            "p90": round(self.p90, 4),
            "disagreement_band": round(self.disagreement_band, 4),
            "phi_eff_range": [round(v, 4) for v in self.phi_eff_range],
            "sw_range": [round(v, 4) for v in self.sw_range],
            "hold_enforced": self.hold_enforced,
            "claim_state": self.claim_state,
            "limitations": self.limitations,
            "human_decision_point": self.human_decision_point,
            "vault_receipt": self.vault_receipt,
        }


class PetroEnsemble:
    """Compute Archie, Indonesia, and Simandoux saturation estimates — v2."""

    REQUIRED_INPUT_PARAMS = ["rt", "phi", "rw", "vsh"]
    OPTIONAL_PARAMS = ["a", "m", "n", "rsh"]
    PARAM_DEFAULTS = {"a": 1.0, "m": 2.0, "n": 2.0}
    PHI_EFF_MIN, PHI_EFF_MAX = 0.01, 0.40
    SW_MIN, SW_MAX = 0.0, 1.0

    def __init__(self, guard: PhysicsGuard | None = None) -> None:
        self.guard = guard or PhysicsGuard()

    @staticmethod
    def _clamp_sw(value: float) -> float:
        return max(0.0, min(1.0, value))

    def _archie(self, rt: float, phi: float, rw: float, a: float, m: float, n: float) -> EnsembleModelResult:
        water_term = max((a * rw) / max((phi**m) * rt, 1e-9), 1e-9)
        sw = self._clamp_sw(water_term ** (1.0 / n))
        status = "PASS" if (0 < sw < 1) else "FAIL"
        return EnsembleModelResult(name="archie", sw=sw, physics_status=status)

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
    ) -> EnsembleModelResult:
        shale_term = (vsh ** max(0.01, (1.0 - vsh))) / sqrt(max(rsh, 1e-6))
        clean_term = sqrt(max(phi**m / max(a * rw, 1e-9), 1e-9))
        conductivity = max((1.0 / sqrt(max(rt, 1e-9))) - shale_term, 0.0)
        sw = self._clamp_sw((conductivity / max(clean_term, 1e-9)) ** (2.0 / n))
        status = "PASS" if (0 < sw < 1) else "FAIL"
        return EnsembleModelResult(name="indonesia", sw=sw, physics_status=status)

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
    ) -> EnsembleModelResult:
        shale_conductivity = vsh / max(rsh, 1e-6)
        water_conductivity = max((1.0 / max(rt, 1e-9)) - shale_conductivity, 0.0)
        saturation_term = max((water_conductivity * a * rw) / max(phi**m, 1e-9), 1e-9)
        sw = self._clamp_sw(saturation_term ** (1.0 / n))
        status = "PASS" if (0 < sw < 1) else "FAIL"
        return EnsembleModelResult(name="simandoux", sw=sw, physics_status=status)

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
        # ── v2 required inputs ──────────────────────
        required_curves: list[str] | None = None,
        top_md: float | None = None,
        bottom_md: float | None = None,
        qc_state_ref: str = "",
        user_inputs: dict | None = None,
        user_defaults: dict | None = None,
    ) -> PetroEnsembleResult:
        """
        Compute three Sw models. All v2 traceability fields are emitted.

        Args:
            required_curves: list of curve mnemonics that were expected
            top_md, bottom_md: interval top and bottom measured depth (m)
            qc_state_ref: reference to geox_well_qc_logs qc_overall output
            user_inputs: dict of {param: value} actually provided by user
            user_defaults: dict of {param: default_value} applied automatically
        """
        user_inputs = user_inputs or {}
        user_defaults = user_defaults or {}
        required_curves = required_curves or []

        # Track applied defaults
        applied: dict[str, Any] = {}
        effective_rsh = rsh if rsh is not None else max(rw * (5.0 + temp / 100.0), 1.5)
        if rsh is None:
            applied["rsh"] = {"value": effective_rsh, "source": "computed_from_rw_and_temp"}
        for param, default in self.PARAM_DEFAULTS.items():
            if param not in user_inputs:
                applied[param] = {"value": default, "source": "default"}

        # Check required curves present/absent
        user_keys = set(user_inputs.keys()) if user_inputs else set()
        present = [p for p in self.REQUIRED_INPUT_PARAMS if p in user_keys]
        absent = [p for p in self.REQUIRED_INPUT_PARAMS if p not in user_keys]

        # Handle absent vsh gracefully
        effective_vsh = vsh if vsh is not None else 0.0

        # Compute models
        models = [
            self._archie(rt, phi, rw, a, m, n),
            self._indonesia(rt, phi, rw, effective_vsh, a, m, n, effective_rsh),
            self._simandoux(rt, phi, rw, effective_vsh, a, m, n, effective_rsh),
        ]

        # Mark defaulted params
        for model in models:
            if model.name == "indonesia" and rsh is None:
                model.is_defaulted = True
                model.defaulted_params = {"rsh": round(effective_rsh, 4)}
            if "a" in applied and not ("a" in user_inputs):
                if not model.defaulted_params:
                    model.defaulted_params = {}
                model.defaulted_params.setdefault("a", applied["a"]["value"])
            if "m" in applied and not ("m" in user_inputs):
                if not model.defaulted_params:
                    model.defaulted_params = {}
                model.defaulted_params.setdefault("m", applied["m"]["value"])

        # PhysicsGuard validation
        validations: dict[str, Any] = {}
        invalid_models: list[str] = []
        for model in models:
            validation = self.guard.validate({
                "sw": model.sw,
                "porosity": phi,
                "vsh": effective_vsh,
            })
            validations[model.name] = validation.to_dict()
            if validation.hold:
                model.physics_status = validation.status
                invalid_models.append(model.name)

        # Statistics
        sw_values = np.array([m.sw for m in models], dtype=float)
        p10, p50, p90 = np.percentile(sw_values, [10, 50, 90])
        disagreement_band = float(p90 - p10)
        hold_enforced = disagreement_band > 0.20 or bool(invalid_models)

        # Interval coverage
        net_m = round((bottom_md - top_md), 1) if (top_md and bottom_md) else None

        # Confidence limitations
        limitations: list[str] = []
        if absent:
            limitations.append(f"Required input parameters absent: {absent}")
        if invalid_models:
            limitations.append(f"PhysicsGuard violations: {invalid_models}")
        if disagreement_band > 0.20:
            limitations.append(f"Model disagreement band {disagreement_band:.2f} exceeds 0.20 — interpretations may differ significantly")
        if net_m and net_m < 10.0:
            limitations.append(f"Thin interval ({net_m}m) — Sw estimates have higher uncertainty")

        # Determine claim state
        if absent:
            claim_state = ClaimTag.HYPOTHESIS
        elif hold_enforced:
            claim_state = ClaimTag.HYPOTHESIS
        elif disagreement_band > 0.15:
            claim_state = ClaimTag.COMPUTED
        else:
            claim_state = ClaimTag.COMPUTED  # petrophysics is always computed

        # Human decision point
        human_decision_point = ""
        if hold_enforced:
            human_decision_point = (
                f"888_HOLD: Model disagreement ({disagreement_band:.2f}) or "
                f"physics violations detected. Do not use for decision without human review. "
                f"Review models: {[m.name for m in models if m.physics_status != 'PASS']}"
            )

        # phi_eff and sw ranges
        phi_eff_range = [
            round(max(self.PHI_EFF_MIN, phi * 0.8), 4),
            round(min(self.PHI_EFF_MAX, phi * 1.2), 4),
        ]
        sw_range = [round(float(p10), 4), round(float(p90), 4)]

        payload = {k: v for k, v in {
            "saturation_model": "Archie/Indonesia/Simandoux ensemble",
            "required_curves_present": present,
            "required_curves_absent": absent,
            "applied_defaults": applied,
            "interval_coverage": {"top_md": top_md, "bottom_md": bottom_md, "net_m": net_m},
            "mean": float(sw_values.mean()),
            "p10": float(p10), "p50": float(p50), "p90": float(p90),
            "disagreement_band": disagreement_band,
        }.items() if v is not None}

        verdict = "HOLD" if hold_enforced else "SEAL"
        vault_receipt = make_vault_receipt("geox_well_compute_petrophysics", payload, verdict)

        return PetroEnsembleResult(
            saturation_model="Archie/Indonesia/Simandoux ensemble",
            required_curves_present=present,
            required_curves_absent=absent,
            applied_defaults=applied,
            interval_coverage={"top_md": top_md, "bottom_md": bottom_md, "net_m": net_m} if top_md else {},
            confidence_limitations=limitations,
            prerequisite_qc_state=qc_state_ref,
            models=models,
            mean=float(sw_values.mean()),
            p10=float(p10),
            p50=float(p50),
            p90=float(p90),
            disagreement_band=disagreement_band,
            phi_eff_range=phi_eff_range,
            sw_range=sw_range,
            hold_enforced=hold_enforced,
            claim_state=claim_state,
            limitations=limitations,
            human_decision_point=human_decision_point,
            vault_receipt=vault_receipt,
        )
