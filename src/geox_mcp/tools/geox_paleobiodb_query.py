"""
geox_paleobiodb_query.py — Public-facing GEOX tool wrapper around PBDBClient.

DITEMPA BUKAN DIBERI — Forged, Not Given.

Adds:
- TTL cache layer to be a good PBDB citizen (anonymous tier = ~10 req/s, throttled beyond).
- Unified envelope: BiostratEnvelope (status / data / evidence / confidence / sources / warnings).
- Modes: taxa | occurrence | zone | age_intervals.
- Read-only. No F13 permit required. action_class=OBSERVE.

Substrate already exists at geox_mcp/tools/biostrat/taxonomy.py (PBDBClient).
This module is the thin "GEOX surface" that the public tool wires to.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Literal

from geox_mcp.tools.biostrat.taxonomy import PBDBClient
from geox_mcp.tools.biostrat.schemas import BiostratEnvelope

logger = logging.getLogger(__name__)

# ── TTL Cache ────────────────────────────────────────────────────────────────
# PBDB anonymous rate limit is ~10 req/s sustained, throttled sharply above that.
# Cache layer keyed on (mode, params_hash) with default 24h TTL.
# Cache lives in-process only — restart wipes it. That's acceptable; PBDB results
# are stable and idempotent.

_CACHE_TTL_SECONDS = 86_400  # 24h
_CACHE_MAX_ENTRIES = 512

_cache: dict[str, tuple[float, Any]] = {}


def _cache_get(key: str) -> Any | None:
    if key not in _cache:
        return None
    ts, val = _cache[key]
    if time.time() - ts > _CACHE_TTL_SECONDS:
        del _cache[key]
        return None
    return val


def _cache_set(key: str, val: Any) -> None:
    if len(_cache) >= _CACHE_MAX_ENTRIES:
        # evict oldest
        oldest = min(_cache.items(), key=lambda kv: kv[1][0])
        _cache.pop(oldest[0], None)
    _cache[key] = (time.time(), val)


def _cache_key(mode: str, params: dict[str, Any]) -> str:
    return f"{mode}::{json.dumps(params, sort_keys=True, default=str)}"


# ── Mode dispatch ────────────────────────────────────────────────────────────

Mode = Literal["taxa", "occurrence", "zone", "age_intervals"]


async def _mode_taxa(
    client: PBDBClient,
    name: str,
    rank: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Resolve a taxon name against PBDB taxonomy.

    Returns TaxonRecord-shaped dict with pbdb_oid, accepted_name, first/last
    occurrence (Ma), n_occurrences, and provenance="PBDB".
    """
    # Prefer exact match; fall back to autocomplete → best match
    rec = await client.taxa_get(name)
    if rec is None:
        autos = await client.taxa_autocomplete(name, limit=limit)
        if not autos:
            return {
                "matched": False,
                "query": name,
                "suggestions": [],
            }
        # Take the autocomplete top hit and re-resolve
        top = autos[0]
        rec = await client.taxa_get(top.get("nam", name))

    if rec is None:
        return {
            "matched": False,
            "query": name,
            "suggestions": [a.get("nam") for a in autos] if autos else [],
        }

    return {
        "matched": True,
        "taxon": rec.model_dump(),
        "query": name,
    }


