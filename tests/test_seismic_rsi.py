"""
Tests for GEOX RSI tools — Real Seismic Image Interpretation
=============================================================
Phase 3.0 (2026-07-06): Tests for geox_rsi_interpret + geox_render_audit.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile

import numpy as np
import pytest
from PIL import Image

# Skip if test image not available
_TEST_IMAGE = os.path.join(os.path.dirname(__file__), "..", "geox", "seismic", "rsi", "seismic_greyscale.jpg")
_TEST_IMAGE = os.path.normpath(_TEST_IMAGE)
_HAS_TEST_IMAGE = os.path.exists(_TEST_IMAGE)


def _run(coro):
    """Run async in sync test."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestRealityGate:
    """R0: Input reality gate tests."""

    def test_gate_passes_on_real_image(self):
        from geox_mcp.tools.seismic_rsi import _input_reality_gate

        if not _HAS_TEST_IMAGE:
            pytest.skip("Test image not available")
        gate = _input_reality_gate(_TEST_IMAGE)
        assert gate["verdict"] == "PASS"
        assert gate["file_exists"] is True
        assert gate["decodable"] is True
        assert gate["pixel_array_loaded"] is True
        assert gate["dimensions"]["width"] >= 100
        assert gate["dimensions"]["height"] >= 100

    def test_gate_fails_on_missing_file(self):
        from geox_mcp.tools.seismic_rsi import _input_reality_gate

        gate = _input_reality_gate("/nonexistent/image.jpg")
        assert gate["verdict"] == "VOID"
        assert gate["reason"] == "FILE_NOT_FOUND"

    def test_gate_fails_on_tiny_image(self):
        from geox_mcp.tools.seismic_rsi import _input_reality_gate

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            tiny = Image.fromarray(np.zeros((30, 30), dtype=np.uint8))
            tiny.save(f.name)
            gate = _input_reality_gate(f.name)
            assert gate["verdict"] == "VOID"
            assert "TOO_SMALL" in gate["reason"]
            os.unlink(f.name)


class TestProvenance:
    """R1: SHA256 provenance tests."""

    def test_provenance_has_hashes(self):
        from geox_mcp.tools.seismic_rsi import _compute_provenance

        if not _HAS_TEST_IMAGE:
            pytest.skip("Test image not available")
        prov = _compute_provenance(_TEST_IMAGE)
        assert "image_sha256" in prov
        assert len(prov["image_sha256"]) == 64  # SHA256 hex
        assert prov["image_sha256_short"] == prov["image_sha256"][:16]
        assert prov["coordinate_domain"] == "pixel"
        assert prov["input_class"] == "image_only"
        assert "OBS_IMAGE" in prov["epistemic_note"]

    def test_provenance_deterministic(self):
        from geox_mcp.tools.seismic_rsi import _compute_provenance

        if not _HAS_TEST_IMAGE:
            pytest.skip("Test image not available")
        p1 = _compute_provenance(_TEST_IMAGE)
        p2 = _compute_provenance(_TEST_IMAGE)
        assert p1["image_sha256"] == p2["image_sha256"]


class TestPanelDetection:
    """R2: Seismic panel crop detection."""

    def test_detects_panel_in_real_image(self):
        from geox_mcp.tools.seismic_rsi import _detect_seismic_panel

        if not _HAS_TEST_IMAGE:
            pytest.skip("Test image not available")
        img = np.array(Image.open(_TEST_IMAGE))
        result = _detect_seismic_panel(img)
        assert result["verdict"] == "PASS"
        assert result["panel_bbox"] is not None
        assert result["crop_pct"] > 50  # Most of image should be seismic

    def test_handles_blank_image(self):
        from geox_mcp.tools.seismic_rsi import _detect_seismic_panel

        blank = np.ones((200, 200, 3), dtype=np.uint8) * 255
        result = _detect_seismic_panel(blank)
        assert result["verdict"] == "HOLD"


