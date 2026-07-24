#!/usr/bin/env python3
"""CI: assert tools_manifest public surface is self-consistent across ALL derived surfaces.

Usage:
  python scripts/check_registry_truth.py           # offline: manifest vs all derived surfaces
  python scripts/check_registry_truth.py --live    # also tools/list on :8081
Exit 0 = TRUE, 1 = DRIFT

Asserts:
  1. manifest public_tools == CANONICAL_PUBLIC_SURFACE.json
  2. llms.txt heading count == actual generated list length
  3. openapi.json x-mcp-tools count == plugin_export count
  4. tools.json surface_tools == public_tool_names() count
  5. geox_workspace present in both public + plugin_export
  6. PROTOCOL_CONFORMANCE.md contains no hardcoded integer tool count
  7. pyproject.toml contains no stale tool count claim
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geox_mcp.surface_manifest import (  # noqa: E402
    load_surface_manifest,
    plugin_export_tool_names,
    public_tool_names,
)

drift = False


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

    # ── 1. manifest vs canonical snapshot ──────────────────────────────────
    snap_path = ROOT / "CANONICAL_PUBLIC_SURFACE.json"
    check(snap_path.exists(), "CANONICAL_PUBLIC_SURFACE.json exists")
    if snap_path.exists():
        snap = json.loads(snap_path.read_text())
        snap_set = set(snap.get("public_tools") or [])
        if manifest != snap_set:
            print("  only_manifest:", sorted(manifest - snap_set))
            print("  only_snapshot:", sorted(snap_set - manifest))
        check(manifest == snap_set, f"manifest == snapshot ({len(manifest)} tools)")

    # ── 2. llms.txt heading count == actual generated list ─────────────────
    llms_path = ROOT / "llms.txt"
    if llms_path.exists():
        llms_text = llms_path.read_text()
        lines = [l for l in llms_text.splitlines() if l.startswith("# GEOX")]
        if lines:
            m = re.search(r"\((\d+) Public Tools\)", lines[0])
            if m:
                llms_count = int(m.group(1))
                check(llms_count == len(manifest), f"llms.txt heading ({llms_count}) == manifest ({len(manifest)})")
        # Count actual enumerated tools
        tool_lines = [l for l in llms_text.splitlines() if re.match(r"^\d+\.\s+\*\*geox_", l)]
        check(len(tool_lines) == len(manifest), f"llms.txt tool entries ({len(tool_lines)}) == manifest ({len(manifest)})")
    else:
        check(False, "llms.txt exists")

    # ── 3. openapi.json x-mcp-tools count == plugin_export ─────────────────
    openapi_path = ROOT / ".well-known" / "openapi.json"
    if openapi_path.exists():
        openapi = json.loads(openapi_path.read_text())
        x_mcp_tools = openapi.get("paths", {}).get("/mcp", {}).get("post", {}).get("x-mcp-tools", [])
        check(
            len(x_mcp_tools) == len(plugin_export),
            f"openapi x-mcp-tools ({len(x_mcp_tools)}) == plugin_export ({len(plugin_export)})",
        )
        # Assert NO hardcoded count in description
        desc = openapi.get("paths", {}).get("/mcp", {}).get("post", {}).get("description", "")
        check("15 ZEN-15" not in desc, "openapi description has no '15 ZEN-15' hardcode")
        check("ZEN-15" not in desc, "openapi description has no 'ZEN-15' reference")
    else:
        check(False, ".well-known/openapi.json exists")

    # ── 4. tools.json surface_tools == public count ────────────────────────
    tools_path = ROOT / ".well-known" / "tools.json"
    if tools_path.exists():
        tj = json.loads(tools_path.read_text())
        surface = tj.get("surface_tools")
        check(surface == len(manifest), f"tools.json surface_tools ({surface}) == manifest ({len(manifest)})")
    else:
        check(False, ".well-known/tools.json exists")

    # ── 5. ZEN-15 core tools on public surface (FIX BRIEF v2 P0) ───────────
    zen15 = {
        "geox_well_ingest",
        "geox_well_qc",
        "geox_petrophysics",
        "geox_sequence",
        "geox_well_desk",
        "geox_seismic_ingest",
        "geox_seismic_compute",
        "geox_seismic_interpret",
        "geox_basin",
        "geox_deep_time_state",
        "geox_geomechanics",
        "geox_subsurface_model",
        "geox_claim",
        "geox_prospect",
        "geox_surface_status",
    }
    check(len(manifest) == 15, f"public surface is ZEN-15 (got {len(manifest)})")
    missing_zen = sorted(zen15 - manifest)
    extra_zen = sorted(manifest - zen15)
    check(not missing_zen, f"ZEN-15 tools present (missing: {missing_zen})")
    check(not extra_zen, f"no public extras beyond ZEN-15 (extra: {extra_zen})")
    # demoted tools must not be public
    check("geox_workspace" not in manifest, "geox_workspace demoted to internal")
    check("geox_falsify" not in manifest, "geox_falsify demoted to internal")

    # ── 6. PROTOCOL_CONFORMANCE.md has no hardcoded counts ─────────────────
    proto_path = ROOT / "PROTOCOL_CONFORMANCE.md"
    if proto_path.exists():
        proto_text = proto_path.read_text()
        # Any integer followed by "tool" on same line (e.g. "15 tools", "24 tools")
        hardcoded = re.findall(r"\b(\d+)\s+(?:public\s+)?(?:canonical\s+)?(?:operational\s+)?tools?\b", proto_text, re.IGNORECASE)
        check(not hardcoded, f"PROTOCOL_CONFORMANCE.md has no hardcoded tool count (found: {hardcoded})")
    else:
        check(False, "PROTOCOL_CONFORMANCE.md exists")

    # ── 7. pyproject.toml has no stale tool count ──────────────────────────
    pyproject_path = ROOT / "pyproject.toml"
    if pyproject_path.exists():
        pyproject = pyproject_path.read_text()
        check("35 canonical MCP tools" not in pyproject, "pyproject.toml has no '35 canonical MCP tools' claim")
    else:
        check(False, "pyproject.toml exists")

    # ── 8. Live probe (optional) ───────────────────────────────────────────
    if args.live:
        import urllib.request

        def post(body, headers=None):
            h = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
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
                        "protocolVersion": "2025-06-18",
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
            if live != manifest:
                print("  only_manifest:", sorted(manifest - live))
                print("  only_live:", sorted(live - manifest))
            check(live == manifest, f"live tools/list ({len(live)}) == manifest ({len(manifest)})")
        except Exception as e:
            check(False, f"live probe: {e}")

    if drift:
        print("registry_truth=DRIFT")
        return 1
    print("registry_truth=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
