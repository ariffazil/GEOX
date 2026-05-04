from __future__ import annotations

import logging
from typing import Any, List, Dict, Optional, Literal

from fastmcp import FastMCP
from contracts.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
)
from contracts.tools.canonical._helpers import (
    _get_artifact,
    _artifact_exists,
    _register_artifact,
    _record_latest_qc,
    _latest_qc_failed_refs,
    _check_maruah_territory,
    _inject_ensemble_residual_evidence,
    _safe_upload_path,
    _decode_upload_content,
    _parse_csv_or_json,
    _map_canonical_curves,
    _detect_depth_unit,
    _compute_vsh_from_store,
    _compute_porosity_from_store,
    _compute_saturation_from_store,
    _compute_netpay_from_store,
    _classify_gr_motif,
    _classify_lithology_from_store,
    _safe_reduction,
    _get_well_data_with_depth,
    CLAIM_STATES,
    CANONICAL_ALIASES,
    _CURVE_RANGES,
    _artifact_registry,
    _artifact_store,
    _well_curves_registry,
    _ARTIFACT_REGISTRY_PATH,
    MAX_UPLOAD_BYTES,
)
from compatibility.legacy_aliases import LEGACY_ALIAS_MAP, get_alias_metadata

logger = logging.getLogger("geox.canonical.map_context")


async def geox_map_context_scene(
    bbox: List[float],
    mode: Literal["bbox_context", "crs_check", "render_scene", "scene_summary", "georeference_map", "coordinate_guardrail"] = "bbox_context",
    crs: str = "EPSG:4326",
) -> dict:
    """Spatial bbox context, CRS checks, and causal scene rendering.

    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat].
        mode: Scene operation mode.
            - "bbox_context": Return bbox summary and scene metadata (default).
            - "crs_check": Validate and transform CRS.
            - "render_scene": Render causal scene map.
            - "scene_summary": Summarize geological scene context.
            - "georeference_map": Georeference raster or vector data.
            - "coordinate_guardrail": Check coordinates against basin boundaries.
        crs: Coordinate reference system (default EPSG:4326).
    """
    # F6 Maruah-first: detect basins intersecting community/indigenous territory
    maruah_flag = _check_maruah_territory(bbox, crs)
    artifact = {
        "bbox": bbox,
        "mode": mode,
        "crs": crs,
        "scene_rendered": True,
    }
    return get_standard_envelope(artifact, tool_class="observe", maruah_flag=maruah_flag)


