"""
kernel_client.py — GEOX ↔ arifOS Kernel Bridge
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

Thin async HTTP client for calling arifOS mega-tools from GEOX.
Gracefully degrades if the kernel is unreachable (GEOX still works standalone).

Usage:
    async with GeoxKernelClient() as client:
        session_id = await client.init_anchor(identity="GEOX", task="prospect eval")
        await client.vault_seal(session_id=session_id, payload=verdict_dict)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("geox.kernel_client")

KERNEL_URL = os.getenv("ARIFOS_KERNEL_URL", "https://arifosmcp.arif-fazil.com/mcp")
KERNEL_TIMEOUT = float(os.getenv("ARIFOS_KERNEL_TIMEOUT", "5.0"))

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


class GeoxKernelClient:
    """
    Calls arifOS mega-tools via the MCP JSON-RPC protocol.

    Falls back silently if the kernel is unreachable — GEOX verdicts are
    still returned to the caller; only the vault write is skipped.
    """

    def __init__(self, kernel_url: str = KERNEL_URL, timeout: float = KERNEL_TIMEOUT) -> None:
        self.kernel_url = kernel_url
        self.timeout = timeout
        self._client: "httpx.AsyncClient | None" = None

    async def __aenter__(self) -> "GeoxKernelClient":
        if _HAS_HTTPX:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
        """Send a single MCP tools/call request. Returns result dict or None on failure."""
        if not _HAS_HTTPX or self._client is None:
            return None
        try:
            resp = await self._client.post(
                self.kernel_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                },
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", {})
        except Exception as exc:
            logger.warning("Kernel call %s failed (degraded mode): %s", tool_name, exc)
            return None

    async def init_anchor(self, identity: str = "GEOX", task: str = "geoscience evaluation") -> str | None:
        """
        Call init_anchor(mode="init") on the arifOS kernel.
        Returns session_id string or None if unavailable.
        """
        result = await self._call("init_anchor", {"mode": "init", "identity": identity, "task": task})
        if result:
            content = result.get("content", [{}])
            if isinstance(content, list) and content:
                text = content[0].get("text", "{}")
                try:
                    import json
                    parsed = json.loads(text)
                    return parsed.get("session_id") or parsed.get("anchor_id")
                except Exception:
                    pass
        return None

    async def vault_seal(self, payload: dict[str, Any], session_id: str | None = None) -> bool:
        """
        Call vault_ledger(mode="seal") to write verdict to VAULT999.
        Returns True if sealed, False if skipped or failed.
        """
        args: dict[str, Any] = {"mode": "seal", "payload": payload}
        if session_id:
            args["session_id"] = session_id
        result = await self._call("vault_ledger", args)
        if result:
            logger.info("VAULT999 seal confirmed for payload")
            return True
        logger.warning("VAULT999 seal skipped — kernel unreachable (standalone mode)")
        return False
