"""Amplitude physics gates (A-*) — DRAFT, NOT WIRED.

Status: PASS | WARN | KILL | UNMEASURED | NOT_APPLICABLE | PARTIALLY_MEASURED | COMPUTABLE
        + receipt_hash.
This module mirrors `structure_gates/` but every body currently returns UNMEASURED with
reason="gate not implemented". The physics will be filled in after the spec is ratified.

Hypothesis aggregation (mirror of structure_gates):
  any KILL → REJECTED
  no KILL + at least one measured gate → SURVIVES_CURRENT_TESTS
  no measurable gates → UNTESTED
  conflicting measured gates → INCONCLUSIVE

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt

from geox_mcp.tools.amplitude_gates.a_pol import gate_a_pol
from geox_mcp.tools.amplitude_gates.a_phase import gate_a_phase
from geox_mcp.tools.amplitude_gates.a_scale import gate_a_scale
from geox_mcp.tools.amplitude_gates.a_prov import gate_a_prov
from geox_mcp.tools.amplitude_gates.a_imp import gate_a_imp
from geox_mcp.tools.amplitude_gates.a_avo import gate_a_avo
from geox_mcp.tools.amplitude_gates.a_offset import gate_a_offset
from geox_mcp.tools.amplitude_gates.a_tuning import gate_a_tuning
from geox_mcp.tools.amplitude_gates.a_prop import gate_a_prop
from geox_mcp.tools.amplitude_gates.a_snr import gate_a_snr
from geox_mcp.tools.amplitude_gates.a_artifact import gate_a_artifact
from geox_mcp.tools.amplitude_gates.a_conform import gate_a_conform
from geox_mcp.tools.amplitude_gates.a_4d import gate_a_4d

__all__ = [
    "gate_a_pol",
    "gate_a_phase",
    "gate_a_scale",
    "gate_a_prov",
    "gate_a_imp",
    "gate_a_avo",
    "gate_a_offset",
    "gate_a_tuning",
    "gate_a_prop",
    "gate_a_snr",
    "gate_a_artifact",
    "gate_a_conform",
    "gate_a_4d",
    "run_all_amplitude_gates",
    "aggregate_amplitude_hypothesis_status",
    "AMPLITUDE_HYPOTHESIS_STATUS_MAP",
]

AMPLITUDE_HYPOTHESIS_STATUS_MAP: dict[str, str] = {
    "KILL": "REJECTED",
    "PASS": "SURVIVES_CURRENT_TESTS",
    "PARTIAL": "SURVIVES_CURRENT_TESTS",
    "WARN": "SURVIVES_CURRENT_TESTS",
    "UNMEASURED": "UNTESTED",
    "INCONCLUSIVE": "INCONCLUSIVE",
    "PARTIALLY_MEASURED": "SURVIVES_CURRENT_TESTS",
    "COMPUTABLE": "UNTESTED",
    "NOT_APPLICABLE": "UNTESTED",
}


def aggregate_amplitude_hypothesis_status(
    gates: dict[str, Any],
    kills: list[str],
    passes: list[str],
    warns: list[str],
    unmeasured: list[str],
) -> str:
    """Mirror of structure_gates.aggregate_hypothesis_status."""
    if kills:
        return "REJECTED"
    measured = len(passes) + len(warns) + len(kills)
    if measured == 0:
        return "UNTESTED"
    return "SURVIVES_CURRENT_TESTS"


# Class groupings — used by the playbook (resources/playbooks/amplitude_dhi.yaml).
CLASS_I_GATES: tuple[str, ...] = ("A-POL", "A-PHASE", "A-SCALE", "A-PROV")
CLASS_II_GATES: tuple[str, ...] = ("A-IMP", "A-AVO", "A-OFFSET", "A-TUNING", "A-PROP")
CLASS_III_GATES: tuple[str, ...] = ("A-SNR", "A-ARTIFACT", "A-CONFORM", "A-4D")


def _stub_reason() -> str:
    return "gate not implemented"


def run_all_amplitude_gates(
    framework: dict[str, Any] | None = None,
    *,
    include_class_iii: bool = True,
) -> dict[str, Any]:
    """Run the full A-* matrix. Currently every gate returns UNMEASURED with a stub reason.

    Mirrors structure_gates.run_all_structure_gates contract surface where applicable
    so a future amplifier_validate mode can drop in.

    Hard stop semantics (per spec / playbook):
      any Class I UNMEASURED → the playbook halts before Class II
      any KILL → the playbook halts

    This function does NOT enforce the hard stop itself — it runs all gates and reports.
    The playbook / router is the place that enforces ordering. This separation matches
    structure_gates: the gates compute; the orchestrator decides.
    """
    framework = framework if isinstance(framework, dict) else {}

    gates_spec: list[tuple[str, Any]] = [
        # Class I — representation
        ("A-POL", gate_a_pol),
        ("A-PHASE", gate_a_phase),
        ("A-SCALE", gate_a_scale),
        ("A-PROV", gate_a_prov),
        # Class II — physics
        ("A-IMP", gate_a_imp),
        ("A-AVO", gate_a_avo),
        ("A-OFFSET", gate_a_offset),
        ("A-TUNING", gate_a_tuning),
        ("A-PROP", gate_a_prop),
    ]
    if include_class_iii:
        gates_spec.extend(
            [
                ("A-SNR", gate_a_snr),
                ("A-ARTIFACT", gate_a_artifact),
                ("A-CONFORM", gate_a_conform),
                ("A-4D", gate_a_4d),
            ]
        )

    results: dict[str, Any] = {}
    kills: list[str] = []
    passes: list[str] = []
    warns: list[str] = []
    unmeasured: list[str] = []
    not_applicable: list[str] = []
    partially_measured: list[str] = []
    computable: list[str] = []

    for name, fn in gates_spec:
        r = fn(framework)
        results[name] = r
        v = str(r.get("status") or r.get("verdict") or "UNMEASURED")
        if v == "KILL":
            kills.append(name)
        elif v == "PASS":
            passes.append(name)
        elif v == "WARN":
            warns.append(name)
        elif v == "NOT_APPLICABLE":
            not_applicable.append(name)
        elif v == "PARTIALLY_MEASURED":
            partially_measured.append(name)
        elif v == "COMPUTABLE":
            computable.append(name)
        else:
            unmeasured.append(name)

    if kills:
        combined = "KILL"
    elif passes or warns:
        combined = "PASS" if not unmeasured else "PARTIAL"
    elif partially_measured:
        combined = "PARTIALLY_MEASURED"
    elif computable:
        combined = "COMPUTABLE"
    else:
        combined = "UNMEASURED"

    hypothesis_status = aggregate_amplitude_hypothesis_status(results, kills, passes, warns, unmeasured)

    return {
        "gates": results,
        "combined_verdict": combined,
        "hypothesis_status": hypothesis_status,
        "kills": kills,
        "passes": passes,
        "warns": warns,
        "unmeasured": unmeasured,
        "not_applicable": not_applicable,
        "partially_measured": partially_measured,
        "computable": computable,
        "inconclusive": unmeasured,
        "class_i_gates": list(CLASS_I_GATES),
        "class_ii_gates": list(CLASS_II_GATES),
        "class_iii_gates": list(CLASS_III_GATES),
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "preferred_hypothesis": None,
        "note": (
            "A-* scaffold only — every gate body returns UNMEASURED with "
            "reason='gate not implemented'. UNMEASURED is not PASS. The "
            "playbook enforces Class I → II → III ordering; this function does "
            "not. preferred_hypothesis is always None — GEOX proposes, arifOS seals."
        ),
    }