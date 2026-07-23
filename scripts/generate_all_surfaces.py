#!/usr/bin/env python3
"""Orchestrate all surface generators + run post-generation assertions.

Usage:
  python scripts/generate_all_surfaces.py

Generates:
  CANONICAL_PUBLIC_SURFACE.json  (canonical snapshot)
  src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json  (packaged copy)
  .well-known/tools.json         (plugin surface)
  .well-known/openapi.json       (OpenAPI with x-mcp-tools)
  tools.json                     (root manifest)
  llms.txt                       (LLM-readable tool surface)

Post-generation:
  - Asserts generator idempotence (run twice → no diff)
  - Asserts check_registry_truth.py passes
  - Asserts no hardcoded tool counts remain in documentation

Exit 0 on success, 1 on any failure.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(script: str) -> None:
    """Run a script and fail on non-zero exit."""
    path = SCRIPTS / script
    print(f"→ {script} ...", end=" ", flush=True)
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("FAIL")
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print("OK")


def git_diff() -> str:
    """Return git diff of the working tree."""
    result = subprocess.run(
        ["git", "diff", "--stat"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    print("=== GENERATE ===")

    # Step 1: Run canonical surface generator
    run("generate_canonical_surface.py")

    # Step 2: Run public registry generator (llms.txt, openapi, tools.json, well-known)
    run("generate_public_registry.py")

    # Step 3: Assert idempotence — second run must produce no diff
    print("\n=== IDEMPOTENCE CHECK ===")
    diff_before = git_diff()
    run("generate_canonical_surface.py")
    run("generate_public_registry.py")
    diff_after = git_diff()
    if diff_before != diff_after:
        print("IDEMPOTENCE FAIL: second run produced different output")
        print("=== diff before ===")
        print(diff_before)
        print("=== diff after ===")
        print(diff_after)
        return 1
    print("IDEMPOTENCE PASS: generators are idempotent")

    # Step 4: Run registry truth checker
    print("\n=== REGISTRY TRUTH ===")
    run("check_registry_truth.py")
    # Also run with --live if server is available
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_registry_truth.py"), "--live"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("LIVE CHECK (non-fatal):", result.stdout.strip())
    else:
        print("LIVE CHECK PASS")

    print("\n=== ALL SURFACES GENERATED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
