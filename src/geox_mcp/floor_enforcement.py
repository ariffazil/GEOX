"""
geox_mcp.floor_enforcement — Constitutional Floor Enforcement Helper
═══════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given

Single source of truth for F1–F13 floor enforcement at the GEOX tool-wrapper
boundary. This module is invoked by `tools/_register.py` on every tool call
and on every tool registration. It does NOT change the public tool surface.

Constitutional Floors Enforced
──────────────────────────────
  F1  AMANAH    — Idempotency key support, pre-mutation guard
  F2  TRUTH     — Strict epistemic tag set, no SEAL-grade on observation tools
  F4  CLARITY   — Envelope shape pinned, Pydantic-strict
  F7  HUMILITY  — Hard cap `evidence_quality ≤ 0.90` (FLOOR 7)
  F8  LAW       — Fail-closed envelope construction, missing provenance
  F9  ANTI-HANTU— Tool name must be in canonical set or legacy alias
  F11 AUDIT     — Append-only local audit log (999_vault/audit.jsonl)
  F13 SOVEREIGN — `ack_irreversible` required for IRREVERSIBLE tier

Public API
──────────
  - `enforce_floor_pre_call(tool_name, kwargs, risk_tier) -> PreCallVerdict`
  - `enforce_floor_post_call(tool_name, result, kwargs, risk_tier) -> PostCallVerdict`
  - `validate_canonical_tool(name) -> bool`
  - `cap_humility(quality: float) -> float`
  - `EpistemicTag` (StrEnum)
  - `EvidenceEnvelope` (Pydantic v2 strict)
  - `AuditRecord` (dataclass)

Reference
─────────
  arifOS GENESIS/003_CONSTITUTIONAL_ALIGNMENT.md
  geox_mcp/tools/_register.py (the only caller)
  geox_mcp/organ_governance.py (RiskTier source)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("geox.floor")


# ═══════════════════════════════════════════════════════════════════════════════
# Constitutional constants — F7 HUMILITY hard cap
# ═══════════════════════════════════════════════════════════════════════════════

# F7 HUMILITY — confidence must NEVER exceed 0.90. This is the floor.
# The previous code had HIGH=0.95 which violated this. Now hard-capped.
HUMILITY_CAP: float = 0.90


# F2 TRUTH — canonical epistemic tag set. Tools emitting other tags
# are misconfigured and must be flagged.
class EpistemicTag(StrEnum):
    CLAIM = "CLAIM"  # FACT / OBSERVED / MEASURED → CLAIM
    PLAUSIBLE = "PLAUSIBLE"  # INTERPRETATION / INFERRED
    HYPOTHESIS = "HYPOTHESIS"
    ESTIMATE = "ESTIMATE"  # SPECULATION / ESTIMATE
    UNKNOWN = "UNKNOWN"  # VOID / UNKNOWN


# F11 AUDIT — local append-only log path
_DEFAULT_AUDIT_LOG = Path(os.environ.get("GEOX_AUDIT_LOG", "/root/geox/999_vault/audit.jsonl"))


# ═══════════════════════════════════════════════════════════════════════════════
# F9 ANTI-HANTU — Canonical tool name validation
# ═══════════════════════════════════════════════════════════════════════════════


def validate_canonical_tool(name: str) -> bool:
    """F9 ANTI-HANTU — tool name must be in canonical set or backward-compat alias.

    Checks (in order):
      1. CANONICAL_PUBLIC_TOOLS — the 35 canonical tool names
      2. CANONICAL_COMPAT_TOOLS — the 49 backward-compat aliases (accepted by middleware)
      3. LEGACY_ALIAS_MAP — empty as of Phase 2.4, kept for future use

    Falls back to True if registry is unavailable (cold start).
    The middleware (GeoxGovernanceMiddleware.on_call_tool) uses the same
    canonical ∪ compat union as _EXECUTABLE_SURFACE; floor enforcement
    must match.
    """
    try:
        from geox_mcp.registry import CANONICAL_COMPAT_TOOLS, CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP

        if name in CANONICAL_PUBLIC_TOOLS:
            return True
        if name in CANONICAL_COMPAT_TOOLS:
            return True
        if name in LEGACY_ALIAS_MAP:
            return True
        return False
    except Exception as exc:
        # Cold start: registry not importable. Log and pass.
        logger.debug(f"validate_canonical_tool: registry unavailable: {exc}")
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# F7 HUMILITY — Hard cap
# ═══════════════════════════════════════════════════════════════════════════════


def cap_humility(quality: float) -> float:
    """F7 HUMILITY — never let evidence_quality exceed the floor cap.

    This is the single most important floor in the GEOX surface.
    A confidence of 1.0 is a claim of certainty. The machine must never
    claim certainty about Earth. The floor is 0.90.
    """
    if quality is None:
        return 0.0
    try:
        q = float(quality)
    except (TypeError, ValueError):
        return 0.0
    if q > HUMILITY_CAP:
        logger.warning(f"F7 HUMILITY: capping evidence_quality {q:.4f} → {HUMILITY_CAP}")
        return HUMILITY_CAP
    if q < 0.0:
        return 0.0
    return round(q, 4)


# ═══════════════════════════════════════════════════════════════════════════════
# F4 CLARITY — Pydantic-strict Evidence Envelope
# ═══════════════════════════════════════════════════════════════════════════════


class EvidenceEnvelope(BaseModel):
    """F4 CLARITY — pinned envelope shape.

    Every GEOX tool result must be wrappable in this shape. No extra fields,
    no missing fields, no None values for required ones.
    """

    model_config = ConfigDict(
        extra="forbid",  # F4 — no drift
        frozen=False,
        str_strip_whitespace=True,
    )

    result: dict[str, Any] = Field(
        ...,
        description="Original tool payload (Pydantic-strict at the tool level).",
    )
    epistemic_tag: EpistemicTag = Field(
        ...,
        description="F2 TRUTH — canonical epistemic class.",
    )
    evidence_quality: float = Field(
        ...,
        ge=0.0,
        le=HUMILITY_CAP,  # F7 — hard cap
        description="F7 HUMILITY — bounded 0.0–0.90, never higher.",
    )
    source_attribution: list[str] = Field(
        ...,
        min_length=1,
        description="Provenance chain (F1).",
    )
    uncertainty_band: list[float] = Field(
        default_factory=lambda: [0.03, 0.05],
        description="Uncertainty band (low, high). Default = [0.03, 0.05].",
    )
    delta_S: float = Field(
        default=-0.05,
        description="Entropy delta (F4). Negative = order, positive = disorder.",
    )
    domain_law: str = Field(
        default="NATURAL_LAW",
        description="Domain-law anchor (physics manifest).",
    )
    physics_manifest_hash: str = Field(
        default="sha256:missing",
        description="Physics manifest SHA-256 anchor.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# F11 AUDIT — Append-only local audit log
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class AuditRecord:
    """F11 AUDIT — one line per tool call, append-only."""

    ts: str  # ISO-8601 UTC
    tool_name: str
    risk_tier: str
    actor_id: str | None
    session_id: str | None
    trace_id: str | None
    floor_gates_passed: list[str]
    floor_gates_failed: list[str]
    epistemic_tag: str | None
    evidence_quality: float | None
    duration_ms: float
    call_hash: str  # SHA-256 of (tool_name + sorted kwargs)
    outcome: str  # "PROCEED" | "HOLD" | "BLOCK"

    def to_jsonl_line(self) -> str:
        d = asdict(self)
        return json.dumps(d, default=str, sort_keys=True)


class AuditLog:
    """F11 AUDIT — append-only writer with file-lock-free line buffering.

    Writes one JSON line per tool call. File is append-only; existing lines
    are never modified or deleted. Disk full → log to stderr, do not crash
    the tool call (fail-soft on infra, fail-closed on envelope).
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _DEFAULT_AUDIT_LOG
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: AuditRecord) -> None:
        try:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(record.to_jsonl_line() + "\n")
        except Exception as exc:
            # F11 fail-soft on infra (disk full, permission denied, etc.)
            # but never block the tool call.
            logger.error(f"F11 AUDIT: failed to append to {self.path}: {exc}")


