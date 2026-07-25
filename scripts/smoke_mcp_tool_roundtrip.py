#!/usr/bin/env python3
"""GEOX MCP tool round-trip smoke (P1 fix gate · 2026-07-25).

Proves the tool plane is callable through FastMCP serialization — not just
that /health is up. Catches the regression:

  AttributeError: 'dict' object has no attribute 'to_mcp_result'

Flow:
  1. In-process: stamp ToolResult → to_mcp_result() must work
  2. Live :8081: MCP initialize → tools/call geox_surface_status
     Fail hard if response mentions to_mcp_result or AttributeError

Exit 0 = green. Exit 1 = regression.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

BASE = os.environ.get("GEOX_SMOKE_URL", "http://127.0.0.1:8081").rstrip("/")
MCP = f"{BASE}/mcp/"


def _http_json(
    method: str,
    url: str,
    payload: dict | None = None,
    headers: dict | None = None,
) -> tuple[int, dict, dict]:
    data = json.dumps(payload).encode() if payload is not None else None
    hdrs = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            hdr = {k.lower(): v for k, v in resp.headers.items()}
            try:
                return resp.status, json.loads(body) if body else {}, hdr
            except json.JSONDecodeError:
                return resp.status, {"raw": body}, hdr
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        hdr = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
        try:
            return e.code, json.loads(body) if body else {"raw": body}, hdr
        except json.JSONDecodeError:
            return e.code, {"raw": body}, hdr


def check_inprocess() -> list[str]:
    failures: list[str] = []
    from fastmcp.tools.base import ToolResult

    from geox_mcp.ext_witness_stamp import stamp_and_gate

    tr = ToolResult(
        structured_content={
            "ok": True,
            "status": "OK",
            "mode": "offline_stub",
            "tool": "geox_surface_status",
        }
    )
    out = stamp_and_gate(tr, tool_name="geox_surface_status")
    if not hasattr(out, "to_mcp_result"):
        failures.append(f"inprocess: stamp returned {type(out)} without to_mcp_result")
        return failures
    try:
        out.to_mcp_result()
    except Exception as exc:  # noqa: BLE001
        failures.append(f"inprocess: to_mcp_result raised {type(exc).__name__}: {exc}")
    sc = getattr(out, "structured_content", None) or {}
    if "ext_witness_ready" not in sc:
        failures.append("inprocess: structured_content missing ext_witness_ready")
    return failures


def check_live_mcp() -> list[str]:
    failures: list[str] = []
    # 1) health
    try:
        code, health, _ = _http_json("GET", f"{BASE}/health")
        if code != 200:
            failures.append(f"live health HTTP {code}")
            return failures
    except Exception as exc:  # noqa: BLE001
        failures.append(f"live health unreachable: {exc}")
        return failures

    # 2) MCP initialize → mcp-session-id
    code, init_body, init_hdr = _http_json(
        "POST",
        MCP,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "geox-smoke-mcp-roundtrip", "version": "1.0.0"},
            },
        },
    )
    sid = init_hdr.get("mcp-session-id") or init_hdr.get("Mcp-Session-Id")
    if not sid:
        # some transports put it in body
        sid = (init_body.get("result") or {}).get("sessionId")
    if not sid:
        failures.append(
            f"live MCP initialize missing mcp-session-id (HTTP {code} body={str(init_body)[:200]})"
        )
        return failures

    # 3) tools/call geox_surface_status
    # Authority session optional — we fail on serialization, not on SESSION_MISSING.
    code, call_body, _ = _http_json(
        "POST",
        MCP,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "geox_surface_status",
                "arguments": {
                    "mode": "registry",
                    "session_id": os.environ.get("GEOX_SMOKE_SESSION_ID", "SEAL-smoke-roundtrip"),
                    "actor_id": os.environ.get("GEOX_SMOKE_ACTOR_ID", "ARIF"),
                },
            },
        },
        headers={"mcp-session-id": sid, "Mcp-Session-Id": sid},
    )

    blob = json.dumps(call_body)
    if "to_mcp_result" in blob or "has no attribute 'to_mcp_result'" in blob:
        failures.append(f"live tools/call serialization regression: {blob[:400]}")
        return failures
    if "AttributeError" in blob and "dict" in blob:
        failures.append(f"live tools/call AttributeError on dict: {blob[:400]}")
        return failures

    # Accept: success result OR governed HOLD (session). Not internal server crash.
    err = call_body.get("error") if isinstance(call_body, dict) else None
    if err and isinstance(err, dict):
        msg = str(err.get("message", ""))
        # -32600 missing MCP session is transport; already have sid so unexpected
        if "Internal" in msg or "traceback" in msg.lower() or "AttributeError" in msg:
            failures.append(f"live tools/call internal error: {msg[:300]}")
            return failures
        # SESSION_MISSING / HOLD is acceptable for smoke without valid arif_init
        print(f"NOTE: tools/call returned governed error (ok for auth): {msg[:160]}")
    else:
        result = call_body.get("result") if isinstance(call_body, dict) else None
        if result is None and code >= 500:
            failures.append(f"live tools/call HTTP {code} no result: {blob[:300]}")
        else:
            print(f"PASS live tools/call HTTP {code} (result present or governed)")

    return failures


def main() -> int:
    failures: list[str] = []
    failures.extend(check_inprocess())
    failures.extend(check_live_mcp())

    if failures:
        print("FAIL smoke_mcp_tool_roundtrip:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS smoke_mcp_tool_roundtrip: ToolResult stamp + live tools/call wire")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
