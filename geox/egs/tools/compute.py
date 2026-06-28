"""
compute.py — EGS Compute MCP Tools
====================================
GEOX EGS: Seismic computation and data QC tools.
Extends existing geox_seismic_compute with EGS-pedigreed uncertainty propagation.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

from geox.egs.engines.physics import (
    acoustic_impedance,
    castagna_mudrock_vp_to_vs,
    elastic_impedance,
    gardner_vp_to_rho,
    voigt_reuss_hill,
)

logger = logging.getLogger("geox.egs.tools.compute")


# ═══════════════════════════════════════════════════════════════════════════════
# Seismic Compute
# ═══════════════════════════════════════════════════════════════════════════════


async def egs_seismic_compute(
    vp_m_s: float,
    rho_g_cc: float | None = None,
    vs_m_s: float | None = None,
    compute_ai: bool = True,
    compute_ei: bool = False,
    chi: float = 0.3,
    use_gardner: bool = False,
) -> dict[str, Any]:
    """Compute seismic properties from velocity and density.

    OBS — Pure computation, reads no mutable state.
    """
    if rho_g_cc is None and use_gardner:
        rho_g_cc = gardner_vp_to_rho(vp_m_s)

    if rho_g_cc is None:
        return {"success": False, "error": "rho_g_cc required or set use_gardner=True", "recoverable": True}

    results: dict[str, Any] = {
        "vp_m_s": vp_m_s,
        "rho_g_cc": rho_g_cc,
    }

    if compute_ai:
        results["ai"] = acoustic_impedance(vp_m_s, rho_g_cc)
        results["ai_unit"] = "m/s * g/cc"

    if vs_m_s is None:
        vs_m_s = castagna_mudrock_vp_to_vs(vp_m_s)

    results["vs_m_s"] = vs_m_s
    results["vp_vs_ratio"] = vp_m_s / vs_m_s if vs_m_s > 0 else float("inf")

    if compute_ei:
        results["ei"] = elastic_impedance(vp_m_s, vs_m_s, rho_g_cc, chi)
        results["ei_unit"] = "m/s * g/cc"
        results["ei_chi"] = chi

    return {"success": True, "results": results}


async def egs_rock_physics(
    vp_mineral: float = 5500.0,
    vp_fluid: float = 1500.0,
    porosity: float = 0.2,
    rho_mineral: float = 2.65,
    rho_fluid: float = 1.0,
) -> dict[str, Any]:
    """Compute Voigt-Reuss-Hill bounds for velocity estimation.

    OBS — Pure computation.
    """
    if porosity < 0 or porosity > 1:
        return {"success": False, "error": "Porosity must be between 0 and 1", "recoverable": True}

    result = voigt_reuss_hill(vp_mineral, vp_fluid, porosity, rho_mineral, rho_fluid)
    result["porosity"] = porosity
    return {"success": True, "results": result}


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Registry
# ═══════════════════════════════════════════════════════════════════════════════


EGS_COMPUTE_TOOLS: dict[str, dict[str, Any]] = {
    "geox_egs_seismic_compute": {
        "description": "Compute seismic properties (AI, EI, Vp/Vs) from velocity and density.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vp_m_s": {"type": "number", "description": "P-wave velocity in m/s"},
                "rho_g_cc": {"type": "number", "description": "Density in g/cc"},
                "vs_m_s": {
                    "type": "number",
                    "description": "S-wave velocity in m/s (optional — uses Castagna mudrock if absent)",
                },
                "compute_ai": {"type": "boolean", "description": "Compute acoustic impedance"},
                "compute_ei": {"type": "boolean", "description": "Compute elastic impedance"},
                "chi": {"type": "number", "description": "Chi parameter for EI (default 0.3)"},
                "use_gardner": {"type": "boolean", "description": "Estimate density from Vp via Gardner"},
            },
            "required": ["vp_m_s"],
            "additionalProperties": False,
        },
        "handler": egs_seismic_compute,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    "geox_egs_rock_physics": {
        "description": "Compute Voigt-Reuss-Hill velocity bounds from mineral/fluid properties.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vp_mineral": {"type": "number", "description": "Mineral matrix Vp (m/s)"},
                "vp_fluid": {"type": "number", "description": "Fluid Vp (m/s)"},
                "porosity": {"type": "number", "description": "Fractional porosity (0-1)"},
                "rho_mineral": {"type": "number", "description": "Mineral density (g/cc)"},
                "rho_fluid": {"type": "number", "description": "Fluid density (g/cc)"},
            },
            "additionalProperties": False,
        },
        "handler": egs_rock_physics,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
}


def register_compute_tools(mcp: FastMCP) -> None:
    """Register EGS compute tools with the FastMCP server."""
    for tool_name, tool_def in EGS_COMPUTE_TOOLS.items():
        mcp.tool(name=tool_name, description=tool_def["description"])(tool_def["handler"])
        logger.info(f"Registered EGS compute tool: {tool_name}")