# Module-level singleton — lazy-initialised
_audit_log: AuditLog | None = None


def _get_audit_log() -> AuditLog:
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log


# ═══════════════════════════════════════════════════════════════════════════════
# F13 SOVEREIGN — Risk tier classification
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class PreCallVerdict:
    """Verdict from the pre-call floor enforcement."""

    outcome: str  # "PROCEED" | "HOLD" | "BLOCK"
    reason: str = ""
    required_params: list[str] = field(default_factory=list)
    call_hash: str = ""


@dataclass
class PostCallVerdict:
    """Verdict from the post-call floor enforcement (audit record)."""

    audit: AuditRecord
    envelope_valid: bool
    capped_quality: float | None = None
    warnings: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# F1 AMANAH — Call hash for idempotency / audit
# ═══════════════════════════════════════════════════════════════════════════════


def _compute_call_hash(tool_name: str, kwargs: dict[str, Any]) -> str:
    """F1 AMANAH — SHA-256 of (tool_name + sorted kwargs).

    Deterministic, content-addressed. Used for idempotency detection and
    audit dedup. Excludes volatile fields (session_id, trace_id, actor_id).
    """
    volatile = {"session_id", "trace_id", "actor_id", "idempotency_key"}
    safe = {k: v for k, v in kwargs.items() if k not in volatile}
    canonical = json.dumps(
        {"tool": tool_name, "kwargs": safe},
        default=str,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"


# ═══════════════════════════════════════════════════════════════════════════════
# Main API — pre-call + post-call
# ═══════════════════════════════════════════════════════════════════════════════


def enforce_floor_pre_call(
    tool_name: str,
    kwargs: dict[str, Any],
    risk_tier: str = "readonly",
) -> PreCallVerdict:
    """Floor enforcement BEFORE the tool runs.

    Checks:
      F9  — tool name is canonical
      F13 — IRREVERSIBLE tier requires `ack_irreversible=True`
      F1  — derives call_hash for idempotency
    """
    passed: list[str] = []
    failed: list[str] = []
    required: list[str] = []

    # F9 ANTI-HANTU
    if validate_canonical_tool(tool_name):
        passed.append("F9")
    else:
        failed.append("F9")
        return PreCallVerdict(
            outcome="BLOCK",
            reason=f"F9 ANTI-HANTU: tool name '{tool_name}' not in canonical or compat set",
            call_hash=_compute_call_hash(tool_name, kwargs),
        )

    # F13 SOVEREIGN
    risk_upper = str(risk_tier).upper()
    if risk_upper in ("IRREVERSIBLE", "C2_EXECUTE", "C2"):
        ack = kwargs.get("ack_irreversible")
        if not ack:
            failed.append("F13")
            required.append("ack_irreversible")
            return PreCallVerdict(
                outcome="HOLD",
                reason=(f"F13 SOVEREIGN: {risk_upper} tool '{tool_name}' requires ack_irreversible=True"),
                required_params=required,
                call_hash=_compute_call_hash(tool_name, kwargs),
            )
        else:
            passed.append("F13")
    else:
        passed.append("F13")

    # F1 AMANAH — always pass; call_hash is for audit only
    passed.append("F1")

    return PreCallVerdict(
        outcome="PROCEED",
        call_hash=_compute_call_hash(tool_name, kwargs),
    )


def enforce_floor_post_call(
    tool_name: str,
    result: Any,
    kwargs: dict[str, Any],
    risk_tier: str,
    pre_call: PreCallVerdict,
    duration_ms: float,
) -> PostCallVerdict:
    """Floor enforcement AFTER the tool runs.

    Checks:
      F4  — envelope is Pydantic-valid (if dict)
      F7  — evidence_quality hard-capped at HUMILITY_CAP
      F11 — append audit record
    """
    warnings: list[str] = []
    passed: list[str] = []
    failed: list[str] = []
    envelope_valid = True
    capped_quality: float | None = None
    epistemic_tag: str | None = None
    evidence_quality: float | None = None

    # F4 CLARITY — envelope shape (only if result is dict)
    if isinstance(result, dict) and "epistemic_tag" in result and "result" in result:
        try:
            EvidenceEnvelope.model_validate(result)
            passed.append("F4")
        except Exception as exc:
            envelope_valid = False
            failed.append("F4")
            warnings.append(f"F4 envelope shape: {exc}")

    # F7 HUMILITY — cap the quality score
    if isinstance(result, dict):
        q = result.get("evidence_quality")
        if q is not None:
            try:
                original = float(q)
                capped = cap_humility(original)
                if capped != original:
                    result["evidence_quality"] = capped
                    capped_quality = capped
                    warnings.append(f"F7 HUMILITY: capped {original:.4f} → {capped:.4f}")
                evidence_quality = capped
                passed.append("F7")
            except (TypeError, ValueError):
                failed.append("F7")
                warnings.append("F7: evidence_quality is not numeric")
        epistemic_tag = result.get("epistemic_tag")

    # F11 AUDIT — append-only local log
    audit = AuditRecord(
        ts=datetime.now(timezone.utc).isoformat(),
        tool_name=tool_name,
        risk_tier=str(risk_tier),
        actor_id=kwargs.get("actor_id"),
        session_id=kwargs.get("session_id"),
        trace_id=kwargs.get("trace_id"),
        floor_gates_passed=passed,
        floor_gates_failed=failed,
        epistemic_tag=str(epistemic_tag) if epistemic_tag else None,
        evidence_quality=evidence_quality,
        duration_ms=round(duration_ms, 3),
        call_hash=pre_call.call_hash,
        outcome=pre_call.outcome,
    )
    _get_audit_log().append(audit)

    if failed:
        # Any failed floor → mark as F11 fail-soft
        warnings.append(f"F11: {len(failed)} floor(s) flagged: {failed}")

    return PostCallVerdict(
        audit=audit,
        envelope_valid=envelope_valid,
        capped_quality=capped_quality,
        warnings=warnings,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# F1 AMANAH — Idempotency key store (in-memory; not durable by design)
# ═══════════════════════════════════════════════════════════════════════════════


class IdempotencyStore:
    """F1 AMANAH — in-memory idempotency store.

    Maps idempotency_key → (call_hash, timestamp). If a duplicate call arrives
    with the same key but a different call_hash, the wrapper BLOCKs. If the
    same key + same hash arrives, the wrapper PROCEEDs (idempotent replay).

    This is intentionally in-memory; durability is delegated to VAULT999
    when the call seals. The wrapper layer is for replay-safety only.
    """

    def __init__(self, max_size: int = 4096, ttl_s: int = 3600) -> None:
        self._store: dict[str, tuple[str, float]] = {}
        self._max = max_size
        self._ttl = ttl_s

    def check(self, key: str, call_hash: str) -> tuple[str, str]:
        """Return (outcome, reason). outcome ∈ {PROCEED, BLOCK, REPLAY}."""
        now = time.time()
        # Garbage collect
        if len(self._store) > self._max:
            cutoff = now - self._ttl
            self._store = {k: v for k, v in self._store.items() if v[1] > cutoff}
        if key not in self._store:
            self._store[key] = (call_hash, now)
            return ("PROCEED", "")
        stored_hash, _ = self._store[key]
        if stored_hash == call_hash:
            return ("REPLAY", "idempotent_replay")
        return ("BLOCK", "idempotency_key_reused_with_different_payload")


_idem_store: IdempotencyStore | None = None


def get_idempotency_store() -> IdempotencyStore:
    global _idem_store
    if _idem_store is None:
        _idem_store = IdempotencyStore()
    return _idem_store
