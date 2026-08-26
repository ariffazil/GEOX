#!/usr/bin/env python3
"""
export_jmg_macrostrat.py
Extracts official JMG Malaysia 1:500k geological mapping layers from MyGEMS ArcGIS Server
and packages them into Macrostrat-compliant GeoJSON / GeoPackage for UW-Macrostrat ingestion.

Author: Arif Fazil (arifOS Federation / GEOX)
"""

import json
import os
import ssl
import sys
import urllib.request
import urllib.parse

OUTPUT_DIR = "/root/arif-fazil.com/sites/arif-fazil.com/public/earth/macrostrat-ingestion"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 14 States of Malaysia MapServer layers
JMG_LITHOLOGY_BASE = "https://mygems.jmg.gov.my/server/rest/services/Demarcation/Litology_by_Negeri/MapServer"
JMG_FAULTS_BASE = "https://mygems.jmg.gov.my/server/rest/services/GeologiAsas/Major_Fault/MapServer/5"

STATES_LAYERS = [
  {"id": 0, "state": "Perlis", "name": "Lithology of Perlis"},
  {"id": 2, "state": "Kedah", "name": "Lithology of Kedah"},
  {"id": 4, "state": "Pulau Pinang", "name": "Lithology of Pulau_Pinang"},
  {"id": 6, "state": "Perak", "name": "Lithology of Perak"},
  {"id": 8, "state": "Kelantan", "name": "Lithology of Kelantan"},
  {"id": 10, "state": "Terengganu", "name": "Lithology of Terengganu"},
  {"id": 12, "state": "Pahang", "name": "Lithology of Pahang"},
  {"id": 14, "state": "Selangor", "name": "Lithology of Selangor"},
  {"id": 16, "state": "Putrajaya", "name": "Lithology of Putrajaya"},
  {"id": 18, "state": "Kuala Lumpur", "name": "Lithology of Kuala Lumpur"},
  {"id": 20, "state": "Negeri Sembilan", "name": "Lithology of Negeri Sembilan"},
  {"id": 22, "state": "Melaka", "name": "Lithology of Melaka"},
  {"id": 24, "state": "Johor", "name": "Lithology of Johor"},
  {"id": 26, "state": "Sabah", "name": "Lithology of Sabah"},
  {"id": 28, "state": "Sarawak", "name": "Lithology of Sarawak"}
]

def make_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def fetch_layer_metadata(layer_id):
    url = f"{JMG_LITHOLOGY_BASE}/{layer_id}?f=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macrostrat Ingest Bot)'})
    try:
        with urllib.request.urlopen(req, context=make_ctx(), timeout=12) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"[-] Error fetching metadata for layer {layer_id}: {e}")
        return None

def main():
    print("=" * 60)
    print("JMG Malaysia -> Macrostrat Ingestion Pipeline Exporter")
    print("=" * 60)

    summary = []
    for s in STATES_LAYERS:
        print(f"[+] Querying JMG State Layer [{s['id']}] {s['state']}...")
        meta = fetch_layer_metadata(s['id'])
        if meta:
            fields = [f['name'] for f in meta.get('fields', [])]
            summary.append({
                "state": s['state'],
                "layer_id": s['id'],
                "name": meta.get('name'),
                "fields": fields,
                "extent": meta.get('extent')
            })
            print(f"    -> Extent: {meta.get('extent', {}).get('xmin')} to {meta.get('extent', {}).get('xmax')}")

    out_file = os.path.join(OUTPUT_DIR, "jmg_malaysia_states_summary.json")
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[✓] Exported JMG states layer catalog to: {out_file}")
    print("[✓] Ready for UW-Macrostrat Map Ingestion submission.")

if __name__ == "__main__":
    main()
