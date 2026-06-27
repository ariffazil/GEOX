"""
synthesis_state.py — Pipeline State Tracker (D2)

DITEMPA BUKAN DIBERI — Forged, not given.

Tracks the state of a basin synthesis pipeline run across all 11 stages.
Each stage records:
  - completion status
  - primitives/tools invoked
  - fallback paths taken
  - gaps registered
  - confidence allocation

F4 CLARITY: Strict Pydantic, no drift.
F13 SOVEREIGN: No self-elevation — this is a state record, not a judge.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class StageStatus(StrEnum):
    """Status of a pipeline stage."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FALLBACK_USED = "fallback_used"
    GAP_REGISTERED = "gap_registered"
    ABORTED = "aborted"


class PrimitiveInvocation(BaseModel):
    """Record of a single primitive/tool invocation within a stage."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    tool_name: str = Field(..., min_length=1, description="Name of the tool/fetcher invoked")
    mode: str = Field(default="default", description="Mode/operation used")
    invoked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the tool was invoked (UTC)",
    )
    latency_ms: float = Field(default=0.0, ge=0.0, description="Response latency in ms")
    success: bool = Field(default=False, description="Whether the call succeeded")
    error_detail: str = Field(default="", description="Error message if failed")
    fallback_used: Optional[str] = Field(default=None, description="Fallback tool used if primary failed")
    raw_response_hash: str = Field(default="", description="Hash of response for audit")


class StageRecord(BaseModel):
    """Record of a single pipeline stage execution."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    stage: int = Field(ge=1, le=11, description="Stage number (1-11)")
    name: str = Field(..., min_length=1, description="Stage name (e.g. 'resolve', 'tectonic_skeleton')")
    status: StageStatus = Field(default=StageStatus.PENDING, description="Current stage status")
    started_at: Optional[datetime] = Field(default=None, description="When stage started")
    completed_at: Optional[datetime] = Field(default=None, description="When stage completed")
    primitives_invoked: list[PrimitiveInvocation] = Field(default_factory=list, description="All tool invocations in this stage")
    fallback_path_taken: Optional[str] = Field(default=None, description="Which fallback chain was used (if any)")
    confidence: float = Field(default=0.0, ge=0.0, le=0.90, description="Stage-level confidence (F7 capped)")
    outputs_summary: dict[str, Any] = Field(default_factory=dict, description="Key outputs from this stage")
    notes: str = Field(default="", description="Any contextual notes")


