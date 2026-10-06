# IBS Kinabalu Basin — Deep Research & Reality Update
**Date:** 2026-10-06 · **Author:** 333-AGI (FI-003) · **Session:** SEAL-5662675babe246f8
**Trigger:** F13 (Arif) — poster day (PGCE/abstract: "Why Revisit the Kinabalu Basin?"), order: *"do one deep research on how to solve this, probe my existing work on Kinabalu Basin and update the reality"*
**Labels:** OBS = witnessed on this machine · PUB = published literature (cited) · INT = interpretation (capped 0.75)

---

## 1 · THE PROBLEM, DECOMPOSED (INT from poster text + PUB)

The poster names four failure modes. Each is a different animal:

| # | Failure mode | Class | Solvable by |
|---|---|---|---|
| P1 | Multiple stratigraphic nomenclatures (Sabah Stages ↔ Sarawak/Brunei Cycles ↔ company schemes) | **Lexicon** | Crosswalk registry + event-anchored backbone |
| P2 | Inconsistent seismic marker picking / horizon correlation | **Workflow** | RGT-volume interpretation + well-tied keylines + confidence maps |
| P3 | Legacy interpretations, "one stage = multiple tectonic events" | **Event model** | Event-stack decomposition (ABKSS-class), unconformity age re-ranking |
| P4 | Cross-border (Brunei) uncertainty → play fairway + opportunity risk | **Integration** | Isochron anchors + provenance + shelf-margin trajectory bridge |

**PUB — this problem is 50 years old and fully documented.** Bol & van Hoorn (1980) Stages; Levell (1987) DRU/LIU/UIU/SRU; Ho (1978)/Doust (1981) Cycles; Morrison & Lee (2003, GSM) mapped both onto Haq TB sequences and explicitly flagged "lack of consistent stratigraphic nomenclature… fragmentation compounded by political boundaries"; PETRONAS PMU (2007) chronostrat chart admitted "Sabah's stratigraphic nomenclature varies among companies and geoscientists"; Malek et al. (2007) documented Shell vs Murphy divergent schemes. IBS Phase I is therefore not re-litigating geology — it is the **first institutional convergence play**, and there is quantified precedent (see §3.1).

---

## 2 · REALITY PROBE — WHAT THE MACHINE ALREADY HOLDS (OBS)

Probed 2026-10-06 by `rg` sweep + file reads. The federation is **not empty** on Kinabalu — it carries a sealed, dated knowledge core:

| Asset | Path | Status | Content |
|---|---|---|---|
| Sabah strat ontology | `/root/GEOX/resources/ontology/sabah_basin_strat.yaml` | LIVE, NSPW-updated 2026-07-16 | Physics-9 seismic-anchored stratigraphy; **IRON LAW: biostrat calibrates, never verifies**; NSPW (North Sabah–Pagasa Wedge) mobile-shale wedge as mechanical spine; Sabah Trough = flexural, not trench |
| ABKSS event stack | `/root/GEOX/resources/structural_restoration/nw_sabah_context.md` | LIVE | 5-phase tectonic framework (ASAS→BEBAS→KAPUR→SABAR→SENJA) with recalibrated ages: BMU/TCU 23 Ma, **DRU 13 Ma (Lunt & Madon 2017)**, UIU 10.5, SRU 8.5; overprinting + mobile-shale + basement-heterogeneity guards |
| Biostrat reference stack | `/root/GEOX/resources/ontology/biostrat_reference_stack.yaml` | LIVE, canonical | Nannotax3 + GTS2012 + operator Kinabalu/Sabah reports; LBF <2500m TVDSS, CNN deeper |
| OKF Sabah bundle | `/root/GEOX/okf/sabah-basin/` (8 files) | SEALED 2026-07-20 (vault seq 12) | sabah-ladder (Stages I–VI), kinabalu prospect (INT conf 0.65), nw-sabah basin, bekantan-1 well, morley-2023 + nspw-mud-canopy evidence |
| Kill matrix | `/root/GEOX/geox/skills/subsurface/petro/sabah_kill_matrix.py` | LIVE | Hypothesis-kill logic for Sabah plays |
| Correlation doctrine | `/root/GEOX/skills/well-correlation-rigor/SKILL.md` | LIVE | Well-tie discipline |
| Macrostrat/JMG ingest | `/root/GEOX/ingest/macrostrat-malaysia/` | LIVE | MY-relevant strat packages + myGEMS catalog |
| **Kinabalu scar** | `/root/memory/evidence/kinabalu_scar/` (+2026-09-cycle) | OBSERVED, critical | **2026-06-15: EGRS biostratigrapher Abd Hadi Hashim confirmed "the biostrat data is wrong" (SB409/SB412 tops)** — after Arif refused (Feb 2026) to polish a deliverable from broken biostrat inputs. Attendees include 3 of today's poster co-authors. This scar is the institutional genesis of the IBS revisit. |

