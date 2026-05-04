"""
GEOX Sovereign 13 — Canonical Tool Orchestrator
═══════════════════════════════════════════════════════════════════════════════
Thin registration layer. All tool implementations live in
contracts.tools.canonical.* modules.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastmcp import FastMCP

from contracts.canonical_registry import CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP
from compatibility.legacy_aliases import get_alias_metadata

# ── Canonical tool implementations ───────────────────────────────────────────
from contracts.tools.canonical.ingest import geox_data_ingest_bundle
from contracts.tools.canonical.qc import geox_data_qc_bundle
from contracts.tools.canonical.subsurface import (
    geox_subsurface_generate_candidates,
    geox_subsurface_verify_integrity,
)
from contracts.tools.canonical.seismic import geox_seismic_analyze_volume
from contracts.tools.canonical.section import geox_section_interpret_correlation
from contracts.tools.canonical.map_context import geox_map_context_scene
from contracts.tools.canonical.time4d import geox_time4d_analyze_system
from contracts.tools.canonical.prospect import (
    geox_prospect_evaluate,
    geox_prospect_judge_preview,
    geox_prospect_judge_seal,
    geox_prospect_judge_verdict,
)
from contracts.tools.canonical.evidence import geox_evidence_summarize_cross
from contracts.tools.canonical.registry import (
    geox_system_registry_status,
    geox_history_audit,
)
from contracts.tools.canonical.dst import geox_dst_ingest_test

logger = logging.getLogger("geox.unified13")

# ═══════════════════════════════════════════════════════════════════════════════
# ALIAS DISPATCH
# ═══════════════════════════════════════════════════════════════════════════════

async def dispatch_alias(old_name: str, canonical_name: str, **kwargs: Any) -> dict:
    """Centralized dispatcher for aliases with deprecation metadata."""
    if canonical_name == "geox_data_ingest_bundle":
        stype = "well" if "well" in old_name else "seismic" if "seismic" in old_name else "earth3d"
        uri = kwargs.get("source_uri") or kwargs.get("volume_ref") or kwargs.get("bundle_uri")
        res = await geox_data_ingest_bundle(
            source_uri=uri, source_type=stype, well_id=kwargs.get("well_id")
        )
    elif canonical_name == "geox_subsurface_generate_candidates":
        target = "petrophysics" if "petrophysics" in old_name or "petro" in old_name else "structure"
        refs = [kwargs.get("well_id") or kwargs.get("volume_ref") or "N/A"]
        res = await geox_subsurface_generate_candidates(target_class=target, evidence_refs=refs)
    elif canonical_name == "geox_system_registry_status":
        res = await geox_system_registry_status()
    elif canonical_name == "geox_prospect_evaluate":
        res = await geox_prospect_evaluate(kwargs.get("prospect_ref", "N/A"))
    else:
        res = {"status": "SUCCESS", "message": f"Aliased from {old_name} to {canonical_name}"}

    meta = get_alias_metadata(old_name, canonical_name)
    res.update(meta)
    return res


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════════

_TOOL_REGISTRY: list[tuple[str, Any]] = [
    ("geox_data_ingest_bundle", geox_data_ingest_bundle),
    ("geox_data_qc_bundle", geox_data_qc_bundle),
    ("geox_subsurface_generate_candidates", geox_subsurface_generate_candidates),
    ("geox_subsurface_verify_integrity", geox_subsurface_verify_integrity),
    ("geox_seismic_analyze_volume", geox_seismic_analyze_volume),
    ("geox_section_interpret_correlation", geox_section_interpret_correlation),
    ("geox_map_context_scene", geox_map_context_scene),
    ("geox_time4d_analyze_system", geox_time4d_analyze_system),
    ("geox_prospect_evaluate", geox_prospect_evaluate),
    ("geox_prospect_judge_preview", geox_prospect_judge_preview),
    ("geox_prospect_judge_seal", geox_prospect_judge_seal),
    ("geox_prospect_judge_verdict", geox_prospect_judge_verdict),
    ("geox_evidence_summarize_cross", geox_evidence_summarize_cross),
    ("geox_system_registry_status", geox_system_registry_status),
    ("geox_history_audit", geox_history_audit),
    ("geox_dst_ingest_test", geox_dst_ingest_test),
]


def register_unified_tools(mcp: FastMCP, profile: str = "full") -> None:
    """Registers the 13 Canonical Sovereign tools and the Legacy Alias Bridge."""

    # ── Register canonical 13 ────────────────────────────────────────────────
    for name, func in _TOOL_REGISTRY:
        mcp.tool(name=name)(func)

    # ── Assert canonical count ───────────────────────────────────────────────
    # Count is 14: 13 original sovereign tools + history_audit
    assert len(CANONICAL_PUBLIC_TOOLS) == 14, (
        f"F0_CONSTITUTION_BREACH: Expected 14 sovereign tools, "
        f"got {len(CANONICAL_PUBLIC_TOOLS)}"
    )

    # ── Legacy alias bridge ──────────────────────────────────────────────────
    _show_legacy = os.getenv("GEOX_SHOW_LEGACY_ALIASES", "false").lower() in ("1", "true", "yes")
    if not _show_legacy:
        logger.info("Legacy aliases hidden (GEOX_SHOW_LEGACY_ALIASES=false). Expose only canonical 13 + preview/seal.")

    for old_name, new_name in LEGACY_ALIAS_MAP.items():
        if "." in old_name:
            continue

        def make_alias(o: str = old_name, n: str = new_name) -> Any:
            async def alias_func(
                well_id: str | None = None,
                source_uri: str | None = None,
                volume_ref: str | None = None,
                prospect_ref: str | None = None,
            ) -> dict:
                return await dispatch_alias(
                    o,
                    n,
                    well_id=well_id,
                    source_uri=source_uri,
                    volume_ref=volume_ref,
                    prospect_ref=prospect_ref,
                )

            alias_func.__name__ = o
            alias_func.__doc__ = f"Legacy Alias for {n} (Deprecated)."
            return alias_func

        if _show_legacy:
            mcp.tool(
                name=old_name,
                description=f"[DEPRECATED] Alias for {new_name}. Update calling contract by 2026-06-01.",
                annotations={"deprecated": True, "canonical_name": new_name},
            )(make_alias())

    # ── Well correlation tools (non-canonical, kept for compatibility) ───────
    from contracts.tools.well_correlation import register_well_correlation_tools

    register_well_correlation_tools(mcp)
