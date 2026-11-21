"""
tests/test_federation_flow.py — Test Suite for Federation, arifFlow, FRAME & CHRON
════════════════════════════════════════════════════════════════════════════════════
Verifies:
  1. Complete 11-organ federation mapping & authority bands.
  2. 17 Earth domains mapping covering all 27 canonical tools.
  3. arifFlow receipt emission (JCS SHA-256 body hash, flock concurrency).
  4. FRAME independent witness protocol & offline graceful degradation.
  5. CHRON bitemporal episode logging.
  6. Server endpoints: /federation, /flow, and enriched /status.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import pytest
from starlette.testclient import TestClient

from geox_mcp.federation_flow import (
    FEDERATION_ORGANS,
    GEOX_DOMAINS,
    emit_flow_receipt,
    get_federation_topology,
    log_chron_event,
    request_frame_witness,
)
from geox_mcp.server import create_app
from geox_mcp.tools_manifest import CANONICAL_TOOLS


def test_federation_organs_topology():
    """Verify all 11 federation organs are registered with valid roles and authority bands."""
    expected_organs = {
        "arifos",
        "arifflow",
        "chron",
        "frame",
        "geox",
        "wealth",
        "well",
        "signal",
        "hermes",
        "aaa",
        "a_forge",
    }
    assert set(FEDERATION_ORGANS.keys()) == expected_organs
    assert len(FEDERATION_ORGANS) == 11

    # Check key port & authority assignments
    assert FEDERATION_ORGANS["arifos"].port == 8088
    assert FEDERATION_ORGANS["arifos"].authority_band == "SOVEREIGN_KERNEL"

    assert FEDERATION_ORGANS["arifflow"].port == 7073
    assert FEDERATION_ORGANS["arifflow"].authority_band == "OPERATIONAL_FLOW"

    assert FEDERATION_ORGANS["frame"].port == 18085
    assert FEDERATION_ORGANS["frame"].authority_band == "INDEPENDENT_WITNESS"

    assert FEDERATION_ORGANS["geox"].port == 8081
    assert FEDERATION_ORGANS["geox"].authority_band == "PHYSICAL_EARTH"

    assert FEDERATION_ORGANS["wealth"].port == 18082
    assert FEDERATION_ORGANS["well"].port == 18083
    assert FEDERATION_ORGANS["signal"].port == 18084
    assert FEDERATION_ORGANS["hermes"].port == 18087
    assert FEDERATION_ORGANS["aaa"].port == 3001
    assert FEDERATION_ORGANS["a_forge"].port == 7071


def test_geox_domain_topology():
    """Verify all 29 canonical tools are covered across the 17 Earth domains."""
    total_domain_tools = sum(len(tools) for tools in GEOX_DOMAINS.values())
    assert total_domain_tools == 29
    assert len(GEOX_DOMAINS) == 17

    all_mapped_tools = {tool for tools in GEOX_DOMAINS.values() for tool in tools}
    canonical_tool_names = set(CANONICAL_TOOLS.keys())
    assert all_mapped_tools == canonical_tool_names


def test_emit_flow_receipt(tmp_path: Path):
    """Verify receipt generation, canonical JCS body hashing, and safe file write."""
    fake_receipts_path = tmp_path / "receipts.jsonl"

    with patch("geox_mcp.federation_flow.ARIFLOW_RECEIPTS_PATH", fake_receipts_path):
        receipt = emit_flow_receipt(
            tool_name="geox_observe",
            event_type="OBSERVE_COMPLETE",
            status="SUCCESS",
            step_type="Observe",
            duration_ms=45.2,
            session_id="test-session-123",
            actor_id="geox:test_actor",
            extra={"target": "KB-KL2_synthetic"},
        )

    assert receipt["actor_id"] == "geox:test_actor"
    assert receipt["session_id"] == "test-session-123"
    assert receipt["step_type"] == "Observe"
    assert receipt["risk_class"] == "T0Observe"
    assert receipt["routed_organ"] == "GEOX"
    assert len(receipt["jcs_body_hash"]) == 64  # SHA-256
    assert receipt["payload"]["tool"] == "geox_observe"
    assert receipt["payload"]["target"] == "KB-KL2_synthetic"

    # Verify file was written
    assert fake_receipts_path.exists()
    with open(fake_receipts_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        written_data = json.loads(lines[0])
        assert written_data["receipt_id"] == receipt["receipt_id"]
        assert written_data["jcs_body_hash"] == receipt["jcs_body_hash"]


def test_request_frame_witness(tmp_path: Path):
    """Verify FRAME independent witness request handles offline HTTP via fallback queue."""
    fake_frame_req_path = tmp_path / "frame_requests.jsonl"

    with patch("geox_mcp.federation_flow.CHRON_FRAME_REQUESTS_PATH", fake_frame_req_path), \
         patch("geox_mcp.federation_flow.FRAME_URL", "http://127.0.0.1:9999"):  # offline port
        res = request_frame_witness(
            claim_id="claim-sb-001",
            claim="Fault F-1 dips 65 degrees south-west in Upper Miocene sandstone",
            evidence=["seismic_inline_245", "synthetic_well_log_1"],
            confidence=0.88,
        )

    assert res["witness_verdict"] == "RECORDED_PENDING_FRAME"
    assert res["witness_organ"] == "frame"
    assert fake_frame_req_path.exists()

    with open(fake_frame_req_path, "r", encoding="utf-8") as f:
        record = json.loads(f.readline())
        assert record["claim_id"] == "claim-sb-001"
        assert record["claimed_confidence"] == 0.88


def test_log_chron_event(tmp_path: Path):
    """Verify CHRON bitemporal episode registration."""
    fake_chron_path = tmp_path / "episodes.jsonl"

    with patch("geox_mcp.federation_flow.CHRON_EPISODES_PATH", fake_chron_path):
        episode = log_chron_event(
            event_type="STRUCTURAL_CANDIDATE_EMITTED",
            subject="fault:F-01",
            epistemic_status="DERIVED",
            payload={"dip": 65.0, "strike": 140.0},
            valid_from="2026-11-03T00:00:00Z",
        )

    assert episode["organ"] == "geox"
    assert episode["event_type"] == "STRUCTURAL_CANDIDATE_EMITTED"
    assert episode["epistemic_status"] == "DERIVED"
    assert episode["valid_from"] == "2026-11-03T00:00:00Z"
    assert fake_chron_path.exists()

    with open(fake_chron_path, "r", encoding="utf-8") as f:
        record = json.loads(f.readline())
        assert record["episode_id"] == episode["episode_id"]


def test_get_federation_topology():
    """Verify export of complete federation topology dict."""
    topo = get_federation_topology()
    assert topo["organ"] == "GEOX"
    assert topo["total_organs"] == 11
    assert "arifos" in topo["organs"]
    assert "arifflow" in topo["organs"]
    assert "frame" in topo["organs"]
    assert topo["geox_surface"]["canonical_tools_count"] == 29
    assert topo["geox_surface"]["total_domains"] == 17
    assert topo["geox_surface"]["p0_promotion_gate"] == "HOLD"


def test_server_endpoints():
    """Verify /federation, /flow, and enriched /status on live Starlette app."""
    app = create_app()
    client = TestClient(app)

    # 1. GET /federation
    res_fed = client.get("/federation")
    assert res_fed.status_code == 200
    fed_data = res_fed.json()
    assert fed_data["organ"] == "GEOX"
    assert fed_data["total_organs"] == 11
    assert len(fed_data["organs"]) == 11

    # 2. GET /flow
    res_flow = client.get("/flow")
    assert res_flow.status_code == 200
    flow_data = res_flow.json()
    assert flow_data["organ"] == "GEOX"
    assert "flow_engine" in flow_data
    assert "frame_witness" in flow_data
    assert "chron_store" in flow_data

    # 3. GET /status (enriched with federation)
    res_status = client.get("/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert "federation" in status_data
    assert status_data["federation"]["total_organs"] == 11
    assert status_data["canonical_tools"] == 29
