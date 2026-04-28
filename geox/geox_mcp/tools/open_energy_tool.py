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
    return ClaimTag.VOID.value if error else ClaimTag.OBSERVED.value


def _build_limitations(source: str, data_type: str, error: bool, error_detail: str | None = None) -> list[str]:
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
    """
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
        return {
            "commodity": commodity,
            "status": "error",
            "claim_tag": ClaimTag.VOID.value,
            "error": str(exc),
            "vault_receipt": _make_vault_receipt("geox_price_observe_eia", {"commodity": commodity}, "VOID"),
            "limitations": ["Client exception — check network and EIA_API_KEY"],
            "governance": {"f1_amanah": "read_only", "f2_truth": "source_unavailable"},
        }

    error = result.get("_eia_error", False)
    claim_tag = _determine_claim_tag(error)
    verdict = "SEAL" if claim_tag == ClaimTag.OBSERVED.value else "HOLD"
    payload = {"commodity": commodity, "frequency": frequency, "start": start, "end": end}

    return {
        "commodity": commodity,
        "status": "loaded" if not error else "void",
        "claim_tag": claim_tag,
        "provenance": result.get("_eia_provenance", {}),
        "prices": result.get("prices", []),
        "eia_error": error,
        "eia_status": result.get("_eia_status"),
        "vault_receipt": _make_vault_receipt("geox_price_observe_eia", payload, verdict),
        "limitations": _build_limitations("eia", "price", error, result.get("_eia_detail")),
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
    """
    client = EIAClient(api_key=api_key)
    try:
        if data_type == "crude_oil":
            result = asyncio.run(
                client.fetch_crude_production(area=area, frequency=frequency, start=start, end=end)
            )
        else:
            result = asyncio.run(
                client.fetch_natural_gas_production(area=area, frequency=frequency, start=start, end=end)
            )
    except Exception as exc:
        logger.exception("geox_production_observe_eia failed")
        return {
            "data_type": data_type,
            "area": area,
            "status": "error",
            "claim_tag": ClaimTag.VOID.value,
            "error": str(exc),
            "vault_receipt": _make_vault_receipt("geox_production_observe_eia", {"data_type": data_type, "area": area}, "VOID"),
            "limitations": ["Client exception — check network and EIA_API_KEY"],
            "governance": {"f1_amanah": "read_only", "f2_truth": "source_unavailable"},
        }

    error = result.get("_eia_error", False)
    claim_tag = _determine_claim_tag(error)
    verdict = "SEAL" if claim_tag == ClaimTag.OBSERVED.value else "HOLD"
    payload = {"data_type": data_type, "area": area, "frequency": frequency}

    return {
        "data_type": data_type,
        "area": area,
        "status": "loaded" if not error else "void",
        "claim_tag": claim_tag,
        "provenance": result.get("_eia_provenance", {}),
        "production": result.get("production", []),
        "eia_error": error,
        "eia_status": result.get("_eia_status"),
        "vault_receipt": _make_vault_receipt("geox_production_observe_eia", payload, verdict),
        "limitations": _build_limitations("eia", "production", error, result.get("_eia_detail")),
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
    """
    client = NPDClient()
    try:
        if well_name:
            result = asyncio.run(client.search_wellbore_by_name(well_name))
        else:
            # Return a sample of recent exploration wellbores (first 50)
            res = asyncio.run(client.fetch_wellbores_exploration())
            if "_npd_error" in res:
                result = res
            else:
                rows = res.get("_npd_data", [])[:50]
                result = {
                    "query": "*",
                    "count": len(rows),
                    "wellbores": [{"source": "wellbore_exploration", **r} for r in rows],
                    "_npd_provenance": res.get("_npd_provenance", {}),
                }
    except Exception as exc:
        logger.exception("geox_well_load_npd failed")
        return {
            "well_name": well_name,
            "status": "error",
            "claim_tag": ClaimTag.VOID.value,
            "error": str(exc),
            "vault_receipt": _make_vault_receipt("geox_well_load_npd", {"well_name": well_name}, "VOID"),
            "limitations": ["Client exception — check network connectivity to NPD"],
            "governance": {"f1_amanah": "read_only", "f2_truth": "source_unavailable"},
        }

    error = result.get("_npd_error", False)
    claim_tag = _determine_claim_tag(error)
    verdict = "SEAL" if claim_tag == ClaimTag.OBSERVED.value else "HOLD"
    payload = {"well_name": well_name, "include_production": include_production}

    return {
        "well_name": well_name,
        "status": "loaded" if not error else "void",
        "claim_tag": claim_tag,
        "provenance": result.get("_npd_provenance", {}),
        "wellbores": result.get("wellbores", []),
        "count": result.get("count", 0),
        "npd_error": error,
        "npd_status": result.get("_npd_status"),
        "vault_receipt": _make_vault_receipt("geox_well_load_npd", payload, verdict),
        "limitations": _build_limitations("npd", "well", error, result.get("_npd_detail")),
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
    """
    client = NPDClient()
    try:
        fields_res = asyncio.run(client.fetch_fields())
        if "_npd_error" in fields_res:
            return {
                "field_name": field_name,
                "status": "error",
                "claim_tag": ClaimTag.VOID.value,
                "npd_error": True,
                "npd_status": fields_res.get("_npd_status"),
                "vault_receipt": _make_vault_receipt("geox_field_observe_npd", {"field_name": field_name}, "VOID"),
                "limitations": _build_limitations("npd", "field", True, fields_res.get("_npd_detail")),
                "governance": {"f1_amanah": "read_only", "f2_truth": "npd_norway_public"},
            }

        all_fields = fields_res.get("_npd_data", [])
        if field_name:
            matched = [
                f for f in all_fields
                if field_name.lower() in str(f.get("fldName") or f.get("Field") or f.get("name", "")).lower()
            ]
        else:
            matched = all_fields[:100]  # cap at 100 if no filter

        production = []
        if include_production and matched:
            # Fetch production and filter for the first matched field
            first_name = str(matched[0].get("fldName") or matched[0].get("Field") or matched[0].get("name", ""))
            prod_res = asyncio.run(client.get_field_production(first_name))
            if "_npd_error" not in prod_res:
                production = prod_res.get("production", [])

    except Exception as exc:
        logger.exception("geox_field_observe_npd failed")
        return {
            "field_name": field_name,
            "status": "error",
            "claim_tag": ClaimTag.VOID.value,
            "error": str(exc),
            "vault_receipt": _make_vault_receipt("geox_field_observe_npd", {"field_name": field_name}, "VOID"),
            "limitations": ["Client exception — check network connectivity to NPD"],
            "governance": {"f1_amanah": "read_only", "f2_truth": "source_unavailable"},
        }

    payload = {"field_name": field_name, "include_production": include_production}
    return {
        "field_name": field_name,
        "status": "loaded",
        "claim_tag": ClaimTag.OBSERVED.value,
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
    """
    client = NPDClient()
    try:
        result = asyncio.run(client.get_field_production(field_name))
    except Exception as exc:
        logger.exception("geox_production_observe_npd failed")
        return {
            "field_name": field_name,
            "status": "error",
            "claim_tag": ClaimTag.VOID.value,
            "error": str(exc),
            "vault_receipt": _make_vault_receipt("geox_production_observe_npd", {"field_name": field_name}, "VOID"),
            "limitations": ["Client exception — check network connectivity to NPD"],
            "governance": {"f1_amanah": "read_only", "f2_truth": "source_unavailable"},
        }

    error = result.get("_npd_error", False)
    claim_tag = _determine_claim_tag(error)
    verdict = "SEAL" if claim_tag == ClaimTag.OBSERVED.value else "HOLD"
    payload = {"field_name": field_name}

    return {
        "field_name": field_name,
        "status": "loaded" if not error else "void",
        "claim_tag": claim_tag,
        "provenance": result.get("_npd_provenance", {}),
        "production": result.get("production", []),
        "count": result.get("count", 0),
        "npd_error": error,
        "npd_status": result.get("_npd_status"),
        "vault_receipt": _make_vault_receipt("geox_production_observe_npd", payload, verdict),
        "limitations": _build_limitations("npd", "production", error, result.get("_npd_detail")),
        "governance": {
            "f1_amanah": "read_only",
            "f2_truth": "npd_norway_public",
            "f7_humility": "allocated_monthly_production_may_be_revised",
        },
    }
