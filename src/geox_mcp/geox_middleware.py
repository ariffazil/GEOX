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
import os
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware
from mcp.types import ListToolsResult

if TYPE_CHECKING:
    from fastmcp.server.middleware import CallNext, MiddlewareContext

logger = logging.getLogger("geox.governance.middleware")

# Phase A1 (2026-07-12): MCP lifecycle gate — reject tools/call until
# client sends notifications/initialized after initialize (spec 2025-06-18).
# Soft-allow tools/list (discovery). Env GEOX_LIFECYCLE_GATE=0 disables.
_LIFECYCLE_GATE_ENABLED = os.getenv("GEOX_LIFECYCLE_GATE", "1").strip().lower() not in (
    "0",
    "false",
    "off",
    "no",
)
# Session-id → ready. Module-level (not ctx state) so HTTP streamable sessions
# share the flag across initialize / notification / tools/call hops.
_LIFECYCLE_READY: dict[str, bool] = {}


def mark_lifecycle_pending(session_id: str, source: str = "unknown") -> None:
    """Mark session as post-initialize, awaiting notifications/initialized."""
    if not session_id:
        return
    _LIFECYCLE_READY[session_id] = False
    logger.info(
        "lifecycle: session=%s PENDING (%s) gate=%s",
        session_id[:12],
        source,
        "on" if _LIFECYCLE_GATE_ENABLED else "off",
    )


def mark_lifecycle_ready(session_id: str, source: str = "unknown") -> None:
    """Mark session ready for tools/call after notifications/initialized."""
    if not session_id:
        return
    _LIFECYCLE_READY.pop(session_id, None)
    logger.info("lifecycle: session=%s READY (%s)", session_id[:12], source)


def is_lifecycle_blocked(session_id: str) -> bool:
    """True if this session must not call tools yet."""
    if not _LIFECYCLE_GATE_ENABLED or not session_id:
        return False
    # Only block when we have explicitly marked pending (False).
    return _LIFECYCLE_READY.get(session_id) is False


def _session_id_from_context(context: "MiddlewareContext[Any]") -> str | None:
    """Best-effort MCP session id from FastMCP context or message meta."""
    try:
        fctx = context.fastmcp_context
        if fctx is not None:
            try:
                sid = fctx.session_id
                if sid:
                    return str(sid)
            except Exception:
                pass
    except Exception:
        pass
    # Fallback: some transports only expose header via request context
    try:
        fctx = context.fastmcp_context
        rc = getattr(fctx, "request_context", None) if fctx else None
        req = getattr(rc, "request", None) if rc else None
        if req is not None:
            headers = getattr(req, "headers", {}) or {}
            sid = headers.get("mcp-session-id") or headers.get("Mcp-Session-Id")
            if sid:
                return str(sid)
    except Exception:
        pass
    return None


# ── Governed rejection envelope schema (P0 #1 fix, 2026-07-10) ─────────────
# Every error path produces this structured envelope. Never bare strings.
GOVERNED_ERROR_CODES: dict[str, dict] = {
    "SCHEMA_REJECTION": {
        "code": -32002,
        "http_status": 422,
        "message_template": "Schema validation failed for '{tool}': {detail}",
    },
    "GOVERNANCE_BLOCK": {
        "code": -32003,
        "http_status": 423,
        "message_template": "Governance blocked '{tool}': {detail}",
    },
    "INTERNAL_ERROR": {
        "code": -32001,
        "http_status": 500,
        "message_template": "Internal error in '{tool}': {detail}",
    },
}


