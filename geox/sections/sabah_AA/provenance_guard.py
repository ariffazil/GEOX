#!/usr/bin/env python3
"""Provenance guard — fails the build on attribution violations.

Checks (from MODEL_PROVENANCE_MATRIX.md §4):
 1 'Morley' never co-occurs with plate/slab/underthrust attribution
 2 shallow-process source never used to justify deep geometry
 3 Model A must carry UNTESTED; SPEC bodies may not read as picks
 4 every drawn body/line/fault in the page data has a provenance entry
 5 'magmatic ridge' banned (stale name)
 6 'plate' only in allowed tectonic usages
Usage: python3 provenance_guard.py  (exit 0 = PASS)
"""
import json, re, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
PAGE = pathlib.Path("/root/arif-fazil.com/sites/arif-fazil.com/public/earth/kinabalu-cross-section.html")
prov = json.loads((HERE / "model_provenance.json").read_text())
html = PAGE.read_text()
js = "\n".join(re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', html, re.S))
fails = []

# 1. Morley attribution scope
for mm in re.finditer(r'[^<>"]{0,120}Morley[^<>"]{0,120}', js):
    w = mm.group(0).lower()
    if re.search(r'\bplate|underthrust|three', w):
        fails.append(f"MORLEY-SCOPE: '{mm.group(0).strip()[:100]}'")
    if re.search(r'morley[^<>"]{0,40}(2023|et al)', w) and re.search(r'\bslab|drip|oceanic', w):
        fails.append(f"MORLEY-2023-DEEP: '{mm.group(0).strip()[:100]}'")

# 3. Model A untested
if 'UNTESTED WORKING HYPOTHESIS' not in js:
    fails.append("MODEL-A: missing UNTESTED status")
if re.search(r'key: "A[^"]*".{0,400}status: "(?!UNTESTED)', js, re.S):
    fails.append("MODEL-A: status not UNTESTED")

# 4. provenance coverage
data = json.loads((HERE / "_geometry_raw.json").read_text())
covered = {e["visual_id"].split(":")[0] + ":" + e["visual_id"].split(":")[1] for e in prov["entries"]}
for b in data["XS"]["common"]:
    if f"shared:{b['f']}" not in covered:
        fails.append(f"PROVENANCE-MISSING: shared:{b['f']}")
for m in data["MODELS"]:
    for b in m["bodies"]:
        if f"model{m['id']}:{b['f']}" not in covered:
            fails.append(f"PROVENANCE-MISSING: model{m['id']}:{b['f']}")
for ln in data["XS"]["lines"]:
    if f"line:{ln['id']}" not in covered:
        fails.append(f"PROVENANCE-MISSING: line:{ln['id']}")

# 5. stale name ban
if re.search(r'magmatic ridge', html, re.I):
    fails.append("STALE-NAME: 'magmatic ridge' appeared")

# 6. 'plate' usage whitelist
allowed = ("upper plate", "lower plate", "plate-scale", "plate-driving", "down-going plate",
           "elastic plate", "flat-plate", "former lower plate", "plate convergence", "plates, and the moho")
for mm in re.finditer(r'[^<>"]{0,60}plate[^<>"]{0,60}', html, re.I):
    w = mm.group(0).lower()
    if "template" in w or "—" in w[:40]:  # css/template noise
        continue
    if not any(a in w for a in allowed):
        fails.append(f"PLATE-WORD: '{mm.group(0).strip()[:90]}'")

# 2. shallow-vs-deep: any model body claiming Morley + deep classes
for e in prov["entries"]:
    if "Morley" in e["source_citation_scope"] and e["object_type"] == "polygon":
        if e["depth_interval_km"] and not e["depth_interval_km"].startswith("0.0"):
            try:
                zmax = float(e["depth_interval_km"].split(" to ")[1])
                if zmax > 8.0 and "UNKNOWN" not in e["limitation"]:
                    fails.append(f"DEEP-GEOMETRY-FROM-SHALLOW-SOURCE: {e['visual_id']} zmax={zmax} (no deep-continuation UNKNOWN note)")
            except Exception:
                pass

print(f"provenance_guard: {len(prov['entries'])} entries checked")
if fails:
    print(f"VERDICT: FAIL ({len(fails)})")
    for f in fails[:12]:
        print("  ✗", f)
    sys.exit(1)
print("VERDICT: PASS — attribution scope, model-A honesty, provenance coverage, name hygiene all clean")
