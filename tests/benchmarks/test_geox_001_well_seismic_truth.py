"""
GEOX-001: Well-Seismic Truth Test — Model Deserves To Live

Proves the six success conditions and the three verdict paths.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from geox_core.benchmarks.geox_001_well_seismic_truth import (
    SCENARIO_GOOD,
    SCENARIO_HOLD,
    SCENARIO_KILL,
    render_killer_yaml,
    run_geox_001,
    write_fixture_bundle,
)


SIX_KEYS = [
    "1_qc_verified",
    "2_evidence_graph",
    "3_synthetic_tie_drift",
    "4_claim_obs_der_int_spec",
    "5_active_challenge",
    "6_verdict_no_fake_certainty",
]


def test_hold_demo_matches_killer_shape():
    """Default wedge: +38 ms mistie → HOLD, model does not deserve to live."""
    r = run_geox_001(scenario=SCENARIO_HOLD)
    assert r["all_six_success_conditions"] is True
    for k in SIX_KEYS:
        assert r["success_conditions"][k] is True, k

    k = r["killer_output"]
    assert k["verdict"] == "HOLD"
    assert "Horizon H1" in k["claim"]
    assert any("38" in x or "+38" in x for x in k["reason"])
    assert any("INTERPRETATION" in x for x in k["reason"])
    assert any("checkshot" in x.lower() for x in k["reason"])
    assert r["model_deserves_to_live"] is False
    assert r["workflow"]["synthetic_tie"]["mistie_ms"] == pytest.approx(38.0, abs=1.0)

    yaml = render_killer_yaml(r)
    assert "verdict: HOLD" in yaml
    assert "falsification:" in yaml
    assert "next_test:" in yaml


def test_good_tie_proceeds():
    r = run_geox_001(scenario=SCENARIO_GOOD)
    assert r["all_six_success_conditions"] is True
    assert r["killer_output"]["verdict"] == "PROCEED"
    assert r["model_deserves_to_live"] is True
    assert abs(r["workflow"]["synthetic_tie"]["mistie_ms"]) <= 8.0
    assert r["workflow"]["synthetic_tie"]["residual_class"] == "good_tie"


def test_kill_on_contradiction():
    r = run_geox_001(scenario=SCENARIO_KILL)
    assert r["all_six_success_conditions"] is True
    assert r["killer_output"]["verdict"] == "KILL"
    assert r["model_deserves_to_live"] is False
    assert abs(r["workflow"]["synthetic_tie"]["mistie_ms"]) >= 40.0
    # offset well contradiction present
    tops = [t for t in r["workflow"]["claim"]["evidence_against"] if "nearby well" in t["item"]]
    assert len(tops) >= 1


def test_evidence_graph_has_obs_der_int_spec():
    r = run_geox_001(scenario=SCENARIO_HOLD)
    nodes = r["workflow"]["evidence_graph"]["nodes"]
    rungs = {n["rung"] for n in nodes}
    assert "OBS" in rungs
    assert "DER" in rungs
    assert "INT" in rungs
    assert "SPEC" in rungs
    edges = r["workflow"]["evidence_graph"]["edges"]
    assert len(edges) >= 5


def test_claim_challenge_and_epistemic():
    r = run_geox_001(scenario=SCENARIO_HOLD)
    claim = r["workflow"]["claim"]
    assert claim["rung"] in ("OBS", "DER", "INT", "SPEC")
    assert len(claim["evidence_for"]) >= 1
    assert len(claim["evidence_against"]) >= 3
    assert len(claim["alternatives"]) >= 1
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
    assert "verdict: HOLD" in out["killer_yaml"]
