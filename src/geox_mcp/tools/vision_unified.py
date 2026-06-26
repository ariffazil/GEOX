"""
geox_vision — Unified Vision Interpretation (Phase 2)
══════════════════════════════════════════════════════
Absorbs: geox_vision_minimax_inference, geox_vision_mimo_inference (ghost),
         geox_vision_audit, geox_vision_calibrate, geox_vision_perceptual_inventory

Modes: infer_minimax, infer_mimo, audit, calibrate, perceptual

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations
from typing import Any, Literal

async def geox_vision(
    mode: Literal["infer_minimax", "infer_mimo", "audit", "calibrate", "perceptual"] = "infer_minimax",
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
) -> dict[str, Any]:
    """Unified vision-based seismic interpretation.

    Modes:
      infer_minimax - MiniMax M3 VLM inference on seismic sections
      infer_mimo    - MiMo Embodied-7B native multimodal inference
      audit         - AC_Risk scoring and VisionVerdict
      calibrate     - Synthetic forward-inverse calibration harness
      perceptual    - Build perceptual inventory from explicit inputs
    """
    kwargs = locals().copy()
    if mode == "infer_mimo":
        from geox_mcp.tools.vision import geox_vision_mimo_inference as _impl
        return await _impl(
            image_path=kwargs.get("image_path", ""),
            basin_context=kwargs.get("basin_context", "unknown"),
            interpretation_goal=kwargs.get("interpretation_goal", "Identify structural features"),
            has_segy=kwargs.get("has_segy", False),
            mimo_backend_url=kwargs.get("mimo_backend_url"),
            mimo_model=kwargs.get("mimo_model"),
        )

    if mode == "audit":
        from geox_mcp.tools.vision import geox_vision_audit as _impl
        return await _impl(**{k: v for k, v in kwargs.items() if k != "mode"})

    if mode == "calibrate":
        from geox_mcp.tools.vision import geox_vision_calibrate as _impl
        return await _impl(**{k: v for k, v in kwargs.items() if k != "mode"})

    if mode == "perceptual":
        from geox_mcp.tools.vision import geox_vision_perceptual_inventory as _impl
        return await _impl(
            image_path=kwargs.get("image_path", ""),
            model_id=kwargs.get("model_id", "minimax-M3-vision"),
            **{k: v for k, v in kwargs.items() if k not in ("mode", "image_path", "model_id")},
        )

    # Default: infer_minimax
    from geox_mcp.tools.vision import geox_vision_minimax_inference as _impl
    return await _impl(
        image_path=kwargs.get("image_path", ""),
        basin_context=kwargs.get("basin_context", "unknown"),
        interpretation_goal=kwargs.get("interpretation_goal", "Identify structural features"),
        has_segy=kwargs.get("has_segy", False),
        mcp_url=kwargs.get("mcp_url"),
    )
