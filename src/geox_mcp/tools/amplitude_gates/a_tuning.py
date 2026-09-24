"""A-TUNING — amplitude ≠ thickness, below λ/4 thickness-modulated. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §2
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_tuning(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-TUNING",
        framework,
        invariant=(
            "tuning thickness declared AND above/below-tuning state declared before any "
            "amplitude-to-property inversion"
        ),
        evidence_refs=["TODO: cite Widess 1973 / tuning thickness reference"],
    )