#!/usr/bin/env python3
"""RETIRED 2026-11-24 — legacy surface generator (W8, 2026-07-24).

This script wrote a *lean* CANONICAL_PUBLIC_SURFACE.json at the repo root, a
.well-known/tools.json, and contracts/mcp_surface.yaml — a third writer racing the
two canonical generators, and the source of the duplicate root canonical surface
(lean schema, no capability_packs) that publish_docroot.py mirrored to the site.

The single owners now are:
  * tools.json · .well-known/tools.json · .well-known/openapi.json · llms.txt
        -> scripts/generate_public_registry.py
  * src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json (rich SOT)
    contracts/tools.yaml · tools_sot.yaml · README badge
        -> scripts/generate_all_surfaces.py
  * the public docroot is published from those (scripts/publish_docroot.py)

It FAILS CLOSED rather than silently producing a competing shape, so no automation
can reintroduce duplicate authority. See tests/test_single_writer_surface.py.
"""

from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.stderr.write(
        "regenerate_surface.py is RETIRED (2026-11-24).\n"
        "Use: python3 scripts/generate_all_surfaces.py      (canonical surface/contracts)\n"
        "     python3 scripts/generate_public_registry.py   (tools.json/well-known/llms.txt)\n"
        "     python3 scripts/publish_docroot.py            (publish)\n"
    )
    raise SystemExit(2)
