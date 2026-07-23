"""
geox_seismic_interpret — Seismic Interpretation (Phase 2 + P0 truth fix 2026-07-23)
════════════════════════════════════════════════════════════════════════════════
Absorbs: geox_horizon_contrast_surface, geox_fault_stick_ingest_tool,
         geox_volume_frame_tool, geox_blend_volume_tool

Live modes (public, callable):
  horizon_contrast — 1D multi-attribute boundary detector (ToAC)
  fault_sticks     — Fault stick CSV/GeoJSON ingest (not auto-extract)
  volume_frame     — Volume frame read/write
  blend            — Alpha/RGB volume blending

Aliased / not-yet-public modes return honest HOLD with required path:
  rsi_pipeline, contrast, vision, interpret_section, track_horizon, extract_faults

P0 fix: attribute_data + depth are first-class parameters on the public signature
so horizon_contrast is reachable (additionalProperties was blocking them).

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any, Literal

# Modes the handler can execute today
_LIVE_MODES = frozenset({"horizon_contrast", "fault_sticks", "volume_frame", "blend"})

# Manifest-claimed but not public-executable — deliberate HOLD, not silent remaps
_NOT_YET_MODES: dict[str, str] = {
    "rsi_pipeline": (
        "RSI pipeline is internal-only (geox_rsi_interpret). "
        "Not on public surface by sovereign rule — promote only with F13 call."
    ),
    "contrast": "Alias of horizon_contrast — pass mode=horizon_contrast with attribute_data+depth.",
    "vision": (
        "Vision modes (geox_visual_understand / geox_vision_*) are separate tools. "
        "geox_seismic_interpret does not run VLM. Call geox_visual_understand for OBS_IMAGE."
    ),
    "interpret_section": "P1 not built — requires 2D amplitude[trace,sample] grid + physics gates.",
    "track_horizon": "P1 not built — phase-consistent 2D/3D tracking not on public surface.",
    "extract_faults": "Auto fault-plane extraction not proven. Use fault_sticks ingest only.",
    "build_structure": "P1 structural framework loop not built.",
    "falsify": "Use geox_falsify for claim physics checks; wire K-* gates in P1.",
    "observe_image": "Use geox_visual_understand for OBS_IMAGE (note: VLM may be template without callback).",
}


async def geox_seismic_interpret(
    mode: str = "horizon_contrast",
    # ── horizon_contrast inputs (P0: public schema must accept these) ──
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
    # ── legacy / unused surface noise (kept for schema stability) ──
    horizon_query: str = "unconformity",
    threshold: float = 0.5,
    confidence_cap: float = 0.9,
    cube_ref: str | None = None,
    volume_inline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Unified seismic interpretation — public modes only.

    horizon_contrast requires:
      attribute_data: dict of attr_name → list[float] (same length as depth)
      depth: list[float] in metres (or TWT if caller labels as such — units on caller)

    Attribute keys (preferred, P0 typed):
      seismic_amplitude | acoustic_impedance | coherence | phase | frequency | curvature
      Legacy key 'amplitude' is treated as seismic_amplitude unless values look like AI (>>100).

    Local engine verdicts are QUALIFIED_CANDIDATE at most — arifOS seals.
    """
    mode_norm = (mode or "horizon_contrast").strip().lower()

    # ── Mode aliases (explicit, not silent remaps to wrong errors) ──
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
            "local_verdict": "QUALIFIED_CANDIDATE",  # never local SEAL
            "claim_tag": "HYPOTHESIS",
            "hint": "Use live_modes only, or F13-promote internal tools deliberately.",
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
    # Prefer explicit params; also accept nested volume_inline for host convenience
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
            "optional_params": [
                "geological_query",
                "well_ties",
                "peak_threshold",
                "min_separation_m",
                "custom_query",
            ],
            "typed_attribute_keys": [
                "seismic_amplitude",
                "acoustic_impedance",
                "coherence",
                "phase",
                "frequency",
                "curvature",
            ],
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
            "hint": (
                "Build 1D profiles from SEG-Y inline first (geox_seismic_compute / volume_frame), "
                "then pass attribute_data+depth. Do not pass only source_uri."
            ),
        }

    # Normalize legacy 'amplitude' key semantics for horizon_contrast
    attrs = dict(attrs)
    if "amplitude" in attrs and "seismic_amplitude" not in attrs and "acoustic_impedance" not in attrs:
        vals = attrs["amplitude"]
        try:
            mx = max(abs(float(v)) for v in vals if v is not None)
        except Exception:
            mx = 0.0
        if mx > 100.0:
            # Looks like AI — rekey
            attrs["acoustic_impedance"] = attrs.pop("amplitude")
        else:
            attrs["seismic_amplitude"] = attrs.pop("amplitude")

    from geox_mcp.tools.horizon_contrast import geox_horizon_contrast_surface as _impl

    # geological_query: allow horizon_query alias from old surface
    gq = geological_query or horizon_query or "sequence_boundary"
    if horizon_query and geological_query == "sequence_boundary" and horizon_query != "unconformity":
        # prefer explicit geological_query; if only horizon_query set via old clients
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

    # Stamp public contract: local engine never SEAL
    if isinstance(result, dict):
        result.setdefault("tool", "geox_seismic_interpret")
        result["mode"] = "horizon_contrast"
        result["local_verdict"] = "QUALIFIED_CANDIDATE"
        result["seal_authority"] = "arifOS_only"
        result["capability_note"] = (
            "1D multi-attribute boundary detector. Not HorizonSurface3D. "
            "Not structural framework. Agent proposes; GEOX assists; Arif seals."
        )
        # Downgrade any local SEAL string in nested envelope
        gov = result.get("governance_status") or result.get("governance", {})
        if gov == "SEAL" or (isinstance(gov, dict) and gov.get("status") == "SEAL"):
            result["governance_status"] = "QUALIFY"
            result["governance_note"] = "Local SEAL remapped to QUALIFY — arifOS seals only"
        if isinstance(result.get("result"), dict):
            # nested standard envelope
            pass
    return result
