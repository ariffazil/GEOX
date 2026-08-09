"""
geox_diagenesis — Diagenesis & Mechanical Compaction
=====================================================
Modes: compaction, full

Wraps geox_core.diagenesis.compaction:
  - athy_porosity            (Athy 1930 exponential porosity-depth law)
  - sclater_christie_porosity (Sclater & Christie 1980 lithology-specific)
  - compaction_correction     (measured vs expected, flags NORMAL/UNDER/OVER)

DITEMPA BUKAN DIBERI — compaction is measured against model, not assumed.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox.diagenesis")


async def geox_diagenesis(
    mode: str = "compaction",
    depth_m: float | None = None,
    measured_porosity: float | None = None,
    lithology: str = "sandstone",
    surface_porosity: float = 0.45,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Diagenesis analysis: mechanical compaction models (Athy 1930,
    Sclater & Christie 1980), compaction correction, overpressure detection.

    Modes:
      compaction - Run Athy and Sclater-Christie porosity models plus
                   compaction correction (if measured_porosity is provided).
                   Requires: depth_m
      full       - Same as compaction (all sub-analyses given available inputs)
    """
    from geox_core.diagenesis.compaction import (
        athy_porosity,
        compaction_correction,
        sclater_christie_porosity,
    )

    result: dict[str, Any] = {
        "mode": mode,
        "session_id": session_id,
        "actor_id": actor_id,
        "trace_id": trace_id,
    }

    errors: list[str] = []

    def _run_compaction() -> dict[str, Any] | None:
        if depth_m is None:
            errors.append(f"mode={mode} requires depth_m")
            return None

        # Athy (1930) — uses surface_porosity and default compaction coefficient
        phi_athy = athy_porosity(depth_m, surface_porosity=surface_porosity)

        # Sclater & Christie (1980) — lithology-specific
        phi_sc = sclater_christie_porosity(lithology, depth_m)

        out: dict[str, Any] = {
            "depth_m": depth_m,
            "lithology": lithology,
            "athy_porosity": round(phi_athy, 4),
            "sclater_christie_porosity": round(phi_sc, 4),
            "surface_porosity_input": surface_porosity,
            "models": ["Athy-1930", "Sclater-Christie-1980"],
        }

        # Compaction correction (requires measured_porosity)
        if measured_porosity is not None:
            cc = compaction_correction(measured_porosity, depth_m, lithology)
            out["compaction_correction"] = cc
            # Overpressure heuristic: significant undercompaction may indicate overpressure
            residual = cc.get("residual", 0.0)
            if residual > 0.05:
                out["overpressure_flag"] = "POSSIBLE_OVERPRESSURE"
                out["overpressure_note"] = (
                    "Residual porosity > 0.05 above Sclater-Christie trend. "
                    "Consider pore-pressure analysis before drilling."
                )
            else:
                out["overpressure_flag"] = "NOT_INDICATED"
        else:
            out["compaction_correction"] = None
            out["note"] = "Provide measured_porosity for compaction_correction and overpressure flag."

        return out

    if mode in ("compaction", "full"):
        r = _run_compaction()
        if r is not None:
            result["compaction"] = r

    else:
        errors.append(f"Unknown mode: {mode!r}. Valid: compaction, full")

    if errors:
        result["errors"] = errors

    result["governance"] = {
        "session_id": session_id,
        "actor_id": actor_id,
        "action_class": "OBSERVE",
        "mutation": False,
    }

    logger.debug("geox_diagenesis mode=%s result_keys=%s", mode, list(result.keys()))
    return result
