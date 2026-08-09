"""
geox_source_rock — Source Rock Evaluation (Peters-Cassa / van Krevelen)
=======================================================================
Modes: toc, kerogen, maturity, delalogr, full

Wraps geox_core.source_rock.parameters:
  - classify_toc          (Peters-Cassa 1994)
  - classify_kerogen      (van Krevelen diagram)
  - classify_maturity     (Tmax-based maturity windows)
  - estimate_toc_deltalogr (Passey 1990 ΔlogR method)

DITEMPA BUKAN DIBERI — Source rock quality is measured, not assumed.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox.source_rock")


async def geox_source_rock(
    mode: str = "full",
    toc_wt_pct: float | None = None,
    hydrogen_index: float | None = None,
    oxygen_index: float | None = None,
    tmax_c: float | None = None,
    kerogen_type: str = "II",
    density_neutron_separation: float | None = None,
    baseline_resistivity: float | None = None,
    shale_resistivity: float | None = None,
    baseline_density: float | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Source rock evaluation: TOC classification (Peters-Cassa 1994), kerogen
    typing (van Krevelen), maturity windows, ΔlogR TOC estimation.

    Modes:
      toc      - Classify TOC quality (Peters-Cassa 1994): requires toc_wt_pct
      kerogen  - Type kerogen from HI/OI/Tmax (van Krevelen): requires hydrogen_index
      maturity - Classify thermal maturity from Tmax: requires tmax_c, kerogen_type
      delalogr - Estimate TOC from ΔlogR (Passey 1990): requires density_neutron_separation,
                 baseline_resistivity, shale_resistivity, baseline_density
      full     - Run all applicable sub-modes given supplied parameters
    """
    from geox_core.source_rock.parameters import (
        classify_kerogen,
        classify_maturity,
        classify_toc,
        estimate_toc_deltalogr,
    )

    result: dict[str, Any] = {
        "mode": mode,
        "session_id": session_id,
        "actor_id": actor_id,
        "trace_id": trace_id,
    }

    def _run_toc() -> dict[str, Any] | None:
        if toc_wt_pct is None:
            return None
        return classify_toc(toc_wt_pct)

    def _run_kerogen() -> dict[str, Any] | None:
        if hydrogen_index is None:
            return None
        return classify_kerogen(hydrogen_index, oxygen_index, tmax_c)

    def _run_maturity() -> str | None:
        if tmax_c is None:
            return None
        return classify_maturity(tmax_c, kerogen_type)

    def _run_delalogr() -> dict[str, Any] | None:
        # Map task-spec params → actual estimate_toc_deltalogr signature:
        # estimate_toc_deltalogr(depth_m, resistivity_ohm_m, sonic_us_ft, density_gcc, lom,
        #                        baseline_resistivity, baseline_sonic)
        # density_neutron_separation → used as proxy for density_gcc when provided
        # shale_resistivity          → mapped to resistivity_ohm_m
        if shale_resistivity is None:
            return None
        depth_m = 0.0  # depth not provided in delalogr mode — declare in epistemic
        resistivity_ohm_m = shale_resistivity
        density_gcc = density_neutron_separation  # separation proxy; caller should calibrate
        bl_res = baseline_resistivity if baseline_resistivity is not None else 2.0
        bl_den = baseline_density  # unused by core (baseline_sonic), retained for traceability
        out = estimate_toc_deltalogr(
            depth_m=depth_m,
            resistivity_ohm_m=resistivity_ohm_m,
            density_gcc=density_gcc,
            baseline_resistivity=bl_res,
        )
        if bl_den is not None:
            out["baseline_density_input"] = bl_den
        if density_neutron_separation is not None:
            out["density_neutron_separation_input"] = density_neutron_separation
        out["epistemic"] = (
            out.get("epistemic", "")
            + " depth_m=0 (not supplied); calibrate with actual depth for production use."
        )
        return out

    errors: list[str] = []

    if mode == "toc":
        r = _run_toc()
        if r is None:
            errors.append("mode=toc requires toc_wt_pct")
        else:
            result["toc"] = r

    elif mode == "kerogen":
        r = _run_kerogen()
        if r is None:
            errors.append("mode=kerogen requires hydrogen_index")
        else:
            result["kerogen"] = r

    elif mode == "maturity":
        r = _run_maturity()
        if r is None:
            errors.append("mode=maturity requires tmax_c")
        else:
            result["maturity"] = {"tmax_c": tmax_c, "kerogen_type": kerogen_type, "stage": r}

    elif mode == "delalogr":
        r = _run_delalogr()
        if r is None:
            errors.append("mode=delalogr requires shale_resistivity")
        else:
            result["delalogr"] = r

    elif mode == "full":
        r_toc = _run_toc()
        if r_toc is not None:
            result["toc"] = r_toc

        r_ker = _run_kerogen()
        if r_ker is not None:
            result["kerogen"] = r_ker

        r_mat = _run_maturity()
        if r_mat is not None:
            result["maturity"] = {"tmax_c": tmax_c, "kerogen_type": kerogen_type, "stage": r_mat}

        r_dlr = _run_delalogr()
        if r_dlr is not None:
            result["delalogr"] = r_dlr

        if not any(k in result for k in ("toc", "kerogen", "maturity", "delalogr")):
            errors.append(
                "mode=full: no inputs supplied. Provide toc_wt_pct, hydrogen_index, "
                "tmax_c, or shale_resistivity."
            )

    else:
        errors.append(f"Unknown mode: {mode!r}. Valid: toc, kerogen, maturity, delalogr, full")

    if errors:
        result["errors"] = errors

    result["governance"] = {
        "session_id": session_id,
        "actor_id": actor_id,
        "action_class": "OBSERVE",
        "mutation": False,
    }

    logger.debug("geox_source_rock mode=%s result_keys=%s", mode, list(result.keys()))
    return result
