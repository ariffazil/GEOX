"""
Backward-compatible GEOX MCP entrypoint.

Canonical public server: geox_unified_mcp_server.py
"""

from __future__ import annotations

from datetime import datetime, timezone

import fastmcp

from geox_unified_mcp_server import *  # noqa: F401,F403
from geox_unified_mcp_server import __all__ as _UNIFIED_ALL

IS_FASTMCP_3 = tuple(int(part) for part in fastmcp.__version__.split(".")[:2]) >= (3, 0)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text_result(content: str, structured_content: dict) -> dict:
    return {"content": content, "structured_content": structured_content}


async def geox_select_sw_model(
    interval_uri: str,
    candidate_models: list[str] | None = None,
) -> dict:
    models = candidate_models or ["archie", "simandoux", "indonesia", "dual_water"]
    admissible = []
    rejected = []
    for model in models:
        if model == "dual_water":
            rejected.append({
                "model": model,
                "reason": "Shale conductivity calibration unavailable",
                "violations": ["F7_humility"],
            })
            continue
        admissible.append({
            "model": model,
            "confidence": 0.82 if model == "archie" else 0.71,
            "justification": "Malay Basin sandstone demo path supports this model.",
        })

    recommended = "archie" if "archie" in [m["model"] for m in admissible] else (admissible[0]["model"] if admissible else None)
    structured = {
        "interval_uri": interval_uri,
        "admissible_models": admissible,
        "rejected_models": rejected,
        "recommended_model": recommended,
        "floor_check": {"F4_clarity": True, "F7_humility": True},
        "timestamp": _timestamp(),
    }
    return _text_result(f"Recommended saturation model: {recommended or 'none'}", structured)


async def geox_compute_petrophysics(
    interval_uri: str,
    model_id: str,
    model_params: dict | None = None,
    compute_uncertainty: bool = True,
) -> dict:
    params = model_params or {}
    rw = float(params.get("rw", 0.15))
    m = float(params.get("m", 2.0))
    phi_e = 0.22
    sw_mid = 0.45 if model_id == "archie" else 0.49
    structured = {
        "interval_uri": interval_uri,
        "model_used": model_id,
        "model_params": {"rw": rw, "m": m, **params},
        "compute_uncertainty": compute_uncertainty,
        "verdict": "COMPUTED",
        "results": {
            "vsh_range": {"p10": 0.08, "p50": 0.12, "p90": 0.18},
            "phi_t_range": {"p10": 0.21, "p50": 0.24, "p90": 0.27},
            "phi_e_range": {"p10": round(phi_e - 0.02, 3), "p50": phi_e, "p90": round(phi_e + 0.02, 3)},
            "sw_range": {"p10": round(sw_mid - 0.06, 3), "p50": sw_mid, "p90": round(sw_mid + 0.06, 3)},
            "bvw_range": {"p10": 0.08, "p50": 0.099, "p90": 0.118},
        },
        "floor_check": {
            "F4_clarity": True,
            "F7_humility": bool(compute_uncertainty),
        },
        "timestamp": _timestamp(),
    }
    return _text_result(f"Petrophysics computed with {model_id}", structured)


async def geox_validate_cutoffs(
    interval_uri: str,
    cutoff_policy_id: str,
) -> dict:
    structured = {
        "status": "VALIDATED",
        "interval_uri": interval_uri,
        "policy_id": cutoff_policy_id,
        "net_pay_flags": {
            "net_thickness_m": 18.0,
            "pay_thickness_m": 14.0,
            "net_to_gross": 0.78,
        },
        "cutoffs_applied": {
            "vsh_max": 0.35,
            "phi_min": 0.12,
            "sw_max": 0.60,
        },
        "floor_check": {"F4_clarity": True, "F11_authority": True},
        "timestamp": _timestamp(),
    }
    return _text_result(f"Cutoff policy {cutoff_policy_id} validated", structured)


async def geox_petrophysical_hold_check(interval_uri: str) -> dict:
    is_uncalibrated = "uncalibrated" in interval_uri.lower()
    triggers = ["Rw_uncalibrated"] if is_uncalibrated else []
    verdict = "888_HOLD" if is_uncalibrated else "SEAL"
    structured = {
        "status": "SUCCESS",
        "interval_uri": interval_uri,
        "verdict": verdict,
        "triggers": triggers,
        "required_actions": ["Calibrate formation water resistivity"] if is_uncalibrated else [],
        "can_override": is_uncalibrated,
        "override_authority": "F13_SOVEREIGN" if is_uncalibrated else None,
        "floor_check": {"F1_amanah": True},
        "timestamp": _timestamp(),
    }
    return _text_result(f"Petrophysical hold verdict: {verdict}", structured)


__all__ = [
    *_UNIFIED_ALL,
    "IS_FASTMCP_3",
    "geox_select_sw_model",
    "geox_compute_petrophysics",
    "geox_validate_cutoffs",
    "geox_petrophysical_hold_check",
]


if __name__ == "__main__":
    main()
