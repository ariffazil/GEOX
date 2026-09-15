#!/usr/bin/env python3
"""Sprint 1: Add family + tier to tools_manifest.yaml, extend SurfaceTool, update generator.

Classification-only. NO renames, NO deletions, NO routing changes.
"""

from __future__ import annotations

import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "src" / "geox_mcp" / "tools_manifest.yaml"

# ── Family + Tier classification ──────────────────────────────────────────
# Based on Capability Graph doctrine:
#   evidence  → What Earth evidence exists?
#   ingest    → Can this dataset be trusted?
#   interpret → What does the Earth mean?
#   model     → What is the integrated Earth model?
#   prospect  → Should we believe this opportunity exists?
#   view      → Show the evidence.
#   research  → Experimental Earth science.
#
# Tiers:
#   A = Core (default discovery,13 tools)
#   B = Specialist (opt-in, 5 tools)
#   C = Research (advanced/research only, 8 tools)
#   Z = Internal/infrastructure (not surfaced)

TOOL_CLASSIFICATION: dict[str, dict[str, str]] = {
    # ── Public Tier A: Core ───────────────────────────────────────────
    "geox_basin":             {"family": "evidence",  "tier": "A"},
    "geox_claim":             {"family": "evidence",  "tier": "A"},
    "geox_source":            {"family": "evidence",  "tier": "A"},
    "geox_spatial":           {"family": "evidence",  "tier": "A"},
    "geox_temporal":          {"family": "evidence",  "tier": "A"},
    "geox_deep_time":         {"family": "evidence",  "tier": "A"},
    "geox_well_qc":           {"family": "ingest",    "tier": "A"},
    "geox_well":              {"family": "interpret",  "tier": "A"},
    "geox_petrophysics":      {"family": "interpret",  "tier": "A"},
    "geox_seismic_interpret": {"family": "interpret",  "tier": "A"},
    "geox_model":             {"family": "model",     "tier": "A"},
    "geox_prospect":          {"family": "prospect",  "tier": "A"},
    "geox_map":               {"family": "view",      "tier": "A"},
    # ── Public Tier B: Specialist ─────────────────────────────────────
    "geox_well_ingest":       {"family": "ingest",    "tier": "B"},
    "geox_seismic_ingest":    {"family": "ingest",    "tier": "B"},
    "geox_seismic_compute":   {"family": "interpret",  "tier": "B"},
    "geox_geomechanics":      {"family": "interpret",  "tier": "B"},
    "geox_contrast_metabolize": {"family": "interpret", "tier": "B"},
    "geox_paleobiodb_query":  {"family": "evidence",  "tier": "B"},
    # ── Public Tier C: Research (GLOF cascade) ────────────────────────
    "geox_glof_cascade_initialize":  {"family": "research", "tier": "C"},
    "geox_glof_cascade_step":        {"family": "research", "tier": "C"},
    "geox_glof_cascade_phase":       {"family": "research", "tier": "C"},
    "geox_glof_cascade_inverse":     {"family": "research", "tier": "C"},
    "geox_glof_cascade_metabolize":  {"family": "research", "tier": "C"},
    "geox_glof_cascade_mcmc_inverse": {"family": "research", "tier": "C"},
    "geox_glof_cascade_propagate":   {"family": "research", "tier": "C"},
    # ── Internal: classify by domain ──────────────────────────────────
    "geox_gravmag_studio":            {"family": "interpret", "tier": "Z"},
    "geox_sediment_mass_balance":     {"family": "model",     "tier": "Z"},
    "geox_claim_graph_evaluate":      {"family": "evidence",  "tier": "Z"},
    "geox_to_wealth_bridge":          {"family": "prospect",  "tier": "Z"},
    "geox_well_desurvey":             {"family": "interpret", "tier": "Z"},
    "geox_physical_reality_interpret": {"family": "interpret", "tier": "Z"},
    "geox_geological_cognition_run":  {"family": "interpret", "tier": "Z"},
    "geox_panel_d_render_mcp":        {"family": "view",      "tier": "Z"},
    "geox_segy_trace_audit":          {"family": "ingest",    "tier": "Z"},
    "geox_well_tie_compute":          {"family": "interpret", "tier": "Z"},
    "geox_3d_model_build":            {"family": "model",     "tier": "Z"},
    "geox_wealth_bridge_run":         {"family": "prospect",  "tier": "Z"},
    "geox_rsi_interpret":             {"family": "interpret", "tier": "Z"},
    "geox_render_audit":              {"family": "view",      "tier": "Z"},
    "geox_map_export_package":        {"family": "view",      "tier": "Z"},
    "geox_atlas":                     {"family": "evidence",  "tier": "Z"},
    "geox_forbidden_claims_scan":     {"family": "evidence",  "tier": "Z"},
    "geox_doctrine":                  {"family": "evidence",  "tier": "Z"},
    "geox_egs_query_entity":          {"family": "evidence",  "tier": "Z"},
    "geox_egs_query_claim":           {"family": "evidence",  "tier": "Z"},
    "geox_egs_query_uncertainty":     {"family": "evidence",  "tier": "Z"},
    "geox_egs_query_provenance":      {"family": "evidence",  "tier": "Z"},
    "geox_egs_claim_create":          {"family": "evidence",  "tier": "Z"},
    "geox_egs_claim_challenge":       {"family": "evidence",  "tier": "Z"},
    "geox_egs_evidence_attach":       {"family": "evidence",  "tier": "Z"},
    "geox_egs_evidence_reason":       {"family": "evidence",  "tier": "Z"},
    "geox_egs_seismic_compute":       {"family": "interpret", "tier": "Z"},
    "geox_egs_rock_physics":          {"family": "interpret", "tier": "Z"},
    "geox_egs_data_qc_bundle":        {"family": "ingest",    "tier": "Z"},
    "geox_egs_scenario_audit":        {"family": "evidence",  "tier": "Z"},
    "geox_seismic_cognition":         {"family": "interpret", "tier": "Z"},
    "geox_visual_enhance":            {"family": "view",      "tier": "Z"},
    "geox_visual_generate_hypotheses": {"family": "interpret", "tier": "Z"},
    "geox_panel_d_render":            {"family": "view",      "tier": "Z"},
    "geox_cognitive_rank_hypotheses":  {"family": "interpret", "tier": "Z"},
    "geox_segy_audit":                {"family": "ingest",    "tier": "Z"},
    "geox_well_tie":                  {"family": "interpret", "tier": "Z"},
    "geox_3d_model":                  {"family": "model",     "tier": "Z"},
    "geox_wealth_consequence":        {"family": "prospect",  "tier": "Z"},
    "geox_bid_round_screener":        {"family": "prospect",  "tier": "Z"},
    "geox_simulate_accommodation":    {"family": "model",     "tier": "Z"},
    "geox_simulate_surfaces":         {"family": "model",     "tier": "Z"},
    "geox_simulate_sequences":        {"family": "model",     "tier": "Z"},
    "geox_simulate_routing":          {"family": "model",     "tier": "Z"},
    "geox_biostrat_nn_age":           {"family": "evidence",  "tier": "Z"},
    "geox_biostrat_ruling_check":     {"family": "evidence",  "tier": "Z"},
    "geox_macrostrat_calibrate":      {"family": "evidence",  "tier": "Z"},
    "geox_tie_receipt":               {"family": "interpret", "tier": "Z"},
    "geox_tie_preflight":             {"family": "interpret", "tier": "Z"},
    "geox_benchmark_001":             {"family": "research",  "tier": "Z"},
    "geox_well_time_depth_calibrate": {"family": "interpret", "tier": "Z"},
    "geox_well_seismic_mistie_rms":   {"family": "interpret", "tier": "Z"},
    "geox_wavelet_extract_least_squares": {"family": "interpret", "tier": "Z"},
    "geox_dst_ingest_test":           {"family": "ingest",    "tier": "Z"},
}