**Gap analysis (OBS→DER):** what exists is *framework-grade* (ontology, event stack, iron laws). What is missing for Phase II: (a) a machine-readable **crosswalk registry** (Stage↔Cycle↔TB↔GTS2020↔Brunei sequence), (b) the **8 keylines** as versioned digital objects (they live in PETRONAS systems, not here — UNKNOWN to this machine), (c) biostrat event database with reworking flags, (d) any RGT/ML interpretation compute wired to GEOX.

---

## 3 · DEEP RESEARCH — STATE OF THE ART ("how to solve") (PUB)

### 3.1 The proven precedent: graphic-correlation chronosequences
The unified Sabah–Sarawak scheme already exists in quantified form (GSM, "Upper Tertiary chronosequence stratigraphy… graphic correlation"): ~60 offshore Sabah wells, 9 type wells (Kikeh-1, Gumusut-1B), **15 hiatuses (H05–H120) → 16 chronosequences**, tightly correlative with Sarawak's 20 — proving one regional event spine is extractable from biostratigraphy alone. Shell seismic horizons were shown to correspond to biostrat hiatuses, **but the hiatuses are more numerous** — i.e., seismic stages under-resolve the events. This is the quantitative ancestor of IBS Phase II and the answer to "one stage = multiple events."

### 3.2 The age problem is real and unresolved — use it, don't hide it
- Classic: MMU/DRU = TB 2.4 sb ≈ 15.5 Ma, tied to SCS spreading cessation (Kessler & Jong 2023; Morrison & Lee 2003; Balaguru: BMU 22–20 Ma = Sabah Orogeny, "real" deep regional).
- Revision: **Lunt & Madon 2017 redated DRU to ~13–12 Ma** (already adopted in GEOX ABKSS, OBS).
- Consequence (INT, 0.75): Stage IV sub-stage boundaries as picked today can bracket 2+ pulses (e.g., UIU 10.5 Ma slab-breakoff/wedge-top vs SRU 8.5 Ma transpression "Meliau Orogeny" vs 5.2 Ma late transpressional event). **Recommendation: framework publishes ages as ranges with provenance per event, never single-point ages.**

### 3.3 Cross-border Brunei bridge — three hard anchors
1. **Gartrell et al. 2011 (BSP)**: redefined Brunei Miocene–Recent into 10 third-order sequences using **shelf-margin trajectory + structural kinematics**; two boundaries hard-calibrated to global falls (11.7, 5.73 Ma). Autocyclic forcing (sediment supply, delta-top tectonics) dominates — TB scheme alone under-resolves Brunei. → Adopt shelf-margin trajectory as the shared Sabah↔Brunei correlation observable.
2. **Provenance (Breitfeld et al., UCL)**: **Champion (= East Baram) Delta is distinguishable from West Baram Delta** by chrome-spinel, garnet, detrital-zircon populations (Crocker recycling signature). → A litho-independent, border-blind correlation anchor for exactly the East Baram sub-basin named in the poster.
3. **Setap mobile-shale decollement (Morley et al. 2003, JSG)**: same detachment system runs both sides — wedge kinematics (Jerudong/Belait growth) gives a structural-timing correlation grid independent of nomenclature.

