---
id: geox-seismic-interpretation
name: GEOX Seismic Interpretation Lane
version: 1.0.0
description: GEOX seismic interpretation lane discipline — from raw SEG-Y to interpretation bundle with physics gates. USE WHEN: 'interpret this seismic line', 'pick horizons', 'find stratigraphic traps', 'AVO analysis', 'segy slice'. Covers: geox_seismic_ingest (inspect/export) → geox_seismic_interpret (horizon_contrast, fault_sticks, interpret_bundle with >=3 hypotheses, rsi_pipeline) → geox_seismic_compute (avo_forward Zoeppritz/Shuey/LMR/Castagna) → geox_contrast_metabolize (ISOLATE→MEASURE→CLASSIFY). Iron rules: GEOX proposes geometry and physics-gates it; preferred_hypothesis is ALWAYS null from GEOX (local max = QUALIFIED_CANDIDATE; arifOS seals); every interpretation must carry >=3 competing stratigraphic hypotheses; gates return PASS|WARN|KILL|UNMEASURED + receipt_hash.
owner: 333-AGI
risk_tier: low
floor_scope: [F1, F2, F7, F11]
autonomy_tier: T1
organ_domain: geox
forged: 2026-09-04
---

# GEOX Seismic Interpretation Lane

GEOX seismic interpretation lane discipline — from raw SEG-Y to interpretation bundle with physics gates. USE WHEN: 'interpret this seismic line', 'pick horizons', 'find stratigraphic traps', 'AVO analysis', 'segy slice'. Covers: geox_seismic_ingest (inspect/export) → geox_seismic_interpret (horizon_contrast, fault_sticks, interpret_bundle with >=3 hypotheses, rsi_pipeline) → geox_seismic_compute (avo_forward Zoeppritz/Shuey/LMR/Castagna) → geox_contrast_metabolize (ISOLATE→MEASURE→CLASSIFY). Iron rules: GEOX proposes geometry and physics-gates it; preferred_hypothesis is ALWAYS null from GEOX (local max = QUALIFIED_CANDIDATE; arifOS seals); every interpretation must carry >=3 competing stratigraphic hypotheses; gates return PASS|WARN|KILL|UNMEASURED + receipt_hash.

## Provenance

Forged 2026-09-04 by 333-AGI (session SEAL-83defc585b5a4296) from live organ tool surfaces + FEDERATION_SKILL_PROFILE gap analysis. Source of truth: the organ MCP surface itself — when skill and tool surface disagree, the tool surface wins and this skill must be revised.
