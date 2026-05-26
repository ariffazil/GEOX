"""
epistemic/__init__.py — GEOX Epistemic Layer
==========================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Sprint 4 modules — Constitutional Recursion.

Exports:
  - assumption_lineage: AssumptionRecord, AssumptionGraph, AssumptionStatus, AssumptionType
  - epistemic_runtime: EpistemicRuntime, EpistemicEvent, EpistemicEventType
  - contradiction_ontology: ContradictionRecord, ContradictionType, ContradictionSeverity, ResolutionPath, classify_contradiction
  - anti_beautiful_one: AntiBeautifulOne, BeautyMetrics
  - meta_epistemic_audit: MetaEpistemicAuditor, MetaAuditRecord, ConstitutionalVerdict
  - godel_wall: godel_wall_check, GodelWallRecord, GodelWallVerdict, UndecidableReason, GodelWallError
"""

from .assumption_lineage import (
    AssumptionRecord,
    AssumptionGraph,
    AssumptionStatus,
    AssumptionType,
    get_assumption_graph,
    reset_assumption_graph,
)

from .epistemic_runtime import (
    EpistemicRuntime,
    EpistemicEvent,
    EpistemicEventType,
    get_or_create_runtime,
    get_runtime,
)

from .contradiction_ontology import (
    ContradictionRecord,
    ContradictionType,
    ContradictionSeverity,
    ResolutionPath,
    classify_contradiction,
    get_contradiction_record,
)

from .anti_beautiful_one import (
    AntiBeautifulOne,
    BeautyMetrics,
)

from .meta_epistemic_audit import (
    MetaEpistemicAuditor,
    MetaAuditRecord,
    ConstitutionalVerdict,
)

from .godel_wall import (
    godel_wall_check,
    check_and_raise,
    GodelWallRecord,
    GodelWallVerdict,
    UndecidableReason,
    GodelWallError,
)

__all__ = [
    # assumption_lineage
    "AssumptionRecord",
    "AssumptionGraph",
    "AssumptionStatus",
    "AssumptionType",
    "get_assumption_graph",
    "reset_assumption_graph",
    # epistemic_runtime
    "EpistemicRuntime",
    "EpistemicEvent",
    "EpistemicEventType",
    "get_or_create_runtime",
    "get_runtime",
    # contradiction_ontology
    "ContradictionRecord",
    "ContradictionType",
    "ContradictionSeverity",
    "ResolutionPath",
    "classify_contradiction",
    "get_contradiction_record",
    # anti_beautiful_one
    "AntiBeautifulOne",
    "BeautyMetrics",
    # meta_epistemic_audit
    "MetaEpistemicAuditor",
    "MetaAuditRecord",
    "ConstitutionalVerdict",
    # godel_wall
    "godel_wall_check",
    "check_and_raise",
    "GodelWallRecord",
    "GodelWallVerdict",
    "UndecidableReason",
    "GodelWallError",
]
