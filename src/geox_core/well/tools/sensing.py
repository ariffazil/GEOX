"""
GEOX Well Stratigraphy — L1: 10 m GR Sensing
═══════════════════════════════════════════════════════════════

Computes 10 m equal-interval GR bins for L1 sensing.
Returns bin statistics (P10, P50, P90, mean, motif) per interval.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from typing import Any

import numpy as np


def compute_gr_bins(
    depth: np.ndarray,
    gr: np.ndarray,
    zone_top: float,
    zone_base: float,
    bin_size_m: float = 10.0,
) -> list[dict[str, Any]]:
    """
    L1 Sensing: Compute 10 m GR statistics bins over a depth interval.

    Each bin reports: depth_mid, p10, p50, p90, mean, std, motif.

    Parameters
    ----------
    depth : np.ndarray
        Depth array (same length as gr), in metres.
    gr : np.ndarray
        Gamma ray values (API units).
    zone_top : float
        Top of zone in metres.
    zone_base : float
        Base of zone in metres.
    bin_size_m : float, default 10.0
        Bin size in metres.

    Returns
    -------
    list[dict]
        Each dict: depth_top, depth_base, depth_mid, p10, p50, p90,
        mean, std, n_samples, motif, confidence.
    """
    from geox_mcp.tools.kernel._petrophysics import _classify_gr_motif

    # Restrict to zone
    mask = (depth >= zone_top) & (depth <= zone_base)
    d_zone = depth[mask]
    gr_zone = gr[mask]

    if len(d_zone) < 3:
        return []

    bins: list[dict[str, Any]] = []
    bin_top = zone_top

    while bin_top < zone_base:
        bin_base = min(bin_top + bin_size_m, zone_base)
        bm = (d_zone >= bin_top) & (d_zone < bin_base)
        gr_bin = gr_zone[bm]

        if len(gr_bin) >= 3:
            p10 = float(np.percentile(gr_bin, 10))
            p50 = float(np.percentile(gr_bin, 50))
            p90 = float(np.percentile(gr_bin, 90))
            mean = float(np.nanmean(gr_bin))
            std = float(np.nanstd(gr_bin))

            motif_result = _classify_gr_motif(gr_bin, d_zone[bm])
            motif = motif_result.get("motif", "INSUFFICIENT_DATA")
            confidence = motif_result.get("confidence", 0.0)

            bins.append(
                {
                    "depth_top": round(bin_top, 2),
                    "depth_base": round(bin_base, 2),
                    "depth_mid": round((bin_top + bin_base) / 2, 2),
                    "p10": round(p10, 1),
                    "p50": round(p50, 1),
                    "p90": round(p90, 1),
                    "mean": round(mean, 1),
                    "std": round(std, 1),
                    "n_samples": int(len(gr_bin)),
                    "motif": motif,
                    "confidence": round(confidence, 2),
                    "claim_state": "DERIVED_CANDIDATE",
                }
            )
        else:
            bins.append(
                {
                    "depth_top": round(bin_top, 2),
                    "depth_base": round(bin_base, 2),
                    "depth_mid": round((bin_top + bin_base) / 2, 2),
                    "p10": None,
                    "p50": None,
                    "p90": None,
                    "mean": None,
                    "std": None,
                    "n_samples": int(len(gr_bin)),
                    "motif": "INSUFFICIENT_DATA",
                    "confidence": 0.0,
                    "claim_state": "INSUFFICIENT_DATA",
                }
            )

        bin_top = bin_base

    return bins
