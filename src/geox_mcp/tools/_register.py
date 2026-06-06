"""
GEOX Tool Registration Engine — Shared wrapper & annotation logic.
══════════════════════════════════════════════════════════════════════
Extracted from unified_13.py for domain-server composition via mcp.mount().

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
from typing import Any

from fastmcp import FastMCP

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
    "HIGH": 0.95,
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
    provenance = result.get("provenance") or {}
    source_attribution = [
        "GEOX:src/geox_mcp/server.py",
        f"GEOX:tool/{tool_name}",
    ]
    if provenance.get("tool_version"):
        source_attribution.append(f"GEOX:version/{provenance['tool_version']}")

    # Build the envelope. Per Appendix B, the original payload goes under "result".
    envelope = {
        "result": result,
        "epistemic_tag": tag,
        "evidence_quality": quality,
        "source_attribution": source_attribution,
        "uncertainty_band": [round(float(band[0]), 4), round(float(band[1]), 4)],
        "delta_S": round(float(delta_s), 4),
    }
    return envelope


def _make_receipt_wrapper(func: Any, name: str) -> Any:
    """Wrap a tool function to write Supabase domain receipts (fail-soft) AND emit Evidence Contract envelope."""

    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if inspect.iscoroutinefunction(func):
            res = await func(*args, **kwargs)
        else:
            res = func(*args, **kwargs)

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
                                loop.create_task(
                                    record_evidence(
                                        session_ref=kwargs.get("session_id", "geox_session"),
                                        source_type=item.get("source_type", name),
                                        claim_state=item.get("claim_state", "EST"),
                                        title=item.get("title"),
                                        content=item.get("content"),
                                        confidence=item.get("confidence"),
                                        organ_code="GEOX",
                                    )
                                )
                # Write artifacts
                if "artifacts" in res:
                    artifacts = res.get("artifacts") or []
                    if isinstance(artifacts, list):
                        for a in artifacts:
                            if isinstance(a, dict):
                                loop.create_task(
                                    record_artifact(
                                        bucket=a.get("bucket", "geox_artifacts"),
                                        path=a.get("path", ""),
                                        filename=a.get("filename", "unknown"),
                                        artifact_type=a.get("type"),
                                        organ_code="GEOX",
                                        session_ref=kwargs.get("session_id", "geox_session"),
                                    )
                                )
        except Exception as e:
            logger.debug(f"GEOX Supabase adapter failed (fail-soft): {e}")

        # Emit Evidence Contract envelope (Appendix B)
        res = _geox_wrap_envelope(name, res)
        return res

    functools.update_wrapper(wrapper, func)
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
