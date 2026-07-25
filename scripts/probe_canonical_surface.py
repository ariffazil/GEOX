#!/usr/bin/env python3
"""
scripts/probe_canonical_surface.py — Reproduces the P0-1 audit probe.

Forged 2026-07-25 · FI-008 (kimi-code) — GEOX agent-init work order.

This script is the one-shot CLI version of the canonical-surface invariant.
It probes the live GEOX MCP server (and HTTP /tools endpoint) and reports
drift between the live tool surface and CANONICAL_PUBLIC_TOOLS.

Usage:
    python scripts/probe_canonical_surface.py                 # default :8081
    GEOX_MCP_URL=http://127.0.0.1:8081 python scripts/probe_canonical_surface.py
    python scripts/probe_canonical_surface.py --inproc         # no network
    python scripts/probe_canonical_surface.py --json           # machine output

Exit codes:
    0 — clean (drift_count == 0 AND gap_count == 0)
    1 — drift detected (live has tools not in canonical)
    2 — gap detected (canonical has tools not in live)
    3 — both drift and gap
    4 — server unreachable / MCP error
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geox_mcp.canonical_surface_gate import (  # noqa: E402
    canonical_set,
    drift_report,
    EVT_SURFACE_DRIFT,
    EVT_SURFACE_GAP,
)


DEFAULT_MCP_URL = os.getenv("GEOX_MCP_URL", "http://127.0.0.1:8081")
DEFAULT_HTTP_TOOLS_URL = f"{DEFAULT_MCP_URL.rstrip('/')}/tools"
DEFAULT_MCP_RPC_URL = f"{DEFAULT_MCP_URL.rstrip('/')}/mcp/"


# ── Probes ────────────────────────────────────────────────────────────────


def probe_inproc() -> dict[str, Any]:
    """No-network probe: just check that the manifest loads cleanly.

    Useful for CI without a live server.
    """
    canonical = canonical_set()
    report = drift_report(sorted(canonical))
    report["source"] = "inproc:manifest_only"
    report["status_code"] = 200 if report["ok"] else 409
    return report


def probe_http_tools(base_url: str, timeout: float = 5.0) -> dict[str, Any]:
    """Probe the HTTP /tools endpoint (non-MCP)."""
    url = f"{base_url.rstrip('/')}/tools"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read().decode())
    live_names = [t["name"] for t in payload.get("tools", [])]
    report = drift_report(live_names)
    report["source"] = f"{url} (HTTP GET)"
    report["http_count"] = payload.get("count")
    return report


def probe_mcp_tools_list(rpc_url: str, timeout: float = 8.0) -> dict[str, Any]:
    """Probe MCP /mcp/ tools/list (the real connector surface).

    Implements the standard MCP lifecycle:
        1. initialize → get session id
        2. notifications/initialized
        3. tools/list
    """
    # 1. initialize
    init_body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "probe_canonical_surface", "version": "1.0"},
            },
        }
    ).encode()
    req = urllib.request.Request(
        rpc_url,
        data=init_body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        sid = r.headers.get("mcp-session-id", "")
    if not sid:
        raise RuntimeError(f"no mcp-session-id header returned from {rpc_url}")

    # 2. notifications/initialized
    req = urllib.request.Request(
        rpc_url,
        data=json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": sid,
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=timeout).read()

    # 3. tools/list
    req = urllib.request.Request(
        rpc_url,
        data=json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }
        ).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": sid,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read().decode())

    tools = payload.get("result", {}).get("tools", [])
    live_names = [t.get("name", "") for t in tools if t.get("name")]
    report = drift_report(live_names)
    report["source"] = f"{rpc_url} (MCP tools/list)"
    report["mcp_count"] = len(tools)
    return report


def probe_drift_endpoint(base_url: str, timeout: float = 5.0) -> dict[str, Any] | None:
    """Probe the GEOX /drift endpoint (returns last middleware observation)."""
    url = f"{base_url.rstrip('/')}/drift"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 409:
            # drift is signaled via 409 — read body for the report
            return json.loads(e.read().decode())
        return None
    except Exception:
        return None


# ── Reporting ──────────────────────────────────────────────────────────────


def format_report(report: dict[str, Any], *, json_mode: bool) -> str:
    if json_mode:
        return json.dumps(report, indent=2, sort_keys=True)
    lines: list[str] = []
    lines.append("=" * 64)
    lines.append("GEOX canonical-surface audit probe (P0-1 · 2026-07-25)")
    lines.append("=" * 64)
    lines.append(f"source:            {report.get('source', '?')}")
    lines.append(f"canonical_count:   {report.get('canonical_count')}")
    lines.append(f"live_count:        {report.get('live_count')}")
    lines.append(f"drift_count:       {report.get('drift_count', 0)}")
    lines.append(f"gap_count:         {report.get('gap_count', 0)}")
    lines.append(f"ok:                {report.get('ok', False)}")
    if "http_count" in report:
        lines.append(f"http_count:        {report['http_count']}")
    if "mcp_count" in report:
        lines.append(f"mcp_count:         {report['mcp_count']}")
    if report.get("drifted"):
        lines.append("")
        lines.append(f"DRIFTED ({len(report['drifted'])}): {report['drifted'][:10]}")
        if len(report["drifted"]) > 10:
            lines.append(f"  ... and {len(report['drifted']) - 10} more")
    if report.get("missing"):
        lines.append("")
        lines.append(f"MISSING ({len(report['missing'])}): {report['missing'][:10]}")
        if len(report["missing"]) > 10:
            lines.append(f"  ... and {len(report['missing']) - 10} more")
    lines.append("")
    if report.get("ok"):
        lines.append("VERDICT: CLEAN — live MCP connector surface equals canonical.")
        lines.append(f"event: {EVT_SURFACE_DRIFT.replace('SURFACE_DRIFT', 'SURFACE_OK')}")
    else:
        if report.get("drift_count", 0) > 0:
            lines.append(
                f"VERDICT: DRIFT — {report['drift_count']} non-canonical tool(s) "
                f"exposed. Event: {EVT_SURFACE_DRIFT}"
            )
        if report.get("gap_count", 0) > 0:
            lines.append(
                f"VERDICT: GAP — {report['gap_count']} canonical tool(s) missing "
                f"from live. Event: {EVT_SURFACE_GAP}"
            )
    lines.append("=" * 64)
    return "\n".join(lines)


def exit_code_for(report: dict[str, Any]) -> int:
    drift = report.get("drift_count", 0) or 0
    gap = report.get("gap_count", 0) or 0
    if drift and gap:
        return 3
    if drift:
        return 1
    if gap:
        return 2
    return 0


# ── Main ──────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--base-url",
        default=DEFAULT_MCP_URL,
        help=f"GEOX base URL (default: {DEFAULT_MCP_URL})",
    )
    parser.add_argument(
        "--rpc-url",
        default=DEFAULT_MCP_RPC_URL,
        help="MCP JSON-RPC endpoint URL (default: derived from --base-url)",
    )
    parser.add_argument(
        "--inproc",
        action="store_true",
        help="Skip network probes; only check in-process manifest integrity.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable report.",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Skip the MCP /mcp/ tools/list probe (HTTP /tools only).",
    )
    parser.add_argument(
        "--no-http",
        action="store_true",
        help="Skip the HTTP /tools probe (MCP only).",
    )
    parser.add_argument(
        "--no-drift-endpoint",
        action="store_true",
        help="Skip the GEOX /drift endpoint probe.",
    )
    args = parser.parse_args(argv)

    if args.inproc:
        report = probe_inproc()
        print(format_report(report, json_mode=args.json))
        return exit_code_for(report)

    # Always do the inproc check too — cheap, catches local regressions.
    inproc = probe_inproc()
    if not inproc.get("ok"):
        # Local manifest is broken — fail before even touching the network.
        print(format_report(inproc, json_mode=args.json))
        return exit_code_for(inproc)

    reports: dict[str, Any] = {"inproc": inproc}

    if not args.no_http:
        try:
            reports["http_tools"] = probe_http_tools(args.base_url)
        except Exception as e:
            reports["http_tools"] = {"error": f"{type(e).__name__}: {e}"}

    if not args.no_mcp:
        try:
            reports["mcp_tools_list"] = probe_mcp_tools_list(args.rpc_url)
        except Exception as e:
            reports["mcp_tools_list"] = {"error": f"{type(e).__name__}: {e}"}

    if not args.no_drift_endpoint:
        reports["drift_endpoint"] = probe_drift_endpoint(args.base_url) or {
            "error": "endpoint unavailable"
        }

    if args.json:
        print(json.dumps(reports, indent=2, sort_keys=True))
    else:
        for label, report in reports.items():
            print(f"\n── {label} ──")
            if "error" in report:
                print(f"  ERROR: {report['error']}")
            else:
                print(format_report(report, json_mode=False))

    # Exit code reflects the WORST probe result.
    worst = 0
    for report in reports.values():
        if "error" in report:
            worst = max(worst, 4)
            continue
        worst = max(worst, exit_code_for(report))
    return worst


if __name__ == "__main__":
    sys.exit(main())
