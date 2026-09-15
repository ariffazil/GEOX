"""Dual-era MCP transport shim — stateless 2026-07-28 + legacy 2025-11-25.

DITEMPA BUKAN DIBERI.

WHY THIS FILE EXISTS (root cause, measured 2026-09-15)
=====================================================
GEOX's ``/mcp`` surface is FastMCP 3.4.6 over ``mcp`` 1.29.0 with
``stateless_http=False`` (see ``server.py::create_app``).  A modern stateless
probe (``MCP-Protocol-Version: 2026-07-28`` + ``Mcp-Method: server/discover``)
is rejected with HTTP 400 **twice over**, before any method dispatch happens:

1. ``mcp/server/streamable_http.py:835-851``
   ``StreamableHTTPSessionManager._validate_session()``::

       if not self.mcp_session_id:
           return True
       request_session_id = self._get_session_id(request)
       if not request_session_id:
           response = self._create_error_response(
               "Bad Request: Missing session ID", HTTPStatus.BAD_REQUEST)

   Measured: ``{"code":-32600,"message":"Bad Request: Missing session ID"}``.

2. ``mcp/server/streamable_http.py:864-882``
   ``_validate_protocol_version()`` against
   ``mcp/shared/version.py::SUPPORTED_PROTOCOL_VERSIONS`` which is
   ``["2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"]``
   (``mcp.types.LATEST_PROTOCOL_VERSION == "2025-11-25"``).
   Any request *carrying* ``MCP-Protocol-Version: 2026-07-28`` is therefore
   400'd even with a valid session id.  Measured::

       {"code":-32600,"message":"Bad Request: Unsupported protocol version:
        2026-07-28. Supported versions: 2024-11-05, 2025-03-26, 2025-06-18,
        2025-11-25"}

Neither ``mcp`` 1.29.0 nor ``fastmcp`` 3.4.6 knows the method
``server/discover`` (grep: zero matches in both packages), and GEOX's own
``McpProtocolVersionMiddleware`` already whitelists ``2026-07-28`` — so the
*app level* intends to speak the modern era while the *transport level* 400s it.

Bumping to ``mcp`` 2.0.0 is NOT an option: it renames ``McpError`` →
``MCPError`` and drops ``StreamableHTTPServerTransport._check_accept_headers``,
which breaks every 1.x-built transport in the federation (external audit, 2026-09).

WHAT THIS MIDDLEWARE DOES (additive, transport untouched)
=========================================================
Placed *innermost* (closest to the router, inside OriginValidation / McpAuth /
McpProtocolVersion / McpLifecycle), it:

* answers ``server/discover`` natively — no session required — with the same
  result shape arifOS (:8088) and FED (:7074) emit, so the federation sees one
  era-consistent discovery contract;
* bridges any *other* session-less request that declares the modern era
  (``MCP-Protocol-Version: 2026-07-28`` header, ``Mcp-Method`` header, or body
  ``_meta`` protocolVersion) onto a single shared internal 2025-11-25 session,
  so ``tools/list`` / ``tools/call`` / ``resources/*`` / ``prompts/*`` work
  without the client holding a session id;
* translates an unsupported ``MCP-Protocol-Version`` value down to the version
  the installed SDK actually negotiated, instead of letting the transport 400 it.

Legacy traffic is untouched: a request that carries ``Mcp-Session-Id`` and a
version the SDK supports never enters the era code paths (early return).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger("geox_mcp.stateless_era")

# Versions the installed transport (mcp 1.29.0) accepts without 400.
SDK_SUPPORTED_VERSIONS: tuple[str, ...] = (
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
    "2025-11-25",
)
# What the transport actually negotiates for a bridged internal session.
BRIDGE_NEGOTIATED_VERSION = "2025-11-25"
# Modern stateless era we advertise.
MODERN_ERA = "2026-07-28"
ADVERTISED_VERSIONS: tuple[str, ...] = (
    "2026-07-28",
    "2025-11-25",
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
)

_MCP_PATHS = ("/mcp", "/mcp/")


def _header(scope: dict[str, Any], name: str) -> str:
    target = name.lower().encode("latin-1")
    for key, value in scope.get("headers", []):
        if key.lower() == target:
            return value.decode("latin-1")
    return ""


async def _read_body(receive) -> bytes:
    chunks: list[bytes] = []
    while True:
        message = await receive()
        if message["type"] != "http.request":
            break
        chunks.append(message.get("body", b"") or b"")
        if not message.get("more_body", False):
            break
    return b"".join(chunks)


def _body_receive(body: bytes):
    served = False

    async def _receive():
        nonlocal served
        if served:
            return {"type": "http.disconnect"}
        served = True
        return {"type": "http.request", "body": body, "more_body": False}

    return _receive


def _scope_with_headers(scope: dict[str, Any], overrides: dict[str, str], drop: tuple[str, ...] = ()) -> dict[str, Any]:
    """Return a copy of ``scope`` with ``overrides`` applied (case-insensitive)."""
    overrides_l = {k.lower(): v for k, v in overrides.items()}
    drops = {d.lower() for d in drop}
    new_scope = dict(scope)
    out: list[tuple[bytes, bytes]] = []
    seen: set[str] = set()
    for key, value in scope.get("headers", []):
        name = key.decode("latin-1").lower()
        if name in drops:
            continue
        if name in overrides_l:
            if name in seen:
                continue
            seen.add(name)
            out.append((key, overrides_l[name].encode("latin-1")))
        else:
            out.append((key, value))
    for name, value in overrides_l.items():
        if name not in seen:
            out.append((name.encode("latin-1"), value.encode("latin-1")))
    new_scope["headers"] = out
    return new_scope


async def _send_json(send, payload: dict[str, Any], status: int = 200, extra_headers: dict[str, str] | None = None) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ]
    for name, value in (extra_headers or {}).items():
        headers.append((name.lower().encode("latin-1"), value.encode("latin-1")))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body, "more_body": False})


class McpStatelessEraMiddleware:
    """Serve the stateless MCP 2026-07-28 era over the stateful FastMCP transport."""

    def __init__(
        self,
        app,
        *,
        server_name: str = "GEOX",
        server_version: str = "unknown",
        instructions: str = "",
        surface_count: int | None = None,
        website_url: str = "https://geox.arif-fazil.com",
    ) -> None:
        self.app = app
        self.server_name = server_name
        self.server_version = server_version
        self.instructions = instructions
        self.surface_count = surface_count
        self.website_url = website_url
        self._bridge_session_id: str | None = None
        self._bridge_lock = asyncio.Lock()

    # ── ASGI entrypoint ─────────────────────────────────────────────────
    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http" or scope.get("method") != "POST" or scope.get("path") not in _MCP_PATHS:
            await self.app(scope, receive, send)
            return

        version = _header(scope, "mcp-protocol-version")
        session_id = _header(scope, "mcp-session-id")

        # Pure legacy traffic: a session id + a version the SDK supports.
        # Never read the body, never rewrite, never bridge.
        if session_id and (not version or version in SDK_SUPPORTED_VERSIONS):
            await self.app(scope, receive, send)
            return

        mcp_method = _header(scope, "mcp-method")
        body = await _read_body(receive)

        # Translate an era header the installed SDK does not know
        # (2026-07-28 …) down to the version it negotiated. Without this the
        # transport 400s even when the session gate passes.
        if version and version not in SDK_SUPPORTED_VERSIONS:
            logger.debug("MCP_ERA_VERSION_TRANSLATED: %s -> %s", version, BRIDGE_NEGOTIATED_VERSION)
            scope = _scope_with_headers(scope, {"mcp-protocol-version": BRIDGE_NEGOTIATED_VERSION})
            version = BRIDGE_NEGOTIATED_VERSION

        message: dict[str, Any] | None = None
        try:
            parsed = json.loads(body.decode("utf-8") or "{}")
            if isinstance(parsed, dict):
                message = parsed
        except Exception:
            message = None

        method = str((message or {}).get("method") or "")
        meta_version = ""
        params = (message or {}).get("params")
        if isinstance(params, dict):
            meta = params.get("_meta")
            if isinstance(meta, dict):
                meta_version = str(meta.get("io.modelcontextprotocol/protocolVersion") or "")

        era_declared = bool(version or mcp_method or meta_version)

        # Legacy handshake, session-bearing traffic, or undeclared requests
        # (e.g. a client's plain initialize) → downstream untouched.
        if not era_declared or session_id or method in ("initialize",):
            await self.app(_scope_with_headers(scope, {}), _body_receive(body), send)
            return

        # ── MODERN STATELESS ERA ────────────────────────────────────────
        if method == "server/discover":
            await self._serve_discover(send, message)
            return

        if method in ("notifications/initialized", "initialized", "notifications/cancelled"):
            # Stateless notifications carry no session; acknowledge per spec.
            await send(
                {
                    "type": "http.response.start",
                    "status": 202,
                    "headers": [(b"content-length", b"0"), (b"x-mcp-era", b"stateless-2026-07-28")],
                }
            )
            await send({"type": "http.response.body", "body": b"", "more_body": False})
            return

        # Any other stateless method → bridge onto one shared internal session.
        await self._bridge_and_forward(scope, body, send, method)

    # ── server/discover (native, federation-consistent) ─────────────────
    def _discover_result(self) -> dict[str, Any]:
        capabilities: dict[str, Any] = {
            "experimental": {},
            "logging": {},
            "prompts": {"listChanged": True},
            "resources": {"subscribe": False, "listChanged": True},
            "tools": {"listChanged": True},
            "extensions": {"io.modelcontextprotocol/ui": {}},
        }
        meta: dict[str, Any] = {
            "io.modelcontextprotocol/serverInfo": {
                "name": self.server_name,
                "version": self.server_version,
                "websiteUrl": self.website_url,
            },
            "io.modelcontextprotocol/protocolVersion": MODERN_ERA,
            "io.modelcontextprotocol/transport": "streamable-http (dual-era: 2026-07-28 stateless + 2025-11-25 stateful)",
        }
        if self.surface_count is not None:
            meta["io.geox/surface"] = {
                "public_tools": self.surface_count,
                "source": "geox_mcp.registry.CANONICAL_PUBLIC_TOOLS",
            }
        return {
            "resultType": "complete",
            "supportedVersions": list(ADVERTISED_VERSIONS),
            "capabilities": capabilities,
            "instructions": self.instructions
            or (
                "GEOX Earth-intelligence MCP surface. Dual-era: 2026-07-28 stateless "
                "(server/discover first) and 2025-11-25 stateful handshake."
            ),
            "ttlMs": 300000,
            "cacheScope": "public",
            "_meta": meta,
        }

    async def _serve_discover(self, send, message: dict[str, Any] | None) -> None:
        msg_id = (message or {}).get("id")
        payload = {"jsonrpc": "2.0", "id": msg_id, "result": self._discover_result()}
        logger.info("MCP_ERA_DISCOVER: served stateless server/discover id=%r", msg_id)
        await _send_json(
            send,
            payload,
            status=200,
            extra_headers={
                "MCP-Protocol-Version": MODERN_ERA,
                "X-MCP-Era": "stateless-2026-07-28",
                "Cache-Control": "no-store",
            },
        )

    # ── session bridge for the remaining stateless methods ──────────────
    async def _bootstrap_session(self) -> str | None:
        """Create one internal 2025-11-25 session and complete the handshake."""
        init_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "geox-stateless-bridge-init",
                "method": "initialize",
                "params": {
                    "protocolVersion": BRIDGE_NEGOTIATED_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "geox-stateless-bridge", "version": "1.0"},
                },
            }
        ).encode()
        status, headers, _ = await self._internal_request(init_body, method="initialize", session=None)
        sid = headers.get("mcp-session-id") or headers.get("mcp-session_id")
        if status != 200 or not sid:
            logger.warning("MCP_ERA_BRIDGE_INIT_FAILED: status=%s sid_present=%s", status, bool(sid))
            return None
        ack_body = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode()
        ack_status, _, _ = await self._internal_request(ack_body, method="notifications/initialized", session=sid)
        try:  # best-effort: mirror GEOX's HTTP lifecycle gate bookkeeping
            from geox_mcp.geox_middleware import mark_lifecycle_ready

            mark_lifecycle_ready(sid, source="stateless-era-bridge")
        except Exception:
            pass
        logger.info("MCP_ERA_BRIDGE_READY: internal session established (ack=%s)", ack_status)
        return sid

    async def _internal_request(self, body: bytes, *, method: str, session: str | None):
        scope: dict[str, Any] = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/mcp/",
            "raw_path": b"/mcp/",
            "query_string": b"",
            "root_path": "",
            "client": ("127.0.0.1", 0),
            "server": ("127.0.0.1", 0),
            "headers": [
                (b"content-type", b"application/json"),
                (b"accept", b"application/json, text/event-stream"),
                (b"mcp-protocol-version", BRIDGE_NEGOTIATED_VERSION.encode()),
                (b"mcp-method", method.encode()),
                (b"host", b"127.0.0.1"),
            ]
            + ([(b"mcp-session-id", session.encode())] if session else []),
        }
        captured: dict[str, Any] = {"status": 0, "headers": {}, "body": b""}

        async def _capture(message):
            if message["type"] == "http.response.start":
                captured["status"] = message["status"]
                for key, value in message.get("headers", []):
                    captured["headers"][key.decode("latin-1").lower()] = value.decode("latin-1")
            elif message["type"] == "http.response.body":
                captured["body"] += message.get("body", b"") or b""

        await self.app(scope, _body_receive(body), _capture)
        return captured["status"], captured["headers"], captured["body"]

    async def _bridge_and_forward(self, scope, body: bytes, send, method: str) -> None:
        sid = self._bridge_session_id
        for attempt in (1, 2):
            if not sid:
                async with self._bridge_lock:
                    if not self._bridge_session_id:
                        self._bridge_session_id = await self._bootstrap_session()
                    sid = self._bridge_session_id
            if not sid:
                # Honest failure: no bridge → forward untouched, so the caller
                # sees the transport's real 400 rather than a fabricated success.
                await self.app(_scope_with_headers(scope, {}), _body_receive(body), send)
                return

            forward_scope = _scope_with_headers(scope, {"mcp-session-id": sid})
            captured: list[dict[str, Any]] = []

            async def _capture(message):
                captured.append(message)

            await self.app(forward_scope, _body_receive(body), _capture)
            status = next((m["status"] for m in captured if m["type"] == "http.response.start"), 0)
            if status == 404 and attempt == 1:
                logger.info("MCP_ERA_BRIDGE_STALE: 404 on %s — re-bootstrapping", method)
                self._bridge_session_id = None
                sid = None
                continue
            logger.info("MCP_ERA_BRIDGE_FORWARD: method=%s status=%s", method, status)
            for message in captured:
                if message["type"] == "http.response.start":
                    message["headers"] = list(message.get("headers", [])) + [
                        (b"x-mcp-era", b"stateless-2026-07-28")
                    ]
                await send(message)
            return
