"""
GEOX Well Stratigraphy — L2: Geological Package Builder
═══════════════════════════════════════════════════════════════

Aggregates 10 m GR bins into geological packages based on motif stacking.
Each package represents a consistent depositional phase.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from typing import Any


def build_packages(
    gr_bins: list[dict[str, Any]],
    min_package_thickness_m: float = 20.0,
    p50_shift_api: float = 15.0,
) -> list[dict[str, Any]]:
    """
    L2 Package Builder: Aggregate 10 m GR bins into geological packages.

    A package is a contiguous set of bins where the dominant motif and
    GR signature remain coherent. Package boundaries are placed where:
      - Motif changes (e.g., BELL -> FUNNEL)
      - P50 shift exceeds threshold
      - Gap in data exceeds min package thickness

    Parameters
    ----------
    gr_bins : list[dict]
        10 m GR bins from compute_gr_bins().
    min_package_thickness_m : float, default 20.0
        Minimum thickness for a valid package.
    p50_shift_api : float, default 15.0
        P50 shift threshold for detecting package boundaries.

    Returns
    -------
    list[dict]
        Each dict: top, base, thickness, dominant_motif, p50_mean,
        stacking_pattern, package_type.
    """
    if not gr_bins:
        return []

    packages: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []

    for bin_ in gr_bins:
        if bin_.get("motif") == "INSUFFICIENT_DATA" or bin_.get("p50") is None:
            # Flush current package on data gap
            if current:
                packages.append(_finalize_package(current))
                current = []
            continue

        if not current:
            current = [bin_]
            continue

        prev = current[-1]
        p50_shift = abs((bin_["p50"] or 0) - (prev.get("p50") or 0))
        motif_change = bin_["motif"] != prev["motif"]

        if motif_change or p50_shift > p50_shift_api:
            if current:
                packages.append(_finalize_package(current))
            current = [bin_]
        else:
            current.append(bin_)

    if current:
        packages.append(_finalize_package(current))

    # Filter by minimum thickness
    packages = [p for p in packages if p["thickness"] >= min_package_thickness_m]

    # Classify stacking pattern
    for i, pkg in enumerate(packages):
        pkg["stacking_pattern"] = _classify_stacking(pkg, packages, i)

    return packages


def _finalize_package(bins: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate package properties from constituent bins."""
    top = bins[0]["depth_top"]
    base = bins[-1]["depth_base"]
    thickness = base - top

    motifs = [b["motif"] for b in bins if b.get("motif")]
    from collections import Counter
    dominant = Counter(motifs).most_common(1)[0][0] if motifs else "UNKNOWN"

    p50_vals = [b["p50"] for b in bins if b.get("p50") is not None]
    p50_mean = sum(p50_vals) / len(p50_vals) if p50_vals else None

    return {
        "top": round(top, 2),
        "base": round(base, 2),
        "thickness": round(thickness, 2),
        "n_bins": len(bins),
        "dominant_motif": dominant,
        "p50_mean": round(p50_mean, 1) if p50_mean is not None else None,
        "motif_sequence": motifs,
        "claim_state": "DERIVED_CANDIDATE",
    }


def _classify_stacking(
    pkg: dict[str, Any],
    all_pkgs: list[dict[str, Any]],
    idx: int,
) -> str:
    """Classify vertical stacking pattern from motif sequence."""
    seq = pkg.get("motif_sequence", [])

    # Count motif types
    bell_count = sum(1 for m in seq if m == "BELL")
    funnel_count = sum(1 for m in seq if m == "FUNNEL")
    blocky_count = sum(1 for m in seq if m == "BLOCKY")
    serrated_count = sum(1 for m in seq if m == "SERRATED")
    total = len(seq) if seq else 1

    if funnel_count / total > 0.5:
        return "COARSENING_UPWARD"
    elif bell_count / total > 0.5:
        return "FINING_UPWARD"
    elif blocky_count / total > 0.5:
        return "AMALGAMATED"
    elif serrated_count / total > 0.5:
        return "HETEROLITHIC"
    else:
        return "MIXED"
