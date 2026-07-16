"""
Tests for geox_bid_round_screener — MBR 2026 Multi-Block Bid Round Screener.

Verifies F1-F13 compliance:
  F2 TRUTH     — all evidence fields labeled, composite score capped at 0.90
  F3 WITNESS   — operator_actor_id required (no anonymous)
  F7 HUMILITY  — confidence cap at 0.90
  F9 ANTI-HANTU — no fabricated data; scoring based on heuristics
  F11 AUDIT    — audit_receipt present in every output
  F12 INJECTION — hostile input rejected by sanitization
  F13 SOVEREIGN — output is advisory, not binding

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_GEOX_SRC = Path("/root/geox/src")
if str(_GEOX_SRC) not in sys.path:
    sys.path.insert(0, str(_GEOX_SRC))

from geox_mcp.tools.bid_round_screener import (
    BidRoundRequest,
    BidRoundResponse,
    BlockInput,
    BlockRecommendation,
    _assign_recommendation,
    _BID_THRESHOLD,
    _PARTNER_THRESHOLD,
    _CONFIDENCE_CAP,
    _compute_capital_required,
    _compute_composite_score,
    _compute_evidence_strength,
    _compute_fiscal_score,
    _compute_geological_risk,
    _derive_play_type,
    _generate_tool_call_hash,
    _identify_key_risks,
    geox_bid_round_screener,
)


# ── FIXTURE ──────────────────────────────────────────────────────────────────


def _make_mbr2026_request() -> BidRoundRequest:
    """Full MBR 2026 bid round with 4 blocks (2 Malay exploration, 1 Sabah, 1 DRO)."""
    return BidRoundRequest(
        bid_round_id="MBR_2026",
        operator="NOC_A_MPM",
        operator_actor_id="ARIF",
        blocks=[
            {
                "block_id": "PM447",
                "basin": "Malay",
                "lat_min": 5.0,
                "lat_max": 5.5,
                "lon_min": 104.3,
                "lon_max": 104.7,
                "block_type": "exploration",
            },
            {
                "block_id": "PM523",
                "basin": "Malay",
                "lat_min": 4.5,
                "lat_max": 5.0,
                "lon_min": 103.5,
                "lon_max": 104.0,
                "block_type": "exploration",
            },
            {
                "block_id": "SB304",
                "basin": "Sabah",
                "lat_min": 5.3,
                "lat_max": 6.0,
                "lon_min": 118.0,
                "lon_max": 118.5,
                "block_type": "exploration",
            },
            {
                "block_id": "Cempaka",
                "basin": "Malay",
                "lat_min": 5.0,
                "lat_max": 5.3,
                "lon_min": 104.5,
                "lon_max": 104.7,
                "block_type": "DRO",
            },
        ],
        fiscal_regimes=["Standard_PSC", "EPT_ShallowWater"],
        risk_tolerance="medium",
    )


# ── UNIT: Scoring Functions ──────────────────────────────────────────────────


class TestScoringFunctions:
    def test_derive_play_type_malay_exploration(self):
        assert _derive_play_type("Malay", "exploration") == "tertiary_clastic"

    def test_derive_play_type_sabah_exploration(self):
        assert _derive_play_type("Sabah", "exploration") == "pre_tertiary_carbonate"

    def test_derive_play_type_sarawak_exploration(self):
        assert _derive_play_type("Sarawak", "exploration") == "carbonate_buildup"

    def test_derive_play_type_dro(self):
        assert _derive_play_type("Malay", "DRO") == "brownfield_dro"
        assert _derive_play_type("Sabah", "DRO") == "brownfield_dro"

    def test_derive_play_type_unknown_basin(self):
        assert _derive_play_type("FrontierBasin", "exploration") == "mixed_play"

    def test_geological_risk_malay(self):
        risk = _compute_geological_risk("Malay", "exploration")
        assert 0.0 < risk <= 1.0
        assert risk == 0.30

    def test_geological_risk_sabah(self):
        risk = _compute_geological_risk("Sabah", "exploration")
        assert risk == 0.45

    def test_geological_risk_dro_discount(self):
        risk_expl = _compute_geological_risk("Malay", "exploration")
        risk_dro = _compute_geological_risk("Malay", "DRO")
        assert risk_dro < risk_expl

    def test_capital_required_exploration_malay(self):
        assert _compute_capital_required("Malay", "exploration") == 0.30

    def test_capital_required_dro_malay(self):
        assert _compute_capital_required("Malay", "DRO") == 0.20

    def test_fiscal_score_standard_psc(self):
        assert _compute_fiscal_score(["Standard_PSC"]) == 0.65

    def test_fiscal_score_best_of_multiple(self):
        score = _compute_fiscal_score(["Standard_PSC", "EPT_ShallowWater"])
        assert score == 0.75

    def test_fiscal_score_unknown_regime(self):
        assert _compute_fiscal_score(["UnknownRegime"]) == 0.50

    def test_fiscal_score_empty_list(self):
        assert _compute_fiscal_score([]) == 0.50

    def test_evidence_strength_capped_at_090(self):
        """F7 HUMILITY: evidence strength never exceeds 0.90."""
        strength = _compute_evidence_strength("Malay", "DRO", 0.10)
        assert strength <= _CONFIDENCE_CAP

    def test_evidence_strength_dro_higher_than_exploration(self):
        s_dro = _compute_evidence_strength("Malay", "DRO", 0.30)
        s_expl = _compute_evidence_strength("Malay", "exploration", 0.30)
        assert s_dro >= s_expl

    def test_composite_score_capped_at_090(self):
        """F7 HUMILITY: composite score never exceeds 0.90."""
        score = _compute_composite_score(0.90, 0.10, 0.90, "high")
        assert score <= _CONFIDENCE_CAP

    def test_composite_score_risk_tolerance_effect(self):
        score_low = _compute_composite_score(0.80, 0.40, 0.65, "low")
        score_high = _compute_composite_score(0.80, 0.40, 0.65, "high")
        assert score_high > score_low

    def test_assign_recommendation_bid(self):
        assert _assign_recommendation(0.80) == "BID"

    def test_assign_recommendation_partner(self):
        assert _assign_recommendation(0.60) == "PARTNER"

    def test_assign_recommendation_no_bid(self):
        assert _assign_recommendation(0.30) == "NO_BID"

    def test_assign_recommendation_boundary_bid(self):
        assert _assign_recommendation(_BID_THRESHOLD) == "BID"

    def test_assign_recommendation_boundary_partner(self):
        assert _assign_recommendation(_PARTNER_THRESHOLD) == "PARTNER"

    def test_identify_key_risks_high_risk(self):
        risks = _identify_key_risks("Sabah", "exploration", 0.60, 0.40)
        assert "high_geological_risk" in risks
        assert "active_tectonics_trap_integrity" in risks

    def test_identify_key_risks_dro(self):
        risks = _identify_key_risks("Malay", "DRO", 0.15, 0.75)
        assert "brownfield_decline_curve" in risks

    def test_identify_key_risks_low_risk_malay(self):
        risks = _identify_key_risks("Malay", "exploration", 0.20, 0.80)
        assert "standard_exploration_risk" in risks


# ── UNIT: Pydantic Schemas ───────────────────────────────────────────────────


class TestSchemas:
    def test_block_input_valid(self):
        block = BlockInput(
            block_id="PM447",
            basin="Malay",
            lat_min=5.0,
            lat_max=5.5,
            lon_min=104.3,
            lon_max=104.7,
        )
        assert block.block_id == "PM447"
        assert block.block_type == "exploration"

    def test_block_input_dro(self):
        block = BlockInput(
            block_id="Cempaka",
            basin="Malay",
            lat_min=5.0,
            lat_max=5.3,
            lon_min=104.5,
            lon_max=104.7,
            block_type="DRO",
        )
        assert block.block_type == "DRO"

    def test_block_input_invalid_bbox(self):
        with pytest.raises(ValueError, match="lat_max must be >= lat_min"):
            BlockInput(
                block_id="Bad",
                basin="Malay",
                lat_min=5.5,
                lat_max=5.0,
                lon_min=104.3,
                lon_max=104.7,
            )

    def test_bid_round_request_valid(self):
        req = BidRoundRequest(
            bid_round_id="MBR_2026",
            operator="NOC_A_MPM",
            operator_actor_id="ARIF",
            blocks=[
                {
                    "block_id": "PM447",
                    "basin": "Malay",
                    "lat_min": 5.0,
                    "lat_max": 5.5,
                    "lon_min": 104.3,
                    "lon_max": 104.7,
                }
            ],
        )
        assert len(req.blocks) == 1
        assert req.risk_tolerance == "medium"

    def test_bid_round_request_empty_blocks_fails(self):
        with pytest.raises(ValueError):
            BidRoundRequest(
                bid_round_id="MBR_2026",
                operator="NOC_A_MPM",
                operator_actor_id="ARIF",
                blocks=[],
            )

    def test_recommendation_model(self):
        rec = BlockRecommendation(
            block_id="PM447",
            basin="Malay",
            recommendation="BID",
            composite_score=0.78,
            play_type="tertiary_clastic",
            geological_risk=0.25,
            capital_required=0.30,
            evidence_strength=0.85,
            fiscal_score=0.65,
            key_risks=["standard_exploration_risk"],
            supporting_evidence_refs=[],
            challenging_evidence_refs=[],
        )
        assert rec.recommendation == "BID"
        assert rec.epistemic_band == "INT_SCREEN"


# ── INTEGRATION: Full Pipeline ───────────────────────────────────────────────


class TestIntegration:
    @pytest.mark.asyncio
    async def test_happy_path_mbr2026(self):
        """Full MBR 2026 round with 4 blocks."""
        req = _make_mbr2026_request()
        resp = await geox_bid_round_screener(req)

        assert isinstance(resp, BidRoundResponse)
        assert len(resp.recommendation_matrix) == 4

        for rec in resp.recommendation_matrix:
            assert rec.recommendation in ("BID", "PARTNER", "NO_BID")
            assert 0.0 <= rec.composite_score <= _CONFIDENCE_CAP
            assert rec.epistemic_band == "INT_SCREEN"

        scores = [r.composite_score for r in resp.recommendation_matrix]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_summary_counts(self):
        req = _make_mbr2026_request()
        resp = await geox_bid_round_screener(req)

        bid = sum(1 for r in resp.recommendation_matrix if r.recommendation == "BID")
        partner = sum(1 for r in resp.recommendation_matrix if r.recommendation == "PARTNER")
        no_bid = sum(1 for r in resp.recommendation_matrix if r.recommendation == "NO_BID")

        assert resp.summary.bid_count == bid
        assert resp.summary.partner_count == partner
        assert resp.summary.no_bid_count == no_bid
        assert resp.summary.maruah_check == "CLEAR"

    @pytest.mark.asyncio
    async def test_f1_f13_compliance_report(self):
        req = _make_mbr2026_request()
        resp = await geox_bid_round_screener(req)

        assert resp.f1_f13_compliance.reversibility == "FULL"
        assert resp.f1_f13_compliance.evidence_labeled is True
        assert resp.f1_f13_compliance.humility_cap_applied is True
        assert resp.f1_f13_compliance.maruah_preserved is True
        assert resp.f1_f13_compliance.audit_logged is True

    @pytest.mark.asyncio
    async def test_f11_audit_receipt(self):
        req = _make_mbr2026_request()
        resp = await geox_bid_round_screener(req)

        assert resp.audit_receipt is not None
        assert resp.audit_receipt.tool_call_hash.startswith("VAULT999::BR::")
        assert resp.audit_receipt.actor_id == "ARIF"
        assert resp.audit_receipt.verdict == "PLAUSIBLE"
        assert resp.audit_receipt.issued_at

    @pytest.mark.asyncio
    async def test_dro_lower_risk_than_exploration(self):
        req = BidRoundRequest(
            bid_round_id="TEST_DRO",
            operator="TEST",
            operator_actor_id="test_user",
            blocks=[
                {
                    "block_id": "ExplBlock",
                    "basin": "Malay",
                    "lat_min": 5.0,
                    "lat_max": 5.5,
                    "lon_min": 104.3,
                    "lon_max": 104.7,
                    "block_type": "exploration",
                },
                {
                    "block_id": "DROBlock",
                    "basin": "Malay",
                    "lat_min": 5.0,
                    "lat_max": 5.3,
                    "lon_min": 104.5,
                    "lon_max": 104.7,
                    "block_type": "DRO",
                },
            ],
        )
        resp = await geox_bid_round_screener(req)
        dro = next(r for r in resp.recommendation_matrix if r.block_id == "DROBlock")
        expl = next(r for r in resp.recommendation_matrix if r.block_id == "ExplBlock")
        assert dro.geological_risk < expl.geological_risk

    @pytest.mark.asyncio
    async def test_sabah_higher_risk_than_malay(self):
        req = BidRoundRequest(
            bid_round_id="TEST_BASIN",
            operator="TEST",
            operator_actor_id="test_user",
            blocks=[
                {
                    "block_id": "MalayBlock",
                    "basin": "Malay",
                    "lat_min": 5.0,
                    "lat_max": 5.5,
                    "lon_min": 104.3,
                    "lon_max": 104.7,
                    "block_type": "exploration",
                },
                {
                    "block_id": "SabahBlock",
                    "basin": "Sabah",
                    "lat_min": 5.3,
                    "lat_max": 6.0,
                    "lon_min": 118.0,
                    "lon_max": 118.5,
                    "block_type": "exploration",
                },
            ],
        )
        resp = await geox_bid_round_screener(req)
        sabah = next(r for r in resp.recommendation_matrix if r.block_id == "SabahBlock")
        malay = next(r for r in resp.recommendation_matrix if r.block_id == "MalayBlock")
        assert sabah.geological_risk > malay.geological_risk


# ── SECURITY: F12 INJECTION + F3 WITNESS ─────────────────────────────────────


class TestSecurity:
    @pytest.mark.asyncio
    async def test_f3_witness_actor_required(self):
        req = BidRoundRequest(
            bid_round_id="MBR_2026",
            operator="NOC_A_MPM",
            operator_actor_id="ARIF",
            blocks=[
                {
                    "block_id": "PM447",
                    "basin": "Malay",
                    "lat_min": 5.0,
                    "lat_max": 5.5,
                    "lon_min": 104.3,
                    "lon_max": 104.7,
                }
            ],
        )
        req.operator_actor_id = ""
        with pytest.raises(ValueError, match="F3 WITNESS"):
            await geox_bid_round_screener(req)

    def test_f12_injection_block_id(self):
        with pytest.raises(ValueError, match="sanitization"):
            BlockInput(
                block_id="; rm -rf /;",
                basin="Malay",
                lat_min=5.0,
                lat_max=5.5,
                lon_min=104.3,
                lon_max=104.7,
            )

    def test_f12_injection_basin(self):
        with pytest.raises(ValueError, match="sanitization"):
            BlockInput(
                block_id="PM447",
                basin="Malay; DROP TABLE blocks;--",
                lat_min=5.0,
                lat_max=5.5,
                lon_min=104.3,
                lon_max=104.7,
            )

    def test_f12_injection_bid_round_id(self):
        with pytest.raises(ValueError, match="sanitization"):
            BidRoundRequest(
                bid_round_id="$(evil_command)",
                operator="NOC_A",
                operator_actor_id="ARIF",
                blocks=[
                    {
                        "block_id": "PM447",
                        "basin": "Malay",
                        "lat_min": 5.0,
                        "lat_max": 5.5,
                        "lon_min": 104.3,
                        "lon_max": 104.7,
                    }
                ],
            )

    def test_f12_injection_operator_actor_id(self):
        with pytest.raises(ValueError, match="sanitization"):
            BidRoundRequest(
                bid_round_id="MBR_2026",
                operator="NOC_A",
                operator_actor_id="ARIF`whoami`",
                blocks=[
                    {
                        "block_id": "PM447",
                        "basin": "Malay",
                        "lat_min": 5.0,
                        "lat_max": 5.5,
                        "lon_min": 104.3,
                        "lon_max": 104.7,
                    }
                ],
            )

    def test_f12_long_field_rejected(self):
        with pytest.raises(ValueError, match="max length"):
            BlockInput(
                block_id="A" * 200,
                basin="Malay",
                lat_min=5.0,
                lat_max=5.5,
                lon_min=104.3,
                lon_max=104.7,
            )

    def test_f12_script_tag_rejected(self):
        with pytest.raises(ValueError, match="sanitization"):
            BlockInput(
                block_id="<script>alert(1)</script>",
                basin="Malay",
                lat_min=5.0,
                lat_max=5.5,
                lon_min=104.3,
                lon_max=104.7,
            )


# ── AUDIT: Hash Determinism ──────────────────────────────────────────────────


class TestAudit:
    def test_hash_deterministic(self):
        req1 = _make_mbr2026_request()
        req2 = _make_mbr2026_request()
        assert _generate_tool_call_hash(req1) == _generate_tool_call_hash(req2)

    def test_hash_differs_on_actor(self):
        req1 = _make_mbr2026_request()
        req2 = _make_mbr2026_request()
        req2.operator_actor_id = "OTHER"
        assert _generate_tool_call_hash(req1) != _generate_tool_call_hash(req2)

    def test_hash_prefix(self):
        h = _generate_tool_call_hash(_make_mbr2026_request())
        assert h.startswith("VAULT999::BR::")


# ── EDGE CASES ───────────────────────────────────────────────────────────────


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_single_block(self):
        req = BidRoundRequest(
            bid_round_id="TEST",
            operator="TEST",
            operator_actor_id="test_user",
            blocks=[
                {
                    "block_id": "PM447",
                    "basin": "Malay",
                    "lat_min": 5.0,
                    "lat_max": 5.5,
                    "lon_min": 104.3,
                    "lon_max": 104.7,
                }
            ],
        )
        resp = await geox_bid_round_screener(req)
        assert len(resp.recommendation_matrix) == 1
        assert resp.summary.bid_count + resp.summary.partner_count + resp.summary.no_bid_count == 1

    @pytest.mark.asyncio
    async def test_high_risk_tolerance_scores_higher(self):
        blocks = [
            {
                "block_id": "PM447",
                "basin": "Sabah",
                "lat_min": 5.3,
                "lat_max": 6.0,
                "lon_min": 118.0,
                "lon_max": 118.5,
                "block_type": "exploration",
            }
        ]
        req_high = BidRoundRequest(
            bid_round_id="T",
            operator="T",
            operator_actor_id="T",
            blocks=blocks,
            risk_tolerance="high",
        )
        req_low = BidRoundRequest(
            bid_round_id="T",
            operator="T",
            operator_actor_id="T",
            blocks=blocks,
            risk_tolerance="low",
        )
        resp_high = await geox_bid_round_screener(req_high)
        resp_low = await geox_bid_round_screener(req_low)
        assert resp_high.recommendation_matrix[0].composite_score >= resp_low.recommendation_matrix[0].composite_score

    @pytest.mark.asyncio
    async def test_unknown_basin_graceful(self):
        req = BidRoundRequest(
            bid_round_id="TEST",
            operator="TEST",
            operator_actor_id="test_user",
            blocks=[
                {
                    "block_id": "Unknown1",
                    "basin": "FrontierBasin",
                    "lat_min": 0.0,
                    "lat_max": 1.0,
                    "lon_min": 100.0,
                    "lon_max": 101.0,
                    "block_type": "exploration",
                }
            ],
        )
        resp = await geox_bid_round_screener(req)
        assert len(resp.recommendation_matrix) == 1
        rec = resp.recommendation_matrix[0]
        assert rec.play_type == "mixed_play"
        assert rec.recommendation in ("BID", "PARTNER", "NO_BID")

    @pytest.mark.asyncio
    async def test_multiple_fiscal_regimes_uses_best(self):
        req = BidRoundRequest(
            bid_round_id="TEST",
            operator="TEST",
            operator_actor_id="test_user",
            blocks=[
                {
                    "block_id": "PM447",
                    "basin": "Malay",
                    "lat_min": 5.0,
                    "lat_max": 5.5,
                    "lon_min": 104.3,
                    "lon_max": 104.7,
                }
            ],
            fiscal_regimes=["SFA", "EPT_ShallowWater"],
        )
        resp = await geox_bid_round_screener(req)
        assert resp.recommendation_matrix[0].fiscal_score == 0.75
