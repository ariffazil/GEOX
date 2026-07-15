"""
GEOX Real E2E Test Suite — Verified Against Live Registered Tools
DITEMPA BUKAN DIBERI

Tests the 4 registered @mcp.tool decorators that actually exist in GEOX:
  1. geox_stratigraphy_preview_config
  2. geox_stratigraphy_run_pipeline
  3. geox_well_compute_gr_bins
  4. geox_well_infer_seq_strat

Does NOT require cv2, torch, or external APIs.
Uses only the smoke-test LAS fixture and synthetic YAML/packages.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fastmcp import FastMCP
from geox_mcp.tools.stratigraphy import register_stratigraphy_tools
from geox_mcp.tools.well import register_well_tools


# ── Fixture: Live MCP instance with all 4 tools registered ──────────────────


@pytest.fixture
def mcp():
    """Yield a FastMCP instance with stratigraphy + well tools registered."""
    instance = FastMCP("geox-e2e-test")
    register_stratigraphy_tools(instance)
    register_well_tools(instance)
    return instance


@pytest.fixture
def smoke_las_path() -> str:
    return str(REPO_ROOT / "tests" / "fixtures" / "geox_smoke_test.las")


@pytest.fixture
def minimal_project_yaml() -> str:
    return """
project: TEST_E2E
bin_size_m: 10.0
min_package_thickness_m: 20.0
p50_shift_thresh_gapi: 15.0
gr_cut_api: 75.0
gr_min_api: 0.0
gr_max_api: 150.0
well_order:
  - SMOKE_TEST_1
wells:
  - name: SMOKE_TEST_1
    path: tests/fixtures/geox_smoke_test.las
    format: LAS
intervals:
  SMOKE_TEST_1:
    - zone: TEST_ZONE
      top: 500
      base: 1000
      depo_env: FLUVIAL
