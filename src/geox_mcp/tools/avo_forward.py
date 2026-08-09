"""
geox_avo_forward — AVO Forward Modeling (Zoeppritz / Shuey / LMR / Castagna)
=============================================================================
Modes: zoeppritz, shuey, lmr, castagna, full

Wraps geox_core.avo.avo_forward:
  - zoeppritz_rpp      (exact Bortfeld/Zoeppritz R_PP)
  - shuey_avo          (Shuey 2-term linearised AVO)
  - lmr_decompose      (Lambda-Mu-Rho, Goodway 1997)

Wraps geox_core.avo.castagna:
  - castagna_mudrock_vp_to_vs  (Vs prediction from Vp)
  - castagna_mudrock_fallback  (with explicit ACRisk and honest flags)

DITEMPA BUKAN DIBERI — impedance is the earth, sliced by angle.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox.avo_forward")


async def geox_avo_forward(
    mode: str = "zoeppritz",
    vp1: float | None = None,
    vs1: float | None = None,
    rho1: float | None = None,
    vp2: float | None = None,
    vs2: float | None = None,
    rho2: float | None = None,
    theta_deg: float | None = None,
    vp: float | None = None,
    vs: float | None = None,
    rho: float | None = None,
    fluid_zone: str = "brine",
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """AVO forward modeling: Zoeppritz exact Rpp, Shuey 2-term linearized,
    Lambda-Mu-Rho decomposition (Goodway 1997), Castagna mudrock line.

    Modes:
      zoeppritz - Exact R_PP(theta) via Bortfeld: requires vp1,vs1,rho1,vp2,vs2,rho2,theta_deg
      shuey     - Shuey 2-term AVO (R0, G, AVO class): requires vp1,vs1,rho1,vp2,vs2,rho2
      lmr       - Lambda-Mu-Rho decomposition: requires vp, vs (single float), rho
      castagna  - Castagna mudrock Vs prediction: requires vp; fluid_zone optional
      full      - Run all applicable modes given supplied parameters
    """
    import numpy as np

    from geox_core.avo.avo_forward import lmr_decompose, shuey_avo, zoeppritz_rpp
    from geox_core.avo.castagna import castagna_mudrock_fallback, castagna_mudrock_vp_to_vs

    result: dict[str, Any] = {
        "mode": mode,
        "session_id": session_id,
        "actor_id": actor_id,
        "trace_id": trace_id,
    }

    def _require_interface(needed: list[str]) -> list[str]:
        """Return list of missing parameter names."""
        mapping = {
            "vp1": vp1, "vs1": vs1, "rho1": rho1,
            "vp2": vp2, "vs2": vs2, "rho2": rho2,
            "theta_deg": theta_deg, "vp": vp,
        }
        return [n for n in needed if mapping.get(n) is None]

    errors: list[str] = []

    def _run_zoeppritz() -> dict[str, Any] | None:
        missing = _require_interface(["vp1", "vs1", "rho1", "vp2", "vs2", "rho2", "theta_deg"])
        if missing:
            errors.append(f"mode=zoeppritz missing: {missing}")
            return None
        theta_arr = np.asarray([theta_deg], dtype=float)
        rpp = zoeppritz_rpp(vp1, vs1, rho1, vp2, vs2, rho2, theta_arr)
        return {
            "R_PP": float(rpp[0]),
            "theta_deg": theta_deg,
            "above": {"vp": vp1, "vs": vs1, "rho": rho1},
            "below": {"vp": vp2, "vs": vs2, "rho": rho2},
            "method": "Bortfeld-Zoeppritz",
            "acrisk": 0.05 if theta_deg <= 30 else 0.10,
            "reference": "Bortfeld-1961",
        }

    def _run_shuey() -> dict[str, Any] | None:
        missing = _require_interface(["vp1", "vs1", "rho1", "vp2", "vs2", "rho2"])
        if missing:
            errors.append(f"mode=shuey missing: {missing}")
            return None
        theta_max = theta_deg if theta_deg is not None else 30.0
        avo = shuey_avo(vp1, vs1, rho1, vp2, vs2, rho2, theta_max=theta_max)
        return avo.to_dict()

    def _run_lmr() -> dict[str, Any] | None:
        # lmr_decompose accepts arrays; wrap scalar inputs.
        # Accept either standalone vp/vs/rho or layer-1 vp1/vs1/rho1.
        vs_input = vs if vs is not None else vs1
        vp_input = vp if vp is not None else vp1
        rho_input = rho if rho is not None else rho1
        missing = []
        if vp_input is None: missing.append("vp or vp1")
        if vs_input is None: missing.append("vs or vs1")
        if rho_input is None: missing.append("rho or rho1")
        if missing:
            errors.append(f"mode=lmr missing: {missing}")
            return None
        lmr = lmr_decompose(
            np.asarray([vp_input]),
            np.asarray([vs_input]),
            np.asarray([rho_input]),
        )
        return {
            "lambda_rho": float(lmr.lambda_rho[0]),
            "mu_rho": float(lmr.mu_rho[0]),
            "vp": float(lmr.vp[0]),
            "vs": float(lmr.vs[0]),
            "rho": float(lmr.rho[0]),
            "units": lmr.units,
            "acrisk": lmr.acrisk,
            "claim_state": lmr.claim_state,
            "provenance": lmr.provenance,
            "reference": "Goodway-Renzi-Best-1997",
        }

    def _run_castagna() -> dict[str, Any] | None:
        vp_input = vp if vp is not None else vp1
        if vp_input is None:
            errors.append("mode=castagna missing: vp (or vp1)")
            return None
        out = castagna_mudrock_fallback(vp_input, fluid_zone=fluid_zone)
        # vs may be ndarray scalar — coerce
        import numpy as _np
        vs_val = out.get("vs")
        if hasattr(vs_val, "item"):
            out["vs"] = float(vs_val.item())
        elif hasattr(vs_val, "__float__"):
            out["vs"] = float(vs_val)
        out["vp_input"] = vp_input
        out["reference"] = "Castagna-Batzle-Eastwood-1985"
        return out

    if mode == "zoeppritz":
        r = _run_zoeppritz()
        if r is not None:
            result["zoeppritz"] = r

    elif mode == "shuey":
        r = _run_shuey()
        if r is not None:
            result["shuey"] = r

    elif mode == "lmr":
        r = _run_lmr()
        if r is not None:
            result["lmr"] = r

    elif mode == "castagna":
        r = _run_castagna()
        if r is not None:
            result["castagna"] = r

    elif mode == "full":
        r_z = _run_zoeppritz()
        if r_z is not None:
            result["zoeppritz"] = r_z

        r_s = _run_shuey()
        if r_s is not None:
            result["shuey"] = r_s

        r_l = _run_lmr()
        if r_l is not None:
            result["lmr"] = r_l

        r_c = _run_castagna()
        if r_c is not None:
            result["castagna"] = r_c

        if not any(k in result for k in ("zoeppritz", "shuey", "lmr", "castagna")):
            errors.append(
                "mode=full: no sub-modes ran. Provide vp1/vs1/rho1/vp2/vs2/rho2/theta_deg "
                "for Zoeppritz/Shuey, vp/vs/rho for LMR, vp for Castagna."
            )

    else:
        errors.append(
            f"Unknown mode: {mode!r}. Valid: zoeppritz, shuey, lmr, castagna, full"
        )

    if errors:
        result["errors"] = errors

    result["governance"] = {
        "session_id": session_id,
        "actor_id": actor_id,
        "action_class": "OBSERVE",
        "mutation": False,
    }

    logger.debug("geox_avo_forward mode=%s result_keys=%s", mode, list(result.keys()))
    return result
