#!/usr/bin/env python3
"""Render the GEOX public-surface sitemap from PUBLIC_SURFACE_MANIFEST.json.

This is the deterministic public-surface assembly tool. It is the ONLY writer
for `apps/site/sitemap.xml`. The manifest is the single source of truth — the
sitemap is a derived artifact.

Why this exists:
  - The previous sitemap listed /wiki.html and /network.html that no backing
    asset provides (soft-404). It also under-published the cockpit overlays,
    basin workflow, and MCP Apps catalogue.
  - A future sweep that re-emits the sitemap MUST consume this manifest so the
    "no-delete sync" preserved_overlays list cannot be silently dropped.

Usage:
  python scripts/render_public_surface.py            # writes sitemap
  python scripts/render_public_surface.py --check    # exits 1 if drift

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "static" / "PUBLIC_SURFACE_MANIFEST.json"
SITEMAP = REPO_ROOT / "apps" / "site" / "sitemap.xml"


def _load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _build_sitemap(manifest: dict) -> str:
    base_url = manifest["base_url"].rstrip("/")
    urlset = ET.Element("urlset", xmlns="http://sitemaps.org/schemas/sitemap/0.9")

    for route in manifest["routes"]:
        if "sitemap" not in route.get("exposed_via", []):
            continue
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = f"{base_url}{route['path']}"
        ET.SubElement(url, "lastmod").text = route["lastmod"]
        ET.SubElement(url, "priority").text = f"{route['priority']:.2f}"

    rough = ET.tostring(urlset, encoding="unicode")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ")
    return pretty.split("\n", 1)[1] + "\n" if pretty.startswith("<?xml") else pretty


def render() -> str:
    manifest = _load_manifest()
    return _build_sitemap(manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render GEOX sitemap from manifest")
    parser.add_argument("--check", action="store_true", help="Verify sitemap matches manifest; exit 1 on drift")
    args = parser.parse_args()

    rendered = render()

    if args.check:
        if not SITEMAP.exists():
            print(f"FAIL: {SITEMAP} does not exist — run without --check to write it", file=sys.stderr)
            return 1
        existing = SITEMAP.read_text(encoding="utf-8")
        if existing != rendered:
            print(f"FAIL: {SITEMAP} drift vs manifest. Re-run `python scripts/render_public_surface.py`.", file=sys.stderr)
            return 1
        print(f"OK: {SITEMAP} matches manifest")
        return 0

    SITEMAP.parent.mkdir(parents=True, exist_ok=True)
    SITEMAP.write_text(rendered, encoding="utf-8")
    print(f"WROTE: {SITEMAP} ({len(rendered)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
