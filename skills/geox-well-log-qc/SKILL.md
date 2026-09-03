---
id: geox-well-log-qc
name: GEOX Well Log QC Lane
version: 1.0.0
description: Well log ingestion and QC lane — LAS/DST/deviation/tops into interpretable curves. USE WHEN: 'load LAS', 'QC well logs', 'depth monotonicity', 'null fraction', 'petrophysical interpretation'. Covers: geox_well_ingest (auto-detect, standardize_curves, normalize_units, qc_strict) → geox_well_qc (depth monotonicity, null %, physical range) → geox_well (view/desk hydrate tracks with petrophysics) → geox_petrophysics (Vsh/porosity/Sw/permeability/net-pay, canon9 profiles, lem_inference). Iron rules: QC before interpretation always; qc_strict=True default; never interpret logs that fail physical range checks; label interpretations INTERPRETATION truth-class.
owner: 333-AGI
risk_tier: low
floor_scope: [F1, F2, F7, F11]
autonomy_tier: T1
organ_domain: geox
forged: 2026-09-04
---

# GEOX Well Log QC Lane

Well log ingestion and QC lane — LAS/DST/deviation/tops into interpretable curves. USE WHEN: 'load LAS', 'QC well logs', 'depth monotonicity', 'null fraction', 'petrophysical interpretation'. Covers: geox_well_ingest (auto-detect, standardize_curves, normalize_units, qc_strict) → geox_well_qc (depth monotonicity, null %, physical range) → geox_well (view/desk hydrate tracks with petrophysics) → geox_petrophysics (Vsh/porosity/Sw/permeability/net-pay, canon9 profiles, lem_inference). Iron rules: QC before interpretation always; qc_strict=True default; never interpret logs that fail physical range checks; label interpretations INTERPRETATION truth-class.

## Provenance

Forged 2026-09-04 by 333-AGI (session SEAL-83defc585b5a4296) from live organ tool surfaces + FEDERATION_SKILL_PROFILE gap analysis. Source of truth: the organ MCP surface itself — when skill and tool surface disagree, the tool surface wins and this skill must be revised.
