#!/usr/bin/env python3
"""GEOX deploy gate — the deploy FAILS unless the live surface matches the registry.

P0 protocol trust (2026-10-15), forged after Claude Code could not use GEOX:
every 2026-07-28 reply lacked ``resultType`` and the defect was invisible to
curl. This gate verifies with a STRICT client (httpx), never curl.

Checks (all must pass):
  1. /health is healthy and ``git_version`` == the deployed commit.
  2. ``surface_drift.ok == True`` and ``canonical_count == live_count``
     (registry.py::CANONICAL_PUBLIC_TOOLS is the only truth).
  3. Stateless 2026-07-28 contract, live over the wire:
       tools/list, tools/call(geox_surface_status), resources/list,
       prompts/list → each replies ``result.resultType == "complete"``,
       content-length == actual bytes (httpx enforces this strictly).
  4. geox_surface_status reports the deployed SHA and live tool count
     matching the canonical count.

Usage:
  python scripts/deploy_gate.py                          # expect local git HEAD
  python scripts/deploy_gate.py --expect-sha <short_sha> # explicit expectation
  python scripts/deploy_gate.py --url http://127.0.0.1:8081

Exit 0 = deploy verified. Exit 1 = gate BLOCKED (deploy failed).
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import httpx  # noqa: E402

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS  # noqa: E402

MODERN_ERA = "2026-07-28"

failures: list[str] = []
receipts: list[str] = []


def ok(msg: str) -> None:
    receipts.append(f"PASS  {msg}")
    print(f"  [PASS] {msg}")


def fail(msg: str) -> None:
    failures.append(msg)
    receipts.append(f"FAIL  {msg}")
    print(f"  [FAIL] {msg}")


def _meta() -> dict:
    return {
        "io.modelcontextprotocol/protocolVersion": MODERN_ERA,
        "io.modelcontextprotocol/clientCapabilities": {},
    }


def stateless_call(client: httpx.Client, method: str, *, tool: str | None = None, params: dict | None = None) -> dict:
    """One strict 2026-07-28 stateless request. httpx raises on
    content-length mismatch — strictness is the point."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": MODERN_ERA,
        "Mcp-Method": method,
    }
    if tool:
        headers["Mcp-Name"] = tool
    body: dict = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {"_meta": _meta()}}
    if tool:
        body["params"] = {"name": tool, "arguments": {}, "_meta": _meta()}
    resp = client.post("/mcp", headers=headers, json=body)
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="GEOX live deploy gate")
    parser.add_argument("--url", default="http://127.0.0.1:8081")
    parser.add_argument("--expect-sha", default=None, help="expected short SHA (default: local git HEAD)")
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    expect_sha = args.expect_sha
    if expect_sha is None:
        try:
            expect_sha = subprocess.run(
                ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except Exception as exc:
            print(f"[GATE] cannot determine expected SHA: {exc}")
            return 1

    print(f"[GATE] GEOX deploy gate — target {args.url} expect sha {expect_sha}")

    # ── 1. wait for health ─────────────────────────────────────────────
    deadline = time.time() + args.timeout
    health: dict = {}
    with httpx.Client(base_url=args.url, timeout=10.0) as client:
        while time.time() < deadline:
            try:
                r = client.get("/health")
                if r.status_code == 200:
                    health = r.json()
                    if health.get("status") == "healthy":
                        break
            except Exception:
                pass
            time.sleep(2.0)
        if health.get("status") != "healthy":
            fail(f"/health not healthy after {args.timeout}s (last: {health.get('status')})")
            return _summary()

        git_version = str(health.get("git_version", ""))
        if expect_sha in git_version:
            ok(f"/health git_version={git_version} matches deployed {expect_sha}")
        else:
            fail(f"/health git_version={git_version!r} != expected {expect_sha!r}")

        # ── 2. registry truth ──────────────────────────────────────────
        drift = health.get("surface_drift", {})
        canonical_n = len(CANONICAL_PUBLIC_TOOLS)
        if drift.get("ok") is True and drift.get("canonical_count") == drift.get("live_count"):
            ok(f"surface_drift ok (canonical={drift.get('canonical_count')} live={drift.get('live_count')})")
        else:
            fail(f"surface_drift mismatch: {json.dumps(drift)[:200]}")
        if drift.get("canonical_count") != canonical_n:
            fail(f"health canonical_count {drift.get('canonical_count')} != registry {canonical_n}")
        else:
            ok(f"registry truth count {canonical_n} confirmed live")

        # ── 3. stateless 2026-07-28 contract (STRICT client) ───────────
        for method, tool in [
            ("tools/list", None),
            ("tools/call", "geox_surface_status"),
            ("resources/list", None),
            ("prompts/list", None),
        ]:
            label = method if not tool else f"{method}({tool})"
            try:
                data = stateless_call(client, method, tool=tool)
                result = data.get("result")
                if isinstance(result, dict) and result.get("resultType") == "complete":
                    ok(f"stateless {label}: resultType=complete")
                else:
                    fail(
                        f"stateless {label}: missing resultType (result keys: "
                        f"{sorted(result.keys())[:6] if isinstance(result, dict) else type(result).__name__})"
                    )
            except Exception as exc:
                fail(f"stateless {label}: strict client error — {type(exc).__name__}: {exc}")

        # ── 4. status tool facts ───────────────────────────────────────
        try:
            data = stateless_call(client, "tools/call", tool="geox_surface_status")
            inner = json.loads(data["result"]["content"][0]["text"])
            sha = inner.get("deployed_git_sha")
            if expect_sha in str(sha):
                ok(f"geox_surface_status deployed_git_sha={sha}")
            else:
                fail(f"geox_surface_status deployed_git_sha={sha!r} != {expect_sha!r}")
            lc = (inner.get("live_counts") or {}).get("tools")
            cc = (inner.get("canonical_counts") or {}).get("tools")
            if lc is None:
                fail("geox_surface_status live_counts.tools = None (cannot witness)")
            elif lc == cc:
                ok(f"geox_surface_status live tools={lc} == canonical {cc}")
            else:
                fail(f"geox_surface_status live tools={lc} != canonical {cc}")
        except Exception as exc:
            fail(f"geox_surface_status probe failed: {type(exc).__name__}: {exc}")

    return _summary()


def _summary() -> int:
    print()
    print(
        "[GATE] "
        + (
            "VERIFIED — deploy matches registry and 2026-07-28 contract"
            if not failures
            else f"BLOCKED — {len(failures)} failure(s)"
        )
    )
    for r in receipts:
        print("       " + r)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
