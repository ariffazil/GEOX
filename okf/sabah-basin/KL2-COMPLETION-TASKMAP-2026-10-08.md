# KINABALU BASIN KL2 — COMPLETION TASK MAP

> **Compiled:** 2026-10-08 · **Compiler:** FI-003 (333-AGI lane, DECODER)
> **Sovereign:** Muhammad Arif bin Fazil (F13) — domain authority, upstream geoscience PETRONAS Carigali
> **Lane:** PUBLIC. Method + public literature + measured public data. **No PETRONAS-confidential data on this VPS** (`lane_governance.hard_wall`, irreversible-risk class).
> **Status:** NOT SEALED — working task map, H-class where noted.
> **Scope of this compile:** four external ENTERPRISE reports audited against first-party SOT, one F13 sovereign hypothesis registered, two figures forged, one live-data capability gap measured.

---

## 0 · What is now anchored to real Earth (L0, measured this session)

The **real B–B′ transect** was computed from verifiable coordinates, replacing the 600 km schematic that every prior figure used.

| Item | Value | Provenance |
|---|---|---|
| B (NW end, Dangerous Grounds) | 7.78°N, 113.00°E | chosen, on-line with both anchors |
| B′ (SE end, Sulu Sea) | 5.10°N, 118.60°E | chosen, on-line with both anchors |
| **Total length** | **687 km** | haversine, computed |
| Layang-Layang / Swallow Reef (7.372°N, 113.847°E) | **103.9 km** along track | MEASURED |
| Mt Kinabalu 4,095 m (6.075°N, 116.558°E) | **435.9 km** along track | MEASURED |
| Sandakan (5.84°N, 118.12°E) | **50.9 km OFF-transect**, projects to 603 km along track | MEASURED — not on B–B′ |

**Consequence:** every figure in this session placed Mt Kinabalu at ~413 km on a 600 km axis and drew "Sandakan → Sulu Sea" as an on-line station. Both are wrong. The real line is **87 km longer**, Kinabalu sits at **435.9 km**, and **Sandakan is 50.9 km off-line** — it must be labelled as such or removed.

*Correction recorded: an earlier hand estimate put Sandakan at ~118 km off-track. The computed value from the actual transect is **50.9 km**. The estimate was sent to Telegram before the computation was checked; the correction follows it. Same defect class as D11/D13 — a number presented before it was measured.*


**Not measured (and deliberately not invented):** along-track position of the Pekaka–Tepat high, the Sabah Trough axis, and the deformation front. GEOX SOT carries **no published coordinates** for any of them. They are SCHEMATIC until tied.

---

## 1 · BLOCKER-CLASS — GEOX has no working live path for potential-field or bathymetry data

This is the single highest-priority defect, because it blocks **the cheapest decisive test of F13's own hypothesis**.

| Source | Endpoint tested | Result |
|---|---|---|
| GEBCO 2026 OPeNDAP | `dap.ceda.ac.uk/.../GEBCO_2026_sub_ice.nc` | **DEAD** — `.dds` → HTTP 404. CEDA serves an nginx autoindex, **not** a DAP endpoint |
| ETOPO2022 THREDDS dodsC | `ngdc.noaa.gov/thredds/dodsC/globalDatasetScan/...` | **DEAD** — root → 400, tile → `NetCDF: file not found` |
| ETOPO2022 fileServer | same path via `/fileServer/` | **404** |
| Sandwell–Smith gravity (legacy CGI) | `topex.ucsd.edu/cgi-bin/get_data.cgi` | **HTTP 500** on POST, both `grav_32.1` and `grav_3` |
| NOAA CoastWatch ERDDAP | `coastwatch.pfeg.noaa.gov/erddap/` | **000** — connection fails (egress-restricted) |
| EMODnet WCS | `emodnet.ec.europa.eu/geoserver/ows` | **404** |
| OpenTopography API | `portal.opentopography.org/API/globaldem` | **400** — key/params required |

**Two distinct failure classes, do not collapse them:**
- **GEOX code defect:** `src/geox_core/io/gebco_fetcher.py` documents `GEOX_GEBCO_OFFLINE=0` → "attempts local cache or OPeNDAP subsetting" and stores `GEBCO_OPENDAP` URLs. Those URLs do not serve DAP. The documented live mode **cannot work**. Same class as `emag2_fetcher.py`, which the hypothesis ledger already records as "local EMAG2 = offline stub = UNKNOWN".
- **Host egress restriction:** ERDDAP returns 000 while other hosts return real HTTP codes, i.e. selective egress. Federation governed egress runs through A-FORGE `forge_fetch` (EgressPolicy.ts) — that lane was **not** used here and may be the actual working path.

