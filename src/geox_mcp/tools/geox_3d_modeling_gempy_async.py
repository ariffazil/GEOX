"""
GEOX 3D Modeling (GemPy) — Async MCP Wrapper
═════════════════════════════════════════════
Entry: geox_3d_modeling_gempy.run_gempy_3d_model()
epistemic: INT_SEISMIC → INT_3D_STRUCTURE (requires well tie calibration)
DITEMPA BUKAN DIBERI — Forged 2026-07-06.
"""

from __future__ import annotations
import asyncio
from typing import Any

from geox_mcp.tools.geox_3d_modeling_gempy import run_gempy_3d_model


async def geox_3d_model(model_json_path: str, output_dir: str) -> dict[str, Any]:
    """Build 3D implicit structural model from 2D horizon/fault picks using GemPy.

    Returns: GemPy model manifest, lithology grid, block model summary.
    """
    return await asyncio.get_event_loop().run_in_executor(None, lambda: run_gempy_3d_model(model_json_path, output_dir))
