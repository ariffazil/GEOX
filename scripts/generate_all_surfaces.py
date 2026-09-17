#!/usr/bin/env python3
"""Regenerate ALL surface artifacts from registry.py::CANONICAL_PUBLIC_TOOLS.

registry.py is the ONLY truth. Every surface is GENERATED from it.
This script overwrites drifted surfaces to match.

Usage:
  python scripts/generate_all_surfaces.py              # regenerate all
  python scripts/generate_all_surfaces.py --dry-run    # show what would change

Surfaces regenerated:
  1. tools_sot.yaml
  2. src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json
  3. tools.json (root)
  4. llms.txt header + tool list
  5. contracts/tools.yaml
  6. README.md badge + capabilities heading
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, GHOST_TOOLS  # noqa: E402
from geox_mcp.surface_manifest import (  # noqa: E402
    load_surface_manifest,
    manifest_tool_map,
    public_tool_names,
    capability_packs,
    workflow_packs,
    earth_capability_graph,
)
from geox_mcp.registry import (  # noqa: E402
    tools_for_profile,
    discovery_profile_names,
)

TRUTH_SET: set[str] = set(CANONICAL_PUBLIC_TOOLS)
TRUTH_COUNT: int = len(CANONICAL_PUBLIC_TOOLS)
TRUTH_SORTED: list[str] = sorted(CANONICAL_PUBLIC_TOOLS)
NOW_UTC = datetime.now(timezone.utc).isoformat()

changes: list[str] = []


def diff_label(path: str, before: str, after: str) -> None:
    """Record a change for summary."""
    if before.strip() != after.strip():
        changes.append(f"  CHANGED: {path}")
    else:
        changes.append(f"  UNCHANGED: {path}")


def get_tool_metadata(name: str) -> dict:
    """Get tool metadata from manifest for a given tool name."""
    tool_map = manifest_tool_map()
    entry = tool_map.get(name)
    if entry is None:
        return {
            "name": name,
            "domain": "unknown",
            "axis": "unknown",
            "lane": "unknown",
            "description": "",
            "governance": {"action_class": "OBSERVE"},
            "family": "unclassified",
            "tier": "Z",
        }
    return {
        "name": entry.name,
        "domain": entry.domain,
        "axis": entry.axis,
        "lane": entry.lane,
        "description": entry.description,
        "ui": entry.ui,
        "governance": entry.governance,
        "family": entry.family,
        "tier": entry.tier,
        "subfamily": entry.subfamily,
    }


def regenerate_tools_sot_yaml(dry_run: bool) -> None:
    """Regenerate tools_sot.yaml."""
    path = ROOT / "tools_sot.yaml"
    before = path.read_text() if path.exists() else ""

    tools = []
    for name in TRUTH_SORTED:
        meta = get_tool_metadata(name)
        tools.append(
            {
                "name": name,
                "domain": meta["domain"],
                "axis": meta["axis"],
                "lane": meta["lane"],
                "family": meta["family"],
                "tier": meta["tier"],
                "access": "public",
                "description": meta["description"] or f"GEOX tool: {name}",
                "annotations": {
                    "read_only": True,
                    "destructive": False,
                    "idempotent": True,
                },
            }
        )

    # Tier distribution summary
    tier_dist = {}
    for t in tools:
        tier_dist[t["tier"]] = tier_dist.get(t["tier"], 0) + 1

    data = {
        "organ": "GEOX",
        "version": datetime.now(timezone.utc).strftime("%Y.%m.%d"),
        "sot_source": "registry.py::CANONICAL_PUBLIC_TOOLS",
        "live_port": 8081,
        "public_count": TRUTH_COUNT,
        "regenerated": NOW_UTC,
        "regenerated_by": "generate_all_surfaces.py (registry.py truth)",
        "sprint1_classified": True,
        "tier_distribution": tier_dist,
        "tools": tools,
    }

    after = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    diff_label("tools_sot.yaml", before, after)

    if not dry_run:
        path.write_text(after)
        print(f"  ✓ Wrote tools_sot.yaml ({TRUTH_COUNT} tools)")
    else:
        print(f"  → Would write tools_sot.yaml ({TRUTH_COUNT} tools)")


def regenerate_canonical_public_surface_json(dry_run: bool) -> None:
    """Regenerate src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json."""
    path = ROOT / "src" / "geox_mcp" / "generated" / "CANONICAL_PUBLIC_SURFACE.json"
    before = path.read_text() if path.exists() else ""

    tools_list = []
    for name in TRUTH_SORTED:
        meta = get_tool_metadata(name)
        entry = {
            "name": name,
            "domain": meta["domain"],
            "axis": meta["axis"],
            "lane": meta["lane"],
            "family": meta["family"],
            "tier": meta["tier"],
            "description": meta["description"] or f"GEOX tool: {name}",
            "ui": meta.get("ui"),
            "governance": meta["governance"],
        }
        if meta.get("subfamily"):
            entry["subfamily"] = meta["subfamily"]
        tools_list.append(entry)

    packs = capability_packs()
    workflows = workflow_packs()
    graph = earth_capability_graph()

    # Discovery profiles with tool lists
    profiles = {}
    for pname in discovery_profile_names():
        profiles[pname] = {
            "tools": tools_for_profile(pname),
            "count": len(tools_for_profile(pname)),
        }

    data = {
        "schema": "geox.canonical_public_surface.v2",
        "generated_at": NOW_UTC,
        "source": "registry.py::CANONICAL_PUBLIC_TOOLS",
        "public_count": TRUTH_COUNT,
        "internal_count": len(GHOST_TOOLS),
        "public_tools": TRUTH_SORTED,
        "tools": tools_list,
        "families": sorted(set(m["family"] for m in tools_list)),
        "tier_distribution": {
            tier: [t["name"] for t in tools_list if t["tier"] == tier] for tier in sorted(set(t["tier"] for t in tools_list))
        },
        "capability_packs": packs,
        "discovery_profiles": profiles,
        "workflow_packs": workflows,
        "earth_capability_graph": graph,
        "rule": "tools/list MUST equal public_tools. Docs must not hardcode counts.",
    }

    after = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    diff_label("CANONICAL_PUBLIC_SURFACE.json", before, after)

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after)
        print(f"  ✓ Wrote CANONICAL_PUBLIC_SURFACE.json ({TRUTH_COUNT} tools)")
    else:
        print(f"  → Would write CANONICAL_PUBLIC_SURFACE.json ({TRUTH_COUNT} tools)")


def regenerate_tools_json(dry_run: bool) -> None:
    """Regenerate tools.json (root)."""
    path = ROOT / "tools.json"
    before = path.read_text() if path.exists() else ""

    # Read existing to preserve internal list if present
    existing = {}
    if path.exists():
        try:
            existing = json.loads(before)
        except json.JSONDecodeError:
            pass

    data = {
        "app_export": TRUTH_SORTED,
        "internal": existing.get("internal", []),
        "manifest_path": "src/geox_mcp/registry.py::CANONICAL_PUBLIC_TOOLS",
        "public": TRUTH_SORTED,
        "version": datetime.now(timezone.utc).strftime("%Y.%m.%d"),
        "policy": f"Generated {NOW_UTC} — public = registry.py::CANONICAL_PUBLIC_TOOLS ({TRUTH_COUNT} tools)",
    }

    after = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    diff_label("tools.json", before, after)

    if not dry_run:
        path.write_text(after)
        print(f"  ✓ Wrote tools.json ({TRUTH_COUNT} tools)")
    else:
        print(f"  → Would write tools.json ({TRUTH_COUNT} tools)")


def regenerate_llms_txt(dry_run: bool) -> None:
    """Regenerate llms.txt header and tool list."""
    path = ROOT / "llms.txt"
    before = path.read_text() if path.exists() else ""

    # Group tools by family
    family_groups: dict[str, list[dict]] = {}
    for name in TRUTH_SORTED:
        meta = get_tool_metadata(name)
        fam = meta.get("family", "unclassified")
        family_groups.setdefault(fam, []).append({"name": name, "meta": meta, "tier": meta.get("tier", "Z")})

    family_labels = {
        "evidence": "1. Evidence & Orientation",
        "ingest": "2. Data Intake & QC",
        "interpret": "3. Earth Interpretation",
        "model": "4. Integration & Models",
        "prospect": "5. Prospect & Decision",
        "view": "6. Presentation",
        "research": "7. Research / Cascade Lab",
        "seismic": "8. Seismic Sources & Traces",
        "structural": "9. Structural Calibration",
    }
    tier_labels = {"A": "Core", "B": "Specialist", "C": "Research", "Z": "Internal"}

    tool_lines = []
    ordered_families = [
        "evidence",
        "ingest",
        "interpret",
        "model",
        "prospect",
        "view",
        "research",
        "seismic",
        "structural",
    ]
    leftover_families = [f for f in family_groups if f not in ordered_families]
    for fam_key in ordered_families + leftover_families:
        group = family_groups.get(fam_key, [])
        if not group:
            continue
        label = family_labels.get(fam_key, fam_key.title())
        tool_lines.append(f"### {label}")
        tool_lines.append("")
        for item in sorted(group, key=lambda x: x["name"]):
            name = item["name"]
            meta = item["meta"]
            tier = item["tier"]
            desc = meta["description"] or f"GEOX tool: {name}"
            tier_label = tier_labels.get(tier, tier)
            tool_lines.append(f"- **{name}** [Tier {tier} — {tier_label}]: {desc}")
        tool_lines.append("")

    lines = [
        f"# GEOX — Earth Intelligence Sovereign Kernel ({TRUTH_COUNT} Public Tools)",
        "> Doctrine: Physics before narrative. Governed evidence only.",
        "> Surface: generated from registry.py::CANONICAL_PUBLIC_TOOLS",
        f"> Capability families: {len(family_groups)} | Sprint 1 classified",
        "",
        "## 1. Capability Graph — Tool Surface",
        "",
    ]
    lines.extend(tool_lines)
    lines.extend(
        [
            "## 2. Tier Legend",
            "- **Tier A (Core)**: Default discovery. All agents see these.",
            "- **Tier B (Specialist)**: Opt-in after task declaration.",
            "- **Tier C (Research)**: Advanced/research. Not visible by default.",
            "",
            "## 3. Capability Packs",
            "",
            "### earth_core (Tier A — 13 tools)",
            "Default discovery surface. Basin context, data validation, well/seismic interpretation, prospect assessment.",
            "",
            "### earth_specialist (Tier B — 6 tools)",
            "Opt-in. Seismic computation, geomechanics, data ingestion, paleobiology.",
            "",
            "### earth_research (Tier C — 7 tools)",
            "Advanced/research only. Sub-packs:",
            "- **cascade** (5): GLOF cascade simulation (initialize, step, phase, metabolize, propagate)",
            "- **inversion** (2): Bayesian inference (inverse, mcmc_inverse)",
            "- **restoration** (0): Structural restoration (PLANNED)",
            "- **simulation** (0): Stratigraphic simulation (PLANNED)",
            "- **uncertainty** (0): Uncertainty quantification (PLANNED)",
            "",
            "## 4. Workflow Packs",
            "",
            "### well_to_correlation (7 steps → CorrelationPackage)",
            "basin → well → well_qc → petrophysics → deep_time → model → map",
            "",
            "### seismic_to_prospect (8 steps → ProspectEvidencePackage)",
            "basin → seismic_ingest → seismic_compute → seismic_interpret → geomechanics → model → prospect → claim",
            "",
            "### basin_screening (8 steps → PlayFairwaySummary)",
            "basin → spatial → temporal → source → deep_time → claim → prospect → map",
            "",
            "### glof_uncertainty (6 steps → UncertaintyReport)",
            "initialize → propagate → phase → inverse → mcmc_inverse → metabolize",
            "",
            "## 5. Agent Reasoning Logic",
            "- Evidence before interpretation.",
            "- Governance stays server-side.",
            "- App-enabled workspace URI: `ui://geox/workspace-v1.html` (text/html;profile=mcp-app).",
        ]
    )

    after = "\n".join(lines) + "\n"
    diff_label("llms.txt", before, after)

    if not dry_run:
        path.write_text(after)
        print(f"  ✓ Wrote llms.txt ({TRUTH_COUNT} tools)")
    else:
        print(f"  → Would write llms.txt ({TRUTH_COUNT} tools)")


def regenerate_contracts_tools_yaml(dry_run: bool) -> None:
    """Regenerate contracts/tools.yaml."""
    path = ROOT / "contracts" / "tools.yaml"
    before = path.read_text() if path.exists() else ""

    tools_dict = {}
    for name in TRUTH_SORTED:
        meta = get_tool_metadata(name)
        tools_dict[name] = {
            "category": meta["domain"],
            "lane": meta["lane"],
            "family": meta["family"],
            "capability_tier": meta["tier"],
            "risk_tier": "readonly",
            "description": meta["description"] or f"GEOX tool: {name}",
        }

    data = {
        "schema_version": datetime.now(timezone.utc).strftime("%Y.%m.%d"),
        "organ": "GEOX",
        "authority": "ariffazil/geox",
        "mcp_transport": "streamable-http",
        "mcp_endpoints": {
            "direct": "https://geox.arif-fazil.com/mcp",
            "kernel_gateway": "https://mcp.arif-fazil.com/mcp",
            "local": "http://127.0.0.1:8081/mcp",
        },
        "health_endpoint": "http://127.0.0.1:8081/health",
        "canonical_tool_count": TRUTH_COUNT,
        "contract_epoch": f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-GEOX-{TRUTH_COUNT}TOOLS-ZEN",
        "source_of_truth": "src/geox_mcp/registry.py::CANONICAL_PUBLIC_TOOLS",
        "floor_enforcement": "delegated-to-arifos",
        "physics_boundary": "Physics9",
        "tools": tools_dict,
    }

    header = (
        "# GEOX Earth Intelligence Tool Registry\n"
        "# SOT: src/geox_mcp/registry.py — CANONICAL_PUBLIC_TOOLS\n"
        f"# Regenerated: {NOW_UTC}\n"
        "#\n"
        "# DITEMPA BUKAN DIBERI — Forged, Not Given.\n"
        "#\n"
        "# THIS FILE IS GENERATED FROM registry.py. DO NOT EDIT MANUALLY.\n"
        "# The single source of truth is src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS.\n"
        "# If tools.yaml and registry.py disagree, registry.py wins.\n\n"
    )

    after = header + yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    diff_label("contracts/tools.yaml", before, after)

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after)
        print(f"  ✓ Wrote contracts/tools.yaml ({TRUTH_COUNT} tools)")
    else:
        print(f"  → Would write contracts/tools.yaml ({TRUTH_COUNT} tools)")


def regenerate_readme_badge(dry_run: bool) -> None:
    """Regenerate README.md badge count and capabilities heading."""
    path = ROOT / "README.md"
    if not path.exists():
        print(f"  ⚠ README.md not found, skipping")
        return

    text = path.read_text()
    original = text

    # Fix badge: GEOX-NN Canonical Tools (self-heal: insert after title if absent)
    if re.search(r"GEOX-\d+\s+Canonical\s+Tools", text):
        text = re.sub(
            r"GEOX-\d+\s+Canonical\s+Tools",
            f"GEOX-{TRUTH_COUNT} Canonical Tools",
            text,
        )
    else:
        text = re.sub(
            r"(^# .+$)",
            rf"\1\n\n![GEOX-{TRUTH_COUNT} Canonical Tools](https://img.shields.io/badge/GEOX-{TRUTH_COUNT}_Canonical_Tools-0b7285)",
            text,
            count=1,
            flags=re.MULTILINE,
        )

    # Fix capabilities heading: Core Capabilities (N Tools)
    text = re.sub(
        r"Core\s+Capabilities\s*\(\d+\s+Tools\)",
        f"Core Capabilities ({TRUTH_COUNT} Tools)",
        text,
    )

    # Fix MCP tools mermaid reference: "N MCP tools"
    text = re.sub(
        r"\d+\s+MCP\s+tools",
        f"{TRUTH_COUNT} MCP tools",
        text,
    )

    # Fix SOT-MANIFEST header mcp_tools_live
    text = re.sub(
        r"mcp_tools_live:\s*\d+",
        f"mcp_tools_live: {TRUTH_COUNT}",
        text,
    )

    diff_label("README.md", original, text)

    if not dry_run:
        path.write_text(text)
        print(f"  ✓ Updated README.md (badge={TRUTH_COUNT})")
    else:
        print(f"  → Would update README.md (badge={TRUTH_COUNT})")


def main() -> int:
    ap = argparse.ArgumentParser(description="Regenerate all GEOX surfaces from registry.py truth")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    args = ap.parse_args()

    print(f"═══ GEOX Surface Regeneration ═══")
    print(f"  Truth source: registry.py::CANONICAL_PUBLIC_TOOLS")
    print(f"  Truth count:  {TRUTH_COUNT}")
    print(f"  Truth tools:  {TRUTH_SORTED}")
    print(f"  Mode:         {'DRY-RUN' if args.dry_run else 'WRITE'}")
    print()

    load_surface_manifest.cache_clear()

    surfaces = [
        ("tools_sot.yaml", regenerate_tools_sot_yaml),
        ("CANONICAL_PUBLIC_SURFACE.json", regenerate_canonical_public_surface_json),
        ("tools.json", regenerate_tools_json),
        ("llms.txt", regenerate_llms_txt),
        ("contracts/tools.yaml", regenerate_contracts_tools_yaml),
        ("README.md", regenerate_readme_badge),
    ]

    for name, fn in surfaces:
        print(f"── {name} ──")
        fn(dry_run=args.dry_run)
        print()

    print(f"═══ SUMMARY ═══")
    for c in changes:
        print(c)
    print(f"\n  Total surfaces: {len(surfaces)}")
    print(f"  Changed: {sum(1 for c in changes if 'CHANGED' in c)}")
    print(f"  Unchanged: {sum(1 for c in changes if 'UNCHANGED' in c)}")

    if args.dry_run:
        print(f"\n  DRY-RUN complete. No files were written.")
    else:
        print(f"\n  All surfaces regenerated from registry.py truth.")
        # Run check to verify
        print(f"\n═══ POST-GENERATION VERIFICATION ═══")
        import subprocess

        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_registry_truth.py"), "--strict"],
            cwd=str(ROOT),
            capture_output=False,
        )
        return result.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
