# LOOPSTRUCTURAL_1_8_COMPATIBILITY_MATRIX.md — M1.1

**Status:** ANALYSIS (no mutation). Adapter currently proves IMPORTABILITY only, not modelling compatibility.

---

## 1. Adapter state (OBS)

`src/geox_core/engines/geospatial/loopstructural_adapter.py` (228 lines):
- Only LoopStructural reference is `import LoopStructural as _ls` (availability gate) + `__version__`.
- Methods `fault_network_model`, `fold_model` are numpy scaffolds — they do NOT call any LoopStructural modelling API.
- `_LOOPSTRUCTURAL_AVAILABLE=True` in venv (1.8.2); `_check_dependencies()` fails closed with ImportError otherwise.

## 2. API surface verified (OBS, venv LoopStructural 1.8.2)

| Symbol | Available (1.8.2) | Required by GEOX (M1) | Current adapter usage | Path / replacement | Test needed |
|---|---|---|---|---|---|
| `GeologicalModel` | ✅ top-level + `modelling.GeologicalModel` | yes (model construction) | none (import only) | use `modelling.GeologicalModel` | construct empty model |
| `StratigraphicColumn` | ✅ top-level | yes (unit ages/order) | none | use top-level | column build |
| `LoopStructuralConfig` | ✅ top-level | yes (interpolator/process config) | none | use top-level | config load |
| `InterpolatorBuilder` | ✅ top-level | yes (surface interpolation) | none | use top-level | surface interpolate |
| `FaultNetwork` | ❌ top-level | yes (fault features) | none | **UNKNOWN — probe `modelling.features`** | feature enum |
| `FaultSegment` | ❌ top-level | yes | none | UNKNOWN — probe `modelling.features` | — |
| `FaultDisplacement` | ❌ top-level | yes | none | UNKNOWN — probe `modelling.features` | — |
| `FoldFrame` | ❌ top-level | yes (fold frame) | none | UNKNOWN — probe `modelling.features` | — |
| `modelling.features` | ✅ submodule present | yes (fault/fold feature classes) | none | introspect contents | symbol enumeration |

**Key finding:** the adapter's docstring claims fault-network and fold support, but:
(a) the adapter never calls the API, and (b) the symbols it would need (`FaultNetwork`,
`FaultSegment`, `FaultDisplacement`, `FoldFrame`) are NOT top-level in 1.8.x — they
live (if at all) in `modelling.features`, which is not yet enumerated. Compatibility
is therefore UNPROVEN in both directions.

## 3. Version pin reconciliation

- Registry + adapter docstring + error message now pin `>=1.8.0,<2` (MIT license).
- venv runtime = 1.8.2 (satisfies); system python = 1.8.0 (satisfies).
- `2.0.0` does not exist on PyPI → the old pin would never resolve.

## 4. Next probe (blocking, before vertical slice)

Introspect `LoopStructural.modelling.features` and `modelling.core` in venv 1.8.2 to
enumerate the real fault/fold/stratigraphic-feature class names. This closes the
`FaultNetwork`/`FoldFrame` UNKNOWN rows and lets the vertical slice pick concrete APIs.

## 5. Compatibility verdict

**PARTIAL — importable, not yet modelling-compatible.** Adapter is a license- and
version-correct scaffold; the LoopStructural 1.8.x modelling API it must call is not
yet enumerated, and the adapter does not call it. No M1.2 restoration can run until
this matrix's UNKNOWN rows are closed.
