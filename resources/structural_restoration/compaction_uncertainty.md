# Compaction Uncertainty Propagation

## Core Principle

Small porosity differences integrated over a thick sediment column can create material restoration differences. Uncertainty must be accumulated by depth interval, not applied as an arbitrary uniform vertical shift. (SR_INV_009, EUREKA-07)

## Compaction Scenario Structure

```yaml
compaction_scenario:
  reference_curve: "named curve or dataset"
  measured_depth_limit_m: null      # Maximum depth with measured support
  extrapolation_end_depth_m: null   # Depth to which curve is extrapolated
  porosity_adjustment:
    type: "absolute_porosity_points" # NOT relative %
    value: null
  depth_interval_m: null            # Interval for uncertainty accumulation
  evidence_class: "MEASURED | PUBLISHED | EXTRAPOLATED | ASSUMED"
```

## Critical Distinction: "5%" is Ambiguous

GEOX must force the caller to distinguish:
- **5 absolute porosity percentage points** (e.g., 20% → 25%)
- **5 per cent relative change** (e.g., 20% → 21%)

These produce very different restoration results.

## Rules

1. No compaction curve may be extrapolated beyond measured support without: explicit scenario name, extrapolation interval, and uncertainty envelope
2. Measured, published, extrapolated, and assumed parameters must remain distinguishable (SR_INV_010)
3. Compaction extrapolation must produce low, reference, and high scenarios (SR_INV_009)
4. Uniform lithology across laterally variable facies must be declared UNIFORM_LITHOLOGY_ASSUMPTION (SR_INV_012)

## Available Compaction Models in GEOX

- Athy (1930) — exponential porosity-depth: φ(z) = φ₀ · exp(-c·z)
- Sclater & Christie (1980) — shale/sand calibration
- Dickinson (1953) — Gulf Coast reference

The existing engine at `src/geox_core/engines/stratigraphy/accommodation.py` implements Athy with Sclater & Christie calibration. This is the reference implementation. Other curves are scenario overrides.
