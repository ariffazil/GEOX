"""
geox_seismic_interpret — Seismic Interpretation (Phase 2 + P0/C/A/D 2026-07-23)
════════════════════════════════════════════════════════════════════════════════
Live modes (public, callable):
  horizon_contrast   — 1D multi-attribute boundary detector (ToAC)
  fault_sticks       — Fault stick CSV/GeoJSON ingest (not auto-extract)
  volume_frame       — Volume frame read/write
  blend              — Alpha/RGB volume blending
  structure_validate — G2–G9 + K-* structural falsifier (+ interpretation_bundle)
  interpret          — propose→validate→compare bundle (framework and/or image)
  interpret_section  — RSI image-true propose (INT_SEISMIC, QUALIFIED_CANDIDATE)
  rsi_pipeline       — thin alias → geox_rsi_interpret
  section_image      — alias interpret_section
  segy_slice         — Phase D: SEG-Y → MeasurementContext + amplitude stats
  track_horizon      — F1 zen: 2D phase-aware DP track → horizon polylines
  measure_throw      — F1 zen: cutoffs → dmax_m/length_m/throw_profile_m + gates

Still HOLD (not public-executable):
  vision, extract_faults, build_structure, observe_image, falsify

Local engine verdicts are QUALIFIED_CANDIDATE at most — arifOS seals.
preferred_hypothesis always null from GEOX (human adjudicates).
DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any

# Modes the handler can execute today
_LIVE_MODES = frozenset(
    {
        "horizon_contrast",
        "fault_sticks",
        "volume_frame",
        "blend",
        "structure_validate",
        "interpret",
        "classical_section",
        "interpret_section",
        "rsi_pipeline",
        "section_image",
        "segy_slice",
        "segy_2d",
        "track_horizon",  # F1 zen 2D phase track
        "measure_throw",  # F1 zen throw → structure gates
        "cutoff_throw",  # alias measure_throw
    }
)

# Manifest-claimed but not public-executable — deliberate HOLD, not silent remaps
_NOT_YET_MODES: dict[str, str] = {
    "contrast": "Alias of horizon_contrast — pass mode=horizon_contrast with attribute_data+depth.",
    "vision": (
        "Vision modes (geox_visual_understand / geox_vision_*) are separate tools. "
        "geox_seismic_interpret does not run VLM. Call geox_visual_understand for OBS_IMAGE."
    ),
    "extract_faults": "Auto fault-plane extraction not proven. Use measure_throw + structure_validate.",
    "build_structure": "Use structure_validate on a proposed framework; full build_structure loop later.",
    "falsify": "Use geox_falsify (claim_type=structural_*) for claim physics checks.",
    "observe_image": "Use geox_visual_understand for OBS_IMAGE (HOLD without VLM).",
}


def _json_safe(obj: Any) -> Any:
    """Make tool payloads JSON-serializable for MCP structuredContent.

    RSI/geometry paths leak numpy scalars (esp. numpy.bool_, float64). FastMCP
    then fails json.dumps → clients see 'outputSchema defined but no structured
    output returned' even though governance ALLOWED and the engine succeeded.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    # numpy scalars / arrays (and similar)
    item = getattr(obj, "item", None)
    if callable(item):
        try:
            return _json_safe(item())
        except Exception:
            pass
    tolist = getattr(obj, "tolist", None)
    if callable(tolist):
        try:
            return _json_safe(tolist())
        except Exception:
            pass
    if hasattr(obj, "__fspath__"):
        return str(obj)
    # last resort — keep transport alive over perfect fidelity
    return str(obj)


