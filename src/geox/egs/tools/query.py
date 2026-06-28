"""
query.py — EGS Query MCP Tools
================================
GEOX EGS: Structured query API for earth graph entities, claims, uncertainty, provenance.

Wired into existing geox_basin and geox_surface_status tools via mode expansion.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastmcp import FastMCP

from geox.egs.engines.geometry import bounding_box_contains, bounding_box_intersects, haversine_distance
from geox.egs.models.claims import ClaimEnvelope, ClaimStatus
from geox.egs.models.entities import EarthGraph
from geox.egs.models.provenance import ProvenanceChain
from geox.egs.models.uncertainty import UncertainValue

logger = logging.getLogger("geox.egs.tools.query")

# Global EGS state — the authoritative earth graph
# In production, this would be persisted to a database
_EGS_GRAPH: EarthGraph = EarthGraph()
_EGS_CLAIMS: dict[str, ClaimEnvelope] = {}
_EGS_PROVENANCE: dict[str, ProvenanceChain] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# State Accessors (for server.py integration)
# ═══════════════════════════════════════════════════════════════════════════════


def get_graph() -> EarthGraph:
    return _EGS_GRAPH


def get_claims() -> dict[str, ClaimEnvelope]:
    return _EGS_CLAIMS


def get_provenance() -> dict[str, ProvenanceChain]:
    return _EGS_PROVENANCE


# ═══════════════════════════════════════════════════════════════════════════════
# Query Tools
# ═══════════════════════════════════════════════════════════════════════════════


async def egs_query_entity(
    entity_id: str | None = None,
    entity_type: str | None = None,
    name_contains: str | None = None,
    bbox: list[float] | None = None,
    active_only: bool = True,
    limit: int = 100,
) -> dict[str, Any]:
    """Query earth graph entities.

    OBS — Pure query, no mutation. Read-only.
    Returns serialized entity summaries.
    """
    graph = _EGS_GRAPH
    results: list[dict[str, Any]] = []

    collections: dict[str, dict] = {
        "basin": graph.basins,
        "play": graph.plays,
        "strat_unit": graph.strat_units,
        "horizon": graph.horizons,
        "fault": graph.faults,
        "volume": graph.volumes,
        "well": graph.wells,
        "survey": graph.surveys,
    }

    for etype, coll in collections.items():
        if entity_type and etype != entity_type:
            continue
        for eid, entity in coll.items():
            if active_only and not entity.active:
                continue
            if entity_id and eid != entity_id:
                continue
            if name_contains and name_contains.lower() not in entity.name.lower():
                continue
            if bbox and hasattr(entity, "bounding_box") and entity.bounding_box:
                # Check if entity bbox overlaps query bbox
                e_bbox = entity.bounding_box
                q_bbox = (bbox[0], bbox[1], bbox[2], bbox[3])
                if not bounding_box_intersects(e_bbox, q_bbox):
                    continue

            results.append(
                {
                    "id": eid,
                    "name": entity.name,
                    "entity_type": etype,
                    "description": entity.description[:200] if entity.description else "",
                    "version": entity.version,
                    "active": entity.active,
                    "tags": entity.tags,
                }
            )

            if len(results) >= limit:
                break
        if len(results) >= limit:
            break

    return {
        "success": True,
        "count": len(results),
        "results": results,
        "query": {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "name_contains": name_contains,
            "bbox": bbox,
            "active_only": active_only,
        },
    }


async def egs_query_claim(
    claim_id: str | None = None,
    status: str | None = None,
    domain: str | None = None,
    entity_id: str | None = None,
    author: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Query claim envelopes.

    OBS — Pure query, no mutation. Read-only.
    """
    results: list[dict[str, Any]] = []

    for cid, claim in _EGS_CLAIMS.items():
        if claim_id and cid != claim_id:
            continue
        if status and claim.status.value != status:
            continue
        if domain and claim.domain.value != domain:
            continue
        if entity_id and claim.entity_id != entity_id:
            continue
        if author and author.lower() not in claim.author.lower():
            continue

        results.append(
            {
                "id": cid,
                "title": claim.title,
                "statement": claim.statement[:300],
                "status": claim.status.value,
                "domain": claim.domain.value,
                "grade": claim.grade.value,
                "confidence_score": claim.confidence_score,
                "entity_type": claim.entity_type,
                "entity_id": claim.entity_id,
                "evidence_for": len(claim.evidence_for),
                "evidence_against": len(claim.evidence_against),
                "author": claim.author,
                "created_at": claim.created_at.isoformat(),
            }
        )

        if len(results) >= limit:
            break

    return {
        "success": True,
        "count": len(results),
        "results": results,
        "query": {"claim_id": claim_id, "status": status, "domain": domain},
    }


