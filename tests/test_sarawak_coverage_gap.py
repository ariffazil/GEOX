"""Regression tests for the Sarawak coverage fix and honest COVERAGE_GAP responses.

Field defect 2026-10-23: a working Sarawak geologist asked GEOX about "Sarawak Basin" and
"North Luconia" and received a bare {"error": "Basin data not found"}. Root cause was not missing
data alone — tools/basin.py already resolved aliases and degraded to a Macrostrat-limited profile,
but the unified geox_basin tool routes through evidence_reason._reason_basin_baseline, which
hard-failed. Two code paths, one forgiving, one not.

These tests pin the corrected behaviour:
  1. Sarawak provinces resolve to real profiles.
  2. An unregistered basin returns a structured COVERAGE_GAP, not a bare error.
  3. The analogue offered is geographically justified, or none is offered — never a blanket default.
"""
from __future__ import annotations

import asyncio

import pytest

from geox_mcp.tools.evidence_reason import _reason_basin_baseline


def _call(name: str):
    return asyncio.run(_reason_basin_baseline(name, "default"))


@pytest.mark.parametrize(
    "name",
    ["Sarawak Basin", "North Luconia", "Central Luconia", "Balingian", "Baram", "Luconia"],
)
def test_sarawak_basins_resolve_to_profile(name: str) -> None:
    """Every Sarawak province must resolve, including via alias, not raise a dead end."""
    result = _call(name)
    artifact = result.get("primary_artifact", {})
    assert result.get("execution_status") == "SUCCESS", (
        f"{name!r} did not resolve: {artifact.get('status')}"
    )
    overview = artifact.get("local_interpretation", {}).get("basin_overview", {})
    assert overview.get("basin_name"), f"{name!r} resolved without a basin_name"
    assert overview.get("tectonic_setting"), f"{name!r} resolved without tectonic setting"


def test_unregistered_basin_returns_coverage_gap_not_bare_error() -> None:
    result = _call("Kertang Basin")
    artifact = result.get("primary_artifact", {})
    assert artifact.get("status") == "COVERAGE_GAP"
    assert artifact.get("reason") == "no_registry_entry"
    assert "error" not in artifact
    # The gap must be named precisely and be actionable.
    assert artifact.get("to_close_gap", {}).get("action", "").endswith("basin_profile.yaml")
    # And the user must be told what they can still do.
    assert isinstance(artifact.get("still_available"), list) and artifact["still_available"]
    assert isinstance(artifact.get("registered_basins"), list) and artifact["registered_basins"]


def test_analogue_is_geographically_justified_or_absent() -> None:
    """A distant basin must not be presented as an analogue — false transfer is worse than none."""
    result = _call("Bintuni Bay")  # Papua, roughly 19 degrees from any Sarawak or Sabah centre
    artifact = result.get("primary_artifact", {})
    assert artifact.get("status") == "COVERAGE_GAP"
    assert artifact.get("nearest_registered_analogue") is None
    assert "too far" in (artifact.get("analogue_reason") or "")


def test_coverage_gap_never_claims_a_finding() -> None:
    """A coverage gap is an absence of registry evidence, not a statement about the geology."""
    artifact = _call("Narnia Basin").get("primary_artifact", {})
    assert artifact.get("claim_state") == "NO_VALID_EVIDENCE"
    assert "not a finding that the basin lacks geology" in artifact.get("detail", "")