class SynthesisState(BaseModel):
    """Master state tracker for a basin synthesis pipeline run.

    Tracks: basin identification, stage completion, primitives invoked,
    fallback paths, gaps, and per-stage uncertainty.

    F4 CLARITY: Every field is typed and validated.
    F13 SOVEREIGN: No auto-judgment — this is state tracking, not deliberation.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    basin_id: str = Field(default="", description="Canonical basin identifier")
    basin_name: str = Field(default="", description="Requested basin name (input)")
    run_id: str = Field(
        default="",
        description="Unique run identifier (e.g. 'synthesis-2026-06-26-001')",
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Pipeline start time (UTC)",
    )
    completed_at: Optional[datetime] = Field(default=None, description="Pipeline completion time (UTC)")
    aborted: bool = Field(default=False, description="True if pipeline was aborted")
    abort_reason: str = Field(default="", description="Why pipeline aborted (if applicable)")

    # ── Phase 2: STRANGE LOOP tracking ───────────────────────────────────────
    iteration_count: int = Field(
        default=0,
        ge=0,
        description="Number of strange loop iterations completed (0 = first pass)",
    )
    convergence_threshold: float = Field(
        default=0.01,
        ge=0.0,
        le=1.0,
        description="ΔS threshold for strange loop convergence",
    )
    max_iterations: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum strange loop iterations before accepting best result",
    )
    previous_s_state: Optional[dict[str, Any]] = Field(
        default=None,
        description="S(x,t) from previous iteration for ΔS computation",
    )
    delta_S_history: list[float] = Field(
        default_factory=list,
        description="ΔS per iteration for convergence tracking",
    )
    converged: bool = Field(
        default=False,
        description="True if strange loop converged (ΔS < convergence_threshold)",
    )

    stages: dict[int, StageRecord] = Field(
        default_factory=dict,
        description="Stage records keyed by stage number (1-11)",
    )

    @property
    def current_stage(self) -> int:
        """Current stage number (first pending, or 11 if all complete)."""
        for i in range(1, 12):
            if i not in self.stages or self.stages[i].status in (
                StageStatus.PENDING,
                StageStatus.IN_PROGRESS,
            ):
                return i
        return 11

    @property
    def stages_completed(self) -> int:
        """Number of stages that reached COMPLETED or FALLBACK_USED status."""
        return sum(1 for s in self.stages.values() if s.status in (StageStatus.COMPLETED, StageStatus.FALLBACK_USED))

    def start_stage(self, stage: int, name: str) -> StageRecord:
        """Mark a stage as in-progress and return its record."""
        record = StageRecord(
            stage=stage,
            name=name,
            status=StageStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
        )
        self.stages[stage] = record
        return record

    def complete_stage(
        self,
        stage: int,
        confidence: float = 0.5,
        outputs: Optional[dict[str, Any]] = None,
        fallback_used: Optional[str] = None,
        notes: str = "",
    ) -> StageRecord:
        """Mark a stage as completed (or fallback_used)."""
        record = self.stages.get(stage)
        if record is None:
            record = self.start_stage(stage, f"stage_{stage}")
        record.completed_at = datetime.now(timezone.utc)
        record.status = StageStatus.FALLBACK_USED if fallback_used else StageStatus.COMPLETED
        record.fallback_path_taken = fallback_used
        record.confidence = min(confidence, 0.90)
        if outputs:
            record.outputs_summary.update(outputs)
        if notes:
            record.notes = notes
        self.stages[stage] = record
        return record

    def abort_stage(self, stage: int, reason: str) -> StageRecord:
        """Mark a stage as aborted (pipeline halt)."""
        record = self.stages.get(stage)
        if record is None:
            record = self.start_stage(stage, f"stage_{stage}")
        record.status = StageStatus.ABORTED
        record.completed_at = datetime.now(timezone.utc)
        record.notes = f"ABORTED: {reason}"
        self.stages[stage] = record
        self.aborted = True
        self.abort_reason = reason
        self.completed_at = datetime.now(timezone.utc)
        return record

    def record_invocation(
        self,
        stage: int,
        tool_name: str,
        mode: str = "default",
        success: bool = False,
        latency_ms: float = 0.0,
        error_detail: str = "",
        fallback_used: Optional[str] = None,
        raw_response_hash: str = "",
    ) -> PrimitiveInvocation:
        """Log a tool invocation within a stage."""
        record = self.stages.get(stage)
        if record is None:
            record = self.start_stage(stage, f"stage_{stage}")
        invocation = PrimitiveInvocation(
            tool_name=tool_name,
            mode=mode,
            success=success,
            latency_ms=latency_ms,
            error_detail=error_detail,
            fallback_used=fallback_used,
            raw_response_hash=raw_response_hash,
        )
        record.primitives_invoked.append(invocation)
        return invocation

    @property
    def total_primitives_invoked(self) -> int:
        """Total tool invocations across all stages."""
        return sum(len(s.primitives_invoked) for s in self.stages.values())

    def summary(self) -> dict[str, Any]:
        """Return a summary dict for BasinSynthesisReport."""
        return {
            "basin_id": self.basin_id,
            "basin_name": self.basin_name,
            "run_id": self.run_id,
            "aborted": self.aborted,
            "abort_reason": self.abort_reason if self.aborted else None,
            "stages_completed": self.stages_completed,
            "current_stage": self.current_stage,
            "total_primitives_invoked": self.total_primitives_invoked,
            # Phase 2: STRANGE LOOP convergence
            "iteration_count": self.iteration_count,
            "convergence_threshold": self.convergence_threshold,
            "max_iterations": self.max_iterations,
            "converged": self.converged,
            "delta_S_history": self.delta_S_history,
            "stage_summary": {
                s.stage: {
                    "name": s.name,
                    "status": s.status.value,
                    "confidence": s.confidence,
                    "primitives_called": len(s.primitives_invoked),
                    "fallback_used": s.fallback_path_taken,
                }
                for s in sorted(self.stages.values(), key=lambda x: x.stage)
                if s.stage in self.stages
            },
        }


__all__ = [
    "StageStatus",
    "PrimitiveInvocation",
    "StageRecord",
    "SynthesisState",
]
