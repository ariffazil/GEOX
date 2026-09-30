"""Axis B — Differential: DTW trace alignment, isopach, expansion index, differential ratio.

DTW DOES NOT MEASURE THICKNESS
-----------------------------
This is the defect this module exists to prevent, and it is stated here, at the top, because
it is the single easiest number in a section to relay wrongly.

``dtw_align_traces`` returns the **relative warping** between two traces: how one trace's
samples must be stretched to line up with the other's. That warp is a *shape* statement. It
says nothing about metres. A trace with no reflector offset and a trace with a
thousand-metre-thick wedge can both give an identical warp profile. **Thickness requires
horizon picks on BOTH traces** — that is :func:`compute_isopach`, and it is a different
measurement from a different input.

Doctrine preserved here (CONTRACT §7)
------------------------------------
* Rule 6 — DTW gives warp, not thickness. See above.
* Rule 1 — ``EI <= 1`` is only a statement about the *interval / syn-tectonic timing claim*
  it was measured on. **Absence of a growth wedge does not kill extension**: a fault moving
  slower than the sedimentation rate leaves no growth signature at all. A missing EI is
  ``UNMEASURED`` — never 1.0, never 0.0, and never a kill.
* Rule 5 — decompaction. Raw isopach thickness is thickness in *depth*; "constant
  thickness" means constant in *time*. Every thickness Measurement here carries that
  caveat in its notes. This module does not decompact; it declares that it did not.
* Rule 10 — the null hypothesis is mandatory. :func:`isopach_differential` returns the
  ratio whose ~1.0 value *favours the null* (uniform deposition), and it says so.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .types import Measurement, measured, unmeasured

__all__ = [
    "DTW_WARP_ONLY_WARNING",
    "compute_isopach",
    "dtw_align_traces",
    "expansion_index",
    "isopach_differential",
    "trace_thickness_profile",
]

#: One-line receipt for anything that logs a DTW result. Print it next to the number.
DTW_WARP_ONLY_WARNING = (
    "DTW measures RELATIVE WARP/STRETCH between two traces, NOT thickness. Thickness requires "
    "horizon picks on both traces (compute_isopach)."
)

_NON_DECOMPACTED_NOTE = (
    "thickness is raw isopach (no decompaction applied) — compaction thins parallel beds with "
    "zero tectonics, and 'constant thickness' means constant in TIME, not in depth (CONTRACT §7 rule 5)"
)


# ── DTW (implemented in numpy: no `dtw` library is installed, and none is wanted) ───────
def dtw_align_traces(
    a: np.ndarray,
    b: np.ndarray,
    *,
    band: int | None = None,
) -> dict[str, Any]:
    """Dynamic time warping of two traces. Pure numpy, optional Sakoe-Chiba band.

    Parameters
    ----------
    a, b:
        1-D float arrays (one trace each, e.g. a seismic trace or a log curve).
    band:
        Sakoe-Chiba half-band: the admissible path satisfies ``|i - j| <= band``. ``None``
        means unconstrained. A band narrower than ``|len(a) - len(b)|`` cannot admit any
        path, so it is *raised* to that width and the raised value is returned in ``"band"``.

    Returns
    -------
    dict[str, Any]
        ``{"path": int ndarray (n,2) of (i, j) index pairs, monotone and starting at (0,0),
        "distance": float — the accumulated |a[i] - b[j]| along the optimal path,
        "warp_stretch_profile": float ndarray, one value per path node — the LOCAL STRETCH of
        b relative to a, i.e. how many b-samples are consumed per a-sample (1.0 = the two
        traces advance together; 2.0 = b runs twice as fast in a's index; ``inf`` where the
        path advances in j without advancing in i), "band": int — the effective half-band}.

    Raises
    ------
    ValueError
        On non-1-D, empty or non-finite input.

    Notes
    -----
    **DTW measures RELATIVE WARPING between two traces. It does NOT measure thickness.**
    Thickness needs horizon picks on both traces — see :func:`compute_isopach`. Do not
    conflate them: a stretch factor is not a stratigraphic thickness, and a zero warp does
    not mean "no growth wedge" (a wedge thickens without warping anything).

    Tie-breaking is deterministic and diagonal-first: when a diagonal, vertical and
    horizontal move cost the same, the diagonal is taken, so identical traces give the exact
    identity path rather than an arbitrary equal-cost detour.
    """
    A = np.asarray(a, dtype=float)
    B = np.asarray(b, dtype=float)
    if A.ndim != 1 or B.ndim != 1:
        raise ValueError(f"dtw_align_traces expects 1-D traces, got ndim={A.ndim} and {B.ndim}")
    if A.size == 0 or B.size == 0:
        raise ValueError("dtw_align_traces received an empty trace")
    if not np.all(np.isfinite(A)) or not np.all(np.isfinite(B)):
        raise ValueError(
            "traces contain non-finite values — a NaN cost silently wrecks the DP; fill or mask first"
        )

    n, m = int(A.size), int(B.size)
    if band is None:
        band_eff = max(n, m)
    else:
        band_eff = int(band)
        if band_eff < 0:
            raise ValueError(f"band must be >= 0 or None, got {band!r}")
        band_eff = max(band_eff, abs(n - m))

    big = math.inf
    cost = np.full((n, m), big, dtype=float)
    for i in range(n):
        j_lo = max(0, i - band_eff)
        j_hi = min(m - 1, i + band_eff)
        if j_lo > j_hi:
            continue
        ai = A[i]
        row = np.abs(ai - B[j_lo : j_hi + 1])
        for offset, j in enumerate(range(j_lo, j_hi + 1)):
            local = row[offset]
            if i == 0 and j == 0:
                cost[i, j] = local
                continue
            up = cost[i - 1, j] if i > 0 else big
            left = cost[i, j - 1] if j > 0 else big
            diag = cost[i - 1, j - 1] if (i > 0 and j > 0) else big
            if not np.isfinite(up) and not np.isfinite(left) and not np.isfinite(diag):
                cost[i, j] = big
                continue
            # np.argmin returns the first minimum => diagonal wins ties (deterministic).
            best = np.argmin(np.array([diag, up, left], dtype=float))
            cost[i, j] = local + (diag if best == 0 else up if best == 1 else left)

    if not np.isfinite(cost[n - 1, m - 1]):
        raise ValueError(
            f"no admissible DTW path exists within band={band_eff} for traces of length {n} and {m}"
        )

    # Backtrack.
    path: list[tuple[int, int]] = [(n - 1, m - 1)]
    i, j = n - 1, m - 1
    while i > 0 or j > 0:
        diag = cost[i - 1, j - 1] if (i > 0 and j > 0) else big
        up = cost[i - 1, j] if i > 0 else big
        left = cost[i, j - 1] if j > 0 else big
        best = int(np.argmin(np.array([diag, up, left], dtype=float)))
        if best == 0:
            i, j = i - 1, j - 1
        elif best == 1:
            i -= 1
        else:
            j -= 1
        path.append((i, j))
    path.reverse()
    path_arr = np.asarray(path, dtype=int)

    # Local stretch profile: dj/di along the path, centred windows of +-1 node.
    stretch = np.empty(path_arr.shape[0], dtype=float)
    idx_i = path_arr[:, 0]
    idx_j = path_arr[:, 1]
    for k in range(path_arr.shape[0]):
        lo = max(0, k - 1)
        hi = min(path_arr.shape[0] - 1, k + 1)
        di = int(idx_i[hi] - idx_i[lo])
        dj = int(idx_j[hi] - idx_j[lo])
        stretch[k] = (dj / di) if di > 0 else math.inf

    return {
        "path": path_arr,
        "distance": float(cost[n - 1, m - 1]),
        "warp_stretch_profile": stretch,
        "band": int(band_eff),
    }


# ── isopach from two picked horizons ───────────────────────────────────────────────────
def _as_mask(mask: np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(mask)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be a 2-D boolean mask, got ndim={arr.ndim}")
    return arr.astype(bool)


def _require_dz(dz_m: float) -> float:
    dz = float(dz_m)
    if not math.isfinite(dz) or dz <= 0.0:
        raise ValueError(f"dz_m must be finite and > 0, got {dz_m!r}")
    return dz


def trace_thickness_profile(
    top_mask: np.ndarray,
    bot_mask: np.ndarray,
    *,
    dz_m: float,
) -> np.ndarray:
    """Per-trace thickness in metres; ``NaN`` where a pick is absent. **No interpolation.**

    Non-contract helper (the contract's :func:`compute_isopach` returns only Measurements),
    but this is the array the reducers and the caller's isopach map need. ``NaN`` is a
    first-class value here: it means *not measured on this trace*, never zero.

    A trace where the picks cross (``bot`` at or above ``top``) is also ``NaN``: that is a
    polarity/pick-order defect, not a negative thickness.
    """
    top = _as_mask(top_mask, "top_mask")
    bot = _as_mask(bot_mask, "bot_mask")
    if top.shape != bot.shape:
        raise ValueError(f"top_mask {top.shape} and bot_mask {bot.shape} must have the same shape")
    dz = _require_dz(dz_m)
    n_traces = top.shape[1]
    out = np.full(n_traces, np.nan, dtype=float)
    for t in range(n_traces):
        rows_top = np.nonzero(top[:, t])[0]
        rows_bot = np.nonzero(bot[:, t])[0]
        if rows_top.size == 0 or rows_bot.size == 0:
            continue
        z_top = float(np.mean(rows_top)) * dz
        z_bot = float(np.mean(rows_bot)) * dz
        if z_bot <= z_top:
            continue
        out[t] = z_bot - z_top
    return out


def _mask_gap_report(top: np.ndarray, bot: np.ndarray) -> dict[str, Any]:
    """Count and locate traces where a pick is missing. Reported, never quietly filled."""
    n_traces = top.shape[1]
    top_any = top.any(axis=0)
    bot_any = bot.any(axis=0)
    missing_top = np.nonzero(~top_any)[0]
    missing_bot = np.nonzero(~bot_any)[0]
    either = np.nonzero(~(top_any & bot_any))[0]
    return {
        "n_traces": int(n_traces),
        "n_traces_missing_top": int(missing_top.size),
        "n_traces_missing_bottom": int(missing_bot.size),
        "n_traces_missing_either": int(either.size),
        "first_gap_trace_index": int(either[0]) if either.size else None,
        "last_gap_trace_index": int(either[-1]) if either.size else None,
    }


def compute_isopach(
    top_mask: np.ndarray,
    bot_mask: np.ndarray,
    *,
    dz_m: float,
) -> dict[str, Measurement]:
    """Per-trace thickness from two picked horizons. Keys: ``"thickness_m"``, ``"coverage"``.

    ``thickness_m`` is the mean of the per-trace thicknesses over the traces where **both**
    picks exist. Where either pick is absent the trace contributes nothing: it is counted,
    indexed and written into ``notes`` — **the gap is never interpolated over silently**.
    If no trace has both picks, ``thickness_m`` is ``UNMEASURED`` (value ``None``), because
    an absent thickness is not a thin one.

    ``coverage`` (unit ``ratio``) is the fraction of traces that carried both picks; it is
    reported as its own Measurement so it cannot be lost on the way to a downstream gate
    (CONTRACT §6 maps it to ``horizons[].coverage_pct`` / K-REGIME-COVERAGE).

    A trace whose picks cross (bottom at or above top) is treated as unmeasured and
    reported separately in ``uncertainty``: that is a pick-order/polarity defect, not a
    negative isopach.
    """
    top = _as_mask(top_mask, "top_mask")
    bot = _as_mask(bot_mask, "bot_mask")
    if top.shape != bot.shape:
        raise ValueError(f"top_mask {top.shape} and bot_mask {bot.shape} must have the same shape")
    dz = _require_dz(dz_m)

    profile = trace_thickness_profile(top, bot, dz_m=dz)
    gap = _mask_gap_report(top, bot)
    n_traces = int(top.shape[1])
    n_measured = int(np.isfinite(profile).sum())
    coverage = (n_measured / n_traces) if n_traces else 0.0

    crossed = 0
    for t in range(n_traces):
        rows_top = np.nonzero(top[:, t])[0]
        rows_bot = np.nonzero(bot[:, t])[0]
        if rows_top.size and rows_bot.size and float(np.mean(rows_bot)) <= float(np.mean(rows_top)):
            crossed += 1

    shared_unc: dict[str, Any] = {
        "dz_m": dz,
        "n_traces": n_traces,
        "n_traces_measured": n_measured,
        "n_traces_not_measured": n_traces - n_measured,
        "gap_report": gap,
        "pick_integration": "per-trace pick = mean of the True rows of that horizon mask in that trace",
        "interpolation": "NONE — masked gaps stay unmeasured and are counted",
        "decompaction_applied": False,
    }
    notes = [
        _NON_DECOMPACTED_NOTE,
        (
            f"masked gaps: {gap['n_traces_missing_either']} of {n_traces} traces have no top and/or "
            f"no bottom pick (missing top {gap['n_traces_missing_top']}, missing bottom "
            f"{gap['n_traces_missing_bottom']}"
            + (
                f", first at trace {gap['first_gap_trace_index']}, last at {gap['last_gap_trace_index']}"
                if gap["n_traces_missing_either"]
                else ""
            )
            + ") — excluded from the mean and counted, never interpolated"
        ),
    ]
    if crossed:
        notes.append(
            f"{crossed} trace(s) have the bottom pick at or above the top pick — treated as "
            "UNMEASURED (pick-order/polarity defect), not as zero or negative thickness"
        )

    method = (
        "B/isopach: per-trace horizon pick (mean of mask rows) -> "
        "thickness = (row_bot - row_top) * dz_m; mean over traces with both picks"
    )
    out: dict[str, Measurement] = {}
    if n_measured == 0:
        out["thickness_m"] = unmeasured(
            "m",
            method=method,
            reason=(
                "no trace carries picks on BOTH horizons — thickness is unmeasurable here; this is "
                "not a thin interval and not a zero"
            ),
            uncertainty={**shared_unc, "crossed_picks": crossed},
            notes=notes,
        )
    else:
        thick = profile[np.isfinite(profile)]
        out["thickness_m"] = Measurement(
            value=float(np.mean(thick)),
            unit="m",
            status="MEASURED" if coverage >= 1.0 else "PARTIAL",
            n_samples=n_measured,
            coverage=float(coverage),
            method=method,
            uncertainty={
                **shared_unc,
                "crossed_picks": crossed,
                "mean_m": float(np.mean(thick)),
                "median_m": float(np.median(thick)),
                "min_m": float(np.min(thick)),
                "max_m": float(np.max(thick)),
                "std_m": float(np.std(thick)) if thick.size > 1 else 0.0,
                "range_p95_p5_m": float(np.percentile(thick, 95) - np.percentile(thick, 5))
                if thick.size > 1
                else 0.0,
            },
            notes=notes
            + (
                [
                    f"PARTIAL: only {n_measured}/{n_traces} traces carry both picks "
                    f"(coverage {coverage:.3f})",
                ]
                if coverage < 1.0
                else []
            ),
        )
    out["coverage"] = Measurement(
        value=float(coverage),
        unit="ratio",
        status="MEASURED",
        n_samples=n_traces,
        coverage=float(coverage),
        method=method + "; coverage = traces with both picks / total traces",
        uncertainty={"gap_report": gap},
        notes=["coverage is reported as a first-class Measurement — it is mandatory alongside any "
               "number downstream (CONTRACT §5)"],
    )
    return out


# ── expansion index (growth wedge) ─────────────────────────────────────────────────────
def expansion_index(
    thickness_hangingwall: np.ndarray,
    thickness_footwall: np.ndarray,
) -> dict[str, Measurement]:
    """EI = hangingwall thickness / footwall thickness, per trace, then reduced.

    Keys: ``"expansion_index"`` (unit ``ratio``, median over pairs — median, because a single
    trace with an almost-zero footwall thickness would otherwise dominate a mean) and
    ``"n_pairs"`` (unit ``count``, how many trace pairs carried finite thickness on BOTH walls).

    If either side has no valid entries the expansion index is **UNMEASURED — not 1.0 and not
    0.0**. A missing wedge measurement is not the absence of a wedge, and the reducer refuses
    to guess: 1.0 would silently assert "no growth", 0.0 would assert "thinning", and both
    would be fabricated.

    **Absence of a growth wedge does not kill extension** (CONTRACT §7 rule 1). A fault moving
    slower than the sedimentation rate leaves *no* growth signature at all. When a value is
    returned, the notes also state what a value <= 1.0 does and does not falsify: it is scoped
    to the interval / syn-tectonic *timing* claim, never to extension itself.

    ``NaN`` entries (unmeasured traces, e.g. a masked gap from :func:`compute_isopach`) are
    skipped and counted; non-positive footwall thickness cannot form a ratio and is likewise
    skipped and reported.
    """
    hw = np.asarray(thickness_hangingwall, dtype=float).ravel()
    fw = np.asarray(thickness_footwall, dtype=float).ravel()
    if hw.size != fw.size:
        raise ValueError(
            f"hangingwall ({hw.size}) and footwall ({fw.size}) thickness arrays must have equal length"
        )

    finite_hw = np.isfinite(hw)
    finite_fw = np.isfinite(fw)
    positive_fw = finite_fw & (fw > 0.0)
    pair = finite_hw & positive_fw
    n_pairs = int(pair.sum())
    n_total = int(hw.size)

    dropped_nonfinite_hw = int((~finite_hw).sum())
    dropped_nonfinite_fw = int((~finite_fw).sum())
    dropped_nonpositive_fw = int((finite_fw & ~positive_fw).sum())

    coverage = (n_pairs / n_total) if n_total else 0.0
    method = (
        "B/expansion_index: EI_i = hw_i / fw_i on traces where BOTH are finite and fw > 0; "
        "reduced by median (mean and percentiles in uncertainty)"
    )
    shared_unc: dict[str, Any] = {
        "n_traces": n_total,
        "n_pairs_valid": n_pairs,
        "n_hangingwall_unmeasured": dropped_nonfinite_hw,
        "n_footwall_unmeasured": dropped_nonfinite_fw,
        "n_footwall_nonpositive": dropped_nonpositive_fw,
        "reduction": "median of per-trace EI",
        "decompaction_applied": False,
    }
    doctrine_notes = [
        _NON_DECOMPACTED_NOTE,
        "an unmeasured expansion index is UNMEASURED: it is not 1.0 (no growth) and not 0.0 "
        "(thinning) — those would be fabricated numbers",
        "CONTRACT §7 rule 1: absence of a growth wedge does NOT kill extension — a fault moving "
        "slower than the sedimentation rate leaves no growth signature at all",
    ]

    out: dict[str, Measurement] = {}
    if n_pairs == 0:
        out["expansion_index"] = unmeasured(
            "ratio",
            method=method,
            reason=(
                "no trace pair has finite thickness on BOTH walls "
                f"(hw unmeasured {dropped_nonfinite_hw}, fw unmeasured {dropped_nonfinite_fw}, "
                f"fw <= 0 {dropped_nonpositive_fw} of {n_total} traces) — the expansion index is "
                "not measured, so it cannot be offered as 1.0 or 0.0"
            ),
            uncertainty=shared_unc,
            notes=doctrine_notes,
        )
    else:
        ei = hw[pair] / fw[pair]
        median_ei = float(np.median(ei))
        notes = list(doctrine_notes)
        if median_ei <= 1.0:
            notes.append(
                f"median EI = {median_ei:.3f} <= 1: this falsifies the SYN-TECTONIC TIMING claim "
                "for THIS interval only (K-EXT-GROWTH, scoped) — it is not a kill of extension "
                "itself, and it is not a statement about any other interval"
            )
        else:
            notes.append(
                f"median EI = {median_ei:.3f} > 1: consistent with a growth wedge on this interval; "
                "it is a candidate, and it does not by itself distinguish tectonic from "
                "differential-compaction control"
            )
        out["expansion_index"] = Measurement(
            value=median_ei,
            unit="ratio",
            status="MEASURED" if coverage >= 1.0 else "PARTIAL",
            n_samples=n_pairs,
            coverage=float(coverage),
            method=method,
            uncertainty={
                **shared_unc,
                "median_ratio": median_ei,
                "mean_ratio": float(np.mean(ei)),
                "p25_ratio": float(np.percentile(ei, 25)),
                "p75_ratio": float(np.percentile(ei, 75)),
                "min_ratio": float(np.min(ei)),
                "max_ratio": float(np.max(ei)),
                "iqr_ratio": float(np.percentile(ei, 75) - np.percentile(ei, 25)),
            },
            notes=notes
            + (
                [
                    f"PARTIAL: {n_pairs}/{n_total} traces form a valid pair "
                    f"(coverage {coverage:.3f})",
                ]
                if coverage < 1.0
                else []
            ),
        )

    out["n_pairs"] = measured(
        float(n_pairs),
        "count",
        coverage=float(coverage),
        n_samples=n_total,
        method=method + "; n_pairs is the number of trace pairs that carried a valid ratio",
        uncertainty=shared_unc,
        notes=[
            "the count of valid pairs is itself measured — it is how much evidence the ratio "
            "rests on, and it is reported even when the ratio is UNMEASURED",
        ],
    )
    return out


# ── isopach differential: the tectonic test ────────────────────────────────────────────
def _robust_spread(values: np.ndarray) -> float | None:
    v = values[np.isfinite(values)]
    if v.size < 2:
        return None
    return float(np.percentile(v, 90) - np.percentile(v, 10))


def isopach_differential(
    thickness_map: np.ndarray,
    *,
    structure_axis: int = 1,
) -> dict[str, Measurement]:
    """Does the SAME interval change thickness ACROSS the structure? Key: ``"differential_ratio"``.

    ``structure_axis`` is the axis of ``thickness_map`` that runs **along** the structure (parallel
    to its strike, e.g. the fault trace direction). The complementary axis runs **across** it.

    The ratio is built from robust spreads, aggregated by median over profiles:

    * ``S_along`` = median over across-structure positions of (p90 - p10) of the thickness along
      the structure;
    * ``S_across`` = median over along-structure positions of (p90 - p10) of the thickness across
      the structure;
    * ``differential_ratio = S_across / S_along``.

    **value ~ 1.0 => uniform => favours eustatic/supply control (the NULL depositional
    hypothesis)** (CONTRACT §7 rule 10: the null is mandatory, and this is its number). A large
    ratio (>~2) means the interval thickens across the structure while staying coherent along it,
    which is what a growth wedge looks like — a candidate, not a verdict.

    Returns UNMEASURED when there is not enough 2-D structure to separate the two directions,
    when fewer than two valid values exist per profile, or when ``S_along`` is exactly zero
    while ``S_across`` is not (the ratio is unbounded: infinite differential). When **both**
    spreads are exactly zero the map is numerically uniform in every direction; the 0/0 case is
    returned as 1.0 **by an explicitly declared convention** that is written into the notes and
    ``uncertainty`` — it is a statement about a measured uniformity, not a fabricated number.

    ``NaN`` cells are unmeasured (masked gaps) and are skipped, never filled.
    """
    tmap = np.asarray(thickness_map, dtype=float)
    if tmap.ndim == 1:
        return {
            "differential_ratio": unmeasured(
                "ratio",
                method="B/isopach_differential: across-structure spread / along-structure spread",
                reason=(
                    "a 1-D thickness array cannot separate the across-structure direction from the "
                    "along-structure direction; supplying only one profile makes the ratio "
                    "undefined rather than 1"
                ),
                notes=["pass a 2-D isopach map and name the along-structure axis"],
            )
        }
    if tmap.ndim != 2:
        raise ValueError(f"thickness_map must be 2-D or 1-D, got ndim={tmap.ndim}")
    if int(structure_axis) not in (0, 1):
        raise ValueError(
            f"structure_axis must be 0 or 1 for a 2-D map, got {structure_axis!r}"
        )
    axis_along = int(structure_axis)
    axis_across = 1 - axis_along

    n_cells = int(tmap.size)
    n_valid_cells = int(np.isfinite(tmap).sum())
    coverage = (n_valid_cells / n_cells) if n_cells else 0.0

    s_along_profiles: list[float] = []
    for idx in range(tmap.shape[axis_across]):
        prof = tmap.take(idx, axis=axis_across)
        s = _robust_spread(prof)
        if s is not None:
            s_along_profiles.append(s)
    s_across_profiles: list[float] = []
    for idx in range(tmap.shape[axis_along]):
        prof = tmap.take(idx, axis=axis_along)
        s = _robust_spread(prof)
        if s is not None:
            s_across_profiles.append(s)

    method = (
        "B/isopach_differential: robust spread (p90 - p10) per profile, median-aggregated; "
        f"ratio = S_across / S_along with structure_axis={axis_along} (along) and "
        f"axis {axis_across} (across)"
    )
    shared_unc: dict[str, Any] = {
        "structure_axis": axis_along,
        "n_along_profiles": len(s_along_profiles),
        "n_across_profiles": len(s_across_profiles),
        "n_cells": n_cells,
        "n_valid_cells": n_valid_cells,
        "spread_definition": "p90 - p10 of the valid values in a profile (numpy linear interpolation)",
        "S_along_m": float(np.median(s_along_profiles)) if s_along_profiles else None,
        "S_across_m": float(np.median(s_across_profiles)) if s_across_profiles else None,
        "null_hypothesis": "ratio ~ 1.0 => uniform across the structure => favours "
        "depositional/eustatic/supply control (the NULL hypothesis)",
    }

    if not s_along_profiles or not s_across_profiles:
        return {
            "differential_ratio": unmeasured(
                "ratio",
                method=method,
                reason=(
                    "the map does not contain at least two profiles of at least two valid values in "
                    f"both directions (along {len(s_along_profiles)}, across {len(s_across_profiles)}) "
                    "— across- and along-structure variation cannot be separated"
                ),
                uncertainty=shared_unc,
                notes=["a differential needs a 2-D isopach map; one trace profile is not a map"],
            )
        }

    s_along = float(np.median(s_along_profiles))
    s_across = float(np.median(s_across_profiles))
    eps = 1e-12

    if s_along <= eps and s_across <= eps:
        return {
            "differential_ratio": measured(
                1.0,
                "ratio",
                coverage=coverage,
                n_samples=n_valid_cells,
                method=method,
                uncertainty={
                    **shared_unc,
                    "zero_division_convention": (
                        "S_along = S_across = 0 exactly: the map is numerically uniform in both "
                        "directions, so 0/0 is reported as 1.0 by an explicitly declared convention "
                        "— uniform is the limit the ratio describes"
                    ),
                },
                notes=[
                    "thickness is uniform in BOTH directions: 1.0 here is a declared 0/0 convention "
                    "for a numerically uniform map, not an interpolation of a missing value",
                    "uniform thickness favours the null depositional hypothesis — no growth wedge "
                    "signature is present in this interval (CONTRACT §7 rule 1: that does not by "
                    "itself kill extension)",
                    _NON_DECOMPACTED_NOTE,
                ],
            )
        }

    if s_along <= eps:
        return {
            "differential_ratio": unmeasured(
                "ratio",
                method=method,
                reason=(
                    f"S_along is zero while S_across = {s_across:g} m: the ratio is unbounded "
                    "(division by zero). The map is uniform along the structure and differential "
                    "across it, which the ratio cannot express as a finite number"
                ),
                uncertainty=shared_unc,
                notes=[
                    "UNMEASURED because the ratio has no finite value here — an 'infinity' or a "
                    "substituted large number would both be fabrications",
                    _NON_DECOMPACTED_NOTE,
                ],
            )
        }

    ratio = s_across / s_along
    notes = [
        f"S_across={s_across:g} m / S_along={s_along:g} m = {ratio:g} "
        "(robust spreads, medians over profiles)",
        _NON_DECOMPACTED_NOTE,
    ]
    if abs(ratio - 1.0) <= 0.25:
        notes.append(
            "ratio ~ 1.0: thickness changes no more across the structure than along it — this "
            "FAVOURS the null (depositional/eustatic/supply control) over a tectonic growth wedge"
        )
    elif ratio > 1.0:
        notes.append(
            "ratio > 1.0: thickness varies preferentially ACROSS the structure — a growth-wedge "
            "candidate for this interval (candidate only; the falsifier rules, not this function)"
        )
    else:
        notes.append(
            "ratio < 1.0: thickness varies preferentially ALONG the structure — that pattern is "
            "not a simple across-structure growth wedge"
        )

    return {
        "differential_ratio": measured(
            float(ratio),
            "ratio",
            coverage=coverage,
            n_samples=n_valid_cells,
            method=method,
            uncertainty={
                **shared_unc,
                "ratio": float(ratio),
                "along_spread_profile_spreads_m": [float(v) for v in s_along_profiles],
                "across_spread_profile_spreads_m": [float(v) for v in s_across_profiles],
                "ratio_iqr_of_profile_spreads": (
                    float(
                        np.percentile(s_across_profiles, 75) - np.percentile(s_across_profiles, 25)
                    )
                    if len(s_across_profiles) > 1
                    else 0.0
                ),
            },
            notes=notes,
        )
    }