async def _mode_occurrence(
    client: PBDBClient,
    taxon: str,
    interval: str | None = None,
    cc: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """List fossil occurrences for a taxon.

    Filters: interval (e.g. 'Miocene', 'Cretaceous'), cc (ISO country code, e.g. 'MY').
    """
    rows = await client.occs_list(
        base_name=taxon,
        interval=interval,
        cc=cc,
        limit=limit,
    )
    return {
        "query": taxon,
        "filters": {"interval": interval, "cc": cc, "limit": limit},
        "count": len(rows),
        "occurrences": rows,
    }


async def _mode_zone(
    client: PBDBClient,
    fossil_group: str = "calcareous_nannofossil",
) -> dict[str, Any]:
    """Get biozone catalogue for a fossil group.

    fossil_group ∈ {calcareous_nannofossil, planktonic_foram}
      calcareous_nannofossil → PBDB scale=5 (NN/NP zones)
      planktonic_foram       → PBDB scale=24 (Blow/Wade foram zones)
    """
    if fossil_group == "calcareous_nannofossil":
        rows = await client.get_nannoplankton_zones()
        scale_used = 5
    elif fossil_group == "planktonic_foram":
        rows = await client.get_foram_zones()
        scale_used = 24
    else:
        return {
            "error": f"unsupported fossil_group: {fossil_group}",
            "supported": ["calcareous_nannofossil", "planktonic_foram"],
        }

    return {
        "fossil_group": fossil_group,
        "pbdb_scale": scale_used,
        "count": len(rows),
        "zones": rows,
    }


async def _mode_age_intervals(client: PBDBClient) -> dict[str, Any]:
    """Get ICS international chronostratigraphic ages from PBDB (scale=1).

    Eons → eras → periods → epochs → ages. Single canonical ladder.
    """
    rows = await client.get_ics_intervals()
    return {
        "scale": 1,
        "scheme": "ICS",
        "count": len(rows),
        "intervals": rows,
    }


# ── Public tool entry ───────────────────────────────────────────────────────


async def geox_paleobiodb_query(
    mode: str = "taxa",
    name: str = "",
    taxon: str = "",
    rank: str | None = None,
    interval: str | None = None,
    cc: str | None = None,
    fossil_group: str = "calcareous_nannofossil",
    limit: int = 50,
) -> dict[str, Any]:
    """Public GEOX tool: query the Paleobiology Database (PBDB v1.2).

    Args:
        mode: One of {taxa, occurrence, zone, age_intervals}.
        name: For mode=taxa — taxon name to resolve (e.g. "Emiliania huxleyi").
        taxon: For mode=occurrence — taxon name whose occurrences to list.
        rank: For mode=taxa — optional rank filter (genus, species, family, ...).
        interval: For mode=occurrence — geologic time filter (Miocene, Cretaceous, ...).
        cc: For mode=occurrence — ISO country code (MY, US, ID, ...).
        fossil_group: For mode=zone — calcareous_nannofossil | planktonic_foram.
        limit: Max records (default 50).

    Returns:
        BiostratEnvelope-shaped dict. status=ok|partial|error.
    """
    # Param normalisation: tools_wiring may pass `name=` or `taxon=` for taxa.
    if mode == "taxa" and not name and taxon:
        name = taxon

    if mode not in ("taxa", "occurrence", "zone", "age_intervals"):
        return BiostratEnvelope(
            status="error",
            tool="geox_paleobiodb_query",
            data={"mode": mode},
            confidence=0.0,
            sources=[],
            warnings=[f"unknown mode: {mode}"],
            provenance="GEOX · PBDB substrate",
        ).model_dump()

    cache_params = {
        "name": name, "taxon": taxon, "rank": rank,
        "interval": interval, "cc": cc, "fossil_group": fossil_group,
        "limit": limit,
    }
    key = _cache_key(mode, cache_params)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    client = PBDBClient()
    try:
        warnings: list[str] = []

        if mode == "taxa":
            if not name:
                return BiostratEnvelope(
                    status="error",
                    tool="geox_paleobiodb_query",
                    data={"hint": "mode=taxa requires `name`"},
                    confidence=0.0,
                    warnings=["missing parameter: name"],
                    provenance="GEOX · PBDB substrate",
                ).model_dump()
            data = await _mode_taxa(client, name, rank=rank, limit=limit)

        elif mode == "occurrence":
            taxon_name = taxon or name
            if not taxon_name:
                return BiostratEnvelope(
                    status="error",
                    tool="geox_paleobiodb_query",
                    data={"hint": "mode=occurrence requires `taxon`"},
                    confidence=0.0,
                    warnings=["missing parameter: taxon"],
                    provenance="GEOX · PBDB substrate",
                ).model_dump()
            data = await _mode_occurrence(client, taxon_name, interval=interval, cc=cc, limit=limit)
            if data["count"] == 0:
                warnings.append(f"no occurrences found for {taxon_name} with given filters")

        elif mode == "zone":
            data = await _mode_zone(client, fossil_group=fossil_group)
            if "error" in data:
                warnings.append(data["error"])

        else:  # age_intervals
            data = await _mode_age_intervals(client)

        status = "partial" if warnings else "ok"
        envelope = BiostratEnvelope(
            status=status,
            tool="geox_paleobiodb_query",
            data=data,
            evidence=[{"uri": "https://paleobiodb.org/data1.2", "role": "primary"}],
            confidence=0.85 if status == "ok" else 0.5,
            epistemic_label="OBS",
            sources=["https://paleobiodb.org/data1.2"],
            warnings=warnings,
            provenance="GEOX · PBDB substrate",
        )
        result = envelope.model_dump()
        _cache_set(key, result)
        return result
    except Exception as e:
        logger.warning("PBDB query failed: mode=%s err=%s", mode, e)
        return BiostratEnvelope(
            status="error",
            tool="geox_paleobiodb_query",
            data={"mode": mode, "exception_type": type(e).__name__},
            confidence=0.0,
            sources=["https://paleobiodb.org/data1.2"],
            warnings=[f"PBDB request failed: {type(e).__name__}"],
            provenance="GEOX · PBDB substrate",
        ).model_dump()
    finally:
        await client.close()
