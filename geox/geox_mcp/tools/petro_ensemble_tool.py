"""
MCP wrapper for GEOX saturation ensemble computation.
"""

from __future__ import annotations

from geox.core.petro_ensemble import PetroEnsemble


def geox_compute_sw_ensemble_tool(
    rt: float,
    phi: float,
    rw: float,
    vsh: float,
    temp: float,
    a: float = 1.0,
    m: float = 2.0,
    n: float = 2.0,
    rsh: float | None = None,
) -> dict:
    result = PetroEnsemble().compute_sw_ensemble(rt=rt, phi=phi, rw=rw, vsh=vsh, temp=temp, a=a, m=m, n=n, rsh=rsh)
    return result.to_dict()
