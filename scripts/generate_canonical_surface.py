#!/usr/bin/env python3
"""Regenerate CANONICAL_PUBLIC_SURFACE.json from tools_manifest.yaml."""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from geox_mcp.surface_manifest import (  # noqa: E402
    internal_tool_names,
    load_surface_manifest,
    manifest_tools,
    public_tool_names,
)


def main() -> None:
    load_surface_manifest.cache_clear()
    public = public_tool_names()
    internal = internal_tool_names()
    tools = []
    for t in manifest_tools():
        if t.visibility != "public":
            continue
        tools.append({
            "name": t.name,
            "domain": t.domain,
            "axis": t.axis,
            "lane": t.lane,
            "description": (t.description or "")[:200],
            "ui": t.ui,
            "governance": t.governance,
        })
    out = {
        "schema": "geox.canonical_public_surface.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "tools_manifest.yaml",
        "public_count": len(public),
        "internal_count": len(internal),
        "public_tools": public,
        "tools": tools,
        "rule": "tools/list MUST equal public_tools. Docs must not hardcode counts.",
    }
    for rel in (
        "CANONICAL_PUBLIC_SURFACE.json",
        "src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json",
        # docs/ target = per-release snapshot the README and CI can reference.
        # Kills the "52 vs 31" prose-drift class permanently: if the count in
        # the snapshot diverges from the live tools/list, the drift test fails.
        "docs/canonical_public_tools.json",
    ):
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, indent=2) + "\n")
        print("wrote", path, "public_count=", out["public_count"])

if __name__ == "__main__":
    main()
