# Sabah Cross-Section Audit — External Review (relayed by Arif, 2026-10-13)

> **Provenance:** External-model audit of an agent-generated Sabah cross-section (PROJECT_2026-v2.2 lineage, `CANDIDATE` — not sealed), relayed verbatim by Arif (F13 sovereign) 2026-10-13. Archived by FI-008 as the evidence base for the 2026-10-13 GEOX correction batch. Tier: T3 synthesis over T1/T2 sources (URLs inline). Full session text lives in this session's wire log; this archive preserves the operational content.
>
> **Corrections already applied same-day (FI-008, git working tree):** plate framing in `sabah_basin_strat.yaml` + `sabah_basin/{basin_profile.yaml,tectonic_history.md}` + `nw_sabah_context.md`; Pilia citation split (NatGeosc=drip model / Gondwana Research=tomography); Madon 2025 Moho 26–33 → 32.8–52.5 km in `sabah_basin/claims.json` (verified live against publisher abstract); SRU single-age → AGE HOLD; NN9/NN10 boundary-scheme note in `nn_zones.json`; well evidence registry created at `resources/registry/wells_sabah.json`.

## TL;DR (audit's own)

- **Agent output: not fit for use as-is.** Tepat-1 was an oil and gas discovery in 2018, confirmed by Tepat-2 in 2022. Telupid ophiolite is in central Sabah (~117.1°E), well east of the Crocker Range. The Sabah Trough is floored by thinned Dangerous Grounds continental crust, not near-oceanic crust. The real collision was Dangerous Grounds/Reed Bank continental crust against the Sabah margin after PSCS subduction — not "Eurasia vs Philippine Sea Plate". Fabricated well outcomes and the "Ratified" stamp are governance failures, more serious than the geology errors.
- **The age contradictions mostly need bookkeeping, not new rocks.** DRU 13.5–12.5 Ma (Morley 2023) vs ~12–13 Ma (Lunt 2022) vs ~15.5 Ma (spreading-end models) tie to different events/calibrations/domains. Arif's 14.2–14.91 Ma is the outlier needing explicit marker basis. SRU 9.4 vs ~8.5 Ma is probably marker choice (top NN9 vs stage IVC/IVD), not just GTS2012 vs GTS2020. Carry multiple age models keyed to biostratigraphic events.
- **GEOX next steps:** 2 weeks — well/outcome registry + hypothesis-ID registry enforced by `outputSchema`/`isError` + cross-tool age-conflict check. 2 months — marker-based chronostratigraphy service (`geox.chrono`) + structural section engine (LoopStructural/GemPy + kinematic fault-fold). 6 months — Sabah evaluation suite with trap/known-answer/conflict tasks (GeoBenchX-style).

## Error ledger (agent output under audit)

| # | Agent claim | Type | Verdict |
|---|---|---|---|
| 1 | Tepat-1 "DRY / stratigraphic test" | Factual | Wrong: public oil & gas discovery (2018), appraised by Tepat-2 (2022) |
| 2 | Outcomes for placeholder Wells A/B/D | Fabrication | Most serious. Placeholders have no outcomes; text borrowed real play names (Rotan Sands, stage IVC) to sound credible |
| 3 | "Ratified 2026-10-13" | Overclaimed certainty | Model is v2.2-CANDIDATE, not sealed; governance state invented |
| 4 | Detachment ~15 km | Unsupported | Published range ~5–8.7 km (ADS, JSG 2018); wedge >8 km thick (Morley 2024) |
| 5 | H2 redefined as hyperextended crust/OCT | Governance (ID drift) | Breaks hypothesis identity; mint new ID (e.g. H5=H1-over-H2 stacked), freeze H1–H4 |
| 6 | Onshore drawn as seawater, no Crocker Fm | Rendering | Wrong; Crocker Formation is the onshore backbone |
| 7 | Telupid ophiolite inside Crocker Range | Factual | Wrong location (central Sabah ~5.65°N 117.12°E); age contested (Miocene 9.2–10.5 Ma zircons, Tsikouras 2021, vs Mesozoic Chert-Spilite); Ranau peridotites are the ultramafics near Kinabalu |
| 8 | Sabah Trough floor = thin near-oceanic crust | Factual | Contradicts gravity–magnetic + seismic evidence for thinned continental crust (Hinz 1989; Franke 2008; Vijayan 2013: no crustal suture, no relict oceanic crust; Gilligan 2026) |
| 9 | SRU 8.5–9.0 (Top NN9), DRU 13–12 | Silent override | Took GEOX profile ages over the chart without flagging the conflict. Note: "Top NN9 = 8.5" is internally inconsistent in ANY timescale (top NN9 = 9.53 hamatus / 10.41 kugleri) |
| 10 | "Eurasian vs Philippine Sea Plate collision" (GEOX profile) | Factual | Wrong framing; PSCS subduction then Dangerous Grounds collision (Hall 2013) |

