#!/usr/bin/env python3
"""CI: assert tools_manifest public surface is self-consistent and optional live probe.

Usage:
  python scripts/check_registry_truth.py           # offline: manifest vs generated snapshot
  python scripts/check_registry_truth.py --live    # also tools/list on :8081
Exit 0 = TRUE, 1 = DRIFT
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geox_mcp.surface_manifest import load_surface_manifest, public_tool_names  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="Probe localhost:8081 tools/list")
    args = ap.parse_args()

    load_surface_manifest.cache_clear()
    manifest = set(public_tool_names())
    snap_path = ROOT / "CANONICAL_PUBLIC_SURFACE.json"
    if not snap_path.exists():
        print("FAIL: missing CANONICAL_PUBLIC_SURFACE.json — run generate step")
        return 1
    snap = json.loads(snap_path.read_text())
    snap_set = set(snap.get("public_tools") or [])
    drift = False
    if manifest != snap_set:
        print("DRIFT: manifest vs generated snapshot")
        print("  only_manifest", sorted(manifest - snap_set))
        print("  only_snapshot", sorted(snap_set - manifest))
        drift = True
    else:
        print(f"OK snapshot: public_count={len(manifest)}")

    # pyproject must not hardcode a false tool count
    pyproject = (ROOT / "pyproject.toml").read_text()
    if "35 canonical MCP tools" in pyproject:
        print("DRIFT: pyproject.toml still claims '35 canonical MCP tools'")
        drift = True

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
                    parts = [
                        ln[5:].strip()
                        for ln in raw.splitlines()
                        if ln.startswith("data:")
                    ]
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
                print("DRIFT: live tools/list vs manifest")
                print("  only_manifest", sorted(manifest - live))
                print("  only_live", sorted(live - manifest))
                drift = True
            else:
                print(f"OK live tools/list: count={len(live)}")
        except Exception as e:
            print(f"FAIL live probe: {e}")
            drift = True

    if drift:
        print("registry_truth=DRIFT")
        return 1
    print("registry_truth=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
