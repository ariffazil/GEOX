"""
geox/geox_mcp/tools/spglobal_tool.py — S&P Global MCP Tool Surface
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

GEOX public mission surface for S&P Global energy & commodity data.
All tools return canonical GEOX schema with ClaimTag, provenance, and VAULT999.

Constitutional:
  F1 AMANAH  — read-only; no writes to shared state
  F2 TRUTH   — provenance stamped with S&P Global endpoint and timestamp
  F7 HUMILITY — explicit uncertainty: vendor data subject to latency and licensing
  F9 ANTI-HANTU — no synthetic data passed as observed truth
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from geox.services.spglobal_client import SPGlobalClient
from geox.skills.earth_science.seismic_wrappers import ClaimTag

logger = logging.getLogger("geox.tools.spglobal")


# ══════════════════════════════════════════════════════════════════════════════
# Vault receipt helper (mirrors las_ingestor.py pattern)
# ══════════════════════════════════════════════════════════════════════════════


def _make_vault_receipt(tool_name: str, payload: dict, verdict: str) -> dict:
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(f"{tool_name}:{canonical}".encode("utf-8")).hexdigest()
    return {
        "vault": "VAULT999",
        "tool_name": tool_name,
        "verdict": verdict,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hash": digest[:16],
    }


# ══════════════════════════════════════════════════════════════════════════════
# Shared provenance builder
# ══════════════════════════════════════════════════════════════════════════════


def _build_provenance(spg_result: dict) -> str:
    """Extract a human-readable provenance string from S&P Global response."""
    prov = spg_result.get("_spg_provenance", {})
    endpoint = prov.get("endpoint", "unknown")
    ts = prov.get("requested_at", datetime.now(timezone.utc).isoformat())
    return f"sp_global_api:{endpoint}@{ts}"


def _build_limitations(spg_result: dict, data_type: str) -> list[str]:
    """Build F7 humility limitations list."""
    limitations: list[str] = [
        "S&P Global data is subject to vendor latency, licensing terms, and regional coverage gaps",
        "Price assessments reflect Platts methodology; may differ from exchange-traded prices",
    ]
    if spg_result.get("_spg_error"):
        limitations.append(f"S&P Global API returned error: {spg_result.get('_spg_detail', 'unknown')}")
    if data_type in ("price", "price_history"):
        limitations.append("Benchmark prices are assessment-based, not transaction-based")
    if data_type == "well":
        limitations.append("Well data completeness varies by jurisdiction and operator reporting")
    if data_type == "basin":
        limitations.append("Basin aggregations are estimates derived from multiple sources")
    return limitations


def _determine_claim_tag(spg_result: dict) -> str:
    """Map S&P Global response to GEOX ClaimTag."""
    if spg_result.get("_spg_error"):
        return ClaimTag.HYPOTHESIS.value
    data = spg_result.get("_spg_data")
    if data is None:
        return ClaimTag.UNKNOWN.value
    return ClaimTag.OBSERVED.value


# ══════════════════════════════════════════════════════════════════════════════
# Public Tool Surface
# ══════════════════════════════════════════════════════════════════════════════


def geox_well_load_spglobal(
    well_id: str,
    api_key: str | None = None,
    include_production: bool = False,
    include_logs: bool = False,
) -> dict[str, Any]:
    """
    Load well header data from S&P Global Energy Portal into witness context.

    Args:
        well_id: S&P Global well identifier or UWI.
        api_key: Optional override for SPGLOBAL_API_KEY.
        include_production: Whether to fetch monthly production volumes.
        include_logs: Whether to fetch log curve summaries.

    Returns:
        Canonical GEOX dict with well header, claim_tag, provenance, vault_receipt.
    """
    client = SPGlobalClient(api_key=api_key)
    try:
        result = asyncio.run(
            client.fetch_well(
                well_id=well_id,
                include_production=include_production,
                include_logs=include_logs,
            )
        )
    except Exception as exc:
        logger.exception("geox_well_load_spglobal failed")
        return {
            "well_id": well_id,
            "status": "error",
            "claim_tag": ClaimTag.VOID.value,
            "error": str(exc),
            "vault_receipt": _make_vault_receipt("geox_well_load_spglobal", {"well_id": well_id}, "VOID"),
            "limitations": ["Client exception — check network and API key"],
            "governance": {"f1_amanah": "read_only", "f2_truth": "source_unavailable"},
        }

    claim_tag = _determine_claim_tag(result)
    verdict = "SEAL" if claim_tag == ClaimTag.OBSERVED.value else "HOLD"
    payload = {"well_id": well_id, "include_production": include_production, "include_logs": include_logs}

    return {
        "well_id": well_id,
        "status": "loaded" if claim_tag == ClaimTag.OBSERVED.value else "void",
        "claim_tag": claim_tag,
        "provenance": _build_provenance(result),
        "well_header": result.get("well", {}),
        "spg_raw": result.get("_spg_data"),
        "spg_error": result.get("_spg_error", False),
        "spg_status": result.get("_spg_status"),
        "vault_receipt": _make_vault_receipt("geox_well_load_spglobal", payload, verdict),
        "limitations": _build_limitations(result, "well"),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "sp_global_api",
            "f7_humility": "vendor_latency_and_coverage",
            "f9_antihantu": "no_synthetic_data",
        },
    }


def geox_well_search_spglobal(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    api_key: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Search S&P Global well inventory by geographic bounding box.

    Args:
        min_lat, max_lat, min_lon, max_lon: Decimal degrees bounding box.
        api_key: Optional override for SPGLOBAL_API_KEY.
        limit: Max results (capped at 500 by API).

    Returns:
        Canonical GEOX dict with well list, claim_tag, provenance.
    """
    client = SPGlobalClient(api_key=api_key)
    try:
        result = asyncio.run(
            client.search_wells_by_bbox(
                min_lat=min_lat,
                max_lat=max_lat,
                min_lon=min_lon,
                max_lon=max_lon,
                limit=limit,
            )
        )
    except Exception as exc:
        logger.exception("geox_well_search_spglobal failed")
        return {
            "bbox": [min_lat, min_lon, max_lat, max_lon],
            "status": "error",
            "claim_tag": ClaimTag.VOID.value,
            "error": str(exc),
            "vault_receipt": _make_vault_receipt("geox_well_search_spglobal", {"bbox": [min_lat, min_lon, max_lat, max_lon]}, "VOID"),
            "limitations": ["Client exception — check network and API key"],
            "governance": {"f1_amanah": "read_only", "f2_truth": "source_unavailable"},
        }

    claim_tag = _determine_claim_tag(result)
    verdict = "SEAL" if claim_tag == ClaimTag.OBSERVED.value else "HOLD"
    payload = {"bbox": [min_lat, min_lon, max_lat, max_lon], "limit": limit}

    return {
        "bbox": [min_lat, min_lon, max_lat, max_lon],
        "status": "loaded" if claim_tag == ClaimTag.OBSERVED.value else "void",
        "claim_tag": claim_tag,
        "provenance": _build_provenance(result),
        "wells": result.get("wells", []),
        "count": result.get("count", 0),
        "spg_error": result.get("_spg_error", False),
        "spg_status": result.get("_spg_status"),
        "vault_receipt": _make_vault_receipt("geox_well_search_spglobal", payload, verdict),
        "limitations": _build_limitations(result, "well_search"),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "sp_global_api",
            "f7_humility": "vendor_latency_and_coverage",
        },
    }


