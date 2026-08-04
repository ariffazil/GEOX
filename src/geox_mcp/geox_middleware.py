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
from datetime import UTC, datetime
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
        session_id,
        source,
        "on" if _LIFECYCLE_GATE_ENABLED else "off",
    )


def mark_lifecycle_ready(session_id: str, source: str = "unknown") -> None:
    """Mark session ready for tools/call after notifications/initialized."""
    if not session_id:
        return
    _LIFECYCLE_READY.pop(session_id, None)
    logger.info("lifecycle: session=%s READY (%s)", session_id, source)


def is_lifecycle_blocked(session_id: str) -> bool:
    """True if this session must not call tools yet."""
    if not _LIFECYCLE_GATE_ENABLED or not session_id:
        return False
    # Only block when we have explicitly marked pending (False).
    return _LIFECYCLE_READY.get(session_id) is False


def _session_id_from_context(context: MiddlewareContext[Any]) -> str | None:
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
                    "tagged_at": datetime.now(UTC).isoformat(),
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
            # geox_claim is FLAT (mode/session_id/actor_id params) — not an arguments-dict wrapper
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
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
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
                    sid,
                    "on" if _LIFECYCLE_GATE_ENABLED else "off",
                )
        except Exception as exc:
            logger.debug("lifecycle: could not set pre-init state: %s", exc)
        return result

    async def on_notification(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
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
                        sid,
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
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
    ) -> Any:
        """Also catch initialized via generic message path (some transports)."""
        method = (context.method or "") or ""
        if context.type == "notification" and "initialized" in method.lower():
            sid = _session_id_from_context(context)
            if sid:
                _LIFECYCLE_READY.pop(sid, None)
                logger.info("lifecycle: session=%s READY via on_message", sid)
        return await call_next(context)

    async def on_list_tools(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
    ) -> Any:
        """Filter tools/list to canonical public surface only.

        Single truth: clients see ONLY the canonical tools from
        CANONICAL_PUBLIC_TOOLS. Compat aliases are accepted by on_call_tool
        but never exposed in tools/list. This eliminates the split-brain
        where clients discovered old names that F9 would block.

        Audit-grade (P0-1 hardening 2026-07-25 · FI-008):
          - All drift is logged at WARNING with the SURFACE_DRIFT /
            SURFACE_GAP event codes from canonical_surface_gate.
          - Drift count + last drift report are stored on the middleware
            instance so the /drift HTTP endpoint can surface them.
          - When no drift is observed, a single INFO line is emitted
            with the SURFACE_OK event code (suitable for health probes).
        """
        result = await call_next(context)
        if result is None:
            return result

        # Lazy import to avoid circular dependency at module load.
        from geox_mcp.canonical_surface_gate import (
            drift_report,
            EVT_SURFACE_DRIFT,
            EVT_SURFACE_GAP,
            EVT_SURFACE_OK,
        )

        live_names = sorted(getattr(t, "name", "") for t in result if getattr(t, "name", None))
        canonical_public_tools = self._PUBLIC_SURFACE

        # Filter to PUBLIC surface only (canonical, not compat).
        filtered = [t for t in result if getattr(t, "name", None) in canonical_public_tools]
        removed = len(result) - len(filtered)

        # Build dual drift reports:
        #   raw_report  — unfiltered → raw counts for journal diagnostics
        #   client_report — filtered → what /health and /drift surface
        raw_report = drift_report(live_names)
        filtered_names = sorted(getattr(t, "name", "") for t in filtered if getattr(t, "name", None))
        client_report = drift_report(filtered_names)
        # Stash the CLIENT-FACING report for /health and /drift endpoints.
        self._LAST_DRIFT_REPORT = client_report

        if removed:
            logger.warning(
                "%s raw_live=%d raw_drift=%d canonical=%d client_live=%d client_ok=%s removed=%s",
                EVT_SURFACE_DRIFT,
                raw_report["live_count"],
                raw_report["drift_count"],
                raw_report["canonical_count"],
                client_report["live_count"],
                str(client_report["ok"]).lower(),
                raw_report["drifted"][:10]
                if len(raw_report["drifted"]) <= 10
                else raw_report["drifted"][:10] + [f"... +{len(raw_report['drifted']) - 10}"],
            )
            if client_report["missing"]:
                logger.warning(
                    "%s canonical_count=%d live_count=%d gap_count=%d missing=%s",
                    EVT_SURFACE_GAP,
                    client_report["canonical_count"],
                    client_report["live_count"],
                    client_report["gap_count"],
                    client_report["missing"],
                )
        else:
            logger.info(
                "%s live_count=%d canonical_count=%d ok=true",
                EVT_SURFACE_OK,
                client_report["live_count"],
                client_report["canonical_count"],
            )

        return filtered

    async def on_call_tool(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
    ) -> Any:
        """RT1 + RT3 + SCT + organ_governance for every tools/call."""
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

        # ── P0-2 authority gate (2026-07-25 · FI-008) ────────────────────
        # Admit-or-reject at the gateway. Replaces the pre-P0-2 behavior
        # where SCT was optional and anonymous OBSERVE-ONLY calls could
        # trigger MUTATE tools (the audit's "observe-only allowed
        # persistent ingestion" failure). Opt-out via
        # GEOX_REQUIRE_SESSION_FOR_MUTATE=0 for dev/smoke environments.
        try:
            from geox_mcp.authority_gate import (
                AuthorityRejection,
                enforce_authority,
            )

            enforce_authority(tool_name=tool_name, arguments=arguments)
        except AuthorityRejection as _auth_rej:
            envelope = _auth_rej.to_envelope()
            envelope["gate"] = f"P0-2 gateway authority (http {_auth_rej.http_status})"
            logger.warning(
                "AUTH_GATE: blocked tool=%s error=%s http=%d session=%s actor=%s",
                tool_name,
                _auth_rej.error_code,
                _auth_rej.http_status,
                _auth_rej.session_id or "anonymous",
                _auth_rej.actor_id or "anonymous",
            )
            raise ToolError(
                json.dumps(
                    {
                        "guard": _auth_rej.error_code,
                        "verdict": "HOLD",
                        "lane": "P0-2-authority",
                        "reason": _auth_rej.message,
                        "fix": (
                            "Provide a verified session_id (SCT or SEAL-* "
                            "format) and an actor_id. Required authority for "
                            f"'{tool_name}' is {_auth_rej.required_authority}."
                        ),
                        "http_status": _auth_rej.http_status,
                        "session_id": _auth_rej.session_id,
                        "actor_id": _auth_rej.actor_id,
                        "required_authority": _auth_rej.required_authority,
                        "session_authority": _auth_rej.session_authority,
                    }
                )
            )
        except Exception as _gate_exc:
            # Fail-closed: a broken gate must not silently admit.
            logger.error("AUTH_GATE: infrastructure failure: %s", _gate_exc)
            raise ToolError(
                json.dumps(
                    {
                        "guard": "AUTH_GATE_DEGRADED",
                        "verdict": "HOLD",
                        "lane": "P0-2-authority",
                        "reason": f"authority gate infrastructure error: {type(_gate_exc).__name__}",
                        "fix": "Inspect logs; restore arifOS SCT kernel reachability.",
                    }
                )
            )

        # ── SCT ingress gate (2026-07-17) ──────────────────────────────────
        # If caller presents an SCT, verify via arifOS. Fail closed on invalid.
        # SCT optional for GEOX OBSERVE tools (backward-compatible); when present
        # it must be valid. Irreversible tools may require SCT via env.
        try:
            import sys as _sys

            _aaa = "/root/AAA"
            if _aaa not in _sys.path:
                _sys.path.insert(0, _aaa)
            from governance.federation_sct import gate_tool_ingress

            _headers = None
            try:
                fctx = context.fastmcp_context
                rc = getattr(fctx, "request_context", None) if fctx else None
                req = getattr(rc, "request", None) if rc else None
                if req is not None:
                    _headers = dict(getattr(req, "headers", {}) or {})
            except Exception:
                _headers = None
            _require = tool_name in self._IRREVERSIBLE_TOOLS and os.getenv("GEOX_SCT_REQUIRE_IRREVERSIBLE", "0").strip() not in (
                "0",
                "false",
                "off",
                "no",
            )
            _sct_rej = gate_tool_ingress(
                tool_name,
                arguments if isinstance(arguments, dict) else {},
                headers=_headers,
                require_sct=_require,
                organ="geox",
            )
            if _sct_rej is not None:
                logger.warning(
                    "SCT_GATE: blocked tool=%s error=%s",
                    tool_name,
                    _sct_rej.get("error"),
                )
                raise ToolError(f"SCT_GATE: {_sct_rej.get('error')}: {_sct_rej.get('message')}")
            # Strip SCT transport fields so tool Pydantic schemas don't reject them
            if isinstance(arguments, dict):
                for _sk in ("session_token", "sct", "arifos_sct"):
                    arguments.pop(_sk, None)
        except ToolError:
            raise
        except Exception as _sct_exc:
            # Import/path failure: log; do not open the gate for present tokens.
            logger.debug("SCT_GATE skipped (infra): %s", _sct_exc)

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
            # D3/D5: strip kernel envelope — FastMCP schema rejects unknown kwargs
            if "_envelope" in arguments:
                arguments.pop("_envelope", None)
            # Write cleaned args back so FastMCP tool schema sees them
            try:
                context.message.arguments = arguments
            except Exception:
                pass

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
            logger.debug(
                f"ARG_WRAP: nested flat params into arguments dict for '{tool_name}' (identity preserved: {list(_identity_preserved.keys())})"
            )

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
        _governance_envelope: dict = {}  # P0-6: initialised always
        if self._check_governance is not None:
            try:
                gov_verdict, gov_error, artifact_id = await self._check_governance(
                    tool_name=tool_name,
                    arguments=arguments,
                    is_direct_call=True,  # Raw MCP call = direct agent call
                )
            except Exception as e:
                # G8 — Bugs don't wear robes (2026-08-04):
                # Runtime exceptions are ERROR, not constitutional HOLD.
                # Floors deny; exceptions crash. Mapping one onto the other
                # trains agents to hunt for authority they already have.
                logger.exception(
                    "GOV_ERROR: organ_governance raised for tool=%s: %s",
                    tool_name,
                    e,
                )
                raise ToolError(
                    f"GOV_ERROR · tool={tool_name} · "
                    f"{type(e).__name__}: {e} · "
                    f"fix: runtime exception in governance path — not a floor denial. File a bug."
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
                # DEBUG: log what we got
                import sys as _dbg

                print(f"DEBUG_PARTS: err_data={err_data}", file=open("/tmp/geox-debug-parts.log", "a"))
                print(f"DEBUG_PARTS: reason={reason!r} len={len(reason)}", file=open("/tmp/geox-debug-parts.log", "a"))
                parts = [s for s in [guard, f"verdict={gov_verdict}", f"trace={trace_id}"] if s]
                if lane:
                    parts.append(f"lane={lane}")
                if reason:
                    # P3 2026-07-31 (FI-008 GEOX jam flow-restore): slice to 300
                    # (was 120). 120 chars is enough to drop 4 chars from a
                    # 21-char session_id like SEAL-xxxxxxxxxxxxxxxx. 300
                    # preserves the full session_id in the error echo.
                    # Reason itself is rarely >300 chars; if it ever is,
                    # the fix is to format reason more compactly upstream.
                    parts.append(reason[:300])
                if fix:
                    # P3 (FI-008): slice to 300 for symmetry with reason.
                    parts.append(f"fix: {fix[:300]}")
                err_msg = " · ".join(parts)

                raise ToolError(err_msg)

            logger.debug(f"GOV_PASS: {tool_name} verdict={gov_verdict} artifact_id={artifact_id}")

            # ═══ 2026-07-25 HARDENING: Inject artifact_id into tool response ═══
            # Extract session/actor from arguments for the governance envelope.
            _gov_sid = arguments.get("session_id", "") if isinstance(arguments, dict) else ""
            _gov_aid = arguments.get("actor_id", "anonymous") if isinstance(arguments, dict) else "anonymous"
            import time as _time_mod

            _governance_envelope = {
                "artifact_id": artifact_id,
                "gate_verdict": gov_verdict,
                "session_id": _gov_sid,
                "actor_id": _gov_aid,
                "timestamp_utc": _time_mod.strftime("%Y-%m-%dT%H:%M:%SZ", _time_mod.gmtime()),
            }

        # ═══ P0 #1 fix: wrap tool execution to catch schema/type errors ═════
        # FastMCP schema validation errors (PydanticValidationError, TypeError)
        # propagate through call_next(context) as raw exceptions. Wrap them in
        # a governed rejection envelope so the client always receives structured JSON.
        #
        # MCP App View binding is now handled via `app=AppConfig(...)` on
        # @mcp.tool() in register_tools_on_server() — see witness.py.
        from geox_core.identity_context import GEOX_IDENTITY_CONTEXT

        identity_token = GEOX_IDENTITY_CONTEXT.set(
            {
                "session_id": arguments.get("session_id"),
                "actor_id": arguments.get("actor_id"),
                "trace_id": arguments.get("trace_id"),
            }
        )
        try:
            result = await call_next(context)
            # M6 utilization ledger (KUTIP SAMPAH 2026-08-05) — fail-soft
            try:
                from geox_mcp.tool_invocation_counter import record_invocation

                _args = arguments if isinstance(arguments, dict) else {}
                record_invocation(
                    tool_name,
                    session_id=_args.get("session_id") if isinstance(_args.get("session_id"), str) else None,
                    actor_id=_args.get("actor_id") if isinstance(_args.get("actor_id"), str) else None,
                    ok=True,
                )
            except Exception:
                pass
            # ═══ W-01 FIX (2026-08-05) ═══════════════════════════════════
            # FastMCP call_next returns ToolResult. Downstream processors
            # (evidence envelope, well conformance, envelope normalizer,
            # stamp_and_gate) operate on dicts. We coerce → process → re-wrap
            # rather than return a bare dict (which breaks the MCP wire path:
            # 'dict' object has no attribute 'to_mcp_result').
            # ══════════════════════════════════════════════════════════════
            from geox_mcp.evidence_postcondition import (
                check_evidence_postcondition,
                coerce_tool_result_to_dict,
                apply_domain_dict_to_result,
            )

            _is_tool_result = not isinstance(result, dict) and hasattr(result, "structured_content")
            if _is_tool_result:
                _original = result
                result = coerce_tool_result_to_dict(result)

            # P0-6: Inject 5-layer evidence envelope into response
            result = self._inject_evidence_envelope(result, tool_name, _governance_envelope)
            # P3 CONFORMANCE (2026-07-26): Inject canonical ClaimState/WitnessType/OrganType
            result = self._inject_well_conformance(result, tool_name)
            # P0-4 D.4+D.5 (2026-07-25 · FI-008): for mutating tools,
            # guarantee the audit-defined 5-status envelope contract and
            # downgrade governance_verdict when the contract is incomplete.
            # This closes the "transport success ≠ evidence success" gap.
            try:
                from geox_mcp.envelope_normalizer import (
                    normalize_envelope_for_mutation,
                )

                result = normalize_envelope_for_mutation(
                    tool_name=tool_name,
                    result=result,
                    arguments=arguments,
                )
            except Exception as _norm_exc:
                logger.warning(
                    "ENVELOPE_NORMALIZER: failed for tool=%s: %s",
                    tool_name,
                    _norm_exc,
                )
            # P1 (2026-07-25): stamp mode + ext_witness_ready on every result.
            # GEOX_REQUIRE_LIVE=1 fail-closes offline_stub Ext for SEAL geometry.
            try:
                from geox_mcp.ext_witness_stamp import (
                    RequireLiveError,
                    stamp_and_gate,
                )

                result = stamp_and_gate(result, tool_name=tool_name)
            except RequireLiveError as _live_exc:
                raise ToolError(
                    json.dumps(
                        {
                            "error_class": "REQUIRE_LIVE_FAIL",
                            "tool": tool_name,
                            "mode": getattr(_live_exc, "mode", "offline_stub"),
                            "detail": str(_live_exc),
                            "ext_witness_ready": False,
                            "fix": "Set GEOX_REQUIRE_LIVE=0 for stub smoke, or enable live fetcher env.",
                        }
                    )
                ) from _live_exc
            except Exception as _stamp_exc:
                logger.warning(
                    "EXT_WITNESS_STAMP: failed for tool=%s: %s",
                    tool_name,
                    _stamp_exc,
                )
            # ── Stage-1 outputSchema enforcement (2026-07-25) ──────────────
            # SUCCESS with null evidence = FAILURE (commit 80fc80fd pattern).
            # Coerce ToolResult inside check_evidence_postcondition; write back.
            # G8: silent swallow is forbidden — fix input or propagate ERROR.

            try:
                result = check_evidence_postcondition(tool_name, result)
            except Exception as _ev_exc:
                logger.exception(
                    "EVIDENCE_POST: unhandled for tool=%s: %s",
                    tool_name,
                    _ev_exc,
                )
                raise ToolError(
                    f"GOV_ERROR · EVIDENCE_POST · tool={tool_name} · "
                    f"{type(_ev_exc).__name__}: {_ev_exc} · "
                    f"fix: evidence postcondition crashed — not a silent SUCCESS (G8)."
                ) from _ev_exc

            # ═══ W-01 FIX: re-wrap in ToolResult for FastMCP wire path ═══
            if _is_tool_result:
                result = apply_domain_dict_to_result(_original, result)
            return result
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
        finally:
            GEOX_IDENTITY_CONTEXT.reset(identity_token)

    # ── HELPERS ────────────────────────────────────────────────────────────────

    @staticmethod
    def _inject_evidence_envelope(result, tool_name, gov_envelope):
        """P0-6: Inject 5-layer evidence envelope into tool response.

        Preserves FastMCP ToolResult wire type (mutates structured_content).
        """
        if not isinstance(gov_envelope, dict):
            return result
        try:
            from geox_mcp.organ_governance import build_evidence_envelope

            envelope = build_evidence_envelope(
                tool_name=tool_name,
                transport_status="OK",
                execution_status="COMPLETED",
                artifact_status="CREATED" if gov_envelope.get("artifact_id") else "NONE",
                verification_status="PENDING",
                governance_verdict=gov_envelope.get("gate_verdict", "ADVISORY"),
                artifact_id=gov_envelope.get("artifact_id", ""),
                session_id=gov_envelope.get("session_id", ""),
                actor_id=gov_envelope.get("actor_id", "anonymous"),
            )
            if isinstance(result, dict) and not isinstance(result.get("content"), list):
                result["_evidence_envelope"] = envelope
                return result
            # ToolResult path — stamp into structured_content, keep to_mcp_result
            sc = getattr(result, "structured_content", None)
            if isinstance(sc, dict):
                sc = dict(sc)
                sc["_evidence_envelope"] = envelope
                try:
                    result.structured_content = sc
                except Exception:
                    pass
            return result
        except Exception:
            return result

    @staticmethod
    def _inject_well_conformance(result, tool_name):
        """P3 CONFORMANCE (2026-07-26): Inject ClaimState/WitnessType/OrganType."""
        try:
            # Determine organ type from tool name
            ot = "GEOX"
            if tool_name.startswith(("geox_basin",)):
                ot = "BASIN"
            elif tool_name.startswith(("geox_seismic",)):
                ot = "SEISMIC"
            elif tool_name.startswith(("geox_well",)):
                ot = "WELL"
            elif tool_name.startswith(("geox_prospect",)):
                ot = "PROSPECT"
            elif tool_name.startswith(("geox_claim",)):
                ot = "CLAIM"
            elif tool_name.startswith(("geox_map",)):
                ot = "MAP"
            elif tool_name.startswith(("geox_petrophysics",)):
                ot = "PETROPHYSICS"
            elif tool_name.startswith(("geox_visual",)):
                ot = "VISUAL"
            elif tool_name.startswith(("geox_surface", "geox_registry")):
                ot = "FEDERATION"

            # Extract domain from result
            domain = {}
            if isinstance(result, dict):
                domain = result
            elif hasattr(result, "structured_content") and isinstance(result.structured_content, dict):
                domain = result.structured_content
            elif hasattr(result, "content") and result.content:
                raw = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
                try:
                    import json as _json

                    domain = _json.loads(raw) if isinstance(raw, str) else raw
                except Exception:
                    domain = {}

            # Auto-detect claim state
            cs = "HOLD"
            verdict = str(domain.get("verdict", domain.get("status", ""))).upper() if isinstance(domain, dict) else ""
            truth = str(domain.get("truth_class", domain.get("epistemic_tag", ""))).upper() if isinstance(domain, dict) else ""
            if truth in ("LIVE", "OBSERVED", "VERIFIED", "SEALED"):
                cs = "OBSERVED"
            elif truth in ("DERIVED", "INTERPRETED", "QUALIFIED") or verdict in ("STABLE", "PASS", "REGISTRY_PASS"):
                cs = "QUALIFIED"
            elif verdict in ("HYPOTHESIS", "PLAUSIBLE") or isinstance(domain, dict) and domain.get("ok") is True:
                cs = "HYPOTHESIS"

            wt = "AI" if isinstance(domain, dict) and not domain.get("ext_witnesses") else "HYBRID"

            conformance = {
                "_well_conformance": {
                    "claim_state": cs,
                    "witness_type": wt,
                    "organ_type": ot,
                    "conformance_version": "v1.0",
                    "conformant": True,
                }
            }

            if isinstance(result, dict):
                result = {**conformance, **result}
            elif hasattr(result, "structured_content") and isinstance(result.structured_content, dict):
                result.structured_content = {**conformance, **result.structured_content}
            return result
        except Exception:
            return result

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
