"""Stub gate builder — A-* scaffold only.

Every A-* gate currently returns UNMEASURED with reason="gate not implemented".
Physics comes after spec ratification.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt


def stub_gate(
    gate_id: str,
    framework: dict[str, Any],
    *,
    invariant: str,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Return an UNMEASURED receipt for a gate whose physics is not yet wired.

    The invariant string documents what the gate WILL enforce once implemented.
    """
    _ = framework  # intentionally unused in stub
    return make_gate_receipt(
        gate_id,
        "UNMEASURED",
        reason="gate not implemented",
        equation=invariant,
        inputs={"framework_keys": sorted(list((framework or {}).keys()))},
        thresholds={},
        calculated_result={},
        exceptions_considered=[],
        evidence_refs=evidence_refs or [],
        gate_type="amplitude_physics",
    )