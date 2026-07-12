# WARNING: Auto-generated from server.py to reduce monolith size.
# DITEMPA BUKAN DIBERI

from typing import Any, Literal
import sys
import os
import json
import inspect
import logging
from datetime import datetime, UTC
import numpy as np
from pydantic import BaseModel

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, SURFACE_TOOLS, INTERNAL_TOOLS, get_tool_domain
from geox_mcp.server import (
    _geox_annotations,
    _safe_forward,
)

logger = logging.getLogger("geox.mcp.tools_wiring")


def _parse_str_arguments(arguments: Any) -> Any:
    """F1 AMANAH: parse stringified JSON arguments into dicts.

    Some MCP transports serialize arguments as JSON strings instead of dicts.
    Pydantic rejects strings at the function signature level. This helper
    runs BEFORE Pydantic validation, converting str → dict.
    """
    if arguments is None:
        return None
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
            if isinstance(parsed, dict):
                logger.debug("ARG_PARSE: converted stringified JSON to dict")
                return parsed
            else:
                logger.warning(f"ARG_PARSE: JSON parsed but not a dict: {type(parsed)}")
                return arguments
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"ARG_PARSE: failed to parse string as JSON: {e}")
            return arguments
    return arguments


def _auto_construct_request(impl, args: dict) -> Any:
    """Auto-construct Pydantic request model from flat dict args.
    17 tools in earth_surface.py/earth_surface_2.py define functions with
    `request: SomePydanticModel` but the MCP wrapper passed flat kwargs via
    `**dict(arguments)`. This helper inspects the impl signature: if the
    first parameter is a BaseModel subclass, it constructs the model from
    flat args. Otherwise returns the raw dict for **kwargs impls.
    """
    if not args:
        return None
    try:
        sig = inspect.signature(impl)
        for _name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                try:
                    if issubclass(param.annotation, BaseModel):
                        return param.annotation(**args)
                except TypeError:
                    pass
    except Exception:
        pass
    return args  # fallback: return raw dict for **kwargs impls


async def _auto_call(impl, arguments: dict | None) -> dict[str, Any]:
    """Universal impl caller — auto-constructs Pydantic models + serializes response.

    Handles both model-based impls (`request: SomeModel`) and flat-kwargs impls.
    Serializes Pydantic response models to dict for FastMCP compatibility.
    """
    args = dict(arguments or {})
    req = _auto_construct_request(impl, args)
    if isinstance(req, BaseModel):
        result = await impl(req)
    else:
        result = await impl(**req)
    return result.model_dump() if isinstance(result, BaseModel) else result


