"""
geox_core.physics.td_methods.linear — Eureka 1 fitter #1

Straight-line linear interpolation between checkshot levels.

This is the original behaviour of `compute_td_from_checkshot` in
`geox_core/core/welltie.py:65` — refactored here to share the
envelope contract with the other three fitters.

Properties:
  - Piecewise C^0 (continuous, not differentiable at checkshot levels)
  - Cannot extrapolate — fails closed outside the checkshot range
  - The "honest" fitter: makes no smoothness assumption, lets the data speak

Use this when:
  - Checkshot density is high (≥ 1 per 100 m)
  - The velocity field is clearly layered (no smooth gradients)
  - You want the most conservative, falsifiable T-D curve
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from geox_core.physics.td_methods.base import (
    TDFitResult,
    _audit,
    _coverage,
    _extrapolation_risk,
    _validate_inputs,
)


def fit_linear(
    checkshot_data: List[Dict[str, Any]],
    depth_array: np.ndarray,
) -> TDFitResult:
    """Linear interpolation of TWT from checkshot table.

    Fails closed if checkshot depth range doesn't cover depth_array.
    """
    cs_d, cs_t = _validate_inputs(checkshot_data, depth_array)
    min_d, max_d = float(cs_d.min()), float(cs_d.max())

    if depth_array.min() < min_d or depth_array.max() > max_d:
        raise ValueError(
            f"Linear fitter: checkshot covers [{min_d:.1f}, {max_d:.1f}] m MD — "
            f"depth array extends to {depth_array.min():.1f}..{depth_array.max():.1f} m MD. "
            f"Cannot extrapolate. Use layer_cake or vo_k with regional prior, or extend checkshot."
        )

    twt_interp = np.interp(depth_array, cs_d, cs_t)
    residual_at_cs = np.interp(cs_d, depth_array, twt_interp) - cs_t
    rmse = float(np.sqrt(np.mean(residual_at_cs**2)))
    cov = _coverage(depth_array, cs_d)
    audit = _audit(twt_interp, depth_array, residual_at_cs)

    return TDFitResult(
        method="linear",
        equation="TWT(z) = piecewise-linear through (z_i, TWT_i) anchor points",
        coefficients=[],
        twt_ms=twt_interp,
        residuals_ms=residual_at_cs,
        rmse_ms=rmse,
        physics_guard=audit,
        extrapolation_risk=0.0,  # fail-closed above, so risk is 0 by construction
        fail_closed=True,
    )
