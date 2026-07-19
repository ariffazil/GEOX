# GEOX Dimension-Native Registry Package
# DITEMPA BUKAN DIBERI
#
# Canonical surface: 16 sovereign public tools (Phase 2 Clean Architecture, 2026-06-22).
# Source of truth: src/geox_mcp/registry.py::CANONICAL_PUBLIC_TOOLS
from __future__ import annotations

from contracts.enums import (
    CONSTITUTIONAL_FLOORS,
    SEAL,
    ClaimTag,
    Dimension,
    FloorStatus,
    ProspectVerdict,
    Runtime,
    ToolCategory,
    Transport,
    Verdict,
)

# CANONICAL_TOOLS moved to src/geox_mcp/registry.py — import from there.
# Kept here as a re-export for backward compat during transition.
try:
    from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS as CANONICAL_TOOLS
except ImportError:
    # Fallback: derive from the old enum if registry.py not importable
    from contracts.enums.statuses import CANONICAL_TOOLS  # noqa: F401

__all__ = [
    "Dimension",
    "Verdict",
    "FloorStatus",
    "Runtime",
    "Transport",
    "ToolCategory",
    "ProspectVerdict",
    "ClaimTag",
    "CONSTITUTIONAL_FLOORS",
    "CANONICAL_TOOLS",
    "SEAL",
]
