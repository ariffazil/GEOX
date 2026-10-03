"""Earth Witness Chat — local proxy server (checklist §2-§4, §7).

Binds 127.0.0.1 ONLY. Calls geox_observe through local MCP :8081. Returns the
coordinator packet only. No disk persistence of uploads; no writes to
earth_memory.db or VAULT999. Public exposure (Caddy) is a Gate 6 Class-B
decision — do not rebind without ARIF's APPROVE.

Run:  python3 -m uvicorn chat.server:app --host 127.0.0.1 --port 8765
"""

from __future__ import annotations

import base64
import io
import os
import secrets
import time
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from chat.forbidden_scan import scan_reply
from chat.mcp_client import McpClient, McpError

app = FastAPI(title="GEOX Earth Witness Chat", docs_url=None, redoc_url=None)

MAX_BYTES = 10 * 1024 * 1024  # checklist §2
ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "application/pdf": "pdf"}
SESSION_TTL = 30 * 60  # checklist §7
PER_IP_WINDOW = 60.0
PER_IP_MAX = 10
DAILY_BUDGET = int(os.getenv("EARTH_WITNESS_DAILY_BUDGET", "200"))
# Secure cookie behind the TLS vhost (Gate checklist F). Local plain-http
# dev may set EARTH_WITNESS_COOKIE_SECURE=0; prod default is ON.
COOKIE_SECURE = os.getenv("EARTH_WITNESS_COOKIE_SECURE", "1") == "1"

_mcp = McpClient()
_sessions: dict[str, float] = {}
_rate: dict[str, list[float]] = {}
_SESSION_CAP = 10_000
_RATE_CAP = 10_000


def _prune_states(now: float) -> None:
    """Bounded-memory guard (hardening 2026-10-03): expired keys are dropped once
    the state dicts grow past their caps, so memory is bounded between restarts."""
    if len(_sessions) > _SESSION_CAP:
        for k in [k for k, t in _sessions.items() if now - t >= SESSION_TTL]:
            _sessions.pop(k, None)
    if len(_rate) > _RATE_CAP:
        for k in [k for k, w in _rate.items() if not w or now - w[-1] >= PER_IP_WINDOW]:
            _rate.pop(k, None)


_budget = {"day": time.gmtime().tm_yday, "used": 0}
STATICS = os.path.join(os.path.dirname(__file__), "static")


def _hold(reason: str) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "status": "HOLD",
            "reason": reason,
            "verdict": "HOLD — observation budget or rate limit reached. Try later; nothing was guessed to compensate.",
        },
    )


def _session_id(request: Request, response: Response) -> str:
    sid = request.cookies.get("ew_sid")
    now = time.time()
    if sid and sid in _sessions and now - _sessions[sid] < SESSION_TTL:
        _sessions[sid] = now
        return sid
    sid = secrets.token_urlsafe(16)
    _sessions[sid] = now
    response.set_cookie("ew_sid", sid, httponly=True, samesite="lax", secure=COOKIE_SECURE, max_age=SESSION_TTL)
    return sid


def _strip_exif(raw: bytes, content_type: str) -> tuple[bytes, str]:
    """Re-encode to clean pixels — EXIF/GPS removed BEFORE hashing (checklist §2).

    2026-10-03 hotfix: the old pixel-copy (putdata(list(img.getdata())))
    materialised one Python tuple per pixel — a 12MP phone photo demanded
    gigabytes and OOM-killed the service under MemoryMax. PIL re-save drops
    EXIF/GPS/XMP unless explicitly passed back, so a bounded thumbnail +
    plain re-save keeps the privacy promise at sane memory.
    """
    if content_type == "application/pdf":
        import pymupdf

        doc = pymupdf.open(stream=raw, filetype="pdf")
        pix = doc[0].get_pixmap(dpi=150)
        buf = io.BytesIO()
        pix.save(buf, "png", compress_level=6)
        doc.close()
        return buf.getvalue(), "image/png"
    with Image.open(io.BytesIO(raw)) as img:
        img.thumbnail((4096, 4096))  # evidence-grade resolution; bounds RAM
        buf = io.BytesIO()
        fmt = "PNG" if content_type == "image/png" else "WEBP" if content_type == "image/webp" else "JPEG"
        if fmt != "PNG":
            img.save(buf, format=fmt, quality=92)
        else:
            img.save(buf, format=fmt)
        mime = {"PNG": "image/png", "WEBP": "image/webp", "JPEG": "image/jpeg"}[fmt]
    return buf.getvalue(), mime


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(STATICS, "index.html"))


