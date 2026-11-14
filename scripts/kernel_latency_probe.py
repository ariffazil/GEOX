#!/usr/bin/env python3
"""kernel_latency_probe.py — reproduce and attribute the raw-MCP tools/call stall.

The symptom
-----------
An external MCP client (curl, fedobs, MCPJam) opens a session against GEOX and
calls a tool. `initialize` and `tools/list` return in milliseconds. The
`tools/call` can take ~20 seconds. To a client that is indistinguishable from a
hang. A client that gave up and logged "None" hid the symptom instead of
filing it — which is how this script exists.

The question this answers
-------------------------
Is the stall in GEOX (session enforcement, the arifOS probe, cold start) or is
it inherited from a degraded sibling organ? The three candidates have very
different fixes, and guessing wrong sends the repair to the wrong owner.

It measures, per call:
  * arifOS reachability and latency (/health, /api/build-info, arif_judge)
  * the GEOX MCP session handshake (initialize, notifications/initialized)
  * GEOX tools/list
  * GEOX tools/call for each named tool, repeated
and then attributes: a slow tools/call that coincides with a degraded arifOS is
INHERITED, not a GEOX defect. A slow tools/call with a healthy arifOS IS a GEOX
defect.

Read-only. No restart. Nothing is mutated.

Usage:
    python3 scripts/kernel_latency_probe.py
    python3 scripts/kernel_latency_probe.py --tool geox_surface_status --repeat 3
    python3 scripts/kernel_latency_probe.py --json /tmp/latency.json

Exit codes:
    0  PASS             — every tools/call under the threshold, arifOS healthy
    1  FAIL             — a tools/call is slow while arifOS is healthy (GEOX-side)
    2  UPSTREAM_DEGRADED / UNKNOWN — the stall is inherited, or unattributable

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from pathlib import Path

DEFAULT_TOOLS = ("geox_claim", "geox_list_registered_sources", "geox_surface_status")
JSON_HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def _post(url: str, payload: dict, headers: dict | None = None, timeout: int = 90) -> tuple[int, float, bytes, dict]:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers={**JSON_HEADERS, **(headers or {})})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, time.monotonic() - t0, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, time.monotonic() - t0, exc.read(), dict(exc.headers or {})
    except Exception as exc:
        return 0, time.monotonic() - t0, f"ERROR: {exc}".encode(), {}


def _get(url: str, timeout: int = 30) -> tuple[int, float, bytes]:
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, time.monotonic() - t0, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, time.monotonic() - t0, exc.read()
    except Exception as exc:
        return 0, time.monotonic() - t0, f"ERROR: {exc}".encode()


def probe_arifos(base: str) -> dict:
    """Is the constitutional kernel healthy and how fast is it?"""
    out: dict = {"base": base, "health": None, "build_info": None, "judge": None, "degraded": False, "notes": []}

    code, dt, _body = _get(f"{base}/health")
    out["health"] = {"code": code, "seconds": round(dt, 3)}
    if code != 200:
        out["degraded"] = True
        out["notes"].append(f"/health returned {code}")

    code, dt, _body = _get(f"{base}/api/build-info")
    out["build_info"] = {"code": code, "seconds": round(dt, 3)}
    if code != 200:
        out["degraded"] = True
        out["notes"].append(f"/api/build-info returned {code}")

    # A trivial judge candidate — the fastest possible kernel round trip.
    code, dt, _, hdrs = _post(
        f"{base}/mcp",
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "kernel_latency_probe", "version": "1.0"},
            },
        },
    )
    sid = hdrs.get("mcp-session-id") or hdrs.get("Mcp-Session-Id") or ""
    judge_headers = {"Mcp-Session-Id": sid} if sid else {}
    if sid:
        _post(
            f"{base}/mcp",
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            headers={"Mcp-Session-Id": sid},
        )
    # arifOS runs a STATELESS era (2026-07-28) where no Mcp-Session-Id is
    # issued; the call still goes out, just without the header. A missing
    # session id is NOT evidence of degradation.
    code, dt, _, _ = _post(
        f"{base}/mcp",
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "arif_judge", "arguments": {"candidate": "latency probe"}},
        },
        headers=judge_headers,
    )
    out["judge"] = {"code": code, "seconds": round(dt, 3), "stateless": not bool(sid)}
    if code != 200:
        out["degraded"] = True
        out["notes"].append(f"arif_judge returned {code}")
    return out


def arif_mcp_path_is_slow(arifos: dict, budget: float) -> bool:
    """arifOS can serve /health in milliseconds while its /mcp dispatch takes
    12-19 s. Health therefore does NOT certify the MCP path. The judge round
    trip is the instrument that measures the path GEOX actually depends on."""
    j = arifos.get("judge") or {}
    secs = j.get("seconds")
    return bool(secs is not None and secs > budget)


def probe_geox(base: str, tools: Sequence[str], repeat: int) -> dict:
    """Walk the raw MCP lifecycle and time each step."""
    out: dict = {"base": base, "handshake": {}, "tools": {}}

    code, dt, _, hdrs = _post(
        f"{base}/mcp",
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "kernel_latency_probe", "version": "1.0"},
            },
        },
    )
    out["handshake"]["initialize"] = {"code": code, "seconds": round(dt, 3)}
    sid = hdrs.get("mcp-session-id") or hdrs.get("Mcp-Session-Id") or ""
    if not sid:
        out["handshake"]["error"] = "no Mcp-Session-Id"
        return out

    code, dt, _, _ = _post(
        f"{base}/mcp",
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers={"Mcp-Session-Id": sid},
    )
    out["handshake"]["notifications_initialized"] = {"code": code, "seconds": round(dt, 3)}

    code, dt, _, _ = _post(
        f"{base}/mcp",
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        headers={"Mcp-Session-Id": sid},
    )
    out["handshake"]["tools_list"] = {"code": code, "seconds": round(dt, 3)}

    for tool in tools:
        samples = []
        for i in range(repeat):
            code, dt, _, _ = _post(
                f"{base}/mcp",
                {
                    "jsonrpc": "2.0",
                    "id": 10 + i,
                    "method": "tools/call",
                    "params": {"name": tool, "arguments": {"actor_id": "claude-code-kvm8"}},
                },
                headers={"Mcp-Session-Id": sid},
            )
            samples.append({"code": code, "seconds": round(dt, 3)})
        out["tools"][tool] = {
            "samples": samples,
            "max_seconds": max((s["seconds"] for s in samples), default=None),
            "ok": all(s["code"] == 200 for s in samples),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--geox", default="http://127.0.0.1:8081")
    ap.add_argument("--arifos", default="http://127.0.0.1:8088")
    ap.add_argument("--tool", action="append", default=[], help="tool to time (repeatable)")
    ap.add_argument("--repeat", type=int, default=2, help="samples per tool")
    ap.add_argument("--threshold-s", type=float, default=2.0, help="tools/call budget in seconds")
    ap.add_argument("--json", help="write the raw result JSON here")
    args = ap.parse_args()

    tools = args.tool or list(DEFAULT_TOOLS)

    print("═" * 78)
    print("KERNEL LATENCY PROBE — is the raw-MCP stall GEOX's or inherited?")
    print("═" * 78)

    arifos = probe_arifos(args.arifos)
    if arif_mcp_path_is_slow(arifos, args.threshold_s):
        arifos["degraded"] = True
        arifos["notes"].append(
            f"arifOS /mcp dispatch took {(arifos.get('judge') or {}).get('seconds')}s "
            f"(budget {args.threshold_s}s) while /health was fast"
        )
    print(f"\narifOS {arifos['base']}")
    for k in ("health", "build_info", "judge"):
        v = arifos.get(k) or {}
        print(f"  {k:<12} code={v.get('code')}  {v.get('seconds')}s")
    print(f"  DEGRADED     : {'YES' if arifos['degraded'] else 'no'}"
          + (f"  ({'; '.join(arifos['notes'])})" if arifos["notes"] else ""))

    geox = probe_geox(args.geox, tools, args.repeat)
    print(f"\nGEOX {geox['base']} — raw MCP session")
    for k, v in (geox.get("handshake") or {}).items():
        if isinstance(v, dict):
            print(f"  {k:<26} code={v.get('code')}  {v.get('seconds')}s")
        else:
            print(f"  {k:<26} {v}")
    print("\n  tools/call")
    slow = []
    for tool, v in (geox.get("tools") or {}).items():
        times = ", ".join(f"{s['seconds']}s" for s in v["samples"])
        flag = ""
        if v["max_seconds"] is not None and v["max_seconds"] > args.threshold_s:
            flag = "   ← OVER BUDGET"
            slow.append(tool)
        print(f"    {tool:<30} {times}{flag}")

    verdict, reason = "PASS", "every tools/call within budget and arifOS healthy"
    if slow and arifos["degraded"]:
        verdict = "UPSTREAM_DEGRADED"
        reason = (
            "tools/call exceeded the budget for " + ", ".join(slow) +
            " WHILE arifOS was degraded (" + "; ".join(arifos["notes"]) +
            "). The stall is INHERITED from arifOS, not a GEOX defect."
        )
    elif slow:
        verdict = "FAIL"
        reason = (
            "tools/call exceeded the budget for " + ", ".join(slow) +
            " while arifOS was HEALTHY — the stall is GEOX-side."
        )
    elif arifos["degraded"]:
        verdict = "UPSTREAM_DEGRADED"
        reason = "arifOS is degraded (" + "; ".join(arifos["notes"]) + ") though no tool exceeded budget."

    result = {"arifos": arifos, "geox": geox, "verdict": verdict, "reason": reason, "threshold_s": args.threshold_s}
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("\n" + "═" * 78)
    print(f"VERDICT: {verdict}")
    print(f"  {reason}")
    print("═" * 78)
    return {"PASS": 0, "FAIL": 1}.get(verdict, 2)


if __name__ == "__main__":
    raise SystemExit(main())
