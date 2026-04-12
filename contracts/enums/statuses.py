# GEOX Contracts — Canonical Enums and Statuses
# DITEMPA BUKAN DIBERI — Forged, Not Given
#
# This module owns the truth for all response enums, verdicts, and statuses.
# NO runtime may define its own enums. All imports MUST come from here.

from enum import Enum
from typing import Literal


class Dimension(Enum):
    """The 7 canonical dimensions of subsurface interpretation."""
    PROSPECT = "prospect"
    WELL = "well"
    SECTION = "section"
    EARTH3D = "earth3d"
    TIME4D = "time4d"
    PHYSICS = "physics"
    MAP = "map"
    CROSS = "cross"


class Verdict(Enum):
    """Constitutional verdicts for all tool executions."""
    SEAL = "SEAL"           # 000 - Perfect alignment, execute
    COMPLY = "COMPLY"       # 101-499 - Compliant with remediation
    CAUTION = "CAUTION"     # 500-899 - Compliant with warnings
    HOLD = "HOLD"           # Awaiting human decision
    SABAR = "SABAR"         # Wait and retry
    VOID = "VOID"           # 999 - Ethical violation, blocked


class FloorStatus(Enum):
    """Status of individual constitutional floor checks."""
    PASS = "PASS"
    MARGINAL = "MARGINAL"
    FAIL = "FAIL"
    NA = "N/A"


class Runtime(Enum):
    """Supported runtime environments."""
    VPS = "vps"
    FASTMCP = "fastmcp"
    LOCAL = "local"


class Transport(Enum):
    """Supported transport protocols."""
    HTTP = "http"
    MCP = "mcp"
    STDIO = "stdio"
    SSE = "sse"


class ToolCategory(Enum):
    """Categories of tools in the GEOX ecosystem."""
    FOUNDATION = "foundation"       # Phase A - Core tools
    PHYSICS = "physics"             # Phase B - Physics engine
    BRIDGE = "bridge"               # Control/governance
    DEMO = "demo"                   # Demonstration/pilot
    SYSTEM = "system"               # Health and status


class ProspectVerdict(Enum):
    """Specific verdicts for prospect evaluation."""
    DRO = "DRO"     # Drill, but with Recommendations/Observations
    DRIL = "DRIL"   # Drill — all systems go
    HOLD = "HOLD"   # Hold — requires human review
    DROP = "DROP"   # Drop — not viable


class ClaimTag(Enum):
    """Evidence taxonomy for claims."""
    CLAIM = "CLAIM"           # Verified claim
    PLAUSIBLE = "PLAUSIBLE"   # Plausible but unverified
    HYPOTHESIS = "HYPOTHESIS" # Working hypothesis


# Type aliases for common patterns
VerdictCode = Literal["SEAL", "COMPLY", "CAUTION", "HOLD", "SABAR", "VOID"]
FloorCode = Literal["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13"]
DimensionCode = Literal["prospect", "well", "section", "earth3d", "time4d", "physics", "map", "cross"]


# The 13 constitutional floors
CONSTITUTIONAL_FLOORS = [
    "F1",   # AMANAH - Reversibility
    "F2",   # TRUTH - Accuracy
    "F3",   # TRI-WITNESS - Consensus
    "F4",   # CLARITY - Entropy reduction
    "F5",   # PEACE² - Non-destruction
    "F6",   # EMPATHY - RASA listening
    "F7",   # HUMILITY - Uncertainty acknowledgment
    "F8",   # GENIUS - Systemic health
    "F9",   # ETHICS - Anti-dark-patterns
    "F10",  # CONSCIENCE - No false consciousness claims
    "F11",  # AUDITABILITY - Transparent logs
    "F12",  # RESILIENCE - Graceful failure
    "F13",  # ADAPTABILITY - Safe evolution
]


# All tools in the GEOX ecosystem
CANONICAL_TOOLS = [
    # Foundation (Phase A)
    "geox_load_seismic_line",
    "geox_build_structural_candidates",
    "geox_evaluate_prospect",
    "geox_feasibility_check",
    "geox_verify_geospatial",
    "geox_calculate_saturation",
    "geox_query_memory",
    # Physics Engine (Phase B)
    "geox_select_sw_model",
    "geox_compute_petrophysics",
    "geox_validate_cutoffs",
    "geox_petrophysical_hold_check",
    # Bridge & Governance
    "bridge.sync_state",
    "bridge.interpret_causal_scene",
    "bridge.audit_policy_violation",
    "bridge.check_operator_legality",
    # Demo
    "geox_malay_basin_pilot",
    # System
    "geox_health",
]


# Seal constant
SEAL = "DITEMPA BUKAN DIBERI"
