"""
geox_observe artifact resolution — fail closed, never send the path as image bytes
═════════════════════════════════════════════════════════════════════════════════
2026-11-04 (333-AGI). Regression cover for the D-1 defect:

geox-mcp runs with PrivateTmp=true, so a caller's /tmp path is invisible to the
organ. earth_observe used to fall back to `artifact_ref.encode("utf-8")` and send
the PATH TEXT to the vision provider as image bytes. The provider rejected the
message shape ("messages[1].content must be a string") and the organ surfaced a
FATAL INTERNAL_ERROR "server bug" — a client input error dressed as an organ bug,
with a paid VLM call burnt on garbage.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import base64

import pytest


def test_unreadable_path_holds_instead_of_sending_path_bytes():
    from geox_mcp.tools.earth_observe import geox_observe

    r = geox_observe(
        artifact_ref="/tmp/definitely-not-visible-to-the-organ/photo.png",
        modality_hint="rock",
    )
    assert r.get("isError") is True
    assert r.get("status") == "HOLD"
    assert r.get("error_class") == "ARTIFACT_NOT_READABLE"
    assert r.get("severity") == "RECOVERABLE"
    assert "PrivateTmp" in (r.get("hint") or "")
    # it must NOT have produced an observation packet
    assert "packet_id" not in r


def test_plain_text_artifact_is_rejected_as_not_an_image():
    from geox_mcp.tools.earth_observe import geox_observe

    r = geox_observe(artifact_ref="this is not an image at all", modality_hint="rock")
    assert r.get("isError") is True
    assert r.get("error_class") == "ARTIFACT_NOT_READABLE"


def test_base64_image_is_accepted():
    """Inline base64 (no data: prefix) still works — the real feature stays."""
    import numpy as np
    from PIL import Image

    from geox_mcp.tools.earth_observe import geox_observe

    buf = "/tmp/opencode/_obs_b64_probe.png"
    Image.fromarray((np.random.default_rng(5).random((48, 48, 3)) * 255).astype("uint8"), "RGB").save(buf)
    b64 = base64.b64encode(open(buf, "rb").read()).decode()

    # patch the vision backend so the test does not spend a VLM call
    import geox_mcp.tools.earth_observe as eo

    class _Stub:
        backend_name = "stub"

        def inspect_artifact(self, **kw):
            assert len(kw["image_bytes"]) > 100, "image bytes were not resolved"
            return type(
                "R",
                (),
                {
                    "backend_name": "stub",
                    "model_id": "stub",
                    "latency_ms": 1,
                    "response_hash": "stub",
                    "raw_response": {
                        "modality": "rock",
                        "visible_features": [],
                        "ocr_text": [],
                        "measurements": [],
                        "hypotheses": [],
                        "limitations": {"image_cannot_determine": []},
                    },
                },
            )()

    orig = eo.get_vision_backend
    eo.get_vision_backend = lambda: _Stub()
    try:
        r = eo.geox_observe(artifact_ref=b64, modality_hint="rock")
    finally:
        eo.get_vision_backend = orig
    assert not r.get("isError"), r.get("message")
    assert r.get("packet_id")


def test_data_uri_image_is_accepted():
    import numpy as np
    from PIL import Image

    from geox_mcp.tools.earth_observe import geox_observe

    buf = "/tmp/opencode/_obs_datauri_probe.png"
    Image.fromarray((np.random.default_rng(6).random((48, 48, 3)) * 255).astype("uint8"), "RGB").save(buf)
    uri = "data:image/png;base64," + base64.b64encode(open(buf, "rb").read()).decode()

    import geox_mcp.tools.earth_observe as eo

    class _Stub:
        def inspect_artifact(self, **kw):
            assert kw["image_bytes"][:4] == b"\x89PNG", "not a PNG payload"
            return type(
                "R",
                (),
                {
                    "backend_name": "stub",
                    "model_id": "stub",
                    "latency_ms": 1,
                    "response_hash": "stub",
                    "raw_response": {
                        "modality": "rock",
                        "visible_features": [],
                        "ocr_text": [],
                        "measurements": [],
                        "hypotheses": [],
                        "limitations": {"image_cannot_determine": []},
                    },
                },
            )()

    orig = eo.get_vision_backend
    eo.get_vision_backend = lambda: _Stub()
    try:
        r = eo.geox_observe(artifact_ref=uri, modality_hint="rock")
    finally:
        eo.get_vision_backend = orig
    assert not r.get("isError"), r.get("message")
    assert r.get("packet_id")


def test_provider_400_is_classified_as_input_error_not_server_bug():
    from geox_mcp.federation_safety import classify_error

    err = Exception("HTTP Error 400: Bad Request")
    r = classify_error(err, source_tool="geox_observe", source_organ="geox")
    assert r["error_class"] == "BAD_INPUT_VALUE"
    assert r["severity"] == "RECOVERABLE"
    assert r["suspected_layer"] == "input_validation"
    assert "server bug" not in r["next_action"]


def test_image_magic_detector():
    from geox_mcp.tools.earth_observe import _looks_like_image

    assert _looks_like_image(b"\x89PNG\r\n\x1a\n" + b"0" * 20)
    assert _looks_like_image(b"\xff\xd8\xff\xe0" + b"0" * 20)
    assert _looks_like_image(b"RIFF" + b"0000" + b"WEBP" + b"0" * 8)
    assert not _looks_like_image(b"/tmp/some/path.png")
    assert not _looks_like_image(b"")
