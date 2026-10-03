"""Runtime-hotfix guard tests — K-DIP / K-THROW hallucination block.

Origin: uncommitted runtime hotfix found on /opt/geox (2026-10-03, author
UNKNOWN, preserved in stash@{0}) and uplifted to source. A vision-language
model cannot measure dip in degrees or throw in milliseconds from a picture;
soliciting them produced hallucinated geometry piped into K-DIP / K-THROW /
K-EXT-DIP. These tests pin the guarantee: the adapter NEVER populates
strike_dip_deg / throw_ms from VLM output, even when the model volunteers them.
"""

from __future__ import annotations

import asyncio
import json

from geox_core.engines.vision.mimo_vlm_adapter import MiMoVLMAdapter
from geox_core.earth_witness.vision_backend import GeminiVertexVisionBackend  # noqa: F401 — import guard


class _FakeBackend:
    backend_id = "fake-vlm"

    def call(self, image_path: str, prompt: str, **kwargs) -> str:  # noqa: ARG002
        # The VLM HALLUCINATES geometry fields — exactly the failure mode.
        return json.dumps(
            {
                "reflectors": [],
                "faults": [
                    {
                        "id": "F1",
                        "type": "normal",
                        "lateral_extent_inlines": [100, 200],
                        "twt_range_ms": [1200, 1400],
                        "strike_dip_deg": 37.5,
                        "throw_ms": 45.0,
                        "confidence": 0.8,
                    }
                ],
                "amplitude_zones": [],
                "axis_metadata": {
                    "twt_range_ms": [0, 3000],
                    "inline_range": [1000, 2000],
                    "polarity_convention": "unknown",
                    "display_units": "TWT-ms",
                    "color_polarity": "unknown",
                    "confidence": 0.5,
                },
                "global_assessment": "test",
                "overall_confidence": 0.5,
            }
        )


def test_vlm_hallucinated_strike_dip_and_throw_are_dropped(tmp_path):
    img = tmp_path / "section.png"
    img.write_bytes(b"\x89PNG fake")
    adapter = MiMoVLMAdapter(backend=_FakeBackend())
    result = asyncio.run(adapter.interpret(str(img)))
    assert result.success, result.error
    faults = result.inventory.faults
    assert len(faults) == 1
    f = faults[0]
    # The hallucinated geometry MUST be None — deterministic lanes are the
    # only producers of dip/throw (structure_tensor, calibration_derive).
    assert f.strike_dip_deg is None, "VLM strike_dip_deg leaked into fault facts"
    assert f.throw_ms is None, "VLM throw_ms leaked into fault facts"
