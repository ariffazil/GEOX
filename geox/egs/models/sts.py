"""
sts.py — State Transition Surface Model
========================================
THE eureka. A basin is a state machine over space and time, not a stack of horizons.

Reality loop: observe → hypothesize states → test transitions → fork on contrast → loop.
Diachroneity is default. Translation layer bridges interpretation schemes.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ═══════════════════════════════════════════════════════════════════════════════
# BasinState — tectonostratigraphic phase
# ═══════════════════════════════════════════════════════════════════════════════


class BasinState(Enum):
    """Tectonostratigraphic phases. Extensible — add as evidence demands."""

    PRERIFT = "prerift"
    SYN_RIFT_1 = "syn_rift_1"
    SYN_RIFT_2 = "syn_rift_2"
    SYN_RIFT_N = "syn_rift_n"
    BREAKUP = "breakup"
    POST_RIFT_SAG = "post_rift_sag"
    DRIFT = "drift"
    THERMAL_SUBSIDENCE = "thermal_subsidence"
    INVERSION = "inversion"
    UPLIFT = "uplift"
    DENUDATION = "denudation"
    FORELAND = "foreland"
    PASSIVE_MARGIN_COLLAPSE = "passive_margin_collapse"
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# Diachroneity — every surface carries this
# ═══════════════════════════════════════════════════════════════════════════════


class DiachroneityClass(StrEnum):
    """No surface is isochronous unless proven. Default: strongly_diachronous."""

    ISOCHRONOUS = "isochronous"  # Proven with independent chronometric anchors
    WEAKLY_DIACHRONOUS = "weakly_diachronous"  # Near-synchronous within resolution
    STRONGLY_DIACHRONOUS = "strongly_diachronous"  # Default — diachroneity expected
    NODE_LOCAL = "node_local"  # Valid only within one BasinNode


# ═══════════════════════════════════════════════════════════════════════════════
# EvidenceTag — claim classification
# ═══════════════════════════════════════════════════════════════════════════════


class EvidenceTag(StrEnum):
    EVIDENCE = "EVIDENCE"  # Observed/measured
    INTERPRET = "INTERPRET"  # Reasoned/inferred
    UNKNOWN = "UNKNOWN"  # Missing data — gap registered


# ═══════════════════════════════════════════════════════════════════════════════
# StateTransitionSurface (STS) — the core object
# ═══════════════════════════════════════════════════════════════════════════════


class StateTransitionSurface(BaseModel):
    """A boundary between two BasinStates. Diachronous by default.

    Every STS is a hypothesis to be tested, not a fact to be defended.
    Contrast triggers fork — never force convergence.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"STS-{uuid.uuid4().hex[:12]}")
    basin_node_id: str = Field(..., description="Parent BasinNode ID")
    from_state: BasinState
    to_state: BasinState

    # Evidence foundation
    evidence_types: list[str] = Field(
        default_factory=list,
        description="e.g. seismic_facies_change, tectonic_break, sequence_geometry, "
        "biostrat_shift, unconformity, thermal_anomaly",
    )
    age_band_ma: tuple[float, float] | None = Field(default=None, description="(t_min_Ma, t_max_Ma) — bands, never single values")
    spatial_extent: dict[str, Any] | None = Field(default=None, description="GeoJSON polygon of spatial extent")
    diachroneity_class: DiachroneityClass = Field(
        default=DiachroneityClass.STRONGLY_DIACHRONOUS,
        description="Default: strongly diachronous. Isochronous requires proof.",
    )

    # Supporting picks (HorizonPick references)
    supporting_picks: list[str] = Field(default_factory=list, description="HorizonPick IDs")

    # Translation layer — semantic mapping between schemes
    translation_layer: dict[str, str] = Field(
        default_factory=dict,
        description='e.g. {"PCSB": "ROU", "TTE": "ROU_event", "Published": "ROU_Prabal2024"}',
    )

    # Epistemic state
    claim_tag: EvidenceTag = Field(default=EvidenceTag.INTERPRET)
    confidence: Literal["HIGH", "MED", "LOW"] = "MED"

    # Audit
    provenance: list[dict[str, str]] = Field(
        default_factory=list,
        description="[{'step':'hypothesize','hash':'sha256:...','ts':'ISO-8601'}]",
    )
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @field_validator("from_state", "to_state")
    @classmethod
    def _states_must_differ(cls, v: BasinState, info: Any) -> BasinState:
        # Skip cross-field check here — handled at StateGraph level
        return v


# ═══════════════════════════════════════════════════════════════════════════════
# BasinNode — a structural compartment with its own state graph
# ═══════════════════════════════════════════════════════════════════════════════


