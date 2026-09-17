"""Axis A — Shape: structure-tensor dip, in-section azimuth and curvature.

The layer is deterministic CV. It returns *numbers with coverage*, never a verdict and
never a probability (CONTRACT §0, §3).

Method (named precisely, because a caller may need to reproduce it)
-----------------------------------------------------------------
1. ``skimage.feature.structure_tensor(section, sigma, mode="reflect")`` gives the local
   second-moment matrix of the Sobel gradients, smoothed by a Gaussian window of width
   ``sigma``. Its elements are ``Arr = <g_r^2>``, ``Arc = <g_r g_c>``, ``Acc = <g_c^2>``
   where ``r`` is the row (z / time) axis and ``c`` the column (trace) axis.
2. **Physical spacing.** Anisotropic sampling is handled by converting the tensor to the
   physical metric, ``T_zz = Arr/dz^2``, ``T_xx = Acc/dx^2``, ``T_xz = Arc/(dz*dx)``.
   The local reflector slope follows from the tensor itself, not from a pixel ratio::

       m = -(T_xz / T_zz) = -(Arc / Arr) * (dz / dx)          # dz per metre of x

   ``m > 0`` means the reflector deepens toward +x (down to the right). This is exact for
   a planar (linear) reflector, and is the analytic 2x2 eigendirection of the tensor —
   ``structure_tensor_eigenvectors`` is not exported by scikit-image 0.26, so the
   eigendirection is solved here in closed form instead of imported.
3. **Vertical exaggeration.** ``theta_true = atan(tan(theta_apparent) / ve)`` (CONTRACT §1,
   §4). ``ve`` is the dimensionless display ratio (vertical scale / horizontal scale) —
   not a velocity. Curvature is then evaluated in the *true* metric (``dz_true = dz / ve``).
4. **Curvature.** ``kappa = d(theta)/d(s)`` in the true metric, expanded along the
   reflector as ``(dtheta/dx + dtheta/dz * tan(theta)) * cos(theta)`` with units 1/m.
   ``kappa > 0`` = the reflector steepens toward +x (down-dip steepening, the listric
   rollover sense); ``kappa < 0`` = it flattens.
5. **Validity.** A tensor is *valid* where it is finite, inside the edge guard
   (3*sigma, because Sobel + Gaussian contaminate the border), and anisotropic enough to
   define a direction: ``(l1 - l2) / (l1 + l2) >= min_anisotropy``. A constant region has
   no reflector and is therefore not a measurement — it is dropped and *lowers coverage*.

Doctrine preserved here (CONTRACT §7)
------------------------------------
* Rule 3 — **"listric" is not a CV output.** ``geometry_class_fired`` is emitted only by a
  declared rule whose name is in ``Measurement.method``; the rule's thresholds and its
  per-rule evaluation receipt are in ``uncertainty`` and ``notes``. No rule fires ->
  ``UNMEASURED``, value ``None``.
* Rule 8 — a single horizon records only the last event. Nothing here composes a tectonic
  story out of one horizon; that is the caller's (falsifier's) job.
* ``UNMEASURED`` is never upgraded in transit, and it is never PASS and never KILL.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import ndimage
from scipy import stats as _stats
from skimage.feature import structure_tensor

from .types import Measurement, measured, unmeasured

__all__ = [
    "GEOMETRY_RULES",
    "KINK_BOUNDARY_SKIP_SAMPLES",
    "KINK_MAX_SIDE_SPREAD_DEG",
    "KINK_MIN_GAP_DEG",
    "KINK_MIN_GROUP_FRACTION",
    "LISTRIC_MIN_DIP_RANGE_DEG",
    "LISTRIC_MIN_SAMPLES",
    "LISTRIC_MIN_SPEARMAN",
    "MIN_ANISOTROPY",
    "MIN_COVERAGE_FOR_MEASURED",
    "PLANAR_MAX_ABS_CURVATURE_1_M",
    "PLANAR_MAX_SPREAD_DEG",
    "AZIMUTH_MIN_ABS_DIP_DEG",
    "RULE_KINKED",
    "RULE_LISTRIC",
    "RULE_PLANAR",
    "compute_dip_field",
    "extract_axis_a",
]

# ── declared geometry rules ────────────────────────────────────────────────────────────
# A class name may only be emitted by one of these, and only when its decision inputs are
# MEASURED. `listric` is an INTERPRETATION (CONTRACT §7 rule 3).
RULE_PLANAR = "RULE-STR-01-PLANAR"
RULE_LISTRIC = "RULE-STR-02-LISTRIC"
RULE_KINKED = "RULE-STR-03-KINKED"

PLANAR_MAX_SPREAD_DEG = 3.0
PLANAR_MAX_ABS_CURVATURE_1_M = 1e-4
LISTRIC_MIN_SPEARMAN = 0.5
LISTRIC_MIN_SAMPLES = 20
LISTRIC_MIN_DIP_RANGE_DEG = 5.0
KINK_MIN_GAP_DEG = 8.0
KINK_MIN_GROUP_FRACTION = 0.15
KINK_MAX_SIDE_SPREAD_DEG = 4.0
KINK_BOUNDARY_SKIP_SAMPLES = 3

MIN_ANISOTROPY = 0.30
MIN_COVERAGE_FOR_MEASURED = 0.5
AZIMUTH_MIN_ABS_DIP_DEG = 0.5

#: The rule registry. Every entry is a *declared* rule: name, class emitted, the exact
#: predicate, its thresholds, and the precedence order in which it is tested.
GEOMETRY_RULES: dict[str, dict[str, Any]] = {
    RULE_KINKED: {
        "class": "KINKED",
        "precedence": 1,
        "declared": (
            "A DISCRETE DIP-DOMAIN BOUNDARY exists: scanning the horizon in x, there is a split "
            "index where the mean dip on each side differs by >= kink_min_gap_deg, each side is "
            "internally tight (p95 - p5 <= kink_max_side_spread_deg), and each side holds "
            ">= kink_min_group_fraction of the samples. The transition samples within "
            "kink_boundary_skip_samples of the boundary belong to neither domain and are declared "
            "as a boundary zone."
        ),
        "params": {
            "kink_min_gap_deg": KINK_MIN_GAP_DEG,
            "kink_min_group_fraction": KINK_MIN_GROUP_FRACTION,
            "kink_max_side_spread_deg": KINK_MAX_SIDE_SPREAD_DEG,
            "kink_boundary_skip_samples": KINK_BOUNDARY_SKIP_SAMPLES,
        },
    },
    RULE_PLANAR: {
        "class": "PLANAR",
        "precedence": 2,
        "declared": (
            "Horizon dip spread (p95 - p5 of dip magnitude) <= planar_max_spread_deg AND "
            "|mean signed curvature| <= planar_max_abs_curvature_1_m."
        ),
        "params": {
            "planar_max_spread_deg": PLANAR_MAX_SPREAD_DEG,
            "planar_max_abs_curvature_1_m": PLANAR_MAX_ABS_CURVATURE_1_M,
        },
    },
    RULE_LISTRIC: {
        "class": "LISTRIC",
        "precedence": 3,
        "declared": (
            "Dip magnitude increases systematically with depth: Spearman rank correlation of "
            "|dip| against sample depth >= listric_min_spearman, with n >= listric_min_samples and "
            "a dip range (p95 - p5) >= listric_min_dip_range_deg. This is an INTERPRETATION of a "
            "measured trend, not a raw CV output."
        ),
        "params": {
            "listric_min_spearman": LISTRIC_MIN_SPEARMAN,
            "listric_min_samples": LISTRIC_MIN_SAMPLES,
            "listric_min_dip_range_deg": LISTRIC_MIN_DIP_RANGE_DEG,
        },
    },
}

_INTERIOR_NOTE = (
    "Only the section interior is measured: a border of ceil(3*sigma) + 2 samples is excluded — "
    "1 px for the Sobel gradient stencil, 3*sigma for the Gaussian tensor window, and 1 px for the "
    "difference stencil used by the curvature term. Inside that border the plane-wave estimate is "
    "exact to machine precision; on it, it is not."
)


# ── validation helpers ─────────────────────────────────────────────────────────────────
def _as_section(section: np.ndarray) -> np.ndarray:
    arr = np.asarray(section, dtype=float)
    if arr.ndim != 2:
        raise ValueError(
            f"section must be a 2-D float array of shape (n_samples_z, n_traces), got ndim={arr.ndim}"
        )
    if arr.size == 0:
        raise ValueError("section is empty — nothing to measure")
    if not np.all(np.isfinite(arr)):
        raise ValueError(
            "section contains non-finite values — a NaN would silently poison the tensor window; "
            "mask it out or fill it before measuring"
        )
    return arr


def _spacings(dz_m: float, dx_m: float) -> tuple[float, float]:
    dz = float(dz_m)
    dx = float(dx_m)
    for name, val in (("dz_m", dz), ("dx_m", dx)):
        if not math.isfinite(val) or val <= 0.0:
            raise ValueError(f"{name} must be finite and > 0, got {val!r}")
    return dz, dx


def _require_ve(ve: float) -> float:
    ve_f = float(ve)
    if not math.isfinite(ve_f) or ve_f <= 0.0:
        raise ValueError(
            f"ve must be finite and > 0 — it is the dimensionless display ratio "
            f"(vertical scale / horizontal scale), not a velocity; got {ve!r}"
        )
    return ve_f


# ── the field computation ──────────────────────────────────────────────────────────────
def _dip_field(
    section: np.ndarray,
    *,
    dz_m: float,
    dx_m: float,
    ve: float = 1.0,
    sigma: float = 1.0,
    min_anisotropy: float = MIN_ANISOTROPY,
) -> dict[str, Any]:
    """Structure-tensor field. Internal — the public surface is :func:`compute_dip_field`.

    Returns arrays: ``dip_signed_deg`` (VE-corrected, + = down toward +x),
    ``dip_apparent_signed_deg`` (uncorrected, kept for the calibration receipt),
    ``azimuth_deg`` (in-section, NaN where undefined), ``curvature_1_m``, ``valid``,
    ``anisotropy``, plus the scalars ``guard_px``, ``dz_true_m``, ``n_interior``.
    """
    arr = _as_section(section)
    dz, dx = _spacings(dz_m, dx_m)
    ve_f = _require_ve(ve)
    sig = float(sigma)
    if not math.isfinite(sig) or sig <= 0.0:
        raise ValueError(f"sigma must be finite and > 0, got {sigma!r}")

    nz, nx = arr.shape
    # Edge guard: 1 px Sobel halo + the 3*sigma Gaussian window radius + 1 px for the
    # difference stencil behind the curvature term. Measured empirically (probe 2026-09-18):
    # at sigma=1 the plane-wave dip error falls to ~5e-15 by index 5 and is ~3e-2 at index 3.
    guard = int(math.ceil(3.0 * sig)) + 2
    interior = np.zeros(arr.shape, dtype=bool)
    if nz > 2 * guard and nx > 2 * guard:
        interior[guard : nz - guard, guard : nx - guard] = True
    else:
        # Section too small for a border guard: measure everything and declare it.
        guard = 0
        interior[:] = True

    Arr, Arc, Acc = structure_tensor(arr, sigma=sig, mode="reflect")

    with np.errstate(divide="ignore", invalid="ignore"):
        Tzz = Arr / (dz * dz)
        Txx = Acc / (dx * dx)
        Txz = Arc / (dx * dz)

        finite = np.isfinite(Tzz) & np.isfinite(Txx) & np.isfinite(Txz)
        trace = Txx + Tzz
        disc = np.sqrt(np.maximum((Txx - Tzz) ** 2 + 4.0 * Txz**2, 0.0))
        e_major = 0.5 * (trace + disc)
        e_minor = 0.5 * (trace - disc)
        anisotropy = np.where(
            trace > 0.0, (e_major - e_minor) / np.where(trace > 0.0, trace, 1.0), 0.0
        )
        anisotropy = np.nan_to_num(anisotropy, nan=0.0, posinf=0.0, neginf=0.0)

    valid = finite & interior & (Tzz > 0.0) & (anisotropy >= float(min_anisotropy))

    slope = np.zeros(arr.shape, dtype=float)  # dz per metre of x, signed
    np.divide(-Txz, Tzz, out=slope, where=valid)
    slope = np.where(valid, slope, 0.0)

    # Vertical-exaggeration correction: tan(theta_true) = tan(theta_apparent) / ve.
    dip_apparent = np.degrees(np.arctan(slope))
    dip_true = np.degrees(np.arctan(np.tan(np.radians(dip_apparent)) / ve_f))
    dip_true = np.where(valid, dip_true, 0.0)

    # Curvature in the TRUE metric: kappa = d(theta)/d(s).
    dz_true = dz / ve_f
    tan_true = np.tan(np.radians(dip_true))
    with np.errstate(divide="ignore", invalid="ignore"):
        d_theta_dx = np.gradient(dip_true, dx, axis=1)  # deg per metre of x
        d_theta_dz = np.gradient(dip_true, dz_true, axis=0)  # deg per true metre of z
    curvature_deg_m = (d_theta_dx + d_theta_dz * tan_true) * np.cos(np.radians(dip_true))
    curvature_1_m = np.radians(curvature_deg_m)  # deg/m -> rad/m = 1/m

    # A difference stencil at a pixel whose neighbour is invalid reads a zero-fill, not a
    # reflector: that manufactures curvature out of nothing (measured: mean|kappa| ~2.5e-4 1/m
    # over a perfectly planar section before this erosion). So the curvature needs its
    # neighbourhood valid, not just the pixel — 1 px morphological core.
    curv_core = valid & np.asarray(
        ndimage.binary_erosion(valid, structure=np.ones((3, 3), dtype=bool)), dtype=bool
    )
    curvature_1_m = np.where(curv_core, curvature_1_m, 0.0)

    # In-section apparent dip azimuth, clockwise from +x. Only defined where the reflector
    # actually dips: a flat reflector has no dip direction and must not pollute a circular mean.
    azimuth = np.full(arr.shape, np.nan, dtype=float)
    has_azimuth = valid & (np.abs(dip_true) >= AZIMUTH_MIN_ABS_DIP_DEG)
    azimuth[has_azimuth] = np.where(dip_true[has_azimuth] > 0.0, 0.0, 180.0)

    return {
        "dip_signed_deg": dip_true,
        "dip_apparent_signed_deg": np.where(valid, dip_apparent, 0.0),
        "azimuth_deg": azimuth,
        "curvature_1_m": curvature_1_m,
        "valid": valid,
        "curv_valid": curv_core,
        "anisotropy": anisotropy,
        "guard_px": int(guard),
        "n_interior": int(interior.sum()),
        "dz_true_m": float(dz_true),
        "dz_m": float(dz),
        "dx_m": float(dx),
        "ve": float(ve_f),
        "sigma": float(sig),
        "min_anisotropy": float(min_anisotropy),
        "shape": (int(nz), int(nx)),
    }


def _circular_mean_deg(azimuths: np.ndarray) -> float | None:
    """Circular mean — atan2 of summed unit vectors. Linear averaging of 350 and 10 gives 180."""
    vals = np.asarray(azimuths, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return None
    rad = np.radians(vals)
    s = float(np.sum(np.sin(rad)))
    c = float(np.sum(np.cos(rad)))
    if abs(s) < 1e-15 and abs(c) < 1e-15:
        return None
    return float(math.degrees(math.atan2(s, c)) % 360.0)


def _spread_deg(values: np.ndarray, lo: float = 5.0, hi: float = 95.0) -> float:
    if values.size < 2:
        return 0.0
    return float(np.percentile(values, hi) - np.percentile(values, lo))


def _reduce(
    value: float | None,
    *,
    unit: str,
    coverage: float,
    n_samples: int,
    method: str,
    uncertainty: dict[str, Any],
    notes: list[str],
) -> Measurement:
    """MEASURED when coverage is sufficient, PARTIAL when the horizon is mostly unreadable."""
    if value is None or n_samples == 0:
        return unmeasured(
            unit,
            method=method,
            reason="no valid samples — nothing was measured (this is not a zero, and not a pass)",
            uncertainty=uncertainty,
            notes=notes,
        )
    if coverage < MIN_COVERAGE_FOR_MEASURED:
        return Measurement(
            value=float(value),
            unit=unit,
            status="PARTIAL",
            n_samples=int(n_samples),
            coverage=float(coverage),
            method=method,
            uncertainty=uncertainty,
            notes=notes
            + [
                f"PARTIAL: coverage {coverage:.3f} < {MIN_COVERAGE_FOR_MEASURED} — the number is real "
                "but it rests on a minority of the horizon",
            ],
        )
    return measured(
        float(value),
        unit,
        coverage=float(coverage),
        n_samples=int(n_samples),
        method=method,
        uncertainty=uncertainty,
        notes=notes,
    )


def _field_method(f: dict[str, Any]) -> str:
    return (
        "A/structure_tensor: skimage.feature.structure_tensor (Sobel gradients + Gaussian window "
        f"sigma={f['sigma']:g}, mode=reflect) -> 2x2 tensor in physical metric "
        f"(dz_m={f['dz_m']:g}, dx_m={f['dx_m']:g}); slope m=-(T_xz/T_zz); "
        f"VE correction tan(theta_true)=tan(theta_app)/ve with ve={f['ve']:g}; "
        f"validity: finite AND interior(guard={f['guard_px']}px) AND T_zz>0 AND anisotropy>="
        f"{f['min_anisotropy']:g}"
    )


# ── Axis A public surface ──────────────────────────────────────────────────────────────
def compute_dip_field(
    section: np.ndarray,
    *,
    dz_m: float,
    dx_m: float,
    ve: float = 1.0,
    sigma: float = 1.0,
) -> dict[str, Measurement]:
    """Structure-tensor dip/azimuth field over the whole section.

    Returns keys: ``"dip_deg"``, ``"dip_azimuth_deg"``, ``"curvature"``.

    Reductions over the valid field (each Measurement carries ``coverage`` and ``n_samples``):

    * ``dip_deg`` — mean dip **magnitude**. A signed mean over a whole section cancels
      (reflectors dip both ways) and would report ~0 for a strongly folded section; the
      signed statistics ride along in ``uncertainty``.
    * ``curvature`` — mean **|kappa|** in 1/m, same argument.
    * ``dip_azimuth_deg`` — circular mean of the in-section apparent dip azimuth (clockwise
      from +x). **This is not a 3-D azimuth**: a 2-D section cannot give one, and azimuth
      is undefined on flat ground, so samples with |dip| < ``AZIMUTH_MIN_ABS_DIP_DEG``
      are excluded and, if none remain, the key is UNMEASURED rather than 0.

    The VE correction ``tan(theta_true) = tan(theta_apparent) / ve`` is applied to every dip
    before any statistic is taken.
    """
    f = _dip_field(section, dz_m=dz_m, dx_m=dx_m, ve=ve, sigma=sigma)
    method = _field_method(f)
    valid = f["valid"]
    n_valid = int(valid.sum())
    n_interior = int(f["n_interior"])
    coverage = (n_valid / n_interior) if n_interior else 0.0

    dip = np.abs(f["dip_signed_deg"][valid])
    signed = f["dip_signed_deg"][valid]
    curv_core = f["curv_valid"]
    n_curv = int(curv_core.sum())
    curv = np.abs(f["curvature_1_m"][curv_core])
    signed_curv = f["curvature_1_m"][curv_core]
    az = f["azimuth_deg"][valid]
    az_valid = az[np.isfinite(az)]

    shared_unc: dict[str, Any] = {
        "sigma": f["sigma"],
        "dz_m": f["dz_m"],
        "dx_m": f["dx_m"],
        "vertical_exaggeration": f["ve"],
        "min_anisotropy": f["min_anisotropy"],
        "guard_px": f["guard_px"],
        "n_interior_samples": n_interior,
        "n_invalid_samples": n_interior - n_valid,
        "n_curvature_samples": n_curv,
        "n_curvature_dropped_for_invalid_neighbour": n_valid - n_curv,
    }
    shared_notes = [_INTERIOR_NOTE]

    out: dict[str, Measurement] = {}

    if n_valid == 0:
        reason = (
            "no valid structure-tensor samples: every interior sample was non-finite, had T_zz<=0, "
            f"or fell below the anisotropy gate ({f['min_anisotropy']:g}) — a section with no "
            "coherent reflector gradient cannot yield a dip"
        )
        out["dip_deg"] = unmeasured("deg", method=method, reason=reason, uncertainty=shared_unc)
        out["curvature"] = unmeasured("1/m", method=method, reason=reason, uncertainty=shared_unc)
        out["dip_azimuth_deg"] = unmeasured(
            "deg_azimuth",
            method=method,
            reason=reason
            + "; an azimuth also requires a non-zero dip, which is unavailable here",
            uncertainty=shared_unc,
        )
        return out

    out["dip_deg"] = _reduce(
        float(np.mean(dip)),
        unit="deg",
        coverage=coverage,
        n_samples=n_valid,
        method=method,
        uncertainty={
            **shared_unc,
            "reduction": "mean of |dip| over valid samples (signed mean would cancel across the section)",
            "p5_deg": float(np.percentile(dip, 5)),
            "p50_deg": float(np.percentile(dip, 50)),
            "p95_deg": float(np.percentile(dip, 95)),
            "max_deg": float(np.max(dip)),
            "mean_signed_deg": float(np.mean(signed)),
            "spread_p95_p5_deg": _spread_deg(dip),
        },
        notes=shared_notes
        + [
            "VE-corrected: tan(theta_true) = tan(theta_apparent) / ve; "
            "an uncorrected display stretch inflates every dip in this field",
            "dip of the locally dominant reflector gradient — at a truncation or a crossing "
            "reflector the tensor angle is an average of two populations",
        ],
    )

    out["curvature"] = _reduce(
        float(np.mean(curv)) if n_curv else None,
        unit="1/m",
        coverage=(n_curv / n_interior) if n_interior else 0.0,
        n_samples=n_curv,
        method=method
        + "; curvature kappa = d(theta)/d(s) in the true metric "
        "(dtheta/dx + dtheta/dz*tan(theta)) * cos(theta)",
        uncertainty={
            **shared_unc,
            "reduction": "mean of |kappa| over valid samples",
            "p50_1_m": float(np.percentile(curv, 50)) if n_curv else None,
            "p95_1_m": float(np.percentile(curv, 95)) if n_curv else None,
            "mean_signed_1_m": float(np.mean(signed_curv)) if n_curv else None,
            "radius_of_curvature_median_m": (
                float(1.0 / np.percentile(curv, 50)) if n_curv and np.percentile(curv, 50) > 0 else None
            ),
        },
        notes=shared_notes
        + [
            "kappa is a differential of a smoothed field: it is the noisiest number this layer emits "
            "and is reported with its p50/p95 alongside",
            "kappa additionally requires a VALID 1-px neighbourhood (morphological core): a difference "
            "stencil spanning an invalid pixel would read a zero-fill and invent curvature",
        ],
    )

    az_mean = _circular_mean_deg(az_valid)
    if az_mean is None:
        out["dip_azimuth_deg"] = unmeasured(
            "deg_azimuth",
            method=method + "; circular mean (atan2 of summed unit vectors)",
            reason=(
                "no sample has |dip| >= "
                f"{AZIMUTH_MIN_ABS_DIP_DEG:g} deg, so no dip direction exists to average — a flat "
                "field has no azimuth (this is not 0 deg)"
            ),
            uncertainty={**shared_unc, "n_azimuth_samples": 0},
            notes=shared_notes,
        )
    else:
        az_cov = (az_valid.size / n_valid) if n_valid else 0.0
        out["dip_azimuth_deg"] = _reduce(
            az_mean,
            unit="deg_azimuth",
            coverage=az_cov,
            n_samples=int(az_valid.size),
            method=method + "; circular mean (atan2 of summed unit vectors) — azimuths are circular",
            uncertainty={
                **shared_unc,
                "n_azimuth_samples": int(az_valid.size),
                "azimuth_min_abs_dip_deg": AZIMUTH_MIN_ABS_DIP_DEG,
                "azimuth_convention": "clockwise from +x (the trace / section x axis), in-section apparent",
                "dimension": "2-D section — this is NOT a 3-D azimuth; a 3-D orientation needs "
                "spatial import (Axis C)",
                "r_vector_length": (
                    float(np.hypot(np.sum(np.sin(np.radians(az_valid))), np.sum(np.cos(np.radians(az_valid)))))
                    / az_valid.size
                    if az_valid.size
                    else None
                ),
            },
            notes=shared_notes
            + [
                "in-section apparent dip azimuth only: it cannot distinguish dip to the right (+x) "
                "from dip into or out of the section",
            ],
        )
    return out


# ── geometry classification (declared rules only) ──────────────────────────────────────
def _rule_planar(dip_mag: np.ndarray, curvature_mean: float) -> tuple[bool, str, dict[str, Any]]:
    spread = _spread_deg(dip_mag)
    ok = (
        dip_mag.size >= 5
        and spread <= PLANAR_MAX_SPREAD_DEG
        and abs(curvature_mean) <= PLANAR_MAX_ABS_CURVATURE_1_M
    )
    receipt = (
        f"{RULE_PLANAR} spread_p95_p5={spread:.3f} deg (max {PLANAR_MAX_SPREAD_DEG:g}), "
        f"|curvature_mean|={abs(curvature_mean):.3e} 1/m (max {PLANAR_MAX_ABS_CURVATURE_1_M:g}), "
        f"n={dip_mag.size} -> {'FIRED' if ok else 'not fired'}"
    )
    return ok, receipt, {
        "spread_p95_p5_deg": spread,
        "curvature_mean_1_m": float(curvature_mean),
        "n_samples": int(dip_mag.size),
    }


def _rule_kinked(
    dip_mag: np.ndarray, z_m: np.ndarray, x_m: np.ndarray
) -> tuple[bool, str, dict[str, Any]]:
    """Discrete dip-domain boundary: two tight dip domains separated by a jump, in x order."""
    n = dip_mag.size
    min_side = max(3, int(math.ceil(KINK_MIN_GROUP_FRACTION * n)))
    best: dict[str, Any] | None = None
    if n >= 2 * min_side + 2 * KINK_BOUNDARY_SKIP_SAMPLES:
        order = np.lexsort((z_m, x_m))  # along the horizon: by x, then depth
        d_s = dip_mag[order]
        x_s = x_m[order]
        for k in range(min_side + KINK_BOUNDARY_SKIP_SAMPLES, n - min_side - KINK_BOUNDARY_SKIP_SAMPLES + 1):
            lo = d_s[: k - KINK_BOUNDARY_SKIP_SAMPLES]
            hi = d_s[k + KINK_BOUNDARY_SKIP_SAMPLES :]
            if lo.size < min_side or hi.size < min_side:
                continue
            lo_mean = float(np.mean(lo))
            hi_mean = float(np.mean(hi))
            jump = abs(hi_mean - lo_mean)
            lo_spread = _spread_deg(lo)
            hi_spread = _spread_deg(hi)
            if (
                jump >= KINK_MIN_GAP_DEG
                and lo_spread <= KINK_MAX_SIDE_SPREAD_DEG
                and hi_spread <= KINK_MAX_SIDE_SPREAD_DEG
            ):
                if best is None or jump > best["jump_deg"]:
                    best = {
                        "boundary_index": int(k),
                        "x_boundary_m": float(x_s[k]),
                        "jump_deg": jump,
                        "dip_mean_lo_deg": lo_mean,
                        "dip_mean_hi_deg": hi_mean,
                        "lo_spread_deg": lo_spread,
                        "hi_spread_deg": hi_spread,
                        "n_lo": int(lo.size),
                        "n_hi": int(hi.size),
                        "boundary_zone_samples": int(2 * KINK_BOUNDARY_SKIP_SAMPLES),
                    }
    ok = best is not None
    receipt = (
        f"{RULE_KINKED} "
        + (
            f"boundary at index {best['boundary_index']} (x={best['x_boundary_m']:.1f} m): "
            f"jump={best['jump_deg']:.3f} deg (min {KINK_MIN_GAP_DEG:g}), "
            f"side spreads={best['lo_spread_deg']:.3f}/{best['hi_spread_deg']:.3f} deg "
            f"(max {KINK_MAX_SIDE_SPREAD_DEG:g}) -> FIRED"
            if best is not None
            else f"no split with jump >= {KINK_MIN_GAP_DEG:g} deg and both sides tight "
            f"(p95-p5 <= {KINK_MAX_SIDE_SPREAD_DEG:g} deg) and both sides >= {KINK_MIN_GROUP_FRACTION:g} "
            f"of n={n} -> not fired"
        )
    )
    return ok, receipt, best or {"n_samples": int(n)}


def _rule_listric(dip_mag: np.ndarray, z_m: np.ndarray) -> tuple[bool, str, dict[str, Any]]:
    n = dip_mag.size
    span = _spread_deg(dip_mag)
    rho: float | None = None
    p_value: float | None = None
    if n >= LISTRIC_MIN_SAMPLES and float(np.ptp(z_m)) > 0.0:
        res = _stats.spearmanr(z_m, dip_mag)
        rho = float(res.statistic)
        p_value = float(res.pvalue)
    ok = (
        rho is not None
        and n >= LISTRIC_MIN_SAMPLES
        and span >= LISTRIC_MIN_DIP_RANGE_DEG
        and rho >= LISTRIC_MIN_SPEARMAN
    )
    receipt = (
        f"{RULE_LISTRIC} n={n} (min {LISTRIC_MIN_SAMPLES}), dip_range_p95_p5={span:.3f} deg "
        f"(min {LISTRIC_MIN_DIP_RANGE_DEG:g}), spearman(|dip|, depth)="
        f"{'n/a' if rho is None else f'{rho:.3f}'} (min {LISTRIC_MIN_SPEARMAN:g}) -> "
        f"{'FIRED' if ok else 'not fired'}"
    )
    return ok, receipt, {
        "spearman_rho": rho,
        "spearman_p_value": p_value,
        "dip_range_p95_p5_deg": span,
        "n_samples": int(n),
        "reduction": "dip magnitude vs sample depth (relative to section top: the absolute datum is "
        "unknown and Spearman is rank-based, so the datum does not matter)",
    }


def extract_axis_a(
    section: np.ndarray,
    horizon_mask: np.ndarray,
    *,
    dz_m: float,
    dx_m: float,
    ve: float = 1.0,
) -> dict[str, Measurement]:
    """Per-horizon shape metrics, plus a declared-rule ``geometry_class_fired``.

    Returns keys: ``"dip_deg_mean"``, ``"dip_deg_p95"``, ``"curvature_mean"``,
    ``"dip_azimuth_deg"``, ``"geometry_class_fired"``.

    ``geometry_class_fired`` carries value ``1.0`` **only** when a rule in
    :data:`GEOMETRY_RULES` fires *and* its decision inputs are ``MEASURED``; the rule name is
    in ``Measurement.method``, the class in ``uncertainty["class"]``, and every rule that was
    evaluated — fired or not — leaves a receipt in ``uncertainty["rule_evaluations"]`` and
    ``notes``. Otherwise it is ``UNMEASURED`` with value ``None``. ``"listric"`` is an
    interpretation, never a raw CV output (CONTRACT §7 rule 3).

    ``dip_deg_mean`` / ``dip_deg_p95`` are reductions of the dip **magnitude** (the signed
    statistics are in ``uncertainty``): the downstream consumer is an angle-of-repose
    comparison, which is a magnitude test. ``coverage`` is the fraction of the *picked
    horizon* that had valid tensor input — gaps are counted, never interpolated over.
    """
    arr = _as_section(section)
    mask = np.asarray(horizon_mask, dtype=bool)
    if mask.shape != arr.shape:
        raise ValueError(
            f"horizon_mask shape {mask.shape} does not match section shape {arr.shape}"
        )
    f = _dip_field(arr, dz_m=dz_m, dx_m=dx_m, ve=ve)
    method = _field_method(f)

    n_mask = int(mask.sum())
    if n_mask == 0:
        reason = "horizon_mask contains no True samples — there is no horizon to measure"
        empty = {k: unmeasured(_unit_for(k), method=method, reason=reason) for k in
                 ("dip_deg_mean", "dip_deg_p95", "curvature_mean", "dip_azimuth_deg")}
        empty["geometry_class_fired"] = unmeasured(
            "count",
            method="geometry-rule-set[" + "|".join(GEOMETRY_RULES) + "]",
            reason=reason + " — no rule can be evaluated without horizon samples",
        )
        return empty

    valid_mask = mask & f["valid"]
    n_valid = int(valid_mask.sum())
    coverage = n_valid / n_mask
    rows, cols = np.nonzero(valid_mask)

    curv_mask = mask & f["curv_valid"]
    n_curv = int(curv_mask.sum())
    curv_coverage = n_curv / n_mask

    dz_true = f["dz_true_m"]
    dx = f["dx_m"]
    z_m = rows.astype(float) * dz_true
    x_m = cols.astype(float) * dx
    dip_mag = np.abs(f["dip_signed_deg"][valid_mask])
    dip_signed = f["dip_signed_deg"][valid_mask]
    curv = f["curvature_1_m"][curv_mask]
    az = f["azimuth_deg"][valid_mask]

    shared_unc: dict[str, Any] = {
        "sigma": f["sigma"],
        "dz_m": f["dz_m"],
        "dx_m": f["dx_m"],
        "dz_true_m": dz_true,
        "vertical_exaggeration": f["ve"],
        "min_anisotropy": f["min_anisotropy"],
        "guard_px": f["guard_px"],
        "n_mask_samples": n_mask,
        "n_invalid_mask_samples": n_mask - n_valid,
        "invalid_mask_fraction": 1.0 - coverage,
        "n_curvature_samples": n_curv,
        "n_curvature_dropped_for_invalid_neighbour": n_valid - n_curv,
        "depth_basis": "depth measured from the top of the section array (relative); absolute datum "
        "is unknown to this layer",
    }
    gap_note = (
        f"coverage={coverage:.3f}: {n_mask - n_valid} of {n_mask} picked samples had no valid "
        "structure-tensor input (border guard, T_zz<=0, or below the anisotropy gate); they are "
        "excluded and counted, never interpolated"
    )
    shared_notes = [gap_note, _INTERIOR_NOTE]

    out: dict[str, Measurement] = {}
    dip_mean = float(np.mean(dip_mag)) if n_valid else None
    dip_p95 = float(np.percentile(dip_mag, 95)) if n_valid else None
    curv_mean = float(np.mean(curv)) if n_curv else None

    out["dip_deg_mean"] = _reduce(
        dip_mean,
        unit="deg",
        coverage=coverage,
        n_samples=n_valid,
        method=method,
        uncertainty={
            **shared_unc,
            "reduction": "mean of |dip| over the picked horizon",
            "mean_signed_deg": float(np.mean(dip_signed)) if n_valid else None,
            "p50_deg": float(np.percentile(dip_mag, 50)) if n_valid else None,
        },
        notes=shared_notes,
    )
    out["dip_deg_p95"] = _reduce(
        dip_p95,
        unit="deg",
        coverage=coverage,
        n_samples=n_valid,
        method=method,
        uncertainty={
            **shared_unc,
            "reduction": "95th percentile of |dip| over the picked horizon",
            "spread_p95_p5_deg": _spread_deg(dip_mag) if n_valid else None,
            "max_deg": float(np.max(dip_mag)) if n_valid else None,
            "angle_of_repose_input": "this is the number the angle-of-repose and "
            "K-REGIME-DISPLAY gates consume; it is a magnitude",
        },
        notes=shared_notes,
    )
    out["curvature_mean"] = _reduce(
        curv_mean,
        unit="1/m",
        coverage=curv_coverage,
        n_samples=n_curv,
        method=method
        + "; curvature kappa = d(theta)/d(s) in the true metric "
        "(dtheta/dx + dtheta/dz*tan(theta)) * cos(theta)",
        uncertainty={
            **shared_unc,
            "reduction": "mean SIGNED curvature over the picked horizon (a horizon rolls one way; "
            "the sign is orientation-informative here and is not thrown away)",
            "interpretation": "kappa > 0 = steepens toward +x (down-dip steepening, listric-rollover "
            "sense); kappa < 0 = flattens toward +x",
            "p50_1_m": float(np.percentile(curv, 50)) if n_curv else None,
            "abs_mean_1_m": float(np.mean(np.abs(curv))) if n_curv else None,
        },
        notes=shared_notes
        + [
            "curvature coverage is lower than dip coverage where picked samples sit next to "
            "unmeasurable ground: a difference stencil across an invalid pixel reads a zero-fill",
        ],
    )

    az_valid = az[np.isfinite(az)]
    az_mean = _circular_mean_deg(az_valid)
    if az_mean is None:
        out["dip_azimuth_deg"] = unmeasured(
            "deg_azimuth",
            method=method + "; circular mean (atan2 of summed unit vectors)",
            reason=(
                "no picked sample has |dip| >= "
                f"{AZIMUTH_MIN_ABS_DIP_DEG:g} deg: a (near-)flat horizon has no dip direction, so "
                "its azimuth is undefined — not 0"
            ),
            uncertainty={**shared_unc, "n_azimuth_samples": 0},
            notes=shared_notes,
        )
    else:
        out["dip_azimuth_deg"] = _reduce(
            az_mean,
            unit="deg_azimuth",
            coverage=(az_valid.size / n_valid) if n_valid else 0.0,
            n_samples=int(az_valid.size),
            method=method + "; circular mean (atan2 of summed unit vectors) — azimuths are circular",
            uncertainty={
                **shared_unc,
                "n_azimuth_samples": int(az_valid.size),
                "azimuth_convention": "clockwise from +x (trace axis), in-section apparent dip azimuth",
                "dimension": "2-D section — NOT a 3-D azimuth",
                "r_vector_length": float(
                    np.hypot(
                        np.sum(np.sin(np.radians(az_valid))), np.sum(np.cos(np.radians(az_valid)))
                    )
                )
                / az_valid.size,
            },
            notes=shared_notes
            + ["a circular mean of dip directions: 350 deg and 10 deg average to 0 deg, never to 180 deg"],
        )

    out["geometry_class_fired"] = _classify(
        dip_mag=dip_mag,
        z_m=z_m,
        x_m=x_m,
        curvature_mean=curv_mean,
        inputs_measured=(
            out["dip_deg_p95"].status == "MEASURED" and out["curvature_mean"].status == "MEASURED"
        ),
        input_statuses={
            "dip_deg_p95": out["dip_deg_p95"].status,
            "curvature_mean": out["curvature_mean"].status,
            "dip_deg_mean": out["dip_deg_mean"].status,
        },
        coverage=coverage,
        n_samples=n_valid,
        method=method,
    )
    return out


_UNITS: dict[str, str] = {
    "dip_deg_mean": "deg",
    "dip_deg_p95": "deg",
    "curvature_mean": "1/m",
    "dip_azimuth_deg": "deg_azimuth",
    "geometry_class_fired": "count",
}


def _unit_for(key: str) -> str:
    return _UNITS.get(key, "ratio")


def _classify(
    *,
    dip_mag: np.ndarray,
    z_m: np.ndarray,
    x_m: np.ndarray,
    curvature_mean: float | None,
    inputs_measured: bool,
    input_statuses: dict[str, str],
    coverage: float,
    n_samples: int,
    method: str,
) -> Measurement:
    rule_method = "geometry-rule-set[" + "|".join(GEOMETRY_RULES) + "]"
    evaluations: list[str] = []
    fired: str | None = None
    evidence: dict[str, Any] = {"n_samples": int(n_samples), "input_statuses": input_statuses}

    if n_samples == 0:
        return unmeasured(
            "count",
            method=rule_method,
            reason="no valid horizon samples: no declared rule has any input to evaluate",
            uncertainty=evidence,
            notes=["geometry_class is not emitted — UNMEASURED, not 'planar' and not 'unknown'"],
        )

    if not inputs_measured or curvature_mean is None:
        return unmeasured(
            "count",
            method=rule_method,
            reason=(
                "no rule may fire: the decision inputs are not MEASURED "
                f"({input_statuses}) — CONTRACT §4 emits a geometry class only from MEASURED inputs"
            ),
            uncertainty=evidence,
            notes=[
                "a partially readable horizon cannot carry a geometry classification; the "
                "classification would outrank its own evidence",
                f"coverage={coverage:.3f}",
            ],
        )

    # Precedence: a discrete dip-domain boundary outranks a trend, and both outrank 'planar'.
    kink_ok, kink_receipt, kink_ev = _rule_kinked(dip_mag, z_m, x_m)
    evaluations.append(kink_receipt)
    if kink_ok:
        fired = RULE_KINKED
        evidence["kink"] = kink_ev
    else:
        planar_ok, planar_receipt, planar_ev = _rule_planar(dip_mag, curvature_mean)
        evaluations.append(planar_receipt)
        evidence["planar"] = planar_ev
        if planar_ok:
            fired = RULE_PLANAR
        else:
            listric_ok, listric_receipt, listric_ev = _rule_listric(dip_mag, z_m)
            evaluations.append(listric_receipt)
            evidence["listric"] = listric_ev
            if listric_ok:
                fired = RULE_LISTRIC

    evidence["rule_evaluations"] = evaluations
    evidence["rule_precedence"] = {
        name: rule["precedence"] for name, rule in GEOMETRY_RULES.items()
    }

    if fired is None:
        return unmeasured(
            "count",
            method=rule_method,
            reason=(
                "no declared geometry rule fired — the measured numbers are reported, the "
                "classification is withheld (CONTRACT §7 rule 3: 'listric' is not a CV output)"
            ),
            uncertainty=evidence,
            notes=[
                "each rule's predicate and outcome is recorded in uncertainty['rule_evaluations']",
                "values are still available: dip_deg_mean, dip_deg_p95, curvature_mean",
            ],
        )

    rule = GEOMETRY_RULES[fired]
    return measured(
        1.0,
        "count",
        coverage=float(coverage),
        n_samples=int(n_samples),
        method=fired,
        uncertainty={
            **evidence,
            "class": rule["class"],
            "rule": fired,
            "declared_predicate": rule["declared"],
            "parameters": rule["params"],
            "precedence": rule["precedence"],
        },
        notes=[
            f"geometry_class={rule['class']}",
            f"emitted by declared rule {fired} (method field). Predicate: {rule['declared']}",
            "this is an INTERPRETATION of measured dip/curvature under a named rule — not a raw "
            "CV output, and not a tectonic verdict (CONTRACT §7 rule 3)",
            f"evaluation receipts: {'; '.join(evaluations)}",
        ],
    )
