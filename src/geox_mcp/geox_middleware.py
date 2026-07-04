"""
geox_middleware.py — FastMCP Governance Middleware for GEOX
============================================================

FORGE 2026-06-25 — replaces the legacy_mcp_handler RT1/RT3 enforcement
that lived in server.py. Moves constitutional governance from the HTTP
transport layer to FastMCP's native Middleware hook system.

DITEMPA BUKAN DIBERI — Forged, Not Given

Governance model:
  RT1  (Runtime Tier 1): tool name must be in CANONICAL_PUBLIC_TOOLS.
                          Blocks undeclared tools (F8 LAW).
  RT3  (Runtime Tier 3): irreversible tools require ack_irreversible=True.
                          Blocks irreversible state changes without sovereign consent (F1 AMANAH).
  organ_governance:       route C2+/IRREVERSIBLE through arifOS kernel for judgment.
                          (F1 AMANAH + F13 SOVEREIGN).

The middleware runs at the FastMCP method layer — NOT the HTTP layer —
which means it only fires for actual MCP messages (not health checks,
not static file routes, not /ready probes). That eliminates the wasted
work the old HTTP middlewares did.

FastMCP converts ToolError → clean JSON-RPC error response, so RT1/RT3
violations surface to clients as proper MCP errors with no custom plumbing.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware
from mcp.types import ListToolsResult

if TYPE_CHECKING:
    from fastmcp.server.middleware import CallNext, MiddlewareContext

logger = logging.getLogger("geox.governance.middleware")


class GeoxGovernanceMiddleware(Middleware):
    """
    Constitutional governance for GEOX tools at the FastMCP method layer.

    Replaces the per-request JSON-RPC dispatch logic that used to live in
    legacy_mcp_handler. This is the FORGE 2026-06-25 refactor.

    Hooks:
      - on_initialize   → log session start; no enforcement (initialize is metadata only)
      - on_call_tool    → RT1 (canonical name) + RT3 (ack_irreversible) + organ_governance

    Resources, prompts, and list_* calls are ungoverned — they are
    evidence-bearing reads that arifOS already routes as REFLECT_ONLY.
    """

    # Tools that perform irreversible state changes.
    # F1 AMANAH: no irreversible action without explicit human ack.
    # Phase 2: geox_claim(mode="seal") and geox_prospect(mode="seal") are the
    # canonical irreversible paths. MUST stay in sync with
    # scripts/control_plane_server_patch.py _IRREVERSIBLE_TOOLS.
    _IRREVERSIBLE_TOOLS: frozenset[str] = frozenset(
        {
            "geox_claim",  # mode="seal" requires ack_irreversible=True
            "geox_prospect",  # mode="seal" requires ack_irreversible=True
        }
    )

    def __init__(
        self,
        *,
        canonical_public_tools: set[str],
        canonical_compat_tools: set[str],
        arifos_route_query_enabled: bool = False,
        check_governance_fn: Any = None,
    ) -> None:
        """
        Args:
          canonical_public_tools: set of allowed tool names (RT1 allowlist + tools/list surface)
          canonical_compat_tools: backward-compat alias names accepted by on_call_tool but NOT exposed in tools/list
          arifos_route_query_enabled: if True, route_query tool gets a pass-through lane
          check_governance_fn: async (tool_name, args) -> (verdict, error_response|None)
                               imported lazily to avoid circular imports at module load.
        """
        # on_call_tool accepts both canonical + compat (backward compat during transition)
        self._EXECUTABLE_SURFACE: set[str] = set(canonical_public_tools) | set(canonical_compat_tools)
        # on_list_tools exposes ONLY canonical tools to clients (single truth)
        self._PUBLIC_SURFACE: set[str] = set(canonical_public_tools)
        self._arifos_route_query_enabled = arifos_route_query_enabled
        self._check_governance = check_governance_fn
        logger.info(
            f"GeoxGovernanceMiddleware armed: {len(self._PUBLIC_SURFACE)} public tools, "
            f"{len(self._EXECUTABLE_SURFACE)} executable tools (incl. compat), "
            f"{len(self._IRREVERSIBLE_TOOLS)} irreversible tools, "
            f"route_query={'enabled' if arifos_route_query_enabled else 'disabled'}"
        )

    # ── HOOKS ─────────────────────────────────────────────────────────────────

    async def on_initialize(
        self,
        context: "MiddlewareContext[Any]",
        call_next: "CallNext[Any, Any]",
    ) -> Any:
        """Log initialize; no enforcement (metadata-only request)."""
        try:
            client_info = context.message.params.clientInfo if context.message and context.message.params else None
            logger.info(
                "session_init: client=%s version=%s",
                getattr(client_info, "name", "unknown"),
                getattr(client_info, "version", "unknown"),
            )
        except Exception:
            pass
        return await call_next(context)

    async def on_list_tools(
        self,
        context: "MiddlewareContext[Any]",
        call_next: "CallNext[Any, Any]",
    ) -> Any:
        """Filter tools/list to canonical public surface only.

        Single truth: clients see ONLY the 16 canonical tools from
        CANONICAL_PUBLIC_TOOLS. Compat aliases are accepted by on_call_tool
        but never exposed in tools/list. This eliminates the split-brain
        where clients discovered old names that F9 would block.
        """
        result = await call_next(context)
        if result is None:
            return result
        # Filter to PUBLIC surface only (canonical 16, not compat)
        filtered = [t for t in result if getattr(t, "name", None) in self._PUBLIC_SURFACE]
        removed = len(result) - len(filtered)
        if removed:
            logger.debug(f"surface_filter: removed {removed} non-canonical tools from tools/list")
        return filtered

    async def on_call_tool(
        self,
        context: "MiddlewareContext[Any]",
        call_next: "CallNext[Any, Any]",
    ) -> Any:
        """RT1 + RT3 + organ_governance for every tools/call."""
        tool_name: str = getattr(context.message, "name", "")
        arguments: dict[str, Any] = getattr(context.message, "arguments", {}) or {}

        # ── RT1: tool name must be in executable surface (canonical + compat) ──
        if tool_name not in self._EXECUTABLE_SURFACE:
            # Special-case: arifos_route_query gets a pass-through when feature-flagged
            if not (self._arifos_route_query_enabled and tool_name == "arifos_route_query"):
                logger.warning(f"RT1_BLOCK: tool '{tool_name}' is not on canonical public surface")
                raise ToolError(
                    f"RT1_GUARD: Tool '{tool_name}' is not on the canonical or compat surface. "
                    f"Canonical surface has {len(self._PUBLIC_SURFACE)} declared tools. "
                    f"Use geox_surface_status(mode='registry') to enumerate available tools."
                )

        # ── T7: Deprecation warning for backward-compat aliases ──
        # If tool is in compat surface but NOT in canonical public surface, warn.
        if tool_name not in self._PUBLIC_SURFACE and tool_name in self._EXECUTABLE_SURFACE:
            logger.warning(
                f"DEPRECATED: Tool '{tool_name}' is a backward-compat alias. "
                f"Canonical tool names are available via geox_surface_status(mode='registry'). "
                f"Scheduled removal: 2026-07-30."
            )

        # ── RT3: irreversible tools require explicit ack_irreversible=True ──
        # The check is MODE-aware, not just tool-name. Read-only / screen / compute
        # / preview modes do NOT require ack_irreversible. Only the SEAL mode of
        # geox_claim and geox_prospect does.
        if tool_name in self._IRREVERSIBLE_TOOLS:
            needs_ack = False
            if tool_name == "geox_claim":
                # mode=seal is the irreversible path
                needs_ack = (arguments.get("mode") == "seal") or (arguments.get("action") == "seal")
            elif tool_name == "geox_prospect":
                # verdict=seal is the irreversible path
                needs_ack = arguments.get("verdict") == "seal"
            if needs_ack:
                ack = arguments.get("ack_irreversible", False)
                if not ack:
                    logger.warning(
                        f"RT3_BLOCK: {tool_name} in seal mode requires ack_irreversible=True. "
                        f"F1 Amanah: irreversible operations require explicit human consent."
                    )
                    raise ToolError(
                        f"RT3_GUARD: Tool '{tool_name}' in seal mode performs an irreversible "
                        f"state change. F1 Amanah requires explicit human consent via "
                        f"ack_irreversible=True. Provide ack_irreversible=True in the tool "
                        f"call arguments to proceed."
                    )

        # ── Organ governance: route C2+/IRREVERSIBLE through arifOS kernel ──
        if self._check_governance is not None:
            try:
                gov_verdict, gov_error = await self._check_governance(
                    tool_name=tool_name,
                    arguments=arguments,
                    is_direct_call=True,  # Raw MCP call = direct agent call
                )
            except Exception as e:
                # Fail-closed per F1 AMANAH: governance check itself failing → HOLD
                logger.error(f"organ_governance check raised: {e}")
                raise ToolError(
                    f"GOV_GATE: constitutional governance check failed for '{tool_name}'. "
                    f"F1 Amanah: no execution without verified judgment. ({type(e).__name__}: {e})"
                ) from e

            if gov_error is not None:
                # check_governance returns a JSONResponse-shaped dict on HOLD/VOID.
                # We need to extract the message and re-raise as ToolError so FastMCP
                # emits a clean MCP error response.
                err_msg = self._extract_error_message(gov_error)
                logger.warning(f"GOV_BLOCK: {tool_name} verdict={gov_verdict}: {err_msg[:120]}")
                raise ToolError(err_msg)

            logger.debug(f"GOV_PASS: {tool_name} verdict={gov_verdict}")

        return await call_next(context)

    # ── HELPERS ────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_error_message(gov_error: Any) -> str:
        """
        Convert check_governance's JSONResponse-shaped return into a flat
        error message suitable for ToolError.

        check_governance returns a starlette.responses.JSONResponse or a dict with
        structure: {"error": {"code": -32xxx, "message": "...", "data": {...}}}
        """
        try:
            # JSONResponse has .body (bytes of JSON)
            if hasattr(gov_error, "body"):
                body = gov_error.body
                if isinstance(body, bytes):
                    body = body.decode("utf-8", errors="replace")
                parsed = json.loads(body)
                return parsed.get("error", {}).get("message", "governance denied")
            # dict shape
            if isinstance(gov_error, dict):
                return gov_error.get("error", {}).get("message", "governance denied")
            # string fallback
            return str(gov_error)
        except Exception:
            return "governance denied (unable to parse response)"


# ─── TTL Middleware (Q3 seal 2026-07-03) ──────────────────────────────────


# Default TTL for tools/list responses (SEP-2549 compliant).
# 30 seconds — long enough to absorb cache hits between federation
# health probes, short enough that drift is found within one probe
# cycle (arifos_attest_all default cadence ≈ 60s).
DEFAULT_LIST_TTL_MS = 30_000


class GeoxToolListTtlMiddleware(Middleware):
    """
    Inject `meta.ttlMs` (SEP-2549) into every tools/list response.

    Per the spec, clients MUST treat a tools/list response without
    `ttlMs` as immediately stale (ttl=0). Without this middleware,
    every MCP-canonical client re-fetches the entire tool list on
    every request, defeating the SEP-2549 cache hint.

    Additional envelope: `fingerprint` is a SHA-256 over tool names +
    inputSchemas, used downstream by the federation drift watcher to
    cheaply detect registration changes without re-parsing every
    tool.
    """

    async def on_list_tools(
        self,
        context: MiddlewareContext,
        call_next: CallNext,
    ) -> Any:
        result = await call_next(context)
        # Q3 seal (2026-07-03): compute and log a stable drift fingerprint
        # over the registered tool surface. The fingerprint itself goes
        # back to the federation watcher via stderr/cron. We do NOT wrap
        # the result into a ListToolsResult because FastMCP 3.4.x returns
        # its own FastMCPProviderTool list (not mcp.types.Tool), and
        # cross-type coercion breaks validation. The ttlMs envelope on
        # the wire-format tools/list response is therefore delegated to
        # the arifOS gateway (arifos_arif_organ_attest_all consumers).
        try:
            tools = list(result) if hasattr(result, "__iter__") else []
        except TypeError:
            tools = []
        if not tools:
            return result

        import hashlib

        h = hashlib.sha256()
        names = []
        for tool in tools:
            try:
                name = getattr(tool, "name", "") or ""
                names.append(name)
                schema = getattr(tool, "inputSchema", None)
                schema_dump = json.dumps(schema or {}, sort_keys=True, default=str)
                h.update(name.encode("utf-8"))
                h.update(b"|")
                h.update(schema_dump.encode("utf-8"))
                h.update(b"||")
            except Exception:
                continue
        fingerprint = "sha256:" + h.hexdigest()
        logger.info(f"Q3_TTL: tools_list fingerprint={fingerprint} ttlMs={DEFAULT_LIST_TTL_MS} count={len(names)}")
        return result
        if not isinstance(result, ListToolsResult):
            return result

        # Compute a cheap stable fingerprint over tool names + input
        # schema hashes. This is the federation drift watcher's
        # primary signal — cheap to compute, cheap to compare.
        import hashlib

        h = hashlib.sha256()
        for tool in sorted(result.tools, key=lambda t: t.name):
            h.update(tool.name.encode("utf-8"))
            # inputSchema is a dict; sort keys for stable hash
            try:
                schema_dump = json.dumps(
                    tool.inputSchema,
                    sort_keys=True,
                    default=str,
                )
            except TypeError:
                schema_dump = str(tool.inputSchema)
            h.update(b"|")
            h.update(schema_dump.encode("utf-8"))
            h.update(b"||")
        fingerprint = "sha256:" + h.hexdigest()

        existing_meta = dict(result.meta or {})
        existing_meta["ttlMs"] = DEFAULT_LIST_TTL_MS
        existing_meta["spec"] = "SEP-2549"
        existing_meta["fingerprint"] = fingerprint
        result.meta = existing_meta
        return result
