#!/usr/bin/env python3
"""GEOX Skill Page Generator"""
import json
import os
from pathlib import Path

SKILL_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — GEOX Skill</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <header class="site-header">
    <div class="container">
      <a href="../index.html" class="logo">GEOX</a>
      <nav class="nav-links">
        <a href="../catalog.html" class="active">Skills</a>
        <a href="../wiki.html">Wiki</a>
      </nav>
    </div>
  </header>
  <main class="skill-detail container">
    <div class="breadcrumb">
      <a href="../catalog.html">Skills</a> / {name}
    </div>
    <h1 class="skill-title">{name}</h1>
    <p class="skill-subtitle">{description}</p>
    <div class="skill-meta" style="margin-bottom: 2rem;">
      <span class="tag">{domain_name}</span>
      <span class="tag">Complexity: {complexity}/5</span>
    </div>
    <div class="io-box">
      <h4>MCP Resource</h4>
      <code>{mcp_resource}</code>
    </div>
  </main>
  <footer class="site-footer">
    <div class="footer-seal">DITEMPA BUKAN DIBERI</div>
  </footer>
</body>
</html>'''

def generate():
    with open('registry.json', 'r') as f:
        registry = json.load(f)
    Path('skills').mkdir(exist_ok=True)
    domain_map = {d['id']: d for d in registry['domains']}
    for sid, skill in registry['skills'].items():
        domain = domain_map[skill['domain']]
        html = SKILL_TEMPLATE.format(
            name=skill['name'],
            description=skill['description'],
            domain_name=domain['name'],
            complexity=skill['complexity'],
            mcp_resource=skill['mcp_resource']
        )
        with open(f'skills/{sid}.html', 'w') as f:
            f.write(html)
    print(f"Generated {len(registry['skills'])} skill pages")

if __name__ == '__main__':
    os.chdir('/root/geox-site')
    generate()
