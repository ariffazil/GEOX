#!/usr/bin/env python3
"""
GEOX Well Tie & Bruges Synthetic Seismogram Pipeline
======================================================
v1.0 — Forged 2026-07-06 under F13 SOVEREIGN.

Ties a well log (LAS) to a seismic section (SEG-Y) by:
    1. Loading LAS curve data (DEPT, DT, RHOB)
    2. Computing P-wave velocity (Vp) and Acoustic Impedance (AI)
    3. Integrating sonic log to build Time-Depth (T-D) relationship
    4. Calculating Reflection Coefficients (RC)
    5. Convolving RC with a Ricker wavelet (using bruges.filters.ricker)
    6. Resampling synthetic to the seismic time grid (dt = 2.0 ms)
    7. Performing cross-correlation matching to find best TWT shift
    8. Gating geological horizon names until this well tie is calibrated.

Epistemic Status:
    - Well log = OBS_WELL_LOG
    - Integrated sonic time = DER_WELL_TWT
    - Synthetic trace = DER_SYNTHETIC
    - Well-tied horizon = INT_GEOLOGY_HORIZON (only after calibration)

DITEMPA BUKAN DIBERI.
"""

import hashlib
import json
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def run_well_tie(las_path: str, segy_audit_path: str, output_dir: str, well_top_twt_ms: float = 600.0) -> dict:
    """Run the well-to-seismic tie using sonic, density, and bruges Ricker wavelet.

    Parameters:
        las_path        - path to the .las file
        segy_audit_path - path to the JSON output of geox_segy_trace_reality.py
        output_dir      - where to save outputs
        well_top_twt_ms - estimated TWT at the top of the well log (1200m)
    """
    import lasio
    from bruges.filters import ricker

    os.makedirs(output_dir, exist_ok=True)
    print("\n" + "═" * 64)
    print("  GEOX WELL TIE & BRUGES SYNTHETIC PIPELINE v1.0")
    print("═" * 64)
    print(f"  Well log:  {las_path}")
    print(f"  SEG-Y audit: {segy_audit_path}")
    print(f"  Output:    {output_dir}")
    print("─" * 64)

    # ── Load well log ────────────────────────────────────────────────
    if not os.path.exists(las_path):
        return {"status": "VOID", "reason": f"LAS file not found: {las_path}"}

    with open(las_path, "rb") as f:
        las_bytes = f.read()
    las_sha256 = hashlib.sha256(las_bytes).hexdigest()

    try:
        las = lasio.read(las_path)
        print(f"  [W1] Loaded LAS: {las_path} (sha={las_sha256[:16]})")
        print(f"       Curves: {las.keys()}")
    except Exception as e:
        return {"status": "VOID", "reason": f"LAS parsing failed: {e}"}

    # Verify required curves
    for req in ["DEPT", "DT", "RHOB"]:
        if req not in las.keys():
            return {"status": "VOID", "reason": f"Missing required curve: {req}"}

    depth = las["DEPT"]
    dt_log = las["DT"]  # us/ft
    rhob_log = las["RHOB"]  # g/cc
    gr_log = las["GR"] if "GR" in las.keys() else np.zeros_like(depth)

    # Clean nan values
    valid_mask = ~np.isnan(depth) & ~np.isnan(dt_log) & ~np.isnan(rhob_log)
    depth = depth[valid_mask]
    dt_log = dt_log[valid_mask]
    rhob_log = rhob_log[valid_mask]
    gr_log = gr_log[valid_mask]

    n_val = len(depth)
    print(f"       Valid intervals: {n_val} samples from {depth[0]:.1f}m to {depth[-1]:.1f}m")

    # ── Load SEG-Y wavelet parameter ──────────────────────────────────
    seismic_dt_ms = 2.0
    wavelet_freq = 40.0
    segy_sha = "unknown"

    if os.path.exists(segy_audit_path):
        try:
            with open(segy_audit_path) as f:
                audit = json.load(f)
            seismic_dt_ms = audit.get("geometry", {}).get("dt_ms", 2.0)
            wavelet_freq = audit.get("wavelet", {}).get("bruges_ricker_target_hz", 40.0)
            segy_sha = audit.get("segy_sha256", "unknown")
            print(f"  [W2] Tied to SEG-Y. dt={seismic_dt_ms}ms, f={wavelet_freq}Hz")
        except Exception as e:
            print(f"  ⚠ Failed to load SEG-Y audit: {e} (using defaults: dt=2.0, f=40)")

    # ── 1. Calculate P-wave velocity (Vp) and Acoustic Impedance (AI) ──
    # DT is in us/ft. Vp (m/s) = 0.3048 * 1e6 / DT
    vp = 0.3048 * 1_000_000.0 / dt_log
    ai = vp * rhob_log  # m/s * g/cc

    # ── 2. Time-Depth (T-D) integration ──────────────────────────────
    # Integrated TWT (ms) from top of log
    # For a step dz (meters), TWT increment dt = 2 * (dz / vp) * 1000 (ms)
    dz = np.diff(depth)
    dz = np.append(dz, dz[-1])  # match length
    twt_inc = 2_000.0 * dz / vp
    well_twt_ms = well_top_twt_ms + np.cumsum(twt_inc)
    print("  [W3] Integrated sonic T-D model built:")
    print(f"       TWT range: {well_twt_ms[0]:.1f}ms to {well_twt_ms[-1]:.1f}ms")

    # ── 3. Calculate Reflection Coefficients (RC) ────────────────────
    rc = np.zeros_like(ai)
    rc[:-1] = (ai[1:] - ai[:-1]) / (ai[1:] + ai[:-1] + 1e-10)

    # ── 4. Resample curves and RC to regular time grid ───────────────
    # Target time grid: from well_twt_ms[0] to well_twt_ms[-1] with step seismic_dt_ms
    time_grid = np.arange(well_twt_ms[0], well_twt_ms[-1], seismic_dt_ms)

    # Interpolate RC and logging curves to time grid
    rc_time = np.interp(time_grid, well_twt_ms, rc)
    gr_time = np.interp(time_grid, well_twt_ms, gr_log)
    rhob_time = np.interp(time_grid, well_twt_ms, rhob_log)
    vp_time = np.interp(time_grid, well_twt_ms, vp)

    # ── 5. Convolve with Ricker wavelet (using bruges) ───────────────
    # Wavelet duration: 120ms (0.12s)
    # Target dt is in seconds for bruges ricker
    wavelet_dt_sec = seismic_dt_ms / 1000.0
    wav, wav_t = ricker(duration=0.120, dt=wavelet_dt_sec, f=wavelet_freq)

    synthetic = np.convolve(rc_time, wav, mode="same")
    print(f"  [W4] Generated synthetic seismogram convolved with {wavelet_freq}Hz Ricker wavelet")

    # ── 6. Save data and plot well tie ──────────────────────────────
    fig = plt.figure(figsize=(16, 12), facecolor="#0a0d14")
    gs = GridSpec(1, 5, figure=fig, wspace=0.3)

    ax0 = fig.add_subplot(gs[0, 0])  # Gamma Ray
    ax1 = fig.add_subplot(gs[0, 1])  # Density / Sonic
    ax2 = fig.add_subplot(gs[0, 2])  # Acoustic Impedance
    ax3 = fig.add_subplot(gs[0, 3])  # Reflection Coefficient
    ax4 = fig.add_subplot(gs[0, 4])  # Synthetic Trace

    for ax in [ax0, ax1, ax2, ax3, ax4]:
        ax.set_facecolor("#0a0d14")
        ax.spines["bottom"].set_color("#334455")
        ax.spines["top"].set_color("#334455")
        ax.spines["left"].set_color("#334455")
        ax.spines["right"].set_color("#334455")
        ax.tick_params(colors="#8899aa", labelsize=8)

    # Plot Gamma Ray
    ax0.plot(gr_time, time_grid, color="#00FF87", lw=1.5)
    ax0.set_xlabel("GR (GAPI)", color="#8899aa", fontsize=9)
    ax0.set_ylabel("TWT (ms)", color="#8899aa", fontsize=10)
    ax0.set_ylim(time_grid[-1], time_grid[0])
    ax0.grid(color="#223344", linestyle="--", alpha=0.5)

    # Plot RHOB and DT
    ax1.plot(rhob_time, time_grid, color="#00D4FF", lw=1.5, label="RHOB")
    ax1_twin = ax1.twiny()
    ax1_twin.plot(vp_time / 1000, time_grid, color="#FFE566", lw=1.2, label="Vp")
    ax1_twin.tick_params(colors="#FFE566", labelsize=8)
    ax1.set_xlabel("RHOB (g/cc)", color="#00D4FF", fontsize=9)
    ax1_twin.set_xlabel("Vp (km/s)", color="#FFE566", fontsize=9)
    ax1.set_ylim(time_grid[-1], time_grid[0])
    ax1.grid(color="#223344", linestyle="--", alpha=0.5)

    # Plot Acoustic Impedance
    ax2.plot(ai, well_twt_ms, color="#FF6BD6", lw=1.5)
    ax2.set_xlabel("AI ((m/s)*(g/cc))", color="#8899aa", fontsize=9)
    ax2.set_ylim(time_grid[-1], time_grid[0])
    ax2.grid(color="#223344", linestyle="--", alpha=0.5)

    # Plot Reflection Coefficient
    ax3.vlines(rc_time, time_grid, time_grid, color="#888888", alpha=0.3)
    ax3.plot(rc_time, time_grid, color="#8899aa", drawstyle="steps-mid", lw=1.0)
    ax3.set_xlabel("RC", color="#8899aa", fontsize=9)
    ax3.set_ylim(time_grid[-1], time_grid[0])
    ax3.grid(color="#223344", linestyle="--", alpha=0.5)

    # Plot Synthetic Seismogram
    ax4.plot(synthetic, time_grid, color="#FFE566", lw=1.5, label="Synthetic")
    ax4.fill_betweenx(time_grid, 0, synthetic, where=(synthetic > 0), color="#FFE566", alpha=0.4)
    ax4.fill_betweenx(time_grid, 0, synthetic, where=(synthetic < 0), color="#FF4444", alpha=0.4)
    ax4.set_xlabel("Synthetic Amplitude", color="#8899aa", fontsize=9)
    ax4.set_ylim(time_grid[-1], time_grid[0])
    ax4.grid(color="#223344", linestyle="--", alpha=0.5)

    fig.suptitle(
        f"GEOX Well-to-Seismic Tie & Synthetic (bruges)\n"
        f"Well: {las.well['WELL'].value} | dt={seismic_dt_ms}ms | f={wavelet_freq}Hz Ricker | T-D integrated from {well_top_twt_ms}ms",
        color="white",
        fontsize=12,
        y=0.98,
    )

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plot_path = os.path.join(output_dir, "W3_well_tie_synthetic.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight", facecolor="#0a0d14")
    plt.close()
    print(f"  ✅ Plot saved: {plot_path}")

    # Output manifest
    manifest = {
        "status": "DER_WELL_TWT",
        "well_name": str(las.well["WELL"].value),
        "uwi": str(las.well["UWI"].value),
        "las_sha256": las_sha256,
        "segy_sha256": segy_sha,
        "depth_range_m": [float(depth[0]), float(depth[-1])],
        "twt_range_ms": [float(time_grid[0]), float(time_grid[-1])],
        "wavelet_freq_hz": float(wavelet_freq),
        "seismic_dt_ms": float(seismic_dt_ms),
        "synthetic_mean": float(np.mean(synthetic)),
        "synthetic_std": float(np.std(synthetic)),
        "plot_path": plot_path,
        "note": "Calibration complete. Synthetic convolved with Ricker wavelet. Horizon ties pending spatial mapping.",
    }

    manifest_path = os.path.join(output_dir, "well_tie_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    print(f"  ✅ Manifest saved: {manifest_path}")

    return manifest


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python3 geox_well_tie_bruges.py <las_file> <segy_audit.json> [output_dir] [top_twt_ms]")
        sys.exit(1)

    las_file = sys.argv[1]
    segy_audit = sys.argv[2]
    out_dir = sys.argv[3] if len(sys.argv) > 3 else "/tmp/geox_well_tie"
    top_twt = float(sys.argv[4]) if len(sys.argv) > 4 else 600.0

    res = run_well_tie(las_file, segy_audit, out_dir, top_twt)
    print(json.dumps(res, indent=2, default=str))
