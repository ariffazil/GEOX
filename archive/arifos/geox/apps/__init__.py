"""
GEOX Apps — Host-agnostic interactive applications.

This package contains GEOX MCP Apps with their manifests and implementations.
Each app is self-contained and portable across hosts.

DITEMPA BUKAN DIBERI
"""

from pathlib import Path
import json
import typing

from ..contracts.app_manifest import GeoXAppManifest, get_app_registry, Dimension, AppDomain


def _normalize_manifest(raw: dict) -> dict:
    """Normalize legacy manifest fields before Pydantic validation."""
    # Ensure dimension exists
    if "dimension" not in raw:
        domain = raw.get("domain", "")
        dimension_map = {
            "seismic": Dimension.EARTH_3D,
            "petrophysics": Dimension.WELL,
            "geology": Dimension.SECTION,
            "economics": Dimension.PROSPECT,
            "governance": Dimension.DASHBOARD,
            "general": Dimension.DASHBOARD,
            "wells": Dimension.WELL,
            "maps": Dimension.MAP,
        }
        raw["dimension"] = dimension_map.get(domain, Dimension.DASHBOARD).value
    return raw


def load_app_manifest(app_name: str) -> GeoXAppManifest:
    """
    Load an app manifest by name.
    
    Args:
        app_name: App directory name (e.g., 'seismic_viewer')
    
    Returns:
        Parsed GeoXAppManifest
    """
    manifest_path = Path(__file__).parent / app_name / "manifest.json"
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    normalized = _normalize_manifest(raw)
    return GeoXAppManifest.model_validate(normalized)


def register_all_apps() -> None:
    """Register all built-in GEOX apps."""
    registry = get_app_registry()
    
    apps_dir = Path(__file__).parent
    for app_dir in apps_dir.iterdir():
        if app_dir.is_dir() and (app_dir / "manifest.json").exists():
            try:
                manifest = load_app_manifest(app_dir.name)
                registry.register(manifest)
            except Exception as e:
                print(f"[GEOX Apps] Failed to load {app_dir.name}: {e}")


# Auto-register on import
register_all_apps()
