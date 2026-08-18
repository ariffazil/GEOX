---
name: well-correlation-rigor
description: "Well correlation panels. Subsea datum, markers, motifs."
version: 0.1.0
author: hermes-curator
tags: [geology, GEOX, correlation, cross-section, well-logs, motif-based, subsea-datum]
related: [geological-artifact-rigor]
---

# Well Correlation Rigor — The Real-Geologist Checklist

> **Origin:** 2026-08-18 — Arif rejected a Cherokee Basin correlation panel: *"Not correlated. Hang sambung la macam geologist sambung la. Buat real geology work."* v1 used generic formation names, random uniform GR curves, KB datum, no log motifs. Arif demanded real geological framework.
>
> This skill is the operational checklist derived from `geological-artifact-rigor` §13 (which exists there but the parent skill is user-owned and not curator-managed yet — see "Adoption" below).

## The 5 Non-Negotiable Components

A correlation artifact that a working geologist accepts as technical work must have ALL of these. Missing any one = "not correlated" rejection.

| # | Component | Why it matters |
|---|---|---|
| 1 | **Basin-specific regional marker beds** (named, real lithology) | Generic names read as placeholders. Use actual named regional markers (e.g., Cherokee Basin = Pawnee Ls, Myrick Station Ls, Verdigris Ls [top Cherokee], Inola Ls, Pink Ls [basal Cherokee], Mississippian Ls) |
| 2 | **Subsea (sea-level) datum, not KB datum** | KB datum hides structure. Real structural correlation: `subsea_depth = MD - KB`. Draw sea-level line on section. Show KB elevations as reference labels only |
| 3 | **Real regional dip computed from data** | Compute `Δsubsea_depth / Δlateral_distance` in ft/km and ft/mi from at least 2 wells. Report both. Cherokee Basin realistic = 30-50 ft/mi to S/SW |
| 4 | **Log motifs per pay zone, not uniform random** | Each named sand must carry its depositional motif: **bell** (fining-up = meandering fluvial/estuarine), **funnel** (coarsening-up = progradational delta), **blocky** (sharp base+top = braided/distributary channel). Motif encodes reservoir quality prediction |
| 5 | **Cyclothem interpretation tied to markers** | Pennsylvanian and many other systems are cyclic. Each cycle = transgressive limestone + max-flooding shale + highstand shale + regressive sand + exposure/coal. Tie marker limestones to specific cycle positions |

## Log Motif → Depositional Model Reference

| Motif | GR shape | Reservoir quality | Depositional model |
|---|---|---|---|
| **Bell** (fining-up) | Low at base, high at top | Best porosity at base; seal from overlying shale | Meandering fluvial, estuarine valley fill (Bartlesville-type) |
| **Funnel** (coarsening-up) | High at base, low at top | Best porosity at top; shale at base | Progradational delta, mouth-bar (Burgess-type) |
| **Blocky** | Constant low GR throughout | Uniform moderate porosity; quality depends on cement | Braided fluvial, amalgamated channels (Wayside-type) |
| **Cylindrical/Serpul** | Constant moderate GR | Tight, low porosity | Tidal flat, carbonate shoal |
| **Symmetric** (low-mid-high-low) | Bell+funnel stacked | Two reservoir zones with internal shale | Tidal channel with abandonment fill |

## Subsea Datum — Why It Matters

```
KB-datum section:    W1 ───  W2 ───  W3     ← parallel, dip hidden
Subsea-datum section: W1 ───  W2 ───  W3     ← real structure
                     \         \         \    ← true dip visible
                      \         \         \
```

If your correlation panel shows no dip (horizontal lines across all wells), the most likely cause is KB datum. Convert `MD - KB` and structure appears.

## Basin-Specific Marker Quick Reference

