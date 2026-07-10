"""
claim_graph.py — Claim Graph Evaluator Engine
═══════════════════════════════════════════════
Evaluate parent claim validity when child claims fail.

Claims form a directed acyclic graph (DAG). Parent claims depend on child claims.
This engine evaluates whether parent claims survive when children fail.

Dependency types:
  AND — parent fails if ANY child fails
  OR  — parent fails only if ALL children fail
  WEIGHTED — parent validity = weighted sum of child validities

Failure propagation:
  1. A leaf claim receives a verdict (SUPPORTED / CONTRADICTED / INCONCLUSIVE)
  2. The verdict propagates UP the DAG through dependency edges
  3. Each parent evaluates its children's verdicts against its dependency type
  4. The process continues until the root claims are evaluated

DITEMPA BUKAN DIBERI — Forged, Not Given.

References:
  - Peters, S.E. & Gaines, R.R. (2012) — claim decomposition for Great Unconformity
  - Standard DAG evaluation from graph theory
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ClaimVerdict(str, Enum):
    """Verdict for a claim."""

    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"
    NOT_TESTED = "not_tested"
    VOID = "void"


class DependencyType(str, Enum):
    """How a parent claim depends on its children."""

    AND = "and"  # parent fails if ANY child fails
    OR = "or"  # parent fails only if ALL children fail
    WEIGHTED = "weighted"  # parent validity = weighted sum


class FailureMode(str, Enum):
    """How failure propagates."""

    CASCADE = "cascade"  # failure propagates to all ancestors
    LOCAL = "local"  # failure stays at this node
    ATTENUATED = "attenuated"  # failure weakens with distance


@dataclass
class ClaimNode:
    """A single claim in the graph."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    statement: str = ""
    truth_class: str = "INTERPRETATION"  # FACT / DERIVED / INTERPRETATION / SPECULATION
    verdict: ClaimVerdict = ClaimVerdict.NOT_TESTED
    confidence: float = 0.5  # 0-1
    evidence_count: int = 0
    challenge_count: int = 0
    # Graph structure
    parent_ids: list[str] = field(default_factory=list)
    child_ids: list[str] = field(default_factory=list)
    dependency_type: DependencyType = DependencyType.AND
    weight: float = 1.0  # for WEIGHTED dependencies
    failure_mode: FailureMode = FailureMode.CASCADE
    # Metadata
    provenance: str = ""
    eureka_id: int | None = None
    domain: str = "general"


@dataclass
class ClaimEdge:
    """A directed edge from child to parent."""

    child_id: str
    parent_id: str
    weight: float = 1.0
    necessary: bool = True  # if False, child failure doesn't kill parent


@dataclass
class EvaluationResult:
    """Result of evaluating the entire claim graph."""

    root_claims: list[ClaimNode]
    all_claims: dict[str, ClaimNode]
    failure_propagation: list[dict[str, Any]]
    surviving_claims: list[str]
    failed_claims: list[str]
    inconclusive_claims: list[str]
    not_tested_claims: list[str]
    graph_health: float  # 0-1, fraction of claims that survive
    summary: dict[str, Any]
    provenance: dict[str, Any]


