from geox.core.basin_charge import BasinChargeSimulator
from geox.geox_mcp.server import geox_time4d_verify_timing


def test_basin_charge_simulator_returns_probability():
    history = [
        {"age_ma": 95.0, "duration_ma": 12.0, "temperature_c": 88.0},
        {"age_ma": 72.0, "duration_ma": 14.0, "temperature_c": 105.0},
        {"age_ma": 58.0, "duration_ma": 10.0, "temperature_c": 128.0},
    ]
    result = BasinChargeSimulator().simulate(
        burial_history=history,
        trap_age_ma=60.0,
        carrier_permeability_md=250.0,
        buoyancy_pressure_mpa=4.0,
        seal_capacity_mpa=6.0,
    ).to_dict()
    assert result["charge_probability"] >= 0.0
    assert "vault_receipt" in result


def test_existing_time_tool_returns_basin_charge():
    result = geox_time4d_verify_timing("BEK-2", trap_ma=60.0, charge_ma=58.0)
    assert result["timing_valid"] is True
    assert "basin_charge" in result
