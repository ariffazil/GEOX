# Physics-validation gate spec for fault picks (K-*)

**Authority:** F13 sovereign input 2026-07-23  
**Status:** SPEC (not yet implemented as product loop)  
**Use:** Multiplicative POS-style gates — any KILL → repick; all INCONCLUSIVE → INCONCLUSIVE

Each gate returns `PASS | KILL | INCONCLUSIVE` + receipt.  
INCONCLUSIVE is valid (see live `geox_falsify` on Andersonian normal fault without wells/V).

| Gate | Rule | Kill when |
|------|------|-----------|
| **K-DIP** | Dip vs regime: normal 55–70°, reverse 20–40°, strike-slip subvertical | Outside range without reactivation evidence |
| **K-THROW** | Displacement profile tapers toward tips | Constant/increasing throw at tip |
| **K-DL** | Max displacement / length in ~10⁻³–10⁻¹ global envelope | Extreme outliers without linkage story |
| **K-XCUT** | Horizons non-crossing; age–fault consistency | Younger cut without growth geometry |
| **K-RESTORE** | Line-length/area balance closes within tolerance | Gaps/overlaps that invalidate geometry |
| **K-VEL** | Interval V from T–D physical for claimed lithology | Impossible velocities |
| **K-GROWTH** | Syn-kinematic claim ⇒ expansion index > 1 | Growth claimed but EI ≤ 1 |

## Current GEOX status

| Half | State |
|------|--------|
| Checking (falsify / claim) | LIVE — disciplined INCONCLUSIVE works |
| Proposing (section interpret) | CODE partial; public path repaired for 1D contrast only |
| K-* product suite | **NOT BUILT** — this file is the binding spec |

## Benchmark

Alcalde et al. human-variance section — score agent picks against known interpreter disagreement.

## Implementation order

1. P0 contract truth (schema/handler) — done 2026-07-23  
2. P1 accept FaultStick candidates into K-DIP / K-THROW stubs  
3. Full K-suite + F3 benchmark  

DITEMPA BUKAN DIBERI
