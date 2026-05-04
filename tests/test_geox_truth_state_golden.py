"""
GEOX Truth-State Golden Tests — Post-ChatGPT audit fixes
=========================================================
Validates:
  1. Judge schema accepts ack_irreversible
  2. No evidence → cannot be VERIFIED
  3. Confidence band is None / computed=False (not fake zeros)
  4. History audit returns structured error, never raw 502
  5. DST structured ingestion derives correct metrics
  6. Claim-state enforcement blocks contradictions

DITEMPA BUKAN DIBERI
"""
from __future__ import annotations

import pytest
import asyncio

from contracts.enums.statuses import get_standard_envelope, enforce_claim_state, ArtifactStatus
from contracts.tools.canonical.prospect import (
    geox_prospect_evaluate,
    geox_prospect_judge_preview,
    geox_prospect_judge_seal,
    geox_prospect_judge_verdict,
)
from contracts.tools.canonical.registry import geox_history_audit
from contracts.tools.canonical.time4d import geox_time4d_analyze_system
from contracts.tools.canonical.dst import geox_dst_ingest_test


# ═══════════════════════════════════════════════════════════════════════════════
# Test 1 — Judge schema accepts ack_irreversible
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_judge_seal_accepts_ack():
    """geox_prospect_judge_seal must have ack_irreversible in its signature."""
    import inspect
    sig = inspect.signature(geox_prospect_judge_seal)
    assert "ack_irreversible" in sig.parameters
    assert "judge_pin" in sig.parameters


@pytest.mark.asyncio
async def test_judge_verdict_backward_compat():
    """Old canonical name must still work and delegate to seal."""
    import inspect
    sig = inspect.signature(geox_prospect_judge_verdict)
    assert "ack_irreversible" in sig.parameters


@pytest.mark.asyncio
async def test_judge_preview_no_ack_required():
    """Preview must be reversible and NOT require ack_irreversible."""
    result = await geox_prospect_judge_preview(prospect_ref="TEST", ac_risk_score=0.3)
    assert result["claim_state"] == "JUDGE_PREVIEW"
    assert result["artifact_status"] != "SEAL"
    assert result["primary_artifact"]["reversible"] is True


@pytest.mark.asyncio
async def test_judge_seal_blocks_without_ack():
    """Seal without ack_irreversible must return RT3_GUARD_F1_AMANAH."""
    result = await geox_prospect_judge_seal(
        prospect_ref="TEST", ac_risk_score=0.3, ack_irreversible=False
    )
    assert result["execution_status"] == "ERROR"
    assert result["governance_status"] == "HOLD"
    assert result["primary_artifact"]["error_code"] == "RT3_GUARD_F1_AMANAH"


# ═══════════════════════════════════════════════════════════════════════════════
# Test 2 — No evidence cannot be verified
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_no_evidence_no_verified():
    """String-only prospect_ref must not produce VERIFIED or SEAL."""
    result = await geox_prospect_evaluate(prospect_ref="StringOnly")
    assert result["artifact_status"] != "VERIFIED"
    assert result["claim_state"] in ("HYPOTHESIS", "NO_VALID_EVIDENCE")
    assert result["primary_artifact"]["score_type"] == "heuristic_screening"


@pytest.mark.asyncio
async def test_time4d_no_evidence_undetermined():
    """time4d without evidence_refs must return UNDETERMINED."""
    result = await geox_time4d_analyze_system(prospect_ref="TEST", mode="burial")
    assert result["primary_artifact"]["maturity"] == "UNDETERMINED"
    assert result["claim_state"] == "NO_VALID_EVIDENCE"
    assert result["artifact_status"] != "VERIFIED"


@pytest.mark.asyncio
async def test_enforce_claim_state_downgrades_verified():
    """enforce_claim_state must downgrade VERIFIED when evidence_refs is empty."""
    result = {
        "artifact_status": "VERIFIED",
        "claim_state": "HYPOTHESIS",
        "evidence_refs": [],
    }
    corrected = enforce_claim_state(result, evidence_refs=[])
    assert corrected["artifact_status"] == "DRAFT"
    assert "_claim_corrected" in corrected


# ═══════════════════════════════════════════════════════════════════════════════
# Test 3 — Confidence band cannot be fake zero
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_confidence_not_fake_zero():
    """When no computation occurs, confidence_band must not be 0.0/0.0/0.0."""
    result = await geox_prospect_evaluate(prospect_ref="StringOnly")
    cb = result.get("confidence_band")
    # Should be None or have computed=False
    if cb is not None:
        assert cb.get("computed") is False
    # Explicitly reject the old fake-zero default
    assert cb != {"p10": 0.0, "p50": 0.0, "p90": 0.0}


@pytest.mark.asyncio
async def test_standard_envelope_default_confidence_is_none():
    """get_standard_envelope must default confidence_band to None."""
    env = get_standard_envelope({"test": True})
    assert env["confidence_band"] is None or env["confidence_band"].get("computed") is False


# ═══════════════════════════════════════════════════════════════════════════════
# Test 4 — History audit must not 502
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_history_audit_long_query_safe():
    """Very long query must return structured error, never crash."""
    q = "DST " + "CO2 24% H2S 20ppm " * 100
    result = await geox_history_audit(query=q)
    assert result["execution_status"] in ("SUCCESS", "ERROR")
    assert "error_code" in result["primary_artifact"] or "records" in result["primary_artifact"]


@pytest.mark.asyncio
async def test_history_audit_null_bytes_stripped():
    """Null bytes in query must be sanitized."""
    q = "test\x00injection"
    result = await geox_history_audit(query=q)
    assert result["execution_status"] in ("SUCCESS", "ERROR")
    assert "\x00" not in result["primary_artifact"].get("query", "")


# ═══════════════════════════════════════════════════════════════════════════════
# Test 5 — DST structured metrics
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_dst_ingest_derives_metrics():
    """DST ingestion must compute CGR, WGR, HC gas, drawdown."""
    result = await geox_dst_ingest_test(
        well_id="Lebah_Hijau",
        gas_rate_mmscfd=20,
        condensate_rate_stbd=240,
        water_rate_stbd=60,
        co2_mol_pct=24,
        bhp_psi=3069,
        whp_psi=1706,
    )
    dm = result["primary_artifact"]["derived_metrics"]
    assert dm["cgr_stb_per_mmscf"] == 12.0
    assert dm["wgr_stb_per_mmscf"] == 3.0
    assert dm["hydrocarbon_gas_mmscfd"] == 15.2
    assert dm["drawdown_proxy_psi"] == 1363.0
    assert "HIGH_CO2" in result["primary_artifact"]["flags"]
    assert result["claim_state"] == "INGESTED"
