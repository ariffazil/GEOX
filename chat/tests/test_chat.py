"""Earth Witness chat proxy tests — checklist §9 acceptance surface.

The MCP layer is stubbed to the REAL geox_observe pipeline (deterministic mock
backend), so proxy logic is tested against genuine tool behaviour — no live
:8081 dependency, no external vision calls (I8).
"""

from __future__ import annotations

import hashlib
import io
import os
import time

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import chat.server as srv
from tests.earth_bench.earthbench import tiny_png_b64


class InProcessMcp:
    """Calls the real geox_observe impl with the deterministic mock backend."""

    def call_tool(self, name, arguments):
        assert name == "geox_observe"
        os.environ["GEOX_VISION_FORCE_MOCK"] = "1"
        os.environ["GEOX_VISION_MOCK_SCENARIO"] = os.environ.get("EW_TEST_SCENARIO", "limestone_outcrop")
        try:
            from geox_mcp.tools.earth_observe import geox_observe

            packet = geox_observe(**arguments)
        finally:
            os.environ.pop("GEOX_VISION_FORCE_MOCK", None)
            os.environ.pop("GEOX_VISION_MOCK_SCENARIO", None)
        return packet


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(srv, "_mcp", InProcessMcp())
    srv._rate.clear()
    return TestClient(srv.app)


def _jpeg_with_gps_tail() -> tuple[bytes, bytes]:
    """JPEG + trailing pseudo-EXIF GPS nonce. Returns (raw, cleaned_expected)."""
    img = Image.new("RGB", (16, 16), (120, 110, 90))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    raw = buf.getvalue() + b"\xff\xdaEXIFGPSNONCE1234567890"
    # replicate the server strip: decode pixels, re-encode
    clean_buf = io.BytesIO()
    im = Image.open(io.BytesIO(raw))
    clean = Image.new(im.mode, im.size)
    clean.putdata(list(im.getdata()))
    clean.save(clean_buf, format="JPEG", quality=92)
    return raw, clean_buf.getvalue()


