"""
GEOX EGS→Map Provenance Bridge
=================================
Phase 2.4 (2026-07-02): Auto-populate map provenance from Earth Graph System.

Every map render and export now optionally enriches provenance by consulting
the EGS (Earth Graph System) for layer-level claim, entity, and uncertainty
records.

Architecture:
  geox_map_render_preview → checks EGS for each layer's claim/entity data
  geox_map_export_package  → embeds EGS-enriched provenance in PROV sidecar

EGS data populated via:
  geox_egs_claim_create — when a layer is registered as a geological claim
  geox_egs_evidence_attach — when evidence is bound to a layer claim
  geox_egs_query_provenance — queried by this bridge for enrichment

F2 TRUTH: If EGS has no data for a layer, bridge returns empty enrichment.
           Never fabricates provenance.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox.provenance_bridge")

# ── In-memory EGS cache (populated by geox_egs tools at runtime) ─────────────
# In production this would be a DB/Redis lookup.
# For now, matches the in-memory pattern in /root/GEOX/src/geox/egs/tools/query.py
_EGS_GRAPH: dict[str, dict[str, Any]] = {}
_EGS_CLAIMS: dict[str, dict[str, Any]] = {}
_EGS_PROVENANCE: dict[str, dict[str, Any]] = {}


def register_provenance(layer_id: str, prov_record: dict[str, Any]) -> None:
    """Register a provenance record for a layer (called by EGS tools at runtime)."""
    _EGS_PROVENANCE[layer_id] = prov_record


def register_claim(layer_id: str, claim_record: dict[str, Any]) -> None:
    """Register a claim for a layer."""
    _EGS_CLAIMS[layer_id] = claim_record


def register_entity(layer_id: str, entity_record: dict[str, Any]) -> None:
    """Register an entity for a layer."""
    _EGS_GRAPH[layer_id] = entity_record


async def enrich_layer_provenance(layer_id: str) -> dict[str, Any]:
    """Enrich a layer's provenance by consulting EGS.

    Returns enriched metadata if EGS has records, otherwise empty dict.
    Called by geox_map_render_preview and geox_map_export_package.
    """
    result: dict[str, Any] = {"layer_id": layer_id}

    claim = _EGS_CLAIMS.get(layer_id)
    if claim:
        result["claim_id"] = claim.get("id", "unknown")
        result["claim_status"] = claim.get("status", "unknown")
        result["claim_statement"] = claim.get("statement", "")

    entity = _EGS_GRAPH.get(layer_id)
    if entity:
        result["entity_type"] = entity.get("entity_type", "unknown")
        result["entity_name"] = entity.get("name", layer_id)
        result["entity_confidence"] = entity.get("confidence_score")

    prov = _EGS_PROVENANCE.get(layer_id)
    if prov:
        result["provenance_chain"] = prov.get("chain", [])
        result["provenance_source"] = prov.get("source", "unknown")

    return result


async def enrich_batch_provenance(layer_ids: list[str]) -> list[dict[str, Any]]:
    """Enrich provenance for multiple layers at once.

    Used by geox_map_export_package to build enriched PROV sidecar.
    Gracefully degrades: layers without EGS data return minimal records.
    """
    results = []
    for lid in layer_ids:
        enriched = await enrich_layer_provenance(lid)
        results.append(enriched)
    return results


def provenance_coverage(layer_ids: list[str]) -> dict[str, Any]:
    """Report what fraction of layers have EGS provenance coverage.

    Returns coverage stats for logging and QA gating.
    """
    total = len(layer_ids)
    if total == 0:
        return {"coverage_pct": 0.0, "covered": 0, "total": 0}

    covered = sum(1 for lid in layer_ids if lid in _EGS_PROVENANCE or lid in _EGS_CLAIMS)
    return {
        "coverage_pct": round(covered / total * 100, 1),
        "covered": covered,
        "total": total,
    }
