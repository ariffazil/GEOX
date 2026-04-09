"""
geox_mcp_server.py — GEOX MCP Server for arifOS
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

DEPRECATION NOTICE:
This file is now a thin backward-compatible wrapper around the refactored
host-agnostic architecture. The actual implementation has been moved to:

  - arifos/geox/tools/core.py           (domain logic)
  - arifos/geox/tools/services/         (service layer)
  - arifos/geox/contracts/types.py      (type definitions)
  - arifos/geox/tools/adapters/fastmcp_adapter.py  (FastMCP transport)

For new development, import directly from the modular structure:
  from arifos.geox.tools.core import geox_evaluate_prospect
  from arifos.geox.tools.adapters.fastmcp_adapter import mcp

This wrapper maintains backward compatibility with existing deployments
while the ecosystem migrates to the new host-agnostic architecture.

MIGRATION PATH:
  Old: from geox_mcp_server import mcp
  New: from arifos.geox.tools.adapters.fastmcp_adapter import mcp
"""

from __future__ import annotations

import warnings

# Emit deprecation warning
warnings.warn(
    "geox_mcp_server.py is deprecated. "
    "Use arifos.geox.tools.adapters.fastmcp_adapter for FastMCP transport, "
    "or arifos.geox.tools.core for host-agnostic tools. "
    "See GEOX_MCP_APPS_ARCHITECTURE.md for migration guide.",
    DeprecationWarning,
    stacklevel=2,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Re-export from new architecture (backward compatibility)
# ═══════════════════════════════════════════════════════════════════════════════

# FastMCP server instance (primary export)
from arifos.geox.tools.adapters.fastmcp_adapter import (
    mcp,
    main,
    create_server,
    GEOX_VERSION,
    GEOX_SEAL,
    HAS_HTTP_ROUTES,
)

# Core tools (for direct programmatic use)
from arifos.geox.tools.core import (
    geox_load_seismic_line,
    geox_build_structural_candidates,
    geox_feasibility_check,
    geox_verify_geospatial,
    geox_evaluate_prospect,
    geox_query_memory,
    geox_calculate_saturation,
    geox_select_sw_model,
    geox_compute_petrophysics,
    geox_validate_cutoffs,
    geox_petrophysical_hold_check,
    geox_health,
)

# Type contracts (for type checking)
from arifos.geox.contracts.types import (
    GeoXResult,
    GeoXStatus,
    SeismicLineResult,
    StructuralCandidatesResult,
    ProspectEvaluationResult,
    FeasibilityResult,
    GeospatialVerificationResult,
    MemoryQueryResult,
    SwCalculationResult,
    SwModelAdmissibilityResult,
    PetrophysicsResult,
    CutoffValidationResult,
    PetrophysicsHoldResult,
    HealthResult,
)

__version__ = GEOX_VERSION
__seal__ = GEOX_SEAL

__all__ = [
    # Server
    "mcp",
    "main",
    "create_server",
    "GEOX_VERSION",
    "GEOX_SEAL",
    "HAS_HTTP_ROUTES",
    # Tools
    "geox_load_seismic_line",
    "geox_build_structural_candidates",
    "geox_feasibility_check",
    "geox_verify_geospatial",
    "geox_evaluate_prospect",
    "geox_query_memory",
    "geox_calculate_saturation",
    "geox_select_sw_model",
    "geox_compute_petrophysics",
    "geox_validate_cutoffs",
    "geox_petrophysical_hold_check",
    "geox_health",
    # Types
    "GeoXResult",
    "GeoXStatus",
    "SeismicLineResult",
    "StructuralCandidatesResult",
    "ProspectEvaluationResult",
    "FeasibilityResult",
    "GeospatialVerificationResult",
    "MemoryQueryResult",
    "SwCalculationResult",
    "SwModelAdmissibilityResult",
    "PetrophysicsResult",
    "CutoffValidationResult",
    "PetrophysicsHoldResult",
    "HealthResult",
]

# ═══════════════════════════════════════════════════════════════════════════════
# Backward-compatible CLI entrypoint
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
