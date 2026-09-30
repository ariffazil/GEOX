#!/usr/bin/env python3
"""Structural Restoration Parity Check — P0-005.

Validates that:
  registry tools_sot.yaml
  = registry structural_restoration_registry.yaml
  = wiring.py registered functions

Run: python3 scripts/check_structural_restoration_parity.py
Exit 0 = PASS, Exit 1 = FAIL.

Forged: 2026-09-14
"""

import sys
from pathlib import Path

import yaml

ROOT = Path("/root/GEOX")
SOT_PATH = ROOT / "tools_sot.yaml"
REGISTRY_PATH = ROOT / "src/geox_mcp/registry/structural_restoration_registry.yaml"
WIRING_PATH = ROOT / "src/geox_mcp/tools/structural_restoration/wiring.py"

EXPECTED_TOOLS = [
    "geox_validate_restoration_inputs",
    "geox_compute_accommodation_space",
    "geox_compute_basement_subsidence",
    "geox_compute_fill_ratio",
    "geox_propagate_compaction_uncertainty",
    "geox_build_distance_weighted_uncertainty",
    "geox_analyse_fault_inheritance",
    "geox_qc_seismic_fault_geomechanics",
    "geox_run_forward_inverse_test",
]


def check_sot():
    """Check tools_sot.yaml contains all expected tools."""
    with open(SOT_PATH) as f:
        sot = yaml.safe_load(f)
    sot_names = {t["name"] for t in sot.get("tools", [])}
    missing = [t for t in EXPECTED_TOOLS if t not in sot_names]
    return missing


def check_registry():
    """Check structural_restoration_registry.yaml contains all expected tools."""
    with open(REGISTRY_PATH) as f:
        reg = yaml.safe_load(f)
    reg_names = {t["name"] for t in reg.get("tools", [])}
    missing = [t for t in EXPECTED_TOOLS if t not in reg_names]
    return missing


def check_wiring():
    """Check wiring.py contains all expected tool registrations."""
    content = WIRING_PATH.read_text()
    missing = [t for t in EXPECTED_TOOLS if f'name="{t}"' not in content]
    return missing


def check_invariants():
    """Check each tool has invariant references in SOT."""
    with open(SOT_PATH) as f:
        sot = yaml.safe_load(f)
    missing_invariants = []
    for t in sot.get("tools", []):
        if t["name"] in EXPECTED_TOOLS and "invariants" not in t:
            missing_invariants.append(t["name"])
    return missing_invariants


def main():
    errors = []

    # 1. SOT check
    missing_sot = check_sot()
    if missing_sot:
        errors.append(f"SOT missing: {missing_sot}")

    # 2. Registry check
    missing_reg = check_registry()
    if missing_reg:
        errors.append(f"Registry missing: {missing_reg}")

    # 3. Wiring check
    missing_wiring = check_wiring()
    if missing_wiring:
        errors.append(f"Wiring missing: {missing_wiring}")

    # 4. Invariant check
    missing_inv = check_invariants()
    if missing_inv:
        errors.append(f"SOT missing invariants: {missing_inv}")

    # Report
    print("=" * 60)
    print("STRUCTURAL RESTORATION PARITY CHECK")
    print("=" * 60)
    print(f"Expected tools: {len(EXPECTED_TOOLS)}")
    print()

    if not errors:
        print("✓ SOT:           PASS — all tools registered")
        print("✓ Registry:      PASS — all tools declared")
        print("✓ Wiring:        PASS — all tools wired")
        print("✓ Invariants:    PASS — all tools have invariant refs")
        print()
        print("VERDICT: PASS")
        return 0
    else:
        for e in errors:
            print(f"✗ {e}")
        print()
        print("VERDICT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
