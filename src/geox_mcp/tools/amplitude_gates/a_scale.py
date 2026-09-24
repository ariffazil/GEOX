"""A-SCALE — amplitude scalar calibration. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §1
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_scale(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-SCALE",
        framework,
        invariant=(
            "amplitude_scalar_calibration == TRUE_AMPLITUDE AND true-amplitude chain + "
            "well tie present; otherwise UNMEASURED for absolute-amplitude claims"
        ),
        evidence_refs=["TODO: cite true-amplitude processing reference"],
    )