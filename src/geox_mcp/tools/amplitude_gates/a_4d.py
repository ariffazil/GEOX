"""A-4D — time-lapse amplitude change exceeds NRMS repeatability floor. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §3
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_4d(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-4D",
        framework,
        invariant=(
            "Δamplitude(time-lapse) > NRMS repeatability floor for the survey / vintage; "
            "otherwise KILL"
        ),
        evidence_refs=["TODO: cite NRMS / 4D repeatability reference"],
    )