# LOOPSTRUCTURAL_REALITY_AUDIT.md

**Status:** EMPIRICAL — tested in venv (LoopStructural 1.8.2, python 3.12, pydantic 2.14).
**Method:** introspect 86 modules + build real models + attempt fault/fold/restoration path.
**Principle:** PASS only if tested-and-observed; FAIL if absent; UNKNOWN if present-but-not-demonstrated.

---

## 1. The answer to the most expensive question

> **Can LoopStructural 1.8.x satisfy M1 (4×2D + 1×3D restoration + RestorationBundle + 3 hypotheses)?**

**NO — not as a native capability.** LoopStructural 1.8.x is an **implicit structural
MODELLING library** (faults, folds, foliations interpolation), NOT a restoration engine.
It models present-day faulted/folded geometry. Restoration-to-prefault-coordinates is
NOT a demonstrable native workflow. The roadmap's "adapter exists → M1 = hardening +
surfacing" premise is **false for restoration**: hardening the adapter cannot conjure a
restoration algorithm that does not exist upstream.

---

## 2. Capability table (Arif's format)

| Capability | Status | Evidence (OBS) |
|---|---|---|
| GeologicalModel | **PASS** | `GeologicalModel(bb[0], bb[1])` built; claudius + duplex loaded; bounding box, stratigraphic column live |
| Stratigraphic Surfaces | **PASS** | `create_and_add_foliation('strati')` → `evaluate_feature_value` returned 8000 values (min −153.5, max 468.4) |
| Fault Feature | **PASS** | `create_and_add_fault` → `FaultSegment` created, `fault_names()=['fault1']` |
| Fold Frame | **PASS (model) / FAIL (unfold)** | `FoldFrame`, `FoldEvent`, `_fold_rotation_angle_feature`, `fold_function` (fourier/trigo/lambda) exist; **no `unfold`/reverse-fold API** — only `rot_mat` + `get_deformed_orientation` |
| Restoration to Prefault Coordinates | **UNKNOWN (not demonstrated)** | `FaultSegment.apply_to_points(reverse=True)` exists + runs ("Unfault the array of points"), but `reverse=True` produced IDENTICAL output to `reverse=False` (Δ=18.195 both) — reverse not demonstrated to restore |
| Export Mesh | **PASS** | `evaluate_model`, `get_block_model`, `get_stratigraphic_surfaces`, `get_fault_surfaces`, `ModelExporter`, `to_dict/to_file/to_recipe_json` |
| 2D Restoration Candidate | **FAIL (native)** | no balanced cross-section / area-balance / flexural-slip module exists |
| 3D Restoration Candidate | **FAIL (native)** | same — modelling-only |
| RestorationBundle (3 competing hypotheses) | **FAIL (native)** | must be built in GEOX on top of exported geometry + unfaulting primitive |

---

## 3. Module-tree evidence (OBS)

- 86 modules enumerated. **ZERO** with `restor/unfold/deform/backstrip/kinematic` in the name.
- Restoration-relevant source keywords exist ONLY as:
  - `_fault_segment.py` → `apply_to_points(reverse=False)` "Unfault the array of points"
  - `_base_geological_feature.py` → `_apply_faults(reverse=False)` "restored location"
  - `geological_model.py` → `faults_displacement_magnitude` (displacement ↔ restoration magnitude conversion)
  - `_foldframe.py` → comment "in the restored space" (fold computed in unfaulted space)
- **No module implements balanced restoration, unfolding, or cross-section balancing.**

---

## 4. Empirical test receipts

```
load_claudius(): data(DataFrame X/Y/Z/val/feature_name/nx/ny/nz) + bb(2×3)
  model = GeologicalModel(bb[0], bb[1])            # NOTE: docstring example bb[:,0] is STALE for 1.8.2
  model.data = data                                # set_model_data() is deprecated
  model.create_and_add_foliation('strati')         # → interpolator built, 8000 grid values
  stratigraphic_column: [Basement, Base Unconformity]

load_duplex(): features = [fault1, fault2, strati]; fault val = 0.0 (displacement NOT encoded)
  model.create_and_add_fault('fault1', displacement=100.0, data=f1, fault_center=[1.28,1.48,3.92],
      fault_slip_vector=[0,0,1], major_axis=5, minor_axis=2, intermediate_axis=2)
  fault type: FaultSegment
  point y=+1.98:  apply_to_points(reverse=False) → Δ=18.195
                  apply_to_points(reverse=True ) → Δ=18.195   # IDENTICAL → reverse not reversing
```

---

## 5. What this means for M1

| Roadmap requirement | LoopStructural 1.8.x reality | GEOX action |
|---|---|---|
| 4×2D restoration | NOT native | build restoration on top of `apply_to_points` + exported geometry; balance checks are GEOX-side |
| 1×3D restoration | NOT native | same |
| RestorationBundle | NOT native | GEOX schema (DRAFT_CANDIDATE) + wrapper |
| 3 competing hypotheses | NOT native | GEOX perturbation/ensemble layer (Chamberlin) |
| fault handling | PASS (modelling) | reuse |
| fold handling | PASS (modelling) / FAIL (unfold) | unfold must be built or sourced elsewhere |
| export | PASS | reuse |

**Verdict: LoopStructural can supply the STRUCTURAL MODEL. It cannot supply the
RESTORATION. The M1 restoration engine must be built in GEOX (or a restoration-capable
engine substituted) — "adapter hardening" alone is insufficient and cannot close the
RM5.96M vendor gap.**

---

## 6. Blockers to M1.2 (in order)

1. Restoration algorithm source decision: build-on-LoopStructural vs substitute engine
   (e.g. flexural-slip unfolding / Move-equivalent). This is an **architecture decision → 888/Arif**.
2. Prove `apply_to_points(reverse=True)` restores (or document its real semantics) —
   the reverse flag did not reverse in test; needs a minimal two-point displacement proof.
3. Synthetic fixture set (GATE C) — still blocked on provenance matrix acceptance.
4. Actor binding (GATE A) — still OBSERVE_ONLY.
