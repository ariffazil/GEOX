"""Gate calculation receipts — formula + inputs + hash.

Every physics gate must emit a receipt so audit trails are under test.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

GateStatus = Literal["PASS", "WARN", "KILL", "UNMEASURED", "NOT_APPLICABLE"]


def receipt_hash(payload: dict[str, Any]) -> str:
    """Stable sha256 over sorted JSON of receipt body (excludes receipt_hash itself)."""
    body = {k: v for k, v in payload.items() if k != "receipt_hash"}
    raw = json.dumps(body, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def make_gate_receipt(
    gate_id: str,
    status: GateStatus,
    *,
    inputs: dict[str, Any] | None = None,
    inputs_used: list[str] | None = None,
    measurement_units: str = "",
    equation: str = "",
    equation_or_rule: str = "",
    thresholds: dict[str, Any] | None = None,
    threshold_source: str = "",
    calculated_result: dict[str, Any] | None = None,
    exceptions_considered: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    reason: str = "",
    missing_inputs: list[str] | None = None,
    findings: list[dict[str, Any]] | None = None,
    gate_type: str = "physics",
) -> dict[str, Any]:
    """Canonical gate result with audit receipt.

    `verdict` mirrors `status` for backward compatibility (UNMEASURED kept as-is).
    """
    eq = equation_or_rule or equation
    receipt: dict[str, Any] = {
        "gate": gate_id,
        "gate_id": gate_id,
        "status": status,
        "verdict": status,  # alias — includes UNMEASURED
        "reason": reason,
        "inputs": inputs or {},
        "inputs_used": inputs_used or [],
        "measurement_units": measurement_units,
        "equation": eq,
        "equation_or_rule": eq,
        "thresholds": thresholds or {},
        "threshold_source": threshold_source,
        "calculated_result": calculated_result or {},
        "exceptions_considered": exceptions_considered or [],
        "evidence_refs": evidence_refs or [],
        "missing_inputs": missing_inputs or [],
        "findings": findings or [],
        "type": gate_type,
    }
    receipt["receipt_hash"] = receipt_hash(receipt)
    return receipt