**Task T0.1 — Repoint or retire the dead fetchers.** Probe via `forge_fetch`; if reachable, repoint `gebco_fetcher` + `emag2_fetcher` to working endpoints; if not, mark both `mode=offline_stub` **explicitly in the docstring** so no agent believes the live path exists. Per `OFFLINE_STUBS.md` rule 1, stub output must never be promoted to Earth truth.
**Task T0.2 — Wire a real gravity source.** Candidates in priority order: (a) WGM2012 regional netCDF subset via `forge_fetch`; (b) ICGEM spherical-harmonic model (XGM2019e / GECO) synthesised along B–B′ — GEOX already references `geox_icgem_models`; (c) current Sandwell–Smith v32+ REST endpoint.
**Task T0.3 — Close the registered gap.** `src/geox_mcp/tools/geophysics_studio_screen.py:44` states `"oceanic crust / density inversion not modelled"`. The **forward** half now exists (`trough_crust_thin_gravity.py`). The **inverse/observed-comparison** half needs T0.2 first.

---

## 2 · Defects found in the four ENTERPRISE reports (all first-party verified)

| # | Report claim | First-party verdict | File |
|---|---|---|---|
| D1 | DRU ≈ 15.5 Ma as "Strong Evidence" / "basin-scale invariant" | **REFUTED.** Spine: `age_range_ma: [11.7, 13.77]`, poster "~13–12 Ma". 15.5 is the Balaguru&Hall **"MMU/DRU conflation reading"**; ledger: "legacy 15 Ma was a **rounding artifact**"; decision rule: "**purge all 15.5-ghost picks from keylines**" | `kinabalu_event_spine.yaml` |
| D2 | SRU + DRU = basin-scale invariants | **REFUTED.** `sru_rule_2026_10_01`: "SRU is Kinabalu-only (upper plate): **not an invariant**"; DRU `scope: per-sub-basin unknown — THE testable question` | `kinabalu_basin/basin_profile.yaml` |
| D3 | Chart hardcoded DRU band 14.2–15.5 as the **structural boundary of every megasequence box** | **REFUTED + regression.** Report #2 retracted 15.5; the deliverable reinstated it. Also 14.2 fails the datum's own QC rule (`age_divergence_ma: 0.5`; NN5_base = **14.91**, divergence 0.71) | `nn_datum_borneo2023.yaml` |
| D4 | "Meliau / active folding" @ 3.5 Ma in the chart EVENTS column | **VIOLATION of a receipted ruling.** Spine:63 — `"Meliau" (coinage, unverified — **keep off artifacts**)`. IBS:150 ties it to SRU ~8.5 Ma dual-reading form, receipt `20261006T070754966603580Z`. Chart also displaced it ~5 My | `kinabalu_event_spine.yaml` |
| D5 | BMU "22–20 Ma", event @21 | **REFUTED.** `age_range_ma: [23, 24]`, `L_BMU = "~24 Ma"`; 22 = legacy. Spine falsifier: "BMU younger than 20 Ma … collapses the 2-phase pre-DRU stack" | `kinabalu_event_spine.yaml` |
| D6 | "Layang-Layang = substrate, NOT basin" (chart label, `INTERPRET strong`) | **CONTRADICTS registry + deletes a witness.** `basin_id: LAYANG_LAYANG_BASIN`, own 7-event clock ROU→IRU→BU→carbonate_top→**RU**, `collision_response_sign: SUBSIDE + DROWN` (opposite to Kinabalu's UPLIFT+ERODE). **RU is the lower-plate leg of LANGGAR** — the only both-plates surface family | `layang_layang_basin/basin_profile.yaml` |
| D7 | Chaotic cores drawn at 15.5–40 Ma ("Stage II–III?") | **MISPLACED ~5–25 My.** UIU ~10.5 Ma "mud-canopy coalescence burst (<0.1 My)"; "mud volcanoes, Rotan-type turbidite fairways (**13–10.5 Ma**)"; `block_H_fact`: "chimneys/pipes **CUT the SRU**" | `kinabalu_event_spine.yaml` |
| D8 | Cross-section defects: VE "4× vs 32×", granite "10–8 Ma", "DRU/BMU 15.5–22" on one line | **REFUTED — already correct in source.** `kinabalu_xs.py:22` → `L_GR="~7.85–7.22 Ma"`, `L_BMU="~24 Ma"`, `L_DRU="~13–12 Ma"` drawn separately; `:338` **computes** VE (renders 16.1×), so single-VE is structural | `kinabalu_xs.py` |
| D9 | "500 MMbbl OOIP" on the public page | **NOT FOUND.** Section footer says "**no volumetrics shown**". But see D10 | deployed bundle |
| D10 | *(new, found by probe)* public docs example `geox.stoiip({prospect:"KINABALU-N"})` → `p10/p50/p90_mmbbl` with `provenance: ["OBS: seismic_attr.kin_n"]` | **PROVENANCE DEFECT on a public surface.** `KINABALU-N` has **zero hits** in GEOX; `seismic_attr.kin_n` **does not exist**. An `OBS:` tag on a synthetic illustration (STOIIP pipeline is demoed on **Marmousi2**, a public synthetic) is provenance laundering. Confidentiality: LOW. F2 integrity: real | deployed bundle |
| D11 | Airy check "your claim fits the numbers" | **NON-DISCRIMINATING.** Two free parameters (fill S, reference crust) span **h ≈ −2 → 19 km**. See §4 | computed this session |
| D12 | Sidek et al. 2016 Moho 26–33 km cited as the evidence that refutes thin crust | **EVIDENCE-CLASS ERROR (F13 caught it).** It is a **gravity inversion** — non-unique, smoothing-regularised, therefore **structurally biased against** a narrow local Moho rise. DERIVED ≠ MEASURED: an inverse model cannot falsify a forward claim, only fail to support it | F13, 2026-10-07 |
| D13 | Copilot figure carried **three inconsistent values of h** | drawn geometry **6.9 km** · Airy with its own S=3.71 km **14.8 km** · panel label **"7–13 km"**. The label was fitted to the drawing, not computed from the model | computed this session |
| D14 | Sibling reports contradict each other on velocity | #1: Rotan–Buluh–Bunga Lili "velocity trends hampir sama" · #3: "the inboard is faster, as the TZ data showed". **Same TZ data, opposite conclusion** — and #3's depocentre claim depends on it | reports #1, #3 |

**Pattern across all four reports (the meta-finding):** every headline "eureka" was **already in GEOX SOT**.

| Report | Headline | First-party status |
|---|---|---|
| #1 | "Kinabalu Basin mungkin bukan sebuah basin" | `parent_system: NW_BORNEO_COLLISION_SYSTEM` — already a field |
| #2 | "surfaces still aren't stored as hypotheses" | spine stores them with `competing_ages`, `witnesses`, `falsifier`, `identity_ruling`, `status` |
| #3 | "it's a stack, not three basins" | `LAYANG_LAYANG_KINABALU_CONTRAST_NOTE.md`, 2026-07-07, verbatim |
| #4 | chart + matrix | built on D1–D7 |

**Root cause is architectural, not agent quality:** the membrane is **one-way**. `hard_wall` correctly keeps PETRONAS data off this VPS, but the enterprise agent also cannot read the GEOX spine — so it re-derives it and then contradicts it. The spine is **pre-cleared by its own header**: *"This file is METHOD + PUBLIC LITERATURE only. No PETRONAS-confidential data here, ever."* It has never been given to the enterprise side.

---

## 3 · Tasks to complete KL2

### P0 — blocking, cheap, reversible

| ID | Task | Why | Owner / lane | Falsifier / done-when |
|---|---|---|---|---|
| **T1** | **DRU identity — ANSWERED PROVISIONALLY 2026-10-08.** External ENTERPRISE review (F13-relayed under `FORGE`) rules **DRU = SABAR, provisional**, self-framed as 888 HOLD: *"a working hypothesis call, not an irreversible identity seal."* Recorded in the spine as `sabar_ruling_2026_10_08`, version bumped 0.1.0 → **0.2.0**. **Provenance class: REPORTED/INTERPRET — not MEASURED, not an F13 first-person ruling.** LANGGAR is **not** retired; it stays a live falsifiable competitor. Falsifier = **T12**. **Open consequence preserved, not smoothed:** if DRU = SABAR and SABAR is upper-plate-only, `nw_borneo/claims.json` loses LANGGAR's upper-plate leg → LANGGAR is no longer a both-plates family. That file **must be reconciled explicitly**. Competing position retained: `nw_borneo/basin_profile.yaml` maps SABAR = **UIU**. Contradiction UNRESOLVED pending T12. **Effect on D6:** RU (lower plate, Layang-Layang) is untouched → `LAYANG_LAYANG_BASIN` keeps entity status; the demotion stays rejected | external review → recorded by FI-003 | spine `sabar_ruling_2026_10_08` present, version 0.2.0, YAML valid |
| **T2** | **Transmit the spine to the enterprise side** — `kinabalu_event_spine.yaml` + `nn_datum_borneo2023.yaml` + `LAYANG_LAYANG_KINABALU_CONTRAST_NOTE.md` | Already public-lane by header. Prevents the next four reports re-deriving and contradicting SOT. Highest leverage per unit effort in this whole map | FI-003, reversible | next enterprise report cites spine ages (11.7–13.77 / 8.5–9 / 23–24) instead of 15.5 |
| **T3** | **Fix D10** — retag the public `geox.stoiip` docs example `OBS:` → synthetic/illustrative, drop unregistered `KINABALU-N` | Public surface + F2 provenance integrity | FI-003, reversible | redeployed bundle carries no `OBS:` tag pointing at a non-existent dataset |
| **T4** | **Re-render the 3-realm chart bound to the spine** | It is going to a CP review carrying D3/D4/D5/D6/D7. `kinabalu_xs.py:22` already proves the pattern: source labels from one place, compute VE | FI-003 | chart ages == spine ages, Meliau absent, Realm 1 = `LAYANG_LAYANG_BASIN` + coverage note |
| **T5** | **Resolve the NN-ladder off-by-one** — `nn_datum_borneo2023.yaml` (NN10_base=9.53, NN9_base=10.55, NN5_base=14.91) vs `basin_profile.yaml:60` relay (NN9=9.53, NN5=14.2) | Same 2023 framework, **9.53 attached to NN10 in one and NN9 in the other**. Decides whether "SRU ≈8.6 Base NN10A" and "9.53 top NN9" are the same surface | F13 + enterprise | one datum declared canonical; the other marked superseded |
| **T6** | **Capture SB5A** (Laletha, Workshop#1, 5 Oct) as SRU candidate H3 | Post-dates the **2026-10-01 Arif settlement** by four days, so it is genuinely new relative to SOT — the one real contribution in report #4 | FI-003, additive | `sru_rule` carries H1/H2/H3 with the settlement preserved, not reopened |

### P1 — the science that actually advances KL2

| ID | Task | Blocker | Falsifier |
|---|---|---|---|
| **T8a** | ~~Build the forward Bouguer model~~ **DONE 2026-10-08** — `geox/skills/subsurface/gravity/trough_crust_thin_gravity.py`; `h` **swept, not drawn**; offshore observation only; atoll flagged as a 2D artifact | none — executed, `py_compile` clean | ΔBouguer vs published Moho: **341** mGal @ h=5 km · **297** @ 7 · **253** @ 9 · **209** @ 11 · **166** @ 13 · **124** @ 15 · **62** @ 18 · **5** @ 21 · **−49** @ 24. Detection threshold now quantified |
| **T8b** | **Measure free-air / Bouguer along real B–B′** and compare against T8a (falsifier F1 of `TROUGH-CRUST-THIN`) | **T0.2** — no working gravity source | Thin crust → Bouguer HIGH over the trough axis. T8a says the signal is resolvable for **h ≤ ~18 km** (≥62 mGal), i.e. across nearly the whole Airy-allowed range |
| **T7** | **Constrain S** — total sediment thickness to acoustic basement under the trough axis | internal lane (KL2) | `h = REF − (2.924 + 0.4185·S)/0.2203`. Needed to test **whether isostasy alone explains the depth** — NOT to obtain `h`, which T8b measures directly |
| **T9** | **Depth-convert before any depocentre claim** — Rotan-1 + Barton-2 TZ | internal lane | checkshots exist (MALIGAN-1, PEKAKA-1, SUGUT, SOLISIP-1 measured; BARTON-2 in the DTS audit list; BULUH-1 flagged **pseudo-checkshot / SYNTHETIC**). If east-thickening survives → foredeep migration holds; if it vanishes → VOID |
| **T10** | **Settle D14 — the velocity sign** (inboard faster, or velocity trends the same?) | internal lane, TZ data | one first-party measurement ends a two-report contradiction that the depocentre claim depends on |
| **T11** | **Backstrip Tepat-1 + Pekaka-1** | internal lane; **method already parameterised** | `sabah_basin_strat.yaml → geox_basin_backstrip` already assigns **Tepat-1 = `suture`**, **Pekaka-1 / Nuri-1 / Falkon-1 = `layang_domain`**, with `timing_windows`. `sabah_two_oceanics.yaml` names Tepat-1 "**loading overprint on thermal**" — the well that separates flexural from thermal subsidence |
| **T12** | **Run the DRU per-well dating test** — `decision_rule_DRU_dating_test` | internal lane | THE decider, in SOT since 2026-10-06 and **never mentioned by any of the four reports**. Outcome 3 ("age varies between sub-basins") is the **framework result, not a failure** — Morley's own prediction that surfaces are composites |
| **T13** | **Build the timing gate** (report #2 item 2) | none — purely public-lane code | any "event Y caused surface X" claim must pass an age-overlap check or return VOID. Would have auto-killed granite→SRU (7.85–7.22 Ma cannot cause an 8.6/9.53 Ma surface). **Also needs an identity-uniqueness check** — a timing gate does not catch T1 |

### P2 — do NOT build (already exists)

| Claimed "fix" | Reality |
|---|---|
| Surface Registry | **EXISTS** — spine carries name/aliases/`age_range_ma`/event_class/citation/witnesses/`falsifier`/status/`competing_ages`/`identity_ruling`/scope; `nn_datum` is the timescale layer with `ladder_is_continuous: true`. Missing only: per-surface *seismic criterion* field + GTS2012/GTS2020 tag |
| Falsifier per hypothesis | **ALREADY THE NORM** — `falsifier` in spine, 2× in each `claims.json`, `TEPAT-PEKAKA-MODEL-C` has falsifier conditions + `data_wall`, LANGGAR has a registered falsifier |
| Public/internal membrane | **EXISTS AS GOVERNANCE** — `lane_governance.hard_wall`. Not yet a lint; D10 is an open case against it |

---

## 4 · The `TROUGH-CRUST-THIN` hypothesis — current state

**Registered:** `okf/sabah-basin/hypothesis_ledger.yaml` → `TROUGH-CRUST-THIN`, `prior: 0.35`, 6 predictions, 5 for, 4 against, `status: open, testable, H-class — NOT SEALED`.

**F13's claim (verbatim):** *"there is extension ridge along sabah trough (almost oceanic crust in physics nature) so thats why the crust terbenam masuk ke dalam."*

**Rename applied** (name claims only what is measured): RIDGE ≠ THIN-CRUST. A ridge predicts axial high + hummocky basement + linear symmetric magnetics; KL2 shows **tilted half-grabens** under Pekaka → thinned continental / OCT, not an active ridge. So: **thin crust OPEN, active ridge HOLD** (that one stays `TEPAT-PEKAKA-MODEL-C`, `verdict_class: UNSUPPORTED`, `prior: 0.15`). Model C's verdict does **not** transfer — a dated magmatic claim and a crustal-constitution claim are different objects.

**Two findings that rehabilitate it:**
1. **Sidek's Moho is an inverse model** (D12) — admissible as "fails to support", never as "falsifies".
2. **The magnetics argument is non-diagnostic.** "No magnetic anomalies <~15.5 Ma" rules out magnetised oceanic layer 2A, but **serpentinisation destroys magnetite** — an exhumed serpentinised mantle floor is also magnetically quiet. It separates *oceanic* from *not-oceanic*; it does **not** separate *continental* from *OCT*.

**Two findings that constrain it:**
1. **True oceanic crust is excluded by bathymetry.** Parsons–Sclater puts 16–30 Ma oceanic crust at 3.9–4.5 km; the observed trough is **2.9 km**. The live end-member is **exhumed serpentinised mantle / OCT**, which is buoyant (ρ≈2600 vs 3300) and therefore sits *shallower* than mature oceanic crust — consistent with "almost oceanic in physics nature" without being oceanic.
2. **The Airy check is not evidence** (D11, D13). Sensitivity sweep, independently recomputed:

| S (km fill) | ref 30 km | ref 32 km | ref 35 km | ref 38 km |
|---|---|---|---|---|
| 3.0 | 11.1 | 13.1 | 16.1 | 19.1 |
| 3.7 | 9.8 | 11.8 | 14.8 | 17.8 |
| 5.0 | 7.3 | 9.3 | 12.3 | 15.3 |
| 8.0 | 1.6 | 3.6 | 6.6 | 9.6 |
| 10.0 | −2.2 | −0.2 | 2.8 | 5.8 |

`h = REF − (2.9 + 0.4185·S) / 0.2203`. Spans **−2 → 19 km**. It is a plausibility screen, not a discriminator.

**⇒ ORDERING CORRECTED 2026-10-08 (v1 of this map had it inverted, and the external review endorsed the inversion).** The original claim was *T7 (constrain S) outranks T8 (gravity)*, reasoning `h = f(S)`. That holds **only for the Airy route**. Executing T8a showed the gravity route constrains `h` **directly, without `S`** — and once `h` is measured, `S` becomes whatever isostatic balance requires. So **T8b constrains T7, not the reverse.** They answer different questions: gravity *measures* `h`; `S` tests whether isostasy **alone** explains the depth. Measured ΔBouguer vs published Moho: **341** mGal @ h=5 km · 297 @ 7 · 253 @ 9 · 209 @ 11 · 166 @ 13 · 124 @ 15 · **62 @ 18** · 5 @ 21 · −49 @ 24 → resolvable for **h ≤ ~18 km**, i.e. across nearly the whole Airy-allowed range.

**Scope limit recorded in the ledger (`isostasy_scope_limit`):** isostasy creates **space** for sediment; it does not drive thrusting. NW vergence still requires the SE load (NSPW advance). This hypothesis explains trough **depth and Te** — it must not be sold as replacing flexure.

**SOT already supports the mechanism vocabulary:** `sabah_basin_strat.yaml` — NSPW is "the **mechanical spine** connecting deep tectonic forcing to shallow stratigraphy"; Sabah Trough is "**NOT a subduction trench** — flexural depression caused by NSPW mass loading on **hyperextended** Dangerous Grounds crust". `IBS-KINABALU-DEEP-RESEARCH-2026-10-06.md:55` — "**Setap mobile-shale decollement (Morley et al. 2003, JSG)**: same detachment system runs both sides". F13's "compression **ditampan** oleh NSPW dan shale base — Setap shale" is that mechanism, in his own words.

**Against, from F13's own earlier work:** `sabah_two_oceanics.yaml` (F13-authored, SABAH_EUREKA_LEDGER v1.0, 2026-07-10) — Domain B = rifted **CONTINENTAL**, "Mesozoic continental basement", `initial_subsidence_km: 2.0`. This is the sovereign contradicting his own July eureka. Legitimate, and it is recorded rather than smoothed.

**Also genuinely under-resolved in SOT:** `sabah_trough/basin_profile.yaml` `crust_origin` says "Same Dangerous Grounds **extended crust** … bent downward" — it never states *how far* extension went. The OCT end-member is a real gap, not a settled matter.

---

## 5 · Artifacts forged this session (all public lane, none sealed)

| Artifact | Path | Note |
|---|---|---|
| Hypothesis cross-section | `geox/skills/subsurface/section/pekaka_layang_ext_xs.py` → `output/pekaka_layang_ext_xs_{dark,light}.{png,svg}` | Spine-bound ages parsed at render time (`DRU 11.7–13.77 · SRU 8.5–9 · BMU 23–24 · UIU ~10.5 · collision 23–24 · NSPW 500×150 km`). Draws **both** Moho solutions; Sidek 26–33 km marked OFF-PANEL rather than faked in. VE **computed** = 14.2× |
| Forward Bouguer model | `geox/skills/subsurface/gravity/trough_crust_thin_gravity.py` | h **swept**, not drawn. Offshore observation only (onshore excluded, not faked — a near-field cell singularity produced a spurious +385 mGal at Mt Kinabalu in the Copilot v1). Atoll flagged as a **2D artifact**. Includes the Airy sensitivity panel |
| Real transect fetch | `scripts/fetch_kl2_realdata.py` → `data/kl2_realdata/{transect.npz,provenance.json}` | 687 km, real anchors. `data_mode` recorded per `OFFLINE_STUBS.md` rule 2; bathymetry + gravity honestly **UNMEASURED**, never substituted with a drawn profile |
| Ledger entry | `okf/sabah-basin/hypothesis_ledger.yaml` → `TROUGH-CRUST-THIN` | YAML validated: 6 models, `kill_rules` intact |

**Two defects I shipped and then closed myself** (recorded, not hidden): the first render printed `UNRESOLVED` for values that exist — `_ont` path was wrong (`/basin`, not top level) and `_label` double-tilded UIU. Both fixed; verified in the render log.

---

## 6 · The binary — answered provisionally 2026-10-08

> **Is DRU the upper-plate expression of LANGGAR, or is DRU = SABAR?**

Blocks: T1 → the spine `identity_ruling` → T13's uniqueness check → whether D6's deletion of Layang-Layang destroys the lower-plate witness → whether a both-plates surface exists at all → the outward-correlation rule ("from Kinabalu outward, never inward").

**ANSWERED PROVISIONALLY 2026-10-08 → `DRU = SABAR`**, recorded as `sabar_ruling_2026_10_08`, spine v0.2.0. Provenance REPORTED/INTERPRET (external review, F13-relayed), **not** an F13 first-person ruling and **not** MEASURED. LANGGAR stays live; falsifier = T12; `nw_borneo/claims.json` needs explicit reconciliation (T14 below).

---

*DITEMPA BUKAN DIBERI* · REALITY > EVERYTHING · UNKNOWN is a valid result

---

## 7 · Addenda from the 2026-10-08 external review (adopted verbatim where specified)

**A. Figure wording — exact distinctions required** (prevents raster samples being read as point observations):
- "GEBCO_2019 15″ cell elevation, sampled along B–B′."
- "Maximum sampled trough depth: −2,924 m at chainage 191.3 km."
- "Trough-axis position is line-specific, not a mapped regional-axis solution."
- "Mount Kinabalu: +3,945 m sampled GEBCO cell; Low's Peak geodetic elevation: 4,095.2 m."
- "Layang-Layang value is a coarse-cell terrain value; not reef crest, island elevation, or water-depth observation."

Applied in `scripts/kl2_reality_calibration.py`.

**B. Evidence hierarchy (adopted):**
1. **Measured** — line geometry, GEBCO sampled elevation/depth, along-line trough minimum.
2. **Derived** — water-depth input `dw`, line-specific source-to-trough separation (87 km).
3. **Unknown** — `S`, Bouguer/free-air response, basement architecture, `Te`, Moho, OCT vs thinned continental.
4. **Decision gate — CORRECTED 2026-10-08.** This addendum first recorded "T7 before T8" on the reviewer's reasoning that `h` is highly sensitive to `S`. True for the **Airy** route only. T8a (forward model, now executed) shows gravity pins `h` directly, so **T8b before T7**. `S` stays decisive for a *different* question — whether isostasy alone explains the depth. Reviewer and FI-003 both made the original error; recorded, not silently edited.

The 165→87 km correction changes the *spatial input* to any flexural/load–moat model by ~1.9× and upgrades the
question from schematic plausibility to testable forward modelling. It does **not** by itself determine `Te`,
crustal thickness, load geometry, `S`, or crustal origin. Recorded so nobody re-reads it as support.

**C. Sandakan:** confirmed **50.9 km off-transect** (the earlier ~118 km was a hand estimate, retracted in §0).
Label `OFF_TRANSECT` — applied — or remove entirely.

**D. New task T14 (P0):** reconcile `nw_borneo_collision_system/claims.json` against `sabar_ruling_2026_10_08`.
If DRU = SABAR, LANGGAR's upper-plate leg is unassigned. Either re-identify it or restate LANGGAR as a
two-expression family. Do not leave the two files contradicting.

**E. Witness status:** the bathymetry was probed first-party (MEASURED, L0) **and** independently audited by the
external review, which passed every value including the −2,924 m / 191.3 km minimum and the coarse-grid caveats.
On the ladder DECLARED → OBSERVED → MEASURED → **WITNESSED** → FALSIFIED → ATTESTED, this claim now reaches
WITNESSED. It is **not** ATTESTED — nothing here is sealed.
