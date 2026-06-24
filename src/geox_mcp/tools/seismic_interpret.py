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
    return await _impl(**{k: v for k, v in kwargs.items() if k != "mode"})
