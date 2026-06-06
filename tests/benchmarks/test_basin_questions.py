import pytest
from pathlib import Path
from geox_mcp.tools.basin import (
    geox_basin_resolve,
    geox_basin_profile,
    geox_query_intake,
    geox_abstraction_guard,
    geox_literature_ingest,
)
from geox_mcp.tools.evidence_reason import geox_evidence_reason


@pytest.mark.asyncio
async def test_benchmark_basin_overview():
    # Prompt: "Tell me about Malay Basin"
    # Intake routes to Malay Basin
    intake = await geox_query_intake(query="Tell me about Malay Basin")
    assert intake["execution_status"] == "SUCCESS"
    assert intake["primary_artifact"]["routed_intent"] == "basin_overview"
    assert intake["primary_artifact"]["pre_resolved_basin"] == "Malay Basin"

    # Resolve Basin
    resolve = await geox_basin_resolve(name="Malay Basin")
    assert resolve["execution_status"] == "SUCCESS"
    assert resolve["primary_artifact"]["basin_id"] == "MALAY_BASIN"
    assert "Malay Basin" in resolve["primary_artifact"]["aliases"]

    # Baseline Profile Overview
    profile = await geox_basin_profile(basin_name="Malay Basin", mode="overview", claim_strictness="screen")
    assert profile["execution_status"] == "SUCCESS"
    assert profile["claim_state"] == "INTERPRETED"
    assert "basin_name" in profile["primary_artifact"]["interpreted"]
    assert "tectonic_history" in profile["primary_artifact"]["interpreted"]


@pytest.mark.asyncio
async def test_benchmark_deep_syn_rift_play():
    # Prompt: "Evaluate Malay Basin deep syn-rift play"
    profile = await geox_basin_profile(basin_name="Malay Basin", mode="play_fairway", claim_strictness="appraise")
    assert profile["execution_status"] == "SUCCESS"
    # Check that play fairways are retrieved
    assert len(profile["primary_artifact"]["play_fairways"]) > 0
    # Deep syn-rift play should be part of it
    play_names = [p["play_name"] for p in profile["primary_artifact"]["play_fairways"]]
    assert any("Deep Syn-rift Play" in name for name in play_names)


@pytest.mark.asyncio
async def test_benchmark_screen_gas_prospect_forbidden():
    # Prompt: "Screen a gas prospect in Malay Basin"
    # Decision level claim without evidence refs should be held or restricted
    profile = await geox_basin_profile(basin_name="Malay Basin", mode="risk", claim_strictness="decision", evidence_refs=[])
    assert profile["governance_status"] == "HOLD"
    assert "site_specific_stoiip_or_reserves_adjudication" in profile["primary_artifact"]["forbidden_claims"]


@pytest.mark.asyncio
async def test_benchmark_contradiction_scan():
    # Prompt: "Run contradiction scan on Malay Basin stratigraphic trap"
    profile = await geox_basin_profile(basin_name="Malay Basin", mode="contradiction_scan")
    assert profile["execution_status"] == "SUCCESS"
    assert "claims.json" in [Path(f).name for f in profile["evidence_refs"]]


@pytest.mark.asyncio
async def test_benchmark_evidence_reason_baseline():
    # Prompt: "Explain why AVO anomaly may fail in Malay Basin"
    # Call evidence reasoning with empty refs but known basin (mode = baseline)
    reason = await geox_evidence_reason(basin_name="Malay Basin", reasoning_mode="baseline")
    assert reason["execution_status"] == "SUCCESS"
    assert reason["claim_state"] == "INTERPRETED"
    # Check that it returns hypotheses and limits
    assert len(reason["primary_artifact"]["process_hypotheses"]) > 0
    assert "observed" in reason["primary_artifact"]
    assert not reason["primary_artifact"]["observed"]  # should be empty per P3 rules


@pytest.mark.asyncio
async def test_benchmark_metaphor_guard():
    # Prompt: "masalah rumah tangga anda fault seal analysis"
    guard = await geox_abstraction_guard(concept="fault seal analysis", query="masalah rumah tangga")
    assert guard["execution_status"] == "SUCCESS"
    assert guard["primary_artifact"]["status"] == "METAPHOR_NOT_MODEL"
    assert "metaphor_mappings" in guard["primary_artifact"]


@pytest.mark.asyncio
async def test_benchmark_literature_ingest():
    # Ingest Madon 2021 PDF
    pdf_path = "/root/.gemini/antigravity-cli/brain/2cac89a4-07df-4975-a727-92b9ccb0bd2f/.tempmediaStorage/6a1dd264a26ba533.pdf"
    res = await geox_literature_ingest(file_path=pdf_path, basin_name="Malay Basin")
    
    assert res["execution_status"] == "SUCCESS"
    assert res["primary_artifact"]["artifact_type"] == "literature_review"
    assert "Mazlan Madon" in res["primary_artifact"]["author"]
    assert "Five decades" in res["primary_artifact"]["title"]
    assert len(res["primary_artifact"]["claim_candidates"]) == 7
    assert res["primary_artifact"]["claim_state"] == "DRAFT"

