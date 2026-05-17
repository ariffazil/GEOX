# Sensing & Signals

Sensing is the foundation of Earth Intelligence. All downstream processing depends on the quality of upstream acquisition.

## Overview

The Sensing domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `signal_acquisition` | Acquire raw sensor signals | machine, infrastructure |
| `telemetry_link` | Establish data telemetry | machine, infrastructure |
| `sensor_calibration` | Calibrate against ground truth | machine, human |
| `noise_filtering` | Remove noise from signals | machine |

## Signal Acquisition

Raw signals come from multiple sources:
- **Orbital**: SAR, optical, multispectral, thermal
- **Aerial**: LiDAR, photogrammetry, aerial survey
- **Ground**: seismometers, GPS stations, IoT sensors
- **Maritime**: sonar, bathymetric echo sounders

### Quality Metrics

Signal quality is measured by:
- **SNR** (Signal-to-Noise Ratio): Higher is better
- **Resolution**: Spatial, spectral, temporal
- **Coverage**: Fill factor of observation
- **Calibration**: Traceability to reference standards

## Telemetry Link

Data must be transmitted from sensor to processor. Telemetry considerations:
- **Protocol**: MQTT, HTTP, custom binary
- **Latency**: Real-time vs delayed
- **Reliability**: Acknowledgment and retry
- **Security**: Encryption, authentication

## Calibration

All sensors drift. Calibration establishes the relationship between raw measurement and physical quantity.

### Calibration Hierarchy

1. **Primary**: Traceable to SI standards
2. **Secondary**: Cross-calibrated against primary
3. **Field**: In-situ calibration against known targets
4. **Relative**: Normalized to baseline conditions

## Noise Filtering

Noise sources:
- **Thermal**: Random electron motion
- **Atmospheric**: Scattering, absorption
- **Electronic**: Interference, quantization
- **Systematic**: Sensor artifacts, processing errors

### Filter Types

- **Temporal**: Moving average, Kalman filter
- **Spatial**: Low-pass, median filter
- **Spectral**: Band-pass, notch filter
- **Adaptive**: Wavelet, machine learning denoisers

## Constitutional Constraints

Sensing operations must satisfy:
- **F3 Input Clarity**: Observation purpose is explicit
- **F8 Grounding**: Measurements traceable to evidence
- **F9 Anti-Hantu**: No fabricated or manipulated signals

## See Also

- [Geodesy & Position](geodesy.md) — Coordinate reference
- [Atmosphere & Weather](atmosphere.md) — Environmental context
- [Noise Filtering](../../apps/site/skills/noise_filtering.html) — Skill detail
