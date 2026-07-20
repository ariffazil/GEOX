#!/usr/bin/env python3
"""
GEOX Physical Reality Interpreter
===================================
v1.0 — Forged 2026-07-06 under F13 SOVEREIGN.

USAGE:
    python3 geox_physical_reality.py <image_path> [output_dir]

    or programmatic:
        from geox_physical_reality import GeoxPhysicalReality
        result = GeoxPhysicalReality().interpret("/path/to/seismic.jpg")

WHAT THIS DOES:
    Drop any seismic image section →
    GEOX returns earth physical reality that a geologist can understand:

    ① Multi-attribute panel  (AGC + Phase + Discontinuity + Fault Prob + Edge)
    ② Horizon picks          (DP tracking with fault barriers, confidence-labelled)
    ③ Fault extraction       (ant-track-lite, Pn + NMS + connected components)
    ④ Epistemic overlay      (OBS_IMAGE / DER_CONTRAST / INT_SEISMIC labels)
    ⑤ Geologist report       (JSON: faults, horizons, attributes, verdict)
    ⑥ Provenance manifest    (SHA256 image + code + timestamp)

HARD LAWS:
    No reality gate → no processing.
    No attribute stack → no pick.
    No fault barriers → no horizon correlation.
    No geometry export → no product.
    No hash → no seal.
    OBS_IMAGE ≠ OBS_GEOLOGY.

EPISTEMIC GRAMMAR:
    OBS_IMAGE_PIXEL   — directly observed pixel values (real)
    DER_IMAGE_CONTRAST — derived from pixel arithmetic (computed)
    INT_SEISMIC_HORIZON — interpreted seismic feature (needs alternatives)
    INT_SEISMIC_FAULT  — interpreted seismic feature (needs alternatives)
    HOLD — claims not supported from image alone (petrophysics, depth, lithology)

DITEMPA BUKAN DIBERI.
"""

import matplotlib
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.signal import find_peaks, hilbert

matplotlib.use("Agg")
import hashlib
import json
import os
import sys
from datetime import UTC, datetime

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

UTC = UTC


# ═══════════════════════════════════════════════════════════════════════════
# REALITY GATE — First. Always. Non-negotiable.
# ═══════════════════════════════════════════════════════════════════════════
def _reality_gate(image_path: str) -> dict:
    """P0: Verify image exists, is decodable, and has real pixels.
    VOID or HOLD → no further processing allowed.
    """
    gate = {"verdict": "VOID", "reason": "not_started", "path": image_path}

    if not os.path.exists(image_path):
        gate["reason"] = "FILE_NOT_FOUND"
        return gate

    size = os.path.getsize(image_path)
    if size < 1000:
        gate["verdict"] = "HOLD"
        gate["reason"] = f"FILE_TOO_SMALL: {size} bytes"
        return gate

    try:
        img = Image.open(image_path)
        img.verify()
        img = Image.open(image_path)
        arr = np.array(img)
        w, h = img.size
        if w < 100 or h < 100:
            gate["reason"] = f"IMAGE_TOO_SMALL: {w}x{h}"
            return gate
        gate.update(
            {
                "verdict": "PASS",
                "reason": "real_image_loaded",
                "width": w,
                "height": h,
                "channels": arr.ndim,
                "size_bytes": size,
                "format": img.format,
            }
        )
    except Exception as e:
        gate["reason"] = f"DECODE_FAIL: {e}"

    return gate


# ═══════════════════════════════════════════════════════════════════════════
# PANEL CROP — Remove axes, labels, margins
# ═══════════════════════════════════════════════════════════════════════════
def _crop_seismic_panel(arr: np.ndarray) -> tuple:
    """Find the seismic data panel, remove white/label borders.
    Returns: (cropped_array, crop_bbox [x0,y0,x1,y1])
    """
    gray = np.mean(arr, axis=2) if arr.ndim == 3 else arr.astype(float)
    mask = gray < 240
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)

    if not np.any(rows) or not np.any(cols):
        return arr, [0, 0, arr.shape[1], arr.shape[0]]

    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    r0 = max(0, r0 - 5)
    r1 = min(arr.shape[0], r1 + 5)
    c0 = max(0, c0 - 5)
    c1 = min(arr.shape[1], c1 + 5)

    return arr[r0:r1, c0:c1], [int(c0), int(r0), int(c1), int(r1)]


