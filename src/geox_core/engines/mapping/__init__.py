"""GEOX Mapping Engine — Layer Registry.

Lists available map layers for a given bounding box and theme.
Stub implementation — returns empty layer list until real data sources are wired.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations
from typing import Any


def list_layers(
    bbox: list[float],
    theme: str | None = None,
    include_unavailable: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """List available map layers for a bounding box.

    Args:
        bbox: [west, south, east, north] in EPSG:4326
        theme: Optional theme filter (e.g. 'geology', 'bathymetry')
        include_unavailable: If True, include layers that can't be fetched

    Returns:
        Dict with 'layers' list and 'metadata' dict.
    """
    return {
        "status": "stub",
        "layers": [],
        "metadata": {
            "bbox": bbox,
            "theme": theme,
            "note": "Mapping engine stub — no real data sources wired yet. "
            "Wire Natural Earth, OneGeology, or GEBCO layers to activate.",
        },
    }