Pattern: errors 2/3/5/9 are the system letting an LLM write into fields that should only be filled from registered evidence. Prompts won't fix that; schema + registry enforcement will.

## Verified fact-checks (key sources)

- **Tepat-1/2:** PETRONAS Dec-2022 release (T1): https://www.petronas.com/media/media-releases/malaysia-doubles-exploration-success-2022-10-discoveries ; PETRONAS MPM exploration page (T1): https://www.petronas.com/mpm/malaysia-e-p/exploration ; S&P (T3, gas column + oil rim, Nido-equivalent): https://spglobal.com/commodity-insights/en/research-analytics/potential-in-ultra-deepwater-sabah-malaysia
- **Telupid:** central Sabah, Sandakan Division, ~5.65°N 117.12°E; Tongkul 1997 (Mesozoic ophiolitic basement, Cret–Olig cover): https://www.sciencedirect.com/science/article/abs/pii/S0743954797000068 ; Miocene zircons 9.2–10.5 Ma, Tsikouras et al. 2021 Geology: https://pubs.geoscienceworld.org/gsa/geology/article/49/7/789/595632/
- **NSPW detachment:** ADS method, NW Borneo FTB (JSG 2018): basal detachment ~1.9° landward dip, ~5–8.7 km depth: https://www.sciencedirect.com/science/article/pii/S0191814118304322 ; Morley 2024 ESR: wedges >8 km thick, several hundred km wide. 15 km has no published support. Always state datum (below seabed vs sea level).
- **Mud canopy (Morley et al. 2023 Geosphere 19:291):** ~50 MV centres, 4–80 km² each; dense canopy ~1900 km²; MV-affected mini-basins ~3500 km²; onset coincides with UIU (base stage IVC); early canopy basin IVC (~10.5–8 Ma), late IVD (~8–7 Ma); source mobile shale ~2–4 km sub-sea, ~1 km thick; pre-canopy mini-basins loaded by up to 4 km clastics. Show canopy as horizon tied to UIU, not fixed depth. https://pubs.geoscienceworld.org/gsa/geosphere/article/19/1/291/619254/
- **Sabah Trough crust:** Vijayan, Foss & Stagg 2013 JAES — 25–30 km crust (Luconia/DG) thinning to 25–20 km under trough "without tectonic discontinuity"; foredeep not trench; "no evidence of any crustal suture... nor any relict oceanic crust beneath the trough". Gilligan et al. 2026 JGR (10.1029/2025JB031499): DG crust beneath Sabah; 60 km under Crocker Range, 24 km central Sabah. Cullen 2010 debate = trench position, not oceanic floor.
- **Plate framing:** Hall 2013: "During the Paleogene the Proto-South China Sea was subducted beneath northern Borneo. Subduction ended with Early Miocene collision of the Dangerous Grounds/Reed Bank/North Palawan block and the Sabah–Cagayan Arc." https://www.sciencedirect.com/science/article/abs/pii/S1367912013002095
- **Madon 2025 (verified live by FI-008 2026-10-13):** Madon, Linang & Pilia 2025, Tectonophysics (1 Sep 2025), "Seismic-constrained gravity inversion of Moho depth beneath Sabah": Moho 32.8–52.5 km, mean 40.8 km; "Sabah is not in complete isostatic equilibrium... highly overcompensated". https://www.sciencedirect.com/science/article/abs/pii/S0040195125003026
- **Pilia 2023 (verified live by FI-008):** NatGeosc doi:10.1038/s41561-023-01201-7 = "Post-subduction tectonics induced by extension from a lithospheric drip" (mechanism model); Pilia, Rawlinson et al. 2023 Gondwana Research = P/S arrival-time tomography, slab-like HVA >250 km. GEOX's old "Pilia 2023 (Nature Geoscience) — detached slab tomography" conflated the two; corrected.

