"""geox_cross_section — sample a real-data geological transect (bathymetry + gravity).

Closes the "GEOX has no cross-section tool" gap (found 2026-10-23: HERMES built the
dip/strike sections OUTSIDE the organ because all 27 tools compute rock properties
and none render a section). This module is the DATA half — great-circle transect
sampling of real NOAA bathymetry + Sandwell & Smith free-air gravity — the profile
that the SVG/HTML renderer (forge_work/2026-10-23/borneo-section/{svg,build_html}.py)
already consumes. Data sources are open; nothing is drawn by hand.

Authority: 555_COMPUTE_ONLY — returns a profile, never a verdict.
"""

from __future__ import annotations
import math
import os
from pathlib import Path
from typing import Any

import numpy as np

# ── data paths (open datasets; env-overridable so the tool is not hardcoded) ──
_DEFAULT_DATA = Path("/root/forge_work/2026-10-23/borneo-section/data")
BATHY_TIF = os.environ.get("GEOX_SECTION_BATHY", str(_DEFAULT_DATA / "borneo_wide.tif"))
GRAV_NC = os.environ.get("GEOX_SECTION_GRAV", str(_DEFAULT_DATA / "grav_34.1.nc"))

# ── canonical transects (extensible — pass start/end to make a new line) ─────
LINES: dict[str, dict[str, Any]] = {
    "BB_dip": {
        "name": "B–B′",
        "label": "DIP LINE",
        "start": (3.85, 115.30),
        "end": (7.10, 112.35),
        "note": "SE→NW, perpendicular to the N51°E strike of the deepwater fold-thrust belt",
    },
    "AA_strike": {
        "name": "A–A′",
        "label": "STRIKE LINE",
        "start": (5.30, 113.20),
        "end": (7.00, 115.25),
        "note": "SW→NE, parallel to the N51°E strike of the fold-thrust belt",
    },
}


def gc_interp(p0, p1, n):
    """Great-circle interpolate between two (lat, lon) points. Returns (pts, length_km)."""
    lat0, lon0 = math.radians(p0[0]), math.radians(p0[1])
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    d = 2 * math.asin(
        math.sqrt(math.sin((lat1 - lat0) / 2) ** 2 + math.cos(lat0) * math.cos(lat1) * math.sin((lon1 - lon0) / 2) ** 2)
    )
    out = []
    for i in range(n):
        f = i / (n - 1)
        a = math.sin((1 - f) * d) / math.sin(d)
        b = math.sin(f * d) / math.sin(d)
        x = a * math.cos(lat0) * math.cos(lon0) + b * math.cos(lat1) * math.cos(lon1)
        y = a * math.cos(lat0) * math.sin(lon0) + b * math.cos(lat1) * math.sin(lon1)
        z = a * math.sin(lat0) + b * math.sin(lat1)
        out.append((math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))))
    return out, d * 6371.0


def bearing(p0, p1):
    lat0, lat1 = math.radians(p0[0]), math.radians(p1[0])
    dl = math.radians(p1[1] - p0[1])
    y = math.sin(dl) * math.cos(lat1)
    x = math.cos(lat0) * math.sin(lat1) - math.sin(lat0) * math.cos(lat1) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def _sample_raster(path: str, pts):
    import rasterio

    with rasterio.open(path) as ds:
        vals = np.array([v[0] for v in ds.sample([(lon, lat) for lat, lon in pts])], dtype=float)
        nod = ds.nodata
    if nod is not None:
        vals[vals == nod] = np.nan
    vals[vals < -9000] = np.nan
    return vals


_GRAV = {}


def _sample_grav(path: str, pts):
    import netCDF4

    if "ds" not in _GRAV:
        ds = netCDF4.Dataset(path)
        _GRAV["ds"] = ds
        _GRAV["lat"] = ds.variables["lat"][:]
        _GRAV["lon"] = ds.variables["lon"][:]
        _GRAV["z"] = ds.variables["z"]
    z = _GRAV["z"]
    lat = _GRAV["lat"][:]
    lon = _GRAV["lon"][:]
    out = []
    for la, lo in pts:
        j = int(round((la - lat[0]) / (lat[1] - lat[0])))
        i = int(round((lo - lon[0]) / (lon[1] - lon[0])))
        j = min(max(j, 0), z.shape[0] - 1)
        i = min(max(i, 0), z.shape[1] - 1)
        out.append(float(z[j, i]))
    return np.array(out, dtype=float)