def classify_manifest(dry_run: bool = False) -> int:
    """Add family + tier to every tool in tools_manifest.yaml."""
    with open(MANIFEST_PATH) as f:
        manifest = yaml.safe_load(f)

    tools = manifest["tools"]
    classified = 0
    unclassified = []

    for tool in tools:
        name = tool["name"]
        cls = TOOL_CLASSIFICATION.get(name)
        if cls:
            tool["family"] = cls["family"]
            tool["tier"] = cls["tier"]
            classified += 1
        else:
            # Infer from domain if not explicitly mapped
            domain = tool.get("domain", "unknown")
            vis = tool.get("visibility", "public")
            if "seismic" in domain:
                tool["family"] = "interpret"
            elif "well" in domain:
                tool["family"] = "ingest"
            elif "basin" in domain or "stratigraphy" in domain:
                tool["family"] = "evidence"
            elif "petrophysics" in domain:
                tool["family"] = "interpret"
            elif "model" in domain:
                tool["family"] = "model"
            elif "prospect" in domain:
                tool["family"] = "prospect"
            elif "spatial" in domain or "map" in domain:
                tool["family"] = "view"
            elif "hazard" in domain:
                tool["family"] = "research"
            elif "governance" in domain:
                tool["family"] = "evidence"
            else:
                tool["family"] = "evidence"

            tool["tier"] = "Z" if vis == "internal" else "A"
            unclassified.append(name)
            classified += 1

    # Update manifest header
    manifest["sprint1_classified"] = True
    manifest["family_count"] = len(set(t.get("family", "") for t in tools))
    manifest["tier_distribution"] = {
        tier: len([t for t in tools if t.get("tier") == tier])
        for tier in ["A", "B", "C", "Z"]
    }

    if not dry_run:
        with open(MANIFEST_PATH, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False,
                      allow_unicode=True, width=120)
        print(f"  ✓ Classified {classified}/{len(tools)} tools")
        print(f"  Families: {manifest['family_count']}")
        print(f"  Tiers: {manifest['tier_distribution']}")
        if unclassified:
            print(f"  ⚠ Auto-inferred {len(unclassified)} tools: {unclassified}")
    else:
        print(f"  → Would classify {classified}/{len(tools)} tools")

    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    raise SystemExit(classify_manifest(dry_run=dry))