class ClaimGraph:
    """Directed acyclic graph of geological claims.

    Supports:
    - Adding claims with dependencies
    - Evaluating verdicts on leaf claims
    - Propagating failures through the graph
    - Computing graph health metrics
    """

    def __init__(self) -> None:
        self.claims: dict[str, ClaimNode] = {}
        self.edges: list[ClaimEdge] = []
        self._children: dict[str, list[str]] = defaultdict(list)  # parent -> children
        self._parents: dict[str, list[str]] = defaultdict(list)  # child -> parents

    def add_claim(self, claim: ClaimNode) -> str:
        """Add a claim to the graph. Returns claim ID."""
        self.claims[claim.id] = claim
        for child_id in claim.child_ids:
            self._children[claim.id].append(child_id)
            self._parents[child_id].append(claim.id)
            self.edges.append(
                ClaimEdge(
                    child_id=child_id,
                    parent_id=claim.id,
                    weight=claim.weight,
                )
            )
        return claim.id

    def set_verdict(self, claim_id: str, verdict: ClaimVerdict, confidence: float = 0.5) -> None:
        """Set verdict on a claim."""
        if claim_id in self.claims:
            self.claims[claim_id].verdict = verdict
            self.claims[claim_id].confidence = confidence

    def get_children(self, claim_id: str) -> list[ClaimNode]:
        """Get direct children of a claim."""
        return [self.claims[cid] for cid in self._children.get(claim_id, []) if cid in self.claims]

    def get_parents(self, claim_id: str) -> list[ClaimNode]:
        """Get direct parents of a claim."""
        return [self.claims[pid] for pid in self._parents.get(claim_id, []) if pid in self.claims]

    def get_leaf_claims(self) -> list[ClaimNode]:
        """Get claims with no children (leaf nodes)."""
        return [c for c in self.claims.values() if not self._children.get(c.id)]

    def get_root_claims(self) -> list[ClaimNode]:
        """Get claims with no parents (root nodes)."""
        return [c for c in self.claims.values() if not self._parents.get(c.id)]

    def evaluate_node(self, claim_id: str) -> ClaimVerdict:
        """Evaluate a single node based on its children's verdicts.

        AND: SUPPORTED if all children SUPPORTED, else CONTRADICTED if any CONTRADICTED
        OR: SUPPORTED if any child SUPPORTED, else CONTRADICTED if all CONTRADICTED
        WEIGHTED: SUPPORTED if weighted sum > 0.5, else CONTRADICTED
        """
        claim = self.claims.get(claim_id)
        if not claim:
            return ClaimVerdict.VOID

        children = self.get_children(claim_id)

        # Leaf node — return existing verdict
        if not children:
            return claim.verdict

        child_verdicts = [(c.verdict, c.weight) for c in children]

        if claim.dependency_type == DependencyType.AND:
            return self._evaluate_and(child_verdicts)
        elif claim.dependency_type == DependencyType.OR:
            return self._evaluate_or(child_verdicts)
        elif claim.dependency_type == DependencyType.WEIGHTED:
            return self._evaluate_weighted(child_verdicts)
        else:
            return ClaimVerdict.INCONCLUSIVE

    def _evaluate_and(self, child_verdicts: list[tuple[ClaimVerdict, float]]) -> ClaimVerdict:
        """AND dependency: fail if ANY child fails."""
        has_contradicted = any(v == ClaimVerdict.CONTRADICTED for v, _ in child_verdicts)
        has_inconclusive = any(v == ClaimVerdict.INCONCLUSIVE for v, _ in child_verdicts)
        all_supported = all(v == ClaimVerdict.SUPPORTED for v, _ in child_verdicts)

        if has_contradicted:
            return ClaimVerdict.CONTRADICTED
        if all_supported:
            return ClaimVerdict.SUPPORTED
        if has_inconclusive:
            return ClaimVerdict.INCONCLUSIVE
        return ClaimVerdict.NOT_TESTED

    def _evaluate_or(self, child_verdicts: list[tuple[ClaimVerdict, float]]) -> ClaimVerdict:
        """OR dependency: fail only if ALL children fail."""
        has_supported = any(v == ClaimVerdict.SUPPORTED for v, _ in child_verdicts)
        all_contradicted = all(v == ClaimVerdict.CONTRADICTED for v, _ in child_verdicts)

        if has_supported:
            return ClaimVerdict.SUPPORTED
        if all_contradicted:
            return ClaimVerdict.CONTRADICTED
        return ClaimVerdict.INCONCLUSIVE

    def _evaluate_weighted(self, child_verdicts: list[tuple[ClaimVerdict, float]]) -> ClaimVerdict:
        """WEIGHTED dependency: weighted sum of child confidences."""
        if not child_verdicts:
            return ClaimVerdict.NOT_TESTED

        total_weight = sum(w for _, w in child_verdicts)
        if total_weight == 0:
            return ClaimVerdict.INCONCLUSIVE

        weighted_score = 0.0
        for verdict, weight in child_verdicts:
            if verdict == ClaimVerdict.SUPPORTED:
                weighted_score += weight
            elif verdict == ClaimVerdict.CONTRADICTED:
                weighted_score -= weight
            # INCONCLUSIVE and NOT_TESTED contribute 0

        normalized = weighted_score / total_weight
        if normalized > 0.5:
            return ClaimVerdict.SUPPORTED
        elif normalized < -0.5:
            return ClaimVerdict.CONTRADICTED
        return ClaimVerdict.INCONCLUSIVE


