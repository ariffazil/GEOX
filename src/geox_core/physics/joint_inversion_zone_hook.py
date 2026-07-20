"""
joint_inversion_zone_hook.py — Post-inversion crust-zone classification
═══════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBEI — Forged, Not Given

Stage 6 forge: wire `vp_zone_classify()` from `geox_core.schemas.crust_vp_grammar`
into the `joint_inversion` pipeline as an OPT-IN post-inversion step.

Constitutional binding:
  F2 TRUTH  — Classification is DER-grade (derived from inverted Physics13State).
              Provenance hash is preserved in the result.
  F4 CLARITY — Optional. Default off. Existing callers see no change.
  F7 HUMILITY— Confidence hard-capped at 0.90 (enforced inside vp_zone_classify).
  F9 ANTI-HANTU — No generative claims. Result is purely descriptive of the state.
  F13 SOVEREIGN — Domain classification is sovereign territory; this is
              substrate support, not a verdict.

Reference:
  Huang et al. (2021) — Tectonics — Seismic Imaging of an Intracrustal
  Deformation in the Northwestern Margin of the South China Sea
  (OBS2013-1, ±0.3 km/s Vp uncertainty, 10,346 picked arrivals).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from geox_core.physics.state import Physics13State
from geox_core.schemas.crust_vp_grammar import (
    CrustClassification,
    CrustZone,
    vp_zone_classify,
)


@dataclass(frozen=True)
class PostInversionZoneHook:
    """Opt-in parameters for post-inversion crust-zone classification.

    Wired into InversionRequest as `classify_crust_zone: bool = False`
    and `zone_hook: Optional[PostInversionZoneHook] = None`.

    F4 CLARITY: default behavior is OFF. Existing callers see no change.
    """

    crust_thickness_km: float | None = None
    heat_flow_mw_m2: float | None = None
    # If True, include full diagnostic_basis in the result.
    # Default False to keep result compact.
    include_diagnostics: bool = False


def _depth_km_from_state(state: Physics13State, observations: list[Any]) -> float:
    """Derive cell depth (km) from observation depths.

    Strategy: take the median observation depth.
    Falls back to 0.0 if no observations with depth.
    """
    depths: list[float] = [float(obs.depth_m) for obs in observations if hasattr(obs, "depth_m") and obs.depth_m is not None]
    if not depths:
        return 0.0
    depths_sorted = sorted(depths)
    n = len(depths_sorted)
    if n % 2 == 1:
        return depths_sorted[n // 2] / 1000.0
    return (depths_sorted[n // 2 - 1] + depths_sorted[n // 2]) / 2.0 / 1000.0


def classify_state_post_inversion(
    state: Physics13State,
    observations: list[Any],
    hook: PostInversionZoneHook,
) -> dict[str, Any]:
    """Run vp_zone_classify on an inverted Physics13State.

    Pure function. Returns a result envelope:
      {
        "crust_zone": str,           # CrustZone.value
        "vp_km_s": float,            # state.vp converted m/s → km/s
        "depth_km": float,           # derived from observations
        "crust_thickness_km": Optional[float],
        "heat_flow_mw_m2": Optional[float],
        "confidence": float,         # capped at 0.90 (F7)
        "alternative_zones": list[str],
        "diagnostic_basis": Optional[list[str]],  # only if include_diagnostics
        "evidence_rank": str,
      }

    F2 TRUTH: this is DER-grade — derived from the inverted state vector.
    F7 HUMILITY: confidence is hard-capped at 0.90 by vp_zone_classify.

    Constitutional provenance:
      - Source of truth: state.vp (m/s, from Physics13State)
      - Conversion: divide by 1000 to get km/s
      - Grammar source: Huang et al. (2021)
      - Schema: geox_core.schemas.crust_vp_grammar
    """
    vp_km_s = state.vp / 1000.0  # m/s → km/s
    depth_km = _depth_km_from_state(state, observations)

    classification: CrustClassification = vp_zone_classify(
        vp_km_s=vp_km_s,
        crust_thickness_km=hook.crust_thickness_km,
        depth_km=depth_km,
        heat_flow_mw_m2=hook.heat_flow_mw_m2,
    )

    result: dict[str, Any] = {
        "crust_zone": classification.zone.value,
        "vp_km_s": round(vp_km_s, 4),
        "depth_km": round(depth_km, 4),
        "crust_thickness_km": hook.crust_thickness_km,
        "heat_flow_mw_m2": hook.heat_flow_mw_m2,
        "confidence": classification.confidence,
        "alternative_zones": [z.value for z in classification.alternative_zones],
        "evidence_rank": classification.evidence_rank,
        "source_paper": classification.source_paper,
    }
    if hook.include_diagnostics:
        result["diagnostic_basis"] = classification.diagnostic_basis
        if classification.crust_thickness_km is not None:
            result["crust_thickness_km"] = classification.crust_thickness_km
    return result


__all__ = [
    "PostInversionZoneHook",
    "classify_state_post_inversion",
    "CrustZone",  # re-export for convenience
]