async def egs_query_uncertainty(
    entity_id: str,
    entity_type: str | None = None,
) -> dict[str, Any]:
    """Query uncertainty associated with an entity or claim.

    OBS — Pure query, no mutation.
    """
    # First check claims
    uncertainties: list[dict[str, Any]] = []
    for cid, claim in _EGS_CLAIMS.items():
        if claim.entity_id != entity_id:
            continue
        if entity_type and claim.entity_type != entity_type:
            continue
        if claim.uncertainty:
            u = claim.uncertainty
            uncertainties.append(
                {
                    "claim_id": cid,
                    "claim_title": claim.title,
                    "label": u.label,
                    "value": u.value,
                    "uncertainty_kind": u.uncertainty.kind.value,
                    "nature": u.nature.value,
                    "grade": u.grade.value,
                }
            )

    return {
        "success": True,
        "entity_id": entity_id,
        "uncertainty_count": len(uncertainties),
        "uncertainties": uncertainties,
    }


async def egs_query_provenance(
    entity_id: str,
    entity_type: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Query provenance history for an entity.

    OBS — Pure query, no mutation.
    """
    chain = _EGS_PROVENANCE.get(entity_id)
    if not chain:
        return {
            "success": True,
            "entity_id": entity_id,
            "records": [],
            "count": 0,
        }

    records = chain.get_history(limit=limit)
    return {
        "success": True,
        "entity_id": entity_id,
        "entity_type": chain.entity_type,
        "current_version": chain.current_version,
        "count": len(records),
        "records": [
            {
                "id": r.id,
                "action": r.action.value,
                "agent": r.agent,
                "agent_kind": r.agent_kind.value,
                "timestamp": r.timestamp.isoformat(),
                "description": r.description,
                "previous_version": r.previous_version,
                "new_version": r.new_version,
                "evidence_refs": r.evidence_refs,
            }
            for r in records
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Registry — returns tool definitions for server.py integration
# ═══════════════════════════════════════════════════════════════════════════════


EGS_QUERY_TOOLS: dict[str, dict[str, Any]] = {
    "egs_query_entity": {
        "description": "Query earth graph entities by type, name, bbox, or ID. Pure read-only query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Filter by entity ID"},
                "entity_type": {
                    "type": "string",
                    "enum": ["basin", "play", "strat_unit", "horizon", "fault", "volume", "well", "survey"],
                    "description": "Filter by entity type",
                },
                "name_contains": {"type": "string", "description": "Filter by name substring"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Spatial filter [min_lon, min_lat, max_lon, max_lat]",
                },
                "active_only": {"type": "boolean", "description": "Only active entities"},
                "limit": {"type": "integer", "description": "Max results"},
            },
            "additionalProperties": False,
        },
        "handler": egs_query_entity,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    "egs_query_claim": {
        "description": "Query claim envelopes by status, domain, entity, or author. Pure read-only query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": [s.value for s in ClaimStatus],
                    "description": "Filter by claim status",
                },
                "domain": {"type": "string", "description": "Filter by domain"},
                "entity_id": {"type": "string"},
                "author": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "additionalProperties": False,
        },
        "handler": egs_query_claim,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    "egs_query_uncertainty": {
        "description": "Query uncertainty associated with an entity or claim. Pure read-only query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Entity ID"},
                "entity_type": {"type": "string", "description": "Entity type filter"},
            },
            "required": ["entity_id"],
            "additionalProperties": False,
        },
        "handler": egs_query_uncertainty,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    "egs_query_provenance": {
        "description": "Query provenance history for an entity. Pure read-only query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Entity ID"},
                "entity_type": {"type": "string"},
                "limit": {"type": "integer", "description": "Max records"},
            },
            "required": ["entity_id"],
            "additionalProperties": False,
        },
        "handler": egs_query_provenance,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
}


def register_query_tools(mcp: FastMCP) -> None:
    """Register all EGS query tools with the FastMCP server."""
    for tool_name, tool_def in EGS_QUERY_TOOLS.items():
        mcp.tool(name=tool_name, description=tool_def["description"])(tool_def["handler"])
        logger.info(f"Registered EGS query tool: {tool_name}")