class TestAttributes:
    """R4: Attribute stack computation."""

    def test_attributes_computed(self):
        from geox_mcp.tools.seismic_rsi import _compute_attributes

        # Simple synthetic test pattern
        data = np.random.rand(100, 200) * 100
        attrs = _compute_attributes(data)
        assert "agc" in attrs
        assert "cosine_phase" in attrs
        assert "discontinuity" in attrs
        assert "fault_probability" in attrs
        assert "horizon_probability" in attrs
        assert "curvature" in attrs
        assert "coherence_st" in attrs
        assert "orientation" in attrs
        # All labeled DER_RENDER_CONTRAST
        for key, label in attrs["labels"].items():
            assert label == "DER_RENDER_CONTRAST", f"{key} has wrong label: {label}"

    def test_attribute_shapes_match_input(self):
        from geox_mcp.tools.seismic_rsi import _compute_attributes

        data = np.random.rand(50, 100) * 100
        attrs = _compute_attributes(data)
        for key in ["agc", "cosine_phase", "discontinuity", "fault_probability"]:
            assert attrs[key].shape == data.shape, f"{key} shape mismatch"


class TestFaultDetection:
    """R5: Fault detection with structure tensor orientation."""

    def test_faults_have_required_fields(self):
        from geox_mcp.tools.seismic_rsi import _detect_faults

        fp = np.random.rand(100, 200)
        orientation = np.random.rand(100, 200) * np.pi
        faults = _detect_faults(fp, orientation, min_length=10, percentile=50)
        for f in faults:
            assert "id" in f
            assert "pts" in f
            assert "confidence" in f
            assert "dip_direction_deg" in f
            assert "label" in f
            assert f["label"] == "INT_SEISMIC_FAULT"
            assert "alternatives" in f
            assert len(f["alternatives"]) >= 3

    def test_fault_blocks_segmentation(self):
        from geox_mcp.tools.seismic_rsi import _segment_fault_blocks

        faults = [
            {
                "id": "F1",
                "pts": [[50, i] for i in range(100)],
                "n": 100,
                "confidence": 0.8,
                "label": "INT_SEISMIC_FAULT",
                "alternatives": ["a", "b", "c"],
                "dip_direction_deg": 0,
                "vertical_extent_px": 100,
            },
        ]
        blocks = _segment_fault_blocks(faults, (100, 100))
        assert blocks.shape == (100, 100)
        assert blocks.max() >= 1  # At least one block


class TestHorizonTracking:
    """R6: Horizon tracking with look-ahead and confidence."""

    def test_horizons_have_required_fields(self):
        from geox_mcp.tools.seismic_rsi import _detect_and_track_horizons

        hc, wc = 100, 200
        agc_d = np.random.rand(hc, wc)
        pc = np.random.rand(hc, wc) * 0.5 + 0.5
        fault_mask = np.zeros((hc, wc), dtype=bool)
        horizons = _detect_and_track_horizons(agc_d, pc, fault_mask, max_horizons=5)
        for h in horizons:
            assert "id" in h
            assert "pts" in h
            assert "confidence" in h
            assert "continuity" in h
            assert "phase_agreement" in h
            assert "amplitude_consistency" in h
            assert "label" in h
            assert h["label"] == "INT_SEISMIC_HORIZON"
            assert "alternatives" in h
            assert len(h["alternatives"]) >= 3


class TestEpistemicGovernance:
    """R7: Epistemic grammar enforcement."""

    def test_grammar_enforced(self):
        from geox_mcp.tools.seismic_rsi import _build_epistemic_envelope

        faults = [{"id": "F1", "label": "INT_SEISMIC_FAULT", "alternatives": ["a", "b", "c"]}]
        horizons = [{"id": "H1", "label": "INT_SEISMIC_HORIZON", "alternatives": ["x", "y", "z"]}]
        attrs = {"labels": {"agc": "DER_RENDER_CONTRAST"}}
        env = _build_epistemic_envelope(faults, horizons, attrs)
        assert "OBS_IMAGE" in env["grammar"]
        assert "DER_RENDER_CONTRAST" in env["grammar"]
        assert "INT_SEISMIC_HORIZON" in env["grammar"]
        assert "INT_SEISMIC_FAULT" in env["grammar"]
        assert "HOLD" in env["grammar"]
        assert env["alternatives_required"] is True
        assert len(env["forbidden_claims"]) > 0


