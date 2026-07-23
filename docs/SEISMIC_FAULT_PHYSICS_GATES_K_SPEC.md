# Physics-validation gate spec for fault picks (K-*)

**Authority:** F13 sovereign input 2026-07-23 + external literature zen 2026-07-23  
**Status:** **LIVE PRODUCT** — `structure_validate` + `geox_falsify(structural_*)`  
**SOT (zen):** `docs/SEISMIC_SECTION_INTERPRET_ZEN.md`  
**Code:** `src/geox_mcp/tools/structure_gates/`

Each gate returns `PASS | KILL | INCONCLUSIVE` + receipt.  
INCONCLUSIVE is valid. Gates are **correlated** — not blind POS multiply.

| Gate | Rule | Kill when | Literature |
|------|------|-----------|------------|
| **K-DIP** | Dip vs regime after **VE correction**: normal 55–70°, reverse/thrust 20–40°, SS 75–90° | Outside range without reactivation / fluid-pressure flag | Anderson; Célérier 2008; Alcalde VE bias 2019 |
| **K-THROW** | Throw tapers to elliptical tip-line | Constant/increasing throw at tip | Barnett et al. 1987 AAPG |
| **K-DL** | D/L ~10⁻³–10⁻¹ global; Earth bulk **0.005–0.05** | Extreme outliers without linkage story | Kim & Sanderson 2005; Torabi & Berg 2011 |
| **K-XCUT** | Horizons non-crossing; age–fault consistency | Impossible crosscut / order | Bond group SE 2019 |
| **K-RESTORE** | Line-length/area residual within tol | Gaps/overlaps that invalidate geometry | Dahlstrom 1969; Groshong ADS |
| **K-VEL** | Interval V physical for lithology prior | Impossible velocities | rock-physics bands |
| **K-GROWTH** | Syn-kinematic claim ⇒ EI > 1 | Growth claimed but EI ≤ 1 | Thorsen 1963; Castelltort caveats |

## Live status

| Half | State |
|------|--------|
| Checking | LIVE — structure_validate + structural falsify |
| Proposing | LIVE partial — interpret_section/RSI (INT_SEISMIC) |
| Benchmarks | OPEN — F3/CRACKS/Alcalde harness (need provenance packs) |

## Call

```python
await geox_seismic_interpret(mode="structure_validate", framework={...})
# or
await geox_falsify(claim_type="structural_fault", context={...})
```

DITEMPA BUKAN DIBERI
