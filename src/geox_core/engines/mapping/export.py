"""GEOX Mapping Engine — Package Export.

Exports a map package with PROV sidecar for provenance tracking.
Stub implementation — returns package structure until real export is wired.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations
from typing import Any


def export_package(
    scene_plan_id: str,
    formats: list[str] | None = None,
    include_sources: bool = False,
    include_provenance: bool = True,
    review_mode: str = "draft",
    output_dir: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Export a map package with provenance sidecar.

    Args:
        scene_plan_id: Scene plan ID from plan_scene
        formats: Output formats (e.g. ['png', 'pdf', 'geojson'])
        include_sources: Include source data files
        include_provenance: Include PROV sidecar
        review_mode: 'draft' or 'final'
        output_dir: Output directory

    Returns:
        Dict with 'package_path', 'formats', 'provenance', 'metadata'.
    """
    return {
        "status": "stub",
        "scene_plan_id": scene_plan_id,
        "formats": formats or ["png"],
        "include_sources": include_sources,
        "include_provenance": include_provenance,
        "review_mode": review_mode,
        "note": "Mapping engine stub — no export backend wired. Wire reportlab/matplotlib to produce actual map packages.",
    }
