"""
GEOX-001: Well-Seismic Truth Test — Model Deserves To Live

Locked threshold law + six success conditions + constitutional DRAFT_ONLY.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from geox_core.benchmarks.geox_001_well_seismic_truth import (
    MANDATORY_ALTERNATIVES,
    MISTIE_KILL_MS,
    MISTIE_PROCEED_MS,
    PIPELINE_STAGES,
    SCENARIO_GOOD,
    SCENARIO_HOLD,
    SCENARIO_KILL,
    render_killer_yaml,
    run_geox_001,
    write_fixture_bundle,
)

CORE_SIX = [
    "QC_verified_ingested_files",
    "explicit_evidence_graph",
    "synthetic_tie_and_drift_result",
    "claim_with_OBS_DER_INT_SPEC_separation",
    "active_challenge_or_alternative_interpretation",
    "verdict_can_say_PROCEED_HOLD_KILL_without_pretending_certainty",
]


def test_hold_demo_threshold_law():
    """Default wedge: mistie in (15, 25] → HOLD, DRAFT_ONLY, model does not live."""
    r = run_geox_001(scenario=SCENARIO_HOLD)
    assert r["all_six_success_conditions"] is True
    for k in CORE_SIX:
        assert r["success_conditions"][k] is True, k

    k = r["GEOX_001_receipt"]
    assert k["verdict"] == "HOLD"
    assert "Horizon H1" in k["claim"]
    mistie = abs(r["workflow"]["synthetic_tie"]["mistie_ms"])
    assert MISTIE_PROCEED_MS < mistie <= MISTIE_KILL_MS
    assert r["model_deserves_to_live"] is False
    assert k["constitutional_status"]["VAULT999_status"] == "DRAFT_ONLY"
    assert k["constitutional_status"]["seal_allowed"] is False
    assert set(k["evidence_classes"].keys()) == {"OBS", "DER", "INT", "SPEC"}

    yaml = render_killer_yaml(r)
    assert "verdict: HOLD" in yaml
    assert "VAULT999_status: DRAFT_ONLY" in yaml
    assert "evidence_classes:" in yaml


def test_good_tie_proceeds():
    r = run_geox_001(scenario=SCENARIO_GOOD)
    assert r["all_six_success_conditions"] is True
    assert r["killer_output"]["verdict"] == "PROCEED"
    assert r["model_deserves_to_live"] is True
    assert abs(r["workflow"]["synthetic_tie"]["mistie_ms"]) <= MISTIE_PROCEED_MS
    assert r["workflow"]["synthetic_tie"]["residual_class"] == "good_tie"
    assert r["constitutional_status"]["VAULT999_status"] == "DRAFT_ONLY"


def test_kill_on_mistie_gt_25_and_contradiction():
    """Classic +38 ms mistie is KILL under threshold law (>25 ms)."""
    r = run_geox_001(scenario=SCENARIO_KILL)
    assert r["all_six_success_conditions"] is True
    assert r["killer_output"]["verdict"] == "KILL"
    assert r["model_deserves_to_live"] is False
    assert abs(r["workflow"]["synthetic_tie"]["mistie_ms"]) > MISTIE_KILL_MS
    tops = [t for t in r["workflow"]["claim"]["evidence_against"] if "nearby well" in t["item"]]
    assert len(tops) >= 1


def test_pipeline_000_to_777():
    r = run_geox_001(scenario=SCENARIO_HOLD)
    assert r["pipeline_stages"] == list(PIPELINE_STAGES)
    for stage in PIPELINE_STAGES:
        assert stage in r["pipeline"], stage
    assert len(r["pipeline"]["555_challenge"]) >= 4


def test_mandatory_four_alternatives():
    r = run_geox_001(scenario=SCENARIO_HOLD)
    texts = {a["text"] for a in r["workflow"]["challenge"]}
    for required in MANDATORY_ALTERNATIVES:
        assert required in texts


def test_evidence_graph_has_obs_der_int_spec():
    r = run_geox_001(scenario=SCENARIO_HOLD)
    nodes = r["workflow"]["evidence_graph"]["nodes"]
    rungs = {n["rung"] for n in nodes}
    assert {"OBS", "DER", "INT", "SPEC"} <= rungs
    assert len(r["workflow"]["evidence_graph"]["edges"]) >= 5


def test_claim_challenge_and_epistemic():
    r = run_geox_001(scenario=SCENARIO_HOLD)
    claim = r["workflow"]["claim"]
    assert claim["rung"] in ("OBS", "DER", "INT", "SPEC")
    assert len(claim["evidence_for"]) >= 1
    assert len(claim["evidence_against"]) >= 3
    assert len(claim["alternatives"]) >= 4
    epi = r["workflow"]["epistemic_classification"]
    assert epi["las_curves"] == "OBS"
    assert epi["synthetic_seismogram"] == "DER"
    assert epi["horizon_h1_mapped_event"] == "INT"
    assert epi["velocity_model"] == "SPEC"


def test_confidence_never_pretends_certainty():
    for s in (SCENARIO_GOOD, SCENARIO_HOLD, SCENARIO_KILL):
        r = run_geox_001(scenario=s)
        assert r["workflow"]["verdict"]["confidence_cap"] <= 0.90
        assert r["workflow"]["verdict"]["verdict"] in ("PROCEED", "HOLD", "KILL")
        assert r["constitutional_status"]["seal_allowed"] is False


def test_schema_file_exists():
    schema = _SRC / "geox_core" / "benchmarks" / "geox_001_schema.json"
    assert schema.exists()
    data = json.loads(schema.read_text())
    assert data["title"].startswith("GEOX-001")


def test_write_fixtures(tmp_path):
    d = write_fixture_bundle(tmp_path, SCENARIO_HOLD)
    assert (d / "well_a.las").exists()
    assert (d / "checkshot.json").exists()
    assert (d / "seismic_trace.json").exists()
    assert (d / "horizon_h1.json").exists()
    assert (d / "tops.json").exists()
    assert (d / "velocity_assumption.json").exists()


@pytest.mark.asyncio
async def test_mcp_tool_surface():
    from geox_mcp.tools.benchmark_001 import geox_benchmark_001

    out = await geox_benchmark_001(scenario="mistie_hold", include_full_workflow=True)
    assert out["status"] == "success"
    assert out["tool"] == "geox_benchmark_001"
    assert out["all_six_success_conditions"] is True
    assert out["killer_output"]["verdict"] == "HOLD"
    assert out["killer_output"]["constitutional_status"]["VAULT999_status"] == "DRAFT_ONLY"
    assert "verdict: HOLD" in out["killer_yaml"]
