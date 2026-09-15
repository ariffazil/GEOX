#!/usr/bin/env python3
"""Sprint 5: Earth Capability Graph — workflows as graph edges.

The graph captures:
- Tool dependency edges (what feeds what)
- Workflow paths (ordered sequences through the graph)
- Cross-workflow bridges (shared tools and evidence flow)
- Entry points (which tools start reasoning chains)
- Decision points (which tools produce actionable outputs)
"""

from __future__ import annotations

import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "src" / "geox_mcp" / "tools_manifest.yaml"

EARTH_CAPABILITY_GRAPH = {
    "version": "1.0.0",
    "description": "GEOX Earth Capability Graph — tool dependencies, workflow paths, and evidence flow.",
    "doctrine": "Capability → Organ → Tool → Skill. Graph edges are witnessed dependencies, not declared hierarchies.",

    # ── Nodes: every public tool is a graph node ──────────────────────
    "nodes": {
        # Evidence & Orientation (entry points)
        "geox_basin":     {"family": "evidence",  "role": "entry_point",  "description": "Basin context — most workflows start here"},
        "geox_claim":     {"family": "evidence",  "role": "decision_point", "description": "Claim registration and verification"},
        "geox_source":    {"family": "evidence",  "role": "evidence_node", "description": "Source rock and diagenesis"},
        "geox_spatial":   {"family": "evidence",  "role": "evidence_node", "description": "Spatial indexing and discovery"},
        "geox_temporal":  {"family": "evidence",  "role": "evidence_node", "description": "Temporal analytics"},
        "geox_deep_time": {"family": "evidence",  "role": "evidence_node", "description": "Chronostratigraphic framework"},
        "geox_paleobiodb_query": {"family": "evidence", "role": "evidence_node", "description": "Paleobiology data"},

        # Ingest (data gates)
        "geox_well_ingest":    {"family": "ingest", "role": "data_gate", "description": "Well data registration"},
        "geox_well_qc":        {"family": "ingest", "role": "data_gate", "description": "Well data quality control"},
        "geox_seismic_ingest": {"family": "ingest", "role": "data_gate", "description": "Seismic data registration"},

        # Interpretation (reasoning nodes)
        "geox_well":              {"family": "interpret", "role": "reasoning_node", "description": "Well data query and visualization"},
        "geox_petrophysics":      {"family": "interpret", "role": "reasoning_node", "description": "Petrophysical analysis"},
        "geox_seismic_compute":   {"family": "interpret", "role": "reasoning_node", "description": "Seismic computation"},
        "geox_seismic_interpret": {"family": "interpret", "role": "reasoning_node", "description": "Seismic interpretation"},
        "geox_geomechanics":      {"family": "interpret", "role": "reasoning_node", "description": "Geomechanical analysis"},
        "geox_contrast_metabolize": {"family": "interpret", "role": "reasoning_node", "description": "Anomalous contrast pipeline"},

        # Model (integration nodes)
        "geox_model": {"family": "model", "role": "integration_node", "description": "Integrated subsurface model"},

        # Prospect (decision points)
        "geox_prospect": {"family": "prospect", "role": "decision_point", "description": "Prospect assessment and risk"},

        # View (presentation)
        "geox_map": {"family": "view", "role": "presentation_node", "description": "Map rendering and visualization"},

        # Research (advanced)
        "geox_glof_cascade_initialize":  {"family": "research", "role": "entry_point",  "subfamily": "cascade",   "description": "GLOF state initialization"},
        "geox_glof_cascade_step":        {"family": "research", "role": "reasoning_node", "subfamily": "cascade",  "description": "State advancement"},
        "geox_glof_cascade_phase":       {"family": "research", "role": "reasoning_node", "subfamily": "cascade",  "description": "Yield surface evaluation"},
        "geox_glof_cascade_propagate":   {"family": "research", "role": "reasoning_node", "subfamily": "cascade",  "description": "Wave propagation"},
        "geox_glof_cascade_inverse":     {"family": "research", "role": "reasoning_node", "subfamily": "inversion", "description": "Grid-search inference"},
        "geox_glof_cascade_mcmc_inverse": {"family": "research", "role": "decision_point", "subfamily": "inversion", "description": "MCMC posterior sampling"},
        "geox_glof_cascade_metabolize":  {"family": "research", "role": "integration_node", "subfamily": "cascade", "description": "F-I-M loop closure"},
    },

    # ── Edges: tool dependency graph ──────────────────────────────────
    # Format: {from, to, relationship, evidence_type}
    "edges": [
        # === Evidence backbone ===
        {"from": "geox_basin", "to": "geox_spatial",   "rel": "context_for",     "evidence": "basin_extent"},
        {"from": "geox_basin", "to": "geox_temporal",   "rel": "context_for",     "evidence": "stratigraphic_framework"},
        {"from": "geox_basin", "to": "geox_source",     "rel": "context_for",     "evidence": "petroleum_system"},
        {"from": "geox_basin", "to": "geox_deep_time",  "rel": "context_for",     "evidence": "chronostratigraphy"},
        {"from": "geox_basin", "to": "geox_map",        "rel": "context_for",     "evidence": "spatial_extent"},

        # === Well analysis chain ===
        {"from": "geox_well_ingest", "to": "geox_well_qc",     "rel": "feeds",  "evidence": "raw_curves"},
        {"from": "geox_well_qc",     "to": "geox_well",         "rel": "feeds",  "evidence": "validated_curves"},
        {"from": "geox_well",        "to": "geox_petrophysics", "rel": "feeds",  "evidence": "curve_data"},
        {"from": "geox_basin",       "to": "geox_well",         "rel": "context_for", "evidence": "stratigraphic_framework"},

        # === Seismic analysis chain ===
        {"from": "geox_seismic_ingest",  "to": "geox_seismic_compute",   "rel": "feeds",  "evidence": "segy_data"},
        {"from": "geox_seismic_compute", "to": "geox_seismic_interpret", "rel": "feeds",  "evidence": "attributes_volumes"},
        {"from": "geox_seismic_interpret", "to": "geox_geomechanics",    "rel": "feeds",  "evidence": "structural_model"},
        {"from": "geox_basin",           "to": "geox_seismic_interpret", "rel": "context_for", "evidence": "depositional_model"},

        # === Model integration (convergence point) ===
        {"from": "geox_petrophysics",      "to": "geox_model", "rel": "feeds", "evidence": "petrophysical_properties"},
        {"from": "geox_seismic_interpret",  "to": "geox_model", "rel": "feeds", "evidence": "structural_framework"},
        {"from": "geox_geomechanics",       "to": "geox_model", "rel": "feeds", "evidence": "stress_state"},
        {"from": "geox_deep_time",          "to": "geox_model", "rel": "feeds", "evidence": "temporal_framework"},
        {"from": "geox_source",             "to": "geox_model", "rel": "feeds", "evidence": "source_rock_properties"},
        {"from": "geox_basin",              "to": "geox_model", "rel": "context_for", "evidence": "basin_context"},

        # === Prospect decision chain ===
        {"from": "geox_model",    "to": "geox_prospect", "rel": "feeds",       "evidence": "integrated_model"},
        {"from": "geox_basin",    "to": "geox_prospect", "rel": "context_for", "evidence": "play_context"},
        {"from": "geox_prospect", "to": "geox_claim",    "rel": "feeds",       "evidence": "prospect_hypothesis"},
        {"from": "geox_prospect", "to": "geox_map",      "rel": "feeds",       "evidence": "prospect_geometry"},

        # === GLOF cascade chain ===
        {"from": "geox_glof_cascade_initialize", "to": "geox_glof_cascade_step",      "rel": "feeds", "evidence": "initial_state_33d"},
        {"from": "geox_glof_cascade_step",       "to": "geox_glof_cascade_phase",     "rel": "feeds", "evidence": "evolved_state"},
        {"from": "geox_glof_cascade_step",       "to": "geox_glof_cascade_propagate", "rel": "feeds", "evidence": "state_for_propagation"},
        {"from": "geox_glof_cascade_propagate",  "to": "geox_glof_cascade_inverse",   "rel": "feeds", "evidence": "wave_observations"},
        {"from": "geox_glof_cascade_inverse",    "to": "geox_glof_cascade_mcmc_inverse", "rel": "feeds", "evidence": "grid_search_posterior"},
        {"from": "geox_glof_cascade_phase",      "to": "geox_glof_cascade_metabolize", "rel": "feeds", "evidence": "yield_surface"},
        {"from": "geox_glof_cascade_mcmc_inverse", "to": "geox_glof_cascade_metabolize", "rel": "feeds", "evidence": "mcmc_posterior"},

        # === Cross-family bridges ===
        {"from": "geox_paleobiodb_query", "to": "geox_deep_time", "rel": "feeds", "evidence": "biostratigraphic_constraints"},
        {"from": "geox_contrast_metabolize", "to": "geox_seismic_interpret", "rel": "feeds", "evidence": "contrast_hypotheses"},
    ],

    # ── Workflow paths through the graph ──────────────────────────────
    "workflow_paths": {
        "well_to_correlation": {
            "path": [
                "geox_basin", "geox_well", "geox_well_qc", "geox_petrophysics",
                "geox_deep_time", "geox_model", "geox_map",
            ],
            "entry": "geox_basin",
            "output": "geox_map",
            "crosses_families": ["evidence", "ingest", "interpret", "model", "view"],
        },
        "seismic_to_prospect": {
            "path": [
                "geox_basin", "geox_seismic_ingest", "geox_seismic_compute",
                "geox_seismic_interpret", "geox_geomechanics", "geox_model",
                "geox_prospect", "geox_claim",
            ],
            "entry": "geox_basin",
            "output": "geox_claim",
            "crosses_families": ["evidence", "ingest", "interpret", "model", "prospect"],
        },
        "basin_screening": {
            "path": [
                "geox_basin", "geox_spatial", "geox_temporal", "geox_source",
                "geox_deep_time", "geox_claim", "geox_prospect", "geox_map",
            ],
            "entry": "geox_basin",
            "output": "geox_map",
            "crosses_families": ["evidence", "prospect", "view"],
        },
        "glof_uncertainty": {
            "path": [
                "geox_glof_cascade_initialize", "geox_glof_cascade_propagate",
                "geox_glof_cascade_phase", "geox_glof_cascade_inverse",
                "geox_glof_cascade_mcmc_inverse", "geox_glof_cascade_metabolize",
            ],
            "entry": "geox_glof_cascade_initialize",
            "output": "geox_glof_cascade_metabolize",
            "crosses_families": ["research"],
        },
    },

    # ── Hub analysis: which tools appear in most paths ────────────────
    "hub_tools": {
        "geox_basin":      {"in_workflows": 3, "role": "universal_context_provider"},
        "geox_model":      {"in_workflows": 2, "role": "integration_convergence_point"},
        "geox_prospect":   {"in_workflows": 2, "role": "decision_convergence_point"},
        "geox_claim":      {"in_workflows": 2, "role": "evidence_registration"},
        "geox_map":        {"in_workflows": 2, "role": "presentation_convergence_point"},
        "geox_deep_time":  {"in_workflows": 2, "role": "temporal_framework_provider"},
    },

    # ── Evidence flow summary ─────────────────────────────────────────
    "evidence_types": [
        "basin_extent", "stratigraphic_framework", "petroleum_system",
        "chronostratigraphy", "raw_curves", "validated_curves", "curve_data",
        "petrophysical_properties", "segy_data", "attributes_volumes",
        "structural_framework", "structural_model", "stress_state",
        "temporal_framework", "source_rock_properties", "basin_context",
        "integrated_model", "play_context", "prospect_hypothesis",
        "prospect_geometry", "biostratigraphic_constraints", "contrast_hypotheses",
        "initial_state_33d", "evolved_state", "wave_observations",
        "grid_search_posterior", "mcmc_posterior", "yield_surface",
    ],
}


def add_capability_graph(dry_run: bool = False) -> int:
    with open(MANIFEST_PATH) as f:
        manifest = yaml.safe_load(f)

    manifest["earth_capability_graph"] = EARTH_CAPABILITY_GRAPH

    if not dry_run:
        with open(MANIFEST_PATH, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False,
                      allow_unicode=True, width=120)
        print(f"  ✓ Added earth_capability_graph")
        print(f"    Nodes: {len(EARTH_CAPABILITY_GRAPH['nodes'])}")
        print(f"    Edges: {len(EARTH_CAPABILITY_GRAPH['edges'])}")
        print(f"    Workflow paths: {len(EARTH_CAPABILITY_GRAPH['workflow_paths'])}")
        print(f"    Hub tools: {len(EARTH_CAPABILITY_GRAPH['hub_tools'])}")
        print(f"    Evidence types: {len(EARTH_CAPABILITY_GRAPH['evidence_types'])}")
    else:
        print(f"  → Would add earth_capability_graph")

    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    raise SystemExit(add_capability_graph(dry_run=dry))
