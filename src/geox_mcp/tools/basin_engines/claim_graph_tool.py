"""
geox_claim_graph_evaluate — Claim Graph Evaluator MCP Tool
═══════════════════════════════════════════════════════════
Evaluate parent claim validity when child claims fail.

Uses DAG evaluation with AND/OR/WEIGHTED dependency types.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any


async def geox_claim_graph_evaluate(
    claims: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    initial_verdicts: dict[str, str] | None = None,
    failure_propagation: str = "cascade",
) -> dict[str, Any]:
    """Evaluate a claim dependency graph.

    Claims form a directed acyclic graph (DAG). Parent claims depend on child claims.
    This tool evaluates whether parent claims survive when children fail.

    Dependency types:
      AND — parent fails if ANY child fails
      OR  — parent fails only if ALL children fail
      WEIGHTED — parent validity = weighted sum of child validities

    Args:
        claims: List of {id, title, statement, truth_class, dependency_type, weight}
        edges: List of {child_id, parent_id, weight}
        initial_verdicts: {claim_id: "supported"|"contradicted"|"inconclusive"|"not_tested"}
        failure_propagation: "cascade"|"local"|"attenuated"

    Returns:
        EvaluationResult with root verdicts, failure propagation path,
        graph health metrics, and surviving/failed claim lists.

    OBS — Pure evaluation. No mutation.
    """
    from geox_core.engines.basin.claim_graph import (
        ClaimGraph,
        ClaimNode,
        ClaimVerdict,
        DependencyType,
        evaluate_graph,
    )

    # Build graph
    graph = ClaimGraph()

    # Map dependency type strings
    dep_map = {
        "and": DependencyType.AND,
        "or": DependencyType.OR,
        "weighted": DependencyType.WEIGHTED,
    }

    # Add claims
    for c in claims:
        node = ClaimNode(
            id=c.get("id", ""),
            title=c.get("title", ""),
            statement=c.get("statement", ""),
            truth_class=c.get("truth_class", "INTERPRETATION"),
            dependency_type=dep_map.get(c.get("dependency_type", "and"), DependencyType.AND),
            weight=c.get("weight", 1.0),
            provenance=c.get("provenance", ""),
            eureka_id=c.get("eureka_id"),
            domain=c.get("domain", "general"),
        )
        graph.add_claim(node)

    # Add edges (parent-child relationships)
    for e in edges:
        child_id = e.get("child_id", "")
        parent_id = e.get("parent_id", "")
        if parent_id in graph.claims and child_id in graph.claims:
            parent = graph.claims[parent_id]
            if child_id not in parent.child_ids:
                parent.child_ids.append(child_id)
                graph._children[parent_id].append(child_id)
                graph._parents[child_id].append(parent_id)

    # Set initial verdicts
    verdict_map = {
        "supported": ClaimVerdict.SUPPORTED,
        "contradicted": ClaimVerdict.CONTRADICTED,
        "inconclusive": ClaimVerdict.INCONCLUSIVE,
        "not_tested": ClaimVerdict.NOT_TESTED,
        "void": ClaimVerdict.VOID,
    }

    for cid, verdict_str in (initial_verdicts or {}).items():
        graph.set_verdict(cid, verdict_map.get(verdict_str, ClaimVerdict.NOT_TESTED))

    # Evaluate
    result = evaluate_graph(graph)

    # Build output
    return {
        "success": True,
        "graph_health": result.graph_health,
        "summary": result.summary,
        "root_claims": [
            {
                "id": c.id,
                "title": c.title,
                "verdict": c.verdict.value,
                "confidence": c.confidence,
            }
            for c in result.root_claims
        ],
        "all_claims": {
            cid: {
                "id": c.id,
                "title": c.title,
                "verdict": c.verdict.value,
                "truth_class": c.truth_class,
                "eureka_id": c.eureka_id,
            }
            for cid, c in result.all_claims.items()
        },
        "failure_propagation": result.failure_propagation,
        "surviving_claims": result.surviving_claims,
        "failed_claims": result.failed_claims,
        "inconclusive_claims": result.inconclusive_claims,
        "not_tested_claims": result.not_tested_claims,
        "provenance": result.provenance,
        "epistemic": {
            "truth_class": "INTERPRETATION",
            "evidence_tag": "INT",
            "not_fact_because": [
                "Claim verdicts depend on evidence quality (not evaluated here)",
                "Dependency structure is human-defined (subjective)",
                "AND/OR/WEIGHTED are simplifications of real relationships",
                "Failure propagation assumes DAG structure (no cycles)",
            ],
        },
    }


async def geox_claim_graph_sabah_eureka() -> dict[str, Any]:
    """Load and evaluate the canonical Sabah Two Oceanics claim graph.

    Returns the pre-built graph for the 13 eurekas from SABAH_EUREKA_LEDGER::v1.0.

    OBS — Read-only evaluation of the canonical graph.
    """
    from geox_core.engines.basin.claim_graph import (
        build_sabah_eureka_graph,
        evaluate_graph,
    )

    graph = build_sabah_eureka_graph()
    result = evaluate_graph(graph)

    return {
        "success": True,
        "artifact_id": "SABAH_EUREKA_LEDGER::v1.0",
        "graph_health": result.graph_health,
        "summary": result.summary,
        "root_claims": [
            {
                "id": c.id,
                "title": c.title,
                "verdict": c.verdict.value,
                "eureka_id": c.eureka_id,
            }
            for c in result.root_claims
        ],
        "all_claims": {
            cid: {
                "id": c.id,
                "title": c.title,
                "verdict": c.verdict.value,
                "truth_class": c.truth_class,
                "eureka_id": c.eureka_id,
            }
            for cid, c in result.all_claims.items()
        },
        "failure_propagation": result.failure_propagation,
        "provenance": result.provenance,
    }
