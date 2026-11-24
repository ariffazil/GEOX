"""Source rock evaluation functions — TOC, kerogen, maturity, ΔlogR."""

from __future__ import annotations
import math
from typing import Any


def classify_toc(toc_wt_pct: float) -> dict[str, Any]:
    # TOC gives QUANTITY only (Peters & Cassa 1994). Hydrocarbon TYPE is a
    # Rock-Eval (HI) property or a declared kerogen type — never implied by TOC.
    if toc_wt_pct < 0.5:
        q = "poor"
    elif toc_wt_pct < 1.0:
        q = "fair"
    elif toc_wt_pct < 2.0:
        q = "good"
    elif toc_wt_pct < 4.0:
        q = "very_good"
    else:
        q = "excellent"
    return {
        "toc_wt_pct": toc_wt_pct,
        "quality": q,
        "generation_potential": "HOLD",
        "generation_potential_note": "TOC classifies source-rock QUANTITY only. Hydrocarbon TYPE requires Rock-Eval hydrogen_index or an explicitly supplied kerogen_type — supply either to obtain a type label.",
        "reference": "Peters-Cassa-1994",
    }


def classify_kerogen(hydrogen_index: float, oxygen_index: float | None = None, tmax_c: float | None = None) -> dict[str, Any]:
    if hydrogen_index > 600:
        kt, desc, prod = "I", "Algal/lacustrine — oil-prone", "oil"
    elif hydrogen_index > 300:
        kt, desc, prod = "II", "Marine — oil-prone", "oil"
    elif hydrogen_index > 200:
        kt, desc, prod = "II/III", "Mixed — oil/gas", "oil_gas"
    elif hydrogen_index > 50:
        kt, desc, prod = "III", "Terrestrial — gas-prone", "gas"
    else:
        kt, desc, prod = "IV", "Inert — no potential", "none"
    r = {
        "kerogen_type": kt,
        "hydrogen_index_mgHC_gTOC": hydrogen_index,
        "description": desc,
        "expected_products": prod,
        "reference": "van-Krevelen-Peters-1994",
    }
    if oxygen_index is not None:
        r["oxygen_index_mgCO2_gTOC"] = oxygen_index
    if tmax_c is not None:
        r["tmax_c"] = tmax_c
        r["maturity"] = classify_maturity(tmax_c, kt)
    return r


def classify_maturity(tmax_c: float, kerogen_type: str = "II") -> str:
    imm, oil, gas = (440, 450, 470) if kerogen_type == "I" else ((430, 450, 470) if kerogen_type == "III" else (435, 455, 470))
    if tmax_c < imm:
        return "immature"
    elif tmax_c < oil:
        return "early_mature"
    elif tmax_c < gas:
        return "oil_window"
    elif tmax_c < gas + 20:
        return "wet_gas_window"
    else:
        return "dry_gas_or_overmature"


def estimate_toc_deltalogr(
    depth_m: float,
    resistivity_ohm_m: float,
    sonic_us_ft: float | None = None,
    density_gcc: float | None = None,
    lom: float | None = None,
    baseline_resistivity: float | None = None,
    baseline_sonic: float | None = None,
) -> dict[str, Any]:
    """Passey et al. (1990) sonic/resistivity ΔlogR TOC estimate.

    ΔlogR = log10(R / R_baseline) + 0.02 · (Δt − Δt_baseline)
    TOC   = ΔlogR · 10^(2.297 − 0.1688 · LOM)

    Fails loud (ValueError) on inputs that would otherwise yield a believable
    wrong number. None = not supplied → default applied and listed in
    ``defaults_applied`` (confidence capped at LOW).
    """
    defaults_applied: list[str] = []
    if lom is None:
        lom = _LOM_DEFAULT
        defaults_applied.append("lom")
    if baseline_resistivity is None:
        baseline_resistivity = _BASELINE_RT_DEFAULT
        defaults_applied.append("baseline_resistivity")
    if baseline_sonic is None:
        baseline_sonic = _BASELINE_DT_DEFAULT
        defaults_applied.append("baseline_sonic")

    if resistivity_ohm_m is None or resistivity_ohm_m <= 0:
        raise ValueError(f"resistivity_ohm_m must be > 0 for ΔlogR (got {resistivity_ohm_m})")
    if baseline_resistivity <= 0 or baseline_sonic <= 0:
        raise ValueError(
            f"baseline_resistivity and baseline_sonic must be > 0 (got {baseline_resistivity}, {baseline_sonic})"
        )
    if sonic_us_ft is None:
        # The previous density→sonic conversion was not a published Passey form
        # (ρ=2.4 g/cc gave Δt≈1512 µs/ft). Refuse rather than invent a porosity track.
        raise ValueError(
            "ΔlogR needs sonic_us_ft (Passey 1990 sonic overlay); density-only input is not supported"
            + (f" (density_gcc={density_gcc} ignored)" if density_gcc is not None else "")
        )

    delta_log_r = math.log10(resistivity_ohm_m / baseline_resistivity) + 0.02 * (sonic_us_ft - baseline_sonic)
    toc = max(0.0, delta_log_r * (10 ** (2.297 - 0.1688 * lom)))
    conf = "LOW" if (lom < 2 or lom > 11 or defaults_applied) else "MEDIUM"
    q = classify_toc(toc)
    return {
        "toc_wt_pct": round(toc, 3),
        "delta_log_r": round(delta_log_r, 4),
        "lom": lom,
        "depth_m": depth_m,
        "method": "Passey-1990",
        "confidence": conf,
        "quality": q["quality"],
        "generation_potential": q["generation_potential"],
        "inputs_used": {
            "resistivity_ohm_m": resistivity_ohm_m,
            "sonic_us_ft": sonic_us_ft,
            "baseline_resistivity_ohm_m": baseline_resistivity,
            "baseline_sonic_us_ft": baseline_sonic,
            "lom": lom,
        },
        "defaults_applied": defaults_applied,
        "epistemic": "DER — ΔlogR. Baselines must be picked in a non-source fine-grained interval; "
        "calibrate with Rock-Eval for A-grade.",
    }


_LOM_DEFAULT = 7.0
_BASELINE_RT_DEFAULT = 2.0
_BASELINE_DT_DEFAULT = 90.0
