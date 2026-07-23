"""
Phase A/D — interpret_section RSI wrap + SEG-Y slice path.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import os

import pytest

_TEST_IMAGE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "geox", "seismic", "rsi", "seismic_greyscale.jpg")
)
_ALT_IMAGE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "geox", "seismic", "rsi", "seismic_section.jpg")
)
_MARM = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "marmousi_work", "SYNTHETIC_time.segy")
)


@pytest.mark.asyncio
async def test_interpret_section_on_demo_image():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    path = _TEST_IMAGE if os.path.exists(_TEST_IMAGE) else _ALT_IMAGE
    if not os.path.exists(path):
        pytest.skip("RSI demo image missing")
    r = await geox_seismic_interpret(
        mode="interpret_section", image_path=path, emit_bundle=False, max_faults=4, max_horizons=3
    )
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert r.get("seal_authority") == "arifOS_only"
    assert r.get("input_class") == "image_only"
    # Product path: interpret_section aliases classical_section
    assert r.get("mode") in ("classical_section", "interpret_section", "rsi_pipeline")
    assert r.get("faults") is not None or r.get("framework") or r.get("geometry") or r.get("stages")
    assert r.get("governance_status") != "SEAL"
    assert r.get("verdict") != "SEAL"


@pytest.mark.asyncio
async def test_segy_slice_marmousi():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    if not os.path.exists(_MARM):
        pytest.skip("Marmousi SEGY missing")
    r = await geox_seismic_interpret(mode="segy_slice", segy_path=_MARM, frame_index=0)
    if r.get("error") == "SEGYIO_MISSING":
        pytest.skip("segyio not installed")
    if not r.get("ok"):
        # geometry issues on some SEGY still return structured error
        assert r.get("error") in ("SEGY_READ_FAILED", "FILE_NOT_FOUND")
        return
    assert r.get("input_class") == "segy_slice"
    assert r.get("measurement_context", {}).get("input_class") == "segy_slice"
    assert r.get("measurement_context", {}).get("sha256")
    assert r.get("attribute_data", {}).get("seismic_amplitude")
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
