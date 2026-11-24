"""
GEOX Alignment Tests — GEOX Organ Layer (G-1 to G-5)

These tests verify GEOX-specific invariants. They require the GEOX MCP
server to be running on port 8081 (systemd: geox-mcp.service).

When GEOX is offline, tests are skipped with clear documentation. When
GEOX is online, they exercise:
  - Physics sanity (G-1)
  - Epistemic honesty (G-2)
  - Provenance completeness (G-3)
  - Cognitive reversibility (G-4)
  - Mandate boundaries (G-5)

Reference: /root/geox/docs/GEOXALIGNMENTTESTS.md §2
Sovereign: arif (F13). Sealed: 2026-06-24.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from typing import Any

import pytest

GEOX_MCP_HOST = os.environ.get("GEOX_MCP_HOST", "127.0.0.1")
GEOX_MCP_PORT = int(os.environ.get("GEOX_MCP_PORT", "8081"))


def geox_is_alive() -> bool:
    """Check if GEOX MCP server is reachable on :8081."""
    try:
        with socket.create_connection((GEOX_MCP_HOST, GEOX_MCP_PORT), timeout=2):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


# Skip all tests in this module if GEOX MCP is not running
pytestmark = pytest.mark.skipif(
    not geox_is_alive(),
    reason=f"GEOX MCP server not reachable at {GEOX_MCP_HOST}:{GEOX_MCP_PORT}. "
           "Start with: systemctl start geox-mcp",
)


# === G-1 — Physics sanity ===
#
# MOVED 2026-11-24 (FI-003). The three G-1 tests that lived here wrapped
# ``call_geox_tool`` — a stub raising NotImplementedError unconditionally —
# inside ``pytest.raises((ValueError, RuntimeError, NotImplementedError))``.
# Two of them passed green without executing any GEOX code. They now live in
# tests/test_g1_physics_refusal.py, call the tools in-process, and assert the
# returned refusal state ({"status": "INVALID"} / envelope ERROR+HOLD+REJECTED).
#
# See TEST_TRUTH_AUDIT.md for the rest of this module's skip inventory.



# === G-2 — Epistemic honesty ===

class TestG2EpistemicHonesty:
    """G-2: Every interpretation is correctly tagged."""

    @pytest.fixture
    def q15_well_data(self) -> dict[str, Any]:
        """Real Q15 well 15/9-19 data from Danish North Sea."""
        return {
            "well_name": "15/9-19",
            "field": "Q15 North Sea Danish",
            "depth_range_m": [3615.434, 4636.514],
            "curve_count": 23,
        }

    def test_g2_1_log_observations_tagged_episodic(self, q15_well_data):
        """Raw logs → type='episodic' (raw measurement, not interpretation)."""
        # Ingest via OSDU exchange layer should produce type='episodic' or 'semantic'
        # but with low confidence and epistemic_level='OBS'
        # (Stub: this is the contract, tested via the open-source ingest script)
        pytest.skip("Covered by ingest_open_source_data.py — see /root/forge_work/2026-06-24-rls-hardening/tests/")

    def test_g2_1_derived_curves_tagged_semantic(self, q15_well_data):
        """Derived curves → type='semantic' (derived, algorithmically traceable)."""
        pytest.skip(
            "Invariant now covered locally by tests/test_curve_origin_l5.py "
            "(L5/L10 origin separation, added 2026-11-24)"
        )

    def test_g2_1_sealed_actions_tagged_governance(self):
        """Sealed actions (judgments) → type='governance' with confidence=1.0."""
        # The substrate enforces this via the F10 ONTOLOGY CHECK.
        # Test: can a sealed action be re-tagged as non-governance?
        pytest.skip("Tested by substrate test T10.1 — see test_align_substrate.py")


# === G-3 — Provenance replay ===

class TestG3ProvenanceReplay:
    """G-3: Every GEOX verdict can be traced back to its evidence chain."""

    def test_g3_replay_from_audit_log(self):
        """Given a memory_id, the audit log row contains signature + actor + organ + floors."""
        # This is partially tested by substrate tests (T11.1).
        # The GEOX-specific part: provenance is exposed via the geox_* MCP tools.
        pytest.skip("MCP tool wiring pending — covered conceptually in substrate tests")


# === G-4 — Cognitive reversibility ===

class TestG4CognitiveReversibility:
    """G-4: GEOX beliefs are temporally reconstructible."""

    def test_g4_supersession_chain_intact(self):
        """Supersession chain (supersedes/superseded_by FK) preserves history."""
        # Substrate invariant: this is enforced by the schema.
        # Test: are there records in arifosmcp_memory_records with supersedes set?
        # (Stub — needs ad-hoc query against Supabase)
        pytest.skip("Live substrate query — see /root/forge_work/2026-06-24-rls-hardening/tests/")


# === G-5 — Mandate boundaries ===

class TestG5MandateBoundaries:
    """G-5: GEOX does not mutate WELL/WEALTH/AAA state directly."""

    def test_g5_geox_does_not_write_to_well(self):
        """GEOX has no write path to WELL organ tables."""
        # Architectural invariant: GEOX writes only to arifosmcp_* tables
        # and emits sealed artifacts via the OSDU exchange layer.
        # WELL writes happen via WELL organ MCP, not GEOX.
        # Test: scan GEOX MCP server code for table references to well.*
        # Stub: this is enforced by code review + arifOS governance.
        pytest.skip("Code-review invariant — not testable as a unit test")

    def test_g5_geox_does_not_write_to_wealth(self):
        """GEOX has no write path to WEALTH organ tables."""
        pytest.skip("Code-review invariant — not testable as a unit test")


# === Entry point ===

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
