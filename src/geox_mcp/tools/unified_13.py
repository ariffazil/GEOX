"""
GEOX Witness Core — Canonical Tool Orchestrator
═══════════════════════════════════════════════════════════════════════════════
10 tools. Physics-9 foundation. No interpretation. No narrative.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastmcp import FastMCP

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP
from geox_core.compatibility.legacy_aliases import get_alias_metadata

# ── Canonical tool implementations ───────────────────────────────────────────
from geox_mcp.tools.data import geox_data_ingest_bundle
from geox_mcp.tools.qc import geox_data_qc_bundle
from geox_mcp.tools.petrophysics import (
    geox_subsurface_generate_candidates,
    geox_subsurface_verify_integrity,
)
from geox_mcp.tools.seismic_well_tie import (
    geox_seismic_well_tie_compute,
    geox_time_depth_anchor,
    geox_forward_model_synthetic,
)
from geox_mcp.tools.anomalous_contrast import geox_anomalous_contrast_detector
from geox_mcp.tools.dst import geox_dst_ingest_test
from geox_mcp.tools.registry import geox_system_registry_status

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
    ("geox_dst_ingest_test", geox_dst_ingest_test),
    ("geox_subsurface_generate_candidates", geox_subsurface_generate_candidates),
    ("geox_subsurface_verify_integrity", geox_subsurface_verify_integrity),
    ("geox_seismic_well_tie_compute", geox_seismic_well_tie_compute),
    ("geox_time_depth_anchor", geox_time_depth_anchor),
    ("geox_forward_model_synthetic", geox_forward_model_synthetic),
    ("geox_anomalous_contrast_detector", geox_anomalous_contrast_detector),
    ("geox_system_registry_status", geox_system_registry_status),
]

_TOOL_ANNOTATIONS: dict[str, dict] = {
    "geox_data_ingest_bundle": {"ui": {"resourceUri": "ui://well_desk"}},
    "geox_subsurface_generate_candidates": {"ui": {"resourceUri": "ui://earth_volume"}},
}


def register_unified_tools(mcp: FastMCP, profile: str = "full") -> None:
    """Registers the 10 Witness Core tools."""

    # ── Register canonical 10 ────────────────────────────────────────────────
    for name, func in _TOOL_REGISTRY:
        kwargs: dict[str, Any] = {"name": name}
        if name in _TOOL_ANNOTATIONS:
            kwargs["annotations"] = _TOOL_ANNOTATIONS[name]
        mcp.tool(**kwargs)(func)

    # ── Assert canonical count ───────────────────────────────────────────────
    assert len(CANONICAL_PUBLIC_TOOLS) == 10, (
        f"F0_CONSTITUTION_BREACH: Expected 10 sovereign tools, "
        f"got {len(CANONICAL_PUBLIC_TOOLS)}"
    )

    # ── Legacy alias bridge ──────────────────────────────────────────────────
    _show_legacy = os.getenv("GEOX_SHOW_LEGACY_ALIASES", "false").lower() in ("1", "true", "yes")
    if not _show_legacy:
        logger.info("Legacy aliases hidden (GEOX_SHOW_LEGACY_ALIASES=false).")

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
