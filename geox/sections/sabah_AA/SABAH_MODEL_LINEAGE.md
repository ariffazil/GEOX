# SABAH_MODEL_LINEAGE — every model, every citation, what each actually claims
Schema: model ID · author/year · exact cited claim · time interval · domain · depth/scale ·
source pointer · section geometry published? · evidence type · limitation · **what it does NOT claim**
Status: v1 · 2026-10-20 · GEOX/333-AGI · machine records: `sabah_model_provenance.json`, `model_provenance.json`
Guard: `provenance_guard.py` (PASS at commit) · Companion: `MODEL_PROVENANCE_MATRIX.md` (figure audit) · `H-EXT-01.md` (theory)

## 0. Attribution law (frozen, non-negotiable)
1. **Morley et al. (2023)** = North Sabah–Pagasa Wedge **mobile shale / mud canopy system only**
   (mini-basins, feeder pipes, chambers, intrusions, mud volcanoes, shallow gravity deformation).
   Never cited for: three plates · slab remnant · lithospheric drip · underthrust geometry ·
   oceanic basin · extension corridor. Deep continuation of the canopy = **UNKNOWN**.
2. "Plate" is reserved for defined lithospheric plates. Mud canopies, coloured polygons and
   tectonostratigraphic units are NOT plates.
3. "magmatic ridge" is a **retired name** (Model A renamed 2026-10 → "rift-axis intrusions?"; the
   page states "not a spreading ridge").
4. Published constraint ≠ fitted pick. Cornwell 2025 imaging is drawn as **published, not fitted**.

## 1. Historical / published models

### M-HIN89 — Hinz, K. et al. (1989), Geologische Rundschau 78: 705–730
- Claim: thrust tectonics along the NW Sabah continental margin; imbricate thrusts on 2D seismic.
- Time: Miocene contraction · Domain: NW Sabah margin · Scale: crustal.
- Section geometry published? **No along-A–A′ geometry** — regional seismic lines, not this transect.
- Evidence: 2D seismic interpretation.
- Limitation: pre-3D era; thrust style contested by later mobile-shale work.
- **Does NOT claim:** mud canopy · mantle driver · extension · any plate stack beneath Sabah Basin.

### M-HT93 — Hazebroek, H.P. & Tan, D.N.K. (1993), GSM Bull. 33: 195–210
- Claim: Tertiary tectonic evolution of the NW Sabah margin; the DRU family as regional unconformity
  (the "~15.5 Ma published chart" lineage).
- Time: Paleogene–Miocene · Domain: NW Sabah · Scale: basin-to-crustal.
- Section geometry? Schematic regional framework only.
- Evidence: field + subsurface synthesis.
- **Does NOT claim:** an age-precision for the DRU (its value is a chart calibration, not a pick) · mantle geometry.

### M-HUT05 — Hutchison, C.S. (2005), *Geology of North-West Borneo* (Elsevier)
- Claim: regional synthesis — accretionary/collisional framework of NW Borneo incl. ophiolite belts.
- Time: Mesozoic–Cenozoic · Domain: NW Borneo · Scale: regional.
- Section geometry? No. **Does NOT claim:** local Sabah Basin geometry · one winning driver.

### M-BAL03 — Balaguru, A., Nichols, G. & Hall, R. (2003), GSM Bull. 46: 335–351
- Claim: origin of the "circular basins" of Sabah.
- Time: Miocene · Domain: Sabah interior · Scale: basin. **Does NOT claim:** deep crustal architecture.

### M-BH09 — Balaguru, A. & Hall, R. (2009), AAPG Search & Discovery #30084
- Claim: tectonic evolution and sedimentation of Sabah; BMU deformation narrative.
- Time: Cretaceous–Cenozoic · Domain: Sabah · Scale: regional. Section geometry? Regional cartoons only.
- **Does NOT claim:** an A–A′ geometry · mantle driver specifics.

### M-HALL13 — Hall, R. (2013), J. Asian Earth Sci. 76: 399–411  ★ precedent for H-EXT-01
- Claim: **contraction AND extension in northern Borneo driven by subduction rollback** — a
  post-subduction extensional phase is explicitly part of this model.
- Time: Neogene–present · Domain: northern Borneo · Scale: lithospheric.
- Section geometry? Conceptual cartoons, not a measured corridor.
- **Does NOT claim:** a continuous extension corridor along Sabah · oceanic breakup in Sabah ·
  that extension began at a dated unconformity.

### M-COT10 / M-COT13 — Cottam, M.A. et al. (2010) JGS 167: 49–60; (2013) JGS 170: 805–816
- Claim: Kinabalu granite U–Pb **7.85–7.22 Ma**, pulsed emplacement + rapid exhumation;
  emplacement ~7–12 km **under extension**.
- Time: Late Miocene · Domain: Crocker Range/Kinabalu · Scale: pluton + crustal.
- Evidence: geochronology + thermochronology (hard numbers).
- **Does NOT claim:** the extension mechanism · a corridor geometry · any slab.

