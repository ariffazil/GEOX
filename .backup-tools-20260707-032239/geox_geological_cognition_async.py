"""
GEOX Geological Cognition — Async MCP Wrapper
═════════════════════════════════════════════
epistemic: OBS → LLM_COGNITION → ranked_hypotheses
DITEMPA BUKAN DIBERI — Forged 2026-07-06.
"""

from __future__ import annotations
import asyncio
from typing import Any

from geox_mcp.tools.geox_geological_cognition import (
    classify_reflector_packages,
    detect_terminations,
    screen_imaging_artifacts,
    rank_hypotheses,
    build_geologist_report,
)


async def geox_cognitive_classify(agc: Any, cp: Any, pc: Any, n_zones: int = 5) -> dict[str, Any]:
    """Classify reflector packages across seismic section."""
    return await asyncio.get_event_loop().run_in_executor(None, lambda: classify_reflector_packages(agc, cp, pc, n_zones))


async def geox_cognitive_terminate(horizons: Any, agc: Any, pc: Any) -> dict[str, Any]:
    """Detect reflector terminations (onlap, downlap, truncation, concordance)."""
    return await asyncio.get_event_loop().run_in_executor(None, lambda: detect_terminations(horizons, agc, pc))


async def geox_cognitive_screen_artifacts(agc: Any, cp: Any, pc: Any) -> dict[str, Any]:
    """Screen for imaging artifacts."""
    return await asyncio.get_event_loop().run_in_executor(None, lambda: screen_imaging_artifacts(agc, cp, pc))


async def geox_cognitive_rank_hypotheses(faults: Any, horizons: Any, packages: Any) -> dict[str, Any]:
    """Rank geological hypotheses by basin-specific prior probability."""
    return await asyncio.get_event_loop().run_in_executor(None, lambda: rank_hypotheses(faults, horizons, packages))


async def geox_cognitive_build_report(packages: Any, terminations: Any) -> dict[str, Any]:
    """Build structured geologist report from cognitive outputs."""
    return await asyncio.get_event_loop().run_in_executor(None, lambda: build_geologist_report(packages, terminations))
