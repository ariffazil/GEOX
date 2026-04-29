from geox.skills.subsurface.sensitivity_tool import geox_run_sensitivity_sweep_tool

def geox_run_sensitivity_sweep(**kwargs) -> dict:
    percent_delta = kwargs.pop("percent_delta", 0.2)
    return geox_run_sensitivity_sweep_tool(base_inputs=kwargs, percent_delta=percent_delta)

__all__ = ["geox_run_sensitivity_sweep_tool", "geox_run_sensitivity_sweep"]
