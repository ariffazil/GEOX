"""
geox/geox_mcp/tools/open_energy_tool.py — Free/Open Energy Data Tool Surface
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

GEOX public mission surface for FREE energy & subsurface data sources:
  • EIA (U.S. Energy Information Administration) — prices, production, reserves
  • NPD (Norwegian Offshore Directorate) — wellbores, fields, production, facilities

No enterprise contracts. No paywalls. EIA requires free registration; NPD is
completely open with zero authentication.

Constitutional:
  F1 AMANAH  — read-only
  F2 TRUTH   — government/public data with full provenance
  F7 HUMILITY — explicit data limitations and revision notes
  F9 ANTI-HANTU — no synthetic data passed as observed truth
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from geox.services.eia_client import EIAClient
from geox.services.npd_client import NPDClient
from geox.skills.earth_science.seismic_wrappers import ClaimTag

logger = logging.getLogger("geox.tools.open_energy")


# ══════════════════════════════════════════════════════════════════════════════
# Vault receipt helper
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
# Shared helpers
# ══════════════════════════════════════════════════════════════════════════════


def _determine_claim_tag(error: bool) -> str:
    return ClaimTag.UNKNOWN.value if error else ClaimTag.OBSERVED.value


def _build_limitations(
    source: str, data_type: str, error: bool, error_detail: str | None = None
) -> list[str]:
    limitations: list[str] = []
    if source == "eia":
        limitations.append("EIA data is U.S.-centric; global coverage is limited to select benchmarks")
        limitations.append("Production data is survey-based and subject to revision")
        if data_type == "price":
            limitations.append("Spot prices reflect survey averages, not individual transactions")
    elif source == "npd":
        limitations.append("NPD data covers Norwegian Continental Shelf only")
        limitations.append("Well data reflects public reporting; confidential wells are excluded")
        if data_type == "production":
            limitations.append("Monthly production is allocated and may be revised")
    if error and error_detail:
        limitations.append(f"API error: {error_detail}")
    return limitations


# ══════════════════════════════════════════════════════════════════════════════
# Structured error schema (M5)
# ══════════════════════════════════════════════════════════════════════════════
#
# Every failure path in this module emits exactly one of these shapes:
#
#   {"error": "upstream_unavailable", "source": "npd.no", "retry_hint": "later"}
#   {"error": "bad_request",          "source": "eia.gov", "http_status": 400, "details": "..."}
#   {"error": "config_missing",       "source": "eia.gov", "details": "EIA_API_KEY not set"}
#   {"error": "timeout",              "source": "npd.no",  "retry_hint": "later"}
#   {"error": "unsupported_query",    "source": "npd.no",  "details": "..."}
#
# The tool wrapper (_wrap_tool_error) adds claim_tag, vault_receipt, limitations,
# governance, data_origin=None, and any context fields (commodity, field_name, etc.).


def _build_structured_error(
    error_code: str,
    source: str,
    http_status: int | None = None,
    details: str | None = None,
    retry_hint: str | None = None,
) -> dict[str, Any]:
    """Return a minimal, machine-parseable error descriptor."""
    err: dict[str, Any] = {"error": error_code, "source": source, "data_origin": None}
    if http_status is not None:
        err["http_status"] = http_status
    if details:
        err["details"] = details[:300]
    if retry_hint:
        err["retry_hint"] = retry_hint
    return err


def _eia_client_error_to_schema(client_result: dict[str, Any]) -> dict[str, Any]:
    """Map EIA client error dict (_eia_* keys) to canonical structured error."""
    status = client_result.get("_eia_status", 0)
    detail = str(client_result.get("_eia_detail", ""))
    if status == 401 or "missing_api_key" in detail:
        return _build_structured_error(
            "config_missing",
            "eia.gov",
            http_status=status,
            details="EIA_API_KEY not configured — register free at https://www.eia.gov/opendata/",
        )
    if status == 0:
        return _build_structured_error(
            "upstream_unavailable", "eia.gov", details=detail or None, retry_hint="later"
        )
    try:
        status_int = int(status)
    except (TypeError, ValueError):
        status_int = 0
    if 400 <= status_int < 500:
        return _build_structured_error(
            "bad_request", "eia.gov", http_status=status_int, details=detail or None
        )
    return _build_structured_error(
        "upstream_unavailable", "eia.gov", http_status=status_int or None, retry_hint="later"
    )


def _npd_client_error_to_schema(client_result: dict[str, Any]) -> dict[str, Any]:
    """Map NPD client error dict (_npd_* keys) to canonical structured error."""
    status = client_result.get("_npd_status", 0)
    detail = str(client_result.get("_npd_detail", ""))
    if "Unknown endpoint" in detail:
        return _build_structured_error("unsupported_query", "npd.no", details=detail)
    if status == 0:
        return _build_structured_error(
            "upstream_unavailable", "npd.no", details=detail or None, retry_hint="later"
        )
    try:
        status_int = int(status)
    except (TypeError, ValueError):
        status_int = 0
    if 400 <= status_int < 500:
        return _build_structured_error(
            "bad_request", "npd.no", http_status=status_int, details=detail or None
        )
    return _build_structured_error(
        "upstream_unavailable", "npd.no", http_status=status_int or None, retry_hint="later"
    )


def _wrap_tool_error(
    error_schema: dict[str, Any],
    tool_name: str,
    context_fields: dict[str, Any],
    upstream_source: str,
    data_type: str,
) -> dict[str, Any]:
    """
    Attach GEOX canonical envelope (claim_tag, vault_receipt, limitations,
    governance) to a structured error payload.
    """
    result: dict[str, Any] = {
        **context_fields,
        "status": "error",
        "claim_tag": ClaimTag.UNKNOWN.value,
        **error_schema,
    }
    result["vault_receipt"] = _make_vault_receipt(tool_name, context_fields, "VOID")
    result["limitations"] = _build_limitations(
        upstream_source, data_type, True, error_schema.get("details")
    )
    result["governance"] = {"f1_amanah": "read_only", "f2_truth": "source_unavailable"}
    return result


# ══════════════════════════════════════════════════════════════════════════════
# EIA Tools
# ══════════════════════════════════════════════════════════════════════════════


def geox_price_observe_eia(
    commodity: str = "wti",
    frequency: str = "daily",
    api_key: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """
    Observe petroleum spot prices from the FREE U.S. EIA API.

    Args:
        commodity: "wti", "brent", "gasoline", "diesel", "henry_hub_gas", "propane"
        frequency: "daily" | "weekly" | "monthly" | "annual"
        api_key: Optional override for EIA_API_KEY env var.
        start: Optional YYYY-MM-DD start date.
        end: Optional YYYY-MM-DD end date.

    Returns:
        Canonical GEOX dict with prices, claim_tag, provenance, vault_receipt.
        On failure: structured error object with error/source/details fields.
    """
    context = {"commodity": commodity, "frequency": frequency, "start": start, "end": end}
    client = EIAClient(api_key=api_key)
    try:
        result = asyncio.run(
            client.fetch_price_spot(
                commodity=commodity,
                frequency=frequency,
                start=start,
                end=end,
            )
        )
    except Exception as exc:
        logger.exception("geox_price_observe_eia failed")
        schema = _build_structured_error(
            "upstream_unavailable", "eia.gov", details=str(exc)[:300], retry_hint="later"
        )
        return _wrap_tool_error(schema, "geox_price_observe_eia", context, "eia", "price")

    if result.get("_eia_error"):
        schema = _eia_client_error_to_schema(result)
        return _wrap_tool_error(schema, "geox_price_observe_eia", context, "eia", "price")

    payload = context
    return {
        "commodity": commodity,
        "status": "loaded",
        "claim_tag": ClaimTag.OBSERVED.value,
        "data_origin": "OBSERVED",
        "provenance": result.get("_eia_provenance", {}),
        "prices": result.get("prices", []),
        "vault_receipt": _make_vault_receipt("geox_price_observe_eia", payload, "SEAL"),
        "limitations": _build_limitations("eia", "price", False),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "eia_gov_api",
            "f7_humility": "survey_based_subject_to_revision",
            "f9_antihantu": "no_synthetic_data",
        },
    }


def geox_production_observe_eia(
    data_type: str = "crude_oil",
    area: str = "US",
    frequency: str = "monthly",
    api_key: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """
    Observe U.S. production data from the FREE EIA API.

    Args:
        data_type: "crude_oil" or "natural_gas"
        area: "US" or state abbreviation (e.g. "TX", "ND")
        frequency: "monthly" | "annual"
        api_key: Optional EIA_API_KEY override.
        start: Optional YYYY-MM-DD.
        end: Optional YYYY-MM-DD.

    Returns:
        Canonical GEOX dict with production records.
        On failure: structured error object with error/source/details fields.
    """
    context = {"data_type": data_type, "area": area, "frequency": frequency}
    client = EIAClient(api_key=api_key)
    try:
        if data_type == "crude_oil":
            result = asyncio.run(
                client.fetch_crude_production(area=area, frequency=frequency, start=start, end=end)
            )
        else:
            result = asyncio.run(
                client.fetch_natural_gas_production(
                    area=area, frequency=frequency, start=start, end=end
                )
            )
    except Exception as exc:
        logger.exception("geox_production_observe_eia failed")
        schema = _build_structured_error(
            "upstream_unavailable", "eia.gov", details=str(exc)[:300], retry_hint="later"
        )
        return _wrap_tool_error(
            schema, "geox_production_observe_eia", context, "eia", "production"
        )

    if result.get("_eia_error"):
        schema = _eia_client_error_to_schema(result)
        return _wrap_tool_error(
            schema, "geox_production_observe_eia", context, "eia", "production"
        )

    payload = context
    return {
        "data_type": data_type,
        "area": area,
        "status": "loaded",
        "claim_tag": ClaimTag.OBSERVED.value,
        "data_origin": "OBSERVED",
        "provenance": result.get("_eia_provenance", {}),
        "production": result.get("production", []),
        "vault_receipt": _make_vault_receipt("geox_production_observe_eia", payload, "SEAL"),
        "limitations": _build_limitations("eia", "production", False),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "eia_gov_api",
            "f7_humility": "survey_based_subject_to_revision",
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# NPD Tools (NO API KEY REQUIRED)
# ══════════════════════════════════════════════════════════════════════════════


def geox_well_load_npd(
    well_name: str | None = None,
    include_production: bool = False,
) -> dict[str, Any]:
    """
    Load wellbore data from the FREE Norwegian Offshore Directorate (NPD).
    NO API KEY REQUIRED. NO REGISTRATION.

    Args:
        well_name: Optional wellbore name to search (case-insensitive substring).
        include_production: Whether to fetch field production context.

    Returns:
        Canonical GEOX dict with wellbore data, claim_tag, provenance.
        On failure: structured error object with error/source/details fields.
    """
    context = {"well_name": well_name, "include_production": include_production}
    client = NPDClient()
    try:
        if well_name:
            result = asyncio.run(client.search_wellbore_by_name(well_name))
        else:
            res = asyncio.run(client.fetch_wellbores_exploration())
            if res.get("_npd_error"):
                schema = _npd_client_error_to_schema(res)
                return _wrap_tool_error(schema, "geox_well_load_npd", context, "npd", "well")
            rows = res.get("_npd_data", [])[:50]
            result = {
                "query": "*",
                "count": len(rows),
                "wellbores": [{"source": "wellbore_exploration", **r} for r in rows],
                "_npd_provenance": res.get("_npd_provenance", {}),
            }
    except Exception as exc:
        logger.exception("geox_well_load_npd failed")
        schema = _build_structured_error(
            "upstream_unavailable", "npd.no", details=str(exc)[:300], retry_hint="later"
        )
        return _wrap_tool_error(schema, "geox_well_load_npd", context, "npd", "well")

    if result.get("_npd_error"):
        schema = _npd_client_error_to_schema(result)
        return _wrap_tool_error(schema, "geox_well_load_npd", context, "npd", "well")

    payload = context
    return {
        "well_name": well_name,
        "status": "loaded",
        "claim_tag": ClaimTag.OBSERVED.value,
        "data_origin": "OBSERVED",
        "provenance": result.get("_npd_provenance", {}),
        "wellbores": result.get("wellbores", []),
        "count": result.get("count", 0),
        "vault_receipt": _make_vault_receipt("geox_well_load_npd", payload, "SEAL"),
        "limitations": _build_limitations("npd", "well", False),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "npd_norway_public",
            "f7_humility": "ncs_coverage_only_confidential_excluded",
            "f9_antihantu": "no_synthetic_data",
        },
    }


def geox_field_observe_npd(
    field_name: str | None = None,
    include_production: bool = False,
) -> dict[str, Any]:
    """
    Observe field data from the FREE Norwegian Offshore Directorate (NPD).
    NO API KEY REQUIRED.

    Args:
        field_name: Optional field name filter.
        include_production: Whether to include monthly production records.

    Returns:
        Canonical GEOX dict with field summaries and optional production.
        On failure: structured error object with error/source/details fields.
    """
    context = {"field_name": field_name, "include_production": include_production}
    client = NPDClient()
    try:
        fields_res = asyncio.run(client.fetch_fields())
        if fields_res.get("_npd_error"):
            schema = _npd_client_error_to_schema(fields_res)
            return _wrap_tool_error(schema, "geox_field_observe_npd", context, "npd", "field")

        all_fields = fields_res.get("_npd_data", [])
        if field_name:
            matched = [
                f
                for f in all_fields
                if field_name.lower()
                in str(
                    f.get("fldName") or f.get("Field") or f.get("name", "")
                ).lower()
            ]
        else:
            matched = all_fields[:100]

        production = []
        if include_production and matched:
            first_name = str(
                matched[0].get("fldName")
                or matched[0].get("Field")
                or matched[0].get("name", "")
            )
            prod_res = asyncio.run(client.get_field_production(first_name))
            if not prod_res.get("_npd_error"):
                production = prod_res.get("production", [])

    except Exception as exc:
        logger.exception("geox_field_observe_npd failed")
        schema = _build_structured_error(
            "upstream_unavailable", "npd.no", details=str(exc)[:300], retry_hint="later"
        )
        return _wrap_tool_error(schema, "geox_field_observe_npd", context, "npd", "field")

    payload = context
    return {
        "field_name": field_name,
        "status": "loaded",
        "claim_tag": ClaimTag.OBSERVED.value,
        "data_origin": "OBSERVED",
        "provenance": fields_res.get("_npd_provenance", {}),
        "fields": matched,
        "count": len(matched),
        "production": production,
        "vault_receipt": _make_vault_receipt("geox_field_observe_npd", payload, "SEAL"),
        "limitations": _build_limitations("npd", "field", False),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "npd_norway_public",
            "f7_humility": "ncs_coverage_only",
            "f9_antihantu": "no_synthetic_data",
        },
    }


def geox_production_observe_npd(
    field_name: str,
) -> dict[str, Any]:
    """
    Observe monthly production for a specific field from NPD.
    NO API KEY REQUIRED.

    Args:
        field_name: Field name (e.g. "STATFJORD", "GULLFAKS").

    Returns:
        Canonical GEOX dict with monthly production records.
        On failure: structured error object with error/source/details fields.
    """
    context = {"field_name": field_name}
    client = NPDClient()
    try:
        result = asyncio.run(client.get_field_production(field_name))
    except Exception as exc:
        logger.exception("geox_production_observe_npd failed")
        schema = _build_structured_error(
            "upstream_unavailable", "npd.no", details=str(exc)[:300], retry_hint="later"
        )
        return _wrap_tool_error(
            schema, "geox_production_observe_npd", context, "npd", "production"
        )

    if result.get("_npd_error"):
        schema = _npd_client_error_to_schema(result)
        return _wrap_tool_error(
            schema, "geox_production_observe_npd", context, "npd", "production"
        )

    payload = context
    return {
        "field_name": field_name,
        "status": "loaded",
        "claim_tag": ClaimTag.OBSERVED.value,
        "data_origin": "OBSERVED",
        "provenance": result.get("_npd_provenance", {}),
        "production": result.get("production", []),
        "count": result.get("count", 0),
        "vault_receipt": _make_vault_receipt("geox_production_observe_npd", payload, "SEAL"),
        "limitations": _build_limitations("npd", "production", False),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "npd_norway_public",
            "f7_humility": "allocated_monthly_production_may_be_revised",
        },
    }