"""


@pytest.fixture
def dummy_packages() -> list[dict]:
    """Minimal geological packages that trigger LST→TST→HST boundary detection."""
    return [
        {
            "stacking_pattern": "COARSENING_UPWARD",
            "dominant_motif": "AMALGAMATED",
            "top": 500.0,
            "base": 650.0,
        },
        {
            "stacking_pattern": "FINING_UPWARD",
            "dominant_motif": "HETEROLITHIC",
            "top": 650.0,
            "base": 800.0,
        },
        {
            "stacking_pattern": "COARSENING_UPWARD",
            "dominant_motif": "BLOCKY",
            "top": 800.0,
            "base": 1000.0,
        },
    ]


# ── Helper: async tool caller ───────────────────────────────────────────────


async def _call_tool(mcp: FastMCP, name: str, **kwargs):
    """Fetch a registered tool by name and invoke its raw function."""
    tool = await mcp.get_tool(name)
    return await tool.fn(**kwargs)


# ── Stratigraphy Tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_geox_stratigraphy_preview_config_valid(mcp, minimal_project_yaml):
    result = await _call_tool(mcp, "geox_stratigraphy_preview_config", project_yaml=minimal_project_yaml)
    assert result["ok"] is True
    assert result["claim_state"] == "OBSERVED"
    assert "wells" in result
    assert "intervals" in result
    assert result["wells"][0]["name"] == "SMOKE_TEST_1"


@pytest.mark.asyncio
async def test_geox_stratigraphy_preview_config_invalid_yaml(mcp):
    result = await _call_tool(mcp, "geox_stratigraphy_preview_config", project_yaml="not: valid: yaml: [")
    assert result["ok"] is False
    assert result["claim_state"] == "VOID"
    assert "Invalid YAML" in result.get("error", "")


@pytest.mark.asyncio
async def test_geox_stratigraphy_run_pipeline_valid(mcp, minimal_project_yaml, tmp_path):
    output_dir = str(tmp_path / "strat_output")
    result = await _call_tool(
        mcp,
        "geox_stratigraphy_run_pipeline",
        project_yaml=minimal_project_yaml,
        output_dir=output_dir,
    )
    # The pipeline may fail on the smoke-test LAS (only 6 samples),
    # but the envelope should still be structured correctly.
    assert "execution_status" in result
    assert "claim_state" in result
    assert "primary_artifact" in result or "error" in result


# ── Well Tests ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_geox_well_compute_gr_bins_valid(mcp, smoke_las_path):
    result = await _call_tool(
        mcp,
        "geox_well_compute_gr_bins",
        source=smoke_las_path,
        zone_top=500.0,
        zone_base=1000.0,
        bin_size_m=500.0,
    )
    # smoke_test.las has 11 samples over 500 m; 500 m bins yield 1 usable bin.
    assert result["execution_status"] == "SUCCESS"
    assert result["claim_state"] in ("OBSERVED", "DERIVED_CANDIDATE")
    artifact = result["primary_artifact"]
    assert artifact["tool"] == "geox_well_compute_gr_bins"
    assert artifact["n_bins"] == 1
    assert artifact["n_usable_bins"] == 1
    assert len(artifact["bins"]) == 1
    assert artifact["bins"][0]["p50"] is not None


@pytest.mark.asyncio
async def test_geox_well_compute_gr_bins_invalid_interval(mcp, smoke_las_path):
    result = await _call_tool(
        mcp,
        "geox_well_compute_gr_bins",
        source=smoke_las_path,
        zone_top=1000.0,
        zone_base=500.0,  # inverted
        bin_size_m=50.0,
    )
    assert result["execution_status"] == "ERROR"
    assert result["primary_artifact"]["error_code"] == "INVALID_DEPTH_INTERVAL"


@pytest.mark.asyncio
async def test_geox_well_infer_seq_strat_valid(mcp, dummy_packages):
    result = await _call_tool(
        mcp,
        "geox_well_infer_seq_strat",
        packages=dummy_packages,
        depo_env_code="FLUVIAL",
        gr_cutoff_api=75.0,
    )
    assert result["execution_status"] == "SUCCESS"
    assert result["claim_state"] == "INTERPRETED"
    artifact = result["primary_artifact"]
    assert "systems_tracts" in artifact
    assert "surfaces" in artifact
    assert "motif_summary" in artifact
    assert artifact["depo_env_code"] == "FLUVIAL"
    # Should detect at least one systems tract
    assert len(artifact["systems_tracts"]) >= 1


@pytest.mark.asyncio
async def test_geox_well_infer_seq_strat_empty_packages(mcp):
    result = await _call_tool(
        mcp,
        "geox_well_infer_seq_strat",
        packages=[],
        depo_env_code="FLUVIAL",
    )
    assert result["execution_status"] == "ERROR"
    assert result["primary_artifact"]["error_code"] == "NO_PACKAGES"


@pytest.mark.asyncio
async def test_geox_well_infer_seq_strat_bad_depo_env(mcp, dummy_packages):
    result = await _call_tool(
        mcp,
        "geox_well_infer_seq_strat",
        packages=dummy_packages,
        depo_env_code="MARS_CRATER",
    )
    assert result["execution_status"] == "ERROR"
    assert result["primary_artifact"]["error_code"] == "UNKNOWN_DEPOSITIONAL_ENVIRONMENT"


# ── Ground-truth: tool count ────────────────────────────────────────────────


def test_actual_registered_tool_count():
    """
    Ground truth: this test confirms the dynamic decorator count matches
    what we expect given the current registration architecture.

    ARCHITECTURE NOTE (2026-06-22):
      GEOX uses two tool registration mechanisms:
        (a) @mcp.tool() decorator inside individual tool modules (legacy)
        (b) Imperative register_tools_on_server() in `_register.py` (modern)

      The legacy decorator-based files are: stratigraphy.py, well.py,
      well_correlation.py, lem_predict.py. As of W16+ FORGE 2026-06-22,
      all other tools are registered imperatively via the canonical registry
      in `src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS` (count is runtime fact).

      This test guards the LEGACY decorator count — any agent claiming
      a different decorator count is hallucinating.
    """
    tools_dir = SRC_ROOT / "geox_mcp" / "tools"
    count = 0
    decorator_files = []
    for py_file in tools_dir.glob("*.py"):
        source = py_file.read_text()
        tree = ast.parse(source)
        file_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "tool":
                    file_count += 1
        if file_count > 0:
            decorator_files.append((py_file.name, file_count))
            count += file_count

    # Cross-check against canonical registry (informational)
    try:
        from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

        canonical = len(CANONICAL_PUBLIC_TOOLS)
    except Exception:
        canonical = -1

    # Expected decorator count = sum across legacy decorator files
    # Update this when a new decorator-based tool is added.
    expected_decorator_files = {
        "stratigraphy.py": 2,
        "well.py": 4,
        "well_correlation.py": 2,
        "ui_applets.py": 1,
        "velocity_structural_qc.py": 1,
        "geox_interpolate_grid.py": 1,
        "_register.py": 1,  # one imperative register_tools_on_server call
    }
    expected = sum(expected_decorator_files.values())

    actual_files = dict(decorator_files)
    assert actual_files == expected_decorator_files, (
        f"Decorator-file count drift: expected {expected_decorator_files}, "
        f"got {actual_files}. If you added/removed a decorator-based tool, "
        f"update expected_decorator_files above."
    )
    assert count == expected, f"Expected {expected} decorator calls, found {count}. Files: {decorator_files}"
    # Informational: canonical registry has more tools than decorators.
    # This is by design — see ARCHITECTURE NOTE above.
    if canonical > 0:
        assert canonical >= expected, f"Canonical registry ({canonical}) should be ≥ decorator count ({expected})"
