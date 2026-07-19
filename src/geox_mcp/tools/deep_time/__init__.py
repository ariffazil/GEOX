"""deep_time/__init__.py — Deep Time State subpackage.

Gathers the Age Resolver, ICS Chart, schemas, formulas, data loaders,
epistemic tagging, and Earth State Vector assembly for the
geox_deep_time_state GEOX MCP tool.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from .age_resolver import AgeResolution, resolve_age_query
from .data_loaders import (
    load_atmospheric_o2,
    load_benthic_d18O,
    load_biotic_realm,
    load_co2_estimate,
    load_ice_extent,
    load_magnetic_polarity,
    load_sea_level_estimate,
    load_supercontinent_state,
    load_temperature_estimate,
)
from .epistemic import cap_confidence, tag_epistemic_level
from .formulas import (
    day_length_hours,
    orbital_eccentricity_approx,
    solar_luminosity_fraction,
)
from .ics_chart import ICSChart, ics_chart_v2024_12
from .schemas import (
    EarthStateEnvelope,
    EarthStateVariable,
    EarthStateVector,
    GovernanceFooter,
    PolarityState,
)
from .vector import assemble_earth_state_vector, assemble_envelope

__all__ = [
    "resolve_age_query",
    "AgeResolution",
    "ICSChart",
    "ics_chart_v2024_12",
    "EarthStateVariable",
    "EarthStateVector",
    "EarthStateEnvelope",
    "GovernanceFooter",
    "PolarityState",
    "solar_luminosity_fraction",
    "day_length_hours",
    "orbital_eccentricity_approx",
    "tag_epistemic_level",
    "cap_confidence",
    "load_co2_estimate",
    "load_benthic_d18O",
    "load_temperature_estimate",
    "load_sea_level_estimate",
    "load_magnetic_polarity",
    "load_atmospheric_o2",
    "load_supercontinent_state",
    "load_biotic_realm",
    "load_ice_extent",
    "assemble_earth_state_vector",
    "assemble_envelope",
]
