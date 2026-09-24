"""A-ARTIFACT — stability across offsets, azimuths, vintages. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §3
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_artifact(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-ARTIFACT",
        framework,
        invariant=(
            "anomaly reproducible across offset / azimuth / vintage AND not a multiple, "
            "sideswipe, or migration swing"
        ),
        evidence_refs=["TODO: cite artifact / multiple reference"],
    )