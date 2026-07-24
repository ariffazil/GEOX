"""
🌊 GEOX Classical Image Baseline (PR-A2)

Pure-numpy/scipy implementation. No ML. Provides:

  - structure_tensor(image)        Local dip/azimuth field
  - semblance_coherence(image, w)   Coherence / discontinuity map
  - ridge_extraction(coherence)     Ridge / skeleton candidate horizons
  - dp_horizon_tracker(seed, attr)  Dynamic-programming horizon tracker
  - rgt_estimation(image)           Relative Geological Time field (proxy)

Complements `classical_section_propose.py` with explicit numerical primitives
that gates may consume directly.

Doctrine:
  - Model proposes, gates challenge.
  - Output is CANDIDATE_GEOMETRY, not a final geological verdict.
  - Image-only input → INT_SEISMIC; never OBS_GEOLOGY.

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

import numpy as np


def artifact_sha256(array: np.ndarray) -> str:
    """Stable SHA-256 over raw float32 bytes."""
    raw = np.ascontiguousarray(array, dtype=np.float32).tobytes()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def structure_tensor(image: np.ndarray, sigma: float = 1.0) -> dict[str, np.ndarray]:
    """Compute 2D structure tensor + dip/azimuth/coherence."""
    if image.ndim != 2:
        raise ValueError(f"expected 2D image, got {image.shape}")

    from scipy.ndimage import gaussian_filter, sobel

    img = gaussian_filter(image.astype(np.float32), sigma=sigma)
    Ix = sobel(img, axis=1)
    Iz = sobel(img, axis=0)

    Ixx = gaussian_filter(Ix * Ix, sigma=sigma)
    Ixz = gaussian_filter(Ix * Iz, sigma=sigma)
    Izz = gaussian_filter(Iz * Iz, sigma=sigma)

    trace = Ixx + Izz
    det = Ixx * Izz - Ixz * Ixz
    disc = np.maximum(trace * trace / 4.0 - det, 0.0)
    sqrt_disc = np.sqrt(disc)
    eig1 = trace / 2.0 + sqrt_disc
    eig2 = trace / 2.0 - sqrt_disc

    dip_rad = np.where(np.abs(Izz) > 1e-9, np.arctan2(Ixz, Izz), 0.0)
    azimuth_rad = np.where(np.abs(Ixx) > 1e-9, np.arctan2(Ixz, Ixx), 0.0)
    coherence = np.where((eig1 + eig2) > 1e-9, (eig1 - eig2) / (eig1 + eig2), 0.0)

    return {
        "dip_rad": dip_rad,
        "azimuth_rad": azimuth_rad,
        "coherence": coherence,
        "eigval_max": eig1,
        "eigval_min": eig2,
    }


def semblance_coherence(image: np.ndarray, window: int = 5) -> np.ndarray:
    """Semblance-like coherence ∈ [0, 1] over a vertical window."""
    if image.ndim != 2:
        raise ValueError(f"expected 2D image, got {image.shape}")
    if window < 3 or window % 2 == 0:
        window = max(3, window | 1)

    from scipy.ndimage import uniform_filter

    img = image.astype(np.float32)
    num = uniform_filter(img, size=(window, 1)) ** 2
    den = uniform_filter(img**2, size=(window, 1))
    coherence = np.where(den > 1e-9, num / den, 0.0)
    return np.clip(coherence, 0.0, 1.0)


def ridge_extraction(
    image: np.ndarray,
    sigma: float = 1.0,
    threshold: float = 0.5,
) -> list[dict[str, Any]]:
    """Extract ridge polylines from smoothed amplitude peaks."""
    if image.ndim != 2:
        raise ValueError(f"expected 2D image, got {image.shape}")

    from scipy.ndimage import gaussian_filter

    smoothed = gaussian_filter(image.astype(np.float32), sigma=sigma)
    abs_img = np.abs(smoothed)
    mx = abs_img.max() if abs_img.size else 0.0
    if mx <= 0:
        return []
    norm = abs_img / mx

    ridges: list[dict[str, Any]] = []
    n_samples, n_traces = norm.shape
    for x in range(n_traces):
        col = norm[:, x]
        above = col >= threshold
        for z in range(1, n_samples - 1):
            if above[z] and col[z] >= col[z - 1] and col[z] >= col[z + 1]:
                ridges.append(
                    {
                        "ridge_id": f"R-{len(ridges):04d}",
                        "points": [[float(x), float(z)]],
                        "amplitude_mean": float(col[z]),
                    }
                )
    return _merge_ridge_points(ridges, distance_thresh=3.0)


def _merge_ridge_points(ridges: list[dict[str, Any]], distance_thresh: float = 3.0) -> list[dict[str, Any]]:
    if not ridges:
        return []
    used = [False] * len(ridges)
    out: list[dict[str, Any]] = []
    for i, r in enumerate(ridges):
        if used[i]:
            continue
        chain = list(r["points"])
        amps = [r["amplitude_mean"]]
        used[i] = True
        last_x = chain[-1][0]
        last_y = chain[-1][1]
        for j in range(i + 1, len(ridges)):
            if used[j]:
                continue
            p = ridges[j]["points"][0]
            dx = p[0] - last_x
            dy = p[1] - last_y
            if 0 <= dx <= distance_thresh * 2 and abs(dy) <= distance_thresh * 3:
                chain.append(p)
                amps.append(ridges[j]["amplitude_mean"])
                used[j] = True
                last_x = p[0]
                last_y = p[1]
        out.append(
            {
                "ridge_id": f"R-{len(out):04d}",
                "points": chain,
                "amplitude_mean": float(np.mean(amps)) if amps else 0.0,
            }
        )
    return out


def dp_horizon_tracker(
    seed_points: list[tuple[int, int]],
    image: np.ndarray,
    dip_penalty: float = 0.5,
    amplitude_weight: float = 1.0,
) -> dict[str, Any]:
    """DP horizon tracker (Bienati/Casulli/Lutz family)."""
    if image.ndim != 2:
        raise ValueError(f"expected 2D image, got {image.shape}")
    if not seed_points:
        return {"horizon_id": "H-0000", "points": [], "n_traces_walked": 0, "gap_traces": []}

    n_samples, n_traces = image.shape
    points: list[tuple[float, float]] = []
    gaps: list[int] = []
    seeds = sorted(seed_points, key=lambda p: p[0])
    current_x, current_y = seeds[0]
    points.append((float(current_x), float(current_y)))

    for target_x in range(current_x + 1, n_traces):
        y_min = max(0, current_y - int(dip_penalty * 3))
        y_max = min(n_samples - 1, current_y + int(dip_penalty * 3))
        best_y = current_y
        best_cost = float("inf")
        for y in range(y_min, y_max + 1):
            dip_cost = abs(y - current_y) * dip_penalty
            amp = abs(float(image[y, target_x]))
            amp_cost = -amplitude_weight * amp
            cost = dip_cost + amp_cost
            if cost < best_cost:
                best_cost = cost
                best_y = y
        if best_y == current_y and abs(best_cost) == float("inf"):
            gaps.append(target_x)
            continue
        points.append((float(target_x), float(best_y)))
        current_y = best_y

    return {
        "horizon_id": "H-0000",
        "points": points,
        "n_traces_walked": len(points),
        "gap_traces": gaps,
    }


def rgt_estimation(image: np.ndarray, sigma: float = 2.0) -> dict[str, np.ndarray]:
    """Estimate a Relative Geological Time field from image + dip."""
    if image.ndim != 2:
        raise ValueError(f"expected 2D image, got {image.shape}")

    tens = structure_tensor(image, sigma=sigma)
    dip = tens["dip_rad"]
    coh = tens["coherence"]
    n_samples, n_traces = dip.shape
    rgt = np.zeros_like(dip)
    rgt[:, 0] = 0.0
    for x in range(1, n_traces):
        path_step = np.where(
            np.abs(dip[:, x]) < math.pi / 2 - 0.01,
            1.0 / np.maximum(np.cos(dip[:, x]), 1e-3),
            1.0,
        )
        rgt[:, x] = rgt[:, x - 1] + path_step
    return {"rgt": rgt, "dip_rad": dip, "coherence": coh}


def horizons_from_rgt(
    rgt_field: np.ndarray,
    n_levels: int = 5,
    smoothness: float = 1.0,
) -> list[dict[str, Any]]:
    """Extract iso-RGT contours as horizon candidates."""
    if rgt_field.ndim != 2:
        raise ValueError(f"expected 2D RGT, got {rgt_field.shape}")

    from scipy.ndimage import gaussian_filter

    smoothed = gaussian_filter(rgt_field, sigma=smoothness)
    rgt_min = float(smoothed.min())
    rgt_max = float(smoothed.max())
    if rgt_max <= rgt_min:
        return []
    levels = np.linspace(
        rgt_min + 0.05 * (rgt_max - rgt_min),
        rgt_max - 0.05 * (rgt_max - rgt_min),
        n_levels,
    )
    n_samples, n_traces = smoothed.shape
    out: list[dict[str, Any]] = []
    for k, level in enumerate(levels):
        points: list[tuple[float, float]] = []
        for x in range(n_traces):
            col = smoothed[:, x]
            for z in range(1, n_samples):
                if (col[z - 1] - level) * (col[z] - level) <= 0:
                    if col[z] == col[z - 1]:
                        z_at = float(z)
                    else:
                        frac = (level - col[z - 1]) / (col[z] - col[z - 1])
                        z_at = float(z - 1) + frac
                    points.append((float(x), z_at))
                    break
        if points:
            out.append(
                {
                    "horizon_id": f"H-{k:04d}",
                    "rgt_level": float(level),
                    "points": points,
                    "tracker_method": "rgt",
                    "confidence_by_point": [1.0] * len(points),
                }
            )
    return out


def classical_baseline(
    image: np.ndarray,
    *,
    sigma: float = 1.0,
    n_horizon_levels: int = 5,
    dip_penalty: float = 0.5,
    coherence_threshold: float = 0.3,
) -> dict[str, Any]:
    """Run the full classical baseline (PR-A2 entry point).

    Returns candidate geometry only — never a final verdict.
    """
    n_samples, n_traces = image.shape
    tens = structure_tensor(image, sigma=sigma)
    coh = semblance_coherence(image, window=5)
    rgt_out = rgt_estimation(image, sigma=sigma)

    candidate_horizons = horizons_from_rgt(rgt_out["rgt"], n_levels=n_horizon_levels)
    candidate_horizons.extend(ridge_extraction(image, sigma=sigma))

    fault_mask = (coh < coherence_threshold).astype(np.float32)
    candidate_faults: list[dict[str, Any]] = []
    for x in range(n_traces):
        col = fault_mask[:, x]
        for z in range(1, n_samples - 1):
            if col[z] > 0 and col[z - 1] > 0 and col[z + 1] > 0:
                candidate_faults.append(
                    {
                        "fault_id": f"F-cand-{len(candidate_faults):04d}",
                        "points": [[float(x), float(z)]],
                        "confidence_by_segment": [float(1.0 - coh[z, x])],
                    }
                )

    return {
        "tool": "geox_classical_baseline",
        "artifact_sha256": artifact_sha256(image),
        "shape": [int(n_samples), int(n_traces)],
        "structure_tensor_dip_rad": tens["dip_rad"],
        "azimuth_rad": tens["azimuth_rad"],
        "coherence_map": coh,
        "rgt_field": rgt_out["rgt"],
        "candidate_horizons": candidate_horizons,
        "candidate_faults": candidate_faults,
        "epistemic_label": "INT_SEISMIC",
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "note": (
            "Classical candidate geometry. Never a final geological verdict. "
            "Run structure_validate on this output before sealing."
        ),
    }


__all__ = [
    "artifact_sha256",
    "classical_baseline",
    "dp_horizon_tracker",
    "horizons_from_rgt",
    "ridge_extraction",
    "rgt_estimation",
    "semblance_coherence",
    "structure_tensor",
]
