"""A-PROV — processing vintage provenance. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §1
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_prov(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-PROV",
        framework,
        invariant=(
            "amplitudes comparable only within one processing_vintage.vintage_id; "
            "cross-vintage claims require a cross-equalisation / mistie receipt"
        ),
        evidence_refs=["TODO: cite cross-equalisation reference"],
    )