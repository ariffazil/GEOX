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
