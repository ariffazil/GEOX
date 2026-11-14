"""A-PROP — propagation compensation. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §2
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_prop(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-PROP",
        framework,
        invariant=(
            "amplitudes compensated for geometric spreading, Q absorption, transmission "
            "loss through overburden; declared before any time/depth amplitude comparison"
        ),
        evidence_refs=["TODO: cite propagation / Q compensation reference"],
    )