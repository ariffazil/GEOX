"""
Probabilistic STOIIP / EMV — lognormal Monte Carlo (not flat EMV screening).

Bridge toward WEALTH organ. Not Petrel GRV grids — volume factors as distributions.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from geox_core.wealth.wealth_score_kernel import compute_emv


def _lognormal_samples(p10: float, p50: float, p90: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Approximate lognormal from P10/P50/P90 (P10 high side for volumes).

    Exploration convention: P10 = high case, P90 = low case.
    """
    # map: low=P90, mid=P50, high=P10
    low, mid, high = float(p90), float(p50), float(p10)
    low, mid, high = max(low, 1e-12), max(mid, 1e-12), max(high, 1e-12)
    # log space
    mu = np.log(mid)
    # sigma from high/low span ~ 2.56σ for 80% central interval (P10-P90)
    sigma = max((np.log(high) - np.log(low)) / 2.56, 1e-6)
    return rng.lognormal(mean=mu, sigma=sigma, size=n)


def stoiip_monte_carlo(
    *,
    area_km2_p10: float,
    area_km2_p50: float,
    area_km2_p90: float,
    h_m_p10: float,
    h_m_p50: float,
    h_m_p90: float,
    ntg_p10: float,
    ntg_p50: float,
    ntg_p90: float,
    phi_p10: float,
    phi_p50: float,
    phi_p90: float,
    so_p10: float = 0.75,
    so_p50: float = 0.65,
    so_p90: float = 0.55,
    bo_p10: float = 1.15,
    bo_p50: float = 1.25,
    bo_p90: float = 1.40,
    n_sims: int = 5000,
    seed: int = 42,
) -> dict[str, Any]:
    """STOIIP (MMstb) Monte Carlo.

    Formula: STOIIP_bbl = 7758 * A_acres * h_ft * NTG * φ * So / Bo
    """
    rng = np.random.default_rng(seed)
    n = int(max(500, min(n_sims, 50000)))

    # area km2 → acres
    a_km2 = _lognormal_samples(area_km2_p10, area_km2_p50, area_km2_p90, n, rng)
    a_acres = a_km2 * 247.105
    h_m = _lognormal_samples(h_m_p10, h_m_p50, h_m_p90, n, rng)
    h_ft = h_m * 3.28084
    ntg = np.clip(_lognormal_samples(ntg_p10, ntg_p50, ntg_p90, n, rng), 0.01, 1.0)
    phi = np.clip(_lognormal_samples(phi_p10, phi_p50, phi_p90, n, rng), 0.01, 0.4)
    so = np.clip(_lognormal_samples(so_p10, so_p50, so_p90, n, rng), 0.1, 0.9)
    bo = np.clip(_lognormal_samples(bo_p10, bo_p50, bo_p90, n, rng), 1.0, 2.5)

    stoiip_mmstb = (7758.0 * a_acres * h_ft * ntg * phi * so / bo) / 1e6

    def pct(arr: np.ndarray, q: float) -> float:
        # volume convention: P10 high, P90 low
        return float(np.percentile(arr, 100 - q if q in (10, 90) else 50)) if q != 50 else float(np.percentile(arr, 50))

    # np percentile: 10th = low, 90th = high → map to P90/P10
    p90 = float(np.percentile(stoiip_mmstb, 10))  # low case
    p50 = float(np.percentile(stoiip_mmstb, 50))
    p10 = float(np.percentile(stoiip_mmstb, 90))  # high case

    return {
        "formula": "STOIIP_bbl = 7758 × A_acres × h_ft × NTG × φ × So / Bo",
        "n_sims": n,
        "seed": seed,
        "stoiip_mmstb": {"p90": round(p90, 3), "p50": round(p50, 3), "p10": round(p10, 3)},
        "mean_mmstb": round(float(np.mean(stoiip_mmstb)), 3),
        "std_mmstb": round(float(np.std(stoiip_mmstb)), 3),
        "inputs_distributions": {
            "area_km2": {"p10": area_km2_p10, "p50": area_km2_p50, "p90": area_km2_p90},
            "h_m": {"p10": h_m_p10, "p50": h_m_p50, "p90": h_m_p90},
            "ntg": {"p10": ntg_p10, "p50": ntg_p50, "p90": ntg_p90},
            "phi": {"p10": phi_p10, "p50": phi_p50, "p90": phi_p90},
            "so": {"p10": so_p10, "p50": so_p50, "p90": so_p90},
            "bo": {"p10": bo_p10, "p50": bo_p50, "p90": bo_p90},
        },
        "epistemic": "DER from lognormal MC — not a 3D grid GRV",
        "anti_hantu": [
            "STOIIP is not a map until GRV is grid-integrated",
            "P10/P50/P90 here are volume percentiles, not prospect POS",
        ],
    }


def emv_from_stoiip_mc(
    stoiip: dict[str, Any],
    *,
    pos: float = 0.30,
    value_per_mmstb_usd_mm: float = 8.0,
    dry_hole_cost_usd_mm: float = 35.0,
    recovery_factor: float = 0.30,
) -> dict[str, Any]:
    """EMV using recoverable P50 and binary success — still simple, but volumes are MC."""
    s = stoiip["stoiip_mmstb"]
    rec_p50 = s["p50"] * recovery_factor
    rec_p10 = s["p10"] * recovery_factor
    rec_p90 = s["p90"] * recovery_factor
    success_value = rec_p50 * value_per_mmstb_usd_mm
    # three-branch EMV using P90/P50/P10 success cases equally under success
    scenarios = [
        {"name": "success_p90_low", "probability": pos * 0.3, "outcome": rec_p90 * value_per_mmstb_usd_mm},
        {"name": "success_p50", "probability": pos * 0.4, "outcome": success_value},
        {"name": "success_p10_high", "probability": pos * 0.3, "outcome": rec_p10 * value_per_mmstb_usd_mm},
        {"name": "dry_hole", "probability": 1.0 - pos, "outcome": -abs(dry_hole_cost_usd_mm)},
    ]
    emv = compute_emv(scenarios)
    return {
        "pos": pos,
        "recovery_factor": recovery_factor,
        "recoverable_mmstb": {
            "p90": round(rec_p90, 3),
            "p50": round(rec_p50, 3),
            "p10": round(rec_p10, 3),
        },
        "value_per_mmstb_usd_mm": value_per_mmstb_usd_mm,
        "dry_hole_cost_usd_mm": dry_hole_cost_usd_mm,
        "scenarios": scenarios,
        "emv_usd_mm": emv,
        "epistemic": "DER — POS still INT; volumes from MC",
        "note": "Not a full PSC cashflow model — use WEALTH organ for NPV under fiscal terms",
    }