async def geox_cross_section(
    line: str | None = None,
    start: list[float] | None = None,
    end: list[float] | None = None,
    n: int = 701,
) -> dict:
    """Sample a real-data geological transect (bathymetry + free-air gravity).

    Pass a named `line` ("BB_dip" | "AA_strike") or explicit `start`/`end` [lat, lon].
    Returns the great-circle profile (dist_km, lat, lon, elev_m, grav_mgal) with
    provenance. COMPUTE_ONLY — this is the data half of a cross-section; rendering
    (SVG/HTML) consumes this profile.
    """
    spec = None
    if line:
        spec = LINES.get(line)
        if spec is None:
            return {"status": "INVALID", "error": f"unknown line={line!r}. Valid: {sorted(LINES)}"}
    elif start and end:
        spec = {"name": "custom", "label": "CUSTOM", "start": tuple(start), "end": tuple(end), "note": "caller-supplied transect"}
    if spec is None:
        return {"status": "INVALID", "error": "provide line= or start+end (each [lat, lon])"}

    pts, dist_km = gc_interp(spec["start"], spec["end"], n)
    brg = bearing(spec["start"], spec["end"])

    elev = None
    grav = None
    bathy_err = None
    grav_err = None
    try:
        elev = _sample_raster(BATHY_TIF, pts)
    except Exception as e:  # noqa: BLE001
        bathy_err = f"{type(e).__name__}: {e}"
    try:
        if Path(GRAV_NC).exists():
            grav = _sample_grav(GRAV_NC, pts)
    except Exception as e:  # noqa: BLE001
        grav_err = f"{type(e).__name__}: {e}"

    step = dist_km / (n - 1)
    return {
        "status": "OK",
        "line": spec["name"],
        "label": spec["label"],
        "start": list(spec["start"]),
        "end": list(spec["end"]),
        "length_km": round(dist_km, 1),
        "bearing_deg": round(brg, 1),
        "n": n,
        "note": spec["note"],
        "dist_km": [round(i * step, 2) for i in range(n)],
        "lat": [round(p[0], 5) for p in pts],
        "lon": [round(p[1], 5) for p in pts],
        "elev_m": None if elev is None else [None if not np.isfinite(v) else round(float(v), 1) for v in elev],
        "grav_mgal": None if grav is None else [None if not np.isfinite(v) else round(float(v), 2) for v in grav],
        "provenance": {
            "bathymetry": "NOAA NCEI DEM mosaic (open)" if bathy_err is None else f"UNAVAILABLE: {bathy_err}",
            "gravity": "Sandwell & Smith V34.1, 1 arc-min (Scripps, open)"
            if grav is None or grav_err is None
            else f"UNAVAILABLE: {grav_err}",
            "method": "great-circle interpolation, nearest-neighbour sampling — nothing drawn by hand",
            "authority": "555_COMPUTE_ONLY",
        },
    }


def render_svg(profile: dict, width: int = 1240, height: int = 460) -> str:
    """Render a profile (from geox_cross_section) as a 2-panel SVG: bathymetry + gravity.

    The render half of the cross-section gap. Deterministic, dependency-free SVG
    (pure string construction) - no matplotlib, no PIL. Data is MEASURED (elev/grav),
    nothing drawn by hand.
    """
    dist = profile.get("dist_km") or []
    elev = profile.get("elev_m") or []
    grav = profile.get("grav_mgal") or []
    if not dist or not elev:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="80"><text x="10" y="30" font-family="sans-serif" font-size="12">INVALID - no profile data</text></svg>'
    x0, x1 = dist[0], dist[-1]
    dx = (x1 - x0) or 1.0
    ev = [v for v in elev if v is not None]
    gv = [v for v in grav if v is not None] if grav else []
    e_lo, e_hi = (min(ev), max(ev)) if ev else (-3000, 2000)
    g_lo, g_hi = (min(gv), max(gv)) if gv else (-40, 100)
    pad_l, pad_r, pad_t, pad_b = 46, 12, 14, 30
    pw = width - pad_l - pad_r
    top_h = height * 0.52
    bot_h = height * 0.30

    def X(v):
        return pad_l + (v - x0) / dx * pw

    def Yz(z):
        return pad_t + (e_hi - z) / (e_hi - e_lo) * (top_h - 20)

    def Yg(g):
        return pad_t + top_h + 26 + (g_hi - g) / (g_hi - g_lo) * (bot_h - 16)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" font-family="sans-serif">',
        f'<rect width="{width}" height="{height}" fill="#0d1117"/>',
        f'<text x="{pad_l}" y="16" fill="#e6edf3" font-size="14" font-weight="bold">{profile.get("name","")} - {profile.get("label","")} ({profile.get("length_km","")} km, bearing {profile.get("bearing_deg","")} deg)</text>',
        f'<text x="{pad_l}" y="30" fill="#8b949e" font-size="9">{profile.get("note","")} - MEASURED (NOAA bathymetry, Sandwell & Smith V34.1 gravity)</text>',
    ]
    pts = " ".join(f"{X(d):.1f},{Yz(z):.1f}" for d, z in zip(dist, elev) if z is not None)
    if pts:
        parts.append(f'<polyline points="{pts}" fill="none" stroke="#58a6ff" stroke-width="1.4"/>')
        lastx = pts.split()[-1].split(",")[0]
        parts.append(f'<path d="M {pts.split()[0]} L {pts} L {lastx},{Yz(e_lo)} Z" fill="#0d2b4566"/>')
    parts.append(f'<text x="{pad_l}" y="{Yz(e_lo)+12}" fill="#58a6ff" font-size="9">bathymetry {e_lo:.0f} to {e_hi:.0f} m</text>')
    if gv:
        gpts = " ".join(f"{X(d):.1f},{Yg(g):.1f}" for d, g in zip(dist, grav) if g is not None)
        parts.append(f'<polyline points="{gpts}" fill="none" stroke="#f0883e" stroke-width="1.2"/>')
        parts.append(f'<text x="{pad_l}" y="{Yg(g_lo)+12}" fill="#f0883e" font-size="9">free-air gravity {g_lo:.0f} to {g_hi:.0f} mGal</text>')
    for i in range(0, int(dx) + 1, 100):
        parts.append(f'<text x="{X(i):.1f}" y="{height-8}" fill="#8b949e" font-size="8" text-anchor="middle">{i} km</text>')
    parts.append('</svg>')
    return "\n".join(parts)
