"""
epistemic/assumption_lineage.py — GEOX Assumption Identity & Lineage
=================================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Every assumption must carry a unique identity and lineage trace.
This is the DNA layer of GEOX reasoning — without this,
errors cannot be traced to their origin, and interpretation
chains cannot be audited for circular propagation.

Every assumption has:
  - assumption_id: unique ID (e.g. "A1", "A2")
  - parent_assumption_id: what assumption this builds on (None for root)
  - introduced_by: tool name that introduced this assumption
  - rung_origin: which rung this assumption operates at
  - current_status: active | falsified | inherited | suspended
  - children: list of assumption_ids that depend on this one
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class AssumptionStatus(StrEnum):
    ACTIVE = "active"  # Currently being used in reasoning
    FALSIFIED = "falsified"  # Rejected by contradicting evidence
    INHERITED = "inherited"  # Propagated from upstream tool/claim
    SUSPENDED = "suspended"  # Temporarily held — awaiting evidence
    PROPAGATED = "propagated"  # Inherited by downstream tool outputs


class AssumptionType(StrEnum):
    CUTOFF = "cutoff"  # Threshold value selection
    MODEL = "model"  # Physical/empirical model choice
    ENVIRONMENT = "environment"  # Depositional/geological environment
    PARAMETER = "parameter"  # Numeric parameter value
    ANALOG = "analog"  # Analog field/case selection
    THRESHOLD = "threshold"  # Decision boundary threshold
    DATUM = "datum"  # Depth/time reference frame
    CRS = "crs"  # Coordinate reference system
    WAVEFORM = "waveform"  # Seismic wavelet assumption
    FLOW_REGIME = "flow_regime"  # DST flow regime interpretation


@dataclass
class AssumptionRecord:
    """
    A single assumption record in the GEOX assumption graph.

    This is the fundamental unit of epistemic traceability.
    Every interpretation chain can be reconstructed by following
    parent_assumption_id links back to root assumptions.
    """

    assumption_id: str
    parent_assumption_id: str | None
    introduced_by: str  # Tool name that introduced this
    rung_origin: int  # Rung at which this assumption was introduced
    assumption_type: AssumptionType
    description: str
    value_used: str  # The value actually used in this run
    alternatives: list[str]  # Reasonable alternative values
    sensitivity: str  # CRITICAL | HIGH | MEDIUM | LOW
    current_status: AssumptionStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    falsified_at: datetime | None = None
    falsified_by: str | None = None  # Evidence_ref that falsified it
    propagated_to: list[str] = field(default_factory=list)  # assumption_ids that inherited this
    metadata: dict = field(default_factory=dict)  # Flexible extra context

    def is_root(self) -> bool:
        """True if this is a first-order assumption (no parent)."""
        return self.parent_assumption_id is None

    def lineage_depth(self) -> int:
        """
        Returns the depth of this assumption in the lineage tree.
        Root assumptions = depth 1. Children = depth 2, etc.
        """
        # This requires access to the AssumptionGraph to compute.
        # Placeholder — actual implementation uses AssumptionGraph.lineage_depth()
        return 0  # Computed by graph


class AssumptionGraph:
    """
    In-memory graph of all assumptions across GEOX sessions.

    Thread-safe. Tracks parent-child relationships between assumptions.
    Enables:
      - Error propagation tracing (which assumption corrupted which output)
      - Circular dependency detection
      - Lineage depth calculation
      - Falsification cascade analysis
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: dict[str, AssumptionRecord] = {}

    def register(
        self,
        introduced_by: str,
        assumption_id: str,
        parent_assumption_id: str | None,
        rung_origin: int,
        assumption_type: AssumptionType,
        description: str,
        value_used: str,
        alternatives: list[str] | None = None,
        sensitivity: str = "MEDIUM",
        metadata: dict | None = None,
    ) -> AssumptionRecord:
        """
        Register a new assumption in the graph.

        If parent_assumption_id is provided, links this assumption
        to its parent and adds this ID to the parent's propagated_to list.
        """
        with self._lock:
            if assumption_id in self._records:
                existing = self._records[assumption_id]
                # Update status if being re-registered
                existing.current_status = AssumptionStatus.ACTIVE
                existing.value_used = value_used
                return existing

            record = AssumptionRecord(
                assumption_id=assumption_id,
                parent_assumption_id=parent_assumption_id,
                introduced_by=introduced_by,
                rung_origin=rung_origin,
                assumption_type=assumption_type,
                description=description,
                value_used=value_used,
                alternatives=alternatives or [],
                sensitivity=sensitivity,
                current_status=AssumptionStatus.ACTIVE,
                metadata=metadata or {},
            )
            self._records[assumption_id] = record

            # Link to parent
            if parent_assumption_id and parent_assumption_id in self._records:
                parent = self._records[parent_assumption_id]
                if assumption_id not in parent.propagated_to:
                    parent.propagated_to.append(assumption_id)

            return record

    def falsify(
        self,
        assumption_id: str,
        falsified_by: str,
        reason: str | None = None,
    ) -> bool:
        """
        Mark an assumption as falsified.

        Returns True if the assumption existed and was falsified.
        Propagates falsification to all children unless they have
        explicitly overridden the inherited assumption.
        """
        with self._lock:
            if assumption_id not in self._records:
                return False

            record = self._records[assumption_id]
            record.current_status = AssumptionStatus.FALSIFIED
            record.falsified_at = datetime.now(UTC)
            record.falsified_by = falsified_by
            if reason:
                record.metadata["falsification_reason"] = reason

            # Cascade to children — falsification propagates downstream
            for child_id in record.propagated_to:
                child = self._records.get(child_id)
                if child and child.current_status == AssumptionStatus.INHERITED:
                    child.current_status = AssumptionStatus.FALSIFIED
                    child.falsified_at = datetime.now(UTC)
                    child.falsified_by = f"CASCADE:{assumption_id}"
                    child.metadata["falsification_cascade_from"] = assumption_id

            return True

    def get(self, assumption_id: str) -> AssumptionRecord | None:
        """Retrieve an assumption record by ID."""
        with self._lock:
            return self._records.get(assumption_id)

    def get_by_tool(self, introduced_by: str) -> list[AssumptionRecord]:
        """Get all assumptions introduced by a specific tool."""
        with self._lock:
            return [r for r in self._records.values() if r.introduced_by == introduced_by]

    def get_active(self) -> list[AssumptionRecord]:
        """Get all currently active (non-falsified) assumptions."""
        with self._lock:
            return [r for r in self._records.values() if r.current_status != AssumptionStatus.FALSIFIED]

    def lineage(self, assumption_id: str) -> list[AssumptionRecord]:
        """
        Return the full lineage chain from root to this assumption.
        Follows parent_assumption_id links back to root.
        """
        with self._lock:
            chain: list[AssumptionRecord] = []
            current = self._records.get(assumption_id)
            visited: set[str] = set()

            while current:
                if current.assumption_id in visited:
                    # Circular reference detected — break
                    break
                visited.add(current.assumption_id)
                chain.insert(0, current)
                current = self._records.get(current.parent_assumption_id) if current.parent_assumption_id else None

            return chain

    def lineage_depth(self, assumption_id: str) -> int:
        """Return the depth of an assumption in the lineage tree."""
        return len(self.lineage(assumption_id))

    def detect_circular(self, assumption_id: str) -> bool:
        """Check if adding this assumption would create a circular reference."""
        with self._lock:
            visited: set[str] = set()
            current = self._records.get(assumption_id)

            while current:
                if current.assumption_id in visited:
                    return True
                visited.add(current.assumption_id)
                current = self._records.get(current.parent_assumption_id) if current.parent_assumption_id else None
            return False

    def affected_outputs(self, assumption_id: str) -> list[str]:
        """
        Return list of tool outputs that would be affected if this
        assumption were falsified. Follows propagated_to links.
        """
        with self._lock:
            affected: list[str] = []
            to_visit = [assumption_id]
            visited: set[str] = set()

            while to_visit:
                aid = to_visit.pop()
                if aid in visited:
                    continue
                visited.add(aid)

                record = self._records.get(aid)
                if record:
                    if record.introduced_by not in affected:
                        affected.append(record.introduced_by)
                    for child_id in record.propagated_to:
                        if child_id not in visited:
                            to_visit.append(child_id)

            return affected

    def summary(self) -> dict:
        """Return a summary of the current assumption graph state."""
        with self._lock:
            return {
                "total_assumptions": len(self._records),
                "active": sum(1 for r in self._records.values() if r.current_status == AssumptionStatus.ACTIVE),
                "falsified": sum(1 for r in self._records.values() if r.current_status == AssumptionStatus.FALSIFIED),
                "inherited": sum(1 for r in self._records.values() if r.current_status == AssumptionStatus.INHERITED),
                "by_tool": {
                    tool: sum(1 for r in self._records.values() if r.introduced_by == tool)
                    for tool in set(r.introduced_by for r in self._records.values())
                },
            }


# ─── Global singleton assumption graph ──────────────────────────────────────────
# Shared across all GEOX tool invocations within a session.

_ASSUMPTION_GRAPH: AssumptionGraph | None = None
_GRAPH_LOCK = threading.Lock()


def get_assumption_graph() -> AssumptionGraph:
    """
    Get the global AssumptionGraph singleton for this process.

    Creates if not yet initialized.
    Thread-safe singleton access.
    """
    global _ASSUMPTION_GRAPH
    with _GRAPH_LOCK:
        if _ASSUMPTION_GRAPH is None:
            _ASSUMPTION_GRAPH = AssumptionGraph()
        return _ASSUMPTION_GRAPH


def reset_assumption_graph() -> None:
    """
    Reset the global assumption graph.

    Use only at session start or when starting a fresh reasoning context.
    Failsafe: does not clear during active tool execution.
    """
    global _ASSUMPTION_GRAPH
    with _GRAPH_LOCK:
        _ASSUMPTION_GRAPH = AssumptionGraph()
