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

from .anti_beautiful_one import (
    AntiBeautifulOne,
    BeautyMetrics,
)
from .assumption_lineage import (
    AssumptionGraph,
    AssumptionRecord,
    AssumptionStatus,
    AssumptionType,
    get_assumption_graph,
    reset_assumption_graph,
)
from .contradiction_ontology import (
    ContradictionRecord,
    ContradictionSeverity,
    ContradictionType,
    ResolutionPath,
    classify_contradiction,
    get_contradiction_record,
)
from .epistemic_runtime import (
    EpistemicEvent,
    EpistemicEventType,
    EpistemicRuntime,
    get_or_create_runtime,
    get_runtime,
)
from .godel_wall import (
    GodelWallError,
    GodelWallRecord,
    GodelWallVerdict,
    UndecidableReason,
    check_and_raise,
    godel_wall_check,
)
from .meta_epistemic_audit import (
    ConstitutionalVerdict,
    MetaAuditRecord,
    MetaEpistemicAuditor,
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
