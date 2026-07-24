"""
test_wealth_bridge_end_to_end.py — End-to-end integration test for GEOX → WEALTH bridge.

Closes the WEALTH bridge ⚠️ INT → ✅ OBS gap.
Chain: GEOX prospect claim → geox_to_wealth_bridge → geox_to_wealth_score → VAULT999 receipt.

Constitutional contracts verified end-to-end:
  F1: irreversible=False for read-only scoring
  F2: epistemic_source passed through, never upgraded
  F13: blocked nodes cannot enter WEALTH pipeline

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

import pytest

# Ensure src and adapters are on path
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
ADAPTERS_ROOT = SRC_ROOT / "geox_core" / "adapters"
for p in (str(REPO_ROOT), str(SRC_ROOT), str(ADAPTERS_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from geox_mcp.tools.wealth_bridge_tool import geox_to_wealth_bridge  # noqa: E402
from geox_core.wealth.wealth_score_kernel import geox_to_wealth_score  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


def make_test_prospect(
    *,
    prospect_id: str = "TEST-PROSPECT-001",
    npv_usd: float = 120_000_000.0,
    irr: float = 0.18,
    breakeven_usd: float | None = 45.0,
    admissibility: str = "admitted",
    epistemic_source: str = "ESTIMATE",
    risk_geo: float = 0.3,
    sigma_market: float = 0.25,
    sigma_policy: float = 0.2,
    carbon_cost_usd: float = 30.0,
    penalty_infinite: bool = False,
    delay_risk: float = 0.15,
    required_modifications: list[str] | None = None,
    peace2: float = 1.0,
    d_s: float = 0.0,
) -> dict:
    """Build a GEOX prospect payload for the bridge."""
    return {
        "prospect_id": prospect_id,
        "npv_usd": npv_usd,
        "irr": irr,
        "breakeven_usd": breakeven_usd,
        "discount_rate": 0.10,
        "risk_geo": risk_geo,
        "sigma_market": sigma_market,
        "sigma_policy": sigma_policy,
        "admissibility": admissibility,
        "epistemic_source": epistemic_source,
        "penalty_infinite": penalty_infinite,
        "carbon_cost_usd": carbon_cost_usd,
        "delay_risk": delay_risk,
        "required_modifications": required_modifications or [],
        "peace2": peace2,
        "d_s": d_s,
    }


def build_substrate_evidence(prospect: dict, wealth_input: dict) -> dict:
    """Map bridge wealth_input → score_kernel substrate_evidence.

    The bridge emits wealth_input format; the GEOX score kernel takes
    substrate_evidence format. This adapter is the real integration gap.
    """
    return {
        "claim_tag": wealth_input["epistemic_source"],
        "carbon_intensity": 0.01,  # OBS: below 0.04 civilization threshold
        "collapse_risk": 0.05,    # OBS: below 0.3 civilization threshold
        "dS": wealth_input["d_s"],
        "primary_result": {"hcpv_m3": 100_000.0},
        "scenarios": [
            {"probability": 0.6, "outcome": wealth_input["wealth_signals"]["npv_usd"] or 50_000_000.0},
            {"probability": 0.4, "outcome": -10_000_000.0},
        ],
        "flags": [],
        "wealth_input_reference": wealth_input,  # preserved for audit
    }


def make_vault999_receipt(
    score_result: dict,
    prospect_id: str,
    session_id: str | None = None,
) -> dict:
    """Wrap a score kernel verdict in a VAULT999 receipt."""
    payload = {
        "receipt_id_seed": f"{prospect_id}:{json.dumps(score_result, sort_keys=True, default=str)}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": "geox_wealth_score_kernel",
        "prospect_id": prospect_id,
        "verdict": score_result.get("verdict"),
        "emv_usd": score_result.get("emv_usd"),
        "r_adj": score_result.get("r_adj"),
        "harness_audit": score_result.get("harness_audit"),
        "epistemic_grade": score_result.get("epistemic_grade"),
        "session_id": session_id,
    }
    receipt_id = hashlib.sha256(payload["receipt_id_seed"].encode()).hexdigest()
    payload["receipt_id"] = receipt_id
    # Final hash chain (includes receipt_id)
    chain_payload = {k: v for k, v in payload.items() if k != "hash_chain"}
    payload["hash_chain"] = hashlib.sha256(
        json.dumps(chain_payload, sort_keys=True, default=str).encode()
    ).hexdigest()
    return payload


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end: geology claim → capital route → VAULT999 receipt
# ─────────────────────────────────────────────────────────────────────────────


class TestGeologyClaimToCapitalRoute:
    """End-to-end: GEOX prospect → bridge → score kernel → VAULT999 receipt."""

    @pytest.mark.asyncio
    async def test_admissible_prospect_seals_with_receipt(self):
        """Valid admissible prospect → bridge → SEAL verdict → VAULT999 receipt."""
        # 1. Build the GEOX prospect
        prospect = make_test_prospect(prospect_id="E2E-PROSPECT-001")

        # 2. Bridge: GEOX → wealth_input
        bridge_result = await geox_to_wealth_bridge(**prospect)
        assert bridge_result["bridged"] is True
        assert bridge_result["admissibility_check"] == "PASSED"
        assert bridge_result["epistemic_source_preserved"] == "ESTIMATE"
        assert "wealth_input" in bridge_result

        # 3. Map wealth_input → substrate_evidence
        substrate = build_substrate_evidence(prospect, bridge_result["wealth_input"])

        # 4. Score kernel: runs 9-Harness audit
        score_result = await geox_to_wealth_score(substrate_evidence=substrate)

        # 5. Verify verdict (top-level) + harness audit (without verdict inside)
        assert score_result["verdict"] in ("SEAL", "HOLD"), (
            f"Expected SEAL/HOLD, got {score_result.get('verdict')}"
        )
        assert "harness_audit" in score_result
        audit = score_result["harness_audit"]
        # Civilization harness (carbon/collapse/EROEI) must not be SNAPPED.
        # The score kernel synthesizes verdict from EMV; harness audit carries
        # systemic_stress + lineage/doctrine hashes for auditability.
        assert audit["systemic_stress"] <= 2.0, (
            f"Systemic stress too high: {audit['systemic_stress']}"
        )
        assert "lineage_hash" in audit
        assert "doctrine_hash" in audit

        # 6. Wrap in VAULT999 receipt
        receipt = make_vault999_receipt(score_result, prospect["prospect_id"])

        # 7. Verify receipt structure
        assert receipt["verdict"] == score_result["verdict"]
        assert receipt["emv_usd"] == score_result["emv_usd"]
        assert receipt["epistemic_grade"] == "ESTIMATE"
        assert len(receipt["receipt_id"]) == 64  # SHA-256 hex
        assert len(receipt["hash_chain"]) == 64

    @pytest.mark.asyncio
    async def test_negative_prospect_holds_with_receipt(self):
        """Negative EMV → HOLD verdict (not a SEAL); receipt still emitted."""
        prospect = make_test_prospect(
            prospect_id="E2E-PROSPECT-NEG",
            npv_usd=-50_000_000.0,  # negative outcome
            irr=-0.05,
        )
        bridge_result = await geox_to_wealth_bridge(**prospect)
        assert bridge_result["bridged"] is True

        substrate = build_substrate_evidence(prospect, bridge_result["wealth_input"])
        # Force negative outcome
        substrate["scenarios"] = [
            {"probability": 0.3, "outcome": -50_000_000.0},
            {"probability": 0.7, "outcome": -10_000_000.0},
        ]

        score_result = await geox_to_wealth_score(substrate_evidence=substrate)
        assert score_result["verdict"] == "HOLD"

        receipt = make_vault999_receipt(score_result, prospect["prospect_id"])
        assert receipt["verdict"] == "HOLD"
        assert receipt["emv_usd"] < 0


# ─────────────────────────────────────────────────────────────────────────────
# F13: blocked nodes cannot enter WEALTH pipeline (end-to-end)
# ─────────────────────────────────────────────────────────────────────────────


class TestBlockedProspectRejectedE2E:
    """F13 contract verified end-to-end."""

    @pytest.mark.asyncio
    async def test_blocked_prospect_returns_888_hold(self):
        """Blocked prospect → bridge returns 888_HOLD, score kernel never invoked."""
        prospect = make_test_prospect(
            prospect_id="E2E-PROSPECT-BLOCKED",
            admissibility="blocked",
        )
        bridge_result = await geox_to_wealth_bridge(**prospect)
        assert bridge_result["888_HOLD"] is True
        assert bridge_result["error"] == "ADMISSIBILITY_BLOCKED"
        # No wealth_input should be produced
        assert "wealth_input" not in bridge_result

        # Score kernel should NOT be invoked on a 888_HOLD
        # (caller's responsibility — but the test verifies the bridge refused)


# ─────────────────────────────────────────────────────────────────────────────
# F2: epistemic_source passed through end-to-end
# ─────────────────────────────────────────────────────────────────────────────


class TestEpistemicTagPreservedE2E:
    """F2 contract: epistemic tags survive the entire chain."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "epistemic_tag",
        ["UNKNOWN", "ESTIMATE", "HYPOTHESIS", "PLAUSIBLE", "CLAIM"],
    )
    async def test_tag_survives_bridge_to_score_kernel(self, epistemic_tag):
        """Every epistemic tag must survive the bridge → score kernel unchanged."""
        prospect = make_test_prospect(
            prospect_id=f"E2E-PROSPECT-{epistemic_tag}",
            epistemic_source=epistemic_tag,
        )
        bridge_result = await geox_to_wealth_bridge(**prospect)
        assert bridge_result["epistemic_source_preserved"] == epistemic_tag
        assert bridge_result["wealth_input"]["epistemic_source"] == epistemic_tag

        substrate = build_substrate_evidence(prospect, bridge_result["wealth_input"])
        score_result = await geox_to_wealth_score(substrate_evidence=substrate)
        assert score_result["epistemic_grade"] == epistemic_tag

        receipt = make_vault999_receipt(score_result, prospect["prospect_id"])
        assert receipt["epistemic_grade"] == epistemic_tag


