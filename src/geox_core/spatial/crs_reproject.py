"""
crs_reproject.py — CRS Reprojection Module (P1.4)
===================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Enforces canonical coordinate system handling for all GEOX spatial data.

Hard rules:
  - No free-text coordinates — must declare source_crs and target_crs
  - No CRS-less world coordinates — reject with KNOWN_CRS_REQUIRED
  - No mixing depth datum with horizontal CRS — depth_datum is separate
  - Round-trip test: transform(src→tgt→src) must be within 1cm tolerance
  - Unknown CRS rejected unless ASSET_MODE=sandbox

Supported CRS (Malaysia-focused):
  EPSG:4326 — WGS84 (canonical internal)
  EPSG:3168 — Kertau (Malay Peninsula, ft)
  EPSG:3375 — RSO Malaya (meters)
  EPSG:29872 — Timbalai 1948 / UTM zone 50N (Sabah)
  EPSG:29873 — Timbalai 1948 / UTM zone 49N (Sarawak)
  EPSG:32649 — WGS84 / UTM zone 49N
  EPSG:32650 — WGS84 / UTM zone 50N
  EPSG:3857  — Web Mercator (mapping display)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("geox.crs")

# ─── CRS Registry ────────────────────────────────────────────────────────────
# Authority: EPSG Registry (https://epsg.org/)
# Last verified: 2026-06-14

CANONICAL_CRS = "EPSG:4326"
CANONICAL_CRS_NAME = "WGS84"

# Malaysia-focused CRS — extend as needed for other basins
KNOWN_CRS: dict[str, dict[str, Any]] = {
    "EPSG:4326": {
        "name": "WGS84",
        "area": "Global",
        "unit": "degree",
        "type": "geographic",
    },
    "EPSG:3168": {
        "name": "Kertau (Malay Peninsula)",
        "area": "Peninsular Malaysia",
        "unit": "Clark's foot",
        "type": "projected",
        "note": "Used in older Malay Basin surveys",
    },
    "EPSG:3375": {
        "name": "RSO Malaya (meters)",
        "area": "Peninsular Malaysia",
        "unit": "metre",
        "type": "projected",
        "note": "Modern Peninsular Malaysia surveys",
    },
    "EPSG:29872": {
        "name": "Timbalai 1948 / UTM zone 50N",
        "area": "Sabah & Labuan",
        "unit": "metre",
        "type": "projected",
        "note": "Sabah surveys",
    },
    "EPSG:29873": {
        "name": "Timbalai 1948 / UTM zone 49N",
        "area": "Sarawak",
        "unit": "metre",
        "type": "projected",
        "note": "Sarawak surveys",
    },
    "EPSG:32649": {
        "name": "WGS84 / UTM zone 49N",
        "area": "Global (zone 49N)",
        "unit": "metre",
        "type": "projected",
    },
    "EPSG:32647": {
        "name": "WGS84 / UTM zone 47N",
        "area": "Global (zone 47N)",
        "unit": "metre",
        "type": "projected",
    },
    "EPSG:32648": {
        "name": "WGS84 / UTM zone 48N",
        "area": "Global (zone 48N)",
        "unit": "metre",
        "type": "projected",
    },
    "EPSG:32650": {
        "name": "WGS84 / UTM zone 50N",
        "area": "Global (zone 50N)",
        "unit": "metre",
        "type": "projected",
    },
    "EPSG:3857": {
        "name": "Web Mercator",
        "area": "Global (web mapping)",
        "unit": "metre",
        "type": "projected",
        "note": "For display only — not for subsurface measurement",
    },
}

ASSET_MODE = os.getenv("GEOX_ASSET_MODE", "production")


def is_known_crs(crs: str) -> bool:
    """Check if a CRS string is in the known registry."""
    return crs.upper() in KNOWN_CRS


def validate_crs(
    crs: str,
    allow_unknown: bool | None = None,
) -> tuple[bool, str]:
    """Validate a CRS string.

    Args:
        crs: EPSG code (e.g. "EPSG:4326")
        allow_unknown: Override for sandbox mode. None = use ASSET_MODE.

    Returns:
        (is_valid, message)
    """
    crs = crs.upper().strip()

    if not crs.startswith("EPSG:"):
        return False, f"CRS must be EPSG code (e.g. EPSG:4326), got '{crs}'"

    allow = allow_unknown if allow_unknown is not None else (ASSET_MODE == "sandbox")

    if crs in KNOWN_CRS:
        return True, f"Known CRS: {KNOWN_CRS[crs]['name']}"

    # Unknown CRS — try pyproj
    try:
        import pyproj

        crs_obj = pyproj.CRS(crs)
        if crs_obj.is_valid:
            if not allow:
                return False, (
                    f"CRS '{crs}' ({crs_obj.name}) is valid but not in known registry. "
                    "Add to KNOWN_CRS in crs_reproject.py or use sandbox mode."
                )
            return True, f"Valid CRS: {crs_obj.name} (not in known registry — sandbox mode)"
        return False, f"Invalid CRS: '{crs}' — pyproj reports invalid"
    except Exception as exc:
        return False, f"Unknown CRS: '{crs}' — {exc}"


def reproject_point(
    x: float,
    y: float,
    source_crs: str,
    target_crs: str = CANONICAL_CRS,
) -> tuple[float, float]:
    """Reproject a single (x, y) coordinate from source_crs to target_crs.

    Args:
        x: X coordinate (longitude/easting)
        y: Y coordinate (latitude/northing)
        source_crs: Source EPSG code
        target_crs: Target EPSG code (default: EPSG:4326)

    Returns:
        (x_out, y_out) in target CRS

    Raises:
        ValueError: If CRS is invalid or transformation fails
    """
    import pyproj

    valid_src, msg_src = validate_crs(source_crs)
    if not valid_src:
        raise ValueError(f"Invalid source CRS: {msg_src}")

    valid_tgt, msg_tgt = validate_crs(target_crs)
    if not valid_tgt:
        raise ValueError(f"Invalid target CRS: {msg_tgt}")

    transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)
    x_out, y_out = transformer.transform(x, y)
    return (x_out, y_out)


def reproject_points(
    points: list[tuple[float, float]],
    source_crs: str,
    target_crs: str = CANONICAL_CRS,
) -> list[tuple[float, float]]:
    """Reproject a list of (x, y) coordinates.

    Args:
        points: List of (x, y) tuples
        source_crs: Source EPSG code
        target_crs: Target EPSG code (default: EPSG:4326)

    Returns:
        List of (x_out, y_out) in target CRS
    """
    import pyproj

    valid_src, msg_src = validate_crs(source_crs)
    if not valid_src:
        raise ValueError(f"Invalid source CRS: {msg_src}")

    valid_tgt, msg_tgt = validate_crs(target_crs)
    if not valid_tgt:
        raise ValueError(f"Invalid target CRS: {msg_tgt}")

    transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)
    return [transformer.transform(x, y) for x, y in points]


def roundtrip_tolerance(
    points: list[tuple[float, float]],
    source_crs: str,
    tolerance_m: float = 0.01,
) -> tuple[bool, list[float]]:
    """Test round-trip fidelity: source → canonical → source.

    Args:
        points: List of (x, y) tuples in source_crs
        source_crs: Source EPSG code
        tolerance_m: Maximum acceptable deviation in metres (default 1cm)

    Returns:
        (passes, deviations_m): True if all deviations ≤ tolerance_m
    """
    # Forward: source → canonical
    forward = reproject_points(points, source_crs, CANONICAL_CRS)
    # Inverse: canonical → source
    inverse = reproject_points(forward, CANONICAL_CRS, source_crs)

    deviations = []
    for (x_orig, y_orig), (x_inv, y_inv) in zip(points, inverse):
        dev = ((x_orig - x_inv) ** 2 + (y_orig - y_inv) ** 2) ** 0.5
        deviations.append(dev)

    passes = all(d <= tolerance_m for d in deviations)
    return (passes, deviations)


def get_crs_info(crs: str) -> dict[str, Any]:
    """Get metadata about a known CRS."""
    crs = crs.upper().strip()
    if crs in KNOWN_CRS:
        return KNOWN_CRS[crs]
    try:
        import pyproj

        crs_obj = pyproj.CRS(crs)
        return {
            "name": crs_obj.name,
            "area": str(crs_obj.area_of_use) if crs_obj.area_of_use else "unknown",
            "unit": "unknown",
            "type": crs_obj.type_name,
            "note": "Dynamically resolved — not in known registry",
        }
    except Exception:
        return {"name": "unknown", "area": "unknown", "unit": "unknown", "type": "unknown", "note": "Unknown CRS"}


def to_provenance_entry(
    source_crs: str,
    target_crs: str = CANONICAL_CRS,
    depth_datum: str | None = None,
) -> dict[str, Any]:
    """Build a CRS provenance record for injection into tool output envelopes.

    Args:
        source_crs: Original CRS of the data
        target_crs: CRS used for computation (default: EPSG:4326)
        depth_datum: Depth reference (KB, MSL, DF, etc.)

    Returns:
        Dict with crs_source, crs_target, crs_info_source, crs_info_target, depth_datum
    """
    source_info = get_crs_info(source_crs)
    target_info = get_crs_info(target_crs)

    return {
        "crs_source": source_crs,
        "crs_target": target_crs,
        "crs_info_source": source_info,
        "crs_info_target": target_info,
        "depth_datum": depth_datum or "unknown",
        "roundtrip_verified": False,  # Caller must run roundtrip_tolerance to set True
    }
