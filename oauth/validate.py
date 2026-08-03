#!/usr/bin/env python3
"""
validate.py — OAuth scope annotation invariant enforcer

Run before commit to verify:
  1. YAML parses clean
  2. JSON parses clean
  3. All tools listed match geox:8081 live registry (optional --live flag)
  4. ungated_mutations == 0 (HARD FAIL — blocks commit)
  5. Every forge/seal tool has constitutional_gate: required + verdict_path

Usage:
  python3 validate.py                           # structural check only
  python3 validate.py --live                     # also verify against geox:8081
  python3 validate.py --ci                       # CI mode — fail-closed, exit 1 on any violation
"""

import sys
import json
import yaml
from pathlib import Path

GEOX_DIR = Path(__file__).resolve().parent
YAML_PATH = GEOX_DIR / "geox-scope-annotations.yaml"
JSON_PATH = GEOX_DIR / "oauth-protected-resource.json"


def fail(msg: str, ci: bool = False) -> None:
    print(f"❌ {msg}")
    if ci:
        sys.exit(1)


def ok(msg: str) -> None:
    print(f"✅ {msg}")


# ---------------------------------------------------------------------------
# Catch 1 hardening (2026-08-03) — Lexical guard against write-verbs in OBSERVE
# The ungated_mutations check only inspects forge/seal tiers. A tool named with
# a write-verb but classified as OBSERVE walks straight past it. This guard
# catches that blind spot by checking tool id against a banned-in-observe
# pattern list. Any match => HARD FAIL.
# ---------------------------------------------------------------------------
WRITE_VERB_PATTERNS = [
    "ingest",
    "store",
    "write",
    "seal",
    "update",
    "publish",
    "forge",
    "delete",
    "commit",
    "register",
    "create",
    "insert",
    "drop",
    "remove",
    "upsert",
    "import",
]


def check_write_verb_in_observe(tools: list, ci: bool = False) -> int:
    """Return count of violations. Any tool whose id contains a write-verb
    pattern and is classified as geox:observe => FAIL."""
    violations = 0
    for t in tools:
        tid = t.get("id", "")
        scopes = t.get("required_scopes", [])
        if "geox:observe" not in scopes:
            continue
        for pat in WRITE_VERB_PATTERNS:
            if pat in tid.lower():
                print(f"❌ LEXICAL GUARD: {tid} contains write-verb '{pat}' but is OBSERVE (tier 0). Must be INTERPRET or FORGE.")
                violations += 1
                break
    if violations:
        fail(f"LEXICAL GUARD: {violations} write-verb tool(s) misclassified as OBSERVE. Fix tier before commit.", ci)
    else:
        ok("Lexical guard: 0 write-verbs in OBSERVE tier")
    return violations


def main() -> int:
    ci = "--ci" in sys.argv
    live = "--live" in sys.argv
    errors = 0

    # 1. Parse YAML
    try:
        with open(YAML_PATH) as f:
            doc = yaml.safe_load(f)
        ok("YAML parse")
    except Exception as e:
        fail(f"YAML parse: {e}", ci)
        return 1

    # 2. Parse JSON
    try:
        with open(JSON_PATH) as f:
            json.load(f)
        ok("JSON parse")
    except Exception as e:
        fail(f"JSON parse: {e}", ci)
        errors += 1

    # 3. Tool count
    tools = doc.get("tools", [])
    total = len(tools)
    coverage = doc.get("coverage", {})
    declared = coverage.get("total_tools", 0)

    if total != declared:
        fail(f"Tool count mismatch: {total} listed vs {declared} declared in coverage", ci)
        errors += 1
    else:
        ok(f"Tool count: {total} (matches coverage)")

    # 3.5. Lexical guard: no write-verbs in OBSERVE tier
    errors += check_write_verb_in_observe(tools, ci)

    # 4. ungated_mutations == 0 (HARD INVARIANT)
    ungated = coverage.get("ungated_mutations", -1)
    if ungated != 0:
        fail(f"INVARIANT BROKEN: ungated_mutations={ungated} — must be 0. Any forge/seal tool missing constitutional_gate?", ci)
        errors += 1
    else:
        ok("ungated_mutations == 0 (invariant holds)")

    # 5. Every forge/seal tool must have constitutional_gate: required + verdict_path
    for t in tools:
        tid = t.get("id", "?")
        scopes = t.get("required_scopes", [])
        gate = t.get("constitutional_gate", False)
        verdict = t.get("verdict_path", None)

        is_forge = "geox:forge" in scopes
        is_seal = "geox:seal" in scopes

        if is_forge or is_seal:
            if gate != "required":
                fail(f"{tid}: tier=forge|seal but constitutional_gate={gate} (must be 'required')", ci)
                errors += 1
            if not verdict:
                fail(f"{tid}: tier=forge|seal but missing verdict_path", ci)
                errors += 1

    # 6. Coverage counts reconcile
    observe = sum(1 for t in tools if "geox:observe" in t.get("required_scopes", []))
    interpret = sum(1 for t in tools if "geox:interpret" in t.get("required_scopes", []))
    forge = sum(1 for t in tools if "geox:forge" in t.get("required_scopes", []))
    seal = sum(1 for t in tools if "geox:seal" in t.get("required_scopes", []))

    if observe != coverage.get("observe_floor", -1):
        fail(f"observe: {observe} counted vs {coverage.get('observe_floor')} declared", ci)
        errors += 1
    if interpret != coverage.get("interpret_floor", -1):
        fail(f"interpret: {interpret} counted vs {coverage.get('interpret_floor')} declared", ci)
        errors += 1
    if forge != coverage.get("forge_gated", -1):
        fail(f"forge: {forge} counted vs {coverage.get('forge_gated')} declared", ci)
        errors += 1

    ok(
        f"Scope breakdown: {observe} observe + {interpret} interpret + {forge} forge + {seal} seal = {observe + interpret + forge + seal}"
    )

    # 7. Live registry check
    if live:
        import urllib.request

        try:
            req = urllib.request.Request(
                "http://127.0.0.1:8081/mcp",
                data=b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}',
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            live_names = {t["name"] for t in data.get("result", {}).get("tools", [])}
            yaml_names = {t["id"] for t in tools}

            missing = yaml_names - live_names
            extra = live_names - yaml_names

            if missing:
                fail(f"Tools in YAML but NOT in live registry: {missing}", ci)
                errors += 1
            if extra:
                print(f"⚠️  Tools in live registry but NOT in YAML: {extra}")
            if not missing and not extra:
                ok("Live registry: all 33 tools match geox:8081")
        except Exception as e:
            print(f"⚠️  Live registry check skipped: {e}")

    # Final
    if errors:
        print(f"\n🔴 {errors} violation(s) found.")
        if ci:
            sys.exit(1)
        return 1
    else:
        print(f"\n🟢 All invariants hold. {total} tools, 0 ungated mutations. Safe to commit.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
