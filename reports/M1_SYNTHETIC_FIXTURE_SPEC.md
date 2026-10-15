# M1_SYNTHETIC_FIXTURE_SPEC.md — GATE C (design only, NOT generated)

**Status:** SPEC. Fixtures NOT generated this run (per stop-condition: generate only after inventory + matrix complete).
**Purpose limit:** schema / adapter / invariants / failure-path testing ONLY. No geological-validity claim.

---

## 1. Why synthetic

Existing fixtures are well LAS only (synthetic Volve + Sandakan demos). The M1
restoration slice needs: a 2D line, a structural map, well tops + marker ages,
orientation, velocity/depth input, stratigraphic column + unit ages, compaction
parameters, and a datum horizon. None of these exist as synthetic fixtures.

## 2. Synthetic fixture rules (binding)

1. Every file path/name carries the token `SYNTHETIC`.
2. No PETRONAS names, coordinates, well names, field names, or copied geometry.
3. No mixing with real evidence (separate directory from `resources/basins/*`).
4. No geological-validity claim — values are *geometrically self-consistent*, not *real*.
5. Deterministic seed + generator provenance recorded per file (re-runnable).
6. Public geological NOMENCLATURE (e.g. "Sandakan Fm", "Volve") is allowed only where
   already public; synthetic VALUES must be visibly implausible-as-real (see §4).

## 3. Component set (8 files)

| File | Contents | Generator | Seed |
|---|---|---|---|
| `SYNTHETIC_2d_line.json` | one 2D interpreted horizon + 1 fault stick (X/Z polylines) | deterministic script | `m1-line-0001` |
| `SYNTHETIC_structure_map.json` | gridded top-horizon depth map (regular grid) | deterministic script | `m1-map-0001` |
| `SYNTHETIC_well_tops.yaml` | 8 wells × tops (MD, TVDSS) + marker ages (Ma) | deterministic script | `m1-tops-0001` |
| `SYNTHETIC_orientation.csv` | bedding dip/dip-azimuth per unit (uniform + jitter) | deterministic script | `m1-orient-0001` |
| `SYNTHETIC_velocity.yaml` | V0 + k (linear v(z)) per unit for depth conversion | deterministic script | `m1-vel-0001` |
| `SYNTHETIC_strat_column.yaml` | unit names + absolute ages (Ma) | hand-authored (no real basin copied) | — |
| `SYNTHETIC_compaction.yaml` | φ0 + c (Athy) per lithology class | published-default values | — |
| `SYNTHETIC_datum.yaml` | datum horizon reference (name + depth reference) | hand-authored | — |

## 4. Anti-real markers (so it can never be mistaken for field data)

- 8 wells at artificial spacing (e.g. exactly 2.0 km apart on a synthetic grid).
- Marker ages at round, non-stratigraphic values (e.g. 5.0, 10.0, 20.0, 30.0 Ma).
- Constant structural offset per fault (uniform 25 m throw) — geometrically impossible in real geology.
- Velocity = pure linear v(z), no lateral variation.
- Compaction = textbook Athy with default φ0/c, no calibration.

## 5. Provenance record per file

```yaml
synthetic: true
generator: <script path>
seed: <seed>
generated_at: <iso-ts>
sha256: <hash>
purpose: [schema, adapter, invariants, failure_path]
geological_validity: NONE
```

## 6. NOT this run

- Do not generate the files now (stop-condition).
- Do not write generators until the provenance matrix is human-accepted.
- Do not point M1.1 at real `resources/basins/*` until each is classified ALLOW.
