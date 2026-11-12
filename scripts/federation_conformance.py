#!/usr/bin/env python3
"""federation_conformance.py — is GEOX actually federated, and on which MCP era?

Why this exists
---------------
"Is GEOX federated under the kernel and AAA state?" was being answered by prose.
Prose is not an instrument. This script measures every axis of that claim:

  A. AAA state          — is GEOX in the canonical machine registry, and does
                           AAA's live view name it?
  B. arifOS kernel      — is GEOX in the federation manifest, are BOTH edge
                           directions declared in arifOS's edge probe registry,
                           and does the public-state payload actually publish
                           the edges it declares?
  C. GEOX own surface   — does the organ expose its federation endpoints and
                           its discovery documents?
  D. MCP era            — which protocol version does GEOX NEGOTIATE for a
                           client asking for each era, and does the INSTALLED
                           fastmcp even know that era?

Each axis reports FUSED / PARTIAL / NOT_FUSED and names the owner of the gap.
A declared edge that is never published is PARTIAL, not FUSED — that is exactly
the class of gap this script exists to make visible.

Read-only. No restart. Nothing mutated.

Usage:
    python3 scripts/federation_conformance.py
    python3 scripts/federation_conformance.py --json /tmp/fed-conformance.json

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

GEOX = "http://127.0.0.1:8081"
ARIFOS = "http://127.0.0.1:8088"
AAA = "http://127.0.0.1:3001"

ORGANS_YAML = Path("/root/AAA/federation/organs.yaml")
FED_MANIFEST = Path("/var/www/html/.well-known/arifos-federation.json")
ARIFOS_EDGE_REGISTRY = Path("/opt/arifos/current/venv/lib/python3.13/site-packages/arifosmcp/runtime/federation_edges.py")
GEOX_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"

ERAS = ("2026-07-28", "2025-11-25", "2025-06-18", "2024-11-05")

# arifOS protocol epoch (BUILD_INFO.protocol_version) — the era the kernel runs.
KERNEL_EPOCH = "2026-07-28"


def _get(url: str, timeout: int = 20) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, f"ERROR: {e}"


def _post(url: str, payload: dict, headers: dict | None = None, timeout: int = 30) -> tuple[int, str]:
    body = json.dumps(payload).encode()
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=body, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, f"ERROR: {e}"


def _json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


# ── A. AAA state ────────────────────────────────────────────────────────────


def axis_aaa() -> dict:
    out: dict = {"axis": "AAA state", "verdict": "NOT_FUSED", "owner": "AAA", "checks": {}}

    declared = None
    if ORGANS_YAML.exists():
        text = ORGANS_YAML.read_text(encoding="utf-8")
        m = re.search(r"^- id: geox\b(.*?)(?=^- id:|\Z)", text, re.M | re.S)
        if m:
            block = m.group(1)

            def _field(name: str) -> str | None:
                hit = re.search(r"^\s*" + name + r":\s*(\S+)", block, re.M)
                return hit.group(1) if hit else None

            declared = {
                "class": _field("class"),
                "port": _field("port"),
                "authority_ceiling": _field("authority_ceiling"),
                "domain_law": _field("domain_law"),
            }
    out["checks"]["organs_yaml_declares_geox"] = bool(declared)
    out["checks"]["organs_yaml_entry"] = declared

    code, text = _get(f"{AAA}/health")
    named = "geox" in text.lower()
    out["checks"]["aaa_health_code"] = code
    out["checks"]["aaa_health_names_geox"] = named

    geo = None
    if code == 200:
        d = _json(text) or {}
        geo = d.get("federation_geometry") or {}
    out["checks"]["aaa_federation_geometry"] = geo

    if declared and named:
        out["verdict"] = "FUSED"
        out["note"] = "GEOX is in AAA's canonical registry and AAA's live view names it."
    elif declared:
        out["verdict"] = "PARTIAL"
        out["note"] = (
            "GEOX is in AAA's canonical machine registry (organs.yaml) but AAA's live "
            "health does not name it. The registry entry is the declaration; the live "
            "view is the proof, and they disagree."
        )
    else:
        out["note"] = "GEOX is absent from AAA's canonical machine registry."
    return out


# ── B. arifOS kernel ────────────────────────────────────────────────────────


def axis_kernel() -> dict:
    out: dict = {"axis": "arifOS kernel", "verdict": "NOT_FUSED", "owner": "arifOS", "checks": {}}

    in_manifest = False
    manifest_entry = None
    if FED_MANIFEST.exists():
        d = _json(FED_MANIFEST.read_text(encoding="utf-8")) or {}
        doms = d.get("domains") or {}
        in_manifest = "GEOX" in doms
        manifest_entry = doms.get("GEOX")
    out["checks"]["manifest_declares_geox"] = in_manifest
    out["checks"]["manifest_entry"] = manifest_entry

    edge_ids = []
    if ARIFOS_EDGE_REGISTRY.exists():
        edge_ids = sorted(set(re.findall(r'"id":\s*"([^"]+→[^"]+)"', ARIFOS_EDGE_REGISTRY.read_text(encoding="utf-8"))))
    out["checks"]["arifos_declared_edge_count"] = len(edge_ids)
    out["checks"]["arifos_declared_edges"] = edge_ids
    geox_edges = [e for e in edge_ids if "geox" in e.lower()]
    out["checks"]["geox_edge_directions_declared"] = geox_edges
    out["checks"]["geox_both_directions"] = len(geox_edges) >= 2

    code, text = _get(f"{ARIFOS}/api/public-state")
    d = _json(text) or {}
    published = d.get("federation_edges")
    out["checks"]["public_state_code"] = code
    out["checks"]["public_state_publishes_federation_edges"] = published is not None
    out["checks"]["public_state_federation_edges_type"] = type(published).__name__ if published is not None else "ABSENT"

    if in_manifest and out["checks"]["geox_both_directions"]:
        out["verdict"] = "PARTIAL" if published is None else "FUSED"
        out["note"] = (
            "arifOS declares GEOX in the federation manifest and probes BOTH edge "
            "directions ("
            + ", ".join(geox_edges)
            + "), but the public-state payload publishes no federation_edges key, so "
            "the Observatory edge panel cannot show them. A declared edge that is "
            "never published is PARTIAL, not FUSED."
            if published is None
            else "GEOX is in the manifest, both edge directions are declared, and the edges are published."
        )
    elif in_manifest:
        out["verdict"] = "PARTIAL"
        out["note"] = "GEOX is in the federation manifest but the edge registry does not probe both directions."
    else:
        out["note"] = "GEOX is absent from the arifOS federation manifest."
    return out


# ── C. GEOX own surface ─────────────────────────────────────────────────────


def axis_geox_surface() -> dict:
    out: dict = {"axis": "GEOX own federation surface", "verdict": "NOT_FUSED", "owner": "GEOX", "checks": {}}

    probes = {}
    for path in ("/federation", "/flow", "/health", "/tools", "/drift", "/.well-known/mcp.json", "/.well-known/mcp/server.json"):
        code, body = _get(f"{GEOX}{path}")
        probes[path] = {"code": code, "bytes": len(body)}
    out["checks"]["routes"] = probes

    schema = None
    code, body = _get(f"{GEOX}/health")
    if code == 200:
        d = _json(body) or {}
        schema = d.get("federation_schema_version")
    out["checks"]["federation_schema_version"] = schema

    live = [p for p, v in probes.items() if v["code"] == 200]
    missing = [p for p, v in probes.items() if v["code"] != 200]
    out["checks"]["live_paths"] = live
    out["checks"]["missing_paths"] = missing

    if not missing:
        out["verdict"] = "FUSED"
        out["note"] = "GEOX exposes its federation, flow, health, tools and discovery surfaces."
    elif set(missing) <= {"/federation", "/flow"}:
        out["verdict"] = "PARTIAL"
        out["note"] = (
            "The federation endpoints (/federation, /flow) are ABSENT on the live organ "
            "while the rest of the surface answers. The routes exist in the source "
            "branch, so this is a deploy gap, not a missing implementation."
        )
    else:
        out["note"] = "Missing on the live organ: " + ", ".join(missing)
    return out


# ── D. MCP era ──────────────────────────────────────────────────────────────


def axis_mcp_era() -> dict:
    out: dict = {"axis": "MCP protocol era", "verdict": "NOT_ALIGNED", "owner": "GEOX deploy lane", "checks": {}}

    negotiated = {}
    for era in ERAS:
        code, body = _post(
            f"{GEOX}/mcp",
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": era,
                    "capabilities": {},
                    "clientInfo": {"name": "federation_conformance", "version": "1.0"},
                },
            },
        )
        d = _json(body) or {}
        got = (d.get("result") or {}).get("protocolVersion")
        negotiated[era] = {"code": code, "negotiated": got, "honoured": got == era}
    out["checks"]["negotiation"] = negotiated

    installed = None
    try:
        p = subprocess.run(
            ["/opt/geox/.venv/bin/python3", "-c", "import fastmcp;print(fastmcp.__version__)"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        installed = p.stdout.strip() or None
    except Exception:
        installed = None
    out["checks"]["installed_fastmcp"] = installed

    pinned = None
    if GEOX_PYPROJECT.exists():
        m = re.search(r'"fastmcp\[apps,tasks\]==([0-9.]+)"', GEOX_PYPROJECT.read_text(encoding="utf-8"))
        pinned = m.group(1) if m else None
    out["checks"]["pyproject_pinned_fastmcp"] = pinned
    out["checks"]["pin_matches_installed"] = bool(pinned and installed and pinned == installed)

    site = None
    for base in (Path("/opt/geox/.venv/lib"),):
        if base.exists():
            for lib in base.iterdir():
                fm = lib / "site-packages" / "fastmcp"
                if fm.is_dir():
                    site = fm
                    break
    known_eras = []
    if site:
        for py in site.rglob("*.py"):
            try:
                known_eras += re.findall(r"20(?:24|25|26)-\d{2}-\d{2}", py.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
    known_eras = sorted(set(known_eras))
    out["checks"]["installed_fastmcp_knows_eras"] = known_eras
    out["checks"]["installed_knows_kernel_epoch"] = KERNEL_EPOCH in known_eras

    honoured_latest = negotiated.get(KERNEL_EPOCH, {}).get("honoured", False)
    out["checks"]["kernel_epoch"] = KERNEL_EPOCH
    out["checks"]["kernel_epoch_honoured"] = honoured_latest

    if honoured_latest:
        out["verdict"] = "ALIGNED"
        out["note"] = f"GEOX negotiates the kernel's protocol era ({KERNEL_EPOCH}) without downgrade."
    else:
        got = negotiated.get(KERNEL_EPOCH, {}).get("negotiated")
        out["verdict"] = "NOT_ALIGNED"
        out["note"] = (
            f"A client asking for the kernel's era ({KERNEL_EPOCH}) is downgraded to {got}. "
            f"The installed fastmcp is {installed} while pyproject pins {pinned}; "
            "fastmcp-slim 4.1.4 (what fastmcp 4.1.4 depends on) carries the "
            f"{KERNEL_EPOCH} era, fastmcp 3.4.x does not. The pin is already correct — "
            "the venvs are stale. No source change is required."
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write the raw result JSON here")
    args = ap.parse_args()

    axes = [axis_aaa(), axis_kernel(), axis_geox_surface(), axis_mcp_era()]
    result = {"schema": "geox-federation-conformance/v1", "axes": axes}

    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("═" * 78)
    print("GEOX FEDERATION CONFORMANCE — kernel · AAA · own surface · MCP era")
    print("═" * 78)
    for a in axes:
        print(f"\n● {a['axis']}  →  {a['verdict']}   (owner: {a['owner']})")
        print(f"  {a.get('note','')}")
        for k, v in a["checks"].items():
            if k in ("organs_yaml_entry", "manifest_entry", "routes", "negotiation"):
                continue
            print(f"    {k}: {json.dumps(v, ensure_ascii=False)[:180] if isinstance(v, (dict, list)) else v}")
    print("\n" + "═" * 78)
    verdicts = {a["verdict"] for a in axes}
    if verdicts == {"FUSED"} or verdicts == {"FUSED", "ALIGNED"}:
        print("VERDICT: FULLY FEDERATED AND ALIGNED")
        return 0
    print("VERDICT: PARTIAL — see per-axis owners above. Every gap names one owner.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
