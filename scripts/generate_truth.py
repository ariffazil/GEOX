#!/usr/bin/env python3
"""
GEOX Truth Generator — Single Source of Truth
==============================================
Reads CANONICAL_PUBLIC_TOOLS from registry.py and generates:
  - server-card.json
  - agent.json (canonical_tools section)
  - capabilities.json
  - llms.txt

Usage:
    python scripts/generate_truth.py

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from geox_mcp.registry import (
    CANONICAL_COMPAT_TOOLS,
    CANONICAL_PUBLIC_TOOLS,
    GEOX_TOOL_MANIFEST,
    INTERNAL_TOOLS,
    SURFACE_TOOLS,
)

ROOT = Path(__file__).parent.parent
NOW = datetime.now(UTC).isoformat()
EPOCH = f"2026-07-07-GEOX-ZEN10-PHASE31"
VERSION = "v2026.07.07-phase3.1-rsi-pipeline"


def generate_server_card():
    """Generate server-card.json from registry."""
    card = {
        "name": "GEOX",
        "version": VERSION,
        "domain": "earth-science/subsurface/petroleum-geology",
        "description": "Governed Earth API for subsurface intelligence. Physics-first. ACRisk-stamped. Claim-disciplined.",
        "governance": "arifOS F1-F13 + ToAC + CANON-9",
        "seal": "DITEMPA BUKAN DIBERI",
        "canonical_tools": len(CANONICAL_PUBLIC_TOOLS),
        "surface_tools": len(SURFACE_TOOLS),
        "internal_tools": len(INTERNAL_TOOLS),
        "backward_compat_tools": len(CANONICAL_COMPAT_TOOLS),
        "total_executable": len(CANONICAL_PUBLIC_TOOLS) + len(CANONICAL_COMPAT_TOOLS),
        "resources": 19,
        "prompts": 9,
        "transport": ["streamable-http", "sse"],
        "auth": {"type": "bearer", "env_var": "GEOX_SECRET_TOKEN"},
        "entrypoint": {"module": "geox_mcp.server", "package": "src"},
        "health_endpoint": "/health",
        "epoch": EPOCH,
        "generated_at": NOW,
        "documentation": {
            "readme": "README.md",
            "capabilities": "resources/capabilities/geox_capabilities.json",
        },
        "maintainer": {"name": "Arif", "org": "arifOS Federation"},
        "license": "AGPL-3.0",
        "repository": "https://github.com/ariffazil/geox",
    }
    out = ROOT / "resources" / "server-card.json"
    out.write_text(json.dumps(card, indent=2) + "\n")
    print(f"  ✅ server-card.json: {card['canonical_tools']} canonical, {card['backward_compat_tools']} compat")


def generate_capabilities():
    """Generate capabilities.json from registry."""
    tools = []
    for name in sorted(CANONICAL_PUBLIC_TOOLS):
        manifest = next((m for m in GEOX_TOOL_MANIFEST if m.get("name") == name), {})
        tools.append(
            {
                "name": name,
                "domain": manifest.get("domain", "unknown"),
                "axis": manifest.get("axis", "unknown"),
                "lane": manifest.get("lane", "unknown"),
                "face": manifest.get("face", "surface"),
            }
        )

    caps = {
        "epoch": EPOCH,
        "generated_at": NOW,
        "version": VERSION,
        "canonical_tool_count": len(CANONICAL_PUBLIC_TOOLS),
        "surface_tool_count": len(SURFACE_TOOLS),
        "internal_tool_count": len(INTERNAL_TOOLS),
        "backward_compat_count": len(CANONICAL_COMPAT_TOOLS),
        "total_executable": len(CANONICAL_PUBLIC_TOOLS) + len(CANONICAL_COMPAT_TOOLS),
        "tools": tools,
        "backward_compat_tools": sorted(CANONICAL_COMPAT_TOOLS),
    }
    out = ROOT / "resources" / "capabilities" / "geox_capabilities.json"
    out.write_text(json.dumps(caps, indent=2) + "\n")
    print(f"  ✅ capabilities.json: {len(tools)} canonical tools")


def generate_agent_card_tools():
    """Update agent.json canonical_tools section from registry."""
    agent_path = ROOT / ".well-known" / "agent.json"
    agent = json.loads(agent_path.read_text())

    agent["canonical_tools"] = {
        "count": len(CANONICAL_PUBLIC_TOOLS),
        "locked": True,
        "lock_file": "src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS",
        "server_runtime_lock": f"src/geox_mcp/server.py:_EXPECTED_CANONICAL={len(CANONICAL_PUBLIC_TOOLS)}",
        "epoch": EPOCH,
        "tools": sorted(CANONICAL_PUBLIC_TOOLS),
        "surface_tools": sorted(SURFACE_TOOLS),
        "internal_plumbing": sorted(INTERNAL_TOOLS),
        "backward_compat_aliases": len(CANONICAL_COMPAT_TOOLS),
    }
    agent["version"] = NOW[:10]
    agent["authentication"]["credentials"] = (
        f"Lease-token issued by arifOS arif_lease_issue; "
        f"{len(SURFACE_TOOLS)} surface tools ({len(CANONICAL_PUBLIC_TOOLS)} canonical) + "
        f"{len(CANONICAL_COMPAT_TOOLS)} backward-compat aliases available. ZEN-10 surface."
    )

    agent_path.write_text(json.dumps(agent, indent=2) + "\n")
    print(f"  ✅ agent.json: {len(CANONICAL_PUBLIC_TOOLS)} canonical, {len(CANONICAL_COMPAT_TOOLS)} compat")


def generate_llms_txt():
    """Generate llms.txt from registry."""
    lines = [
        "# GEOX — Governed Earth Intelligence",
        "",
        f"Version: {VERSION}",
        f"Epoch: {EPOCH}",
        f"Generated: {NOW}",
        "",
        "## Canonical Surface",
        "",
        f"14 canonical tools (10 surface + 4 internal) + 131 backward-compat aliases.",
        "",
        "### Surface Tools (10)",
        "",
    ]
    for name in sorted(SURFACE_TOOLS):
        manifest = next((m for m in GEOX_TOOL_MANIFEST if m.get("name") == name), {})
        lines.append(f"- **{name}** ({manifest.get('domain', 'unknown')}): {manifest.get('axis', 'unknown')}")

    lines.extend(["", "### Internal Tools (4)", ""])
    for name in sorted(INTERNAL_TOOLS):
        lines.append(f"- **{name}**")

    lines.extend(
        [
            "",
            "## Backward Compatibility",
            "",
            f"131 legacy tool names are accepted by middleware and routed to canonical dimension tools.",
            "Migration routes are defined in src/geox_mcp/surface_migration.py.",
            "",
            "## Governance",
            "",
            "- F1-F13 constitutional floors enforced",
            "- Lane-based authority: discovery/evidence/reasoning/judgment",
            "- Judgment lane tools MUST route through arifOS kernel",
            "- Evidence-only: GEOX never self-judges",
            "",
            "## Transport",
            "",
            "- Streamable HTTP (primary)",
            "- SSE (legacy)",
            "- Stdio (local agents)",
            "",
        ]
    )

    out = ROOT / "resources" / "llms.txt"
    out.write_text("\n".join(lines) + "\n")
    print(f"  ✅ llms.txt: {len(lines)} lines")


if __name__ == "__main__":
    print("GEOX Truth Generator — Single Source of Truth")
    print("=" * 50)
    print(f"Source: registry.py")
    print(f"  CANONICAL_PUBLIC_TOOLS: {len(CANONICAL_PUBLIC_TOOLS)}")
    print(f"  SURFACE_TOOLS: {len(SURFACE_TOOLS)}")
    print(f"  INTERNAL_TOOLS: {len(INTERNAL_TOOLS)}")
    print(f"  CANONICAL_COMPAT_TOOLS: {len(CANONICAL_COMPAT_TOOLS)}")
    print()

    generate_server_card()
    generate_capabilities()
    generate_agent_card_tools()
    generate_llms_txt()

    print()
    print("All descriptors generated from registry.py.")
    print("Run this after any change to the canonical tool surface.")
