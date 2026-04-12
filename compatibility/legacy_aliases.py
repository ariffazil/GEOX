# GEOX Compatibility — Legacy Aliases
# DITEMPA BUKAN DIBERI
#
# ⚠️ DEPRECATED: This module contains legacy aliases for backward compatibility.
# New code should import directly from contracts.*
#
# This quarantine zone prevents contract drift by centralizing all legacy names.

import warnings

# Emit deprecation warnings
warnings.warn(
    "compatibility.legacy_aliases is deprecated. "
    "Import from contracts.* instead.",
    DeprecationWarning,
    stacklevel=2
)

# ═══════════════════════════════════════════════════════════════════════════════
# ENUM ALIASES (from contracts.enums)
# ═══════════════════════════════════════════════════════════════════════════════

from contracts.enums import (
    Dimension as _Dimension,
    Verdict as _Verdict,
    FloorStatus as _FloorStatus,
    Runtime as _Runtime,
    Transport as _Transport,
    ToolCategory as _ToolCategory,
    ProspectVerdict as _ProspectVerdict,
    ClaimTag as _ClaimTag,
    CONSTITUTIONAL_FLOORS as _CONSTITUTIONAL_FLOORS,
    CANONICAL_TOOLS as _CANONICAL_TOOLS,
    SEAL as _SEAL,
)

# Legacy names (pre-constitution)
Dimension = _Dimension
Verdict = _Verdict
FloorStatus = _FloorStatus
Runtime = _Runtime
Transport = _Transport
ToolCategory = _ToolCategory
ProspectVerdict = _ProspectVerdict
ClaimTag = _ClaimTag
CONSTITUTIONAL_FLOORS = _CONSTITUTIONAL_FLOORS
CANONICAL_TOOLS = _CANONICAL_TOOLS
SEAL = _SEAL

# ═══════════════════════════════════════════════════════════════════════════════
# TOOL ALIASES (legacy geox_* namespace)
# ═══════════════════════════════════════════════════════════════════════════════

# These aliases allow old code to use geox_* names while the canonical
# contracts use clean tool definitions.

# Foundation tools
geox_load_seismic_line = "geox_load_seismic_line"
geox_build_structural_candidates = "geox_build_structural_candidates"
geox_evaluate_prospect = "geox_evaluate_prospect"
geox_feasibility_check = "geox_feasibility_check"
geox_verify_geospatial = "geox_verify_geospatial"
geox_calculate_saturation = "geox_calculate_saturation"
geox_query_memory = "geox_query_memory"

# Physics Engine tools
geox_select_sw_model = "geox_select_sw_model"
geox_compute_petrophysics = "geox_compute_petrophysics"
geox_validate_cutoffs = "geox_validate_cutoffs"
geox_petrophysical_hold_check = "geox_petrophysical_hold_check"

# Bridge tools
bridge_sync_state = "bridge.sync_state"
bridge_interpret_causal_scene = "bridge.interpret_causal_scene"
bridge_audit_policy_violation = "bridge.audit_policy_violation"
bridge_check_operator_legality = "bridge.check_operator_legality"

# Demo tools
geox_malay_basin_pilot = "geox_malay_basin_pilot"

# System tools
geox_health = "geox_health"


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY REGISTRY ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

# Old registry module names map to new structure
LEGACY_REGISTRY_MAP = {
    "registries.common": "contracts.enums.statuses",
    "registries.prospect": "registries.prospect",  # Stays in registries
    "registries.well": "registries.well",
    "registries.section": "registries.section",
    "registries.earth3d": "registries.earth3d",
    "registries.time4d": "registries.time4d",
    "registries.physics": "registries.physics",
    "registries.map": "registries.map",
    "registries.cross": "registries.cross",
}


def resolve_legacy_import(module_name: str) -> str:
    """Resolve a legacy module name to its new location."""
    if module_name in LEGACY_REGISTRY_MAP:
        new_module = LEGACY_REGISTRY_MAP[module_name]
        warnings.warn(
            f"{module_name} is deprecated. Use {new_module} instead.",
            DeprecationWarning,
            stacklevel=3
        )
        return new_module
    return module_name


__all__ = [
    # Enums
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
    # Tool name aliases
    "geox_load_seismic_line",
    "geox_build_structural_candidates",
    "geox_evaluate_prospect",
    "geox_feasibility_check",
    "geox_verify_geospatial",
    "geox_calculate_saturation",
    "geox_query_memory",
    "geox_select_sw_model",
    "geox_compute_petrophysics",
    "geox_validate_cutoffs",
    "geox_petrophysical_hold_check",
    "bridge_sync_state",
    "bridge_interpret_causal_scene",
    "bridge_audit_policy_violation",
    "bridge_check_operator_legality",
    "geox_malay_basin_pilot",
    "geox_health",
    # Functions
    "resolve_legacy_import",
]
