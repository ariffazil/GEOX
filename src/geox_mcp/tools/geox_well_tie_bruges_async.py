"""
GEOX Well Tie (Bruges) — Async MCP Wrapper
═══════════════════════════════════════════
Entry: geox_well_tie_bruges.run_well_tie()
epistemic: OBS_WELL_LOG → DER_WELL_TWT → DER_SYNTHETIC → INT_GEOLOGY_HORIZON
DITEMPA BUKAN DIBERI — Forged 2026-07-06.
"""

from __future__ import annotations
import asyncio
from typing import Any

from geox_mcp.tools.geox_well_tie_bruges import run_well_tie


async def geox_well_tie(
    las_path: str,
    segy_audit_path: str,
    output_dir: str,
    well_top_twt_ms: float = 600.0,
) -> dict[str, Any]:
    """Run well-to-seismic tie using bruges Ricker wavelet.

    Returns: synthetic seismogram, cross-correlation shift, calibrated horizons.
    """
    return await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: run_well_tie(las_path, segy_audit_path, output_dir, well_top_twt_ms),
    )
