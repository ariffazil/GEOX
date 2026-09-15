#!/usr/bin/env python3
"""Sprint 3: Add workflow_packs to tools_manifest.yaml.

Workflow packs define geological workflows as ordered tool sequences.
Each workflow maps a user intent to a capability-pack-scoped tool chain.
"""

from __future__ import annotations

import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "src" / "geox_mcp" / "tools_manifest.yaml"

WORKFLOW_PACKS = {
    "well_to_correlation": {
        "label": "Well → Correlation",
        "intent": "Evaluate well data, build correlations, and produce a validated correlation package.",
        "pack_requirement": "earth_core",
        "required_packs": ["earth_core"],
        "optional_packs": ["earth_specialist"],
        "steps": [
            {"tool": "geox_basin", "purpose": "Establish basin and stratigraphic context"},
            {"tool": "geox_well", "purpose": "Load and view well curves"},
            {"tool": "geox_well_qc", "purpose": "Validate depth datum, curve units, missing intervals"},
            {"tool": "geox_petrophysics", "purpose": "Compute Vsh, porosity, Sw, permeability, net pay"},
            {"tool": "geox_deep_time", "purpose": "Chronostratigraphic framework for correlation"},
            {"tool": "geox_model", "purpose": "Build integrated subsurface model"},
            {"tool": "geox_map", "purpose": "Render correlation map and cross-sections"},
        ],
        "output_contract": "CorrelationPackage",
        "output_fields": [
            "validated_well_evidence",
            "curve_unit_datum_qc_receipt",
            "petrophysical_interpretation",
            "correlation_hypothesis_with_alternatives",
            "explicit_unknown_intervals",
        ],
        "blocking_conditions": [
            "missing_depth_datum",
            "unknown_curve_units",
            "unresolved_duplicate_curves",
        ],
    },
    "seismic_to_prospect": {
        "label": "Seismic → Prospect",
        "intent": "Evaluate seismic data, build structural and stratigraphic interpretation, and produce a prospect evidence package.",
        "pack_requirement": "earth_specialist",
        "required_packs": ["earth_core", "earth_specialist"],
        "optional_packs": [],
        "steps": [
            {"tool": "geox_basin", "purpose": "Establish basin and petroleum system context"},
            {"tool": "geox_seismic_ingest", "purpose": "Register and validate seismic input (SEG-Y)"},
            {"tool": "geox_seismic_compute", "purpose": "Run attributes, inversion, well tie"},
            {"tool": "geox_seismic_interpret", "purpose": "Horizons, faults, facies, DHI interpretation"},
            {"tool": "geox_geomechanics", "purpose": "Stress compatibility, reactivation probability"},
            {"tool": "geox_model", "purpose": "Build integrated subsurface model"},
            {"tool": "geox_prospect", "purpose": "Prospect hypothesis, risk assessment, volumetrics"},
            {"tool": "geox_claim", "purpose": "Register and verify prospect claims"},
        ],
        "output_contract": "ProspectEvidencePackage",
        "output_fields": [
            "seismic_lineage_and_readiness",
            "horizon_fault_interpretation",
            "structural_charge_seal_hypothesis",
            "risk_register_and_evidence_gaps",
            "prospect_statement_observation_vs_interpretation",
        ],
        "blocking_conditions": [
            "unknown_seismic_phase_polarity",
            "missing_processing_lineage",
            "crs_mismatch_well_seismic",
        ],
    },
    "basin_screening": {
        "label": "Basin Screening",
        "intent": "Screen a basin for petroleum prospectivity — play fairway analysis from regional context to prospect ranking.",
        "pack_requirement": "earth_core",
        "required_packs": ["earth_core"],
        "optional_packs": ["earth_specialist"],
        "steps": [
            {"tool": "geox_basin", "purpose": "Basin profile, tectonic setting, stratigraphy"},
            {"tool": "geox_spatial", "purpose": "Spatial indexing, H3 grid, proximity analysis"},
            {"tool": "geox_temporal", "purpose": "Basin lifecycle, decline curves, timing"},
            {"tool": "geox_source", "purpose": "Source rock presence, kerogen type, maturity"},
            {"tool": "geox_deep_time", "purpose": "Chronostratigraphic framework and paleogeography"},
            {"tool": "geox_claim", "purpose": "Register and verify play/fairway claims"},
            {"tool": "geox_prospect", "purpose": "Screen and rank prospects"},
            {"tool": "geox_map", "purpose": "Render play fairway map"},
        ],
        "output_contract": "PlayFairwaySummary",
        "output_fields": [
            "basin_profile_and_tectonic_context",
            "source_reservoir_seal_presence",
            "play_fairway_map",
            "prospect_ranking_with_risk",
            "evidence_gaps_and_unknowns",
        ],
        "blocking_conditions": [
            "no_source_rock_evidence",
            "missing_stratigraphic_framework",
        ],
    },
    "glof_uncertainty": {
        "label": "GLOF Uncertainty Analysis",
        "intent": "Run GLOF cascade simulation with Bayesian inversion for uncertainty quantification.",
        "pack_requirement": "earth_research",
        "required_packs": ["earth_research"],
        "optional_packs": [],
        "steps": [
            {"tool": "geox_glof_cascade_initialize", "purpose": "Initialize 33D GLOF state"},
            {"tool": "geox_glof_cascade_propagate", "purpose": "1D Saint-Venant wave propagation"},
            {"tool": "geox_glof_cascade_phase", "purpose": "Yield surface evaluation"},
            {"tool": "geox_glof_cascade_inverse", "purpose": "Bayesian grid-search inference"},
            {"tool": "geox_glof_cascade_mcmc_inverse", "purpose": "Full MCMC posterior sampling"},
            {"tool": "geox_glof_cascade_metabolize", "purpose": "Close F-I-M loop, emit receipt"},
        ],
        "output_contract": "UncertaintyReport",
        "output_fields": [
            "posterior_parameter_distributions",
            "convergence_diagnostics",
            "breach_probability_33d",
            "downstream_impact_scenarios",
            "non_convergence_hold_if_applicable",
        ],
        "blocking_conditions": [
            "mcmc_non_convergence",
            "insufficient_observation_data",
        ],
        "resource_budget_required": True,
        "random_seed_required": True,
    },
}


def add_workflow_packs(dry_run: bool = False) -> int:
    with open(MANIFEST_PATH) as f:
        manifest = yaml.safe_load(f)

    manifest["workflow_packs"] = WORKFLOW_PACKS

    if not dry_run:
        with open(MANIFEST_PATH, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False,
                      allow_unicode=True, width=120)
        print(f"  ✓ Added workflow_packs ({len(WORKFLOW_PACKS)} workflows)")
        for name, wf in WORKFLOW_PACKS.items():
            print(f"    {name}: {len(wf['steps'])} steps → {wf['output_contract']}")
    else:
        print(f"  → Would add {len(WORKFLOW_PACKS)} workflow packs")

    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    raise SystemExit(add_workflow_packs(dry_run=dry))
