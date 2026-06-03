"""
geox_core.physics.td_methods.layer_cake — Eureka 1 fitter #4

Layer-cake velocity model: each formation (between two tops) has its own
interval velocity, calibrated to the checkshot levels that fall within it.

The geologically-correct fitter: every layer respects the actual stratigraphy.
Tops are passed in as (name, top_md) pairs; V_int per layer is solved
from the checkshot transit time across that layer.

Properties:
  - C^0 (piecewise constant V_int per layer, but TWT is C^1 across top boundaries)
  - Geologically anchored: a salt layer is a salt layer, not a polynomial
  - Per-layer V_int is a single physics-grade number (no smoothing)
  - Fails closed if any layer has zero checkshot coverage
  - V_int per layer is exposed as the primary output (interpretable)

Use this when:
  - You have formation tops (well picks)
  - The velocity field is clearly layered (carbonate platforms, salt, etc.)
  - You need per-layer V_int for volumetric work
  - Overpressure is suspected in specific intervals
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from geox_core.physics.td_methods.base import (
    TDFitResult,
    _audit,
    _coverage,
    _extrapolation_risk,
    _validate_inputs,
)


def fit_layer_cake(
    checkshot_data: List[Dict[str, Any]],
    depth_array: np.ndarray,
    tops: List[Tuple[str, float]],  # [(name, top_md), ...]
    v_fallback: float = 2200.0,
    allow_extrapolation: bool = False,
) -> TDFitResult:
    """Layer-cake T-D from checkshot + formation tops.

    Args:
        checkshot_data: list of {"depth_md", "twt_ms"} or [[d, t], ...]
        depth_array: target depths
        tops: formation tops as [(name, top_md), ...], ordered shallow → deep.
              A synthetic "surface" top at depth=0 is auto-prepended.
        v_fallback: V_int to use if a layer has no checkshot coverage (m/s)
        allow_extrapolation: if False, raises on layers with zero coverage

    Returns:
        TDFitResult where the equation describes V_int per layer
        and the residual is per-checkshot-point deviation from the
        layer-cake prediction.
    """
    cs_d, cs_t = _validate_inputs(checkshot_data, depth_array)
    if not tops:
        raise ValueError("layer_cake fitter requires formation tops. Pass tops=[(name, depth), ...].")

    # Normalise tops, prepend surface
    sorted_tops = sorted(tops, key=lambda x: x[1])
    if sorted_tops[0][1] > 0:
        sorted_tops = [("surface", 0.0)] + sorted_tops
    if sorted_tops[-1][1] < float(depth_array.max()):
        # Append a synthetic "TD" at max(depth_array)
        sorted_tops = sorted_tops + [("TD", float(depth_array.max()))]

    # Build per-layer V_int
    layer_v_int: Dict[str, float] = {}
    layer_coverage: Dict[str, int] = {}
    layer_twt_offset: Dict[str, float] = {sorted_tops[0][0]: 0.0}

    cumulative_twt = 0.0
    for i in range(len(sorted_tops) - 1):
        name_i, top_i = sorted_tops[i]
        name_j, top_j = sorted_tops[i + 1]
        layer_name = f"{name_i}→{name_j}"

        # Checkshots inside this layer
        mask = (cs_d >= top_i) & (cs_d < top_j)
        n_in_layer = int(np.sum(mask))
        layer_coverage[layer_name] = n_in_layer

        if n_in_layer >= 2:
            d_in = cs_d[mask]
            t_in = cs_t[mask]
            d_thick = float(d_in[-1] - d_in[0])
            t_thick = float(t_in[-1] - t_in[0])
            if t_thick > 0 and d_thick > 0:
                v_layer = 2.0 * d_thick / (t_thick / 1000.0)
                v_layer = float(np.clip(v_layer, 1500, 6000))
            else:
                v_layer = v_fallback
        elif n_in_layer == 1:
            d_in = cs_d[mask]
            t_in = cs_t[mask]
            # Single point: use local V_avg as proxy
            v_layer = float(2.0 * float(d_in[0]) / max(float(t_in[0]) / 1000.0, 1e-9))
            v_layer = float(np.clip(v_layer, 1500, 6000))
        else:
            if not allow_extrapolation:
                raise ValueError(
                    f"Layer-cake fitter: layer '{layer_name}' "
                    f"[{top_i:.1f}, {top_j:.1f}] m MD has zero checkshot coverage. "
                    f"Pass allow_extrapolation=True (uses v_fallback={v_fallback} m/s)."
                )
            v_layer = v_fallback

        layer_v_int[layer_name] = v_layer
        layer_thickness = top_j - top_i
        layer_twt_thickness = 2.0 * layer_thickness / max(v_layer, 1500) * 1000.0
        cumulative_twt += layer_twt_thickness
        layer_twt_offset[name_j] = cumulative_twt

    # Build TWT array at target depths
    twt_pred = np.zeros_like(depth_array, dtype=float)
    for j, z in enumerate(depth_array):
        # Find which layer this depth is in
        layer_idx = 0
        for i in range(len(sorted_tops) - 1):
            if sorted_tops[i][1] <= z < sorted_tops[i + 1][1]:
                layer_idx = i
                break
        name_i, top_i = sorted_tops[layer_idx]
        name_j, top_j = sorted_tops[layer_idx + 1]
        layer_name = f"{name_i}→{name_j}"
        v_layer = layer_v_int[layer_name]
        # TWT at this depth = TWT at top of layer + 2*(z-top_i)/v_layer
        twt_pred[j] = layer_twt_offset[name_i] + 2.0 * (z - top_i) / max(v_layer, 1500) * 1000.0

    # Residuals at checkshot points
    twt_at_cs = np.zeros_like(cs_t, dtype=float)
    for j, z in enumerate(cs_d):
        layer_idx = 0
        for i in range(len(sorted_tops) - 1):
            if sorted_tops[i][1] <= z < sorted_tops[i + 1][1]:
                layer_idx = i
                break
        name_i, top_i = sorted_tops[layer_idx]
        name_j, top_j = sorted_tops[layer_idx + 1]
        layer_name = f"{name_i}→{name_j}"
        v_layer = layer_v_int[layer_name]
        twt_at_cs[j] = layer_twt_offset[name_i] + 2.0 * (z - top_i) / max(v_layer, 1500) * 1000.0
    residuals = cs_t - twt_at_cs
    rmse = float(np.sqrt(np.mean(residuals**2)))

    # Build equation
    layer_eq_parts = [f"{n}:V={v:.0f}m/s" for n, v in layer_v_int.items()]
    equation = "TWT(z) = Σ_layers 2·Δz/V_int(layer) ; " + " ; ".join(layer_eq_parts)

    cov = _coverage(depth_array, cs_d)
    audit = _audit(twt_pred, depth_array, residuals)
    risk = 0.0 if all(n >= 1 for n in layer_coverage.values()) else _extrapolation_risk(depth_array, cs_d)

    return TDFitResult(
        method="layer_cake",
        equation=equation,
        coefficients=[float(v) for v in layer_v_int.values()],
        twt_ms=twt_pred,
        residuals_ms=residuals,
        rmse_ms=rmse,
        physics_guard={
            **audit,
            "layer_v_int": layer_v_int,
            "layer_coverage_pts": layer_coverage,
        },
        extrapolation_risk=risk,
        fail_closed=not allow_extrapolation,
    )
