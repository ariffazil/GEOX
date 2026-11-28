# MODEL_PROVENANCE_MATRIX — Sabah A–A′ (Kinabalu cross-section)
Generated 2026-10-20 · machine record: `model_provenance.json` (64 entries, one per visible object)
Source of truth: `_geometry_raw.json` (extracted verbatim from the live page's in-page data; public sources only)

## 0. THE CORRECTION THAT STARTED THIS (recorded permanently)

> **Morley et al. (2023) did NOT propose "three different plates beneath the Sabah Basin."**
> It is a shallow-to-middle crustal **mobile-shale / mud-canopy tectonics** model for the
> North Sabah–Pagasa Wedge: mini-basins, feeder pipes, chambers, mud volcanoes.

Verification against our own surfaces (grep, 2026-10-20):
- `"three plates" / "plates beneath"` → **0 hits** on cross-section, dossier, observatory, PDF.
- `"magmatic ridge"` → **0 hits** anywhere. Model A was **renamed 2026-10** to
  "rift-axis intrusions?" and the page states plainly: *"not a spreading ridge"* —
  ridge-push mechanism withdrawn (REFS.TS02 records the rename).
- The word "plate" on the cross-section appears only as: *upper/lower plate* (classic
  subduction vocabulary, Model C), *plate-scale vs gravitational* (King et al. 2010),
  and *no plate-driving push is claimed* (Model A). All legitimate tectonic usage.
- Therefore the "three plates / Morley model" reading is a **misreading of a schematic** —
  three differently coloured deep polygons in a drawing are three drawn bodies, not three
  plates. That misreading is exactly what this matrix exists to prevent.

**Do not cite Morley for:** three plates · three-slab stack · continental underthrusting ·
slab remnant · any deep plate boundary.
**Morley citation scope (frozen):** mobile shale, mud canopy, mini-basins, feeder pipes,
chambers, mud volcanoes — the NSPW shallow system only. Its deep continuation = UNKNOWN.

## 1. Ontological split (the four "choices" are NOT one menu)

| Class | Model | Scale | What it answers | Status |
|---|---|---|---|---|
| **D. Author-generated alternative** | **A · rift-axis intrusions?** | local body-scale (deep) | could a local heat source exist along the trough axis? | **AUTHOR HYPOTHESIS — UNTESTED — NOT A PUBLISHED MODEL** (TS02, Fazil 2026) |
| **A. Shallow process model** | **B · mud canopy (NSPW)** | shallow (wedge interior) | what fills and deforms the wedge? | PUBLISHED (Morley et al. 2023) — citation scope: shallow system only |
| **B. Crustal architecture model** | **C · underthrust Dangerous Grounds** | crustal | what is the crustal architecture? | CLASSIC SYNTHESIS (Hinz 1989; Hazebroek & Tan 1993; Hutchison 2005) — contested by Vijayan et al. 2013 |
| **C. Mantle-process driver** | **D · slab remnant + gravity tectonics** | mantle + crustal response | what drives uplift/extension? | PUBLISHED CONSTRAINTS (Cornwell 2025 imaging; Cottam 2010/2013 ages) + conceptual mantle geometry |

They address **different depths and processes and can coexist** — they are not four
mutually exclusive whole-Earth models. Ranking without a scoring rule is prohibited;
the honest output is the model family + the next discriminating measurement.

## 2. Model-by-model audit (the four questions)

**A — rift-axis intrusions?**
- From one paper? No — a working note (TS02, Fazil 2026).
- Synthesis? No — deliberately minimal.
- New GEOX/Arif hypothesis? **YES, 2026, untested.**
- Does any cited paper publish an along-section geometry? **NO** — parameterised configuration only.
- What do the sources support? Regional context + potential-field hints only. Not intrusion geometry.
- Per-body provenance: all Model A bodies = SPEC / author-generated (see JSON entries `modelA:*`).

**B — mud canopy (NSPW)**
- From one paper? Primarily yes — **Morley et al. 2023, Geosphere 19(1): 291** (3D seismic + wells).
- Synthesis? Minor (wedge-fill naming from regional framework).
- New hypothesis? No.
- Published along-section geometry? Partial — wedge architecture published, **not along A–A′**.
- What does the paper support? **Shallow process only** — mobile shale, mini-basins, feeder pipes,
  chambers, mud volcanoes. **Not** plate identity, crustal interpretation, or mantle geometry.

**C — underthrust Dangerous Grounds**
- From one paper? No — classic synthesis (Hinz et al. 1989; Hazebroek & Tan 1993; Hutchison 2005).
- Synthesis? **YES** — multi-source.
- New hypothesis? No — it is the inherited framework.
- Published along-section geometry? **NO** — drawn as schematic.
- What do the sources support? Plate-scale convergence context + crustal-architecture hypothesis.
  **Contested:** Vijayan et al. 2013 — DG crust 25–30 km, **no crustal suture and no relict
  oceanic crust beneath the trough**; the trough is a **foredeep, not a trench**.

**D — slab remnant + gravity tectonics**
- From one paper? No — synthesis (Hall 2013; Cottam et al. 2010/2013; King et al. 2010; Cornwell et al. 2025).
- Synthesis? YES.
- New hypothesis? No.
- Published along-section geometry? **Partially** — the W-dipping discontinuity at **45–55 km is
  published imaging (Cornwell et al. 2025)** and is drawn as a **published constraint, NOT fitted
  to this line**; the slab shape and asthenosphere are conceptual.
- What do the sources support? Deep discontinuity (constraint), granite timing 7.85–7.22 Ma,
  plate-scale vs gravitational budget (King 2010). Not an along-line slab geometry.

## 3. Numeric discipline (figure-audit anchors carried)
- Moho: KMY 32.8 ± 2.5 km (Sidek et al. 2016); regional Moho 32.8–52.5 km (gravity inversion);
  crustal max ~60 km beneath Crocker Range, min ~24 km central Sabah (receiver functions).
- Surfaces as ranges, not points: BMU ~23–24 Ma · **DRU 13.5–12.5 Ma (some picks 14.2–14.9)** ·
  UIU ~10.5 · SRU ~8.5–9.5. Where the page draws "DRU ~14.2 Ma" it is a calibration pick
  inside that range — the range is the honest claim.
- Kinabalu granite 7.85–7.22 Ma, emplacement ~7–12 km, intruded under extension.
- Basal detachment ~5–8.7 km below seabed, dipping landward ~1.9°.
- Top NN9 ≈ 9.53 Ma — any "Top NN9 at 8.5 Ma" statement is internally inconsistent.

## 4. Visual grammar rules now enforced (see `provenance_guard.py`)
1. No author cited for a claim absent from their source record (Morley ↔ plates = FAIL).
2. A shallow-process paper may not justify deep geometry.
3. SPEC/author bodies may never read as observed picks (Model A must carry UNTESTED).
4. Every drawn geometry carries a provenance entry.
5. Incompatible scales may not share one undifferentiated menu (hence §1).
6. The word "plate" is reserved for tectonic plates; mud canopies and coloured polygons are not plates.
7. "magmatic ridge" is a stale name — banned (Model A is "rift-axis intrusions?").

## 5. History preserved
- Prior visuals archived versioned in this directory: `base_{A,B,C,D}.png`, `styl_D_c{1,2}.png`
  (c1 rejected by witness — recorded), `final_D.png`, with `RECEIPT-SABAH-AA-002.json`,
  `qc_report.json`, `manifest.json` (sha256 of every file).
- Nothing deleted. This matrix is additive; the page's prior state is in git history.