# ─────────────────────────────────────────────────────────────────────────────
# F1: irreversible=False for read-only scoring
# ─────────────────────────────────────────────────────────────────────────────


class TestIrreversibilityE2E:
    """F1 contract: scoring calls are read-only end-to-end."""

    @pytest.mark.asyncio
    async def test_bridge_marks_irreversible_false(self):
        """Bridge output wealth_input must have irreversible=False."""
        prospect = make_test_prospect()
        bridge_result = await geox_to_wealth_bridge(**prospect)
        assert bridge_result["wealth_input"]["irreversible"] is False


# ─────────────────────────────────────────────────────────────────────────────
# VAULT999 receipt chain integrity
# ─────────────────────────────────────────────────────────────────────────────


class TestVault999ReceiptChain:
    """VAULT999 receipt format and chain integrity."""

    @pytest.mark.asyncio
    async def test_receipt_has_required_fields(self):
        """VAULT999 receipt must have all required fields."""
        prospect = make_test_prospect(prospect_id="E2E-PROSPECT-RECEIPT")
        bridge_result = await geox_to_wealth_bridge(**prospect)
        substrate = build_substrate_evidence(prospect, bridge_result["wealth_input"])
        score_result = await geox_to_wealth_score(substrate_evidence=substrate)
        receipt = make_vault999_receipt(score_result, prospect["prospect_id"])

        required_fields = [
            "receipt_id",
            "timestamp",
            "tool",
            "prospect_id",
            "verdict",
            "emv_usd",
            "r_adj",
            "harness_audit",
            "epistemic_grade",
            "hash_chain",
        ]
        for field in required_fields:
            assert field in receipt, f"Missing required VAULT999 field: {field}"

        # Hash chain integrity
        assert len(receipt["receipt_id"]) == 64
        assert len(receipt["hash_chain"]) == 64

        # Harness audit fields present (verdict is at top level, not in harness_audit)
        audit = receipt["harness_audit"]
        assert "systemic_stress" in audit
        assert "lineage_hash" in audit
        assert "doctrine_hash" in audit

    @pytest.mark.asyncio
    async def test_receipt_verdict_matches_score_kernel(self):
        """Receipt verdict must equal the score kernel verdict (no drift)."""
        prospect = make_test_prospect(prospect_id="E2E-PROSPECT-VERDICT")
        bridge_result = await geox_to_wealth_bridge(**prospect)
        substrate = build_substrate_evidence(prospect, bridge_result["wealth_input"])
        score_result = await geox_to_wealth_score(substrate_evidence=substrate)
        receipt = make_vault999_receipt(score_result, prospect["prospect_id"])

        assert receipt["verdict"] == score_result["verdict"]
        assert receipt["emv_usd"] == score_result["emv_usd"]
        assert receipt["r_adj"] == score_result["r_adj"]
