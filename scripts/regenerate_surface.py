#!/usr/bin/env python3
"""Regenerate GEOX public surface artifacts from tools_manifest.yaml.

W8 hardening pass 2026-07-24.

Source of truth: `src/geox_mcp/tools_manifest.yaml`
Generates:
  - CANONICAL_PUBLIC_SURFACE.json
  - .well-known/tools.json
  - contracts/mcp_surface.yaml (subset, count fields)

This script MUST be idempotent. The public count must match the manifest's
public tool count exactly. Run as part of CI to enforce surface parity.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "src" / "geox_mcp" / "tools_manifest.yaml"
CANONICAL = REPO_ROOT / "CANONICAL_PUBLIC_SURFACE.json"
WELL_KNOWN = REPO_ROOT / ".well-known" / "tools.json"
MCP_SURFACE = REPO_ROOT / "contracts" / "mcp_surface.yaml"


def _load_manifest() -> dict:
    if not MANIFEST.is_file():
        print(f"FATAL: manifest not found at {MANIFEST}", file=sys.stderr)
        sys.exit(2)
    return yaml.safe_load(MANIFEST.read_text())


def _public_tools(manifest: dict) -> list[dict]:
    return [t for t in manifest.get("tools", []) if t.get("visibility") == "public"]


def _regenerate_canonical(manifest: dict) -> int:
    public = _public_tools(manifest)
    payload = {
        "schema": "geox.canonical_public_surface.v1",
        "generated_at": "2026-07-24T11:45:00Z",
        "source": "tools_manifest.yaml",
        "public_count": len(public),
        "internal_count": sum(
            1 for t in manifest.get("tools", []) if t.get("visibility") != "public"
        ),
        "public_tools": [t["name"] for t in public],
        "tools": [
            {
                "name": t["name"],
                "domain": t.get("domain"),
                "description": t.get("description"),
                "axis": t.get("axis"),
                "lane": t.get("lane"),
                "visibility": t.get("visibility"),
            }
            for t in public
        ],
        "rule": "tools/list MUST equal public_tools. Docs must not hardcode counts.",
    }
    CANONICAL.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return len(public)


def _regenerate_well_known(manifest: dict) -> int:
    public = _public_tools(manifest)
    all_tools = manifest.get("tools", [])
    payload = {
        "$schema": "geox.well-known.tools.v1",
        "canonical_tools": len(public),
        "internal_tools": sum(1 for t in all_tools if t.get("visibility") != "public"),
        "manifest_path": "src/geox_mcp/tools_manifest.yaml",
        "organ": manifest.get("organ", "GEOX"),
        "policy": "tools_manifest.yaml is the single source of truth",
        "surface_tools": [t["name"] for t in public],
        "tools": [
            {
                "name": t["name"],
                "domain": t.get("domain"),
                "visibility": t.get("visibility"),
                "description": t.get("description"),
            }
            for t in all_tools
        ],
        "version": manifest.get("manifest_version", "1"),
    }
    WELL_KNOWN.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return len(public)


def _update_mcp_surface_yaml(public_count: int) -> None:
    if not MCP_SURFACE.is_file():
        return
    text = MCP_SURFACE.read_text()
    # Update canonical_tool_count while preserving everything else
    import re

    text = re.sub(
        r"^canonical_tool_count:.*$",
        f"canonical_tool_count: {public_count}",
        text,
        flags=re.MULTILINE,
    )
    MCP_SURFACE.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify surfaces agree with manifest; do not write.",
    )
    args = parser.parse_args()

    manifest = _load_manifest()
    public = _public_tools(manifest)
    expected_count = len(public)
    print(f"manifest public tools: {expected_count}")

    if args.check:
        canonical = json.loads(CANONICAL.read_text())
        canonical_count = canonical.get("public_count", 0)
        if canonical_count != expected_count:
            print(
                f"FAIL: CANONICAL_PUBLIC_SURFACE.json public_count={canonical_count} "
                f"!= manifest public={expected_count}"
            )
            return 1
        print("OK: surface agrees with manifest")
        return 0

    canonical_count = _regenerate_canonical(manifest)
    wk_count = _regenerate_well_known(manifest)
    _update_mcp_surface_yaml(canonical_count)
    print(f"regenerated CANONICAL_PUBLIC_SURFACE.json: {canonical_count} tools")
    print(f"regenerated .well-known/tools.json: {wk_count} surface tools")
    return 0


if __name__ == "__main__":
    sys.exit(main())
