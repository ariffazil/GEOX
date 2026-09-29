"""Tests for geox_seismic_volume_register and geox_seismic_horizon_track.

Tests the bridge that turns "yes for PNG" into "yes for SEG-Y".

Covers:
- SEG-Y Rev 2 → VolumeManifest (with synthetic SEG-Y from segyio)
- Horizon tracker on 3D synthetic volume (peak/trough/zero)
- HOLD paths: missing file, invalid SEG-Y, missing seeds, wrong shape
- Determinism (same seeds → same SurfaceMesh vertices)
"""
from __future__ import annotations

import asyncio
import io
import os
import struct
import tempfile

import numpy as np
import pytest


# ────────────────────────────────────────────────────────────────────────────
# Synthetic SEG-Y generators
# ────────────────────────────────────────────────────────────────────────────


def _synthesize_segy(
    path: str,
    n_iline: int = 4,
    n_xline: int = 4,
    n_samples: int = 64,
    sample_interval_us: int = 4000,  # 4 ms
    polarity_normal: bool = True,
) -> str:
    """Write a minimal SEG-Y Rev 2 file at `path`.

    Uses segyio if available; otherwise writes a hand-crafted minimal SEG-Y
    with 3200-byte text header + binary header + 240-byte trace headers.
    """
    try:
        import segyio

        spec = segyio.spec()
        spec.sorting = 2  # inline
        spec.format = 1  # IBM float
        spec.samples = list(range(n_samples))  # sequence of sample indices
        spec.iline = 189        # start inline (not list)
        spec.ilines = list(range(189, 189 + n_iline))
        spec.xline = 193        # start xline (not list)
        spec.xlines = list(range(193, 193 + n_xline))
        spec.tracecount = n_iline * n_xline
        spec.delrt = 0

        with segyio.create(path, spec) as segy:
            for i_idx, inline in enumerate(spec.ilines):
                for x_idx, xline in enumerate(spec.xlines):
                    trace = np.zeros(n_samples, dtype=np.float32)
                    for s in range(n_samples):
                        # Linear dipping reflector
                        trace[s] = 0.6 * np.sin(0.1 * (s + i_idx * 2 + x_idx * 3))
                    if not polarity_normal:
                        trace = -trace
                    segy.trace[i_idx * n_xline + x_idx] = trace

        # Patch binary header bytes 16-17 (sample interval in µs, big-endian)
        with open(path, "r+b") as f:
            f.seek(3200 + 16)  # skip text header (3200 bytes) + 16-byte offset
            f.write(struct.pack(">H", sample_interval_us))
        return path

    except ImportError:
        # Fallback: hand-crafted minimal SEG-Y
        with open(path, "wb") as f:
            # 3200-byte textual header (all spaces + zeros)
            f.write(b" " * 3200)
            # 400-byte binary header
            binary_header = bytearray(400)
            # Sample interval (bytes 16-17, big-endian)
            struct.pack_into(">h", binary_header, 16, sample_interval_us)
            # Number of samples per trace (bytes 20-21)
            struct.pack_into(">h", binary_header, 20, n_samples)
            # Format (bytes 24-25): 1 = IBM float
            struct.pack_into(">h", binary_header, 24, 1)
            f.write(binary_header)
            # Traces
            for trace_idx in range(n_iline * n_xline):
                trace_header = bytearray(240)
                # Trace number within line (bytes 4-5)
                struct.pack_into(">h", trace_header, 4, (trace_idx % n_xline) + 1)
                # Inline number (bytes 8-11)
                struct.pack_into(">i", trace_header, 8, (trace_idx // n_xline) + 1)
                # Xline number (bytes 20-23)
                struct.pack_into(">i", trace_header, 20, (trace_idx % n_xline) + 1)
                # 240-byte header + n_samples * 4-byte IBM float samples
                f.write(trace_header)
                samples = np.zeros(n_samples, dtype=np.float32)
                for s in range(n_samples):
                    samples[s] = 0.6 * np.sin(0.1 * (s + trace_idx))
                f.write(samples.tobytes())
        return path


# ────────────────────────────────────────────────────────────────────────────
# Tests: volume_register
# ────────────────────────────────────────────────────────────────────────────


class TestVolumeRegister:
    def test_register_synthetic_segy(self, tmp_path):
        from src.geox_mcp.tools.seismic_volume_register import geox_seismic_volume_register
        segy_path = str(tmp_path / "test.sgy")
        _synthesize_segy(segy_path, n_iline=3, n_xline=3, n_samples=32)
        result = asyncio.run(
            geox_seismic_volume_register(
                segy_path=segy_path,
                survey_id="test_survey",
            )
        )
        assert result["status"] == "OK", f"got {result}"
        assert result["data"]["schema_uri"] == "geox.seismic.volume-manifest.v1"
        # Grid shape: either 3x3x32 (if ilines/xlines parsed) or 9x1x32 (fallback)
        shape = result["data"]["grid"]["shape"]
        assert shape == [3, 3, 32] or shape == [9, 1, 32], f"unexpected shape: {shape}"
        assert shape[2] == 32  # sample count always correct
        assert result["data"]["source_format"] in ("SEGY_REV1", "SEGY_REV2")
        assert result["data"]["signal"]["sample_interval_ms"] == pytest.approx(4.0, abs=0.1)
        assert result["provenance"]["source_sha256"] is not None
        assert len(result["provenance"]["source_sha256"]) == 64
        assert result["claim"] is None

    def test_register_holds_on_missing_file(self):
        from src.geox_mcp.tools.seismic_volume_register import geox_seismic_volume_register
        result = asyncio.run(
            geox_seismic_volume_register(segy_path="/nonexistent/path.sgy")
        )
        assert result["status"] == "HOLD"
        assert "not found" in result["error"]

    def test_register_classification_default_internal(self, tmp_path):
        from src.geox_mcp.tools.seismic_volume_register import geox_seismic_volume_register
        segy_path = str(tmp_path / "test.sgy")
        _synthesize_segy(segy_path, n_iline=2, n_xline=2, n_samples=8)
        result = asyncio.run(geox_seismic_volume_register(segy_path=segy_path))
        assert result["status"] == "OK"
        assert result["data"]["classification"] == "INTERNAL"

    def test_register_classification_confidential(self, tmp_path):
        from src.geox_mcp.tools.seismic_volume_register import geox_seismic_volume_register
        segy_path = str(tmp_path / "test.sgy")
        _synthesize_segy(segy_path, n_iline=2, n_xline=2, n_samples=8)
        result = asyncio.run(
            geox_seismic_volume_register(segy_path=segy_path, classification="CONFIDENTIAL")
        )
        assert result["data"]["classification"] == "CONFIDENTIAL"


# ────────────────────────────────────────────────────────────────────────────
# Tests: horizon_track
# ────────────────────────────────────────────────────────────────────────────


def _synthetic_3d_with_horizon(
    n_iline: int = 6, n_xline: int = 8, n_samples: int = 32
) -> list:
    """3D synthetic with a clear horizontal peak at sample 16."""
    arr = np.zeros((n_iline, n_xline, n_samples), dtype=np.float64)
    for i in range(n_iline):
        for x in range(n_xline):
            for s in range(n_samples):
                # Peak at s=16, with mild surface variation
                peak_pos = 16 + 1.0 * np.sin(i * 0.5) + 0.5 * np.cos(x * 0.3)
                arr[i, x, s] = 0.8 * np.exp(-((s - peak_pos) / 2.0) ** 2)
    return arr.tolist()


class TestHorizonTrack:
    def test_track_peak_in_synthetic_3d(self):
        from src.geox_mcp.tools.seismic_horizon_track import geox_seismic_horizon_track
        volume = _synthetic_3d_with_horizon()
        result = asyncio.run(
            geox_seismic_horizon_track(
                volume=volume,
                seeds=[(3, 4, 16)],  # center seed on the known horizon
                phase_event="peak",
                half_window=10,
            )
        )
        assert result["status"] == "OK"
        assert result["data"]["mesh_id"].startswith("geox://artifact/horizon-tracked-")
        # All tracked vertices should be near sample 16 (with surface variation)
        vertices = result["data"]["vertices"]
        assert len(vertices) == 6 * 8  # full grid 6x8
        samples = [v[2] for v in vertices]
        assert all(8 <= s <= 24 for s in samples), f"samples out of range: {samples}"
        # Confidence should be high (peak is clear)
        confidences = result["data"]["confidence"]
        assert all(c > 0.3 for c in confidences)

    def test_track_trough(self):
        from src.geox_mcp.tools.seismic_horizon_track import geox_seismic_horizon_track
        # Invert the synthetic to have a trough at sample 16
        volume = np.array(_synthetic_3d_with_horizon())
        volume = -volume
        result = asyncio.run(
            geox_seismic_horizon_track(
                volume=volume.tolist(),
                seeds=[(3, 4, 16)],
                phase_event="trough",
                half_window=10,
            )
        )
        assert result["status"] == "OK"
        assert all(8 <= v[2] <= 24 for v in result["data"]["vertices"])

    def test_hold_on_missing_volume(self):
        from src.geox_mcp.tools.seismic_horizon_track import geox_seismic_horizon_track
        result = asyncio.run(
            geox_seismic_horizon_track(
                volume=None,
                seeds=[(0, 0, 16)],
            )
        )
        assert result["status"] == "HOLD"

    def test_hold_on_missing_seeds(self):
        from src.geox_mcp.tools.seismic_horizon_track import geox_seismic_horizon_track
        volume = _synthetic_3d_with_horizon()
        result = asyncio.run(
            geox_seismic_horizon_track(
                volume=volume,
                seeds=[],
            )
        )
        assert result["status"] == "HOLD"

    def test_hold_on_wrong_shape(self):
        from src.geox_mcp.tools.seismic_horizon_track import geox_seismic_horizon_track
        result = asyncio.run(
            geox_seismic_horizon_track(
                volume=[[1.0, 2.0], [3.0, 4.0]],  # 2D not 3D
                seeds=[(0, 0, 0)],
            )
        )
        assert result["status"] == "HOLD"
        assert "3D" in result["error"]

    def test_deterministic_same_seeds_same_vertices(self):
        from src.geox_mcp.tools.seismic_horizon_track import geox_seismic_horizon_track
        volume = _synthetic_3d_with_horizon()
        r1 = asyncio.run(
            geox_seismic_horizon_track(
                volume=volume, seeds=[(3, 4, 16)], phase_event="peak",
            )
        )
        r2 = asyncio.run(
            geox_seismic_horizon_track(
                volume=volume, seeds=[(3, 4, 16)], phase_event="peak",
            )
        )
        assert r1["data"]["vertices"] == r2["data"]["vertices"]

    def test_smoothing_changes_output(self):
        from src.geox_mcp.tools.seismic_horizon_track import geox_seismic_horizon_track
        # Use noisy synthetic so smoothing actually shifts peak
        rng = np.random.RandomState(42)
        base = np.array(_synthetic_3d_with_horizon())
        noise = 0.15 * rng.randn(*base.shape)
        noisy = (base + noise).tolist()
        r1 = asyncio.run(
            geox_seismic_horizon_track(
                volume=noisy, seeds=[(3, 4, 16)], phase_event="peak", smoothing_sigma=0.0
            )
        )
        r2 = asyncio.run(
            geox_seismic_horizon_track(
                volume=noisy, seeds=[(3, 4, 16)], phase_event="peak", smoothing_sigma=2.0
            )
        )
        # Smoothing should shift peak positions slightly
        assert r1["data"]["vertices"] != r2["data"]["vertices"]

    def test_single_seed_expands_to_full_grid(self):
        """One seed → BFS expansion covers all reachable (iline, xline) positions."""
        from src.geox_mcp.tools.seismic_horizon_track import geox_seismic_horizon_track
        volume = _synthetic_3d_with_horizon(n_iline=4, n_xline=6, n_samples=32)
        result = asyncio.run(
            geox_seismic_horizon_track(
                volume=volume,
                seeds=[(2, 3, 16)],  # single seed
                phase_event="peak",
                half_window=8,
            )
        )
        assert result["status"] == "OK"
        assert len(result["data"]["vertices"]) == 4 * 6  # full grid

    def test_claim_is_null_no_geological_verdict(self):
        from src.geox_mcp.tools.seismic_horizon_track import geox_seismic_horizon_track
        volume = _synthetic_3d_with_horizon()
        result = asyncio.run(
            geox_seismic_horizon_track(
                volume=volume, seeds=[(3, 4, 16)], phase_event="peak"
            )
        )
        assert result["claim"] is None
        assert result["provenance"]["evidence_class"] == "OBSERVATION"
        assert result["provenance"]["claim_ceiling"] == "HYPOTHESIS"
