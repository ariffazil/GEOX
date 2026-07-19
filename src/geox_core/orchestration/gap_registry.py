"""
gap_registry.py — Gap Taxonomy for Basin Synthesis Pipeline (D4)

DITEMPA BUKAN DIBERI — Forged, not given.

7 canonical gap types per the blueprint:
  GAP_TECTONIC_SKELETON — GPlates + earthquake both fail
  GAP_STRAT_COLUMN      — Macrostrat + OneGeology + existing profile all fail
  GAP_CRUST_VP          — No Vp data, Moho estimate from ICGEM only
  GAP_THERMAL           — No IHFC data, crustal-type proxy only
  GAP_DEEP_TIME         — Deep time state failed — abort pipeline
  GAP_GEOMECHANICS      — Stage 7 cannot derive from stages 2+5 — abort
  GAP_VOXEL_OBSERVATION — Zero wells/seismic in bbox — voxels from priors only

Each registered gap carries:
  - gap_type: canonical GapType enum
  - stage: pipeline stage that triggered the gap
  - detail: human-readable description of what's missing
  - fallback_used: what was used instead (or None if abort)

F2 TRUTH: When a fetcher returns nothing, we register a Gap — never fabricate.
F4 CLARITY: Strict Pydantic, no drift.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GapType(StrEnum):
    """Canonical gap taxonomy — 8 named data/knowledge gaps.

    Phase 2 addition: GAP_CONVERGENCE for strange loop non-convergence.
    """

    GAP_TECTONIC_SKELETON = "GAP_TECTONIC_SKELETON"
    GAP_STRAT_COLUMN = "GAP_STRAT_COLUMN"
    GAP_CRUST_VP = "GAP_CRUST_VP"
    GAP_THERMAL = "GAP_THERMAL"
    GAP_DEEP_TIME = "GAP_DEEP_TIME"
    GAP_GEOMECHANICS = "GAP_GEOMECHANICS"
    GAP_VOXEL_OBSERVATION = "GAP_VOXEL_OBSERVATION"
    # Phase 2: Strange loop did not converge
    GAP_CONVERGENCE = "GAP_CONVERGENCE"


# Severity classification
ABORT_GAPS: set[GapType] = {GapType.GAP_DEEP_TIME, GapType.GAP_GEOMECHANICS}
WARNING_GAPS: set[GapType] = {
    GapType.GAP_TECTONIC_SKELETON,
    GapType.GAP_STRAT_COLUMN,
    GapType.GAP_CRUST_VP,
    GapType.GAP_THERMAL,
    GapType.GAP_VOXEL_OBSERVATION,
    GapType.GAP_CONVERGENCE,
}


class GapEntry(BaseModel):
    """A single registered data/knowledge gap.

    F2 TRUTH: documents what failed and what fallback was used.
    F4 CLARITY: strict typing, no free-text drift.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    gap_type: GapType = Field(description="Canonical gap type from the 7-type taxonomy")
    stage: int = Field(ge=1, le=11, description="Pipeline stage (1-11) that triggered this gap")
    detail: str = Field(
        default="No detail provided",
        description="Human-readable description of what data is missing and why",
    )
    fallback_used: str | None = Field(
        default=None,
        description="What proxy / fallback / prior was used instead (None if pipeline aborted)",
    )
    gap_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence of the fallback data (0.0 = complete gap, 1.0 = proxy with full confidence)",
    )
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the gap was registered (UTC)",
    )


class GapRegistry(BaseModel):
    """Registry holding all gaps encountered during a basin synthesis run.

    Provides query methods:
      - has_abort_gaps() → True if any ABORT gap registered (pipeline must halt)
      - abort_gaps() → list of GAP_DEEP_TIME / GAP_GEOMECHANICS entries
      - warning_gaps() → non-abort gaps that reduce confidence
      - summary() → dict summary for reporting
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    basin_id: str = Field(default="", description="Canonical basin identifier")
    entries: list[GapEntry] = Field(
        default_factory=list,
        description="All registered gaps in order of registration",
    )

    def register(
        self,
        gap_type: GapType,
        stage: int,
        detail: str = "",
        fallback_used: str | None = None,
        gap_confidence: float = 0.0,
    ) -> GapEntry:
        """Register a new gap and return the entry."""
        entry = GapEntry(
            gap_type=gap_type,
            stage=stage,
            detail=detail,
            fallback_used=fallback_used,
            gap_confidence=gap_confidence,
        )
        self.entries.append(entry)
        return entry

    def has_abort_gaps(self) -> bool:
        """True if any abort-level gap (DEEP_TIME or GEOMECHANICS) is registered."""
        return any(e.gap_type in ABORT_GAPS for e in self.entries)

    def abort_gaps(self) -> list[GapEntry]:
        """Return only gaps that abort the pipeline."""
        return [e for e in self.entries if e.gap_type in ABORT_GAPS]

    def warning_gaps(self) -> list[GapEntry]:
        """Return gaps that warn but don't abort."""
        return [e for e in self.entries if e.gap_type in WARNING_GAPS]

    def has_gap(self, gap_type: GapType) -> bool:
        """Check if a specific gap type has been registered."""
        return any(e.gap_type == gap_type for e in self.entries)

    @property
    def gap_count(self) -> int:
        """Total number of registered gaps."""
        return len(self.entries)

    def summary(self) -> dict[str, Any]:
        """Return a summary dict for BasinSynthesisReport."""
        return {
            "total_gaps": self.gap_count,
            "abort_gaps": [e.gap_type.value for e in self.abort_gaps()],
            "warning_gaps": [e.gap_type.value for e in self.warning_gaps()],
            "entries": [
                {
                    "gap_type": e.gap_type.value,
                    "stage": e.stage,
                    "detail": e.detail,
                    "fallback_used": e.fallback_used,
                    "gap_confidence": e.gap_confidence,
                }
                for e in self.entries
            ],
        }


__all__ = [
    "GapType",
    "GapEntry",
    "GapRegistry",
    "ABORT_GAPS",
    "WARNING_GAPS",
]
