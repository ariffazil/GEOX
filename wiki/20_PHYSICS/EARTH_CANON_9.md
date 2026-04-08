# EARTH.CANON_9 — Fundamental Geophysical Variables

> **Type:** Physics  
> **Epistemic Level:** OBS (observational foundation)  
> **Confidence:** 1.0  
> **Tags:** [physics, canon, geophysics, foundation, variables]  
> **Sources:** [[raw/papers/earth_physics_canon.pdf]]  
> **arifos_floor:** F2  

---

## The Canon

The 9 canonical physical quantities that **completely describe** any subsurface Earth material:

| # | Variable | Symbol | Unit | Physical Meaning | Primary Log/Source |
|---|----------|--------|------|------------------|-------------------|
| **1** | **Density** | ρ | kg/m³ | Bulk mass density | RHOB (density log) |
| **2** | **P-wave Velocity** | Vp | m/s | Compressional elastic wave speed | DTCO (sonic) |
| **3** | **S-wave Velocity** | Vs | m/s | Shear elastic wave speed | DTSM (sonic) |
| **4** | **Electrical Resistivity** | ρₑ | Ω·m | Opposition to current flow | RT (resistivity) |
| **5** | **Magnetic Susceptibility** | χ | SI (dimensionless) | Response to magnetic fields | MAG (survey) |
| **6** | **Thermal Conductivity** | k | W/(m·K) | Heat transfer capacity | TC (temp log) |
| **7** | **Pressure** | P | Pa | Pore/fluid pressure | MDT/RFT (tester) |
| **8** | **Temperature** | T | K | Thermal energy state | BHT/DTS (temp) |
| **9** | **Porosity** | φ | fraction (0–1) | Normalized void volume | PHI (neutron/density/NMR) |

---

## Physics Completeness

With these 9, you can derive **all exploration-grade geophysics**:

### From Mechanical (ρ, Vp, Vs)
```
Acoustic Impedance:     I = ρ × Vp
Poisson's Ratio:        ν = (Vp² - 2Vs²) / 2(Vp² - Vs²)
Bulk Modulus:           K = ρ(Vp² - 4/3 Vs²)
Shear Modulus:          μ = ρ × Vs²
Seismic Reflectivity:   R = (I₂ - I₁) / (I₂ + I₁)
```

### From EM-Thermal (ρₑ, χ, k)
```
Formation Factor:       F = ρₑ(rock) / ρₑ(fluid)
Heat Flow:              q = -k × ∇T
Apparent Resistivity:   ρa = f(ρₑ, χ, geometry)
```

### From State (P, T, φ)
```
Effective Stress:       σ' = σ - P
Water Saturation:       Sw = f(ρₑ, φ, Rw) [Archie]
Thermal Gradient:       ∇T = ∂T/∂z
Formation Volume Factor: B = f(P, T, fluid)
```

---

## Canonical Schema

```python
class EarthCanon9(BaseModel):
    """
    The 9 fundamental geophysical variables.
    Minimal basis for forward-modeling crustal Earth.
    """
    # Mechanical
    density: float = Field(..., ge=1000, le=3000)  # kg/m³
    vp: float = Field(..., ge=1500, le=8000)       # m/s
    vs: float = Field(..., ge=0, le=5000)          # m/s
    
    # EM-Thermal
    resistivity: float = Field(..., ge=0.01, le=10000)  # Ω·m
    magnetic_suscept: float = Field(..., ge=-1, le=100)  # SI
    thermal_conduct: float = Field(..., ge=0.5, le=10)   # W/(m·K)
    
    # State
    pressure: float = Field(..., ge=0, le=200e6)    # Pa
    temperature: float = Field(..., ge=273, le=800) # K
    porosity: float = Field(..., ge=0, le=1)        # fraction
```

---

## Physics Note: Void Volume is the Primitive

At **F2 physics** level, the fundamental quantity is **void volume** (Vv).

**Canonical 9 uses φ (porosity)** as the field representation:
- φ = Vv / Vt (void volume / total bulk volume)
- Dimensionless, bounded [0, 1]
- Invertible into saturation, permeability, formation factor

**Alternative representations:**
- **Void ratio** (soils): e = Vv / Vs
- **Void volume** (absolute): Vv = φ × Vt

---

## Porosity Types (Next Layer)

EARTH.CANON_9 φ is **total porosity** (φt). Downstream distinction:

| Type | Definition | Symbol |
|------|------------|--------|
| **Total** | All void space | φt |
| **Effective** | Connected voids only | φe |
| **Isolated** | Non-connected voids | φi = φt - φe |
| **Primary** | Depositional | φp |
| **Secondary** | Post-depositional | φs |

**⚠️ 888_HOLD trigger:** Reporting φe as φt without disclosure (F2 violation).

---

## Related Pages

- [[20_PHYSICS/Acoustic_Impedance]] — Derivation from ρ, Vp
- [[20_PHYSICS/Elastic_Moduli]] — K, μ, ν derivations
- [[20_PHYSICS/Porosity_Types]] — φt, φe, φi deep-dive
- [[20_PHYSICS/Saturation_Models]] — Sw from Archie equations
- [[30_MATERIALS/RATLAS_Index]] — Material-specific Canon_9 values

---

## Telemetry

```
[EARTH.CANON_9 | ρ:2650.0 Vp:3500.0 Vs:1800.0 ρₑ:10.50 χ:0.0012 k:2.50 P:25.00MPa T:373.0K φ:0.150 | SEALED]
```

---

*DITEMPA BUKAN DIBERI — Physics first, interpretation second.*