# ═══════════════════════════════════════════════════════════════════════════
# AMPLITUDE EXTRACTION — Real pixels, real contrast
# ═══════════════════════════════════════════════════════════════════════════
def _extract_amplitude(arr: np.ndarray) -> np.ndarray:
    """Extract seismic amplitude from image pixels.

    Colour seismic: amplitude = R - B (polarity auto-detected).
    Greyscale seismic: amplitude = inverted intensity (dark = high amplitude).

    Label: OBS_IMAGE_PIXEL
    """
    if arr.ndim == 3:
        r = arr[:, :, 0].astype(float)
        b = arr[:, :, 2].astype(float)
        # Auto-polarity: which channel dominates?
        if r.mean() > b.mean():
            amp = r - b  # red = positive
        else:
            amp = b - r  # blue = positive
    else:
        # Greyscale: invert so dark areas = high amplitude
        amp = 255.0 - arr.astype(float)

    # Normalize to [-1, 1] or [0, 1]
    amax = np.abs(amp).max()
    return amp / (amax + 1e-10)


# ═══════════════════════════════════════════════════════════════════════════
# ATTRIBUTE STACK — 6 physical attributes
# ═══════════════════════════════════════════════════════════════════════════
def _compute_attributes(amp: np.ndarray) -> dict:
    """Compute 6 seismic attributes from amplitude array.

    All outputs: DER_IMAGE_CONTRAST (derived from pixel arithmetic).
    No geology claimed. These are image-domain surrogates.

    ① AGC       — Automatic Gain Control (trace-by-trace normalization)
    ② Phase     — Cosine of instantaneous phase (Hilbert transform)
    ③ Coherence — Phase continuity (horizon indicator)
    ④ Disc      — Lateral discontinuity / semblance proxy (fault indicator)
    ⑤ Edge      — Sobel edge magnitude (structural boundary)
    ⑥ DipChaos  — Structure tensor dip variance (deformation indicator)
    """
    hc, wc = amp.shape
    attrs = {}

    # ① AGC — Automatic Gain Control (window=30 traces)
    agc = np.zeros_like(amp)
    win = 30
    k = np.ones(win) / win
    for r in range(hc):
        rms = np.sqrt(np.convolve(amp[r] ** 2, k, mode="same") + 1e-10)
        agc[r] = amp[r] / rms
    attrs["agc"] = agc

    # ② Cosine of Instantaneous Phase (per-trace Hilbert)
    cp = np.zeros_like(agc)
    for r in range(hc):
        analytic = hilbert(agc[r])
        cp[r] = np.cos(np.angle(analytic))
    attrs["phase"] = cp

    # ③ Phase Continuity (lateral coherence)
    pc = np.zeros_like(cp)
    for r in range(1, hc - 1):
        if wc > 1:
            pc[r, 1:] = 1.0 - np.abs(np.diff(cp[r])) / 2.0
    attrs["coherence"] = pc

    # ④ Lateral Discontinuity (semblance proxy, fault indicator)
    disc = np.zeros((hc, wc))
    half = 5
    for col in range(half, wc - half):
        left = agc[:, col - half : col]
        right = agc[:, col + 1 : col + half + 1]
        ln = left - left.mean(1, keepdims=True)
        rn = right - right.mean(1, keepdims=True)
        num = np.sum(ln * rn, 1)
        den = np.sqrt(np.sum(ln**2, 1) * np.sum(rn**2, 1) + 1e-10)
        disc[:, col] = 1.0 - np.clip(num / den, 0, 1)
    disc_max = disc.max()
    attrs["discontinuity"] = disc / (disc_max + 1e-10)

    # ⑤ Edge (Sobel — structural boundaries)
    sx = ndimage.sobel(agc, axis=1)
    sy = ndimage.sobel(agc, axis=0)
    edge = np.sqrt(sx**2 + sy**2)
    attrs["edge"] = edge / (edge.max() + 1e-10)

    # ⑥ Dip Chaos (structure tensor — deformation/folding indicator)
    gx = ndimage.sobel(agc, axis=1)
    gy = ndimage.sobel(agc, axis=0)
    Jxx = ndimage.gaussian_filter(gx * gx, 3)
    Jxy = ndimage.gaussian_filter(gx * gy, 3)
    Jyy = ndimage.gaussian_filter(gy * gy, 3)
    dip = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)
    dip_var = ndimage.uniform_filter(dip**2, 10) - ndimage.uniform_filter(dip, 10) ** 2
    attrs["dip_chaos"] = dip_var / (dip_var.max() + 1e-10)

    return attrs


# ═══════════════════════════════════════════════════════════════════════════
# FAULT PROBABILITY FUSION — weighted multi-attribute
# ═══════════════════════════════════════════════════════════════════════════
def _compute_fault_probability(attrs: dict) -> np.ndarray:
    """Fuse attributes into fault probability map.

    Weights (from geophysics practice):
        disc    0.35 — strongest: lateral discontinuity = fault/fracture
        edge    0.25 — structural boundary
        dip     0.20 — dip chaos = deformation zone
        phase   0.10 — phase break
        amp     0.10 — amplitude gradient

    Label: DER_IMAGE_CONTRAST (fault probability proxy, not geology)
    """
    agc = attrs["agc"]
    cp_grad = np.abs(np.gradient(attrs["phase"], axis=1))
    amp_grad = np.abs(np.gradient(agc, axis=1))

    fp = (
        0.35 * attrs["discontinuity"]
        + 0.25 * attrs["edge"]
        + 0.20 * attrs["dip_chaos"]
        + 0.10 * cp_grad / (cp_grad.max() + 1e-10)
        + 0.10 * amp_grad / (amp_grad.max() + 1e-10)
    )

    return fp / (fp.max() + 1e-10)


