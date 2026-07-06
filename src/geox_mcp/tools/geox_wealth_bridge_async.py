"""
GEOX Wealth Bridge — Async MCP Wrapper
════════════════════════════════════════
Entry: geox_wealth_bridge.run_wealth_bridge()
epistemic: INT_3D_STRUCTURE → CAPITAL_CONSEQUENCE (requires F13 sovereign seal)
DITEMPA BUKAN DIBERI — Forged 2026-07-06.
"""

from __future__ import annotations
import asyncio
from typing import Any

from geox_mcp.tools.geox_wealth_bridge import run_wealth_bridge


async def geox_wealth_consequence(
    gempy_manifest_path: str,
    grid_path: str,
    well_manifest_path: str,
    output_dir: str,
    exploration_capex_usd: float = 40_000_000.0,
    oil_price_usd_per_bbl: float = 75.0,
    development_cost_usd_per_bbl: float = 35.0,
) -> dict[str, Any]:
    """Calculate capital consequence from 3D structural model via WEALTH HarnessEngine.

    Returns: EMV, NPV, capital x-rate, 9-Harness audit.
    """
    return await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: run_wealth_bridge(
            gempy_manifest_path,
            grid_path,
            well_manifest_path,
            output_dir,
            exploration_capex_usd,
            oil_price_usd_per_bbl,
            development_cost_usd_per_bbl,
        ),
    )