### 3.4 AI/ML for Phase II — the 2025–26 toolset that actually ships
| Task | Method (PUB) | Why it fits IBS |
|---|---|---|
| Basin-scale marker consistency | **RGT (relative geologic time) volumes** — RGT-Est (arXiv 2605.01273, sinusoidal mapping + sparse horizon priors); confidence-aware RGT tracking (Zheng et al. 2026) | One topologically-consistent chronostratigraphic field per survey; unconformities + faults handled; confidence maps show WHERE picks are unstable — exactly the marker-inconsistency detector Phase I suffered from |
| Expert-in-the-loop interpretation | **HorAgent** (Liu et al. 2026): state-aware agent, 1D+2D model fusion, MAE 2.07 ms on F3 | The 8 keylines become sparse priors/prompts → dense horizons with QC gates. Human stays in command |
| Well zonation/correlation | **LithoFormer** (arXiv 2607.22804): Seq2Seq PatchTST+RoPE, **Law-of-Superposition loss**, −90% boundary error | Consistent zonations across hundreds of wells; kills log-motif subjectivity flagged in the poster |
| Biostrat unification | Graphic correlation engine (§3.1) + reworking flags + multi-group witness (nanno + planktonic + palyno + LBF) | GEOX biostrat stack already canonical (OBS); iron law already encoded |
| GDE/RDE maps | RGT-flattened attribute volumes → chronostrat-consistent facies belts; Bayesian paleogeography ensembles (Frontiers 2026, Bohai case: −40% uncertainty) | HD GDE/RDE with NFE, as promised in poster conclusion |

### 3.5 Structural/tectonic model spine (PUB, matches machine's NSPW)
Morley et al. 2023 (Geosphere) + Morley 2024 (ESR) NSPW wedge; Pilia et al. 2023 (Nat. Geosci.) detached PSCS slab tomography; Domzig et al. 2024 (EAGE) deepwater Sabah sequential restorations — mid-crustal detachments, distal compression, **untested plays per episode**; Cottam et al. 2013 Kinabalu granite ultra-fast cooling. The machine's ABKSS already encodes this (OBS) — Phase II should restore the 8 keylines through these phases (event-tagged restoration, not single-step — the overprinting guard already in GEOX doctrine).

---

## 4 · THE BLUEPRINT — 7 WORKSTREAMS (INT, synthesised)

**W1 · Event-spine registry (kills P1).** One machine-readable registry: every regional surface gets `{name, aliases (Stage/Cycle/TB/company), age_range, age_provenance, event_class, witness_basis}`. Crosswalk table = generated view, hand-built never again. *Seed exists: sabah_basin_strat.yaml + ABKSS (OBS). Deliverable: `kinabalu_event_spine.yaml`.*

**W2 · Biostrat recalibration protocol (kills the scar class).** Multi-group witness with reworked-assemblage flags; calibrate-not-verify (already iron law, OBS); SB409/SB412-class tops quarantined pending re-entry QC; every age assignment carries its evidence chain. *GEOX biostrat stack is the engine.*

**W3 · Keylines as versioned digital control (kills P2 at the root).** The 8 keylines become frozen, hashed interpretation objects — every pick carries {method: human/ML, confidence, tie-well}. Disagreement between vintages becomes measurable, not narrative.

**W4 · RGT-volume interpretation + confidence maps (Phase II AI/ML).** Train on keyline labels; HorAgent-style loop; deliver per-surface confidence — the instability map IS the residual-inconsistency map.

**W5 · Cross-border anchors (kills P4).** Shelf-margin trajectory grid + provenance (zircon/spinel/garnet) sampling line across East Baram/Champion + shared unconformity isochrons with published ranges (§3.2). Correlate by observables, translate by crosswalk (W1).

**W6 · Event-tagged structural restoration.** Restore keylines through ABKSS phases (multi-step, overprinting guard, mobile-shale aware). Output: per-phase paleogeography → feeds GDE/RDE.

**W7 · HD GDE/RDE + missed-opportunity screen.** RGT-flattened facies belts + NFE ring-fence + per-episode untested plays (Domzig pattern: each tectonic episode holds untested plays). Prospect register diffed against drained/assigned areas = the "missed opportunities" list the poster promises.

**Order:** W1→W2 → (W3 ∥ W5) → W4 → W6 → W7. W1/W2 are cheap and unblock everything; they are also the only two that fix *governance*, not geology.

---

## 5 · REALITY UPDATE (Δ ledger)

