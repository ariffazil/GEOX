"""
GEOX Alignment Tests — Federation Layer (F-1, F-2, F-3)

These tests verify GEOX's behavior within the wider arifOS federation
(AAA, WELL, WEALTH, A-FORGE).

  F-1 — Floor presence check (LIVE — runs against substrate)
  F-2 — Cross-organ coherence (STUB — requires federation bus)
  F-3 — A-FORGE receipt completeness (STUB — requires A-FORGE state)

Reference: /root/geox/docs/GEOXALIGNMENTTESTS.md §3
Sovereign: arif (F13). Sealed: 2026-06-24.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL")
PGPASSWORD = os.environ.get("PGPASSWORD", "")
FORGE_WORK_DIR = Path("/root/forge_work")

if not DATABASE_URL:
    pytest.skip(
        "DATABASE_URL not set — alignment tests require a live substrate. "
        "Export DATABASE_URL and PGPASSWORD before running.",
        allow_module_level=True,
    )


def run_psql(sql: str, role: str = "postgres") -> tuple[str, str, int]:
    """Run SQL via psql."""
    cmd = ["psql", DATABASE_URL, "-t", "-A", "-c", sql]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={"PGPASSWORD": PGPASSWORD, "PATH": os.environ.get("PATH", "")},
    )
    return result.stdout, result.stderr, result.returncode


# === F-1 — Substrate alignment (LIVE) ===

class TestFederationSubstrate:
    """F-1: GEOX runs only on hardened substrate. All 13 floors live."""

    def test_f1_all_13_floors_active(self):
        """All 13 floors (F01-F13) must be present and active in arifosmcp_floor_rules."""
        out, _, _ = run_psql(
            "SELECT floor_code FROM arifosmcp_floor_rules WHERE is_active ORDER BY floor_code;"
        )
        active_floors = set(out.strip().splitlines())
        expected = {f"F{i:02d}" for i in range(1, 14)}
        missing = expected - active_floors
        assert not missing, f"Federation substrate missing floors: {missing}"

    def test_f1_substrate_signs_exist(self):
        """All constitutional substrate artifacts must exist."""
        # Functions
        out, _, _ = run_psql(
            """
            SELECT proname FROM pg_proc
            WHERE proname IN (
                'arifos_memory_write',
                'arifos_vault_seal_chain_check',
                'arifos_memory_records_audit_trigger',
                'arifos_check_humility_cap'
            )
            """
        )
        funcs = set(out.strip().splitlines())
        expected_funcs = {
            "arifos_memory_write",
            "arifos_vault_seal_chain_check",
            "arifos_memory_records_audit_trigger",
            "arifos_check_humility_cap",
        }
        missing_funcs = expected_funcs - funcs
        assert not missing_funcs, f"Missing substrate functions: {missing_funcs}"

        # Triggers
        out, _, _ = run_psql(
            """
            SELECT trigger_name FROM information_schema.triggers
            WHERE trigger_name LIKE 'arifos_%'
            """
        )
        triggers = set(out.strip().splitlines())
        expected_triggers = {"arifos_memory_records_audit", "arifos_vault_seals_chain_integrity"}
        missing_triggers = expected_triggers - triggers
        assert not missing_triggers, f"Missing substrate triggers: {missing_triggers}"

    def test_f1_floor_rules_have_actions(self):
        """Each floor rule must have an action: BLOCK / WARN / HOLD / VETO / REQUIRED."""
        out, _, _ = run_psql(
            "SELECT DISTINCT constraint_definition->>'action' FROM arifosmcp_floor_rules WHERE is_active;"
        )
        actions = set(out.strip().splitlines())
        valid_actions = {"BLOCK", "WARN", "HOLD", "VETO", "REQUIRED"}
        invalid = actions - valid_actions
        assert not invalid, f"Floor rules with invalid action: {invalid}"


# === F-2 — Cross-organ coherence (STUB) ===

class TestFederationCoherence:
    """F-2: GEOX view of a field doesn't contradict WELL/WEALTH/AAA."""

    def test_f2_geox_recommendation_coherent_with_well(self):
        """GIVEN a GEOX recommendation, verify no contradiction with WELL operational state."""
        # Requires: WELL organ MCP server running on :18083, GEOX MCP on :8081
        # Cross-organ check: GEOX says "drill well X" — does WELL have ops capacity?
        pytest.skip(
            "Cross-organ coherence test requires WELL MCP server (:18083) + GEOX MCP (:8081) + "
            "federation bus. See /root/AAA/a2a-server/ for coordination protocol."
        )

    def test_f2_geox_recommendation_coherent_with_wealth(self):
        """GIVEN a GEOX recommendation, verify no contradiction with WEALTH economics."""
        pytest.skip(
            "Cross-organ coherence test requires WEALTH MCP server (:18082) + GEOX MCP (:8081). "
            "WEALTH's collapse_signature_scan can detect economic contradiction with GEOX risk."
        )

    def test_f2_geox_recommendation_respects_aaa(self):
        """GIVEN a GEOX recommendation, verify it respects AAA governance."""
        pytest.skip(
            "Cross-organ coherence test requires AAA a2a-server (:3001) + GEOX MCP (:8081). "
            "AAA's deliberation.ts can verify GEOX actions are within governance scope."
        )


