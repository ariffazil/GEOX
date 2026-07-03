"""
sts_rift_bridge.py — Rift Kinematics → STS BasinState Bridge (P1)
==================================================================
Maps rift kinematics (β + subsidence) to BasinState transitions.

This is the P0×P1 intersection:
  P0 (GPlates): WHERE was the basin?
  P1 (McKenzie): WHY did it subside?
  Bridge: WHAT BasinState does this imply?

DITEMPA BUKAN DIBERI — Forged, Not Given.
Forged: 2026-07-03
"""

from __future__ import annotations

from typing import Any

# ═══════════════════════════════════════════════════════════════════════════
# Pure mapping — no I/O, no side effects. TESTable standalone.
# ═══════════════════════════════════════════════════════════════════════════

# Canonical mapping: RiftPhase → BasinState
_RIFT_TO_BASIN_STATE: dict[str, str] = {
    "prerift": "prerift",
    "syn_rift": "syn_rift_1",
    "breakup": "breakup",
    "post_rift": "post_rift_sag",
    "thermal_sag": "thermal_subsidence",
}


def rift_phase_to_basin_state(rift_phase_value: str) -> str:
    """Map RiftPhase → BasinState value. Returns 'unknown' if no match."""
    return _RIFT_TO_BASIN_STATE.get(rift_phase_value, "unknown")


def compute_basin_state_sequence(
    beta: float,
    time_since_rift_ma: float,
    subsidence_rate_mm_yr: float | None = None,
) -> dict[str, Any]:
    """Compute a full BasinState sequence from rift kinematics.

    Returns a dict ready to feed into a BasinNode.states list.
    Each state carries:
      - state: BasinState value
      - beta: extension factor at that state
      - subsidence_km: cumulative subsidence
      - confidence: epistemic confidence

    Example output for Kinabalu Deep:
    {
      "states": [
        {"state": "prerift", "beta": 1.0, "subsidence_km": 0.0, "confidence": 0.85},
        {"state": "syn_rift_1", "beta": 3.75, "subsidence_km": 2.2, "confidence": 0.85},
        {"state": "post_rift_sag", "beta": 3.75, "subsidence_km": 2.8, "confidence": 0.75},
      ],
      "alternatives": ["breakup", "syn_rift_2"],
      "evidence_gaps": ["heat_flow_mw_m2", "magnetic_anomaly_data"],
    }
    """
    from geox_core.skills.subsurface.rift_kinematics import (
        compute_rift_kinematics,
        compute_beta,
        initial_subsidence,
        thermal_subsidence,
        classify_rift_phase,
        RiftPhase,
    )

    result = compute_rift_kinematics(
        crust_thickness_initial_km=30.0,  # default continental
        crust_thickness_current_km=30.0 / beta,
        time_since_rift_ma=time_since_rift_ma,
        subsidence_rate_mm_yr=subsidence_rate_mm_yr,
    )

    states: list[dict[str, Any]] = [
        {
            "state": "prerift",
            "beta": 1.0,
            "subsidence_km": 0.0,
            "confidence": 0.85,
        }
    ]

    # Active rift state — only append if extension actually occurred (β > 1.05)
    if result.beta > 1.05:
        rift_state = rift_phase_to_basin_state(result.rift_phase.value)
        states.append(
            {
                "state": rift_state,
                "beta": result.beta,
                "subsidence_km": result.initial_subsidence_km,
                "confidence": result.confidence,
            }
        )

    # Post-rift / thermal sag (if time has passed)
    if time_since_rift_ma > 0 and result.thermal_subsidence_km > 0.01:
        states.append(
            {
                "state": "thermal_subsidence" if result.rift_phase == RiftPhase.POST_RIFT else "post_rift_sag",
                "beta": result.beta,
                "subsidence_km": result.total_subsidence_km,
                "confidence": max(0.65, result.confidence - 0.10),
            }
        )

    alternatives = [rift_phase_to_basin_state(a.value) for a in result.alternative_phases]

    return {
        "states": states,
        "alternatives": alternatives,
        "evidence_gaps": result.evidence_gaps,
        "rift_kinematics": {
            "beta": result.beta,
            "initial_subsidence_km": result.initial_subsidence_km,
            "thermal_subsidence_km": result.thermal_subsidence_km,
            "total_subsidence_km": result.total_subsidence_km,
            "rift_phase": result.rift_phase.value,
            "confidence": result.confidence,
        },
    }


__all__ = [
    "rift_phase_to_basin_state",
    "compute_basin_state_sequence",
    "_RIFT_TO_BASIN_STATE",
]
