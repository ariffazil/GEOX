"""A-AVO — AVO intercept–gradient admissibility. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §2
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_avo(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-AVO",
        framework,
        invariant=(
            "intercept–gradient sits on basin-local background trend ± admissible_fluid_deviation; "
            "AVO class is DERIVED (never asserted); Vp/Vs measured/bounded; "
            "n_usable_stacks >= 3"
        ),
        evidence_refs=["TODO: cite Zoeppritz/Shuey; Rutherford–Williams 1989; Castagna–Smith 1994; Castagna 1998 (Class IV)"],
    )