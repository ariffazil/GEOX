"""
MCP wrapper for basin charge simulation.
"""

from __future__ import annotations

from geox.core.basin_charge import BasinChargeSimulator


def geox_simulate_basin_charge_tool(
    burial_history: list[dict[str, float]],
    trap_age_ma: float,
    carrier_permeability_md: float,
    buoyancy_pressure_mpa: float,
    seal_capacity_mpa: float,
    fault_density: float = 0.1,
) -> dict:
    result = BasinChargeSimulator().simulate(
        burial_history=burial_history,
        trap_age_ma=trap_age_ma,
        carrier_permeability_md=carrier_permeability_md,
        buoyancy_pressure_mpa=buoyancy_pressure_mpa,
        seal_capacity_mpa=seal_capacity_mpa,
        fault_density=fault_density,
    )
    return result.to_dict()
