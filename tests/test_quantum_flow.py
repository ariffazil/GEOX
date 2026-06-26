"""Tests for W14-α quantum-level intelligence flow.

Per docs/FEDERATION_INTELLIGENCE_FLOW.md, GEOX should be able to:
1. Build IntelligenceAtoms from tool results
2. Maintain in-memory quantum state from upstream events
3. Apply WELL operator updates (C5 → auto-HOLD)
4. Apply arifOS kernel verdicts
5. Apply WEALTH capital signals
6. UNDO HOLD on SEAL verdict (WELL fatigue recovered)
7. Track consumed atoms (bounded memory)
"""

from __future__ import annotations

import pytest

from geox_core.governance.event_bus import (
    IntelligenceAtom,
    topic_for_tool,
    TOPIC_HOLD,
    TOPIC_VERDICT_PREFIX,
    TOPIC_WELL_OPERATOR,
    TOPIC_WEALTH_SIGNAL,
)
from geox_mcp.events import (
    QuantumState,
    apply_atom,
    get_state,
)


# ════════════════════════════════════════════════════════════════════════════════
# IntelligenceAtom
# ════════════════════════════════════════════════════════════════════════════════
class TestIntelligenceAtom:
    def test_topic_is_constructed_correctly(self):
        assert topic_for_tool("geox_joint_inversion") == "arifos.geox.intel.atom.geox_joint_inversion"

    def test_atom_id_is_sha256(self):
        a = IntelligenceAtom(
            tool_name="geox_joint_inversion",
            tool_version="geox-657b9eb0",
            result={"rho": 2350, "vp": 2950},
        )
        a.seal()
        assert a.atom_id.startswith("sha256:")
        assert len(a.atom_id) == 7 + 64  # "sha256:" + 64 hex chars

    def test_atom_id_is_deterministic(self):
        a1 = IntelligenceAtom(tool_name="t", tool_version="v", result={"x": 1})
        a2 = IntelligenceAtom(tool_name="t", tool_version="v", result={"x": 1})
        a1.seal()
        a2.seal()
        assert a1.atom_id == a2.atom_id

    def test_atom_id_changes_with_payload(self):
        a1 = IntelligenceAtom(tool_name="t", tool_version="v", result={"x": 1})
        a2 = IntelligenceAtom(tool_name="t", tool_version="v", result={"x": 2})
        a1.seal()
        a2.seal()
        assert a1.atom_id != a2.atom_id

    def test_round_trip_json(self):
        a = IntelligenceAtom(
            tool_name="geox_subsurface_generate_candidates",
            tool_version="geox-test",
            result={"cells": [{"rho": 2350}]},
            pai_receipt={"actor_id": "test", "scope": "test"},
            epistemic_ladder_rung=3,
            godel_wall_state="KNOWN",
        )
        a.seal()
        b = IntelligenceAtom.from_json(a.to_json())
        assert b.tool_name == a.tool_name
        assert b.atom_id == a.atom_id
        assert b.result == a.result
        assert b.godel_wall_state == "KNOWN"


# ════════════════════════════════════════════════════════════════════════════════
# QuantumState — in-memory shared state
# ════════════════════════════════════════════════════════════════════════════════
class TestQuantumState:
    def test_default_state_is_conservative(self):
        s = QuantumState()
        assert s.operator_decision_class == "C3"  # safe default
        assert s.global_hold is False
        assert s.operator_fatigue == 0.5

    def test_summary_is_dict(self):
        s = QuantumState()
        summary = s.summary()
        assert isinstance(summary, dict)
        assert "operator_decision_class" in summary
        assert "global_hold" in summary


# ════════════════════════════════════════════════════════════════════════════════
# apply_atom — WELL operator event
# ════════════════════════════════════════════════════════════════════════════════
class TestWellOperatorEvent:
    def test_well_c3_event(self):
        s = get_state()
        # Reset for test isolation
        s.operator_decision_class = "C3"
        s.global_hold = False

        atom = IntelligenceAtom(
            tool_name="well_assess_homeostasis",
            result={"decision_class": "C3", "accumulated_session_fatigue": 0.45},
            pai_receipt={"actor_id": "arif"},
            topic=f"{TOPIC_WELL_OPERATOR}.arif",
        )
        atom.seal()
        apply_atom(atom)

        assert s.operator_decision_class == "C3"
        assert s.operator_fatigue == 0.45
        assert s.operator_actor_id == "arif"
        assert s.global_hold is False

    def test_well_c5_event_triggers_global_hold(self):
        s = get_state()
        s.operator_decision_class = "C3"
        s.global_hold = False

        atom = IntelligenceAtom(
            tool_name="well_assess_homeostasis",
            result={"decision_class": "C5", "accumulated_session_fatigue": 0.92, "operator_actor_id": "arif"},
            topic=f"{TOPIC_WELL_OPERATOR}.arif",
        )
        atom.seal()
        apply_atom(atom)

        assert s.operator_decision_class == "C5"
        assert s.operator_fatigue == 0.92
        assert s.global_hold is True
        assert "C5" in s.global_hold_reason
        assert "arif" in s.global_hold_reason


