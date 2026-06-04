"""
geox_core.physics.td_methods — Eureka 1: The 4 T-D Fitters

The 4 ways to map depth → time when you have checkshot data:

  1. linear       — straight line between checkshot levels (current behaviour, fail-closed)
  2. polynomial   — weighted polynomial fit through checkshots (smooth, C^infinity)
  3. vo_k         — Vo-Keystone: linear + exponential compaction
  4. layer_cake   — per-formation interval velocity (geologically anchored)

All four return the same envelope contract:
  {
    "method": str,
    "equation": str,
    "coefficients": list,
    "twt_ms": np.ndarray,
    "residuals_ms": np.ndarray,
    "rmse_ms": float,
    "physics_guard": {
      "bounds_ok": bool,
      "drift_ok": bool,
      "gradient_ok": bool,
      "curvature_ok": bool,
      "violations": list,
    },
    "extrapolation_risk": float,  # 0.0–1.0; how dangerous was the depth coverage
    "fail_closed": bool,
  }

The PhysicsGuard is invoked inside every fitter — no T-D curve leaves this module
without being audited. The f2 floor (F2 TRUTH) is enforced here, not at the MCP surface.

DITEMPA BUKAN DIBERI — forges capability without surface bloat.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from geox_core.physics.guards import PhysicsGuard

# ── Envelope contract ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TDFitResult:
    """The standard envelope for every T-D fitter."""

    method: str
    equation: str
    coefficients: list[float]
    twt_ms: np.ndarray
    residuals_ms: np.ndarray
    rmse_ms: float
    physics_guard: dict[str, Any]
    extrapolation_risk: float
    fail_closed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "equation": self.equation,
            "coefficients": [float(c) for c in self.coefficients],
            "twt_ms": [float(t) for t in self.twt_ms],
            "residuals_ms": [float(r) for r in self.residuals_ms],
            "rmse_ms": float(self.rmse_ms),
            "physics_guard": self.physics_guard,
            "extrapolation_risk": float(self.extrapolation_risk),
            "fail_closed": bool(self.fail_closed),
        }


# ── Common input validation ─────────────────────────────────────────────────


def _validate_inputs(
    checkshot_data: list[dict[str, Any]],
    depth_array: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Pull (depth_md, twt_ms) arrays out of any checkshot format.

    Accepts:
      - [{"depth_md": float, "twt_ms": float}, ...]
      - [[depth_md, twt_ms], ...]

    Fails closed if < 2 points.
    """
    if not checkshot_data:
        raise ValueError("checkshot_data is empty.")
    first = checkshot_data[0]
    if isinstance(first, (list, tuple)):
        depths = np.array([float(r[0]) for r in checkshot_data], dtype=float)  # type: ignore[arg-type,index]
        twts = np.array([float(r[1]) for r in checkshot_data], dtype=float)  # type: ignore[arg-type,index]
    else:
        depths = np.array([float(r["depth_md"]) for r in checkshot_data], dtype=float)  # type: ignore[index]
        twts = np.array([float(r["twt_ms"]) for r in checkshot_data], dtype=float)  # type: ignore[index]

    if len(depths) < 2:
        raise ValueError("Checkshot has < 2 points. Cannot fit a T-D function.")
    if len(depths) != len(twts):
        raise ValueError("Checkshot depth and TWT arrays have different lengths.")

    return depths, twts


def _coverage(
    depth_array: np.ndarray,
    cs_depths: np.ndarray,
) -> float:
    """Fraction of depth_array covered by checkshot range. 0.0 = no coverage, 1.0 = full."""
    if len(cs_depths) == 0 or len(depth_array) == 0:
        return 0.0
    min_d, max_d = float(cs_depths.min()), float(cs_depths.max())
    inside = (depth_array >= min_d) & (depth_array <= max_d)
    return float(np.sum(inside)) / float(len(depth_array))


def _extrapolation_risk(
    depth_array: np.ndarray,
    cs_depths: np.ndarray,
) -> float:
    """Quantify how much of the requested depth is OUTSIDE the checkshot range.

    Returns 0.0 if all depth values are inside the range, climbing to 1.0 if
    the entire array is outside. This is a *risk* number, not a verdict.
    """
    if len(cs_depths) == 0 or len(depth_array) == 0:
        return 1.0
    min_d, max_d = float(cs_depths.min()), float(cs_depths.max())
    outside = (depth_array < min_d) | (depth_array > max_d)
    return float(np.sum(outside)) / float(len(depth_array))


def _audit(
    twt_ms: np.ndarray,
    depth_array: np.ndarray,
    residual_twt_ms: np.ndarray,
) -> dict[str, Any]:
    """Run PhysicsGuard on the fitter output. Returns the receipt.

    Checks: Vp bounds [1500, 6000], drift |dv/dz| ≤ 50, curvature sanity.
    """
    guard = PhysicsGuard()
    if len(depth_array) < 2:
        return {"bounds_ok": True, "drift_ok": True, "gradient_ok": True, "curvature_ok": True, "violations": []}
    dz = np.diff(depth_array)
    dt = np.diff(twt_ms) / 1000.0  # ms → s
    # Avoid div-by-zero
    safe_dz = np.where(dz > 0, dz, 1e-9)
    v_inst = 2.0 * safe_dz / np.where(dt > 0, dt, 1e-9)
    # Pair v_inst with depth_array[:-1] (same length, both N-1) so np.diff matches
    z_for_audit = depth_array[:-1]
    vel_result = guard.validate_velocity_sanity(v_inst, z_for_audit)
    bounds_ok = bool(np.all((v_inst >= 1500) & (v_inst <= 6000)))
    gradient_ok = not vel_result.hold
    # Curvature on residuals (synthetic z for the check, since we don't have raw z)
    drift_curve = residual_twt_ms
    if len(drift_curve) >= 3:
        curv_result = guard.validate_drift_sanity(drift_curve, np.linspace(0, 1, len(drift_curve)))
        curvature_ok = not curv_result.hold
    else:
        curvature_ok = True
    drift_ok = bounds_ok and gradient_ok and curvature_ok
    return {
        "bounds_ok": bounds_ok,
        "drift_ok": drift_ok,
        "gradient_ok": gradient_ok,
        "curvature_ok": curvature_ok,
        "violations": vel_result.to_dict().get("violations", []),
        "authority": "F2_PHYSICS_GUARD",
    }