def evaluate_graph(graph: ClaimGraph) -> EvaluationResult:
    """Evaluate the entire claim graph bottom-up.

    Algorithm:
    1. Start with leaf claims (already have verdicts)
    2. For each level, evaluate parents based on children
    3. Propagate until root claims are evaluated
    4. Track failure propagation path

    Returns EvaluationResult with full analysis.
    """
    failure_propagation: list[dict[str, Any]] = []
    evaluated: set[str] = set()

    # Topological sort (BFS from leaves)
    # Process in layers: leaves first, then their parents, etc.
    remaining = set(graph.claims.keys())

    max_iterations = len(graph.claims) + 1
    iteration = 0

    while remaining and iteration < max_iterations:
        iteration += 1
        to_evaluate = []

        for cid in list(remaining):
            children = graph.get_children(cid)
            # Can evaluate if all children are already evaluated
            if all(c.id in evaluated for c in children):
                to_evaluate.append(cid)

        if not to_evaluate:
            # Deadlock — circular dependency or missing nodes
            break

        for cid in to_evaluate:
            old_verdict = graph.claims[cid].verdict
            new_verdict = graph.evaluate_node(cid)

            if old_verdict != new_verdict and old_verdict == ClaimVerdict.NOT_TESTED:
                failure_propagation.append(
                    {
                        "claim_id": cid,
                        "old_verdict": old_verdict.value,
                        "new_verdict": new_verdict.value,
                        "reason": "propagated from children",
                        "children_verdicts": [{"id": c.id, "verdict": c.verdict.value} for c in graph.get_children(cid)],
                    }
                )

            graph.claims[cid].verdict = new_verdict
            evaluated.add(cid)
            remaining.discard(cid)

    # Collect results
    all_claims = graph.claims
    surviving = [cid for cid, c in all_claims.items() if c.verdict == ClaimVerdict.SUPPORTED]
    failed = [cid for cid, c in all_claims.items() if c.verdict == ClaimVerdict.CONTRADICTED]
    inconclusive = [cid for cid, c in all_claims.items() if c.verdict == ClaimVerdict.INCONCLUSIVE]
    not_tested = [cid for cid, c in all_claims.items() if c.verdict == ClaimVerdict.NOT_TESTED]

    total = len(all_claims)
    graph_health = len(surviving) / total if total > 0 else 0.0

    root_claims = graph.get_root_claims()

    summary = {
        "total_claims": total,
        "surviving": len(surviving),
        "failed": len(failed),
        "inconclusive": len(inconclusive),
        "not_tested": len(not_tested),
        "graph_health": graph_health,
        "root_verdicts": {c.id: c.verdict.value for c in root_claims},
    }

    return EvaluationResult(
        root_claims=root_claims,
        all_claims=all_claims,
        failure_propagation=failure_propagation,
        surviving_claims=surviving,
        failed_claims=failed,
        inconclusive_claims=inconclusive,
        not_tested_claims=not_tested,
        graph_health=graph_health,
        summary=summary,
        provenance={
            "method": "DAG_evaluation",
            "dependency_types": ["AND", "OR", "WEIGHTED"],
            "propagation": "bottom-up topological",
            "iterations": iteration,
        },
    )


def propagate_failure(
    graph: ClaimGraph,
    failed_claim_id: str,
    failure_mode: FailureMode = FailureMode.CASCADE,
) -> list[dict[str, Any]]:
    """Propagate a specific failure through the graph.

    Returns list of affected claims with their new verdicts.
    """
    affected: list[dict[str, Any]] = []
    visited: set[str] = set()

    def _propagate(claim_id: str, depth: int) -> None:
        if claim_id in visited:
            return
        visited.add(claim_id)

        claim = graph.claims.get(claim_id)
        if not claim:
            return

        # Mark as contradicted
        old_verdict = claim.verdict
        claim.verdict = ClaimVerdict.CONTRADICTED

        affected.append(
            {
                "claim_id": claim_id,
                "old_verdict": old_verdict.value,
                "new_verdict": ClaimVerdict.CONTRADICTED.value,
                "depth": depth,
                "failure_mode": failure_mode.value,
            }
        )

        # Propagate to parents
        if failure_mode == FailureMode.CASCADE:
            for parent in graph.get_parents(claim_id):
                # Check if parent can still survive (OR dependency)
                if parent.dependency_type == DependencyType.OR:
                    siblings = graph.get_children(parent.id)
                    has_other_support = any(s.id != claim_id and s.verdict == ClaimVerdict.SUPPORTED for s in siblings)
                    if has_other_support:
                        # Parent survives — don't propagate
                        continue
                _propagate(parent.id, depth + 1)
        elif failure_mode == FailureMode.ATTENUATED:
            if depth < 3:  # limit propagation depth
                for parent in graph.get_parents(claim_id):
                    _propagate(parent.id, depth + 1)
        # LOCAL: don't propagate

    _propagate(failed_claim_id, 0)
    return affected


