"""
process_state_graph.py — ProcessStateGraph (ADR-008)

═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, not given.

Process-state Markov graph for VoxelState4.process_state.

Per ADR-008 §1: "process_state compresses history (origin, depositional_environment,
transitions). Real histories are non-cyclic and asymmetric."

This module provides a typed edge set over (origin, environment, transition)
states. The graph supports forward propagation of process state across time.

Anti-misconception spine:
  • "rock cycle is one clean loop"  →  this graph allows non-cyclic paths
  • "everything was once lava"  →  has_been_molten is a graph node, not default
  • "sediment = dried mud"  →  depositional_environment is a graph node with 9 types

Skeleton-only this cycle. Real propagation logic (Markov chain) deferred to
subsequent tranche with empirical calibration.

═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from geox_core.schemas.voxel_state import (
    DepositionalEnvironment,
    IgneousContext,
    LastMajorTransition,
    MetamorphicRegime,
    OriginType,
    ProcessState,
)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. EDGE TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class EdgeKind(StrEnum):
    """
    Kind of process-state transition edge.
    """

    formation = "formation"  # initial formation (e.g., melt_crystallization, deposition_lithification)
    metamorphism = "metamorphism"  # P-T transformation
    deformation = "deformation"  # strain event
    erosion = "erosion"  # exhumation event
    diagenesis = "diagenesis"  # low-T alteration
    unknown = "unknown"


class ProcessStateEdge(BaseModel):
    """
    A single transition edge in the process-state graph.

    e.g., (sedimentary, fluvial, deposition_lithification) → (metamorphic, regional, metamorphism)
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    from_state: ProcessState = Field(description="Starting process state")
    to_state: ProcessState = Field(description="Ending process state")
    edge_kind: EdgeKind = Field(default=EdgeKind.unknown)
    probability: float = Field(
        ge=0.0,
        le=1.0,
        description="Transition probability (per Myr or per unit time, calibration pending)",
    )
    time_duration_myr: float | None = Field(default=None, ge=0.0, description="Typical duration of this transition in Myr")
    evidence_refs: list[str] = Field(
        default_factory=list, description="Artifact refs supporting this edge (per Claim 2 / Claim 3)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CANONICAL EDGE SET — initial graph topology
# ═══════════════════════════════════════════════════════════════════════════════


def _make_initial_state(
    origin: OriginType,
    environment: DepositionalEnvironment = DepositionalEnvironment.unknown,
    igneous: IgneousContext = IgneousContext.unknown,
    metamorphic: MetamorphicRegime = MetamorphicRegime.unknown,
    transition: LastMajorTransition = LastMajorTransition.unknown,
    has_been_molten: bool | None = None,
    has_been_exhumed: bool | None = None,
) -> ProcessState:
    """Helper for building initial ProcessState nodes."""
    return ProcessState(
        origin=origin,
        depositional_environment=environment,
        igneous_context=igneous,
        metamorphic_regime=metamorphic,
        has_been_molten=has_been_molten,
        has_been_exhumed=has_been_exhumed,
        last_major_transition=transition,
    )


# ─── Canonical edges ────────────────────────────────────────────────────────
# These are the "obvious" first-order transitions. Probabilities are STUB
# values pending empirical calibration from real basin data (Phase 2).


CANONICAL_EDGES: list[ProcessStateEdge] = [
    # ── Sedimentary formation ──
    ProcessStateEdge(
        from_state=_make_initial_state(OriginType.sedimentary),
        to_state=_make_initial_state(
            OriginType.sedimentary,
            environment=DepositionalEnvironment.fluvial,
            transition=LastMajorTransition.deposition_lithification,
            has_been_molten=False,
        ),
        edge_kind=EdgeKind.formation,
        probability=0.95,
        time_duration_myr=5.0,
    ),
    ProcessStateEdge(
        from_state=_make_initial_state(OriginType.sedimentary),
        to_state=_make_initial_state(
            OriginType.sedimentary,
            environment=DepositionalEnvironment.marine_shelf,
            transition=LastMajorTransition.deposition_lithification,
            has_been_molten=False,
        ),
        edge_kind=EdgeKind.formation,
        probability=0.95,
        time_duration_myr=10.0,
    ),
    # ── Sedimentary → Metamorphic ──
    ProcessStateEdge(
        from_state=_make_initial_state(
            OriginType.sedimentary,
            transition=LastMajorTransition.deposition_lithification,
        ),
        to_state=_make_initial_state(
            OriginType.metamorphic,
            metamorphic=MetamorphicRegime.regional,
            transition=LastMajorTransition.metamorphism,
            has_been_molten=False,
        ),
        edge_kind=EdgeKind.metamorphism,
        probability=0.30,
        time_duration_myr=50.0,
    ),
    ProcessStateEdge(
        from_state=_make_initial_state(
            OriginType.sedimentary,
            transition=LastMajorTransition.deposition_lithification,
        ),
        to_state=_make_initial_state(
            OriginType.metamorphic,
            metamorphic=MetamorphicRegime.contact,
            transition=LastMajorTransition.metamorphism,
            has_been_molten=False,
        ),
        edge_kind=EdgeKind.metamorphism,
        probability=0.10,
        time_duration_myr=5.0,
    ),
    # ── Metamorphic → Exhumation ──
    ProcessStateEdge(
        from_state=_make_initial_state(
            OriginType.metamorphic,
            metamorphic=MetamorphicRegime.regional,
            transition=LastMajorTransition.metamorphism,
            has_been_exhumed=False,
        ),
        to_state=_make_initial_state(
            OriginType.metamorphic,
            metamorphic=MetamorphicRegime.regional,
            transition=LastMajorTransition.strong_erosion,
            has_been_exhumed=True,
        ),
        edge_kind=EdgeKind.erosion,
        probability=0.40,
        time_duration_myr=100.0,
    ),
    # ── Igneous formation ──
    ProcessStateEdge(
        from_state=_make_initial_state(OriginType.igneous),
        to_state=_make_initial_state(
            OriginType.igneous,
            igneous=IgneousContext.intrusive_body,
            transition=LastMajorTransition.melt_crystallization,
            has_been_molten=True,
        ),
        edge_kind=EdgeKind.formation,
        probability=0.60,
        time_duration_myr=1.0,
    ),
    ProcessStateEdge(
        from_state=_make_initial_state(OriginType.igneous),
        to_state=_make_initial_state(
            OriginType.igneous,
            igneous=IgneousContext.lava_flow,
            transition=LastMajorTransition.melt_crystallization,
            has_been_molten=True,
        ),
        edge_kind=EdgeKind.formation,
        probability=0.30,
        time_duration_myr=0.01,
    ),
    # ── Igneous → Metamorphic (unusual but possible) ──
    ProcessStateEdge(
        from_state=_make_initial_state(
            OriginType.igneous,
            transition=LastMajorTransition.melt_crystallization,
            has_been_molten=True,
        ),
        to_state=_make_initial_state(
            OriginType.metamorphic,
            metamorphic=MetamorphicRegime.regional,
            transition=LastMajorTransition.metamorphism,
            has_been_molten=True,
        ),
        edge_kind=EdgeKind.metamorphism,
        probability=0.05,
        time_duration_myr=200.0,
    ),
    # ── Diagenesis (low-T alteration) ──
    ProcessStateEdge(
        from_state=_make_initial_state(
            OriginType.sedimentary,
            transition=LastMajorTransition.deposition_lithification,
        ),
        to_state=_make_initial_state(
            OriginType.sedimentary,
            transition=LastMajorTransition.diagenesis,
        ),
        edge_kind=EdgeKind.diagenesis,
        probability=0.50,
        time_duration_myr=20.0,
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PROCESS STATE GRAPH — typed graph over ProcessState nodes
# ═══════════════════════════════════════════════════════════════════════════════


class ProcessStateGraph(BaseModel):
    """
    Directed graph over ProcessState nodes with typed edges.

    This is the substrate for process-state propagation in VoxelState4.
    Future Markov-chain logic will use this graph as transition matrix.

    Skeleton-only this cycle. Propagation logic deferred to Phase 2.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    edges: list[ProcessStateEdge] = Field(
        default_factory=lambda: list(CANONICAL_EDGES),
        description="Edge set for process-state transitions",
    )

    def find_outgoing(self, from_state: ProcessState) -> list[ProcessStateEdge]:
        """
        Find all edges originating from a given ProcessState.

        Returns list of edges where from_state matches.
        """
        return [edge for edge in self.edges if _states_match(edge.from_state, from_state)]

    def find_incoming(self, to_state: ProcessState) -> list[ProcessStateEdge]:
        """Find all edges terminating at a given ProcessState."""
        return [edge for edge in self.edges if _states_match(edge.to_state, to_state)]

    def has_been_molten_reachable(
        self,
        start: ProcessState,
        target_visited: set[tuple] | None = None,
    ) -> bool:
        """
        Check whether a `has_been_molten=True` state is reachable from `start`.

        anti_misconception: "everything was once lava"
        Most crustal voxels should NOT have has_been_molten reachable.
        """
        if target_visited is None:
            target_visited = set()

        state_key = _state_key(start)
        if state_key in target_visited:
            return False  # cycle detected, no infinite loop
        target_visited.add(state_key)

        if start.has_been_molten is True:
            return True

        for edge in self.find_outgoing(start):
            if self.has_been_molten_reachable(edge.to_state, target_visited):
                return True

        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 4. HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def _state_key(state: ProcessState) -> tuple:
    """Hashable key for a ProcessState — for cycle detection in graph search."""
    return (
        state.origin,
        state.depositional_environment,
        state.igneous_context,
        state.metamorphic_regime,
        state.last_major_transition,
        state.has_been_molten,
        state.has_been_exhumed,
    )


def _states_match(a: ProcessState, b: ProcessState) -> bool:
    """
    Soft match between two ProcessState nodes.

    Two states match if all their **non-unknown** fields agree.
    Allows graph traversal from a partially-specified starting state.
    """
    pairs = [
        (a.origin, b.origin),
        (a.depositional_environment, b.depositional_environment),
        (a.igneous_context, b.igneous_context),
        (a.metamorphic_regime, b.metamorphic_regime),
        (a.last_major_transition, b.last_major_transition),
    ]
    for x, y in pairs:
        if x == "unknown" or y == "unknown":
            continue
        if x != y:
            return False
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════


__all__ = [
    "EdgeKind",
    "ProcessStateEdge",
    "ProcessStateGraph",
    "CANONICAL_EDGES",
]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════


def _self_test() -> None:
    """
    Smoke test for ProcessStateGraph.

    Run via: python -m geox_core.governance.process_state_graph
    """
    from geox_core.schemas.voxel_state import ProcessState

    graph = ProcessStateGraph()

    # Test: sedimentary fluvial voxel — molten should NOT be reachable
    fluvial_sand = ProcessState(
        origin=OriginType.sedimentary,
        depositional_environment=DepositionalEnvironment.fluvial,
        has_been_molten=False,
    )
    assert graph.has_been_molten_reachable(fluvial_sand) is False

    # Test: igneous intrusive voxel — molten SHOULD be reachable
    intrusive_granite = ProcessState(
        origin=OriginType.igneous,
        igneous_context=IgneousContext.intrusive_body,
        has_been_molten=True,
    )
    assert graph.has_been_molten_reachable(intrusive_granite) is True

    # Test: outgoing edges from a sedimentary state
    edges = graph.find_outgoing(fluvial_sand)
    assert len(edges) >= 1  # at least one formation edge

    print("ProcessStateGraph self-test PASSED.")


if __name__ == "__main__":
    _self_test()
