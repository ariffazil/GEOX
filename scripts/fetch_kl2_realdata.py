#!/usr/bin/env python3
"""
fetch_kl2_realdata.py — pull REAL Earth data along the true B-B' transect for the
Kinabalu Basin KL2 project. PUBLIC LANE only (GEBCO / satellite gravity).

Replaces the hand-drawn seabed profile used in every prior figure this session with
measured bathymetry, and attempts measured free-air gravity. Honesty rules enforced:
  * OFFLINE_STUBS.md rule 1 — never promote offline_stub to Earth truth.
  * OFFLINE_STUBS.md rule 2 — surface data_mode + provenance for every array.
  * Void Guard — "no data" is reported as UNMEASURED, never silently defaulted.

Usage: python3 fetch_kl2_realdata.py
"""

import json
import os
import sys
import time
import traceback

import numpy as np

OUT = "/root/GEOX/data/kl2_realdata"
os.makedirs(OUT, exist_ok=True)

# ── real transect ────────────────────────────────────────────────────────────
# Anchored on two named, verifiable features so the line is reproducible:
#   Layang-Layang / Swallow Reef  7.372 N, 113.847 E   (NW, Dangerous Grounds)
#   Mt Kinabalu                   6.075 N, 116.558 E   (Crocker Range, 4095 m)
# Extended NW into Dangerous Grounds and SE into the Sulu Sea.
ANCHOR_LL = (7.372, 113.847)
ANCHOR_KIN = (6.075, 116.558)
B = (7.78, 113.00)     # NW end
Bp = (5.10, 118.60)    # SE end


def great_circle_distance(lat1, lon1, lat2, lon2):
    """Haversine, km."""
    R = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


TOTAL_KM = great_circle_distance(B[0], B[1], Bp[0], Bp[1])
N = 700
t = np.linspace(0.0, 1.0, N)
LAT = B[0] + t * (Bp[0] - B[0])
LON = B[1] + t * (Bp[1] - B[1])
# cumulative along-track distance (km) for a labelled x-axis
DIST = np.concatenate([[0.0], np.cumsum(
    [great_circle_distance(LAT[i], LON[i], LAT[i + 1], LON[i + 1]) for i in range(N - 1)])])

# where do the two anchors fall along the track?
def along_track_of(pt):
    d = np.hypot((LAT - pt[0]) * 111.0, (LON - pt[1]) * 111.0 * np.cos(np.radians(pt[0])))
    return DIST[int(np.argmin(d))]


report = {
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "lane": "PUBLIC — no PETRONAS-confidential data",
    "transect": {
        "name": "B-B' (sabah_nw_se)",
        "B_nw": {"lat": B[0], "lon": B[1]},
        "B_prime_se": {"lat": Bp[0], "lon": Bp[1]},
        "anchors": {
            "layang_layang_swallow_reef": {"lat": ANCHOR_LL[0], "lon": ANCHOR_LL[1],
                                           "along_track_km": round(float(along_track_of(ANCHOR_LL)), 1)},
            "mt_kinabalu_4095m": {"lat": ANCHOR_KIN[0], "lon": ANCHOR_KIN[1],
                                  "along_track_km": round(float(along_track_of(ANCHOR_KIN)), 1)},
        },
        "total_length_km": round(float(TOTAL_KM), 1),
        "n_samples": int(N),
        "method": "linear lat/lon interpolation (adequate at 700 km, 5-8 deg N); cumulative haversine for distance axis",
    },
    "datasets": {},
}

np.savez(f"{OUT}/transect.npz", lat=LAT, lon=LON, dist_km=DIST)
print(f"transect B-B': {TOTAL_KM:.0f} km, {N} samples")
print(f"  Layang-Layang at {report['transect']['anchors']['layang_layang_swallow_reef']['along_track_km']} km")
print(f"  Mt Kinabalu   at {report['transect']['anchors']['mt_kinabalu_4095m']['along_track_km']} km")

# ── 1. GEBCO bathymetry via OPeNDAP (server-side subset) ─────────────────────
gebco_ok = False
BASE = "https://dap.ceda.ac.uk/bodc/gebco/global/gebco_2026/sub_ice_topography_bathymetry/netcdf/"
CANDIDATES = ["GEBCO_2026_sub_ice.nc"]
# verified 2026-10-08 from the live CEDA directory listing; earlier candidates 404'd
ETOPO_FALLBACK = ("https://www.ngdc.noaa.gov/thredds/dodsC/global/ETOPO2022/15s/"
                  "15s_bed_elev_netcdf/ETOPO_2022_v1_15s_bed_elev_N90W180.nc")
lat_lo, lat_hi = min(LAT) - 0.15, max(LAT) + 0.15
lon_lo, lon_hi = min(LON) - 0.15, max(LON) + 0.15