def _jpeg_bytes(color: tuple[int, int, int] = (140, 120, 95), tail: bytes = b"") -> bytes:
    img = Image.new("RGB", (16, 16), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue() + tail


def _post(client, *, image=None, **form):
    if image is None:
        image = _jpeg_bytes()
    data = {
        "modality_hint": form.get("modality_hint", ""),
        "basin": form.get("basin", ""),
        "objective": form.get("objective", ""),
        "field_tests_json": form.get("field_tests_json", "{}"),
        "scale_json": form.get("scale_json", "{}"),
        "seismic_json": form.get("seismic_json", "{}"),
    }
    files = {"image": ("photo.jpg", image, "image/jpeg")}
    return client.post("/api/observe", data=data, files=files)


def test_basin_context_leaves_confidence_unchanged(client, monkeypatch):
    import base64 as b64

    png = b64.b64decode(tiny_png_b64().split(",", 1)[1])
    r1 = client.post(
        "/api/observe",
        data={"modality_hint": "rock", "field_tests_json": "{}", "scale_json": "{}", "seismic_json": "{}"},
        files={"image": ("p.png", png, "image/png")},
    )
    r2 = client.post(
        "/api/observe",
        data={"modality_hint": "rock", "basin": "Sabah", "field_tests_json": "{}", "scale_json": "{}", "seismic_json": "{}"},
        files={"image": ("p.png", png, "image/png")},
    )
    assert r1.status_code == r2.status_code == 200
    c1 = r1.json()["packet"]["epistemic"]["confidence"]
    c2 = r2.json()["packet"]["epistemic"]["confidence"]
    assert c1 == c2, "basin context must never inflate confidence (I7)"


def test_carbonate_without_acid_asks_for_hcl(client):
    r = _post(client, image=_jpeg_bytes(), modality_hint="rock")
    assert r.status_code == 200
    p = r.json()["packet"]
    assert p["epistemic"]["state"] == "INPUT_REQUIRED"
    reqs = [t["test_name"] for t in p["limitations"]["requested_human_tests"]]
    assert "dilute_hcl" in reqs


def test_fizz_powder_ranks_dolostone_first_and_stays_candidate(client):
    r = _post(client, image=_jpeg_bytes(), modality_hint="rock", field_tests_json='{"hcl": "weak_on_powder"}')
    assert r.status_code == 200
    p = r.json()["packet"]
    hyps = p["hypotheses"]
    assert hyps and "dolostone" in hyps[0]["label"].lower()
    # never an oracle: either still asking for tests or review-pending — never SEAL
    assert p["epistemic"]["state"] in ("INPUT_REQUIRED", "REVIEW_PENDING")
    assert p["epistemic"]["verdict"] != "SEAL"


def test_bright_spot_never_says_gas_and_requests_polarity(client, monkeypatch):
    monkeypatch.setenv("EW_TEST_SCENARIO", "seismic")
    r = _post(client, image=_jpeg_bytes((90,110,140)), modality_hint="seismic_display")
    assert r.status_code == 200
    p = r.json()["packet"]
    blob = " ".join(h["label"].lower() for h in p["hypotheses"])
    assert "gas" not in blob and "hydrocarbon" not in blob
    miss = " ".join(p["limitations"]["missing_metadata"]).lower()
    assert "polarity" in miss
    reqs = [t["test_name"] for t in p["limitations"]["requested_human_tests"]]
    assert "polarity_declaration" in reqs


def test_false_label_is_ocr_text_only(client, monkeypatch):
    monkeypatch.setenv("EW_TEST_SCENARIO", "seismic")
    r = _post(client, image=_jpeg_bytes((90,110,140)), modality_hint="seismic_display")
    p = r.json()["packet"]
    ocrs = " ".join(o["text"] for o in p["observations"]["ocr_text"])
    assert "Inline 1420" in ocrs
    ocr_words = {w.lower() for o in p["observations"]["ocr_text"] for w in o["text"].split() if len(w) > 4}
    for h in p["hypotheses"]:
        for s in h.get("supporting", []):
            assert str(s).lower() not in ocr_words, "OCR must never back an earth hypothesis"


def test_gps_stripped_and_no_disk_persistence(client, tmp_path, monkeypatch):
    raw, expected_clean = _jpeg_with_gps_tail()
    before = set(os.listdir("/tmp"))
    r = _post(client, image=raw, modality_hint="rock")
    assert r.status_code == 200
    p = r.json()["packet"]
    # hash recorded in provenance is of the CLEANED pixels, not the raw upload
    import base64 as b64

    sent_b64 = p  # packet only carries sha; recompute cleaned sha locally
    assert p["artifact"]["sha256"] == hashlib.sha256(expected_clean).hexdigest()
    assert p["artifact"]["sha256"] != hashlib.sha256(raw).hexdigest()
    # no new upload file left on disk
    time.sleep(0.1)
    after = set(os.listdir("/tmp"))
    new = {n for n in after - before if n.startswith(("photo", "upload", "tmp"))}
    assert not new, f"uploads must not persist: {new}"


def test_rate_limit_triggers_hold(client):
    ip = "testclient"
    srv._rate[ip] = [time.time()] * srv.PER_IP_MAX
    r = _post(client, image=_jpeg_bytes(), modality_hint="rock")
    assert r.status_code == 429
    assert r.json()["status"] == "HOLD"


def test_oversize_rejected(client):
    big = b"\x00" * (srv.MAX_BYTES + 1)
    r = _post(client, image=big, modality_hint="rock")
    assert r.status_code == 413


def test_malformed_upload_governed_415_not_500(client):
    """Garbage bytes and corrupt PDFs must be governed rejections, never unhandled 500s."""
    for payload, name, ctype in (
        (b"not-an-image-just-text-bytes", "x.bin", "application/octet-stream"),
        (b"%PDF-garbage-truncated", "x.pdf", "application/pdf"),
    ):
        r = client.post(
            "/api/observe",
            data={"modality_hint": "rock", "field_tests_json": "{}", "scale_json": "{}", "seismic_json": "{}"},
            files={"image": (name, payload, ctype)},
        )
        assert r.status_code == 415, f"{name!r} returned {r.status_code}, expected governed 415"
