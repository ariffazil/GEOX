#!/usr/bin/env python3
"""Fix YAML corruption in surface.yaml and tools_manifest.yaml.
Problem: OpenCode appended LEM tool entries using proper - name: format 
after a section of legacy scalar entries (- toolname) and a metadata map.
Solution: Rebuild the tools: list cleanly, strip the orphan metadata.
"""
import yaml

for fname in ['surface.yaml', 'tools_manifest.yaml']:
    path = f'/root/GEOX/src/geox_mcp/{fname}'
    
    with open(path) as f:
        lines = f.readlines()
    
    # Phase 1: Extract the header (first 4 lines)
    header = lines[:4]  # manifest_version, generated_from, public_transport, tools:
    
    # Phase 2: Extract all tools - both proper - name: and legacy - scalars
    # The tools section runs from line 4 (index 4) to wherever the last - item is
    
    # Find where tools section ends (last line starting with '-')
    last_dash_idx = None
    for i in range(4, len(lines)):
        if lines[i].startswith('- '):
            last_dash_idx = i
    
    if last_dash_idx is None:
        print(f"{fname}: No tools found!")
        continue
    
    # Get all tool entries from line 4 to last_dash_idx
    # Parse them as YAML to rebuild properly
    tools_section = ''.join(lines[4:last_dash_idx+1])
    
    # Parse the YAML list
    tools_list = yaml.safe_load(tools_section)
    
    # Normalize: convert scalars to {name: scalar}
    normalized = []
    legacy_count = 0
    for t in tools_list:
        if isinstance(t, str):
            normalized.append({'name': t, 'visibility': 'internal'})
            legacy_count += 1
        else:
            normalized.append(t)
    
    # Count public tools
    public_count = sum(1 for t in normalized if t.get('visibility') == 'public')
    internal_count = sum(1 for t in normalized if t.get('visibility') == 'internal')
    
    print(f"{fname}: {len(tools_list)} entries ({legacy_count} legacy scalars normalized)")
    print(f"  Public: {public_count}, Internal: {internal_count}")
    
    # Phase 3: Rebuild the file with clean YAML
    # Write header
    with open(path, 'w') as f:
        for line in header:
            f.write(line)
        
        # Write each tool with proper - name: format
        for t in normalized:
            f.write(yaml.dump([t], default_flow_style=False, sort_keys=False, allow_unicode=True).lstrip('- '))
            f.write('\n')
    
    # Phase 4: Verify
    with open(path) as f:
        rebuilt = yaml.safe_load(f)
    
    final_tools = rebuilt.get('tools', [])
    final_public = sum(1 for t in final_tools if t.get('visibility') == 'public')
    final_internal = sum(1 for t in final_tools if t.get('visibility') == 'internal')
    print(f"  Verified: {len(final_tools)} tools, Public={final_public}, Internal={final_internal}")
    
    # List LEM tools
    lem = [t['name'] for t in final_tools if any(x in t['name'] for x in 
        ['gempy', 'h3_', 'lancedb', 'stac_', 'dde'])]
    print(f"  LEM tools: {lem}")

print("\n✅ YAML fix complete")
