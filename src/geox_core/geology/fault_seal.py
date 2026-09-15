"""SGR (Shale Gouge Ratio) pure computation kernel.

SGR = Σ(Vsh(i) × Δz(i)) / throw × 100%

This is a FAULT-ROCK PROXY, not a seal verdict.
No universal thresholds. Output states "NOT_A_SEAL_VERDICT".

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class StratigraphicZone:
    """One zone in the slipped interval."""
    zone_id: str
    thickness_m: float
    vsh: float  # Volume of shale (0.0-1.0)
    source_ref: Optional[str] = None


@dataclass
class SGResult:
    """SGR computation result — NOT a seal verdict."""
    sgr_fraction: float  # 0.0-1.0
    sgr_percent: float   # 0.0-100.0
    status: Literal["COMPUTED", "HOLD", "UNKNOWN"] = "COMPUTED"
    interpretation: str = "NOT_A_SEAL_VERDICT"
    formula_variant: str = "yielding_1997"
    throw_m: Optional[float] = None
    n_zones: int = 0
    total_vsh_thickness: float = 0.0
    limitations: list[str] = field(default_factory=list)
    uncertainty: Optional[dict] = None
    errors: list[str] = field(default_factory=list)


def compute_sgr(
    zones: list[dict],
    throw_m: float,
    formula_variant: str = "yielding_1997",
    uncertainty: Optional[dict] = None,
) -> dict:
    """Compute SGR from stratigraphic zones and fault throw.

    zones: list of {zone_id, thickness_m, vsh, source_ref?}
    throw_m: fault throw in meters (must be > 0)
    formula_variant: "yielding_1997" (default) or "continuous_vsh"
    uncertainty: optional {thickness_pct, vsh_pct, throw_pct}

    Returns SGResult as dict.
    NEVER returns a seal verdict. SGR is a fault-rock proxy only.
    """
    errors: list[str] = []
    limitations = [
        "No juxtaposition evaluated",
        "No pressure calibration",
        "No fault-rock capillary calibration",
        "Thresholds are basin/play-specific, not universal",
    ]

    if not zones:
        return SGResult(
            sgr_fraction=0.0, sgr_percent=0.0,
            status="UNKNOWN", errors=["No stratigraphic zones provided"],
            limitations=limitations,
        ).__dict__

    if throw_m is None or throw_m <= 0:
        return SGResult(
            sgr_fraction=0.0, sgr_percent=0.0,
            status="HOLD", errors=["Throw must be > 0 meters"],
            throw_m=throw_m, n_zones=len(zones),
            limitations=limitations,
        ).__dict__

    total_vsh_thickness = 0.0
    for z in zones:
        vsh = float(z.get("vsh", 0.0))
        thickness = float(z.get("thickness_m", 0.0))
        if vsh < 0.0 or vsh > 1.0:
            errors.append(f"Zone {z.get('zone_id', '?')}: Vsh={vsh} outside [0,1]")
        if thickness < 0:
            errors.append(f"Zone {z.get('zone_id', '?')}: negative thickness")
        total_vsh_thickness += vsh * thickness

    sgr_fraction = total_vsh_thickness / throw_m
    sgr_percent = sgr_fraction * 100.0

    # Uncertainty propagation if provided
    unc_result = None
    if uncertainty:
        try:
            t_pct = float(uncertainty.get("thickness_pct", 0.0))
            v_pct = float(uncertainty.get("vsh_pct", 0.0))
            th_pct = float(uncertainty.get("throw_pct", 0.0))
            # Relative uncertainty: sqrt(sum of squared relative uncertainties)
            rel_unc = math.sqrt(t_pct**2 + v_pct**2 + th_pct**2)
            unc_result = {
                "p10": max(0.0, sgr_fraction * (1 - 1.28 * rel_unc)),
                "p50": sgr_fraction,
                "p90": min(1.0, sgr_fraction * (1 + 1.28 * rel_unc)),
                "relative_uncertainty": rel_unc,
            }
        except (TypeError, ValueError):
            errors.append("Invalid uncertainty parameters")

    status: Literal["COMPUTED", "HOLD", "UNKNOWN"] = "HOLD" if errors else "COMPUTED"

    return SGResult(
        sgr_fraction=round(sgr_fraction, 6),
        sgr_percent=round(sgr_percent, 4),
        status=status,
        formula_variant=formula_variant,
        throw_m=throw_m,
        n_zones=len(zones),
        total_vsh_thickness=round(total_vsh_thickness, 4),
        limitations=limitations,
        uncertainty=unc_result,
        errors=errors,
    ).__dict__
