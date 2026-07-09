"""GEOX 1D MCP surface — TD calibrate, mistie RMS, wavelet LS (headless GEOX-001)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from geox_core.engines.seismic.wavelet_extract import extract_wavelet_least_squares
from geox_core.physics.parameters import ricker_wavelet
from geox_mcp.tools.well_1d_surface import (
    geox_wavelet_extract_least_squares,
    geox_well_seismic_mistie_rms,
    geox_well_time_depth_calibrate,
)

TB1 = Path("/root/geox/benchmark-001/data")
LAS = TB1 / "GEOX-001-TB1.las"
CS = TB1 / "GEOX-001-TB1_checkshot.csv"


@pytest.mark.skipif(not LAS.exists() or not CS.exists(), reason="TB1 fixtures missing")
@pytest.mark.asyncio
async def test_time_depth_calibrate_tb1():
    out = await geox_well_time_depth_calibrate(
        las_path=str(LAS),
        checkshot_path=str(CS),
        method="linear",
        residual_threshold_pct=15.0,
        well_id="GEOX-001-TB1",
    )
    assert out["status"] == "success"
    r = out["result"]
    assert r["method"]
    assert isinstance(r["twt_ms"], list) and len(r["twt_ms"]) > 10
    assert isinstance(r["coefficients"], list)
    assert "physics_guard" in r
    assert r["resource_uri"].startswith("geox://well/")
    assert r["vault_receipt"]["vault999_status"] == "DRAFT_ONLY"
    # pure JSON types
    import json

    json.dumps(out)


@pytest.mark.asyncio
async def test_mistie_rms_gate_seal_and_hold():
    n = 200
    dt = 4.0
    t = np.arange(n)
    # synthetic spike train
    synth = np.zeros(n)
    synth[50] = 1.0
    synth[80] = -0.6
    # seismic = delayed copy
    lag = 3  # 12 ms
    seis = np.roll(synth, lag)
    out = await geox_well_seismic_mistie_rms(
        synthetic_trace=synth.tolist(),
        seismic_trace=seis.tolist(),
        dt_ms=dt,
        threshold_ms=25.0,
        well_id="TEST-WELL",
    )
    assert out["status"] == "success"
    r = out["result"]
    assert r["verdict"] in ("SEAL", "HOLD", "VOID")
    assert r["rms_mistie_ms"] <= 25.0 or r["verdict"] == "HOLD"
    assert abs(r["optimal_lag_ms"]) <= 50.0
    assert r["resource_uri"].startswith("geox://")

    # force HOLD with large lag
    seis2 = np.roll(synth, 20)  # 80 ms
    out2 = await geox_well_seismic_mistie_rms(
        synthetic_trace=synth.tolist(),
        seismic_trace=seis2.tolist(),
        dt_ms=dt,
        threshold_ms=25.0,
        max_lag_ms=100.0,
        well_id="TEST-HOLD",
    )
    assert out2["result"]["verdict"] in ("HOLD", "SEAL", "VOID")
    # with 80ms lag should HOLD under 25ms gate
    assert out2["result"]["rms_mistie_ms"] > 25.0 or out2["result"]["verdict"] == "HOLD"


@pytest.mark.asyncio
async def test_wavelet_extract_least_squares():
    n = 256
    dt = 4.0
    # true ricker wavelet
    w_true = ricker_wavelet(25.0, dt / 1000.0)
    # reflectivity spikes
    r = np.zeros(n)
    r[40] = 0.2
    r[90] = -0.15
    r[140] = 0.1
    s = np.convolve(r, w_true, mode="same")
    s = s + 0.01 * np.random.default_rng(0).normal(size=n)

    out = await geox_wavelet_extract_least_squares(
        reflectivity_series=r.tolist(),
        seismic_trace=s.tolist(),
        wavelet_length_ms=100.0,
        epsilon=1e-3,
        dt_ms=dt,
        well_id="TEST-WAV",
    )
    assert out["status"] == "success"
    res = out["result"]
    assert len(res["wavelet"]) >= 5
    assert res["condition_number"] > 0
    assert res["epsilon_used"] > 0
    assert res["phase_class"] in ("zero", "minimum", "mixed", "unknown")
    assert res["resource_uri"].startswith("geox://")
    # engine unit
    eng = extract_wavelet_least_squares(r, s, dt_ms=dt, wavelet_length_ms=100.0)
    assert len(eng["wavelet"]) > 0


def test_registry_has_three_tools():
    from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, SURFACE_TOOLS

    for t in (
        "geox_well_time_depth_calibrate",
        "geox_well_seismic_mistie_rms",
        "geox_wavelet_extract_least_squares",
    ):
        assert t in SURFACE_TOOLS
        assert t in CANONICAL_PUBLIC_TOOLS
    assert len(CANONICAL_PUBLIC_TOOLS) == 73  # 2026-07-09: bumped 72→73 for bid_round_screener (MBR 2026 multi-block)