def _stamp_qualified(
    result: dict[str, Any],
    mode: str,
    transport: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result.setdefault("tool", "geox_seismic_interpret")
    result["mode"] = mode
    result["local_verdict"] = "QUALIFIED_CANDIDATE"
    result["seal_authority"] = "arifOS_only"
    gov = result.get("governance_status") or result.get("governance", {})
    if gov == "SEAL" or (isinstance(gov, dict) and gov.get("status") == "SEAL"):
        result["governance_status"] = "QUALIFY"
        result["governance_note"] = "Local SEAL remapped to QUALIFY — arifOS seals only"
    # RSI may return verdict PARTIAL — map transport language
    if result.get("verdict") == "SEAL":
        result["verdict"] = "PARTIAL"
    # Envelope fields that help outputSchema / clients without changing geology
    result.setdefault("status", "OK" if result.get("ok", True) else "HOLD")
    if result.get("preferred_hypothesis") is not False:
        result.setdefault("preferred_hypothesis", None)
    result.setdefault("claim_tag", "HYPOTHESIS")
    # Inject declared MCP transport metadata into provenance so callers can
    # correlate response → call. Only non-None fields are stamped (avoids
    # # stamping None and overwriting existing provenance).
    if transport:
        prov = result.setdefault("provenance", {})
        if isinstance(prov, dict):
            for k, v in transport.items():
                if v is not None:
                    prov.setdefault(k, v)
    return _json_safe(result)


async def geox_seismic_interpret(
    mode: str = "horizon_contrast",
    # ── horizon_contrast inputs ──
    attribute_data: dict[str, list[float]] | None = None,
    depth: list[float] | None = None,
    geological_query: str = "sequence_boundary",
    well_ties: dict[str, float] | None = None,
    stratigraphic_framework: str = "ABKSS",
    peak_threshold: float = 1.5,
    min_separation_m: float = 20.0,
    custom_query: dict[str, float] | None = None,
    closure_grid: list[dict[str, Any]] | None = None,
    # ── fault_sticks / volume / blend ──
    source_uri: str = "",
    source_type: str = "csv",
    action: str = "get",
    volume_ref: str = "",
    frame_index: int = 0,
    orientation: str = "inline",
    provenance: str = "fixture",
    image_data: str | None = None,
    blend_mode: str = "alpha",
    # ── section / RSI / structure / SEG-Y ──
    image_path: str | None = None,
    artifact_ref: str | None = None,
    framework: dict[str, Any] | None = None,
    faults: list[dict[str, Any]] | None = None,
    horizons: list[dict[str, Any]] | None = None,
    measurement_context: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    earth_constraints: dict[str, Any] | None = None,
    request: dict[str, Any] | None = None,
    segy_path: str | None = None,
    max_faults: int = 20,
    max_horizons: int = 12,
    emit_bundle: bool = True,
    # ── MCP transport envelope (declared in TransportAwareRequest) ──
    # Must be explicit on the handler signature so they actually flow
    # through to provenance. FastMCP rejects **kwargs on tools, so each
    # transport field is declared by name. The schema layer (extra=forbid
    # + TransportAwareRequest) guarantees typos here trip loudly.
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
    source_sha256: str | None = None,
    # ── legacy ──
    horizon_query: str = "unconformity",
    threshold: float = 0.5,
    confidence_cap: float = 0.9,
    cube_ref: str | None = None,
    volume_inline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Unified seismic interpretation — public modes.

    Local engine verdicts are QUALIFIED_CANDIDATE at most — arifOS seals.
    preferred_hypothesis is never set by GEOX.

    Transport metadata (session_id, actor_id, trace_id, source_sha256) is
    declared on the schema (TransportAwareRequest) AND on this signature,
    so it survives both validation and dispatch.
    """
    # Inject transport into a single dict we propagate everywhere
    _transport: dict[str, Any] = {
        "session_id": session_id,
        "actor_id": actor_id,
        "trace_id": trace_id,
        "source_sha256": source_sha256,
    }
    mode_norm = (mode or "horizon_contrast").strip().lower()

    if mode_norm == "contrast":
        mode_norm = "horizon_contrast"
    if mode_norm in ("section_image", "classical_section"):
        # classical_section: declared image-first propose path (structure tensor / RSI)
        mode_norm = "interpret_section"
    if mode_norm == "segy_2d":
        mode_norm = "segy_slice"
    if mode_norm == "cutoff_throw":
        mode_norm = "measure_throw"

    # ── F1 zen: track_horizon ──
    if mode_norm == "track_horizon":
        from geox_mcp.tools.seismic_zen_f1 import zen_track_horizon

        result = await zen_track_horizon(
            image_path=image_path or artifact_ref or source_uri or None,
            amplitude_grid=(request or {}).get("amplitude_grid") if isinstance(request, dict) else None,
            volume_inline=volume_inline,
            max_horizons=max_horizons,
            seed_rows=(request or {}).get("seed_rows") if isinstance(request, dict) else None,
            provenance=provenance or "fixture",
            request=request,
        )
        return _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm, _transport)

    # ── F1 zen: measure_throw → optional structure_validate ──
    if mode_norm == "measure_throw":
        from geox_mcp.tools.seismic_zen_f1 import zen_measure_throw

        result = await zen_measure_throw(
            horizons=horizons,
            faults=faults,
            image_path=image_path or artifact_ref or source_uri or None,
            amplitude_grid=(request or {}).get("amplitude_grid") if isinstance(request, dict) else None,
            volume_inline=volume_inline,
            max_horizons=max_horizons,
            calibration=calibration,
            request=request,
            provenance=provenance or "fixture",
            run_gates=bool((request or {}).get("run_gates", True)) if isinstance(request, dict) else True,
        )
        return _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm, _transport)

    if mode_norm in _NOT_YET_MODES and mode_norm not in _LIVE_MODES:
        return {
            "ok": False,
            "tool": "geox_seismic_interpret",
            "mode": mode,
            "error": "MODE_NOT_PUBLIC",
            "message": _NOT_YET_MODES[mode_norm],
            "live_modes": sorted(_LIVE_MODES),
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
            "claim_tag": "HYPOTHESIS",
            "hint": "Use live_modes only.",
        }

    if mode_norm not in _LIVE_MODES:
        return {
            "ok": False,
            "tool": "geox_seismic_interpret",
            "mode": mode,
            "error": "UNKNOWN_MODE",
            "message": f"Unknown mode '{mode}'. Live: {sorted(_LIVE_MODES)}",
            "live_modes": sorted(_LIVE_MODES),
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
        }

    # ── structure_validate ──
    if mode_norm == "structure_validate":
        from geox_mcp.tools.structure_validate import geox_structure_validate as _impl

        hyp_n = 3
        if isinstance(request, dict) and request.get("hypothesis_count"):
            hyp_n = int(request["hypothesis_count"])
        result = await _impl(
            framework=framework,
            faults=faults,
            horizons=horizons,
            measurement_context=measurement_context,
            calibration=calibration,
            earth_constraints=earth_constraints,
            emit_bundle=emit_bundle,
            hypothesis_count=hyp_n,
        )
        stamped = _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm, transport=_transport)
        stamped["preferred_hypothesis"] = None
        return stamped

    # ── classical_section: image-first PRIMARY propose baseline ──
    if mode_norm == "classical_section":
        path = image_path or artifact_ref or source_uri or ""
        if not path:
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "classical_section",
                "error": "MISSING_IMAGE_PATH",
                "message": "classical_section requires image_path (absolute host path to section PNG/JPG).",
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "input_class": "image_only",
                "epistemic_label": "INT_SEISMIC",
            }
        from geox_mcp.tools.classical_section_propose import geox_classical_section_propose as _cv

        result = await _cv(
            image_path=path,
            max_faults=max_faults,
            max_horizons=max_horizons,
            run_gates=False,  # gates on mode=interpret / structure_validate only
            calibration=calibration or {"input_class": "image_only", "calibrated": False},
        )
        if not isinstance(result, dict):
            result = {"data": result}
        if emit_bundle and result.get("framework") and not result.get("interpretation_bundle"):
            from geox_mcp.domain.seismic_interpret.bundle import build_interpretation_bundle

            result["interpretation_bundle"] = build_interpretation_bundle(
                frameworks_or_primary=result["framework"],
                observations=result.get("observations"),
                calibration=calibration or {"input_class": "image_only"},
                request=request or {"hypothesis_count": 3},
                model_revision="classical_section_v1",
            )
            result["preferred_hypothesis"] = None
        return _stamp_qualified(result, mode_norm)

    # ── interpret: classical propose (if image) → validate → compare ──
    if mode_norm == "interpret":
        from geox_mcp.domain.seismic_interpret.bundle import build_interpretation_bundle
        from geox_mcp.tools.structure_validate import geox_structure_validate as _sv

        path = image_path or artifact_ref or source_uri or ""
        fw: dict[str, Any] = dict(framework or {})
        if faults is not None:
            fw["faults"] = faults
        if horizons is not None:
            fw["horizons"] = horizons
        propose_result = None
        if path and not fw.get("faults") and not fw.get("horizons"):
            from geox_mcp.tools.classical_section_propose import (
                geox_classical_section_propose as _cv,
            )

            propose_result = await _cv(
                image_path=path,
                max_faults=max_faults,
                max_horizons=max_horizons,
                run_gates=False,
                calibration=calibration or {"input_class": "image_only", "calibrated": False},
            )
            if isinstance(propose_result, dict) and propose_result.get("framework"):
                pf = propose_result["framework"]
                fw.setdefault("faults", pf.get("faults") or [])
                fw.setdefault("horizons", pf.get("horizons") or [])
                if pf.get("measurement_context"):
                    fw.setdefault("measurement_context", pf["measurement_context"])
        if fw.get("faults") or fw.get("horizons") or fw.get("velocity"):
            sv = await _sv(
                framework=fw,
                measurement_context=measurement_context or fw.get("measurement_context"),
                calibration=calibration or {"input_class": "image_only" if path else "unknown", "calibrated": False},
                earth_constraints=earth_constraints,
                emit_bundle=True,
                hypothesis_count=int((request or {}).get("hypothesis_count") or 3),
            )
            bundle = sv.get("interpretation_bundle") or sv
            return _stamp_qualified(
                {
                    **(bundle if isinstance(bundle, dict) else {}),
                    "ok": True,
                    "structure_validate": {
                        k: sv.get(k)
                        for k in (
                            "combined_gate_verdict",
                            "kills",
                            "passes",
                            "unmeasured",
                            "gates",
                        )
                    },
                    "propose": {
                        "ran": propose_result is not None,
                        "method": "classical_section",
                        "n_faults": (propose_result or {}).get("n_faults"),
                        "n_horizons": (propose_result or {}).get("n_horizons"),
                    },
                    "preferred_hypothesis": None,
                },
                mode_norm,
                transport=_transport,
            )
        cal = calibration or {"input_class": "image_only" if path else "unknown"}
        bundle = build_interpretation_bundle(
            propose_result=propose_result if isinstance(propose_result, dict) else None,
            calibration=cal,
            earth_constraints=earth_constraints,
            request=request or {"hypothesis_count": 3},
        )
        if not path and not fw:
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "interpret",
                "error": "MISSING_INPUT",
                "message": "interpret requires framework faults/horizons and/or image_path/artifact_ref.",
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
            }
        return _stamp_qualified(bundle, mode_norm, transport=_transport)

    # ── rsi_pipeline: legacy RSI-only (comparator, not primary product) ──
    if mode_norm == "rsi_pipeline":
        path = image_path or artifact_ref or source_uri or ""
        if not path:
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": mode_norm,
                "error": "MISSING_IMAGE_PATH",
                "message": "rsi_pipeline requires image_path (absolute host path).",
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "input_class": "image_only",
                "epistemic_label": "INT_SEISMIC",
            }
        from geox_mcp.tools.seismic_rsi import geox_rsi_interpret as _rsi

        result = await _rsi(
            image_path=path,
            mode="horizon_fault_pick",
            max_faults=max_faults,
            max_horizons=max_horizons,
        )
        if not isinstance(result, dict):
            result = {"data": result}
        result["ok"] = result.get("verdict") not in ("VOID",)
        result["input_class"] = "image_only"
        result["epistemic_label"] = "INT_SEISMIC"
        result["capability_note"] = (
            "Legacy RSI propose (comparator). Prefer mode=classical_section for product path. "
            "Pixel domain ≠ subsurface. arifOS SEAL only."
        )
        alts = result.get("alternatives")
        if not alts:
            result["alternatives"] = [
                {"model_id": "through_going", "prior": "primary RSI pick set"},
                {"model_id": "relay_segmented", "prior": "faults as relays / hard-linked segments"},
                {"model_id": "artifact_dominant", "prior": "picks dominated by acquisition/processing artifacts"},
            ]
        if emit_bundle:
            from geox_mcp.domain.seismic_interpret.bundle import build_interpretation_bundle

            cal = calibration or {"input_class": "image_only", "calibrated": False}
            result["interpretation_bundle"] = build_interpretation_bundle(
                propose_result=result,
                calibration=cal,
                earth_constraints=earth_constraints,
                request=request or {"hypothesis_count": 3},
            )
            result["preferred_hypothesis"] = None
        return _stamp_qualified(result, mode_norm, transport=_transport)

    # ── segy_slice ──
    if mode_norm == "segy_slice":
        path = segy_path or source_uri or volume_ref or cube_ref or ""
        if not path:
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "segy_slice",
                "error": "MISSING_SEGY_PATH",
                "message": "segy_slice requires segy_path or source_uri to a SEG-Y file.",
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
            }
        from geox_mcp.tools.seismic_segy_slice import geox_segy_slice as _segy

        result = await _segy(
            segy_path=path,
            frame_index=frame_index or 0,
            orientation=orientation or "inline",
        )
        return _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm, transport=_transport)

    if mode_norm == "fault_sticks":
        from geox_mcp.tools.paleoscan_forge import geox_fault_stick_ingest_tool as _impl

        return await _impl(source_uri=source_uri or "", source_type=source_type or "csv")

    if mode_norm == "volume_frame":
        from geox_mcp.tools.paleoscan_forge import geox_volume_frame_tool as _impl

        if not (volume_ref or "").strip():
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "volume_frame",
                "error": "MISSING_REQUIRED_FIELD",
                "message": "volume_frame requires volume_ref (ingested seismic volume artifact id).",
                "required_params": ["volume_ref"],
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "claim_tag": "VOID",
            }
        return await _impl(
            action=action or "get",
            volume_ref=volume_ref or "",
            frame_index=frame_index or 0,
            orientation=orientation or "inline",
            provenance=provenance or "fixture",
            image_data=image_data,
        )

    if mode_norm == "blend":
        from geox_mcp.tools.paleoscan_forge import geox_blend_volume_tool as _impl

        # Contract: alpha needs volume_ref_1+2; RGB needs red/green/blue refs.
        # Do not pass a single volume_ref (TypeError + silent mis-dispatch).
        if not volume_ref and not (request and isinstance(request, dict)):
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "blend",
                "error": "MISSING_REQUIRED_FIELD",
                "message": (
                    "blend requires volume refs: alpha → volume_ref_1+volume_ref_2 "
                    "(pass via request={...}); RGB → volume_ref_red/green/blue."
                ),
                "required_params": ["volume_ref_1", "volume_ref_2"],
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "claim_tag": "VOID",
            }
        blend_kwargs: dict[str, Any] = {"blend_mode": blend_mode or "alpha"}
        if isinstance(request, dict):
            for k in (
                "volume_ref_1",
                "volume_ref_2",
                "volume_ref_3",
                "volume_ref_red",
                "volume_ref_green",
                "volume_ref_blue",
                "alpha",
            ):
                if k in request:
                    blend_kwargs[k] = request[k]
        # legacy single volume_ref is insufficient — still declare contract
        if not any(blend_kwargs.get(k) for k in ("volume_ref_1", "volume_ref_red")):
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "blend",
                "error": "MISSING_REQUIRED_FIELD",
                "message": "blend missing volume_ref_1/volume_ref_2 (or RGB refs) in request.",
                "required_params": ["volume_ref_1", "volume_ref_2"],
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "claim_tag": "VOID",
            }
        return await _impl(**blend_kwargs)

    # ── horizon_contrast ──
    attrs = attribute_data
    depths = depth
    if volume_inline and isinstance(volume_inline, dict):
        attrs = attrs or volume_inline.get("attribute_data")
        depths = depths or volume_inline.get("depth")
        if well_ties is None:
            well_ties = volume_inline.get("well_ties")
        if not geological_query or geological_query == "sequence_boundary":
            geological_query = volume_inline.get("geological_query") or geological_query

    if not attrs or not depths:
        return {
            "ok": False,
            "tool": "geox_seismic_interpret",
            "mode": "horizon_contrast",
            "error": "MISSING_REQUIRED_FIELD",
            "message": (
                "horizon_contrast requires attribute_data (dict attr→array) and depth (list[float]). "
                "This is a 1D multi-attribute boundary detector — not a 2D section picker."
            ),
            "required_params": ["attribute_data", "depth"],
            "live_modes": sorted(_LIVE_MODES),
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
            "hint": ("Use mode=segy_slice for MeasurementContext, or build 1D profiles then pass attribute_data+depth."),
        }

    attrs = dict(attrs)
    if "amplitude" in attrs and "seismic_amplitude" not in attrs and "acoustic_impedance" not in attrs:
        vals = attrs["amplitude"]
        try:
            mx = max(abs(float(v)) for v in vals if v is not None)
        except Exception:
            mx = 0.0
        if mx > 100.0:
            attrs["acoustic_impedance"] = attrs.pop("amplitude")
        else:
            attrs["seismic_amplitude"] = attrs.pop("amplitude")

    from geox_mcp.tools.horizon_contrast import geox_horizon_contrast_surface as _impl

    gq = geological_query or horizon_query or "sequence_boundary"
    if horizon_query and geological_query == "sequence_boundary" and horizon_query != "unconformity":
        gq = geological_query if geological_query != "sequence_boundary" else horizon_query

    result = await _impl(
        attribute_data=attrs,
        depth=list(depths),
        mode="full",
        geological_query=gq,
        well_ties=well_ties,
        stratigraphic_framework=stratigraphic_framework,
        peak_threshold=peak_threshold if peak_threshold else threshold,
        min_separation_m=min_separation_m,
        custom_query=custom_query,
        closure_grid=closure_grid,
    )

    if isinstance(result, dict):
        result = _stamp_qualified(result, "horizon_contrast", transport=_transport)
        result["capability_note"] = (
            "1D multi-attribute boundary detector. Not HorizonSurface3D. "
            "Not structural framework. Agent proposes; GEOX assists; Arif seals."
        )
    return result
