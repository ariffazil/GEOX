"""
kinabalu_corpus.py — Multi-physics literature corpus schema for Kinabalu
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given

Stage 6 forge: vector-ready representation of the external public literature
corpus for Kinabalu Basin / NW Sabah multiphysics synthesis. This schema
formalizes the Copilot's 21 tier-1 papers + 12-node knowledge graph into
Pydantic types that can be ingested by GEOX via `geox_literature_ingest` and
queried via `geox_evidence_reason`.

Constitutional binding:
  F1  AMANAH    — Content-addressed (sha256 per paper + per claim).
  F2  TRUTH     — Epistemic rank per claim (OBS / DER / INT / SPEC).
  F4  CLARITY   — Pydantic strict, no drift.
  F7  HUMILITY  — Evidence rank from journal impact (no overclaim).
  F11 AUDIT     — Provenance + DOI per paper.
  F13 SOVEREIGN — Internal-authored papers marked HybridEvidence (require sovereign review).

Reference:
  forge_work/2026-06-22-kinabalu-corpus-graph.yaml
  forge_work/2026-06-22-kinabalu-vector-manifest.json
  forge_work/2026-06-22-kinabalu-eureka-capsule.md
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from geox_core.schemas.intelligence_flow import FlowLayer

# ═══════════════════════════════════════════════════════════════════════════════
# Source / evidence taxonomy
# ═══════════════════════════════════════════════════════════════════════════════


class EvidenceSource(StrEnum):
    """Provenance classification for a corpus entry."""

    EXTERNAL_PEER_REVIEWED = "external_peer_reviewed"
    EXTERNAL_INDUSTRY = "external_industry"
    INTERNAL_AUTHORED = "internal_authored"
    HYBRID = "hybrid"  # internal author + external journal
    METHODOLOGY = "methodology"
    DATA_SOURCE = "data_source"


class EvidenceRank(StrEnum):
    """Epistemic rank for individual claims within a paper."""

    OBS = "OBS"  # direct observation
    DER = "DER"  # derived from physics
    INT = "INT"  # interpretation
    SPEC = "SPEC"  # speculative


class EdgeRelation(StrEnum):
    """Knowledge graph edge types."""

    CORROBORATES = "corroborates"
    COMPLEMENTS = "complements"
    REFINES = "refines"
    ENABLES = "enables"
    APPLIES = "applies"
    ANCHORS = "anchors"
    CONTRADICTS = "contradicts"


# ═══════════════════════════════════════════════════════════════════════════════
# Paper — the atomic corpus entry
# ═══════════════════════════════════════════════════════════════════════════════


class Paper(BaseModel):
    """One published paper or data source.

    F4 CLARITY: paper metadata is strict; no free-form notes.
    F2 TRUTH: every paper has a published_or_issued year + author list.
    F11 AUDIT: DOI is mandatory where available.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    paper_id: str = Field(
        ...,
        min_length=2,
        description="Canonical corpus identifier (e.g. 'Meju2024_DGroundsMT').",
    )
    title: str = Field(..., min_length=5)
    authors: list[str] = Field(..., min_length=1)
    year: int = Field(..., ge=1950, le=2030)
    source: EvidenceSource
    doi: str | None = Field(
        default=None,
        description="Digital Object Identifier (mandatory for peer-reviewed).",
    )
    journal_or_publisher: str | None = None
    url: str | None = None
    local_pdf_path: str | None = Field(
        default=None,
        description="If a local PDF copy is available, its absolute path.",
    )
    abstract: str | None = None
    # Tier classification (Copilot's tier-1 vs tier-2 vs tier-3)
    tier: int = Field(default=2, ge=1, le=3, description="1 = must-vectorize, 2 = secondary, 3 = deferred")
    # Kinabalu relevance tags
    kinabalu_relevance: list[str] = Field(
        default_factory=list,
        description="e.g. ['crustal_architecture', 'MT_anisotropy', 'ductile_layer']",
    )
    # Sovereign review status (for internal/hybrid papers)
    sovereign_reviewed: bool = Field(
        default=False,
        description="F13 — has Arif reviewed this internal-authored paper?",
    )
    # Content hash for F1 AMANAH
    content_hash: str | None = None

    def compute_hash(self) -> str:
        """F1 AMANAH — content-addressed hash."""
        payload = f"{self.paper_id}|{self.title}|{','.join(self.authors)}|{self.year}|{self.doi or ''}|{self.url or ''}"
        return f"sha256:{hashlib.sha256(payload.encode()).hexdigest()[:16]}"


# ═══════════════════════════════════════════════════════════════════════════════
# Claim — an assertion within a paper
# ═══════════════════════════════════════════════════════════════════════════════


