# GEOX Physics Adapter Specification
**Version:** 2026.04.14-ADAPTER  
**Seal:** 999_SEAL  
**Scope:** 3 highest-value adapters only (lean start)

---

## Axiom

Adapters are **thin linguistic membranes** between existing physics engines and the GEOX ToAC governance layer. No physics is re-implemented. Only: input marshaling, output normalization, uncertainty extraction, and transform logging.

---

## 1. Adapter 1 — OpenQuake (HAZARD)

### 1.1 Engine
- **Name:** OpenQuake Engine
- **Purpose:** Probabilistic Seismic Hazard Analysis (PSHA), scenario GMFs, damage/loss
- **Reference:** [github.com/gem/oq-engine](https://github.com/gem/oq-engine)

### 1.2 Adapter Interface

```python
class OpenQuakeAdapter:
    async def compute_pga_map(
        self,
        job_ini_path: str,           # OpenQuake job config
        source_model_xml: str,       # Fault/area source model
        gmpe_logic_tree: str,        # GMPE logic tree XML
        site_model_csv: str,         # Site conditions (Vs30, z1.0, z2.5)
        region: str,                 # Basin/region name for calibration lookup
    ) -> PhysicsAdapterResult:
        ...
```

### 1.3 Output Schema (`PhysicsAdapterResult`)

```json
{
  "raw_output": {
    "hazard_curves": "s3://geox/oq/malay_basin/hc.csv",
    "uniform_hazard_spectra": "s3://geox/oq/malay_basin/uhs.csv",
    "gmf_realizations": "s3://geox/oq/malay_basin/gmf.nc"
  },
  "uncertainty_bands": {
    "type": "logic_tree_envelope",
    "realization_count": 200,
    "p10_pga": 0.08,
    "p50_pga": 0.21,
    "p90_pga": 0.47,
    "gmpe_branch_weights": [0.35, 0.35, 0.30]
  },
  "validation_residual": {
    "metric": "rmse_vs_shakemap",
    "value": 0.12,
    "reference_data": "USGS_ShakeMap_2026q1"
  },
  "transform_stack": [
    "gmpe_selection",
    "mesh_coarsening",
    "site_amplification"
  ],
  "computational_cost_ms": 124500
}
```

### 1.4 ToAC Handoff

```python
u_phys = estimate_u_phys(
    data_density=samples / grid_cells,
    calibration_residual=result.validation_residual.value,
    boundary_condition_uncertainty="medium",
)
d_transform = product_of(result.transform_stack)
b_cog = detect_bias_scenario(user_context)

ac_risk, verdict = toac.evaluate(
    u_phys=u_phys,
    d_transform=d_transform,
    b_cog=b_cog,
    domain="HAZARD",
)
```

---

## 2. Adapter 2 — MODFLOW (HYDRO)

### 2.1 Engine
- **Name:** MODFLOW 6 (groundwater flow) + SEAWAT (variable-density flow)
- **Purpose:** Aquifer simulation, drawdown forecasting, saltwater intrusion
- **Reference:** [github.com/MODFLOW-USGS/modflow6](https://github.com/MODFLOW-USGS/modflow6)

### 2.2 Adapter Interface

```python
class ModflowAdapter:
    async def simulate_flow(
        self,
        model_name: str,
        nam_file_path: str,          # MODFLOW name file
        well_package: dict,          # pumping rates, screen depths
        recharge_raster: str,        # recharge grid (optional)
        simulation_years: int,
        region: str,
    ) -> PhysicsAdapterResult:
        ...
```

### 2.3 Output Schema

```json
{
  "raw_output": {
    "head_grid": "s3://geox/mf/malay_basin/head.nc",
    "budget_file": "s3://geox/mf/malay_basin/budget.csv",
    "concentration_grid": "s3://geox/mf/malay_basin/conc.nc"
  },
  "uncertainty_bands": {
    "type": "monte_carlo_parameter_perturbation",
    "realization_count": 50,
    "parameter_perturbed": "hydraulic_conductivity",
    "perturbation_distribution": "lognormal",
    "head_p10": -45.2,
    "head_p50": -38.7,
    "head_p90": -32.1
  },
  "validation_residual": {
    "metric": "rmse_vs_observed_heads",
    "value": 2.4,
    "reference_data": "JPS_monitoring_wells_2025"
  },
  "transform_stack": [
    "mesh_coarsening",
    "parameter_zonation",
    "recharge_interpolation"
  ],
  "computational_cost_ms": 89000
}
```

### 2.4 ToAC Handoff

Same pattern as OpenQuake, with `domain="HYDRO"` and mandatory **F6** (water sovereignty) review if public aquifer depletion is implied.

---

## 3. Adapter 3 — TOUGH2 (CCS)

### 3.1 Engine
- **Name:** TOUGH2 / TOUGH3 (multiphase flow) or E300 CO₂ module
- **Purpose:** CO₂ injection, plume migration, storage capacity verification
- **Reference:** [tough.lbl.gov](https://tough.lbl.gov/)

### 3.2 Adapter Interface

```python
class Tough2Adapter:
    async def simulate_plume(
        self,
        model_name: str,
        mesh_file: str,              # TOUGH MESH / ELEME format
        injection_schedule: list,    # rate (kg/s) vs time
        formation_properties: dict,  # porosity, permeability, capillary pressure
        seal_thickness_map: str,     # caprock thickness raster
        simulation_years: int,
        region: str,
    ) -> PhysicsAdapterResult:
        ...
```

### 3.3 Output Schema

```json
{
  "raw_output": {
    "saturation_grid": "s3://geox/t2/sarawak_co2/sat.nc",
    "pressure_grid": "s3://geox/t2/sarawak_co2/pres.nc",
    "mass_balance": "s3://geox/t2/sarawak_co2/mb.csv",
    "plume_boundary_shp": "s3://geox/t2/sarawak_co2/plume.shp"
  },
  "uncertainty_bands": {
    "type": "ensemble_perturbation",
    "realization_count": 30,
    "parameters_perturbed": ["permeability", "capillary_pressure"],
    "plume_extent_p10_km2": 12.4,
    "plume_extent_p50_km2": 18.7,
    "plume_extent_p90_km2": 26.3,
    "overpressure_p90_mpa": 2.1
  },
  "validation_residual": {
    "metric": "not_yet_available",
    "value": null,
    "reference_data": "sleipner_benchmark_2027"
  },
  "transform_stack": [
    "mesh_simplification",
    "equation_of_state_selection",
    "relative_permeability_table_interpolation"
  ],
  "computational_cost_ms": 340000
}
```

### 3.4 ToAC Handoff

- `domain="CCS"`
- **F8** (regulatory) and **F2** (truth) are always active.
- If `validation_residual.value is None`, `U_phys` floor is **+0.15** (unvalidated engine).
- All CCS certification documents route through **888_HOLD** regardless of AC_Risk.

---

## 4. Common `PhysicsAdapterResult` Contract

All adapters must return an object conforming to:

```python
@dataclass
class PhysicsAdapterResult:
    raw_output: dict[str, str]          # URIs to engine outputs
    uncertainty_bands: dict             # P10/P50/P90 or full ensemble metadata
    validation_residual: dict           # {metric, value, reference_data}
    transform_stack: list[str]          # Named transforms for D_transform calc
    computational_cost_ms: int          # Resource accounting
```

---

## 5. Adapter → ToAC → Product Pipeline

```
Adapter Inputs → Physics Engine → AdapterResult
                                    ↓
                              U_phys estimation
                                    ↓
                              D_transform calculation
                                    ↓
                              B_cog detection
                                    ↓
                              AC_Risk evaluation
                                    ↓
                              Verdict (SEAL/QUALIFY/HOLD/VOID)
                                    ↓
                              Product Versioning Envelope
                                    ↓
                              Vault Anchor (arifOS 999)
                                    ↓
                              888_HOLD gate (if required)
                                    ↓
                              Externalization or BLOCK
```

---

**Sealed:** 2026-04-14T05:40:00Z  
**DITEMPA BUKAN DIBERI**
