"""Calibration helpers — vertical-exaggeration and time-to-depth corrections.

Why this module exists
----------------------
Every dip measured off a display is a *display* number until it has been corrected.
Two defects make a CV dip meaningless, and both are silent:

  * **Vertical exaggeration (VE).** A section displayed with the vertical axis stretched
    makes every surface look steeper than it is. ``tan(theta_apparent) = ve *
    tan(theta_true)``, so an uncorrected 20 deg bed displayed at ve = 2 reads 36 deg.
  * **Time domain.** A two-way-time section is not depth. A dip in ms/sample has no
    centimetre meaning until an interval-velocity model converts it.

``declare_calibration_state`` does not *do* the correction — it forces the caller to
declare what the display is, so that a downstream gate (K-REGIME-DISPLAY in
``geox_mcp.tools.structure_gates.tectonic_regime``) can decide whether any dip in the
bundle is geometry or decoration.

Doctrine preserved here
-----------------------
* CONTRACT §4 — ``apply_ve_correction``, ``time_to_depth``, ``declare_calibration_state``.
* CONTRACT §7 rule 5 — decompaction is a different correction (depth, not display);
  it lives with the thickness code, not here.
* No function here returns a probability. Calibration state is a declaration, not a
  confidence.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

__all__ = [
    "MIGRATION_STATES",
    "apply_ve_correction",
    "declare_calibration_state",
    "time_to_depth",
]

#: Declared migration vocabulary. "unknown" is a legitimate — and distrustful — declaration.
MIGRATION_STATES: tuple[str, ...] = ("migrated", "unmigrated", "unknown")

_VE_UNITY_TOL = 1e-9


def apply_ve_correction(dip_apparent_deg: float, ve: float) -> float:
    """Remove the display stretch from an apparent dip.

    ``tan(theta_true) = tan(theta_apparent) / ve``, evaluated in radians, returned in degrees.

    Parameters
    ----------
    dip_apparent_deg:
        Apparent dip measured *off the display*, signed, in degrees.
    ve:
        **Vertical exaggeration — a DIMENSIONLESS display ratio
        (vertical scale / horizontal scale), NOT a velocity.** Writing it as a velocity
        is a dimensional error: VE has no units, and multiplying it by a time or a
        depth produces nothing that means anything. ``ve = 2.0`` means one metre of
        true vertical section is drawn two metres tall relative to the horizontal scale.
        ``ve = 1.0`` is an unexaggerated (1:1) display and leaves the dip untouched.

    Returns
    -------
    float
        True dip in degrees, same sign convention as the input.

    Raises
    ------
    ValueError
        If ``ve`` is non-finite or <= 0 (a display ratio cannot be zero or negative —
        a non-positive VE would *flip or collapse* the vertical axis), or if the
        apparent dip is non-finite or at/beyond vertical (|dip| >= 90 deg), where the
        tangent is unbounded and no finite VE correction exists.

    Notes
    -----
    A tilted *time* axis is a separate correction and is not applied here: if the section
    is in two-way time, run :func:`time_to_depth` first (or declare the time domain in
    :func:`declare_calibration_state` and let the caller refuse the number).
    """
    ve_f = float(ve)
    if not math.isfinite(ve_f) or ve_f <= 0.0:
        raise ValueError(
            f"vertical exaggeration (ve) must be finite and > 0 — it is a dimensionless "
            f"display ratio, not a velocity; got {ve!r}"
        )
    dip_f = float(dip_apparent_deg)
    if not math.isfinite(dip_f):
        raise ValueError(f"dip_apparent_deg must be finite, got {dip_apparent_deg!r}")
    if abs(dip_f) >= 90.0 - 1e-9:
        raise ValueError(
            f"apparent dip {dip_f} deg is at or beyond vertical — tan() is unbounded and "
            "no finite VE correction exists"
        )
    theta_apparent_rad = math.radians(dip_f)
    theta_true_rad = math.atan(math.tan(theta_apparent_rad) / ve_f)
    return float(math.degrees(theta_true_rad))


def time_to_depth(twt_ms: float | np.ndarray, interval_velocity_m_s: float) -> float | np.ndarray:
    """Convert two-way travel time to depth, ``d = v * (twt / 2)``.

    Parameters
    ----------
    twt_ms:
        Two-way travel time in **milliseconds** (scalar or array). Converted to seconds
        internally, then halved because the recorded time is a *two-way* path.
    interval_velocity_m_s:
        Interval velocity in metres per second, used over that interval.

    Returns
    -------
    float
        Depth in metres (``float`` for scalar input, ``ndarray`` for array input).

    Raises
    ------
    ValueError
        If ``interval_velocity_m_s`` is non-finite or <= 0 (a zero velocity divides the
        section into a singularity, not a depth), if the time is non-finite, or if the
        two-way time is negative.

    Notes
    -----
    A single interval velocity is a *locally* valid statement. Layered velocity
    (V(z) or a Dix interval stack) must be converted layer by layer by the caller —
    this function does not invent a gradient.
    """
    v = float(interval_velocity_m_s)
    if not math.isfinite(v) or v <= 0.0:
        raise ValueError(
            f"interval_velocity_m_s must be finite and > 0, got {interval_velocity_m_s!r} "
            "(time cannot be turned into depth without a positive interval velocity)"
        )
    t = np.asarray(twt_ms, dtype=float)
    if not np.all(np.isfinite(t)):
        raise ValueError("twt_ms contains non-finite values; a NaN time is not a depth")
    if np.any(t < 0.0):
        raise ValueError(
            f"twt_ms must be non-negative two-way time; got min={float(np.min(t))!r}"
        )
    depth = v * (t / 1000.0) / 2.0
    if np.ndim(twt_ms) == 0:
        return float(depth)
    return depth


def declare_calibration_state(
    *,
    vertical_exaggeration: float | None,
    velocity_model_present: bool,
    time_domain: bool,
    migration_state: str = "unknown",
    ve_corrected: bool = False,
) -> dict[str, Any]:
    """Declare what the display is, and whether dips measured off it can be trusted.

    Parameters
    ----------
    vertical_exaggeration:
        The dimensionless display ratio (vertical scale / horizontal scale). **Not a
        velocity.** ``None`` means *not declared* — which is not the same as 1.0, and is
        treated as a problem.
    velocity_model_present:
        Whether an interval-velocity model is available for the time-to-depth step.
    time_domain:
        Whether the section is in two-way time rather than depth.
    migration_state:
        ``"migrated"`` | ``"unmigrated"`` | ``"unknown"`` (default ``"unknown"``).
        **Migrated data do not follow the tan(theta_apparent) relation** that
        :func:`apply_ve_correction` inverts — migration moves and reshapes events — so the
        state must be declared rather than assumed. An undeclared (``"unknown"``) section
        cannot have its dips certified, and ``dips_trustworthy`` is False.
    ve_corrected:
        Whether the caller has *already* applied :func:`apply_ve_correction` to the dips
        in the bundle. This is the "(or corrected)" branch of the rule: a declared,
        corrected VE is acceptable; an undeclared one is not.

    Returns
    -------
    dict[str, Any]
        ``{"dips_trustworthy": bool, "problems": list[str], "migration_state": str}``.
        ``problems`` is the receipt: each entry names one reason the dips cannot be
        certified as geometry. Empty problems + True means: VE is 1.0 or declared and
        corrected, and the section is either depth domain or backed by a velocity model,
        and the migration state is declared.

    Raises
    ------
    ValueError
        If ``migration_state`` is not one of :data:`MIGRATION_STATES`.
    """
    problems: list[str] = []

    ms = str(migration_state).strip().lower()
    if ms not in MIGRATION_STATES:
        raise ValueError(
            f"migration_state must be one of {MIGRATION_STATES}, got {migration_state!r}"
        )

    ve: float | None
    if vertical_exaggeration is None:
        ve = None
        problems.append(
            "vertical_exaggeration unknown — apparent dips are a display artifact until the "
            "dimensionless display ratio (vertical scale / horizontal scale, NOT a velocity) is declared"
        )
    else:
        try:
            ve = float(vertical_exaggeration)
        except (TypeError, ValueError):
            ve = None
            problems.append(
                f"vertical_exaggeration not a number ({vertical_exaggeration!r}) — treated as undeclared"
            )
        else:
            if not math.isfinite(ve) or ve <= 0.0:
                problems.append(
                    f"vertical_exaggeration={ve} is not a valid display ratio (> 0 required)"
                )
                ve = None
            elif abs(ve - 1.0) > _VE_UNITY_TOL and not ve_corrected:
                problems.append(
                    f"vertical_exaggeration={ve} != 1 and ve_corrected is False — apparent dips are "
                    "inflated by the display stretch; apply apply_ve_correction() (tan(theta_app)= ve*tan(theta_true))"
                )

    if time_domain and not velocity_model_present:
        problems.append(
            "time-domain section without an interval-velocity model — a dip in ms/sample is not a "
            "depth gradient; time is not depth"
        )

    if ms == "migrated":
        problems.append(
            "section declared migrated — migrated data do not follow the tan(theta_apparent) relation "
            "inverted by apply_ve_correction(); dips must be re-derived from the migrated geometry and "
            "the display stretch declared separately"
        )
    elif ms == "unknown":
        problems.append(
            "migration_state unknown — an undeclared section cannot have its apparent-dip relation "
            "certified; declare 'migrated' or 'unmigrated' (migration_state)"
        )

    dips_trustworthy = not problems
    return {
        "dips_trustworthy": bool(dips_trustworthy),
        "problems": problems,
        "migration_state": ms,
    }
