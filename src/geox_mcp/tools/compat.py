"""
GEOX Phase 2 — Backward Compatibility Wrappers
═══════════════════════════════════════════════
Thin wrappers mapping old tool names → new 15-tool surface.
These survive for 1 release cycle then are deleted.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox.compat")

# ── WELL domain ──────────────────────────────────────────────────────────────

async def geox_data_ingest_bundle(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_well_ingest(mode='auto') instead."""
    from geox_mcp.tools.well_ingest import geox_well_ingest
    kwargs.setdefault("mode", "auto")
    return await geox_well_ingest(*args, **kwargs)


async def geox_las_inspect(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_well_ingest(mode='las') instead."""
    from geox_mcp.tools.well_ingest import geox_well_ingest
    kwargs.setdefault("mode", "las")
    return await geox_well_ingest(*args, **kwargs)


async def geox_header_inspect(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_well_ingest(mode='header') instead."""
    from geox_mcp.tools.well_ingest import geox_well_ingest
    kwargs.setdefault("mode", "header")
    return await geox_well_ingest(*args, **kwargs)


async def geox_seismic_segy_inspect(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_well_ingest(mode='segy_inspect') instead."""
    from geox_mcp.tools.well_ingest import geox_well_ingest
    kwargs.setdefault("mode", "segy_inspect")
    return await geox_well_ingest(*args, **kwargs)


async def geox_dst_ingest_test(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_well_ingest(mode='dst') instead."""
    from geox_mcp.tools.well_ingest import geox_well_ingest
    kwargs.setdefault("mode", "dst")
    return await geox_well_ingest(*args, **kwargs)


async def geox_data_qc_bundle(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_well_qc() instead."""
    from geox_mcp.tools.well_qc import geox_well_qc
    return await geox_well_qc(*args, **kwargs)


async def geox_lem_predict(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_petrophysics(mode='lem_inference') instead."""
    from geox_mcp.tools.petrophysics_unified import geox_petrophysics
    kwargs.setdefault("mode", "lem_inference")
    return await geox_petrophysics(*args, **kwargs)


async def geox_subsurface_generate_candidates(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_petrophysics(mode='generate') instead."""
    from geox_mcp.tools.petrophysics_unified import geox_petrophysics
    kwargs.setdefault("mode", "generate")
    return await geox_petrophysics(*args, **kwargs)


async def geox_subsurface_verify_integrity(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_petrophysics(mode='verify') instead."""
    from geox_mcp.tools.petrophysics_unified import geox_petrophysics
    kwargs.setdefault("mode", "verify")
    return await geox_petrophysics(*args, **kwargs)


async def geox_sequence_interpret(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_sequence() instead."""
    from geox_mcp.tools.sequence import geox_sequence
    return await geox_sequence(*args, **kwargs)


# ── SEISMIC domain ───────────────────────────────────────────────────────────

async def geox_segy_export_tool(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_seismic_ingest(mode='export_segy') instead."""
    from geox_mcp.tools.seismic_ingest import geox_seismic_ingest
    kwargs.setdefault("mode", "export_segy")
    return await geox_seismic_ingest(*args, **kwargs)


async def geox_seismic_compute(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_seismic_compute with explicit mode instead.
    This wrapper preserves the old default-mode behavior."""
    from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute as _new
    return await _new(*args, **kwargs)


async def geox_seismic_compute_attribute_tool(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_seismic_compute(mode='attribute') instead."""
    from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute
    kwargs.setdefault("mode", "attribute")
    return await geox_seismic_compute(*args, **kwargs)


async def geox_seismic_inversion(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_seismic_compute(mode='inversion') instead."""
    from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute
    kwargs.setdefault("mode", "inversion")
    return await geox_seismic_compute(*args, **kwargs)


async def geox_horizon_contrast_surface(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_seismic_interpret(mode='horizon_contrast') instead."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret
    kwargs.setdefault("mode", "horizon_contrast")
    return await geox_seismic_interpret(*args, **kwargs)


async def geox_fault_stick_ingest_tool(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_seismic_interpret(mode='fault_sticks') instead."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret
    kwargs.setdefault("mode", "fault_sticks")
    return await geox_seismic_interpret(*args, **kwargs)


async def geox_volume_frame_tool(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_seismic_interpret(mode='volume_frame') instead."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret
    kwargs.setdefault("mode", "volume_frame")
    return await geox_seismic_interpret(*args, **kwargs)


async def geox_blend_volume_tool(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_seismic_interpret(mode='blend') instead."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret
    kwargs.setdefault("mode", "blend")
    return await geox_seismic_interpret(*args, **kwargs)


async def geox_vision_minimax_inference(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_vision(mode='infer_minimax') instead."""
    from geox_mcp.tools.vision_unified import geox_vision
    kwargs.setdefault("mode", "infer_minimax")
    return await geox_vision(*args, **kwargs)


async def geox_vision_audit(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_vision(mode='audit') instead."""
    from geox_mcp.tools.vision_unified import geox_vision
    kwargs.setdefault("mode", "audit")
    return await geox_vision(*args, **kwargs)


async def geox_vision_calibrate(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_vision(mode='calibrate') instead."""
    from geox_mcp.tools.vision_unified import geox_vision
    kwargs.setdefault("mode", "calibrate")
    return await geox_vision(*args, **kwargs)


async def geox_vision_perceptual_inventory(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_vision(mode='perceptual') instead."""
    from geox_mcp.tools.vision_unified import geox_vision
    kwargs.setdefault("mode", "perceptual")
    return await geox_vision(*args, **kwargs)


# ── MODEL domain ─────────────────────────────────────────────────────────────

async def geox_joint_inversion(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_subsurface_model(mode='joint_inversion') instead."""
    from geox_mcp.tools.subsurface_model import geox_subsurface_model
    kwargs.setdefault("mode", "joint_inversion")
    return await geox_subsurface_model(*args, **kwargs)


async def geox_gravity_magnetic_forward(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_subsurface_model(mode='gravity_magnetic') instead."""
    from geox_mcp.tools.subsurface_model import geox_subsurface_model
    kwargs.setdefault("mode", "gravity_magnetic")
    return await geox_subsurface_model(*args, **kwargs)


async def geox_mt_forward(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_subsurface_model(mode='mt_forward') instead."""
    from geox_mcp.tools.subsurface_model import geox_subsurface_model
    kwargs.setdefault("mode", "mt_forward")
    return await geox_subsurface_model(*args, **kwargs)


async def geox_coord_transform_tool(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_geomechanics(mode='coord_transform') instead."""
    from geox_mcp.tools.geomechanics_unified import geox_geomechanics
    kwargs.setdefault("mode", "coord_transform")
    return await geox_geomechanics(*args, **kwargs)


async def geox_blockspace_resolution_tool(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_geomechanics(mode='blockspace') instead."""
    from geox_mcp.tools.geomechanics_unified import geox_geomechanics
    kwargs.setdefault("mode", "blockspace")
    return await geox_geomechanics(*args, **kwargs)


# ── BASIN domain ─────────────────────────────────────────────────────────────

async def geox_basin_resolve(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_basin(mode='resolve') instead."""
    from geox_mcp.tools.basin_unified import geox_basin
    kwargs.setdefault("mode", "resolve")
    return await geox_basin(*args, **kwargs)


async def geox_basin_profile(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_basin(mode='profile') instead."""
    from geox_mcp.tools.basin_unified import geox_basin
    kwargs.setdefault("mode", "profile")
    return await geox_basin(*args, **kwargs)


async def geox_query_intake(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_basin(mode='intake') instead."""
    from geox_mcp.tools.basin_unified import geox_basin
    kwargs.setdefault("mode", "intake")
    return await geox_basin(*args, **kwargs)


async def geox_query_macrostrat(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_basin(mode='macrostrat') instead."""
    from geox_mcp.tools.basin_unified import geox_basin
    kwargs.setdefault("mode", "macrostrat")
    return await geox_basin(*args, **kwargs)


async def geox_deep_time_state(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_basin(mode='deep_time') instead."""
    from geox_mcp.tools.basin_unified import geox_basin
    kwargs.setdefault("mode", "deep_time")
    return await geox_basin(*args, **kwargs)


async def geox_emag2_ingest(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_basin(mode='emag2') instead."""
    from geox_mcp.tools.basin_unified import geox_basin
    kwargs.setdefault("mode", "emag2")
    return await geox_basin(*args, **kwargs)


async def geox_icgem_models(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_basin(mode='icgem') instead."""
    from geox_mcp.tools.basin_unified import geox_basin
    kwargs.setdefault("mode", "icgem")
    return await geox_basin(*args, **kwargs)


async def geox_map_context_scene(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_basin(mode='scene') instead."""
    from geox_mcp.tools.basin_unified import geox_basin
    kwargs.setdefault("mode", "scene")
    return await geox_basin(*args, **kwargs)


# ── GOVERNANCE domain ────────────────────────────────────────────────────────

async def geox_claim_create(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_claim(mode='create') instead."""
    from geox_mcp.tools.claim_unified import geox_claim
    kwargs.setdefault("mode", "create")
    return await geox_claim(*args, **kwargs)


async def geox_claim_validate(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_claim(mode='validate') instead."""
    from geox_mcp.tools.claim_unified import geox_claim
    kwargs.setdefault("mode", "validate")
    return await geox_claim(*args, **kwargs)


async def geox_claim_challenge(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_claim(mode='challenge') instead."""
    from geox_mcp.tools.claim_unified import geox_claim
    kwargs.setdefault("mode", "challenge")
    return await geox_claim(*args, **kwargs)


async def geox_claim_seal(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_claim(mode='seal') instead."""
    from geox_mcp.tools.claim_unified import geox_claim
    kwargs.setdefault("mode", "seal")
    return await geox_claim(*args, **kwargs)


async def geox_evidence_attach(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_claim(mode='attach_evidence') instead."""
    from geox_mcp.tools.claim_unified import geox_claim
    kwargs.setdefault("mode", "attach_evidence")
    return await geox_claim(*args, **kwargs)


async def geox_evidence_discover(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_evidence(mode='discover') instead."""
    from geox_mcp.tools.evidence_unified import geox_evidence
    kwargs.setdefault("mode", "discover")
    return await geox_evidence(*args, **kwargs)


async def geox_evidence_reason(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_evidence(mode='reason') instead."""
    from geox_mcp.tools.evidence_unified import geox_evidence
    kwargs.setdefault("mode", "reason")
    return await geox_evidence(*args, **kwargs)


async def geox_literature_ingest(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_evidence(mode='ingest_literature') instead."""
    from geox_mcp.tools.evidence_unified import geox_evidence
    kwargs.setdefault("mode", "ingest_literature")
    return await geox_evidence(*args, **kwargs)


async def geox_prospect_evaluate(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_prospect() instead."""
    from geox_mcp.tools.prospect_unified import geox_prospect
    return await geox_prospect(*args, **kwargs)


# ── DOCTRINE domain ──────────────────────────────────────────────────────────

async def geox_doctrine_assumption_register(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_doctrine(mode='assumption_register') instead."""
    from geox_mcp.tools.doctrine_unified import geox_doctrine
    kwargs.setdefault("mode", "assumption_register")
    return await geox_doctrine(*args, **kwargs)


async def geox_doctrine_anti_beautiful_one(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_doctrine(mode='anti_beautiful_one') instead."""
    from geox_mcp.tools.doctrine_unified import geox_doctrine
    kwargs.setdefault("mode", "anti_beautiful_one")
    return await geox_doctrine(*args, **kwargs)


async def geox_doctrine_godel_review(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_doctrine(mode='godel_review') instead."""
    from geox_mcp.tools.doctrine_unified import geox_doctrine
    kwargs.setdefault("mode", "godel_review")
    return await geox_doctrine(*args, **kwargs)


async def geox_abstraction_guard(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_doctrine(mode='abstraction_guard') instead."""
    from geox_mcp.tools.doctrine_unified import geox_doctrine
    kwargs.setdefault("mode", "abstraction_guard")
    return await geox_doctrine(*args, **kwargs)


async def geox_biostrat_constraint(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_doctrine(mode='biostrat') instead."""
    from geox_mcp.tools.doctrine_unified import geox_doctrine
    kwargs.setdefault("mode", "biostrat")
    return await geox_doctrine(*args, **kwargs)


async def geox_prithvi_eo_inference(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Use geox_doctrine(mode='prithvi_eo') instead."""
    from geox_mcp.tools.doctrine_unified import geox_doctrine
    kwargs.setdefault("mode", "prithvi_eo")
    return await geox_doctrine(*args, **kwargs)


async def geox_attribute_registry_list_tool(*args: Any, **kwargs: Any) -> dict:
    """[DEPRECATED] Internal registry query — use geox_system_registry_status or arif_ops_measure."""
    return {
        "status": "DEPRECATED",
        "message": "geox_attribute_registry_list_tool is now internal. Use arif_ops_measure for system queries.",
    }
