"""
Tests for GEOX → WEALTH Adapter (WELD-002)
DITEMPA BUKAN DIBERI
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, "/root/arifOS/packages/arifos-types/py")
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from arifos_types import (
        ResourceNode,
        EpistemicTag,
        TelemetryPayload,
        Verdict,
        Witness,
        DecisionContext,
        GeologyNode,
        EngineeringNode,
        EconomicsNode,
        GovernanceNode,
    )
    from wealth_bridge import geox_to_wealth, AdmissibilityError, WealthInput

    TYPES_AVAILABLE = True
except ImportError:
    TYPES_AVAILABLE = False
    pytest.skip("arifos_types not installed", allow_module_level=True)


def make_mock_node(
    admissibility_status: str = "admissible",
    risk_geo: float = 0.3,
    epistemic_geo: EpistemicTag = EpistemicTag.ESTIMATE,
    sigma_policy: float = 0.2,
    required_modifications: list = None,
) -> ResourceNode:
    """Factory for mock ResourceNode fixtures."""
    return ResourceNode(
        id="TEST-NODE-001",
        decision_context=DecisionContext(
            jurisdiction="MY",
            analysis_date="2026-04-18",
            market_regime="oil_bull",
            model_version="v0.1",
        ),
        geology=GeologyNode(
            volume_p50=150.0,
            quality_index=0.65,
            depth_m=2500.0,
            structure_complexity=0.3,
            risk_geo=risk_geo,
            epistemic_geo=epistemic_geo,
        ),
        engineering=EngineeringNode(
            recovery_factor=0.35,
            capex_usd=50_000_000.0,
            opex_usd_per_unit=25.0,
            cycle_time_months=18,
        ),
        economics=EconomicsNode(
            price_model="brent_2026",
            discount_rate=0.1,
            fiscal_terms="PSC",
            npv_usd=120_000_000.0,
            irr=0.18,
            sigma_market=0.25,
        ),
        governance=GovernanceNode(
            policy_state="approved",
            admissibility_status=admissibility_status,
            sigma_policy=sigma_policy,
            carbon_cost_usd_per_tco2e=45.0,
            delay_risk=0.15,
            penalty_infinite=False,
            required_modifications=required_modifications or [],
        ),
    )


def make_mock_telemetry() -> TelemetryPayload:
    """Factory for mock TelemetryPayload."""
    return TelemetryPayload(
        epoch=1744939200.0,
        session_id="test-session-001",
        pipeline_stage="888_JUDGE",
        dS=0.15,
        peace2=1.1,
        kappa_r=0.85,
        shadow=0.05,
        confidence=0.88,
        psi_le=0.82,
        verdict=Verdict.PROCEED,
        witness=Witness(human="ARIF", ai="AAA-AGENT", earth="SEISMIC"),
        qdf=0.80,
        floor_violations=[],
        hash="abc123def456",
    )


class TestEpistemicTagPreservation:
    """F2 contract: epistemic tags must never be upgraded at domain boundary."""

    @pytest.mark.parametrize("epistemic_tag", [
        EpistemicTag.UNKNOWN,
        EpistemicTag.ESTIMATE,
        EpistemicTag.HYPOTHESIS,
        EpistemicTag.PLAUSIBLE,
        EpistemicTag.CLAIM,
    ])
    def test_epistemic_tag_passed_through_untouched(self, epistemic_tag):
        """Every epistemic tag must survive the bridge unchanged."""
        node = make_mock_node(epistemic_geo=epistemic_tag)
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert result["epistemic_source"] == epistemic_tag.value

    def test_estimate_never_becomes_claim(self):
        """F2 violation: ESTIMATE cannot become CLAIM at boundary."""
        node = make_mock_node(epistemic_geo=EpistemicTag.ESTIMATE)
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert result["epistemic_source"] == EpistemicTag.ESTIMATE.value
        assert result["epistemic_source"] != EpistemicTag.CLAIM.value


class TestAdmissibilityFilter:
    """F13 contract: governance-blocked nodes cannot enter WEALTH pipeline."""

    def test_blocked_node_raises_admissibility_error(self):
        """Blocked node must raise AdmissibilityError — not silently pass."""
        node = make_mock_node(admissibility_status="blocked")
        telemetry = make_mock_telemetry()
        with pytest.raises(AdmissibilityError) as exc_info:
            geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert "blocked" in str(exc_info.value).lower()
        assert exc_info.value.node_id == "TEST-NODE-001"

    def test_deferred_node_passes_with_delay_risk(self):
        """Deferred is admissible — passes with delay_risk preserved."""
        node = make_mock_node(admissibility_status="deferred")
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert result["extractive_signals"]["admissibility"] == "deferred"
        assert result["extractive_signals"]["delay_risk"] == 0.15

    def test_admissible_node_passes_cleanly(self):
        """Admissible node passes without error."""
        node = make_mock_node(admissibility_status="admissible")
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert result["extractive_signals"]["admissibility"] == "admissible"


class TestMaruahDerivation:
    """Maruah score derived from governance layer, not hardcoded."""

    def test_maruah_from_sigma_policy(self):
        """Higher sigma_policy → lower maruah."""
        node_low_sigma = make_mock_node(sigma_policy=0.1)
        node_high_sigma = make_mock_node(sigma_policy=0.6)
        telemetry = make_mock_telemetry()

        result_low = geox_to_wealth(node_low_sigma, telemetry, Verdict.PROCEED)
        result_high = geox_to_wealth(node_high_sigma, telemetry, Verdict.PROCEED)

        assert result_low["maruah_score"] > result_high["maruah_score"]

    def test_maruah_penalized_by_required_modifications(self):
        """Required modifications reduce maruah score."""
        node_clean = make_mock_node(required_modifications=[])
        node_modified = make_mock_node(required_modifications=["env_study", "social_impact"])
        telemetry = make_mock_telemetry()

        result_clean = geox_to_wealth(node_clean, telemetry, Verdict.PROCEED)
        result_modified = geox_to_wealth(node_modified, telemetry, Verdict.PROCEED)

        assert result_clean["maruah_score"] > result_modified["maruah_score"]

    def test_maruah_bounded_at_zero(self):
        """Maruah cannot go below 0."""
        node = make_mock_node(sigma_policy=0.99, required_modifications=["x", "y", "z"])
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert result["maruah_score"] >= 0.0


class TestIrreversibility:
    """F1 contract: scoring calls are read-only, irreversible=False."""

    def test_scoring_is_not_irreversible(self):
        """Read-only scoring must have irreversible=False."""
        node = make_mock_node()
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert result["irreversible"] is False

    def test_task_definition_set(self):
        """Task definition must identify the node being scored."""
        node = make_mock_node()
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert f"score_resource_node:{node.id}" == result["task_definition"]


class TestWealthSignals:
    """Wealth signals correctly mapped from ResourceNode."""

    def test_sigma_values_preserved(self):
        """All sigma values (geo, market, policy) pass through."""
        node = make_mock_node()
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert result["wealth_signals"]["sigma_geo"] == 0.3
        assert result["wealth_signals"]["sigma_market"] == 0.25
        assert result["wealth_signals"]["sigma_policy"] == 0.2

    def test_economics_mapped(self):
        """NPV, IRR, breakeven all mapped correctly."""
        node = make_mock_node()
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert result["wealth_signals"]["npv_usd"] == 120_000_000.0
        assert result["wealth_signals"]["irr"] == 0.18


class TestExtractiveSignals:
    """Extractive signals correctly mapped from governance."""

    def test_carbon_cost_preserved(self):
        """Carbon cost passes through unchanged."""
        node = make_mock_node()
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert result["extractive_signals"]["carbon_cost"] == 45.0

    def test_penalty_infinite_preserved(self):
        """Penalty infinite flag passes through."""
        node = make_mock_node()
        node.governance.penalty_infinite = True
        telemetry = make_mock_telemetry()
        result = geox_to_wealth(node, telemetry, Verdict.PROCEED)
        assert result["extractive_signals"]["penalty_inf"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])