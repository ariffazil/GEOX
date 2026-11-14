"""A-PHASE — wavelet phase state. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §1
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_phase(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-PHASE",
        framework,
        invariant=(
            "wavelet extracted AND phase residual bounded AND phase_state == ZERO_PHASE; "
            "otherwise UNMEASURED"
        ),
        evidence_refs=["TODO: cite wavelet phase extraction reference"],
    )