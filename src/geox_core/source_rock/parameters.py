"""Source rock evaluation functions — TOC, kerogen, maturity, ΔlogR."""
from __future__ import annotations
import math
from typing import Any

def classify_toc(toc_wt_pct: float) -> dict[str, Any]:
    if toc_wt_pct < 0.5:    q, p = "poor", "negligible"
    elif toc_wt_pct < 1.0:  q, p = "fair", "limited_gas"
    elif toc_wt_pct < 2.0:  q, p = "good", "gas_oil"
    elif toc_wt_pct < 4.0:  q, p = "very_good", "oil_prone"
    else:                   q, p = "excellent", "major_oil"
    return {"toc_wt_pct": toc_wt_pct, "quality": q, "generation_potential": p, "reference": "Peters-Cassa-1994"}

def classify_kerogen(hydrogen_index: float, oxygen_index: float | None = None, tmax_c: float | None = None) -> dict[str, Any]:
    if hydrogen_index > 600:     kt, desc, prod = "I", "Algal/lacustrine — oil-prone", "oil"
    elif hydrogen_index > 300:   kt, desc, prod = "II", "Marine — oil-prone", "oil"
    elif hydrogen_index > 200:   kt, desc, prod = "II/III", "Mixed — oil/gas", "oil_gas"
    elif hydrogen_index > 50:    kt, desc, prod = "III", "Terrestrial — gas-prone", "gas"
    else:                        kt, desc, prod = "IV", "Inert — no potential", "none"
    r = {"kerogen_type": kt, "hydrogen_index_mgHC_gTOC": hydrogen_index, "description": desc, "expected_products": prod, "reference": "van-Krevelen-Peters-1994"}
    if oxygen_index is not None: r["oxygen_index_mgCO2_gTOC"] = oxygen_index
    if tmax_c is not None: r["tmax_c"] = tmax_c; r["maturity"] = classify_maturity(tmax_c, kt)
    return r

def classify_maturity(tmax_c: float, kerogen_type: str = "II") -> str:
    imm, oil, gas = (440, 450, 470) if kerogen_type == "I" else ((430, 450, 470) if kerogen_type == "III" else (435, 455, 470))
    if tmax_c < imm: return "immature"
    elif tmax_c < oil: return "early_mature"
    elif tmax_c < gas: return "oil_window"
    elif tmax_c < gas + 20: return "wet_gas_window"
    else: return "dry_gas_or_overmature"

def estimate_toc_deltalogr(depth_m: float, resistivity_ohm_m: float, sonic_us_ft: float | None = None, density_gcc: float | None = None, lom: float = 7.0, baseline_resistivity: float = 2.0, baseline_sonic: float = 90.0) -> dict[str, Any]:
    delta_log_r = math.log10(resistivity_ohm_m / baseline_resistivity) if resistivity_ohm_m > 0 and baseline_resistivity > 0 else 0.0
    if sonic_us_ft is not None and baseline_sonic > 0: delta_log_r += 0.02 * (sonic_us_ft - baseline_sonic)
    elif density_gcc is not None:
        vp_ms = 310 * (density_gcc * 1000) ** 0.25
        dt_us_ft = 1e6 / vp_ms * 3.28084
        delta_log_r += 0.02 * (dt_us_ft - baseline_sonic)
    toc = max(0.0, delta_log_r * (10 ** (2.297 - 0.1688 * lom)))
    conf = "LOW" if (lom < 2 or lom > 11 or (sonic_us_ft is None and density_gcc is None)) else "MEDIUM"
    q = classify_toc(toc)
    return {"toc_wt_pct": round(toc, 3), "delta_log_r": round(delta_log_r, 4), "lom": lom, "depth_m": depth_m, "method": "Passey-1990", "confidence": conf, "quality": q["quality"], "generation_potential": q["generation_potential"], "epistemic": "DER — ΔlogR. Calibrate with Rock-Eval for A-grade."}