- **From:** Kinabalu knowledge = fragmented across PETRONAS systems + sealed GEOX framework assets + one vindicated biostrat scar; no unified event spine; Phase II methods unnamed.
- **To:** This file = the convergence blueprint binding (a) machine-held sealed assets, (b) 50 years of published correlation science, (c) 2025–26 AI/ML toolset, into 7 executable workstreams with the 8 keylines as control objects.
- **Falsifier (BL12):** If Phase II proceeds without W1 (event-spine registry) + W2 (biostrat protocol) first, ML at scale will industrialise the inconsistency — that would falsify this blueprint's ordering claim.
- **Poster-day ammo (verified PUB):** (1) DRU has been redated 15.5→13–12 Ma (Lunt & Madon 2017) — "one stage, multiple events" has a name; (2) graphic correlation already extracted a 15-hiatus Sabah chronosequence spine correlative with Sarawak — the unification has quantified precedent; (3) Champion vs West Baram deltas are provably distinct in detrital zircon/provenance — border-blind correlation is physically possible.

*Companion controller:* `REALITYPLAN-ibs-kinabalu.json` (same dir). DITEMPA BUKAN DIBERI.

---

## ADDENDUM A — Provenance corrections after adversarial fact-check (2026-10-06, poster day)

Challenger: Copilot ENTERPRISE review (M365 + web routes). Resolution after document-level verification:

| Claim | Resolution | Poster-safe form |
|---|---|---|
| "Lunt & Madon 2017 redated DRU to ~13–12 Ma" | Substance CONFIRMED, citation sharpened: explicit bracket **13.77–11.7 Ma, younger preferred** is in the follow-up **BGSM 74 (2022)** *Field and well evidence for major unconformities in north Sarawak…*; 2017 BGSM 64 is *Onshore to offshore correlation of northern Borneo*. BGSM 74 also states DRU ≠ Doust MMU (**~3.5–4 My apart**) and traces the legacy "ca. 15 Ma" to a rounding artifact from Bol & van Hoorn schematics. | "The DRU is now bracketed ~13.8–11.7 Ma — several My younger than the Sarawak MMU; the old 15 Ma label was a rounding artifact (Lunt & Madon 2017; Lunt BGSM 74 2022)." |
| Chronosequence counts | RESOLVED 3-way: (a) **Krebs AAPG 2006 abstract** (*A New Chronosequence Stratigraphy…*, public) = **100+ wells, ≥22 hiatuses (H05–H180), 23 chronosequences (S05–S190)**, combined Sabah+Sarawak Tertiary; contains the thesis quote "seismic horizons may merge and be misidentified unless verified by microfossils". (b) **Krebs, GSM Bulletin** (author confirmed: William N. Krebs, PETRONAS Carigali) = Sabah **>60 wells / 9 type / 15 hiatuses / 16 chronosequences**, Sarawak **~70 wells / 20 / 20**. (c) Challenger's ">70 wells / 13 hiatuses / 14 sequences / 7+6" matches NEITHER published version — ">70" likely bled from the Sarawak row. My earlier "unverifiable" call was wrong about existence, right to doubt the numbers. | "Graphic correlation of 100+ wells shows seismic horizons can merge and be misidentified unless verified by microfossils (Krebs 2006; Krebs, GSM Bulletin)." |
| UIU/SRU "Meliau" — "no source found" | OVERTURNED: Balaguru, *Orogeny in Action* (EAGE/Earthdoc abstract) — IRU ~10.6 Ma (Kinabalu emplacement), SRU 8.6 Ma, "Meliau Orogeny" = author's coinage. Canonical surface definitions: Levell 1987 (BGSM 21). Attribute as one published reading. | Secondary anchor only; the DRU/MMU story is the lead. |
| PMU 2007 chart flag — "no source found" | OVERTURNED: quoted verbatim inside the FOSI/IAGI *Tertiary Uplift and Miocene Evolution of NW Borneo* paper (grey-literature chart described in published text). | "PETRONAS PMU's 2007 chronostratigraphic chart already flagged the Sabah stage problem (discussed in later NW Borneo literature)." |
| Compound unconformity example | NEW: **Kimanis Bay-1** penetrates a compound BMU+DRU surface (Lunt 2021, J. Asian Earth Sci.; summarised nummulites.net 2021). | Strongest single "one marker, two events" well example. |
| Team Phase I numbers (M365 deck, May/June vintage) | NOT verifiable from VPS; internally consistent with abstract (8 keylines = 5 dip + 3 strike; SB409 re-blocking coherent with scar file SB409/SB412). Confirm currency with Siti Arasy before quoting. | Results line as compiled by challenger, pending currency check. |

