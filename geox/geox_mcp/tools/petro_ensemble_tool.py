"""
MCP wrapper for GEOX petrophysical saturation ensemble — v2.
Surfaces all v2 fields from PetroEnsembleResult.
"""

from __future__ import annotations

from geox.core.petro_ensemble import PetroEnsemble


def geox_compute_sw_ensemble_tool(
    rt: float,
    phi: float,
    rw: float,
    vsh: float,
    temp: float,
    a: float = 1.0,
    m: float = 2.0,
    n: float = 2.0,
    rsh: float | None = None,
    # v2 fields
    required_curves: list[str] | None = None,
    top_md: float | None = None,
    bottom_md: float | None = None,
    qc_state_ref: str = "",
) -> dict:
    """
    geox_well_compute_petrophysics — v2.

    New v2 output fields:
      saturation_model, required_curves_present/absent,
      applied_defaults, interval_coverage, confidence_limitations,
      prerequisite_qc_state, phi_eff_range, sw_range,
      claim_state, human_decision_point, vault_receipt
    """
    pe = PetroEnsemble()
    user_inputs = {"rt": rt, "phi": phi, "rw": rw, "vsh": vsh}
    result = pe.compute_sw_ensemble(
        rt=rt, phi=phi, rw=rw, vsh=vsh, temp=temp,
        a=a, m=m, n=n, rsh=rsh,
        required_curves=required_curves,
        top_md=top_md, bottom_md=bottom_md,
        qc_state_ref=qc_state_ref,
        user_inputs=user_inputs,
        user_defaults={} if rsh is not None else {"rsh": None},
    )
    return result.to_dict()
