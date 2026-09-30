# Restoration QC Checklist

## Pre-Computation (validate_restoration_inputs)

- [ ] Source surface ID and name present
- [ ] Target surface ID and name present
- [ ] CRS EPSG or name declared
- [ ] CRS match between source and target
- [ ] XY units match
- [ ] Z units match
- [ ] Z convention match (positive_up vs positive_down)
- [ ] Vertical datum match
- [ ] Source age declared
- [ ] Target age declared
- [ ] Ages are not equal
- [ ] Stratigraphic ordering explicit
- [ ] Source geometry marked immutable
- [ ] Scenario marked immutable

## Computation

- [ ] Subtraction order recorded
- [ ] Sign convention declared
- [ ] Units of result declared
- [ ] No source geometry overwritten
- [ ] New immutable scenario object created
- [ ] Full provenance chain recorded

## Post-Computation

- [ ] Uncertainty envelope attached
- [ ] Distance-decay parameters are scenario inputs, not basin constants
- [ ] Compaction extrapolation interval declared (if applicable)
- [ ] Evidence class (MEASURED/PUBLISHED/EXTRAPOLATED/ASSUMED) for all parameters
- [ ] Fill-ratio diagnostic guard applied (if applicable)
- [ ] Fault generation not assigned from azimuth alone
- [ ] At least two competing hypotheses registered for material decisions
- [ ] Output carries version ID, timestamp, and hash

## Interpretation Gate

- [ ] Restoration products framed as observations, not explanations
- [ ] Tectonic interpretation separated from geometric product
- [ ] Competing hypotheses enumerated with relative probabilities
- [ ] Stress orientation used as QC constraint, not forced answer
- [ ] No interpretation exceeds input data resolution
