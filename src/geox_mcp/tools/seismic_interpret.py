"""
geox_seismic_interpret — Seismic Interpretation (Phase 2)
═════════════════════════════════════════════════════════
Absorbs: geox_horizon_contrast_surface, geox_fault_stick_ingest_tool,
         geox_volume_frame_tool, geox_blend_volume_tool

Modes: horizon_contrast, fault_sticks, volume_frame, blend

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any, Literal


async def geox_seismic_interpret(
    mode: Literal["horizon_contrast", "fault_sticks", "volume_frame", "blend"] = "horizon_contrast",
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
) -> dict[str, Any]:
    """Unified seismic interpretation.

    Modes:
      horizon_contrast - ToAC-as-Attention horizon detection pipeline
      fault_sticks     - Fault stick CSV/GeoJSON ingest
      volume_frame     - Volume frame read/write (inline/crossline/time)
      blend            - Alpha/RGB volume blending
    """
    kwargs = locals().copy()
    if mode == "fault_sticks":
        from geox_mcp.tools.paleoscan_forge import geox_fault_stick_ingest_tool as _impl

        return await _impl(
            source_uri=kwargs.get("source_uri", ""),
            source_type=kwargs.get("source_type", "csv"),
        )

    if mode == "volume_frame":
        from geox_mcp.tools.paleoscan_forge import geox_volume_frame_tool as _impl

        return await _impl(
            action=kwargs.get("action", "get"),
            volume_ref=kwargs.get("volume_ref", ""),
            frame_index=kwargs.get("frame_index", 0),
            orientation=kwargs.get("orientation", "inline"),
            provenance=kwargs.get("provenance", "fixture"),
            image_data=kwargs.get("image_data"),
        )

    if mode == "blend":
        from geox_mcp.tools.paleoscan_forge import geox_blend_volume_tool as _impl

        return await _impl(
            blend_mode=kwargs.get("blend_mode", "alpha"),
            **{k: v for k, v in kwargs.items() if k != "mode"},
        )

    # Default: horizon_contrast
    from geox_mcp.tools.horizon_contrast import geox_horizon_contrast_surface as _impl

    # ZEN fix 2026-07-20: map MCP surface params to impl params.
    # horizon_contrast_surface expects attribute_data + depth arrays,
    # not the file-level source_uri/action params. If caller passed
    # file-level params without computed attribute data, signal clearly.
    has_attribute_data = "attribute_data" in kwargs and kwargs["attribute_data"] is not None
    has_source = kwargs.get("source_uri") or kwargs.get("volume_ref")

    if not has_attribute_data:
        if has_source:
            return {
                "ok": False,
                "error": "horizon_contrast requires pre-computed attribute_data + depth arrays.",
                "hint": "Use geox_seismic_compute(mode='attribute') first to compute attributes, then pass attribute_data and depth arrays.",
                "provided_params": {
                    k: v for k, v in kwargs.items() if k in ("source_uri", "volume_ref", "frame_index", "orientation") and v
                },
                "required_params": ["attribute_data", "depth"],
                "tool": "geox_seismic_interpret",
            }
        return {
            "ok": False,
            "error": "horizon_contrast requires attribute_data (dict of attribute→array) and depth (list of floats).",
            "required_params": ["attribute_data", "depth"],
            "tool": "geox_seismic_interpret",
        }

    # Filter to only impl-accepted params
    import inspect as _inspect

    _sig = _inspect.signature(_impl)
    _accepted = set(_sig.parameters.keys())
    _filtered = {k: v for k, v in kwargs.items() if k in _accepted and k != "mode"}
    return await _impl(**_filtered)
