"""
GEOX Well Stratigraphy — L2: Generalized Geological Package Builder
═══════════════════════════════════════════════════════════════════════════════

Merges 10 m sensing bins into geological packages (bottom-up traversal).
Package boundaries detected by:
  1. P50 baseline shift
  2. Motif inversion (FU <-> CU)
  3. Maximum package thickness

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from .config import HUMAN_LABELS, MOTIF_COLORS


def build_packages(
    bins_10m: list[dict[str, Any]],
    min_pkg_m: float = 20.0,
    shift_thresh_gapi: float = 15.0,
    max_pkg_m: float = 400.0,
) -> list[dict[str, Any]]:
    """
    Merge 10 m bins into geological packages (bottom-up, compatibility rules).

    Parameters
    ----------
    bins_10m : list[dict]
        10 m sensing bins from sense_bins().
    min_pkg_m : float, default 20.0
        Minimum package thickness in metres.
    shift_thresh_gapi : float, default 15.0
        P50 shift threshold for detecting package boundaries (GAPI).
    max_pkg_m : float, default 400.0
        Maximum package thickness before forced split.

    Returns
    -------
    list[dict] with keys: TOP, BASE, THICKNESS, HUMAN_MOTIF, RIDER_MOTIF,
        NET_TREND, VARIABILITY, GR_BASELINE_SHIFT, GR_MEAN, GR_P10, GR_P50,
        GR_P90, N_BINS.
    """
    if not bins_10m:
        return []

    # Sort deepest first (bottom-up traversal)
    bu = sorted(bins_10m, key=lambda x: -x["TOP"])
    current = [bu[0]]
    groups = []

    for b in bu[1:]:
        last = current[-1]
        p50_break = (
            b["P50"] is not None and last["P50"] is not None
            and abs(b["P50"] - last["P50"]) > shift_thresh_gapi
        )
        mot_inversion = (
            {b["MICRO_MOTIF"], last["MICRO_MOTIF"]}
            == {"Fining Upward", "Coarsening Upward"}
        )
        thickness_now = abs(current[0]["TOP"] - current[-1]["BASE"])
        if p50_break or mot_inversion or thickness_now >= max_pkg_m:
            groups.append(current)
            current = [b]
        else:
            current.append(b)
    groups.append(current)

    # Finalize each group
    result = []
    for g in groups:
        g_sorted = sorted(g, key=lambda x: x["TOP"])
        pkg = _finalize_package(g_sorted)

        if pkg["THICKNESS"] < min_pkg_m and result:
            prev = result.pop()
            merged_bins = sorted(
                g_sorted + prev.get("_bins", []),
                key=lambda x: x["TOP"],
            )
            merged = _finalize_package(merged_bins)
            merged["_bins"] = merged_bins
            result.append(merged)
        else:
            pkg["_bins"] = g_sorted
            result.append(pkg)

    return result


def _finalize_package(bins: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute package summary from list of 10 m bins (sorted shallow-first)."""
    tops = [x["TOP"] for x in bins]
    bases = [x["BASE"] for x in bins]
    means = [x["MEAN"] for x in bins if x["MEAN"] is not None]
    p10s = [x["P10"] for x in bins if x["P10"] is not None]
    p50s = [x["P50"] for x in bins if x["P50"] is not None]
    p90s = [x["P90"] for x in bins if x["P90"] is not None]
    rngs = [x["RANGE"] for x in bins if x["RANGE"] is not None]
    slps = [x["SLOPE"] for x in bins if x["SLOPE"] is not None]
    micros = [x["MICRO_MOTIF"] for x in bins
              if x["MICRO_MOTIF"] not in ("Heterolithic", None)]
    import numpy as np

    gr_mean = round(float(np.mean(means)), 2) if means else None
    gr_p10 = (
        round(float(np.percentile(p10s, 10)), 2) if len(p10s) >= 2
        else (round(p10s[0], 2) if p10s else None)
    )
    gr_p50 = round(float(np.median(p50s)), 2) if p50s else None
    gr_p90 = (
        round(float(np.percentile(p90s, 90)), 2) if len(p90s) >= 2
        else (round(p90s[0], 2) if p90s else None)
    )
    net_slope = float(np.mean(slps)) if slps else 0.0
    rng_mean = float(np.mean(rngs)) if rngs else 0.0

    # Determine motif
    if not means:
        human_motif = "Heterolithic"
        rider_motif = "Serrated"
    elif net_slope < -0.18 and abs(net_slope) > 0.18:
        human_motif = "Fining Upward"
        rider_motif = "Bell"
    elif net_slope > 0.18:
        human_motif = "Coarsening Upward"
        rider_motif = "Funnel"
    elif rng_mean < 18:
        human_motif = "Blocky"
        rider_motif = "Cylindrical"
    else:
        if micros:
            dom = Counter(micros).most_common(1)[0][0]
            human_motif = dom
            rider_motif = {v: k for k, v in HUMAN_LABELS.items()}.get(dom, "Serrated")
        else:
            human_motif = "Serrated / Irregular Pattern"
            rider_motif = "Serrated"

    variability = "Low" if rng_mean < 15 else ("Moderate" if rng_mean < 35 else "High")

    baseline_shift = 0.0
    if len(p50s) >= 4:
        half = len(p50s) // 2
        baseline_shift = round(abs(np.mean(p50s[:half]) - np.mean(p50s[half:])), 1)

    return {
        "TOP": round(min(tops), 2),
        "BASE": round(max(bases), 2),
        "THICKNESS": round(max(bases) - min(tops), 1),
        "HUMAN_MOTIF": human_motif,
        "RIDER_MOTIF": rider_motif,
        "NET_TREND": ("Net Fining Upward" if human_motif == "Fining Upward"
                      else "Net Coarsening Upward" if human_motif == "Coarsening Upward"
                      else "Aggradational"),
        "VARIABILITY": variability,
        "GR_BASELINE_SHIFT": baseline_shift,
        "GR_MEAN": gr_mean,
        "GR_P10": gr_p10,
        "GR_P50": gr_p50,
        "GR_P90": gr_p90,
        "N_BINS": len(bins),
    }
