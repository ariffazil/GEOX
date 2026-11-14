"""A-CONFORM — flat spot / conformance is a depth-domain claim. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §3
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_conform(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-CONFORM",
        framework,
        invariant=(
            "flat spot / conformance to structure is a DEPTH-domain claim; TWT-only "
            "flatness without depth-converted test → KILL"
        ),
        evidence_refs=["TODO: cite depth conversion / flat-spot reference"],
    )