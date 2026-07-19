# GEOX Open Data Sources Registry
> **Purpose:** Production wiring reference for real measurement data into GEOX.
> **Last updated:** 2026-07-05
> **Scope:** Freely accessible / open geoscience data with API or bulk download.

---

## 1. WELL LOG DATA

| Source | URL | API | Formats | Coverage | License | Python Lib | Difficulty |
|--------|-----|-----|---------|----------|---------|------------|------------|
| **Norway Diskos** | [sodir.no/en/diskos](https://www.sodir.no/en/diskos/wells/) | REST API (cloud-based, open API since 2015) | LAS, DLIS, CSV | Norwegian Continental Shelf | Open (free registration) | requests | Medium |
| **UK National Data Repository (NDR)** | [ndr.nstauthority.co.uk](https://ndr.nstauthority.co.uk/) | Bulk download portal (free registration) | LAS, SEG-Y, CSV | UK offshore | Open Government Licence | requests | Medium |
| **USGS Well Log Data** | [usgs.gov/programs/well-log-data](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/well-log-data) | Bulk download (no REST API) | LAS, CSV | US (state-by-state) | Public domain | requests | Hard (scattered) |
| **Kansas Geological Survey (KGS)** | [kgs.ku.edu/Magellan/Logs](https://www.kgs.ku.edu/Magellan/Logs/) | Web search + direct LAS download | LAS (v2, v3) | Kansas, US | Open | requests | Easy |
| **Australia NOPIMS** | [ga.gov.au/nopims](https://www.ga.gov.au/nopims) | Portal + bulk download | LAS, well reports, core images | Australian offshore | Open (free registration) | requests | Medium |
| **Australia NVCL** | [auscope.org.au/nvcl](https://www.auscope.org.au/nvcl/) | REST API (WFS/WMS) | HyLogger spectra, mineralogy CSV | Australia (state surveys) | Open | `nvcl_kit` (pip) | Easy |
| **Canada CER / C-NLOPB** | [cer-rec.gc.ca](https://www.cer-rec.gc.ca/en/about/north-offshore/access-information.html) | Portal + bulk download | LAS, well reports | Canada offshore (Atlantic) | Open Government | requests | Medium |
| **Ontario Petroleum Wells** | [geohub.lio.gov.on.ca](https://geohub.lio.gov.on.ca/) | ESRI REST API | GeoJSON, CSV, Shapefile | Ontario, Canada | Open Government | requests, arcgis | Easy |
| **HIFLD Oil & Gas Wells** | [hifld-geoplatform.opendata.arcgis.com](https://hifld-geoplatform.opendata.arcgis.com/) | ESRI REST, WFS, WMS | GeoJSON, CSV, Shapefile, GeoTIFF | US (all states) | Open | requests, arcgis | Easy |
| **NZ Petroleum & Minerals** | [nzpam.govt.nz/maps-geoscience](https://www.nzpam.govt.nz/maps-geoscience/geodata-catalogue) | Geodata Catalogue + bulk download | LAS, well reports, seismic | New Zealand | Open (free registration) | requests | Medium |
| **EarthAnalytics.ai (Diskos derivative)** | [earthanalytics.ai](https://www.earthanalytics.ai/interpreted-well-data-from-all-released-wells-on-the-ncs) | API / download | CSV, interpreted logs | Norwegian Continental Shelf | Open | requests | Easy |

---

## 2. SEISMIC DATA

| Source | URL | API | Formats | Coverage | License | Python Lib | Difficulty |
|--------|-----|-----|---------|----------|---------|------------|------------|
| **TerraNubis / Open Seismic Repository** | [terranubis.com/osr](https://terranubis.com/osr) | Direct download (free projects) | OpendTect format, SEG-Y | F3 (Netherlands), Penobscot (Canada), FORCE ML | CC BY-SA | `segyio`, `opendtect` | Easy |
| **SEG Open Data** | [seg.org/seam/open-data](https://seg.org/seam/open-data/) | Google Drive bulk download | SEG-Y, binary grids | SEAM Phase I (GoM synthetic), Time Lapse Pilot | Open (SEG) | `segyio` | Easy |
| **UK NDR Seismic** | [ndr.nstauthority.co.uk](https://ndr.nstauthority.co.uk/) | Portal + bulk download | SEG-Y | UK offshore | Open Government Licence | `segyio` | Medium |
| **Norway Diskos Seismic** | [sodir.no/en/diskos](https://www.sodir.no/en/diskos/) | REST API (cloud) | SEG-Y, SEGD | Norwegian Continental Shelf | Open (free registration) | `segyio` | Medium |
| **Australia NOPIMS Seismic** | [ga.gov.au/nopims](https://www.ga.gov.au/nopims) | Portal + bulk download | SEG-Y | Australian offshore | Open (free registration) | `segyio` | Medium |
| **NZ NZPAM Seismic** | [nzpam.govt.nz/maps-geoscience](https://www.nzpam.govt.nz/maps-geoscience/geodata-catalogue) | Geodata Catalogue | SEG-Y (2D + 3D) | New Zealand | Open (free registration) | `segyio` | Medium |
| **SeisDARE** | [essd.copernicus.org/articles/13/1053/2021](https://essd.copernicus.org/articles/13/1053/2021/) | Bulk download (academic) | SEG-Y, SEG-D, SU | Global (academic compilations) | CC BY | `segyio`, `obspy` | Medium |
| **USGS Seismic** | [pubs.usgs.gov](https://pubs.usgs.gov/) | Bulk download per publication | SEG-Y | US (various surveys) | Public domain | `segyio` | Hard (scattered) |
| **OpenSeisML** | [arxiv.org/html/2605.20539](https://arxiv.org/html/2605.20539) | Academic dataset | SEG-Y, LAS | UK NDR-derived | Academic | `segyio` | Medium |
| **USGS Earthquake Catalog (ComCat)** | [earthquake.usgs.gov/fdsnws/event/1](https://earthquake.usgs.gov/fdsnws/event/1/) | **REST API (FDSN)** | JSON, CSV, GeoJSON | Global (real-time + historical) | Public domain | `obspy`, `requests` | **Easy** |

---

## 3. GRAVITY & MAGNETICS

| Source | URL | API | Formats | Coverage | License | Python Lib | Difficulty |
|--------|-----|-----|---------|----------|---------|------------|------------|
| **EMAG2 v3** | [ncei.noaa.gov/EMAG2_V3](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.geophysical_models%3AEMAG2_V3) | Bulk download | GeoTIFF, NetCDF, CSV | Global (2-arc-min) | Public domain | `rasterio`, `xarray` | Easy |
| **BGI Gravity Models** | [bgi.obs-mip.fr](https://bgi.obs-mip.fr/grids-and-models-2/) | Bulk download | GeoTIFF, NetCDF, ASCII grid | Global (WGM2012) | Open | `rasterio`, `xarray` | Easy |
| **ICGEM** | [icgem.gfz-potsdam.de](https://icgem.gfz-potsdam.de/home) | **REST service** (grid computation) | Spherical harmonics → custom grids (GeoTIFF, ASCII) | Global | Open (GFZ) | `pyshtools`, `requests` | **Easy** |
| **Geoscience Australia Geophysics** | [ga.gov.au/data-pubs](https://www.ga.gov.au/data-pubs) | **WMS/WFS** + bulk download | GeoTIFF, NetCDF, Shapefile | Australia (national grids) | Open Government | `rasterio`, `owslib` | **Easy** |
| **SA SARIG Geophysics** | [services.sarig.sa.gov.au](https://services.sarig.sa.gov.au/vector/geophysical_data/wfs) | **WFS + WMS** | GeoJSON, Shapefile | South Australia | Open | `owslib`, `geopandas` | **Easy** |
| **Tellus (BGS/NERC)** | [bgs.ac.uk/gsinfon/tellus](https://www.bgs.ac.uk/geological-data/opengeoscience/) | Bulk download | GeoTIFF, CSV | UK (Northern Ireland, SW England) | Open Government | `rasterio` | Easy |
| **ETOPO Global Relief** | [ncei.noaa.gov/products/etopo-global-relief-model](https://www.ncei.noaa.gov/products/etopo-global-relief-model) | Bulk download | GeoTIFF, NetCDF | Global (1-arc-min) | Public domain | `rasterio`, `xarray` | Easy |
| **OpenTopography** | [portal.opentopography.org](https://portal.opentopography.org/apidocs/) | **REST API** (SRTM, ALOS, Copernicus, NASADEM) | GeoTIFF, ASCII grid | Global (30m-90m) | Open (API key required) | `bmi-topography` (pip) | **Easy** |

---

## 4. GEOLOGICAL MAPS & STRATIGRAPHY

| Source | URL | API | Formats | Coverage | License | Python Lib | Difficulty |
|--------|-----|-----|---------|----------|---------|------------|------------|
| **Macrostrat** | [macrostrat.org](https://macrostrat.org/) | **REST API v2** (`/api/v2/`) | JSON, GeoJSON | Global (225+ maps, 2.5M polygons) | Open (CC BY) | `requests`, `rmacrostrat` (R) | **Easy** |
| **OneGeology Portal** | [portal.onegeology.org](http://portal.onegeology.org/) | **WMS + WFS** (OGC standards) | GeoJSON, GML, images | Global (1:1M scale) | Varies by contributor | `owslib`, `geopandas` | **Easy** |
| **BGS OpenGeoscience** | [bgs.ac.uk/geological-data/opengeoscience](https://www.bgs.ac.uk/geological-data/opengeoscience/) | **WMS, WFS, OGC API** | GeoJSON, GML, images | UK | Open Government Licence | `owslib`, `geopandas` | **Easy** |
| **BGS Boreholes (SOBI)** | [bgs.ac.uk/datasets/boreholes-index](https://www.bgs.ac.uk/datasets/boreholes-index/) | **OGC API, WFS** | JSON, GeoJSON | UK (1M+ boreholes) | Open Government | `requests`, `geopandas` | **Easy** |
| **USGS Geological Maps** | [mrdata.usgs.gov](https://mrdata.usgs.gov/) | **WMS + bulk download** | Shapefile, GeoJSON, KML | US + territories | Public domain | `geopandas`, `owslib` | Easy |
| **Geoscience Australia Geology** | [ga.gov.au/data-pubs](https://www.ga.gov.au/data-pubs) | **WMS/WFS** | GeoJSON, Shapefile | Australia | Open Government | `owslib`, `geopandas` | **Easy** |
| **Macrostrat API (detailed)** | `https://macrostrat.org/api/v2/` | REST endpoints: `/defs/strat_names`, `/defs/columns`, `/geologic_units/map`, `/defs/intervals` | JSON | Global | Open | `requests` | **Easy** |

### Macrostrat Key Endpoints (already wired?):
```
GET /api/v2/defs/strat_names?strat_name={name}
GET /api/v2/defs/columns?col_id={id}
GET /api/v2/geologic_units/map?lat={lat}&lng={lng}
GET /api/v2/defs/intervals?interval_name={name}
GET /api/v2/geologic_units/map?strat_name_id={id}&format=geojson_bare
```

---

## 5. GEOCHEMISTRY & PETROLOGY

| Source | URL | API | Formats | Coverage | License | Python Lib | Difficulty |
|--------|-----|-----|---------|----------|---------|------------|------------|
| **EarthChem / PetDB 2.0** | [earthchem.org](https://earthchem.org/) | **REST API v4** (Node.js/Express, OpenSearch backend) | JSON, CSV export | Global (30M+ analytical values) | Open (CC BY) | `earthchem-pyclient` (pip/GitHub) | **Easy** |
| **GEOROC 2.0** | [georoc.eu](https://georoc.eu/) | **REST API** (DIGIS) | JSON, CSV | Global (32M+ data values, 20K+ pubs) | Open | `pygeoroc`, requests | **Easy** |
| **USGS National Geochemical Database** | [mrdata.usgs.gov/ngdb](https://mrdata.usgs.gov/ngdb/) | Bulk download (Shapefile + CSV) | CSV, Shapefile | US + Alaska (1.5M samples) | Public domain | `pandas`, `geopandas` | Easy |
| **NAVDAT** | [navdat.org](http://navdat.org/) | Via EarthChem Portal | CSV | Western US volcanics | Open | via EarthChem | Medium |
| **SedDB** | [www.earthchem.org/seddb](https://earthchem.org/) | Via EarthChem Portal | CSV | Global marine sediments | Open | via EarthChem | Medium |
| **MetPetDB** | [metpetdb.rpi.edu](https://earthchem.org/) | Via EarthChem Portal | CSV | Global metamorphic petrology | Open | via EarthChem | Medium |
| **EarthChem Library** | [library.earthchem.org](https://earthchem.org/) | Upload/download repository | CSV, various | Global (community-contributed) | Open | requests | Easy |
| **GANSEKI** | Via EarthChem Portal | Integrated | CSV | Japanese geochemistry | Open | via EarthChem | Medium |

### EarthChem/PetDB API v4 Endpoints:
```
Base: https://petdb.org/api/v4/
GET /samples?filters={...}
GET /analyses?filters={...}
GET /citations
POST /export (async, returns S3 URL)
```

### GEOROC 2.0 API:
```
Base: https://georoc.eu/api/
Requires API key (free registration)
GET /samples, /compilations, /references
```

---

## 6. TECTONIC & PLATE RECONSTRUCTION

| Source | URL | API | Formats | Coverage | License | Python Lib | Difficulty |
|--------|-----|-----|---------|----------|---------|------------|------------|
| **GPlates** | [gplates.org](https://www.gplates.org/) | Desktop + **pyGPlates Python API** | GPML, Shapefile, raster | Global (deep time) | Open (GPL) | `pygplates` (pip) | **Easy** |
| **GPlately** | [github.com/GPlates/gplately](https://github.com/GPlates/gplately) | Python package | GPML, CSV | Global | Open (GPL) | `gplately` (pip) | **Easy** |
| **PlateTectonicTools** | [github.com/EarthByte/PlateTectonicTools](https://github.com/GPlates/GPlates) | Python package | GPML | Global | Open | `ptt` (pip) | Easy |
| **EarthByte Rotations** | [earthbyte.org](https://www.earthbyte.org/) | Bulk download | ROT, GPML | Global reconstructions | Open | pygplates | Easy |
| **Macrostrat Intervals** | `macrostrat.org/api/v2/defs/intervals` | REST API | JSON | Global (geochronological) | Open | requests | **Easy** |

---

## 7. SATELLITE / REMOTE SENSING

| Source | URL | API | Formats | Coverage | License | Python Lib | Difficulty |
|--------|-----|-----|---------|----------|---------|------------|------------|
| **Sentinel Hub** | [sentinel-hub.com](https://www.sentinel-hub.com/) | **REST API** (OGC WMS/WCS) | GeoTIFF, NetCDF | Global (Sentinel-1/2/3) | Open (Copernicus) | `sentinelhub-py` (pip) | **Easy** |
| **Copernicus Data Space** | [dataspace.copernicus.eu](https://dataspace.copernicus.eu/) | **STAC API + S3** | GeoTIFF, NetCDF | Global | Open (Copernicus) | `sentinelhub-py`, `pystac` | **Easy** |
| **USGS Landsat** | [usgs.gov/landsat](https://www.usgs.gov/landsat) | **STAC API** (via EarthExplorer / M2M) | GeoTIFF | Global | Public domain | `landsatxplore`, `pystac` | Medium |
| **AWS Open Data (Landsat/Sentinel)** | [registry.opendata.aws](https://registry.opendata.aws/) | **S3 direct access** | COG (Cloud-Optimized GeoTIFF) | Global | Open | `rasterio`, `stackstac` | **Easy** |
| **ASTER GDEM** | [asterweb.jpl.nasa.gov](https://asterweb.jpl.nasa.gov/gdem.asp) | Bulk download | GeoTIFF | Global (30m) | Open (NASA) | `rasterio` | Easy |
| **SRTM DEM** | Via OpenTopography | **REST API** | GeoTIFF | Global (30m/90m) | Open (NASA) | `bmi-topography` | **Easy** |
| **Google Earth Engine** | [earthengine.google.com](https://earthengine.google.com/) | **Python API** (cloud compute) | Various (computed on server) | Global (massive catalog) | Free (registration) | `ee` (pip) | Medium |
| **OpenTopography** | [portal.opentopography.org](https://portal.opentopography.org/apidocs/) | **REST API** | GeoTIFF, ASCII | Global (multi-DEM) | Open (API key) | `bmi-topography` | **Easy** |

---

## 8. ADDITIONAL / CROSS-CUTTING

| Source | URL | API | Formats | Coverage | License | Python Lib | Difficulty |
|--------|-----|-----|---------|----------|---------|------------|------------|
| **Macrostrat xDD** | [xdd.wisc.edu](https://xdd.wisc.edu/) | REST API | JSON | Global (literature mining) | Open | requests | Medium |
| **PANGAEA** | [pangaea.de](https://www.pangaea.de/) | **REST API + OAI-PMH** | CSV, NetCDF, JSON | Global (earth science) | CC BY | `pangaeapy` | Easy |
| **SEDAC (NASA)** | [sedac.ciesin.columbia.edu](https://sedac.ciesin.columbia.edu/) | WMS/WFS + bulk download | GeoTIFF, Shapefile, CSV | Global | Open | `owslib` | Easy |
| **UNAVCO / IRIS** | [iris.edu](https://www.iris.edu/) | **FDSN web services** | miniSEED, SAC, RESP | Global (seismology) | Open | `obspy` | **Easy** |
| **FDSN Federation** | [fdsn.org](https://fdsn.org/) | **Standardized REST** | miniSEED, StationXML | Global | Open | `obspy` | **Easy** |

---

## PRIORITY WIRING ORDER (for GEOX production)

### Tier 1 — Wire immediately (REST APIs, easy integration):
1. **Macrostrat** — geological maps + stratigraphy REST API
2. **OpenTopography** — DEM via REST API (`bmi-topography`)
3. **USGS ComCat** — earthquake catalog REST API
4. **ICGEM** — gravity field model computation service
5. **EarthChem/PetDB v4** — geochemistry REST API
6. **GEOROC 2.0** — geochemistry REST API
7. **FDSN/IRIS** — seismology web services via ObsPy
8. **Sentinel Hub** — satellite imagery REST API

### Tier 2 — Wire with registration (portal + download):
9. **Norway Diskos** — well logs + seismic (REST API, free registration)
10. **UK NDR** — well logs + seismic (bulk download, OGL)
11. **BGS OpenGeoscience** — UK geology WMS/WFS
12. **Geoscience Australia** — geophysics WMS/WFS
13. **EMAG2 v3** — global magnetics (bulk GeoTIFF)
14. **BGI WGM2012** — global gravity (bulk GeoTIFF)
15. **TerraNubis/OSR** — open seismic volumes (F3, Penobscot)

### Tier 3 — Wire later (scattered, harder):
16. **USGS NGDB** — US geochemistry (bulk CSV)
17. **NZ NZPAM** — NZ well logs + seismic
18. **Australia NVCL** — drill core mineralogy
19. **GPlates/pyGPlates** — plate reconstructions
20. **Google Earth Engine** — cloud-based remote sensing

---

## PYTHON LIBRARY QUICK REFERENCE

```bash
# Geospatial core
pip install rasterio geopandas owslib xarray rioxarray

# Seismic
pip install segyio obspy

# Well logs
pip install lasio welly striplog

# Geochemistry
pip install earthchem-pyclient  # github.com/jesserobertson/earthchem-pyclient
pip install pygeoroc             # github.com/pofatu/pygeoroc

# Remote sensing
pip install sentinelhub-py landsatxplore pystac stackstac
pip install earthengine-api      # Google Earth Engine

# DEM / Topography
pip install bmi-topography       # OpenTopography REST API

# Tectonic reconstruction
pip install pygplates gplately

# Geological data
pip install requests             # Macrostrat REST API

# General earth science
pip install pangaeapy            # PANGAEA
```

---

## NOTES

- **Macrostrat is the single most valuable API for GEOX** — covers stratigraphy, geological maps, geochronology, and links to literature (xDD). Wire first.
- **EarthChem + GEOROC** together cover >30M geochemical analyses globally. Both have REST APIs.
- **Diskos** is the gold standard for national data repositories — cloud-based with open API since 2015.
- **ICGEM** is unique — you send spherical harmonic coefficients and it returns computed gravity grids on-the-fly.
- **OpenTopography** + **Sentinel Hub** + **AWS Open Data** cover all remote sensing needs with proper Python SDKs.
- **FDSN** standardizes seismology web services globally — ObsPy wraps it beautifully.
- All "bulk download" sources can be cached locally and served via GEOX's own API layer.
