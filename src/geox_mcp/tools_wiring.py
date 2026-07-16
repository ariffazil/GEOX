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
                    "mode": mode,
                    "source_uri": source_uri,
                    "source_type": source_type,
                    "well_id": well_id,
                    "standardize_curves": standardize_curves,
                    "normalize_units": normalize_units,
                    "content_base64": content_base64,
                    "filename": filename,
                    "target_dir": target_dir,
                    "overwrite": overwrite,
                    "batch_mode": batch_mode,
                    "artifact_refs": artifact_refs,
                    "qc_strict": qc_strict,
                    "source_crs": source_crs,
                    "depth_datum": depth_datum,
                    "file_format": file_format,
                    "las_metadata": las_metadata,
                    "las_curve_info": las_curve_info,
                    "segy_metadata": segy_metadata,
                    "seismic_metadata": seismic_metadata,
                    "deviation_metadata": deviation_metadata,
                    "tops_metadata": tops_metadata,
                    "field": field,
                    "reservoir_name": reservoir_name,
                    "test_name": test_name,
                    "test_duration_hr": test_duration_hr,
                    "main_flow_hr": main_flow_hr,
                    "main_buildup_hr": main_buildup_hr,
                    "choke_size_64ths": choke_size_64ths,
                    "bhp_psi": bhp_psi,
                    "bht_c": bht_c,
                    "whp_psi": whp_psi,
                    "wht_c": wht_c,
                    "gas_rate_mmscfd": gas_rate_mmscfd,
                    "condensate_rate_stbd": condensate_rate_stbd,
                    "water_rate_stbd": water_rate_stbd,
                    "co2_mol_pct": co2_mol_pct,
                    "h2s_ppm": h2s_ppm,
                    "bsw_pct": bsw_pct,
                    "chloride_ppm": chloride_ppm,
                    "wgr_stb_per_mmscf": wgr_stb_per_mmscf,
                    "permeability_md_min": permeability_md_min,
                    "permeability_md_max": permeability_md_max,
                    "skin_min": skin_min,
                    "skin_max": skin_max,
                },
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
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

    # DEREGISTERED ZEN-15 — @mcp.tool(name="geox_well_qc", annotations=_geox_annotations("geox_well_qc"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_well_desurvey", annotations=_geox_annotations("geox_well_desurvey"))

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
                    "mode": mode,
                    "target_class": target_class,
                    "evidence_refs": evidence_refs,
                    "realizations": realizations,
                    "gr_clean": gr_clean,
                    "gr_shale": gr_shale,
                    "vsh_method": vsh_method,
                    "matrix_density": matrix_density,
                    "fluid_density": fluid_density,
                    "sw_model": sw_model,
                    "rw": rw,
                    "archie_a": archie_a,
                    "archie_m": archie_m,
                    "archie_n": archie_n,
                    "vsh_cutoff": vsh_cutoff,
                    "phi_cutoff": phi_cutoff,
                    "sw_cutoff": sw_cutoff,
                    "rt_cutoff": rt_cutoff,
                    "zone_top_m": zone_top_m,
                    "zone_base_m": zone_base_m,
                    "basin_context": basin_context,
                    "canon9_profile": canon9_profile,
                    "target_depth_m": target_depth_m,
                    "cube_inline": cube_inline,
                    "use_synth_cube": use_synth_cube,
                    "lmr_inline": lmr_inline,
                    "candidate_ref": candidate_ref,
                    "domain": domain,
                    "well_id": well_id,
                    "curves": curves,
                    "depth_m": depth_m,
                    "depth_top_m": depth_top_m,
                    "depth_bot_m": depth_bot_m,
                    "target_properties": target_properties,
                    "basin": basin,
                    "rw_ohm_m": rw_ohm_m,
                    "rho_matrix_g_cc": rho_matrix_g_cc,
                    "rho_fluid_g_cc": rho_fluid_g_cc,
                    "patch_size_m": patch_size_m,
                    "cell_states": cell_states,
                    "areal_extent_m2": areal_extent_m2,
                    "pay_zone_thickness_m": pay_zone_thickness_m,
                    "formation_volume_factor": formation_volume_factor,
                    "water_saturation": water_saturation,
                    "oil_density_kg_m3": oil_density_kg_m3,
                    "recovery_factor": recovery_factor,
                },
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
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
                "session_id": session_id,
                "actor_id": actor_id,
                "trace_id": trace_id,
                "version": "v2026.06.22-phase2",
                "git_version": git_version,
                "canonical_tools": len(CANONICAL_PUBLIC_TOOLS),
                "mcp_transport": "http",
                "mcp_port": 8081,
                "registered_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

        # registry mode — WELL-style rich drift report
        # Domain sourced from GEOX_TOOL_MANIFEST via get_tool_domain() (registry.py).
        # Single source of truth — structured manifest replaces hardcoded inline dict.
        from geox_mcp.surface_manifest import manifest_tool_map

        canonical_set = set(CANONICAL_PUBLIC_TOOLS)
        all_manifest = manifest_tool_map()

        canonical_list = []
        phantom_list = []
        internal_list = []

        for tool_name, entry in sorted(all_manifest.items()):
            domain = entry.domain if hasattr(entry, "domain") else get_tool_domain(tool_name)
            if tool_name in canonical_set:
                canonical_list.append(
                    {
                        "name": tool_name,
                        "domain": domain,
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
            elif entry.is_internal if hasattr(entry, "is_internal") else False:
                internal_list.append(tool_name)
            else:
                phantom_list.append(tool_name)

        # Multi-surface parity (manifest / runtime / plugin export / docs snapshot)
        from geox_mcp.surface_manifest import plugin_export_tool_names
        from geox_mcp.tools.registry import (
            _load_generated_public_surface,
            _load_plugin_export_surface,
        )

        expected_app_export = set(plugin_export_tool_names())
        plugin_export_public = _load_plugin_export_surface() or expected_app_export
        generated_public = _load_generated_public_surface() or set(canonical_set)
        plugin_export_only = sorted(plugin_export_public - expected_app_export)
        missing_from_app_export = sorted(expected_app_export - plugin_export_public)
        generated_only = sorted(generated_public - set(canonical_set))
        missing_from_generated = sorted(set(canonical_set) - generated_public)

        has_drift = bool(
            phantom_list
            or plugin_export_only
            or missing_from_app_export
            or generated_only
            or missing_from_generated
            or expected_app_export != set(canonical_set)
        )
        return {
            "status": "healthy",
            "organ": "GEOX",
            "session_id": session_id,
            "actor_id": actor_id,
            "trace_id": trace_id,
            "surface_version": "geox-2026.07.15-zen15",
            "canonical_callable": canonical_list,
            "canonical_tools": sorted(canonical_set),
            "intended_tools": len(all_manifest),
            "registered_tools": len(all_manifest),
            "callable_tools": len(canonical_list),
            "public_count": len(canonical_set),
            "phantom_tools": phantom_list,
            "internal_tools": internal_list,
            "plugin_export_public": sorted(plugin_export_public),
            "expected_app_export": sorted(expected_app_export),
            "plugin_export_only_tools": plugin_export_only,
            "missing_from_app_export": missing_from_app_export,
            "generated_public_only": generated_only,
            "missing_from_generated": missing_from_generated,
            "deprecated_callable": [],
            "alias_conflicts": [],
            "registry_truth": "DRIFT" if has_drift else "PASS",
            "verdict": "REGISTRY_DRIFT" if has_drift else "REGISTRY_PASS",
            "perception_class": "OBSERVED",
            "claim_state": "OBSERVED",
            "evidence_tag": "COMPUTED",
            "confidence_level": "HIGH",
            "humility_score": 0.05,
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
                "mode": mode,
                "volume_ref": volume_ref,
                "output_path": output_path,
                "sample_interval_ms": sample_interval_ms,
                "textual_header": textual_header,
                "overwrite": overwrite,
                "provenance": provenance,
                "segy_metadata": segy_metadata,
                "seismic_metadata": seismic_metadata,
                "source_uri": source_uri,
                "source_type": source_type,
                "well_id": well_id,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
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
                "mode": mode,
                "source_uri": source_uri,
                "source_type": source_type,
                "action": action,
                "volume_ref": volume_ref,
                "frame_index": frame_index,
                "orientation": orientation,
                "provenance": provenance,
                "image_data": image_data,
                "blend_mode": blend_mode,
                "horizon_query": horizon_query,
                "threshold": threshold,
                "confidence_cap": confidence_cap,
                "cube_ref": cube_ref,
                "volume_inline": volume_inline,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    # DEREGISTERED ZEN-15 — @mcp.tool(name="geox_vision", annotations=_geox_annotations("geox_vision"))

    # ── SEISMIC VISION AI — 4 modes (Phase 3.2, 2026-07-06) ────────────────────
    # Cognitive visual AI taxonomy: OBS_IMAGE / DER_RENDER_ENHANCEMENT / GEN_HYPOTHESIS / DER_COGNITIVE_RENDER

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_visual_understand", annotations=_geox_annotations("geox_visual_understand"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_visual_enhance", annotations=_geox_annotations("geox_visual_enhance"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_visual_generate_hypotheses", annotations=_geox_annotations("geox_visual_generate_hypotheses"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_panel_d_render", annotations=_geox_annotations("geox_panel_d_render"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_physical_reality_interpret", annotations=_geox_annotations("geox_physical_reality_interpret"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_cognitive_rank_hypotheses", annotations=_geox_annotations("geox_cognitive_rank_hypotheses"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_segy_audit", annotations=_geox_annotations("geox_segy_audit"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_well_tie", annotations=_geox_annotations("geox_well_tie"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_3d_model", annotations=_geox_annotations("geox_3d_model"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_wealth_consequence", annotations=_geox_annotations("geox_wealth_consequence"))

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
                "mode": mode,
                "survey_type": survey_type,
                "easting_m": easting_m,
                "northing_m": northing_m,
                "prisms": prisms,
                "magnetization_a_m": magnetization_a_m,
                "field_declination_deg": field_declination_deg,
                "field_inclination_deg": field_inclination_deg,
                "layers": layers,
                "frequencies_hz": frequencies_hz,
                "observations": observations,
                "prior": prior,
                "max_iter": max_iter,
                "tolerance": tolerance,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
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
                "mode": mode,
                "claim_id": claim_id,
                "claim_text": claim_text,
                "claim_type": claim_type,
                "truth_class": truth_class,
                "evidence_ids": evidence_ids,
                "uncertainty_p10": uncertainty_p10,
                "uncertainty_p50": uncertainty_p50,
                "uncertainty_p90": uncertainty_p90,
                "uncertainty_distribution": uncertainty_distribution,
                "alternatives": alternatives,
                "provenance": provenance,
                "authority": authority,
                "challenge_text": challenge_text,
                "alternative_claim_text": alternative_claim_text,
                "alternative_evidence_ids": alternative_evidence_ids,
                "challenge_evidence_ids": challenge_evidence_ids,
                "alternative_uncertainty": alternative_uncertainty,
                "challenger_provenance": challenger_provenance,
                "ack_irreversible": ack_irreversible,
                "seal_verdict": seal_verdict,
                "voxel_state": voxel_state,
                "evidence_id": evidence_id,
                "evidence_type": evidence_type,
                "epistemic_label": epistemic_label,
                "forbidden_uses": forbidden_uses,
                "source_citation": source_citation,
                "category": category,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
            ack_irreversible=ack_irreversible,
        )
        return await _impl(**args)

    # RESURRECTED 2026-07-16 — evidence is the lifeblood of the claim system
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

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_relief_ingest", annotations=_geox_annotations("geox_relief_ingest"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_bathymetry_ingest", annotations=_geox_annotations("geox_bathymetry_ingest"))

    # ── EXTENDED EARTH DIMENSIONS — D4-D17 Open Data (2026-06-25 FORGE) ───────

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_heatflow_query", annotations=_geox_annotations("geox_heatflow_query"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_stress_query", annotations=_geox_annotations("geox_stress_query"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_geochem_query", annotations=_geox_annotations("geox_geochem_query"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_plate_reconstruct", annotations=_geox_annotations("geox_plate_reconstruct"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_paleomag_query", annotations=_geox_annotations("geox_paleomag_query"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_gravity_change_query", annotations=_geox_annotations("geox_gravity_change_query"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_ocean_query", annotations=_geox_annotations("geox_ocean_query"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_erddap_query", annotations=_geox_annotations("geox_erddap_query"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_climate_reanalysis", annotations=_geox_annotations("geox_climate_reanalysis"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_hydrology_query", annotations=_geox_annotations("geox_hydrology_query"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_satellite_catalog", annotations=_geox_annotations("geox_satellite_catalog"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_uk_petroleum_query", annotations=_geox_annotations("geox_uk_petroleum_query"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_geology_map_query", annotations=_geox_annotations("geox_geology_map_query"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_space_weather", annotations=_geox_annotations("geox_space_weather"))

    # ── PHYSICS-FIRST STRATIGRAPHY ENGINES — Phase 3.0 (2026-07-03) ────────────
    # The extinction event: replaces LST/TST/HST taxonomy with physics simulation.
    # Sequences EMERGE from accommodation + eustasy + sediment, not from rules.
    # DITEMPA BUKAN DIBERI.

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_simulate_accommodation", annotations=_geox_annotations("geox_simulate_accommodation"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_simulate_surfaces", annotations=_geox_annotations("geox_simulate_surfaces"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_simulate_sequences", annotations=_geox_annotations("geox_simulate_sequences"))

    # RE-REGISTERED 2026-07-13 — sediment routing for provenance-routing skill (earth-decode-7)
    @mcp.tool(name="geox_simulate_routing", annotations=_geox_annotations("geox_simulate_routing"))
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

    # ═══════════════════════════════════════════════════════════════════════════════
    # SEISMIC PIPELINE TOOLS — Phase 3.0 RSI Cognition (2026-07-06)
    # Platform-agnostic seismic interpretation pipeline.
    # Implements IMAGE-FIRST COGNITION + NON-UNIQUENESS LAW doctrines.
    # OBS_IMAGE ≠ OBS_GEOLOGY. Pixels are observed. Geology requires calibration.
    # ═══════════════════════════════════════════════════════════════════════════════

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_physical_reality_interpret", annotations=_geox_annotations("geox_physical_reality_interpret"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_geological_cognition_run", annotations=_geox_annotations("geox_geological_cognition_run"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_panel_d_render_mcp", annotations=_geox_annotations("geox_panel_d_render_mcp"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_segy_trace_audit", annotations=_geox_annotations("geox_segy_trace_audit"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_well_tie_compute", annotations=_geox_annotations("geox_well_tie_compute"))

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

    # ── WELL-TIE P2–P4: Time-Depth Calibrate · Mistie RMS · Wavelet Extract ────

    # DEREGISTERED 2026-07-10 — # ZEN 2026-07-11 G1: merged into geox_seismic_compute — geox_well_time_depth_calibrate

    # DEREGISTERED 2026-07-10 — # ZEN 2026-07-11 G1: merged into geox_seismic_compute — geox_well_seismic_mistie_rms

    # DEREGISTERED 2026-07-10 — # ZEN 2026-07-11 G1: merged into geox_seismic_compute — geox_wavelet_extract_least_squares

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_3d_model_build", annotations=_geox_annotations("geox_3d_model_build"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_wealth_bridge_run", annotations=_geox_annotations("geox_wealth_bridge_run"))

    # ── GEOLOGICAL MAP PIPELINE — 4-Verb Chain (2026-07-02 FORGE) ────────────

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_layers_list", annotations=_geox_annotations("geox_map_layers_list"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_scene_plan", annotations=_geox_annotations("geox_map_scene_plan"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_render_preview", annotations=_geox_annotations("geox_map_render_preview"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_map_export_package", annotations=_geox_annotations("geox_map_export_package"))

    # ── BID ROUND SCREENER — MBR 2026 (2026-07-09) ─────────────────────────
    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_bid_round_screener", annotations=_geox_annotations("geox_bid_round_screener"))

    # ── COLLISION ZONE — Two Oceanics Physics (Phase Zen, 2026-07-10) ────────
    # Implements collision zone physics from Arif's Sabah Eureka Ledger v1.0.
    # Two blocks (accretionary + rifted), suture, accommodation ratio, loading ratio.
    # Detects 6 Eureka signatures. Margin Principle embedded.
    # DITEMPA BUKAN DIBERI.

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_collision_zone", annotations=_geox_annotations("geox_collision_zone"))

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_collision_chronology", annotations=_geox_annotations("geox_collision_chronology"))

    # ── DOMAIN EVIDENCE GATE — geox_diagnose (Phase Zen, 2026-07-10) ──────────
    # Pre-flight check: "Does GEOX have evidence for this question?"
    # Returns NO_DOMAIN_EVIDENCE / PARTIAL / READY.
    # When NO_DOMAIN_EVIDENCE: use ChatGPT, not GEOX.

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_diagnose", annotations=_geox_annotations("geox_diagnose"))

    # ── EARTH OBSERVE — 24-in-1 consolidated surface (Zen, 2026-07-10) ──────
    # One tool. 24 modes. Replaces 24 individual Earth data fetchers.
    # earthquake, relief, bathymetry, heatflow, stress, geochem,
    # plate_reconstruct, paleomag, gravity, ocean, erddap, climate,
    # hydrology, satellite, uk_petroleum, geology_map, space_weather,
    # nsta, context_at_location, isitwater, gravity_screen,
    # judgment_preflight, interpolate_grid, report_to_workflow

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_observe", annotations=_geox_annotations("geox_observe"))

    # ═══════════════════════════════════════════════════════════════════════════════
    # BASIN ANALYSIS ENGINES (4) — Phase 0 (2026-07-10)
    # Physics-first basin analysis: backstripping, mass balance, thermal maturity,
    # claim graph evaluation. Complements simulate_* with backward reconstruction.
    # ═══════════════════════════════════════════════════════════════════════════════

    # RESURRECTED 2026-07-16 — Steckler & Watts 1978 + Sclater & Christie 1980 backstripping
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

    # RESURRECTED 2026-07-16 — Peters 2012 sediment cycling framework
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

    # RESURRECTED 2026-07-16 — EasyRo (Sweeney & Burnham 1990) + TTI (Lopatin 1971)
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

    # RESURRECTED 2026-07-16 — DAG claim graph evaluation for falsification
    @mcp.tool(name="geox_claim_graph_evaluate", annotations=_geox_annotations("geox_claim_graph_evaluate"))
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
    # POPPERIAN FALSIFICATION ENGINE — geox_falsify
    # GENESIS/015 architecture: Kill Matrix K001-K007 + contradiction scan
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(name="geox_falsify", annotations=_geox_annotations("geox_falsify"))
    async def _falsify(
        claim_text: str,
        claim_type: str = "general",
        mode: str = "full",
        kill_matrix: list[str] | None = None,
        context: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Popperian falsification — tests claims against Kill Matrix K001-K007 + contradiction scan.

        GENESIS/015: physics must prove the claim is right.
        ANY KILL → claim rejected. REVIEW > 0 → treat as KILL until resolved.
        All PASS → PROCEED to arifOS 888_JUDGE.

        modes: full | quick | physics_only | kill_matrix_only
        """
        from geox_mcp.tools.falsify import geox_falsify as _impl

        return await _impl(
            claim_text=claim_text,
            claim_type=claim_type,
            mode=mode,
            kill_matrix=kill_matrix,
            context=context,
            evidence=evidence,
            session_id=session_id,
            actor_id=actor_id,
        )

    # ═══════════════════════════════════════════════════════════════════════════════
    # CONTRADICTION SCAN — geox_contradiction_scan
    # 13-type contradiction ontology for cross-claim detection
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(name="geox_contradiction_scan", annotations=_geox_annotations("geox_contradiction_scan"))
    async def _contradiction_scan(
        claims: list[dict[str, Any]],
        mode: str = "pairwise",
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Scan claims for contradictions using the13-type ontology.

        Classifies: MEASUREMENT_CONFLICT, DATUM_CONFLICT, MODEL_PHYSICS_VIOLATION,
        INTERPRETATION_OBSERVATION_MISMATCH, CROSS_MODAL_CONFLICT, etc.
        FATAL → VOID. HIGH → 888_HOLD. MEDIUM → FLAG.
        """
        from geox_mcp.tools.contradiction_scan import geox_contradiction_scan as _impl

        return await _impl(
            claims=claims,
            mode=mode,
            session_id=session_id,
            actor_id=actor_id,
        )

    # ═══════════════════════════════════════════════════════════════════════════════
    # LEM PREDICT — geox_lem_predict
    # Large Earth Model inference (physics-prior until weights deploy)
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(name="geox_lem_predict", annotations=_geox_annotations("geox_lem_predict"))
    async def _lem_predict(
        well_id: str,
        curves: dict[str, list[float]],
        depth_m: list[float],
        target_properties: list[str] | None = None,
        mode: str = "physics_prior",
        depth_top_m: float | None = None,
        depth_bot_m: float | None = None,
        basin: str | None = None,
        rw_ohm_m: float | None = None,
        rho_matrix_g_cc: float | None = None,
        rho_fluid_g_cc: float | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """LEM inference — predict rock properties from well log curves.

        Default mode: physics_prior (Archie, density-porosity, Gardner, Wyllie).
        Transformer/hybrid modes require888_HOLD for weight deployment.
        """
        from geox_mcp.tools.lem_predict import geox_lem_predict, LEMPredictRequest

        req = LEMPredictRequest(
            well_id=well_id,
            curves=curves,
            depth_m=depth_m,
            target_properties=target_properties or ["porosity", "sw"],
            mode=mode,
            depth_top_m=depth_top_m,
            depth_bot_m=depth_bot_m,
            basin=basin,
            rw_ohm_m=rw_ohm_m,
            rho_matrix_g_cc=rho_matrix_g_cc,
            rho_fluid_g_cc=rho_fluid_g_cc,
            actor_id=actor_id,
            session_id=session_id,
        )
        return await geox_lem_predict(req)

    # ═══════════════════════════════════════════════════════════════════════════════
    # GEOX→WEALTH BRIDGE — geox_to_wealth_bridge
    # Cross-organ data bridge for capital intelligence
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(name="geox_to_wealth_bridge", annotations=_geox_annotations("geox_to_wealth_bridge"))
    async def _to_wealth_bridge(
        prospect_id: str,
        npv_usd: float | None = None,
        irr: float | None = None,
        breakeven_usd: float | None = None,
        discount_rate: float = 0.10,
        risk_geo: float = 0.0,
        sigma_market: float = 0.0,
        sigma_policy: float = 0.0,
        admissibility: str = "admitted",
        epistemic_source: str = "ESTIMATE",
        penalty_infinite: bool = False,
        carbon_cost_usd: float = 0.0,
        delay_risk: float = 0.0,
        required_modifications: list[str] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Bridge GEOX prospect data to WEALTH score_kernel input.

        F2: epistemic_source passed through, never upgraded.
        F13: blocked nodes cannot enter WEALTH pipeline.
        """
        from geox_mcp.tools.wealth_bridge_tool import geox_to_wealth_bridge as _impl

        return await _impl(
            prospect_id=prospect_id,
            npv_usd=npv_usd,
            irr=irr,
            breakeven_usd=breakeven_usd,
            discount_rate=discount_rate,
            risk_geo=risk_geo,
            sigma_market=sigma_market,
            sigma_policy=sigma_policy,
            admissibility=admissibility,
            epistemic_source=epistemic_source,
            penalty_infinite=penalty_infinite,
            carbon_cost_usd=carbon_cost_usd,
            delay_risk=delay_risk,
            required_modifications=required_modifications,
            session_id=session_id,
            actor_id=actor_id,
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

    # DEREGISTERED ZEN-15 — geox_well_desk_open (absorbed into geox_well_desk)

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

    # DEREGISTERED ZEN-15 — geox_well_desk_publish (absorbed into geox_well_desk)

    # DEREGISTERED ZEN-15 — geox_render_well_panel (absorbed into geox_well_desk)

    # ═══════════════════════════════════════════════════════════════════════════════
    # ZEN-15 CANONICAL TOOLS (2026-07-13)
    # Unified tools absorbing multiple legacy tools into mode-based interfaces.
    # DITEMPA BUKAN DIBERI.
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(name="geox_gravmag_studio", annotations=_geox_annotations("geox_gravmag_studio"))
    async def _gravmag_studio(
        mode: str = "open",
        survey_type: str = "gravity",
        prisms: list[dict[str, Any]] | None = None,
        magnetization_a_m: float = 0.0,
        field_declination_deg: float = 0.0,
        field_inclination_deg: float = 0.0,
        grid_extent_m: float = 50000.0,
        grid_n: int = 40,
        backend: str = "auto",
        # screen-only params — observed_grid accepts list OR JSON string (MCP transport fix)
        observed_grid: Any = None,
        observed_units: str | None = None,
        observed_source: str | None = None,
        observed_extent_m: float | None = None,
        alternatives_declared: Any = None,
        # governance params (accepted, not forwarded to implementation)
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Gravity/magnetic studio: forward modeling and screening. Modes: open, screen.

        open   — interactive GravMag Studio UI with forward modeling.
            Params: survey_type, prisms, magnetization_a_m, field_declination_deg,
            field_inclination_deg, grid_extent_m, grid_n, backend.

        screen — screening analysis against observed data (falsification lane).
            Additional required params: observed_grid (2D list), observed_units
            ("mGal"/"nT"), observed_source (provenance string).
            Optional: observed_extent_m, alternatives_declared.
        """
        if mode == "screen":
            import json as _json
            from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen as _impl

            # F1 AMANAH: MCP transport may serialize nested lists as JSON strings
            _og = observed_grid or []
            if isinstance(_og, str):
                try:
                    _og = _json.loads(_og)
                except (ValueError, TypeError):
                    return {"verdict": "VOID", "error": f"observed_grid is a string but not valid JSON: {_og[:200]}"}
            _ad = alternatives_declared
            if isinstance(_ad, str):
                try:
                    _ad = _json.loads(_ad)
                except (ValueError, TypeError):
                    _ad = None

            return await _impl(
                survey_type=survey_type,
                prisms=prisms or [],
                grid_extent_m=grid_extent_m,
                grid_n=grid_n,
                observed_grid=_og,
                observed_units=observed_units or "mGal",
                observed_source=observed_source or "synthetic_probe",
                magnetization_a_m=magnetization_a_m,
                field_declination_deg=field_declination_deg,
                field_inclination_deg=field_inclination_deg,
                backend=backend,
                alternatives_declared=_ad,
                observed_extent_m=observed_extent_m,
            )
        # Default: open
        from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open as _impl

        return await _impl(
            survey_type=survey_type,
            prisms=prisms or [],
            magnetization_a_m=magnetization_a_m,
            field_declination_deg=field_declination_deg,
            field_inclination_deg=field_inclination_deg,
            grid_extent_m=grid_extent_m,
            grid_n=grid_n,
            backend=backend,
        )

    @mcp.tool(name="geox_well_desk", annotations=_geox_annotations("geox_well_desk"))
    async def _well_desk(
        mode: str = "open",
        well_id: str = "",
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
        """Well desk: interactive view, publish, render. Modes: open, publish, render.

        open    — interactive well-desk view (MCP App)
        publish — render and publish well panel image
        render  — render well-log panel with petrophysics
        """
        if mode == "publish":
            from geox_mcp.tools.integration_well import geox_well_desk_publish as _impl

            return await _impl(
                well_id=well_id,
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
        if mode == "render":
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
        # Default: open
        from geox_mcp.tools.integration_well import geox_well_desk_open as _impl

        return await _impl(
            well_id=well_id,
            mode="summary",
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

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
