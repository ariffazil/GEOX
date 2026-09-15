# GEOX Calibration Workflow

## Purpose
Guide the geologist through creating a CalibrationWitness — the measurement acquisition instrument that unlocks structural interpretation gates.

## Binding Safety Rules
1. Clicks are **interpreted anchors**, not ground truth
2. Display-derived proxy data CANNOT support quantitative amplitude analysis, AVO, or native well-tie
3. Velocity/T-D quality and coverage can still block structural conversion
4. MCP Apps improves portability but does not create geological validity

## Workflow Steps

### 1. Bind Evidence
- Select registered SEG-Y / image / section / well tie
- Confirm data representation: NATIVE_TRACE or DISPLAY_DERIVED_PROXY
- Confirm data classification: synthetic / public / restricted
- Confirm authority state

### 2. Declare Domain
- Vertical: TWT (ms) / Depth (m) / Mixed
- Horizontal: distance (m) / inline / CDP / crossline
- CRS if applicable

### 3. Calibrate Horizontal Axis
- Click two known horizontal positions (CDP, inline, distance)
- System computes pixel→distance or pixel→grid transform
- Review residual/error

### 4. Calibrate Vertical Axis
- Click two known time/depth ticks
- System computes pixel→TWT/depth transform
- Review residual/error

### 5. Attach Velocity/T-D
- Select registered velocity model, checkshot, VSP, or T-D curve
- Validate units, datum, coverage, version

### 6. Mark Interpretation Anchors
- Click: fault traces, horizons, dip segments, throw pairs, well locations
- Each pick gets: pick_id, kind, coordinates, epistemic_tag (INTERPRETED), observer, uncertainty

### 7. Inspect Uncertainty
- Review click error, interpolation error, velocity uncertainty
- System propagates uncertainty to derived quantities

### 8. Seal Witness
- Confirm calibrated frame is fit for stated use
- System produces CalibrationReceipt
- Gates consume witness: UNMEASURED → CALIBRATED_INPUT_AVAILABLE → COMPUTABLE

## Gate Readiness Matrix

| Gate | Minimum Calibration | What Remains Required |
|------|-------------------|----------------------|
| K-DIP | Axes + scale + domain + fault pick | True-vs-apparent dip assumption, VE, line orientation |
| K-DL | Horizontal + vertical scale + fault pick | D/L definition, error propagation |
| K-THROW | Scale + T-D/velocity + throw pair | Correlated markers, fault cutoffs |
| K-RESTORE | Calibrated dimensions + fault geometry | Kinematics, restoration method |
| K-VEL | Valid velocity/T-D object | Coverage/quality validation |

## 888 HOLD Conditions
The following conditions PREVENT proceeding from calibration to prospect claims:
1. Source authority absent
2. No cryptographically bound data version
3. Vertical domain ambiguous (TWT shown as depth)
4. Missing velocity/T-D for depth results
5. Calibration error exceeds tolerances
6. Picks don't identify semantic meaning
7. Output doesn't declare OBS/DER/INT/SPEC
8. Only conceptual placeholders presented as multi-hypothesis evidence

## Epistemic Labels
Every output declares:
- **OBS**: Directly observed (click positions, pixel values)
- **DER**: Deterministically calculated (scale, coordinates, transforms)
- **INT**: Interpretation (fault/horizon picks, structural style)
- **SPEC**: Testable hypothesis (seal capacity, compartmentalization)

DITEMPA BUKAN DIBERI — Forged, Not Given
