"""
geox_well_desurvey — 3D Wellbore Geometry Adapter (Phase 2)
═══════════════════════════════════════════════════════════
Computes TVD, X/Y, and TVDSS trajectory from deviation survey.

Gate A: file created but NOT YET wired into MCP server.py or registry.py.
Awaiting Gate B (registry) + Gate C (exposure).

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

logger = logging.getLogger("geox.well_desurvey")


async def geox_well_desurvey(
    well_id: str,
    collar: dict[str, float],
    survey: list[dict[str, float]],
    method: Literal["minimum_curvature", "tangential"] = "minimum_curvature",
    declination_deg: float = 0.0,
    kb_elevation_m: float | None = None,
    step_size_m: float = 10.0,
    crs_in: str = "EPSG:3375",
    crs_out: str = "EPSG:3375",
) -> dict[str, Any]:
    """Compute 3D wellbore trajectory from collar + deviation survey.

    Computes minimum-curvature (default) or tangential 3D well path from
    magnetic-north deviation survey, applies magnetic declination to true
    north, supports CRS transforms, and outputs geox.desurvey.v1 envelope
    with claim-tagged uncertainty (CLAIM/PLAUSIBLE/ESTIMATE).

    Parameters
    ----------
    well_id : str
        Unique well identifier (e.g. "Baram-1").
    collar : dict
        {x_collar, y_collar} in crs_in projected coordinates (e.g. Easting,
        Northing in metres for EPSG:3375 RTM-Malaya). For geographic WGS84,
        project before calling.
    survey : list of dict
        [{md, inc, azi}, ...] where azi is MAGNETIC by convention.
        Minimum 2 stations required.
    method : str
        "minimum_curvature" (default, industry standard) or "tangential".
    declination_deg : float
        Magnetic declination to apply. Positive = East. Default 0.0.
    kb_elevation_m : float or None
        Kelly Bushing elevation above mean sea level (m). Required for TVDSS.
    step_size_m : float
        Output sample interval (m). Default 10.0.
    crs_in, crs_out : str
        EPSG codes for projected CRS. If different, pyproj transforms.

    Returns
    -------
    dict
        geox.desurvey.v1 envelope with rows, qc_report, claim_envelope.

    See Also
    --------
    geox_well_ingest : LAS / deviation survey ingestion (separate concern)
    geox_well_qc : QC for curves, depth, completeness
    """
    from geox_core.engines.well.desurvey_core import desurvey as _impl

    logger.info(
        "geox_well_desurvey well_id=%s method=%s stations=%d decl=%.3f kb=%s",
        well_id,
        method,
        len(survey),
        declination_deg,
        kb_elevation_m,
    )

    return _impl(
        well_id=well_id,
        collar=collar,
        survey=survey,
        method=method,
        declination_deg=declination_deg,
        kb_elevation_m=kb_elevation_m,
        step_size_m=step_size_m,
        crs_in=crs_in,
        crs_out=crs_out,
    )