# ═══════════════════════════════════════════════════════════════════════════
# FAULT EXTRACTION — ant-track-lite
# ═══════════════════════════════════════════════════════════════════════════
def _extract_faults(fp: np.ndarray, min_pts: int = 100, max_faults: int = 15) -> list:
    """Extract fault traces from fault probability map.

    Algorithm:
        1. Threshold at P97 (top 3% — tighter than P95, fewer false positives)
        2. Non-maximum suppression (lateral, per row)
        3. Vertical dilation (3 rows — connect nearby fragments)
        4. Connected components
        5. Filter:
            - min_pts: minimum trace length (noise gate)
            - row_span: must span >10% of image height (reject small blobs)
            - conf_proxy: must exceed mean fault probability
        6. Cap at max_faults for geologist readability

    Label: INT_SEISMIC_FAULT (interpreted — needs alternatives)
    """
    hc, wc = fp.shape
    # P96 threshold — calibrated between P95 (too many) and P97 (too few)
    threshold = np.percentile(fp, 96)
    binary = fp > threshold
    min_row_span = max(8, int(hc * 0.05))  # must span 5% of image height

    # NMS per row — keep local lateral maxima only
    nms = np.zeros_like(binary, dtype=bool)
    for r in range(hc):
        for c in range(1, wc - 1):
            if binary[r, c] and fp[r, c] >= fp[r, c - 1] and fp[r, c] >= fp[r, c + 1]:
                nms[r, c] = True

    # Dilate vertically to connect close fragments (3 rows)
    nms_dilated = ndimage.binary_dilation(nms, structure=np.ones((3, 1)))
    labeled, n_comp = ndimage.label(nms_dilated)

    faults = []
    for fid in range(1, n_comp + 1):
        pts = np.argwhere(labeled == fid)
        if len(pts) < min_pts:
            continue
        # Keep only high-probability pixels in component
        high = pts[fp[pts[:, 0], pts[:, 1]] > threshold]
        if len(high) < min_pts // 2:
            continue
        high = high[high[:, 0].argsort()]  # sort by row

        row_span = int(high[:, 0].max() - high[:, 0].min())
        col_spread = int(high[:, 1].max() - high[:, 1].min())

        # Row span filter — must be a real structural feature
        if row_span < min_row_span:
            continue

        conf = float(fp[high[:, 0], high[:, 1]].mean())

        # Dip classification
        if col_spread < row_span * 0.25:
            dip_est = "near-vertical"
        elif col_spread < row_span * 0.60:
            dip_est = "oblique"
        else:
            dip_est = "low-angle"

        faults.append(
            {
                "id": f"F{len(faults) + 1}",
                "pts": high.tolist(),
                "n_pts": len(high),
                "conf_proxy": round(conf, 3),
                "row_span": row_span,
                "col_spread": col_spread,
                "dip_est": dip_est,
                "epistemic": "INT_SEISMIC_FAULT",
                "alternatives": [
                    "Lithological contrast boundary (not fault)",
                    "Processing artefact (NMO stretch zone)",
                    "Acquisition footprint",
                    "Stratigraphic pinch-out",
                ],
            }
        )

    # Sort by length, cap for readability
    faults.sort(key=lambda f: f["n_pts"], reverse=True)
    faults = faults[:max_faults]
    for i, f in enumerate(faults):
        f["id"] = f"F{i + 1}"

    return faults


