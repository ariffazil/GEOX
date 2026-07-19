"""
GEOX Panel D — Async MCP Wrapper
═════════════════════════════════════
epistemic: INT_SEISMIC → DER_COGNITIVE_RENDER
DITEMPA BUKAN DIBERI — Forged 2026-07-06.
"""

from __future__ import annotations

import asyncio
from typing import Any

from geox_mcp.tools.geox_panel_d import render_cognitive_panel


async def geox_panel_d_render_async(
    attrs: Any,
    fp: Any,
    faults: Any,
    horizons: Any,
    packages: Any,
    terminations: Any,
    artifacts: Any,
    hypotheses: Any,
    raw_arr: Any,
    crop_bbox: Any,
    prov: Any,
    output_dir: str,
) -> dict[str, Any]:
    """Render the Cognitive Interpretation Dashboard (Panel D)."""
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: render_cognitive_panel(
            attrs, fp, faults, horizons, packages, terminations, artifacts, hypotheses, raw_arr, crop_bbox, prov, output_dir
        ),
    )
    return {"status": "DER_COGNITIVE_RENDER", "output_path": result}
