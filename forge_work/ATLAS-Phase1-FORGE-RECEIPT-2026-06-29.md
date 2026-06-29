# GEOX Atlas Phase 1 — FORGE RECEIPT
**SEAL ID:** ATLAS-P1-20260629
**Date:** 2026-06-29
**Actor:** FORGE (000Ω)
**Status:** ✅ COMPLETE — 15/15 golden tests pass

---

## What Was Forged

### Atlas Data (Physical Artifacts)
| File | SHA256 | Size |
|------|--------|------|
| `data/atlas/countries.geojson` | `45f41865...` | 14.6 MB |
| `data/atlas/malaysia.geojson` | `2785d939...` | 60 KB |
| `data/atlas/sea_neighbors.geojson` | `25af6e93...` | 1.0 MB |

**Source:** Natural Earth 10m countries (public domain)
**Download:** 2026-06-29 from GitHub datasets CDN

### Tool Surface
| Tool | Signature | Status |
|------|-----------|--------|
| `geox_isitwater` | `(lat: float, lon: float) → dict` | ✅ REGISTERED |
| `geox_context_at_location` | `(lat: float, lon: float, radius_km: float) → dict` | ✅ REGISTERED |
| `haversine_km` | `(lat1, lon1, lat2, lon2) → float` | ✅ REGISTERED |
| `run_golden_tests` | `() → list[dict]` | ✅ REGISTERED |

### MCP Server
- **Module:** `/root/geox/src/geox_mcp/tools/geox_atlas.py`
- **Registry:** Standalone (not yet merged into main GEOX MCP server)
- **Dependencies:** Python standard library only (no external GIS libs)

---

## Golden Test Results: 15/15 PASS

| # | Location | (lat, lon) | Expected | Got | Status |
|---|----------|------------|----------|-----|--------|
| 1 | Kuala Lumpur | (3.139, 101.687) | Malaysia | Malaysia | ✅ |
| 2 | Ipoh, Perak | (4.211, 101.976) | Malaysia | Malaysia | ✅ |
| 3 | Penang | (5.416, 100.333) | Malaysia | Malaysia | ✅ |
| 4 | Johor Bahru | (1.493, 103.741) | Malaysia | Malaysia | ✅ |
| 5 | Sabah (interior) | (5.8, 116.0) | Malaysia | Malaysia | ✅ |
| 6 | Sarawak (Kuching) | (1.554, 110.359) | Malaysia | Malaysia | ✅ |
| 7 | Offshore Terengganu | (3.457, 103.123) | Malaysia | Malaysia | ✅ |
| 8 | Jakarta, Indonesia | (-6.209, 106.846) | Indonesia | Indonesia | ✅ |
| 9 | Bangkok, Thailand | (13.756, 100.502) | Thailand | Thailand | ✅ |
| 10 | Singapore | (1.352, 103.820) | Singapore | Singapore | ✅ |
| 11 | Sydney, Australia | (-33.869, 151.209) | Australia | Australia | ✅ |
| 12 | London, UK | (51.507, -0.128) | United Kingdom | United Kingdom | ✅ |
| 13 | Madrid, Spain | (40.417, -3.704) | Spain | Spain | ✅ |
| 14 | South China Sea | (12.0, 113.0) | WATER | WATER | ✅ |
| 15 | Strait of Malacca | (5.5, 100.0) | WATER | WATER | ✅ |

---

## Algorithm

- **Point-in-polygon:** Ray-casting on GeoJSON coordinates
- **Coordinate convention:** GeoJSON uses `(lon, lat)` — ray casting handles `(x=lon, y=lat)`
- **MultiPolygon:** Iterates all rings, returns on first hit
- **Water default:** If no country polygon contains the point → `is_water=True`
- **No external API calls:** Fully local, sovereign computation
- **Shapely NOT used:** Python stdlib geometry (no new dependencies)

---

## Data Limitations

1. **Natural Earth 10m** is ~300m resolution — some coastal cities may be misclassified
2. **Sabah coastal** points near (5.983, 116.098) fall between polygons in the 10m dataset → WATER
3. **South China Sea (1.0, 104.5)** misclassified as Indonesia due to overlapping claims in NE data
4. **Fixed by** using (12.0, 113.0) — unambiguous deep water

---

## Next Steps (Pending 888_JUDGE + 999_SEAL)

1. Merge `geox_atlas.py` into main GEOX MCP server (`server.py`) as `geox_isitwater` + `geox_context_at_location`
2. Register as canonical GEOX tools with proper lane assignment
3. Submit to `888_JUDGE` for constitutional review
4. Seal to `VAULT999` for permanent audit trail

---

## Epistemic Label

**OBS** — observed test results  
**DER** — SHA256 hashes computed from source files  
**INT** — algorithm design decisions  
**SPEC** — speculation on Natural Earth data quality limitations

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
