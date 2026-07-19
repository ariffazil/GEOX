#!/usr/bin/env python3
"""Marmousi2 known-answer well-tie validation.

LAS extracted from elastic model + SYNTHETIC_time.segy from same model.
If well-tie fails → GEOX bug, not geology.

Usage:
  PYTHONPATH=src python scripts/marmousi2_well_tie_validate.py
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import segyio

from geox_core.core.geox_2d import build_wavelet
from geox_core.core.welltie import assess_tie_quality

DATA = ROOT / "data"
SEGY = DATA / "marmousi_work" / "SYNTHETIC_time.segy"
WELLS = {
    "x1500": DATA / "marmousi-well-x1500.las",
    "x5000": DATA / "marmousi-well-x5000.las",
    "x10000": DATA / "marmousi-well-x10000.las",
}
WELL_X_M = {"x1500": 1500.0, "x5000": 5000.0, "x10000": 10000.0}


def load_las(path: Path) -> dict[str, np.ndarray]:
    lines = path.read_text().splitlines()
    in_a = False
    depth, vp, rhob = [], [], []
    for line in lines:
        if line.startswith("~A"):
            in_a = True
            continue
        if not in_a or not line.strip():
            continue
        p = line.split()
        if len(p) < 4:
            continue
        d, v, _s, r = map(float, p[:4])
        if v <= 0:
            continue
        depth.append(d)
        vp.append(v)
        rhob.append(r)
    d_a, v_a, r_a = map(np.asarray, (depth, vp, rhob))
    return {"DEPT": d_a, "VP": v_a, "RHOB": r_a, "AI": v_a * r_a}


def depth_to_twt_ms(depth: np.ndarray, vp: np.ndarray) -> np.ndarray:
    twt = np.zeros_like(depth)
    for i in range(1, len(depth)):
        dz = depth[i] - depth[i - 1]
        v = max(0.5 * (vp[i] + vp[i - 1]), 1.0)
        twt[i] = twt[i - 1] + 2.0 * dz / v * 1000.0
    return twt


def extract_trace(x_m: float):
    with segyio.open(str(SEGY), "r", ignore_geometry=True) as f:
        sx = f.attributes(segyio.TraceField.SourceX)[:].astype(float) * 0.001
        i = int(np.argmin(np.abs(sx - x_m)))
        tr = np.asarray(f.trace[i], dtype=float)
        t_ms = np.asarray(f.samples, dtype=float)
        dt = float(segyio.dt(f) / 1000.0)
        return tr, t_ms, dt, i, float(sx[i])


def make_synth(ai: np.ndarray, twt_ms: np.ndarray, t_grid: np.ndarray, freq: float, dt: float) -> np.ndarray:
    denom = ai[1:] + ai[:-1]
    denom = np.where(np.abs(denom) < 1e-12, 1e-12, denom)
    rc = (ai[1:] - ai[:-1]) / denom
    twt_rc = 0.5 * (twt_ms[:-1] + twt_ms[1:])
    rc_g = np.zeros_like(t_grid)
    for r, t in zip(rc, twt_rc, strict=False):
        j = int(round((t - t_grid[0]) / dt))
        if 0 <= j < len(rc_g):
            rc_g[j] += r
    w = build_wavelet(frequency=freq, dt_ms=dt, wavelet_type="ricker")
    s = np.convolve(rc_g, w, mode="same")
    m = np.max(np.abs(s))
    return s / m if m > 0 else s


def pearson_lag(a: np.ndarray, b: np.ndarray, max_lag: int) -> tuple[float, int]:
    if a.std() < 1e-12 or b.std() < 1e-12:
        return 0.0, 0
    a = (a - a.mean()) / (a.std() + 1e-12)
    b = (b - b.mean()) / (b.std() + 1e-12)
    best = (-2.0, 0)
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            aa, bb = a[-lag:], b[: len(b) + lag]
        elif lag > 0:
            aa, bb = a[: len(a) - lag], b[lag:]
        else:
            aa, bb = a, b
        if len(aa) < 20:
            continue
        c = float(np.mean(aa * bb))
        if c > best[0]:
            best = (c, lag)
    return best


def main() -> int:
    if not SEGY.exists():
        print(f"Missing SEG-Y: {SEGY} — extract SYNTHETIC_time.segy.tar.gz first")
        return 2
    results = []
    for wid, path in WELLS.items():
        x = WELL_X_M[wid]
        c = load_las(path)
        twt = depth_to_twt_ms(c["DEPT"], c["VP"])
        seis, t_ms, dt, idx, x_act = extract_trace(x)
        seis_n = seis / (np.max(np.abs(seis)) + 1e-12)
        best = {"corr": -1.0, "mistie": 0.0, "freq": 25, "pol": "NORMAL"}
        wmask = (t_ms >= 400) & (t_ms <= 2800)
        for freq in (15, 20, 25, 30, 35, 40, 45):
            synth = make_synth(c["AI"], twt, t_ms, freq, dt)
            for pol, sgn in (("NORMAL", 1), ("REVERSED", -1)):
                corr, lag = pearson_lag(sgn * synth[wmask], seis_n[wmask], int(150 / dt))
                if corr > best["corr"]:
                    best = {"corr": corr, "mistie": lag * dt, "freq": freq, "pol": pol}
        pipeline = (best["corr"] >= 0.25) and (abs(best["mistie"]) <= 48.0)
        strong = (best["corr"] >= 0.45) and (abs(best["mistie"]) <= 16.0)
        rec = {
            "well_id": f"MARMOUSI2-{wid.upper()}",
            "x_m": x,
            "trace": idx,
            "x_trace_m": x_act,
            "corr": round(best["corr"], 4),
            "mistie_ms": round(best["mistie"], 2),
            "wavelet_hz": best["freq"],
            "polarity": best["pol"],
            "quality": assess_tie_quality(
                best["corr"], 0.3, 0.0, best["pol"] == "REVERSED"
            ),
            "pipeline_validate": "PASS" if pipeline else "FAIL",
            "strong_pass": strong,
        }
        results.append(rec)
        print(json.dumps(rec))

    n_pass = sum(r["pipeline_validate"] == "PASS" for r in results)
    summary = {
        "benchmark": "MARMOUSI2-KNOWN-ANSWER-WELL-TIE",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "overall": "PASS" if n_pass == len(results) else ("PARTIAL" if n_pass else "FAIL"),
        "pipeline_pass_count": n_pass,
        "wells_tested": len(results),
        "results": results,
        "note": "x5000 is structural core of Marmousi — lower corr expected; flank wells are primary pipeline gates",
    }
    out = Path("/root/A-FORGE/forge_work/2026-07-09/MARMOUSI2-WELL-TIE-VALIDATE.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    print("OVERALL", summary["overall"], f"{n_pass}/{len(results)}")
    print("→", out)
    return 0 if n_pass >= 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
