"""
geox/services/npd_client.py — Norwegian Offshore Directorate (NPD) Client
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

Completely FREE. No API key. No registration. No rate limits.

The Norwegian Offshore Directorate maintains public FactPages with daily-updated
data on all petroleum activities on the Norwegian Continental Shelf:
  • 7,500+ wellbores
  • 120+ fields
  • 1,000+ facilities
  • Monthly production per field
  • Licenses, companies, surveys, stratigraphy

Data is returned as CSV from NPD's ReportServer and parsed into structured dicts.

Constitutional:
  F2 TRUTH   — official government regulatory data
  F7 HUMILITY — well data reflects public reporting; confidential wells excluded
  F11 AUDIT  — provenance stamped with NPD source URL

License: Free to copy and use with attribution (per NPD terms).
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("geox.services.npd")

# NPD FactPages ReportServer CSV endpoints (public, no auth)
_NPD_CSV_BASE = "https://factpages.npd.no/ReportServer_npdpublic"

_ENDPOINTS = {
    "wellbore_exploration": f"{_NPD_CSV_BASE}?/FactPages/TableView/wellbore_exploration_all&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "wellbore_development": f"{_NPD_CSV_BASE}?/FactPages/TableView/wellbore_development_all&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "wellbore_other": f"{_NPD_CSV_BASE}?/FactPages/TableView/wellbore_other_all&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "field": f"{_NPD_CSV_BASE}?/FactPages/TableView/field&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "field_production_monthly": f"{_NPD_CSV_BASE}?/FactPages/TableView/field_production_monthly&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "field_production_year_month": f"{_NPD_CSV_BASE}?/FactPages/TableView/field_production_year_month&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "discovery": f"{_NPD_CSV_BASE}?/FactPages/TableView/discovery&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "company": f"{_NPD_CSV_BASE}?/FactPages/TableView/company&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "facility_fixed": f"{_NPD_CSV_BASE}?/FactPages/TableView/facility_fixed&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "facility_moveable": f"{_NPD_CSV_BASE}?/FactPages/TableView/facility_moveable&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "license": f"{_NPD_CSV_BASE}?/FactPages/TableView/licence&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "survey": f"{_NPD_CSV_BASE}?/FactPages/TableView/survey&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
    "stratigraphy": f"{_NPD_CSV_BASE}?/FactPages/TableView/baa_and_ppa&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&CultureCode=en",
}


@dataclass
class NPDProvenance:
    endpoint: str
    requested_at: str
    response_status: int
    row_count: int
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": "npd_norway",
            "endpoint": self.endpoint,
            "requested_at": self.requested_at,
            "response_status": self.response_status,
            "row_count": self.row_count,
            "latency_ms": self.latency_ms,
        }


class NPDClient:
    """
    Client for the Norwegian Offshore Directorate public FactPages.

    ZERO AUTH REQUIRED. This is the ultimate miskin-friendly energy data source.
    All data is public, updated daily, and free to use with attribution.
    """

    def __init__(self, timeout: float = 60.0) -> None:
        self.timeout = timeout

    async def _fetch_csv(self, endpoint_key: str) -> dict[str, Any]:
        """Fetch and parse a CSV endpoint from NPD."""
        url = _ENDPOINTS.get(endpoint_key)
        if not url:
            return {
                "_npd_error": True,
                "_npd_status": 400,
                "_npd_detail": f"Unknown endpoint: {endpoint_key}",
            }

        t0 = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                text = resp.text
        except httpx.HTTPStatusError as exc:
            logger.warning("NPD HTTP error: %s -> %s", url, exc.response.status_code)
            return {
                "_npd_error": True,
                "_npd_status": exc.response.status_code,
                "_npd_detail": exc.response.text[:500],
                "_npd_url": url,
            }
        except httpx.RequestError as exc:
            logger.warning("NPD request error: %s -> %s", url, exc)
            return {
                "_npd_error": True,
                "_npd_status": 0,
                "_npd_detail": str(exc),
                "_npd_url": url,
            }

        latency = (datetime.now(timezone.utc) - t0).total_seconds() * 1000
        # Parse CSV
        try:
            reader = csv.DictReader(io.StringIO(text, newline=""))
            rows = list(reader)
        except Exception as exc:
            return {
                "_npd_error": True,
                "_npd_status": 200,
                "_npd_detail": f"CSV parse error: {exc}",
                "_npd_url": url,
            }

        provenance = NPDProvenance(
            endpoint=endpoint_key,
            requested_at=t0.isoformat(),
            response_status=200,
            row_count=len(rows),
            latency_ms=round(latency, 2),
        )
        return {
            "_npd_data": rows,
            "_npd_provenance": provenance.to_dict(),
        }

    # ── Wellbores ─────────────────────────────────────────────────────────────

    async def fetch_wellbores_exploration(self) -> dict[str, Any]:
        """All exploration wellbores on the Norwegian Continental Shelf."""
        return await self._fetch_csv("wellbore_exploration")

    async def fetch_wellbores_development(self) -> dict[str, Any]:
        """All development wellbores on the Norwegian Continental Shelf."""
        return await self._fetch_csv("wellbore_development")

    async def fetch_wellbores_other(self) -> dict[str, Any]:
        """All other wellbores (scientific, appraisal, etc.)."""
        return await self._fetch_csv("wellbore_other")

    async def search_wellbore_by_name(self, name: str) -> dict[str, Any]:
        """Search wellbores by name (case-insensitive substring match)."""
        results = []
        for key in ("wellbore_exploration", "wellbore_development", "wellbore_other"):
            res = await self._fetch_csv(key)
            if "_npd_error" in res:
                continue
            for row in res.get("_npd_data", []):
                # Column names vary slightly; try common names
                wb_name = row.get("wlbWellboreName") or row.get("Wellbore name") or row.get("Name", "")
                if name.lower() in str(wb_name).lower():
                    results.append({"source": key, **row})
        return {
            "query": name,
            "count": len(results),
            "wellbores": results,
            "_npd_provenance": {
                "source": "npd_norway",
                "endpoint": "wellbore_search",
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "response_status": 200,
                "row_count": len(results),
            },
        }

    # ── Fields & Production ───────────────────────────────────────────────────

    async def fetch_fields(self) -> dict[str, Any]:
        """All fields on the Norwegian Continental Shelf."""
        return await self._fetch_csv("field")

    async def fetch_field_production_monthly(self) -> dict[str, Any]:
        """Monthly production per field (oil, gas, NGL, condensate)."""
        return await self._fetch_csv("field_production_monthly")

    async def fetch_field_production_by_year_month(self) -> dict[str, Any]:
        """Production aggregated by year and month."""
        return await self._fetch_csv("field_production_year_month")

    async def get_field_production(self, field_name: str) -> dict[str, Any]:
        """Filter monthly production for a specific field."""
        res = await self._fetch_csv("field_production_monthly")
        if "_npd_error" in res:
            return res
        rows = res.get("_npd_data", [])
        matched = [
            row for row in rows
            if field_name.lower() in str(row.get("prfInformationCarrier") or row.get("Field") or "").lower()
        ]
        return {
            "field_name": field_name,
            "count": len(matched),
            "production": matched,
            "_npd_provenance": {
                "source": "npd_norway",
                "endpoint": "field_production_filtered",
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "response_status": 200,
                "row_count": len(matched),
            },
        }

    # ── Discoveries & Facilities ──────────────────────────────────────────────

    async def fetch_discoveries(self) -> dict[str, Any]:
        """All discoveries on the NCS."""
        return await self._fetch_csv("discovery")

    async def fetch_facilities_fixed(self) -> dict[str, Any]:
        """Fixed production facilities."""
        return await self._fetch_csv("facility_fixed")

    async def fetch_facilities_moveable(self) -> dict[str, Any]:
        """Moveable facilities (rigs, vessels)."""
        return await self._fetch_csv("facility_moveable")

    async def fetch_companies(self) -> dict[str, Any]:
        """Licensed operators and licensees."""
        return await self._fetch_csv("company")

    async def fetch_licenses(self) -> dict[str, Any]:
        """Production licenses."""
        return await self._fetch_csv("license")

    async def fetch_surveys(self) -> dict[str, Any]:
        """Geophysical surveys."""
        return await self._fetch_csv("survey")

    # ── Health ────────────────────────────────────────────────────────────────

    async def health_check(self) -> dict[str, Any]:
        res = await self._fetch_csv("field")
        if "_npd_error" in res:
            return {"reachable": False, "status": res.get("_npd_status"), "detail": res.get("_npd_detail")}
        return {
            "reachable": True,
            "row_count": res["_npd_provenance"].get("row_count"),
            "latency_ms": res["_npd_provenance"].get("latency_ms"),
        }
