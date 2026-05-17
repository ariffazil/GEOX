# Time & Change

Everything changes. GEOX captures temporal dynamics through change detection, time series analysis, and forecasting.

## Overview

The Time domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `change_detect` | Identify changes between epochs | machine, orbital |
| `time_series` | Analyze temporal patterns | machine |
| `forecast_model` | Predict future states | machine |
| `anomaly_detect` | Identify outliers | machine, void |

## Change Detection

Change detection answers "what changed, where, when?"

### Change Types

- **Land cover**: Forest → agriculture → urban
- **Urban expansion**: Greenfield → built environment
- **Coastal erosion**: Shoreline retreat
- **Infrastructure**: New roads, buildings

### Methods

- **Post-classification**: Compare classified maps
- **Bi-temporal**: Direct image comparison
- **Continuum**: Continuous monitoring
- **AI-based**: Deep learning change detection

## Time Series Analysis

Temporal data reveals patterns:
- **Trend**: Long-term direction
- **Seasonality**: Cyclical patterns
- **Breakpoints**: Regime shifts
- **Noise**: Random variation

### Statistical Methods

- **ARIMA**: Autoregressive integrated moving average
- **STL**: Seasonal decomposition of loess
- **Mann-Kendall**: Trend significance
- **CUSUM**: Change point detection

## Forecast Modeling

Forecasting projects future states:
- **Short-term**: Days to weeks (weather, traffic)
- **Medium-term**: Months to years (climate, growth)
- **Long-term**: Decades (sea level, urbanization)

### Ensemble Methods

- **NWP**: Numerical weather prediction
- **Climate models**: CMIP6 scenarios
- **ML ensembles**: Machine learning combinations
- **Storylines**: What-if scenario exploration

## Anomaly Detection

Anomalies are deviations from expected:
- **Spatial**: Unexpected values at location
- **Temporal**: Unexpected changes over time
- **Contextual**: Unexpected given conditions

### Detection Approaches

- **Threshold**: Exceedance of critical values
- **Statistical**: Beyond confidence intervals
- **ML-based**: Learned normal patterns
- **Physics-based**: Violation of conservation laws

## Constitutional Constraints

Time operations must satisfy:
- **F7 Confidence**: Forecast uncertainty explicitly stated
- **F2 Truth**: No fabrication of future scenarios
- **F11 Coherence**: Forecasts consistent with physics

## See Also

- [Atmosphere & Weather](atmosphere.md) — Weather forecasting
- [Sensing & Signals](sensing.md) — Temporal resolution
- [Forecast Model](../../apps/site/skills/forecast_model.html) — Skill detail
