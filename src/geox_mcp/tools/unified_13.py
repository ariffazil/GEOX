"""
GEOX Witness Core — Canonical 16-Tool Orchestrator
═════════════════════════════════════════════════
16 tools. Physics-9 foundation. No interpretation. No narrative.

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
from geox_mcp.tools.ingestion import (
    geox_las_inspect,
    geox_seismic_inspect,
    geox_deviation_survey_inspect,
    geox_tops_inspect,
    geox_seismic_segy_inspect,
)
from geox_mcp.tools.qc import geox_data_qc_bundle
from geox_mcp.tools.dst import geox_dst_ingest_test
from geox_mcp.tools.petrophysics import (
    geox_subsurface_generate_candidates,
    geox_subsurface_verify_integrity,
)
from geox_mcp.tools.seismic_compute import geox_seismic_compute
from geox_mcp.tools.sequence import geox_sequence_interpret
from geox_mcp.tools.evidence_reason import geox_evidence_reason
from geox_mcp.tools.prospect import geox_prospect_evaluate
from geox_mcp.tools.map_context import geox_map_context_scene
from geox_mcp.tools.registry import geox_system_registry_status
from geox_mcp.tools.paleoscan_forge import (
    geox_coord_transform_tool,
    geox_blockspace_resolution_tool,
    geox_volume_get_frame_tool,
    geox_volume_set_frame_tool,
    geox_seismic_compute_attribute_tool,
    geox_fault_stick_ingest_tool,
    geox_attribute_registry_list_tool,
    geox_blend_volume_alpha_tool,
    geox_blend_volume_rgb_tool,
    geox_segy_export_tool,
)
from geox_mcp.tools.claims import (
    geox_claim_create,
    geox_claim_challenge,
    geox_evidence_attach,
    geox_claim_seal,
)

logger = logging.getLogger("geox.unified13")

# ═══════════════════════════════════════════════════════════════════════════════
# ALIAS DISPATCH
# ═══════════════════════════════════════════════════════════════════════════════


async def dispatch_alias(old_name: str, canonical_name: str, **kwargs: Any) -> dict:
    """Centralized dispatcher for aliases with deprecation metadata."""
    if canonical_name == "geox_data_ingest_bundle":
        stype = "well" if "well" in old_name else "seismic" if "seismic" in old_name else "earth3d"
        uri = kwargs.get("source_uri") or kwargs.get("volume_ref") or kwargs.get("bundle_uri")
        res = await geox_data_ingest_bundle(source_uri=uri, source_type=stype, well_id=kwargs.get("well_id"))
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
    ("geox_las_inspect", geox_las_inspect),
    ("geox_seismic_inspect", geox_seismic_inspect),
    ("geox_deviation_survey_inspect", geox_deviation_survey_inspect),
    ("geox_tops_inspect", geox_tops_inspect),
    ("geox_seismic_segy_inspect", geox_seismic_segy_inspect),
    ("geox_subsurface_generate_candidates", geox_subsurface_generate_candidates),
    ("geox_subsurface_verify_integrity", geox_subsurface_verify_integrity),
    ("geox_seismic_compute", geox_seismic_compute),
    ("geox_sequence_interpret", geox_sequence_interpret),
    ("geox_evidence_reason", geox_evidence_reason),
    ("geox_prospect_evaluate", geox_prospect_evaluate),
    ("geox_map_context_scene", geox_map_context_scene),
    ("geox_system_registry_status", geox_system_registry_status),
    # paleoscan_python v2.0.0 forge
    ("geox_coord_transform_tool", geox_coord_transform_tool),
    ("geox_blockspace_resolution_tool", geox_blockspace_resolution_tool),
    ("geox_volume_get_frame_tool", geox_volume_get_frame_tool),
    ("geox_volume_set_frame_tool", geox_volume_set_frame_tool),
    ("geox_seismic_compute_attribute_tool", geox_seismic_compute_attribute_tool),
    ("geox_fault_stick_ingest_tool", geox_fault_stick_ingest_tool),
    ("geox_attribute_registry_list_tool", geox_attribute_registry_list_tool),
    # paleoscan_python v2.0.0 forge — blending + export
    ("geox_blend_volume_alpha_tool", geox_blend_volume_alpha_tool),
    ("geox_blend_volume_rgb_tool", geox_blend_volume_rgb_tool),
    ("geox_segy_export_tool", geox_segy_export_tool),
    # H5: Claim Engine
    ("geox_claim_create", geox_claim_create),
    ("geox_claim_challenge", geox_claim_challenge),
    ("geox_evidence_attach", geox_evidence_attach),
    ("geox_claim_seal", geox_claim_seal),
]

_TOOL_ANNOTATIONS: dict[str, dict] = {
    # MCP 2025-11-25 spec annotations per tool
    "geox_data_ingest_bundle": {
        "ui": {"resourceUri": "ui://well_desk"},
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_data_qc_bundle": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_dst_ingest_test": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_las_inspect": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_seismic_inspect": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_deviation_survey_inspect": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_tops_inspect": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_seismic_segy_inspect": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_subsurface_generate_candidates": {
        "ui": {"resourceUri": "ui://earth_volume"},
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_subsurface_verify_integrity": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_seismic_compute": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_sequence_interpret": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_evidence_reason": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_prospect_evaluate": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_map_context_scene": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_system_registry_status": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    # paleoscan_python v2.0.0 forge
    "geox_coord_transform_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_blockspace_resolution_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_volume_get_frame_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_volume_set_frame_tool": {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
    "geox_seismic_compute_attribute_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_fault_stick_ingest_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_attribute_registry_list_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    # paleoscan_python v2.0.0 forge — blending + export
    "geox_blend_volume_alpha_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_blend_volume_rgb_tool": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_segy_export_tool": {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
    # H5: Claim Engine
    "geox_claim_create": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_claim_challenge": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_evidence_attach": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "geox_claim_seal": {
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


def register_unified_tools(mcp: FastMCP, profile: str = "full") -> None:
    """Registers the 13 Witness Core tools."""

    # ── Register canonical 13 ────────────────────────────────────────────────
    from geox_mcp.organ_governance import GEOX_RISK_MAP, RiskTier
    import sys

    if "/root/arifOS" not in sys.path:
        sys.path.append("/root/arifOS")

    for name, func in _TOOL_REGISTRY:
        kwargs: dict[str, Any] = {"name": name}

        # Inject [REQUIRES_888_HOLD: true] into description for high-risk tools
        risk = GEOX_RISK_MAP.get(name, RiskTier.C1_ADVISORY)
        if risk in (RiskTier.C2_EXECUTE, RiskTier.IRREVERSIBLE):
            doc = func.__doc__ or ""
            kwargs["description"] = f"{doc}\n\n[REQUIRES_888_HOLD: true]"

        if name in _TOOL_ANNOTATIONS:
            kwargs["annotations"] = _TOOL_ANNOTATIONS[name]

        # Wrap function to write Supabase domain receipts
        import inspect

        def make_wrapper(f=func, n=name):
            async def wrapper(*args, **kwargs):
                if inspect.iscoroutinefunction(f):
                    res = await f(*args, **kwargs)
                else:
                    res = f(*args, **kwargs)

                # Intercept domain records
                try:
                    from arifOS.supabase_adapter import record_evidence, record_artifact
                    import asyncio

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
                                                source_type=item.get("source_type", n),
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

            # Preserve signature
            import functools

            functools.update_wrapper(wrapper, f)
            return wrapper

        mcp.tool(**kwargs)(make_wrapper())

    # ── Assert canonical count ───────────────────────────────────────────────
    if len(CANONICAL_PUBLIC_TOOLS) != 30:
        raise ValueError(f"F0_CONSTITUTION_BREACH: Expected 30 sovereign tools, got {len(CANONICAL_PUBLIC_TOOLS)}")

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
