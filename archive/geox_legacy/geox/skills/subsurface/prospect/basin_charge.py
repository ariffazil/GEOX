"""
MCP tool for geox_time4d_verify_timing and geox_simulate_basin_charge.
v2: full spec output with verdict, reversal_conditions, burial_carrier_context.
"""

from __future__ import annotations

from geox.core.basin_charge import BasinChargeSimulator


def geox_simulate_basin_charge_tool(
    burial_history: list[dict],
    trap_age_ma: float,
    carrier_permeability_md: float,
    buoyancy_pressure_mpa: float,
    seal_capacity_mpa: float,
    fault_density: float = 0.1,
) -> dict:
    """geox_simulate_basin_charge — v2 wrapper."""
    result = BasinChargeSimulator().simulate(
        burial_history=burial_history,
        trap_age_ma=trap_age_ma,
        carrier_permeability_md=carrier_permeability_md,
        buoyancy_pressure_mpa=buoyancy_pressure_mpa,
        seal_capacity_mpa=seal_capacity_mpa,
        fault_density=fault_density,
    )
    return result.to_dict()


def geox_time4d_verify_timing_tool(
    burial_history: list[dict],
    trap_age_ma: float,
    carrier_permeability_md: float,
    buoyancy_pressure_mpa: float,
    seal_capacity_mpa: float,
    fault_density: float = 0.1,
) -> dict:
    """
    geox_time4d_verify_timing — v2 full spec.
    
    Returns:
      verdict: screening | probable | improbable | void
      claim_state: OBSERVED | COMPUTED | HYPOTHESIS | VOID
      reversal_conditions: conditions that would flip verdict
      burial_carrier_assumptions: scenario context
      limitations: what limits confidence
      human_decision_point: where human review is required
    """
    result = BasinChargeSimulator().verify_timing(
        burial_history=burial_history,
        trap_age_ma=trap_age_ma,
        carrier_permeability_md=carrier_permeability_md,
        buoyancy_pressure_mpa=buoyancy_pressure_mpa,
        seal_capacity_mpa=seal_capacity_mpa,
        fault_density=fault_density,
    )
    return result.to_dict()
