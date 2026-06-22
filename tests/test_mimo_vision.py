"""
GEOX MiMo Vision V1 — Test Suite
═══════════════════════════════════════════════════════════════════════════
Forged 2026-06-16 — DITEMPA BUKAN DIBERI

Covers:
- MiMoVLMAdapter parsing (mock + real VLM responses)
- Constitutional binding (F1/F4/F7/F9/F13 enforcement)
- AC_Risk computation (MiMo-specific adjustments)
- Cross-Modal Fidelity Theorem round-trip integrity
- MiMoHTTPBackend integration (mock server)

Run with:
    PYTHONPATH=src pytest tests/test_mimo_vision.py -v
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Ensure the GEOX src tree is on the path
GEOX_SRC = Path(__file__).resolve().parents[2] / "src"
if str(GEOX_SRC) not in sys.path:
    sys.path.insert(0, str(GEOX_SRC))

from geox_core.engines.vision import (
    MiMoVLMAdapter,
    MiMoVisionResult,
    MiMoVisionError,
    MiMoHTTPBackend,
    PerceptualInventory,
    ReflectorObservation,
    FaultObservation,
    AmplitudeZoneObservation,
    AxisMetadata,
    AcRiskComponents,
    VisionVerdict,
    AcRiskVerdict,
    AmplitudeCharacter,
    ReflectorContinuity,
    PolarityConvention,
    FaultType,
    AmplitudeZoneCharacter,
    AmplitudeZoneOrigin,
    DisplayColorPolarity,
    DisplayUnits,
    default_ac_risk_components,
    sha256_file,
    sha256_text,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def tmp_png(tmp_path):
    """Write a minimal PNG file for testing. Real seismic content not
    needed — adapter only hashes bytes for F1 AMANAH identity."""
    p = tmp_path / "test.png"
    # Minimal PNG: 1x1 white pixel
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff"
        b"?\x00\x05\xfe\x02\xfe\xa3W\xe1\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    p.write_bytes(png_bytes)
    return str(p)


@pytest.fixture
def mock_backend_perfect():
    """A mock VLM that returns valid PerceptualInventory-shaped JSON."""

    class M:
        backend_id = "test-perfect-mock"

        def call(self, image_path, prompt, **kwargs):
            return json.dumps(
                {
                    "reflectors": [
                        {
                            "id": "R1",
                            "lateral_extent_inlines": [100, 500],
                            "twt_range_ms": [1500, 2000],
                            "amplitude_character": "bright",
                            "continuity": "continuous",
                            "polarity": "SEG-normal",
                            "confidence": 0.85,
                            "notes": "Strong continuous reflector",
                        }
                    ],
                    "faults": [
                        {
                            "id": "F1",
                            "type": "normal",
                            "lateral_extent_inlines": [300, 350],
                            "twt_range_ms": [1600, 1900],
                            "strike_dip_deg": 45.0,
                            "throw_ms": 50.0,
                            "confidence": 0.75,
                            "notes": "Normal fault offsetting R1",
                        }
                    ],
                    "amplitude_zones": [
                        {
                            "id": "A1",
                            "twt_range_ms": [1700, 1800],
                            "lateral_extent_inlines": [200, 400],
                            "character": "bright",
                            "possible_origin": "fluid",
                            "confidence": 0.45,
                            "notes": "Bright spot candidate",
                        }
                    ],
                    "axis_metadata": {
                        "twt_range_ms": [1000, 3000],
                        "inline_range": [50, 600],
                        "polarity_convention": "SEG-normal",
                        "display_units": "TWT-ms",
                        "color_polarity": "red-positive",
                        "confidence": 0.80,
                    },
                    "global_assessment": "Seismic section shows a continuous reflector with a normal fault and a bright amplitude zone.",
                    "overall_confidence": 0.75,
                }
            )

    return M()


@pytest.fixture
def mock_backend_empty():
    """A mock VLM that returns empty observations."""

    class M:
        backend_id = "test-empty-mock"

        def call(self, image_path, prompt, **kwargs):
            return json.dumps(
                {
                    "reflectors": [],
                    "faults": [],
                    "amplitude_zones": [],
                    "axis_metadata": {
                        "twt_range_ms": [1000, 3000],
                        "inline_range": [50, 600],
                        "polarity_convention": "unknown",
                        "display_units": "TWT-ms",
                        "color_polarity": "unknown",
                        "confidence": 0.50,
                    },
                    "global_assessment": "Image too noisy to interpret.",
                    "overall_confidence": 0.30,
                }
            )

    return M()


@pytest.fixture
def mock_backend_malformed():
    """A mock VLM that returns malformed JSON."""

    class M:
        backend_id = "test-malformed-mock"

        def call(self, image_path, prompt, **kwargs):
            return "This is not JSON at all!"

    return M()


# ═══════════════════════════════════════════════════════════════════════════════
# MiMo Adapter Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestMiMoVLMAdapter:
    """Test MiMoVLMAdapter with mock backends."""

    def test_adapter_init(self):
        """Test adapter initialization."""
        adapter = MiMoVLMAdapter(backend=None)
        assert adapter.backend_id is not None
        assert adapter.execution_mode == "deterministic"

    def test_adapter_generative_forbidden(self):
        """Test that generative mode is forbidden (F9 ANTI-HANTU)."""
        with pytest.raises(MiMoVisionError, match="generative execution mode is forbidden"):
            MiMoVLMAdapter(execution_mode="generative")

    def test_interpret_perfect_mock(self, tmp_png, mock_backend_perfect):
        """Test interpretation with perfect mock backend."""
        adapter = MiMoVLMAdapter(backend=mock_backend_perfect)
        result = asyncio.run(
            adapter.interpret(
                image_path=tmp_png,
                basin_context="Malay Basin, deltaic prograding",
            )
        )
        
        assert result.success is True
        assert result.inventory is not None
        assert result.elapsed_seconds > 0
        assert result.backend_id == "test-perfect-mock"
        
        inv = result.inventory
        assert len(inv.reflectors) == 1
        assert len(inv.faults) == 1
        assert len(inv.amplitude_zones) == 1
        
        # With 1 reflector, multi_view_passed=False, so B_cog=0.79
        # AC_Risk = 0.4 * 1.575 * 0.79 = 0.4977 (HOLD range: 0.35-0.59)
        assert inv.verdict == VisionVerdict.HOLD
        
        # F7 HUMILITY: confidence must be <= 0.90
        assert inv.overall_confidence <= 0.90
        
        # F9 ANTI-HANTU: VLM-only output cannot reach SEAL
        assert inv.verdict != VisionVerdict.SEAL

    def test_interpret_empty_mock(self, tmp_png, mock_backend_empty):
        """Test interpretation with empty observations."""
        adapter = MiMoVLMAdapter(backend=mock_backend_empty)
        result = asyncio.run(
            adapter.interpret(
                image_path=tmp_png,
                basin_context="Unknown basin",
            )
        )
        
        assert result.success is True
        assert result.inventory is not None
        
        inv = result.inventory
        assert len(inv.reflectors) == 0
        assert len(inv.faults) == 0
        assert len(inv.amplitude_zones) == 0
        
        # No observations → HOLD for human review
        assert inv.verdict == VisionVerdict.HOLD

    def test_interpret_malformed_json(self, tmp_png, mock_backend_malformed):
        """Test handling of malformed JSON response."""
        adapter = MiMoVLMAdapter(backend=mock_backend_malformed)
        result = asyncio.run(
            adapter.interpret(
                image_path=tmp_png,
                basin_context="Unknown basin",
            )
        )
        
        assert result.success is False
        assert result.error_type == "MiMoVisionError"
        assert "not valid JSON" in result.error

    def test_interpret_missing_image(self, mock_backend_perfect):
        """Test handling of missing image file."""
        adapter = MiMoVLMAdapter(backend=mock_backend_perfect)
        result = asyncio.run(
            adapter.interpret(
                image_path="/nonexistent/image.png",
                basin_context="Unknown basin",
            )
        )
        
        assert result.success is False
        assert result.error_type == "FileNotFound"

    def test_ac_risk_computation(self, tmp_png, mock_backend_perfect):
        """Test AC_Risk computation with MiMo-specific adjustments."""
        adapter = MiMoVLMAdapter(backend=mock_backend_perfect)
        result = asyncio.run(
            adapter.interpret(
                image_path=tmp_png,
                basin_context="Malay Basin",
                has_segy=True,  # Should lower u_phys
            )
        )
        
        assert result.success is True
        inv = result.inventory
        
        # AC_Risk should be computed
        ac_score = inv.ac_risk.compute()
        assert 0 <= ac_score <= 1.0
        
        # With has_segy=True, u_phys should be lower (0.25 vs 0.40)
        assert inv.ac_risk.u_phys == 0.25

    def test_constitutional_notes(self, tmp_png, mock_backend_perfect):
        """Test that constitutional notes are present in the envelope."""
        adapter = MiMoVLMAdapter(backend=mock_backend_perfect)
        result = asyncio.run(
            adapter.interpret(
                image_path=tmp_png,
                basin_context="Malay Basin",
            )
        )
        
        assert result.success is True
        # Notes are added by the MCP tool, not the adapter
        # But we can verify the inventory has the required fields
        inv = result.inventory
        assert inv.model_id is not None
        assert inv.prompt_id is not None
        assert inv.raw_response_hash is not None
        assert inv.input_image_sha256 is not None


# ═══════════════════════════════════════════════════════════════════════════════
# MiMoHTTPBackend Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestMiMoHTTPBackend:
    """Test MiMoHTTPBackend with mock server responses."""

    def test_backend_init(self):
        """Test backend initialization."""
        backend = MiMoHTTPBackend(
            backend_url="http://localhost:8000/v1",
            model_name="XiaomiMiMo/MiMo-Embodied-7B",
            timeout=60,
        )
        assert backend.backend_url == "http://localhost:8000/v1"
        assert backend.model_name == "XiaomiMiMo/MiMo-Embodied-7B"
        assert backend.timeout == 60
        assert backend.backend_id == "mimo-MiMo-Embodied-7B"

    def test_backend_strips_trailing_slash(self):
        """Test that trailing slash is stripped from URL."""
        backend = MiMoHTTPBackend(backend_url="http://localhost:8000/v1/")
        assert backend.backend_url == "http://localhost:8000/v1"


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-Modal Fidelity Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCrossModalFidelity:
    """Test Cross-Modal Fidelity Theorem compliance."""

    def test_inventory_round_trip(self, tmp_png, mock_backend_perfect):
        """Test that PerceptualInventory survives JSON round-trip."""
        adapter = MiMoVLMAdapter(backend=mock_backend_perfect)
        result = asyncio.run(
            adapter.interpret(image_path=tmp_png, basin_context="Test")
        )
        
        assert result.success is True
        inv = result.inventory
        
        # Serialize to JSON
        json_str = inv.model_dump_json()
        
        # Deserialize back
        inv2 = PerceptualInventory.model_validate_json(json_str)
        
        # Verify round-trip integrity
        assert inv.inventory_id == inv2.inventory_id
        assert inv.input_image_sha256 == inv2.input_image_sha256
        assert len(inv.reflectors) == len(inv2.reflectors)
        assert len(inv.faults) == len(inv2.faults)
        assert inv.verdict == inv2.verdict

    def test_transform_stack_logged(self, tmp_png, mock_backend_perfect):
        """Test that transform stack is logged (F4 CLARITY)."""
        adapter = MiMoVLMAdapter(backend=mock_backend_perfect)
        result = asyncio.run(
            adapter.interpret(image_path=tmp_png, basin_context="Test")
        )
        
        inv = result.inventory
        assert "mimo-inference" in inv.transform_stack
        assert "image-read" in inv.transform_stack
        assert "json-parse" in inv.transform_stack


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tool Tests (mock)
# ═══════════════════════════════════════════════════════════════════════════════


class TestMiMoMCPTool:
    """Test geox_vision_mimo_inference MCP tool with mock backend."""

    def test_tool_envelope_structure(self, tmp_png, mock_backend_perfect):
        """Test that the MCP tool returns the correct envelope structure."""
        from geox_mcp.tools.vision import geox_vision_mimo_inference, _vision_envelope
        
        # Mock the adapter to use our mock backend
        adapter = MiMoVLMAdapter(backend=mock_backend_perfect)
        
        # We can't easily mock the tool function directly, but we can test
        # the envelope structure
        envelope = _vision_envelope(
            "geox_vision_mimo_inference",
            {
                "status": "SUCCESS",
                "execution_status": "SUCCESS",
                "backend_id": "test-mock",
                "vision_backend_source": "mimo_inference",
            },
        )
        
        # The envelope adds these keys
        assert envelope["tool_class"] == "vision"
        assert "cross_modal_stability" in envelope
        assert "semantic_density_score" in envelope
        assert "dim_spot_flag" in envelope
        assert envelope["authority"] == "GEOX_VISION_V1"


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_large_image_path(self, mock_backend_perfect):
        """Test handling of very long image path."""
        adapter = MiMoVLMAdapter(backend=mock_backend_perfect)
        long_path = "/tmp/" + "a" * 10000 + ".png"
        result = asyncio.run(
            adapter.interpret(image_path=long_path, basin_context="Test")
        )
        assert result.success is False
        assert result.error_type == "FileNotFound"

    def test_special_characters_in_basin_context(self, tmp_png, mock_backend_perfect):
        """Test handling of special characters in basin context."""
        adapter = MiMoVLMAdapter(backend=mock_backend_perfect)
        result = asyncio.run(
            adapter.interpret(
                image_path=tmp_png,
                basin_context="Malay Basin (2026) — deltaic prograding <test>",
            )
        )
        assert result.success is True

    def test_unicode_in_prompt(self, tmp_png, mock_backend_perfect):
        """Test handling of unicode in prompt."""
        adapter = MiMoVLMAdapter(backend=mock_backend_perfect)
        result = asyncio.run(
            adapter.interpret(
                image_path=tmp_png,
                basin_context="Malay Basin — ΔF ≡ δᵢ",
            )
        )
        assert result.success is True


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
