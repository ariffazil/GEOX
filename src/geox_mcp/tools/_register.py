"""
GEOX Tool Registration Engine — Shared wrapper & annotation logic.
════════════════════════════════════════════════════════════════
Extracted from unified_13.py for domain-server composition via mcp.mount().

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import functools
import inspect
import logging
from typing import Any

from fastmcp import FastMCP

from geox_mcp.organ_governance import GEOX_RISK_MAP, RiskTier

logger = logging.getLogger("geox.register")


def _make_receipt_wrapper(func: Any, name: str) -> Any:
    """Wrap a tool function to write Supabase domain receipts (fail-soft)."""

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

        return res

    functools.update_wrapper(wrapper, func)
    return wrapper


def register_tools_on_server(
    mcp: FastMCP,
    tools: list[tuple[str, Any]],
    annotations: dict[str, dict] | None = None,
) -> None:
    """Register a list of (name, func) tuples on a FastMCP server with receipts + annotations."""
    annotations = annotations or {}

    for name, func in tools:
        kwargs: dict[str, Any] = {"name": name}

        # Inject [REQUIRES_888_HOLD: true] into description for high-risk tools
        risk = GEOX_RISK_MAP.get(name, RiskTier.C1_ADVISORY)
        if risk in (RiskTier.C2_EXECUTE, RiskTier.IRREVERSIBLE):
            doc = func.__doc__ or ""
            kwargs["description"] = f"{doc}\n\n[REQUIRES_888_HOLD: true]"

        if name in annotations:
            kwargs["annotations"] = annotations[name]

        wrapped = _make_receipt_wrapper(func, name)
        mcp.tool(**kwargs)(wrapped)
