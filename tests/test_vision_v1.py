"""
GEOX Vision V1 — Test Suite
══════════════════════════════════════════════════════════════════════════
Forged 2026-06-07 — DITEMPA BUKAN DIBERI

Covers:
- PerceptualInventory schema validation (F1/F4/F7/F9/F13 enforcement)
- AC_Risk computation (per TOAC_CANON.md thresholds)
- MiniMaxVLMAdapter parsing (mock + real VLM responses)
- Vision test harness (synthetic forward-inverse)
- Cross-Modal Fidelity Theorem round-trip integrity
- No canonical registry mutation (sanity check on the forge itself)

Run with:
    PYTHONPATH=src pytest tests/test_vision_v1.py -v
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
    MiniMaxVLMAdapter,
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
    AntiHantuError,
    VisionResult,
)
from geox_core.engines.vision.vision_test_harness import (
    build_synthetic_2d_section,
    render_section_to_png,
    compare_to_ground_truth,
    run_synthetic_forward_inverse,
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
                            "lateral_extent_inlines": [0, 100],
                            "twt_range_ms": [400, 600],
                            "amplitude_character": "bright",
                            "continuity": "continuous",
                            "polarity": "SEG-normal",
                            "confidence": 0.7,
                        },
                    ],
                    "faults": [
                        {
                            "id": "F1",
                            "type": "normal",
                            "lateral_extent_inlines": [40, 60],
                            "twt_range_ms": [0, 2000],
                            "strike_dip_deg": 75,
                            "throw_ms": 50,
                            "confidence": 0.6,
                        },
                    ],
                    "amplitude_zones": [
                        {
                            "id": "A1",
                            "twt_range_ms": [1000, 1100],
                            "lateral_extent_inlines": [20, 80],
                            "character": "bright",
                            "possible_origin": "lithology",
                            "confidence": 0.5,
                        },
                    ],
                    "axis_metadata": {
                        "twt_range_ms": [0, 2000],
                        "inline_range": [0, 100],
                        "polarity_convention": "SEG-normal",
                        "display_units": "TWT-ms",
                        "color_polarity": "red-positive",
                        "confidence": 0.8,
                    },
                    "global_assessment": "Test section",
                    "overall_confidence": 0.6,
                }
            )

    return M()


@pytest.fixture
def mock_backend_overconfident():
    """A mock that returns 0.95 confidence — should be rejected by F7."""

    class M:
        backend_id = "test-overconfident"

        def call(self, image_path, prompt, **kwargs):
            return json.dumps(
                {
                    "reflectors": [],
                    "faults": [],
                    "amplitude_zones": [],
                    "axis_metadata": {
                        "twt_range_ms": [0, 2000],
                        "inline_range": [0, 100],
                        "polarity_convention": "unknown",
                        "display_units": "unknown",
                        "color_polarity": "unknown",
                        "confidence": 0.5,
                    },
                    "global_assessment": "Nothing",
                    "overall_confidence": 0.95,  # > 0.90 hard cap
                }
            )

    return M()


# ═══════════════════════════════════════════════════════════════════════════════
# PerceptualInventory schema tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPerceptualInventory:
    def test_default_ac_risk_unverified(self):
        ac = default_ac_risk_components()
        # 0.45 * 2.10 * 0.79 = 0.747 (capped) — but with default components
        # let me just check the verdict is HOLD or VOID for unaided VLM
        verdict = ac.to_verdict()
        assert verdict in (AcRiskVerdict.HOLD, AcRiskVerdict.VOID)

    def test_default_ac_risk_multiview_lowers(self):
        ac_unverified = default_ac_risk_components(multi_view_passed=False)
        ac_mv = default_ac_risk_components(multi_view_passed=True)
        assert ac_mv.compute() < ac_unverified.compute()

    def test_default_ac_risk_physics_validated_lowers_further(self):
        ac_mv = default_ac_risk_components(multi_view_passed=True)
        ac_pv = default_ac_risk_components(physics_validated=True)
        assert ac_pv.compute() < ac_mv.compute()

    def test_d_transform_bounded(self):
        for stack in [
            ["image-read"],
            ["image-read", "vlm-inference", "json-parse"],
            ["image-read", "vlm-inference", "vlm-inference", "vlm-inference"],
        ]:
            ac = default_ac_risk_components(transform_stack=stack)
            assert 1.0 <= ac.d_transform <= 3.0

    def test_f7_humility_hard_cap(self, tmp_png):
        """overall_confidence > 0.90 must be rejected."""
        with pytest.raises(Exception) as excinfo:
            PerceptualInventory(
                inventory_id="test_f7",
                image_path=tmp_png,
                input_image_sha256="a" * 64,
                global_assessment="test",
                overall_confidence=0.95,
                model_id="m",
                prompt_id="p",
                raw_response_hash="h",
                ac_risk=default_ac_risk_components(),
                axis_metadata=AxisMetadata(
                    twt_range_ms=(0, 1000),
                    inline_range=(0, 1000),
                    polarity_convention=PolarityConvention.UNKNOWN,
                    display_units=DisplayUnits.TWT_MS,
                    color_polarity=DisplayColorPolarity.UNKNOWN,
                    confidence=0.5,
                ),
            )
        assert "F7" in str(excinfo.value) or "0.9" in str(excinfo.value)

    def test_f9_anti_hantu_seal_without_physics(self, tmp_png):
        """verdict=SEAL with physics_validated=False must be rejected."""
        with pytest.raises(Exception) as excinfo:
            PerceptualInventory(
                inventory_id="test_f9",
                image_path=tmp_png,
                input_image_sha256="b" * 64,
                global_assessment="test",
                overall_confidence=0.5,
                model_id="m",
                prompt_id="p",
                raw_response_hash="h",
                verdict=VisionVerdict.SEAL,
                ac_risk=default_ac_risk_components(),
                axis_metadata=AxisMetadata(
                    twt_range_ms=(0, 1000),
                    inline_range=(0, 1000),
                    polarity_convention=PolarityConvention.UNKNOWN,
                    display_units=DisplayUnits.TWT_MS,
                    color_polarity=DisplayColorPolarity.UNKNOWN,
                    confidence=0.5,
                ),
            )
        assert "F9" in str(excinfo.value) or "ANTI-HANTU" in str(excinfo.value)

    def test_f13_fluid_zone_sets_human_review(self, tmp_png):
        inv = PerceptualInventory(
            inventory_id="test_f13",
            image_path=tmp_png,
            input_image_sha256="c" * 64,
            global_assessment="test",
            overall_confidence=0.5,
            model_id="m",
            prompt_id="p",
            raw_response_hash="h",
            ac_risk=default_ac_risk_components(),
            axis_metadata=AxisMetadata(
                twt_range_ms=(0, 1000),
                inline_range=(0, 1000),
                polarity_convention=PolarityConvention.UNKNOWN,
                display_units=DisplayUnits.TWT_MS,
                color_polarity=DisplayColorPolarity.UNKNOWN,
                confidence=0.5,
            ),
            amplitude_zones=[
                AmplitudeZoneObservation(
                    zone_id="A1",
                    twt_range_ms=(1000, 1100),
                    lateral_extent_inlines=(0, 100),
                    character=AmplitudeZoneCharacter.BRIGHT,
                    possible_origin=AmplitudeZoneOrigin.FLUID,
                    confidence=0.7,
                )
            ],
        )
        assert inv.human_review_required is True

    def test_f13_hold_verdict_sets_human_review(self, tmp_png):
        inv = PerceptualInventory(
            inventory_id="test",
            image_path=tmp_png,
            input_image_sha256="d" * 64,
            global_assessment="test",
            overall_confidence=0.5,
            model_id="m",
            prompt_id="p",
            raw_response_hash="h",
            verdict=VisionVerdict.HOLD,
            ac_risk=default_ac_risk_components(),
            axis_metadata=AxisMetadata(
                twt_range_ms=(0, 1000),
                inline_range=(0, 1000),
                polarity_convention=PolarityConvention.UNKNOWN,
                display_units=DisplayUnits.TWT_MS,
                color_polarity=DisplayColorPolarity.UNKNOWN,
                confidence=0.5,
            ),
        )
        assert inv.human_review_required is True

    def test_to_json_canonical_round_trip(self, tmp_png):
        inv = PerceptualInventory(
            inventory_id="test_roundtrip",
            image_path=tmp_png,
            input_image_sha256="e" * 64,
            global_assessment="test",
            overall_confidence=0.5,
            model_id="m",
            prompt_id="p",
            raw_response_hash="f" * 64,
            ac_risk=default_ac_risk_components(),
            axis_metadata=AxisMetadata(
                twt_range_ms=(0, 1000),
                inline_range=(0, 1000),
                polarity_convention=PolarityConvention.UNKNOWN,
                display_units=DisplayUnits.TWT_MS,
                color_polarity=DisplayColorPolarity.UNKNOWN,
                confidence=0.5,
            ),
        )
        # Per Cross-Modal Fidelity Theorem, round-trip should preserve
        s = inv.to_json_canonical()
        inv2 = PerceptualInventory.model_validate_json(s)
        assert inv.inventory_id == inv2.inventory_id
        assert inv.input_image_sha256 == inv2.input_image_sha256

    def test_seal_receipt_format(self, tmp_png):
        inv = PerceptualInventory(
            inventory_id="test_seal",
            image_path=tmp_png,
            input_image_sha256="g" * 64,
            global_assessment="test",
            overall_confidence=0.5,
            model_id="m",
            prompt_id="p",
            raw_response_hash="h",
            ac_risk=default_ac_risk_components(),
            axis_metadata=AxisMetadata(
                twt_range_ms=(0, 1000),
                inline_range=(0, 1000),
                polarity_convention=PolarityConvention.UNKNOWN,
                display_units=DisplayUnits.TWT_MS,
                color_polarity=DisplayColorPolarity.UNKNOWN,
                confidence=0.5,
            ),
        )
        r = inv.to_seal_receipt()
        assert r["verdict"] == "INTERPRETATION"
        assert r["n_reflectors"] == 0
        assert 0.0 <= r["ac_risk"] <= 1.0

    def test_sha256_helpers(self, tmp_png):
        h1 = sha256_file(tmp_png)
        h2 = hashlib.sha256(open(tmp_png, "rb").read()).hexdigest()
        assert h1 == h2
        assert sha256_text("hello") == hashlib.sha256(b"hello").hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# Adapter tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestMiniMaxVLMAdapter:
    def test_jitu_circuit_breaker(self):
        """Generative execution mode must be rejected (F9 ANTI-HANTU)."""
        with pytest.raises(AntiHantuError):
            MiniMaxVLMAdapter(execution_mode="generative")

    def test_file_not_found(self):
        adapter = MiniMaxVLMAdapter()
        result = asyncio.run(adapter.interpret(image_path="/nonexistent.png"))
        assert not result.success
        assert result.error_type == "FileNotFound"

    @pytest.mark.asyncio
    async def test_perfect_mock_parses(self, tmp_png, mock_backend_perfect):
        adapter = MiniMaxVLMAdapter(backend=mock_backend_perfect)
        result = await adapter.interpret(image_path=tmp_png)
        assert result.success
        # The mock returns "correct" observations but is still a VLM-only
        # input (no multi-view, no physics). AC_Risk = 0.45 * 2.32 * 0.79 = 0.825
        # → VOID. The harness correctly identifies this as unsafe to seal.
        # What we test here is that PARSING succeeded, not that the
        # verdict is sealable.
        assert result.inventory.verdict in (
            VisionVerdict.INTERPRETATION,
            VisionVerdict.QUALIFY,
            VisionVerdict.HOLD,
            VisionVerdict.VOID,
        )
        assert len(result.inventory.reflectors) == 1
        assert len(result.inventory.faults) == 1
        assert len(result.inventory.amplitude_zones) == 1

    @pytest.mark.asyncio
    async def test_overconfident_rejected(self, tmp_png, mock_backend_overconfident):
        """F7 hard cap should reject 0.95 confidence."""
        adapter = MiniMaxVLMAdapter(backend=mock_backend_overconfident)
        result = await adapter.interpret(image_path=tmp_png)
        assert not result.success
        assert result.error_type == "ValidationError"
        assert "0.9" in result.error or "F7" in result.error

    @pytest.mark.asyncio
    async def test_malformed_json_rejected(self, tmp_png):
        class BadJsonMock:
            backend_id = "bad-json"

            def call(self, image_path, prompt, **kwargs):
                return "this is not json at all {"

        adapter = MiniMaxVLMAdapter(backend=BadJsonMock())
        result = await adapter.interpret(image_path=tmp_png)
        assert not result.success
        assert result.error_type == "AntiHantuError"

    @pytest.mark.asyncio
    async def test_missing_axis_metadata_rejected(self, tmp_png):
        class NoAxisMock:
            backend_id = "no-axis"

            def call(self, image_path, prompt, **kwargs):
                return json.dumps(
                    {
                        "reflectors": [],
                        "faults": [],
                        "amplitude_zones": [],
                        # axis_metadata missing!
                        "global_assessment": "test",
                        "overall_confidence": 0.5,
                    }
                )

        adapter = MiniMaxVLMAdapter(backend=NoAxisMock())
        result = await adapter.interpret(image_path=tmp_png)
        assert not result.success
        assert result.error_type == "AntiHantuError"
        assert "axis" in result.error.lower()

    @pytest.mark.asyncio
    async def test_lenient_enum_handling(self, tmp_png):
        """Non-canonical enum values should be mapped to OTHER/UNKNOWN via
        _missing_ methods, not crash the whole inventory."""

        class LenientMock:
            backend_id = "lenient"

            def call(self, image_path, prompt, **kwargs):
                return json.dumps(
                    {
                        "reflectors": [
                            {
                                "id": "R1",
                                "lateral_extent_inlines": [0, 100],
                                "twt_range_ms": [400, 600],
                                "amplitude_character": "weird-description",  # not in enum
                                "continuity": "continuous",
                                "polarity": "unknown",
                                "confidence": 0.5,
                            }
                        ],
                        "faults": [],
                        "amplitude_zones": [
                            {
                                "id": "A1",
                                "twt_range_ms": [1000, 1100],
                                "lateral_extent_inlines": [20, 80],
                                "character": "frobnicated",  # not in enum
                                "possible_origin": "yogic",  # not in enum
                                "confidence": 0.5,
                            }
                        ],
                        "axis_metadata": {
                            "twt_range_ms": [0, 2000],
                            "inline_range": [0, 100],
                            "polarity_convention": "SEG-normal",
                            "display_units": "ms",  # not in enum
                            "color_polarity": "red-positive",
                            "confidence": 0.8,
                        },
                        "global_assessment": "Lenient test",
                        "overall_confidence": 0.5,
                    }
                )

        adapter = MiniMaxVLMAdapter(backend=LenientMock())
        result = await adapter.interpret(image_path=tmp_png)
        # Axis is mapped to UNKNOWN, character/origin to OTHER/UNKNOWN
        assert result.success
        assert result.inventory.axis_metadata.display_units == DisplayUnits.UNKNOWN
        assert result.inventory.amplitude_zones[0].character == AmplitudeZoneCharacter.OTHER
        assert result.inventory.amplitude_zones[0].possible_origin == AmplitudeZoneOrigin.UNKNOWN


# ═══════════════════════════════════════════════════════════════════════════════
# Vision test harness tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestVisionTestHarness:
    def test_synthetic_section_build(self):
        section, gt = build_synthetic_2d_section(seed=42)
        assert section.shape == (300, 200)  # n_twt, n_inlines
        assert len(gt.reflectors) == 4
        assert len(gt.faults) == 1
        assert len(gt.bright_zones) == 1

    def test_render_to_png(self, tmp_path):
        section, gt = build_synthetic_2d_section(seed=42)
        out = str(tmp_path / "test.png")
        p = render_section_to_png(section, gt, out)
        assert os.path.exists(p)
        assert os.path.getsize(p) > 1000  # not empty

    def test_compare_perfect_match(self):
        section, gt = build_synthetic_2d_section(seed=42)
        # Build a perfect inventory
        inv = PerceptualInventory(
            inventory_id="test_perfect",
            image_path="/tmp/x.png",
            input_image_sha256="a" * 64,
            global_assessment="perfect",
            overall_confidence=0.7,
            model_id="m",
            prompt_id="p",
            raw_response_hash="h",
            ac_risk=default_ac_risk_components(),
            axis_metadata=AxisMetadata(
                twt_range_ms=gt.twt_range_ms,
                inline_range=gt.inline_range,
                polarity_convention=PolarityConvention.SEG_NORMAL,
                display_units=DisplayUnits.TWT_MS,
                color_polarity=DisplayColorPolarity.RED_POSITIVE,
                confidence=0.8,
            ),
            reflectors=[
                ReflectorObservation(
                    reflector_id=f"R{i + 1}",
                    lateral_extent_inlines=(0, gt.n_inlines),
                    twt_range_ms=(r["twt_range_ms"][0] - 5, r["twt_range_ms"][1] + 5),
                    amplitude_character=AmplitudeCharacter.BRIGHT if r["amplitude_sign"] > 0 else AmplitudeCharacter.DIM,
                    continuity=ReflectorContinuity.CONTINUOUS,
                    polarity=PolarityConvention.SEG_NORMAL,
                    confidence=0.7,
                )
                for i, r in enumerate(gt.reflectors)
            ],
            faults=[
                FaultObservation(
                    fault_id="F1",
                    type=FaultType.NORMAL,
                    lateral_extent_inlines=(gt.faults[0]["inline_center"] - 10, gt.faults[0]["inline_center"] + 10),
                    twt_range_ms=gt.faults[0]["twt_range_ms"],
                    confidence=0.7,
                ),
            ],
            amplitude_zones=[
                AmplitudeZoneObservation(
                    zone_id="A1",
                    twt_range_ms=z["twt_range_ms"],
                    lateral_extent_inlines=z["lateral_extent_inlines"],
                    character=AmplitudeZoneCharacter.BRIGHT,
                    possible_origin=AmplitudeZoneOrigin.LITHOLOGY,
                    confidence=0.6,
                )
                for z in gt.bright_zones
            ],
        )
        pr = compare_to_ground_truth(inv, gt)
        assert pr["reflectors"]["precision"] == 1.0
        assert pr["reflectors"]["recall"] == 1.0
        assert pr["faults"]["recall"] == 1.0
        assert pr["zones"]["recall"] == 1.0

    def test_compare_phantom_detected(self):
        section, gt = build_synthetic_2d_section(seed=42)
        # Add a phantom reflector
        inv = PerceptualInventory(
            inventory_id="test_phantom",
            image_path="/tmp/x.png",
            input_image_sha256="a" * 64,
            global_assessment="phantom",
            overall_confidence=0.5,
            model_id="m",
            prompt_id="p",
            raw_response_hash="h",
            ac_risk=default_ac_risk_components(),
            axis_metadata=AxisMetadata(
                twt_range_ms=gt.twt_range_ms,
                inline_range=gt.inline_range,
                polarity_convention=PolarityConvention.SEG_NORMAL,
                display_units=DisplayUnits.TWT_MS,
                color_polarity=DisplayColorPolarity.RED_POSITIVE,
                confidence=0.5,
            ),
            reflectors=[
                ReflectorObservation(
                    reflector_id="R_phantom",
                    lateral_extent_inlines=(0, 100),
                    twt_range_ms=(950, 1000),  # not in any GT reflector
                    amplitude_character=AmplitudeCharacter.DIM,
                    continuity=ReflectorContinuity.DISCONTINUOUS,
                    polarity=PolarityConvention.UNKNOWN,
                    confidence=0.4,
                ),
            ],
        )
        pr = compare_to_ground_truth(inv, gt)
        assert pr["reflectors"]["false_positives"][0]["vlm_id"] == "R_phantom"
        assert pr["reflectors"]["precision"] == 0.0  # 1 FP, 0 TP
        assert pr["reflectors"]["recall"] == 0.0  # 4 GT not detected

    @pytest.mark.asyncio
    async def test_full_harness_run_with_perfect_mock(self, tmp_path):
        from geox_core.engines.vision.vision_test_harness import run_synthetic_forward_inverse

        class M:
            backend_id = "test-perfect"

            def call(self, image_path, prompt, **kwargs):
                return json.dumps(
                    {
                        "reflectors": [
                            {
                                "id": "R1",
                                "lateral_extent_inlines": [0, 200],
                                "twt_range_ms": [380, 420],
                                "amplitude_character": "bright",
                                "continuity": "continuous",
                                "polarity": "SEG-normal",
                                "confidence": 0.7,
                            },
                            {
                                "id": "R2",
                                "lateral_extent_inlines": [0, 200],
                                "twt_range_ms": [780, 820],
                                "amplitude_character": "bright",
                                "continuity": "continuous",
                                "polarity": "SEG-normal",
                                "confidence": 0.7,
                            },
                            {
                                "id": "R3",
                                "lateral_extent_inlines": [130, 200],
                                "twt_range_ms": [1180, 1220],
                                "amplitude_character": "dim",
                                "continuity": "discontinuous",
                                "polarity": "SEG-reverse",
                                "confidence": 0.7,
                            },
                            {
                                "id": "R4",
                                "lateral_extent_inlines": [0, 200],
                                "twt_range_ms": [1480, 1520],
                                "amplitude_character": "variable",
                                "continuity": "discontinuous",
                                "polarity": "unknown",
                                "confidence": 0.5,
                            },
                        ],
                        "faults": [
                            {
                                "id": "F1",
                                "type": "normal",
                                "lateral_extent_inlines": [120, 140],
                                "twt_range_ms": [0, 2000],
                                "strike_dip_deg": 75,
                                "throw_ms": 80,
                                "confidence": 0.7,
                            },
                        ],
                        "amplitude_zones": [
                            {
                                "id": "A1",
                                "twt_range_ms": [1100, 1250],
                                "lateral_extent_inlines": [70, 160],
                                "character": "bright",
                                "possible_origin": "lithology",
                                "confidence": 0.6,
                            },
                        ],
                        "axis_metadata": {
                            "twt_range_ms": [0, 2000],
                            "inline_range": [0, 200],
                            "polarity_convention": "SEG-normal",
                            "display_units": "TWT-ms",
                            "color_polarity": "red-positive",
                            "confidence": 0.8,
                        },
                        "global_assessment": "Test",
                        "overall_confidence": 0.6,
                    }
                )

        report = await run_synthetic_forward_inverse(
            backend=M(),
            output_png=str(tmp_path / "synth.png"),
            output_report=str(tmp_path / "synth_report.json"),
        )
        assert report.vision_verdict != "VOID"
        assert report.precision_recall["reflectors"]["f1"] >= 0.9


# ═══════════════════════════════════════════════════════════════════════════════
# Forge integrity check — verify the forge itself didn't touch the
# canonical registry (F13 SOVEREIGN territory is preserved).
# ═══════════════════════════════════════════════════════════════════════════════


class TestForgeIntegrity:
    def test_canonical_registry_unchanged(self):
        """The vision V1 forge must NOT have modified the canonical
        tool registry in src/geox_mcp/server.py:CANONICAL_PUBLIC_TOOLS.
        This is F13 SOVEREIGN territory per GEOX AGENTS.md."""
        from pathlib import Path

        # Find the canonical registry file. The registry lives in
        # src/geox_mcp/server.py per GEOX AGENTS.md "modern dimension-native layout"
        registry_files = [
            GEOX_SRC / "geox_mcp" / "server.py",
        ]
        for path in registry_files:
            if not path.exists():
                continue
            content = path.read_text()
            # These are the existing canonical tools that must not be mutated
            must_exist = [
                "geox_claim_create",
                "geox_claim_validate",
                "geox_claim_seal",
                "geox_horizon_contrast_surface",
            ]
            for tool in must_exist:
                # The new vision forge must NOT have removed these
                assert tool in content, (
                    f"CORE INVARIANT VIOLATION: {tool} missing from {path}. "
                    f"The vision V1 forge may have accidentally mutated the "
                    f"canonical tool registry. Per GEOX AGENTS.md, this is "
                    f"888_HOLD territory."
                )

    def test_vision_module_does_not_export_canonical_tool(self):
        """The vision V1 module must NOT export tools that look like
        canonical geox_* tools (those require 888_HOLD). It can export
        Python functions but not FastMCP-registered tools."""
        import geox_core.engines.vision as vision

        # Vision module is additive scaffolding, not a tool registration
        assert hasattr(vision, "MiniMaxVLMAdapter")
        # It should NOT have any tool decorated with @mcp.tool
        # (this is just an import-level check; the real test is no
        # canonical registry change)
        assert "geox_seismic_vision_ingest" not in dir(vision)  # not yet built
