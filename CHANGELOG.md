# Changelog — GEOX (Earth Sciences)

All notable changes to the GEOX organ.

## [Unreleased]

### Added — 2026-10-03 (docs/readme-harden · ARIFOS::GEOX::README_HARDEN::v1)
- README rebuilt to generated-truth: status block (`scripts/generate_readme_status.py`, host-side snapshot — canonical 27 / live 27 / drift 0 / runtime-vs-main commits), inventory block generated from `registry.py` (CI-gated), badge URL now self-heals with the count
- Contradiction fixes: seal-mode wording (`geox_claim(mode='seal')` = local claim-ledger bookkeeping, never a constitutional SEAL), precise writes statement (local workspace only, never federation DBs), precise resource-estimates statement (advisory DER/SPEC ranges, never booked resources), single epistemic-label mapping table incl. `UNKNOWN`
- New sections: Images & multimodal (`geox_observe` live, chat local-only pending Gate 6), physics-limits table, MCP usage (auth position: `P3_AUTH_LITE` OAuth 2.1/DPoP + static client-ID registry; client JSON + real example envelope), data provenance & licence, BSL-1.1 parameters inline, redeploy pointer with the two-check verification rule
- `README_HARDEN` — quickstart dev port 18081 (8081 is the production organ); infra paths/ports moved to DEPLOYMENT.md; "Recent changes" moved here
- `reports/readme_harden/2026-10-03_confidentiality_scan.md` — basin-pack provenance scan, REPORT ONLY: **CRITICAL** — internal well-evaluation data (WCR Rotan-1 TD/TVDSS, formation picks, reservoir top, GWC depth, PDA biostrat values, "deck 3133"/NOC Carigali provenance) present in public repo; sovereign decision pending, nothing deleted

### Changed — 2026-10-03 (earth-witness lanes, feat branches)
- `feat/earth-witness-v1`: `geox_observe` wired as 27th canonical tool (Earth Witness v1, I1–I9 in code, contradiction auditor, deterministic-mock vision backend with Gemini adapter); deployed — live 27/27 parity green
- `feat/earth-witness-chat`: EarthBench (7/7, forbidden-claim rate 0), Earth Witness chat proxy + mobile UI (127.0.0.1 only, EXIF/GPS strip, rate limit → HOLD, forbidden-claim scan → HOLD), 8/8 §9 acceptance tests — **Gate 6 Class-B package awaiting sovereign APPROVE**, not exposed
- RT1 recovery derivation + surface-drift CI gate (Lane 333d work, sealed 2026-10-03); `09-boundary-ratchet.yml` merge-marker corruption fixed (was silently dead)

### Changed
- Dropped dead `master` branch triggers — fleet unified to `main`
- SOUL linkage updated

### Fixed
- MCP protocol 2025-03-26 acceptance (TS SDK/Kimi default) in version gate

## [2026.07.13] — Earth OS Release

### Added
- Constitutional physics stack documentation
- Seismic structural validation gates (G0–G10)
- Petrophysics blueprint
- GLOF cascade architecture diagrams

### Changed
- Post-merge drift audit completed
- MCP apps readiness matrix

## [2026.05.01] — Initial Federation Release

### Added
- Initial GEOX organ
- MCP tool reference
- Earth witness documentation
- Geohazard assessment capabilities
