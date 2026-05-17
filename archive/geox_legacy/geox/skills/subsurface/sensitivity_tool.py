"""
MCP wrapper for sensitivity sweeps.
"""

from __future__ import annotations

from geox.core.sensitivity import SensitivitySweep


def geox_run_sensitivity_sweep_tool(base_inputs: dict, percent_delta: float = 0.2) -> dict:
    return SensitivitySweep().run(base_inputs=base_inputs, percent_delta=percent_delta).to_dict()
