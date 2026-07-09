"""
geox_benchmark_001 — Well-Seismic Truth Test MCP surface
═══════════════════════════════════════════════════════════
GEOX-001: Model Deserves To Live

If the well does not tie, the model does not get to speak as truth.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any, Literal

from geox_core.benchmarks.geox_001_orthogonal_route import (
    gate_tool,
    run_geox_001_with_orthogonal_route,
)
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
    # Orthogonal Base first (GENESIS/013)
    enforce_orthogonal_base: bool = True,
    las_path: str = "",
    use_real_las: bool = False,
    checkshot_path: str = "",
    tops_path: str = "",
    seismic_path: str = "",
) -> dict[str, Any]:
    """GEOX-001 Well-Seismic Truth Test — Model Deserves To Live.

    Routing law (mandatory): Orthogonal Base before Cognitive/Dimensional:
      well_ingest → well_qc → tie_preflight → well_tie → tie_receipt
      → only then claim / contrast / verdict.

    Scenarios: mistie_hold | good_tie | kill_contradiction
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

    if enforce_orthogonal_base:
        result = await run_geox_001_with_orthogonal_route(
            scenario=scenario,
            las_path=las_path or None,
            use_real_las=use_real_las,
            checkshot_path=checkshot_path or None,
            tops_path=tops_path or None,
            seismic_path=seismic_path or None,
        )
    else:
        result = run_geox_001(scenario=scenario)
        result["orthogonal_base"] = {
            "status": "bypassed",
            "base_complete": True,
            "warning": "enforce_orthogonal_base=False — not for field claims",
        }

    out: dict[str, Any] = {
        "status": "success",
        "tool": "geox_benchmark_001",
        "benchmark_id": result["benchmark_id"],
        "title": result["title"],
        "thesis": result["thesis"],
        "domain": result.get("domain", "GEOX"),
        "test_type": result.get("test_type"),
        "scenario": result["scenario"],
        "metabolic_plane": result.get("metabolic_plane"),
        "orthogonal_base": result.get("orthogonal_base"),
        "tool_gates": result.get("tool_gates")
        or {
            "geox_vision": gate_tool(
                "geox_vision",
                bool((result.get("orthogonal_base") or {}).get("base_complete")),
            ),
        },
        "all_six_success_conditions": result["all_six_success_conditions"],
        "success_conditions": result["success_conditions"],
        "pipeline_stages": result.get("pipeline_stages"),
        "GEOX_001_receipt": result.get("GEOX_001_receipt") or result["killer_output"],
        "killer_output": result["killer_output"],
        "killer_yaml": render_killer_yaml(result),
        "evidence_classes": result.get("evidence_classes"),
        "constitutional_status": result.get("constitutional_status"),
        "model_deserves_to_live": result["model_deserves_to_live"],
        "tie_receipt": result["tie_receipt"],
        "anti_hantu": result["anti_hantu"],
        "excluded": result.get("excluded"),
        "claim_state": "INTERPRETED",
        "perception_class": "INTERPRETATION",
        "confidence_level": "MEDIUM"
        if result["killer_output"]["verdict"] == "HOLD"
        else ("HIGH" if result["killer_output"]["verdict"] == "PROCEED" else "LOW"),
        "governance_status": result["killer_output"]["verdict"],
        "timestamp_utc": result["timestamp_utc"],
        "routing_law": "Orthogonal Base first — GENESIS/013",
    }
    if include_full_workflow:
        out["workflow"] = result["workflow"]
        out["pipeline"] = result.get("pipeline")
    if fixture_note:
        out["fixtures_dir"] = fixture_note
    if result.get("real_las"):
        out["real_las"] = result["real_las"]
    return out
