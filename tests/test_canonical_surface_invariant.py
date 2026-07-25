"""P0-1 hardening 2026-07-25 · FI-008 — Live canonical surface invariant.

The audit identified that the live MCP connector and other surfaces may
diverge from CANONICAL_PUBLIC_TOOLS. This test asserts:

  1. ``canonical_surface_gate.filter_tools_list`` strips drift and preserves
     canonical tools. Drift is observable, not fatal.
  2. The drift report function correctly classifies names into
     {canonical ∩ live, canonical − live, live − canonical}.
  3. The HTTP ``/drift`` endpoint contract returns the drift report
     (verified via in-process invocation of ``drift_handler``).
  4. ``surface_invariant_violated`` returns False when the live surface
     exactly equals the canonical public surface.

These tests run without a live server — they validate the gate module
directly. The complementary live re-probe lives in
``scripts/probe_canonical_surface.py``.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from geox_mcp.canonical_surface_gate import (
    canonical_set,
    drift_report,
    filter_tools_list,
    is_canonical,
    surface_invariant_violated,
)
from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def canonical_names() -> set[str]:
    return set(CANONICAL_PUBLIC_TOOLS)


@pytest.fixture
def live_with_drift(canonical_names: set[str]) -> list[dict[str, Any]]:
    """Live tools/list with 3 drift entries (audit-named legacy aliases)."""
    return [
        {"name": "geox_well_ingest", "description": "ok"},
        {"name": "geox_las_inspect", "description": "drift"},  # audit-named
        {"name": "geox_data_ingest_bundle", "description": "drift"},  # audit-named
        {"name": "geox_blockspace_resolution_tool", "description": "drift"},  # audit-named
        {"name": "geox_workspace", "description": "ok"},
    ]


# ── 1. canonical_set ───────────────────────────────────────────────────────


def test_canonical_set_matches_registry(canonical_names: set[str]) -> None:
    assert canonical_set() == frozenset(canonical_names)


def test_canonical_set_includes_well_known_tools() -> None:
    """Audit-critical tools must be in canonical public."""
    required = {
        "geox_well_ingest",
        "geox_well_qc",
        "geox_seismic_compute",
        "geox_surface_status",
        "geox_workspace",
        "geox_claim",
        "geox_prospect",
    }
    missing = required - canonical_set()
    assert not missing, f"canonical surface missing audit-critical tools: {missing}"


# ── 2. is_canonical ────────────────────────────────────────────────────────


def test_is_canonical_returns_true_for_known_tools() -> None:
    assert is_canonical("geox_well_ingest") is True


def test_is_canonical_returns_false_for_drift_names() -> None:
    """The 7 audit-named legacy names must NOT be canonical public."""
    audit_drift = [
        "geox_las_inspect",
        "geox_data_ingest_bundle",
        "geox_data_qc_bundle",
        "geox_seismic_segy_inspect",
        "geox_coord_transform_tool",
        "geox_blockspace_resolution_tool",
        "geox_attribute_registry_list_tool",
    ]
    for name in audit_drift:
        assert is_canonical(name) is False, (
            f"audit drift name {name!r} leaked into canonical public surface"
        )


def test_is_canonical_returns_false_for_unknown() -> None:
    assert is_canonical("not_a_real_tool") is False


# ── 3. filter_tools_list ───────────────────────────────────────────────────


def test_filter_strips_drift(live_with_drift: list[dict[str, Any]]) -> None:
    """filter_tools_list removes non-canonical entries from the live list."""
    filtered = filter_tools_list(live_with_drift, log_drift=False)
    kept_names = {t["name"] for t in filtered}
    assert kept_names == {"geox_well_ingest", "geox_workspace"}
    # No drift entries survive.
    for entry in filtered:
        assert is_canonical(entry["name"]), f"{entry['name']!r} survived the filter"


def test_filter_preserves_empty_input() -> None:
    assert filter_tools_list([], log_drift=False) == []


def test_filter_preserves_pure_canonical(canonical_names: set[str]) -> None:
    """If every live tool is canonical, the filter is a no-op."""
    live = [{"name": n} for n in sorted(canonical_names)]
    filtered = filter_tools_list(live, log_drift=False)
    assert {t["name"] for t in filtered} == canonical_names
    assert len(filtered) == len(live)


def test_filter_tolerates_missing_name_field() -> None:
    """Entries without a `name` field are dropped (defensive)."""
    live: list[dict[str, Any]] = [
        {"name": "geox_well_ingest"},
        {"description": "no name"},
        {},
        {"name": None},
    ]
    filtered = filter_tools_list(live, log_drift=False)
    assert len(filtered) == 1
    assert filtered[0]["name"] == "geox_well_ingest"


# ── 4. drift_report ────────────────────────────────────────────────────────


def test_drift_report_clean_when_equal(canonical_names: set[str]) -> None:
    """When live exactly equals canonical, report is ok=True."""
    report = drift_report(sorted(canonical_names))
    assert report["canonical_count"] == len(canonical_names)
    assert report["live_count"] == len(canonical_names)
    assert report["drift_count"] == 0
    assert report["gap_count"] == 0
    assert report["ok"] is True
    assert report["drifted"] == []
    assert report["missing"] == []


def test_drift_report_detects_live_extras(
    live_with_drift: list[dict[str, Any]],
) -> None:
    """Drift = names in live but NOT in canonical."""
    live_names = [t["name"] for t in live_with_drift]
    report = drift_report(live_names)
    assert report["drift_count"] == 3  # the 3 audit-named legacy entries
    assert set(report["drifted"]) == {
        "geox_las_inspect",
        "geox_data_ingest_bundle",
        "geox_blockspace_resolution_tool",
    }


def test_drift_report_detects_canonical_gaps(canonical_names: set[str]) -> None:
    """Gap = names in canonical but NOT in live."""
    sparse = ["geox_well_ingest", "geox_workspace"]
    report = drift_report(sparse)
    assert report["gap_count"] == len(canonical_names) - len(sparse)
    assert "geox_well_ingest" not in report["missing"]
    assert "geox_workspace" not in report["missing"]
    assert report["ok"] is False


# ── 5. surface_invariant_violated ─────────────────────────────────────────


def test_invariant_violated_on_drift() -> None:
    live = ["geox_well_ingest", "geox_las_inspect"]
    assert surface_invariant_violated(live) is True


def test_invariant_violated_on_gap(canonical_names: set[str]) -> None:
    """Sparse live list is also a violation (canonical must be fully exposed)."""
    sparse = ["geox_well_ingest"]
    assert surface_invariant_violated(sparse) is True


def test_invariant_holds_when_equal(canonical_names: set[str]) -> None:
    assert surface_invariant_violated(sorted(canonical_names)) is False


# ── 6. /drift endpoint contract (in-process) ──────────────────────────────


def test_drift_endpoint_returns_drift_report(monkeypatch) -> None:
    """``drift_handler`` must return a JSONResponse with the report fields."""
    from geox_mcp import server

    # Pre-populate the middleware's last report (otherwise live_count=0).
    sample_report = drift_report(sorted(CANONICAL_PUBLIC_TOOLS))
    fake_mw = type("MW", (), {"_LAST_DRIFT_REPORT": sample_report})()
    monkeypatch.setattr(server, "_geox_governance_middleware", fake_mw)

    response = asyncio.run(server.drift_handler(None))
    assert response.status_code == 200, "clean surface must return 200"
    body = response.body.decode()
    assert "ok=true" in body or '"ok": true' in body or '"ok":true' in body
    assert "canonical_count" in body
    assert "drift_count" in body


def test_drift_endpoint_returns_409_on_drift(monkeypatch) -> None:
    """When drift detected, endpoint returns 409 Conflict (audit-reproducible)."""
    from geox_mcp import server

    bad_report = drift_report(["geox_well_ingest", "geox_las_inspect"])
    fake_mw = type("MW", (), {"_LAST_DRIFT_REPORT": bad_report})()
    monkeypatch.setattr(server, "_geox_governance_middleware", fake_mw)

    response = asyncio.run(server.drift_handler(None))
    assert response.status_code == 409, (
        f"drift must return 409, got {response.status_code}"
    )
    body = response.body.decode()
    assert "geox_las_inspect" in body


# ── 7. Live surface parity sanity check (skipped without server) ─────────


import socket
import urllib.error
import urllib.request


def _geox_server_reachable(host: str = "127.0.0.1", port: int = 8081) -> bool:
    """Return True iff the GEOX MCP server is reachable on host:port."""
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


@pytest.mark.skipif(
    not _geox_server_reachable(),
    reason="GEOX MCP server not reachable on 127.0.0.1:8081 (skip live parity probe)",
)
def test_live_mcp_tools_list_matches_canonical() -> None:
    """Probe live :8081 /mcp/ tools/list and assert equality with canonical.

    Skipped automatically when the GEOX MCP server is not running locally.
    CI runs without a server — this assertion fires when a developer (or a
    staging environment) runs ``pytest tests/`` against a live GEOX.
    """
    import json

    # 1. initialize — get a session id from the Mcp-Session-Id response header.
    req = urllib.request.Request(
        "http://127.0.0.1:8081/mcp/",
        data=json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        ).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        sid = r.headers.get("mcp-session-id", "")
    assert sid, "no session id returned from /mcp/ initialize"

    # 2. notifications/initialized
    req = urllib.request.Request(
        "http://127.0.0.1:8081/mcp/",
        data=json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}
        ).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": sid,
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=5).read()

    # 3. tools/list
    req = urllib.request.Request(
        "http://127.0.0.1:8081/mcp/",
        data=json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }
        ).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": sid,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        payload = json.loads(r.read().decode())

    live_names = {t["name"] for t in payload.get("result", {}).get("tools", [])}
    canonical = set(CANONICAL_PUBLIC_TOOLS)
    drift = sorted(live_names - canonical)
    gap = sorted(canonical - live_names)
    assert live_names == canonical, (
        f"live MCP tools/list diverges from canonical: "
        f"drift={drift}, gap={gap}"
    )
