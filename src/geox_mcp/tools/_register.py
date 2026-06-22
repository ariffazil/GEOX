"""
GEOX Tool Registration Engine — Shared wrapper & annotation logic.
══════════════════════════════════════════════════════════════════════
Extracted from unified_13.py for domain-server composition via mcp.mount().

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from typing import Any

from fastmcp import FastMCP

from geox_mcp.floor_enforcement import (
    HUMILITY_CAP,
    enforce_floor_post_call,
    enforce_floor_pre_call,
    get_idempotency_store,
)
from geox_mcp.organ_governance import GEOX_RISK_MAP, RiskTier

logger = logging.getLogger("geox.register")


# ── Evidence Contract envelope (Appendix B of 000_CONSTITUTION.md) ─────────
# GEOX already emits many envelope-like fields (perception_class,
# claim_state, evidence_tag, cross_modal_stability, dim_spot_flag,
# metabolic.uncertainty.uncertainty_range). This wrapper maps them to the
# canonical 6-field envelope AND places all existing fields under "result"
# per spec. arifOS reads this; it does not negotiate field names.
# GEOX does NOT name the Laws (L01-L13) — that is arifOS's job.

_EPISTEMIC_MAP = {
    "OBSERVED": "CLAIM",
    "FACT": "CLAIM",
    "MEASURED": "CLAIM",
    "INTERPRETATION": "PLAUSIBLE",
    "INFERRED": "PLAUSIBLE",
    "HYPOTHESIS": "HYPOTHESIS",
    "ESTIMATE": "ESTIMATE",
    "SPECULATION": "ESTIMATE",
    "UNKNOWN": "UNKNOWN",
    "VOID": "UNKNOWN",
}

_CONFIDENCE_QUALITY = {
    # F7 HUMILITY: HIGH=0.90 (was 0.95 — violated F7 cap). 0.90 is the
    # constitutional floor for any evidence_quality value in the GEOX surface.
    "HIGH": HUMILITY_CAP,
    "MEDIUM": 0.70,
    "MODERATE": 0.70,
    "LOW": 0.30,
    "VERY_LOW": 0.10,
    "NONE": 0.05,
}


def _classify_geox_epistemic(result: dict) -> tuple:
    """Derive (epistemic_tag, evidence_quality) from GEOX result fields."""
    # Tag: prefer perception_class → claim_state → evidence_tag
    raw = result.get("perception_class") or result.get("claim_state") or result.get("evidence_tag") or "UNKNOWN"
    tag = _EPISTEMIC_MAP.get(str(raw).upper(), "UNKNOWN")
    # Quality: confidence_level + humility_score (inverted)
    conf = str(result.get("confidence_level") or "LOW").upper()
    quality = _CONFIDENCE_QUALITY.get(conf, 0.30)
    humility = float(result.get("humility_score") or 0.0)
    # Adjust: high humility → lower quality (organ admits uncertainty)
    if humility > 0.3:
        quality = max(quality - 0.15, 0.10)
    # Penalize dim_spot_flag (negative constraint warning)
    if result.get("dim_spot_flag"):
        quality = max(quality - 0.10, 0.10)
    # Penalize conflict_flags
    conflicts = result.get("conflict_flags") or []
    if isinstance(conflicts, list) and conflicts:
        quality = max(quality - 0.05 * len(conflicts), 0.05)
    return (tag, round(quality, 4))


def _geox_wrap_envelope(tool_name: str, result: Any) -> Any:
    """Wrap a GEOX tool result in the canonical Evidence Contract envelope."""
    if not isinstance(result, dict):
        return result
    # Skip if already enveloped (idempotent)
    if "epistemic_tag" in result and "evidence_quality" in result and "result" in result:
        return result
    # Governance / error blocks pass through unwrapped
    if result.get("error_code") or result.get("governance_status") == "BLOCKED":
        return result

    tag, quality = _classify_geox_epistemic(result)

    # Uncertainty band: from metabolic.uncertainty.uncertainty_range
    metabolic = result.get("metabolic") or {}
    uncertainty = metabolic.get("uncertainty") or {}
    band = uncertainty.get("uncertainty_range") or [0.03, 0.05]
    if not (isinstance(band, list) and len(band) == 2):
        band = [0.03, 0.05]

    # delta_S: from existing fields if present, else heuristic
    delta_s = metabolic.get("delta_s")
    if delta_s is None:
        # Heuristic: -0.05 base, +0.05 per conflict, -0.02 if high quality
        conflicts = result.get("conflict_flags") or []
        n_conf = len(conflicts) if isinstance(conflicts, list) else 0
        delta_s = round(-0.05 + (0.05 * n_conf) - (0.02 * quality), 4)

    # source_attribution: from provenance + tool name
    # F1-FIX 2026-06-06: provenance may be a string (default for claim_create) instead of a dict.
    # Guard with isinstance so we don't crash every tool that emits a string provenance.
    provenance_raw = result.get("provenance")
    provenance = provenance_raw if isinstance(provenance_raw, dict) else {}
    source_attribution = [
        "GEOX:src/geox_mcp/server.py",
        f"GEOX:tool/{tool_name}",
    ]
    if provenance.get("tool_version"):
        source_attribution.append(f"GEOX:version/{provenance['tool_version']}")

    # GEOX identity anchor: physics_manifest_hash + domain_law
    try:
        from geox_core.physics.manifest import get_domain_law, get_physics_manifest_hash

        _env_domain_law = get_domain_law()
        _env_physics_hash = get_physics_manifest_hash()
    except Exception:
        import os as _os_env

        _env_domain_law = "NATURAL_LAW"
        _env_physics_hash = _os_env.environ.get("GEOX_PHYSICS_MANIFEST_HASH", "sha256:missing")

    # Build the envelope. Per Appendix B, the original payload goes under "result".
    envelope = {
        "result": result,
        "epistemic_tag": tag,
        "evidence_quality": quality,
        "source_attribution": source_attribution,
        "uncertainty_band": [round(float(band[0]), 4), round(float(band[1]), 4)],
        "delta_S": round(float(delta_s), 4),
        "domain_law": _env_domain_law,
        "physics_manifest_hash": _env_physics_hash,
    }
    return envelope


def _make_receipt_wrapper(func: Any, name: str) -> Any:
    """Wrap a tool function to write Supabase domain receipts (fail-soft) AND emit Evidence Contract envelope."""

    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        import inspect
        import os

        # Extract session/provenance fields from kwargs
        session_id = kwargs.pop("session_id", None)
        actor_id = kwargs.pop("actor_id", None)
        trace_id = kwargs.pop("trace_id", None)
        # F1 AMANAH — idempotency key (optional, for replay-safe calls)
        idempotency_key = kwargs.pop("idempotency_key", None)
        # F13 SOVEREIGN — explicit acknowledgement for IRREVERSIBLE tier
        ack_irreversible = kwargs.pop("ack_irreversible", None)

        # ── F1/F9/F13 — pre-call floor enforcement ──────────────────────────
        risk_tier = GEOX_RISK_MAP.get(name, RiskTier.C1_ADVISORY)
        pre_call = enforce_floor_pre_call(
            tool_name=name,
            kwargs=kwargs,
            risk_tier=str(risk_tier),
        )
        if pre_call.outcome == "BLOCK":
            logger.error(f"Floor BLOCK on {name}: {pre_call.reason}")
            # F11 AUDIT — record the blocked attempt
            enforce_floor_post_call(
                tool_name=name,
                result={"error_code": "FLOOR_BLOCK"},
                kwargs=kwargs,
                risk_tier=str(risk_tier),
                pre_call=pre_call,
                duration_ms=0.0,
            )
            return {
                "error_code": "FLOOR_BLOCK",
                "governance_status": "BLOCKED",
                "tool_name": name,
                "reason": pre_call.reason,
                "call_hash": pre_call.call_hash,
            }
        if pre_call.outcome == "HOLD":
            logger.warning(f"Floor HOLD on {name}: {pre_call.reason}")
            # F11 AUDIT — record the held attempt
            enforce_floor_post_call(
                tool_name=name,
                result={"error_code": "FLOOR_HOLD"},
                kwargs=kwargs,
                risk_tier=str(risk_tier),
                pre_call=pre_call,
                duration_ms=0.0,
            )
            return {
                "error_code": "FLOOR_HOLD",
                "governance_status": "HOLD",
                "tool_name": name,
                "reason": pre_call.reason,
                "required_params": pre_call.required_params,
                "call_hash": pre_call.call_hash,
            }

        # ── F1 AMANAH — idempotency check (replay-safe) ────────────────────
        if idempotency_key:
            outcome, reason = get_idempotency_store().check(
                idempotency_key, pre_call.call_hash
            )
            if outcome == "BLOCK":
                logger.error(
                    f"F1 idempotency violation on {name}: {reason}"
                )
                return {
                    "error_code": "F1_IDEMPOTENCY_VIOLATION",
                    "governance_status": "BLOCKED",
                    "tool_name": name,
                    "reason": reason,
                }

        # ── Run the tool ────────────────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            if inspect.iscoroutinefunction(func):
                res = await func(*args, **kwargs)
            else:
                res = func(*args, **kwargs)
        except Exception as exc:
            # F4 CLARITY — log the failure but return a structured error
            duration_ms = (time.perf_counter() - t0) * 1000
            enforce_floor_post_call(
                tool_name=name,
                result={"error": str(exc)},
                kwargs=kwargs,
                risk_tier=str(risk_tier),
                pre_call=pre_call,
                duration_ms=duration_ms,
            )
            raise
        duration_ms = (time.perf_counter() - t0) * 1000

        # ── F4/F7/F11 — post-call floor enforcement + audit ─────────────────
        post_call = enforce_floor_post_call(
            tool_name=name,
            result=res,
            kwargs=kwargs,
            risk_tier=str(risk_tier),
            pre_call=pre_call,
            duration_ms=duration_ms,
        )
        for w in post_call.warnings:
            logger.info(f"[{name}] {w}")

        # Inject session/provenance plumbing into envelope (P4)
        if isinstance(res, dict):
            # If it is already enveloped (has epistemic_tag and result)
            if "epistemic_tag" in res and "result" in res:
                # Always propagate session lineage — never conditionally drop.
                # If caller passed session_id, it must reach every downstream field.
                res["session_id"] = session_id
                if trace_id:
                    res["trace_id"] = trace_id

                # Plumb provenance
                prov = res.setdefault("provenance", {})
                if isinstance(prov, dict):
                    prov["session_id"] = session_id
                    if trace_id:
                        prov["trace_id"] = trace_id
                    prov["tool_name"] = name
                    # GEOX identity anchor: physics_manifest_hash (NOT constitution_hash)
                    try:
                        from geox_core.physics.manifest import get_domain_law, get_physics_manifest_hash

                        prov["domain_law"] = get_domain_law()
                        prov["physics_manifest_hash"] = get_physics_manifest_hash()
                    except Exception:
                        prov["domain_law"] = "NATURAL_LAW"
                        prov["physics_manifest_hash"] = os.environ.get("GEOX_PHYSICS_MANIFEST_HASH", "sha256:missing")

                # Plumb audit_receipt
                audit = res.setdefault("audit_receipt", {})
                if isinstance(audit, dict):
                    audit["session_id"] = session_id
                    if trace_id:
                        audit["trace_id"] = trace_id
                    audit["actor_id"] = actor_id
                    audit["tool_name"] = name
            else:
                # Not enveloped yet. Add to res so _geox_wrap_envelope can process it.
                res["session_id"] = session_id
                res["actor_id"] = actor_id
                if trace_id:
                    res["trace_id"] = trace_id

        # Intercept domain records
        try:
            import asyncio

            from arifOS.supabase_adapter import record_artifact, record_evidence

            loop = asyncio.get_running_loop()
            if isinstance(res, dict):
                # Write evidence
                if "evidence_items" in res or "evidence" in res:
                    items = res.get("evidence_items") or res.get("evidence") or []
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                task = loop.create_task(
                                    record_evidence(
                                        session_ref=session_id or "geox_session",
                                        source_type=item.get("source_type", name),
                                        claim_state=item.get("claim_state", "EST"),
                                        title=item.get("title"),
                                        content=item.get("content"),
                                        confidence=item.get("confidence"),
                                        organ_code="GEOX",
                                    )
                                )
                                task.add_done_callback(lambda t: logger.debug(f"Evidence record task done: {t.exception() if t.exception() else 'ok'}"))
                # Write artifacts
                if "artifacts" in res:
                    artifacts = res.get("artifacts") or []
                    if isinstance(artifacts, list):
                        for a in artifacts:
                            if isinstance(a, dict):
                                task = loop.create_task(
                                    record_artifact(
                                        bucket=a.get("bucket", "geox_artifacts"),
                                        path=a.get("path", ""),
                                        filename=a.get("filename", "unknown"),
                                        artifact_type=a.get("type"),
                                        organ_code="GEOX",
                                        session_ref=session_id or "geox_session",
                                    )
                                )
                                task.add_done_callback(lambda t: logger.debug(f"Artifact record task done: {t.exception() if t.exception() else 'ok'}"))
        except Exception as e:
            logger.debug(f"GEOX Supabase adapter failed (fail-soft): {e}")

        # Emit Evidence Contract envelope (Appendix B)
        res = _geox_wrap_envelope(name, res)

        # Post-wrap double check for envelope root session_id/trace_id
        # Always propagate — never conditionally drop session lineage
        if isinstance(res, dict) and "epistemic_tag" in res:
            res["session_id"] = session_id
            if trace_id:
                res["trace_id"] = trace_id
            prov = res.setdefault("provenance", {})
            if isinstance(prov, dict):
                prov["session_id"] = session_id
                if trace_id:
                    prov["trace_id"] = trace_id
                prov["tool_name"] = name
                # Re-assert physics manifest identity even in post-wrap
                try:
                    from geox_core.physics.manifest import get_domain_law, get_physics_manifest_hash

                    prov["domain_law"] = get_domain_law()
                    prov["physics_manifest_hash"] = get_physics_manifest_hash()
                except Exception as exc:
                    logger.warning(f"Failed to inject physics manifest in post-wrap for {name}: {exc}")

        return res

    functools.update_wrapper(wrapper, func)

    # Dynamically build wrapper signature to include session_id, actor_id, and trace_id
    try:
        import inspect

        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        if not any(p.name == "session_id" for p in params):
            params.append(
                inspect.Parameter(
                    "session_id",
                    inspect.Parameter.KEYWORD_ONLY,
                    default=None,
                    annotation=str | None,
                )
            )
        if not any(p.name == "actor_id" for p in params):
            params.append(
                inspect.Parameter(
                    "actor_id",
                    inspect.Parameter.KEYWORD_ONLY,
                    default=None,
                    annotation=str | None,
                )
            )
        if not any(p.name == "trace_id" for p in params):
            params.append(
                inspect.Parameter(
                    "trace_id",
                    inspect.Parameter.KEYWORD_ONLY,
                    default=None,
                    annotation=str | None,
                )
            )
        wrapper.__signature__ = sig.replace(parameters=params)

        # Inject annotations so Pydantic's get_function_type_hints succeeds
        wrapper.__annotations__["session_id"] = str | None
        wrapper.__annotations__["actor_id"] = str | None
        wrapper.__annotations__["trace_id"] = str | None
    except Exception as sig_err:
        logger.debug(f"Failed to modify signature for {name}: {sig_err}")

    return wrapper


def register_tools_on_server(
    mcp: FastMCP,
    tools: list[tuple[str, Any]],
    annotations: dict[str, dict] | None = None,
    tasks: set[str] | None = None,
) -> None:
    """Register a list of (name, func) tuples on a FastMCP server with receipts + annotations + tasks."""
    annotations = annotations or {}
    tasks = tasks or set()

    for name, func in tools:
        kwargs: dict[str, Any] = {"name": name}

        # Inject [REQUIRES_888_HOLD: true] into description for high-risk tools
        risk = GEOX_RISK_MAP.get(name, RiskTier.C1_ADVISORY)
        if risk in (RiskTier.C2_EXECUTE, RiskTier.IRREVERSIBLE):
            doc = func.__doc__ or ""
            kwargs["description"] = f"{doc}\n\n[REQUIRES_888_HOLD: true]"

        if name in annotations:
            kwargs["annotations"] = annotations[name]

        # MCP Tasks extension: background execution for long-running async tools
        if name in tasks and asyncio.iscoroutinefunction(func):
            kwargs["task"] = True

        wrapped = _make_receipt_wrapper(func, name)
        mcp.tool(**kwargs)(wrapped)
