"""
geox_core.orchestration — Basin Synthesis Pipeline Conductor

DITEMPA BUKAN DIBERI — Forged, not given.

Phase 1: All fetchers mocked. Substrate-only autonomous forge.
Phase 2: Real fetcher wiring (propose-only).
Phase 3: Validation basins (888_HOLD required).

Exports the 5 modules that compose the basin synthesis pipeline:
    - SynthesisState (D2): Tracks pipeline state across 11 stages
    - ProvenanceLedger (D3): Per-field source attribution
    - GapRegistry (D4): Gap taxonomy — 7 named gap types
    - UncertaintyCascade (D5): Confidence propagation math
    - BasinSynthesisPipeline (D1): Main async orchestrator
"""

from geox_core.orchestration.basin_synthesis_pipeline import (
    BasinSynthesisPipeline,
    BasinSynthesisReport,
    PipelineStage,
)
from geox_core.orchestration.gap_registry import GapRegistry, GapType
from geox_core.orchestration.provenance_ledger import (
    ProvenanceEntry,
    ProvenanceLedger,
)
from geox_core.orchestration.synthesis_state import SynthesisState
from geox_core.orchestration.uncertainty_cascade import (
    UncertaintyCascade,
    cap_confidence,
    cascade_noisy_or,
    cascade_parallel,
    cascade_serial,
)

__all__ = [
    # D2
    "SynthesisState",
    # D3
    "ProvenanceLedger",
    "ProvenanceEntry",
    # D4
    "GapRegistry",
    "GapType",
    # D5
    "cascade_serial",
    "cascade_parallel",
    "cascade_noisy_or",
    "cap_confidence",
    "UncertaintyCascade",
    # D1
    "BasinSynthesisPipeline",
    "BasinSynthesisReport",
    "PipelineStage",
]
