"""
GEOX Physical Reality — Async MCP Wrapper
═════════════════════════════════════════
Entry: geox_physical_reality.GeoxPhysicalReality.interpret()
DITEMPA BUKAN DIBERI — Forged 2026-07-06.
"""

from __future__ import annotations
import asyncio
from typing import Any

from geox_mcp.tools.geox_physical_reality import GeoxPhysicalReality


async def geox_physical_reality_interpret(image_path: str, output_dir: str = "/tmp") -> dict[str, Any]:
    """Physical reality interpreter — multi-attribute panel, horizon picks, fault extraction.

    epistemic: OBS_IMAGE → DER_ATTRIBUTE → INT_SEISMIC
    """
    result = await asyncio.get_event_loop().run_in_executor(None, lambda: GeoxPhysicalReality().interpret(image_path, output_dir))
    # interpret() returns 'verdict', not 'status' — normalize for MCP envelope
    if "verdict" in result and "status" not in result:
        result["status"] = result["verdict"]
    return result
