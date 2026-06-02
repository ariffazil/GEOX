import pytest
import numpy as np
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from geox_mcp.tools.seismic_well_tie import geox_seismic_well_tie_compute, geox_time_depth_anchor
from geox_mcp.tools.seismic_vision import geox_vision_time_to_depth
from geox_core.core.physics_guard import PhysicsGuard

@pytest.fixture
def mock_helpers():
    """Mock all helpers that the seismic well-tie / time-depth tools call.

    Provides:
      - _artifact_exists returns True (artifact present)
      - _get_artifact returns minimal checkshot data (≥2 points, zero drift)
      - _extract_well_curves_from_artifact returns physically-plausible curves
        (Vp in Sabah Basin range, so the velocity sanity check passes)
    """
    depth = np.linspace(0, 1000, 100)
    # Constant Vp=2000 m/s → sonic TWT = 2*d/2000*1000 = d (ms), matches checkshot exactly
    vp = np.full(100, 2000.0)
    rho = np.linspace(2.0, 2.4, 100)   # typical density g/cc
    vsh = np.full(100, 0.3)
    curves = {"rho": rho, "vp": vp, "vsh": vsh, "depth": depth}
    # Checkshot: linear twt = depth (Vavg=2000 m/s) → zero drift against sonic integration
    cs_data = [[0.0, 0.0], [500.0, 500.0], [1000.0, 1000.0]]
    cs_artifact = {"data": cs_data}

    def _get_artifact(artifact_id):
        if artifact_id == "cs_1":
            return cs_artifact
        # well artifact path — return curves directly so _extract can short-circuit
        return {**curves, "data": None}

    with patch('geox_mcp.tools.seismic_well_tie._artifact_exists', return_value=True), \
         patch('geox_mcp.tools.seismic_well_tie._get_artifact', side_effect=_get_artifact), \
         patch('geox_mcp.tools.seismic_well_tie._extract_well_curves_from_artifact', return_value=curves), \
         patch('geox_mcp.tools.seismic_vision.GEOXVisionDepthEngine') as mock_engine:
        yield mock_engine

@pytest.mark.asyncio
async def test_geox_seismic_well_tie_compute_success(mock_helpers):
    """F2: Verify well-tie deterministic computation."""
    result = await geox_seismic_well_tie_compute(
        well_id="well_1",
        volume_ref="seismic_A"
    )
    assert result["execution_status"] == "SUCCESS"
    assert result["claim_state"] == "QUALIFY"
    assert "max_cross_correlation" in result["derived"]
    assert result["audit_receipt"]["deterministic_engine"] == "geox-convolution-v2"

@pytest.mark.asyncio
async def test_geox_time_depth_anchor_success(mock_helpers):
    """F2: Verify T-D anchoring logic."""
    result = await geox_time_depth_anchor(
        well_id="well_1",
        checkshot_ref="cs_1",
        drift_threshold_ms=25.0
    )
    assert result["execution_status"] == "SUCCESS"
    assert result["claim_state"] == "SEAL"
    assert result["audit_receipt"]["authority"] == "F2_PHYSICS_GUARD"

@pytest.mark.asyncio
async def test_geox_vision_time_to_depth_anti_hantu():
    """F9: Verify JITU circuit breaker blocks generative mode."""
    with pytest.raises(PermissionError, match="\[JITU\]"):
        await geox_vision_time_to_depth(
            image_path="any.jpg",
            max_time_ms=3000.0,
            max_cmp=5000.0,
            v_rms_anchor=[2000],
            execution_mode="generative"
        )

def test_physics_guard_sabah_bounds():
    """F2: Verify Sabah Basin velocity boundaries (1480-5500 m/s)."""
    guard = PhysicsGuard()
    
    # Valid
    v_ok = np.array([1500.0, 3000.0, 5400.0])
    z_ok = np.array([0, 500, 1000])
    res_ok = guard.validate_velocity_sanity(v_ok, z_ok)
    assert res_ok.status == "PASS"
    
    # Invalid (Upper Bound)
    v_bad_up = np.array([1500.0, 5600.0])
    res_bad_up = guard.validate_velocity_sanity(v_bad_up, z_ok[:2])
    assert res_bad_up.status == "PHYSICS_VIOLATION"
    assert any(v.parameter == "velocity_absolute" and v.max_bound == 5500.0 for v in res_bad_up.violations)

    # Invalid (Lower Bound)
    v_bad_lo = np.array([1400.0, 3000.0])
    res_bad_lo = guard.validate_velocity_sanity(v_bad_lo, z_ok[:2])
    assert res_bad_lo.status == "PHYSICS_VIOLATION"
    assert any(v.parameter == "velocity_absolute" and v.min_bound == 1480.0 for v in res_bad_lo.violations)

def test_reflectivity_deterministic_math():
    """F2: Verify exact reflectivity computation accuracy."""
    from geox_core.engines.seismic.well_tie import calculate_acoustic_impedance, calculate_reflectivity
    
    rho = np.array([2000.0, 2200.0])
    vp = np.array([2000.0, 2500.0])
    z = calculate_acoustic_impedance(rho, vp)
    r = calculate_reflectivity(z)
    
    expected_r0 = (5500000.0 - 4000000.0) / (5500000.0 + 4000000.0)
    assert abs(r[0] - expected_r0) < 1e-7
