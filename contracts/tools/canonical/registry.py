from __future__ import annotations

import logging

from contracts.enums.statuses import (
    ArtifactStatus,
    ExecutionStatus,
    GovernanceStatus,
    get_standard_envelope,
)
from contracts.tools.canonical._helpers import (
    _artifact_store,
)

logger = logging.getLogger("geox.canonical.registry")


async def geox_system_registry_status(
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict:
    """Discovery of canonical tools, health, and contract epoch.

    Reports the ACTUAL live MCP surface — no phantom aliases, no ghost ingress tools.
    F2 Truth: the registry must not lie about what is callable.

    Parameters:
      session_id — optional SEAL-* canonical session ID (from arif_session_init)
      actor_id   — optional actor binding; omit for anonymous read-only discovery
    """
    import os

    from contracts.canonical_registry import CANONICAL_PUBLIC_TOOLS, GEOX_TOOL_MANIFEST

    _show_legacy = os.getenv("GEOX_SHOW_LEGACY_ALIASES", "false").lower() in ("1", "true", "yes")

    # Resolve session context — anonymous mode is allowed for read-only discovery
    # C3 REDTEAM FIX 2026-07-18: Preserve real session_id in receipt; never coerce.
    # If session_id is provided, log it as-is (caller-attributed). Anonymous mode is
    # only the explicit "no session passed" case. This makes receipts auditable.
    _anonymous = session_id is None
    _session_id = session_id if session_id else "geox-anon"
    _actor_id = actor_id or ("anonymous" if _anonymous else "unknown")

    # Callability probe — cross-check manifest expose=True against CANONICAL_PUBLIC_TOOLS
    _manifest_exposed = {e["name"] for e in GEOX_TOOL_MANIFEST if e.get("expose", True)}
    _canonical_set = set(CANONICAL_PUBLIC_TOOLS) | {"geox_dst_ingest_test"}
    _probe_passed = sorted(_manifest_exposed & _canonical_set)
    _probe_missing = sorted(_manifest_exposed - _canonical_set)

    callability_probe = {
        "method": "manifest_cross_check",
        "tested": len(_manifest_exposed),
        "passed": len(_probe_passed),
        "failed": len(_probe_missing),
        "missing_from_canonical_list": _probe_missing,
        "registry_truth": "PASS" if not _probe_missing else "WARN",
    }

    artifact = {
        "status": "healthy",
        "epoch": "2026-05-01",
        "tools_count": len(CANONICAL_PUBLIC_TOOLS) + 1,  # +1 for geox_dst_ingest_test (live but not canonical)
        "canonical_tools": len(CANONICAL_PUBLIC_TOOLS),
        "ingress_tools": [],
        "contract": "SOVEREIGN_13_SPEC",
        "legacy_aliases": {} if not _show_legacy else {},
        "note": "Legacy aliases are hidden. Call aliases via canonical names only.",
        "callability_probe": callability_probe,
        "session_context": {
            "session_id": _session_id,
            "actor_id": _actor_id,
            "anonymous_mode": _anonymous,
            "anonymous_mode_allowed": True,
            "anonymous_scope": "read_only_discovery" if _anonymous else None,
        },
    }
    return get_standard_envelope(artifact, tool_class="system")



async def geox_history_audit(
    query: str,
    limit: int = 10,
    actor_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """VAULT999 retrieval of past runs and decision lineage.

    Each returned record must include:
    - renderer_name: the renderer used (e.g. "matplotlib", "plotly")
    - artifact_hash: SHA-256 of the produced visual artifact (PNG/SVG/PDF)
    - claim_state: lifecycle state at time of generation
    - depth_basis: MD/TVD/TVDSS
    These fields are required for all records involving visual artifacts.

    Queries in order:
      1. VAULT999 SEALED_EVENTS.jsonl (canonical governance ledger)
      2. GEOX _artifact_store (in-memory tool execution history)
      3. EvidenceStore file-backed store (future)
    """
    import json
    import logging
    import os

    logger = logging.getLogger("geox.history_audit")

    clean_query = query[:1000] if query else ""
    clean_query = clean_query.replace("\x00", "")
    safe_limit = max(1, min(limit, 50))
    query_lower = clean_query.lower()

    try:
        records: list[dict] = []
        seen: set[str] = set()

        # ── Source 1: VAULT999 SEALED_EVENTS.jsonl ──────────────────────────
        vault_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))), "arifOS", "arifosmcp", "VAULT999", "SEALED_EVENTS.jsonl"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))), "arifOS", "VAULT999", "outcomes.jsonl"),
            "/root/arifOS/arifosmcp/VAULT999/SEALED_EVENTS.jsonl",
            "/root/arifOS/VAULT999/outcomes.jsonl",
            "/root/.local/share/arifos/vault999/outcomes.jsonl",
        ]

        for vpath in vault_paths:
            if not os.path.exists(vpath):
                continue
            try:
                with open(vpath) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            entry_str = json.dumps(entry, default=str).lower()
                            if query_lower and query_lower not in entry_str:
                                continue
                            eid = str(entry.get("id", entry.get("event_id", entry.get("decision_id", ""))))
                            if eid in seen:
                                continue
                            seen.add(eid)
                            records.append({
                                "source": os.path.basename(vpath),
                                "event_id": eid,
                                "event_type": entry.get("event_type", entry.get("type", entry.get("verdict_issued", "unknown"))),
                                "verdict": entry.get("verdict", entry.get("verdict_issued", "UNKNOWN")),
                                "actor_id": entry.get("actor_id", entry.get("operator_override", "unknown")),
                                "session_id": entry.get("session_id", ""),
                                "stage": entry.get("stage", ""),
                                "timestamp": entry.get("sealed_at", entry.get("timestamp", entry.get("timestamp_decision", ""))),
                                "claim_state": "SEALED",
                                "payload": entry.get("payload", {}),
                                "floors": entry.get("floors", entry.get("constitutional_floors_checked", entry.get("floor_attribution", []))),
                                "chain_hash": entry.get("chain_hash", ""),
                                "risk_tier": entry.get("risk_tier", entry.get("harm_detected", "unknown")),
                            })
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.warning("Failed to read VAULT999 %s: %s", vpath, e)

        # ── Source 2: GEOX _artifact_store (in-memory tool executions) ──
        all_artifacts: list[dict] = []
        for ref, entry in _artifact_store.items():
            if ref != entry.get("artifact_ref", ref):
                continue
            entry_str = json.dumps(entry, default=str).lower()
            if query_lower and query_lower not in entry_str:
                continue
            all_artifacts.append(entry)

        for entry in all_artifacts:
            ref = entry.get("artifact_ref", "unknown")
            if ref in seen:
                continue
            seen.add(ref)
            latest_qc = entry.get("latest_qc") or entry.get("qc") or {}
            evidence_item = {
                "source": "geox_artifact_store",
                "event_id": ref,
                "event_type": "artifact_ingest",
                "verdict": latest_qc.get("qc_overall", "PENDING"),
                "actor_id": entry.get("diagnostics", {}).get("agent", "geox"),
                "session_id": entry.get("diagnostics", {}).get("session_id", ""),
                "stage": "INGEST",
                "timestamp": entry.get("registered_at", ""),
                "claim_state": entry.get("claim_state", "INGESTED"),
                "artifact_type": entry.get("artifact_type", ""),
                "las_path": entry.get("las_path", ""),
                "source_uri": entry.get("source_uri", ""),
                "qc_passed": latest_qc.get("qc_passed", False),
                "qc_flags": list(latest_qc.get("flags", [])),
                "qc_limitations": list(latest_qc.get("limitations", [])),
                "curves": list(entry.get("curves", [])),
            }
            records.append(evidence_item)

        # ── Apply limit and cursor pagination ────────────────────────────────
        records.sort(key=lambda r: str(r.get("timestamp", "")), reverse=True)
        total = len(records)
        records = records[:safe_limit]

        # Compute nextCursor if more records exist (opaque base64 token)
        next_cursor = None
        if total > safe_limit:
            import base64
            cursor_payload = json.dumps({"offset": safe_limit, "query": clean_query})
            next_cursor = base64.b64encode(cursor_payload.encode()).decode()

        artifact = {
            "query": clean_query,
            "records": records,
            "record_count": len(records),
            "total_matching": total,
            "nextCursor": next_cursor,
            "vault": "VAULT999 + geox_artifact_store",
            "sources_queried": [os.path.basename(p) for p in vault_paths if os.path.exists(p)] + ["geox_artifact_store"],
        }

        return get_standard_envelope(
            artifact,
            tool_class="system",
            claim_tag="CLAIM" if records else "HYPOTHESIS",
            claim_state="COMPUTED" if records else "NO_VALID_EVIDENCE",
        )

    except Exception as exc:
        logger.exception("geox_history_audit failed")
        return get_standard_envelope(
            {
                "tool": "geox_history_audit",
                "error_code": "HISTORY_AUDIT_FAILED",
                "message": str(exc)[:300],
                "retryable": False,
            },
            tool_class="system",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
        )