## Contradiction resolutions (decision rules adopted)

- **DRU (2a):** keep as FAMILY (DRU-shelf, DRU-Spine, DRU-TB, DRU-onshore/TCU-composite); each member gets own marker + age range + calibration tag; merge only on line-by-line seismic continuity. ~15.5 Ma spreading-end tie = plate-event hypothesis, not an age. 13.5–12 Ma = biostrat-led regional consensus. GTS2012→2020 shift ~0.1 Myr cannot explain 1–2 Myr gaps — different marker or different surface.
- **SRU (2b):** 9.4 vs 8.5 = marker choice (top NN9-hamatus 9.53 vs stage IVC/IVD boundary ~8.5–8.6), not timescale. Checks: large (≥15 µm) D. hamatus only; same seismic reflector as Morley's Block H?; legacy 9.4 on which Shell stage calibration?
- **BMU/TCU (2c):** 23–24 Ma = stratigraphic surface; ~21 Ma = geodynamic subduction end (Gilligan). Two linked entities, never one number. DG RU/MMU 16 Ma = separate outboard surface; correlate to DRU only if traced seismically.
- **Deep crust H1–H4 (2d):** H1 and H2 NOT mutually exclusive — published picture stacks them (ophiolitic basement atop underthrust continental crust; mid-crustal discontinuity 23–24 km = top of underthrust crust, W Sabah). Do not rename; mint composite (H5 = H1-over-H2 stacked), freeze H1–H4. H4 = cover-level hypothesis, not basement. Discriminating tests ranked: (1) wide-angle/OBS refraction across trough (Vp 6.0–6.6 thick = continental; thin 6.7–7.2 layer-3 = oceanic; serpentinised gradient = OCT — only test that can rescue the OCT idea, file as new ID); (2) integrate nBOSS receiver-function profiles (public on OSF); (3) joint grav-mag forward models along the exact line, RF-Moho-constrained; (4) ophiolite geochem/geochron (MORB vs SSZ; Telupid Miocene vs Mesozoic chert-spilite = one terrane or two).
- **Kinabalu (2e):** U-Pb zircon 7.85–7.22 Ma (Cottam 2010); ~170 km³ over ~0.6 Myr under extension (Burton-Johnson); emplacement 7–12 km, exhumation ~7 mm/yr (Cottam 2013). Cause candidates: slab breakoff (Cottam 2013), Celebes rollback (Hall 2013), lithospheric drip (Pilia 2023 NatGeosc). Phase C K-Ar spread (6.5–22.9 Ma): HOLD correct. Young cluster (7.8/7.3/6.5) plausible (Bergman 1988 phlogopite 7.8±0.3 matches U-Pb); old ages look like authigenic+detrital mixtures. Protocol: IAA (≥3 size fractions, 1Md/1M vs 2M1 polytype quantification, %detrital-vs-age extrapolation), ⁴⁰Ar/³⁹Ar step-heating (vacuum encapsulation for <0.2 µm illite), U-Pb on true igneous phases (date rims), thin section/SEM FIRST. Check present-day temperature at 4077–4293 m MD — >150°C causes diffusive Ar loss (ages too young).
- **NSPW vs DWFTB (2f):** compatible by domain+time. Hesse/Back/Franke 2009 GSA Bull 121:939 — shortening 8–13 km increasing through time; south = gravity-driven (matches shelf extension), north = basement-driven (exceeds it). Ogawa/Back/Littke 2023 — SW gravity domain: peak shortening at source-rock gas window; NE crustal domain: still oil window. Morley 2023 — NSPW main growth Early–Middle Miocene (deep-seated), Late Miocene onward gravity-driven from mini-basin loading; ~8 km min shortening since late Miocene. Gravity-vs-crustal is a slider along strike and through time, not binary.