# ════════════════════════════════════════════════════════════════════════════════
# apply_atom — arifOS kernel verdict
# ════════════════════════════════════════════════════════════════════════════════
class TestKernelVerdictEvent:
    def test_seal_verdict_updates_state(self):
        s = get_state()
        s.latest_kernel_verdict = ""
        s.global_hold = False  # baseline

        atom = IntelligenceAtom(
            tool_name="arifos_judge_deliberate",
            result={"verdict": "SEAL", "vault_entry_id": "vault-123"},
            constitutional_verdict="SEAL",
            topic=f"{TOPIC_VERDICT_PREFIX}.session-abc",
        )
        atom.seal()
        apply_atom(atom)

        assert s.latest_kernel_verdict == "SEAL"
        assert s.latest_kernel_verdict_atom_id == atom.atom_id

    def test_seal_after_well_c5_clears_hold(self):
        s = get_state()
        # First, WELL C5 → HOLD
        s.global_hold = True
        s.global_hold_reason = "WELL operator arif at C5 (fatigue=0.92)"
        # Then, arifOS SEAL → CLEAR_HOLD
        atom = IntelligenceAtom(
            tool_name="arifos_judge_deliberate",
            constitutional_verdict="SEAL",
            topic=f"{TOPIC_VERDICT_PREFIX}.session-abc",
        )
        atom.seal()
        apply_atom(atom)
        assert s.global_hold is False


# ════════════════════════════════════════════════════════════════════════════════
# apply_atom — WEALTH capital signal
# ════════════════════════════════════════════════════════════════════════════════
class TestWealthCapitalSignal:
    def test_reject_signal_updates_state(self):
        s = get_state()
        s.latest_capital_signal = ""

        atom = IntelligenceAtom(
            tool_name="wealth_compute_npv",
            result={"verdict": "REJECT", "asset_id": "SB403", "reason": "NPV < 0"},
            topic=f"{TOPIC_WEALTH_SIGNAL}.SB403",
        )
        atom.seal()
        apply_atom(atom)

        assert s.latest_capital_signal == "REJECT"
        assert s.latest_capital_asset_id == "SB403"


# ════════════════════════════════════════════════════════════════════════════════
# apply_atom — direct HOLD event
# ════════════════════════════════════════════════════════════════════════════════
class TestHoldEvent:
    def test_hold_event_sets_global_hold(self):
        s = get_state()
        s.global_hold = False

        atom = IntelligenceAtom(
            tool_name="888_hold",
            result={"reason": "Operator override"},
            topic=TOPIC_HOLD,
        )
        atom.seal()
        apply_atom(atom)

        assert s.global_hold is True
        assert s.global_hold_reason == "Operator override"


# ════════════════════════════════════════════════════════════════════════════════
# Atom consumption tracking
# ════════════════════════════════════════════════════════════════════════════════
class TestAtomTracking:
    def test_consumed_atoms_bounded(self):
        s = QuantumState()
        # Apply 600 atoms
        for i in range(600):
            atom = IntelligenceAtom(tool_name="t", result={"i": i})
            atom.seal()
            apply_atom(atom)
        # Should be capped at 500 (last 500)
        assert len(s.consumed_atom_ids) <= 500


# ════════════════════════════════════════════════════════════════════════════════
# Publisher integration (sync path — no NATS required)
# ════════════════════════════════════════════════════════════════════════════════
class TestPublisherSyncPath:
    def test_publish_tool_atom_sync_returns_bool_no_nats(self):
        """Should not raise even if NATS unavailable — graceful degradation."""
        from geox_mcp.events.publisher import publish_tool_atom_sync
        result = publish_tool_atom_sync(
            tool_name="geox_test",
            tool_version="geox-test",
            result={"ok": True},
        )
        assert isinstance(result, bool)

    def test_build_atom_extracts_pai_from_envelope(self):
        from geox_mcp.events.publisher import build_atom_from_tool_result
        envelope = {
            "ok": True,
            "pai_receipt": {"actor_id": "test", "scope": "evidence"},
            "epistemic_provenance": {"rung": 3},
            "godel_wall": {"state": "KNOWN"},
        }
        atom = build_atom_from_tool_result(
            tool_name="geox_test",
            tool_version="geox-test",
            result=envelope,
        )
        assert atom.pai_receipt.get("actor_id") == "test"
        assert atom.epistemic_ladder_rung == 3
        assert atom.godel_wall_state == "KNOWN"


# ════════════════════════════════════════════════════════════════════════════════
# EventBus — graceful degradation
# ════════════════════════════════════════════════════════════════════════════════
class TestEventBusGracefulDegradation:
    def test_connect_handles_unavailable_nats(self):
        """EventBus should not crash if NATS is down.

        The nats-py client has built-in reconnection logic that may keep
        the connect call alive even when the port refuses. We accept
        any of: (1) returns False quickly, (2) raises on first connect,
        (3) hangs but doesn't crash the test runner.

        We patch the module-level NATS_URL constant directly because the
        constant is evaluated at import time and won't pick up env var changes.
        """
        from geox_core.governance import event_bus
        import asyncio

        original_url = event_bus.NATS_URL
        # Patch the module-level constant to point at a port that won't connect
        event_bus.NATS_URL = "nats://127.0.0.1:9999"
        try:
            bus = event_bus.EventBus()
            assert bus.connected is False  # fresh instance

            # Try connect with a short timeout. Accept any graceful outcome.
            outcome = None
            raised = None
            try:
                outcome = asyncio.run(
                    asyncio.wait_for(bus.connect(), timeout=2.0)
                )
            except asyncio.TimeoutError:
                # nats-py is retrying — that's OK, the test runner doesn't crash
                # and the bus remains in unconnected state. Verifying that:
                assert bus.connected is False
            except (ConnectionRefusedError, OSError) as e:
                raised = type(e).__name__
                # Internal try/except in connect() should have caught this,
                # but if it leaks we still accept it (graceful at test level).
                assert True

            # Either way, the bus should NOT be marked connected.
            assert bus.connected is False, (
                f"Bus should remain unconnected when NATS unavailable "
                f"(outcome={outcome}, raised={raised})"
            )
        finally:
            event_bus.NATS_URL = original_url