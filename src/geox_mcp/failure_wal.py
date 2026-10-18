"""failure_wal.py — GEOX Failure Write-Ahead Log (WAL)

Layer 2 (P0). Self-contained, organ-scoped JSONL ledger for GEOX governed
error envelopes. Mirrors the arifOS ``runtime/failure_wal.py`` contract
(append-only, sig_hash, date rotation, feature-flag) but is deliberately
importable WITHOUT ``arifosmcp`` — GEOX's runtime venv does not carry the
arifOS package, so a cross-organ import would silently no-op in production.

F2 TRUTH: every ``build_governed_error_envelope()`` call leaves exactly one
append-only JSONL line. No deletes. No overwrites.

DITEMPA BUKAN DIBERI ⚒️
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_WAL_DIR = Path(
    os.environ.get(
        "GEOX_FAILURE_WAL_DIR",
        "/root/.local/share/geox/state/failure-wal",
    )
)
_WAL_ENABLED = os.environ.get("GEOX_FAILURE_WAL", "1") != "0"
_MAX_LINE_BYTES = 100_000  # 100KB per line safety cap


def _sig_hash(tool: str | None, error_class: str, detail: str) -> str:
    """Deterministic signature: sha256(tool + error_class + detail)."""
    raw = "|".join([tool or "", error_class, (detail or "")[:500]])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def wal_append(
    *,
    tool: str | None,
    error_class: str,
    detail: str,
    session_id: str | None = None,
    trace_id: str | None = None,
    recovery: dict | None = None,
) -> dict[str, Any] | None:
    """Append one governed error envelope line. Never raises.

    Returns the WAL record dict (for inspection), or None if WAL is disabled
    or the append failed. WAL failure MUST NEVER block the error response.
    """
    if not _WAL_ENABLED:
        return None

    try:
        _WAL_DIR.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        record: dict[str, Any] = {
            "ts": now.isoformat(),
            "organ": "geox",
            "tool": tool,
            "error_class": error_class,
            "session_id": session_id,
            "trace_id": trace_id,
            "sig_hash": _sig_hash(tool, error_class, detail or ""),
            "detail": (detail or "")[:2000],
            "recovery": recovery,
        }

        # Date-rotated filename — matches arifOS failure_wal convention.
        wal_file = _WAL_DIR / f"failure-wal-{now.strftime('%Y-%m-%d')}.jsonl"
        line = json.dumps(record, default=str, ensure_ascii=False)
        if len(line.encode("utf-8")) > _MAX_LINE_BYTES:
            line = line[: _MAX_LINE_BYTES - 50] + "...[TRUNCATED]}"

        # Synchronous append — atomic at line level on POSIX.
        with open(wal_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

        return record

    except Exception:
        # WAL failure MUST NEVER block the error response.
        return None


def wal_query_today(
    *,
    sig_hash: str | None = None,
    error_class: str | None = None,
    tool: str | None = None,
) -> list[dict[str, Any]]:
    """Read today's WAL entries, optionally filtered."""
    now = datetime.now(timezone.utc)
    wal_file = _WAL_DIR / f"failure-wal-{now.strftime('%Y-%m-%d')}.jsonl"
    if not wal_file.exists():
        return []

    results: list[dict[str, Any]] = []
    try:
        with open(wal_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if sig_hash and rec.get("sig_hash") != sig_hash:
                    continue
                if error_class and rec.get("error_class") != error_class:
                    continue
                if tool and rec.get("tool") != tool:
                    continue
                results.append(rec)
    except Exception:
        pass

    return results
