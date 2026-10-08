# GEOX Confidentiality Scan — basin data packs (REPORT ONLY)

**Date:** 2026-10-03 · **Auditor:** FI-008 (kimi-code/k3) under `ARIFOS::GEOX::README_HARDEN::v1`
**Trigger:** README hardening — repo `github.com/ariffazil/GEOX` is **PUBLIC** (verified HTTP 200, unauthenticated, 2026-10-03)
**Scope:** `resources/` tree (66 files across basins/, biostrat/, ontology/, capabilities/) + README references
**Method:** pattern scan (`internal`, `carigali`, `petronas`, an internal deck name *(removed 2026-10-08)*, `enterprise`, `top pay`, `rotan`, well-evaluation terms) + manual read of every flagged file
**Authority to act:** removal/redaction is an F13 sovereign decision — this report flags only

> **OUTCOME 2026-10-08 (F13 SOVEREIGN DECISION): PURGE EXECUTED.**
> The sovereign ruled: *"purge and maintain AMANAH — the value is just a number, but the flow and intelligence and synthesis is ours."* All well-file-derived values and internal-artifact provenance below were **redacted from this report, purged from the tree, scrubbed from git history, and force-pushed** on 2026-10-08. Wells de-identified (DW-A, INB-1..n); identity ledger and originals held in a private store outside all repos. The geological reasoning survives in the packs without the numbers.

## Verdict (2026-10-03, as found)

**CRITICAL: internal well-evaluation data was present in a public repo.** The Kinabalu / NW Borneo packs contained values only obtainable from internal PETRONAS-type well files: a Well Completion Report reference, formation-top depth picks in metres MD, a **gas-water contact depth**, reservoir-top depth, and biostrat event values tied to a de-identified well (DW-A). *(All such values removed 2026-10-08.)*

## CRITICAL — internal well evaluation data (values REDACTED 2026-10-08; structure retained)

| Where | What | Evidence |
|---|---|---|
| `resources/basins/kinabalu_basin/claims.json` | **DW-A TD / TVDSS / seabed values** — cited to an internal WCR via a named internal workbook relay *(artifact names removed 2026-10-08)* | WCR = Well Completion Report (internal document) |
| same | Full formation picks in metres MD incl. **top reservoir and GWC/flat-event depths**, interpreter intra-stage tops *(all depths removed 2026-10-08)* | GWC + reservoir top + interpreter picks = internal evaluation-of-record data |
| `resources/basins/nw_borneo_collision_system/basin_profile.yaml` | "candidate pick DW-A NN11/NN10 boundary **[depth pick relative to top pay — REDACTED]**" | depth pick relative to **top pay** in a named well |
| same + `kinabalu_basin/basin_profile.yaml` + `tectonic_history.md` | SRU age candidates incl. **an internal-PDA value [REDACTED]** with the file's own label "**internal values conflict**" | biostrat values from an internal PDA (well age-depth product) |
| `resources/basins/kinabalu_basin/basin_profile.yaml` | Source cited: an internal corporate exploration page *(de-referenced 2026-10-08)* | internal corporate page as evidence source |
| `resources/basins/nw_borneo_collision_system/basin_profile.yaml` + `claims.json` | Provenance header: "**internal deck proxy relay**" *(deck name removed 2026-10-08)* | relay from an internal presentation deck; fingerprints were in the repo |
| `resources/basins/malay_basin/claims.json` | Source: "**internal operator regional studies**" *(de-referenced 2026-10-08)* | internal operator regional studies as claim source |

## HIGH — unverifiable relay provenance (content may be clean, origin is not auditable)

| Where | What |
|---|---|
| `claims.json` across `kinabalu_basin` (17 hits), `nw_borneo_collision_system`, `sabah_trough`, `layang_layang_basin`, `dangerous_grounds`, `northwest_borneo_trough` | "Arif ENTERPRISE relay 2026-09-30" as the source of multiple claims — relay class, "enterprise files not locally readable on KVM8" (own admission in kinabalu claims) — **retained 2026-10-08: this is our own synthesis flow, not operator data** |
| `kinabalu_basin/claims.json` (sys_clm_6) | Enterprise-AI analysis 2026-09-30 + invented event names (BANGKIT, GEMPA) marked "names INVENTED, pending F13" *(tool name de-referenced 2026-10-08)* |

## CLEAN (public, citable)

Levell (1987) Sabah unconformities; Clift et al. (2008); Hinz (1985); IODP Exp 349; Menier et al. (2017); Cornwell et al. (2025); Pilia et al. (2023); Yu et al. (2021); Shi et al. (2020); published nomenclature (DRU/SRU/LIU/UIU, Crocker Formation); MTJDA A-18-01 PSC award (public ceremony, Gastech 2026); all `biostrat/` zone charts; all Earth Witness fixtures and EarthBench cases (synthetic, `I8`). Rotan as a field name where cited to Morley et al. 2023 (public paper names it) — retained in Morley-cited contexts only.

## Resolution (was "Options for the sovereign"; decision recorded above)

1. ~~Redact to public ranges~~ **← CHOSEN and extended: redact + de-identify + full history scrub (2026-10-08)**
2. ~~Make the repo private~~ — not taken
3. ~~Leave as-is with recorded risk acceptance~~ — not taken

## Related non-scan risk (flagged, UNKNOWN — outside my authority)

The BSL-1.1 grants a *commercial* production-licensing right held personally (licensor email is a Gmail address). Whether marketing commercial licences for subsurface tooling conflicts with the licensor's employment terms is an **employment/IP question this scan cannot answer** — flagged per the advisor's note; for the licensor to resolve.

— END OF REPORT. Executed purge: tree + git history + force-push, 2026-10-08 (receipt in AAA reports).
