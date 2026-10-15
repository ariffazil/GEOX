"""
restore.py — Pure-GEOX structural restoration primitive (M1).

restored = present - throw * normalized_displacement_field * slip_vector

Deterministic, reversible, and LoopStructural-independent: it takes the
EVALUATED displacement field as input, not the fault object. This replaces the
non-functional LoopStructural `apply_to_points(reverse=True)` / `faults_enabled`
path documented in LOOPSTRUCTURAL_REALITY_AUDIT.md (2026-10-14): the upstream
primitive does not reverse, so GEOX builds the subtraction directly.

Decision (a) 2026-10-14 (Arif): build restoration in GEOX, not a replacement engine.

Forged: 2026-10-15 · 333-AGI
"""

from __future__ import annotations

import numpy as np


def restore_surface(
    surface: np.ndarray,  # (N,3) present-day (faulted) points
    displacement_field: np.ndarray,  # (N,)  normalized displacement 0..1
    throw: float,
    slip_vector: np.ndarray,  # (3,)  unit slip direction
) -> np.ndarray:
    """Restore faulted surface points to pre-fault coordinates.

    restored = present - throw * field * slip

    Reversible: restore_surface(restored, field, -throw, slip) == present.
    Fail-closed upstream: caller must reject malformed input (NaN field, non-unit slip).
    """
    surface = np.asarray(surface, dtype=float)
    if surface.ndim != 2 or surface.shape[1] != 3:
        raise ValueError(f"surface must be (N,3), got {surface.shape}")
    field = np.asarray(displacement_field, dtype=float)
    if field.ndim != 1 or field.shape[0] != surface.shape[0]:
        raise ValueError(f"displacement_field must be (N,) matching surface N={surface.shape[0]}")
    slip = np.asarray(slip_vector, dtype=float)
    if slip.shape != (3,):
        raise ValueError(f"slip_vector must be (3,), got {slip.shape}")
    if np.any(~np.isfinite(field)):
        raise ValueError("displacement_field contains NaN/inf — reject before modelling")
    return surface - throw * field[:, None] * slip[None, :]


def line_length(points: np.ndarray) -> float:
    """Total cross-section length of a polyline (N,3)."""
    p = np.asarray(points, dtype=float)
    d = np.diff(p, axis=0)
    return float(np.sum(np.sqrt(np.sum(d**2, axis=1))))


def max_throw(surface_z: np.ndarray, window: slice | None = None) -> float:
    """Maximum vertical step (throw) in a surface depth profile z(x)."""
    z = np.asarray(surface_z, dtype=float)
    z = z[np.isfinite(z)]
    if len(z) < 2:
        return float("nan")
    return float(np.max(z) - np.min(z))


def competing_restorations(
    surface: np.ndarray,
    displacement_field: np.ndarray,
    throw: float,
    slip_vector: np.ndarray,
) -> list[dict]:
    """>=3 competing restoration hypotheses (perturbed throw), each with a falsifier."""
    hyps = []
    for f in (0.9, 1.0, 1.1):
        t = throw * f
        restored = restore_surface(surface, displacement_field, t, slip_vector)
        hyps.append(
            {
                "throw": float(t),
                "restored_length": line_length(restored),
                "falsifier": f"restored surface discontinuous if true throw != {t:.1f}",
            }
        )
    return hyps
