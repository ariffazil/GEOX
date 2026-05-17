"""
GEOX Earth Science Skill Pack
═══════════════════════════════════════════════════════════════════════════════
Unified interface to the full open-source geoscience stack installed on
/opt/geox-science/venv.

Provides agent-facing wrappers for:
  • 3D geological modeling (GemPy)
  • Geostatistics (gstlearn, geone, scikit-gstat)
  • Geomorphology / terrain (Landlab, GRASS)
  • Geophysics / inversion (SimPEG, discretize, verde, harmonica)
  • Seismic (segyio, segysak, bruges)
  • Well logs (welly, lasio)
  • 3D visualization (pyvista, vtk)
  • Structural geology (mplstereonet)
  • Geospatial (geopandas, rasterio, shapely)

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Ensure the shared venv is on path
_VENV_SITE = Path("/opt/geox-science/venv/lib/python3.13/site-packages")
if str(_VENV_SITE) not in sys.path:
    sys.path.insert(0, str(_VENV_SITE))

__all__ = [
    "modeling",
    "geostats",
    "terrain",
    "geophysics",
    "seismic",
    "wells",
    "viz",
    "structural",
    "geospatial",
]


def _lazy_import(name: str) -> Any:
    """Lazy import with graceful fallback."""
    try:
        return __import__(name)
    except ImportError as exc:
        raise ImportError(
            f"{name} not available. Activate environment: "
            f"source /opt/geox-science/venv/bin/activate"
        ) from exc


class _LazyModule:
    """Proxy that imports the real module on first attribute access."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._mod = None

    def _ensure(self) -> Any:
        if self._mod is None:
            self._mod = _lazy_import(self._name)
        return self._mod

    def __getattr__(self, item: str) -> Any:
        return getattr(self._ensure(), item)

    def __dir__(self) -> list[str]:
        return dir(self._ensure())


# Lazy proxies — agents can import without heavy load until used
modeling = _LazyModule("gempy")
geostats = _LazyModule("gstlearn")
terrain = _LazyModule("landlab")
geophysics = _LazyModule("simpeg")
seismic = _LazyModule("segyio")
wells = _LazyModule("welly")
viz = _LazyModule("pyvista")
structural = _LazyModule("mplstereonet")
geospatial = _LazyModule("geopandas")


def health_check() -> dict[str, Any]:
    """Return availability status of all Earth science modules."""
    modules = {
        "gempy": "3D geological modeling",
        "gstlearn": "Geostatistics",
        "geone": "Stochastic simulation",
        "landlab": "Terrain / geomorphology",
        "simpeg": "Geophysical inversion",
        "discretize": "Discretization meshes",
        "verde": "Gridding / interpolation",
        "harmonica": "Gravity / magnetics",
        "subsurface": "Subsurface data structures",
        "segyio": "SEG-Y I/O",
        "segysak": "SEGY xarray",
        "bruges": "Seismic attributes",
        "welly": "Well log analysis",
        "lasio": "LAS file I/O",
        "pyvista": "3D visualization",
        "geopandas": "Vector geospatial",
        "rasterio": "Raster geospatial",
        "shapely": "Geometry operations",
        "mplstereonet": "Structural geology",
        "scikit_gstat": "Variography",
    }
    status: dict[str, Any] = {}
    for mod, desc in modules.items():
        try:
            __import__(mod)
            status[mod] = {"available": True, "description": desc}
        except Exception as exc:
            status[mod] = {"available": False, "description": desc, "error": str(exc)}
    return status
