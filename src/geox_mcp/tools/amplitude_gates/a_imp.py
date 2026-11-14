"""A-IMP — impedance contrast admissibility. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §2
Bounds: docs/PHYSICS_9_SPEC.md (ρ, Vp, Vs)
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_imp(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-IMP",
        framework,
        invariant=(
            "R ≈ ΔI / 2I, I = Vp·ρ; required ΔI must be admissible under PHYSICS_9 "
            "rock-physics ranges for the lithology prior"
        ),
        evidence_refs=["docs/PHYSICS_9_SPEC.md"],
    )