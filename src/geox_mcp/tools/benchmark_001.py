"""
geox_benchmark_001 — Well-Seismic Truth Test MCP surface
═══════════════════════════════════════════════════════════
GEOX-001: Model Deserves To Live

If the well does not tie, the model does not get to speak as truth.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any, Literal

from geox_core.benchmarks.geox_001_well_seismic_truth import (
    SCENARIO_GOOD,
    SCENARIO_HOLD,
    SCENARIO_KILL,
    render_killer_yaml,
    run_geox_001,
    write_fixture_bundle,
)

ScenarioArg = Literal["good_tie", "mistie_hold", "kill_contradiction"]


async def geox_benchmark_001(
    scenario: ScenarioArg = "mistie_hold",
    write_fixtures_dir: str = "",
    include_full_workflow: bool = True,
) -> dict[str, Any]:
    """GEOX-001 Well-Seismic Truth Test — Model Deserves To Live.

    Cross-examines a subsurface claim against well + seismic evidence and
    returns PROCEED / HOLD / KILL without fake certainty.

    Scenarios:
      mistie_hold        — default demo (+38 ms mistie → HOLD)
      good_tie           — clean tie → PROCEED (model may live)
      kill_contradiction — large mistie + offset contradiction → KILL

    Success requires all six:
      1 QC-verified files · 2 evidence graph · 3 synthetic tie/drift ·
      4 OBS/DER/INT/SPEC claim · 5 active challenge · 6 honest verdict
    """
    if scenario not in (SCENARIO_GOOD, SCENARIO_HOLD, SCENARIO_KILL):
        return {
            "status": "error",
            "tool": "geox_benchmark_001",
            "error": f"Unknown scenario '{scenario}'. Use good_tie | mistie_hold | kill_contradiction.",
        }

    fixture_note = None
    if write_fixtures_dir:
        path = write_fixture_bundle(write_fixtures_dir, scenario)
        fixture_note = str(path)

    result = run_geox_001(scenario=scenario)

    out: dict[str, Any] = {
        "status": "success",
        "tool": "geox_benchmark_001",
        "benchmark_id": result["benchmark_id"],
        "title": result["title"],
        "thesis": result["thesis"],
        "scenario": result["scenario"],
        "all_six_success_conditions": result["all_six_success_conditions"],
        "success_conditions": result["success_conditions"],
        "killer_output": result["killer_output"],
        "killer_yaml": render_killer_yaml(result),
        "model_deserves_to_live": result["model_deserves_to_live"],
        "tie_receipt": result["tie_receipt"],
        "anti_hantu": result["anti_hantu"],
        "claim_state": "INTERPRETED",
        "perception_class": "INTERPRETATION",
        "confidence_level": "MEDIUM" if result["killer_output"]["verdict"] == "HOLD" else (
            "HIGH" if result["killer_output"]["verdict"] == "PROCEED" else "LOW"
        ),
        "governance_status": result["killer_output"]["verdict"],
        "timestamp_utc": result["timestamp_utc"],
    }
    if include_full_workflow:
        out["workflow"] = result["workflow"]
    if fixture_note:
        out["fixtures_dir"] = fixture_note
    return out