@app.post("/api/observe")
async def observe(
    request: Request,
    response: Response,
    image: bytes | None = File(default=None),
    modality_hint: str = Form(""),
    basin: str = Form(""),
    objective: str = Form(""),
    field_tests_json: str = Form("{}"),
    scale_json: str = Form("{}"),
    seismic_json: str = Form("{}"),
) -> JSONResponse:
    _session_id(request, response)

    # rate limit (per-IP) — checklist §9 "rate limit triggers HOLD"
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    _prune_states(now)
    window = [t for t in _rate.get(ip, []) if now - t < PER_IP_WINDOW]
    if len(window) >= PER_IP_MAX:
        return _hold("per-IP rate limit exceeded")
    window.append(now)
    _rate[ip] = window

    # global daily vision budget — checklist §7
    today = time.gmtime().tm_yday
    if _budget["day"] != today:
        _budget.update(day=today, used=0)
    if _budget["used"] >= DAILY_BUDGET:
        return _hold("daily vision budget exhausted")
    _budget["used"] += 1

    if not image:
        raise HTTPException(400, "image upload required")
    if len(image) > MAX_BYTES:
        raise HTTPException(413, "file exceeds 10 MB limit")

    data_uri: str | dict[str, Any]
    try:
        if image[:5] == b"%PDF-":
            cleaned, mime = _strip_exif(image, "application/pdf")
            data_uri = "data:application/pdf;base64," + base64.b64encode(cleaned).decode()
        else:
            sniff = Image.open(io.BytesIO(image)).format or "JPEG"
            content_type = {"PNG": "image/png", "WEBP": "image/webp"}.get(sniff, "image/jpeg")
            if content_type not in ALLOWED_TYPES:
                raise HTTPException(415, "only jpg, png, webp, pdf allowed")
            cleaned, mime = _strip_exif(image, content_type)
            data_uri = f"data:{mime};base64," + base64.b64encode(cleaned).decode()
    except HTTPException:
        raise
    except Exception:
        # magic-sniff/decode failure = malformed upload, never a 500 (hardening 2026-10-03)
        raise HTTPException(415, "only jpg, png, webp, pdf allowed") from None

    import json as _json

    context: dict[str, Any] = {"source_actor": "earth_witness_chat"}
    if basin and basin not in ("Unknown", ""):
        context["basin_profile"] = basin  # context ONLY — never inflates (I7)
    if objective:
        context["subject_class"] = objective
    scale = _json.loads(scale_json) if scale_json and scale_json != "{}" else None
    if scale and scale.get("value"):
        context["scale"] = scale
    seismic = _json.loads(seismic_json) if seismic_json and seismic_json != "{}" else None
    if seismic:
        if seismic.get("domain"):
            context["domain"] = seismic["domain"]
        dt = {k: v for k, v in seismic.items() if k in ("polarity", "color_map", "gain") and v}
        if dt:
            context["display_transform"] = dt
        meta = {k: v for k, v in seismic.items() if k in ("phase_deg", "stacks", "nearby_well") and v}
        if meta:
            context["acquisition_metadata"] = meta

    try:
        packet = _mcp.call_tool(
            "geox_observe",
            {
                "artifact_ref": data_uri,
                "modality_hint": modality_hint or None,
                "context": context,
                "field_tests": _json.loads(field_tests_json) if field_tests_json != "{}" else None,
            },
        )
    except McpError as exc:
        return JSONResponse(status_code=502, content={"status": "ERROR", "reason": str(exc)[:300]})

    # geox_forbidden_claims_scan (fast in-process form) on EVERY outgoing reply — §7
    scan = scan_reply(packet)
    if not scan["ok"]:
        return _hold(f"forbidden-claim scan hit: {scan['hits'][:3]} — reply withheld")

    return JSONResponse({"status": "OK", "packet": packet})
