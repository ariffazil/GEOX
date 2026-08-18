#!/usr/bin/env python3
"""Anti-drift CI gate — assert ALL surface artifacts match registry.py truth.

registry.py::CANONICAL_PUBLIC_TOOLS is the ONLY truth.
Every other surface is GENERATED. If they disagree, the surface drifted.

Usage:
  python scripts/check_registry_truth.py              # warn on soft drift, fail on hard
  python scripts/check_registry_truth.py --strict     # fail on ANY mismatch
  python scripts/check_registry_truth.py --live       # also probe :8081 tools/list

Exit 0 = all surfaces match truth, 1 = drift detected.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, GHOST_TOOLS  # noqa: E402
from geox_mcp.surface_manifest import (  # noqa: E402
    load_surface_manifest,
    public_tool_names,
)

# ── Truth set ────────────────────────────────────────────────────────────────
TRUTH_SET: set[str] = set(CANONICAL_PUBLIC_TOOLS)
TRUTH_COUNT: int = len(CANONICAL_PUBLIC_TOOLS)
TRUTH_SORTED: list[str] = sorted(CANONICAL_PUBLIC_TOOLS)

drift_count = 0
warn_count = 0


def fail(msg: str) -> None:
    global drift_count
    drift_count += 1
    print(f"  ✗ DRIFT: {msg}")


def warn(msg: str) -> None:
    global warn_count
    warn_count += 1
    print(f"  ⚠ WARN:  {msg}")


def ok(msg: str) -> None:
    print(f"  ✓ OK:    {msg}")


def check_surface(name: str, actual_count: int | None, actual_set: set[str] | None, strict: bool = False) -> None:
    """Compare a surface artifact against truth. Fail on count/set mismatch."""
    if actual_count is not None and actual_count != TRUTH_COUNT:
        msg = f"{name}: count={actual_count}, truth={TRUTH_COUNT}"
        if strict:
            fail(msg)
        else:
            warn(msg)

    if actual_set is not None and actual_set != TRUTH_SET:
        missing = sorted(TRUTH_SET - actual_set)
        extra = sorted(actual_set - TRUTH_SET)
        parts = []
        if missing:
            parts.append(f"missing={missing}")
        if extra:
            parts.append(f"extra={extra}")
        msg = f"{name}: set mismatch — {'; '.join(parts)}"
        fail(msg)  # set mismatch is always hard drift


def extract_manifest_public_tools() -> tuple[int, set[str]]:
    """Read tools_manifest.yaml and extract visibility=public tools (pre-ghost-filter)."""
    load_surface_manifest.cache_clear()
    raw_names = public_tool_names()
    # public_tool_names() returns visibility=public tools BEFORE ghost filtering
    # The registry applies GHOST_TOOLS filter, so we do the same here
    filtered = [n for n in raw_names if n not in GHOST_TOOLS]
    return len(filtered), set(filtered)


def check_manifest(strict: bool) -> None:
    """Check tools_manifest.yaml public tool count and set."""
    print("\n── tools_manifest.yaml ──")
    count, tools = extract_manifest_public_tools()
    check_surface("tools_manifest.yaml", count, tools, strict=strict)
    # Also check the declared public_count_target field
    load_surface_manifest.cache_clear()
    manifest = load_surface_manifest()
    target = manifest.get("public_count_target")
    if target is not None:
        if int(target) != TRUTH_COUNT:
            msg = f"tools_manifest.yaml: public_count_target={target}, truth={TRUTH_COUNT}"
            if strict:
                fail(msg)
            else:
                warn(msg)
        else:
            ok(f"tools_manifest.yaml: public_count_target={target} matches")
    ok(f"tools_manifest.yaml: {count} public tools (post-ghost-filter)")


def check_canonical_surface_json(strict: bool) -> None:
    """Check src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json."""
    print("\n── CANONICAL_PUBLIC_SURFACE.json ──")
    path = ROOT / "src" / "geox_mcp" / "generated" / "CANONICAL_PUBLIC_SURFACE.json"
    if not path.exists():
        fail("CANONICAL_PUBLIC_SURFACE.json not found")
        return
    data = json.loads(path.read_text())
    count = data.get("public_count")
    tools = set(data.get("public_tools") or [])
    check_surface("CANONICAL_PUBLIC_SURFACE.json", count, tools, strict=strict)


def check_llms_txt(strict: bool) -> None:
    """Check llms.txt header count and tool entry count."""
    print("\n── llms.txt ──")
    path = ROOT / "llms.txt"
    if not path.exists():
        fail("llms.txt not found")
        return

    text = path.read_text()

    # Extract count from header line
    header_match = re.search(r"\((\d+)\s+Public\s+Tools\)", text)
    if header_match:
        header_count = int(header_match.group(1))
        if header_count != TRUTH_COUNT:
            msg = f"llms.txt header: count={header_count}, truth={TRUTH_COUNT}"
            if strict:
                fail(msg)
            else:
                warn(msg)
        else:
            ok(f"llms.txt header: {header_count} matches")
    else:
        fail("llms.txt: no '(N Public Tools)' header found")

    # Count tool entries (lines starting with N. **geox_)
    tool_lines = [l for l in text.splitlines() if re.match(r"^\d+\.\s+\*\*geox_", l)]
    entry_count = len(tool_lines)
    if entry_count != TRUTH_COUNT:
        msg = f"llms.txt entries: count={entry_count}, truth={TRUTH_COUNT}"
        if strict:
            fail(msg)
        else:
            warn(msg)
    else:
        ok(f"llms.txt entries: {entry_count} matches")

    # Extract tool names from entries and check set
    entry_names = set()
    for line in tool_lines:
        m = re.search(r"\*\*(geox_\w+)\*\*", line)
        if m:
            entry_names.add(m.group(1))
    check_surface("llms.txt entries", None, entry_names, strict=strict)


def check_tools_sot_yaml(strict: bool) -> None:
    """Check tools_sot.yaml public_count and tool list."""
    print("\n── tools_sot.yaml ──")
    path = ROOT / "tools_sot.yaml"
    if not path.exists():
        fail("tools_sot.yaml not found")
        return

    with open(path) as f:
        data = yaml.safe_load(f)

    count = data.get("public_count")
    tools = set(t["name"] for t in (data.get("tools") or []))
    check_surface("tools_sot.yaml", count, tools, strict=strict)


def check_contracts_tools_yaml(strict: bool) -> None:
    """Check contracts/tools.yaml canonical_tool_count and tool list."""
    print("\n── contracts/tools.yaml ──")
    path = ROOT / "contracts" / "tools.yaml"
    if not path.exists():
        fail("contracts/tools.yaml not found")
        return

    with open(path) as f:
        data = yaml.safe_load(f)

    count = data.get("canonical_tool_count")
    tools = set((data.get("tools") or {}).keys())
    check_surface("contracts/tools.yaml", count, tools, strict=strict)


def check_readme_badge(strict: bool) -> None:
    """Check README.md badge count."""
    print("\n── README.md badge ──")
    path = ROOT / "README.md"
    if not path.exists():
        fail("README.md not found")
        return

    text = path.read_text()
    # Match badge: %20GEOX-NN%20Canonical%20Tools or similar patterns
    badge_match = re.search(r"GEOX-(\d+)\s+Canonical\s+Tools", text)
    if badge_match:
        badge_count = int(badge_match.group(1))
        if badge_count != TRUTH_COUNT:
            msg = f"README badge: count={badge_count}, truth={TRUTH_COUNT}"
            if strict:
                fail(msg)
            else:
                warn(msg)
        else:
            ok(f"README badge: {badge_count} matches")
    else:
        fail("README.md: no 'GEOX-N Canonical Tools' badge found")

    # Also check the "Core Capabilities (N Tools)" heading
    cap_match = re.search(r"Core\s+Capabilities\s*\((\d+)\s+Tools\)", text)
    if cap_match:
        cap_count = int(cap_match.group(1))
        if cap_count != TRUTH_COUNT:
            msg = f"README capabilities heading: count={cap_count}, truth={TRUTH_COUNT}"
            if strict:
                fail(msg)
            else:
                warn(msg)
        else:
            ok(f"README capabilities heading: {cap_count} matches")


def check_tools_json(strict: bool) -> None:
    """Check tools.json (root) public list."""
    print("\n── tools.json (root) ──")
    path = ROOT / "tools.json"
    if not path.exists():
        fail("tools.json not found")
        return

    data = json.loads(path.read_text())
    tools = set(data.get("public") or [])
    count = len(tools)
    check_surface("tools.json", count, tools, strict=strict)


def check_generated_tools_json(strict: bool) -> None:
    """Check src/geox_mcp/generated/tools.json if it exists."""
    print("\n── generated/tools.json ──")
    path = ROOT / "src" / "geox_mcp" / "generated" / "tools.json"
    if not path.exists():
        warn("generated/tools.json not found (optional)")
        return

    data = json.loads(path.read_text())
    tools = set(data.get("public") or [])
    count = len(tools)
    check_surface("generated/tools.json", count, tools, strict=strict)


def check_live_probe(strict: bool) -> None:
    """Probe :8081 tools/list and compare against truth."""
    print("\n── live tools/list (:8081) ──")
    import urllib.request

    def post(body, headers=None):
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if headers:
            h.update(headers)
        req = urllib.request.Request(
            "http://127.0.0.1:8081/mcp",
            data=json.dumps(body).encode(),
            headers=h,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode()
            hdr = dict(r.headers)
            if "data:" in raw:
                parts = [ln[5:].strip() for ln in raw.splitlines() if ln.startswith("data:")]
                raw = parts[-1] if parts else raw
            return hdr, json.loads(raw) if raw.strip() else {}

    try:
        hdr, j = post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "registry-truth", "version": "0"},
                },
            }
        )
        sid = hdr.get("mcp-session-id") or hdr.get("Mcp-Session-Id")
        post(
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            {"Mcp-Session-Id": sid} if sid else None,
        )
        _, j2 = post(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"Mcp-Session-Id": sid} if sid else None,
        )
        live = {t["name"] for t in (j2.get("result") or {}).get("tools") or []}
        check_surface("live tools/list", len(live), live, strict=strict)
    except Exception as e:
        fail(f"live probe: {e}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Assert all GEOX surfaces match registry.py truth")
    ap.add_argument("--strict", action="store_true", help="Fail on ANY mismatch (default: warn on count-only drift)")
    ap.add_argument("--live", action="store_true", help="Also probe :8081 tools/list")
    args = ap.parse_args()

    print(f"═══ GEOX Registry Truth Check ═══")
    print(f"  Truth source: registry.py::CANONICAL_PUBLIC_TOOLS")
    print(f"  Truth count:  {TRUTH_COUNT}")
    print(f"  Truth tools:  {TRUTH_SORTED}")
    print(f"  Mode:         {'STRICT' if args.strict else 'WARN on count drift'}")

    check_manifest(strict=args.strict)
    check_canonical_surface_json(strict=args.strict)
    check_llms_txt(strict=args.strict)
    check_tools_sot_yaml(strict=args.strict)
    check_contracts_tools_yaml(strict=args.strict)
    check_readme_badge(strict=args.strict)
    check_tools_json(strict=args.strict)
    check_generated_tools_json(strict=args.strict)

    if args.live:
        check_live_probe(strict=args.strict)

    print(f"\n═══ RESULT ═══")
    print(f"  Drift:  {drift_count}")
    print(f"  Warn:   {warn_count}")

    if drift_count > 0:
        print(f"  Verdict: DRIFT — {drift_count} surface(s) disagree with registry.py")
        return 1
    elif warn_count > 0 and args.strict:
        print(f"  Verdict: DRIFT (strict mode) — {warn_count} warning(s)")
        return 1
    elif warn_count > 0:
        print(f"  Verdict: PASS with {warn_count} warning(s)")
        return 0
    else:
        print(f"  Verdict: TRUE — all surfaces match registry.py")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
