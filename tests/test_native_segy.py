"""Tests for native SEG-Y registration, QC, and trace extraction.

Verifies:
- Registration validates file, authority, classification
- HOLD for unverified authority
- VOID for missing file
- Header QC returns parsed fields
- Native trace extraction requires registered source
- DISPLAY_DERIVED_PROXY rejected from native-only paths
- Boundary enforcement

DITEMPA BUKAN DIBERI.
"""

import os
import pytest
import numpy as np


# ── Minimal SEG-Y Fixture Generator ──────────────────────────────────────────


def _create_minimal_segy(path: str, n_traces=5, n_samples=100, sample_interval_us=4000):
    """Create a minimal valid SEG-Y file using segyio.

    Produces a file with:
    - 3200-byte textual header
    - 400-byte binary header (with essential fields)
    - n_traces trace headers (240 bytes each) + trace data
    """
    import segyio

    spec = segyio.spec()
    spec.format = 5  # IEEE float 32
    spec.samples = np.arange(n_samples) * (sample_interval_us / 1e6)  # in seconds
    spec.ilines = np.arange(100, 100 + n_traces, dtype=np.intc)
    spec.xlines = np.arange(200, 200 + n_traces, dtype=np.intc)

    with segyio.create(path, spec) as f:
        for i in range(n_traces):
            f.header[i] = {
                segyio.su.iline: 100 + i,
                segyio.su.xline: 200 + i,
            }
            f.trace[i] = np.random.randn(n_samples).astype(np.float32)


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_missing_file():
    """Registration with non-existent file → VOID."""
    from geox_mcp.tools.native_segy import geox_register_native_source

    result = await geox_register_native_source(source_uri="/nonexistent/file.sgy")
    assert result["status"] == "VOID"
    assert "FILE_NOT_FOUND" in result["reason"]


@pytest.mark.asyncio
async def test_register_no_uri():
    """Registration without source_uri → VOID."""
    from geox_mcp.tools.native_segy import geox_register_native_source

    result = await geox_register_native_source(source_uri="")
    assert result["status"] == "VOID"
    assert "SOURCE_URI_REQUIRED" in result["reason"]


@pytest.mark.asyncio
async def test_register_invalid_authority(tmp_path):
    """Registration with invalid authority → VOID."""
    from geox_mcp.tools.native_segy import geox_register_native_source

    segy_path = str(tmp_path / "test_auth.sgy")
    _create_minimal_segy(segy_path)

    result = await geox_register_native_source(
        source_uri=segy_path,
        authority="FAKE_AUTHORITY",
    )
    assert result["status"] == "VOID"
    assert "INVALID_AUTHORITY" in result["reason"]


@pytest.mark.asyncio
async def test_register_synthetic_fixture(tmp_path):
    """Registration of a valid synthetic SEG-Y → REGISTERED."""
    from geox_mcp.tools.native_segy import geox_register_native_source

    segy_path = str(tmp_path / "test.sgy")
    _create_minimal_segy(segy_path)

    result = await geox_register_native_source(
        source_uri=segy_path,
        classification="synthetic",
        authority="SYNTHETIC_VERIFIED",
    )
    assert result["status"] == "REGISTERED"
    assert result["source_id"].startswith("src_")
    assert result["classification"] == "synthetic"
    assert result["authority"] == "SYNTHETIC_VERIFIED"
    assert result["manifest"]["trace_count"] is not None
    assert result["manifest"]["trace_count"] >= 1
    assert result["manifest"]["samples_per_trace"] is not None
    assert result["manifest"]["samples_per_trace"] >= 1
    assert result["manifest"]["sample_interval_us"] is not None
    assert result["manifest"]["sample_interval_us"] > 0


@pytest.mark.asyncio
async def test_register_operator_without_actor_downgrades():
    """OPERATOR_APPROVED without registered_by → downgraded to UNVERIFIED."""
    from geox_mcp.tools.native_segy import geox_register_native_source

    segy_path = "/tmp/test_op.sgy"
    if not os.path.exists(segy_path):
        _create_minimal_segy(segy_path)

    result = await geox_register_native_source(
        source_uri=segy_path,
        authority="OPERATOR_APPROVED",
        # registered_by is None
    )
    assert result["status"] == "REGISTERED"
    assert result["authority"] == "UNVERIFIED"  # downgraded


@pytest.mark.asyncio
async def test_extract_unregistered_source():
    """Extraction from unregistered source → HOLD."""
    from geox_mcp.tools.native_segy import geox_extract_native_trace

    result = await geox_extract_native_trace(source_id="src_nonexistent")
    assert result["status"] == "HOLD"
    assert result["reason"] == "SOURCE_NOT_REGISTERED"


