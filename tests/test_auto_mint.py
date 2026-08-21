"""
Tests for auto_mint — Gate-Pass → Claim Corpus Flywheel (v1)

Forged 2026-08-21. Tests the flywheel: kill-switch, dedup, canonical mint, state=DRAFT.
All tests use a disposable tmp DB — zero risk to live corpus.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from geox_mcp.services.auto_mint import mint_from_gate_pass, _fingerprint, _enabled


# ── Fixtures ──────────────────────────────────────────────────────────────────

CONTRAST_RESULT_SYNTHETIC: dict[str, Any] = {
    "ok": True,
    "tool": "geox_contrast_metabolize",
    "substrate_class": "INERT",
    "authority_ceiling": "COMPUTE_ONLY",
    "local_verdict": "QUALIFIED_CANDIDATE",
    "preferred_hypothesis": None,
    "stage1_isolate": {"anomaly_count": 3, "anomalies": []},
    "stage2_measure": {"measurements": []},
    "stage3_classify": {
        "stage": "CLASSIFY",
        "epistemic_label": "INT",
        "hypothesis_count": 3,
        "hypotheses": [
            {"hypothesis": "Class III AVO — gas sand at ~1800 m", "depth_m": 1800},
            {"hypothesis": "Class II AVO — oil-bearing turbidite at ~2100 m", "depth_m": 2100},
            {"hypothesis": "Lithological contrast — tight carbonate at ~2400 m", "depth_m": 2400},
        ],
        "preferred_hypothesis": None,
        "local_verdict": "QUALIFIED_CANDIDATE",
    },
    "metabolic_receipt": "abc123",
    "_evidence_receipt": {
        "sha256": "abc123",
        "tool": "geox_contrast_metabolize",
        "timestamp": "2026-08-21T00:00:00Z",
        "isError": False,
    },
}


@pytest.fixture()
def tmp_db(tmp_path: Path) -> str:
    """Return path to a disposable EarthMemory DB."""
    return str(tmp_path / "test_auto_mint.db")


def _count_claims(db_path: str) -> int:
    if not Path(db_path).exists():
        return 0
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM earth_memory").fetchone()[0]


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestKillSwitch:
    def test_off(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GEOX_AUTO_MINT", "0")
        assert _enabled() is False


class TestRegistryGuard:
    def test_unknown_tool_skips(self, tmp_db: str, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GEOX_EARTH_MEMORY_DB", tmp_db)
        monkeypatch.setenv("GEOX_AUTO_MINT", "1")
        r = asyncio.get_event_loop().run_until_complete(
            mint_from_gate_pass("geox_unknown_tool", {"ok": True, "local_verdict": "QUALIFIED_CANDIDATE"})
        )
        assert r is not None
        assert r.get("skipped") is not None


class TestVerdictGuard:
    def test_non_gatepass_skips(self, tmp_db: str, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GEOX_EARTH_MEMORY_DB", tmp_db)
        monkeypatch.setenv("GEOX_AUTO_MINT", "1")
        result = {"ok": True, "local_verdict": "COMPUTED", "stage1_isolate": {}, "stage3_classify": {}}
        r = asyncio.get_event_loop().run_until_complete(mint_from_gate_pass("geox_contrast_metabolize", result))
        assert r is not None
        assert r.get("skipped") is not None


class TestCanonicalMint:
    def test_synthetic_convergence(self, tmp_db: str, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GEOX_EARTH_MEMORY_DB", tmp_db)
        monkeypatch.setenv("GEOX_AUTO_MINT", "1")
        r = asyncio.get_event_loop().run_until_complete(
            mint_from_gate_pass(
                "geox_contrast_metabolize",
                CONTRAST_RESULT_SYNTHETIC,
                session_id="test-sess",
                actor_id="test-agent",
            )
        )
        assert r is not None
        assert r["minted"] is True
        assert r["claim_id"].startswith("clm_")
        assert r["earth_memory_id"] is not None
        assert r["state"] == "DRAFT"  # NEVER sealed by auto-mint

    def test_corpus_count_increments(self, tmp_db: str, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GEOX_EARTH_MEMORY_DB", tmp_db)
        monkeypatch.setenv("GEOX_AUTO_MINT", "1")
        before = _count_claims(tmp_db)
        asyncio.get_event_loop().run_until_complete(mint_from_gate_pass("geox_contrast_metabolize", CONTRAST_RESULT_SYNTHETIC))
        assert _count_claims(tmp_db) == before + 1

    def test_provenance_contains_auto_mint(self, tmp_db: str, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GEOX_EARTH_MEMORY_DB", tmp_db)
        monkeypatch.setenv("GEOX_AUTO_MINT", "1")
        asyncio.get_event_loop().run_until_complete(mint_from_gate_pass("geox_contrast_metabolize", CONTRAST_RESULT_SYNTHETIC))
        with sqlite3.connect(tmp_db) as conn:
            payload = json.loads(conn.execute("SELECT payload FROM earth_memory ORDER BY timestamp DESC LIMIT 1").fetchone()[0])
        assert payload["provenance"].startswith("auto-mint:v1")
        assert payload["extra_metadata"]["auto_mint"] is True
        assert payload["extra_metadata"]["source_tool"] == "geox_contrast_metabolize"


class TestDedup:
    def test_second_identical_input_skips(self, tmp_db: str, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GEOX_EARTH_MEMORY_DB", tmp_db)
        monkeypatch.setenv("GEOX_AUTO_MINT", "1")
        asyncio.get_event_loop().run_until_complete(mint_from_gate_pass("geox_contrast_metabolize", CONTRAST_RESULT_SYNTHETIC))
        r = asyncio.get_event_loop().run_until_complete(
            mint_from_gate_pass("geox_contrast_metabolize", CONTRAST_RESULT_SYNTHETIC)
        )
        assert r is not None
        assert r.get("skipped") == "dedup"
        assert r.get("existing_claim_id") is not None


class TestFingerprintDeterministic:
    def test_same_input_same_fingerprint(self):
        fp1 = _fingerprint("geox_contrast_metabolize", CONTRAST_RESULT_SYNTHETIC)
        fp2 = _fingerprint("geox_contrast_metabolize", CONTRAST_RESULT_SYNTHETIC)
        assert fp1 == fp2 and fp1 is not None


class TestSyntheticGuard:
    """A fixture is not a decision — synthetic runs must NEVER enter the sovereign corpus (F2)."""

    def test_synthetic_fixture_never_mints(self, tmp_db: str, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GEOX_EARTH_MEMORY_DB", tmp_db)
        monkeypatch.setenv("GEOX_AUTO_MINT", "1")
        fixture = dict(CONTRAST_RESULT_SYNTHETIC, mode="synthetic")
        r = asyncio.run(mint_from_gate_pass("geox_contrast_metabolize", fixture))
        assert r == {"skipped": "synthetic fixture — real evidence only"}
        assert _count_claims(tmp_db) == 0

    def test_profile_mode_still_mints(self, tmp_db: str, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GEOX_EARTH_MEMORY_DB", tmp_db)
        monkeypatch.setenv("GEOX_AUTO_MINT", "1")
        real = dict(CONTRAST_RESULT_SYNTHETIC, mode="profile")
        r = asyncio.run(mint_from_gate_pass("geox_contrast_metabolize", real))
        assert r is not None and r.get("minted") is True
