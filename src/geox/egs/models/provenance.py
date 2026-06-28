"""
provenance.py — Provenance Records for EGS
============================================
GEOX EGS: ProvenanceRecord, EvidenceRef, version history.

Every earth state change carries a provenance trail.
DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Provenance Types
# ═══════════════════════════════════════════════════════════════════════════════


class ProvenanceAction(str, Enum):
    """The type of action that produced this provenance record."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    MERGED = "merged"
    SPLIT = "split"
    INTERPRETED = "interpreted"
    VALIDATED = "validated"
    CHALLENGED = "challenged"
    RETRACTED = "retracted"
    SEALED = "sealed"
    IMPORTED = "imported"
    COMPUTED = "computed"


class ProvenanceAgentKind(str, Enum):
    """The type of agent that performed the action."""

    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"


class ProvenanceRecord(BaseModel):
    """A single provenance record describing how an earth state came to be."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    action: ProvenanceAction = Field(..., description="What was done")
    agent: str = Field(..., description="Who/what performed the action")
    agent_kind: ProvenanceAgentKind = Field(default=ProvenanceAgentKind.UNKNOWN, description="Type of agent")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = Field(default="", description="Free-text description")
    entity_type: str = Field(default="", description="Type of entity affected")
    entity_id: str = Field(default="", description="ID of entity affected")
    previous_version: int | None = Field(default=None, description="Version before change")
    new_version: int | None = Field(default=None, description="Version after change")
    evidence_refs: list[str] = Field(default_factory=list, description="IDs of evidence supporting this change")
    parent_provenance_id: str | None = Field(default=None, description="Parent record (for branching)")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    notes: str = Field(default="")


# ═══════════════════════════════════════════════════════════════════════════════
# Evidence Reference
# ═══════════════════════════════════════════════════════════════════════════════


class EvidenceKind(str, Enum):
    """The nature of the evidence."""

    WELL_LOG = "well_log"
    SEISMIC = "seismic"
    CORE = "core"
    OUTCROP = "outcrop"
    DST = "dst"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    GEOCHEMICAL = "geochemical"
    BIOSTRAT = "biostrat"
    REMOTE_SENSING = "remote_sensing"
    GRAVITY = "gravity"
    MAGNETIC = "magnetic"
    EM = "em"
    ANALOGUE = "analogue"
    LITERATURE = "literature"
    COMPUTED = "computed"
    INTERPRETATION = "interpretation"
    OTHER = "other"


class EvidenceStrength(str, Enum):
    """Strength of the evidence."""

    DIRECT_MEASUREMENT = "direct_measurement"
    CALIBRATED_DERIVED = "calibrated_derived"
    MULTIPLE_LINES = "multiple_lines"
    SINGLE_LINE = "single_line"
    ANALOGUE_INFERRED = "analogue_inferred"
    SPECULATIVE = "speculative"
    CONTRADICTED = "contradicted"


class EvidenceRef(BaseModel):
    """A reference to evidence supporting or challenging an earth state claim."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    evidence_kind: EvidenceKind = Field(..., description="Type of evidence")
    strength: EvidenceStrength = Field(default=EvidenceStrength.SINGLE_LINE, description="Perceived strength")
    description: str = Field(..., description="What the evidence says")
    source: str = Field(default="", description="Where the evidence comes from")
    url: str | None = Field(default=None, description="URL to evidence artifact")
    file_path: str | None = Field(default=None, description="Local file path")
    supporting: bool = Field(default=True, description="Does it support or challenge the claim?")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = Field(default="", description="Who recorded this evidence")
    uncertainty: str = Field(default="", description="Uncertainty associated with this evidence")
    tags: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# Provenance Chain
# ═══════════════════════════════════════════════════════════════════════════════


class ProvenanceChain(BaseModel):
    """An ordered chain of provenance records for a single entity."""

    model_config = ConfigDict(extra="forbid")
    entity_id: str = Field(..., description="Entity this chain tracks")
    entity_type: str = Field(..., description="Entity type")
    records: list[ProvenanceRecord] = Field(default_factory=list, description="Ordered provenance records")
    current_version: int = Field(default=0, description="Current entity version")

    def add_record(self, record: ProvenanceRecord) -> None:
        """Append a provenance record."""
        self.records.append(record)
        if record.new_version:
            self.current_version = record.new_version

    def get_history(self, limit: int = 10) -> list[ProvenanceRecord]:
        """Get the most recent provenance records."""
        return list(reversed(self.records[-limit:]))

    def get_record(self, record_id: str) -> ProvenanceRecord | None:
        for r in self.records:
            if r.id == record_id:
                return r
        return None
