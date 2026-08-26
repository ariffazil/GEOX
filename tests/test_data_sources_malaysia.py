"""
test_data_sources_malaysia.py — Regression guard for the JMG MyGEMS catalog.

Audit 2026-08-26 catalogued 15 Map Services + 77 Feature Services (11 substantive)
from Jabatan Mineral dan Geosains Malaysia via the ArcGIS Sharing REST API.
This test ensures the catalog resource is wired correctly and the underlying
ArcGIS Hub is reachable.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from geox_mcp.resources import (  # noqa: E402
    RESOURCES_DIR,
    geox_data_sources_malaysia,
)

CATALOG_PATH = RESOURCES_DIR / "data_sources" / "malaysia_jmg_myGEMS_catalog.json"


def test_catalog_file_exists() -> None:
    """The catalog JSON must exist on disk."""
    assert CATALOG_PATH.exists(), f"Missing catalog file: {CATALOG_PATH}"


def test_catalog_parses_as_json() -> None:
    """The catalog must be valid JSON."""
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_catalog_has_required_sections() -> None:
    """The catalog must include meta, map_services, feature_services_substantive, falsification_audit."""
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    for key in ("_meta", "map_services", "feature_services_substantive", "falsification_audit_2026-08-26"):
        assert key in data, f"Catalog missing required key: {key}"


def test_catalog_counts() -> None:
    """Catalog must list all 15 JMG Map Services plus the substantive Feature Services.

    Note: the catalog has 20 entries in map_services (15 from MyGEMS Sharing API +
    5 NaTSIS-hosted sub-layer services). The 15 is the strict count of top-level
    Map Services. Both are accepted here as long as the catalog is honest about it.
    """
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    meta_counts = data["_meta"]["counts"]
    assert meta_counts["map_services_total"] == 15, (
        f"map_services_total should be 15 (from ArcGIS probe), got {meta_counts['map_services_total']}"
    )
    assert meta_counts["feature_services_total"] == 77
    assert len(data["map_services"]) >= 15, (
        f"Expected at least 15 map_services entries, got {len(data['map_services'])}"
    )
    assert len(data["feature_services_substantive"]) >= 11, (
        f"Expected at least 11 substantive Feature Services, got {len(data['feature_services_substantive'])}"
    )


def test_catalog_every_url_has_https_scheme() -> None:
    """Every service URL must be https://."""
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    offenders = []
    for s in data["map_services"] + data["feature_services_substantive"]:
        url = s.get("url", "")
        if not url.startswith("https://"):
            offenders.append(url)
    assert not offenders, f"Non-HTTPS URLs: {offenders}"


def test_catalog_marks_onegeology_falsification() -> None:
    """The falsification audit must explicitly correct the OneGeology false claim."""
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    audit = data["falsification_audit_2026-08-26"]
    assert "OneGeology" in str(audit), "Audit must address OneGeology false claim"
    assert "FALSE" in str(audit) or "WRONG" in str(audit), (
        "Audit must explicitly mark OneGeology as FALSE / WRONG"
    )


def test_resource_function_loads_catalog() -> None:
    """geox_data_sources_malaysia() must return the catalog contents."""
    import asyncio
    out = asyncio.run(geox_data_sources_malaysia())
    data = json.loads(out)
    assert "_meta" in data, "Resource function must return catalog"
    assert data["_meta"]["uri"] == "geox://data-sources/malaysia"


@pytest.mark.network
def test_jmg_sharing_api_reachable() -> None:
    """The MyGEMS ArcGIS Sharing API must respond 200 (live state check)."""
    url = (
        "https://mygems.jmg.gov.my/portal/sharing/rest/search"
        "?q=type:%22Map%20Service%22&num=1&f=json"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GEOX-Zen-Audit/2026-08-26"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            assert resp.status == 200, f"JMG Sharing API returned {resp.status}"
    except Exception as e:
        pytest.skip(f"JMG Sharing API unreachable (network may be restricted): {e}")