## Practical workflow rules (audit) → GEOX adoption

1. Store EVENTS not ages: every pick = marker + well + depth + observer + calibration (GTS2012/2020/Shell-stage legacy); ages computed per timescale on the fly (DINOSTRAT as design example).
2. Parallel named age models (PROJECT_2026-v2.2 / Morley-2023-Lunt-2022 / spreading-end); sections render one model at a time with visible label + diff view (>0.5 Myr threshold).
3. Default diachronous surfaces; merging needs seismic continuity or overlapping age bands.
4. Uncertainty bands min–max with source tier; conflicting tiers shown side by side, never averaged.
5. "Sealed" only by explicit provenance-logged human action. No tool/LLM emits "Ratified".

## GEOX upgrade roadmap (audit, prioritised)

| Horizon | Upgrade | Fixes |
|---|---|---|
| 2wk | Well registry + placeholder⇒outcome:null schema rule | Errors #1 #2 — **DATA LIVE 2026-10-13 (wells_sabah.json); enforcement wiring pending** |
| 2wk | Status enum; sealed-only-by-human-provenance | Error #3 |
| 2wk | Hypothesis registry, frozen definition hashes, new-ID minting, A–D↔H1–H4 map | Error #5 |
| 2wk | `consistency_audit` (age deltas, status, geography) → isError | Errors #6 #7 #9 |
| 2wk | Correct basin profile (plate framing, Pilia attribution, SRU label) | Error #10 — **DONE 2026-10-13** |
| 2mo | `geox.chrono`: event picks, GTS2012/2020 tables, named age models, Wheeler renderer | DRU/SRU/BMU contradictions |
| 2mo | `section_kinematic` (trishear + fault-bend + area balance + ADS), LoopStructural/GemPy for 3D | Errors #4; layer-cake limit |
| 2mo | Geophysics constraint layer (Gilligan/Cornwell RF Moho + underthrust-top picks as hard constraints) | Errors #8; H1/H2 ambiguity |
| 6mo | Sabah eval suite (trap/known-answer/conflict, ~40 tasks) in CI; report fabrication rate per release | Measures everything above |
| 6mo | PROV-style provenance export; optional OSDU alignment | External auditability |
| 6mo | Geochronology module (IAA end-member regression, Ar-Ar/U-Pb data model, HOLD/RELEASE logic) | Phase C K-Ar ambiguity |

MCP design notes: strict `outputSchema` (`additionalProperties:false`, enums for well/model status); conflicts → `isError:true` with machine-readable conflict list; sealing via elicitation-confirmed human approval, logged; sections cite registry entries via `resource_link`; pass state (age-model ID, section ID) as explicit handle arguments.

## Caveats carried forward

- Audit numbers from snippets (verify before T2 ingestion): Morley 2023 SRU ~9–8.5 Ma; GTS2020 D. hamatus ~9.61 Ma; NSPW max thickness (2026 JGR).
- Lunt & Madon 2017 numeric ages not read directly (cited via Morley 2023 / Lunt 2022).
- Tepat-1 reservoir details confidential; public record agrees only on oil & gas in carbonate build-up.
- Published fabrication-rate from the eval suite, falling release over release, is the strongest credibility signal for reviewers.
