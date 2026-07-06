"""
test_prospect_falsify_mode — Falsify/Cabar mode unit tests
Forged: 2026-07-06 | Mode: geox_prospect(falsify/cabar)

Tests the 4 contradiction rules in the FALSIFY/CABAR mode:
  1. prospect_ref keyword validation ("invalid", "leak")
  2. HC column > 0 but seal_thickness == 0
  3. HC column > 2× seal_thickness
  4. Missing evidence_refs = gap

Also tests APEX scoring consistency and falsify/cabar mode parity.
"""

from __future__ import annotations
import pytest, asyncio
from geox_mcp.tools.prospect_unified import geox_prospect


class TestProspectFalsifyMode:
    """Falsify/Cabar mode — contradiction detection and APEX scoring."""

    @pytest.fixture
    def valid_structural_map(self):
        return {
            "estimated_column_height_m": 80,
            "seal_thickness_m": 40,
        }

    # ── Contradiction Rules ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_valid_prospect_no_contradictions(self, valid_structural_map):
        """Valid prospect: no contradictions, ac_risk=0.10, G=0.85."""
        r = await geox_prospect(
            prospect_ref="BOKOR-NORTH",
            mode="falsify",
            evidence_refs=["geox://stratigraphy/sabah/BOKOR-FM"],
            structural_map_inline=valid_structural_map,
        )
        assert r["falsified"] is False
        assert r["results"]["contradictions"] == []
        assert r["results"]["gaps"] == []
        assert r["apex_score"]["G"] == 0.85
        assert r["apex_score"]["C_dark"] == 0.15
        assert r["ac_risk"] == 0.10
        assert r["witness_chain"]["W3"] == 0.90
        assert r["witness_chain"]["human_ack"] is True

    @pytest.mark.asyncio
    async def test_invalid_keyword_leak(self):
        """prospect_ref containing 'leak' → contradiction."""
        r = await geox_prospect(prospect_ref="LEAK-BOKOR", mode="falsify")
        assert r["falsified"] is True
        assert any("LEAK-BOKOR" in c for c in r["results"]["contradictions"])

    @pytest.mark.asyncio
    async def test_invalid_keyword_invalid(self):
        """prospect_ref containing 'invalid' → contradiction."""
        r = await geox_prospect(prospect_ref="INVALID-SEAL", mode="falsify")
        assert r["falsified"] is True
        assert any("INVALID-SEAL" in c for c in r["results"]["contradictions"])

    @pytest.mark.asyncio
    async def test_hc_column_positive_but_seal_zero(self):
        """HC column > 0 but seal_thickness = 0 → physical contradiction."""
        r = await geox_prospect(
            prospect_ref="TEST",
            mode="falsify",
            structural_map_inline={"estimated_column_height_m": 100, "seal_thickness_m": 0},
        )
        assert r["falsified"] is True
        assert any("seal thickness is zero" in c for c in r["results"]["contradictions"])

    @pytest.mark.asyncio
    async def test_hc_column_exceeds_twice_seal_capacity(self):
        """HC column > 2× seal_thickness → seal capacity exceeded."""
        r = await geox_prospect(
            prospect_ref="TEST",
            mode="falsify",
            structural_map_inline={"estimated_column_height_m": 300, "seal_thickness_m": 50},
        )
        assert r["falsified"] is True
        assert any("exceeds critical seal capacity" in c for c in r["results"]["contradictions"])

    # ── Gap Detection ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_no_evidence_refs_is_gap(self, valid_structural_map):
        """No evidence_refs → gaps entry, not contradiction."""
        r = await geox_prospect(
            prospect_ref="VALID-PROSPECT",
            mode="falsify",
            structural_map_inline=valid_structural_map,
        )
        assert r["falsified"] is False
        assert any("No verified evidence" in g for g in r["results"]["gaps"])

    # ── APEX Score Consistency ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_falsified_prospect_c_dark_high(self):
        """Falsified prospect → C_dark=0.50, W3=0.40, human_ack=False."""
        r = await geox_prospect(
            prospect_ref="LEAK-BOKOR",
            mode="falsify",
            structural_map_inline={"estimated_column_height_m": 100, "seal_thickness_m": 0},
        )
        assert r["falsified"] is True
        assert r["apex_score"]["C_dark"] == 0.50
        assert r["apex_score"]["G"] == 0.50
        assert r["witness_chain"]["W3"] == 0.40
        assert r["witness_chain"]["human_ack"] is False
        assert r["ac_risk"] == 0.95

    @pytest.mark.asyncio
    async def test_valid_prospect_c_dark_low(self, valid_structural_map):
        """Clean prospect → C_dark=0.15, G=0.85, W3=0.90."""
        r = await geox_prospect(
            prospect_ref="BOKOR-NORTH",
            mode="falsify",
            evidence_refs=["geox://stratigraphy/sabah/BOKOR-FM"],
            structural_map_inline=valid_structural_map,
        )
        assert r["falsified"] is False
        assert r["apex_score"]["C_dark"] == 0.15
        assert r["apex_score"]["G"] == 0.85
        assert r["witness_chain"]["W3"] == 0.90
        assert r["ac_risk"] == 0.10

    # ── Mode Parity ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_falsify_cabar_mode_parity(self, valid_structural_map):
        """'falsify' and 'cabar' modes return structurally identical output."""
        r_falsify = await geox_prospect(
            prospect_ref="PARITY-TEST",
            mode="falsify",
            evidence_refs=["ref1"],
            structural_map_inline=valid_structural_map,
        )
        r_cabar = await geox_prospect(
            prospect_ref="PARITY-TEST",
            mode="cabar",
            evidence_refs=["ref1"],
            structural_map_inline=valid_structural_map,
        )
        assert r_falsify.keys() == r_cabar.keys()
        assert r_falsify["falsified"] == r_cabar["falsified"]
        assert r_falsify["apex_score"] == r_cabar["apex_score"]
        assert r_falsify["witness_chain"] == r_cabar["witness_chain"]

    # ── Non-falsify modes delegate correctly ───────────────────────────

    @pytest.mark.asyncio
    async def test_non_falsify_mode_delegates(self):
        """screen/appraise/develop modes delegate without TypeError."""
        r = await geox_prospect(
            prospect_ref="DELEGATE-TEST",
            mode="screen",
            evidence_refs=["geox://stratigraphy/sabah/BOKOR-FM"],
        )
        # Delegate ran without TypeError — wrapper bug fixed.
        # The screen-mode delegate returns APEX-form output, not falsify structure.
        assert isinstance(r, dict)
        assert len(r) > 0
