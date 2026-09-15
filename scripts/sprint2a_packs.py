#!/usr/bin/env python3
"""Sprint 2A: Add capability_packs + research sub-family to tools_manifest.yaml.

Pack registry = explicit tool groupings for discovery filtering.
Research sub-families prevent future entropy dumping.
"""

from __future__ import annotations

import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "src" / "geox_mcp" / "tools_manifest.yaml"

# ── Research sub-family mapping ─────────────────────────────────────────
RESEARCH_SUBFAMILY: dict[str, str] = {
    "geox_glof_cascade_initialize":  "cascade",
    "geox_glof_cascade_step":        "cascade",
    "geox_glof_cascade_phase":       "cascade",
    "geox_glof_cascade_metabolize":  "cascade",
    "geox_glof_cascade_propagate":   "cascade",
    "geox_glof_cascade_inverse":     "inversion",
    "geox_glof_cascade_mcmc_inverse": "inversion",
}

# ── Capability Pack definitions ─────────────────────────────────────────
CAPABILITY_PACKS = {
    "earth_core": {
        "tier": "A",
        "label": "Earth Core",
        "description": "Default discovery surface. All agents see these tools.",
        "intent": "Evaluate basin context, validate data, interpret wells/seismic, assess prospects.",
        "tools": [
            "geox_basin", "geox_claim", "geox_deep_time", "geox_map",
            "geox_model", "geox_prospect", "geox_seismic_interpret",
            "geox_source", "geox_spatial", "geox_temporal",
            "geox_petrophysics", "geox_well", "geox_well_qc",
        ],
    },
    "earth_specialist": {
        "tier": "B",
        "label": "Earth Specialist",
        "description": "Opt-in after task declaration. Seismic computation, geomechanics, data ingestion.",
        "intent": "Process raw data, run computations, analyze paleobiology.",
        "tools": [
            "geox_contrast_metabolize", "geox_geomechanics",
            "geox_paleobiodb_query", "geox_seismic_compute",
            "geox_seismic_ingest", "geox_well_ingest",
        ],
    },
    "earth_research": {
        "tier": "C",
        "label": "Earth Research",
        "description": "Advanced/research only. GLOF cascade simulation, Bayesian inversion.",
        "intent": "Run experimental Earth-science computations under bounded resources.",
        "sub_packs": {
            "cascade": {
                "label": "GLOF Cascade Simulation",
                "tools": [
                    "geox_glof_cascade_initialize", "geox_glof_cascade_step",
                    "geox_glof_cascade_phase", "geox_glof_cascade_metabolize",
                    "geox_glof_cascade_propagate",
                ],
            },
            "inversion": {
                "label": "Bayesian Inversion",
                "tools": [
                    "geox_glof_cascade_inverse", "geox_glof_cascade_mcmc_inverse",
                ],
            },
            "restoration": {
                "label": "Structural Restoration (PLANNED)",
                "tools": [],
            },
            "simulation": {
                "label": "Stratigraphic Simulation (PLANNED)",
                "tools": [],
            },
            "uncertainty": {
                "label": "Uncertainty Quantification (PLANNED)",
                "tools": [],
            },
        },
        "tools": [
            "geox_glof_cascade_initialize", "geox_glof_cascade_step",
            "geox_glof_cascade_phase", "geox_glof_cascade_inverse",
            "geox_glof_cascade_mcmc_inverse", "geox_glof_cascade_metabolize",
            "geox_glof_cascade_propagate",
        ],
    },
}


def add_capability_packs(dry_run: bool = False) -> int:
    with open(MANIFEST_PATH) as f:
        manifest = yaml.safe_load(f)

    tools = manifest["tools"]

    # Add subfamily to research tools
    subfamily_count = 0
    for tool in tools:
        name = tool["name"]
        if name in RESEARCH_SUBFAMILY:
            tool["subfamily"] = RESEARCH_SUBFAMILY[name]
            subfamily_count += 1
        elif tool.get("family") == "research" and "subfamily" not in tool:
            tool["subfamily"] = "unclassified"

    # Add capability_packs section
    manifest["capability_packs"] = CAPABILITY_PACKS

    if not dry_run:
        with open(MANIFEST_PATH, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False,
                      allow_unicode=True, width=120)
        print(f"  ✓ Added capability_packs ({len(CAPABILITY_PACKS)} packs)")
        print(f"  ✓ Added subfamily to {subfamily_count} research tools")
        for pack_name, pack in CAPABILITY_PACKS.items():
            print(f"    {pack_name}: {len(pack['tools'])} tools (tier {pack['tier']})")
            if "sub_packs" in pack:
                for sp_name, sp in pack["sub_packs"].items():
                    print(f"      └─ {sp_name}: {len(sp['tools'])} tools")
    else:
        print(f"  → Would add {len(CAPABILITY_PACKS)} capability packs")
        print(f"  → Would add subfamily to {subfamily_count} research tools")

    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    raise SystemExit(add_capability_packs(dry_run=dry))