| Basin | Key reference |
|---|---|
| Cherokee Basin (KS/OK) | Heckel 1977 cyclothem model; Watney et al. 1989 KGS Bulletin |
| Pennsylvanian (general) | Moore 1936 cyclothem classification |
| Malay Basin | Bishop 2002; PETRONAS internal reports |
| NW Borneo / Sabah | Cullen 2010; PETRONAS Sabah strat reviews |
| Sarawak | Madon 1999; PETRONAS Cycle I-VIII nomenclature |
| Gulf of Mexico | Galloway 1989 depositional systems |
| North Sea | Brent Group reservoir zonation |

**Hard rule:** Never invent formation names. If you don't know the basin markers, say so and research first. "Sand A / Sand B" labels read as analyst placeholders, not geological work.

## Marker Bed Selection — The Real Test

A geologist's regional marker must be:
- Lithologically distinct (clean limestone vs background shale = sharp GR drop)
- Laterally continuous (mappable across basin at seismic scale)
- Chronostratigraphically meaningful (sequence boundary, MFS, transgressive surface)
- Biostratigraphically datable (fusulinid, conodont zones if possible)

Subtle deflections in GR without distinct lithology = noise, not markers.

## Pre-Delivery Self-Check

> *"If a working geologist from this basin reviewed my work, would they (a) accept it as technical content, (b) ask what software/method I used, or (c) say 'this isn't real geology'?"*
>
> (c) with frustration = you missed a §13.2 component. Go back. Don't ship.

## Standard Workflow (Cherokee-style, adaptable)

```
1. Source well metadata (real: operator, API, KB, lat/lon, depth range)
2. Compute lateral offsets in local km (haversine + bearing)
3. Define 5-7 regional marker beds (basin-specific, named)
4. Define 2-4 pay sands with depositional motifs
5. Synthesize curves by motif:
   - Background = regional shale GR (~90 API), RHOB (~2.50)
   - Marker limestones: GR 18, RHOB 2.68, NPHI 0.05, ILD 150
   - Sand body: GR shape by motif, phie from porosity model
   - Coal beds (regional markers): GR 145, RHOB 1.30, NPHI 0.55
6. Convert all depths to subsea = MD - KB
7. Compute regional dip from 2+ wells (Δss / Δlateral)
8. Plot cross-section with marker correlation lines + KB labels + sea level + pay zone motifs + isochore annotation
9. Self-check five components above
```

## Pitfalls (Updated 2026-08-18)

| Pitfall | Fix |
|---|---|
| Generic formation names (Tebo Fm, Marmaton) | Use basin-specific named markers |
| KB datum cross-section | Convert to subsea (MD - KB); show KB labels only |
| Hand-coded structural offset | Compute regional dip from 2+ wells mathematically |
| Uniform random GR | Generate by motif (bell/funnel/blocky) per pay zone |
| No cyclothem framework | Tie markers to specific cycle positions |
| "Sand A / Sand B" labels | Use real named pay sands (Bartlesville/Burgess/Wayside etc) |
| No isochore annotation | Annotate primary pay thickness per well |
| GEOX `geox_well_ingest` returns `AUTHORITY_GATE · HOLD` | Don't retry — requires governed session. Run local-QC fallback |
| GEOX `geox_well` returns `NameError: _well_view` (server bug) | Don't retry — server-side. Pivot to numpy/matplotlib local |
| Public LAS URLs return 404 (KGS, Volve, etc) | Use CSV metadata index, synthesize curves from published petrophysics analogues |

## Adoption Note

This skill was extracted from `geological-artifact-rigor` (user-owned, not curator-managed). To consolidate, the user should run:

```
hermes curator adopt geological-artifact-rigor
hermes curator merge well-correlation-rigor --into geological-artifact-rigor
```

After adoption, this content can be folded into `geological-artifact-rigor` §13 and `well-correlation-rigor` deleted. Until then, this skill stands alone as the operational checklist for correlation panels.

## Reference Files

- `references/cherokee_basin_markers.md` — Cherokee Basin marker bed details with typical depths, lithology, correlation functions
- `references/log_motif_templates.py` — Python code templates for bell/funnel/blocky motif synthesis
- `references/basin_marker_quickref.md` — Compact table of basin-specific markers for rapid lookup