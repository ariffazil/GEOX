"""A-POL — amplitude polarity convention. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §1
Convention registry: resources/ontology/amplitude_conventions.yaml
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_pol(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-POL",
        framework,
        invariant=(
            "polarity ∈ {SEG_NORMAL, SEG_REVERSE} AND reproducible from a well synthetic; "
            "otherwise UNMEASURED (never PASS)"
        ),
        evidence_refs=["TODO: cite SEG polarity convention spec"],
    )