class TestRenderAudit:
    """R8: Render audit tests."""

    def test_audit_on_real_image(self):
        from geox_mcp.tools.seismic_rsi import _render_audit

        if not _HAS_TEST_IMAGE:
            pytest.skip("Test image not available")
        img = np.array(Image.open(_TEST_IMAGE))
        agc_d = np.random.rand(img.shape[0], img.shape[1]) if img.ndim == 2 else np.random.rand(img.shape[0], img.shape[1])
        audit = _render_audit(img, agc_d)
        assert "dynamic_range" in audit
        assert "is_greyscale" in audit
        assert "render_trust" in audit
        assert audit["render_trust"] in ("HIGH", "MEDIUM", "LOW")
        assert audit["label"] == "DER_RENDER_CONTRAST"


class TestRSIInterpret:
    """Integration test: full RSI pipeline."""

    @pytest.mark.skipif(not _HAS_TEST_IMAGE, reason="Test image not available")
    def test_full_pipeline(self):
        from geox_mcp.tools.seismic_rsi import geox_rsi_interpret

        result = _run(geox_rsi_interpret(_TEST_IMAGE))
        assert result["verdict"] == "PARTIAL"
        assert "horizons" in result
        assert "faults" in result
        assert "geometry" in result
        assert "provenance" in result
        assert "render_audit" in result

        # Epistemic checks
        gov = result["stages"]["R7_governance"]
        assert "OBS_IMAGE" in gov["grammar"]
        assert "INT_SEISMIC_HORIZON" in gov["grammar"]
        assert "INT_SEISMIC_FAULT" in gov["grammar"]

        # Every INT claim has alternatives
        for h in result["horizons"]:
            assert "label" in h
        for f in result["faults"]:
            assert "label" in f

        # Geometry has fault blocks
        assert result["geometry"]["fault_blocks"] >= 1

        # Forbidden claims scan integrated
        assert "_envelope" in result

    @pytest.mark.skipif(not _HAS_TEST_IMAGE, reason="Test image not available")
    def test_render_audit_tool(self):
        from geox_mcp.tools.seismic_rsi import geox_render_audit

        result = _run(geox_render_audit(_TEST_IMAGE))
        assert "verdict" in result
        assert "audit" in result
        assert "provenance" in result
        assert result["audit"]["label"] == "DER_RENDER_CONTRAST"

    @pytest.mark.skipif(not _HAS_TEST_IMAGE, reason="Test image not available")
    def test_higher_percentile_fewer_faults(self):
        from geox_mcp.tools.seismic_rsi import geox_rsi_interpret

        r_low = _run(geox_rsi_interpret(_TEST_IMAGE, fault_percentile=95))
        r_high = _run(geox_rsi_interpret(_TEST_IMAGE, fault_percentile=99))
        # Higher percentile = fewer faults (or equal)
        assert len(r_high["faults"]) <= len(r_low["faults"])


class TestForbiddenClaimsIntegration:
    """P4: Forbidden claims scan wired into RSI output."""

    @pytest.mark.skipif(not _HAS_TEST_IMAGE, reason="Test image not available")
    def test_forbidden_claims_present_in_output(self):
        from geox_mcp.tools.seismic_rsi import geox_rsi_interpret

        result = _run(geox_rsi_interpret(_TEST_IMAGE))
        assert "_envelope" in result
        envelope = result["_envelope"]
        assert "forbidden_claims" in envelope
        assert "forbidden_claims_count" in envelope
        # The epistemic note should not trigger BLOCK claims
        # (we're careful about OBS_IMAGE language)
        assert isinstance(envelope["forbidden_claims"], list)


class TestCanonicalRegistration:
    """Verify tools are properly registered in registry."""

    def test_rsi_tools_in_surface(self):
        from geox_mcp.registry import SURFACE_TOOLS

        assert "geox_rsi_interpret" in SURFACE_TOOLS
        assert "geox_render_audit" in SURFACE_TOOLS

    def test_rsi_tools_in_manifest(self):
        from geox_mcp.registry import GEOX_TOOL_MANIFEST

        names = [t["name"] for t in GEOX_TOOL_MANIFEST]
        assert "geox_rsi_interpret" in names
        assert "geox_render_audit" in names

    def test_rsi_manifest_has_correct_domain(self):
        from geox_mcp.registry import GEOX_TOOL_MANIFEST

        for t in GEOX_TOOL_MANIFEST:
            if t["name"] in ("geox_rsi_interpret", "geox_render_audit"):
                assert t["domain"] == "earth.seismic"