**Misattribution guard (binding at poster):** all literature points above are framed "consistent with published work"; the team's results are ONLY the Phase I numbers (keylines/wells/coverage/NN standard). Challenger's risk note accepted as correct.

**Concession logged:** challenger's 240-word rewrite already retained the Sarawak clause; my earlier "restore it" correction was unnecessary.

---

## ADDENDUM B — Morley 2023 primary-text corrections, ledger recount, master task board (2026-10-06, evening)

**Trigger:** Copilot ENTERPRISE review with Morley et al. 2023 (Geosphere 19(1), NSPW mud canopy) primary text attached.

### B.1 Corrections accepted from Morley 2023 primary text
- **DRU age strengthened:** Morley places DRU 13.5–12.5 Ma (Fig. 23 ca. 12 Ma) — a third published source alongside Lunt 2022 (BGSM 74) ~13–12 Ma. Balaguru & Hall 2009 (15.5 Ma MMU/DRU) = documented minority reading, NOT part of this estate.
- **Mechanism mixed, not either/or:** Morley ties 13–10.5 Ma to lithospheric stresses + underthrusting of Dangerous Grounds crust, gravity later. "Wedge-top, NOT plate boundary" is our model position, not Morley's words → C2/C3 downgraded to MODEL POSITION.
- **Slab breakoff + wedge-top diachroneity:** NOT in Morley 2023 → tagged SYNTHESIS/INT in the ontology (Morley 2024 + Pilia 2023 lineage, to verify).
- **Key quote (poster-grade, verbatim):** DRU, UIU and SRU are *"mixtures of conformable regions together with local unconformities rather than being simple widespread unconformities."*
- **Canopy correction (applied to `sabah_basin_strat.yaml`):** coalescence is a **UIU event** (short burst, <0.1 My); Stage IVC is the canopy-basin fill from UIU to SRU (~8.5–9 Ma); trigger = thrusting/inversion then stress relaxation. Compression triggers the canopy — not canopy-vs-compression.
- **Scope law:** NSPW is confined to **northern Sabah** (Block H type area); absent in southern Sabah where most deformation post-dates SRU. NSPW phase sequence must NOT be extrapolated basin-wide — Inboard Belt + East Baram need independent evidence. Scope flag written into the ontology.
- **Citation trap:** TWO Lunt 2022 papers (BGSM 74 = DRU age; JAES v.230 = BMU). Always cite "Lunt 2022 (BGSM 74)" for the age.

