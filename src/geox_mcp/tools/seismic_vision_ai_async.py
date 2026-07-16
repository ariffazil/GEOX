"""
GEOX Seismic Vision AI — MCP Tool Wrapper
══════════════════════════════════════════
DEPRECATED 2026-07-16 — All 4 tools deregistered from MCP since 2026-07-10.
This wrapper exists for backward compat only. Canonical: seismic_vision_ai.py.
Do NOT re-register without sovereign approval.

Async wrapper for geox_seismic_vision_ai.py sync functions.
Four modes map to the cognitive visual AI taxonomy:
  geox_visual_understand      → OBS_IMAGE
  geox_visual_enhance        → DER_RENDER_ENHANCEMENT
  geox_visual_generate_hypotheses → GEN_HYPOTHESIS
  geox_panel_d_render        → DER_COGNITIVE_RENDER

DITEMPA BUKAN DIBERI — Forged 2026-07-06 under F13 SOVEREIGN.
"""

from __future__ import annotations
import asyncio
from typing import Any

from geox_mcp.tools.seismic_vision_ai import (  # noqa: F401
    geox_visual_understand,
    geox_visual_enhance,
    geox_visual_generate_hypotheses,
    geox_panel_d_render,
)


async def geox_visual_understand_async(image_path: str, mode: str = "full") -> dict[str, Any]:
    """Async wrapper — geox_visual_understand."""
    return await asyncio.get_event_loop().run_in_executor(None, geox_visual_understand, image_path, mode, None)


async def geox_visual_enhance_async(
    image_path: str, output_path: str, enhancement_mode: str = "contrast_normalize"
) -> dict[str, Any]:
    """Async wrapper — geox_visual_enhance."""
    return await asyncio.get_event_loop().run_in_executor(None, geox_visual_enhance, image_path, output_path, enhancement_mode)


async def geox_visual_generate_hypotheses_async(
    image_path: str, output_dir: str, target_feature_id: str, hypotheses: list[str]
) -> dict[str, Any]:
    """Async wrapper — geox_visual_generate_hypotheses."""
    return await asyncio.get_event_loop().run_in_executor(
        None, geox_visual_generate_hypotheses, image_path, output_dir, target_feature_id, hypotheses
    )


async def geox_panel_d_render_async(
    base_image_path: str, output_path: str, obs_manifest: dict, cognitive_manifest: dict
) -> dict[str, Any]:
    """Async wrapper — geox_panel_d_render."""
    return await asyncio.get_event_loop().run_in_executor(
        None, geox_panel_d_render, base_image_path, output_path, obs_manifest, cognitive_manifest
    )
