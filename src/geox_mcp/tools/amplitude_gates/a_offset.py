"""A-OFFSET — gradient validity inside mute / NMO-stretch-free range. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §2
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_offset(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-OFFSET",
        framework,
        invariant=(
            "gradient computed only inside [angle_min_deg, angle_max_deg] AND both bounds "
            "declared; otherwise UNMEASURED"
        ),
        evidence_refs=["TODO: cite NMO stretch / mute conventions"],
    )