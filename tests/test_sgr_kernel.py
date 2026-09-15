"""Tests for SGR pure kernel."""
import pytest
from geox_core.geology.fault_seal import compute_sgr


def test_basic_sgr():
    zones = [
        {"zone_id": "z1", "thickness_m": 10.0, "vsh": 0.3},
        {"zone_id": "z2", "thickness_m": 20.0, "vsh": 0.8},
    ]
    result = compute_sgr(zones, throw_m=50.0)
    # Expected: (0.3*10 + 0.8*20) / 50 = (3+16)/50 = 19/50 = 0.38
    assert result["sgr_fraction"] == pytest.approx(0.38, abs=0.01)
    assert result["sgr_percent"] == pytest.approx(38.0, abs=0.1)
    assert result["status"] == "COMPUTED"
    assert result["interpretation"] == "NOT_A_SEAL_VERDICT"


def test_no_zones():
    result = compute_sgr([], throw_m=50.0)
    assert result["status"] == "UNKNOWN"


def test_zero_throw():
    result = compute_sgr([{"zone_id": "z1", "thickness_m": 10.0, "vsh": 0.5}], throw_m=0.0)
    assert result["status"] == "HOLD"


def test_uncertainty():
    zones = [{"zone_id": "z1", "thickness_m": 10.0, "vsh": 0.5}]
    result = compute_sgr(zones, throw_m=20.0, uncertainty={"thickness_pct": 0.1, "vsh_pct": 0.15, "throw_pct": 0.2})
    assert result["uncertainty"] is not None
    assert result["uncertainty"]["p10"] < result["uncertainty"]["p50"]
    assert result["uncertainty"]["p90"] > result["uncertainty"]["p50"]


def test_display_proxy_coverage_cap():
    """Verify display-derived proxy evidence caps coverage at 0.25."""
    from geox_core.seismic_pipeline.data_representation import (
        SeismicDataClassification, DataRepresentation, AmplitudeIntegrity
    )
    proxy = SeismicDataClassification(
        data_representation=DataRepresentation.DISPLAY_DERIVED_PROXY,
        amplitude_integrity=AmplitudeIntegrity.DISPLAY_TRANSFORMED,
    )
    assert proxy.quality_coverage_cap == 0.25
    assert proxy.prohibited_uses  # should have items
    assert "quantitative_amplitude_analysis" in proxy.prohibited_uses

    native = SeismicDataClassification(
        data_representation=DataRepresentation.NATIVE_TRACE,
        amplitude_integrity=AmplitudeIntegrity.PRESERVED,
    )
    assert native.quality_coverage_cap == 1.0
    assert "quantitative_amplitude_analysis" in native.permitted_uses
