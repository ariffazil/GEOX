"""
Patch script step 2: handle multi-line @mcp.tool registrations 
where name= is on the line AFTER @mcp.tool(
"""

MULTILINE_TOOL_NAMES = {
    "geox_geological_model_generate",  # → geox_model geological_2d
    "geox_dde_reason",           # → geox_deep_time dde_reason
    "geox_temporal_decline",     # → geox_temporal decline
    "geox_temporal_rrr",         # → geox_temporal rrr
    "geox_temporal_basin_lifecycle",   # → geox_temporal basin_lifecycle
    "geox_temporal_cadence",     # → geox_temporal cadence
    "geox_source_rock",          # → geox_source toc
    "geox_avo_forward",          # → geox_seismic_compute zoeppritz
    "geox_diagenesis",           # → geox_source compaction
    "geox_gempy_implicit_3d",    # → geox_model gempy_3d
    "geox_h3_spatial_index",     # → geox_spatial h3
    "geox_lancedb_embed_store",  # → geox_spatial embed_store
    "geox_stac_discover",        # → geox_spatial stac
}

with open("src/geox_mcp/tools_wiring.py", "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
deregistered = []

while i < len(lines):
    line = lines[i]
    
    # Look for @mcp.tool( on one line, then name= on next line
    stripped = line.rstrip()
    is_mcp_tool_open = ("@mcp.tool(" in stripped) and stripped.rstrip().endswith("(")
    
    if is_mcp_tool_open and i + 1 < len(lines):
        next_line = lines[i + 1]
        matched_name = None
        for tool_name in MULTILINE_TOOL_NAMES:
            if f'name="{tool_name}"' in next_line:
                matched_name = tool_name
                break
        
        if matched_name:
            # Comment out the @mcp.tool( line
            new_lines.append(line.replace("@mcp.tool(", f"# ZEN-CONSOLIDATED — @mcp.tool("))
            deregistered.append(matched_name)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)
    i += 1

print(f"Step 2 deregistered {len(deregistered)} multi-line tools:")
for t in sorted(deregistered):
    print(f"  {t}")

with open("src/geox_mcp/tools_wiring.py", "w") as f:
    f.writelines(new_lines)
print("Done step 2")
