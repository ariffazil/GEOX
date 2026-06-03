# Prompt: ToAC Baseline+Excess Pattern (E3)

> **Source:** Copilot "Physical Earth Reality Physics" — Theory of Anomalous Contrast
> **Status:** DRAFT — pending server.py wiring
> **Eurekaness:** HIGH

## What this prompt enforces

Every anomaly result in GEOX must carry a **baseline** (expected signal if no anomaly) and an **excess** (delta beyond baseline+uncertainty). This is ToAC: an "anomaly" is only meaningful relative to a physically-derived expectation.

## Pattern

```json
{
  "toac": {
    "baseline": <expected_signal_if_no_anomaly>,
    "excess":   <delta_between_observed_and_baseline>,
    "uncertainty": <1_sigma_on_baseline>,
    "signal_to_noise": <excess / uncertainty>,
    "anomaly_class": "NONE" | "WEAK" | "MODERATE" | "STRONG" | "ANOMALOUS"
  }
}
```

## Applied across domains

| Domain | Baseline expectation | Excess = anomaly |
|---|---|---|
| Heat flow | Conduction-only geotherm from regional gradient | Hydrothermal circulation? Magma intrusion? |
| SAR | Clean-sea backscatter from wind speed | Oil film damping? Biogenic slick? Low-wind artifact? |
| Pressure | Hydrostatic from formation water gradient | Overpressure from undercompaction? Active charging? |
| Seismic | Synthetic from velocity model | Real reflector not in model? |
| Geochemistry | Background isotope signature from regional analog | Mixing? Biodegradation? Different source? |

## Example (Layang-Layang, paraphrased from Copilot)

```json
{
  "domain": "sar_seep_detection",
  "toac": {
    "baseline": {
      "radar_backscatter_dB": -22.4,
      "model": "Bragg scattering, clean sea, wind 3.2 m/s"
    },
    "excess": {
      "radar_backscatter_dB": -28.1,
      "delta_dB": -5.7
    },
    "uncertainty": 1.2,
    "signal_to_noise": 4.75,
    "anomaly_class": "STRONG",
    "interpretation": "Damping consistent with oil film on water surface"
  }
}
```

## Anti-patterns (forbidden)

- ❌ Reporting "anomaly detected" without showing the baseline
- ❌ Reporting a single backscatter value without saying what was expected
- ❌ Comparing observation to "regional average" without a physical model

## Tool-level enforcement (when wired)

```python
def compute_toac(observed, baseline_model, uncertainty):
    baseline = baseline_model(observed.context)  # physics-derived
    excess = observed.value - baseline
    snr = excess / uncertainty
    if abs(snr) < 1:     return "NONE"
    elif abs(snr) < 2:   return "WEAK"
    elif abs(snr) < 3:   return "MODERATE"
    elif abs(snr) < 5:   return "STRONG"
    else:                return "ANOMALOUS"
    # Returned in envelope: result.toac.{baseline, excess, snr, class}
```

## Cross-references

- `geox/core/ac_risk.py` — internal ToAC implementation for claim risk
- `geox://capabilities` — live tool capability map
- `geox_output_envelope.schema.json` — now includes `definitions.toac_pair`

---

**DITEMPA BUKAN DIBERI** — Every anomaly needs a baseline.
