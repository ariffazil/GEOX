"""Map all 37 GEOX tools by domain."""
import sys
sys.path.insert(0, "src")

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

domains = {
    "OBSERVE — Ingest & Inspect": [
        "geox_data_ingest_bundle", "geox_data_qc_bundle", "geox_header_inspect",
        "geox_dst_ingest_test", "geox_fault_stick_ingest_tool", "geox_literature_ingest",
        "geox_evidence_discover", "geox_volume_frame_tool",
    ],
    "COMPUTE — Physics Engine": [
        "geox_seismic_compute", "geox_seismic_compute_attribute_tool",
        "geox_horizon_contrast_surface", "geox_blend_volume_tool",
        "geox_blockspace_resolution_tool", "geox_coord_transform_tool", "geox_segy_export_tool",
    ],
    "INTERPRET — Geological": [
        "geox_sequence_interpret", "geox_basin_profile", "geox_basin_resolve",
        "geox_map_context_scene", "geox_subsurface_generate_candidates",
    ],
    "REASON — Synthesis": [
        "geox_evidence_reason", "geox_query_intake", "geox_report_to_workflow",
    ],
    "CLAIM — Truth Pipeline": [
        "geox_claim_create", "geox_claim_validate", "geox_claim_challenge",
        "geox_claim_seal", "geox_evidence_attach",
    ],
    "GOVERN — Integrity": [
        "geox_subsurface_verify_integrity", "geox_prospect_evaluate", "geox_abstraction_guard",
    ],
    "VISION — Seismic Image": [
        "geox_vision_minimax_inference", "geox_vision_perceptual_inventory",
        "geox_vision_audit", "geox_vision_calibrate",
    ],
    "DISCOVERY — Registry": [
        "geox_system_registry_status", "geox_attribute_registry_list_tool",
    ],
}

print("=== 37 GEOX TOOLS — DOMAIN MAP ===\n")
for domain, tools in domains.items():
    print(f"{domain} ({len(tools)})")
    for t in tools:
        assert t in CANONICAL_PUBLIC_TOOLS, f"MISSING: {t}"
        print(f"  ✓ {t}")
    print()

all_mapped = [t for ts in domains.values() for t in ts]
print(f"Total: {len(all_mapped)} | All canonical: {all(t in CANONICAL_PUBLIC_TOOLS for t in all_mapped)}")

print("\n=== CONSOLIDATION PATH: 37 → 33 ===\n")
merges = [
    ("geox_seismic_compute_attribute_tool → geox_seismic_compute",
     "Attribute compute already in seismic_compute(mode='attribute'). Remove standalone tool."),
    ("geox_basin_resolve → geox_basin_profile",
     "Basin lookup already in basin_profile(mode='overview'). Merge as mode='resolve'."),
    ("geox_blockspace_resolution_tool → geox_coord_transform_tool",
     "Both do affine/block math. Add mode='resolution' to coord_transform."),
    ("geox_attribute_registry_list_tool → geox_system_registry_status",
     "Attribute list is a subset of registry status. Merge as mode='attributes'."),
]
for i, (merge, why) in enumerate(merges, 1):
    print(f"{i}. {merge}")
    print(f"   {why}\n")
print("Result: 37 - 4 = 33 tools. All capabilities preserved, no user-facing loss.")
