"""
geox_seismic_interpret — Seismic Interpretation (Phase 2 + P0/C/A/D 2026-07-23)
════════════════════════════════════════════════════════════════════════════════
Live modes (public, callable):
  horizon_contrast   — 1D multi-attribute boundary detector (ToAC)
  fault_sticks       — Fault stick CSV/GeoJSON ingest (not auto-extract)
  volume_frame       — Volume frame read/write
  blend              — Alpha/RGB volume blending
  structure_validate — G2–G9 + K-* structural falsifier
  interpret_section  — RSI image-true propose (INT_SEISMIC, QUALIFIED_CANDIDATE)
  rsi_pipeline       — thin alias → geox_rsi_interpret (F13 execute-all 2026-07-23)
  segy_slice         — Phase D: SEG-Y → MeasurementContext + amplitude stats

Still HOLD (not public-executable):
  vision, track_horizon, extract_faults, build_structure, observe_image, falsify

Local engine verdicts are QUALIFIED_CANDIDATE at most — arifOS seals.
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
        "interpret_section",
        "rsi_pipeline",
        "segy_slice",
    }
)

# Manifest-claimed but not public-executable — deliberate HOLD, not silent remaps
_NOT_YET_MODES: dict[str, str] = {
    "contrast": "Alias of horizon_contrast — pass mode=horizon_contrast with attribute_data+depth.",
    "vision": (
        "Vision modes (geox_visual_understand / geox_vision_*) are separate tools. "
        "geox_seismic_interpret does not run VLM. Call geox_visual_understand for OBS_IMAGE."
    ),
    "track_horizon": "P1 not built — phase-consistent 2D/3D tracking not on public surface.",
    "extract_faults": "Auto fault-plane extraction not proven. Use fault_sticks ingest or interpret_section.",
    "build_structure": "Use structure_validate on a proposed framework; full build_structure loop later.",
    "falsify": "Use geox_falsify (claim_type=structural_*) for claim physics checks.",
    "observe_image": "Use geox_visual_understand for OBS_IMAGE (HOLD without VLM).",
}


def _stamp_qualified(result: dict[str, Any], mode: str) -> dict[str, Any]:
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
    return result


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
    framework: dict[str, Any] | None = None,
    faults: list[dict[str, Any]] | None = None,
    horizons: list[dict[str, Any]] | None = None,
    measurement_context: dict[str, Any] | None = None,
    segy_path: str | None = None,
    max_faults: int = 20,
    max_horizons: int = 12,
    # ── legacy ──
    horizon_query: str = "unconformity",
    threshold: float = 0.5,
    confidence_cap: float = 0.9,
    cube_ref: str | None = None,
    volume_inline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Unified seismic interpretation — public modes.

    Local engine verdicts are QUALIFIED_CANDIDATE at most — arifOS seals.
    """
    mode_norm = (mode or "horizon_contrast").strip().lower()

    if mode_norm == "contrast":
        mode_norm = "horizon_contrast"

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

        result = await _impl(
            framework=framework,
            faults=faults,
            horizons=horizons,
            measurement_context=measurement_context,
        )
        return _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm)

    # ── interpret_section / rsi_pipeline ──
    if mode_norm in ("interpret_section", "rsi_pipeline"):
        path = image_path or source_uri or ""
        if not path:
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": mode_norm,
                "error": "MISSING_IMAGE_PATH",
                "message": "interpret_section/rsi_pipeline requires image_path (absolute host path).",
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
            "RSI image-true propose. Pixel domain ≠ subsurface. "
            "Not OBS_GEOLOGY. Run structure_validate on picks. arifOS SEAL only."
        )
        # Ensure ≥3 alternatives always (G1) — pad from RSI alternatives if thin
        alts = result.get("alternatives")
        if not alts:
            result["alternatives"] = [
                {"model_id": "through_going", "prior": "primary RSI pick set"},
                {"model_id": "relay_segmented", "prior": "faults as relays / hard-linked segments"},
                {"model_id": "artifact_dominant", "prior": "picks dominated by acquisition/processing artifacts"},
            ]
        return _stamp_qualified(result, mode_norm)

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
        return _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm)

    if mode_norm == "fault_sticks":
        from geox_mcp.tools.paleoscan_forge import geox_fault_stick_ingest_tool as _impl

        return await _impl(source_uri=source_uri or "", source_type=source_type or "csv")

    if mode_norm == "volume_frame":
        from geox_mcp.tools.paleoscan_forge import geox_volume_frame_tool as _impl

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

        return await _impl(
            blend_mode=blend_mode or "alpha",
            volume_ref=volume_ref or "",
            provenance=provenance or "fixture",
        )

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
            "hint": (
                "Use mode=segy_slice for MeasurementContext, or build 1D profiles then pass attribute_data+depth."
            ),
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
        result = _stamp_qualified(result, "horizon_contrast")
        result["capability_note"] = (
            "1D multi-attribute boundary detector. Not HorizonSurface3D. "
            "Not structural framework. Agent proposes; GEOX assists; Arif seals."
        )
    return result