@pytest.mark.asyncio
async def test_extract_unverified_authority(tmp_path):
    """Extraction from UNVERIFIED source → HOLD."""
    from geox_mcp.tools.native_segy import geox_register_native_source, geox_extract_native_trace

    segy_path = str(tmp_path / "test_unv.sgy")
    _create_minimal_segy(segy_path)

    reg = await geox_register_native_source(
        source_uri=segy_path,
        authority="UNVERIFIED",
    )
    assert reg["status"] == "REGISTERED"

    result = await geox_extract_native_trace(
        source_id=reg["source_id"],
        trace_index=0,
    )
    assert result["status"] == "HOLD"
    assert result["reason"] == "INSUFFICIENT_AUTHORITY"


@pytest.mark.asyncio
async def test_extract_valid_trace(tmp_path):
    """Extraction from registered, authorized source → OK with NATIVE_TRACE."""
    from geox_mcp.tools.native_segy import geox_register_native_source, geox_extract_native_trace

    segy_path = str(tmp_path / "test_ok.sgy")
    _create_minimal_segy(segy_path, n_traces=5, n_samples=100)

    reg = await geox_register_native_source(
        source_uri=segy_path,
        authority="SYNTHETIC_VERIFIED",
        classification="synthetic",
    )
    assert reg["status"] == "REGISTERED"

    result = await geox_extract_native_trace(
        source_id=reg["source_id"],
        trace_index=2,
    )
    assert result["status"] == "OK"
    assert result["representation"] == "NATIVE_TRACE"
    assert result["epistemic_tag"] == "OBS"
    assert result["trace_ref"]["trace_index"] == 2
    assert result["trace_ref"]["n_samples"] == 100
    assert result["trace_ref"]["sample_interval_us"] > 0  # segyio stores actual interval
    assert result["trace_ref"]["sample_interval_ms"] > 0
    assert result["trace_data_summary"]["n_samples"] == 100


@pytest.mark.asyncio
async def test_extract_invalid_trace_index(tmp_path):
    """Extraction with out-of-range trace index → VOID."""
    from geox_mcp.tools.native_segy import geox_register_native_source, geox_extract_native_trace

    segy_path = str(tmp_path / "test_idx.sgy")
    _create_minimal_segy(segy_path, n_traces=3)

    reg = await geox_register_native_source(
        source_uri=segy_path,
        authority="PUBLIC_VERIFIED",
    )

    result = await geox_extract_native_trace(
        source_id=reg["source_id"],
        trace_index=999,
    )
    assert result["status"] == "VOID"
    assert "TRACE_INDEX_OUT_OF_RANGE" in result["reason"]


@pytest.mark.asyncio
async def test_extract_no_locator():
    """Extraction without trace locator → VOID."""
    from geox_mcp.tools.native_segy import geox_register_native_source, geox_extract_native_trace

    segy_path = str(tmp_path / "test_noloc.sgy") if (tmp_path := __import__("pathlib").Path("/tmp")) else "/tmp/test_noloc.sgy"
    if not os.path.exists(segy_path):
        _create_minimal_segy(segy_path)

    from geox_mcp.tools.native_segy import geox_register_native_source
    reg = await geox_register_native_source(
        source_uri=segy_path,
        authority="PUBLIC_VERIFIED",
    )

    result = await geox_extract_native_trace(source_id=reg["source_id"])
    assert result["status"] == "VOID"
    assert "TRACE_LOCATOR_REQUIRED" in result["reason"]


@pytest.mark.asyncio
async def test_list_registered_sources(tmp_path):
    """List sources shows registered entries."""
    from geox_mcp.tools.native_segy import geox_register_native_source, geox_list_registered_sources

    segy_path = str(tmp_path / "test_list.sgy")
    _create_minimal_segy(segy_path)

    await geox_register_native_source(
        source_uri=segy_path,
        authority="SYNTHETIC_VERIFIED",
    )

    result = await geox_list_registered_sources()
    assert result["n_sources"] >= 1
    assert any(s["authority"] == "SYNTHETIC_VERIFIED" for s in result["sources"])


def test_native_trace_rejects_display_proxy():
    """DISPLAY_DERIVED_PROXY must be rejected from native-only paths."""
    from geox_core.seismic_pipeline.data_representation import (
        DataRepresentation, AmplitudeIntegrity, SeismicDataClassification,
    )

    proxy = SeismicDataClassification(
        data_representation=DataRepresentation.DISPLAY_DERIVED_PROXY,
        amplitude_integrity=AmplitudeIntegrity.DISPLAY_TRANSFORMED,
    )
    native = SeismicDataClassification(
        data_representation=DataRepresentation.NATIVE_TRACE,
        amplitude_integrity=AmplitudeIntegrity.CONDITIONAL,
    )

    # Proxy prohibited from native-only uses
    assert "quantitative_amplitude_analysis" in proxy.prohibited_uses
    assert "native_trace_well_tie_acceptance" in proxy.prohibited_uses
    assert "seismic_inversion" in proxy.prohibited_uses
    assert "avo_classification" in proxy.prohibited_uses

    # Native permitted for those uses
    assert "quantitative_amplitude_analysis" in native.permitted_uses
    assert "native_trace_well_tie" in native.permitted_uses
    assert "seismic_inversion" in native.permitted_uses
