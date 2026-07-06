"""
GEOX RSI — Real Seismic Image Interpretation MCP Tools
=======================================================
Phase 3.0 (2026-07-06): Forged from SCAR_GEOX_RSI_001 failure analysis.

Tools:
  geox_rsi_interpret  — Horizon/fault picking from real seismic images
  geox_render_audit   — Render-vs-amplitude validation

Pipeline:
  R0: INPUT_REALITY_GATE → R1: PROVENANCE → R2: CROP_PANEL →
  R3: AGC → R4: ATTRIBUTE_STACK → R5: FAULT_DETECT →
  R6: HORIZON_TRACK → R7: EPISTEMIC_GOVERN → R8: RENDER_AUDIT

Hard Laws:
  OBS_IMAGE ≠ OBS_GEOLOGY — pixels are observed, geology is interpreted
  Every INT claim needs alternatives
  PETROPHYSICS = HOLD from image-only
  Full SHA256 provenance on every artifact
  No synthetic data in real interpretation mode

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.signal import find_peaks, hilbert


# ═══════════════════════════════════════════════════════════════════════════════
# R0: INPUT REALITY GATE
# ═══════════════════════════════════════════════════════════════════════════════
def _input_reality_gate(image_path: str) -> dict[str, Any]:
    """Verify image is real, decodable, pixels loaded. No interpretation yet."""
    gate: dict[str, Any] = {
        "image_path": image_path,
        "file_exists": False,
        "file_size_bytes": 0,
        "decodable": False,
        "dimensions": None,
        "pixel_array_loaded": False,
        "verdict": "VOID",
        "reason": "",
    }
    if not os.path.exists(image_path):
        gate["reason"] = "FILE_NOT_FOUND"
        return gate
    gate["file_exists"] = True
    gate["file_size_bytes"] = os.path.getsize(image_path)
    try:
        img = Image.open(image_path)
        img.verify()
        img = Image.open(image_path)
        gate["decodable"] = True
        gate["dimensions"] = {"width": img.size[0], "height": img.size[1]}
    except Exception as e:
        gate["reason"] = f"IMAGE_NOT_DECODABLE: {e}"
        return gate
    try:
        arr = np.array(img)
        if arr.ndim < 2 or arr.ndim > 3:
            gate["reason"] = f"INVALID_DIMENSIONS: {arr.ndim}D"
            return gate
        gate["pixel_array_loaded"] = True
    except Exception as e:
        gate["reason"] = f"PIXEL_LOAD_FAILED: {e}"
        return gate
    w, h = gate["dimensions"]["width"], gate["dimensions"]["height"]
    if w < 50 or h < 50:
        gate["reason"] = f"IMAGE_TOO_SMALL: {w}x{h}"
        return gate
    gate["verdict"] = "PASS"
    gate["reason"] = "Real image loaded successfully"
    return gate


# ═══════════════════════════════════════════════════════════════════════════════
# R1: PROVENANCE — SHA256 manifest
# ═══════════════════════════════════════════════════════════════════════════════
def _sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _compute_provenance(image_path: str, code_path: str | None = None) -> dict[str, Any]:
    """Full SHA256 provenance chain. No hash, no seal."""
    manifest: dict[str, Any] = {
        "run_tag": f"GEOX_RSI_{datetime.now(UTC).strftime('%Y%m%dT%H%MZ')}",
        "generated_at": datetime.now(UTC).isoformat(),
        "image_sha256": _sha256_file(image_path),
        "image_sha256_short": _sha256_file(image_path)[:16],
        "image_path": image_path,
        "image_size_bytes": os.path.getsize(image_path),
        "coordinate_domain": "pixel",
        "input_class": "image_only",
        "epistemic_note": "All outputs are OBS_IMAGE/DER_RENDER_CONTRAST. No geology without calibration.",
    }
    if code_path and os.path.exists(code_path):
        manifest["code_sha256"] = _sha256_file(code_path)
        manifest["code_sha256_short"] = _sha256_file(code_path)[:16]
    return manifest


# ═══════════════════════════════════════════════════════════════════════════════
# R2: CROP SEISMIC PANEL
# ═══════════════════════════════════════════════════════════════════════════════
def _detect_seismic_panel(arr: np.ndarray) -> dict[str, Any]:
    """Find actual seismic panel within the image. Remove margins/labels/axes."""
    h, w = arr.shape[:2]
    gray = np.mean(arr, axis=2) if arr.ndim == 3 else arr
    mask = gray < 235
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not np.any(rows) or not np.any(cols):
        return {"panel_bbox": None, "verdict": "HOLD", "reason": "No seismic panel detected"}
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    m = 3
    rmin = max(0, rmin - m)
    rmax = min(h - 1, rmax + m)
    cmin = max(0, cmin - m)
    cmax = min(w - 1, cmax + m)
    return {
        "panel_bbox": [int(cmin), int(rmin), int(cmax), int(rmax)],
        "panel_size": [int(cmax - cmin), int(rmax - rmin)],
        "original_size": [w, h],
        "crop_pct": round((cmax - cmin) * (rmax - rmin) / (w * h) * 100, 1),
        "verdict": "PASS",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# R3: AGC (Automatic Gain Control)
# ═══════════════════════════════════════════════════════════════════════════════
def _agc(data: np.ndarray, win: int = 30) -> np.ndarray:
    """Row-wise AGC normalization."""
    out = np.zeros_like(data)
    k = np.ones(win) / win
    for r in range(data.shape[0]):
        out[r] = data[r] / (np.sqrt(np.convolve(data[r] ** 2, k, mode="same") + 1e-10))
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# R4: ATTRIBUTE STACK — Full geophysical attribute computation
# ═══════════════════════════════════════════════════════════════════════════════
def _compute_attributes(amp_cropped: np.ndarray) -> dict[str, Any]:
    """Compute full attribute stack from real image pixels.

    Returns: agc, cosine_phase, phase_continuity, discontinuity, edge,
    dip_chaos, curvature, fault_probability, horizon_probability.

    All labels are DER_RENDER_CONTRAST (derived from image rendering, not geology).
    """
    hc, wc = amp_cropped.shape

    # AGC
    agc_d = _agc(amp_cropped, 30)

    # Cosine of Instantaneous Phase (Hilbert)
    cp = np.zeros_like(agc_d)
    for r in range(hc):
        cp[r] = np.cos(np.angle(hilbert(agc_d[r])))

    # Phase continuity
    pc = np.zeros_like(cp)
    for r in range(1, hc - 1):
        pc[r, 1:] = 1.0 - np.abs(np.diff(cp[r])) / 2.0

    # Discontinuity (semblance proxy)
    disc = np.zeros((hc, wc))
    for col in range(5, wc - 5):
        l = agc_d[:, col - 5 : col]
        rt = agc_d[:, col + 1 : col + 6]
        ln = l - l.mean(1, keepdims=True)
        rn = rt - rt.mean(1, keepdims=True)
        num = np.sum(ln * rn, 1)
        den = np.sqrt(np.sum(ln**2, 1) * np.sum(rn**2, 1) + 1e-10)
        disc[:, col] = 1.0 - np.clip(num / den, 0, 1)
    disc /= disc.max() + 1e-10

    # Edge (Sobel)
    edge = np.sqrt(ndimage.sobel(agc_d, 1) ** 2 + ndimage.sobel(agc_d, 0) ** 2)
    edge /= edge.max() + 1e-10

    # Structure tensor — dip + dip chaos
    gx = ndimage.sobel(agc_d, 1)
    gy = ndimage.sobel(agc_d, 0)
    Jxx = ndimage.gaussian_filter(gx * gx, 3)
    Jxy = ndimage.gaussian_filter(gx * gy, 3)
    Jyy = ndimage.gaussian_filter(gy * gy, 3)
    dip = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)
    dip_var = ndimage.uniform_filter(dip**2, 10) - ndimage.uniform_filter(dip, 10) ** 2
    dip_var /= dip_var.max() + 1e-10

    # Structure tensor orientation (fault dip direction)
    # Eigenvalues of 2x2 structure tensor
    trace = Jxx + Jyy
    det = Jxx * Jyy - Jxy**2
    discriminant = np.sqrt(np.maximum(trace**2 / 4 - det, 0))
    lambda1 = trace / 2 + discriminant
    lambda2 = trace / 2 - discriminant
    coherence_st = (lambda1 - lambda2) / (lambda1 + lambda2 + 1e-10)
    orientation = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)

    # Curvature attribute (second derivative of amplitude along dip)
    # Approximate curvature via Laplacian
    curvature = ndimage.laplace(agc_d)
    curvature = np.abs(curvature)
    curvature /= curvature.max() + 1e-10

    # Phase gradient (for fault probability)
    cp_grad = np.abs(np.gradient(cp, axis=1))
    agc_grad = np.abs(np.gradient(agc_d, axis=1))

    # ═══ FAULT PROBABILITY FUSION (improved) ═══
    # Added curvature + structure tensor coherence
    fp = (
        0.25 * disc
        + 0.20 * edge
        + 0.15 * dip_var
        + 0.15 * curvature
        + 0.10 * cp_grad
        + 0.10 * agc_grad
        + 0.05 * (1.0 - coherence_st)  # Low coherence = fault zone
    )
    fp /= fp.max() + 1e-10

    # ═══ HORIZON PROBABILITY FUSION (improved) ═══
    anti_fault = 1.0 - fp
    anti_dip = 1.0 - dip_var
    hp = (
        0.35 * pc
        + 0.25 * np.abs(agc_d) / (np.abs(agc_d).max() + 1e-10)
        + 0.20 * coherence_st
        + 0.10 * anti_fault
        + 0.10 * anti_dip
    )
    hp /= hp.max() + 1e-10

    return {
        "agc": agc_d,
        "cosine_phase": cp,
        "phase_continuity": pc,
        "discontinuity": disc,
        "edge": edge,
        "dip_chaos": dip_var,
        "curvature": curvature,
        "coherence_st": coherence_st,
        "orientation": orientation,
        "fault_probability": fp,
        "horizon_probability": hp,
        "labels": {
            "agc": "DER_RENDER_CONTRAST",
            "cosine_phase": "DER_RENDER_CONTRAST",
            "phase_continuity": "DER_RENDER_CONTRAST",
            "discontinuity": "DER_RENDER_CONTRAST",
            "edge": "DER_RENDER_CONTRAST",
            "dip_chaos": "DER_RENDER_CONTRAST",
            "curvature": "DER_RENDER_CONTRAST",
            "coherence_st": "DER_RENDER_CONTRAST",
            "orientation": "DER_RENDER_CONTRAST",
            "fault_probability": "DER_RENDER_CONTRAST",
            "horizon_probability": "DER_RENDER_CONTRAST",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# R5: FAULT DETECTION — Ant-track-lite + structure tensor + curvature
# ═══════════════════════════════════════════════════════════════════════════════
def _detect_faults(
    fp: np.ndarray,
    orientation: np.ndarray,
    min_length: int = 80,
    percentile: float = 95,
    max_faults: int = 20,
) -> list[dict[str, Any]]:
    """Extract faults from fault probability map.

    Uses ant-track-lite: threshold + NMS + connected components.
    Enhanced with structure tensor orientation for fault dip direction.
    """
    hc, wc = fp.shape
    threshold = np.percentile(fp, percentile)
    binary = fp > threshold

    # Non-maximum suppression per row
    nms = np.zeros_like(binary, dtype=bool)
    for r in range(hc):
        for c in range(1, wc - 1):
            if binary[r, c] and fp[r, c] >= fp[r, c - 1] and fp[r, c] >= fp[r, c + 1]:
                nms[r, c] = True

    # Connect vertically close pixels
    nms_dilated = ndimage.binary_dilation(nms, structure=np.ones((3, 1)))
    labeled, n_comp = ndimage.label(nms_dilated)

    faults: list[dict[str, Any]] = []
    for fid in range(1, n_comp + 1):
        pts = np.argwhere(labeled == fid)
        if len(pts) < min_length:
            continue
        high_fp = pts[fp[pts[:, 0], pts[:, 1]] > threshold]
        if len(high_fp) < min_length // 2:
            continue
        high_fp = high_fp[high_fp[:, 0].argsort()]
        conf = float(fp[high_fp[:, 0], high_fp[:, 1]].mean())

        # Compute mean orientation (fault dip direction) from structure tensor
        mean_orient = float(np.mean(orientation[high_fp[:, 0], high_fp[:, 1]]))
        dip_dir_deg = round(np.degrees(mean_orient) % 180, 1)

        # Compute fault length (vertical extent)
        vertical_extent = int(high_fp[:, 0].max() - high_fp[:, 0].min())

        faults.append(
            {
                "id": f"F{len(faults) + 1}",
                "pts": high_fp.tolist(),
                "n": len(high_fp),
                "confidence": round(conf, 3),
                "dip_direction_deg": dip_dir_deg,
                "vertical_extent_px": vertical_extent,
                "label": "INT_SEISMIC_FAULT",
                "alternatives": [
                    "Fault (structural discontinuity)",
                    "Noise / acquisition artifact",
                    "Facies change boundary",
                    "Fluid contact",
                    "Unconformity",
                ],
            }
        )

    faults.sort(key=lambda f: f["n"], reverse=True)
    faults = faults[:max_faults]
    for i, f in enumerate(faults):
        f["id"] = f"F{i + 1}"

    return faults


def _segment_fault_blocks(faults: list[dict[str, Any]], shape: tuple[int, int]) -> np.ndarray:
    """Segment image into fault blocks bounded by detected faults.

    Each pixel gets a block_id. Fault pixels get block_id=0 (boundary).
    """
    hc, wc = shape
    fault_mask = np.zeros((hc, wc), dtype=bool)
    for f in faults:
        for pt in f["pts"]:
            r, c = pt[0], pt[1]
            for dr in range(-2, 3):
                for dc in range(-1, 2):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < hc and 0 <= cc < wc:
                        fault_mask[rr, cc] = True

    # Label connected non-fault regions as blocks
    labeled_blocks, n_blocks = ndimage.label(~fault_mask)
    return labeled_blocks


# ═══════════════════════════════════════════════════════════════════════════════
# R6: HORIZON TRACKING — DP with look-ahead + multi-seed + confidence
# ═══════════════════════════════════════════════════════════════════════════════
def _track_horizon_dp(
    agc_d: np.ndarray,
    fault_mask: np.ndarray,
    seed: int,
    search: int = 5,
    lookahead: int = 10,
) -> np.ndarray:
    """DP horizon tracking with look-ahead penalty and fault barriers.

    Instead of pure greedy (pick best next pixel), looks ahead `lookahead`
    columns and penalizes paths that deviate too much from trend.
    """
    hc, wc = agc_d.shape
    path = np.zeros(wc, dtype=int)
    path[0] = max(0, min(hc - 1, seed))

    for col in range(1, wc):
        prev = int(path[col - 1])
        r_lo = max(0, prev - search)
        r_hi = min(hc, prev + search + 1)
        if r_hi <= r_lo + 1:
            path[col] = prev
            continue

        # Look-ahead: evaluate candidates by matching amplitude at current
        # AND a few columns ahead
        best_r = prev
        best_score = -1e9
        ref = agc_d[prev, col - 1]

        for r in range(r_lo, r_hi):
            # Amplitude similarity at current column
            score = -abs(agc_d[r, col] - ref)

            # Look-ahead bonus: check amplitude similarity at col+1..col+lookahead
            la_count = 0
            la_score = 0.0
            for la in range(1, min(lookahead + 1, wc - col)):
                la_ref = agc_d[r, col]
                la_lo = max(0, r - 2)
                la_hi = min(hc, r + 3)
                if la_hi > la_lo:
                    la_best = min(range(la_lo, la_hi), key=lambda x: abs(agc_d[x, col + la] - la_ref))
                    la_score -= abs(agc_d[la_best, col + la] - la_ref)
                    la_count += 1

            if la_count > 0:
                score += 0.3 * la_score / la_count  # Look-ahead weight

            # Fault barrier penalty
            if fault_mask[r, col]:
                score -= 5.0

            # Continuity penalty (prefer staying close to previous)
            score -= 0.1 * abs(r - prev)

            if score > best_score:
                best_score = score
                best_r = r

        path[col] = best_r

    return path


def _detect_and_track_horizons(
    agc_d: np.ndarray,
    pc: np.ndarray,
    fault_mask: np.ndarray,
    max_horizons: int = 12,
) -> list[dict[str, Any]]:
    """Detect horizon seeds from phase continuity + amplitude, then track with DP.

    Multi-seed: tries multiple seed rows, keeps those with good continuity.
    Confidence scoring from attribute agreement.
    """
    hc, wc = agc_d.shape

    # Horizon seed detection
    row_pc = np.mean(pc, 1)
    row_amp = np.mean(np.abs(agc_d), 1)
    row_amp /= row_amp.max() + 1e-10
    row_sig = row_pc * 0.6 + row_amp * 0.4
    peaks, props = find_peaks(row_sig, distance=20, prominence=0.005)

    horizons: list[dict[str, Any]] = []
    for seed in peaks[: max_horizons * 2]:  # Try more seeds than needed
        path = _track_horizon_dp(agc_d, fault_mask, int(seed), search=5, lookahead=10)

        # Continuity score from path smoothness
        row_std = float(np.std(path))
        cont = max(0, 1.0 - row_std / 12.0)

        # Confidence from attribute agreement (phase continuity along path)
        path_pc = np.array([pc[path[c], c] for c in range(wc)])
        phase_agreement = float(np.mean(np.abs(path_pc)))

        # Confidence from amplitude consistency along path
        path_amp = np.array([agc_d[path[c], c] for c in range(wc)])
        amp_std = float(np.std(path_amp))
        amp_consistency = max(0, 1.0 - amp_std)

        # Combined confidence
        confidence = round(0.4 * cont + 0.3 * phase_agreement + 0.3 * amp_consistency, 3)

        if cont > 0.15:
            horizons.append(
                {
                    "id": f"H{len(horizons) + 1}",
                    "pts": [[int(c), int(path[c])] for c in range(wc)],
                    "seed": int(seed),
                    "n": int(wc),
                    "continuity": round(cont, 3),
                    "phase_agreement": round(phase_agreement, 3),
                    "amplitude_consistency": round(amp_consistency, 3),
                    "confidence": confidence,
                    "label": "INT_SEISMIC_HORIZON",
                    "alternatives": [
                        "Seismic horizon (stratigraphic boundary)",
                        "Noise / side lobe artifact",
                        "Facies transition (not a surface)",
                        "Fluid contact effect",
                        "Processing artifact (AGC smear)",
                    ],
                }
            )

    # Sort by confidence, keep top horizons
    horizons.sort(key=lambda h: h["confidence"], reverse=True)
    horizons = horizons[:max_horizons]
    # Renumber
    for i, h in enumerate(horizons):
        h["id"] = f"H{i + 1}"

    return horizons


# ═══════════════════════════════════════════════════════════════════════════════
# R7: EPISTEMIC GOVERNANCE
# ═══════════════════════════════════════════════════════════════════════════════
def _build_epistemic_envelope(
    faults: list[dict[str, Any]],
    horizons: list[dict[str, Any]],
    attributes: dict[str, Any],
) -> dict[str, Any]:
    """Build epistemic governance envelope.

    Enforces OBS_IMAGE / DER_RENDER_CONTRAST / INT_SEISMIC_HORIZON / INT_SEISMIC_FAULT grammar.
    Every INT claim carries alternatives.
    """
    # Count labels
    obs_items = ["Pixel amplitude (R-B or grayscale inversion)", "Image dimensions", "Pixel array"]
    der_items = [k for k, v in attributes.get("labels", {}).items() if v == "DER_RENDER_CONTRAST"]
    int_items = [f["id"] + " " + f["label"] for f in faults] + [h["id"] + " " + h["label"] for h in horizons]

    # Collect all alternatives
    all_alternatives: list[str] = []
    for f in faults:
        all_alternatives.extend(f.get("alternatives", []))
    for h in horizons:
        all_alternatives.extend(h.get("alternatives", []))

    return {
        "grammar": {
            "OBS_IMAGE": {"count": len(obs_items), "items": obs_items, "note": "Pixels are observed. This is NOT geology."},
            "DER_RENDER_CONTRAST": {
                "count": len(der_items),
                "items": der_items,
                "note": "Derived from image rendering. Requires calibration to become geological.",
            },
            "INT_SEISMIC_HORIZON": {
                "count": len(horizons),
                "note": "Interpreted from image attributes. Alternatives listed per horizon.",
            },
            "INT_SEISMIC_FAULT": {
                "count": len(faults),
                "note": "Interpreted from image attributes. Alternatives listed per fault.",
            },
            "HOLD": {
                "items": ["Petrophysics", "Reserves", "Commerciality", "Lithology", "Fluid type", "Age", "Formation names"],
                "note": "Cannot determine from image alone. Requires calibrated seismic data + well ties.",
            },
        },
        "forbidden_claims": [
            "Lithology from pixel color",
            "Fluid type from amplitude",
            "Depth in meters without calibration",
            "Formation names without biostratigraphy",
            "Reserves or commerciality from image interpretation",
            "Proven reserves from seismic image",
        ],
        "alternatives_required": True,
        "alternatives_count": len(set(all_alternatives)),
        "epistemic_grammar": "OBS_IMAGE ≠ OBS_GEOLOGY. Pixels are observed. Geology requires calibration, well ties, and basin context.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# R8: RENDER AUDIT — validate render-vs-amplitude consistency
# ═══════════════════════════════════════════════════════════════════════════════
def _render_audit(arr_cropped: np.ndarray, agc_d: np.ndarray) -> dict[str, Any]:
    """Audit whether image rendering (colormap, contrast) distorts amplitude.

    Checks:
    1. Dynamic range usage (are we losing information to clipping?)
    2. Color space assumption (greyscale vs color)
    3. Amplitude histogram shape (Gaussian? Clipped? Bimodal?)
    4. AGC vs raw correlation (does AGC preserve structure?)

    Labels: DER_RENDER_CONTRAST (all outputs).
    """
    hc, wc = arr_cropped.shape if arr_cropped.ndim == 2 else arr_cropped.shape[:2]

    # 1. Dynamic range
    if arr_cropped.ndim == 3:
        gray = np.mean(arr_cropped, axis=2)
    else:
        gray = arr_cropped.copy()
    p1, p99 = np.percentile(gray, [1, 99])
    dynamic_range = float(p99 - p1)
    clipped_low = float(np.mean(gray <= p1))
    clipped_high = float(np.mean(gray >= p99))

    # 2. Color detection
    is_greyscale = True
    if arr_cropped.ndim == 3 and arr_cropped.shape[2] >= 3:
        r, g, b = arr_cropped[:, :, 0], arr_cropped[:, :, 1], arr_cropped[:, :, 2]
        color_diff = np.mean(np.abs(r.astype(float) - g.astype(float)) + np.abs(g.astype(float) - b.astype(float)))
        is_greyscale = color_diff < 5.0

    # 3. Histogram shape
    hist, bin_edges = np.histogram(gray.flatten(), bins=64)
    hist_norm = hist / hist.sum()
    entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))

    # 4. AGC vs raw correlation
    if agc_d.shape == gray.shape:
        raw_flat = gray.flatten()
        agc_flat = agc_d.flatten()
        if len(raw_flat) > 1 and np.std(raw_flat) > 0 and np.std(agc_flat) > 0:
            correlation = float(np.corrcoef(raw_flat, agc_flat)[0, 1])
        else:
            correlation = 0.0
    else:
        correlation = None

    # Render trust assessment
    render_trust = "HIGH"
    if dynamic_range < 50:
        render_trust = "LOW"
    elif clipped_low > 0.1 or clipped_high > 0.1:
        render_trust = "MEDIUM"
    elif not is_greyscale:
        render_trust = "MEDIUM"  # Color may encode amplitude differently

    return {
        "dynamic_range": round(dynamic_range, 1),
        "clipped_low_pct": round(clipped_low * 100, 2),
        "clipped_high_pct": round(clipped_high * 100, 2),
        "is_greyscale": is_greyscale,
        "histogram_entropy_bits": round(float(entropy), 2),
        "agc_raw_correlation": round(correlation, 3) if correlation is not None else None,
        "render_trust": render_trust,
        "label": "DER_RENDER_CONTRAST",
        "note": "Render audit validates image fidelity, not geological accuracy. Even a HIGH render trust does not mean the pixels represent true amplitude.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TOOL: geox_rsi_interpret
# ═══════════════════════════════════════════════════════════════════════════════
async def geox_rsi_interpret(
    image_path: str,
    mode: Literal["horizon_fault_pick"] = "horizon_fault_pick",
    max_faults: int = 20,
    max_horizons: int = 12,
    fault_percentile: float = 97.0,
    fault_min_length: int = 80,
    horizon_search: int = 5,
    horizon_lookahead: int = 10,
    include_attributes: bool = False,
) -> dict[str, Any]:
    """Real Seismic Image interpretation — horizon and fault picking from image pixels.

    Processes a real seismic image through the RSI pipeline:
    reality gate → provenance → crop → AGC → attribute stack →
    fault detection → horizon tracking → epistemic governance → render audit.

    OBS_IMAGE ≠ OBS_GEOLOGY: All outputs are pixel-derived, not geological measurements.
    Every INT claim carries alternative interpretations.
    PETROPHYSICS = HOLD from image-only input.

    Args:
        image_path: Path to the seismic image file (JPG, PNG, TIFF)
        mode: Interpretation mode (currently only horizon_fault_pick)
        max_faults: Maximum number of faults to extract
        max_horizons: Maximum number of horizons to track
        fault_percentile: Percentile threshold for fault probability (higher = fewer faults)
        fault_min_length: Minimum pixel length for a valid fault
        horizon_search: Search window (pixels) for horizon tracking
        horizon_lookahead: Look-ahead window for DP horizon tracking
        include_attributes: If True, include full attribute arrays in output (large!)

    Returns:
        Structured interpretation envelope with faults, horizons,
        epistemic governance, render audit, and provenance.
    """
    result: dict[str, Any] = {
        "tool": "geox_rsi_interpret",
        "mode": mode,
        "verdict": "VOID",
        "stages": {},
    }

    # R0: Reality gate
    gate = _input_reality_gate(image_path)
    result["stages"]["R0_reality_gate"] = gate
    if gate["verdict"] != "PASS":
        result["verdict"] = "HOLD"
        result["reason"] = f"Reality gate failed: {gate['reason']}"
        return result

    # Load image
    img = Image.open(image_path)
    arr = np.array(img)

    # R1: Provenance
    this_file = str(Path(__file__).resolve())
    prov = _compute_provenance(image_path, this_file)
    result["stages"]["R1_provenance"] = prov

    # R2: Crop seismic panel
    if arr.ndim == 3:
        gray_full = np.mean(arr, axis=2)
    else:
        gray_full = arr

    panel = _detect_seismic_panel(arr)
    result["stages"]["R2_panel_detect"] = {k: v for k, v in panel.items() if k != "panel_bbox"}

    if panel["verdict"] == "PASS" and panel["panel_bbox"]:
        x0, y0, x1, y1 = panel["panel_bbox"]
        amp_cropped = 255.0 - gray_full[y0:y1, x0:x1].astype(float)
        arr_cropped = arr[y0:y1, x0:x1] if arr.ndim == 3 else arr[y0:y1, x0:x1]
    else:
        amp_cropped = 255.0 - gray_full.astype(float)
        arr_cropped = arr

    hc, wc = amp_cropped.shape

    # R4: Attribute stack
    attrs = _compute_attributes(amp_cropped)
    result["stages"]["R4_attributes"] = {
        "computed": list(attrs["labels"].keys()),
        "labels": attrs["labels"],
    }

    # R5: Fault detection
    faults = _detect_faults(
        attrs["fault_probability"],
        attrs["orientation"],
        min_length=fault_min_length,
        percentile=fault_percentile,
        max_faults=max_faults,
    )
    result["stages"]["R5_faults"] = {
        "count": len(faults),
        "threshold_percentile": fault_percentile,
        "label": "INT_SEISMIC_FAULT",
    }

    # R5b: Fault block segmentation
    fault_blocks = _segment_fault_blocks(faults, (hc, wc))
    n_blocks = int(fault_blocks.max())
    result["stages"]["R5b_fault_blocks"] = {
        "n_blocks": n_blocks,
        "label": "INT_SEISMIC_FAULT",
    }

    # Build fault mask for horizon tracking
    fault_mask = np.zeros((hc, wc), dtype=bool)
    for f in faults:
        for pt in f["pts"]:
            r, c = pt[0], pt[1]
            for dr in range(-3, 4):
                for dc in range(-2, 3):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < hc and 0 <= cc < wc:
                        fault_mask[rr, cc] = True

    # R6: Horizon tracking
    horizons = _detect_and_track_horizons(
        attrs["agc"],
        attrs["phase_continuity"],
        fault_mask,
        max_horizons=max_horizons,
    )
    result["stages"]["R6_horizons"] = {
        "count": len(horizons),
        "label": "INT_SEISMIC_HORIZON",
        "lookahead": horizon_lookahead,
    }

    # R7: Epistemic governance
    govern = _build_epistemic_envelope(faults, horizons, attrs)
    result["stages"]["R7_governance"] = govern

    # R8: Render audit
    audit = _render_audit(arr_cropped, attrs["agc"])
    result["stages"]["R8_render_audit"] = audit

    # Build geometry export (polylines)
    geometry = {
        "horizons": [
            {
                "id": h["id"],
                "pts": h["pts"],
                "confidence": h["confidence"],
                "label": h["label"],
                "alternatives": h["alternatives"],
            }
            for h in horizons
        ],
        "faults": [
            {
                "id": f["id"],
                "pts": f["pts"],
                "confidence": f["confidence"],
                "dip_direction_deg": f["dip_direction_deg"],
                "vertical_extent_px": f["vertical_extent_px"],
                "label": f["label"],
                "alternatives": f["alternatives"],
            }
            for f in faults
        ],
        "fault_blocks": n_blocks,
        "crop": [int(wc), int(hc)],
        "coordinate_domain": "pixel",
    }

    # Build summary (no large arrays)
    result["horizons"] = [
        {
            "id": h["id"],
            "seed": h["seed"],
            "confidence": h["confidence"],
            "continuity": h["continuity"],
            "label": h["label"],
        }
        for h in horizons
    ]
    result["faults"] = [
        {
            "id": f["id"],
            "n_points": f["n"],
            "confidence": f["confidence"],
            "dip_direction_deg": f["dip_direction_deg"],
            "label": f["label"],
        }
        for f in faults
    ]
    result["geometry"] = geometry
    result["provenance"] = prov
    result["render_audit"] = audit

    # Optionally include full attributes
    if include_attributes:
        result["attributes"] = {
            k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in attrs.items() if k not in ("labels",)
        }

    # Forbidden claims scan
    from geox_mcp.tools.forbidden_claims import scan_output_envelope

    result = scan_output_envelope(result)

    result["verdict"] = "PARTIAL"
    result["reason"] = (
        f"Real image interpreted: {len(horizons)} horizons + {len(faults)} faults. "
        "All outputs are OBS_IMAGE/DER_RENDER_CONTRAST/INT_SEISMIC_*. "
        "No geology claimed without calibration + well ties."
    )

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TOOL: geox_render_audit
# ═══════════════════════════════════════════════════════════════════════════════
async def geox_render_audit(
    image_path: str,
    agc_window: int = 30,
) -> dict[str, Any]:
    """Audit image rendering fidelity — validate render-vs-amplitude consistency.

    Checks dynamic range, color space, histogram shape, and AGC correlation.
    All outputs labeled DER_RENDER_CONTRAST.

    This audit answers: "Does the image faithfully represent seismic amplitude,
    or has rendering (colormap, contrast, clipping) distorted the signal?"

    Args:
        image_path: Path to seismic image file
        agc_window: AGC window size for correlation check

    Returns:
        Render audit report with trust assessment.
    """
    gate = _input_reality_gate(image_path)
    if gate["verdict"] != "PASS":
        return {"verdict": "HOLD", "reason": f"Reality gate failed: {gate['reason']}"}

    img = Image.open(image_path)
    arr = np.array(img)
    gray = np.mean(arr, axis=2) if arr.ndim == 3 else arr.astype(float)

    # Crop to panel
    panel = _detect_seismic_panel(arr)
    if panel["verdict"] == "PASS" and panel["panel_bbox"]:
        x0, y0, x1, y1 = panel["panel_bbox"]
        gray_cropped = gray[y0:y1, x0:x1]
    else:
        gray_cropped = gray

    # Compute AGC
    amp = 255.0 - gray_cropped
    agc_d = _agc(amp, agc_window)

    # Run audit
    audit = _render_audit(arr if panel["verdict"] != "PASS" or not panel["panel_bbox"] else arr[y0:y1, x0:x1], agc_d)

    # Provenance
    prov = _compute_provenance(image_path, str(Path(__file__).resolve()))

    result = {
        "tool": "geox_render_audit",
        "verdict": audit["render_trust"],
        "audit": audit,
        "provenance": prov,
        "note": "Render audit validates image fidelity. HIGH trust means the pixels are likely faithful to the rendered amplitude. It does NOT mean the amplitude is true geological amplitude.",
    }

    # Forbidden claims scan
    from geox_mcp.tools.forbidden_claims import scan_output_envelope

    result = scan_output_envelope(result)

    return result
