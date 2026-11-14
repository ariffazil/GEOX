"""Handler-level negative tests for geox_biostrat_lookup_zone (888 verdict 2026-11-12).

The tool is registered but NOT on the canonical 27-tool wire surface (RT1_GUARD),
so its behavior is verified HERE at the handler boundary with a mocked PBDBClient —
the sanctioned lowest-risk option. Status contract:

    handler behavior       VERIFIED_BY_TEST   (this file)
    canonical wire path    NOT EXPOSED        (product decision, not test-driven)
    live negative call     NOT APPLICABLE     (guard blocks the wire path)

Regression targets:
  1. ZONE_NOT_FOUND payload carries `upstream_warnings` (finding #2 of the PBDB review)
  2. a retired/unknown timescale surfaces the upstream warning text, not silence
  3. ages come from eag/lag (data1.2 returns no ea/la — old code emitted nulls)
  4. unknown scheme -> SCHEME_NOT_IN_PBDB without touching the client
"""

from __future__ import annotations

import pytest
from fastmcp import FastMCP

import geox_mcp.tools.biostrat.taxonomy as taxonomy_mod
from geox_mcp.tools_wiring import register_tools_on


def _lookup_handler():
    mcp = FastMCP("zone-handler-test")
    register_tools_on(mcp)
    component = next(
        value for key, value in mcp._local_provider._components.items() if key.startswith("tool:geox_biostrat_lookup_zone@")
    )
    return component.fn


class _FakePBDBClient:
    """Controllable PBDB double: canned intervals + recorded upstream warnings."""

    intervals: list = []
    warnings: list = []

    def __init__(self, timeout: float = 30.0) -> None:
        self.last_warnings: list[str] = []

    async def intervals_list(self, scale: object = 1, limit: int = 200) -> list:
        self.last_warnings = list(self.warnings)
        return list(self.intervals)

    async def close(self) -> None:
        return None


@pytest.fixture
def zone_handler(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(taxonomy_mod, "PBDBClient", _FakePBDBClient)
    return _lookup_handler()


async def test_zone_not_found_carries_upstream_warnings_field(zone_handler) -> None:
    _FakePBDBClient.intervals = [
        {"nam": "NN21", "eag": 0.29, "lag": 0.0, "oid": "int:1500"},
        {"nam": "NN20", "eag": 0.42, "lag": 0.29, "oid": "int:1501"},
    ]
    _FakePBDBClient.warnings = []
    result = await zone_handler(
        arguments={"zone_code": "XX999-NOSUCH", "scheme": "Martini_1971_NN"},
        session_id="SEAL-zone-test",
        actor_id="test",
    )
    assert result["ok"] is False
    assert result["reason_code"] == "ZONE_NOT_FOUND"
    data = result["data"]
    assert "upstream_warnings" in data, "finding #2: warnings must ship in the payload"
    assert data["upstream_warnings"] == []
    assert data["available_count"] == 2


async def test_retired_timescale_surfaces_upstream_warning(zone_handler) -> None:
    _FakePBDBClient.intervals = []
    _FakePBDBClient.warnings = ["timescale '5' was not found"]
    result = await zone_handler(
        arguments={"zone_code": "NN21", "scheme": "Martini_1971_NN"},
        session_id="SEAL-zone-test",
        actor_id="test",
    )
    assert result["ok"] is False
    assert result["reason_code"] == "ZONE_NOT_FOUND"
    assert result["data"]["upstream_warnings"] == ["timescale '5' was not found"]
    assert result["data"]["available_count"] == 0


async def test_valid_zone_returns_eag_lag_ages(zone_handler) -> None:
    _FakePBDBClient.intervals = [{"nam": "NN21", "eag": 0.29, "lag": 0.0, "oid": "int:1500"}]
    _FakePBDBClient.warnings = []
    result = await zone_handler(
        arguments={"zone_code": "NN21", "scheme": "Martini_1971_NN"},
        session_id="SEAL-zone-test",
        actor_id="test",
    )
    assert result["ok"] is True
    data = result["data"]
    assert data["name"] == "NN21"
    assert data["age_top_ma"] == pytest.approx(0.29)
    assert data["age_bottom_ma"] == pytest.approx(0.0)
    assert data["pbdb_oid"] == "int:1500"


async def test_unknown_scheme_rejected_without_client(zone_handler) -> None:
    _FakePBDBClient.intervals = [{"nam": "SHOULD-NOT-BE-READ", "eag": 1.0, "lag": 2.0}]
    result = await zone_handler(
        arguments={"zone_code": "L1", "scheme": "Lunt_2016_LBF"},
        session_id="SEAL-zone-test",
        actor_id="test",
    )
    assert result["ok"] is False
    assert result["reason_code"] == "SCHEME_NOT_IN_PBDB"
