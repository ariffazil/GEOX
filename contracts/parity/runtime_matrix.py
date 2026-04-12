# GEOX Contracts — Runtime Parity Matrix
# DITEMPA BUKAN DIBERI
#
# This module declares exactly what tools each runtime supports.
# This is the single source of truth for runtime capabilities.

from typing import Dict, List, Set
from contracts.enums import Runtime, Transport


# The canonical runtime matrix
RUNTIME_MATRIX: Dict[str, Dict] = {
    Runtime.VPS.value: {
        "tools": [
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
        ],
        "floors": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13"],
        "transport": Transport.HTTP.value,
        "environment": "vps",
        "features": [
            "full_physics_engine",
            "vector_memory",
            "mcp_substrates",
        ],
    },
    Runtime.FASTMCP.value: {
        "tools": [
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
        ],
        "floors": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13"],
        "transport": Transport.MCP.value,
        "environment": "cloud",
        "features": [
            "full_physics_engine",
            "streamable_http",
        ],
    },
    Runtime.LOCAL.value: {
        "tools": [
            # Limited local development set
            "geox_load_seismic_line",
            "geox_evaluate_prospect",
            "geox_feasibility_check",
            "geox_health",
        ],
        "floors": ["F1", "F2", "F9", "F10"],  # Core floors only
        "transport": Transport.STDIO.value,
        "environment": "local",
        "features": [
            "minimal_set",
        ],
    },
}


def get_runtime_tools(runtime: str) -> List[str]:
    """Get the list of tools supported by a runtime."""
    if runtime not in RUNTIME_MATRIX:
        raise ValueError(f"Unknown runtime: {runtime}")
    return RUNTIME_MATRIX[runtime]["tools"]


def get_runtime_floors(runtime: str) -> List[str]:
    """Get the list of floors enforced by a runtime."""
    if runtime not in RUNTIME_MATRIX:
        raise ValueError(f"Unknown runtime: {runtime}")
    return RUNTIME_MATRIX[runtime]["floors"]


def get_runtime_transport(runtime: str) -> str:
    """Get the transport protocol for a runtime."""
    if runtime not in RUNTIME_MATRIX:
        raise ValueError(f"Unknown runtime: {runtime}")
    return RUNTIME_MATRIX[runtime]["transport"]


def runtime_supports_tool(runtime: str, tool: str) -> bool:
    """Check if a runtime supports a specific tool."""
    if runtime not in RUNTIME_MATRIX:
        return False
    return tool in RUNTIME_MATRIX[runtime]["tools"]


def runtime_enforces_floor(runtime: str, floor: str) -> bool:
    """Check if a runtime enforces a specific floor."""
    if runtime not in RUNTIME_MATRIX:
        return False
    return floor in RUNTIME_MATRIX[runtime]["floors"]


def get_common_tools() -> Set[str]:
    """Get tools supported by ALL runtimes."""
    all_tools = [set(RUNTIME_MATRIX[rt]["tools"]) for rt in RUNTIME_MATRIX]
    return all_tools[0].intersection(*all_tools[1:]) if len(all_tools) > 1 else all_tools[0]


def get_parity_report() -> Dict:
    """Generate a parity report comparing runtimes."""
    report = {
        "runtimes": list(RUNTIME_MATRIX.keys()),
        "common_tools": sorted(get_common_tools()),
        "differences": {},
    }
    
    for runtime in RUNTIME_MATRIX:
        other_tools = set()
        for other in RUNTIME_MATRIX:
            if other != runtime:
                other_tools.update(RUNTIME_MATRIX[other]["tools"])
        
        unique_to_this = set(RUNTIME_MATRIX[runtime]["tools"]) - other_tools
        if unique_to_this:
            report["differences"][runtime] = {
                "unique_tools": sorted(unique_to_this),
            }
    
    return report


def verify_parity() -> bool:
    """Verify that VPS and FastMCP have parity."""
    vps_tools = set(RUNTIME_MATRIX[Runtime.VPS.value]["tools"])
    fastmcp_tools = set(RUNTIME_MATRIX[Runtime.FASTMCP.value]["tools"])
    
    if vps_tools != fastmcp_tools:
        missing_in_vps = fastmcp_tools - vps_tools
        missing_in_fastmcp = vps_tools - fastmcp_tools
        
        if missing_in_vps:
            raise RuntimeError(f"Parity violation: Tools in FastMCP but not VPS: {missing_in_vps}")
        if missing_in_fastmcp:
            raise RuntimeError(f"Parity violation: Tools in VPS but not FastMCP: {missing_in_fastmcp}")
    
    return True


__all__ = [
    "RUNTIME_MATRIX",
    "get_runtime_tools",
    "get_runtime_floors",
    "get_runtime_transport",
    "runtime_supports_tool",
    "runtime_enforces_floor",
    "get_common_tools",
    "get_parity_report",
    "verify_parity",
]