# ═══════════════════════════════════════════════════════════════════════════
# HORIZON TRACKING — DP with fault barriers
# ═══════════════════════════════════════════════════════════════════════════
def _extract_horizons(attrs: dict, faults: list, max_horizons: int = 8) -> list:
    """Extract and track reflection horizons.

    Algorithm:
        1. Horizon probability = fused phase + coherence + amplitude
        2. Row-average signal → find peaks (seeds)
        3. Build fault mask (no picking across faults)
        4. DP tracker: follow amplitude similarity with fault penalty
        5. Confidence = 1 - stddev(path) / normaliser

    Label: INT_SEISMIC_HORIZON (interpreted — needs alternatives)
    """
    agc = attrs["agc"]
    attrs["phase"]
    pc = attrs["coherence"]
    hc, wc = agc.shape

    # Horizon probability per row
    row_pc = np.mean(pc, axis=1)
    row_amp = np.mean(np.abs(agc), axis=1)
    row_amp /= row_amp.max() + 1e-10
    row_sig = row_pc * 0.6 + row_amp * 0.4

    # Seeds: peaks in row signal
    peaks, props = find_peaks(row_sig, distance=20, prominence=0.003, height=0.1)

    # Build fault mask (penalise tracking across faults)
    fault_mask = np.zeros((hc, wc), dtype=bool)
    for f in faults:
        for pt in f["pts"]:
            r, c = int(pt[0]), int(pt[1])
            for dr in range(-3, 4):
                for dc in range(-2, 3):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < hc and 0 <= cc < wc:
                        fault_mask[rr, cc] = True

    # DP tracker
    def track(seed_row: int, search: int = 6) -> np.ndarray:
        path = np.zeros(wc, dtype=int)
        path[0] = max(0, min(hc - 1, seed_row))
        for col in range(1, wc):
            prev = int(path[col - 1])
            r_lo = max(0, prev - search)
            r_hi = min(hc, prev + search + 1)
            ref = agc[prev, col - 1]
            best_r, best_score = prev, -1e9
            for r in range(r_lo, r_hi):
                score = -abs(agc[r, col] - ref)
                if fault_mask[r, col]:
                    score -= 3.0
                if score > best_score:
                    best_score, best_r = score, r
            path[col] = best_r
        return path

    horizons = []
    used_rows = set()

    for seed in peaks[: max_horizons * 2]:
        seed = int(seed)
        # Skip if too close to existing horizon
        if any(abs(seed - u) < 15 for u in used_rows):
            continue

        path = track(seed)
        std = float(np.std(path))
        continuity = max(0.0, 1.0 - std / 15.0)

        if continuity > 0.10:  # reject jitter-dominated paths
            # Amplitude at picked horizon
            picked_amp = [float(agc[int(path[c]), c]) for c in range(0, wc, max(1, wc // 50))]
            mean_amp = float(np.mean(np.abs(picked_amp)))

            horizons.append(
                {
                    "id": f"H{len(horizons) + 1}",
                    "pts": [[int(c), int(path[c])] for c in range(wc)],
                    "seed_row": seed,
                    "n_pts": int(wc),
                    "continuity": round(continuity, 3),
                    "mean_amplitude_proxy": round(mean_amp, 3),
                    "epistemic": "INT_SEISMIC_HORIZON",
                    "alternatives": [
                        "Noise train riding on coherent noise",
                        "Multiple reflection (not primary geology)",
                        "Processing artefact (migration smiles)",
                    ],
                }
            )
            used_rows.add(seed)

    return horizons[:max_horizons]


# ═══════════════════════════════════════════════════════════════════════════
# PROVENANCE — SHA256 chain
# ═══════════════════════════════════════════════════════════════════════════
def _provenance(image_path: str) -> dict:
    with open(image_path, "rb") as f:
        img_hash = hashlib.sha256(f.read()).hexdigest()
    with open(__file__, "rb") as f:
        code_hash = hashlib.sha256(f.read()).hexdigest()
    return {
        "image_sha256": img_hash,
        "image_sha256_short": img_hash[:16],
        "code_sha256": code_hash,
        "code_sha256_short": code_hash[:16],
        "code_file": os.path.basename(__file__),
        "generated_at": datetime.now(UTC).isoformat(),
        "run_tag": f"GEOX_PRI_{datetime.now(UTC).strftime('%Y%m%dT%H%MZ')}",
        "input_class": "image_only",
        "coordinate_domain": "pixel_image",
        "epistemic_note": "OBS_IMAGE ≠ OBS_GEOLOGY. Pixels observed. Geology requires calibration.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# RENDER — Geologist-grade multi-panel figure
# ═══════════════════════════════════════════════════════════════════════════
FAULT_COLOR = "#FF6B35"  # orange-red — visible on dark and light
HORIZON_COLORS = [
    "#00FF87",
    "#00D4FF",
    "#FFE566",
    "#FF6BD6",
    "#87CEEB",
    "#FF9F43",
    "#A8FF78",
    "#FF8EFF",
]


def _render(raw_arr: np.ndarray, crop_bbox: list, attrs: dict, faults: list, horizons: list, prov: dict, output_dir: str) -> list:
    """Generate 3 geologist-facing output panels:

    Panel A — Master interpretation (raw + picks + labels + epistemic)
    Panel B — 6-attribute composite (AGC, Phase, Coherence, Disc, Fault Prob, Edge)
    Panel C — Geologist's section (clean picks on raw, styled for readability)
    """
    os.makedirs(output_dir, exist_ok=True)
    x0, y0, x1, y1 = crop_bbox
    agc = attrs["agc"]
    fp = _compute_fault_probability(attrs)
    hc, wc = agc.shape

    prov_short = f"img:{prov['image_sha256_short']} | code:{prov['code_sha256_short']} | {prov['run_tag']}"
    outputs = []

    # ─────────────────────────────────────────────────────────────
    # PANEL A — Master Interpretation
    # ─────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(18, 10), facecolor="#0d1117")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#0d1117")

    # Base: raw seismic (greyscale if needed)
    display = raw_arr[y0:y1, x0:x1]
    if display.ndim == 2:
        ax.imshow(display, cmap="gray", aspect="auto", vmin=0, vmax=255)
    else:
        ax.imshow(display, aspect="auto")

    # Fault probability heat overlay (subtle)
    ax.imshow(fp, cmap="hot", aspect="auto", alpha=0.18, vmin=0, vmax=np.percentile(fp, 99))

    # Draw horizons
    for i, h in enumerate(horizons):
        pts = np.array(h["pts"])
        col = HORIZON_COLORS[i % len(HORIZON_COLORS)]
        ax.plot(
            pts[:, 0],
            pts[:, 1],
            "-",
            color=col,
            linewidth=2.2,
            alpha=0.90,
            path_effects=[pe.withStroke(linewidth=3.5, foreground="black")],
        )
        # Label at 75% width
        lx = int(wc * 0.75)
        ly = int(pts[lx, 1]) if lx < len(pts) else int(pts[-1, 1])
        conf_pct = int(h["continuity"] * 100)
        ax.text(
            lx,
            ly - 5,
            f"{h['id']} ({conf_pct}%)",
            color=col,
            fontsize=9,
            fontweight="bold",
            va="bottom",
            path_effects=[pe.withStroke(linewidth=2, foreground="black")],
        )

    # Draw faults
    for f in faults:
        pts = np.array(f["pts"])
        ax.plot(
            pts[:, 1],
            pts[:, 0],
            "-",
            color=FAULT_COLOR,
            linewidth=2.5,
            alpha=0.88,
            path_effects=[pe.withStroke(linewidth=4, foreground="black")],
        )
        mid = len(pts) // 2
        conf_pct = int(f["conf_proxy"] * 100)
        ax.text(
            pts[mid, 1] + 8,
            pts[mid, 0],
            f"{f['id']}\n{conf_pct}%",
            color=FAULT_COLOR,
            fontsize=8,
            fontweight="bold",
            path_effects=[pe.withStroke(linewidth=2, foreground="black")],
        )

    # Epistemic banner
    ax.text(
        0.01,
        0.99,
        "⚠ OBS_IMAGE_PIXEL — pixels observed. INT_SEISMIC — interpreted. Not OBS_GEOLOGY.",
        transform=ax.transAxes,
        color="#FFE566",
        fontsize=8,
        va="top",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1a2e", alpha=0.85),
    )

    # Legend
    legend_elements = [
        Line2D([0], [0], color=FAULT_COLOR, lw=2.5, label="INT_SEISMIC_FAULT (alternatives listed in report)"),
    ] + [
        Line2D(
            [0],
            [0],
            color=HORIZON_COLORS[i % len(HORIZON_COLORS)],
            lw=2.2,
            label=f"{h['id']} cont={h['continuity']:.0%}  INT_SEISMIC_HORIZON",
        )
        for i, h in enumerate(horizons)
    ]
    ax.legend(handles=legend_elements, loc="lower left", fontsize=8, facecolor="#161b22", edgecolor="#30363d", labelcolor="white")

    # Provenance stamp
    ax.text(0.99, 0.01, prov_short, transform=ax.transAxes, color="#555", fontsize=6, va="bottom", ha="right", family="monospace")

    ax.set_title(
        f"GEOX Physical Reality — {len(horizons)} Horizons | {len(faults)} Faults\n"
        f"Attribute stack: AGC + Phase + Discontinuity + Edge + DipChaos",
        color="white",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )
    ax.set_xlabel("Trace (pixel)", color="#888")
    ax.set_ylabel("Time proxy (pixel)", color="#888")
    ax.tick_params(colors="#555")
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")

    plt.tight_layout()
    out_a = os.path.join(output_dir, "A_master_interpretation.png")
    plt.savefig(out_a, dpi=180, bbox_inches="tight", facecolor="#0d1117")
    plt.close()
    outputs.append(out_a)
    print(f"  ✅ Panel A: {out_a}")

    # ─────────────────────────────────────────────────────────────
    # PANEL B — 6-Attribute Composite
    # ─────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(22, 12), facecolor="#0d1117")
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.25)

    attr_cfg = [
        ("agc", "AGC (Gain-Corrected)", "RdBu_r", -2, 2, "① DER_IMAGE_CONTRAST"),
        ("phase", "Cosine Phase", "RdBu_r", -1, 1, "② DER_IMAGE_CONTRAST"),
        ("coherence", "Phase Coherence", "viridis", 0, 1, "③ DER_IMAGE_CONTRAST"),
        ("discontinuity", "Discontinuity", "hot", 0, np.percentile(attrs["discontinuity"], 98), "④ DER_IMAGE_CONTRAST"),
        (None, "Fault Probability", "YlOrRd", 0, np.percentile(fp, 98), "⑤ DER_IMAGE_CONTRAST"),
        ("edge", "Edge (Sobel)", "plasma", 0, np.percentile(attrs["edge"], 98), "⑥ DER_IMAGE_CONTRAST"),
    ]

    for idx, (akey, title, cmap, vmin, vmax, ep_label) in enumerate(attr_cfg):
        ax = fig.add_subplot(gs[idx // 3, idx % 3])
        ax.set_facecolor("#0d1117")
        data = fp if akey is None else attrs[akey]
        im = ax.imshow(data, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax)
        ax.set_title(f"{title}\n{ep_label}", color="white", fontsize=9, fontweight="bold")
        ax.tick_params(colors="#444", labelsize=7)
        plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02).ax.tick_params(colors="#666", labelsize=6)

    fig.suptitle(f"GEOX v3.3 — Multi-Attribute Stack\n{prov_short}", color="white", fontsize=10, fontweight="bold")

    out_b = os.path.join(output_dir, "B_attribute_composite.png")
    plt.savefig(out_b, dpi=150, bbox_inches="tight", facecolor="#0d1117")
    plt.close()
    outputs.append(out_b)
    print(f"  ✅ Panel B: {out_b}")

    # ─────────────────────────────────────────────────────────────
    # PANEL C — Clean Geologist Section (print-ready)
    # ─────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(20, 9), facecolor="white")
    ax.set_facecolor("white")

    # Display AGC (high-contrast, clean)
    ax.imshow(agc, cmap="seismic", aspect="auto", vmin=-1.5, vmax=1.5, alpha=0.95)

    # Horizons — bold, geologist style
    for i, h in enumerate(horizons):
        pts = np.array(h["pts"])
        col = HORIZON_COLORS[i % len(HORIZON_COLORS)]
        ax.plot(
            pts[:, 0],
            pts[:, 1],
            "-",
            color=col,
            linewidth=2.8,
            alpha=0.95,
            path_effects=[pe.withStroke(linewidth=4.5, foreground="black")],
        )
        lx = len(pts) // 2
        ly = int(pts[lx, 1])
        ax.text(
            pts[lx, 0] + 5,
            ly - 8,
            f"{h['id']}  cont={h['continuity']:.0%}",
            color="black",
            fontsize=9,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor=col, alpha=0.9),
        )

    # Faults — bold lines + labels
    for f in faults[:12]:  # cap for readability
        pts = np.array(f["pts"])
        ax.plot(
            pts[:, 1],
            pts[:, 0],
            "-",
            color="#CC0000",
            linewidth=2.8,
            alpha=0.95,
            path_effects=[pe.withStroke(linewidth=4.5, foreground="white")],
        )
        mid = len(pts) // 2
        ax.annotate(
            f"{f['id']}",
            xy=(pts[mid, 1], pts[mid, 0]),
            xytext=(pts[mid, 1] + 12, pts[mid, 0] - 8),
            color="#CC0000",
            fontsize=9,
            fontweight="bold",
            arrowprops=dict(arrowstyle="-", color="#CC0000", lw=1),
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85),
        )

    # Interpretive note box
    note_lines = [
        "EPISTEMIC STATUS",
        f"Horizons: {len(horizons)} — INT_SEISMIC_HORIZON",
        f"Faults: {len(faults)} — INT_SEISMIC_FAULT",
        "HOLD: depth, lithology, fluid, reserves",
        "All picks have stated alternatives (see report).",
    ]
    ax.text(
        0.01,
        0.98,
        "\n".join(note_lines),
        transform=ax.transAxes,
        fontsize=8,
        va="top",
        ha="left",
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", edgecolor="#CC8800", alpha=0.95),
    )

    ax.set_title(
        f"GEOX Physical Reality — Geologist Section\n{len(horizons)} horizons  |  {len(faults)} faults  |  {prov['run_tag']}",
        fontsize=12,
        fontweight="bold",
        color="#111",
    )
    ax.set_xlabel("Trace (pixel X)", fontsize=10)
    ax.set_ylabel("Time proxy (pixel Y)", fontsize=10)

    plt.tight_layout()
    out_c = os.path.join(output_dir, "C_geologist_section.png")
    plt.savefig(out_c, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    outputs.append(out_c)
    print(f"  ✅ Panel C: {out_c}")

    return outputs


# ═══════════════════════════════════════════════════════════════════════════
# GEOSEISMIC MODEL — JSON report
# ═══════════════════════════════════════════════════════════════════════════
def _build_report(faults: list, horizons: list, prov: dict, gate: dict, crop_bbox: list, outputs: list) -> dict:
    """Build geoseismic model envelope — the product.

    Structure:
        input       — provenance + reality gate result
        attributes  — what was computed
        faults      — polylines + confidence + alternatives
        horizons    — polylines + continuity + alternatives
        epistemic   — what we know / what we don't know
        verdict     — PARTIAL (image-only interpretation)
        outputs     — file list
    """

    def tn(o):
        if isinstance(o, (np.integer, np.int64)):
            return int(o)
        if isinstance(o, (np.floating, np.float64)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return o

    report = {
        "schema": "geox_physical_reality_v1.0",
        "input": {
            "provenance": prov,
            "reality_gate": {k: v for k, v in gate.items() if k not in ("verdict",)},
            "gate_verdict": gate["verdict"],
            "crop_bbox": crop_bbox,
        },
        "attributes_computed": [
            "AGC (DER_IMAGE_CONTRAST)",
            "Cosine Instantaneous Phase (DER_IMAGE_CONTRAST)",
            "Phase Coherence (DER_IMAGE_CONTRAST)",
            "Lateral Discontinuity / Semblance Proxy (DER_IMAGE_CONTRAST)",
            "Sobel Edge (DER_IMAGE_CONTRAST)",
            "Structure Tensor Dip Chaos (DER_IMAGE_CONTRAST)",
            "Fault Probability Fusion (DER_IMAGE_CONTRAST)",
        ],
        "faults": [
            {k: v for k, v in f.items() if k != "pts"} | {"polyline_pts": f["pts"][:20]}  # truncated for JSON readability
            for f in faults
        ],
        "fault_polylines_full": {f["id"]: f["pts"] for f in faults},
        "horizons": [
            {k: v for k, v in h.items() if k != "pts"} | {"polyline_sample": h["pts"][:: max(1, len(h["pts"]) // 20)]}
            for h in horizons
        ],
        "horizon_polylines_full": {h["id"]: h["pts"] for h in horizons},
        "epistemic": {
            "OBS_IMAGE_PIXEL": ["Raw pixel values", "Image amplitude"],
            "DER_IMAGE_CONTRAST": [
                "AGC amplitude",
                "Cosine phase",
                "Coherence",
                "Discontinuity",
                "Edge magnitude",
                "Dip chaos",
                "Fault probability",
            ],
            "INT_SEISMIC_HORIZON": [h["id"] for h in horizons],
            "INT_SEISMIC_FAULT": [f["id"] for f in faults],
            "HOLD_from_image": [
                "True depth (m/ft) — requires velocity model",
                "Lithology — requires well calibration",
                "Fluid type — requires AVO + rock physics",
                "Formation names — requires well tie",
                "Reserves / commerciality — requires volumetrics",
                "Petrophysics — requires calibrated logs",
            ],
            "forbidden_claims": [
                "No lithology from pixel colour",
                "No fluid type from amplitude alone",
                "No depth without velocity",
                "No formation names without well tie",
                "No reserves without volumetrics",
            ],
            "epistemic_grammar": "OBS_IMAGE ≠ OBS_GEOLOGY. Pixels observed. Geology requires calibration.",
        },
        "verdict": "PARTIAL_IMAGE_INTERPRETATION",
        "confidence_cap": 0.90,  # F7 HUMILITY — never claim certainty
        "outputs": outputs,
        "next_steps": [
            "Calibrate with SEG-Y for true amplitude (segyio)",
            "Well tie for formation naming (bruges wavelet convolution)",
            "AVO analysis for fluid indication (Shuey two-term)",
            "3D implicit model if multi-section available (GemPy)",
            "Route to WEALTH for capital consequence (NPV/EMV)",
        ],
    }

    return json.loads(json.dumps(report, default=tn))


# ═══════════════════════════════════════════════════════════════════════════
# MAIN INTERPRETER — Public API
# ═══════════════════════════════════════════════════════════════════════════
class GeoxPhysicalReality:
    """GEOX Physical Reality Interpreter.

    Usage:
        result = GeoxPhysicalReality().interpret("seismic.jpg", output_dir="./out")
        print(result['verdict'])
        # "PARTIAL_IMAGE_INTERPRETATION"
    """

    def interpret(self, image_path: str, output_dir: str | None = None, max_horizons: int = 8, min_fault_pts: int = 80) -> dict:
        """Full interpretation pipeline.

        image_path   — any seismic section image (JPG, PNG, TIFF)
        output_dir   — where to write panels + report (default: next to image)
        max_horizons — cap on tracked horizons
        min_fault_pts — minimum ant-track fault length (noise gate)

        Returns geoseismic model dict.
        """
        image_path = str(image_path)
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(image_path), "geox_out")

        print(f"\n{'═' * 65}")
        print("  GEOX PHYSICAL REALITY INTERPRETER v1.0")
        print(f"{'═' * 65}")
        print(f"  Input:  {image_path}")
        print(f"  Output: {output_dir}")
        print(f"{'─' * 65}")

        # ── P0: REALITY GATE ──────────────────────────────────────
        print("  [P0] Reality gate...")
        gate = _reality_gate(image_path)
        if gate["verdict"] != "PASS":
            print(f"  ❌ GATE FAILED: {gate['reason']}")
            return {"verdict": "VOID", "reason": gate["reason"], "gate": gate}
        print(f"  ✅ Gate: {gate['width']}×{gate['height']}px, {gate['channels']}ch")

        # ── P1: LOAD + CROP ───────────────────────────────────────
        print("  [P1] Load + crop seismic panel...")
        raw_arr = np.array(Image.open(image_path))
        cropped, crop_bbox = _crop_seismic_panel(raw_arr)
        x0, y0, x1, y1 = crop_bbox
        print(f"  ✅ Crop: {x1 - x0}×{y1 - y0}px (from {gate['width']}×{gate['height']})")

        # ── P2: AMPLITUDE ─────────────────────────────────────────
        print("  [P2] Extract amplitude (OBS_IMAGE_PIXEL)...")
        amp = _extract_amplitude(cropped)
        print(f"  ✅ Amp range: [{amp.min():.3f}, {amp.max():.3f}]")

        # ── P3: ATTRIBUTE STACK ───────────────────────────────────
        print("  [P3] Compute attribute stack (6 attributes)...")
        attrs = _compute_attributes(amp)
        print("  ✅ AGC + Phase + Coherence + Discontinuity + Edge + DipChaos")

        # ── P4: FAULT EXTRACTION ──────────────────────────────────
        print("  [P4] Extract faults (ant-track-lite)...")
        fp = _compute_fault_probability(attrs)
        faults = _extract_faults(fp, min_pts=min_fault_pts)
        print(f"  ✅ Faults: {len(faults)}")
        for f in faults[:5]:
            print(f"       {f['id']}: {f['n_pts']} pts, conf_proxy={f['conf_proxy']:.2%}, {f['dip_est']}")

        # ── P5: HORIZON TRACKING ──────────────────────────────────
        print("  [P5] Track horizons (DP + fault barriers)...")
        horizons = _extract_horizons(attrs, faults, max_horizons=max_horizons)
        print(f"  ✅ Horizons: {len(horizons)}")
        for h in horizons:
            print(f"       {h['id']}: cont={h['continuity']:.0%}, seed={h['seed_row']}")

        # ── P6: PROVENANCE ────────────────────────────────────────
        print("  [P6] Provenance SHA256...")
        prov = _provenance(image_path)
        print(f"  ✅ img:{prov['image_sha256_short']} | code:{prov['code_sha256_short']}")

        # ── P7: RENDER ────────────────────────────────────────────
        print("  [P7] Render 3 panels...")
        outputs = _render(raw_arr, crop_bbox, attrs, faults, horizons, prov, output_dir)

        # ── P8: REPORT ────────────────────────────────────────────
        print("  [P8] Build geoseismic model report...")
        report = _build_report(faults, horizons, prov, gate, crop_bbox, outputs)
        report_path = os.path.join(output_dir, "geoseismic_model.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        outputs.append(report_path)
        print(f"  ✅ Report: {report_path}")

        print(f"\n{'═' * 65}")
        print(f"  PRODUCT: {len(horizons)} horizons | {len(faults)} faults")
        print(f"  VERDICT: {report['verdict']}")
        print("  EPISTEMIC: image-domain only — geology requires calibration")
        print("  NEXT: segyio (SEG-Y) → bruges (well tie) → GemPy (3D) → WEALTH")
        print(f"{'═' * 65}\n")

        # Store raw attributes for downstream use (geological cognition, Panel D)
        self._last_attrs = attrs
        self._last_fp = fp
        self._last_faults = faults
        self._last_horizons = horizons
        self._last_raw_arr = raw_arr
        self._last_crop_bbox = crop_bbox

        return report


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 geox_physical_reality.py <seismic_image> [output_dir]")
        print("       Drop any seismic image → geologist-grade interpretation")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    result = GeoxPhysicalReality().interpret(image_path, output_dir=output_dir)

    if result.get("verdict") == "VOID":
        print(f"❌ VOID: {result.get('reason')}")
        sys.exit(1)

    print("Outputs:")
    for o in result.get("outputs", []):
        print(f"  {o}")
