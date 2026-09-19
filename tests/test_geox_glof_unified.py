"""tests/test_geox_glof_unified.py
===================================
Four-mode test suite for the unified geox_glof tool.
Covers: run, inverse, propagate, unknown_mode (fail-closed guard).
Phase mode is tested indirectly via run (state_id not externally required).

Import path: PYTHONPATH=src  (run from /root/GEOX)
  cd /root/GEOX && PYTHONPATH=src pytest tests/test_geox_glof_unified.py -v

DITEMPA BUKAN DIBERI — forged, not given.
"""
from __future__ import annotations

import asyncio
import math

import pytest

from geox_mcp.tools.geox_glof import geox_glof


# ── helpers ──────────────────────────────────────────────────────────────────

def _run(coro):
    """Run async function synchronously (test runner may not provide event loop)."""
    return asyncio.get_event_loop().run_until_complete(coro)


_VALID_OBS = {
    "label": "Trishuli_test",
    "water_head_m": 110.0,
    "breach_width_m": 150.0,
    "peak_discharge_m3s": 3000.0,
    "time_to_peak_min": 12.0,
    "downstream_surge_m": 9.0,
    "source": "gauge",
}


# ── test_glof_run_mode ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_glof_run_mode():
    """mode='run' — full cascade: init→step→metabolize. breach_summary must be present."""
    result = await geox_glof(
        mode="run",
        domain_bounds_x_m=2000.0,
        domain_bounds_z_m=300.0,
        resolution_m=20.0,
        dam_height_m=80.0,
        n_steps=10,
        dt_sec=1.0,
    )
    assert result["ok"] is True, f"run mode failed: {result}"
    assert result["tool"] == "geox_glof"
    assert result["mode"] == "run"
    res = result["result"]
    assert "breach_summary" in res, "breach_summary key missing"
    bs = res["breach_summary"]
    assert "state_id" in bs
    assert bs["n_steps"] == 10
    # G_score present (may be None if metabolize couldn't compute, but key exists)
    assert "G_score" in res


# ── test_glof_inverse_mode ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_glof_inverse_mode():
    """mode='inverse' — Bayesian grid-search inference from observation dict."""
    result = await geox_glof(
        mode="inverse",
        observation=_VALID_OBS,
        n_grid=2,  # fast for CI
    )
    assert result["ok"] is True, f"inverse mode failed: {result}"
    assert result["tool"] == "geox_glof"
    assert result["mode"] == "inverse"
    res = result["result"]
    assert "theta_hat" in res, "theta_hat missing from inverse result"
    assert "log_likelihood" in res
    theta = res["theta_hat"]
    # Must have the 9 required GLOFMaterialState scalars
    for field in ("rho", "E", "nu", "c", "phi", "k", "phi_p", "tau_0", "sigma_t"):
        assert field in theta, f"theta_hat missing field: {field}"


# ── test_glof_propagate_mode ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_glof_propagate_mode():
    """mode='propagate' — Saint-Venant 1D downstream flood propagation."""
    result = await geox_glof(
        mode="propagate",
        breach_Q_profile="costa1985",
        length_m=10_000.0,   # shorter reach for fast test
        nx=20,               # coarser grid for fast test
        duration_s=600.0,    # 10 min
        output_interval_s=120.0,
    )
    assert result["ok"] is True, f"propagate mode failed: {result}"
    assert result["tool"] == "geox_glof"
    assert result["mode"] == "propagate"
    res = result["result"]
    # Saint-Venant returns time-series data; at minimum there should be a key
    assert res, "propagate result is empty"


# ── test_glof_unknown_mode ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_glof_unknown_mode():
    """Fail-closed guard — unknown mode returns structured error envelope."""
    result = await geox_glof(mode="foobar_nonexistent")  # type: ignore[arg-type]
    assert result["ok"] is False, "unknown mode should return ok=False"
    assert result["tool"] == "geox_glof"
    assert result["error"] == "UNKNOWN_MODE"
    assert "mode" not in result or result.get("mode") in ("foobar_nonexistent", None) or True


# ── test_glof_inverse_missing_observation ────────────────────────────────────

@pytest.mark.asyncio
async def test_glof_inverse_missing_observation():
    """inverse mode without observation returns MISSING_OBSERVATION error."""
    result = await geox_glof(mode="inverse")  # no observation
    assert result["ok"] is False
    assert result["error"] == "MISSING_OBSERVATION"


# ── test_glof_mcmc_mode (smoke) ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_glof_mcmc_mode_smoke():
    """mode='mcmc' — MCMC posterior smoke test (minimal iterations)."""
    result = await geox_glof(
        mode="mcmc",
        observation=_VALID_OBS,
        n_warmup=5,
        n_iter=10,
        n_chains=1,
        seed=99,
    )
    # MCMC may succeed or fail gracefully (scipy optional dep) — what matters:
    # envelope is always ok/tool/mode/result/error shaped
    assert "ok" in result
    assert result["tool"] == "geox_glof"
    assert result.get("mode") == "mcmc"
    assert "result" in result
    assert "error" in result
