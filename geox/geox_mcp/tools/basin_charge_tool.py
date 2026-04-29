from geox.skills.subsurface.prospect.basin_charge import (
    geox_simulate_basin_charge_tool,
    geox_time4d_verify_timing_tool,
)

def geox_simulate_basin_charge(
    burial_history: list[dict],
    trap_age_ma: float = 70.0,
    carrier_permeability_md: float = 100.0,
    buoyancy_pressure_mpa: float = 10.0,
    seal_capacity_mpa: float = 25.0,
    fault_density: float = 0.1,
) -> dict:
    return geox_simulate_basin_charge_tool(
        burial_history=burial_history,
        trap_age_ma=trap_age_ma,
        carrier_permeability_md=carrier_permeability_md,
        buoyancy_pressure_mpa=buoyancy_pressure_mpa,
        seal_capacity_mpa=seal_capacity_mpa,
        fault_density=fault_density,
    )
geox_time4d_verify_timing = geox_time4d_verify_timing_tool

__all__ = [
    "geox_simulate_basin_charge_tool",
    "geox_time4d_verify_timing_tool",
    "geox_simulate_basin_charge",
    "geox_time4d_verify_timing",
]