def build_sabah_eureka_graph() -> ClaimGraph:
    """Build the Sabah Two Oceanics claim graph.

    13 parent eurekas → atomic child claims → alternatives.

    This is the canonical graph for the SABAH_EUREKA_LEDGER::v1.0.
    """
    graph = ClaimGraph()

    # Eureka #1: Two domains
    e1 = ClaimNode(
        id="eureka_1",
        title="Two Oceans Not One",
        statement="NW Sabah comprises two lithospheric domains with different subsidence physics",
        dependency_type=DependencyType.AND,
        eureka_id=1,
    )
    e1a = ClaimNode(
        id="e1_subsidence_contrast",
        title="Subsidence contrast",
        statement="Domain A and B have materially different subsidence histories",
        truth_class="INTERPRETATION",
    )
    e1b = ClaimNode(
        id="e1_load_dominance",
        title="Loading dominance",
        statement="Domain A is loading-dominated",
        truth_class="INTERPRETATION",
    )
    e1c = ClaimNode(
        id="e1_thermal_dominance",
        title="Thermal dominance",
        statement="Domain B is thermal-decay-dominated",
        truth_class="INTERPRETATION",
    )
    e1d = ClaimNode(
        id="e1_suture_location",
        title="Suture location",
        statement="The Sabah Trough marks the mechanical boundary between domains",
        truth_class="INTERPRETATION",
    )
    e1.child_ids = [e1a.id, e1b.id, e1c.id, e1d.id]
    for child in [e1a, e1b, e1c, e1d]:
        child.parent_ids = [e1.id]
        graph.add_claim(child)
    graph.add_claim(e1)

    # Eureka #4: Mass deficit
    e4 = ClaimNode(
        id="eureka_4",
        title="Mass Deficit",
        statement="60% of predicted sediment mass is missing from Domain A",
        dependency_type=DependencyType.AND,
        eureka_id=4,
    )
    e4a = ClaimNode(
        id="e4_volume_balance",
        title="Volume balance",
        statement="Source volume exceeds preserved volume by ~60%",
        truth_class="INTERPRETATION",
    )
    e4b = ClaimNode(
        id="e4_bypass_insufficient",
        title="Bypass insufficient",
        statement="Bypass fraction (0.8%) cannot explain the deficit",
        truth_class="INTERPRETATION",
    )
    e4c = ClaimNode(
        id="e4_trough_destination",
        title="Trough destination",
        statement="The missing mass went to the Sabah Trough",
        truth_class="SPECULATION",
    )
    e4.child_ids = [e4a.id, e4b.id, e4c.id]
    for child in [e4a, e4b, e4c]:
        child.parent_ids = [e4.id]
        graph.add_claim(child)
    graph.add_claim(e4)

    # Eureka #12: Margin Principle
    e12 = ClaimNode(
        id="eureka_12",
        title="Margin Principle",
        statement="Unconformities are made at margins; interior only records the result",
        dependency_type=DependencyType.OR,
        eureka_id=12,
    )
    e12a = ClaimNode(
        id="e12_local_unconformities",
        title="Local unconformities",
        statement="ROU/BU/MMU/SRU are local margin events with different mechanisms",
        truth_class="INTERPRETATION",
    )
    e12b = ClaimNode(
        id="e12_margin_summation",
        title="Margin summation",
        statement="Scaled across supercontinent cycles, margin dynamics explain the Great Unconformity",
        truth_class="SPECULATION",
    )
    e12.child_ids = [e12a.id, e12b.id]
    for child in [e12a, e12b]:
        child.parent_ids = [e12.id]
        graph.add_claim(child)
    graph.add_claim(e12)

    # Add remaining eurekas as standalone claims
    for eid, title, stmt, tc in [
        (2, "Three Papers Three Earths", "Tongkul/Sidek/Prabal answered different questions", "INTERPRETATION"),
        (3, "Labels Not Process", "DRU/MMU are label-correlated, not process-correlated", "INTERPRETATION"),
        (5, "Domain B Starved", "Domain B is quantitatively starved of clastic sediment", "INTERPRETATION"),
        (6, "15 Myr Chronology", "The collision is a 15 Myr sequence, not an event", "INTERPRETATION"),
        (7, "Pre-Collision Not Void", "Before unification had old Sabah + old DG", "INTERPRETATION"),
        (8, "Mud Volcano Loading", "Mud volcanoes are the loading release valve", "INTERPRETATION"),
        (9, "Kinabalu Decompression", "Kinabalu granite is post-collisional decompression melt", "INTERPRETATION"),
        (10, "Trough Prospect", "Sabah Trough is a prospect, not just a feature", "SPECULATION"),
        (11, "Bifurcated Risking", "Prospect risking must bifurcate between domains", "INTERPRETATION"),
        (13, "Interior Passive Archive", "Interior is passive archive; margin is active engine", "SPECULATION"),
    ]:
        node = ClaimNode(
            id=f"eureka_{eid}",
            title=title,
            statement=stmt,
            truth_class=tc,
            eureka_id=eid,
        )
        graph.add_claim(node)

    return graph
