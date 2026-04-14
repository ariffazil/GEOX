# GEOX Product Versioning & Audit Schema
**Version:** 2026.04.14-VAULT  
**Seal:** 999_SEAL  

---

## 1. Purpose

Every canonical product emitted by GEOX must be a **governed, versioned, replayable object**. This schema binds GEOX products to the arifOS vault, enabling temporal audit, calibration feedback, and constitutional enforcement.

---

## 2. Minimal Schema

All 12 canonical products must carry this envelope:

```json
{
  "product_id": "geox.hazard.pga.malay_basin.2026q2",
  "version": "1.0.0",
  "product_type": "hazard_map",
  "dimension": "HAZARD",
  "engine": {
    "name": "OpenQuake",
    "version": "3.21.0",
    "adapter_version": "0.2.1"
  },
  "inputs_hash": "sha256:abc123...",
  "inputs_manifest": {
    "data_sources": ["USGS ShakeMap", "JAXA ALOS DEM"],
    "parameter_file_url": "s3://geox/configs/malay_basin_hazard.ini",
    "sample_count": 1240,
    "grid_cell_count": 45000
  },
  "uq_summary": {
    "uncertainty_type": "ensemble",
    "realization_count": 100,
    "p10": 0.12,
    "p50": 0.28,
    "p90": 0.55,
    "std_dev": 0.11
  },
  "ac_risk": 0.31,
  "verdict": "QUALIFY",
  "floor_flags": {
    "F1": false,
    "F2": true,
    "F4": true,
    "F6": true,
    "F7": false,
    "F8": true,
    "F9": false,
    "F11": false,
    "F13": true
  },
  "issued_by": "GEOX runtime sess_efa6f048",
  "sovereign_approval": {
    "required": true,
    "status": "PENDING",
    "ticket_id": "hold_888_7a3f"
  },
  "timestamp_created": "2026-04-14T05:40:00Z",
  "timestamp_sealed": null,
  "vault_anchor": {
    "chain": "arifos_vault_999",
    "merkle_root": "merkle:def456...",
    "sequence": 18472
  },
  "lineage": {
    "parent_products": ["geox.map.malay_basin.2026q1"],
    "child_products": [],
    "calibration_event_id": null
  }
}
```

---

## 3. Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `product_id` | string | Unique identifier: `geox.{dimension}.{type}.{basin}.{period}` |
| `version` | semver | Product specification version |
| `product_type` | enum | One of: `hazard_map`, `hydro_model`, `ccs_plan`, `geochem_anomaly`, `petroleum_system_map`, `dfn_model`, `geological_map`, `stratigraphic_column`, `cross_section`, `3d_model`, `seismic_cube`, `volumetrics_report`, `play_fairway`, `paleogeographic_map`, `geotechnical_model`, `petrophysical_interpretation` |
| `dimension` | enum | `HAZARD`, `HYDRO`, `CCS`, `GEOCHEM`, `PETROLEUM_SYSTEM`, `FRACTURE`, `MAP`, `SECTION`, `EARTH3D`, `TIME4D`, `PHYSICS`, `WELL`, `PROSPECT`, `CROSS`, `DASHBOARD` |
| `engine` | object | Name, version, and adapter version of the physics engine used |
| `inputs_hash` | string | SHA-256 of the canonical input bundle (for reproducibility) |
| `inputs_manifest` | object | Human-readable description of data sources and scale |
| `uq_summary` | object | Uncertainty quantification summary (P10/P50/P90, ensemble size, etc.) |
| `ac_risk` | float | Computed AC_Risk score |
| `verdict` | enum | `SEAL`, `QUALIFY`, `HOLD`, `VOID` |
| `floor_flags` | object | Boolean map of which F1–F13 floors were triggered |
| `issued_by` | string | Session or runtime ID that generated the product |
| `sovereign_approval` | object | 888_HOLD tracking (required, status, ticket_id) |
| `timestamp_created` | ISO8601 | Product generation time |
| `timestamp_sealed` | ISO8601 | Time when verdict was finalized and vault-sealed |
| `vault_anchor` | object | arifOS vault Merkle chain reference |
| `lineage` | object | Parent and child product references, plus calibration event linkage |

---

## 4. Vault Binding

### 4.1 Anchor Requirement

Every product with `verdict ∈ {SEAL, QUALIFY, HOLD}` must be anchored in the arifOS vault before externalization.

Products with `verdict == VOID` must also be anchored (negative evidence is evidence).

### 4.2 Merkle Inclusion

The vault entry contains:

```json
{
  "entry_type": "GEOX_PRODUCT",
  "product_id": "geox.hazard.pga.malay_basin.2026q2",
  "verdict": "QUALIFY",
  "ac_risk": 0.31,
  "inputs_hash": "sha256:abc123...",
  "merkle_leaf_hash": "sha256:xyz789...",
  "sequence": 18472,
  "timestamp": "2026-04-14T05:40:00Z"
}
```

This makes every product:
- **Tamper-evident**
- **Replayable** (re-run from `inputs_hash`)
- **Auditable** (calibration loop can look up past predictions)

---

## 5. Calibration Linkage

When a prediction is later compared to observation, the `lineage.calibration_event_id` is populated:

```json
{
  "lineage": {
    "parent_products": ["geox.hazard.pga.malay_basin.2026q1"],
    "child_products": ["geox.hazard.pga.malay_basin.2026q3"],
    "calibration_event_id": "calib_2026_09_14_q1"
  }
}
```

The calibration event itself is also a vault-anchored object:

```json
{
  "entry_type": "GEOX_CALIBRATION",
  "calibration_id": "calib_2026_09_14_q1",
  "product_id": "geox.hazard.pga.malay_basin.2026q2",
  "misprediction_ratio": 1.35,
  "u_phys_adjustment": 0.10,
  "d_transform_penalty": 0.05,
  "verdict_override": "HOLD"
}
```

---

## 6. Product Type Registry

| Product Type | Dimension | Mandatory 888_HOLD? |
|--------------|-----------|---------------------|
| `hazard_map` | HAZARD | Yes (public) |
| `hydro_model` | HYDRO | Yes (public) |
| `ccs_plan` | CCS | Yes |
| `geochem_anomaly` | GEOCHEM | No |
| `petroleum_system_map` | PETROLEUM_SYSTEM | No |
| `dfn_model` | FRACTURE | No |
| `geological_map` | MAP | No |
| `stratigraphic_column` | SECTION | No |
| `cross_section` | SECTION | No |
| `3d_model` | EARTH3D | No |
| `seismic_cube` | EARTH3D | No |
| `volumetrics_report` | PROSPECT | Yes (public reserves) |
| `play_fairway` | PROSPECT | No |
| `paleogeographic_map` | TIME4D | No |
| `geotechnical_model` | FRACTURE/PHYSICS | Yes (safety certs) |
| `petrophysical_interpretation` | WELL | No |

---

**Sealed:** 2026-04-14T05:40:00Z  
**DITEMPA BUKAN DIBERI**
