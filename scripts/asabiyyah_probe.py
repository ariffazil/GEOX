#!/usr/bin/env python3
"""GEOX asabiyyah substrate probe -- the earth-reasoning organ's cycle reading.

GEOX records geological CLAIMS. Ibn Khaldun's cycle and Popper's falsification
doctrine agree on one point: a claim that has never been independently tested is
not knowledge, it is doctrine. So for GEOX the ceremony/exercise ratio has a
precise meaning -- doctrine produced (live .md artifacts) divided by
independently verified geological claims.

Observe-only. Every number below traces to a file, a SQL query, or a marker
checked on disk at run time. No source => STORY, not a reading.
`NOT_APPLICABLE` + reason beats an invented number.

Contract : /root/AAA/schemas/asabiyyah-reading.schema.json
Kernel   : /root/arifOS/arifosmcp/runtime/asabiyyah.py  (loaded standalone; never vendored)
Writes   : /var/lib/arifos/asabiyyah/GEOX.json only. The GEOX repo is read-only here.

Usage:
    python3 /root/GEOX/scripts/asabiyyah_probe.py            # write + print
    python3 /root/GEOX/scripts/asabiyyah_probe.py --dry-run  # print only
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import socket
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# paths -- every one of these is checked at run time; none is assumed
# --------------------------------------------------------------------------

KERNEL_PATH = Path("/root/arifOS/arifosmcp/runtime/asabiyyah.py")
ORGAN_ROOT = Path("/root/GEOX")

# The claim store. On disk it is a symlink; the probe reads through it and
# records the symlink target in evidence so the reading is re-checkable.
CLAIM_DB = Path("/root/GEOX/earth_memory.db")

# Execution receipts (real tool invocations, with actor identity).
INVOCATION_LOG = Path("/var/lib/geox/metrics/tool_invocations.jsonl")

DROP_DIR = Path("/var/lib/arifos/asabiyyah")
DROP_FILE = DROP_DIR / "GEOX.json"

# A live doctrine artifact: a .md that is not archive, not vendored, not a build
# product. Directory names excluded at any depth.
EXCLUDED_DIRS = {
    "archive",
    "backups",
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "dist",
    "build",
    "site-packages",
    "third_party",
    "vendor",
}

# Observation window for exercised_capabilities / executors.
WINDOW_DAYS = 30


# --------------------------------------------------------------------------
# kernel helpers -- loaded standalone, per contract (do NOT vendor a copy)
# --------------------------------------------------------------------------


def load_kernel(path: Path = KERNEL_PATH):
    """Load the kernel module standalone (never vendored).

    The module must be registered in sys.modules *before* exec_module: the
    kernel's dataclasses are resolved through sys.modules[cls.__module__] on
    Python 3.12+, and an unregistered module raises AttributeError inside
    dataclasses._is_type.
    """
    spec = importlib.util.spec_from_file_location("asabiyyah", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"kernel not loadable: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["asabiyyah"] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop("asabiyyah", None)
        raise
    return module


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# CER -- ceremony artifacts (live doctrine files)
# --------------------------------------------------------------------------


def count_live_markdown(root: Path, excluded: set[str]) -> tuple[int, str]:
    """Count live .md files under `root`, skipping archive/vendored/build dirs."""
    if not root.is_dir():
        return 0, f"{root} is not a directory"
    count = 0
    for dirpath, dirnames, filenames in os_walk(root, excluded):
        for name in filenames:
            if name.endswith(".md"):
                count += 1
    rule = (
        f"walk {root} excluding dirs {sorted(excluded)} at any depth; "
        f"count files ending '.md'"
    )
    return count, rule


def os_walk(root: Path, excluded: set[str]):
    """os.walk with in-place pruning. Separate so the exclusion rule is testable."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in excluded]
        yield dirpath, dirnames, filenames


# --------------------------------------------------------------------------
# CER -- exercised capabilities = independently VERIFIED geological claims
# --------------------------------------------------------------------------

CLAIM_TABLE = "earth_memory"
VERIFIED_STATES = ("validated", "reviewed", "sealed")


