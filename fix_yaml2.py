#!/usr/bin/env python3
"""Fix YAML legacy scalar entries in surface.yaml and tools_manifest.yaml.
Convert '- toolname' (scalar) to '- name: toolname' (mapping) so both files parse cleanly."""
import re, sys

for fname in ['surface.yaml', 'tools_manifest.yaml']:
    path = f'/root/GEOX/src/geox_mcp/{fname}'
    with open(path) as f:
        content = f.read()
    
    count = 0
    def fix_scalar(m, _cnt=[count]):
        _cnt[0] += 1
        val = m.group(1)
        return f'- name: {val}'
    
    content = re.sub(r'^\- ([a-z][a-z_]+)$', fix_scalar, content, flags=re.MULTILINE)
    
    with open(path, 'w') as f:
        f.write(content)
    
    print(f'{fname}: fixed {count} legacy scalar entries')

# Now verify
import yaml
for fname in ['surface.yaml', 'tools_manifest.yaml']:
    path = f'/root/GEOX/src/geox_mcp/{fname}'
    with open(path) as f:
        d = yaml.safe_load(f)
    tools = d.get('tools', [])
    public = [t['name'] for t in tools if t.get('visibility') == 'public']
    internal = [t['name'] for t in tools if t.get('visibility') == 'internal']
    lem = [t['name'] for t in tools if any(x in t['name'] for x in 
        ['gempy','h3_','lancedb','stac_','dde'])]
    ghost = {g: '✓' for g in ['gravmag_studio','sediment_mass_balance','claim_graph_evaluate',
                                'to_wealth_bridge','map_export_package'] 
             if any(g in t['name'] and t.get('visibility') == 'internal' for t in tools)}
    
    print(f'\n✅ {fname}:')
    print(f'   Total={len(tools)} Public={len(public)} Internal={len(internal)}')
    print(f'   LEM tools: {lem}')
    print(f'   Ghosted (internal): {ghost}')
