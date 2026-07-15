"""GEOX-001 orthogonal base routing — GENESIS/013."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from geox_core.benchmarks.geox_001_orthogonal_route import (
    gate_tool,
    run_geox_001_with_orthogonal_route,
    run_orthogonal_base,
)


def test_gate_blocks_cognitive_before_base():
    g = gate_tool("geox_vision", base_complete=False)
    assert g["allowed"] is False
    assert g["error_code"] == "ORTHOGONAL_BASE_INCOMPLETE"


def test_gate_allows_after_base():
    g = gate_tool("geox_claim", base_complete=True)
    assert g["allowed"] is True


def test_gate_blocks_simulate_and_3d():
    for t in ("geox_simulate_routing", "geox_3d_model_build", "geox_map_render_preview"):
        assert gate_tool(t, False)["allowed"] is False


@pytest.mark.asyncio
async def test_orthogonal_base_synthetic_path():
    base = await run_orthogonal_base(las_path=None)
    assert "stages" in base
    assert base["routing_law"].startswith("Orthogonal Base")
    # no LAS → ingest SKIP, not crash
    stages = {s["stage"]: s["status"] for s in base["stages"]}
    assert stages.get("000_well_ingest") == "SKIP"


@pytest.mark.asyncio
async def test_geox_001_with_orthogonal_route_demo():
    r = await run_geox_001_with_orthogonal_route(scenario="mistie_hold")
    assert r["all_six_success_conditions"] is True
    assert "orthogonal_base" in r
    assert r["metabolic_plane"]["genesis"] == "013_GEOX_METABOLIC_SURFACE"
    assert "tool_gates" in r
    # vision gated by base_complete
    assert r["tool_gates"]["geox_vision"]["allowed"] == bool(
        r["orthogonal_base"].get("base_complete")
    )
    assert r["killer_output"]["verdict"] in ("PROCEED", "HOLD", "KILL")


@pytest.mark.asyncio
async def test_mcp_benchmark_enforces_base():
    from geox_mcp.tools.benchmark_001 import geox_benchmark_001

    out = await geox_benchmark_001(scenario="mistie_hold", enforce_orthogonal_base=True)
    assert out["status"] == "success"
    assert out["routing_law"].startswith("Orthogonal Base")
    assert "orthogonal_base" in out