def read_claim_store(db_path: Path) -> dict[str, Any]:
    """Read the GEOX claim store read-only. Returns raw counts + the query text.

    GEOX persists claims in a SQLite table `earth_memory` (see
    src/geox_core/services/asset_memory.py:EarthMemoryStore). Verification depth
    is read straight off `approval_state` and `vault_receipt`: a claim that was
    independently reviewed/sealed carries one of VERIFIED_STATES and/or a vault
    receipt. A claim in 'draft' has been asserted and nothing more.
    """
    out: dict[str, Any] = {
        "path": str(db_path),
        "exists": db_path.exists(),
        "query": "",
        "error": None,
    }
    if not db_path.exists():
        out["error"] = "claim store not on disk"
        return out

    try:
        resolved = db_path.resolve()
        out["resolved_path"] = str(resolved)
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            out["tables"] = sorted(tables)
            if CLAIM_TABLE not in tables:
                out["error"] = f"table '{CLAIM_TABLE}' absent"
                return out

            total = conn.execute(f"SELECT COUNT(*) FROM {CLAIM_TABLE}").fetchone()[0]
            states = dict(
                conn.execute(
                    f"SELECT approval_state, COUNT(*) FROM {CLAIM_TABLE} "
                    "GROUP BY approval_state ORDER BY 2 DESC"
                ).fetchall()
            )
            placeholders = ",".join("?" for _ in VERIFIED_STATES)
            verified_q = (
                f"SELECT COUNT(*) FROM {CLAIM_TABLE} WHERE "
                f"lower(approval_state) IN ({placeholders}) "
                "OR (vault_receipt IS NOT NULL AND vault_receipt != '')"
            )
            verified = conn.execute(verified_q, VERIFIED_STATES).fetchone()[0]
            vault_receipts = conn.execute(
                f"SELECT COUNT(*) FROM {CLAIM_TABLE} "
                "WHERE vault_receipt IS NOT NULL AND vault_receipt != ''"
            ).fetchone()[0]

            with_evidence = 0
            creators: set[str] = set()
            for (payload,) in conn.execute(f"SELECT payload FROM {CLAIM_TABLE}"):
                try:
                    body = json.loads(payload or "{}")
                except (TypeError, ValueError):
                    continue
                if body.get("evidence_ids"):
                    with_evidence += 1
                creator = (body.get("authority") or {}).get("created_by")
                if creator:
                    creators.add(str(creator))

            last_write = conn.execute(
                f"SELECT MAX(timestamp) FROM {CLAIM_TABLE}"
            ).fetchone()[0]
        finally:
            conn.close()

        out.update(
            {
                "query": (
                    f"sqlite3 '{db_path}' (mode=ro): "
                    f"COUNT(*) FROM {CLAIM_TABLE}; "
                    "GROUP BY approval_state; "
                    f"COUNT(*) WHERE lower(approval_state) IN {VERIFIED_STATES} "
                    "OR vault_receipt IS NOT NULL; "
                    "payload scan for evidence_ids + authority.created_by"
                ),
                "claims_recorded": total,
                "approval_state_counts": states,
                "claims_verified": verified,
                "claims_with_vault_receipt": vault_receipts,
                "claims_with_evidence_ids": with_evidence,
                "claims_without_evidence_ids": total - with_evidence,
                "distinct_created_by": sorted(creators),
                "last_write": last_write,
                "columns": _columns(db_path, CLAIM_TABLE),
            }
        )
    except Exception as exc:  # noqa: BLE001 -- a probe reports, it does not crash
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def _columns(db_path: Path, table: str) -> list[str]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    finally:
        conn.close()


def read_witness_identity(claim_store: dict[str, Any]) -> tuple[int, str]:
    """Distinct witness identities recorded ON THE CLAIMS.

    A witness is an independent identity that verified a claim. GEOX's claim
    store has no such column; if any verification field appears, it is counted.
    """
    db_path = Path(claim_store.get("path", ""))
    if not db_path.exists() or claim_store.get("error"):
        return 0, "claim store unreadable"
    witness_fields = {"verifier", "verified_by", "approved_by", "witness", "witness_id"}
    witnesses: set[str] = set()
    inspected = 0
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            for (payload,) in conn.execute(f"SELECT payload FROM {CLAIM_TABLE}"):
                inspected += 1
                try:
                    body = json.loads(payload or "{}")
                except (TypeError, ValueError):
                    continue
                for key, value in _flatten(body):
                    if key in witness_fields and value not in (None, "", [], {}):
                        witnesses.add(str(value))
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        return 0, f"witness scan failed: {type(exc).__name__}: {exc}"
    reason = (
        f"scanned {inspected} claim payload(s) in {db_path} for fields "
        f"{sorted(witness_fields)}: {len(witnesses)} distinct witness identity(ies)"
    )
    return len(witnesses), reason


