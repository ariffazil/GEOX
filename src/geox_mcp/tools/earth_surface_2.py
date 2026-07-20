"""
earth_surface_2.py — MCP tools for Extended Earth Dimensions (D4-D17).

14 tools covering the remaining open-data dimensions:
  D4:  geox_heatflow_query        — IHFC Global Heat Flow Database
  D5:  geox_stress_query          — World Stress Map 2025
  D7:  geox_plate_reconstruct     — GPlates plate tectonic reconstruction
  D6:  geox_geochem_query         — EarthChem/PetDB geochemistry
  D15: geox_uk_petroleum_query    — NSTA UK offshore petroleum
  D10: geox_ocean_query           — Copernicus Marine (CMEMS)
  D10: geox_erddap_query          — NOAA ERDDAP universal ocean gateway
  D16: geox_geology_map_query     — OneGeology national geological maps
  D8:  geox_paleomag_query        — MagIC paleomagnetism database
  D9:  geox_gravity_change_query  — GRACE-FO time-variable gravity
  D11: geox_climate_reanalysis    — ERA5 ECMWF reanalysis
  D12: geox_hydrology_query       — USGS Water Services
  D14: geox_satellite_catalog     — Landsat/MODIS/Sentinel via STAC
  D17: geox_space_weather         — NOAA SWPC geomagnetic/solar

All tools follow GEOX constitutional envelope.

DITEMPA BUKAN DIBERI — the earth dimensions are forged through evidence.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.tools.earth_surface_2")


# ── D4: Heat Flow ──
class HeatFlowRequest(BaseModel):
    minlatitude: float | None = None
    maxlatitude: float | None = None
    minlongitude: float | None = None
    maxlongitude: float | None = None
    limit: int = 100


async def geox_heatflow_query(request: HeatFlowRequest) -> dict[str, Any]:
    """Query IHFC Global Heat Flow Database. OBSERVED — ~91k measurements worldwide."""
    from geox_core.io.ihfc_heatflow_fetcher import HeatFlowQuery, IHFCHeatFlowFetcher

    fetcher = IHFCHeatFlowFetcher()
    q = HeatFlowQuery(**request.model_dump())
    r = fetcher.query(q)
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_heatflow_query",
        "measurements": r.measurements,
        "count": r.count,
        "citation": r.citation,
        "note": r.note,
    }


# ── D5: Crustal Stress ──
class StressRequest(BaseModel):
    minlatitude: float | None = None
    maxlatitude: float | None = None
    minlongitude: float | None = None
    maxlongitude: float | None = None
    quality: str | None = None
    limit: int = 100


async def geox_stress_query(request: StressRequest) -> dict[str, Any]:
    """Query World Stress Map (WSM 2025). OBSERVED — ~100k stress orientation measurements."""
    from geox_core.io.wsm_stress_fetcher import StressQuery, WSMStressFetcher

    fetcher = WSMStressFetcher()
    q = StressQuery(**request.model_dump())
    r = fetcher.query(q)
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_stress_query",
        "records": r.records,
        "count": r.count,
        "citation": r.citation,
        "note": r.note,
    }


# ── D7: Plate Reconstruction ──
class PlateReconstructRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    age_ma: float = Field(..., ge=0, le=4100)
    model: str = "Muller2019"


async def geox_plate_reconstruct(request: PlateReconstructRequest) -> dict[str, Any]:
    """Reconstruct a point through deep time via GPlates. INTERPRETED — plate model dependent."""
    from geox_core.io.gplates_fetcher import GPlatesFetcher, ReconstructionRequest

    fetcher = GPlatesFetcher()
    r = fetcher.reconstruct(ReconstructionRequest(**request.model_dump()))
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_plate_reconstruct",
        "reconstructed_lat": r.reconstructed_lat,
        "reconstructed_lon": r.reconstructed_lon,
        "age_ma": r.age_ma,
        "plate_id": r.plate_id,
        "model": r.model,
        "citation": r.citation,
        "note": r.note,
    }


# ── D6: Geochemistry ──
class GeochemRequest(BaseModel):
    minlatitude: float | None = None
    maxlatitude: float | None = None
    minlongitude: float | None = None
    maxlongitude: float | None = None
    rock_type: str | None = None
    min_sio2: float | None = None
    max_sio2: float | None = None
    limit: int = 100


async def geox_geochem_query(request: GeochemRequest) -> dict[str, Any]:
    """Query EarthChem/PetDB for igneous geochemistry. OBSERVED — global rock analyses."""
    from geox_core.io.earthchem_fetcher import EarthChemFetcher, GeochemQuery

    fetcher = EarthChemFetcher()
    q = GeochemQuery(**request.model_dump())
    r = fetcher.query(q)
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_geochem_query",
        "samples": r.samples,
        "count": r.count,
        "citation": r.citation,
        "note": r.note,
    }


# ── D15: UK Petroleum ──
class UKPetroleumRequest(BaseModel):
    minlatitude: float | None = None
    maxlatitude: float | None = None
    minlongitude: float | None = None
    maxlongitude: float | None = None
    status: str | None = None
    limit: int = 100


async def geox_uk_petroleum_query(request: UKPetroleumRequest) -> dict[str, Any]:
    """Query NSTA UK petroleum data (wells, fields, licences). OBSERVED — UKCS regulatory data."""
    from geox_core.io.nsta_uk_fetcher import NSTAQuery, NSTAUKFetcher

    fetcher = NSTAUKFetcher()
    q = NSTAQuery(**request.model_dump())
    r = fetcher.query(q)
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_uk_petroleum_query",
        "wells": r.wells,
        "count": r.count,
        "citation": r.citation,
        "note": r.note,
    }


# ── D10: Ocean Physics ──
class OceanRequest(BaseModel):
    minlatitude: float = -90
    maxlatitude: float = 90
    minlongitude: float = -180
    maxlongitude: float = 180
    variable: str = "temperature"
    depth_m: float | None = None
    date: str | None = None


async def geox_ocean_query(request: OceanRequest) -> dict[str, Any]:
    """Query Copernicus Marine (CMEMS) for ocean physics/BGC. OBSERVED — satellite + model."""
    from geox_core.io.copernicus_marine_fetcher import CopernicusMarineFetcher, OceanQuery

    fetcher = CopernicusMarineFetcher()
    r = fetcher.query(OceanQuery(**request.model_dump()))
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_ocean_query",
        "data": r.data,
        "count": r.count,
        "variable": r.variable,
        "citation": r.citation,
        "note": r.note,
    }


# ── D10: ERDDAP ──
class ERDDAPRequest(BaseModel):
    dataset_id: str = Field(..., description="ERDDAP dataset ID")
    minlatitude: float | None = None
    maxlatitude: float | None = None
    minlongitude: float | None = None
    maxlongitude: float | None = None
    min_time: str | None = None
    max_time: str | None = None
    limit: int = 100


async def geox_erddap_query(request: ERDDAPRequest) -> dict[str, Any]:
    """Query NOAA ERDDAP for ocean/atmosphere data. OBSERVED — 10k+ datasets from 80+ servers."""
    from geox_core.io.erddap_fetcher import ERDDAPFetcher, ERDDAPQuery

    fetcher = ERDDAPFetcher()
    r = fetcher.query(ERDDAPQuery(**request.model_dump()))
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_erddap_query",
        "data": r.data,
        "count": r.count,
        "dataset_id": r.dataset_id,
        "citation": r.citation,
        "note": r.note,
    }


# ── D16: Geology Maps ──
class GeologyMapRequest(BaseModel):
    minlatitude: float
    maxlatitude: float
    minlongitude: float
    maxlongitude: float
    layers: str | None = None


async def geox_geology_map_query(request: GeologyMapRequest) -> dict[str, Any]:
    """Query OneGeology WMS for national geological maps. OBSERVED — aggregated survey data."""
    from geox_core.io.onegeology_fetcher import GeologyMapQuery, OneGeologyFetcher

    fetcher = OneGeologyFetcher()
    r = fetcher.query(GeologyMapQuery(**request.model_dump()))
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_geology_map_query",
        "features": r.features,
        "count": r.count,
        "wms_url": r.wms_url,
        "citation": r.citation,
        "note": r.note,
    }


# ── D8: Paleomagnetism ──
class PaleomagRequest(BaseModel):
    minlatitude: float | None = None
    maxlatitude: float | None = None
    minlongitude: float | None = None
    maxlongitude: float | None = None
    min_age_ma: float | None = None
    max_age_ma: float | None = None
    limit: int = 100


async def geox_paleomag_query(request: PaleomagRequest) -> dict[str, Any]:
    """Query MagIC for paleomagnetic data. OBSERVED — rock magnetic measurements."""
    from geox_core.io.magic_paleomag_fetcher import MagICFetcher, PaleomagQuery

    fetcher = MagICFetcher()
    r = fetcher.query(PaleomagQuery(**request.model_dump()))
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_paleomag_query",
        "records": r.records,
        "count": r.count,
        "citation": r.citation,
        "note": r.note,
    }


# ── D9: Gravity Change ──
class GraceRequest(BaseModel):
    minlatitude: float = -90
    maxlatitude: float = 90
    minlongitude: float = -180
    maxlongitude: float = 180
    start_date: str | None = None
    end_date: str | None = None


async def geox_gravity_change_query(request: GraceRequest) -> dict[str, Any]:
    """Query GRACE-FO for time-variable gravity (mass change). OBSERVED — satellite gravimetry."""
    from geox_core.io.grace_fetcher import GRACEFetcher, GraceQuery

    fetcher = GRACEFetcher()
    r = fetcher.query(GraceQuery(**request.model_dump()))
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_gravity_change_query",
        "data": r.data,
        "count": r.count,
        "citation": r.citation,
        "note": r.note,
    }


# ── D11: Climate Reanalysis ──
class ClimateReanalysisRequest(BaseModel):
    minlatitude: float = -90
    maxlatitude: float = 90
    minlongitude: float = -180
    maxlongitude: float = 180
    date: str = "2024-01-01"
    variables: list[str] = ["2m_temperature"]
    time: str = "12:00"


async def geox_climate_reanalysis(request: ClimateReanalysisRequest) -> dict[str, Any]:
    """Query ERA5 global reanalysis. OBSERVED — ECMWF hourly data from 1940."""
    from geox_core.io.era5_fetcher import ERA5Fetcher, ERA5Query

    fetcher = ERA5Fetcher()
    r = fetcher.query(ERA5Query(**request.model_dump()))
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_climate_reanalysis",
        "data": r.data,
        "count": r.count,
        "citation": r.citation,
        "note": r.note,
    }


# ── D12: Hydrology ──
class HydrologyRequest(BaseModel):
    minlatitude: float | None = None
    maxlatitude: float | None = None
    minlongitude: float | None = None
    maxlongitude: float | None = None
    state_code: str | None = None
    site_type: str | None = None
    parameter_code: str = "00060"
    period: str = "P7D"
    limit: int = 100


async def geox_hydrology_query(request: HydrologyRequest) -> dict[str, Any]:
    """Query USGS Water Services for streamflow/groundwater. OBSERVED — US real-time."""
    from geox_core.io.usgs_water_fetcher import USGSWaterFetcher, WaterQuery

    fetcher = USGSWaterFetcher()
    r = fetcher.query(WaterQuery(**request.model_dump()))
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_hydrology_query",
        "sites": r.sites,
        "count": r.count,
        "citation": r.citation,
        "note": r.note,
    }


# ── D14: Satellite Imagery ──
class SatelliteCatalogRequest(BaseModel):
    minlatitude: float
    maxlatitude: float
    minlongitude: float
    maxlongitude: float
    datetime_range: str = "2024-01-01/2024-12-31"
    collection: str = "landsat-c2-l2"
    cloud_cover_max: float = 20.0
    limit: int = 10


async def geox_satellite_catalog(request: SatelliteCatalogRequest) -> dict[str, Any]:
    """Search STAC for Landsat/MODIS/Sentinel imagery. OBSERVED — satellite surface reflectance."""
    from geox_core.io.landsat_stac_fetcher import LandsatSTACFetcher, SatelliteQuery

    fetcher = LandsatSTACFetcher()
    r = fetcher.query(SatelliteQuery(**request.model_dump()))
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_satellite_catalog",
        "items": r.items,
        "count": r.count,
        "collection": r.collection,
        "citation": r.citation,
        "note": r.note,
    }


# ── D17: Space Weather ──
class SpaceWeatherRequest(BaseModel):
    product: str = "kp_index"
    limit: int = 100


async def geox_space_weather(request: SpaceWeatherRequest) -> dict[str, Any]:
    """Query NOAA SWPC for space weather (Kp, Dst, solar wind). OBSERVED — real-time."""
    from geox_core.io.noaa_swpc_fetcher import NOAASWPCFetcher, SpaceWeatherQuery

    fetcher = NOAASWPCFetcher()
    r = fetcher.query(SpaceWeatherQuery(**request.model_dump()))
    return {
        "ok": r.ok,
        "mode": r.mode,
        "tool": "geox_space_weather",
        "data": r.data,
        "count": r.count,
        "product": r.product,
        "citation": r.citation,
        "note": r.note,
    }


__all__ = [
    "geox_heatflow_query",
    "geox_stress_query",
    "geox_plate_reconstruct",
    "geox_geochem_query",
    "geox_uk_petroleum_query",
    "geox_ocean_query",
    "geox_erddap_query",
    "geox_geology_map_query",
    "geox_paleomag_query",
    "geox_gravity_change_query",
    "geox_climate_reanalysis",
    "geox_hydrology_query",
    "geox_satellite_catalog",
    "geox_space_weather",
]
