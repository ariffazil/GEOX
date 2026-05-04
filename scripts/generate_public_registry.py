#!/usr/bin/env python3
"""
Generate Public Tool Registry — GEOX Canonical Surface
====================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Reads CANONICAL_TOOLS from contracts.enums.statuses,
computes a SHA-256 hash of the canonical surface,
and writes a public registry JSON for runtime parity verification.

Run after any change to the canonical tool surface:
    python scripts/generate_public_registry.py

Verify parity:
    python -c "from control_plane_server_patch import compute_registry_hash; print(compute_registry_hash())"

Epoch: GEOX-11TOOLS-v0.3
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent.parent / "public_registry.json"


def load_canonical_tools() -> list[str]:
    """Load CANONICAL_TOOLS from contracts.enums.statuses."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from contracts.enums.statuses import CANONICAL_TOOLS
    return CANONICAL_TOOLS


def compute_hash(tools: list[str]) -> str:
    """Compute SHA-256 hash of the canonical tool surface."""
    canonical_sorted = sorted(tools)
    payload = json.dumps(
        {
            "epoch": "GEOX-11TOOLS-v0.3",
            "tools": canonical_sorted,
            "count": len(canonical_sorted),
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
        sort_keys=True,
        indent=2,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def main():
    print("GEOX Public Registry Generator")
    print("=" * 40)

    try:
        tools = load_canonical_tools()
    except Exception as exc:
        print(f"ERROR: Could not load CANONICAL_TOOLS: {exc}")
        sys.exit(1)

    canonical_hash = compute_hash(tools)
    tool_count = len(tools)

    registry = {
        "epoch": "GEOX-11TOOLS-v0.3",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "canonical_tool_count": tool_count,
        "registry_hash": canonical_hash,
        "tools": sorted(tools),
        "manifest_hash_source": "SHA-256(canonical_tools_sorted)",
    }

    # Write public registry
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)

    # Console output
    print(f"Canonical tools : {tool_count}")
    print(f"Registry hash   : {canonical_hash}")
    print(f"Registry written: {REGISTRY_PATH}")
    print()
    print("Canonical surface:")
    for i, tool in enumerate(sorted(tools), 1):
        print(f"  {i:2d}. {tool}")

    # Verify
    if tool_count != 13:
        print()
        print(f"WARNING: Expected 13 canonical tools, got {tool_count}")
        print("Update contracts/enums/statuses.py CANONICAL_TOOLS before proceeding.")

    print()
    print("Registry generation complete.")


if __name__ == "__main__":
    main()