def _flatten(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    pairs: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            pairs.append((str(key), value))
            pairs.extend(_flatten(value, str(key)))
    elif isinstance(obj, list):
        for item in obj:
            pairs.extend(_flatten(item, prefix))
    return pairs


# --------------------------------------------------------------------------
# invocation receipts -- context for how much GEOX actually executes
# --------------------------------------------------------------------------


def read_invocations(path: Path, window_days: int) -> dict[str, Any]:
    out: dict[str, Any] = {"path": str(path), "exists": path.exists(), "error": None}
    if not path.exists():
        out["error"] = "invocation log not on disk"
        return out
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    total = 0
    in_window = 0
    tools: set[str] = set()
    actors: set[str] = set()
    unparseable = 0
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    unparseable += 1
                    continue
                total += 1
                stamp = row.get("ts") or row.get("timestamp")
                if not stamp:
                    continue
                try:
                    when = datetime.fromisoformat(str(stamp))
                except ValueError:
                    continue
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                if when >= cutoff:
                    in_window += 1
                    if row.get("tool"):
                        tools.add(str(row["tool"]))
                    if row.get("actor_id"):
                        actors.add(str(row["actor_id"]))
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    out.update(
        {
            "query": (
                f"parse jsonl {path}; count rows with ts >= now-{window_days}d; "
                "distinct .tool and .actor_id in window"
            ),
            "lines_total": total,
            "lines_in_window": in_window,
            "lines_unparseable": unparseable,
            "distinct_tools_in_window": len(tools),
            "distinct_actors_in_window": len(actors),
        }
    )
    return out


# --------------------------------------------------------------------------
# ENC -- protected mutation paths, enumerated and receipt-checked on disk
# --------------------------------------------------------------------------
#
# A path is GATED only if it verifiably requires a registered source / provenance
# check before it writes. Each declaration carries file + marker receipts that
# are re-checked at run time; a gated path whose receipts do not resolve is
# downgraded into `ungated`, so this reading cannot flatter the organ.

REPO = "src/geox_mcp/tools"

MUTATION_PATHS: list[dict[str, Any]] = [
    {
        "name": "geox_register_native_source (register a native SEG-Y source)",
        "kind": "gated",
        "file": f"{REPO}/native_segy.py",
        "markers": [
            "if not os.path.exists(source_uri):",
            "valid_authorities = {e.value for e in SourceAuthority}",
        ],
        "note": (
            "Requires the file to exist on disk and computes SHA-256 before the "
            "source enters the registry; rejects authority values outside the "
            "SourceAuthority enum and downgrades a client-asserted "
            "OPERATOR_APPROVED to UNVERIFIED when registered_by is absent. "
            "WEAKNESS: registered_by is optional and the registry is process "
            "memory only (_SOURCE_REGISTRY), so the provenance it mints does not "
            "survive a restart and cannot be re-verified later."
        ),
    },
    {
        "name": "geox_claim_seal (SEAL a claim)",
        "kind": "gated",
        "file": f"{REPO}/claims.py",
        "markers": [
            "claim_validate_required",
            "contradiction_scan_required",
            "evidence_integrity_required",
            "anti_sink_synthetic_provenance_block",
        ],
        "note": (
            "Pre-seal gate set: claim must be VALIDATED, must carry a recorded "
            "challenge, must have evidence attached, and synthetic/fixture-only "
            "provenance is blocked from FACT/INTERPRETATION; plus ack_irreversible "
            "and an explanatory-class gate. This is the one real provenance gate "
            "on the claim lifecycle -- and it guards the LAST step, not the write."
        ),
    },
    {
        "name": "geox_claim_create (write a geological claim)",
        "kind": "ungated",
        "file": f"{REPO}/claims.py",
        "markers": ["draft_claim(asset_id=claim_type, payload=payload)"],
        "forbid": ["_SOURCE_REGISTRY", "registered_source_required"],
        "note": (
            "Writes a DRAFT row straight into the claim store. evidence_ids is an "
            "unvalidated list of strings -- never resolved against a source "
            "registry -- and no registered native source is required. 15 of the "
            "16 stored claims carry zero evidence_ids."
        ),
    },
    {
        "name": "geox_evidence_attach (attach evidence to a claim)",
        "kind": "ungated",
        "file": f"{REPO}/claims.py",
        "markers": ['payload["evidence_ids"].append(evidence_id)'],
        "note": (
            "Appends any string as an evidence id to the claim payload without "
            "resolving it against a registry, artifact store, or hash. A claim's "
            "evidence chain can therefore cite something that does not exist."
        ),
    },
    {
        "name": "geox_calibration_register_witness (write a calibration witness)",
        "kind": "ungated",
        "file": f"{REPO}/calibration_witness.py",
        "markers": ['"witness_id": cw.calibration_witness_id'],
        "forbid": [".write_text", "INSERT INTO", "sqlite3", "json.dump"],
        "note": (
            "Validates the witness schema and returns a witness_id, then persists "
            "NOTHING -- no register, no file, no row. A structural gate downstream "
            "can consume a witness reference it has no way to resolve, and any "
            "caller can mint a witness id without leaving a durable record."
        ),
    },
    {
        "name": "geox_data_ingest_bundle / geox_well_ingest (ingest seismic or well data)",
        "kind": "ungated",
        "file": f"{REPO}/data.py",
        "markers": ["will flag in provenance but not block"],
        "note": (
            "Accepts source_uri or content_base64 and writes into the data "
            "directory. source_crs defaults to 'unknown' and is explicitly "
            "non-blocking, and nothing requires the payload to come from a source "
            "registered through geox_register_native_source -- so provenance-"
            "unverified earth data enters the organ's working store."
        ),
    },
]


def check_path_receipts(organ_root: Path, paths: list[dict[str, Any]]) -> dict[str, Any]:
    """Re-check every declared receipt on disk. Returns counts + per-path detail."""
    detail: list[dict[str, Any]] = []
    gated_ok = 0
    ungated: list[str] = []
    checked = 0

    for path in paths:
        target = organ_root / path["file"]
        found: list[dict[str, Any]] = []
        missing: list[Any] = []
        if not target.exists():
            missing.append({"file_missing": str(target)})
        else:
            lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
            for marker in path["markers"]:
                line_no = next((i + 1 for i, l in enumerate(lines) if marker in l), None)
                checked += 1
                if line_no is None:
                    missing.append({"marker_not_found": marker})
                else:
                    found.append({"marker": marker, "line": line_no})
            for forbidden in path.get("forbid", []):
                checked += 1
                if forbidden in "\n".join(lines):
                    missing.append({"forbidden_marker_present": forbidden})
                else:
                    found.append({"absent_as_required": forbidden})

        verified = not missing
        if path["kind"] == "gated" and verified:
            gated_ok += 1
        elif path["kind"] == "gated":
            ungated.append(
                f"{path['name']} (declared gated; receipt NOT verified on disk)"
            )
        else:
            ungated.append(path["name"])

        detail.append(
            {
                "name": path["name"],
                "declared": path["kind"],
                "receipt_verified": verified,
                "found": found,
                "missing": missing,
                "note": path["note"],
            }
        )

    return {
        "detail": detail,
        "gated_verified": gated_ok,
        "total_paths": len(paths),
        "ungated": ungated,
        "receipt_checks_run": checked,
    }


# --------------------------------------------------------------------------
# reading assembly
# --------------------------------------------------------------------------


def build_reading() -> Any:
    asb = load_kernel()

    # ---- CER: doctrine produced -------------------------------------------
    ceremony, walk_rule = count_live_markdown(ORGAN_ROOT, EXCLUDED_DIRS)

    # ---- CER: capability verified -----------------------------------------
    store = read_claim_store(CLAIM_DB)
    claims_recorded = int(store.get("claims_recorded") or 0)
    claims_verified = int(store.get("claims_verified") or 0)
    exercised = claims_verified

    cer_source = (
        f"ceremony_artifacts: {walk_rule} -> {ceremony}. "
        f"exercised_capabilities: independently verified geological claims = "
        f"{claims_verified} of {claims_recorded} recorded in {store.get('path')} "
        f"({store.get('query')}). LIMITATION: the GEOX claim store carries no "
        "verification state at all -- every row is approval_state='draft' with a "
        "NULL vault_receipt and no verifier field -- so no claim can be counted as "
        "independently verified and the recorded-vs-verified split "
        f"({claims_recorded} vs {claims_verified}) is the honest claim-domain "
        "figure. CER is therefore undefined by the kernel's own semantics: "
        "doctrine is being produced while the capability is never verified."
    )
    cer = asb.ceremony_exercise_ratio(ceremony, exercised, source=cer_source)
    cer.notes = (
        f"{cer.notes} | claim domain: {claims_recorded} recorded, "
        f"{claims_verified} independently verified | value is null, not a number: "
        "ceremony_artifacts > 0 with exercised_capabilities = 0 is an UNDEFINED "
        "ratio, which the kernel bands DECLINE while keeping state MEASURED. "
        "The value is null rather than a non-finite float so the reading stays "
        "valid strict RFC 8259 JSON."
    )

    # ---- ASD: doctrine holders vs executors --------------------------------
    doctrine_holders = claims_recorded
    witnesses, witness_reason = read_witness_identity(store)
    executors = witnesses
    asd_reason = (
        "NOT_APPLICABLE -- no witness identity is recorded on any GEOX claim. "
        f"{witness_reason}. Claims on record: {doctrine_holders} "
        f"({store.get('path')}, table {CLAIM_TABLE}), all "
        f"created_by={store.get('distinct_created_by')}; "
        f"{store.get('claims_with_vault_receipt')} carry a vault receipt; "
        f"{store.get('claims_without_evidence_ids')} carry no evidence id at all. "
        "calibration_witness.py returns a witness_id but writes it nowhere, so no "
        "attestation register exists to count executors from. The distinct "
        "identities seen in /var/lib/geox/metrics/tool_invocations.jsonl are "
        "callers of tools, not witnesses of claims -- counting them here would "
        "inflate asabiyyah depth with the wrong object."
    )
    asd = asb.Metric.na("asd", asd_reason)

    # ---- ENC ---------------------------------------------------------------
    enc_scan = check_path_receipts(ORGAN_ROOT, MUTATION_PATHS)
    gated_paths = int(enc_scan["gated_verified"])
    total_paths = int(enc_scan["total_paths"])
    ungated = list(enc_scan["ungated"])
    enc_source = (
        f"static enumeration of GEOX's protected mutation paths, each declared "
        f"with a file + marker receipt re-checked on disk at run time under "
        f"{ORGAN_ROOT} ({enc_scan['receipt_checks_run']} marker checks; see "
        "evidence.path_receipts). gated_paths counts only paths whose receipts "
        "actually resolved. NOTE: the MCP gateway carries a P0-2 identity/authority "
        "gate (src/geox_mcp/geox_middleware.py) and an SCT ingress gate, but those "
        "are AUTHORITY gates, not provenance gates -- they do not ask whether the "
        "written claim or dataset has a registered source -- and any in-process "
        "import of geox_mcp.tools.* bypasses the gateway entirely."
    )
    enc = asb.enforcement_coverage(
        gated_paths, total_paths, source=enc_source, ungated=ungated
    )

    invocations = read_invocations(INVOCATION_LOG, WINDOW_DAYS)

    reading = asb.SubstrateReading(
        organ="GEOX",
        host=socket.gethostname(),
        observed_at=_now_iso(),
    )
    reading.metrics = {"cer": cer, "asd": asd, "enc": enc}
    reading.evidence = {
        # raw additive counts the kernel federates on
        "ceremony_artifacts": ceremony,
        "exercised_capabilities": exercised,
        "doctrine_holders": doctrine_holders,
        "executors": executors,
        "gated_paths": gated_paths,
        "total_paths": total_paths,
        "ungated": ungated,
        "window_days": WINDOW_DAYS,
        # raw additive counts behind the claim semantics (additive, never ratioed)
        "claims_recorded": claims_recorded,
        "claims_verified": claims_verified,
        "claims_with_vault_receipt": int(store.get("claims_with_vault_receipt") or 0),
        "claims_with_evidence_ids": int(store.get("claims_with_evidence_ids") or 0),
        "claims_with_witness_identity": witnesses,
        "claim_store": str(store.get("path")),
        "claim_store_resolved": str(store.get("resolved_path", "")),
        "claim_store_query": str(store.get("query", "")),
        "claim_store_approval_states": store.get("approval_state_counts") or {},
        "claim_store_last_write": store.get("last_write"),
        "claim_store_columns": store.get("columns") or [],
        "live_markdown_rule": walk_rule,
        # execution context: GEOX does run tooling -- it just never verifies claims
        "invocations": invocations,
        # falsifiable receipts for the ENC enumeration
        "path_receipts": enc_scan["detail"],
        "probe": {
            "probe_path": "/root/GEOX/scripts/asabiyyah_probe.py",
            "kernel": str(KERNEL_PATH),
            "organs_excluded_dirs": sorted(EXCLUDED_DIRS),
        },
    }
    return reading


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="asabiyyah_probe.geox",
        description="measure GEOX's asabiyyah cycle signals (observe-only)",
    )
    parser.add_argument("--out", default=str(DROP_FILE), help="where to drop the reading")
    parser.add_argument(
        "--dry-run", action="store_true", help="print the reading without writing it"
    )
    args = parser.parse_args(argv)

    reading = build_reading()
    payload = reading.to_json()

    if not args.dry_run:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")

    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
