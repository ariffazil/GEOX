"""Tests for display-derived proxy extraction.

Verifies that:
- Proxy extraction requires calibration witness
- HOLD witness → HOLD result
- Wrong representation → HOLD in native-only paths
- Proxy output is labeled DISPLAY_DERIVED_PROXY
- Prohibited uses are explicit

DITEMPA BUKAN DIBERI.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_synthetic_image(width=200, height=150):
    """Create a minimal synthetic seismic-like image (dark gray on white)."""
    img = np.ones((height, width, 3), dtype=np.uint8) * 240  # white background
    # Add a dark panel region (simulating seismic section)
    img[20:130, 30:170, :] = 80  # dark gray
    # Add some variation to simulate seismic amplitudes
    for col in range(30, 170):
        amplitude = int(80 + 40 * np.sin((col - 30) * 0.1))
        img[20:130, col, :] = amplitude
    return img


def _make_calibration_witness(status="VALID"):
    """Create a minimal calibration witness dict."""
    return {
        "calibration_witness_id": "calw_test_proxy_001",
        "status": status,
        "evidence_ref": {"dataset_id": "test_image", "classification": "synthetic"},
        "display_domain": {"vertical_domain": "TWT", "vertical_units": "ms"},
        "axis_calibration_h": {
            "anchor_a": {"pixel_x": 0, "pixel_y": 0},
            "anchor_b": {"pixel_x": 100, "pixel_y": 0},
        },
        "axis_calibration_v": {
            "anchor_a": {"pixel_x": 0, "pixel_y": 0, "value": 0},
            "anchor_b": {"pixel_x": 0, "pixel_y": 100, "value": 2000},
        },
    }


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_proxy_requires_calibration():
    """No calibration witness → HOLD."""
    from geox_mcp.tools.display_proxy import geox_extract_display_proxy

    result = await geox_extract_display_proxy(image_path="/nonexistent")
    assert result["status"] == "HOLD"
    assert result["reason"] == "CALIBRATION_REQUIRED"


@pytest.mark.asyncio
async def test_proxy_hold_witness_returns_hold():
    """HOLD calibration witness → HOLD result."""
    from geox_mcp.tools.display_proxy import geox_extract_display_proxy

    witness = _make_calibration_witness(status="HOLD")
    result = await geox_extract_display_proxy(
        image_path="/nonexistent",
        calibration_witness_ref=witness,
    )
    assert result["status"] == "HOLD"
    assert result["reason"] == "WITNESS_HOLD"


@pytest.mark.asyncio
async def test_proxy_requires_image():
    """No image → VOID."""
    from geox_mcp.tools.display_proxy import geox_extract_display_proxy

    witness = _make_calibration_witness()
    result = await geox_extract_display_proxy(calibration_witness_ref=witness)
    assert result["status"] == "VOID"
    assert result["reason"] == "NO_IMAGE"


@pytest.mark.asyncio
async def test_proxy_output_labeled_display_derived(tmp_path):
    """Successful extraction labels output as DISPLAY_DERIVED_PROXY."""
    from geox_mcp.tools.display_proxy import geox_extract_display_proxy
    from PIL import Image

    img_array = _make_synthetic_image()
    img = Image.fromarray(img_array)
    img_path = str(tmp_path / "test_seismic.png")
    img.save(img_path)

    witness = _make_calibration_witness()
    result = await geox_extract_display_proxy(
        image_path=img_path,
        calibration_witness_ref=witness,
    )

    assert result["status"] == "OK"
    assert result["representation"] == "DISPLAY_DERIVED_PROXY"
    assert result["data_representation"] == "DISPLAY_DERIVED_PROXY"
    assert result["amplitude_integrity"] == "DISPLAY_TRANSFORMED"
    assert result["phase_integrity"] == "DISPLAY_TRANSFORMED"
    assert result["epistemic_tag"] == "DER"


@pytest.mark.asyncio
async def test_proxy_prohibited_uses_present(tmp_path):
    """Prohibited uses must include AVO, amplitude preservation, native well-tie."""
    from geox_mcp.tools.display_proxy import geox_extract_display_proxy
    from PIL import Image

    img_array = _make_synthetic_image()
    img = Image.fromarray(img_array)
    img_path = str(tmp_path / "test_seismic.png")
    img.save(img_path)

    witness = _make_calibration_witness()
    result = await geox_extract_display_proxy(
        image_path=img_path,
        calibration_witness_ref=witness,
    )

    prohibited = result["prohibited_uses"]
    assert "quantitative_amplitude_analysis" in prohibited
    assert "avo_classification" in prohibited
    assert "native_well_tie_acceptance" in prohibited
    assert "amplitude_preservation_validation" in prohibited
    assert "native_trace_substitution" in prohibited


@pytest.mark.asyncio
async def test_proxy_limitations_stated(tmp_path):
    """Limitations must document why pixel values ≠ amplitudes."""
    from geox_mcp.tools.display_proxy import geox_extract_display_proxy
    from PIL import Image

    img_array = _make_synthetic_image()
    img = Image.fromarray(img_array)
    img_path = str(tmp_path / "test_seismic.png")
    img.save(img_path)

    witness = _make_calibration_witness()
    result = await geox_extract_display_proxy(
        image_path=img_path,
        calibration_witness_ref=witness,
    )

    assert len(result["limitations"]) >= 4
    assert any("NOT reflection amplitude" in l for l in result["limitations"])
    assert any("AGC" in l or "display transform" in l.lower() for l in result["limitations"])


@pytest.mark.asyncio
async def test_proxy_shape_valid(tmp_path):
    """Proxy array shape should be (n_traces, n_samples)."""
    from geox_mcp.tools.display_proxy import geox_extract_display_proxy
    from PIL import Image

    img_array = _make_synthetic_image(width=300, height=200)
    img = Image.fromarray(img_array)
    img_path = str(tmp_path / "test_seismic.png")
    img.save(img_path)

    witness = _make_calibration_witness()
    result = await geox_extract_display_proxy(
        image_path=img_path,
        calibration_witness_ref=witness,
    )

    assert result["status"] == "OK"
    shape = result["proxy_shape"]
    assert shape["n_traces"] > 0
    assert shape["n_samples"] > 0
    assert shape["n_traces"] < 300  # panel is subset of image
    assert shape["n_samples"] < 200


def test_display_proxy_in_native_rejection():
    """Native-only paths must reject DISPLAY_DERIVED_PROXY."""
    from geox_core.seismic_pipeline.data_representation import (
        SeismicDataClassification, DataRepresentation, AmplitudeIntegrity
    )

    proxy = SeismicDataClassification(
        data_representation=DataRepresentation.DISPLAY_DERIVED_PROXY,
        amplitude_integrity=AmplitudeIntegrity.DISPLAY_TRANSFORMED,
    )

    assert "quantitative_amplitude_analysis" in proxy.prohibited_uses
    assert "avo_classification" in proxy.prohibited_uses
    assert "native_trace_well_tie_acceptance" in proxy.prohibited_uses
    assert "seismic_inversion" in proxy.prohibited_uses
    assert proxy.quality_coverage_cap == 0.25