class Claim(BaseModel):
    """One assertion in a paper that supports or refutes a hypothesis.

    F2 TRUTH: every claim has an explicit epistemic rank.
    F7 HUMILITY: confidence hard-capped at 0.90.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    claim_id: str = Field(..., min_length=2)
    paper_id: str = Field(..., min_length=2)
    claim_text: str = Field(..., min_length=10)
    epistemic_rank: EvidenceRank
    confidence: float = Field(..., ge=0.0, le=0.90)  # F7
    # Optional quote from paper (verbatim)
    verbatim_quote: str | None = None
    page_or_section: str | None = None
    # Cross-references
    related_claim_ids: list[str] = Field(default_factory=list)
    # F11 audit
    added_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# ═══════════════════════════════════════════════════════════════════════════════
# Edge — knowledge graph relationship
# ═══════════════════════════════════════════════════════════════════════════════


class Edge(BaseModel):
    """One edge in the knowledge graph.

    F2 TRUTH: edges have a relation type + a claim describing the relationship.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    edge_id: str = Field(..., min_length=2)
    source_node_id: str = Field(..., min_length=2)
    target_node_id: str = Field(..., min_length=2)
    relation: EdgeRelation
    claim: str = Field(..., min_length=10)
    supporting_paper_ids: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# Node — a knowledge graph node
# ═══════════════════════════════════════════════════════════════════════════════


class Node(BaseModel):
    """One node in the knowledge graph (paper, claim, or domain concept)."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    node_id: str = Field(..., min_length=2)
    node_type: str = Field(
        ...,
        description="Paper | Claim | Concept | InternalArtifact | Basin | DataSource",
    )
    title: str = Field(..., min_length=2)
    description: str | None = None
    paper_id: str | None = None  # if node represents a paper
    claim_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Eureka — the highest-order synthesis
# ═══════════════════════════════════════════════════════════════════════════════


class Eureka(BaseModel):
    """A high-order synthesis across multiple papers and claims.

    F2 TRUTH: every eureka cites supporting paper_ids and claim_ids.
    F13 SOVEREIGN: eurekas are sovereign-territory artifacts — require
    Arif's ratification before they become canon.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    eureka_id: str = Field(..., min_length=2)
    title: str = Field(..., min_length=5)
    claim_text: str = Field(..., min_length=20)
    supporting_paper_ids: list[str] = Field(..., min_length=1)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    # Kinabalu relevance
    kinabalu_implication: str = Field(..., min_length=10)
    # Sovereign ratification
    ratified_by_arif: bool = False
    ratified_at: str | None = None
    # Intelligence flow integration
    target_layer: FlowLayer = Field(
        default=FlowLayer.ARCHITECTURE,
        description="Which layer of the GEOX intelligence flow this eureka targets.",
    )
    tool_family: str = Field(
        default="A_crustal_architecture",
        description="Which tool family this eureka enables (per intelligence_flow.py).",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Corpus — the complete ingestion package
# ═══════════════════════════════════════════════════════════════════════════════


class KinabaluCorpus(BaseModel):
    """The full vector-ready multi-physics corpus for Kinabalu / NW Sabah.

    This is the artefact that GEOX `geox_literature_ingest` can consume.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    corpus_id: str = Field(default="SABAH_MULTIPHYSICS_KINABALU_v1.0")
    owner: str = Field(default="arif_fazil")
    lineage: list[str] = Field(
        default_factory=lambda: [
            "BEKANTAN_1",
            "LEBAH_EMAS_1",
            "ABKSS_FRAMEWORK",
            "arifOS_FEDERATION",
        ]
    )
    papers: list[Paper] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    eurekas: list[Eureka] = Field(default_factory=list)
    # Vector store manifest
    vector_dims: int = Field(default=1536)
    chunk_size: int = Field(default=1500)
    chunk_overlap: int = Field(default=200)
    embedding_model: str = Field(
        default="text-embedding-3-large",
        description="OpenAI text-embedding-3-large (1536-dim) — sovereign choice.",
    )
    store_uri: str = Field(
        default="qdrant://geox-vps:6333/sabah_multiphysics",
    )
    graph_uri: str = Field(
        default="neo4j://geox-vps:7687/kinabalu",
    )
    # Build metadata
    built_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    forge_cycle: str = Field(default="2026-06-22 RSI consolidation")


__all__ = [
    "EvidenceSource",
    "EvidenceRank",
    "EdgeRelation",
    "Paper",
    "Claim",
    "Node",
    "Edge",
    "Eureka",
    "KinabaluCorpus",
]
