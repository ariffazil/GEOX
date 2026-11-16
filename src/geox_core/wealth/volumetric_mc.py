"""
Probabilistic STOIIP / EMV — lognormal Monte Carlo (not flat EMV screening).

Bridge toward WEALTH organ. Not Petrel GRV grids — volume factors as distributions.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from geox_core.wealth.wealth_score_kernel import compute_emv


def _lognormal_mu_sigma(p10: float, p50: float, p90: float) -> tuple[float, float]:
    """Derive log-space (mu, sigma) from exploration P10 (high), P50, P90 (low)."""
    low, mid, high = float(p90), float(p50), float(p10)
    low, mid, high = max(low, 1e-12), max(mid, 1e-12), max(high, 1e-12)
    mu = float(np.log(mid))
    sigma = max((float(np.log(high)) - float(np.log(low))) / 2.56, 1e-6)
    return mu, sigma


def _lognormal_samples(p10: float, p50: float, p90: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Approximate lognormal from P10/P50/P90 (P10 high side for volumes).

    Exploration convention: P10 = high case, P90 = low case.
    """
    mu, sigma = _lognormal_mu_sigma(p10, p50, p90)
    return rng.lognormal(mean=mu, sigma=sigma, size=n)


def correlated_lognormal_pair(
    spec_a: tuple[float, float, float],
    spec_b: tuple[float, float, float],
    n: int,
    rho: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate two lognormal arrays joined by a Gaussian copula with correlation rho."""
    if not (-0.999 <= rho <= 0.999):
        raise ValueError(f"rho must be in [-0.999, 0.999] (got {rho})")
    mu_a, sig_a = _lognormal_mu_sigma(*spec_a)
    mu_b, sig_b = _lognormal_mu_sigma(*spec_b)
    z1 = rng.standard_normal(n)
    z2 = rho * z1 + math.sqrt(max(0.0, 1.0 - rho * rho)) * rng.standard_normal(n)
    return np.exp(mu_a + sig_a * z1), np.exp(mu_b + sig_b * z2)


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
    corr_ntg_phi: float = 0.0,
    return_samples: bool = False,
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
    if corr_ntg_phi != 0.0:
        ntg_raw, phi_raw = correlated_lognormal_pair(
            (ntg_p10, ntg_p50, ntg_p90),
            (phi_p10, phi_p50, phi_p90),
            n,
            corr_ntg_phi,
            rng,
        )
    else:
        ntg_raw = _lognormal_samples(ntg_p10, ntg_p50, ntg_p90, n, rng)
        phi_raw = _lognormal_samples(phi_p10, phi_p50, phi_p90, n, rng)
    ntg = np.clip(ntg_raw, 0.01, 1.0)
    phi = np.clip(phi_raw, 0.01, 0.4)
    so = np.clip(_lognormal_samples(so_p10, so_p50, so_p90, n, rng), 0.1, 0.9)
    bo = np.clip(_lognormal_samples(bo_p10, bo_p50, bo_p90, n, rng), 1.0, 2.5)

    stoiip_mmstb = (7758.0 * a_acres * h_ft * ntg * phi * so / bo) / 1e6

    # np percentile: 10th = low, 90th = high → map to P90/P10 (petroleum descending convention)
    p90 = float(np.percentile(stoiip_mmstb, 10))  # low case
    p50 = float(np.percentile(stoiip_mmstb, 50))
    p10 = float(np.percentile(stoiip_mmstb, 90))  # high case
    std_mmstb = float(np.std(stoiip_mmstb))
    se_mmstb = float(std_mmstb / np.sqrt(n))
    mc_receipt = {
        "seed": seed,
        "n_sims": n,
        "standard_error": round(se_mmstb, 6),
        "percentile_convention": "petroleum_descending",
        "rng_stream": "np.random.default_rng",
        "corr_ntg_phi": corr_ntg_phi,
    }

    out = {
        "formula": "STOIIP_bbl = 7758 × A_acres × h_ft × NTG × φ × So / Bo",
        "n_sims": n,
        "seed": seed,
        "corr_ntg_phi": corr_ntg_phi,
        "percentile_convention": "petroleum_descending",
        "stoiip_mmstb": {"p90": round(p90, 3), "p50": round(p50, 3), "p10": round(p10, 3)},
        "mean_mmstb": round(float(np.mean(stoiip_mmstb)), 3),
        "std_mmstb": round(std_mmstb, 3),
        "standard_error_mmstb": round(se_mmstb, 4),
        "mc_receipt": mc_receipt,
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
            "P10/P50/P90 here use petroleum_descending convention (P10=high, P90=low), not prospect POS",
        ],
    }
    if return_samples:
        out["_samples_mmstb"] = stoiip_mmstb.tolist()
    return out


def _resolve_low_mid_high(
    dist: dict[str, Any], convention: str | None
) -> tuple[float, float, float, str]:
    """Resolve (low, mid, high, convention) strictly from declared percentile_convention."""
    if convention is None:
        raise ValueError(
            "percentile_convention is required ('petroleum_descending' or 'statistical_ascending'); silent inference is forbidden"
        )
    p10, p50, p90 = float(dist["p10"]), float(dist["p50"]), float(dist["p90"])
    if convention == "statistical_ascending":
        if p10 > p90 or p10 > p50 or p50 > p90:
            raise ValueError(
                f"statistical_ascending requires p10 <= p50 <= p90 (got p10={p10}, p50={p50}, p90={p90})"
            )
        return p10, p50, p90, "statistical_ascending"
    if convention == "petroleum_descending":
        if p90 > p10 or p90 > p50 or p50 > p10:
            raise ValueError(
                f"petroleum_descending requires p90 <= p50 <= p10 (got p10={p10}, p50={p50}, p90={p90})"
            )
        return p90, p50, p10, "petroleum_descending"
    raise ValueError(f"Unknown percentile_convention={convention!r}")


def emv_from_stoiip_mc(
    stoiip: dict[str, Any],
    *,
    pos: float = 0.30,
    value_per_mmstb_usd_mm: float = 8.0,
    dry_hole_cost_usd_mm: float = 35.0,
    recovery_factor: float = 0.30,
    samples_mmstb: list[float] | np.ndarray | None = None,
) -> dict[str, Any]:
    """EMV from STOIIP MC — propagates full vector when samples exist, else 3-branch fallback."""
    s = stoiip["stoiip_mmstb"]
    vol_low, vol_mid, vol_high, resolved_conv = _resolve_low_mid_high(
        s, stoiip.get("percentile_convention")
    )
    raw_samples = samples_mmstb if samples_mmstb is not None else stoiip.get("_samples_mmstb")

    if raw_samples is not None and len(raw_samples) > 0:
        arr = np.asarray(raw_samples, dtype=float)
        rec_vec = arr * recovery_factor
        succ_payoffs = rec_vec * value_per_mmstb_usd_mm
        dry_payoff = -abs(dry_hole_cost_usd_mm)
        emv = float(pos * np.mean(succ_payoffs) + (1.0 - pos) * dry_payoff)
        second_moment = float(pos * np.mean(succ_payoffs**2) + (1.0 - pos) * (dry_payoff**2))
        emv_std = math.sqrt(max(0.0, second_moment - emv * emv))
        emv_se = emv_std / math.sqrt(len(arr))
        succ_p90, succ_p50, succ_p10 = (
            float(np.percentile(succ_payoffs, 10)),
            float(np.percentile(succ_payoffs, 50)),
            float(np.percentile(succ_payoffs, 90)),
        )
        emv_distribution: dict[str, Any] = {
            "method": "full_vector_mc",
            "n_samples": len(arr),
            "emv_mean_usd_mm": round(emv, 4),
            "emv_std_usd_mm": round(emv_std, 4),
            "emv_standard_error_usd_mm": round(emv_se, 6),
            "success_value_usd_mm": {
                "p90": round(succ_p90, 3),
                "p50": round(succ_p50, 3),
                "p10": round(succ_p10, 3),
            }
            if resolved_conv == "petroleum_descending"
            else {
                "p10": round(succ_p90, 3),
                "p50": round(succ_p50, 3),
                "p90": round(succ_p10, 3),
            },
            "dry_hole_usd_mm": round(dry_payoff, 3),
        }
        rec_low = float(np.percentile(rec_vec, 10))
        rec_mid = float(np.percentile(rec_vec, 50))
        rec_high = float(np.percentile(rec_vec, 90))
        scenarios = [
            {"name": "full_mc_success", "probability": pos, "outcome": round(float(np.mean(succ_payoffs)), 4)},
            {"name": "dry_hole", "probability": 1.0 - pos, "outcome": dry_payoff},
        ]
        emv_val = round(emv, 6)
    else:
        rec_low = vol_low * recovery_factor
        rec_mid = vol_mid * recovery_factor
        rec_high = vol_high * recovery_factor
        success_value = rec_mid * value_per_mmstb_usd_mm
        scenarios = [
            {"name": "success_low", "probability": pos * 0.3, "outcome": rec_low * value_per_mmstb_usd_mm},
            {"name": "success_mid", "probability": pos * 0.4, "outcome": success_value},
            {"name": "success_high", "probability": pos * 0.3, "outcome": rec_high * value_per_mmstb_usd_mm},
            {"name": "dry_hole", "probability": 1.0 - pos, "outcome": -abs(dry_hole_cost_usd_mm)},
        ]
        emv_val = compute_emv(scenarios)
        emv_distribution = {
            "method": "three_branch_summary_fallback",
            "emv_mean_usd_mm": emv_val,
        }

    rec_out = (
        {"p90": round(rec_low, 3), "p50": round(rec_mid, 3), "p10": round(rec_high, 3)}
        if resolved_conv == "petroleum_descending"
        else {"p10": round(rec_low, 3), "p50": round(rec_mid, 3), "p90": round(rec_high, 3)}
    )
    return {
        "pos": pos,
        "recovery_factor": recovery_factor,
        "percentile_convention": resolved_conv,
        "recoverable_mmstb": rec_out,
        "value_per_mmstb_usd_mm": value_per_mmstb_usd_mm,
        "dry_hole_cost_usd_mm": dry_hole_cost_usd_mm,
        "scenarios": scenarios,
        "emv_usd_mm": emv_val,
        "emv_distribution": emv_distribution,
        "mc_receipt": stoiip.get("mc_receipt"),
        "epistemic": "DER — POS still INT; volumes from MC",
        "note": "Not a full PSC cashflow model — use WEALTH organ for NPV under fiscal terms",
    }