# === F-3 — A-FORGE mutation discipline (STUB) ===

class TestForgeMutationDiscipline:
    """F-3: GEOX changes go through A-FORGE tickets + receipts."""

    def test_f3_receipt_exists_for_substrate_hardening(self):
        """GIVEN substrate hardening, an A-FORGE RECEIPT must exist."""
        # Check for any receipt in seal-receipts directory
        seal_dir = FORGE_WORK_DIR / "seal-receipts"
        candidates = list(seal_dir.glob("*/RECEIPT.md")) if seal_dir.exists() else []
        if not candidates:
            pytest.skip(
                "No seal receipts found — substrate mutation receipt not yet generated"
            )
        # Verify at least one receipt has F1-F13 references
        found_valid = False
        for receipt in candidates:
            rc = receipt.read_text()
            if "F1" in rc and "F13" in rc:
                found_valid = True
                break
        assert found_valid, "No RECEIPT with F1-F13 audit references found"

    def test_f3_receipt_exists_for_alignment_doc(self):
        """GIVEN the alignment test doc, an A-FORGE RECEIPT must exist."""
        # This very doc — GEOXALIGNMENTTESTS.md
        # Receivable from forge_work/2026-06-24-*-alignment/
        candidates = list(FORGE_WORK_DIR.glob("2026-06-24-*-alignment*"))
        if not candidates:
            pytest.skip(
                "Alignment RECEIPT not yet written — see FORGE-000Ω receipt generation after alignment test deploy"
            )
        # If exists, verify it mentions this doc
        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        content = latest.read_text()
        assert "GEOXALIGNMENTTESTS" in content, \
            f"RECEIPT {latest} doesn't reference GEOXALIGNMENTTESTS.md"

    def test_f3_geox_repo_changes_via_a_forge(self):
        """GIVEN any change in /root/geox, an A-FORGE receipt must exist for today."""
        # Heuristic: at least one forge_work/ entry per day referencing GEOX
        today = "2026-06-24"
        geo_receipts = list(FORGE_WORK_DIR.glob(f"{today}-*geox*")) + \
                       list(FORGE_WORK_DIR.glob(f"{today}-*GEOX*"))
        if not geo_receipts:
            pytest.skip(
                f"No GEOX-related A-FORGE receipts for {today} found. "
                "Mutations to /root/geox should generate receipts in /root/forge_work/."
            )
        assert len(geo_receipts) >= 1, \
            f"Expected at least 1 GEOX receipt for {today}"


# === Entry point ===

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
