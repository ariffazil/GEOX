# GEOX Offline Stub Fetchers — H7 Entropy Register

> **Status:** ACTIVE inventory (2026-07-25)  
> **Action:** Do not treat offline stub data as Earth truth (F2).  
> **Default:** Most fetchers set `*_OFFLINE=1` by default → `mode=offline_stub`.  
> **Cutover:** Prefer live when credentials + network available; archive cold later.

## Count: 18 fetchers with offline-stub path

| Fetcher | Env flag (default offline) |
|---------|----------------------------|
| onegeology_fetcher.py | (check file) |
| usgs_water_fetcher.py | `GEOX_USGS_WATER_OFFLINE` |
| emag2_fetcher.py | `GEOX_EMAG2_OFFLINE` |
| usgs_earthquake_fetcher.py | (offline path) |
| wsm_stress_fetcher.py | `GEOX_WSM_OFFLINE` |
| landsat_stac_fetcher.py | `GEOX_STAC_OFFLINE` |
| noaa_swpc_fetcher.py | (offline path) |
| grace_fetcher.py | `GEOX_GRACE_OFFLINE` |
| era5_fetcher.py | (offline path) |
| magic_paleomag_fetcher.py | (offline path) |
| copernicus_marine_fetcher.py | `GEOX_CMEMS_OFFLINE` |
| gebco_fetcher.py | (offline path) |
| gplates_fetcher.py | (offline path) |
| earthchem_fetcher.py | `GEOX_EARTHCHEM_OFFLINE` |
| erddap_fetcher.py | (offline path) |
| nsta_uk_fetcher.py | (offline path) |
| etopo_fetcher.py | (offline path) |
| ihfc_heatflow_fetcher.py | `GEOX_HEATFLOW_OFFLINE` |

## Entropy policy

1. **Never** promote `mode=offline_stub` results to SEAL-grade Earth claims.  
2. Agents must surface `mode` in every GEOX evidence envelope.  
3. Full archive to cold storage requires import-graph proof (`rg` zero callers) — deferred.  
4. Live enable is per-fetcher env flip after credential audit (T2).

## H7 resolution this session

- Documented inventory (entropy: ambiguity → clarity).  
- No mass delete (would break import surface).  
- Next: per-organ smoke that fails if stub used under `require_live=1`.

DITEMPA BUKAN DIBERI
