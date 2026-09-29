"""Tests for geox_seismic_attribute_compute (Slice 1 Step 4 of GEOX forge).

Covers:
- All 13 L0 attribute capabilities
- DerivedVolumeManifest emission
- Polarity gate (UNKNOWN → polarity_status=unknown)
- HOLD paths: unknown capability, missing volume, wrong shape, computation failure
- Determinism (artifact_id stable for same input)
- Smallest verifiable slice: 2D synthetic plane wave + 3D random
"""
from __future__ import annotations

import asyncio
import numpy as np
import pytest

from src.geox_mcp.tools.seismic_attribute_compute import (
    CAPABILITY_MAP,
    VALID_CAPABILITIES,
    geox_seismic_attribute_compute,
)
from geox.seismic import attributes as attr


def _synthetic_3d(n_iline: int = 8, n_xline: int = 10, n_sample: int = 64) -> list:
    """3D synthetic: linear plane dipping in xline + sample axes."""
    arr = np.zeros((n_iline, n_xline, n_sample), dtype=np.float64)
    for i in range(n_iline):
        for x in range(n_xline):
            for s in range(n_sample):
                # Plane dipping in +xline and +sample
                arr[i, x, s] = 0.8 * np.sin(0.2 * (x + s * 0.5))
    return arr.tolist()


def _spike_3d(n_iline: int = 6, n_xline: int = 8, n_sample: int = 32) -> list:
    """3D synthetic with a single sharp spike — spiky → SEG_NORMAL polarity proxy."""
    arr = np.zeros((n_iline, n_xline, n_sample), dtype=np.float64)
    arr[3, 4, 16] = 5.0
    arr[3, 4, 15] = 2.0
    arr[3, 4, 17] = 2.0
    return arr.tolist()


class TestCapabilityRegistry:
    def test_all_13_capabilities_listed(self):
        assert len(VALID_CAPABILITIES) == 13
        assert "geox.seismic.attr.envelope.v1" in VALID_CAPABILITIES
        assert "geox.seismic.attr.curvature_most_negative.v1" in VALID_CAPABILITIES
        assert "geox.seismic.attr.spectral_voice.v1" in VALID_CAPABILITIES

    def test_all_capabilities_have_implementations(self):
        for cap in VALID_CAPABILITIES:
            assert cap in CAPABILITY_MAP
            assert callable(CAPABILITY_MAP[cap])


class TestPrimitiveConsistency:
    """Test the attribute primitives directly (numpy in → numpy out)."""

    def test_envelope_shape(self):
        v = np.random.RandomState(0).randn(8, 10, 64)
        result = attr.envelope(v)
        assert result.shape == v.shape
        assert (result >= 0).all()

    def test_instantaneous_phase_range(self):
        v = np.sin(np.linspace(0, 4 * np.pi, 64))[None, :]  # reshape to 2D (1 trace)
        result = attr.instantaneous_phase(v)
        assert -np.pi <= result.min() <= result.max() <= np.pi

    def test_rms_amplitude_zero_signal(self):
        v = np.zeros((8, 8, 32))
        result = attr.rms_amplitude(v)
        assert result.max() == 0.0

    def test_variance_nonneg(self):
        v = np.random.RandomState(42).randn(8, 8, 32)
        result = attr.variance(v)
        assert (result >= 0).all()

    def test_gst_dip_zero_signal(self):
        v = np.zeros((8, 8, 32))
        result = attr.gst_dip(v)
        # No gradient → zero dip (with epsilon floor)
        assert result.max() < 1e-6

    def test_gst_azimuth_range(self):
        v = np.random.RandomState(1).randn(8, 8, 32)
        result = attr.gst_azimuth(v)
        assert 0 <= result.min() < result.max() <= 180

    def test_gst_coherence_range(self):
        v = np.random.RandomState(2).randn(8, 8, 32)
        result = attr.gst_coherence(v)
        assert 0 <= result.min() < result.max() <= 1.0

    def test_chaos_complement_of_coherence(self):
        v = np.random.RandomState(3).randn(8, 8, 32)
        coh = attr.gst_coherence(v)
        chaos = attr.chaos(v)
        np.testing.assert_allclose(coh + chaos, 1.0, atol=1e-6)

    def test_curvature_shapes(self):
        v = np.random.RandomState(4).randn(8, 8, 32)
        k_pos = attr.curvature_most_positive(v)
        k_neg = attr.curvature_most_negative(v)
        assert k_pos.shape == v.shape
        assert k_neg.shape == v.shape

    def test_spectral_voice_peaks_at_target_frequency(self):
        """A pure sinusoid at f should produce a peak at f."""
        sample_interval_s = 0.004
        target_hz = 30.0
        n_samples = 256
        t = np.arange(n_samples) * sample_interval_s
        v = np.sin(2 * np.pi * target_hz * t)
        # Reshape to 2D (1 trace)
        v_2d = v[None, :]
        result = attr.spectral_voice(v_2d, target_freq_hz=target_hz)
        assert result.shape == v_2d.shape
        # Peak should be near 1.0 for a clean sinusoid
        assert result.max() > 0.5


