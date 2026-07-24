#!/usr/bin/env python3
"""CI: assert public tool surface is self-consistent across ALL surfaces.

Usage:
  python scripts/check_registry_truth.py           # offline: all derived surfaces
  python scripts/check_registry_truth.py --live    # also tools/list on :8081
Exit 0 = TRUE, 1 = DRIFT

Asserts:
   1. registry.CANONICAL_PUBLIC_TOOLS == CANONICAL_PUBLIC_SURFACE.json public_tools
   2. mcp_surface.yaml canonical_tool_count == len(CANONICAL_PUBLIC_TOOLS)
   3. mcp_surface.yaml canonical_tools list == CANONICAL_PUBLIC_TOOLS
   4. llms.txt heading count == actual generated list length
   5. openapi.json x-mcp-tools count == plugin_export count
   6. tools.json surface_tools == public_tool_names() count
   7. ZEN_15_SURFACE.md is marked as archived
   8. PROTOCOL_CONFORMANCE.md contains no hardcoded integer tool count
   9. pyproject.toml contains no stale tool count claim
  10. --live: runtime tools/list count == CANONICAL_PUBLIC_TOOLS count
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

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS  # noqa: E402
from geox_mcp.surface_manifest import (  # noqa: E402
    load_surface_manifest,
    plugin_export_tool_names,
    public_tool_names,
)

drift = False
_PUBLIC_COUNT = len(CANONICAL_PUBLIC_TOOLS)


def check(condition: bool, msg: str) -> None:
    global drift
    if not condition:
        print(f"DRIFT: {msg}")
        drift = True
    else:
        print(f"OK: {msg}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="Probe localhost:8081 tools/list")
    args = ap.parse_args()

    load_surface_manifest.cache_clear()
    manifest = set(public_tool_names())
    plugin_export = set(plugin_export_tool_names())
    canonical_set = set(CANONICAL_PUBLIC_TOOLS)

    # ── 1. registry CANONICAL_PUBLIC_TOOLS vs manifest vs snapshot ──────────
    check(manifest == canonical_set, f"manifest public_tool_names ({len(manifest)}) == CANONICAL_PUBLIC_TOOLS ({_PUBLIC_COUNT})")
    if manifest != canonical_set:
        print("  only_manifest:", sorted(manifest - canonical_set))
        print("  only_registry:", sorted(canonical_set - manifest))

    snap_path = ROOT / "CANONICAL_PUBLIC_SURFACE.json"
    check(snap_path.exists(), "CANONICAL_PUBLIC_SURFACE.json exists")
    if snap_path.exists():
        snap = json.loads(snap_path.read_text())
        snap_set = set(snap.get("public_tools") or [])
        if canonical_set != snap_set:
            print("  only_registry:", sorted(canonical_set - snap_set))
            print("  only_snapshot:", sorted(snap_set - canonical_set))
        check(canonical_set == snap_set, f"CANONICAL_PUBLIC_TOOLS ({_PUBLIC_COUNT}) == snapshot ({len(snap_set)})")

    # ── 2. mcp_surface.yaml canonical_tool_count == registry count ─────────
    surface_yaml_path = ROOT / "contracts" / "mcp_surface.yaml"
    if surface_yaml_path.exists():
        with open(surface_yaml_path) as f:
            surface_doc = yaml.safe_load(f)
        yaml_count = surface_doc.get("canonical_tool_count")
        check(yaml_count == _PUBLIC_COUNT, f"mcp_surface.yaml canonical_tool_count ({yaml_count}) == registry ({_PUBLIC_COUNT})")
        yaml_list = set(surface_doc.get("canonical_tools") or [])
        if yaml_list != canonical_set:
            print("  only_yaml:", sorted(yaml_list - canonical_set))
            print("  only_registry:", sorted(canonical_set - yaml_list))
        check(yaml_list == canonical_set, f"mcp_surface.yaml tools ({len(yaml_list)}) == registry ({_PUBLIC_COUNT})")

    # ── 3. ZEN_15_SURFACE.md is archived ───────────────────────────────────
    zen_path = ROOT / "docs" / "ZEN_15_SURFACE.md"
    zen_archive_path = ROOT / "docs" / "archive" / "ZEN_15_SURFACE_ARCHIVED_2026-07-24.md"
    check(zen_archive_path.exists(), "ZEN_15_SURFACE.md archived copy exists")
    if zen_path.exists():
        zen_text = zen_path.read_text()
        archived = "ARCHIVED" in zen_text and "archived" in zen_text.lower()
        check(archived, "ZEN_15_SURFACE.md marked as ARCHIVED")

    # ── 4. llms.txt heading count == actual public count ───────────────────
    llms_path = ROOT / "llms.txt"
    if llms_path.exists():
        llms_text = llms_path.read_text()
        lines = [l for l in llms_text.splitlines() if l.startswith("# GEOX")]
        if lines:
            m = re.search(r"\((\d+) Public Tools\)", lines[0])
            if m:
                llms_count = int(m.group(1))
                check(llms_count == _PUBLIC_COUNT, f"llms.txt heading ({llms_count}) == registry ({_PUBLIC_COUNT})")
        tool_lines = [l for l in llms_text.splitlines() if re.match(r"^\d+\.\s+\*\*geox_", l)]
        check(len(tool_lines) == _PUBLIC_COUNT, f"llms.txt tool entries ({len(tool_lines)}) == registry ({_PUBLIC_COUNT})")
    else:
        check(False, "llms.txt exists")

    # ── 5. openapi.json x-mcp-tools count == plugin_export ─────────────────
    openapi_path = ROOT / ".well-known" / "openapi.json"
    if openapi_path.exists():
        openapi = json.loads(openapi_path.read_text())
        x_mcp_tools = openapi.get("paths", {}).get("/mcp", {}).get("post", {}).get("x-mcp-tools", [])
        check(
            len(x_mcp_tools) == len(plugin_export),
            f"openapi x-mcp-tools ({len(x_mcp_tools)}) == plugin_export ({len(plugin_export)})",
        )
        desc = openapi.get("paths", {}).get("/mcp", {}).get("post", {}).get("description", "")
        check("15 ZEN-15" not in desc, "openapi description has no '15 ZEN-15' hardcode")
        check("ZEN-15" not in desc, "openapi description has no 'ZEN-15' reference")
    else:
        check(False, ".well-known/openapi.json exists")

    # ── 6. tools.json surface_tools == public count ────────────────────────
    tools_path = ROOT / ".well-known" / "tools.json"
    if tools_path.exists():
        tj = json.loads(tools_path.read_text())
        surface = tj.get("surface_tools")
        check(surface == _PUBLIC_COUNT, f"tools.json surface_tools ({surface}) == registry ({_PUBLIC_COUNT})")
    else:
        check(False, ".well-known/tools.json exists")

    # ── 7. Required public tools present ───────────────────────────────────
    for must in (
        "geox_basin",
        "geox_claim",
        "geox_prospect",
        "geox_seismic_interpret",
        "geox_surface_status",
        "geox_well_ingest",
    ):
        check(must in canonical_set, f"{must} on public surface")
    check("geox_workspace" in canonical_set, "geox_workspace public")
    check("geox_falsify" in canonical_set, "geox_falsify public")

    # ── 8. PROTOCOL_CONFORMANCE.md has no hardcoded counts ─────────────────
    proto_path = ROOT / "PROTOCOL_CONFORMANCE.md"
    if proto_path.exists():
        proto_text = proto_path.read_text()
        hardcoded = re.findall(r"\b(\d+)\s+(?:public\s+)?(?:canonical\s+)?(?:operational\s+)?tools?\b", proto_text, re.IGNORECASE)
        check(not hardcoded, f"PROTOCOL_CONFORMANCE.md has no hardcoded tool count (found: {hardcoded})")
    else:
        check(False, "PROTOCOL_CONFORMANCE.md exists")

    # ── 9. pyproject.toml has no stale tool count ──────────────────────────
    pyproject_path = ROOT / "pyproject.toml"
    if pyproject_path.exists():
        pyproject = pyproject_path.read_text()
        check("35 canonical MCP tools" not in pyproject, "pyproject.toml has no '35 canonical MCP tools' claim")
    else:
        check(False, "pyproject.toml exists")

    # ── 10. Live probe (optional) ─────────────────────────────────────────
    if args.live:
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
                {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, {"Mcp-Session-Id": sid} if sid else None
            )
            _, j2 = post(
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, {"Mcp-Session-Id": sid} if sid else None
            )
            live = {t["name"] for t in (j2.get("result") or {}).get("tools") or []}
            if live != canonical_set:
                print("  only_registry:", sorted(canonical_set - live))
                print("  only_live:", sorted(live - canonical_set))
            check(live == canonical_set, f"live tools/list ({len(live)}) == registry ({_PUBLIC_COUNT})")
        except Exception as e:
            check(False, f"live probe: {e}")

    if drift:
        print("registry_truth=DRIFT")
        return 1
    print("registry_truth=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
