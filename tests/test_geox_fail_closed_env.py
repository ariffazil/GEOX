"""
Tests for fail-closed behavior when GEOX runtime storage environment variables are unset.
Verifies removal of hardcoded /root/geox fallbacks in:
- geox_mcp.floor_enforcement (GEOX_AUDIT_LOG)
- geox_mcp.resource_registry (GEOX_RESOURCE_REGISTRY_DB)
- geox_mcp.services.auto_mint (GEOX_EARTH_MEMORY_DB)
"""

import pytest
from pathlib import Path


def test_audit_log_fail_closed_when_env_unset(monkeypatch):
    from geox_mcp.floor_enforcement import AuditLog

    monkeypatch.delenv("GEOX_AUDIT_LOG", raising=False)
    with pytest.raises(RuntimeError, match="GEOX_AUDIT_LOG environment variable is unset"):
        AuditLog()


def test_post_call_holds_when_audit_log_unset(monkeypatch):
    """A missing GEOX_AUDIT_LOG returns HOLD. AuditLog() itself still raises."""
    import geox_mcp.floor_enforcement as fe

    monkeypatch.delenv("GEOX_AUDIT_LOG", raising=False)
    fe._audit_log = None
    pre = fe.PreCallVerdict(outcome="PROCEED", call_hash="sha256:abc")
    result = {"status": "OK", "ok": True, "n_sources": 0}

    verdict = fe.enforce_floor_post_call(
        tool_name="geox_list_registered_sources",
        result=result,
        kwargs={},
        risk_tier="readonly",
        pre_call=pre,
        duration_ms=1.0,
    )

    assert verdict.audit_recorded is False
    assert verdict.held_result is not None
    assert result["error_code"] == "AUDIT_LOG_UNSET"
    assert result["governance_status"] == "HOLD"
    assert result["status"] == "HOLD"
    assert result["ok"] is False
    assert result["audit_recorded"] is False
    assert "not recorded" in result["reason"]
    assert "F11" in verdict.audit.floor_gates_failed
    assert verdict.audit.outcome == "HOLD"
    assert fe._audit_log is None
    with pytest.raises(RuntimeError, match="GEOX_AUDIT_LOG environment variable is unset"):
        fe.AuditLog()


def test_post_call_records_when_audit_log_set(monkeypatch, tmp_path):
    import geox_mcp.floor_enforcement as fe

    target = tmp_path / "floor-audit.jsonl"
    monkeypatch.setenv("GEOX_AUDIT_LOG", str(target))
    fe._audit_log = None
    pre = fe.PreCallVerdict(outcome="PROCEED", call_hash="sha256:def")
    result = {"status": "OK", "ok": True}

    verdict = fe.enforce_floor_post_call(
        tool_name="geox_list_registered_sources",
        result=result,
        kwargs={},
        risk_tier="readonly",
        pre_call=pre,
        duration_ms=1.0,
    )

    assert verdict.audit_recorded is True
    assert verdict.held_result is None
    assert result == {"status": "OK", "ok": True}
    assert target.exists()
    assert "geox_list_registered_sources" in target.read_text()
    fe._audit_log = None


def test_audit_log_passes_with_env_set(monkeypatch, tmp_path):
    from geox_mcp.floor_enforcement import AuditLog, AuditRecord

    target = tmp_path / "custom_audit.jsonl"
    monkeypatch.setenv("GEOX_AUDIT_LOG", str(target))
    log = AuditLog()
    assert log.path == target

    # Verify write succeeds
    log.append(
        AuditRecord(
            ts="2026-11-03T00:00:00+00:00",
            tool_name="test_tool",
            risk_tier="readonly",
            actor_id="test",
            session_id="s1",
            trace_id="t1",
            floor_gates_passed=[],
            floor_gates_failed=[],
            epistemic_tag="CLAIM",
            evidence_quality=0.9,
            duration_ms=1.0,
            call_hash="sha256:123",
            outcome="PROCEED",
        )
    )
    assert target.exists()


def test_resource_registry_fail_closed_when_env_unset(monkeypatch):
    from geox_mcp import resource_registry

    monkeypatch.delenv("GEOX_RESOURCE_REGISTRY_DB", raising=False)
    with pytest.raises(RuntimeError, match="GEOX_RESOURCE_REGISTRY_DB environment variable is unset"):
        resource_registry._get_connection()


def test_resource_registry_passes_with_env_set(monkeypatch, tmp_path):
    from geox_mcp import resource_registry

    db_file = tmp_path / "resources.db"
    monkeypatch.setenv("GEOX_RESOURCE_REGISTRY_DB", str(db_file))
    resource_registry._init_db()
    assert db_file.exists()


def test_auto_mint_fail_closed_when_env_unset(monkeypatch):
    from geox_mcp.services import auto_mint

    monkeypatch.delenv("GEOX_EARTH_MEMORY_DB", raising=False)
    with pytest.raises(RuntimeError, match="GEOX_EARTH_MEMORY_DB environment variable is unset"):
        auto_mint._db_path()


def test_auto_mint_passes_with_env_set(monkeypatch, tmp_path):
    from geox_mcp.services import auto_mint

    mem_file = tmp_path / "memory.db"
    monkeypatch.setenv("GEOX_EARTH_MEMORY_DB", str(mem_file))
    assert auto_mint._db_path() == mem_file