### M-KING10 — King, R.C. et al. (2010), Marine & Petroleum Geology 27: 238–246
- Claim: balance of **plate-scale vs gravitational tectonics** in the NW Borneo delta + deepwater
  fold-thrust belt; both operate, partitioned.
- Time: Miocene–recent · Domain: NW Borneo margin · Scale: crustal.
- **Does NOT claim:** a winner between drivers · mantle geometry.

### M-COR25 — Cornwell, D.G. et al. (2025), JGR Solid Earth 130(11): e2025JB031466
- Claim: migrated teleseismic P receiver functions reveal intricate post-subduction crust and upper
  mantle beneath Sabah — incl. a **W-dipping discontinuity at 45–55 km**, interpreted as a detached
  slab remnant / related to Celebes Sea subduction.
- Time: present-day structure · Domain: northern Borneo · Scale: crust + upper mantle.
- Section geometry? **Imaged constraint along their own stations — NOT fitted to A–A′** (drawn as
  "published, not fitted"). Evidence: passive seismology.
- **Does NOT claim:** an along-A–A′ slab shape · that the discontinuity is proven slab · any driver.

### M-MOR23 — Morley, C.K. et al. (2023), Geosphere 19(1): 291  ★ FROZEN SCOPE
- Claim: the North Sabah–Pagasa Wedge is a major Miocene **deepwater mud canopy / mobile-shale
  system** — mini-basins (up to ~4 km clastics), feeder pipes, chambers, intrusions, mud volcanoes.
- Time: Miocene · Domain: NSPW (offshore NW Sabah) · Scale: **shallow (sedimentary column to wedge interior)**.
- Section geometry? Wedge architecture from 3D seismic + wells — **not along A–A′**.
- **Does NOT claim:** three plates · a deep plate boundary · slab remnant · drip · underthrusting ·
  oceanic crust · extension corridor. **Its deep continuation is UNKNOWN.**

### M-MOR24 — Morley, C.K. (2024), atypical syn-collisional wedges  [RELAYED via GEOX — verify exact passage before publication]
- Claim as relayed: uplift + **slab breakoff** timing used for the DRU event window (~13–12 Ma).
- Time: Middle–Late Miocene · Domain: NW Borneo · Scale: crustal–lithospheric.
- **Does NOT claim:** (pending verification) — do not cite for plates/drip/oceanic.
- Limitation: the surface/event distinction stands independently (surface ~14.2 pick; published charts ~15.5;
  event 13–12) even if this citation is refined.

### M-VIJ13 — Vijayan, V. et al. (2013)  [anchor value set]
- Claim: Dangerous Grounds crust **25–30 km**, thinning to 20–25 km under the trough with
  **no crustal suture and no relict oceanic crust beneath it**; the **trough is a foredeep, not a trench**.
- **Does NOT claim:** underthrust geometry as imaged fact. Directly constrains/cuts Model C's classic framing.

### M-TOMO22 — teleseismic P & S arrival-time tomography, northern Borneo (S1342937X22003288)
- Claim: mantle structure beneath northern Borneo — PSCS slab remnant near the western coast;
  deeper central-Sabah anomaly.
- Scale: mantle · Evidence: tomography (resolution-limited).
- **Does NOT claim:** crustal expression of extension · a corridor · one driver.

### M-PILIA23 — "Post-subduction tectonics induced by extension from a lithospheric drip",
Nature Geoscience 2023 (s41561-023-01201-7)  [first-author attribution per relay: Pilia et al. — verify before publication]  ★ mechanism for H-EXT-01B
- Claim: geodynamic modelling — **a lithospheric drip can drive extension** in/after subduction
  termination, thinning adjacent orogenic crust, promoting **lower-crustal melting and exhumation**.
- Time: post-subduction · Domain: northern Borneo analog · Scale: lithospheric.
- Section geometry? Numerical model, not an imaged corridor.
- **Does NOT claim:** that Sabah's extension WAS drip-driven · oceanic breakup.

### M-THIN-RELAY — central Sabah thinning factors **~1.2–1.3**  [RELAYED via review; source = SCS continental-rifting study family]
- Claim as relayed: thinning below breakup values → **continental orogenic extension** safer than
  oceanic-rift interpretation. (This is the key "idk if oceanic or what not" answer: current numbers
  favour continental; oceanic = UNMEASURED.)
- Limitation: relayed figure — verify the primary source before publication.

### M-RF16 / M-GRV25 — Sidek et al. (2016) BGSM 62 (doi:10.7186/bgsm62201607); Madon et al. (2025)
- Claim: receiver-function Moho **32.8 ± 2.5 km at KMY**; gravity/crustal structure of Sabah.
- Evidence: passive seismology + gravity. **Does NOT claim:** a driver.

### M-HAQ24 — Haq, B.U. & Ogg, J.G. (2024), Cenozoic sequence boundaries (NgSB chart)
- Claim: global sequence-boundary chronology (NgSB1/8/11/13 anchors used for the surface correlations).
- **Does NOT claim:** any tectonic driver; eustasy ≠ tectonics (this is why DRU ≠ collision onset).

