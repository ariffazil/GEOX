"""
WELL.GR_INTERVAL_COGNITIVE — Cognitive Well Log Analysis Module
==============================================================
Human-scale interval extraction and motif classification from GR logs.
Part of the GEOX petrophysics suite.
"""

import numpy as np
from scipy.signal import savgol_filter

def despike_gr(gr, spike_threshold=50.0):
    """Remove single-point spikes using median replacement."""
    gr = np.array(gr, dtype=float)
    diff = np.abs(np.diff(gr, prepend=gr[0]))
    gr_clean = gr.copy()
    gr_clean[diff > spike_threshold] = np.nan
    if np.all(np.isnan(gr_clean)):
        return np.zeros_like(gr_clean)
    median_val = np.nanmedian(gr_clean)
    return np.nan_to_num(gr_clean, nan=median_val)

def smooth_gr(gr, depth, window_m=7.0, poly=2):
    """Savitzky-Golay smoothing with human-scale window (metres)."""
    gr = np.array(gr)
    depth = np.array(depth)
    if len(depth) < 2:
        return gr
    step = np.median(np.diff(depth))
    if step <= 0 or not np.isfinite(step):
        step = 0.5
    window_pts = int(window_m / step)
    if window_pts % 2 == 0:
        window_pts += 1
    if len(gr) < window_pts:
        return gr
    safe_poly = min(poly, window_pts - 1)
    return savgol_filter(gr, window_pts, safe_poly)

def detect_boundaries(depth, gr_smooth, min_interval=5.0):
    """Derivative-based segmentation for stable boundaries."""
    depth = np.array(depth)
    gr_smooth = np.array(gr_smooth)
    if len(gr_smooth) < 2:
        return []
    dgr = np.gradient(gr_smooth)
    sign = np.sign(dgr)
    idx = [0]
    for i in range(1, len(sign)):
        if sign[i] != sign[i-1]:
            idx.append(i)
    idx.append(len(depth) - 1)
    intervals = []
    for i in range(len(idx) - 1):
        top, base = idx[i], idx[i + 1]
        if depth[base] - depth[top] >= min_interval:
            intervals.append((top, base))
    return intervals

def merge_intervals(intervals, depth, min_interval=5.0):
    """Enforce vertical persistence law (Anti-microscale)."""
    if not intervals:
        return []
    depth = np.array(depth)
    merged = []
    current = list(intervals[0])
    for nxt in intervals[1:]:
        thickness = depth[nxt[1]] - depth[current[0]]
        if thickness < min_interval:
            current[1] = nxt[1]
        else:
            merged.append(tuple(current))
            current = list(nxt)
    merged.append(tuple(current))
    return merged

def classify_motif(gr_segment):
    """Signal-only motif attribution."""
    if len(gr_segment) < 2:
        return "UNKNOWN"
    x = np.arange(len(gr_segment))
    slope = np.polyfit(x, gr_segment, 1)[0]
    variance = np.var(gr_segment)
    if variance < 20:
        return "BLOCKY"
    if slope > 0.05:
        return "BELL"
    if slope < -0.05:
        return "FUNNEL"
    return "HETEROLITHIC"

def attach_nn(intervals_data, biostrat):
    """Attach NN zones as attributes to existing intervals."""
    if not biostrat:
        for row in intervals_data:
            row["NN_zone"], row["NN_confidence"] = None, "NA"
        return intervals_data
    for row in intervals_data:
        zones = [b["nn_zone"] for b in biostrat if row["Top_MD"] <= b["depth"] <= row["Base_MD"]]
        unique_zones = list(set(zones))
        if len(unique_zones) == 1:
            row["NN_zone"], row["NN_confidence"] = unique_zones[0], "HIGH"
        elif len(unique_zones) > 1:
            row["NN_zone"], row["NN_confidence"] = "MIXED", "LOW"
        else:
            row["NN_zone"], row["NN_confidence"] = None, "UNKNOWN"
    return intervals_data

def run_gr_cognitive_pipeline(depth_or_data, gr_array=None, biostrat=None, min_interval_m=5.0, smoothing_window_m=7.0):
    """Main entry point for cognitive GR analysis."""
    if isinstance(depth_or_data, list) and len(depth_or_data) > 0 and isinstance(depth_or_data[0], dict):
        depth = np.array([float(d["depth"]) for d in depth_or_data])
        gr = np.array([float(d["gr"]) for d in depth_or_data])
    else:
        depth, gr = np.array(depth_or_data), np.array(gr_array)
    
    gr_qc = despike_gr(gr)
    gr_s = smooth_gr(gr_qc, depth, smoothing_window_m)
    intervals = detect_boundaries(depth, gr_s, min_interval_m)
    if not intervals:
        intervals = [(0, len(depth)-1)]
    else:
        intervals = merge_intervals(intervals, depth, min_interval_m)

    rows = []
    for i0, i1 in intervals:
        segment = gr_s[i0:i1+1]
        rows.append({
            "Top_MD": float(depth[i0]), "Base_MD": float(depth[i1]),
            "Thickness": float(depth[i1] - depth[i0]),
            "GR_mean": float(np.mean(gr[i0:i1+1])),
            "Motif": classify_motif(segment)
        })
    return {"interval_table": attach_nn(rows, biostrat or []), 
            "qc": {"interval_count": len(rows), "min_interval_m": min_interval_m, "nn_used": bool(biostrat)}}
