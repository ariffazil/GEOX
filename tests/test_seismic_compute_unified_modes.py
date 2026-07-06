import sys
from pathlib import Path
import numpy as np
from unittest.mock import patch

# Ensure /root/geox/src is in path
src_dir = Path(__file__).resolve().parents[1] / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pytest
from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute

@pytest.fixture
def mock_helpers():
    depth = np.linspace(0, 1000, 100)
    vp = np.full(100, 2000.0)
    rho = np.linspace(2.0, 2.4, 100)
    vsh = np.full(100, 0.3)
    curves = {"rho": rho, "vp": vp, "vsh": vsh, "depth": depth}
    cs_data = [[0.0, 0.0], [500.0, 500.0], [1000.0, 1000.0]]
    cs_artifact = {"data": cs_data}

    def _get_artifact(artifact_id):
        if artifact_id == "cs_1":
            return cs_artifact
        return {**curves, "data": None}

    with patch('geox_mcp.tools.seismic_well_tie._artifact_exists', return_value=True), \
         patch('geox_mcp.tools.seismic_well_tie._get_artifact', side_effect=_get_artifact), \
         patch('geox_mcp.tools.seismic_well_tie._extract_well_curves_from_artifact', return_value=curves):
        yield

@pytest.mark.asyncio
async def test_seismic_compute_unified_ingest(mock_helpers):
    # Test delegate to ingest (tengok)
    res = await geox_seismic_compute(
        mode="tengok",
        segy_metadata={"volume_ref": "test_volume.sgy"}
    )
    assert "status" in res or "execution_status" in res

@pytest.mark.asyncio
async def test_seismic_compute_unified_interpret(mock_helpers):
    # Test delegate to interpret (agak)
    amplitude = list(1000.0 + 0.5 * np.arange(100, dtype=float))
    res = await geox_seismic_compute(
        mode="agak",
        volume_ref="test_volume.sgy",
        attribute_data={"amplitude": amplitude},
        depth=list(np.arange(1000, 1100, 1.0))
    )
    assert "derived" in res or "execution_status" in res or "status" in res

@pytest.mark.asyncio
async def test_seismic_compute_unified_cabar(mock_helpers):
    # Test delegate to anomalous_contrast (cabar)
    res = await geox_seismic_compute(
        mode="cabar",
        ai_profile=[4e6, 4.2e6, 6e6],
        ac_depth=[990, 1000, 1005],
        formation_tops={"top_a": 1000.0}
    )
    assert "anomalous_contrast" in res

@pytest.mark.asyncio
async def test_seismic_compute_unified_sahkan(mock_helpers):
    # Test delegate to well_tie (sahkan)
    res = await geox_seismic_compute(
        mode="sahkan",
        well_id="well_1",
        volume_ref="vol_1",
        extraction_window_ms=100.0,
        frequency_band=(10, 50),
        wavelet_type="ricker",
        apply_gardner_fallback=False,
        apply_anisotropy_correction=False,
        q_factor=100.0
    )
    assert "execution_status" in res or "status" in res
