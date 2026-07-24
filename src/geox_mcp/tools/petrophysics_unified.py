"""
geox_petrophysics — Unified Petrophysics Computation (Phase 2)
══════════════════════════════════════════════════════════════
Absorbs: geox_lem_predict, geox_subsurface_generate_candidates,
         geox_subsurface_verify_integrity, STOIIP feed from geox_wealth_feed

Modes: generate, verify, lem_inference, stoip_feed

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

logger = logging.getLogger("geox.petrophysics")


async def geox_petrophysics(
    mode: Literal["generate", "verify", "lem_inference", "stoip_feed"] = "generate",
    # ── subsurface_generate_candidates params ──
    target_class: str | None = None,
    evidence_refs: list[str] | None = None,
    realizations: int = 3,
    gr_clean: float = 15,
    gr_shale: float = 150,
    vsh_method: str = "linear",
    matrix_density: float = 2.65,
    fluid_density: float = 1.0,
    sw_model: str = "archie",
    rw: float = 0.05,
    archie_a: float = 1,
    archie_m: float = 2,
    archie_n: float = 2,
    vsh_cutoff: float = 0.5,
    phi_cutoff: float = 0.1,
    sw_cutoff: float = 0.6,
    rt_cutoff: float = 2,
    zone_top_m: float | None = None,
    zone_base_m: float | None = None,
    basin_context: str | None = None,
    canon9_profile: str = "malay_basin",
    target_depth_m: float | None = None,
    cube_inline: dict[str, Any] | None = None,
    use_synth_cube: bool = True,
    lmr_inline: dict[str, Any] | None = None,
    # ── subsurface_verify_integrity params ──
    candidate_ref: str | None = None,
    domain: str | None = None,
    # ── lem_predict params ──
    well_id: str | None = None,
    curves: dict[str, Any] | None = None,
    depth_m: list[float] | None = None,
    depth_top_m: float | None = None,
    depth_bot_m: float | None = None,
    target_properties: list[str] | None = None,
    basin: str | None = None,
    rw_ohm_m: float | None = None,
    rho_matrix_g_cc: float | None = None,
    rho_fluid_g_cc: float | None = None,
    patch_size_m: float = 0.5,
    # ── STOIIP feed params ──
    cell_states: list[dict[str, Any]] | None = None,
    areal_extent_m2: float = 1e6,
    pay_zone_thickness_m: float = 50.0,
    formation_volume_factor: float = 1.3,
    water_saturation: float = 0.30,
    oil_density_kg_m3: float = 850.0,
    recovery_factor: float = 0.30,
) -> dict[str, Any]:
    """Unified petrophysics — Vsh, porosity, Sw, permeability, net pay, LEM inference.

    Modes:
      generate       - Subsurface candidates (REQUIRES target_class + evidence_refs)
      verify         - Integrity check (REQUIRES candidate_ref + domain — not multi-well list)
      lem_inference  - Curve-based physics-prior (REQUIRES well_id + curves + depth_m)
      stoip_feed     - STOIIP ranking feed for WEALTH organ

    CLAIM (runtime): there is no mode='qc' on this tool — use geox_well_qc.
    CLAIM (runtime): well_id is a single string, not a multi-well array.
    For exploratory Archie/Vsh/phi on curves without evidence store, use lem_inference.
    """
    if mode == "lem_inference":
        if not well_id or not curves or not depth_m:
            return {"status": "INVALID", "errors": ["well_id, curves, and depth_m required for lem_inference mode"]}
        from geox_mcp.tools.lem_predict import geox_lem_predict as _impl

        return await _impl(
            well_id=well_id,
            curves=curves,
            depth_m=depth_m,
            depth_top_m=depth_top_m,
            depth_bot_m=depth_bot_m,
            target_properties=target_properties,
            mode="physics_prior",
            basin=basin,
            rw_ohm_m=rw_ohm_m,
            rho_matrix_g_cc=rho_matrix_g_cc,
            rho_fluid_g_cc=rho_fluid_g_cc,
            patch_size_m=patch_size_m,
        )

    if mode == "verify":
        if not candidate_ref or not domain:
            return {"status": "INVALID", "errors": ["candidate_ref and domain required for verify mode"]}
        from geox_mcp.tools.petrophysics import geox_subsurface_verify_integrity as _impl

        return await _impl(candidate_ref=candidate_ref, domain=domain)

    if mode == "stoip_feed":
        from geox_mcp.tools.integration_wealth import WealthFeedRequest
        from geox_mcp.tools.integration_wealth import geox_wealth_feed as _impl

        req = WealthFeedRequest(
            cell_states=cell_states or [],
            areal_extent_m2=areal_extent_m2,
            pay_zone_thickness_m=pay_zone_thickness_m,
            formation_volume_factor=formation_volume_factor,
            water_saturation=water_saturation,
            oil_density_kg_m3=oil_density_kg_m3,
            recovery_factor=recovery_factor,
        )
        return (await _impl(req)).model_dump(mode="json")

    # Default: generate
    if not target_class or not evidence_refs:
        return {"status": "INVALID", "errors": ["target_class and evidence_refs required for generate mode"]}
    from geox_mcp.tools.petrophysics import geox_subsurface_generate_candidates as _impl

    return await _impl(
        target_class=target_class,
        evidence_refs=evidence_refs,
        realizations=realizations,
        gr_clean=gr_clean,
        gr_shale=gr_shale,
        vsh_method=vsh_method,
        matrix_density=matrix_density,
        fluid_density=fluid_density,
        sw_model=sw_model,
        rw=rw,
        archie_a=archie_a,
        archie_m=archie_m,
        archie_n=archie_n,
        vsh_cutoff=vsh_cutoff,
        phi_cutoff=phi_cutoff,
        sw_cutoff=sw_cutoff,
        rt_cutoff=rt_cutoff,
        zone_top_m=zone_top_m,
        zone_base_m=zone_base_m,
        basin_context=basin_context,
        canon9_profile=canon9_profile,
        target_depth_m=target_depth_m,
        cube_inline=cube_inline,
        use_synth_cube=use_synth_cube,
        lmr_inline=lmr_inline,
    )
