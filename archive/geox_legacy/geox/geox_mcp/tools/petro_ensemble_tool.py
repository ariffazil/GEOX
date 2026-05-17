from geox.skills.subsurface.petro.petro_ensemble import geox_compute_sw_ensemble_tool

def geox_compute_sw_ensemble(
    rt: float,
    phi: float,
    rw: float,
    vsh: float,
    temp: float = 80.0,
    **kwargs,
) -> dict:
    return geox_compute_sw_ensemble_tool(rt=rt, phi=phi, rw=rw, vsh=vsh, temp=temp, **kwargs)

__all__ = ["geox_compute_sw_ensemble_tool", "geox_compute_sw_ensemble"]
