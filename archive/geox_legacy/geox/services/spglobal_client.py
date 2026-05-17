"""
geox/services/spglobal_client.py — S&P Global Commodity Insights API Client
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

Enterprise data bridge to S&P Global's energy & commodities databases.
Covers:
  • S&P Global Connect API      — well, production, and basin data
  • S&P Global Energy Portal    — E&P information, 425+ basins, 5M+ wells
  • Commodity Insights Prices   — benchmark assessments (Brent, WTI, etc.)

Constitutional:
  F2 TRUTH   — all data tagged with source API and timestamp
  F7 HUMILITY — uncertainty bands from vendor data quality specs
  F11 AUDIT  — every call logged with request ID and provenance

Environment:
  SPGLOBAL_API_KEY       — Bearer token or API key
  SPGLOBAL_BASE_URL      — API gateway (default: Connect API staging)
  SPGLOBAL_ENERGY_URL    — Energy Portal base URL
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("geox.services.spglobal")

# S&P Global canonical API gateways
_DEFAULT_CONNECT_URL = "https://api.spglobal.com/v1"
_DEFAULT_ENERGY_URL = "https://energyportal.ci.spglobal.com/api/v1"


@dataclass
class SPGlobalProvenance:
    """Audit stub for every S&P Global API invocation."""

    endpoint: str
    requested_at: str
    response_status: int
    request_id: str | None = None
    latency_ms: float | None = None
    data_freshness: str | None = None  # e.g. "2026-04-27T00:00:00Z"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": "sp_global_api",
            "endpoint": self.endpoint,
            "requested_at": self.requested_at,
            "response_status": self.response_status,
            "request_id": self.request_id,
            "latency_ms": self.latency_ms,
            "data_freshness": self.data_freshness,
        }


class SPGlobalClient:
    """
    Async client for S&P Global energy & commodity data services.

    Designed to degrade gracefully: if no API key is present, the client
    returns structured VOID responses rather than raising. This lets GEOX
    pipelines continue with scaffold data while flagging the provenance gap.
    """

    def __init__(
        self,
        api_key: str | None = None,
        connect_base_url: str | None = None,
        energy_base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.getenv("SPGLOBAL_API_KEY")
        self.connect_base = (connect_base_url or os.getenv("SPGLOBAL_BASE_URL", _DEFAULT_CONNECT_URL)).rstrip("/")
        self.energy_base = (energy_base_url or os.getenv("SPGLOBAL_ENERGY_URL", _DEFAULT_ENERGY_URL)).rstrip("/")
        self.timeout = timeout
        self._has_auth = bool(self.api_key)

    # ── Low-level request wrapper ─────────────────────────────────────────────

    async def _request(
        self,
        method: str,
        endpoint: str,
        base_url: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an authenticated request and return a GEOX-shaped response."""
        url = f"{base_url}/{endpoint.lstrip('/')}"
        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "GEOX-arifOS/0.1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        t0 = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("S&P Global HTTP error: %s %s -> %s", method, url, exc.response.status_code)
            return {
                "_spg_error": True,
                "_spg_status": exc.response.status_code,
                "_spg_detail": exc.response.text[:500],
                "_spg_url": url,
            }
        except httpx.RequestError as exc:
            logger.warning("S&P Global request error: %s %s -> %s", method, url, exc)
            return {
                "_spg_error": True,
                "_spg_status": 0,
                "_spg_detail": str(exc),
                "_spg_url": url,
            }

        latency = (datetime.now(timezone.utc) - t0).total_seconds() * 1000
        provenance = SPGlobalProvenance(
            endpoint=endpoint,
            requested_at=t0.isoformat(),
            response_status=resp.status_code,
            request_id=resp.headers.get("X-Request-ID"),
            latency_ms=round(latency, 2),
        )
        return {"_spg_data": data, "_spg_provenance": provenance.to_dict()}

    # ── Well Data ─────────────────────────────────────────────────────────────

    async def fetch_well(
        self,
        well_id: str,
        include_production: bool = False,
        include_logs: bool = False,
    ) -> dict[str, Any]:
        """
        Retrieve well header and optional production/log summaries.

        Maps to S&P Global Energy Portal well records (~5M wells globally).
        """
        if not self._has_auth:
            return self._void_response("well", well_id, reason="missing_api_key")

        params: dict[str, Any] = {"wellId": well_id}
        if include_production:
            params["includeProduction"] = "true"
        if include_logs:
            params["includeLogs"] = "true"

        result = await self._request("GET", "/wells/detail", self.energy_base, params=params)
        if "_spg_error" in result:
            return result

        # Normalize to GEOX canonical well header schema
        raw = result.pop("_spg_data", {})
        result["well"] = {
            "well_id": well_id,
            "well_name": raw.get("wellName") or raw.get("well_name"),
            "uwi": raw.get("uwi") or raw.get("uniqueWellIdentifier"),
            "basin": raw.get("basin"),
            "operator": raw.get("operator"),
            "country": raw.get("country"),
            "state_province": raw.get("stateProvince") or raw.get("state"),
            "surface_latitude": raw.get("surfaceLatitude") or raw.get("latitude"),
            "surface_longitude": raw.get("surfaceLongitude") or raw.get("longitude"),
            "total_depth_m": raw.get("totalDepth") or raw.get("total_depth_m"),
            "status": raw.get("wellStatus") or raw.get("status"),
            "spud_date": raw.get("spudDate") or raw.get("spud_date"),
            "completion_date": raw.get("completionDate") or raw.get("completion_date"),
        }
        result["include_production"] = include_production
        result["include_logs"] = include_logs
        return result

    async def search_wells_by_bbox(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Spatial well search within a bounding box."""
        if not self._has_auth:
            return self._void_response("well_search", f"bbox:{min_lat},{min_lon}:{max_lat},{max_lon}")

        params = {
            "minLat": min_lat,
            "maxLat": max_lat,
            "minLon": min_lon,
            "maxLon": max_lon,
            "limit": min(limit, 500),
        }
        result = await self._request("GET", "/wells/search", self.energy_base, params=params)
        if "_spg_error" in result:
            return result

        raw = result.pop("_spg_data", {})
        wells = raw.get("wells", raw.get("results", raw.get("data", [])))
        result["wells"] = wells
        result["count"] = len(wells)
        result["limit"] = limit
        return result

    # ── Basin Data ────────────────────────────────────────────────────────────

    async def fetch_basin_summary(self, basin_name: str) -> dict[str, Any]:
        """
        Retrieve basin-level summary: well count, production stats, reserves.
        S&P Global covers 425+ basins worldwide.
        """
        if not self._has_auth:
            return self._void_response("basin", basin_name, reason="missing_api_key")

        result = await self._request("GET", f"/basins/{basin_name}/summary", self.energy_base)
        if "_spg_error" in result:
            return result

        raw = result.pop("_spg_data", {})
        result["basin"] = {
            "basin_name": basin_name,
            "well_count": raw.get("wellCount") or raw.get("well_count"),
            "basin_type": raw.get("basinType") or raw.get("basin_type"),
            "producing_formations": raw.get("producingFormations") or raw.get("producing_formations", []),
            "total_cumulative_production_boe": raw.get("totalCumulativeProduction") or raw.get("total_cumulative_production_boe"),
            "remaining_reserves_mmboe": raw.get("remainingReserves") or raw.get("remaining_reserves_mmboe"),
        }
        return result

    # ── Commodity Prices ──────────────────────────────────────────────────────

    async def fetch_price_assessment(
        self,
        commodity: str,  # "brent", "wti", "henry_hub", etc.
        assessment_date: str | None = None,  # YYYY-MM-DD
        currency: str = "USD",
    ) -> dict[str, Any]:
        """
        Retrieve S&P Global Platts benchmark price assessment.
        https://developer.spglobal.com/commodity/prices
        """
        if not self._has_auth:
            return self._void_response("price", commodity, reason="missing_api_key")

        params: dict[str, Any] = {"commodity": commodity, "currency": currency}
        if assessment_date:
            params["date"] = assessment_date

        result = await self._request("GET", "/commodities/price-assessment", self.connect_base, params=params)
        if "_spg_error" in result:
            return result

        raw = result.pop("_spg_data", {})
        result["price"] = {
            "commodity": commodity,
            "assessment_date": assessment_date or raw.get("assessmentDate"),
            "benchmark_name": raw.get("benchmarkName") or raw.get("benchmark"),
            "price": raw.get("price") or raw.get("value"),
            "unit": raw.get("unit") or raw.get("priceUnit", "USD/bbl"),
            "currency": currency,
            "low": raw.get("low"),
            "high": raw.get("high"),
            "methodology": raw.get("methodology"),
        }
        return result

    async def fetch_price_history(
        self,
        commodity: str,
        start_date: str,
        end_date: str,
        frequency: str = "daily",  # daily | weekly | monthly
    ) -> dict[str, Any]:
        """Historical price assessments for trend analysis."""
        if not self._has_auth:
            return self._void_response("price_history", commodity, reason="missing_api_key")

        params = {
            "commodity": commodity,
            "startDate": start_date,
            "endDate": end_date,
            "frequency": frequency,
        }
        result = await self._request("GET", "/commodities/price-history", self.connect_base, params=params)
        if "_spg_error" in result:
            return result

        raw = result.pop("_spg_data", {})
        result["commodity"] = commodity
        result["frequency"] = frequency
        result["history"] = raw.get("prices", raw.get("data", raw.get("history", [])))
        return result

    # ── Production Data ───────────────────────────────────────────────────────

    async def fetch_well_production(
        self,
        well_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Monthly production volumes for a given well."""
        if not self._has_auth:
            return self._void_response("production", well_id, reason="missing_api_key")

        params: dict[str, Any] = {"wellId": well_id}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        result = await self._request("GET", "/production/monthly", self.energy_base, params=params)
        if "_spg_error" in result:
            return result

        raw = result.pop("_spg_data", {})
        result["well_id"] = well_id
        result["production"] = raw.get("production", raw.get("data", raw.get("monthlyVolumes", [])))
        return result

    # ── Health check ──────────────────────────────────────────────────────────

    async def health_check(self) -> dict[str, Any]:
        """Lightweight connectivity probe against S&P Global Connect."""
        if not self._has_auth:
            return {"reachable": False, "authenticated": False, "reason": "SPGLOBAL_API_KEY not set"}

        result = await self._request("GET", "/health", self.connect_base)
        if "_spg_error" in result:
            return {
                "reachable": False,
                "authenticated": True,
                "status": result.get("_spg_status"),
                "detail": result.get("_spg_detail"),
            }
        return {"reachable": True, "authenticated": True, "latency_ms": result["_spg_provenance"].get("latency_ms")}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _void_response(self, data_type: str, query: str, reason: str = "missing_api_key") -> dict[str, Any]:
        """Return a typed VOID when auth is missing — pipeline-safe."""
        return {
            "_spg_error": True,
            "_spg_status": 401,
            "_spg_detail": f"S&P Global {data_type} lookup voided: {reason}. Set SPGLOBAL_API_KEY.",
            "_spg_query": query,
            "_spg_provenance": {
                "source": "sp_global_api",
                "endpoint": f"/{data_type}",
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "response_status": 401,
            },
        }
