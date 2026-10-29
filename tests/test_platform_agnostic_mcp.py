"""Tests for GEOX MCP platform, model agnostic and timeless interoperability.

Validates:
1. Initialize without session id returns 200 OK with server capabilities
2. Stateless notifications/initialized with Accept: */* returns 202 Accepted
3. Session-less tools/list returns all 27 canonical tools via stateless bridge
4. Session-less read-tier execution (geox_surface_status) executes cleanly
5. Session-less mutation attempt (geox_well_ingest) fails closed with HOLD
"""

from __future__ import annotations

import json
import pytest
from starlette.testclient import TestClient
from geox_mcp.server import create_app
from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_initialize_without_session(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    resp = client.post("/mcp/", json=payload, headers={"Accept": "application/json"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("jsonrpc") == "2.0"
    assert "result" in data
    assert "capabilities" in data["result"]


def test_notification_with_wildcard_accept(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    }
    resp = client.post(
        "/mcp/",
        json=payload,
        headers={"Accept": "*/*"},
    )
    assert resp.status_code == 202


def test_sessionless_tools_list(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
    }
    resp = client.post(
        "/mcp/",
        json=payload,
        headers={"Accept": "*/*"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "result" in data
    tools = data["result"].get("tools", [])
    assert len(tools) == len(CANONICAL_PUBLIC_TOOLS)
    tool_names = {t["name"] for t in tools}
    assert tool_names == set(CANONICAL_PUBLIC_TOOLS)


def test_sessionless_read_tier_execution(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "geox_surface_status",
            "arguments": {},
        },
    }
    resp = client.post(
        "/mcp/",
        json=payload,
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "result" in data
    assert data["result"].get("isError") in (False, None)


def test_sessionless_mutation_fails_closed(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "geox_well_ingest",
            "arguments": {
                "well_name": "TEST_ANON_WELL",
                "las_content": "# Fake LAS data",
            },
        },
    }
    resp = client.post(
        "/mcp/",
        json=payload,
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "result" in data
    # Must be marked error and carry HOLD verdict
    assert data["result"].get("isError") is True
    content = data["result"].get("content", [])
    assert len(content) > 0
    err_text = content[0].get("text", "")
    assert "HOLD" in err_text or "P0-2" in err_text
