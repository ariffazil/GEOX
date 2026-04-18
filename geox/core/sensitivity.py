"""
Sensitivity sweep helpers for GEOX Wave 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from geox.core.ac_risk import compute_ac_risk_governed
from geox.core.governed_output import classify_claim_tag, make_vault_receipt


@dataclass
class SensitivityCase:
    parameter: str
    low_score: float
    base_score: float
    high_score: float
    sensitivity_index: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter,
            "low_score": round(self.low_score, 4),
            "base_score": round(self.base_score, 4),
            "high_score": round(self.high_score, 4),
            "sensitivity_index": round(self.sensitivity_index, 4),
        }


@dataclass
class SensitivitySweepResult:
    base_score: float
    cases: list[SensitivityCase]
    critical_sensitivity: bool
    recommended_verdict: str
    claim_tag: str
    vault_receipt: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_score": round(self.base_score, 4),
            "cases": [case.to_dict() for case in self.cases],
            "critical_sensitivity": self.critical_sensitivity,
            "recommended_verdict": self.recommended_verdict,
            "claim_tag": self.claim_tag,
            "vault_receipt": self.vault_receipt,
        }


class SensitivitySweep:
    """One-at-a-time sensitivity sweep using the governed AC risk engine."""

    def _score(self, base_inputs: dict[str, Any]) -> float:
        result = compute_ac_risk_governed(
            u_ambiguity=float(base_inputs.get("u_ambiguity", 0.3)),
            transform_stack=list(base_inputs.get("transform_stack", ["normalize", "ac_risk"])),
            bias_scenario=str(base_inputs.get("bias_scenario", "ai_vision_only")),
            custom_b_cog=base_inputs.get("custom_b_cog"),
            model_text=base_inputs.get("model_text"),
            truth_score=float(base_inputs.get("truth_score", 0.99)),
            echo_score=float(base_inputs.get("echo_score", 0.0)),
            amanah_locked=bool(base_inputs.get("amanah_locked", True)),
            rasa_present=bool(base_inputs.get("rasa_present", False)),
            irreversible_action=bool(base_inputs.get("irreversible_action", False)),
            prospect_context=base_inputs.get("prospect_context"),
            evidence_credit=float(base_inputs.get("evidence_credit", 0.5)),
        )
        return result.ac_risk_score

    def run(self, base_inputs: dict[str, Any], percent_delta: float = 0.2) -> SensitivitySweepResult:
        base_score = self._score(base_inputs)
        cases: list[SensitivityCase] = []
        for parameter, value in base_inputs.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            low_inputs = dict(base_inputs)
            high_inputs = dict(base_inputs)
            low_inputs[parameter] = value * (1.0 - percent_delta)
            high_inputs[parameter] = value * (1.0 + percent_delta)
            low_score = self._score(low_inputs)
            high_score = self._score(high_inputs)
            delta_score = max(abs(low_score - base_score), abs(high_score - base_score))
            sensitivity_index = delta_score / max(percent_delta, 1e-9)
            cases.append(
                SensitivityCase(
                    parameter=parameter,
                    low_score=low_score,
                    base_score=base_score,
                    high_score=high_score,
                    sensitivity_index=sensitivity_index,
                )
            )

        cases.sort(key=lambda case: case.sensitivity_index, reverse=True)
        critical_sensitivity = bool(cases and cases[0].sensitivity_index > 0.4)
        recommended_verdict = "QUALIFY" if critical_sensitivity else "SEAL"
        payload = {
            "base_score": base_score,
            "top_parameter": cases[0].parameter if cases else None,
            "critical_sensitivity": critical_sensitivity,
        }
        return SensitivitySweepResult(
            base_score=base_score,
            cases=cases,
            critical_sensitivity=critical_sensitivity,
            recommended_verdict=recommended_verdict,
            claim_tag=classify_claim_tag(1.0 - (cases[0].sensitivity_index if cases else 0.0), hold_enforced=critical_sensitivity),
            vault_receipt=make_vault_receipt("geox_run_sensitivity_sweep", payload, verdict=recommended_verdict),
        )