### M-CHOI26 — Choi, T. (2026), TGS/EAGE workshop — Layang-Layang Oligocene play
- Claim: frontier play context. Evidence: workshop abstract. **Does NOT claim:** Sabah crustal architecture.

## 2. GEOX / Arif models (versioned registry)

| ID | Type | Basis | Status | Does NOT claim |
|---|---|---|---|---|
| **G-A** · rift-axis intrusions? | AUTHOR HYPOTHESIS (TS02, Fazil A. 2026) | parameterised; potential-field hints | **UNTESTED — NOT A PUBLISHED MODEL** | not a ridge · no plate push · not a regional driver · not proven anywhere |
| **G-B** · mud canopy (NSPW) | published shallow process (M-MOR23) | 3D seismic + wells | PUBLISHED (shallow scope only) | no deep tail (UNKNOWN) · no plates · no driver |
| **G-C** · underthrust Dangerous Grounds | classic synthesis (M-HIN89/M-HT93/M-HUT05) | schematic | CLASSIC — downgraded to one competing crustal hypothesis | not imaged fact; contested by M-VIJ13 |
| **G-D** · slab remnant + gravity tectonics | synthesis (M-HALL13/M-COT10/13/M-KING10/M-COR25) | published constraints + conceptual mantle geometry | PUBLISHED CONSTRAINTS + conceptual | slab shape not fitted to A–A′ · no driver chosen |
| **H-EXT-01** | **GEOX/Arif source-constrained synthesis** | M-HALL13 extension phase + M-COT timing + M-PILIA23 mechanism + M-TOMO22/M-RF spatial + M-THIN-RELAY | **TESTABLE — not published single-author** | no oceanic crust · no seafloor spreading · no third plate · no measured continuous corridor · no preferred driver |
| H-EXT-01A/B/C/D | competing drivers (rollback / drip / gravitational collapse / inherited reactivation) | alternative mechanisms | ALL LIVE — preferred_hypothesis = **null** | none is chosen absent discriminating observation |

## 3. Literature claim matrix (the disputed items)

| Claim | Verdict | Record |
|---|---|---|
| "Morley theorized 3 plates beneath Sabah Basin" | **REJECT_UNATTRIBUTED** | 0 hits for "three plates"/"plates beneath" on any arif-fazil.com earth surface (grep 2026-10-20). M-MOR23 scope = shallow mobile-shale system. |
| "A magmatic ridge" as a model name | **STALE** | renamed 2026-10; page says "not a spreading ridge"; ban enforced by guard |
| Post-subduction extension across north-central Sabah | L2_SOURCE_CONSTRAINED_SYNTHESIS | M-HALL13 explicit extension phase; M-RF/TOMO spatial; M-COT timing |
| Extension is oceanic spreading | **UNMEASURED** | M-THIN-RELAY: thinning ~1.2–1.3 < breakup values → continental favoured |
| PSCS slab remnant | L2_MANTLE_INTERPRETATION | M-TOMO22, M-COR25 (imaged, not fitted here) |
| Lithospheric drip beneath central Sabah | L2_MANTLE_INTERPRETATION + mechanism modelling | M-TOMO22 anomaly; M-PILIA23 mechanics |
| 45–55 km discontinuity | published constraint (M-COR25) | drawn "published, not fitted" |
| DRU = collision onset | **REJECT** | DRU carries eustatic signal (NgSB8 match); "DRU ≠ collision onset without structural evidence" |

## 4. Unresolved evidence — continental extension vs oceanic breakup
1. Crustal thinning pattern along the whole transect (receiver functions + VDSS): β distribution, not point values.
2. Moho continuity across the Crocker–Kinabalu–Telupid sector (is the Moho pulled up under the corridor?).
3. Extensional fault kinematics + timing (fault-slip analysis, growth strata) — syn- vs post-DRU.
4. Geochronology of extensional fabrics/veins (U–Pb calcite, Ar–Ar) vs granite 7.85–7.22 Ma.
5. Thermochronology exhumation budget (M-COT: rapid — but where is the extensional breakaway?).
6. Seismic anisotropy (shear-wave splitting): corridor-parallel flow vs steep drip fabric.
7. Gravity + FTG with uncertainty: is there a narrow dense strip (oceanic) or broad thinning (continental)?
8. Magnetic character: any seafloor-spreading lineation pattern? (Low-latitude caveat: use AS/RTE, absence = INCONCLUSIVE.)
9. Heat flow/BHT + Ro/Tmax: advective fault-flow vs magmatic heat (discriminate geometry, not "hot").
10. Deep basin fill record in Sabah interior basins: syn-extension unconformities + subsidence curves.

## 5. Versioning
v1 2026-10-20 — created. Prior visuals preserved in this directory (base_*, styl_*, final_D.png);
no historical model was overwritten; G-A renamed once (rift-axis intrusions?, ridge-push withdrawn) with
the rename recorded in REFS.TS02.
