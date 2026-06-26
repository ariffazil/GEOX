"""
geox_well_qc — Well Data Quality Control (Phase 2)
════════════════════════════════════════════════════
Absorbs: geox_data_qc_bundle (renamed, same API)

Modes: full, header, curves, depth, completeness, feature_info

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox.well_qc")


async def geox_well_qc(
    artifact_ref: str,
    artifact_type: str,
    qc_mode: str = "full",
    samples: list[dict[str, Any]] | None = None,
    existing_features: list[str] | None = None,
    candidate_feature: str | None = None,
    target_key: str = "value",
) -> dict[str, Any]:
    """Quality control for well data — depth monotonicity, null %, physical range checks.

    Modes:
      full         - All QC checks (default)
      header       - Well name, UWI, coordinates, datum, depth unit
      curves       - Physical range checks per canonical curve
      depth        - Monotonicity, step consistency, duplicate depth count
      completeness - Which canonical curves present vs missing
      feature_info - Feature Joint Information Statistic (Burlamaque 2026-06-04)
    """
    from geox_mcp.tools.qc import geox_data_qc_bundle as _impl

    return await _impl(
        artifact_ref=artifact_ref,
        artifact_type=artifact_type,
        qc_mode=qc_mode,
        samples=samples,
        existing_features=existing_features,
        candidate_feature=candidate_feature,
        target_key=target_key,
    )