try:
    import xarray as xr
except Exception as e:                                    # pragma: no cover
    xr = None
    print(f"  xarray unavailable: {e}")

if xr is not None:
    SOURCES = [("gebco_2026_bathymetry", BASE + CANDIDATES[0]),
               ("etopo2022_15s_bed_elev", ETOPO_FALLBACK)]
    for label, url in SOURCES:
        try:
            print(f"  trying {label}: {url} ...")
            t0 = time.time()
            ds = xr.open_dataset(url)
            var = ("elevation" if "elevation" in ds.variables
                   else "z" if "z" in ds.variables else list(ds.data_vars)[0])
            box = ds[var].sel(lat=slice(lat_lo, lat_hi), lon=slice(lon_lo, lon_hi))
            arr = box.load().values                          # forces server-side subset
            blat = box.lat.values
            blon = box.lon.values
            ds.close()
            print(f"    OK in {time.time() - t0:.0f}s: {arr.shape}, var={var}")
            # sample along the transect (nearest-neighbour — no invented interpolation)
            bathy = np.array([arr[int(np.argmin(np.abs(blat - la))),
                                  int(np.argmin(np.abs(blon - lo)))]
                              for la, lo in zip(LAT, LON)], dtype=float)
            np.savez(f"{OUT}/real_bathy.npz", dist_km=DIST, lat=LAT, lon=LON,
                     bathy_m=bathy, grid_lat=blat, grid_lon=blon, source=label)
            report["datasets"][label] = {
                "data_mode": "live",
                "source_uri": url,
                "variable": var,
                "grid_shape": list(arr.shape),
                "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sampling": "nearest-neighbour, no interpolation (L0 preserved)",
                "units": "m relative to sea level (negative = below)",
                "stats": {"min_m": float(np.nanmin(bathy)), "max_m": float(np.nanmax(bathy)),
                          "mean_m": float(np.nanmean(bathy))},
                "ext_witness_ready": True,
            }
            print(f"    bathymetry: min {bathy.min():.0f} m, max {bathy.max():.0f} m")
            gebco_ok = True
            break
        except Exception as e:
            print(f"    FAILED: {type(e).__name__}: {str(e)[:220]}")

if not gebco_ok:
    report["datasets"]["bathymetry"] = {
        "data_mode": "UNMEASURED",
        "reason": "GEBCO OPeNDAP and ETOPO2022 THREDDS both failed — see stdout; "
                  "NOT substituted with a drawn profile",
        "ext_witness_ready": False,
    }

# ── 2. free-air gravity: attempt several live sources ────────────────────────
grav_ok = False
GRAV_SOURCES = [
    ("sandwell_ucsd_www", "https://topex.ucsd.edu/WWW_cgi-bin/get_data.cgi"),
    ("bgi_wgm2012", "http://bgi.obs-mip.fr/data-products/"),
    ("icgem", "https://icgem.gfz-potsdam.de/service/getdata"),
    ("noaa_ngdc_gravity", "https://www.ngdc.noaa.gov/mgg/gravity/"),
]
import urllib.request

reach = {}
for tag, url in GRAV_SOURCES:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GEOX/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            reach[tag] = {"http": r.status, "url": url}
    except Exception as e:
        reach[tag] = {"http": None, "url": url, "error": f"{type(e).__name__}: {str(e)[:120]}"}
    print(f"  gravity source {tag}: {reach[tag].get('http', reach[tag].get('error'))}")

report["datasets"]["free_air_gravity"] = {
    "data_mode": "UNMEASURED" if not grav_ok else "live",
    "reason": ("no reachable server-side gravity subset found this session. The legacy "
               "Sandwell-Smith CGI (topex.ucsd.edu/cgi-bin/get_data.cgi) returns HTTP 500 "
               "on POST for both grav_32.1 and grav_3. Reachability of alternates recorded "
               "below. NOT substituted with a hand-drawn curve — that was the defect in the "
               "Copilot figure that F13 corrected."),
    "sources_probed": reach,
    "ext_witness_ready": False,
    "unblock_path": [
        "WGM2012 global grid (BGI/IUGS) regional netCDF subset",
        "ICGEM spherical-harmonic model (e.g. XGM2019e / GECO) synthesised along B-B'",
        "UCSD Sandwell-Smith v32+ via the current REST endpoint (legacy CGI is 500)",
    ],
}

with open(f"{OUT}/provenance.json", "w") as fh:
    json.dump(report, fh, indent=2)

print("\n=== data_mode summary (OFFLINE_STUBS rule 2) ===")
for k, v in report["datasets"].items():
    print(f"  {k}: {v['data_mode']}")
print(f"\nprovenance -> {OUT}/provenance.json")
