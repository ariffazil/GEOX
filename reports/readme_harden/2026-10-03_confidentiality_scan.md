# GEOX Confidentiality Scan — basin data packs (REPORT ONLY, nothing deleted)

**Date:** 2026-10-03 · **Auditor:** FI-008 (kimi-code/k3) under `ARIFOS::GEOX::README_HARDEN::v1`
**Trigger:** README hardening — repo `github.com/ariffazil/GEOX` is **PUBLIC** (verified HTTP 200, unauthenticated, 2026-10-03)
**Scope:** `resources/` tree (66 files across basins/, biostrat/, ontology/, capabilities/) + README references
**Method:** pattern scan (`internal`, `carigali`, `petronas`, `deck 3`, `enterprise`, `top pay`, `rotan`, well-evaluation terms) + manual read of every flagged file
**Authority to act:** removal/redaction is an F13 sovereign decision — this report flags only

## Verdict

**CRITICAL: internal well-evaluation data is present in a public repo.** The Kinabalu / NW Borneo packs contain values that are only obtainable from internal PETRONAS-type well files: a Well Completion Report reference, formation-top depth picks in metres MD, a **gas-water contact depth**, reservoir-top depth, and biostrat event values tied to the Rotan-1 well.

## CRITICAL — internal well evaluation data (public literature cannot contain these)

| Where | What | Evidence |
|---|---|---|
| `resources/basins/kinabalu_basin/claims.json` (~line 76–99) | **Rotan-1 TD 2141 MD / 2114.7 m TVDSS, seabed 1149.4 m** — cited to "**WCR Rotan-1** via `KL2_Wells_Data_Compilation.xlsx` (WELL_HEADERS / FORMATION_TOPS, Geoservice)" | WCR = Well Completion Report (internal document); named xlsx compilation |
| same, line 92 | Full formation picks in metres MD: IVG 1144–1836, NN11 1836.4–1993.9, NN10 →TD, **"top reservoir 1988.7 MD", "GWC/flat event 2071.1–2072.1 MD (2045.8 TVDSS)"**, Landmark IVD/IVC tops | GWC + reservoir top + interpreter picks = internal evaluation-of-record data |
| `resources/basins/nw_borneo_collision_system/basin_profile.yaml` (line 116) | "candidate pick Rotan-1 NN11/NN10 boundary **~1994 m MD, ~5 m below top pay**" | depth pick relative to **top pay** in a named well |
| same file (108, 171) + `kinabalu_basin/basin_profile.yaml` (30) + `tectonic_history.md` (74–77) | SRU age values "**9.53 Ma (top NN9), ~8.6 Ma (base NN10A), 8.50 Ma (Rotan PDA)**" with the file's own label "**internal values conflict**" | biostrat values from an internal PDA (well age-depth product) |
| `resources/basins/kinabalu_basin/basin_profile.yaml` (7, 61) | Source cited: "**PETRONAS MPM exploration page 2026-09-30** (Kinabalu-area wells usage)" | internal corporate page as evidence source |
| `resources/basins/nw_borneo_collision_system/basin_profile.yaml` (line 2) + `claims.json` | Provenance header: "**deck 3133 proxy relay**" | suggests relay from an internal presentation deck; underlying deck not in repo but its fingerprints are (values above) |
| `resources/basins/malay_basin/claims.json` (line 24 + 3 more hits) | Source: "**NOC Carigali regional studies**" | internal operator regional studies as claim source |

## HIGH — unverifiable relay provenance (content may be clean, origin is not auditable)

| Where | What |
|---|---|
| `claims.json` across `kinabalu_basin` (17 hits), `nw_borneo_collision_system`, `sabah_trough`, `layang_layang_basin`, `dangerous_grounds`, `northwest_borneo_trough` | "Arif ENTERPRISE relay 2026-09-30" as the source of multiple claims — relay class, "enterprise files not locally readable on KVM8" (own admission in kinabalu claims) |
| `kinabalu_basin/claims.json` (sys_clm_6) | "BizChat enterprise analysis 2026-09-30" + invented event names (BANGKIT, GEMPA) marked "names INVENTED, pending F13" |

## CLEAN (public, citable)

Levell (1987) Sabah unconformities; Clift et al. (2008); Hinz (1985); IODP Exp 349; Menier et al. (2017); Cornwell et al. (2025); Pilia et al. (2023); Yu et al. (2021); Shi et al. (2020); published nomenclature (DRU/SRU/LIU/UIU, Crocker Formation); MTJDA A-18-01 PSC award (public ceremony, Gastech 2026); all `biostrat/` zone charts; all Earth Witness fixtures and EarthBench cases (synthetic, `I8`).

## Per-file pattern-hit counts (scan footprint)

```
17  basins/kinabalu_basin/claims.json          7  basins/nw_borneo_collision_system/basin_profile.yaml
10  basins/kinabalu_basin/tectonic_history.md  3  basins/nw_borneo_collision_system/claims.json
 8  ontology/sabah_basin_strat.yaml            7  basins/kinabalu_basin/basin_profile.yaml
 4  capabilities/geox_capabilities.json        4  basins/malay_basin/claims.json
 4  basins/sabah_trough/claims.json            4  basins/layang_layang_basin/claims.json
(+ 1–2 hits each in sabah_basin, northwest_borneo_trough, dangerous_grounds, sabah_trough history)
```
(`capabilities/geox_capabilities.json` hits are the tool inventory text, not well data — sampled clean.)

## Options for the sovereign (NONE executed)

1. **Redact to public ranges** — replace flagged values (TD, GWC, picks, PDA ages) with published-literature ranges (Levell 1987 gives SRU ~9–8 Ma publicly), keep the geological reasoning, drop the internal citations. Preserves the science, removes the exposure. *Recommended if the repo stays public.*
2. **Make the repo private** (or move `resources/basins/` to a private companion repo) — fastest, but kills the public-organ value and BSL public-licensing posture.
3. **Leave as-is** — requires an explicit, recorded F13 risk acceptance that Rotan-1 evaluation data (TD, reservoir top, GWC, picks) is public.

## Related non-scan risk (flagged, UNKNOWN — outside my authority)

The BSL-1.1 grants a *commercial* production-licensing right held personally (licensor email is a Gmail address). Whether marketing commercial licences for subsurface tooling conflicts with the licensor's employment terms is an **employment/IP question this scan cannot answer** — flagged per the advisor's note; for the licensor to resolve.

— END OF REPORT. No file in `resources/` was modified.
