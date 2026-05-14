from __future__ import annotations

import asyncio
import csv
from pathlib import Path

from geox.well.mcp_tools import register_well_tools


class _FakeMCP:
    def __init__(self) -> None:
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


def _write_gr_csv(path: Path, rows: list[tuple[float, float]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["depth", "gr"])
        writer.writerows(rows)


def _registered_tools() -> dict:
    fake = _FakeMCP()
    register_well_tools(fake)
    return fake.tools


def test_well_compute_gr_bins_rejects_invalid_interval() -> None:
    tools = _registered_tools()
    result = asyncio.run(
        tools["geox_well_compute_gr_bins"](
            source="/tmp/not-needed.csv",
            zone_top=120.0,
            zone_base=100.0,
        )
    )

    assert result["execution_status"] == "ERROR"
    assert result["governance_status"] == "HOLD"
    assert result["claim_state"] == "NO_VALID_EVIDENCE"
    assert result["primary_artifact"]["error_code"] == "INVALID_DEPTH_INTERVAL"
    assert result["physics_guard"]["guard_passed"] is False


def test_well_compute_gr_bins_rejects_unphysical_gr(tmp_path: Path) -> None:
    source = tmp_path / "bad_gr.csv"
    _write_gr_csv(source, [(100.0, 40.0), (101.0, 350.0), (102.0, 360.0)])
    tools = _registered_tools()

    result = asyncio.run(
        tools["geox_well_compute_gr_bins"](
            source=str(source),
            zone_top=100.0,
            zone_base=103.0,
            bin_size_m=1.0,
        )
    )

    assert result["execution_status"] == "ERROR"
    assert result["primary_artifact"]["error_code"] == "GR_PHYSICS_GUARD_FAILED"
    assert "GR_ABOVE_EXPECTED_RANGE" in result["diagnostics"]["physics_guard"]["violations"]


def test_well_analyze_sequence_success_is_gr_only_hypothesis(tmp_path: Path) -> None:
    source = tmp_path / "valid_gr.csv"
    rows = [(float(depth), 35.0 + (depth - 100.0) * 2.0) for depth in range(100, 141)]
    _write_gr_csv(source, rows)
    tools = _registered_tools()

    result = asyncio.run(
        tools["geox_well_analyze_sequence"](
            source=str(source),
            zone_top=100.0,
            zone_base=140.0,
            depo_env_code="SHOREFACE",
            bin_size_m=10.0,
            min_package_thickness_m=10.0,
        )
    )

    assert result["execution_status"] == "SUCCESS"
    assert result["claim_tag"] == "HYPOTHESIS"
    assert result["perception_class"] == "HYPOTHESIS"
    assert result["uncertainty"] == "High"
    artifact = result["primary_artifact"]
    assert artifact["tool"] == "geox_well_analyze_sequence"
    assert artifact["source_sha256"]
    assert artifact["limitations"]
    assert result["physics_guard"]["guard_passed"] is True


def test_well_infer_seq_strat_rejects_unknown_depo_env() -> None:
    tools = _registered_tools()
    result = asyncio.run(
        tools["geox_well_infer_seq_strat"](
            packages=[
                {
                    "top": 100.0,
                    "base": 120.0,
                    "dominant_motif": "FUNNEL",
                    "stacking_pattern": "COARSENING_UPWARD",
                }
            ],
            depo_env_code="MAGICAL_BASIN",
        )
    )

    assert result["execution_status"] == "ERROR"
    assert result["primary_artifact"]["error_code"] == "UNKNOWN_DEPOSITIONAL_ENVIRONMENT"
    assert "SHOREFACE" in result["diagnostics"]["allowed"]
