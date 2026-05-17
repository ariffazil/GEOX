"""
GEOX Parity Matrix 
═══════════════════════════════════════════════════════════════════════════════
Single source of truth for declaring tool support across the FastMCP (Control Plane)
and VPS (Execution Plane) runtimes.
"""

from typing import Dict, List, Literal

RuntimeType = Literal["fastmcp", "vps"]
ParityStatus = Literal["FULL", "PARTIAL", "DEPRECATED"]

# Example Parity Declaration
# "geox.well.compute_petrophysics": {
#     "fastmcp": "FULL",
#     "vps": "FULL",
#     "public": True
# }

RUNTIME_PARITY_MATRIX: Dict[str, Dict[str, str | bool | List[str]]] = {
    # ─── PROSPECT DIMENSION ──────────────────────────────────────────
    "geox_prospect_evaluate": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },
    "geox_prospect_build_structural_candidates": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },
    "geox_prospect_verify_feasibility": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },

    # ─── WELL DIMENSION ──────────────────────────────────────────────
    "geox_well_load_bundle": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },
    "geox_well_qc_logs": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },
    "geox_well_select_sw_model": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },
    "geox_well_compute_petrophysics": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },
    "geox_well_validate_cutoffs": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },
    "geox_well_verify_petrophysics": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },

    # ─── EARTH3D DIMENSION ───────────────────────────────────────────
    "geox_earth3d_load_volume": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },
    "geox_earth3d_interpret_horizons": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },
    "geox_earth3d_model_geometries": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },
    "geox_earth3d_verify_structural_integrity": {
        "fastmcp": "FULL",
        "vps": "FULL",
        "public": True
    },

    # ─── TIME4D DIMENSION ────────────────────────────────────────────
    "geox_time4d_simulate_burial": {
        "fastmcp": "FULL",
        "vps": "PARTIAL",  # Example: Not active in default VPS
        "public": True
    },
    "geox_time4d_reconstruct_paleo": {
        "fastmcp": "FULL",
        "vps": "PARTIAL",
        "public": True
    },
    "geox_time4d_verify_timing": {
        "fastmcp": "FULL",
        "vps": "PARTIAL",
        "public": True
    },

    # Add other dimensions (Section, Map, Physics, Cross) as needed.
}

def get_tool_parity(tool_name: str) -> Dict:
    return RUNTIME_PARITY_MATRIX.get(tool_name, {
        "fastmcp": "UNKNOWN",
        "vps": "UNKNOWN",
        "public": False
    })
