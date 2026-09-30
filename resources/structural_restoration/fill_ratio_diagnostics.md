# Fill Ratio Diagnostic Protocol

## Definition

```
fill_ratio = sediment_thickness / accommodation
```

## Classification

| Range | Status | Action |
|-------|--------|--------|
| < 0 | INVALID | Mask and report. Check sign convention. |
| 0 – ~1 | Underfilled to filled | Normal range. |
| ~1 | Approximately filled | Accommodation ≈ sediment. |
| > 1 | **ANOMALY** | **Diagnostic review required.** |

## When fill_ratio > 1

This is an observation of a geometric discrepancy. It is NOT an automatic indication of fault activity.

### Diagnostic Checklist (test in order)

| # | Possible cause | How to test |
|---|---------------|-------------|
| 1 | **Reversed subtraction order** | Verify sign convention and which surface is subtracted from which |
| 2 | **Inconsistent restoration ages** | Verify ages of both states are correct and internally consistent |
| 3 | **Mismatched surface extents** | Verify both surfaces cover the same geographic area |
| 4 | **Unit or datum mismatch** | Verify CRS, XY units, Z units, datum, and polarity match |
| 5 | **Erosion or hiatus** | Check for unconformity surfaces or erosion between states |
| 6 | **Compaction model mismatch** | Verify compaction curve is appropriate for lithology and depth range |
| 7 | **Interpolation artefact** | Check grid interpolation method and cell size vs data density |
| 8 | **Missing structural displacement** | Check for faults with displacement not in the restoration |
| 9 | **Inappropriate facies/lithology** | Verify lithology assignment for the depositional setting |
| 10 | **Fault activity** | ONLY after ALL above causes excluded. Requires independent structural evidence. |

### Final Rule

**Fault activity is one hypothesis. Not the only hypothesis.**

A fill_ratio > 1 must complete the diagnostic checklist before any tectonic interpretation is attached. The diagnostic checklist is enforced by the `DiagnosticChecklist` schema in the event ontology.

## NW Sabah Context

In NW Sabah, fill_ratio anomalies may additionally reflect:
- Mobile shale withdrawal (NSPW)
- Mud canopy loading/unloading
- Gravity-driven deformation (DWFTB)
- Multiple overprinted tectonic events

These basin-specific causes supplement — but do not replace — the universal diagnostic checklist.