### B.2 Krebs count war — resolved by version discipline
THREE real Krebs texts: (1) AAPG/S&D Perth 2006, Sabah-only: >70 wells, ≥13 hiatuses (SBH10–110), 14 sequences [Copilot-witnessed, ndx_krebs.pdf]; (2) combined-title version "A New Chronosequence Stratigraphy for the Tertiary of Offshore Sabah and Sarawak": 100+ wells, ≥22 hiatuses (H05–H180), 23 chronosequences [agent-witnessed: https://exa.ai/library/publication/cg198v7r8ll]; (3) **version of record: Krebs 2011, BGSM 57, pp. 39–46, doi 10.7186/bgsm57201106** — Sabah >60 wells/9 type/15 hiatuses/16 chronosequences; Sarawak ~70/20/20 [agent-witnessed body + Copilot-confirmed authorship]. **Rule: poster and framework cite BGSM 57 only.** The exa.ai record answers the challenger's URL demand.

### B.3 Honest ledger recount (arbitrated 2026-10-06 evening)
| Status | Items |
|---|---|
| CLOSED by external evidence | #1 DRU age (Lunt 2022 BGSM 74 + Morley 2023 + estate), #5 Krebs counts (by version-of-record discipline), #6 wording |
| REFRAMED (stronger than closed) | #4 — Morley 2023 quote: named surfaces are mixtures, not simple regional unconformities |
| MODEL POSITION (not closed) | #2 (wedge-top vs plate boundary), #3 (slab breakoff, diachroneity = SYNTHESIS), #7 (corrected: coalescence at UIU) |
| PARTIAL | #13 — chimneys cut SRU in Block H (Morley observed); untested in Inboard Belt |
| OPEN | #8 Kimanis Bay-1, #9 Stage↔NN mapping, #10 thin biostrat, #11 imaging, #12 Brunei tie |

Count: **3 closed, 1 reframed, 3 model-positions, 1 partial, 5 open.** (Prior count of 6 conflated model positions with evidence-closed; challenger's count of 2 undercounts administrative closures.)

### B.4 Website truth-fixes (3 deploys, all live-verified)
1. `earth/kinabalu-cross-section.html` + `earth/kinabalu-basin/`: DRU/BMU 15.5–22 → DRU ~13–12 Ma · BMU ~24 Ma (after Lunt 2022). Receipt `20261006T070448457381112Z`.
2. "Meliau Orogeny" labels → SRU ~8.5 Ma dual-reading form; "post-MMU" → "post-DRU". Receipt `20261006T070754966603580Z`.
3. "MMU = DRU" conflation sentence → explicit distinction (DRU ~13–12, Sarawak MMU ~16, Lunt 2022 BGSM 74). Receipt `20261006T070943590069882Z`.

### B.5 MASTER TASK BOARD — Kinabalu Basin (compiled 2026-10-06, supersedes all partial lists)
**DONE today:** website ×3 receipts · citations locked (Krebs 2011 BGSM 57 doi; Krebs 2006 ×2 variants; Lunt 2022 BGSM 74 vs JAES; Balaguru & Hall 2009 #30084 quote; Kessler & Jong FOSI; PMU-2007 sentence witnessed) · ontology corrected (canopy→UIU, scope flag, synthesis tags) · poster kit v5 + Q&A cards · deep research + RealityPlan + Addenda A/B.
**OPEN — team/F13-side:** (T1) confirm Phase I numbers currency with Siti Arasy (deck May/June vintage); (T2) glossary: TAC, SEM, TriCipta FSM (+NFE confirm); (T3) Phase II scope decision: approve NSPW-north-only constraint + per-belt evidence plan.
**OPEN — 333-AGI (no new data):** (T4) read unread internal assets: `sabah_two_oceanics.yaml`, `nw_borneo_collision_system/basin_profile.yaml`, `northwest_borneo_trough/tectonic_history.md`, `dangerous_grounds/basin_profile.yaml`; (T5) build W1 `kinabalu_event_spine.yaml` v0 (surfaces + age ranges + provenance + aliases + NN anchors); (T6) fetch Krebs S&D PDF + BGSM 57 landing page → one-page citation note; (T7) fetch `bgsm74202205.pdf` body → dual-witness 13.77–11.7 + 3½–4 My sentences; (T8) fetch Earthdoc Balaguru full text (single-witnessed) + Morley 2024 ESR (diachroneity/slab-breakoff check); (T9) RealityPlan JSON v2 refresh (states + this board); (T10) FOSI masthead year check.
**OPEN — Phase II program (data-side):** (T11) DRU falsification drill — biostrat-bracketed wells from the 35+, date vs NN standard, test 15.5 vs 13–12 (falsifier for BOTH literature camps AND our own stack); (T12) keyline audit for 15.5-ghost picks; (T13) Stage↔NN crosswalk = event-spine row 1; (T14) biostrat quarantine + reworking flags (scar-bound); (T15) keylines as frozen hashed objects; (T16) Brunei tie: provenance + shelf-margin trajectory; (T17) RGT volumes + confidence maps; (T18) event-tagged restoration (multi-step, overprinting guard); (T19) HD GDE/RDE + missed-opportunity screen; (T20) Inboard seal test — chimneys vs SRU crosscutting (Block H already answered: they cut); (T21) Kimanis Bay-1 compound-unconformity check (biostrat/VR); (T22) per-belt evidence plan for Inboard + East Baram (scope law).
**Verification hygiene:** (T23) Copilot re-scan of redeployed pages: `https://arif-fazil.com/earth/kinabalu-cross-section.html` + `https://arif-fazil.com/earth/kinabalu-basin/`.
