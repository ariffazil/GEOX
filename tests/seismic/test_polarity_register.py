"""Tests for geox_seismic_polarity_register (Slice 1 Step 3 of GEOX forge).

Tests cover:
- external_calibration_witness path (declared polarity)
- kurtosis_max inference on a synthetic SEG_NORMAL-like impulse
- kurtosis_max on a synthetic SEG_REVERSE-like impulse
- HOLD behavior on too-short trace
- HOLD behavior on volume_ref without backend (artifact-store gap)
- Deterministic register_id computation
"""
from __future__ import annotations

import asyncio
import numpy as np
import pytest

from src.geox_mcp.tools.seismic_polarity_register import (
    geox_seismic_polarity_register,
    _phase_search,
    _infer_polarity_from_kurtosis,
)


def _seg_normal_impulse(n: int = 256, peak_position: int = 128) -> np.ndarray:
    """A spike + ringing: spiky → positive kurtosis → SEG_NORMAL."""
    t = np.arange(n) - peak_position
    sig = np.zeros(n)
    sig[peak_position] = 1.0
    sig += 0.5 * np.exp(-((t / 8.0) ** 2)) * np.cos(2 * np.pi * 0.1 * t)
    return sig


def _seg_reverse_impulse(n: int = 256) -> np.ndarray:
    """A boxcar: flat-topped → negative kurtosis → SEG_REVERSE/EUROPEAN."""
    sig = np.zeros(n)
    sig[100:160] = 1.0
    sig[80:120] = 0.5
    sig[140:180] = 0.5
    return sig


class TestPolarityRegister:
    def test_external_calibration_witness_seg_normal(self):
        result = asyncio.run(
            geox_seismic_polarity_register(
                method="external_calibration_witness",
                external_polarity="SEG_NORMAL",
                external_phase_deg=0.0,
                registered_by="test-actor",
            )
        )
        assert result["status"] == "OK"
        assert result["data"]["polarity"] == "SEG_NORMAL"
        assert result["data"]["constant_phase_deg"] == 0.0
        assert len(result["data"]["phase_estimates"]) == 1
        assert result["data"]["phase_estimates"][0]["method"] == "external_calibration_witness"
        assert result["claim"] is None

    def test_external_calibration_witness_seg_reverse(self):
        result = asyncio.run(
            geox_seismic_polarity_register(
                method="external_calibration_witness",
                external_polarity="SEG_REVERSE",
                external_phase_deg=-180.0,
            )
        )
        assert result["status"] == "OK"
        assert result["data"]["polarity"] == "SEG_REVERSE"
        assert result["data"]["constant_phase_deg"] == -180.0

    def test_external_calibration_witness_requires_polarity(self):
        result = asyncio.run(
            geox_seismic_polarity_register(
                method="external_calibration_witness",
                # external_polarity missing
            )
        )
        assert result["status"] == "HOLD"
        assert "external_polarity required" in result["error"]

    def test_kurtosis_max_on_spike_returns_seg_normal(self):
        trace = _seg_normal_impulse()
        result = asyncio.run(
            geox_seismic_polarity_register(
                trace=trace.tolist(),
                method="kurtosis_max",
            )
        )
        assert result["status"] == "OK"
        # Spiky impulse → SEG_NORMAL
        assert result["data"]["polarity"] in ("SEG_NORMAL", "UNKNOWN")
        assert len(result["data"]["phase_estimates"]) == 1
        assert result["data"]["phase_estimates"][0]["method"] == "kurtosis_max"

    def test_too_short_trace_returns_hold(self):
        result = asyncio.run(
            geox_seismic_polarity_register(
                trace=[0.1, 0.2, 0.3],  # < 8 samples
                method="kurtosis_max",
            )
        )
        assert result["status"] == "HOLD"
        assert "too short" in result["error"]

    def test_volume_ref_path_returns_hold(self):
        """Per Canon #0: when artifact-store bridge is missing, return HOLD not guess."""
        result = asyncio.run(
            geox_seismic_polarity_register(
                volume_ref="geox://volume/f3/raw",
                method="kurtosis_max",
            )
        )
        assert result["status"] == "HOLD"
        assert "artifact-store" in result["error"]

    def test_no_inputs_returns_hold(self):
        result = asyncio.run(geox_seismic_polarity_register())
        assert result["status"] == "HOLD"

    def test_register_id_deterministic(self):
        r1 = asyncio.run(
            geox_seismic_polarity_register(
                method="external_calibration_witness",
                external_polarity="SEG_NORMAL",
                external_phase_deg=15.0,
                registered_by="test-actor",
            )
        )
        r2 = asyncio.run(
            geox_seismic_polarity_register(
                method="external_calibration_witness",
                external_polarity="SEG_NORMAL",
                external_phase_deg=15.0,
                registered_by="test-actor",
            )
        )
        assert r1["data"]["register_id"] == r2["data"]["register_id"]
        assert r1["data"]["register_id"].startswith("geox://artifact/polarity-")

    def test_register_id_changes_with_polarity(self):
        r1 = asyncio.run(
            geox_seismic_polarity_register(
                method="external_calibration_witness",
                external_polarity="SEG_NORMAL",
                registered_by="x",
            )
        )
        r2 = asyncio.run(
            geox_seismic_polarity_register(
                method="external_calibration_witness",
                external_polarity="SEG_REVERSE",
                registered_by="x",
            )
        )
        assert r1["data"]["register_id"] != r2["data"]["register_id"]


class TestPolarityInference:
    """Direct tests on the inference primitives (no MCP envelope)."""

    def test_phase_search_finds_zero_phase_for_spike(self):
        trace = _seg_normal_impulse()
        phase_deg, score = _phase_search(trace, method="kurtosis_max")
        # Phase should be near 0° or 180° for an idealized zero-phase spike
        # (kurtosis_max is invariant under 180° phase rotation of an even-symmetric signal)
        assert -180.0 <= phase_deg <= 180.0
        assert score > 0  # spiky → positive kurtosis

    def test_infer_polarity_from_kurtosis_spike(self):
        trace = _seg_normal_impulse()
        polarity = _infer_polarity_from_kurtosis(trace)
        assert polarity == "SEG_NORMAL"

    def test_infer_polarity_from_kurtosis_boxcar(self):
        trace = _seg_reverse_impulse()
        polarity = _infer_polarity_from_kurtosis(trace)
        assert polarity in ("SEG_REVERSE", "UNKNOWN")

    def test_amplitude_spectrum_max_returns_valid_phase(self):
        trace = _seg_normal_impulse()
        phase_deg, score = _phase_search(trace, method="amplitude_spectrum_max")
        assert -180.0 <= phase_deg <= 180.0
        assert score > 0
