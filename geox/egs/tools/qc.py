"""
qc.py — EGS QC MCP Tools
===========================
GEOX EGS: Data quality control tools for earth entities.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastmcp import FastMCP

from geox.egs.models.claims import ClaimEnvelope, ClaimStatus
from geox.egs.models.entities import EarthGraph
from geox.egs.models.provenance import EvidenceRef, ProvenanceAction, ProvenanceAgentKind, ProvenanceRecord
from geox.egs.tools.query import get_claims, get_graph, get_provenance
from geox.egs.models.uncertainty import ConfidenceGrade

logger = logging.getLogger("geox.egs.tools.qc")


# ═══════════════════════════════════════════════════════════════════════════════
# Quality Control
# ═══════════════════════════════════════════════════════════════════════════════


async def egs_data_qc_bundle(
    entity_type: str | None = None,
    entity_id: str | None = None,
    qc_mode: str = "completeness",
) -> dict[str, Any]:
    """Run quality control checks on earth entities.

    OBS — Read-only analysis. Does not modify state.
    """
    graph = get_graph()
    claims = get_claims()
    results: dict[str, Any] = {
        "qc_mode": qc_mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": [],
        "summary": {"passed": 0, "warnings": 0, "failed": 0},
    }

    if qc_mode == "completeness":
        # Check entity completeness
        entity_counts = {
            "basins": len(graph.basins),
            "plays": len(graph.plays),
            "strat_units": len(graph.strat_units),
            "horizons": len(graph.horizons),
            "faults": len(graph.faults),
            "volumes": len(graph.volumes),
            "wells": len(graph.wells),
            "surveys": len(graph.surveys),
        }

        results["entity_counts"] = entity_counts
        results["total_entities"] = sum(entity_counts.values())

        # Check for entities missing names
        unnamed = 0
        for coll in [
            graph.basins,
            graph.plays,
            graph.strat_units,
            graph.horizons,
            graph.faults,
            graph.volumes,
            graph.wells,
            graph.surveys,
        ]:
            unnamed += sum(1 for e in coll.values() if not e.name and e.active)
        results["unnamed_entities"] = unnamed
        results["checks"].append(
            {
                "check": "entity_names",
                "status": "warning" if unnamed > 0 else "passed",
                "detail": f"{unnamed} entities without names",
            }
        )

        # Check claims
        results["total_claims"] = len(claims)
        draft_claims = sum(1 for c in claims.values() if c.status == ClaimStatus.DRAFT)
        results["draft_claims"] = draft_claims

    elif qc_mode == "consistency":
        # Check for internal consistency issues
        issues: list[dict[str, Any]] = []

        # Check claims with no evidence
        for cid, claim in claims.items():
            total_evidence = len(claim.evidence_for) + len(claim.evidence_against)
            if total_evidence == 0 and claim.status not in (ClaimStatus.DRAFT, ClaimStatus.PROPOSED):
                issues.append(
                    {
                        "claim_id": cid,
                        "title": claim.title,
                        "issue": "Accepted/Sealed claim has no evidence",
                        "severity": "warning",
                    }
                )

            # Check claims with high confidence but poor evidence
            if claim.confidence_score > 0.8 and claim.grade in (
                ConfidenceGrade.D,
                ConfidenceGrade.INFERRED,
            ):
                issues.append(
                    {
                        "claim_id": cid,
                        "title": claim.title,
                        "issue": f"High confidence ({claim.confidence_score}) but low grade ({claim.grade.value})",
                        "severity": "warning",
                    }
                )

        results["issues"] = issues
        results["issue_count"] = len(issues)

    elif qc_mode == "provenance":
        # Check provenance completeness
        provenance_chains = get_provenance()
        entities_with_provenance = len(provenance_chains)

        # Count total provenance records
        total_records = sum(len(c.records) for c in provenance_chains.values())

        results["entities_with_provenance"] = entities_with_provenance
        results["total_provenance_records"] = total_records
        results["checks"].append(
            {
                "check": "provenance_coverage",
                "status": "passed" if entities_with_provenance > 0 else "warning",
                "detail": f"{entities_with_provenance} entities have provenance records",
            }
        )

    else:
        return {"success": False, "error": f"Unknown qc_mode: {qc_mode}", "recoverable": True}

    # Update summary
    for check in results.get("checks", []):
        if check["status"] == "passed":
            results["summary"]["passed"] += 1
        elif check["status"] == "warning":
            results["summary"]["warnings"] += 1
        elif check["status"] == "failed":
            results["summary"]["failed"] += 1

    results["success"] = True
    return results


async def egs_scenario_audit(
    entity_id: str | None = None,
    claim_id: str | None = None,
) -> dict[str, Any]:
    """Audit alternative scenarios / competing interpretations.

    OBS — Read-only analysis.
    """
    claims = get_claims()
    scenarios: list[dict[str, Any]] = []

    for cid, claim in claims.items():
        if entity_id and claim.entity_id != entity_id:
            continue
        if claim_id and cid != claim_id:
            continue
        if claim.alternative_scenarios:
            scenarios.append(
                {
                    "claim_id": cid,
                    "claim_title": claim.title,
                    "scenario_count": len(claim.alternative_scenarios.scenarios),
                    "scenarios": [
                        {
                            "name": s.name,
                            "probability": s.probability,
                            "description": s.description[:200],
                        }
                        for s in claim.alternative_scenarios.scenarios
                    ],
                }
            )

    return {
        "success": True,
        "entity_id": entity_id,
        "claim_id": claim_id,
        "claims_with_scenarios": len(scenarios),
        "scenarios": scenarios,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Registry
# ═══════════════════════════════════════════════════════════════════════════════


EGS_QC_TOOLS: dict[str, dict[str, Any]] = {
    "geox_egs_data_qc_bundle": {
        "description": "Run quality control checks on earth entities: completeness, consistency, provenance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_type": {"type": "string", "description": "Filter by entity type"},
                "entity_id": {"type": "string", "description": "Filter by entity ID"},
                "qc_mode": {
                    "type": "string",
                    "enum": ["completeness", "consistency", "provenance"],
                    "description": "QC check type",
                },
            },
            "additionalProperties": False,
        },
        "handler": egs_data_qc_bundle,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    "geox_egs_scenario_audit": {
        "description": "Audit alternative scenarios / competing interpretations for claims.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Filter by entity ID"},
                "claim_id": {"type": "string", "description": "Filter by claim ID"},
            },
            "additionalProperties": False,
        },
        "handler": egs_scenario_audit,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
}


def register_qc_tools(mcp: FastMCP) -> None:
    """Register EGS QC tools with the FastMCP server."""
    for tool_name, tool_def in EGS_QC_TOOLS.items():
        mcp.tool(name=tool_name, description=tool_def["description"])(tool_def["handler"])
        logger.info(f"Registered EGS QC tool: {tool_name}")
