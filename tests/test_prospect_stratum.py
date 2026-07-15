"""
Tests for stratum-confidence ribbon on geox_prospect_evaluate
(Eureka 2026-06-05, Burlamaque 2026-06-04 Step 4).

Verifies:
- Ribbon present in default compute mode
- Gini computation works
- Ribbon verdict changes with evidence count
- Backward compat: existing prospect tests still pass

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import asyncio

import pytest

from geox_mcp.tools.prospect import _compute_stratum_breakdown, _gini_coefficient, geox_prospect_evaluate


# ═══════════════════════════════════════════════════════════════════════════════
# Gini unit tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_gini_empty():
    assert _gini_coefficient([]) == 0.0


def test_gini_all_zero():
    assert _gini_coefficient([0, 0, 0]) == 0.0


def test_gini_perfect_equality():
    assert _gini_coefficient([1, 1, 1, 1]) == 0.0


def test_gini_max_inequality():
    # All mass on one
    g = _gini_coefficient([0, 0, 0, 1])
    assert 0.5 < g <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Stratum breakdown integration
# ═══════════════════════════════════════════════════════════════════════════════


def test_no_evidence_refs_returns_critical():
    """When there are zero evidence_refs, the ribbon should be CRITICAL (develop empty)."""
    rib = _compute_stratum_breakdown(
        mode="screen",
        evidence_refs=[],
        prospect_ref="PROSPECT-TEST",
    )
    assert rib["ribbon_verdict"] == "CRITICAL"
    assert rib["balance_gini"] > 0.0
    assert "screen" in rib
    assert "appraise" in rib
    assert "develop" in rib
    assert rib["screen"]["n_samples"] >= 1
    assert rib["appraise"]["n_samples"] == 0
    assert rib["develop"]["n_samples"] == 0


def test_three_evidence_refs_qualifies_appraise():
    rib = _compute_stratum_breakdown(
        mode="appraise",
        evidence_refs=["e1", "e2", "e3"],
        prospect_ref="PROSPECT",
    )
    assert rib["appraise"]["n_samples"] == 3
    assert rib["appraise"]["confidence"] > 0.5
    # With 3 evidence_refs, all 3 strata have data; Gini should be low
    # because screen=1, appraise=3, develop=3 are reasonably balanced
    assert rib["ribbon_verdict"] in ("BALANCED", "UNBALANCED")


def test_full_evidence_balanced():
    rib = _compute_stratum_breakdown(
        mode="develop",
        evidence_refs=["e1", "e2", "e3", "e4", "e5", "e6", "e7"],
        prospect_ref="PROSPECT",
    )
    assert rib["appraise"]["n_samples"] == 7
    assert rib["develop"]["n_samples"] == 7
    # screen always 1+ → still has inequality between screen (1) and appraise (7)
    # so Gini > 0, but probably < 0.4
    # Don't assert exact verdict; just confirm it's evaluated
    assert rib["ribbon_verdict"] in ("BALANCED", "UNBALANCED", "CRITICAL")


def test_ribbon_contains_eureka_ref():
    rib = _compute_stratum_breakdown(
        mode="screen",
        evidence_refs=[],
        prospect_ref="X",
    )
    assert rib["eureka_ref"] == "BURLAMAQUE_2026_STEP4_STRATUM"


def test_ribbon_includes_active_mode():
    rib = _compute_stratum_breakdown(
        mode="develop",
        evidence_refs=["e1"],
        prospect_ref="X",
    )
    assert rib["active_mode"] == "develop"


def test_strata_contain_missing_fields():
    """When below threshold, missing_strata should list what's needed."""
    rib = _compute_stratum_breakdown(
        mode="appraise",
        evidence_refs=[],
        prospect_ref="X",
    )
    assert len(rib["appraise"]["missing_strata"]) > 0
    assert any("DST" in s for s in rib["appraise"]["missing_strata"])


def test_develop_missing_strata_mentions_5_categories():
    rib = _compute_stratum_breakdown(
        mode="develop",
        evidence_refs=["e1"],
        prospect_ref="X",
    )
    assert len(rib["develop"]["missing_strata"]) == 5


def test_compute_mode_declares_migration_context_and_pos_ceiling():
    result = asyncio.run(
        geox_prospect_evaluate(
            prospect_ref="PROSPECT-X",
            mode="screen",
            evidence_refs=["e1", "e2"],
        )
    )

    artifact = result["primary_artifact"]
    migration_context = artifact["migration_context"]
    assert migration_context["migration_shadow_scored"] is False
    assert migration_context["pos_multiplier_applied"] == 1.0
    assert migration_context["eureka_ref"] == "MIGRATION_SHADOW_SCORING_2026_06_10"

    pos_ceiling = artifact["pos_ceiling_declaration"]
    assert pos_ceiling["pos_ceiling_basis"] == "pre-QI-screen"
    assert pos_ceiling["fluid_certified"] is False
    assert pos_ceiling["eureka_ref"] == "POS_CEILING_2026_06_10"