def register_tools_on(mcp):
    # ═══════════════════════════════════════════════════════════════════════════════
    # PHASE 2 UNIFIED TOOL WIRING — forge 2026-06-23
    # Wires the 14 mode-consolidated canonical tools that exist as _unified.py
    # implementations but were never registered with FastMCP. Each wrapper
    # delegates to the unified async function via a single 'arguments' dict
    # (FastMCP rejects **kwargs). Clients call as:
    #   {"name": "geox_basin", "arguments": {"arguments": {"mode": "...", "basin_name": "..."}}}
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(name="geox_well_ingest", annotations=_geox_annotations("geox_well_ingest"))
    async def _well_ingest(
        mode: str = "auto",
        source_uri: str | None = None,
        source_type: str = "auto",
        well_id: str | None = None,
        standardize_curves: bool = True,
        normalize_units: bool = True,
        content_base64: str | None = None,
        filename: str | None = None,
        target_dir: str = "/data/geox_las",
        overwrite: bool = False,
        batch_mode: bool = False,
        artifact_refs: list[str] | None = None,
        qc_strict: bool = True,
        source_crs: str = "unknown",
        depth_datum: str | None = None,
        file_format: str | None = None,
        las_metadata: dict[str, Any] | None = None,
        las_curve_info: list[dict[str, Any]] | None = None,
        segy_metadata: dict[str, Any] | None = None,
        seismic_metadata: dict[str, Any] | None = None,
        deviation_metadata: dict[str, Any] | None = None,
        tops_metadata: dict[str, Any] | None = None,
        field: str | None = None,
        reservoir_name: str | None = None,
        test_name: str | None = None,
        test_duration_hr: float | None = None,
        main_flow_hr: float | None = None,
        main_buildup_hr: float | None = None,
        choke_size_64ths: float | None = None,
        bhp_psi: float | None = None,
        bht_c: float | None = None,
        whp_psi: float | None = None,
        wht_c: float | None = None,
        gas_rate_mmscfd: float | None = None,
        condensate_rate_stbd: float | None = None,
        water_rate_stbd: float | None = None,
        co2_mol_pct: float | None = None,
        h2s_ppm: float | None = None,
        bsw_pct: float | None = None,
        chloride_ppm: float | None = None,
        wgr_stb_per_mmscf: float | None = None,
        permeability_md_min: float | None = None,
        permeability_md_max: float | None = None,
        skin_min: float | None = None,
        skin_max: float | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Load well log data (LAS, SEG-Y, DST, deviation, tops)."""
        from geox_mcp.tools.well_ingest import geox_well_ingest as _impl

        try:
            args = _safe_forward(
                _impl,
                {
                    "mode": mode, "source_uri": source_uri, "source_type": source_type,
                    "well_id": well_id, "standardize_curves": standardize_curves,
                    "normalize_units": normalize_units, "content_base64": content_base64,
                    "filename": filename, "target_dir": target_dir, "overwrite": overwrite,
                    "batch_mode": batch_mode, "artifact_refs": artifact_refs,
                    "qc_strict": qc_strict, "source_crs": source_crs,
                    "depth_datum": depth_datum, "file_format": file_format,
                    "las_metadata": las_metadata, "las_curve_info": las_curve_info,
                    "segy_metadata": segy_metadata, "seismic_metadata": seismic_metadata,
                    "deviation_metadata": deviation_metadata, "tops_metadata": tops_metadata,
                    "field": field, "reservoir_name": reservoir_name,
                    "test_name": test_name, "test_duration_hr": test_duration_hr,
                    "main_flow_hr": main_flow_hr, "main_buildup_hr": main_buildup_hr,
                    "choke_size_64ths": choke_size_64ths, "bhp_psi": bhp_psi,
                    "bht_c": bht_c, "whp_psi": whp_psi, "wht_c": wht_c,
                    "gas_rate_mmscfd": gas_rate_mmscfd,
                    "condensate_rate_stbd": condensate_rate_stbd,
                    "water_rate_stbd": water_rate_stbd, "co2_mol_pct": co2_mol_pct,
                    "h2s_ppm": h2s_ppm, "bsw_pct": bsw_pct,
                    "chloride_ppm": chloride_ppm, "wgr_stb_per_mmscf": wgr_stb_per_mmscf,
                    "permeability_md_min": permeability_md_min,
                    "permeability_md_max": permeability_md_max,
                    "skin_min": skin_min, "skin_max": skin_max,
                },
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
            result = await _impl(**args)
            return {
                **(result if isinstance(result, dict) else {"data": result}),
                "_memory": "LIVE_PROBE",
                "_epistemic": {
                    "evidence_layer": "OBS",
                    "confidence": 0.85,
                    "source": "geox_well_ingest",
                    "reversible": True,
                    "authority_claim": "EVIDENCE",
                },
            }
        except Exception as e:
            from geox_mcp.federation_safety import classify_error
            return classify_error(e, source_tool="geox_well_ingest", source_organ="geox")

    @mcp.tool(name="geox_well_qc", annotations=_geox_annotations("geox_well_qc"))
    async def _well_qc(
        artifact_ref: str = "",
        artifact_type: str = "",
        qc_mode: str = "full",
        samples: list[dict[str, Any]] | None = None,
        existing_features: list[str] | None = None,
        candidate_feature: str | None = None,
        target_key: str = "value",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """QC: depth, curves, completeness, FJIS."""
        from geox_mcp.tools.well_qc import geox_well_qc as _impl

        args = _safe_forward(
            _impl,
            {
                "artifact_ref": artifact_ref, "artifact_type": artifact_type,
                "qc_mode": qc_mode, "samples": samples,
                "existing_features": existing_features,
                "candidate_feature": candidate_feature, "target_key": target_key,
            },
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_well_desurvey", annotations=_geox_annotations("geox_well_desurvey"))
    async def _well_desurvey(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """3D wellbore geometry from deviation survey.

        Phase 2.1 (2026-06-28): evidence-only. Computes TVD/X/Y/TVDSS trajectory
        using industry-standard minimum curvature method (wellpathpy). Returns
        geox.desurvey.v1 envelope with claim-tagged uncertainty.
        See forge_work/GEOX-ADAPT-001-r1.md for spec + 12 golden tests.
        """
        from geox_mcp.tools.well_desurvey import geox_well_desurvey as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    @mcp.tool(name="geox_petrophysics", annotations=_geox_annotations("geox_petrophysics"))
    async def _petrophysics(
        mode: str = "generate",
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
        candidate_ref: str | None = None,
        domain: str | None = None,
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
        cell_states: list[dict[str, Any]] | None = None,
        areal_extent_m2: float = 1e6,
        pay_zone_thickness_m: float = 50.0,
        formation_volume_factor: float = 1.3,
        water_saturation: float = 0.30,
        oil_density_kg_m3: float = 850.0,
        recovery_factor: float = 0.30,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Vsh, porosity, Sw, perm, net pay, LEM."""
        from geox_mcp.tools.petrophysics_unified import geox_petrophysics as _impl

        try:
            args = _safe_forward(
                _impl,
                {
                    "mode": mode, "target_class": target_class,
                    "evidence_refs": evidence_refs, "realizations": realizations,
                    "gr_clean": gr_clean, "gr_shale": gr_shale,
                    "vsh_method": vsh_method, "matrix_density": matrix_density,
                    "fluid_density": fluid_density, "sw_model": sw_model,
                    "rw": rw, "archie_a": archie_a, "archie_m": archie_m,
                    "archie_n": archie_n, "vsh_cutoff": vsh_cutoff,
                    "phi_cutoff": phi_cutoff, "sw_cutoff": sw_cutoff,
                    "rt_cutoff": rt_cutoff, "zone_top_m": zone_top_m,
                    "zone_base_m": zone_base_m, "basin_context": basin_context,
                    "canon9_profile": canon9_profile, "target_depth_m": target_depth_m,
                    "cube_inline": cube_inline, "use_synth_cube": use_synth_cube,
                    "lmr_inline": lmr_inline, "candidate_ref": candidate_ref,
                    "domain": domain, "well_id": well_id, "curves": curves,
                    "depth_m": depth_m, "depth_top_m": depth_top_m,
                    "depth_bot_m": depth_bot_m, "target_properties": target_properties,
                    "basin": basin, "rw_ohm_m": rw_ohm_m,
                    "rho_matrix_g_cc": rho_matrix_g_cc,
                    "rho_fluid_g_cc": rho_fluid_g_cc, "patch_size_m": patch_size_m,
                    "cell_states": cell_states, "areal_extent_m2": areal_extent_m2,
                    "pay_zone_thickness_m": pay_zone_thickness_m,
                    "formation_volume_factor": formation_volume_factor,
                    "water_saturation": water_saturation,
                    "oil_density_kg_m3": oil_density_kg_m3,
                    "recovery_factor": recovery_factor,
                },
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
            result = await _impl(**args)
            return {
                **(result if isinstance(result, dict) else {"data": result}),
                "_memory": "LIVE_PROBE",
                "_epistemic": {
                    "evidence_layer": "DER",
                    "confidence": 0.80,
                    "source": "geox_petrophysics",
                    "reversible": True,
                    "authority_claim": "EVIDENCE",
                },
            }
        except Exception as e:
            from geox_mcp.federation_safety import classify_error
            return classify_error(e, source_tool="geox_petrophysics", source_organ="geox")

    @mcp.tool(name="geox_sequence", annotations=_geox_annotations("geox_sequence"))
    async def _sequence(
        workflow: str = "single_well",
        source: str | None = None,
        zone_top: float | None = None,
        zone_base: float | None = None,
        depo_env_code: str = "FLUVIAL",
        bin_size_m: float = 10.0,
        min_package_thickness_m: float = 20.0,
        p50_shift_api: float = 15.0,
        gr_cutoff_api: float = 75.0,
        detail_level: str = "full",
        project_yaml: str | None = None,
        output_dir: str | None = None,
        section_ref: str | None = None,
        well_refs: list[str] | None = None,
        mode: str = "correlation",
        well_las_paths: list[str] | None = None,
        tops: dict[str, Any] | None = None,
        zone_definitions: dict[str, Any] | None = None,
        strat_standard: dict[str, Any] | None = None,
        paleoenvironment_input: list[dict[str, Any]] | None = None,
        checkshot_ref: str | None = None,
        wavelet_mode: str = "ricker",
        wavelet_freq_hz: list[float] | None = None,
        phase_degrees: float = 0.0,
        polarity: str = "SEG_NORMAL",
        synthetics_output: bool = False,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Sequence stratigraphy, correlation. Pattern A wrapper — see sequence_unified.geox_sequence."""
        from geox_mcp.tools.sequence_unified import geox_sequence as _impl

        args = _safe_forward(
            _impl,
            {
                "workflow": workflow,
                "source": source,
                "zone_top": zone_top,
                "zone_base": zone_base,
                "depo_env_code": depo_env_code,
                "bin_size_m": bin_size_m,
                "min_package_thickness_m": min_package_thickness_m,
                "p50_shift_api": p50_shift_api,
                "gr_cutoff_api": gr_cutoff_api,
                "detail_level": detail_level,
                "project_yaml": project_yaml,
                "output_dir": output_dir,
                "section_ref": section_ref,
                "well_refs": well_refs,
                "mode": mode,
                "well_las_paths": well_las_paths,
                "tops": tops,
                "zone_definitions": zone_definitions,
                "strat_standard": strat_standard,
                "paleoenvironment_input": paleoenvironment_input,
                "checkshot_ref": checkshot_ref,
                "wavelet_mode": wavelet_mode,
                "wavelet_freq_hz": wavelet_freq_hz,
                "phase_degrees": phase_degrees,
                "polarity": polarity,
                "synthetics_output": synthetics_output,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    # ── SURFACE DISCOVERY — Federation Standard Registry Tool ────────────────────
    # GAP-1 FIX (2026-06-27): Every organ MUST expose <organ>_surface_status.
    # This is the non-judgment-lane discovery tool. Any MCP client can call it.
    # Returns canonical surface — 16 tools, not the 47 registered ghosts.
    # Mode registry: tool list + domains
    # Mode health: service status
    # DITEMPA BUKAN DIBERI.

    @mcp.tool(name="geox_surface_status", annotations=_geox_annotations("geox_surface_status"))
    async def geox_surface_status(
        mode: str = "registry",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Federation-standard registry probe for GEOX.

        Use this to discover what GEOX actually exposes.
        Not geox_system_registry_status (removed Phase 1).
        Not geox_doctrine (judgment lane, arifOS-only).

        Modes:
          registry  — canonical tool list + domains + affordance summary
          health    — service status, version, uptime

        This is the GAP-1 fix: one standard name across all organs.
        WEALTH has wealth_system_registry_status. GEOX now has geox_surface_status.
        arifOS has arifOS tools for the same purpose.
        """
        import datetime, subprocess

        try:
            git_version = (
                "geox-"
                + subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
            )
        except Exception:
            git_version = "geox-unknown"

        if mode == "health":
            return {
                "status": "healthy",
                "organ": "GEOX",
                "version": "v2026.06.22-phase2",
                "git_version": git_version,
                "canonical_tools": len(CANONICAL_PUBLIC_TOOLS),
                "mcp_transport": "http",
                "mcp_port": 8081,
                "registered_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

        # registry mode — canonical surface only
        # Domain sourced from GEOX_TOOL_MANIFEST via get_tool_domain() (registry.py).
        # Single source of truth — structured manifest replaces hardcoded inline dict.
        canonical_list = []
        for tool_name in CANONICAL_PUBLIC_TOOLS:
            canonical_list.append(
                {
                    "name": tool_name,
                    "domain": get_tool_domain(tool_name),
                    "affordance": {
                        "action_class": "ANALYZE"
                        if tool_name.startswith("geox_")
                        and "claim" not in tool_name
                        and "doctrine" not in tool_name
                        and "evidence" not in tool_name
                        and "prospect" not in tool_name
                        else "OBSERVE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": tool_name in ("geox_claim", "geox_prospect"),
                        "final_authority": "ARIF",
                    },
                }
            )

        return {
            "status": "healthy",
            "organ": "GEOX",
            "surface_version": "geox-2f2e65d4",
            "canonical_tools": canonical_list,
            "tool_count": len(CANONICAL_PUBLIC_TOOLS),
            "note": "31 extra tools are registered in FastMCP but NOT in canonical surface. Use this list only.",
            "registered_at": __import__("datetime", fromlist=["datetime"])
            .datetime.now(__import__("datetime", fromlist=["datetime"]).timezone.utc)
            .isoformat(),
        }

    @mcp.tool(name="geox_seismic_ingest", annotations=_geox_annotations("geox_seismic_ingest"))
    async def _seismic_ingest(
        mode: str = "inspect_segy",
        volume_ref: str | None = None,
        output_path: str | None = None,
        sample_interval_ms: float = 4,
        textual_header: str = "",
        overwrite: bool = False,
        provenance: str = "fixture",
        segy_metadata: dict[str, Any] | None = None,
        seismic_metadata: dict[str, Any] | None = None,
        source_uri: str | None = None,
        source_type: str = "seismic",
        well_id: str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """SEG-Y I/O, header inspection."""
        from geox_mcp.tools.seismic_ingest import geox_seismic_ingest as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode, "volume_ref": volume_ref, "output_path": output_path,
                "sample_interval_ms": sample_interval_ms, "textual_header": textual_header,
                "overwrite": overwrite, "provenance": provenance,
                "segy_metadata": segy_metadata, "seismic_metadata": seismic_metadata,
                "source_uri": source_uri, "source_type": source_type, "well_id": well_id,
            },
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )
        return await _impl(**args)

    @mcp.tool(name="geox_seismic_interpret", annotations=_geox_annotations("geox_seismic_interpret"))
    async def _seismic_interpret(
        mode: str = "horizon_contrast",
        source_uri: str = "",
        source_type: str = "csv",
        action: str = "get",
        volume_ref: str = "",
        frame_index: int = 0,
        orientation: str = "inline",
        provenance: str = "fixture",
        image_data: str | None = None,
        blend_mode: str = "alpha",
        horizon_query: str = "unconformity",
        threshold: float = 0.5,
        confidence_cap: float = 0.9,
        cube_ref: str | None = None,
        volume_inline: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Horizon contrast, faults, frames, blend."""
        from geox_mcp.tools.seismic_interpret import geox_seismic_interpret as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode, "source_uri": source_uri, "source_type": source_type,
                "action": action, "volume_ref": volume_ref,
                "frame_index": frame_index, "orientation": orientation,
                "provenance": provenance, "image_data": image_data,
                "blend_mode": blend_mode, "horizon_query": horizon_query,
                "threshold": threshold, "confidence_cap": confidence_cap,
                "cube_ref": cube_ref, "volume_inline": volume_inline,
            },
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )
        return await _impl(**args)

    @mcp.tool(name="geox_vision", annotations=_geox_annotations("geox_vision"))
    async def _vision(
        mode: str = "infer_minimax",
        image_path: str = "",
        basin_context: str = "unknown",
        interpretation_goal: str = "Identify structural features",
        has_segy: bool = False,
        mimo_backend_url: str | None = None,
        mimo_model: str | None = None,
        mcp_url: str | None = None,
        model_id: str = "minimax-M3-vision",
        perceptual_inventory: dict[str, Any] | None = None,
        ground_truth_inventory: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """VLM inference, audit, calibration, perceptual."""
        from geox_mcp.tools.vision_unified import geox_vision as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode, "image_path": image_path,
                "basin_context": basin_context,
                "interpretation_goal": interpretation_goal,
                "has_segy": has_segy, "mimo_backend_url": mimo_backend_url,
                "mimo_model": mimo_model, "mcp_url": mcp_url,
                "model_id": model_id, "perceptual_inventory": perceptual_inventory,
                "ground_truth_inventory": ground_truth_inventory,
            },
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )
        return await _impl(**args)

    # ── SEISMIC VISION AI — 4 modes (Phase 3.2, 2026-07-06) ────────────────────
    # Cognitive visual AI taxonomy: OBS_IMAGE / DER_RENDER_ENHANCEMENT / GEN_HYPOTHESIS / DER_COGNITIVE_RENDER

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_visual_understand", annotations=_geox_annotations("geox_visual_understand"))
    async def _visual_understand(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Extract visual patterns from seismic image. epistemic: OBS_IMAGE."""
        from geox_mcp.tools.seismic_vision_ai_async import geox_visual_understand_async as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_visual_enhance", annotations=_geox_annotations("geox_visual_enhance"))
    async def _visual_enhance(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Enhance seismic readability. epistemic: DER_RENDER_ENHANCEMENT."""
        from geox_mcp.tools.seismic_vision_ai_async import geox_visual_enhance_async as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_visual_generate_hypotheses", annotations=_geox_annotations("geox_visual_generate_hypotheses"))
    async def _visual_generate_hypotheses(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate visual alternatives across discontinuity gaps. epistemic: GEN_HYPOTHESIS."""
        from geox_mcp.tools.seismic_vision_ai_async import geox_visual_generate_hypotheses_async as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_panel_d_render", annotations=_geox_annotations("geox_panel_d_render"))
    async def _panel_d_render(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Render cognitive interpretation dashboard. epistemic: DER_COGNITIVE_RENDER."""
        from geox_mcp.tools.seismic_vision_ai_async import geox_panel_d_render_async as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_physical_reality_interpret", annotations=_geox_annotations("geox_physical_reality_interpret"))
    async def _physical_reality_interpret(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Multi-attribute physical reality gate + horizon/fault extraction. epistemic: OBS→DER→INT."""
        from geox_mcp.tools.geox_physical_reality_async import geox_physical_reality_interpret as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_cognitive_rank_hypotheses", annotations=_geox_annotations("geox_cognitive_rank_hypotheses"))
    async def _cognitive_rank_hypotheses(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Rank geological hypotheses by basin prior. epistemic: INT_SEISMIC."""
        from geox_mcp.tools.geox_geological_cognition_async import geox_cognitive_rank_hypotheses as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_segy_audit", annotations=_geox_annotations("geox_segy_audit"))
    async def _segy_audit(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Full SEG-Y trace reality pipeline. epistemic: OBS_SEGY_TRACE."""
        from geox_mcp.tools.geox_segy_trace_reality_async import geox_segy_audit as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_well_tie", annotations=_geox_annotations("geox_well_tie"))
    async def _well_tie(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Well-to-seismic tie via bruges. epistemic: DER_SYNTHETIC → INT_GEOLOGY_HORIZON."""
        from geox_mcp.tools.geox_well_tie_bruges_async import geox_well_tie as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_3d_model", annotations=_geox_annotations("geox_3d_model"))
    async def _3d_model(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """3D structural model via GemPy from 2D picks. epistemic: INT_3D_STRUCTURE."""
        from geox_mcp.tools.geox_3d_modeling_gempy_async import geox_3d_model as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_wealth_consequence", annotations=_geox_annotations("geox_wealth_consequence"))
    async def _wealth_consequence(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Capital consequence via WEALTH HarnessEngine. epistemic: CAPITAL_CONSEQUENCE."""
        from geox_mcp.tools.geox_wealth_bridge_async import geox_wealth_consequence as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    @mcp.tool(name="geox_subsurface_model", annotations=_geox_annotations("geox_subsurface_model"))
    async def _subsurface_model(
        mode: str = "joint_inversion",
        survey_type: str = "gravity",
        easting_m: tuple[float, ...] | None = None,
        northing_m: tuple[float, ...] | None = None,
        prisms: list[dict[str, Any]] | None = None,
        magnetization_a_m: float = 0.0,
        field_declination_deg: float = 0.0,
        field_inclination_deg: float = 0.0,
        layers: list[dict[str, Any]] | None = None,
        frequencies_hz: list[float] | None = None,
        observations: dict[str, Any] | None = None,
        prior: dict[str, Any] | None = None,
        max_iter: int = 50,
        tolerance: float = 0.001,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Joint inversion, gravity/mag, MT forward."""
        from geox_mcp.tools.subsurface_model import geox_subsurface_model as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode, "survey_type": survey_type,
                "easting_m": easting_m, "northing_m": northing_m,
                "prisms": prisms, "magnetization_a_m": magnetization_a_m,
                "field_declination_deg": field_declination_deg,
                "field_inclination_deg": field_inclination_deg,
                "layers": layers, "frequencies_hz": frequencies_hz,
                "observations": observations, "prior": prior,
                "max_iter": max_iter, "tolerance": tolerance,
            },
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )
        return await _impl(**args)

    @mcp.tool(name="geox_basin", annotations=_geox_annotations("geox_basin"))
    async def _basin(
        mode: str = "profile",
        name: str = "",
        basin_name: str = "",
        macrostrat_mode: str = "macrostrat_units",
        lat: float | None = None,
        lng: float | None = None,
        age_ma: float | None = None,
        age_top_ma: float | None = None,
        age_bot_ma: float | None = None,
        period: str | None = None,
        query: str | None = None,
        include_pending_datasets: bool = True,
        force: bool = False,
        intent: str = "general",
        bbox: list[float] | None = None,
        scene_mode: str = "bbox_context",
        crs: str = "EPSG:4326",
        vp_slice_inline: dict[str, Any] | None = None,
        profile_mode: str = "overview",
        claim_strictness: str = "screen",
        evidence_refs: list[str] | None = None,
        include_missing_evidence: bool = True,
        # P0+P1 tectonic kernel parameters (2026-07-03)
        reconstruct_mode: str = "position",
        model: str = "Merdith2021",
        models: list[str] | None = None,
        rift_mode: str = "full",
        beta: float | None = None,
        crust_initial_km: float | None = None,
        crust_current_km: float | None = None,
        time_since_rift_ma: float = 0.0,
        subsidence_rate_mm_yr: float | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Profile, resolve, macrostrat, deep_time, emag2, icgem, intake, scene.

        Pattern A (explicit params) — fastmcp 3.4.2 does not support **kwargs in tool
        signatures, so every parameter of basin_unified.geox_basin is declared here.
        Session metadata is forwarded only if the impl signature accepts it.
        """
        from geox_mcp.tools.basin_unified import geox_basin as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode,
                "name": name,
                "basin_name": basin_name,
                "macrostrat_mode": macrostrat_mode,
                "lat": lat,
                "lng": lng,
                "age_ma": age_ma,
                "age_top_ma": age_top_ma,
                "age_bot_ma": age_bot_ma,
                "period": period,
                "query": query,
                "include_pending_datasets": include_pending_datasets,
                "force": force,
                "intent": intent,
                "bbox": bbox,
                "scene_mode": scene_mode,
                "crs": crs,
                "vp_slice_inline": vp_slice_inline,
                "profile_mode": profile_mode,
                "claim_strictness": claim_strictness,
                "evidence_refs": evidence_refs,
                "include_missing_evidence": include_missing_evidence,
                # P0+P1
                "reconstruct_mode": reconstruct_mode,
                "model": model,
                "models": models,
                "rift_mode": rift_mode,
                "beta": beta,
                "crust_initial_km": crust_initial_km,
                "crust_current_km": crust_current_km,
                "time_since_rift_ma": time_since_rift_ma,
                "subsidence_rate_mm_yr": subsidence_rate_mm_yr,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    @mcp.tool(name="geox_claim", annotations=_geox_annotations("geox_claim"))
    async def _claim(
        mode: str = "create",
        claim_id: str = "",
        claim_text: str = "",
        claim_type: str = "other",
        truth_class: str = "INTERPRETATION",
        evidence_ids: list[str] | None = None,
        uncertainty_p10: float | None = None,
        uncertainty_p50: float | None = None,
        uncertainty_p90: float | None = None,
        uncertainty_distribution: str = "lognormal",
        alternatives: list[dict[str, Any]] | None = None,
        provenance: str = "GEOX Claim Engine",
        authority: str = "GEOX_CLAIM_WORKER",
        challenge_text: str = "",
        alternative_claim_text: str = "",
        alternative_evidence_ids: list[str] | None = None,
        challenge_evidence_ids: list[str] | None = None,
        alternative_uncertainty: dict[str, Any] | None = None,
        challenger_provenance: str = "GEOX Claim Engine",
        ack_irreversible: bool = False,
        seal_verdict: str = "SEAL",
        voxel_state: dict[str, Any] | None = None,
        evidence_id: str = "",
        evidence_type: str = "supporting",
        epistemic_label: str | None = None,
        forbidden_uses: list[str] | None = None,
        source_citation: dict[str, Any] | None = None,
        category: str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Create, validate, challenge, seal, attach."""
        from geox_mcp.tools.claim_unified import geox_claim as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode, "claim_id": claim_id, "claim_text": claim_text,
                "claim_type": claim_type, "truth_class": truth_class,
                "evidence_ids": evidence_ids, "uncertainty_p10": uncertainty_p10,
                "uncertainty_p50": uncertainty_p50, "uncertainty_p90": uncertainty_p90,
                "uncertainty_distribution": uncertainty_distribution,
                "alternatives": alternatives, "provenance": provenance,
                "authority": authority, "challenge_text": challenge_text,
                "alternative_claim_text": alternative_claim_text,
                "alternative_evidence_ids": alternative_evidence_ids,
                "challenge_evidence_ids": challenge_evidence_ids,
                "alternative_uncertainty": alternative_uncertainty,
                "challenger_provenance": challenger_provenance,
                "ack_irreversible": ack_irreversible, "seal_verdict": seal_verdict,
                "voxel_state": voxel_state, "evidence_id": evidence_id,
                "evidence_type": evidence_type, "epistemic_label": epistemic_label,
                "forbidden_uses": forbidden_uses, "source_citation": source_citation,
                "category": category,
            },
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            ack_irreversible=ack_irreversible,
        )
        return await _impl(**args)

    @mcp.tool(name="geox_evidence", annotations=_geox_annotations("geox_evidence"))
    async def _evidence(
        mode: str = "synthesize",
        query: str = "",
        scope: str = "all",
        permission_level: str = "authorized",
        file_path: str = "",
        basin_name: str | None = None,
        evidence_refs: list[str] | None = None,
        hypotheses: list[str] | None = None,
        scale: str = "parasequence",
        depo_context: str = "unknown",
        claim_strictness: str = "screen",
        reasoning_mode: str = "default",
        samples: list[dict[str, Any]] | None = None,
        block_size_km: float = 5.0,
        n_folds: int = 5,
        target_key: str = "value",
        feature_keys: list[str] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Discover, synthesize, abduct, contradict, literature. Pattern A wrapper."""
        from geox_mcp.tools.evidence_unified import geox_evidence as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode,
                "query": query,
                "scope": scope,
                "permission_level": permission_level,
                "file_path": file_path,
                "basin_name": basin_name,
                "evidence_refs": evidence_refs,
                "hypotheses": hypotheses,
                "scale": scale,
                "depo_context": depo_context,
                "claim_strictness": claim_strictness,
                "reasoning_mode": reasoning_mode,
                "samples": samples,
                "block_size_km": block_size_km,
                "n_folds": n_folds,
                "target_key": target_key,
                "feature_keys": feature_keys,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    @mcp.tool(name="geox_prospect", annotations=_geox_annotations("geox_prospect"))
    async def _prospect(
        prospect_ref: str | None = None,
        mode: str = "screen",
        evidence_refs: list[str] | None = None,
        verdict: str = "compute",
        judge_pin: str | None = None,
        structural_map_inline: dict[str, Any] | None = None,
        power_params: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
        ack_irreversible: bool = False,
    ) -> dict[str, Any]:
        """Volumetrics, POS, EVOI, risk assessment. Pattern A wrapper."""
        from geox_mcp.tools.prospect_unified import geox_prospect as _impl

        args = _safe_forward(
            _impl,
            {
                "prospect_ref": prospect_ref,
                "mode": mode,
                "evidence_refs": evidence_refs,
                "verdict": verdict,
                "judge_pin": judge_pin,
                "structural_map_inline": structural_map_inline,
                "power_params": power_params,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
            ack_irreversible=ack_irreversible,
        )
        return await _impl(**args)

    # INTERNAL-ONLY 2026-06-27: judgment lane — removed from MCP facade
    # NOTE: by lane policy, geox_doctrine is in the judgment lane and cannot be
    # called directly from non-arifOS clients. Use arifOS judge → GEOX path.
    async def _doctrine(
        mode: str = "anti_beautiful_one",
        introduced_by: str = "",
        rung_origin: int = 0,
        description: str | None = None,
        parent_assumption_id: str | None = None,
        inherited_from: str | None = None,
        epistemic_label: str = "DER",
        claim_id: str = "",
        action: str = "review",
        void_reason: str | None = None,
        rung: int | None = None,
        depends_on_assumption_ids: list[str] | None = None,
        concept: str = "",
        query: str = "",
        state: dict[str, Any] | None = None,
        age_ma: float = 0,
        tile_id: str = "",
        task: str = "land_cover",
        bands: list[str] | None = None,
        time_range_start: str = "2024-01-01",
        time_range_end: str = "2024-12-31",
        cloud_cover_max: float = 0.2,
        source_uri: str | None = None,
        text: str = "",
        grounding_evidence_count: int = 0,
        grounding_evidence_rungs: list[int] | None = None,
        threshold: float = 1.5,
        include_decomposition: bool = True,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Anti-Beautiful-One, assumptions, Gödel, guards. Use mode='registry' for tool discovery.

        NOTE: by lane policy, geox_doctrine is in the judgment lane and cannot be
        called directly from non-arifOS clients. Use arifOS judge → GEOX path.
        Pattern A wrapper — every doctrine_unified.geox_doctrine param declared.
        """
        from geox_mcp.tools.doctrine_unified import geox_doctrine as _impl

        args: dict[str, Any] = {
            "mode": mode,
            "introduced_by": introduced_by,
            "rung_origin": rung_origin,
            "description": description,
            "parent_assumption_id": parent_assumption_id,
            "inherited_from": inherited_from,
            "epistemic_label": epistemic_label,
            "claim_id": claim_id,
            "action": action,
            "void_reason": void_reason,
            "rung": rung,
            "depends_on_assumption_ids": depends_on_assumption_ids,
            "concept": concept,
            "query": query,
            "state": state,
            "age_ma": age_ma,
            "tile_id": tile_id,
            "task": task,
            "bands": bands,
            "time_range_start": time_range_start,
            "time_range_end": time_range_end,
            "cloud_cover_max": cloud_cover_max,
            "source_uri": source_uri,
            "text": text,
            "grounding_evidence_count": grounding_evidence_count,
            "grounding_evidence_rungs": grounding_evidence_rungs,
            "threshold": threshold,
            "include_decomposition": include_decomposition,
        }
        args = _safe_forward(_impl, args, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # ── SURFACE EARTH DOMAIN — Physical Visible Earth (2026-06-25 FORGE) ────────

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_earthquake_catalog", annotations=_geox_annotations("geox_earthquake_catalog"))
    async def _earthquake_catalog(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query USGS Earthquake Catalog for seismic events. OBSERVED data — real seismic events from USGS FDSN API. Public Domain."""
        from geox_mcp.tools.earth_surface import geox_earthquake_catalog as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_relief_ingest", annotations=_geox_annotations("geox_relief_ingest"))
    async def _relief_ingest(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Ingest ETOPO 2022 global relief (topography + bathymetry). OBSERVED data — measured elevation from NOAA NCEI. Public Domain."""
        from geox_mcp.tools.earth_surface import geox_relief_ingest as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_bathymetry_ingest", annotations=_geox_annotations("geox_bathymetry_ingest"))
    async def _bathymetry_ingest(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Ingest GEBCO_2026 global bathymetry grid (ocean floor terrain). OBSERVED data — measured ocean depth from IHO/UNESCO. Public Domain."""
        from geox_mcp.tools.earth_surface import geox_bathymetry_ingest as _impl

        return await _auto_call(_impl, arguments)

    # ── EXTENDED EARTH DIMENSIONS — D4-D17 Open Data (2026-06-25 FORGE) ───────

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_heatflow_query", annotations=_geox_annotations("geox_heatflow_query"))
    async def _heatflow(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query IHFC Global Heat Flow Database. OBSERVED — ~91k measurements. GFZ/IHFC CC-BY-4.0."""
        from geox_mcp.tools.earth_surface_2 import geox_heatflow_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_stress_query", annotations=_geox_annotations("geox_stress_query"))
    async def _stress(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query World Stress Map 2025 (WSM). OBSERVED — ~100k stress orientations. GFZ CC-BY-4.0."""
        from geox_mcp.tools.earth_surface_2 import geox_stress_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_geochem_query", annotations=_geox_annotations("geox_geochem_query"))
    async def _geochem(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query EarthChem/PetDB for igneous geochemistry. OBSERVED — global rock analyses. CC-BY."""
        from geox_mcp.tools.earth_surface_2 import geox_geochem_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_plate_reconstruct", annotations=_geox_annotations("geox_plate_reconstruct"))
    async def _plate(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Reconstruct a point through deep time via GPlates. INTERPRETED — plate model dependent. GPL-2.0."""
        from geox_mcp.tools.earth_surface_2 import geox_plate_reconstruct as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_paleomag_query", annotations=_geox_annotations("geox_paleomag_query"))
    async def _paleomag(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query MagIC for paleomagnetic data. OBSERVED — rock magnetic measurements. CC-BY-4.0."""
        from geox_mcp.tools.earth_surface_2 import geox_paleomag_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_gravity_change_query", annotations=_geox_annotations("geox_gravity_change_query"))
    async def _grace(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query GRACE-FO for time-variable gravity (mass change). OBSERVED — NASA satellite gravimetry. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_gravity_change_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_ocean_query", annotations=_geox_annotations("geox_ocean_query"))
    async def _ocean(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query Copernicus Marine (CMEMS) for ocean physics/BGC. OBSERVED — satellite + model. EU Open Data."""
        from geox_mcp.tools.earth_surface_2 import geox_ocean_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_erddap_query", annotations=_geox_annotations("geox_erddap_query"))
    async def _erddap(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query NOAA ERDDAP for ocean/atmosphere data. OBSERVED — 10k+ datasets. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_erddap_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_climate_reanalysis", annotations=_geox_annotations("geox_climate_reanalysis"))
    async def _climate(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query ERA5 global reanalysis. OBSERVED — ECMWF hourly data from 1940. Copernicus License."""
        from geox_mcp.tools.earth_surface_2 import geox_climate_reanalysis as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_hydrology_query", annotations=_geox_annotations("geox_hydrology_query"))
    async def _hydrology(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query USGS Water Services for streamflow/groundwater. OBSERVED — US real-time. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_hydrology_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_satellite_catalog", annotations=_geox_annotations("geox_satellite_catalog"))
    async def _satellite(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Search STAC for Landsat/MODIS/Sentinel imagery. OBSERVED — satellite surface reflectance. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_satellite_catalog as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_uk_petroleum_query", annotations=_geox_annotations("geox_uk_petroleum_query"))
    async def _nsta(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query NSTA UK petroleum data (wells, fields, licences). OBSERVED — UKCS regulatory. OGL v3.0."""
        from geox_mcp.tools.earth_surface_2 import geox_uk_petroleum_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_geology_map_query", annotations=_geox_annotations("geox_geology_map_query"))
    async def _onegeology(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query OneGeology WMS for national geological maps. OBSERVED — aggregated survey data."""
        from geox_mcp.tools.earth_surface_2 import geox_geology_map_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_space_weather", annotations=_geox_annotations("geox_space_weather"))
    async def _spaceweather(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query NOAA SWPC for space weather (Kp, Dst, solar wind). OBSERVED — real-time. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_space_weather as _impl

        return await _auto_call(_impl, arguments)

    # ── PHYSICS-FIRST STRATIGRAPHY ENGINES — Phase 3.0 (2026-07-03) ────────────
    # The extinction event: replaces LST/TST/HST taxonomy with physics simulation.
    # Sequences EMERGE from accommodation + eustasy + sediment, not from rules.
    # DITEMPA BUKAN DIBERI.

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_simulate_accommodation", annotations=_geox_annotations("geox_simulate_accommodation"))
    async def _simulate_accommodation(
        initial_subsidence_km: float = 2.0,
        thermal_subsidence_rate_mm_yr: float = 0.05,
        eustatic_rate_mm_yr: float = 0.0,
        sediment_supply_rate_m_myr: float = 50.0,
        initial_water_depth_m: float = 100.0,
        duration_ma: float = 10.0,
        time_step_myr: float = 0.5,
        dominant_lithology: str = "sandstone",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Simulate accommodation through time: tectonic subsidence + eustasy + sediment loading + compaction.

        Physics-first: this is the DRIVER of stratigraphy. Not cartoon sea-level curves.
        Surfaces and stacking patterns EMERGE from the simulation.
        Replaces the 'accommodation' concept that LST/TST/HST tries to name but never computes.

        Returns: accommodation steps with surface types and stacking patterns that emerged from physics.
        """
        from geox_core.engines.stratigraphy.accommodation import (
            AccommodationRequest,
            simulate_accommodation as _impl,
        )

        try:
            req = AccommodationRequest(
                initial_subsidence_km=initial_subsidence_km,
                thermal_subsidence_rate_mm_yr=thermal_subsidence_rate_mm_yr,
                eustatic_rate_mm_yr=eustatic_rate_mm_yr,
                sediment_supply_rate_m_myr=sediment_supply_rate_m_myr,
                initial_water_depth_m=initial_water_depth_m,
                duration_ma=duration_ma,
                time_step_myr=time_step_myr,
                dominant_lithology=dominant_lithology,
            )
            result = _impl(req)
            return {"status": "success", "tool": "geox_simulate_accommodation", **result.model_dump()}
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_simulate_accommodation", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_simulate_surfaces", annotations=_geox_annotations("geox_simulate_surfaces"))
    async def _simulate_surfaces(
        initial_subsidence_km: float = 2.0,
        thermal_subsidence_rate_mm_yr: float = 0.05,
        eustatic_rate_mm_yr: float = 0.0,
        sediment_supply_rate_m_myr: float = 50.0,
        initial_water_depth_m: float = 100.0,
        duration_ma: float = 10.0,
        time_step_myr: float = 0.5,
        dominant_lithology: str = "sandstone",
        min_surface_magnitude_m: float = 0.5,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate stratigraphic surfaces from physics: erosion, flooding, MFS, truncation, ravinement.

        Surfaces are REAL, MAPPABLE, FALSIFIABLE — not taxonomic labels.
        This is Sloss's physics: base level → erosion → flooding → surfaces.
        A surface is a physical object. A systems tract is a cartoon.

        Returns: surfaces with type, age, geometry (onlap/downlap/truncation), and packages between them.
        """
        from geox_core.engines.stratigraphy.accommodation import (
            AccommodationRequest,
            simulate_accommodation as _acc_impl,
        )
        from geox_core.engines.stratigraphy.surface_first import generate_surfaces as _surf_impl

        try:
            req = AccommodationRequest(
                initial_subsidence_km=initial_subsidence_km,
                thermal_subsidence_rate_mm_yr=thermal_subsidence_rate_mm_yr,
                eustatic_rate_mm_yr=eustatic_rate_mm_yr,
                sediment_supply_rate_m_myr=sediment_supply_rate_m_myr,
                initial_water_depth_m=initial_water_depth_m,
                duration_ma=duration_ma,
                time_step_myr=time_step_myr,
                dominant_lithology=dominant_lithology,
            )
            acc = _acc_impl(req)
            result = _surf_impl(acc, min_surface_magnitude_m=min_surface_magnitude_m)
            return {"status": "success", "tool": "geox_simulate_surfaces", **result.model_dump()}
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_simulate_surfaces", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_simulate_sequences", annotations=_geox_annotations("geox_simulate_sequences"))
    async def _simulate_sequences(
        initial_subsidence_km: float = 2.0,
        thermal_subsidence_rate_mm_yr: float = 0.05,
        eustatic_rate_mm_yr: float = 0.0,
        sediment_supply_rate_m_myr: float = 50.0,
        initial_water_depth_m: float = 100.0,
        duration_ma: float = 10.0,
        time_step_myr: float = 0.5,
        dominant_lithology: str = "sandstone",
        min_surface_magnitude_m: float = 0.5,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Let sequences EMERGE from physics: accommodation → surfaces → sequences.

        Sequences are NOT classified as LST/TST/HST. They EMERGE from:
        - erosion → sequence boundaries
        - flooding → flooding surfaces
        - maximum flooding → MFS
        - progradation/retrogradation → stacking patterns

        Scale (parasequence/depositional/Sloss) is determined by DURATION, not by rules.
        Resource potential (reservoir/seal/source) is inferred from stacking and surface types.

        Returns: emergent sequences with bounding surfaces, stacking patterns, resource potential, and resource graph.
        """
        from geox_core.engines.stratigraphy.accommodation import (
            AccommodationRequest,
            simulate_accommodation as _acc_impl,
        )
        from geox_core.engines.stratigraphy.surface_first import generate_surfaces as _surf_impl
        from geox_core.engines.stratigraphy.sequence_emergence import emerge_sequences as _seq_impl

        try:
            req = AccommodationRequest(
                initial_subsidence_km=initial_subsidence_km,
                thermal_subsidence_rate_mm_yr=thermal_subsidence_rate_mm_yr,
                eustatic_rate_mm_yr=eustatic_rate_mm_yr,
                sediment_supply_rate_m_myr=sediment_supply_rate_m_myr,
                initial_water_depth_m=initial_water_depth_m,
                duration_ma=duration_ma,
                time_step_myr=time_step_myr,
                dominant_lithology=dominant_lithology,
            )
            acc = _acc_impl(req)
            surfaces = _surf_impl(acc, min_surface_magnitude_m=min_surface_magnitude_m)
            result = _seq_impl(surfaces, acc)
            return {"status": "success", "tool": "geox_simulate_sequences", **result.model_dump()}
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_simulate_sequences", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_simulate_routing", annotations=_geox_annotations("geox_simulate_routing"))
    async def _simulate_routing(
        source_position_km: float = 0.0,
        source_sand_fraction: float = 0.6,
        source_supply_rate_m_myr: float = 100.0,
        source_discharge_m3_s: float = 2000.0,
        profile_length_km: float = 120.0,
        shelf_width_km: float = 50.0,
        shelf_gradient: float = 0.001,
        slope_gradient: float = 0.05,
        slope_start_km: float = 60.0,
        basin_floor_start_km: float = 80.0,
        accommodation_rate_m_myr: float = 50.0,
        duration_ma: float = 10.0,
        time_step_myr: float = 1.0,
        seed: int | None = 42,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Simulate sediment routing from source to sink: deltas, fans, bypass, deposition.

        Physics-first: generates depositional bodies from slope-driven transport,
        sand/mud partitioning, and autogenic lobe switching.
        Not facies modeling. Not geobody picking. Physics.

        Returns: depositional bodies (reservoirs, seals, sources), lobe events,
        mass balance, and emergent environments.
        """
        from geox_core.engines.stratigraphy.sediment_routing import (
            BasinGeometry,
            RoutingRequest,
            SedimentSource,
            simulate_routing as _impl,
        )

        try:
            req = RoutingRequest(
                sources=[
                    SedimentSource(
                        source_id="SOURCE1",
                        position_km=source_position_km,
                        sand_fraction=source_sand_fraction,
                        supply_rate_m_myr=source_supply_rate_m_myr,
                        discharge_m3_s=source_discharge_m3_s,
                    )
                ],
                geometry=BasinGeometry(
                    profile_length_km=profile_length_km,
                    shelf_width_km=shelf_width_km,
                    shelf_gradient=shelf_gradient,
                    slope_gradient=slope_gradient,
                    slope_start_km=slope_start_km,
                    basin_floor_start_km=basin_floor_start_km,
                ),
                accommodation_rate_m_myr=accommodation_rate_m_myr,
                duration_ma=duration_ma,
                time_step_myr=time_step_myr,
                seed=seed,
            )
            result = _impl(req)
            return {"status": "success", "tool": "geox_simulate_routing", **result.model_dump()}
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_simulate_routing", source_organ="geox")

    # ── SEISMIC COGNITION ENGINE — Phase 3.1 (2026-07-06) ──────────────────────
    # 7-layer image-first pipeline for governed seismic interpretation.
    # IMAGE-FIRST COGNITION → SEG-Y VALIDATION → WELL-TIE GEOLOGY → GOVERNANCE
    # Constitutional: F7 humility (cap 0.90), F9 anti-hantu, non-uniqueness.
    # DITEMPA BUKAN DIBERI.

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_seismic_cognition", annotations=_geox_annotations("geox_seismic_cognition"))
    async def _seismic_cognition(
        mode: str = "full_pipeline",
        image_path: str | None = None,
        segy_path: str | None = None,
        well_data: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Seismic Cognition Engine — 7-layer image-first governed pipeline.

        Implements the constitutional doctrine:
          IMAGE-FIRST COGNITION → SEG-Y VALIDATION → WELL-TIE GEOLOGY → GOVERNANCE

        Modes:
          image_first  — Fast cognitive pass from rendered seismic image (Layers 1-3)
          validate     — SEG-Y physical audit (Layer 5)
          calibrate    — Well-tie calibration (Layer 6)
          full_pipeline — Complete chain: image → SEG-Y → well-tie → governance
          doctrine     — Returns the seismic cognition doctrine and layer definitions

        Constitutional invariants:
          - F7 HUMILITY: confidence hard-capped at 0.90
          - F9 ANTI-HANTU: no hallucinated geology
          - Non-uniqueness: every visual feature has multiple possible causes
          - OBS_IMAGE cannot claim geological meaning
          - INT_SEISMIC always keeps alternatives alive
          - DER_SYNTHETIC always labeled synthetic
          - No geology claim without physics validation
          - No economics without well tie
        """
        from geox_core.seismic_cognition import (
            CognitionResult,
            SeismicCognitionEngine,
            get_seismic_cognition_doctrine,
        )

        try:
            if mode == "doctrine":
                return {
                    "status": "success",
                    "tool": "geox_seismic_cognition",
                    "mode": "doctrine",
                    **get_seismic_cognition_doctrine(),
                }

            engine = SeismicCognitionEngine()

            if mode == "image_first":
                if not image_path:
                    return {
                        "status": "error",
                        "tool": "geox_seismic_cognition",
                        "error": "image_path required for image_first mode",
                    }
                result = await engine.process_image_first(image_path)
                return {
                    "status": "success",
                    "tool": "geox_seismic_cognition",
                    "mode": "image_first",
                    **result.to_dict(),
                }

            elif mode == "validate":
                if not segy_path:
                    return {
                        "status": "error",
                        "tool": "geox_seismic_cognition",
                        "error": "segy_path required for validate mode",
                    }
                # Build a prior result from image if provided
                if image_path:
                    prior = await engine.process_image_first(image_path)
                else:
                    prior = CognitionResult()
                result = await engine.validate_with_segy(segy_path, prior)
                return {
                    "status": "success",
                    "tool": "geox_seismic_cognition",
                    "mode": "validate",
                    **result.to_dict(),
                }

            elif mode == "calibrate":
                if not well_data:
                    return {
                        "status": "error",
                        "tool": "geox_seismic_cognition",
                        "error": "well_data required for calibrate mode",
                    }
                # Build prior chain
                if image_path:
                    prior = await engine.process_image_first(image_path)
                else:
                    prior = CognitionResult()
                if segy_path:
                    prior = await engine.validate_with_segy(segy_path, prior)
                result = await engine.calibrate_with_wells(well_data, prior)
                return {
                    "status": "success",
                    "tool": "geox_seismic_cognition",
                    "mode": "calibrate",
                    **result.to_dict(),
                }

            elif mode == "full_pipeline":
                verdict = await engine.full_pipeline(
                    image_path=image_path,
                    segy_path=segy_path,
                    well_data=well_data,
                )
                return {
                    "status": "success",
                    "tool": "geox_seismic_cognition",
                    "mode": "full_pipeline",
                    **verdict.to_dict(),
                }

            else:
                return {
                    "status": "error",
                    "tool": "geox_seismic_cognition",
                    "error": f"Unknown mode: {mode}. Valid: image_first, validate, calibrate, full_pipeline, doctrine",
                }

        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_seismic_cognition", source_organ="geox")

    # ═══════════════════════════════════════════════════════════════════════════════
    # SEISMIC PIPELINE TOOLS — Phase 3.0 RSI Cognition (2026-07-06)
    # Platform-agnostic seismic interpretation pipeline.
    # Implements IMAGE-FIRST COGNITION + NON-UNIQUENESS LAW doctrines.
    # OBS_IMAGE ≠ OBS_GEOLOGY. Pixels are observed. Geology requires calibration.
    # ═══════════════════════════════════════════════════════════════════════════════

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_physical_reality_interpret", annotations=_geox_annotations("geox_physical_reality_interpret"))
    async def _geox_physical_reality_interpret(
        image_path: str,
        output_dir: str | None = None,
        max_faults: int = 15,
        max_horizons: int = 8,
    ) -> dict[str, Any]:
        """Physical reality interpretation from seismic image pixels.

        Full RSI pipeline: reality gate → crop → AGC → phase → discontinuity →
        edge → fault probability → ant-track-lite → DP horizon tracking →
        epistemic governance → provenance manifest.

        OBS_IMAGE ≠ OBS_GEOLOGY: All outputs are pixel-derived.
        Every INT claim carries alternative interpretations.
        PETROPHYSICS = HOLD from image-only input.
        """
        try:
            from geox_mcp.federation_safety import classify_error
            from geox_core.seismic_pipeline.geox_physical_reality import GeoxPhysicalReality

            engine = GeoxPhysicalReality()
            result = engine.interpret(image_path, output_dir=output_dir)
            return {
                "status": "success",
                "tool": "geox_physical_reality_interpret",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_physical_reality_interpret", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_geological_cognition_run", annotations=_geox_annotations("geox_geological_cognition_run"))
    async def _geox_geological_cognition_run(
        image_path: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Geological cognition layer — translate pixel patterns into geological hypotheses.

        Runs after physical reality interpretation. Classifies reflector packages,
        detects terminations (onlap/downlap/truncation), screens imaging artifacts,
        ranks multiple hypotheses per feature, and builds a geologist-style report.

        Every INT claim carries alternatives. Non-uniqueness law enforced.
        """
        try:
            import sys
            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_geological_cognition import run_geological_cognition
            from geox_physical_reality import GeoxPhysicalReality

            # First run physical reality to get attributes
            engine = GeoxPhysicalReality()
            phys = engine.interpret(image_path, output_dir=output_dir)
            if phys.get("status") == "VOID":
                return {"status": "VOID", "reason": "Physical reality gate failed"}

            # Run geological cognition on the attributes
            # Use stored raw arrays from physical reality engine
            attrs = engine._last_attrs
            fp = engine._last_fp
            horizons = engine._last_horizons
            faults = engine._last_faults

            result = run_geological_cognition(attrs, fp, horizons, faults, output_dir)
            return {
                "status": "success",
                "tool": "geox_geological_cognition_run",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_geological_cognition_run", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_panel_d_render_mcp", annotations=_geox_annotations("geox_panel_d_render_mcp"))
    async def _geox_panel_d_render_mcp(
        image_path: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Panel D — Cognitive interpretation rendering.

        Renders what the geologist JUDGES, not what pixels show.
        Zone bands, termination symbols, fault labels, horizon labels,
        artifact boxes, epistemic rulers. The panel a senior geologist
        would show to justify a drilling decision.

        Requires prior physical reality + geological cognition runs.
        """
        try:
            import sys
            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_panel_d import render_cognitive_panel
            from geox_physical_reality import GeoxPhysicalReality
            from geox_geological_cognition import run_geological_cognition

            # Run full pipeline
            engine = GeoxPhysicalReality()
            phys = engine.interpret(image_path, output_dir=output_dir)
            if phys.get("status") == "VOID":
                return {"status": "VOID", "reason": "Physical reality gate failed"}

            # Use stored raw arrays from physical reality engine
            attrs = engine._last_attrs
            fp = engine._last_fp
            horizons = engine._last_horizons
            faults = engine._last_faults
            raw_arr = engine._last_raw_arr
            crop_bbox = engine._last_crop_bbox

            cogn = run_geological_cognition(attrs, fp, horizons, faults, output_dir)

            # Render Panel D
            result = render_cognitive_panel(
                attrs,
                fp,
                faults,
                horizons,
                cogn.get("packages", []),
                cogn.get("terminations", []),
                cogn.get("artifacts", []),
                cogn.get("hypotheses", {}),
                raw_arr,
                crop_bbox,
                phys.get("provenance", {}),
                output_dir or os.path.dirname(image_path),
            )
            return {
                "status": "success",
                "tool": "geox_panel_d_render_mcp",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_panel_d_render_mcp", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_segy_trace_audit", annotations=_geox_annotations("geox_segy_trace_audit"))
    async def _geox_segy_trace_audit(
        segy_path: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """SEG-Y trace reality audit — physical validation from raw traces.

        Ingests SEG-Y, audits trace headers, checks geometry,
        validates amplitude preservation, estimates wavelet phase,
        and computes trace-level attributes.

        This is the PHYSICS_VALIDATION layer — the evidential backbone
        that validates or falsifies image-based interpretations.
        """
        try:
            import sys
            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_segy_trace_reality import (
                ingest_segy,
                audit_trace_headers,
                audit_geometry,
                check_amplitude_preservation,
                check_wavelet_phase,
                compute_trace_attributes,
            )

            ingested = ingest_segy(segy_path)
            header_audit = audit_trace_headers(ingested)
            geom_audit = audit_geometry(ingested)
            amp_audit = check_amplitude_preservation(ingested)
            wavelet_info = check_wavelet_phase(ingested)
            trace_attrs = compute_trace_attributes(ingested, wavelet_info)

            return {
                "status": "success",
                "tool": "geox_segy_trace_audit",
                "header_audit": header_audit,
                "geometry_audit": geom_audit,
                "amplitude_audit": amp_audit,
                "wavelet_info": wavelet_info,
                "trace_attributes_summary": {
                    k: {"shape": v.shape, "dtype": str(v.dtype)} for k, v in trace_attrs.items() if hasattr(v, "shape")
                },
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_segy_trace_audit", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_well_tie_compute", annotations=_geox_annotations("geox_well_tie_compute"))
    async def _geox_well_tie_compute(
        las_path: str,
        segy_path: str | None = None,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Well-tie calibration via bruges — synthetic seismogram generation.

        Loads well logs (LAS), computes synthetic seismogram via bruges,
        and ties to seismic if SEG-Y provided. This is the GEOLOGY layer
        that converts seismic interpretation into formation-calibrated picks.

        Without well tie, all interpretations remain INT_SEISMIC (not OBS_GEOLOGY).
        """
        try:
            import sys
            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_well_tie_bruges import run_well_tie

            result = run_well_tie(las_path, segy_audit_path=segy_path or "", output_dir=output_dir or "/tmp/geox_well_tie")
            return {
                "status": "success",
                "tool": "geox_well_tie_compute",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_well_tie_compute", source_organ="geox")

    # ── Phase 3.3: Tie Receipt + Preflight (2026-07-06) ─────────────────────────

    # ZEN 2026-07-11 G1: merged into geox_seismic_compute mode=tie_receipt
    async def _geox_tie_receipt(
        well_name: str,
        seismic_volume: str = "",
        polarity_convention: str = "",
        phase_convention: str = "",
        seismic_datum: str = "",
        well_datum: str = "",
        depth_basis: str = "MD",
        logs_used: str = "",
        time_depth_checkshot: bool = False,
        time_depth_vsp: bool = False,
        time_depth_confidence: str = "low",
        wavelet_source: str = "assumed",
        wavelet_phase_confidence: str = "low",
        correlation_score: float | None = None,
        residual_class: str = "unexplained",
        rock_lithology_sep: str = "low",
        rock_fluid_sep: str = "low",
        inversion_allowed: bool = False,
        decision_permission: str = "HOLD",
        decision_reason: str = "",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Seismic-to-well tie evidence envelope — metabolizer memory.

        Builds a structured receipt that tells the system what it is allowed to
        believe after a seismic-to-well tie. The receipt matters more than the
        image of the tie. It covers: data inputs, calibration quality, error
        classification, rock physics status, decision permission, and uncertainty.

        Anti-hantu: amplitude is not hydrocarbon. Impedance is not lithology.
        Inversion is not truth. Tie is not validation unless residuals are explained.
        """
        try:
            from geox_core.schemas.tie_receipt import build_tie_receipt

            logs_list = [l.strip() for l in logs_used.split(",") if l.strip()] if logs_used else []

            receipt = build_tie_receipt(
                well_name=well_name,
                seismic_volume=seismic_volume,
                session_id=session_id,
                polarity_convention=polarity_convention,
                phase_convention=phase_convention,
                seismic_datum=seismic_datum,
                well_datum=well_datum,
                depth_basis=depth_basis,
                logs_used=logs_list,
                time_depth_control={
                    "checkshot_present": time_depth_checkshot,
                    "vsp_present": time_depth_vsp,
                    "confidence": time_depth_confidence,
                },
                wavelet={
                    "source": wavelet_source,
                    "phase_confidence": wavelet_phase_confidence,
                },
                tie_quality={
                    "correlation_score": correlation_score,
                    "residual_class": residual_class,
                },
                rock_physics_status={
                    "lithology_separability": rock_lithology_sep,
                    "fluid_separability": rock_fluid_sep,
                },
                inversion_permission={
                    "allowed": inversion_allowed,
                },
                decision_permission=decision_permission,
                decision_reason=decision_reason,
            )

            return {
                "status": "success",
                "tool": "geox_tie_receipt",
                "receipt": receipt,
            }
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_tie_receipt", source_organ="geox")

    # ZEN 2026-07-11 G1: merged into geox_seismic_compute mode=tie_preflight
    async def _geox_tie_preflight(
        well_name: str,
        decision_context: str = "horizon_calibration",
        answers: str = "",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """25-point pre-interpretation gate for seismic-to-well tie.

        Before interpreting a tie, an agent must answer 25 questions covering:
        conventions, datum, calibration, data quality, signal, processing,
        geology, rock physics, resolution, analog, and decision context.

        Same data, different burden of proof: a tie for horizon calibration
        needs less than a tie for reserves booking.

        Returns GO / HOLD / VOID verdict with specific blockers.
        The checklist is not bureaucracy. It is the metabolizer's intake valve.
        """
        try:
            from geox_core.schemas.tie_preflight import run_tie_preflight

            # Parse answers: "1=YES,2=ZERO-PHASE,3=MSL,..."
            answers_dict: dict[int, str] = {}
            if answers:
                for pair in answers.split(","):
                    pair = pair.strip()
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        try:
                            answers_dict[int(k.strip())] = v.strip()
                        except ValueError:
                            pass

            result = run_tie_preflight(
                well_name=well_name,
                decision_context=decision_context,
                answers=answers_dict,
                session_id=session_id,
            )

            return {
                "status": "success",
                "tool": "geox_tie_preflight",
                **result,
            }
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_tie_preflight", source_organ="geox")

    # ── GEOX 1D MCP surface (Orthogonal Base) ─────────────────────────────

    # ZEN 2026-07-11 G1: merged into geox_seismic_compute mode — geox_well_time_depth_calibrate
    async def _geox_well_time_depth_calibrate(
        las_path: str,
        checkshot_path: str,
        method: str = "linear",
        velocity_bounds: list[float] | None = None,
        residual_threshold_pct: float = 10.0,
        well_id: str = "",
        actor_id: str = "geox_1d_mcp",
    ) -> dict[str, Any]:
        """Calibrate time–depth using LAS + checkshot with PhysicsGuard.

        Methods: linear | polynomial | vo_k | layer_cake.
        Returns JSON TDFitResult + geox:// resource URI (DRAFT_ONLY receipt).
        """
        try:
            from geox_mcp.tools.well_1d_surface import geox_well_time_depth_calibrate

            return await geox_well_time_depth_calibrate(
                las_path=las_path,
                checkshot_path=checkshot_path,
                method=method,  # type: ignore[arg-type]
                velocity_bounds=velocity_bounds,
                residual_threshold_pct=residual_threshold_pct,
                well_id=well_id,
                actor_id=actor_id,
            )
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_well_time_depth_calibrate", source_organ="geox")

    # ZEN 2026-07-11 G1: merged into geox_seismic_compute mode — geox_well_seismic_mistie_rms
    async def _geox_well_seismic_mistie_rms(
        synthetic_trace: list[float],
        seismic_trace: list[float],
        dt_ms: float = 4.0,
        time_window_ms: list[float] | None = None,
        threshold_ms: float = 25.0,
        max_lag_ms: float = 50.0,
        well_id: str = "WELL",
        actor_id: str = "geox_1d_mcp",
    ) -> dict[str, Any]:
        """Phase 3 RMS mistie gate — synthetic vs seismic. Verdict SEAL|HOLD|VOID.

        Hard default threshold 25 ms. Absolute ms, not sample units.
        """
        try:
            from geox_mcp.tools.well_1d_surface import geox_well_seismic_mistie_rms

            return await geox_well_seismic_mistie_rms(
                synthetic_trace=synthetic_trace,
                seismic_trace=seismic_trace,
                dt_ms=dt_ms,
                time_window_ms=time_window_ms,
                threshold_ms=threshold_ms,
                max_lag_ms=max_lag_ms,
                well_id=well_id,
                actor_id=actor_id,
            )
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_well_seismic_mistie_rms", source_organ="geox")

    # ZEN 2026-07-11 G1: merged into geox_seismic_compute mode — geox_wavelet_extract_least_squares
    async def _geox_wavelet_extract_least_squares(
        reflectivity_series: list[float],
        seismic_trace: list[float],
        wavelet_length_ms: float = 120.0,
        epsilon: float = 1e-3,
        dt_ms: float = 4.0,
        well_id: str = "WELL",
        actor_id: str = "geox_1d_mcp",
    ) -> dict[str, Any]:
        """Phase 4 Wiener least-squares wavelet extraction from r and seismic."""
        try:
            from geox_mcp.tools.well_1d_surface import geox_wavelet_extract_least_squares

            return await geox_wavelet_extract_least_squares(
                reflectivity_series=reflectivity_series,
                seismic_trace=seismic_trace,
                wavelet_length_ms=wavelet_length_ms,
                epsilon=epsilon,
                dt_ms=dt_ms,
                well_id=well_id,
                actor_id=actor_id,
            )
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_wavelet_extract_least_squares", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_benchmark_001", annotations=_geox_annotations("geox_benchmark_001"))
    async def _geox_benchmark_001(
        scenario: str = "mistie_hold",
        write_fixtures_dir: str = "",
        include_full_workflow: bool = True,
        enforce_orthogonal_base: bool = True,
        las_path: str = "",
        use_real_las: bool = False,
        checkshot_path: str = "",
        tops_path: str = "",
        seismic_path: str = "",
    ) -> dict[str, Any]:
        """GEOX-001: Well-Seismic Truth Test — Model Deserves To Live.

        Orthogonal Base first (GENESIS/013):
          well_ingest → well_qc → tie_preflight → well_tie → tie_receipt
        then Law plane verdict. Cognitive/Dimensional tools blocked until base.

        Thesis: If the well does not tie, the model does not get to speak as truth.
        """
        try:
            from geox_mcp.tools.benchmark_001 import geox_benchmark_001

            if scenario not in ("good_tie", "mistie_hold", "kill_contradiction"):
                return {
                    "status": "error",
                    "tool": "geox_benchmark_001",
                    "error": f"Unknown scenario '{scenario}'",
                }
            return await geox_benchmark_001(
                scenario=scenario,  # type: ignore[arg-type]
                write_fixtures_dir=write_fixtures_dir,
                include_full_workflow=include_full_workflow,
                enforce_orthogonal_base=enforce_orthogonal_base,
                las_path=las_path,
                use_real_las=use_real_las,
                checkshot_path=checkshot_path,
                tops_path=tops_path,
                seismic_path=seismic_path,
            )
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_benchmark_001", source_organ="geox")

    # ── WELL-TIE P2–P4: Time-Depth Calibrate · Mistie RMS · Wavelet Extract ────

    # DEREGISTERED 2026-07-10 — # ZEN 2026-07-11 G1: merged into geox_seismic_compute — geox_well_time_depth_calibrate
    async def _well_time_depth_calibrate(
        las_path: str,
        checkshot_path: str | None = None,
        checkshot_data: str | None = None,
        method: str = "linear",
        velocity_bounds: str | None = None,
        residual_threshold_pct: float = 10.0,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Calibrate time-depth using LAS + checkshot with PhysicsGuard.

        Accepts checkshot as a file path (JSON or CSV) or inline JSON string.
        Dispatches to 4 fitters: linear, polynomial, vo_k, layer_cake.
        Returns TDFitResult with equation, coefficients, residuals, extrapolation_risk.
        """
        try:
            import json
            from geox_mcp.federation_safety import classify_error
            from geox_core.core.welltie_mcp import compute_td_calibrate

            cs_data = None
            if checkshot_data:
                cs_data = json.loads(checkshot_data)
                if isinstance(cs_data, dict) and "checkshots" in cs_data:
                    cs_data = cs_data["checkshots"]
                if not isinstance(cs_data, list):
                    cs_data = [cs_data]

            vb = (1500.0, 6000.0)
            if velocity_bounds:
                parts = json.loads(velocity_bounds) if isinstance(velocity_bounds, str) else velocity_bounds
                if len(parts) >= 2:
                    vb = (float(parts[0]), float(parts[1]))

            result = compute_td_calibrate(
                las_path=las_path,
                checkshot_path=checkshot_path,
                checkshot_data=cs_data,
                method=method,
                velocity_bounds=vb,
                residual_threshold_pct=residual_threshold_pct,
            )
            return {"status": "success", "tool": "geox_well_time_depth_calibrate", **result}
        except Exception as e:
            return classify_error(e, source_tool="geox_well_time_depth_calibrate", source_organ="geox")

    # DEREGISTERED 2026-07-10 — # ZEN 2026-07-11 G1: merged into geox_seismic_compute — geox_well_seismic_mistie_rms
    async def _well_seismic_mistie_rms(
        well_name: str,
        synthetic_trace: list[float],
        seismic_trace: list[float],
        dt_ms: float,
        time_window_ms: list[float],
        threshold_ms: float = 25.0,
        max_lag_ms: float = 50.0,
        checkshot_ref: str | None = None,
        polarity: str = "SEG_NORMAL",
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Falsification gate: RMS mistie between synthetic and seismic.

        Computes cross-correlation, finds optimal lag, computes RMS after shift.
        Constitutional gate: RMS > threshold_ms → HOLD.
        25 ms threshold based on tuning thickness resolution limit.
        """
        try:
            from geox_mcp.federation_safety import classify_error
            from geox_core.schemas.mistie_rms import MistieRMSInput
            from geox_core.core.welltie_mcp import compute_mistie_rms

            inp = MistieRMSInput(
                well_name=well_name,
                synthetic_trace=synthetic_trace,
                seismic_trace=seismic_trace,
                dt_ms=dt_ms,
                time_window_ms=time_window_ms,
                threshold_ms=threshold_ms,
                max_lag_ms=max_lag_ms,
                checkshot_ref=checkshot_ref,
                polarity=polarity,
                session_id=session_id,
            )
            result = compute_mistie_rms(inp)
            return {"status": "success", "tool": "geox_well_seismic_mistie_rms", **result}
        except Exception as e:
            return classify_error(e, source_tool="geox_well_seismic_mistie_rms", source_organ="geox")

    # DEREGISTERED 2026-07-10 — # ZEN 2026-07-11 G1: merged into geox_seismic_compute — geox_wavelet_extract_least_squares
    async def _wavelet_extract_least_squares(
        well_name: str,
        reflectivity_series: list[float],
        seismic_trace: list[float],
        dt_ms: float,
        wavelet_length_ms: float = 100.0,
        epsilon: float = 0.01,
        max_condition_number: float = 100.0,
        min_correlation_after: float = 0.60,
        checkshot_ref: str | None = None,
        polarity: str = "SEG_NORMAL",
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Extract wavelet from earth — Wiener least-squares spectral division.

        Math: W(ω) = S(ω)·R*(ω)/(|R(ω)|²+ε).
        Physical constraints: compact support, causality, phase classification.
        Constitutional gate: condition_number > 10× threshold → VOID.
        """
        try:
            from geox_mcp.federation_safety import classify_error
            from geox_core.schemas.wavelet_extract import WaveletExtractInput
            from geox_core.core.welltie_mcp import extract_wavelet_least_squares

            inp = WaveletExtractInput(
                well_name=well_name,
                reflectivity_series=reflectivity_series,
                seismic_trace=seismic_trace,
                dt_ms=dt_ms,
                wavelet_length_ms=wavelet_length_ms,
                epsilon=epsilon,
                max_condition_number=max_condition_number,
                min_correlation_after=min_correlation_after,
                checkshot_ref=checkshot_ref,
                polarity=polarity,
                session_id=session_id,
            )
            result = extract_wavelet_least_squares(inp)
            return {"status": "success", "tool": "geox_wavelet_extract_least_squares", **result}
        except Exception as e:
            return classify_error(e, source_tool="geox_wavelet_extract_least_squares", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_3d_model_build", annotations=_geox_annotations("geox_3d_model_build"))
    async def _geox_3d_model_build(
        model_json_path: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """3D structural model via GemPy — implicit geological modeling.

        Builds a 3D geological model from 2D interpretation picks.
        Requires a JSON model definition with surfaces, orientations,
        and extent. Outputs 3D visualization and structural model.

        This is the STRUCTURAL_VALIDATION layer — converts 2D picks
        into 3D geological volumes for structural plausibility testing.
        """
        try:
            import sys
            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_3d_modeling_gempy import run_gempy_3d_model

            result = run_gempy_3d_model(model_json_path, output_dir)
            return {
                "status": "success",
                "tool": "geox_3d_model_build",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_3d_model_build", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_wealth_bridge_run", annotations=_geox_annotations("geox_wealth_bridge_run"))
    async def _geox_wealth_bridge_run(
        gempy_manifest_path: str,
        well_data: dict[str, Any] | None = None,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """GEOX → WEALTH capital bridge — economic evaluation of geological models.

        Takes GemPy 3D model manifest and optional well data,
        computes prospect volumetrics, and routes to WEALTH organ
        for NPV/IRR/EMV evaluation.

        Sovereign authority required for capital decisions.
        WEALTH computes. arifOS judges. Arif decides.
        """
        try:
            import sys
            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_wealth_bridge import run_wealth_bridge

            result = run_wealth_bridge(
                gempy_manifest_path, grid_path="", well_manifest_path="", output_dir=output_dir or "/tmp/geox_wealth"
            )
            return {
                "status": "success",
                "tool": "geox_wealth_bridge_run",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_wealth_bridge_run", source_organ="geox")

    # ── GEOLOGICAL MAP PIPELINE — 4-Verb Chain (2026-07-02 FORGE) ────────────

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_layers_list", annotations=_geox_annotations("geox_map_layers_list"))
    async def _map_layers_list(
        bbox: list[float],
        theme: str | None = None,
        include_unavailable: bool = False,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """List available GEOX map layers for a bounding box. Returns layer catalogue with metadata, truth classes, and availability."""
        from geox_mcp.tools.earth_map import geox_map_layers_list as _impl

        return await _auto_call(_impl, {"bbox": bbox, "theme": theme, "include_unavailable": include_unavailable})

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_scene_plan", annotations=_geox_annotations("geox_map_scene_plan"))
    async def _map_scene_plan(
        bbox: list[float],
        layer_ids: list[str] | None = None,
        theme: str | None = None,
        map_purpose: str = "context",
        style_profile: str = "geox_regional_clean_v1",
        crs: str = "EPSG:4326",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a deterministic visual recipe for a geological map scene. No image rendered yet — inspect this plan before rendering."""
        from geox_mcp.tools.earth_map import geox_map_scene_plan as _impl

        return await _auto_call(
            _impl,
            {
                "bbox": bbox,
                "layer_ids": layer_ids,
                "theme": theme,
                "map_purpose": map_purpose,
                "style_profile": style_profile,
                "crs": crs,
            },
        )

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_render_preview", annotations=_geox_annotations("geox_map_render_preview"))
    async def _map_render_preview(
        scene_id: str | None = None,
        bbox: list[float] | None = None,
        layer_ids: list[str] | None = None,
        theme: str | None = None,
        width_px: int = 1024,
        height_px: int = 768,
        style_profile: str = "geox_regional_clean_v1",
        format: str = "image/png",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Render a static map preview from a scene plan or bbox. Images <300KB returned as inline base64."""
        from geox_mcp.tools.earth_map import geox_map_render_preview as _impl

        return await _auto_call(
            _impl,
            {
                "scene_id": scene_id,
                "bbox": bbox,
                "layer_ids": layer_ids,
                "theme": theme,
                "width_px": width_px,
                "height_px": height_px,
                "style_profile": style_profile,
                "format": format,
            },
        )

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_export_package", annotations=_geox_annotations("geox_map_export_package"))
    async def _map_export_package(
        scene_plan_id: str,
        formats: list[str] | None = None,
        include_sources: bool = False,
        include_provenance: bool = True,
        review_mode: str = "draft",
        output_dir: str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a governed export package with map assets, metadata, and provenance sidecars. Final step of the map verb chain."""
        from geox_mcp.tools.earth_map import geox_map_export_package as _impl

        return await _auto_call(
            _impl,
            {
                "scene_plan_id": scene_plan_id,
                "formats": formats,
                "include_sources": include_sources,
                "include_provenance": include_provenance,
                "review_mode": review_mode,
                "output_dir": output_dir,
            },
        )

    # ── BID ROUND SCREENER — MBR 2026 (2026-07-09) ─────────────────────────
    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_bid_round_screener", annotations=_geox_annotations("geox_bid_round_screener"))
    async def _bid_round_screener(
        arguments: dict[str, Any] | str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """MBR 2026 Multi-Block Bid Round Screener — rank N blocks into BID/PARTNER/NO_BID matrix.

        Takes all block opportunities at once, scores each on geological risk,
        capital requirement, evidence strength, and fiscal attractiveness.
        F1-F13 floor compliance inline. Advisory only (F13 SOVEREIGN).
        """
        from geox_mcp.tools.bid_round_screener import geox_bid_round_screener as _impl

        return await _auto_call(
            _impl,
            dict(_parse_str_arguments(arguments) or {}),
        )

    # ── COLLISION ZONE — Two Oceanics Physics (Phase Zen, 2026-07-10) ────────
    # Implements collision zone physics from Arif's Sabah Eureka Ledger v1.0.
    # Two blocks (accretionary + rifted), suture, accommodation ratio, loading ratio.
    # Detects 6 Eureka signatures. Margin Principle embedded.
    # DITEMPA BUKAN DIBERI.

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_collision_zone", annotations=_geox_annotations("geox_collision_zone"))
    async def _collision_zone(
        domain_a: dict[str, Any],
        domain_b: dict[str, Any],
        suture_name: str = "Suture",
        duration_ma: float = 15.0,
        bypass_fraction: float = 0.0,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Analyze a collision zone using Two Oceanics physics.

        Computes accommodation_ratio, loading_ratio, mass_deficit_pct from
        two lithospheric blocks with different subsidence physics.

        Detects Eureka signatures: TWO_OCEANICS, MFS_ASYMMETRY, LOADING_PULSE,
        MASS_DEFICIT, SUTURE_SINK, PROSPECT_BIFURCATION.

        Example (Sabah):
          domain_a = {"name": "Kinabalu", "initial_subsidence_km": 4.0,
                      "loading_rate_m_myr": 400.0, "has_mfs": true}
          domain_b = {"name": "Layang-Layang", "initial_subsidence_km": 2.0,
                      "thermal_rate_mm_yr": 0.20, "has_mfs": false}
          suture_name = "Sabah Trough"
        """
        from geox_mcp.tools.collision_zone import compute_collision

        return compute_collision(
            domain_a=domain_a,
            domain_b=domain_b,
            suture_name=suture_name,
            duration_ma=duration_ma,
            bypass_fraction=bypass_fraction,
        )

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_collision_chronology", annotations=_geox_annotations("geox_collision_chronology"))
    async def _collision_chronology(
        events: list[dict[str, Any]],
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Compute collision chronology from a sequence of tectonic events.

        Takes a list of {age_ma, event_name, description} and computes
        collision duration, event ordering, and the key insight:
        "The collision is not an event. It is a 15 Myr sequence, still finishing."

        Example:
          events = [{"age_ma": 65, "event_name": "DG Rift", "description": "..."},
                    {"age_ma": 21, "event_name": "Collision", "description": "..."},
                    {"age_ma": 7,  "event_name": "Kinabalu Granite", "description": "..."}]
        """
        from geox_mcp.tools.collision_zone import compute_collision_chronology

        return compute_collision_chronology(events)

    # ── DOMAIN EVIDENCE GATE — geox_diagnose (Phase Zen, 2026-07-10) ──────────
    # Pre-flight check: "Does GEOX have evidence for this question?"
    # Returns NO_DOMAIN_EVIDENCE / PARTIAL / READY.
    # When NO_DOMAIN_EVIDENCE: use ChatGPT, not GEOX.

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_diagnose", annotations=_geox_annotations("geox_diagnose"))
    async def _diagnose(
        query: str = "",
        domain: str = "",
        location: str = "",
        basin: str = "",
        required_evidence: list[str] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Check if GEOX has domain evidence for a question.

        Routes questions to either GEOX (evidence analysis) or ChatGPT (general knowledge).

        Returns NO_DOMAIN_EVIDENCE when GEOX has no relevant basin profiles,
        literature, or well data — use ChatGPT for general knowledge questions.

        Returns READY when evidence is sufficient for geox_basin, geox_evidence,
        or geox_contrast_detect analysis.
        """
        from geox_mcp.tools.diagnose import diagnose

        return diagnose(
            query=query,
            domain=domain,
            location=location,
            basin=basin,
            required_evidence=required_evidence,
        )

    # ── EARTH OBSERVE — 24-in-1 consolidated surface (Zen, 2026-07-10) ──────
    # One tool. 24 modes. Replaces 24 individual Earth data fetchers.
    # earthquake, relief, bathymetry, heatflow, stress, geochem,
    # plate_reconstruct, paleomag, gravity, ocean, erddap, climate,
    # hydrology, satellite, uk_petroleum, geology_map, space_weather,
    # nsta, context_at_location, isitwater, gravity_screen,
    # judgment_preflight, interpolate_grid, report_to_workflow

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_observe", annotations=_geox_annotations("geox_observe"))
    async def _observe(
        mode: str,
        query: str = "",
        lat: float | None = None,
        lng: float | None = None,
        bbox: list[float] | None = None,
        limit: int = 10,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Unified Earth observation — 24 data dimensions in one tool.

        Modes: earthquake, relief, bathymetry, heatflow, stress, geochem,
        plate_reconstruct, paleomag, gravity, ocean, erddap, climate,
        hydrology, satellite, uk_petroleum, geology_map, space_weather,
        nsta, context_at_location, isitwater, gravity_screen,
        judgment_preflight, interpolate_grid, report_to_workflow
        """
        from geox_mcp.tools.observe import geox_observe as _impl

        return await _impl(
            mode=mode,
            query=query,
            lat=lat,
            lng=lng,
            bbox=bbox,
            limit=limit,
        )

    # ═══════════════════════════════════════════════════════════════════════════════
    # BASIN ANALYSIS ENGINES (4) — Phase 0 (2026-07-10)
    # Physics-first basin analysis: backstripping, mass balance, thermal maturity,
    # claim graph evaluation. Complements simulate_* with backward reconstruction.
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(name="geox_basin_backstrip", annotations=_geox_annotations("geox_basin_backstrip"))
    async def _basin_backstrip(
        well_ref: str,
        stratigraphic_ages: list[dict[str, Any]],
        lithology_model: dict[str, Any] | None = None,
        palaeobathymetry_model: dict[str, Any] | None = None,
        sea_level_model_ref: str = "",
        water_density_kg_m3: float = 1030.0,
        mantle_density_kg_m3: float = 3300.0,
        uncertainty_realizations: int = 1000,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Reconstruct tectonic and total subsidence through time from validated well stratigraphy.

        Uses Steckler & Watts (1978) Airy isostasy + Sclater & Christie (1980) decompaction.
        """
        from geox_mcp.tools.basin_engines.backstrip_tool import geox_basin_backstrip as _impl

        return await _impl(
            well_ref=well_ref,
            stratigraphic_ages=stratigraphic_ages,
            lithology_model=lithology_model or {},
            palaeobathymetry_model=palaeobathymetry_model or {},
            sea_level_model_ref=sea_level_model_ref,
            water_density_kg_m3=water_density_kg_m3,
            mantle_density_kg_m3=mantle_density_kg_m3,
            uncertainty_realizations=uncertainty_realizations,
        )

    @mcp.tool(name="geox_sediment_mass_balance", annotations=_geox_annotations("geox_sediment_mass_balance"))
    async def _sediment_mass_balance(
        basin_name: str,
        source_eroded_km3: float,
        source_density_kg_m3: float = 2650.0,
        preserved_volumes: list[dict[str, Any]] | None = None,
        bypassed_km3: float = 0.0,
        dissolved_km3: float = 0.0,
        routing_efficiency: float | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Compute source-to-sink sediment mass balance with uncertainty.

        Physics: Peters (2012) sediment cycling framework.
        """
        from geox_mcp.tools.basin_engines.mass_balance_tool import geox_sediment_mass_balance as _impl

        return await _impl(
            basin_name=basin_name,
            source_eroded_km3=source_eroded_km3,
            source_density_kg_m3=source_density_kg_m3,
            preserved_volumes=preserved_volumes,
            bypassed_km3=bypassed_km3,
            dissolved_km3=dissolved_km3,
            routing_efficiency=routing_efficiency,
        )

    @mcp.tool(name="geox_thermal_maturity_history", annotations=_geox_annotations("geox_thermal_maturity_history"))
    async def _thermal_maturity_history(
        well_ref: str,
        burial_history: dict[str, Any],
        heat_flow_history: dict[str, Any] | None = None,
        surface_temp_c: float = 20.0,
        geothermal_gradient_c_km: float = 30.0,
        time_step_myr: float = 1.0,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Model burial + heat flow + maturity through time.

        Uses EasyRo (Sweeney & Burnham 1990) + TTI (Lopatin 1971).
        """
        from geox_mcp.tools.basin_engines.thermal_tool import geox_thermal_maturity_history as _impl

        return await _impl(
            well_ref=well_ref,
            burial_history=burial_history,
            heat_flow_history=heat_flow_history,
            surface_temp_c=surface_temp_c,
            geothermal_gradient_c_km=geothermal_gradient_c_km,
            time_step_myr=time_step_myr,
        )

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_claim_graph_evaluate", annotations=_geox_annotations("geox_claim_graph_evaluate"))
    async def _claim_graph_evaluate(
        claims: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        initial_verdicts: dict[str, str] | None = None,
        failure_propagation: str = "cascade",
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate a claim dependency graph.

        Supports AND/OR/WEIGHTED dependency types and failure propagation.
        """
        from geox_mcp.tools.basin_engines.claim_graph_tool import geox_claim_graph_evaluate as _impl

        return await _impl(
            claims=claims,
            edges=edges,
            initial_verdicts=initial_verdicts,
            failure_propagation=failure_propagation,
        )

    # ═══════════════════════════════════════════════════════════════════════════════
    # MACROSTRAT UPSTREAM PROXY — geox_query_macrostrat
    # Canonical upstream proxy for Macrostrat geological database.
    # Registered as a dedicated tool (not a basin mode) per Option B blueprint.
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="geox_query_macrostrat",
        annotations=_geox_annotations("geox_query_macrostrat"),
    )
    async def _geox_query_macrostrat(
        arguments: dict[str, Any] | str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Query the Macrostrat geological database for regional stratigraphy, lithology, and age data.

        Macrostrat provides regional surface geology — lithology, age, and
        stratigraphic columns derived from published geological maps.
        Data is rung 2 (PROCESS_HYPOTHESIS), not subsurface truth.

        Modes: units, columns, sources, fossils, defs, measurements,
               lithologies, environments, intervals, strat_names, map_units

        Attribution: CC-BY-4.0 — Peters et al. (2018) doi:10.17605/OSF.IO/YNAXW

        Use when: the agent needs surface geology, lithology columns, or
        stratigraphic data from the Macrostrat database for a geographic region.
        """
        arguments = _parse_str_arguments(arguments) or {}
        if isinstance(arguments, dict):
            from geox_mcp.tools.macrostrat_unified import geox_query_macrostrat as _impl

            return await _impl(session_id=session_id, **arguments)
        return {
            "ok": False,
            "tool": "geox_query_macrostrat",
            "origin": "UPSTREAM_MACROSTRAT",
            "reason_code": "INVALID_ARGUMENTS",
            "error": f"Expected dict arguments, got {type(arguments).__name__}",
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # MCP APP VISUAL TOOLS — Main server registration (Fix HOLD-2026-07-11)
    # These tools are also on the witness sub-server via mcp.mount(), but mount does
    # NOT composite annotations/AppConfig into the main server's tools/list.
    # Registering here ensures they appear in tools/list with ui.resourceUri bindings.
    # ═══════════════════════════════════════════════════════════════════════════════

    # PLAN-2026-07-12-GEOX-MCP-APP-SLICE-001 option A — well-desk open (P0)
    try:
        from fastmcp.apps import AppConfig as _AppConfig

        _well_desk_app = _AppConfig(
            resourceUri="ui://geox/well-desk",
            visibility=["app", "model"],
        )
    except Exception:  # pragma: no cover
        _well_desk_app = None

    @mcp.tool(
        name="geox_well_desk_open",
        annotations={
            "title": "Well Desk Open",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        meta={
            "ui": {
                "resourceUri": "ui://geox/well-desk",
                "visibility": ["app", "model"],
            }
        },
        **({"app": _well_desk_app} if _well_desk_app is not None else {}),
    )
    async def _well_desk_open(
        well_id: str,
        mode: str = "summary",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """OBSERVE · Open GEOX well-desk interactive view (SEP-1865).

        Read-only operator summary. Hosts that support MCP Apps open
        ui://geox/well-desk (P0 single-file shell). Hosts without UI still
        receive structuredContent + text. No mutation. No secrets in UI.

        Use when: operator wants interactive well-desk / well summary view.
        Do not use when: ingesting new LAS (use geox_well_ingest) or deep QC
        (use geox_well_qc).
        """
        from datetime import UTC, datetime

        _mode = (mode or "summary").strip().lower()
        if _mode not in ("summary", "tracks"):
            _mode = "summary"
        _wid = (well_id or "").strip()
        if not _wid:
            return {
                "ok": False,
                "isError": True,
                "error_class": "MISSING_REQUIRED_FIELD",
                "message": "well_id is required",
                "tool": "geox_well_desk_open",
            }

        # Lightweight OBSERVE summary — no file IO required for P0 path proof.
        # Future: hydrate from geox_well_qc / artifact store when well_id resolves.
        summary = {
            "well_id": _wid,
            "mode": _mode,
            "band": "UNKNOWN",
            "note": (
                "P0 operator shell — interactive HTML via host iframe; "
                "full multi-track desk is GEOX_WELL_DESK_UI=full."
            ),
            "views": (
                ["composite_log", "summary_card"]
                if _mode == "summary"
                else ["composite_log", "tracks", "crossplot_placeholder"]
            ),
            "patterns_stolen": [
                "instant well identity card",
                "mode switch summary|tracks",
                "host-mediated refresh only",
            ],
        }
        text = (
            f"Well-desk open: well_id={_wid} mode={_mode}. "
            f"UI resource: ui://geox/well-desk. "
            f"Band={summary['band']} (no vitals invented)."
        )
        return {
            "ok": True,
            "tool": "geox_well_desk_open",
            "well_id": _wid,
            "mode": _mode,
            "band": summary["band"],
            "summary": summary,
            "ui": {
                "resourceUri": "ui://geox/well-desk",
                "protocol": "SEP-1865",
                "p0_shell": True,
            },
            "session_id": session_id,
            "actor_id": actor_id,
            "trace_id": trace_id,
            "epistemic": {
                "layer": "OBS",
                "confidence_cap": 0.7,
                "note": "Identity card only until artifact hydrate is wired",
            },
            "ts": datetime.now(UTC).isoformat(),
            "content_text": text,
            "w0": "OPERATOR_VETO_INTACT",
            "final_authority": "ARIF",
        }

    @mcp.tool(
        name="geox_map_context_scene",
        annotations={
            "title": "Map Context Scene",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
            "ui": {"resourceUri": "ui://geox/workspace-v1.html"},
        },
    )
    async def _map_context_scene(
        bbox: list[float],
        mode: str = "bbox_context",
        crs: str = "EPSG:4326",
        vp_slice_inline: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Spatial bbox context, CRS checks, and causal scene rendering.

        Modes:
            - bbox_context: Return bbox summary and scene metadata (default).
            - render_scene: Render causal scene map.
            - render_geojson: Return GeoJSON FeatureCollection with selectable geological features.
            - scene_summary: Summarize geological scene context.
            - crs_check: Validate and transform CRS.
            - coordinate_guardrail: Check coordinates against basin boundaries.
            - georeference_map: Georeference raster or vector data.

        When this tool is called, the MCP host opens the GEOX Workspace
        (ui://geox/workspace-v1.html) in a sandboxed iframe for read-only evidence review.

        Use when: the user provides a bounding box, coordinates, or asks for
        geological context of a region. Also used for rendering geological maps
        with selectable features.
        """
        from geox_mcp.tools.map_context import geox_map_context_scene as _impl

        # ── DEBUG (2026-07-11): verify identity propagation through bridge ──
        import logging

        _log = logging.getLogger("geox.canonical.map_context")
        _log.warning(f"IDENTITY_ARRIVAL: session_id={session_id!r} actor_id={actor_id!r} trace_id={trace_id!r}")

        return await _impl(
            bbox=bbox,
            mode=mode,
            crs=crs,
            vp_slice_inline=vp_slice_inline,
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    @mcp.tool(
        name="geox_well_desk_publish",
        annotations={
            "title": "Well Desk Publish Image",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def _well_desk_publish(
        well_id: str,
        image_base64: str,
        metadata: dict[str, Any],
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """MUTATE · Publish a rendered well-desk image with embedded metadata.

        Accepts the base64-encoded PNG and its associated metadata, saves it
        to /root/GEOX/data/renders/, and seals the hash to the VAULT999
        seal chain.

        Use when: the user clicks 'Publish Image' inside the Well-Desk UI.
        """
        import base64
        import hashlib
        import json
        from datetime import datetime, UTC
        from pathlib import Path

        # 1. Clean input
        _wid = (well_id or "").strip()
        if not _wid:
            return {"ok": False, "isError": True, "message": "well_id is required"}

        # 2. Decode image
        try:
            img_bytes = base64.b64decode(image_base64)
        except Exception as e:
            return {"ok": False, "isError": True, "message": f"Failed to decode base64: {e}"}

        if not img_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return {"ok": False, "isError": True, "message": "Invalid PNG signature"}

        # 3. Save file
        renders_dir = Path(os.environ.get("GEOX_RENDERS_DIR", "/root/GEOX/data/renders"))
        renders_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"well-desk-{_wid}-{timestamp}.png"
        filepath = renders_dir / filename
        filepath.write_bytes(img_bytes)

        # 4. Hash and Seal to VAULT999
        image_sha = f"sha256:{hashlib.sha256(img_bytes).hexdigest()}"
        seal_token = f"SEAL-IMG-{hashlib.sha256(img_bytes).hexdigest()[:16].upper()}"

        seal_entry = {
            "entry_type": "IMAGE_SEAL",
            "token": seal_token,
            "well_id": _wid,
            "image_sha256": image_sha,
            "filename": filename,
            "filepath": str(filepath),
            "issued_at": datetime.now(UTC).isoformat() + "Z",
            "actor": actor_id or "ARIF",
            "session_id": session_id or "geox_session",
            "metadata": metadata,
            "epoch": datetime.now(UTC).isoformat() + "Z",
        }

        # IMAGE_SEAL is a side ledger — NEVER write seal_chain.jsonl / seal_chain_head.json
        # (those are the constitutional hash chain; IMAGE_SEAL pollution broke head 2026-07-12).
        vault_dir = Path(os.environ.get("GEOX_VAULT_IMAGE_DIR", "/root/.local/share/arifos/vault999"))
        vault_dir.mkdir(parents=True, exist_ok=True)
        chain_path = vault_dir / "image_seal_chain.jsonl"
        head_path = vault_dir / "image_seal_head.json"

        # Safe append with lock
        import fcntl
        lock_path = vault_dir / ".image_seal.lock"
        with open(lock_path, "a") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            try:
                # Append to image seal side-chain
                with open(chain_path, "a") as f:
                    f.write(json.dumps(seal_entry) + "\n")
                    f.flush()
                with open(head_path, "w") as f:
                    json.dump(seal_entry, f)
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)

        # 5. Vault witness - append IMAGE_SEAL to constitutional outcomes.jsonl
        try:
            outcomes_path = vault_dir / "outcomes.jsonl"
            vault_entry = {
                "ts": datetime.now(UTC).isoformat(),
                "event": "IMAGE_SEAL",
                "actor": actor_id or "ARIF",
                "session": session_id or "geox_session",
                "tool": "geox_well_desk_publish",
                "verdict": "SEAL",
                "elapsed_ms": 0,
                "image_sha256": image_sha,
                "well_id": _wid,
                "filename": filename,
                "seal_token": seal_token,
            }
            with open(lock_path, "a") as lockf:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
                try:
                    with open(outcomes_path, "a") as f:
                        f.write(json.dumps(vault_entry) + "\n")
                        f.flush()
                finally:
                    fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
        except Exception as vault_err:
            # Non-fatal - side ledger already written
            text += f" (vault witness failed: {vault_err})"

        text = f"Image published successfully. Well: {_wid}. Path: {filepath}. Seal: {seal_token}"

        # Return to client/conversation
        return {
            "ok": True,
            "tool": "geox_well_desk_publish",
            "well_id": _wid,
            "seal_token": seal_token,
            "image_sha256": image_sha,
            "filepath": str(filepath),
            "metadata": metadata,
            "content_text": text,
        }

    @mcp.tool(
        name="geox_render_well_panel",
        annotations={
            "title": "Render Well Panel",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def _render_well_panel(
        well_id: str,
        depth_top: float | None = None,
        depth_base: float | None = None,
        curves: list[str] | None = None,
        las_path: str | None = None,
        interpret: bool = True,
        rw: float = 0.03,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """OBSERVE · Render well-log panel with petrophysics + earth meaning.

        Default interpret=True: open LAS → Vsh/φe/Sw (DERIVED) + GR motif and
        reservoir/fluid read (INTERPRETED) on multi-track PNG with meaning panel.
        Resolves Equinor Volve 15/9-19 and Marmousi demo LAS by well_id or las_path.

        Use when: user wants a well panel, petrophysical interpretation, or earth
        meaning decoded from open-source or provided LAS.
        """
        if interpret:
            try:
                from geox_mcp.render_well_panel_petro import render_interpreted_panel

                return render_interpreted_panel(
                    well_id=well_id,
                    depth_top=depth_top,
                    depth_base=depth_base,
                    las_path=las_path,
                    rw=rw,
                    session_id=session_id,
                    actor_id=actor_id,
                )
            except Exception as e:
                return {
                    "ok": False,
                    "isError": True,
                    "message": f"interpreted panel failed: {type(e).__name__}: {e}",
                    "tool": "geox_render_well_panel",
                }

        # Minimal scaffold fallback when interpret=False and no LAS workflow
        import io
        import base64
        import hashlib
        import math
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        from datetime import datetime, UTC
        from pathlib import Path
        from PIL import Image as PILImage
        from PIL.PngImagePlugin import PngInfo

        _wid = (well_id or "").strip() or "UNKNOWN"
        d0 = float(depth_top if depth_top is not None else 3000.0)
        d1 = float(depth_base if depth_base is not None else 4000.0)
        d = np.arange(d0, d1 + 0.5, 0.5)
        frac = (d - d0) / max(d1 - d0, 1e-9)
        fig, axes = plt.subplots(1, 3, figsize=(8, 7), sharey=True, facecolor="#0f0f1a")
        fig.suptitle(f"GEOX scaffold — {_wid}", color="white")
        for ax, v, col, title in zip(
            axes,
            (30 + 80 * np.sin(frac * math.pi * 3), 10 ** (0.5 + frac), 0.2 + 0.1 * np.sin(frac * math.pi)),
            ("#f1c40f", "#2ecc71", "#3498db"),
            ("GR syn", "RT syn", "φ syn"),
        ):
            ax.plot(v, d, color=col)
            ax.set_title(title, color="white")
            ax.set_facecolor("#0f0f1a")
            ax.tick_params(colors="white")
            ax.invert_yaxis()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, facecolor="#0f0f1a")
        plt.close()
        renders = Path(os.environ.get("GEOX_RENDERS_DIR", "/root/GEOX/data/renders"))
        renders.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        fp = renders / f"well-panel-scaffold-{_wid}-{ts}.png"
        img = PILImage.open(io.BytesIO(buf.getvalue()))
        meta = PngInfo()
        meta.add_text("provenance", "scaffold")
        meta.add_text("well_id", _wid)
        img.save(fp, "PNG", pnginfo=meta)
        raw = fp.read_bytes()
        sha = f"sha256:{hashlib.sha256(raw).hexdigest()}"
        tok = f"SEAL-IMG-{hashlib.sha256(raw).hexdigest()[:16].upper()}"
        return {
            "ok": True,
            "tool": "geox_render_well_panel",
            "well_id": _wid,
            "seal_token": tok,
            "image_sha256": sha,
            "filepath": str(fp),
            "provenance": "scaffold",
            "content_text": f"Scaffold-only panel → {fp}",
            "metadata": {"provenance": "scaffold", "well_id": _wid},
            "image_base64_len": len(base64.b64encode(raw)),
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # POST-REGISTRATION ENRICHMENT — Binding 3 compliance (mcp-builder-doctrine v1.1.0)
    # Injects rich descriptions + "Use when..." trigger from tools_manifest.py
    # into the MCP surface. Without this, the model sees only minimal docstrings.
    # ═══════════════════════════════════════════════════════════════════════════════
    try:
        from geox_mcp.tools_manifest import CANONICAL_TOOLS as _manifest

        _enriched = 0
        _skipped = 0
        # Access tools via FastMCP's local provider component registry
        _components = getattr(getattr(mcp, "_local_provider", None), "_components", {})
        for tool_name, canonical in _manifest.items():
            # FastMCP stores tools as "tool:<name>@" keys in _components
            _key = f"tool:{tool_name}@"
            if _key in _components:
                existing = getattr(_components[_key], "description", "") or ""
                if "Use when" not in existing:
                    _components[_key].description = f"{canonical.description} Use when: {canonical.use_when}"
                    _enriched += 1
                else:
                    _skipped += 1
        logger.info(
            f"MANIFEST_ENRICH: enriched {_enriched}/{len(_manifest)} canonical tools, skipped {_skipped} (already enriched)"
        )
    except Exception as e:
        logger.warning(f"MANIFEST_ENRICH: skipped — {e}")
