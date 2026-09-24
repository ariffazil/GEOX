"""A-SNR — anomaly exceeds background RMS, uncorrelated with acquisition footprint. STUB. NOT IMPLEMENTED.

Spec: docs/SEISMIC_AMPLITUDE_PHYSICS_GATES_A_SPEC.md §3
"""

from __future__ import annotations

from typing import Any

from geox_mcp.tools.amplitude_gates._stub import stub_gate


def gate_a_snr(framework: dict[str, Any]) -> dict[str, Any]:
    return stub_gate(
        "A-SNR",
        framework,
        invariant=(
            "anomaly magnitude > background RMS AND uncorrelated with acquisition footprint "
            "and azimuth geometry; otherwise KILL"
        ),
        evidence_refs=["TODO: cite SNR / acquisition footprint reference"],
    )