# Atmosphere & Weather

The atmosphere mediates all surface observation and constrains operations. Weather affects visibility, sensor performance, and safety.

## Overview

The Atmosphere domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `weather_ingest` | Ingest meteorological data | machine, orbital |
| `atmospheric_correction` | Correct imagery for atmosphere | machine, orbital |
| `climate_trend` | Analyze long-term patterns | machine, human |
| `storm_track` | Forecast storm paths | machine, human |

## Weather Ingest

Meteorological data sources:
- **Synoptic**: Surface stations, radiosondes
- **Remote**: Radar, satellite, GPS occultation
- **Model**: NWP output (GFS, ECMWF, HRRR)

### Data Variables

- Temperature, humidity, pressure
- Wind speed and direction
- Precipitation type and rate
- Cloud cover and height
- Visibility

## Atmospheric Correction

Sensors measure top-of-atmosphere radiance, but surface reflectance is needed for analysis.

### Correction Methods

- **DOS**: Dark object subtraction (simple)
- **6S**: Second simulation of satellite signal (radiative transfer)
- **Flaash**: Industry standard
- **Machine Learning**: Learned atmospheric physics

### Atmospheric Effects

- **Scattering**: Rayleigh (blue), Mie (aerosol)
- **Absorption**: Water vapor, ozone, CO2
- **Emission**: Thermal infrared

## Climate Trend Analysis

Long-term analysis reveals:
- Temperature trends (warming rates)
- Precipitation shifts
- Extreme event frequency changes
- Seasonal migration

### Statistical Methods

- **Linear regression**: Trend magnitude
- **Mann-Kendall**: Significance testing
- **Clustering**: Regimes and transitions
- **PCA**: Dominant modes of variability

## Storm Tracking

Storm tracking combines:
- **Satellite imagery**: Cloud pattern recognition
- **Radar**: Precipitation structure
- **Reanalysis**: Environmental conditions
- **Ensemble forecasting**: Uncertainty

### Products

- **Track forecast**: Center position forecast
- **Intensity forecast**: Maximum sustained winds
- **Wind field**: Spatial distribution
- **Threat radius**: Impact zones

## Operational Constraints

Atmosphere constrains:
- **Flight**: Ceiling, visibility, wind limits
- **Imagery**: Cloud cover blocks optical sensors
- **Communications**: Ionospheric disruption
- **Sensor performance**: Atmospheric degradation

## Constitutional Constraints

Atmosphere operations must satisfy:
- **F2 Truth**: No falsification of climate data
- **F7 Confidence**: Forecast uncertainty explicitly stated
- **F11 Coherence**: Consistent with physical laws

## See Also

- [Sensing & Signals](sensing.md) — Sensor calibration
- [Hazards & Risk](hazards.md) — Storm tracking
- [Weather Ingest](../../apps/site/skills/weather_ingest.html) — Skill detail
