"""Tests for geox_seismic_artifact_get (Slice 1 Step 7 of GEOX forge).

Tests cover:
- File backend reads JSON artifact
- Schema validation succeeds for each artifact kind
- Schema validation fails with HOLD on schema mismatch
- Unknown artifact kind inferred correctly
- geox:// URI prefix required
"""
from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from src.geox_mcp.tools.seismic_artifact_get import (
    FileBackend,
    _infer_kind,
    geox_seismic_artifact_get,
)


@pytest.fixture
def tmp_artifact_root(tmp_path):
    """Build a directory structure of test artifacts."""
    # Volume manifest
    volume = {
        "schema_uri": "geox.seismic.volume-manifest.v1",
        "artifact_id": "geox://volume/test/raw",
        "sha256": "a" * 64,
        "created_by": "test",
        "domain": {"vertical": "TWT", "unit": "ms", "crs": "EPSG:4326"},
        "grid": {
            "shape": [100, 200, 300],
            "spacing": [25.0, 25.0, 4.0],
            "axis_order": ["iline", "xline", "twt"],
        },
        "signal": {
            "polarity": "SEG_NORMAL",
            "phase_deg": 0.0,
            "amplitude_status": "relative",
            "sample_interval_ms": 4.0,
        },
        "storage": {"uri": "file:///tmp/test.zarr", "chunks": None, "dtype": "float32"},
        "source_uri": "file:///tmp/test.sgy",
        "source_format": "SEGY_REV1",
        "classification": "PUBLIC",
    }
    (tmp_path / "volume__test__raw.json").write_text(json.dumps(volume))

    # QC receipt
    qc = {
        "schema_uri": "geox.seismic.qc-receipt.v1",
        "artifact_ref": "geox://derived/coherence/test",
        "qc_id": "geox://qc/test-qc-1",
        "created_by": "test",
        "verdict": "PASS",
        "checks": [],
        "failures": [],
        "code_version": "1.0.0",
    }
    (tmp_path / "qc__test-qc-1.json").write_text(json.dumps(qc))

    # Polarity register
    polarity = {
        "schema_uri": "geox.seismic.polarity-phase-register.v1",
        "register_id": "geox://artifact/polarity-abc123",
        "polarity": "SEG_NORMAL",
        "constant_phase_deg": 0.0,
        "time_shift_ms": 0.0,
        "phase_estimates": [],
        "registered_by": "test",
    }
    (tmp_path / "artifact__polarity-abc123.json").write_text(json.dumps(polarity))

    return tmp_path


class TestInferKind:
    def test_volume_prefix(self):
        assert _infer_kind("geox://volume/f3/raw") == "volume_manifest"

    def test_derived_prefix(self):
        assert _infer_kind("geox://derived/coherence/x") == "derived_volume_manifest"

    def test_qc_prefix(self):
        assert _infer_kind("geox://qc/abc") == "qc_receipt"

    def test_polarity_artifact_prefix(self):
        assert _infer_kind("geox://artifact/polarity-abc") == "polarity_register"

    def test_generic_artifact_prefix(self):
        assert _infer_kind("geox://artifact/fault-stick-1") == "editing_primitive"

    def test_unknown_prefix(self):
        assert _infer_kind("geox://unknown/xyz") == "unknown"

    def test_non_geox_uri(self):
        assert _infer_kind("https://example.com/foo") == "unknown"


class TestFileBackend:
    def test_fetch_existing(self, tmp_artifact_root):
        backend = FileBackend(tmp_artifact_root)
        payload = backend.fetch("geox://volume/test/raw")
        assert payload is not None
        assert payload["schema_uri"] == "geox.seismic.volume-manifest.v1"

    def test_fetch_missing(self, tmp_artifact_root):
        backend = FileBackend(tmp_artifact_root)
        assert backend.fetch("geox://volume/missing/x") is None


class TestArtifactGet:
    def test_get_volume_manifest(self, tmp_artifact_root):
        backend = FileBackend(tmp_artifact_root)
        result = asyncio.run(
            geox_seismic_artifact_get(
                artifact_id="geox://volume/test/raw",
                backend=backend,
            )
        )
        assert result["status"] == "OK"
        assert result["inferred_kind"] == "volume_manifest"
        assert result["validated_against"] == "volume_manifest"
        assert result["payload"]["schema_uri"] == "geox.seismic.volume-manifest.v1"

    def test_get_qc_receipt(self, tmp_artifact_root):
        backend = FileBackend(tmp_artifact_root)
        result = asyncio.run(
            geox_seismic_artifact_get(
                artifact_id="geox://qc/test-qc-1",
                backend=backend,
            )
        )
        assert result["status"] == "OK"
        assert result["inferred_kind"] == "qc_receipt"
        assert result["payload"]["verdict"] == "PASS"

    def test_get_polarity_register(self, tmp_artifact_root):
        backend = FileBackend(tmp_artifact_root)
        result = asyncio.run(
            geox_seismic_artifact_get(
                artifact_id="geox://artifact/polarity-abc123",
                backend=backend,
            )
        )
        assert result["status"] == "OK"
        assert result["inferred_kind"] == "polarity_register"
        assert result["payload"]["polarity"] == "SEG_NORMAL"

    def test_get_missing_artifact(self, tmp_artifact_root):
        backend = FileBackend(tmp_artifact_root)
        result = asyncio.run(
            geox_seismic_artifact_get(
                artifact_id="geox://volume/missing/x",
                backend=backend,
            )
        )
        assert result["status"] == "HOLD"
        assert "not found" in result["error"]

    def test_invalid_geox_uri(self, tmp_artifact_root):
        backend = FileBackend(tmp_artifact_root)
        result = asyncio.run(
            geox_seismic_artifact_get(
                artifact_id="https://example.com/foo",
                backend=backend,
            )
        )
        assert result["status"] == "HOLD"
        assert "geox://" in result["error"]

    def test_schema_validation_failure(self, tmp_artifact_root):
        """If payload is malformed against its kind, return HOLD."""
        bad_path = tmp_artifact_root / "volume__bad__raw.json"
        bad_path.write_text(json.dumps({"this": "is not a volume manifest"}))
        backend = FileBackend(tmp_artifact_root)
        result = asyncio.run(
            geox_seismic_artifact_get(
                artifact_id="geox://volume/bad/raw",
                backend=backend,
            )
        )
        assert result["status"] == "HOLD"
        assert "schema validation failed" in result["error"]

    def test_claim_is_none(self, tmp_artifact_root):
        """Artifact retrieval is a read, not a claim — claim must be None."""
        backend = FileBackend(tmp_artifact_root)
        result = asyncio.run(
            geox_seismic_artifact_get(
                artifact_id="geox://volume/test/raw",
                backend=backend,
            )
        )
        assert result["claim"] is None
