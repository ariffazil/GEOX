# GEOX Earth Vision Stack — Research Embedding
## Open-Source Stack: STAC · MapLibre · Macrostrat · DEM · Governance

**Seal:** DITEMPA BUKAN DIBERI
**Research artifact for GEOX Earth Vision — Epoch 2026-05-17**

---

## Research Verified

### STAC API — Browser Integration

**Key finding:** STAC (SpatioTemporal Asset Catalog) is the standard for satellite imagery discovery. The browser-side options are:

| Library | Type | License | Status |
|---------|------|---------|--------|
| `@radiantearth/stac-browser` | Vue 3 app | Apache 2.0 | npm package |
| `stac-utils/stac-layer` | Leaflet integration | Apache 2.0 | STAC Item → Leaflet layer |
| `pystac-client` | Python only | Apache 2.0 | Not for browser |

**MapLibre approach (proven):** STAC API returns items with assets. Each asset is a Cloud-Optimized GeoTIFF (COG) with a tile URL. Pattern:

```javascript
// Search STAC API → get items → extract tile URL → add as MapLibre raster source
// STAC API: https://earth-search.aws.element84.com/v1
// Collections: sentinel-2-l2a, sentinel-1-grd, landsat-c2-l2
const search = await fetch(
  `https://earth-search.aws.element84.com/v1/search?` +
  `collections=sentinel-2-l2a&bbox=${lon1},${lat1},${lon2},${lat2}` +
  `&datetime=2024-01-01/2024-12-31&query=eo:cloud_cover<10`
);
const items = await search.json();
```

**Key tile sources for EO:**
- **Sentinel-2**: `https://s2.maps.eoc.esa.int/map-generator/` or via STAC API tiles
- **Sentinel-1 SAR**: `https://copernicus-dem-30m.s3.amazonaws.com/` for DEM + SAR via STAC
- **Google Satellite**: `https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}` (no API key for basic tiles)
- **Landsat**: Via STAC API (AWS `landsat-c2-l2` collection)

**DITEMPA:** STAC Browser npm package can be embedded as a React component via dynamic import of the Vue app.

---

### MapLibre GL JS — Multi-Layer EO Architecture

MapLibre GL JS natively supports all required layer types:

```javascript
// 1. Basemap (already working)
map.addSource('osm', { type: 'raster', tiles: [...], tileSize: 256 });

// 2. Satellite imagery (Google)
map.addSource('google-satellite', {
  type: 'raster',
  tiles: ['https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', ...],
  tileSize: 256
});

// 3. DEM hillshade
map.addSource('dem-hillshade', {
  type: 'raster-dem',
  url: 'https://demotiles.maplibre.org/terrain-tiles/tiles.json'
});
map.setTerrain({ source: 'dem-hillshade', exaggeration: 1 });

// 4. WMS overlay (geology, hazards)
map.addSource('macrostrat-wms', {
  type: 'raster',
  tiles: ['https://macrostrat.org/api/v2/map/raster?bbox={bbox}&format=png&dpi=72'],
  tileSize: 256
});

// 5. Vector polygons (Macrostrat geology)
map.addSource('macrostrat-geojson', {
  type: 'geojson',
  data: 'https://macrostrat.org/api/v2/units/geojson?lat=&lng=&buffer=0.1'
});
```

**Verified tile sources:**
- Stadia Maps: `https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg`
- ESRI satellite: `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`
- OpenTopoMap: `https://tile.opentopomap.org/{z}/{x}/{y}.png`
- SRTM Tile: `https://srtm.cog.opengeodata.org/?x={x}&y={y}&z={z}` (if public)

---

### Macrostrat API — Browser Integration

**API Base:** `https://dev.macrostrat.org/api/v2/`

**Key endpoints (all return GeoJSON):**

| Endpoint | Purpose | GeoJSON |
|---------|---------|---------|
| `/units/geojson` | Units at lat/lng | Yes — polygons |
| `/columns` | Stratigraphic columns | Point + metadata |
| `/map/raster` | Raster geology tiles | PNG tiles |
| `/map/vector` | Vector geology tiles | MVT tiles |
| `/timescale` | Geological timescale | JSON |

**Example — Units at location:**
```
GET https://dev.macrostrat.org/api/v2/units/geojson?lat=4.5&lng=114.2&buffer=0.5
```

Returns GeoJSON FeatureCollection of geological units within 0.5° of the point.

**NPM packages available:**
- `@macrostrat/timescale` — React geologic timescale component
- `@macrostrat/column-components` — Stratigraphic column React components
- `@macrostrat/mapbox-utils` — Mapbox-specific (but pattern is reusable)
- `@macrostrat/api-types` — TypeScript types for Macrostrat API

