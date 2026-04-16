"""
AC_Risk Calculation Engine — Theory of Anomalous Contrast (ToAC)
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

The canonical equation:
    AC_Risk = min(1.0, U_phys × D_transform × B_cog)

Where:
    U_phys = Physical model uncertainty [0.0, 1.0]
    D_transform = Transform distortion factor [1.0, 3.0]
    B_cog = Cognitive bias factor [0.0, 1.0]

Verdict thresholds:
    < 0.15 → SEAL
    0.15–0.34 → QUALIFY
    0.35–0.59 → HOLD (888_HOLD triggered)
    ≥ 0.60 → VOID
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class AC_RiskResult:
    """Result of AC_Risk calculation."""
    ac_risk: float
    verdict: str
    explanation: str
    u_phys: float
    d_transform: float
    b_cog: float
    components: Dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════════════
# Transform Distortion Map (Operational Spec)
# ═══════════════════════════════════════════════════════════════════════════════

TRANSFORM_RISK_MAP = {
    "observational": 1.00,
    "linear_scaling": 1.05,
    "contrast_stretch": 1.10,
    "agc_rms": 1.15,
    "agc_inst": 1.25,
    "clahe": 1.35,
    "spectral_balance": 1.20,
    "depth_conversion": 1.30,
    "gmpe_selection": 1.20,
    "mesh_coarsening": 1.25,
    "ai_segmentation": 1.40,
    "vlm_inference": 1.50,
    "policy_translation": 1.35,
    "stochastic_realization_single": 1.80,
    "stochastic_realization_ensemble": 1.10,
    "openquake_gmpe_logic_tree": 1.15,
    "site_amplification": 1.20,
    "source_model_declustering": 1.10,
}

# ═══════════════════════════════════════════════════════════════════════════════
# Bias Scenarios (Operational Spec)
# ═══════════════════════════════════════════════════════════════════════════════

BIAS_MAP = {
    "physics_validated": 0.20,
    "multi_interpreter": 0.28,
    "ai_with_physics": 0.30,
    "unaided_expert": 0.35,
    "ai_vision_only": 0.42,
    "executive_pressure": 0.55,
    "single_model_collapse": 0.65,
    "confirmation_bias": 0.50,
    "authority_bias": 0.48,
    "anchoring_bias": 0.45,
    "pressure_collapse_conflation": 0.70,
}

# ═══════════════════════════════════════════════════════════════════════════════
# Calibration Registry (per engine, basin, product_type)
# ═══════════════════════════════════════════════════════════════════════════════

_CALIBRATION_REGISTRY: Dict[str, Dict[str, Any]] = {}


def get_calibration_key(engine: str, basin: str, product_type: str) -> str:
    return f"{engine}::{basin}::{product_type}"


def register_calibration_event(
    engine: str,
    basin: str,
    product_type: str,
    misprediction_ratio: float,
    u_phys_adjustment: float = 0.0,
    d_transform_penalty: float = 0.0,
) -> None:
    """Log a calibration event for future AC_Risk tuning."""
    key = get_calibration_key(engine, basin, product_type)
    _CALIBRATION_REGISTRY[key] = {
        "misprediction_ratio": misprediction_ratio,
        "u_phys_adjustment": u_phys_adjustment,
        "d_transform_penalty": d_transform_penalty,
        "events": _CALIBRATION_REGISTRY.get(key, {}).get("events", 0) + 1,
    }


def get_calibration_adjustment(engine: str, basin: str, product_type: str) -> Dict[str, Any]:
    """Retrieve calibration adjustments for a given context."""
    key = get_calibration_key(engine, basin, product_type)
    return _CALIBRATION_REGISTRY.get(key, {
        "u_phys_adjustment": 0.0,
        "d_transform_penalty": 0.0,
        "events": 0,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# U_phys Estimation Helper
# ═══════════════════════════════════════════════════════════════════════════════

BOUNDARY_UNCERTAINTY_MAP = {
    "low": 0.05,
    "medium": 0.15,
    "high": 0.30,
}


def estimate_u_phys(
    data_density: float = 0.0,
    parameter_ignorance_ratio: float = 0.0,
    calibration_residual: float = 0.0,
    signal_range: float = 1.0,
    boundary_condition_uncertainty: str = "low",
    temporal_extrapolation_ratio: float = 0.0,
    engine: str = "",
    basin: str = "",
    product_type: str = "",
) -> Dict[str, Any]:
    """
    Estimate U_phys from five proxies, weighted per TOAC_AC_RISK_SPEC.md.
    Applies calibration adjustments if available.
    """
    S = 1.0 - min(1.0, data_density * 2.0)
    S = max(0.0, min(1.0, S))
    P = max(0.0, min(1.0, parameter_ignorance_ratio))
    R = max(0.0, min(1.0, 0.5 * (calibration_residual / max(signal_range, 1e-9))))
    B = BOUNDARY_UNCERTAINTY_MAP.get(boundary_condition_uncertainty, 0.05)
    T = max(0.0, min(1.0, temporal_extrapolation_ratio))

    u_phys = 0.30 * S + 0.25 * P + 0.25 * R + 0.15 * B + 0.05 * T

    adj = get_calibration_adjustment(engine, basin, product_type)
    u_phys += adj.get("u_phys_adjustment", 0.0)
    u_phys = max(0.0, min(1.0, u_phys))

    return {
        "u_phys": round(u_phys, 4),
        "proxies": {
            "S": round(S, 4),
            "P": round(P, 4),
            "R": round(R, 4),
            "B": round(B, 4),
            "T": round(T, 4),
        },
        "calibration_adjustment": adj.get("u_phys_adjustment", 0.0),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Core AC_Risk Computation
# ═══════════════════════════════════════════════════════════════════════════════

def compute_d_transform(transform_stack: List[str]) -> float:
    """Compute D_transform from a stack of transform names."""
    d_transform = 1.0
    for transform in transform_stack:
        d_transform *= TRANSFORM_RISK_MAP.get(transform, 1.25)
    return min(d_transform, 3.0)


def compute_b_cog(
    bias_scenario: str,
    custom_b_cog: Optional[float] = None,
    session_history: Optional[List[Dict[str, Any]]] = None,
    hypotheses_count: int = 1,
    deadline: Optional[datetime] = None,
    complexity_score: float = 0.5,
    auto_detect_bias: bool = False,
) -> Dict[str, Any]:
    """
    Compute B_cog from scenario or custom value.
    If auto_detect_bias=True, runs BiasDetector heuristics.
    """
    if custom_b_cog is not None:
        return {
            "b_cog": max(0.0, min(1.0, custom_b_cog)),
            "scenario": "custom",
            "modifiers": [],
        }

    if auto_detect_bias and session_history is not None:
        from geox.core.bias_detector import BiasDetector
        detection = BiasDetector.detect(
            claimed_scenario=bias_scenario,
            session_history=session_history,
            hypotheses_count=hypotheses_count,
            deadline=deadline,
            complexity_score=complexity_score,
        )
        return {
            "b_cog": detection["b_cog"],
            "scenario": detection["detected_scenario"],
            "modifiers": detection["modifiers"],
            "audit": detection.get("audit"),
        }

    return {
        "b_cog": BIAS_MAP.get(bias_scenario, 0.42),
        "scenario": bias_scenario,
        "modifiers": [],
    }


def compute_ac_risk(
    u_phys: float,
    transform_stack: List[str],
    bias_scenario: str = "ai_vision_only",
    custom_b_cog: Optional[float] = None,
    engine: str = "",
    basin: str = "",
    product_type: str = "",
    session_history: Optional[List[Dict[str, Any]]] = None,
    hypotheses_count: int = 1,
    deadline: Optional[datetime] = None,
    complexity_score: float = 0.5,
    auto_detect_bias: bool = False,
) -> AC_RiskResult:
    """
    Calculate Theory of Anomalous Contrast (ToAC) risk score.
    """
    u_phys = max(0.0, min(1.0, u_phys))

    d_transform = compute_d_transform(transform_stack)
    adj = get_calibration_adjustment(engine, basin, product_type)
    d_transform += adj.get("d_transform_penalty", 0.0)
    d_transform = min(d_transform, 3.0)

    b_cog_result = compute_b_cog(
        bias_scenario=bias_scenario,
        custom_b_cog=custom_b_cog,
        session_history=session_history,
        hypotheses_count=hypotheses_count,
        deadline=deadline,
        complexity_score=complexity_score,
        auto_detect_bias=auto_detect_bias,
    )
    b_cog = b_cog_result["b_cog"]

    ac_risk = u_phys * d_transform * b_cog
    ac_risk = max(0.0, min(1.0, ac_risk))

    if ac_risk < 0.15:
        verdict = "SEAL"
        explanation = (
            f"AC_Risk={ac_risk:.3f}: Low risk. Physical grounding strong. "
            "Proceed with standard QC."
        )
    elif ac_risk < 0.35:
        verdict = "QUALIFY"
        explanation = (
            f"AC_Risk={ac_risk:.3f}: Moderate risk. Proceed with caveats. "
            "Document assumptions per F2 Truth."
        )
    elif ac_risk < 0.60:
        verdict = "HOLD"
        explanation = (
            f"AC_Risk={ac_risk:.3f}: Elevated risk. Human review required per 888_HOLD. "
            "Escalate to qualified interpreter."
        )
    else:
        verdict = "VOID"
        explanation = (
            f"AC_Risk={ac_risk:.3f}: Critical risk. Interpretation unsafe. "
            "Acquire better data or ground-truth validation."
        )

    components = {
        "u_phys": round(u_phys, 4),
        "d_transform": round(d_transform, 4),
        "b_cog": round(b_cog, 4),
        "transform_stack": transform_stack,
        "bias_scenario": b_cog_result.get("scenario", bias_scenario),
        "calibration_events": adj.get("events", 0),
    }
    if b_cog_result.get("modifiers"):
        components["bias_modifiers"] = b_cog_result["modifiers"]
    if b_cog_result.get("audit"):
        components["bias_audit"] = b_cog_result["audit"]

    return AC_RiskResult(
        ac_risk=round(ac_risk, 4),
        verdict=verdict,
        explanation=explanation,
        u_phys=round(u_phys, 4),
        d_transform=round(d_transform, 4),
        b_cog=round(b_cog, 4),
        components=components,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Backward-Compatible ACRiskCalculator Class Wrapper
# ═══════════════════════════════════════════════════════════════════════════════

class ACRiskCalculator:
    """
    Class-based wrapper around compute_ac_risk for backward compatibility
    with tools that call ACRiskCalculator.calculate(...).
    """

    @staticmethod
    def calculate(
        u_phys: float,
        transform_stack: List[str],
        bias_scenario: str = "ai_vision_only",
        custom_b_cog: Optional[float] = None,
        engine: str = "",
        basin: str = "",
        product_type: str = "",
        session_history: Optional[List[Dict[str, Any]]] = None,
        auto_detect_bias: bool = False,
    ) -> "ACRiskResultCompat":
        result = compute_ac_risk(
            u_phys=u_phys,
            transform_stack=transform_stack,
            bias_scenario=bias_scenario,
            custom_b_cog=custom_b_cog,
            engine=engine,
            basin=basin,
            product_type=product_type,
            session_history=session_history,
            auto_detect_bias=auto_detect_bias,
        )
        # Return a compat object with .verdict.value access patterns
        return ACRiskResultCompat(result)


class ACRiskResultCompat:
    """
    Compatibility shim that exposes both dict-like and object-like interfaces
    expected by existing callers (e.g., contracts.tools.well).
    """

    def __init__(self, result: AC_RiskResult):
        self._result = result
        self.ac_risk = result.ac_risk
        self.verdict = _VerdictCompat(result.verdict)
        self.explanation = result.explanation
        self.u_phys = result.u_phys
        self.d_transform = result.d_transform
        self.b_cog = result.b_cog
        self.components = result.components

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ac_risk": self.ac_risk,
            "verdict": self.verdict.value,
            "explanation": self.explanation,
            "u_phys": self.u_phys,
            "d_transform": self.d_transform,
            "b_cog": self.b_cog,
            "components": self.components,
        }


class _VerdictCompat:
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# Verdict with Floor Overrides
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_verdict(
    ac_risk: float,
    u_phys: float,
    d_transform: float,
    b_cog: float,
    mandatory_888_hold: bool = False,
    upstream_verdicts: Optional[List[str]] = None,
    calibration_misprediction_ratio: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compute final verdict with floor overrides per TOAC_AC_RISK_SPEC.md.
    """
    if ac_risk >= 0.60:
        base_verdict = "VOID"
    elif ac_risk >= 0.35:
        base_verdict = "HOLD"
    elif ac_risk >= 0.15:
        base_verdict = "QUALIFY"
    else:
        base_verdict = "SEAL"

    overrides = []

    if u_phys > 0.40:
        if base_verdict == "SEAL":
            base_verdict = "QUALIFY"
        overrides.append("F2")

    if u_phys > 0.60 and base_verdict in ("SEAL", "QUALIFY"):
        base_verdict = "HOLD"
        overrides.append("F7")

    if (b_cog > 0.50 or d_transform > 2.5) and base_verdict in ("SEAL", "QUALIFY"):
        base_verdict = "HOLD"
        overrides.append("F9")

    if d_transform >= 1.80 and base_verdict in ("SEAL", "QUALIFY"):
        base_verdict = "HOLD"
        overrides.append("F1")

    if upstream_verdicts:
        severity = {"SEAL": 0, "QUALIFY": 1, "HOLD": 2, "VOID": 3}
        worst = max(upstream_verdicts, key=lambda v: severity.get(v, 0))
        if severity.get(worst, 0) > severity.get(base_verdict, 0):
            base_verdict = worst
            overrides.append("UPSTREAM")

    if calibration_misprediction_ratio is not None and calibration_misprediction_ratio > 2.0:
        downgrade = {"SEAL": "QUALIFY", "QUALIFY": "HOLD", "HOLD": "VOID", "VOID": "VOID"}
        base_verdict = downgrade.get(base_verdict, "VOID")
        overrides.append("CALIBRATION")

    if mandatory_888_hold:
        base_verdict = "HOLD"
        overrides.append("F13")

    return {
        "verdict": base_verdict,
        "ac_risk": round(ac_risk, 4),
        "overrides": overrides,
        "requires_human_approval": base_verdict in ("HOLD", "VOID"),
    }
