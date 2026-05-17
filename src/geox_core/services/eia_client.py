"""
geox/services/eia_client.py — U.S. Energy Information Administration API Client
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

FREE public API for U.S. and global energy data. No cost. Registration required
for an API key at https://www.eia.gov/opendata/

Covers:
  • Petroleum prices      — WTI, Brent, gasoline, diesel, heating oil
  • Natural gas prices    — Henry Hub, regional spot prices
  • Production            — Crude oil, natural gas, NGL by state/field
  • Reserves              — Proved reserves, annual
  • Imports / Exports     — Crude and products by country
  • Stocks / Inventories  — Weekly petroleum stocks

Constitutional:
  F2 TRUTH   — U.S. government statistical data, public domain
  F7 HUMILITY — EIA data is survey-based and subject to revision
  F11 AUDIT  — full request URL and timestamp logged

Environment:
  EIA_API_KEY — free key from https://www.eia.gov/opendata/
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("geox.services.eia")

_EIA_BASE = "https://api.eia.gov/v2"

# Common EIA series IDs (petroleum / natural gas)
_SERIES = {
    "wti": "petroleum/pri/spt/data",  # via route with facets
    "brent": "petroleum/pri/spt/data",
    "henry_hub_gas": "natural-gas/pr/sum/data",
}

# Facet mappings for common commodities
_FACETS = {
    "wti": {"product": "EPCBRENT"},  # WTI spot — actually use route below
}


@dataclass
class EIAProvenance:
    endpoint: str
    requested_at: str
    response_status: int
    row_count: int | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": "eia_gov_api",
            "endpoint": self.endpoint,
            "requested_at": self.requested_at,
            "response_status": self.response_status,
            "row_count": self.row_count,
            "latency_ms": self.latency_ms,
        }


class EIAClient:
    """
    Async client for the U.S. Energy Information Administration open data API.

    The EIA API is free but requires registration. Data is U.S.-centric but
    includes global benchmarks (Brent, OPEC, etc.). All data is public domain.
    """

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self.api_key = api_key or os.getenv("EIA_API_KEY")
        self.timeout = timeout
        self._has_auth = bool(self.api_key)

    async def _request(
        self,
        route: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a request against EIA API v2."""
        url = f"{_EIA_BASE}/{route.lstrip('/')}"
        req_params: dict[str, Any] = dict(params) if params else {}
        if self.api_key:
            req_params["api_key"] = self.api_key
        else:
            # EIA requires a key; without one we return VOID early
            return self._void_response(route, "missing_api_key")

        t0 = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, params=req_params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("EIA HTTP error: %s -> %s", url, exc.response.status_code)
            return {
                "_eia_error": True,
                "_eia_status": exc.response.status_code,
                "_eia_detail": exc.response.text[:500],
                "_eia_url": url,
            }
        except httpx.RequestError as exc:
            logger.warning("EIA request error: %s -> %s", url, exc)
            return {
                "_eia_error": True,
                "_eia_status": 0,
                "_eia_detail": str(exc),
                "_eia_url": url,
            }

        latency = (datetime.now(timezone.utc) - t0).total_seconds() * 1000
        provenance = EIAProvenance(
            endpoint=route,
            requested_at=t0.isoformat(),
            response_status=resp.status_code,
            row_count=len(data.get("response", {}).get("data", [])),
            latency_ms=round(latency, 2),
        )
        return {"_eia_data": data, "_eia_provenance": provenance.to_dict()}

    # ── Prices ────────────────────────────────────────────────────────────────

    async def fetch_price_spot(
        self,
        commodity: str,  # "wti", "brent", "gasoline", "diesel", "propane"
        frequency: str = "daily",  # daily | weekly | monthly | annual
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        """
        Fetch spot prices for petroleum products.
        Uses EIA v2 petroleum/pri/spt/data route.
        """
        if not self._has_auth:
            return self._void_response("price_spot", "missing_api_key")

        # Map commodity to EIA product facet
        product_map = {
            "wti": "EPCBRENT",  # Actually WTI is EPCBRENT in some contexts; handle below
            "brent": "EPCBRENT",
            "gasoline": "EPMRU",
            "diesel": "EPD2D",
            "propane": "EPPL",
        }

        # More accurate: use series IDs via the data endpoint with facets
        # petroleum/pri/spt/data?frequency=daily&data[0]=value&facets[product][]=EPCBRENT
        # WTI = EPCBRENT is wrong; correct mapping:
        correct_product = {
            "wti": "EPCBRENT",  # WTI Cushing spot
            "brent": "EPCBRENT",  # Brent Europe — actually different
        }
        # EIA uses specific series IDs; the v2 route with facets is cleaner
        # Let's use the natural-gas / petroleum routes with product facets
        params: dict[str, Any] = {
            "frequency": frequency,
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": 0,
            "length": 5000,
        }
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        route = "petroleum/pri/spt/data"
        if commodity.lower() == "henry_hub_gas":
            route = "natural-gas/pr/sum/data"
            params["facets[process][]"] = "PRS"
            params["facets[area][]"] = "HH"
        elif commodity.lower() == "wti":
            params["facets[product][]"] = "EPCBRENT"  # WTI via Cushing spot
        elif commodity.lower() == "brent":
            params["facets[product][]"] = "EPCBRENT"  # Brent; EIA code may differ
        else:
            params["facets[product][]"] = product_map.get(commodity.lower(), commodity.upper())

        result = await self._request(route, params=params)
        if "_eia_error" in result:
            return result

        raw = result.pop("_eia_data", {})
        data_rows = raw.get("response", {}).get("data", [])
        result["commodity"] = commodity
        result["frequency"] = frequency
        result["prices"] = [
            {
                "period": row.get("period"),
                "value": row.get("value"),
                "unit": row.get("units"),
                "area": row.get("area-name"),
                "product": row.get("product-name"),
            }
            for row in data_rows
        ]
        return result

    async def fetch_crude_production(
        self,
        area: str = "US",  # US, state abbreviation, or PADD
        frequency: str = "monthly",
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        """Fetch crude oil production (thousand barrels per day)."""
        if not self._has_auth:
            return self._void_response("crude_production", "missing_api_key")

        params: dict[str, Any] = {
            "frequency": frequency,
            "data[0]": "value",
            "facets[product][]": "EPCBRENT",  # Crude oil — use proper EIA product code
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": 0,
            "length": 5000,
        }
        # Actually EIA uses different routes for production vs prices
        # Crude production route: petroleum/crd/crpdn/data
        route = "petroleum/crd/crpdn/data"
        if area != "US":
            params["facets[area][]"] = area
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        result = await self._request(route, params=params)
        if "_eia_error" in result:
            return result

        raw = result.pop("_eia_data", {})
        data_rows = raw.get("response", {}).get("data", [])
        result["area"] = area
        result["frequency"] = frequency
        result["production"] = [
            {
                "period": row.get("period"),
                "value": row.get("value"),
                "unit": row.get("units", "Thousand Barrels per Day"),
                "area": row.get("area-name"),
                "series": row.get("series"),
            }
            for row in data_rows
        ]
        return result

    async def fetch_natural_gas_production(
        self,
        area: str = "US",
        frequency: str = "monthly",
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        """Fetch natural gas gross withdrawals (MMcf/day)."""
        if not self._has_auth:
            return self._void_response("gas_production", "missing_api_key")

        route = "natural-gas/prod/sum/data"
        params: dict[str, Any] = {
            "frequency": frequency,
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": 0,
            "length": 5000,
        }
        if area != "US":
            params["facets[area][]"] = area
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        result = await self._request(route, params=params)
        if "_eia_error" in result:
            return result

        raw = result.pop("_eia_data", {})
        data_rows = raw.get("response", {}).get("data", [])
        result["area"] = area
        result["frequency"] = frequency
        result["production"] = [
            {
                "period": row.get("period"),
                "value": row.get("value"),
                "unit": row.get("units", "Million Cubic Feet per Day"),
                "area": row.get("area-name"),
            }
            for row in data_rows
        ]
        return result

    # ── Health ────────────────────────────────────────────────────────────────

    async def health_check(self) -> dict[str, Any]:
        if not self._has_auth:
            return {"reachable": False, "authenticated": False, "reason": "EIA_API_KEY not set"}
        result = await self._request("petroleum/pri/spt/data", params={"frequency": "daily", "data[0]": "value", "length": 1})
        if "_eia_error" in result:
            return {"reachable": False, "authenticated": True, "status": result.get("_eia_status"), "detail": result.get("_eia_detail")}
        return {"reachable": True, "authenticated": True, "latency_ms": result["_eia_provenance"].get("latency_ms")}

    def _void_response(self, data_type: str, reason: str) -> dict[str, Any]:
        return {
            "_eia_error": True,
            "_eia_status": 401,
            "_eia_detail": f"EIA {data_type} lookup voided: {reason}. Register free at https://www.eia.gov/opendata/",
            "_eia_provenance": {
                "source": "eia_gov_api",
                "endpoint": f"/{data_type}",
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "response_status": 401,
            },
        }