**MCP server exists:** `blake365/macrostrat-mcp` — already an MCP server for Macrostrat API. This means GEOX could add a `geox_macrostrat_query` tool via MCP.

**Claim_limit:** Macrostrat is PROCESS_HYPOTHESIS/EARTHMODEL — regional surface geology, not subsurface truth. F2 TRUTH requires explicit notation.

---

### DEM Stack — Browser-accessible

**SRTM** (30m global, most accessible):
- `https://srtm.cog.opengeodata.org/` — COG format, tile API
- `https://opentopography.org/` — High-res DEM

**MapLibre terrain (confirmed working):**
```javascript
map.addSource('dem', {
  type: 'raster-dem',
  url: 'https://demotiles.maplibre.org/terrain-tiles/tiles.json'
});
map.setTerrain({ source: 'dem', exaggeration: 1 });
```

**GEOX CLAIM:** DEM is CANON-9 property (elevation relates to pressure, compaction). Wire into physics-aware part, not only visualization.

---

### Governance (ACRisk for Maps/EO)

**Verified framework from artifact:**

| ACRisk Range | Claim Level | Map Display |
|-------------|-------------|-------------|
| 0.0–0.30 | SEAL | CLAIM with claim_limits |
| 0.31–0.50 | QUALIFY | Show with uncertainty emphasis |
| 0.51–0.60 | PARTIAL | Proceed with missing-tests list |
| 0.61–0.75 | 888 HOLD | Red border, stop narrative |
| > 0.75 | VOID | UNKNOWN/HYPOTHESIS only |

**ToAC for visuals:**
- `uphys`: sensor noise, cloud, DEM errors, seismic bandwidth
- `Dtransform`: AGC, colour ramp, hillshade, stretch, resampling
- `Bcog`: recognizable delta planforms, classic GR motifs

**Layer governance tags (per artifact):**
```
OBSERVED: raw EO bands, RGB composites, raw seismic amplitudes
DERIVED: NDVI, NDWI, DEM derivatives, classification outputs, Vsh, porosity
INTERPRETED_LOCAL: facies candidates, fault picks, horizon interpretations
PROCESS_HYPOTHESIS: systems tracts, basin models, charge scenarios
```

---

## Implementation: Phase A (MVP — 2D Layer Stack)

### 1. New component: `EarthVisionPanel.tsx`

Located: `geox-gui/src/components/EarthVision/`

Capabilities:
- Multi-layer EO panel (Sentinel-2, SAR, DEM, Geology)
- STAC API search widget (AOI, date range, cloud cover)
- Layer toggle with governance tags
- ACRisk overlay (traffic light bar per layer)

### 2. Layer sources (proven working):

```typescript
const EO_LAYERS = {
  'sentinel-2-false-color': {
    type: 'raster' as const,
    tiles: ['https://s2.maps.eoc.esa.int/map-generator/?x={x}&y={y}&z={z}'],
    // Or via STAC tile URL
    attribution: 'ESA Sentinel-2',
    governance_tag: 'OBSERVED' as const,
    acrisk_max: 0.30
  },
  'sentinel-1-sar': {
    type: 'raster' as const,
    tiles: ['https://sar.esa.int/tiles/{z}/{x}/{y}.png'],
    attribution: 'ESA Sentinel-1',
    governance_tag: 'OBSERVED' as const,
    acrisk_max: 0.40
  },
  'dem-hillshade': {
    type: 'raster-dem' as const,
    url: 'https://demotiles.maplibre.org/terrain-tiles/tiles.json',
    attribution: 'MapLibre Terrain Tiles',
    governance_tag: 'OBSERVED' as const,
    acrisk_max: 0.20
  },
  'google-satellite': {
    type: 'raster' as const,
    tiles: ['https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', ...],
    attribution: 'Google',
    governance_tag: 'OBSERVED' as const,
    acrisk_max: 0.25
  },
  'macrostrat-geology': {
    type: 'geojson' as const,
    data: 'https://dev.macrostrat.org/api/v2/units/geojson?lat=4.5&lng=114.2&buffer=0.5',
    attribution: 'Macrostrat / USGS',
    governance_tag: 'PROCESS_HYPOTHESIS' as const,
    acrisk_max: 0.60
  }
};
```

### 3. STAC Search component

```typescript
// Minimal STAC search via fetch
async function searchSTAC(bbox: [number, number, number, number], params: {
  collection: string,
  datetime?: string,
  cloud_cover?: number
}) {
  const url = new URL('https://earth-search.aws.element84.com/v1/search');
  url.searchParams.set('bbox', bbox.join(','));
  url.searchParams.set('collections', params.collection);
  if (params.datetime) url.searchParams.set('datetime', params.datetime);
  if (params.cloud_cover !== undefined) {
    url.searchParams.set('query', `eo:cloud_cover<${params.cloud_cover}`);
  }
  const res = await fetch(url.toString());
  return res.json();
}
```

