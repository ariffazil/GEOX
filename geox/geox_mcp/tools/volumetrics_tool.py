"""
MCP wrapper for probabilistic volumetrics.
"""

from __future__ import annotations

from geox.core.volumetrics import ProbabilisticVolumetrics


def geox_compute_volume_probabilistic_tool(
    grv_dist: float | dict[str, float],
    ntg_dist: float | dict[str, float],
    phi_dist: float | dict[str, float],
    sw_dist: float | dict[str, float],
    fvf_dist: float | dict[str, float],
    draws: int = 10_000,
) -> dict:
    result = ProbabilisticVolumetrics(draws=draws).compute_hcpv(
        grv_dist=grv_dist,
        ntg_dist=ntg_dist,
        phi_dist=phi_dist,
        sw_dist=sw_dist,
        fvf_dist=fvf_dist,
    )
    return result.to_dict()