def geox_basin_observe_spglobal(
    basin_name: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve basin-level summary from S&P Global (425+ basins covered).

    Args:
        basin_name: Canonical basin name (e.g. "Permian Basin", "Gulf of Mexico").
        api_key: Optional override for SPGLOBAL_API_KEY.

    Returns:
        Canonical GEOX dict with basin summary, claim_tag, provenance.
    """
    client = SPGlobalClient(api_key=api_key)
    try:
        result = asyncio.run(client.fetch_basin_summary(basin_name=basin_name))
    except Exception as exc:
        logger.exception("geox_basin_observe_spglobal failed")
        return {
            "basin_name": basin_name,
            "status": "error",
            "claim_tag": ClaimTag.VOID.value,
            "error": str(exc),
            "vault_receipt": _make_vault_receipt("geox_basin_observe_spglobal", {"basin_name": basin_name}, "VOID"),
            "limitations": ["Client exception — check network and API key"],
            "governance": {"f1_amanah": "read_only", "f2_truth": "source_unavailable"},
        }

    claim_tag = _determine_claim_tag(result)
    verdict = "SEAL" if claim_tag == ClaimTag.OBSERVED.value else "HOLD"
    payload = {"basin_name": basin_name}

    return {
        "basin_name": basin_name,
        "status": "loaded" if claim_tag == ClaimTag.OBSERVED.value else "void",
        "claim_tag": claim_tag,
        "provenance": _build_provenance(result),
        "basin_summary": result.get("basin", {}),
        "spg_error": result.get("_spg_error", False),
        "spg_status": result.get("_spg_status"),
        "vault_receipt": _make_vault_receipt("geox_basin_observe_spglobal", payload, verdict),
        "limitations": _build_limitations(result, "basin"),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "sp_global_api",
            "f7_humility": "vendor_latency_and_coverage",
        },
    }


def geox_price_observe_spglobal(
    commodity: str = "brent",
    assessment_date: str | None = None,
    api_key: str | None = None,
    currency: str = "USD",
) -> dict[str, Any]:
    """
    Observe S&P Global Platts benchmark price assessment.

    Args:
        commodity: Benchmark code — "brent", "wti", "henry_hub", "lng_jkm", etc.
        assessment_date: YYYY-MM-DD (defaults to latest available).
        api_key: Optional override for SPGLOBAL_API_KEY.
        currency: Price currency (default USD).

    Returns:
        Canonical GEOX dict with price, claim_tag, provenance.
    """
    client = SPGlobalClient(api_key=api_key)
    try:
        result = asyncio.run(
            client.fetch_price_assessment(
                commodity=commodity,
                assessment_date=assessment_date,
                currency=currency,
            )
        )
    except Exception as exc:
        logger.exception("geox_price_observe_spglobal failed")
        return {
            "commodity": commodity,
            "status": "error",
            "claim_tag": ClaimTag.VOID.value,
            "error": str(exc),
            "vault_receipt": _make_vault_receipt("geox_price_observe_spglobal", {"commodity": commodity}, "VOID"),
            "limitations": ["Client exception — check network and API key"],
            "governance": {"f1_amanah": "read_only", "f2_truth": "source_unavailable"},
        }

    claim_tag = _determine_claim_tag(result)
    verdict = "SEAL" if claim_tag == ClaimTag.OBSERVED.value else "HOLD"
    payload = {"commodity": commodity, "assessment_date": assessment_date, "currency": currency}

    return {
        "commodity": commodity,
        "status": "loaded" if claim_tag == ClaimTag.OBSERVED.value else "void",
        "claim_tag": claim_tag,
        "provenance": _build_provenance(result),
        "price": result.get("price", {}),
        "spg_error": result.get("_spg_error", False),
        "spg_status": result.get("_spg_status"),
        "vault_receipt": _make_vault_receipt("geox_price_observe_spglobal", payload, verdict),
        "limitations": _build_limitations(result, "price"),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "sp_global_api",
            "f7_humility": "assessment_based_not_transaction",
        },
    }


def geox_production_observe_spglobal(
    well_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Observe monthly production volumes for a well from S&P Global.

    Args:
        well_id: S&P Global well identifier or UWI.
        start_date: Optional YYYY-MM-DD filter.
        end_date: Optional YYYY-MM-DD filter.
        api_key: Optional override for SPGLOBAL_API_KEY.

    Returns:
        Canonical GEOX dict with production records, claim_tag, provenance.
    """
    client = SPGlobalClient(api_key=api_key)
    try:
        result = asyncio.run(
            client.fetch_well_production(
                well_id=well_id,
                start_date=start_date,
                end_date=end_date,
            )
        )
    except Exception as exc:
        logger.exception("geox_production_observe_spglobal failed")
        return {
            "well_id": well_id,
            "status": "error",
            "claim_tag": ClaimTag.VOID.value,
            "error": str(exc),
            "vault_receipt": _make_vault_receipt("geox_production_observe_spglobal", {"well_id": well_id}, "VOID"),
            "limitations": ["Client exception — check network and API key"],
            "governance": {"f1_amanah": "read_only", "f2_truth": "source_unavailable"},
        }

    claim_tag = _determine_claim_tag(result)
    verdict = "SEAL" if claim_tag == ClaimTag.OBSERVED.value else "HOLD"
    payload = {"well_id": well_id, "start_date": start_date, "end_date": end_date}

    return {
        "well_id": well_id,
        "status": "loaded" if claim_tag == ClaimTag.OBSERVED.value else "void",
        "claim_tag": claim_tag,
        "provenance": _build_provenance(result),
        "production": result.get("production", []),
        "spg_error": result.get("_spg_error", False),
        "spg_status": result.get("_spg_status"),
        "vault_receipt": _make_vault_receipt("geox_production_observe_spglobal", payload, verdict),
        "limitations": _build_limitations(result, "production"),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "sp_global_api",
            "f7_humility": "vendor_latency_and_coverage",
        },
    }