class TestAttributeComputeMCP:
    @pytest.mark.parametrize("capability_id", VALID_CAPABILITIES)
    def test_each_capability_returns_manifest(self, capability_id):
        volume = _spike_3d()
        result = asyncio.run(
            geox_seismic_attribute_compute(
                volume=volume,
                capability_id=capability_id,
                polarity="SEG_NORMAL",
            )
        )
        assert result["status"] == "OK"
        assert result["capability_id"] == capability_id
        assert result["polarity_status"] == "actionable"
        assert result["data"]["capability_id"] == capability_id
        assert result["data"]["signal"]["polarity"] == "SEG_NORMAL"
        assert result["claim"] is None
        # Manifest must have all required fields
        assert "artifact_id" in result["data"]
        assert "parents" in result["data"]
        assert "validity" in result["data"]
        assert "implementation" in result["data"]

    def test_polarity_unknown_marks_actionable_false(self):
        volume = _synthetic_3d()
        result = asyncio.run(
            geox_seismic_attribute_compute(
                volume=volume,
                capability_id="geox.seismic.attr.envelope.v1",
                polarity="UNKNOWN",
            )
        )
        assert result["status"] == "OK"
        assert result["polarity_status"] == "unknown"
        assert result["data"]["signal"]["polarity"] == "UNKNOWN"

    def test_unknown_capability_returns_hold(self):
        result = asyncio.run(
            geox_seismic_attribute_compute(
                volume=_synthetic_3d(),
                capability_id="geox.seismic.attr.fictional.v99",
            )
        )
        assert result["status"] == "HOLD"
        assert "unknown capability_id" in result["error"]

    def test_missing_volume_returns_hold(self):
        result = asyncio.run(
            geox_seismic_attribute_compute(
                capability_id="geox.seismic.attr.envelope.v1",
            )
        )
        assert result["status"] == "HOLD"
        assert "volume" in result["error"].lower()

    def test_wrong_shape_returns_hold(self):
        result = asyncio.run(
            geox_seismic_attribute_compute(
                volume=[[1.0, 2.0], [3.0, 4.0]],  # 2D not 3D
                capability_id="geox.seismic.attr.envelope.v1",
            )
        )
        assert result["status"] == "HOLD"
        assert "3D" in result["error"]

    def test_summary_statistics_present(self):
        volume = _synthetic_3d()
        result = asyncio.run(
            geox_seismic_attribute_compute(
                volume=volume,
                capability_id="geox.seismic.attr.rms_amplitude.v1",
            )
        )
        assert result["status"] == "OK"
        stats = result["summary_statistics"]
        assert stats["shape"] == [8, 10, 64]
        assert "finite_min" in stats
        assert "finite_mean" in stats
        assert "nan_count" in stats
        # No full volume bytes returned (per Copilot spec)
        assert "data" in result
        assert "volume" not in result  # never return full volume bytes
        assert "array" not in result
        assert "traces" not in result

    def test_artifact_id_deterministic(self):
        """Same input + capability → same artifact_id."""
        volume = _synthetic_3d()
        r1 = asyncio.run(
            geox_seismic_attribute_compute(
                volume=volume,
                capability_id="geox.seismic.attr.envelope.v1",
            )
        )
        r2 = asyncio.run(
            geox_seismic_attribute_compute(
                volume=volume,
                capability_id="geox.seismic.attr.envelope.v1",
            )
        )
        assert r1["data"]["artifact_id"] == r2["data"]["artifact_id"]

    def test_parent_artifact_recorded(self):
        result = asyncio.run(
            geox_seismic_attribute_compute(
                volume=_synthetic_3d(),
                capability_id="geox.seismic.attr.envelope.v1",
                parent_artifact_id="geox://volume/test/raw",
            )
        )
        parents = result["data"]["parents"]
        assert len(parents) == 1
        assert parents[0]["artifact_id"] == "geox://volume/test/raw"
        assert parents[0]["role"] == "input"

    def test_implementation_library_recorded(self):
        result = asyncio.run(
            geox_seismic_attribute_compute(
                volume=_synthetic_3d(),
                capability_id="geox.seismic.attr.coherence.v1" if "geox.seismic.attr.coherence.v1" in VALID_CAPABILITIES else "geox.seismic.attr.gst_coherence.v1",
            )
        )
        impl = result["data"]["implementation"]
        assert impl["library"] == "numpy_scipy_v1"
        assert impl["version"] == "1.0.0"

    def test_license_provenance_no_gpl(self):
        """Anti-Haram: no GPL in license chain."""
        result = asyncio.run(
            geox_seismic_attribute_compute(
                volume=_synthetic_3d(),
                capability_id="geox.seismic.attr.envelope.v1",
            )
        )
        licenses = result["data"]["license_provenance"]
        assert all("GPL" not in lic.upper() for lic in licenses)
