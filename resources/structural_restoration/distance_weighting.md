# Distance-Weighted Uncertainty

## Core Principle

Calibration confidence decays spatially. Uncertainty should be zero or minimal only where the restoration is actually calibrated. Away from control, uncertainty increases until reaching a scenario-defined cap. (SR_INV_011, EUREKA-08)

## Generic Form

```
u(d) = min(u_max, u_at_control + growth(d))
```

The linear concept from the Dr Shahram exercise:

```
u(d) = u_max × min(d / d_cutoff, 1)
```

## Critical Rule

**u_max and d_cutoff are scenario parameters, never basin constants.** (SR_INV_011)

The values10 km (calibration influence distance) and300 m (maximum palaeowater-depth uncertainty) from the Dr Shahram exercise are **modelling assumptions** for that specific exercise, not NW Sabah universal truths.

## Mandatory Disclosures

Every uncertainty map must disclose:
- Control points (well locations)
- Distance metric (Euclidean, along-structure, etc.)
- Growth function (linear, exponential, etc.)
- Cut-off distance (km)
- Maximum uncertainty (m)
- Whether these values are observed or assumed

## Implementation Note

The uncertainty propagation engine must support pluggable growth functions. The linear function is the default. Basin-specific or scenario-specific functions may override.
