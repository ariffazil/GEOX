"""Axis C — Orientation: fault azimuth populations with CIRCULAR statistics.

CONTRACT.md §4 (Axis C) — `extract_fault_azimuths`, `azimuth_population_stats`,
`conjugate_pair_test`.

Why this module exists
----------------------
An LLM must never read azimuths off a picture. It calls this module, which returns
*numbers with coverage and uncertainty*. Nothing here returns a probability, a
confidence, or a verdict (CONTRACT.md §0, §3).

The one bug this module exists to prevent
-----------------------------------------
**Azimuth is a CIRCULAR quantity.** Linear averaging of 350 deg and 10 deg gives
180 deg, which is 170 deg wrong. Every reduction in this module goes through
`atan2` of summed unit vectors (or doubled angles for axial data). There is no
`np.mean(azimuths)` anywhere in this file, and there must never be one.

What this module deliberately does NOT do
-----------------------------------------
It does not emit a stress axis. `conjugate_pair_test` observes a *geometric*
conjugate pair and reports the acute bisector and the acute dihedral angle as
OBSERVATIONS. The acute bisector of a conjugate pair is sigma1 in Anderson's
theory, but converting it into a stress state requires fault-slip inversion with
observed slip sense (4 of 6 paleostress parameters), which is arifOS's job.
`K-REGIME-CEILING` KILLs any stress tensor derived from geometry alone
(CONTRACT.md §7 item 9).

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np

from .types import Measurement, measured, unmeasured

__all__ = [
    "circular_mean_deg",
    "acute_angle_between_deg",
    "extract_fault_azimuths",
    "azimuth_population_stats",
    "conjugate_pair_test",
]

# A chord shorter than this (metres) has no defined azimuth — a closed polygon or a
# digitising artefact would otherwise produce a spurious direction.
_CHORD_EPS_M = 1e-9
_R_EPS = 1e-12
# Below this r_vector_length a population carries no preferred orientation.
_DEFAULT_MIN_R_PREFERRED = 0.2


# ─────────────────────────────────────────────────────────────────────────────
# circular primitives
# ─────────────────────────────────────────────────────────────────────────────


def _fold_deg(deg: float, period: float) -> float:
    """Wrap an angle into [0, period), snapping the wrap point to 0.0.

    Without the snap, a circular mean that lands 1e-14 deg below 360 comes back as the
    float 360.0 — numerically the same direction, but outside the declared range and
    enough to break a range assertion downstream.
    """
    period = float(period)
    v = float(deg) % period
    if v >= period - 1e-9 or v < 1e-12:
        return 0.0
    return v


def circular_mean_deg(
    azimuths: Sequence[float] | np.ndarray,
    *,
    axial: bool = False,
) -> tuple[float, float]:
    """(mean_deg, r_vector_length) — the ONLY legal way to reduce azimuths here.

    Directional (``axial=False``): azimuths are compass bearings in degrees measured
    clockwise from +y (north). The mean is ``atan2(sum sin, sum cos)`` and ``r`` is the
    resultant vector length in 0..1 (0 = uniform / no preferred direction, 1 = every
    measurement identical).

    Axial (``axial=True``): the measurements are *lines*, not *directions* — a fault
    trace digitised north-to-south and the same trace digitised south-to-north carry a
    180 deg difference that is geologically meaningless. Doubled angles (2*theta) are
    averaged, so the result is a line orientation in [0, 180) and the arithmetic stays
    circular. This is the Rosenbusch convention for a strike population.

    Raises ValueError on an empty input — an undefined mean is not a number.
    """
    arr = np.asarray(azimuths, dtype=float).ravel()
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError("circular_mean_deg requires at least one finite azimuth")
    ang = np.radians(arr * 2.0 if axial else arr)
    cos_sum = float(np.cos(ang).sum())
    sin_sum = float(np.sin(ang).sum())
    r = math.hypot(cos_sum, sin_sum) / float(arr.size)
    mean = math.degrees(math.atan2(sin_sum, cos_sum))
    if axial:
        return _fold_deg(mean / 2.0, 180.0), r
    return _fold_deg(mean, 360.0), r


def acute_angle_between_deg(a_deg: float, b_deg: float) -> float:
    """Acute angle between two LINE orientations (each modulo 180), in 0..90 deg."""
    d = abs((float(a_deg) - float(b_deg)) % 180.0)
    return float(min(d, 180.0 - d))


def _circular_std_deg(r: float) -> float:
    """Fisher's dispersion estimate sqrt(-2 ln R), in degrees.

    Diverges as R -> 0 (uniform distribution): the caller must declare the ceiling
    rather than silently returning inf. R is clamped to 1 so float noise in the
    resultant length cannot make the logarithm positive, and the perfectly concentrated
    case returns +0.0 (not the -0.0 that sqrt(-0.0) would produce).
    """
    r = float(r)
    if r >= 1.0:
        return 0.0
    if r <= _R_EPS:
        return float("inf")
    return math.degrees(math.sqrt(max(-2.0 * math.log(r), 0.0)))


def _coverage_status(n_valid: int, n_total: int) -> tuple[float, bool]:
    """(coverage, is_partial) — partial when part of the input could not be used."""
    if n_total <= 0:
        return 1.0, False
    cov = float(n_valid) / float(n_total)
    return cov, (n_valid != n_total)


# ─────────────────────────────────────────────────────────────────────────────
# Axis C.1 — per-polyline chord azimuths
# ─────────────────────────────────────────────────────────────────────────────


def _as_polyline(obj: Any) -> np.ndarray | None:
    """Coerce to an (N>=2, 2) finite float array, else None (caller records the skip)."""
    try:
        arr = np.asarray(obj, dtype=float)
    except (TypeError, ValueError):
        return None
    if arr.ndim != 2 or arr.shape[1] != 2 or arr.shape[0] < 2:
        return None
    if not np.all(np.isfinite(arr)):
        return None
    return arr


def _chord_azimuth(poly: np.ndarray) -> tuple[float, float] | None:
    """(azimuth_deg in [0,360), chord_length_m) for a polyline, or None if degenerate.

    Azimuth convention: ``atan2(dx, dy)`` with +x = east and +y = north, so 0 = due
    north and 90 = due east (clockwise positive). The chord runs first-vertex ->
    last-vertex, therefore the value carries the *digitising direction*; fault traces
    are lines, not arrows — pass ``axial=True`` (or fold to [0,180)) when the digitising
    direction is not consistent across the population.
    """
    dx = float(poly[-1, 0] - poly[0, 0])
    dy = float(poly[-1, 1] - poly[0, 1])
    length = math.hypot(dx, dy)
    if length < _CHORD_EPS_M:
        return None
    return _fold_deg(math.degrees(math.atan2(dx, dy)), 360.0), length


def extract_fault_azimuths(
    fault_polylines: list[np.ndarray],
    *,
    x_origin_m: float = 0.0,
    y_origin_m: float = 0.0,
    axial: bool = False,
    min_r_for_preferred: float = _DEFAULT_MIN_R_PREFERRED,
) -> dict[str, Any]:
    """Azimuth of each polyline's end-to-end chord, plus the population reduction.

    NOTE ON THE SIGNATURE: CONTRACT.md §4 declares the return type as
    ``dict[str, Measurement]`` while also specifying ``"azimuth_rosenbusch" (list)``.
    Those two clauses cannot both be literally true; the behaviour follows the key
    specification (a list of the raw per-polyline azimuths) and the annotation is
    widened to ``dict[str, Any]`` rather than lying about it. Every other entry is a
    Measurement.

    Contract keys
    -------------
    ``"azimuth_deg"``        Measurement — the CIRCULAR mean of the chord azimuths.
    ``"azimuth_rosenbusch"`` list[float] — the per-polyline azimuths, i.e. the raw
                             distribution that a Rosenbusch / rose diagram is drawn
                             from. This entry is a LIST, not a Measurement, because it
                             is the evidence set behind the mean.
    ``"n_polylines"``        Measurement — how many polylines contributed a defined
                             chord (``uncertainty`` records how many were rejected).

    Additional mirrors (additive, for the §5 bundle)
    -----------------------------------------------
    ``"r_vector_length"``, ``"circular_std_deg"``, ``"population"`` (the full
    `azimuth_population_stats` result).

    Geometry contract
    -----------------
    Azimuth is CIRCULAR: never averaged linearly here (350 deg and 10 deg average
    linearly to 180 deg — 170 deg wrong). ``x_origin_m`` / ``y_origin_m`` are recorded
    for provenance only; azimuth is translation-invariant, and pretending otherwise
    would be a fabricated sensitivity.

    Degenerate input is skipped, never guessed: fewer than 2 vertices, non-finite
    coordinates, or a zero-length chord has no azimuth, so coverage falls below 1.0 and
    the reason lands in ``notes``.
    """
    polylines = list(fault_polylines or [])
    n_input = len(polylines)

    azimuths: list[float] = []
    lengths: list[float] = []
    centroids: list[tuple[float, float]] = []
    rejects: list[str] = []

    for idx, raw in enumerate(polylines):
        poly = _as_polyline(raw)
        if poly is None:
            rejects.append(
                f"polyline[{idx}]: not an (N>=2, 2) finite float array — skipped, "
                "no azimuth defined"
            )
            continue
        chord = _chord_azimuth(poly)
        if chord is None:
            rejects.append(
                f"polyline[{idx}]: end-to-end chord length < {_CHORD_EPS_M:g} m "
                "(closed or zero-length trace) — skipped, no azimuth defined"
            )
            continue
        az, length = chord
        if axial:
            az = _fold_deg(az, 180.0)
        azimuths.append(az)
        lengths.append(length)
        centroids.append((float(poly[:, 0].mean()), float(poly[:, 1].mean())))

    n_valid = len(azimuths)
    array = np.asarray(azimuths, dtype=float)
    population = azimuth_population_stats(
        array, axial=axial, min_r_for_preferred=min_r_for_preferred
    )

    method = (
        "end_to_end_chord_azimuth atan2(dx,dy) degrees clockwise from north (+y); "
        "population reduced by circular_mean_deg (atan2 of summed unit vectors, "
        "doubled angles when axial=True)"
    )
    unit = "deg" if axial else "deg_azimuth"

    az_meas = population["circular_mean_deg"]
    if az_meas.status == "UNMEASURED":
        azimuth_deg = unmeasured(
            unit, method=method, reason=f"no usable polyline chord (n_input={n_input})"
        )
    elif az_meas.status == "PARTIAL":
        azimuth_deg = Measurement(
            value=az_meas.value,
            unit=unit,
            status="PARTIAL",
            n_samples=az_meas.n_samples,
            coverage=az_meas.coverage,
            method=method,
            uncertainty=az_meas.uncertainty,
            notes=list(az_meas.notes) + rejects[:20],
        )
    else:
        azimuth_deg = Measurement(
            value=az_meas.value,
            unit=unit,
            status="MEASURED",
            n_samples=az_meas.n_samples,
            coverage=az_meas.coverage,
            method=method,
            uncertainty=az_meas.uncertainty,
            notes=list(az_meas.notes) + rejects[:20],
        )

    if n_valid:
        dx = float(np.mean([c[0] for c in centroids]) - x_origin_m)
        dy = float(np.mean([c[1] for c in centroids]) - y_origin_m)
    else:
        dx = dy = 0.0
    azimuth_deg.uncertainty.update(
        {
            "n_input": n_input,
            "n_skipped": n_input - n_valid,
            "chord_length_m": {
                "min": float(min(lengths)) if lengths else None,
                "max": float(max(lengths)) if lengths else None,
            },
            "x_origin_m": float(x_origin_m),
            "y_origin_m": float(y_origin_m),
            "population_centroid_offset_m": [dx, dy],
            "note_on_origin": (
                "azimuth is translation-invariant; origins are provenance only"
            ),
        }
    )

    cov, _ = _coverage_status(n_valid, n_input)
    if n_input == 0:
        n_polylines = unmeasured(
            "count", method=method, reason="no polylines supplied — nothing to measure"
        )
    else:
        n_polylines = measured(
            float(n_valid),
            "count",
            coverage=cov,
            n_samples=n_valid,
            method=method,
            uncertainty={"n_input": n_input, "n_skipped": n_input - n_valid},
            notes=list(rejects[:20]),
        )

    return {
        "azimuth_deg": azimuth_deg,
        "azimuth_rosenbusch": [float(a) for a in azimuths],
        "n_polylines": n_polylines,
        "r_vector_length": population["r_vector_length"],
        "circular_std_deg": population["circular_std_deg"],
        "population": population,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Axis C.2 — population statistics
# ─────────────────────────────────────────────────────────────────────────────


def azimuth_population_stats(
    azimuths: np.ndarray,
    *,
    axial: bool = False,
    min_r_for_preferred: float = _DEFAULT_MIN_R_PREFERRED,
) -> dict[str, Measurement]:
    """Circular statistics of an azimuth population.

    Contract keys
    -------------
    ``"circular_mean_deg"``  atan2 of summed unit vectors (doubled angles if axial).
    ``"circular_std_deg"``   sqrt(-2 ln R) converted to degrees (Fisher). When R is
                             ~0 the distribution is uniform and the dispersion is
                             undefined — the ceiling of 180 deg is reported with
                             status PARTIAL and an explicit note, never an inf and
                             never a silent zero.
    ``"r_vector_length"``    0..1 concentration. **Near zero means there is NO
                             PREFERRED ORIENTATION** and a single "mean strike" is
                             meaningless; the note says so in words.
    ``"n"``                  how many finite azimuths entered the reduction.

    Additive mirror: ``"preferred_orientation"`` (1.0 / 0.0 / UNMEASURED), a declared
    threshold read of `r_vector_length` with the threshold named in `method`.

    Status discipline (CONTRACT.md §3): MEASURED only when every supplied azimuth was
    usable; PARTIAL with a note when some were rejected or when the quantity is not
    fully defined (n == 1 dispersion, R ~ 0 dispersion); UNMEASURED when n == 0.
    """
    arr = np.asarray(azimuths, dtype=float).ravel()
    n_total = int(arr.size)
    finite = arr[np.isfinite(arr)]
    n = int(finite.size)
    cov, partial_by_coverage = _coverage_status(n, n_total)

    method = (
        "circular statistics — resultant vector of unit vectors "
        + ("at doubled angles (axial / line data)" if axial else "at full angles")
    )
    period = 180.0 if axial else 360.0
    unit = "deg"

    excluded = [f"excluded {n_total - n} non-finite azimuth(s) of {n_total}"]

    if n == 0:
        return {
            "circular_mean_deg": unmeasured(
                unit, method=method, reason="no finite azimuths — mean undefined"
            ),
            "circular_std_deg": unmeasured(
                unit, method=method, reason="no finite azimuths — dispersion undefined"
            ),
            "r_vector_length": unmeasured(
                "ratio", method=method, reason="no finite azimuths — R undefined"
            ),
            "n": measured(
                0.0,
                "count",
                coverage=1.0,
                n_samples=0,
                method=method,
                uncertainty={"n_input": n_total},
                notes=excluded if n_total else [],
            ),
            "preferred_orientation": unmeasured(
                "bool",
                method=method,
                reason="n = 0 — orientation preference not testable",
            ),
        }

    mean, r = circular_mean_deg(finite, axial=axial)
    std = _circular_std_deg(r)
    no_preference = r < float(min_r_for_preferred)

    r_notes = list(excluded) if partial_by_coverage else []
    if no_preference:
        r_notes.append(
            f"r_vector_length = {r:.4f} < {min_r_for_preferred:.2f}: the population is "
            "essentially isotropic — there is NO PREFERRED ORIENTATION. A single "
            "'mean strike' is not representative of the fault population at this "
            "concentration; report the distribution (azimuth_rosenbusch), not just the mean."
        )
    else:
        r_notes.append(
            f"r_vector_length = {r:.4f} >= {min_r_for_preferred:.2f}: a preferred "
            "orientation is present in this population (concentration, not confidence)."
        )

    if n >= 2 and not partial_by_coverage:
        r_status = "MEASURED"
    else:
        r_status = "PARTIAL"
        if n < 2:
            r_notes.append("n = 1: R is 1.0 by construction — concentration is not measured.")

    r_kw: dict[str, Any] = dict(
        value=float(r),
        unit="ratio",
        status=r_status,
        n_samples=n,
        coverage=None if r_status == "UNMEASURED" else cov,
        method=method,
        uncertainty={"period_deg": period, "min_r_for_preferred": float(min_r_for_preferred)},
        notes=r_notes,
    )
    r_meas = Measurement(**r_kw)

    mean_notes = list(excluded) if partial_by_coverage else []
    mean_notes.append(
        "circular mean only — a linear mean of azimuths is wrong by construction "
        "(350 deg + 10 deg averages linearly to 180 deg)."
    )
    if no_preference:
        mean_notes.append(
            "NO PREFERRED ORIENTATION: the mean is reported because the quantity is "
            "defined, but it must not be read as a fault trend."
        )
    if n >= 2 and not partial_by_coverage:
        mean_meas = measured(
            mean,
            unit,
            coverage=cov,
            n_samples=n,
            method=method,
            uncertainty={"period_deg": period, "r_vector_length": float(r)},
            notes=mean_notes,
        )
    else:
        mean_meas = Measurement(
            value=float(mean),
            unit=unit,
            status="PARTIAL",
            n_samples=n,
            coverage=cov,
            method=method,
            uncertainty={"period_deg": period, "r_vector_length": float(r)},
            notes=mean_notes + ["n = 1: a single azimuth has no dispersion."],
        )

    if math.isfinite(std):
        std_meas = measured(
            std,
            unit,
            coverage=cov,
            n_samples=n,
            method=method + "; sigma = sqrt(-2 ln R) in degrees",
            uncertainty={"r_vector_length": float(r), "ceiling_deg": 180.0},
            notes=list(excluded) if partial_by_coverage else [],
        )
    else:
        std_meas = Measurement(
            value=180.0,
            unit=unit,
            status="PARTIAL",
            n_samples=n,
            coverage=cov,
            method=method + "; sigma = sqrt(-2 ln R) in degrees",
            uncertainty={"r_vector_length": float(r), "ceiling_deg": 180.0},
            notes=[
                "R ~ 0: the population is uniform, so sqrt(-2 ln R) diverges. The "
                "reported 180 deg is the declared ceiling, NOT a measured dispersion.",
                "This population has NO PREFERRED ORIENTATION.",
            ],
        )

    if n >= 2:
        preferred = measured(
            0.0 if no_preference else 1.0,
            "bool",
            coverage=cov,
            n_samples=n,
            method=(
                f"DECLARED RULE: preferred_orientation = 1.0 iff r_vector_length >= "
                f"{min_r_for_preferred:.2f} (threshold is a convention of this layer, "
                "not a probability)"
            ),
            uncertainty={"r_vector_length": float(r), "min_r_for_preferred": float(min_r_for_preferred)},
            notes=(
                ["NO PREFERRED ORIENTATION — report the full distribution instead."]
                if no_preference
                else ["Preferred orientation present; the distribution is still the evidence."]
            ),
        )
    else:
        preferred = unmeasured(
            "bool",
            method="DECLARED RULE: preferred_orientation needs n >= 2",
            reason="n < 2 — orientation preference is not testable",
        )

    return {
        "circular_mean_deg": mean_meas,
        "circular_std_deg": std_meas,
        "r_vector_length": r_meas,
        "n": measured(
            float(n),
            "count",
            coverage=1.0 if n_total <= 0 else cov,
            n_samples=n,
            method=method,
            uncertainty={"n_input": n_total, "n_excluded": n_total - n},
            notes=excluded if partial_by_coverage else [],
        ),
        "preferred_orientation": preferred,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Axis C.3 — conjugate pair observation (NEVER a stress axis)
# ─────────────────────────────────────────────────────────────────────────────


def _best_two_cluster_split(
    theta: np.ndarray, *, min_cluster_n: int
) -> tuple[tuple[int, int], float, float, float, float] | None:
    """Split a set of axial orientations (in [0,180)) into the best two contiguous arcs.

    Deterministic: every gap between adjacent sorted values is tried as the partition
    boundary (the wrap-around gap is covered by rotating the circle by 90 deg and
    re-sorting). Score = min(r_a, r_b) — the WORST of the two clusters, because a pair
    is only as convincing as its least concentrated member — then max(r_a + r_b).

    Returns (sizes, r_a, r_b, mean_a, mean_b) or None when no two-group split exists.
    """
    n = int(theta.size)
    if n < 2 * min_cluster_n:
        return None

    best: tuple[tuple[float, float], tuple[int, int], float, float, float, float] | None = None

    for rotation in (0.0, 90.0):
        rotated = np.sort(_fold_array(theta + rotation, 180.0))
        for i in range(1, n):
            a = rotated[:i]
            b = rotated[i:]
            if a.size < min_cluster_n or b.size < min_cluster_n:
                continue
            mean_a, r_a = circular_mean_deg(a, axial=True)
            mean_b, r_b = circular_mean_deg(b, axial=True)
            score = (min(r_a, r_b), r_a + r_b)
            if best is None or score > best[0]:
                best = (
                    score,
                    (int(a.size), int(b.size)),
                    float(r_a),
                    float(r_b),
                    float(mean_a),
                    float(mean_b),
                )

    if best is None:
        return None
    _, sizes, r_a, r_b, mean_a, mean_b = best
    return sizes, r_a, r_b, mean_a, mean_b


def _fold_array(arr: np.ndarray, period: float) -> np.ndarray:
    return np.mod(np.asarray(arr, dtype=float), float(period))


def conjugate_pair_test(
    azimuths: np.ndarray,
    *,
    min_cluster_n: int = 3,
    min_n: int = 6,
    min_r: float = 0.8,
    min_dihedral_deg: float = 20.0,
    max_dihedral_deg: float = 90.0,
) -> dict[str, Any]:
    """Observe whether a fault-azimuth population resolves into a conjugate pair.

    Returns EXACTLY four keys — ``{"pair_detected", "bisector_acute_deg",
    "dihedral_acute_deg", "evidence"}`` — and nothing else.

    *** THIS FUNCTION NEVER EMITS A STRESS AXIS. ***

    The acute bisector of a conjugate fault pair IS sigma1 under Anderson's theory of
    conjugate shear failure. That is a textbook statement, and it is still not a
    measurement this layer is allowed to make: converting a bisector into a stress
    state requires *observed slip sense* on each fault and a fault-slip inversion
    (4 of 6 paleostress parameters). Handing a stress axis to a downstream reasoning
    agent from geometry alone is the K-REGIME-CEILING category error (CONTRACT.md §7
    item 9). The bisector is returned as an ORIENTATION OBSERVATION and carries no
    stress interpretation. Stress is arifOS's call, with fault-slip data.

    Method: azimuths are folded to [0,180) as LINES (a conjugate pair in map view is a
    set of line orientations — digitising direction is meaningless), then the best
    two-arc partition of the circle is found by maximising the WORST cluster's
    resultant length. A pair is reported only when both clusters have >=
    ``min_cluster_n`` members, both have r >= ``min_r``, and the acute angle between
    the two cluster means lies inside [``min_dihedral_deg``, ``max_dihedral_deg``].

    ``evidence`` is a plain-language receipt: n, cluster sizes, r values, the two mean
    orientations and the dihedral — enough for an auditor to reproduce or reject the
    observation. It is not a confidence.
    """
    arr = np.asarray(azimuths, dtype=float).ravel()
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    theta = _fold_array(arr, 180.0)

    if n < int(min_n):
        return {
            "pair_detected": False,
            "bisector_acute_deg": None,
            "dihedral_acute_deg": None,
            "evidence": (
                f"n = {n} finite azimuths < min_n = {int(min_n)}: a two-population test "
                "needs a minimum sample; not tested (this is NOT evidence of absence)."
            ),
        }

    split = _best_two_cluster_split(theta, min_cluster_n=int(min_cluster_n))
    if split is None:
        return {
            "pair_detected": False,
            "bisector_acute_deg": None,
            "dihedral_acute_deg": None,
            "evidence": (
                f"n = {n}: no two-arc partition with >= {int(min_cluster_n)} members per "
                "cluster exists — the population is unimodal or too sparse; no conjugate "
                "pair observed."
            ),
        }

    sizes, r_a, r_b, mean_a, mean_b = split
    dihedral = acute_angle_between_deg(mean_a, mean_b)
    bisector, _ = circular_mean_deg(np.array([mean_a, mean_b]), axial=True)

    detected = (
        r_a >= float(min_r)
        and r_b >= float(min_r)
        and float(min_dihedral_deg) <= dihedral <= float(max_dihedral_deg)
    )
    if not detected:
        why = []
        if r_a < float(min_r) or r_b < float(min_r):
            why.append(
                f"cluster r values ({r_a:.3f}, {r_b:.3f}) are below min_r = {float(min_r):.2f} "
                "— the groups are not coherent enough to call a conjugate pair"
            )
        if not (float(min_dihedral_deg) <= dihedral <= float(max_dihedral_deg)):
            why.append(
                f"acute dihedral {dihedral:.2f} deg is outside "
                f"[{float(min_dihedral_deg):.1f}, {float(max_dihedral_deg):.1f}] deg"
            )
        return {
            "pair_detected": False,
            "bisector_acute_deg": None,
            "dihedral_acute_deg": None,
            "evidence": (
                f"n = {n}; best two-arc partition sizes = {sizes}, means = "
                f"({mean_a:.2f}, {mean_b:.2f}) deg. Rejected: " + "; ".join(why) + "."
            ),
        }

    return {
        "pair_detected": True,
        "bisector_acute_deg": float(bisector),
        "dihedral_acute_deg": float(dihedral),
        "evidence": (
            f"n = {n} line orientations folded to [0,180); two coherent clusters: "
            f"sizes = {sizes}, r = ({r_a:.3f}, {r_b:.3f}), mean orientations = "
            f"({mean_a:.2f}, {mean_b:.2f}) deg; acute dihedral = {dihedral:.2f} deg; "
            f"acute bisector = {bisector:.2f} deg. OBSERVATION ONLY — this is a "
            "geometric angular relation. No stress axis, no SHmax, no slip sense is "
            "emitted: stress inference requires fault-slip inversion and belongs to "
            "arifOS (K-REGIME-CEILING)."
        ),
    }