class BasinNode(BaseModel):
    """A structural/compartmental sub-basin. Owns its own state graph.

    A regional basin is a graph of BasinNodes connected by coupling edges.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"BN-{uuid.uuid4().hex[:12]}")
    name: str = Field(..., description="Human-readable name (e.g. 'Kinabalu Deep')")
    parent_basin_id: str = Field(default="", description="Parent Basin ID (EarthGraph)")
    description: str = Field(default="")

    # States this node has experienced
    states: list[BasinState] = Field(default_factory=list, description="Ordered list of states this node has passed through")

    # Geometry
    bbox: tuple[float, float, float, float] | None = Field(default=None, description="(min_lon, min_lat, max_lon, max_lat)")

    # Deep-state hypotheses (not facts — tagged UNKNOWN, path to test)
    candidate_states: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'state': BasinState, 'confidence': LOW, 'test_path': '...'}]",
    )

    claim_tag: EvidenceTag = Field(default=EvidenceTag.INTERPRET)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# ═══════════════════════════════════════════════════════════════════════════════
# StateGraph — the graph of BasinNodes + STS edges
# ═══════════════════════════════════════════════════════════════════════════════


class StateGraph(BaseModel):
    """G_n = (V_n, E_n) — state machine for one or more BasinNodes.

    Regional model: G_region = ⋃ G_n + inter-node coupling edges.
    This is the reality loop engine.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"SG-{uuid.uuid4().hex[:12]}")
    name: str = Field(..., description="e.g. 'Kinabalu State Graph'")
    basin_id: str = Field(default="", description="Parent Basin ID")

    # Nodes = BasinNodes (sub-basin compartments)
    nodes: dict[str, BasinNode] = Field(default_factory=dict)

    # Edges = StateTransitionSurfaces (transitions between states)
    transitions: dict[str, StateTransitionSurface] = Field(default_factory=dict)

    # Inter-node coupling (edges between BasinNodes)
    coupling_edges: list[tuple[str, str, str]] = Field(
        default_factory=list,
        description="[(from_node_id, to_node_id, relation_type), ...]",
    )

    # Open contrast flags (need scenario fork)
    open_contrasts: list[str] = Field(default_factory=list, description="ContrastFlag IDs requiring resolution")

    version: int = Field(default=1)
    claim_tag: EvidenceTag = Field(default=EvidenceTag.INTERPRET)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    # ── Operations ──────────────────────────────────────────────────────────

    def add_node(self, node: BasinNode) -> str:
        """Add a BasinNode. Returns node_id."""
        self.nodes[node.id] = node
        self.version += 1
        return node.id

    def add_transition(self, sts: StateTransitionSurface) -> str:
        """Add an STS edge. Validates that nodes exist and states differ."""
        if sts.basin_node_id not in self.nodes:
            raise ValueError(f"BasinNode {sts.basin_node_id} not in graph. Add node first.")
        if sts.from_state == sts.to_state:
            raise ValueError(f"STS {sts.id}: from_state and to_state must differ ({sts.from_state.value})")
        self.transitions[sts.id] = sts
        self.version += 1
        return sts.id

    def get_node_state_sequence(self, node_id: str) -> list[BasinState]:
        """Return the ordered state sequence for a BasinNode."""
        node = self.nodes.get(node_id)
        if node is None:
            raise ValueError(f"BasinNode {node_id} not found")
        return node.states

    def get_transitions_for_node(self, node_id: str) -> list[StateTransitionSurface]:
        """Return all STS edges for a given BasinNode."""
        return [t for t in self.transitions.values() if t.basin_node_id == node_id]

    def emit_contrast(
        self, sts_a_id: str, sts_b_id: str, delta_metric: str, delta_value: float, threshold: float
    ) -> dict[str, Any]:
        """Emit a ContrastFlag when two STS disagree beyond threshold. Fork scenarios."""
        contrast_id = f"CF-{uuid.uuid4().hex[:12]}"
        self.open_contrasts.append(contrast_id)
        self.version += 1
        return {
            "contrast_id": contrast_id,
            "object_a": sts_a_id,
            "object_b": sts_b_id,
            "delta_metric": delta_metric,
            "delta_value": delta_value,
            "threshold": threshold,
            "action": "fork_scenarios",
            "rule": "never force convergence when credible sources disagree beyond threshold",
        }

    def to_summary(self) -> dict[str, Any]:
        """Reality loop summary — what the graph knows right now."""
        return {
            "graph_id": self.id,
            "name": self.name,
            "basin_id": self.basin_id,
            "num_nodes": len(self.nodes),
            "num_transitions": len(self.transitions),
            "num_coupling_edges": len(self.coupling_edges),
            "open_contrasts": len(self.open_contrasts),
            "version": self.version,
            "nodes": [{"id": n.id, "name": n.name, "states": [s.value for s in n.states]} for n in self.nodes.values()],
            "transitions": [
                {
                    "id": t.id,
                    "node": t.basin_node_id,
                    "from": t.from_state.value,
                    "to": t.to_state.value,
                    "diachroneity": t.diachroneity_class.value,
                    "confidence": t.confidence,
                }
                for t in self.transitions.values()
            ],
        }
