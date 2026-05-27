"""
Test Forward Model Synthetic — F2 Physics Guard Verification
═══════════════════════════════════════════════════════════════════════════════
Verifies deterministic 1D convolution, impedance math, and LEM envelope contract.
DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import asyncio
import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from geox_mcp.tools.forward_model_synthetic import geox_forward_model_synthetic


@pytest.mark.asyncio
async def test_forward_model_with_raw_arrays():
    """Synthetic from raw vp/rho/depth arrays."""
    vp = [2000.0, 2200.0, 2500.0, 2400.0, 2600.0]
    rho = [2.1, 2.2, 2.3, 2.2, 2.4]
    depth = [1000.0, 1005.0, 1010.0, 1015.0, 1020.0]

    result = await geox_forward_model_synthetic(vp=vp, rho=rho, depth=depth, wavelet_type="ricker", wavelet_freq=20.0, dt_ms=4.0)

    assert result["execution_status"] == "SUCCESS"
    assert result["claim_state"] == "COMPUTED"
    pa = result["primary_artifact"]
    assert pa["wavelet_type"] == "ricker"
    assert pa["gardner_fallback_used"] is False
    assert "synthetic_trace" in pa
    assert len(pa["synthetic_trace"]) > 0
    assert "ai_profile" in pa
    assert "rc_series" in pa
    assert "twt_axis_ms" in pa
    assert "depth_to_twt_table" in pa

    # LEM envelope checks
    assert "confidence" in result
    assert "level" in result["confidence"]
    assert "sensitivity_to" in result["confidence"]
    assert "equations_used" in result["provenance"]
    assert "AI = Vp × ρ" in result["provenance"]["equations_used"]
    assert "physics_guard" in result
    assert result["physics_guard"]["guard_passed"] is True
    assert "metabolic" in result
    print("test_forward_model_with_raw_arrays: PASSED")


def test_forward_model_missing_input():
    """Fail-closed on missing inputs."""
    result = asyncio.run(geox_forward_model_synthetic(vp=[], rho=[], depth=[]))  # sync test — asyncio.run OK
    assert result["execution_status"] == "ERROR"
    assert result["claim_state"] == "NO_VALID_EVIDENCE"
    print("test_forward_model_missing_input: PASSED")


@pytest.mark.asyncio
async def test_forward_model_impedance_bounds():
    """F2: Verify AI = Vp × ρ within epsilon."""
    vp = [2000.0, 2500.0]
    rho = [2.0, 2.5]
    depth = [1000.0, 1005.0]

    result = await geox_forward_model_synthetic(vp=vp, rho=rho, depth=depth, output_format="full")
    ai = np.array(result["primary_artifact"]["ai_profile"])
    # AI in SI units: rho (g/cc) * 1000 = kg/m3; vp in m/s
    # AI = 2.0*1000 * 2000 = 4,000,000
    # AI = 2.5*1000 * 2500 = 6,250,000
    expected = np.array([4_000_000.0, 6_250_000.0])
    assert np.allclose(ai, expected, atol=1e-3), f"AI mismatch: {ai} vs {expected}"
    print("test_forward_model_impedance_bounds: PASSED")


@pytest.mark.asyncio
async def test_forward_model_rc_zero_for_uniform():
    """F2: Uniform AI → RC ≈ 0."""
    vp = [2000.0, 2000.0, 2000.0]
    rho = [2.0, 2.0, 2.0]
    depth = [1000.0, 1005.0, 1010.0]

    result = await geox_forward_model_synthetic(vp=vp, rho=rho, depth=depth, output_format="full")
    rc = np.array(result["primary_artifact"]["rc_series"])
    # RC should be near zero for uniform impedance
    assert np.allclose(rc[1:], 0.0, atol=1e-9), f"Uniform AI should yield RC≈0, got {rc}"
    print("test_forward_model_rc_zero_for_uniform: PASSED")


if __name__ == "__main__":
    asyncio.run(test_forward_model_with_raw_arrays())
    test_forward_model_missing_input()
    asyncio.run(test_forward_model_impedance_bounds())
    asyncio.run(test_forward_model_rc_zero_for_uniform())
    print("\nAll forward_model_synthetic tests PASSED.")
