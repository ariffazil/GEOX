"""MCP 2026-07-28 stateless-era contract: EVERY result reply carries resultType.

Root cause (measured live 2026-10-15): GEOX's era bridge relayed FastMCP
replies verbatim, so only tools/list (outer method-matching middleware) and
server/discover carried ``resultType``. Claude Code — a strict 2026-07-28
client — rejects/drops every other reply. Spec: success responses carry
``resultType: "complete"`` (see skill mcp-stateless-protocol §1).

This contract covers, per the P0 fix plan:
  * JSON result replies  — resultType injected, content-length corrected
  * SSE streamed replies — data: frames rewritten, split chunks safe
  * JSON-RPC errors      — untouched (resultType is a RESULT obligation)
  * legacy (2025-11-25 sessionful) traffic — untouched
  * every method the era bridge serves (tools/*, resources/*, prompts/*, ping)

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from geox_mcp.stateless_era import (  # noqa: E402
    MODERN_ERA,
    McpStatelessEraMiddleware,
)


# ── Unit: payload augmentation ───────────────────────────────────────────────


def test_json_result_gets_resulttype():
    from geox_mcp.stateless_era import augment_stateless_result

    payload = {"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}
    out = augment_stateless_result(payload)
    assert out["result"]["resultType"] == "complete"


def test_json_error_untouched():
    from geox_mcp.stateless_era import augment_stateless_result

    payload = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32600, "message": "no"}}
    out = augment_stateless_result(payload)
    assert "resultType" not in out
    assert out == payload


def test_idempotent_when_resulttype_present():
    from geox_mcp.stateless_era import augment_stateless_result

    payload = {"jsonrpc": "2.0", "id": 1, "result": {"resultType": "complete"}}
    out = augment_stateless_result(payload)
    assert out["result"]["resultType"] == "complete"


def test_non_dict_result_untouched():
    from geox_mcp.stateless_era import augment_stateless_result

    payload = {"jsonrpc": "2.0", "id": 1, "result": None}
    assert augment_stateless_result(payload) == payload


# ── ASGI-level integration through the real bridge ──────────────────────────


class _StubInnerApp:
    """Minimal inner app: answers bridge bootstrap (initialize) and then
    serves one canned response per forwarded request, chosen by body method."""

    def __init__(self, canned: dict[str, dict]):
        self.canned = canned
        self.seen: list[dict] = []

    async def __call__(self, scope, receive, send):
        body = b""
        while True:
            msg = await receive()
            body += msg.get("body", b"") or b""
            if not msg.get("more_body", False):
                break
        method = ""
        try:
            method = json.loads(body).get("method", "")
        except Exception:
            pass
        self.seen.append({"method": method, "headers": dict((k.decode(), v.decode()) for k, v in scope.get("headers", []))})

        if method == "initialize":
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"mcp-session-id", b"bridge-test-session"),
                        (b"content-length", b"2"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": b"{}", "more_body": False})
            return

        canned = self.canned.get(method, self.canned.get("*"))
        if canned is None:
            await send({"type": "http.response.start", "status": 404, "headers": []})
            await send({"type": "http.response.body", "body": b"", "more_body": False})
            return
        await send({"type": "http.response.start", "status": 200, "headers": list(canned["headers"])})
        for chunk in canned["chunks"]:
            more = chunk is not canned["chunks"][-1]
            await send({"type": "http.response.body", "body": chunk, "more_body": more})


async def _drive(stub_responses: dict, request_body: dict) -> tuple[int, dict, list[bytes]]:
    """Send one modern-era stateless request through the middleware. Returns
    (status, headers, body_chunks) the CLIENT would receive."""
    stub = _StubInnerApp(stub_responses)
    mw = McpStatelessEraMiddleware(stub, server_name="GEOX-test", server_version="t")

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/mcp",
        "raw_path": b"/mcp",
        "query_string": b"",
        "root_path": "",
        "client": ("127.0.0.1", 0),
        "server": ("127.0.0.1", 0),
        "headers": [
            (b"content-type", b"application/json"),
            (b"accept", b"application/json, text/event-stream"),
            (b"mcp-protocol-version", MODERN_ERA.encode()),
            (b"mcp-method", request_body["method"].encode()),
        ],
    }
    req_bytes = json.dumps(request_body).encode()
    served = {"n": 0}

    async def receive():
        if served["n"]:
            return {"type": "http.disconnect"}
        served["n"] = 1
        return {"type": "http.request", "body": req_bytes, "more_body": False}

    out: dict = {"status": 0, "headers": {}, "chunks": []}

    async def send(message):
        if message["type"] == "http.response.start":
            out["status"] = message["status"]
            out["headers"] = {k.decode().lower(): v.decode() for k, v in message.get("headers", [])}
        elif message["type"] == "http.response.body":
            out["chunks"].append(message.get("body", b"") or b"")

    import asyncio

    await asyncio.get_event_loop().run_in_executor(None, lambda: None)  # keep loop warm
    await mw(scope, receive, send)
    return out["status"], out["headers"], out["chunks"]


def _meta() -> dict:
    return {
        "_meta": {
            "io.modelcontextprotocol/protocolVersion": MODERN_ERA,
            "io.modelcontextprotocol/clientCapabilities": {},
        }
    }


@pytest.mark.asyncio
async def test_bridge_json_result_reply_gets_resulttype():
    """tools/call reply (JSON) must carry resultType after the bridge."""
    raw = json.dumps({"jsonrpc": "2.0", "id": 7, "result": {"content": []}}).encode()
    status, headers, chunks = await _drive(
        {
            "*": {
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(raw)).encode())],
                "chunks": [raw],
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "geox_surface_status", "arguments": {}, **_meta()},
        },
    )
    assert status == 200
    body = b"".join(chunks)
    data = json.loads(body)
    assert data["result"]["resultType"] == "complete", "2026-07-28 result reply missing resultType — strict clients reject it"
    # strict-client invariant: content-length must match the bytes actually sent
    if "content-length" in headers:
        assert int(headers["content-length"]) == len(body), "content-length drift"


@pytest.mark.asyncio
async def test_bridge_json_error_reply_untouched():
    raw = json.dumps({"jsonrpc": "2.0", "id": 8, "error": {"code": -32602, "message": "bad"}}).encode()
    status, headers, chunks = await _drive(
        {"*": {"headers": [(b"content-type", b"application/json")], "chunks": [raw]}},
        {"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "geox_well", "arguments": {}, **_meta()}},
    )
    data = json.loads(b"".join(chunks))
    assert "error" in data
    assert "resultType" not in data


@pytest.mark.asyncio
async def test_bridge_tool_error_result_still_complete():
    """Spec (draft server/tools): a COMPLETED tools/call reply carries
    resultType:'complete' even when the tool itself failed (isError:true).
    content/structuredContent/isError must be preserved verbatim — only the
    discriminator is added."""
    raw = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 10,
            "result": {"content": [{"type": "text", "text": "boom"}], "isError": True},
        }
    ).encode()
    status, headers, chunks = await _drive(
        {
            "*": {
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(raw)).encode())],
                "chunks": [raw],
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "geox_well_ingest", "arguments": {"bad": 1}, **_meta()},
        },
    )
    data = json.loads(b"".join(chunks))
    res = data["result"]
    assert res["isError"] is True, "isError must survive the rewrite"
    assert res["content"] == [{"type": "text", "text": "boom"}], "content must be byte-preserving"
    assert res["resultType"] == "complete", "completed tool errors still carry resultType=complete"
    if "content-length" in headers:
        assert int(headers["content-length"]) == len(b"".join(chunks))


@pytest.mark.asyncio
async def test_bridge_existing_discriminator_preserved():
    """An existing resultType (e.g. input_required from MRTR elicitation)
    is NEVER overwritten with 'complete' — the fix is additive only."""
    raw = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "result": {"resultType": "input_required", "content": [{"type": "text", "text": "name?"}]},
        }
    ).encode()
    status, headers, chunks = await _drive(
        {"*": {"headers": [(b"content-type", b"application/json")], "chunks": [raw]}},
        {"jsonrpc": "2.0", "id": 11, "method": "tools/call", "params": {"name": "geox_claim", "arguments": {}, **_meta()}},
    )
    data = json.loads(b"".join(chunks))
    assert data["result"]["resultType"] == "input_required", "existing discriminator must be preserved, not clobbered"
    assert data["result"]["content"] == [{"type": "text", "text": "name?"}]


@pytest.mark.asyncio
async def test_bridge_sse_stream_frames_get_resulttype():
    """Streamed replies (text/event-stream) must be rewritten frame by frame —
    including a JSON frame split across two body chunks."""
    frame1 = {"jsonrpc": "2.0", "id": 9, "result": {"resources": []}}
    frame2 = {"jsonrpc": "2.0", "id": 9, "result": {"prompts": []}}
    sse = (f"event: message\ndata: {json.dumps(frame1)}\n\nevent: message\ndata: {json.dumps(frame2)}\n\n").encode()
    cut = 30  # split mid-frame-1
    status, headers, chunks = await _drive(
        {"*": {"headers": [(b"content-type", b"text/event-stream")], "chunks": [sse[:cut], sse[cut:]]}},
        {"jsonrpc": "2.0", "id": 9, "method": "resources/list", "params": _meta()},
    )
    body = b"".join(chunks).decode()
    datas = [ln for ln in body.splitlines() if ln.startswith("data:")]
    assert len(datas) == 2
    for ln in datas:
        payload = json.loads(ln[5:].strip())
        assert payload["result"]["resultType"] == "complete"
    # SSE stream structure preserved (event lines + blank separators)
    assert body.count("event: message") == 2
    assert body.endswith("\n\n")


@pytest.mark.asyncio
async def test_every_method_family_gets_resulttype():
    """One reply per method family — tools, resources, prompts, ping."""
    methods = ["tools/list", "resources/list", "prompts/list", "ping"]
    for m in methods:
        raw = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode()
        status, headers, chunks = await _drive(
            {"*": {"headers": [(b"content-type", b"application/json")], "chunks": [raw]}},
            {"jsonrpc": "2.0", "id": 1, "method": m, "params": _meta()},
        )
        assert status == 200, m
        data = json.loads(b"".join(chunks))
        assert data.get("result", {}).get("resultType") == "complete", f"{m} reply missing resultType"


@pytest.mark.asyncio
async def test_legacy_sessionful_traffic_not_augmented():
    """Legacy (session-bearing, SDK-version) requests must pass through the
    era bridge untouched — resultType is a 2026-07-28 obligation only."""
    stub = _StubInnerApp({})
    mw = McpStatelessEraMiddleware(stub, server_name="GEOX-test", server_version="t")
    raw = json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"tools": []}}).encode()
    out: dict = {"status": 0, "chunks": []}

    async def send(message):
        if message["type"] == "http.response.start":
            out["status"] = message["status"]
        elif message["type"] == "http.response.body":
            out["chunks"].append(message.get("body", b"") or b"")

    # Legacy traffic never reaches the bridge: __call__ forwards before bridging.
    # Assert the early-return contract directly.
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp",
        "headers": [(b"mcp-session-id", b"legacy-sess"), (b"mcp-protocol-version", b"2025-11-25")],
    }
    served = {"n": 0}

    async def receive():
        if served["n"]:
            return {"type": "http.disconnect"}
        served["n"] = 1
        return {"type": "http.request", "body": b"{}", "more_body": False}

    # stub answers everything with the raw (non-augmented) JSON
    stub.canned = {"*": {"headers": [(b"content-type", b"application/json")], "chunks": [raw]}}
    await mw(scope, receive, send)
    data = json.loads(b"".join(out["chunks"]))
    assert "resultType" not in data.get("result", {}), "legacy reply must not be modified by the 2026-07-28 era layer"
