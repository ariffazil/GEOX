# GEOX Biostratigraphy Governance Rulings — B1–B8
# DITEMPA BUKAN DIBERI — Forged, Not Given
# Phase 2.5 (2026-07-03): Codified per Arif sovereign spec.
#
# These 8 rulings are constitutional guardrails for every biostratigraphic
# claim processed by the GEOX Earth Intelligence organ. They enforce the
# biostrat-as-calibration doctrine: fossils constrain, they do not dictate.

rulings:

  B1:
    name: "Observation before age"
    rule: "Fossil/taxon extraction is not an age claim. Parse first, calibrate second. Never collapse observation into interpretation."
    applies_to: [geox_biostrat_parse]
    enforcement: "Tool-level: parse output carries evidence_tag, not age claim."
    violation: "Reporting 'Sample is Middle Miocene' without citing which fossils, which scheme, and which calibration."

  B2:
    name: "Zone before Ma"
    rule: "Biozone name must be preserved as primary key before converting to numeric age. NN5 → 'NN5 (Martini 1971)' → 13.65–14.91 Ma. Never NN5 → 14 Ma directly."
    applies_to: [geox_biostrat_nn_age, geox_deep_time_state]
    enforcement: "geox_biostrat_nn_age returns zone + scheme + age bracket, never raw age."
    violation: "Converting biozone directly to absolute age without preserving the zone name and scheme."

  B3:
    name: "Calibration explicit"
    rule: "Every numeric age derived from a biozone must cite its calibration table and version (e.g. GPTS2020, GTS2012, Nannotax3 lookup, operator-specific local table)."
    applies_to: [geox_biostrat_nn_age, geox_deep_time_state]
    enforcement: "calibration field mandatory in nn_age output. not_a_radiometric_age always true."
    violation: "Reporting 'NN5 = 14 Ma' without stating which calibration table was used."

  B4:
    name: "Facies veto"
    rule: "Age interpretation must not violate depositional environment without documented explanation. Open marine nannofossil zone inside freshwater coal requires explicit reworking, thin marine incursion, or facies reinterpretation evidence."
    applies_to: [geox_biostrat_ruling_check]
    enforcement: "Facies veto rules in ruling_check: 5 contradiction patterns across lithology × environment × biozone implication."
    violation: "Accepting a deep marine biozone age in clearly non-marine facies without explanation."

  B5:
    name: "Reworking/caving warning"
    rule: "Out-of-order fossils, mixed assemblages, or abraded specimens trigger contamination/reworking/caving hypotheses. Age fidelity is automatically reduced."
    applies_to: [geox_biostrat_ruling_check, geox_biostrat_parse]
    enforcement: "Reworking/caving keywords detected → auto-tag warnings. Ruling downgraded to WEAK_PASS."
    violation: "Using a fossil occurrence with known reworking risk as an age tie without flagging the uncertainty."

  B6:
    name: "Multi-discipline convergence"
    rule: "Palynology, calcareous nannofossils, foraminifera, lithology, wireline logs, seismic groups, sequence surfaces, and regional tectonic events must cross-check each other. No single fossil group alone certifies an age."
    applies_to: [geox_biostrat_ruling_check]
    enforcement: "required_next_evidence field lists missing disciplines. PASS only when multiple independent lines converge."
    violation: "Claiming a confident age from a single fossil occurrence without corroborating evidence from other disciplines."

  B7:
    name: "Regional diachroneity"
    rule: "Bioevents may migrate across basin space and time. A fossil marker appearing at 14 Ma in one well may appear at 13.5 Ma in another due to migration, ecology, or oceanographic barriers. Never force global synchrony from local data."
    applies_to: [geox_biostrat_nn_age, geox_deep_time_state]
    enforcement: "nn_age output always includes diachroneity warning. Deep time state biozone resolution flagged as 'global average calibration'."
    violation: "Assuming the same biozone = the same absolute age everywhere without considering basin geometry and paleoceanography."

  B8:
    name: "Hold advanced correlation"
    rule: "Larger Benthic Foraminifera (LBF) biozonation, full palynology API integration, live Nannotax3/pforams taxonomy lookup, and multi-well auto-correlation remain behind 888_HOLD. Phase 2.5 unblocks only regex-parsing, lookup, and contradiction detection."
    applies_to: [ALL]
    enforcement: "888_HOLD gate on server.py. Tools requiring external API, taxonomic AI, or multi-well correlation are NOT in SURFACE_TOOLS."
    violation: "Attempting to build or deploy correlation engines that bypass the 888_HOLD gate."

epistemic:
  status: LIVE_INTELLIGENCE
  ratified_by: "Arif (F13 SOVEREIGN)"
  ratified_date: "2026-07-03"
  supersedes: "forge_work/2026-06-22-888-hold-biostrat-coordination.md (8 rulings)"
  confidence: HIGH
  constitutional_floors:
    - F2_TRUTH: "Calibration explicit, uncertainty preserved, evidence_source mandatory"
    - F4_CLARITY: "Four distinct layers: observation → taxonomy → bioevent → interpretation"
    - F6_MARUAH: "Scientific integrity — challenges interpretations, never overrides without evidence"
    - F7_HUMILITY: "Biozone age is a lookup, not a measurement. Confidence capped at 0.85."
