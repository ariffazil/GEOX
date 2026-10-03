"""Minimal MCP streamable-HTTP client for the Earth Witness chat proxy.

Talks to the local GEOX organ only (127.0.0.1:8081 per checklist §7).
Sync httpx — the proxy runs one tool call per request.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any

import httpx

GEOX_MCP_URL = os.getenv("GEOX_MCP_URL", "http://127.0.0.1:8081/mcp")
MCP_TOKEN = os.getenv("EARTH_WITNESS_MCP_TOKEN", "")


class McpError(RuntimeError):
    pass


class McpClient:
    def __init__(self, url: str = GEOX_MCP_URL, token: str = MCP_TOKEN, timeout: float = 60.0):
        self.url = url
        self.token = token
        self.timeout = timeout
        self._session_id: str | None = None
        self._lock = threading.Lock()

    def _headers(self) -> dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if self._session_id:
            h["Mcp-Session-Id"] = self._session_id
        return h

    def _post(self, payload: dict[str, Any]) -> httpx.Response:
        with httpx.Client(timeout=self.timeout) as client:
            return client.post(self.url, json=payload, headers=self._headers())

    def _ensure_session(self) -> None:
        if self._session_id:
            return
        with self._lock:
            if self._session_id:
                return
            resp = self._post(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "earth-witness-chat", "version": "1.0.0"},
                    },
                }
            )
            resp.raise_for_status()
            sid = resp.headers.get("mcp-session-id")
            if not sid:
                raise McpError("GEOX MCP did not return a session id")
            self._session_id = sid
            # notifications/initialized per spec
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _invalidate_session(self) -> None:
        # Organ restarts (deploys, env re-wiring) orphan the MCP session id;
        # the server then answers 404. Drop it and re-initialize once.
        self._session_id = None

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        for attempt in (0, 1):
            self._ensure_session()
            resp = self._post(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                }
            )
            if resp.status_code == 404 and attempt == 0:
                self._invalidate_session()
                continue
            break
        resp.raise_for_status()
        body = resp.json()
        if "error" in body:
            raise McpError(f"MCP error: {body['error']}")
        result = body.get("result", {})
        if result.get("isError"):
            raise McpError(json.dumps(result.get("content", []))[:400])
        for item in result.get("content", []):
            if item.get("type") == "text":
                return json.loads(item["text"])
        raise McpError("no text content in MCP result")
