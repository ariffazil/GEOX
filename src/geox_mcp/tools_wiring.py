# WARNING: Auto-generated from server.py to reduce monolith size.
# DITEMPA BUKAN DIBERI

from typing import Any, Literal
import sys
import os
import json
import logging
from datetime import datetime, UTC
import numpy as np

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, SURFACE_TOOLS, INTERNAL_TOOLS, get_tool_domain
from geox_mcp.server import (
    _geox_annotations,
    _safe_forward,
)

logger = logging.getLogger("geox.mcp.tools_wiring")


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
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Load well log data (LAS, SEG-Y, DST, deviation, tops)."""
        from geox_mcp.tools.well_ingest import geox_well_ingest as _impl

        try:
            args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
            result = await _impl(**args)
            # Discovery 8+9: Enrich result with memory + epistemic signals
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
            # Discovery 3: Structured error envelope
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_well_ingest", source_organ="geox")

    @mcp.tool(name="geox_well_qc", annotations=_geox_annotations("geox_well_qc"))
    async def _well_qc(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """QC: depth, curves, completeness, FJIS."""
        from geox_mcp.tools.well_qc import geox_well_qc as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    @mcp.tool(name="geox_well_desurvey", annotations=_geox_annotations("geox_well_desurvey"))
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
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Vsh, porosity, Sw, perm, net pay, LEM."""
        from geox_mcp.tools.petrophysics_unified import geox_petrophysics as _impl

        try:
            args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
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
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """SEG-Y I/O, header inspection."""
        from geox_mcp.tools.seismic_ingest import geox_seismic_ingest as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    @mcp.tool(name="geox_seismic_interpret", annotations=_geox_annotations("geox_seismic_interpret"))
    async def _seismic_interpret(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Horizon contrast, faults, frames, blend."""
        from geox_mcp.tools.seismic_interpret import geox_seismic_interpret as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    @mcp.tool(name="geox_vision", annotations=_geox_annotations("geox_vision"))
    async def _vision(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """VLM inference, audit, calibration, perceptual."""
        from geox_mcp.tools.vision_unified import geox_vision as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # ── SEISMIC VISION AI — 4 modes (Phase 3.2, 2026-07-06) ────────────────────
    # Cognitive visual AI taxonomy: OBS_IMAGE / DER_RENDER_ENHANCEMENT / GEN_HYPOTHESIS / DER_COGNITIVE_RENDER

    @mcp.tool(name="geox_visual_understand", annotations=_geox_annotations("geox_visual_understand"))
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

    @mcp.tool(name="geox_visual_enhance", annotations=_geox_annotations("geox_visual_enhance"))
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

    @mcp.tool(name="geox_visual_generate_hypotheses", annotations=_geox_annotations("geox_visual_generate_hypotheses"))
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

    @mcp.tool(name="geox_panel_d_render", annotations=_geox_annotations("geox_panel_d_render"))
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

    @mcp.tool(name="geox_physical_reality_interpret", annotations=_geox_annotations("geox_physical_reality_interpret"))
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

    @mcp.tool(name="geox_cognitive_rank_hypotheses", annotations=_geox_annotations("geox_cognitive_rank_hypotheses"))
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

    @mcp.tool(name="geox_segy_audit", annotations=_geox_annotations("geox_segy_audit"))
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

    @mcp.tool(name="geox_well_tie", annotations=_geox_annotations("geox_well_tie"))
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

    @mcp.tool(name="geox_3d_model", annotations=_geox_annotations("geox_3d_model"))
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

    @mcp.tool(name="geox_wealth_consequence", annotations=_geox_annotations("geox_wealth_consequence"))
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
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Joint inversion, gravity/mag, MT forward."""
        from geox_mcp.tools.subsurface_model import geox_subsurface_model as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
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
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
        ack_irreversible: bool = False,
    ) -> dict[str, Any]:
        """Create, validate, challenge, seal, attach."""
        from geox_mcp.tools.claim_unified import geox_claim as _impl

        args = _safe_forward(
            _impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id, ack_irreversible=ack_irreversible
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

    @mcp.tool(name="geox_earthquake_catalog", annotations=_geox_annotations("geox_earthquake_catalog"))
    async def _earthquake_catalog(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query USGS Earthquake Catalog for seismic events. OBSERVED data — real seismic events from USGS FDSN API. Public Domain."""
        from geox_mcp.tools.earth_surface import geox_earthquake_catalog as _impl

        args = dict(arguments or {})
        return await _impl(**args)

    @mcp.tool(name="geox_relief_ingest", annotations=_geox_annotations("geox_relief_ingest"))
    async def _relief_ingest(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Ingest ETOPO 2022 global relief (topography + bathymetry). OBSERVED data — measured elevation from NOAA NCEI. Public Domain."""
        from geox_mcp.tools.earth_surface import geox_relief_ingest as _impl

        args = dict(arguments or {})
        return await _impl(**args)

    @mcp.tool(name="geox_bathymetry_ingest", annotations=_geox_annotations("geox_bathymetry_ingest"))
    async def _bathymetry_ingest(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Ingest GEBCO_2026 global bathymetry grid (ocean floor terrain). OBSERVED data — measured ocean depth from IHO/UNESCO. Public Domain."""
        from geox_mcp.tools.earth_surface import geox_bathymetry_ingest as _impl

        args = dict(arguments or {})
        return await _impl(**args)

    # ── EXTENDED EARTH DIMENSIONS — D4-D17 Open Data (2026-06-25 FORGE) ───────

    @mcp.tool(name="geox_heatflow_query", annotations=_geox_annotations("geox_heatflow_query"))
    async def _heatflow(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query IHFC Global Heat Flow Database. OBSERVED — ~91k measurements. GFZ/IHFC CC-BY-4.0."""
        from geox_mcp.tools.earth_surface_2 import geox_heatflow_query as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_stress_query", annotations=_geox_annotations("geox_stress_query"))
    async def _stress(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query World Stress Map 2025 (WSM). OBSERVED — ~100k stress orientations. GFZ CC-BY-4.0."""
        from geox_mcp.tools.earth_surface_2 import geox_stress_query as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_geochem_query", annotations=_geox_annotations("geox_geochem_query"))
    async def _geochem(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query EarthChem/PetDB for igneous geochemistry. OBSERVED — global rock analyses. CC-BY."""
        from geox_mcp.tools.earth_surface_2 import geox_geochem_query as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_plate_reconstruct", annotations=_geox_annotations("geox_plate_reconstruct"))
    async def _plate(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Reconstruct a point through deep time via GPlates. INTERPRETED — plate model dependent. GPL-2.0."""
        from geox_mcp.tools.earth_surface_2 import geox_plate_reconstruct as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_paleomag_query", annotations=_geox_annotations("geox_paleomag_query"))
    async def _paleomag(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query MagIC for paleomagnetic data. OBSERVED — rock magnetic measurements. CC-BY-4.0."""
        from geox_mcp.tools.earth_surface_2 import geox_paleomag_query as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_gravity_change_query", annotations=_geox_annotations("geox_gravity_change_query"))
    async def _grace(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query GRACE-FO for time-variable gravity (mass change). OBSERVED — NASA satellite gravimetry. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_gravity_change_query as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_ocean_query", annotations=_geox_annotations("geox_ocean_query"))
    async def _ocean(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query Copernicus Marine (CMEMS) for ocean physics/BGC. OBSERVED — satellite + model. EU Open Data."""
        from geox_mcp.tools.earth_surface_2 import geox_ocean_query as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_erddap_query", annotations=_geox_annotations("geox_erddap_query"))
    async def _erddap(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query NOAA ERDDAP for ocean/atmosphere data. OBSERVED — 10k+ datasets. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_erddap_query as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_climate_reanalysis", annotations=_geox_annotations("geox_climate_reanalysis"))
    async def _climate(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query ERA5 global reanalysis. OBSERVED — ECMWF hourly data from 1940. Copernicus License."""
        from geox_mcp.tools.earth_surface_2 import geox_climate_reanalysis as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_hydrology_query", annotations=_geox_annotations("geox_hydrology_query"))
    async def _hydrology(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query USGS Water Services for streamflow/groundwater. OBSERVED — US real-time. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_hydrology_query as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_satellite_catalog", annotations=_geox_annotations("geox_satellite_catalog"))
    async def _satellite(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Search STAC for Landsat/MODIS/Sentinel imagery. OBSERVED — satellite surface reflectance. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_satellite_catalog as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_uk_petroleum_query", annotations=_geox_annotations("geox_uk_petroleum_query"))
    async def _nsta(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query NSTA UK petroleum data (wells, fields, licences). OBSERVED — UKCS regulatory. OGL v3.0."""
        from geox_mcp.tools.earth_surface_2 import geox_uk_petroleum_query as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_geology_map_query", annotations=_geox_annotations("geox_geology_map_query"))
    async def _onegeology(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query OneGeology WMS for national geological maps. OBSERVED — aggregated survey data."""
        from geox_mcp.tools.earth_surface_2 import geox_geology_map_query as _impl

        return await _impl(**dict(arguments or {}))

    @mcp.tool(name="geox_space_weather", annotations=_geox_annotations("geox_space_weather"))
    async def _spaceweather(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query NOAA SWPC for space weather (Kp, Dst, solar wind). OBSERVED — real-time. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_space_weather as _impl

        return await _impl(**dict(arguments or {}))

    # ── PHYSICS-FIRST STRATIGRAPHY ENGINES — Phase 3.0 (2026-07-03) ────────────
    # The extinction event: replaces LST/TST/HST taxonomy with physics simulation.
    # Sequences EMERGE from accommodation + eustasy + sediment, not from rules.
    # DITEMPA BUKAN DIBERI.

    @mcp.tool(name="geox_simulate_accommodation", annotations=_geox_annotations("geox_simulate_accommodation"))
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

    @mcp.tool(name="geox_simulate_surfaces", annotations=_geox_annotations("geox_simulate_surfaces"))
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

    @mcp.tool(name="geox_simulate_sequences", annotations=_geox_annotations("geox_simulate_sequences"))
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

    @mcp.tool(name="geox_seismic_cognition", annotations=_geox_annotations("geox_seismic_cognition"))
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

    @mcp.tool(name="geox_geological_cognition_run", annotations=_geox_annotations("geox_geological_cognition_run"))
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

    @mcp.tool(name="geox_well_tie_compute", annotations=_geox_annotations("geox_well_tie_compute"))
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

    @mcp.tool(name="geox_tie_receipt", annotations=_geox_annotations("geox_tie_receipt"))
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

    @mcp.tool(name="geox_tie_preflight", annotations=_geox_annotations("geox_tie_preflight"))
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

    @mcp.tool(name="geox_3d_model_build", annotations=_geox_annotations("geox_3d_model_build"))
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

    @mcp.tool(name="geox_wealth_bridge_run", annotations=_geox_annotations("geox_wealth_bridge_run"))
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
