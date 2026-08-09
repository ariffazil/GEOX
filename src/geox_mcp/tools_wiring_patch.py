"""
Patch script to consolidate GEOX tools from 42 → 20.
Run: python3 tools_wiring_patch.py
"""
import re

# Read the file
with open("src/geox_mcp/tools_wiring.py", "r") as f:
    content = f.read()

lines = content.split("\n")

# Track changes
changes = []

# ─── Step 1: Comment out @mcp.tool decorators for tools being merged ───────────
# These lines contain @mcp.tool registrations that we want to deregister
DEREGISTER_TOOL_NAMES = {
    "geox_well_view",          # → geox_well view
    "geox_well_desk",          # → geox_well desk
    "geox_sequence",           # → geox_petrophysics sequence
    "geox_surface_status",     # → geox_workspace status
    "geox_visual_understand",  # → geox_seismic_interpret pattern
    "geox_subsurface_model",   # → geox_model subsurface_inversion
    "geox_falsify",            # → geox_claim falsify
    "geox_evidence_synthesize",# → geox_claim synthesize
    "geox_evidence",           # → geox_claim evidence
    "geox_contradiction_scan", # → geox_claim contradict
    "geox_well_tie_compute",   # → geox_seismic_compute well_tie
    "geox_well_seismic_mistie_rms",      # → geox_seismic_compute mistie
    "geox_wavelet_extract_least_squares", # → geox_seismic_compute wavelet
    "geox_avo_forward",        # → geox_seismic_compute zoeppritz
    "geox_map_layers_list",    # → geox_map list_layers
    "geox_map_scene_plan",     # → geox_map scene_plan
    "geox_map_render_preview", # → geox_map render_preview
    "geox_basin_backstrip",    # → geox_basin backstrip
    "geox_thermal_maturity_history",  # → geox_basin thermal_maturity
    "geox_lem_predict",        # → geox_petrophysics lem_predict
    "geox_geological_model_generate", # → geox_model geological_2d
    "geox_gempy_implicit_3d",  # → geox_model gempy_3d
    "geox_h3_spatial_index",   # → geox_spatial h3
    "geox_lancedb_embed_store",# → geox_spatial embed_store
    "geox_stac_discover",      # → geox_spatial stac
    "geox_dde_reason",         # → geox_deep_time dde_reason
    "geox_temporal_decline",   # → geox_temporal decline
    "geox_temporal_rrr",       # → geox_temporal rrr
    "geox_temporal_basin_lifecycle", # → geox_temporal basin_lifecycle
    "geox_temporal_cadence",   # → geox_temporal cadence
    "geox_source_rock",        # → geox_source toc
    "geox_diagenesis",         # → geox_source compaction
}

# Also deregister the duplicate geox_biostrat_calibrate at line 3781
# and duplicate geox_physical_reality_interpret at line 2447
DEREGISTER_DUPLICATES_AT_LINES = {3781, 2447}

new_lines = []
i = 0
deregistered = set()
skip_dup_biostrat = False  # Track if we've seen geox_biostrat_calibrate already
seen_biostrat = False
seen_physical_reality = False

while i < len(lines):
    line = lines[i]
    
    # Check for duplicate biostrat / physical_reality
    is_dup_biostrat = 'name="geox_biostrat_calibrate"' in line and seen_biostrat and "@mcp.tool" in line
    is_dup_physical = 'name="geox_physical_reality_interpret"' in line and seen_physical_reality and "@mcp.tool" in line
    
    if 'name="geox_biostrat_calibrate"' in line and "@mcp.tool" in line:
        if not seen_biostrat:
            seen_biostrat = True
        else:
            is_dup_biostrat = True
    if 'name="geox_physical_reality_interpret"' in line and "@mcp.tool" in line:
        if not seen_physical_reality:
            seen_physical_reality = True
        else:
            is_dup_physical = True
    
    if is_dup_biostrat or is_dup_physical:
        # Comment out this @mcp.tool line
        new_lines.append(line.replace("@mcp.tool(", "# MERGED-ZEN — @mcp.tool("))
        changes.append(f"Deregistered duplicate at line {i+1}")
        i += 1
        continue
    
    # Check if this line registers a tool to be deregistered
    matched_tool = None
    for tool_name in DEREGISTER_TOOL_NAMES:
        if f'name="{tool_name}"' in line and "@mcp.tool" in line:
            matched_tool = tool_name
            break
    
    if matched_tool and matched_tool not in deregistered:
        deregistered.add(matched_tool)
        # Comment out the @mcp.tool decorator line
        new_lines.append(line.replace("@mcp.tool(", f"# ZEN-CONSOLIDATED — @mcp.tool("))
        changes.append(f"Deregistered {matched_tool} at line {i+1}")
    else:
        new_lines.append(line)
    i += 1

print(f"Deregistered {len(deregistered)} tools:")
for t in sorted(deregistered):
    print(f"  {t}")
print(f"Total changes: {len(changes)}")

# Write updated content
updated = "\n".join(new_lines)
with open("src/geox_mcp/tools_wiring.py", "w") as f:
    f.write(updated)
print("Done writing step 1")
