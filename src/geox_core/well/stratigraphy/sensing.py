"""
GEOX Well Stratigraphy — L1: Configurable GR Sensing
═══════════════════════════════════════════════════════════════════════════════

GR statistics per depth bin within defined intervals.
Configurable bin size, with motif classification.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
from scipy import stats as scipy_stats
from scipy.signal import savgol_filter


def sense_bins(
    depth: np.ndarray,
    gr: np.ndarray,
    zone_top: float,
    zone_base: float,
    bin_size_m: float = 10.0,
    gr_cut_api: float = 75.0,
) -> list[dict[str, Any]]:
    """
    L1 Sensing: Compute GR statistics per depth bin within a zone.

    Each bin returns: TOP, BASE, N, P10, P50, P90, MEAN, RANGE, SLOPE, MICRO_MOTIF.

    Motif is OBSERVATIONAL — never UNKNOWN. "Heterolithic" is the fallback
    when GR is absent or insufficient for trend determination.

    Parameters
    ----------
    depth : np.ndarray
        Depth array (metres).
    gr : np.ndarray
        GR array (API).
    zone_top : float
        Top of zone in metres.
    zone_base : float
        Base of zone in metres.
    bin_size_m : float, default 10.0
        Bin size in metres.
    gr_cut_api : float, default 75.0
        Cutoff for motif classification.

    Returns
    -------
    list[dict] with keys: TOP, BASE, N, P10, P50, P90, MEAN, RANGE, SLOPE, MICRO_MOTIF.
    """
    bins: list[dict[str, Any]] = []

    if gr is None or len(gr) == 0:
        start = np.floor(zone_top / bin_size_m) * bin_size_m
        d = start
        while d < zone_base:
            top_b = max(d, zone_top)
            base_b = min(d + bin_size_m, zone_base)
            bins.append({
                "TOP": round(top_b, 2), "BASE": round(base_b, 2), "N": 0,
                "P10": None, "P50": None, "P90": None, "MEAN": None,
                "RANGE": None, "SLOPE": None, "MICRO_MOTIF": "Heterolithic",
            })
            d += bin_size_m
        return bins

    mask = (depth >= zone_top) & (depth <= zone_base)
    d_zone = depth[mask]
    gr_zone = gr[mask]

    # Smooth GR with Savitzky-Golay filter to reduce high-frequency noise
    # before motif classification (Arif 2026-05-22)
    if len(gr_zone) >= 5:
        window = min(21, len(gr_zone) // 2 * 2 + 1)  # odd window, max 21
        window = max(5, window)
        try:
            gr_zone = savgol_filter(gr_zone, window_length=window, polyorder=2)
        except Exception:
            pass  # fallback to raw GR if filter fails

    if len(d_zone) < 2:
        start = np.floor(zone_top / bin_size_m) * bin_size_m
        d = start
        while d < zone_base:
            top_b = max(d, zone_top)
            base_b = min(d + bin_size_m, zone_base)
            bins.append({
                "TOP": round(top_b, 2), "BASE": round(base_b, 2), "N": 0,
                "P10": None, "P50": None, "P90": None, "MEAN": None,
                "RANGE": None, "SLOPE": None, "MICRO_MOTIF": "Heterolithic",
            })
            d += bin_size_m
        return bins

    start = np.floor(zone_top / bin_size_m) * bin_size_m
    d = start
    while d < zone_base:
        top_b = max(d, zone_top)
        base_b = min(d + bin_size_m, zone_base)
        mask_b = (d_zone >= top_b) & (d_zone < base_b)
        sub = gr_zone[mask_b]
        n = int(len(sub))

        if n >= 3:
            sc = np.clip(sub, 0, 200)
            p10 = float(np.percentile(sc, 10))
            p50 = float(np.percentile(sc, 50))
            p90 = float(np.percentile(sc, 90))
            mean = float(sc.mean())
            rng = p90 - p10
            slope = 0.0
            if n >= 5:
                try:
                    slope = float(scipy_stats.linregress(d_zone[mask_b], sc).slope)
                except Exception:
                    slope = 0.0
            micro = _classify_micro_motif(mean, rng, slope, gr_cut_api)
        elif n >= 1:
            sc = np.clip(sub, 0, 200)
            mean = float(sc.mean())
            p50 = mean
            if mean < 50:
                micro = "Blocky"
            elif mean < 90:
                micro = "Serrated / Irregular Pattern"
            else:
                micro = "Serrated / Irregular Pattern"
            p10 = mean
            p90 = mean
            rng = 0.0
            slope = 0.0
        else:
            micro = "Heterolithic"
            p10 = p50 = p90 = mean = rng = slope = None
            mean = None

        bins.append({
            "TOP": round(top_b, 2),
            "BASE": round(base_b, 2),
            "N": n,
            "P10": round(p10, 2) if p10 is not None else None,
            "P50": round(p50, 2) if p50 is not None else None,
            "P90": round(p90, 2) if p90 is not None else None,
            "MEAN": round(mean, 2) if mean is not None else None,
            "RANGE": round(rng, 2) if rng is not None else None,
            "SLOPE": round(slope, 4) if slope is not None else None,
            "MICRO_MOTIF": micro,
        })
        d += bin_size_m

    return bins


def _classify_micro_motif(
    mean: float,
    rng: float,
    slope: float,
    gr_cut: float = 75.0,
) -> str:
    """Classify micro-motif from bin statistics.

    Observational — NEVER returns UNKNOWN.
    Heterolithic is the fallback for ambiguous/no-data bins.
    """
    if mean > gr_cut + 15 and rng < 30:
        return "Serrated / Irregular Pattern"
    if slope < -0.25:
        return "Fining Upward"
    if slope > 0.25:
        return "Coarsening Upward"
    if rng < 18:
        return "Blocky"
    return "Serrated / Irregular Pattern"
