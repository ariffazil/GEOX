"""
test_geox_paleobiodb_query.py — Regression guard for the PBDB public tool.

Validates:
- Tool module imports and exposes geox_paleobiodb_query
- Manifest declares the tool with OBSERVE / read_only / mutation=false
- TTL cache layer hits & misses correctly (no live network)
- Invalid mode returns envelope status=error
- Missing required params return envelope status=error
- Catalog JSON exists, parses, has required sections
- Resource function loads catalog file

Live PBDB network tests are gated behind @pytest.mark.network (skipped by default).

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from geox_mcp.resources import (  # noqa: E402
    RESOURCES_DIR,
    geox_data_sources_paleobiodb,
)
from geox_mcp.tools.geox_paleobiodb_query import (  # noqa: E402
    _cache_get,
    _cache_set,
    _cache_key,
    geox_paleobiodb_query,
)

MANIFEST_PATH = REPO_ROOT / "src" / "geox_mcp" / "tools_manifest.yaml"
CATALOG_PATH = RESOURCES_DIR / "data_sources" / "paleobiodb_catalog.json"


# ── Manifest entry ───────────────────────────────────────────────────────────


def test_manifest_declares_tool() -> None:
    """tools_manifest.yaml must contain geox_paleobiodb_query entry."""
    data = yaml.safe_load(MANIFEST_PATH.read_text())
    tools = data.get("tools", [])
    match = next((t for t in tools if t.get("name") == "geox_paleobiodb_query"), None)
    assert match is not None, "geox_paleobiodb_query missing from tools_manifest.yaml"


def test_manifest_governance_is_observe() -> None:
    """Tool must be OBSERVE class, mutation=false, read_only=true."""
    data = yaml.safe_load(MANIFEST_PATH.read_text())
    tools = data.get("tools", [])
    match = next((t for t in tools if t.get("name") == "geox_paleobiodb_query"), None)
    assert match is not None
    gov = match.get("governance", {})
    ann = match.get("annotations", {})
    assert gov.get("action_class") == "OBSERVE", f"action_class must be OBSERVE, got {gov.get('action_class')}"
    assert gov.get("mutation") is False
    assert ann.get("read_only") is True
    assert ann.get("destructive") is False
    assert ann.get("idempotent") is True


# ── Catalog JSON ─────────────────────────────────────────────────────────────


def test_catalog_file_exists() -> None:
    assert CATALOG_PATH.exists(), f"Missing catalog file: {CATALOG_PATH}"


def test_catalog_parses_as_json() -> None:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_catalog_has_required_sections() -> None:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    for key in ("schema", "resource_uri", "source", "endpoints", "falsification_audit_2026-08-26"):
        assert key in data, f"Catalog missing required key: {key}"


def test_catalog_attribution_required() -> None:
    """PBDB is CC-BY 4.0; attribution must be flagged as required."""
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    src = data.get("source", {})
    assert src.get("license", "").startswith("CC-BY"), "PBDB license should be CC-BY"
    assert src.get("attribution_required") is True
    assert "paleobiodb.org" in src.get("attribution_string", "").lower()


def test_resource_function_loads_catalog() -> None:
    """The async resource function should return the catalog content as JSON string."""
    import asyncio
    result = asyncio.run(geox_data_sources_paleobiodb())
    parsed = json.loads(result)
    assert parsed.get("resource_uri") == "geox://data-sources/paleobiodb"


# ── TTL Cache layer (no network) ─────────────────────────────────────────────


def test_cache_set_and_get() -> None:
    _cache_set("test_key", {"hello": "world"})
    assert _cache_get("test_key") == {"hello": "world"}


def test_cache_key_deterministic() -> None:
    k1 = _cache_key("taxa", {"name": "Emiliania", "limit": 10})
    k2 = _cache_key("taxa", {"limit": 10, "name": "Emiliania"})
    assert k1 == k2, "Cache key should be order-independent"
    k3 = _cache_key("taxa", {"name": "Emiliania", "limit": 11})
    assert k1 != k3, "Cache key should differ when params differ"


# ── Envelope behaviour (no network) ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_mode_returns_error_envelope() -> None:
    """Mode not in {taxa, occurrence, zone, age_intervals} → status=error envelope."""
    result = await geox_paleobiodb_query(mode="bogus_mode")
    assert result["status"] == "error"
    assert "unknown mode" in " ".join(result.get("warnings", []))
    assert result["tool"] == "geox_paleobiodb_query"


@pytest.mark.asyncio
async def test_missing_name_for_taxa_returns_error_envelope() -> None:
    """mode=taxa without name → status=error with helpful hint."""
    result = await geox_paleobiodb_query(mode="taxa", name="")
    assert result["status"] == "error"
    assert any("name" in w.lower() for w in result.get("warnings", []))


@pytest.mark.asyncio
async def test_missing_taxon_for_occurrence_returns_error_envelope() -> None:
    """mode=occurrence without taxon → status=error with helpful hint."""
    result = await geox_paleobiodb_query(mode="occurrence", taxon="")
    assert result["status"] == "error"
    assert any("taxon" in w.lower() for w in result.get("warnings", []))


@pytest.mark.asyncio
async def test_envelope_shape_is_canonical() -> None:
    """Even on error, envelope must include status, tool, data, sources, warnings."""
    result = await geox_paleobiodb_query(mode="bogus")
    for key in ("status", "tool", "data", "sources", "warnings"):
        assert key in result, f"envelope missing key: {key}"
    assert result["tool"] == "geox_paleobiodb_query"


# ── Opt-in network tests (skipped by default) ────────────────────────────────


@pytest.mark.network
@pytest.mark.asyncio
async def test_live_taxa_lookup_emiliania() -> None:
    """Resolve a well-known nannofossil taxon against live PBDB."""
    result = await geox_paleobiodb_query(mode="taxa", name="Emiliania huxleyi")
    assert result["status"] in ("ok", "partial")
    assert result["data"]["matched"] is True
    taxon = result["data"]["taxon"]
    assert taxon["accepted_name"].lower().startswith("emiliania")


@pytest.mark.network
@pytest.mark.asyncio
async def test_live_age_intervals_returns_ics() -> None:
    """Live PBDB scale=1 returns ICS chronostratigraphic intervals."""
    result = await geox_paleobiodb_query(mode="age_intervals")
    assert result["status"] in ("ok", "partial")
    assert result["data"]["count"] > 10
    intervals = result["data"]["intervals"]
    # At least one interval should be a Cenozoic stage name
    names = [iv.get("nam", "") for iv in intervals]
    assert any("Cenozoic" in n or "Quaternary" in n or "Neogene" in n for n in names), \
        f"Expected ICS Cenozoic stages in intervals, got first 10 names: {names[:10]}"


@pytest.mark.network
@pytest.mark.asyncio
async def test_live_zone_nannofossil() -> None:
    """Live PBDB scale=5 returns calcareous nannoplankton zones (NN/NP)."""
    result = await geox_paleobiodb_query(mode="zone", fossil_group="calcareous_nannofossil")
    assert result["status"] in ("ok", "partial")
    assert result["data"]["pbdb_scale"] == 5