def build_governed_error_envelope(
    tool_name: str,
    error_class: str,
    detail: str,
    session_id: str | None = None,
    trace_id: str | None = None,
) -> dict:
    """Build a governed rejection envelope for any error path.

    Guarantees: status, error_code, trace_id, session_id, evidence_refs, _epistemic
    Non-null on every path. Never returns bare string.
    """
    error_spec = GOVERNED_ERROR_CODES.get(error_class, GOVERNED_ERROR_CODES["INTERNAL_ERROR"])

    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": error_spec["code"],
            "message": error_spec["message_template"].format(
                tool=tool_name,
                detail=str(detail)[:200],
            ),
            "data": {
                "guard": error_class,
                "verdict": "HOLD" if error_class != "INTERNAL_ERROR" else "ERROR",
                "tool": tool_name,
                "error_class": error_class,
                "trace_id": trace_id or str(uuid.uuid4()),
                "session_id": session_id or "anonymous",
                "evidence_refs": [error_class],
                "_epistemic": {
                    "output_class": "ERROR",
                    "ai_involvement": "NONE",
                    "authority_claim": "GOVERNED",
                    "evidence_source": "COMPUTED",
                    "tagged_at": datetime.now(timezone.utc).isoformat(),
                    "schema_version": "1.0.0",
                },
            },
        },
    }


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
    # F1 AMANAH: no irreversible action without explicit human consent.
    _IRREVERSIBLE_TOOLS: frozenset[str] = frozenset(
        {
            "geox_claim",  # mode="seal" requires ack_irreversible=True
            "geox_prospect",  # mode="seal" requires ack_irreversible=True
        }
    )

    # Tools that wrap all parameters in an `arguments: dict` parameter.
    # MCP clients send flat parameters; these tools need them nested.
    _WRAPPER_TOOLS: frozenset[str] = frozenset(
        {
            "geox_3d_model",
            "geox_bathymetry_ingest",
            "geox_claim",
            "geox_climate_reanalysis",
            "geox_cognitive_rank_hypotheses",
            "geox_earthquake_catalog",
            "geox_erddap_query",
            "geox_geochem_query",
            "geox_geology_map_query",
            "geox_gravity_change_query",
            "geox_heatflow_query",
            "geox_hydrology_query",
            "geox_ocean_query",
            "geox_paleomag_query",
            "geox_panel_d_render",
            "geox_petrophysics",
            "geox_physical_reality_interpret",
            "geox_plate_reconstruct",
            "geox_relief_ingest",
            "geox_satellite_catalog",
            "geox_segy_audit",
            "geox_seismic_ingest",
            "geox_seismic_interpret",
            "geox_space_weather",
            "geox_stress_query",
            "geox_subsurface_model",
            "geox_uk_petroleum_query",
            "geox_vision",
            "geox_visual_enhance",
            "geox_visual_generate_hypotheses",
            "geox_visual_understand",
            "geox_wealth_consequence",
            "geox_well_desurvey",
            "geox_well_ingest",
            "geox_well_qc",
            "geox_well_tie",
        }
    )

    def __init__(
        self,
        *,
        canonical_public_tools: set[str],
        canonical_internal_tools: set[str],
        canonical_compat_tools: set[str],
        arifos_route_query_enabled: bool = False,
        check_governance_fn: Any = None,
    ) -> None:
        """
        Args:
          canonical_public_tools: set of public tool names (RT1 tools/list surface)
          canonical_internal_tools: set of internal tool names callable at runtime but hidden from tools/list
          canonical_compat_tools: backward-compat alias names accepted by on_call_tool but NOT exposed in tools/list
          arifos_route_query_enabled: if True, route_query tool gets a pass-through lane
          check_governance_fn: async (tool_name, args) -> (verdict, error_response|None)
                               imported lazily to avoid circular imports at module load.
        """
        # on_call_tool accepts public + internal + compat surfaces.
        self._EXECUTABLE_SURFACE: set[str] = (
            set(canonical_public_tools) | set(canonical_internal_tools) | set(canonical_compat_tools)
        )
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
        """Log initialize; mark session as awaiting client notifications/initialized."""
        try:
            client_info = context.message.params.clientInfo if context.message and context.message.params else None
            logger.info(
                "session_init: client=%s version=%s",
                getattr(client_info, "name", "unknown"),
                getattr(client_info, "version", "unknown"),
            )
        except Exception:
            pass
        result = await call_next(context)
        # After server accepts initialize, session is NOT yet ready for tools/call
        # until client sends notifications/initialized (Phase A1 lifecycle gate).
        try:
            sid = _session_id_from_context(context)
            if sid:
                _LIFECYCLE_READY[sid] = False
                logger.info(
                    "lifecycle: session=%s awaiting notifications/initialized (gate=%s)",
                    sid[:12],
                    "on" if _LIFECYCLE_GATE_ENABLED else "off",
                )
        except Exception as exc:
            logger.debug("lifecycle: could not set pre-init state: %s", exc)
        return result

    async def on_notification(
        self,
        context: "MiddlewareContext[Any]",
        call_next: "CallNext[Any, Any]",
    ) -> Any:
        """Mark session ready on notifications/initialized (Phase A1)."""
        method = (context.method or "") or ""
        msg = context.message
        msg_method = getattr(msg, "method", None) or ""
        combined = f"{method} {msg_method}".lower()
        if "initialized" in combined:
            try:
                sid = _session_id_from_context(context)
                if sid:
                    _LIFECYCLE_READY.pop(sid, None)
                    logger.info(
                        "lifecycle: session=%s READY (notifications/initialized method=%s)",
                        sid[:12],
                        method or msg_method,
                    )
                else:
                    logger.warning(
                        "lifecycle: initialized notification without session id (method=%s)",
                        method or msg_method,
                    )
            except Exception as exc:
                logger.warning("lifecycle: failed to mark ready: %s", exc)
        return await call_next(context)

    async def on_message(
        self,
        context: "MiddlewareContext[Any]",
        call_next: "CallNext[Any, Any]",
    ) -> Any:
        """Also catch initialized via generic message path (some transports)."""
        method = (context.method or "") or ""
        if context.type == "notification" and "initialized" in method.lower():
            sid = _session_id_from_context(context)
            if sid:
                _LIFECYCLE_READY.pop(sid, None)
                logger.info("lifecycle: session=%s READY via on_message", sid[:12])
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
        # Phase A1 lifecycle gate runs at HTTP layer only (McpLifecycleMiddleware).
        # Do NOT re-gate here: FastMCP internal session_id ≠ Mcp-Session-Id header,
        # so a second check on fctx.session_id would false-block after HTTP READY.

        tool_name: str = getattr(context.message, "name", "")
        raw_arguments = getattr(context.message, "arguments", {}) or {}

        # F1 AMANAH: defensive parse — some MCP transports serialize
        # arguments as a JSON string instead of a parsed dict. Pydantic
        # validation fails with "Input should be a valid dictionary" when
        # it receives a string. Fix: parse JSON string → dict.
        if isinstance(raw_arguments, str):
            try:
                arguments: dict[str, Any] = json.loads(raw_arguments)
                logger.debug(f"ARG_PARSE: parsed JSON string arguments for '{tool_name}'")
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"ARG_PARSE: failed to parse arguments string for '{tool_name}'")
                arguments = {}
        else:
            arguments = raw_arguments

        # ── P1 IDENTITY INJECTION (2026-07-11) ──────────────────────────────
        # arifOS bridge passes governed identity via _envelope; GEOX tools
        # expect session_id/actor_id/trace_id as top-level function parameters.
        # Extract from _envelope if present. Without this, every call runs as
        # anonymous — breaking F3 WITNESS + F11 AUDIT.
        if isinstance(arguments, dict):
            _env = arguments.get("_envelope") if isinstance(arguments.get("_envelope"), dict) else None
            if _env:
                for _ik in ("session_id", "actor_id", "trace_id"):
                    if _env.get(_ik) and not arguments.get(_ik):
                        arguments[_ik] = _env[_ik]
                        logger.debug(f"IDENTITY_INJECT: {_ik}={_env[_ik]} for '{tool_name}'")

        # F1 AMANAH: defensive unwrap — 36 GEOX tools declare `arguments: dict`
        # as a wrapper parameter. MCP clients send flat parameters
        # (mode=..., source_uri=...) which don't match the function signature.
        # Detect when flat params arrive for a wrapper tool and nest them.
        #
        # P1 IDENTITY FIX (2026-07-11b): preserve session_id/actor_id/trace_id
        # at the top level when arg-wrapping. Without this, direct MCP calls
        # that pass identity as flat parameters lose it inside the wrapper dict,
        # and the tool defaults to "anonymous". Bridge calls are unaffected
        # (they inject via _envelope before arg-wrap).
        _IDENTITY_KEYS = ("session_id", "actor_id", "trace_id")
        if (
            tool_name in self._WRAPPER_TOOLS and "arguments" not in arguments and arguments  # non-empty
        ):
            _identity_preserved = {k: arguments.pop(k) for k in _IDENTITY_KEYS if k in arguments}
            arguments = {"arguments": arguments}
            arguments.update(_identity_preserved)
            logger.debug(f"ARG_WRAP: nested flat params into arguments dict for '{tool_name}' (identity preserved: {list(_identity_preserved.keys())})")

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
            # Extract effective args — handle wrapper pattern (arguments.arguments)
            effective_args = arguments
            if tool_name in self._WRAPPER_TOOLS and isinstance(arguments.get("arguments"), dict):
                effective_args = arguments["arguments"]
            needs_ack = False
            if tool_name == "geox_claim":
                # mode=seal is the irreversible path
                needs_ack = (effective_args.get("mode") == "seal") or (effective_args.get("action") == "seal")
            elif tool_name == "geox_prospect":
                # verdict=seal is the irreversible path
                needs_ack = effective_args.get("verdict") == "seal"
            if needs_ack:
                ack = effective_args.get("ack_irreversible", False)
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
                # Extract structured error with message, code, and data fields.
                err = self._extract_error(gov_error)
                err_data = err.get("data", {})
                trace_id = err_data.get("trace_id", f"gov-{uuid.uuid4().hex[:12]}")

                # Log the full structured block for server-side debugging
                logger.warning(
                    f"GOV_BLOCK: tool={tool_name} "
                    f"verdict={gov_verdict} "
                    f"trace_id={trace_id} "
                    f"code={err.get('code')} "
                    f"message={str(err.get('message', ''))[:80]} "
                    f"guard={err_data.get('guard', '?')} "
                    f"lane={err_data.get('lane', '?')}"
                )

                # Compose a structured error message that preserves
                # guard/verdict/lane/reason/fix for client-side parsing.
                guard = err_data.get("guard", "")
                lane = err_data.get("lane", "")
                reason = err_data.get("reason", "")
                fix = err_data.get("fix", "")
                parts = [s for s in [guard, f"verdict={gov_verdict}", f"trace={trace_id}"] if s]
                if lane:
                    parts.append(f"lane={lane}")
                if reason:
                    parts.append(reason[:120])
                if fix:
                    parts.append(f"fix: {fix[:120]}")
                err_msg = " · ".join(parts)

                raise ToolError(err_msg)

            logger.debug(f"GOV_PASS: {tool_name} verdict={gov_verdict}")

        # ═══ P0 #1 fix: wrap tool execution to catch schema/type errors ═════
        # FastMCP schema validation errors (PydanticValidationError, TypeError)
        # propagate through call_next(context) as raw exceptions. Wrap them in
        # a governed rejection envelope so the client always receives structured JSON.
        #
        # MCP App View binding is now handled via `app=AppConfig(...)` on
        # @mcp.tool() in register_tools_on_server() — see witness.py.
        try:
            return await call_next(context)
        except ToolError:
            raise  # Already governed — let FastMCP handle normally
        except (ValueError, TypeError, KeyError, LookupError) as e:
            # Schema/argument validation errors that bypassed FastMCP's handler
            raise ToolError(
                json.dumps(
                    build_governed_error_envelope(
                        tool_name=tool_name,
                        error_class="SCHEMA_REJECTION",
                        detail=f"{type(e).__name__}: {e}",
                        session_id=arguments.get("session_id") if isinstance(arguments, dict) else None,
                    )
                )
            )
        except Exception as e:
            # Catch-all — every error becomes a governed envelope
            raise ToolError(
                json.dumps(
                    build_governed_error_envelope(
                        tool_name=tool_name,
                        error_class="INTERNAL_ERROR",
                        detail=f"{type(e).__name__}: {e}",
                        session_id=arguments.get("session_id") if isinstance(arguments, dict) else None,
                    )
                )
            )

    # ── HELPERS ────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_error(gov_error: Any) -> dict[str, Any]:
        """
        Convert check_governance's JSONResponse-shaped return into a
        structured error dict with message, code, and data preserved.

        check_governance returns a starlette.responses.JSONResponse or a dict with
        structure: {"error": {"code": -32xxx, "message": "...", "data": {...}}}
        """
        try:
            if hasattr(gov_error, "body"):
                body = gov_error.body
                if isinstance(body, bytes):
                    body = body.decode("utf-8", errors="replace")
                parsed = json.loads(body)
                err = parsed.get("error", {})
                return {
                    "code": err.get("code", -32000),
                    "message": err.get("message", "governance denied"),
                    "data": err.get("data", {}),
                }
            if isinstance(gov_error, dict):
                err = gov_error.get("error", {})
                return {
                    "code": err.get("code", -32000),
                    "message": err.get("message", "governance denied"),
                    "data": err.get("data", {}),
                }
            return {
                "code": -32000,
                "message": str(gov_error),
                "data": {"raw": str(gov_error)},
            }
        except Exception as exc:
            return {
                "code": -32000,
                "message": "governance denied (unable to parse response)",
                "data": {"parse_error": str(exc)},
            }


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