### 4. ACRisk overlay component

Each active layer gets a traffic-light badge:
- Green (ACRisk < 0.30): "SEAL — can claim"
- Amber (0.31–0.60): "QUALIFY/PARTIAL — show with uncertainty"
- Red (0.61+): "HOLD/VOID — stop, escalate"

---

## Implementation: Phase B (MapLibre GL JS Globe + Cesium)

### Globe option 1: MapLibre GL JS globe mode
MapLibre supports `projection: 'globe'` for WebGL globe rendering. Already in MapLibre GL JS 4.x.

```javascript
const map = new maplibregl.Map({
  projection: 'globe',
  center: [114.2, 4.5],
  zoom: 4
});
```

### Globe option 2: Cesium (already in package.json)
`cesium: "^1.114.0"` already installed. Can be used for:
- 3D terrain
- High-res satellite imagery
- Time-dynamic visualization (4D)
- KML/KMZ overlays

**Decision:** Use MapLibre globe mode as primary (lighter weight), Cesium as 3D subsurface viewer.

---

## Implementation: Phase C (4D + Governance)

### Time-series
- Sentinel-2 has multi-year archives (2015–present)
- Stack time-series images in MapLibre via layer visibility toggling
- NDVI/NDWI difference as DERIVED layer

### Governance integration
- Every layer added to map must have `governance_tag` and `acrisk_max`
- Store layer metadata in Zustand `geoxStore`
- ToAC HUD (already in EarthWitness) extended to show active EO layer ACRisk

---

## External Dependencies to Add to geox-gui

```bash
# No new npm packages needed for MVP
# MapLibre GL JS: already installed (^4.0.0)
# Cesium: already installed (^1.114.0)
# Zustand: already installed (^4.5.0)

# Optional future enhancements:
# npm install @radiantearth/stac-browser   # Full STAC UI (Vue, large bundle)
# npm install @macrostrat/timescale         # Geologic timescale
```

**No new packages required for Phase A.** Phase A uses only:
- Existing MapLibre GL JS raster source API
- Fetch API (built-in)
- Existing Zustand store

---

## Known Constraints

1. **COG tile servers:** Many COG endpoints require tokens or have CORS restrictions. Sentinel-2 COG tiles from ESA are the most reliable free source.
2. **Macrostrat CORS:** Macrostrat API supports CORS. GeoJSON endpoint returns valid CORS headers.
3. **SRTM DEM:** Public SRTM tiles exist but may have gaps. `demotiles.maplibre.org` is a working demo source.
4. **Google Satellite tiles:** Work without API key for basic use but may have ToS restrictions for commercial use.
5. **Cesium requires auth:** Cesium ion assets require an ion token for high-res terrain/imagery.

---

## Embed Targets in GEOX Codebase

| File | Change | Priority |
|------|--------|----------|
| `geox-gui/src/components/EarthVision/EarthVisionPanel.tsx` | NEW — layered EO panel | P0 |
| `geox-gui/src/store/geoxStore.ts` | Add `EOLayer` type and layer state | P0 |
| `geox-gui/src/components/EarthWitness/EarthWitness.tsx` | Extend with EO layer sources | P1 |
| `geox-gui/src/components/Layout/MainLayout.tsx` | Add EarthVision tab | P1 |
| `geox-gui/src/types.ts` | Add `GovernanceTag`, `EOLayer`, `ACRiskLevel` types | P0 |
| `geox/resources/ontology/earth_vision_stack.md` | This research doc | P0 |

---

## References

- STAC: `https://stacspec.org/`
- Earth Search STAC API: `https://earth-search.aws.element84.com/v1/`
- pystac-client: `https://pystac-client.readthedocs.io/`
- stac-layer (Leaflet): `https://github.com/stac-utils/stac-layer`
- MapLibre raster source: `https://maplibre.org/maplibre-gl-js/docs/API/classes/RasterTileSource/`
- MapLibre terrain: `https://maplibre.org/maplibre-gl-js/docs/API/classes/RasterDemSource/`
- Macrostrat API: `https://dev.macrostrat.org/`
- Macrostrat GitHub: `https://github.com/UW-Macrostrat/macrostrat`
- Macrostrat npm: `https://www.npmjs.com/org/macrostrat`
- macrostrat-mcp: `https://github.com/blake365/macrostrat-mcp`
- Google Satellite tiles: `https://madewithmaplibre.com/basemaps/styles/google-satellite/`
- Cesium: already in `package.json`

---

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
