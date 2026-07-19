"""
provenance_ledger.py — Per-Field Source Attribution (D3)

DITEMPA BUKAN DIBERI — Forged, not given.

Every field in the final S(x,t) tensor is annotated with:
  - source_tool: which tool/fetcher produced this value
  - source_version: version string of the tool
  - fetched_at: when the data was retrieved
  - fetch_latency_ms: how long the fetch took
  - raw_response_hash: hash of the raw response (for audit)
  - confidence: per-field confidence score (capped at 0.90 per F7)
  - gap_flag: optional GapType if this field came from a fallback

F11 AUDIT: Every VoxelState4 field must carry provenance.
F4 CLARITY: Strict Pydantic, no drift.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceEntry(BaseModel):
    """Provenance for a single field or derived parameter.

    F11 AUDIT: attaches source attribution to every value in the synthesis.
    Phase 2 additions:
      - physics9_fill: True if this field was filled by Physics9 priors
      - derivation_chain: ordered list of tools/priors that contributed
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    field_name: str = Field(
        ...,
        min_length=1,
        description="Name of the field this provenance covers (e.g. 'voxel_field', 'contrast_field', 'crust_zone')",
    )
    source_tool: str = Field(
        ...,
        min_length=1,
        description="Tool/fetcher that produced this value (e.g. 'geox_basin.macrostrat', 'vp_zone_classify')",
    )
    source_version: str = Field(
        default="unknown",
        description="Version identifier of the source tool",
    )
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the data was fetched (UTC)",
    )
    fetch_latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Response latency in milliseconds",
    )
    raw_response_hash: str = Field(
        default="",
        description="SHA-256 hash of the raw response for audit trail",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=0.90,  # F7 HUMILITY cap
        description="Confidence score for this field (0.0–0.90, F7 capped)",
    )
    gap_flag: str | None = Field(
        default=None,
        description="If this field came from a fallback/gap, the GapType (None = direct data)",
    )
    notes: str = Field(
        default="",
        description="Any additional context about the provenance",
    )
    # ── Phase 2: Physics9 fill + derivation chain ────────────────────────────
    physics9_fill: bool = Field(
        default=False,
        description="True if this field was filled from Physics9 universal priors (SANDSTONE/LIMESTONE catalog)",
    )
    derivation_chain: list[str] = Field(
        default_factory=list,
        description="Ordered list of tools/priors that contributed to this field's value",
    )

    @classmethod
    def from_response(
        cls,
        field_name: str,
        source_tool: str,
        raw_response: Any,
        confidence: float = 0.5,
        source_version: str = "unknown",
        fetch_latency_ms: float = 0.0,
        gap_flag: str | None = None,
        notes: str = "",
        physics9_fill: bool = False,
        derivation_chain: list[str] | None = None,
    ) -> ProvenanceEntry:
        """Factory: create a ProvenanceEntry from a raw response.

        Hashes the raw response for audit.
        Phase 2: supports physics9_fill flag + derivation_chain.
        """
        raw_str = str(raw_response).encode("utf-8")
        response_hash = sha256(raw_str).hexdigest()[:16]
        return cls(
            field_name=field_name,
            source_tool=source_tool,
            source_version=source_version,
            fetch_latency_ms=fetch_latency_ms,
            raw_response_hash=response_hash,
            confidence=min(confidence, 0.90),  # F7 cap enforcement
            gap_flag=gap_flag,
            notes=notes,
            physics9_fill=physics9_fill,
            derivation_chain=derivation_chain or [],
        )


class ProvenanceLedger(BaseModel):
    """Ledger holding provenance for all fields in a basin synthesis.

    F11 AUDIT: Every consequential action leaves a trace.
    Provides query methods:
      - get(field_name) → ProvenanceEntry | None
      - all_entries() → list[ProvenanceEntry]
      - confidence_summary() → per-field confidence breakdown
      - unattributed_fields(voxel) → fields without provenance
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    basin_id: str = Field(default="", description="Canonical basin identifier")
    entries: list[ProvenanceEntry] = Field(
        default_factory=list,
        description="All provenance entries in registration order",
    )

    def record(
        self,
        field_name: str,
        source_tool: str,
        raw_response: Any = "",
        confidence: float = 0.5,
        source_version: str = "unknown",
        fetch_latency_ms: float = 0.0,
        gap_flag: str | None = None,
        notes: str = "",
        physics9_fill: bool = False,
        derivation_chain: list[str] | None = None,
    ) -> ProvenanceEntry:
        """Record a new provenance entry."""
        entry = ProvenanceEntry.from_response(
            field_name=field_name,
            source_tool=source_tool,
            raw_response=raw_response,
            confidence=confidence,
            source_version=source_version,
            fetch_latency_ms=fetch_latency_ms,
            gap_flag=gap_flag,
            notes=notes,
            physics9_fill=physics9_fill,
            derivation_chain=derivation_chain,
        )
        self.entries.append(entry)
        return entry

    def get(self, field_name: str) -> ProvenanceEntry | None:
        """Get the latest provenance entry for a field."""
        for entry in reversed(self.entries):
            if entry.field_name == field_name:
                return entry
        return None

    def all_entries(self) -> list[ProvenanceEntry]:
        """Return all provenance entries."""
        return list(self.entries)

    def confidence_summary(self) -> dict[str, float]:
        """Return per-field confidence summary."""
        summary: dict[str, float] = {}
        for entry in self.entries:
            summary[entry.field_name] = entry.confidence
        return summary

    def lowest_confidence_field(self) -> ProvenanceEntry | None:
        """Return the entry with the lowest confidence."""
        if not self.entries:
            return None
        return min(self.entries, key=lambda e: e.confidence)

    @property
    def entry_count(self) -> int:
        """Total number of provenance entries."""
        return len(self.entries)

    def summary(self) -> dict[str, Any]:
        """Return a summary dict for BasinSynthesisReport."""
        return {
            "total_entries": self.entry_count,
            "confidence_summary": self.confidence_summary(),
            "lowest_confidence": (
                {
                    "field": e.field_name,
                    "confidence": e.confidence,
                    "source_tool": e.source_tool,
                }
                if (e := self.lowest_confidence_field())
                else None
            ),
            "entries": [
                {
                    "field_name": e.field_name,
                    "source_tool": e.source_tool,
                    "confidence": e.confidence,
                    "gap_flag": e.gap_flag,
                    "notes": e.notes,
                    "physics9_fill": e.physics9_fill,
                    "derivation_chain": e.derivation_chain,
                }
                for e in self.entries
            ],
        }


__all__ = [
    "ProvenanceEntry",
    "ProvenanceLedger",
]
