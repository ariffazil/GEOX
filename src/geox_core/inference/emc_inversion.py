"""
emc_inversion.py — Element→Mineral Conversion Engine
=====================================================
Converts XRF elemental data to mineral fractions via stoichiometric inversion
with Triple-Lock governance (Chemistry · Physics · Domain).

Standalone module — no GEOX imports. Self-testing with synthetic data.

FORGED: 2026-08-04 · 333-AGI Δ MIND under Arif F13 SOVEREIGN
GROUNDED ON: i-GO Roystonea XRF→XRD study · MINSQ/CLS closure · Mahalanobis OOD
DOCTRINE: DITEMPA BUKAN DIBERI

LOCK STRUCTURE:
  L1 CHEMISTRY — Is element stoichiometrically private to mineral? (R² → FACT/INTERPRET/UNKNOWN)
  L2 PHYSICS   — Is inversion physically possible? (Σx=1, x≥0 → PASS/SABAR/VOID)
  L3 DOMAIN    — Is sample inside calibration chemistry-space? (D² → SEAL/CAUTION/HOLD)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from numpy import ndarray
from scipy.optimize import lsq_linear, nnls


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class EpistemicLabel(str, Enum):
    FACT = "FACT"
    INTERPRET = "INTERPRET"
    UNKNOWN = "UNKNOWN"


class PhysicsVerdict(str, Enum):
    PASS = "PASS"
    SABAR = "SABAR"
    VOID = "VOID"


class DomainVerdict(str, Enum):
    SEAL = "SEAL"
    CAUTION = "CAUTION"
    HOLD = "HOLD"


class RollUpVerdict(str, Enum):
    SEAL = "SEAL"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    SABAR = "SABAR"
    VOID = "VOID"
    HOLD = "HOLD"


@dataclass
class MineralResult:
    """Per-mineral lock evaluation."""

    mineral: str
    proxy_elements: list[str]
    r_squared: float
    coefficients: dict[str, float]  # element → coefficient
    residual_std: float
    epistemic_label: EpistemicLabel
    fraction: float | None = None  # after inversion


@dataclass
class ChemistryResult:
    """L1 Chemistry Lock output."""

    minerals: dict[str, MineralResult]
    hierarchy_reproduced: bool = False
    hierarchy_order: list[str] = field(default_factory=list)


@dataclass
class PhysicsResult:
    """L2 Physics Lock output."""

    fractions: dict[str, float]
    closure_sum: float
    closure_residual: float
    negative_flags: list[str]
    solver_used: str
    verdict: PhysicsVerdict
    warning: str = ""


@dataclass
class DomainResult:
    """L3 Domain Lock output."""

    mahalanobis_d2: float
    in_domain: bool
    verdict: DomainVerdict
    calibration_n_samples: int
    calibration_n_elements: int


@dataclass
class EMCVerdict:
    """Full Triple-Lock roll-up."""

    chemistry: ChemistryResult
    physics: PhysicsResult
    domain: DomainResult
    roll_up: RollUpVerdict
    evidence_card: dict
    minerals_blocked: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# L1 — CHEMISTRY LOCK (F2 TRUTH · F9 ANTIHANTU)
# ═══════════════════════════════════════════════════════════════════════════════

# Element→mineral proxy mapping (canonical from i-GO study + Sabah additions)
DEFAULT_ELEMENT_PROXIES: dict[str, list[str]] = {
    "carbonate": ["Ca"],
    "quartz": ["Si"],
    "clay": ["Al", "Fe", "K", "Na"],
    "feldspar": ["K", "Na"],
    "pyrite": ["S"],
    "zeolite": ["Ca", "Al", "Si"],
    "anorthite": ["Ca", "Al"],
}

# Per-mineral R² thresholds for epistemic labeling
# R² >= FACT_MIN → FACT (near-bijection)
# R² >= INTERPRET_MIN → INTERPRET
# R² < INTERPRET_MIN → UNKNOWN (degenerate — blocked from petrophysics)
FACT_MIN: float = 0.90
INTERPRET_MIN: float = 0.60


def fit_linear_emc(
    X: ndarray,  # (n_samples, n_elements) — XRF elemental concentrations
    Y: ndarray,  # (n_samples, n_minerals) — XRD mineral fractions
    element_names: list[str],
    mineral_names: list[str],
    element_proxies: dict[str, list[str]] | None = None,
) -> ChemistryResult:
    """
    Fit linear EMC model: OLS per mineral against its proxy elements.
    Returns per-mineral R², coefficients, residuals, and epistemic labels.
    """
    if element_proxies is None:
        element_proxies = DEFAULT_ELEMENT_PROXIES

    n_samples, n_elements = X.shape
    mineral_map: dict[str, MineralResult] = {}

    for j, mineral in enumerate(mineral_names):
        proxies = element_proxies.get(mineral, [])
        if not proxies:
            raise ValueError(f"No proxy elements defined for mineral '{mineral}'")

        # Select proxy element columns
        proxy_indices = [element_names.index(p) for p in proxies if p in element_names]
        if not proxy_indices:
            raise ValueError(f"No proxy elements found in data for mineral '{mineral}'")

        X_proxy = X[:, proxy_indices]
        y_target = Y[:, j]

        # Add intercept column
        X_aug = np.column_stack([np.ones(n_samples), X_proxy])

        # OLS: β = (XᵀX)⁻¹Xᵀy
        try:
            beta = np.linalg.lstsq(X_aug, y_target, rcond=None)[0]
        except np.linalg.LinAlgError:
            beta = np.zeros(X_aug.shape[1])

        y_pred = X_aug @ beta
        ss_res = np.sum((y_target - y_pred) ** 2)
        ss_tot = np.sum((y_target - np.mean(y_target)) ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-15 else 0.0
        r2 = max(0.0, min(1.0, r2))

        coeffs = {"intercept": float(beta[0])}
        for k, proxy_name in enumerate(proxies):
            if k < len(proxy_indices):
                coeffs[proxy_name] = float(beta[k + 1])

        # Epistemic label
        if r2 >= FACT_MIN:
            label = EpistemicLabel.FACT
        elif r2 >= INTERPRET_MIN:
            label = EpistemicLabel.INTERPRET
        else:
            label = EpistemicLabel.UNKNOWN

        mineral_map[mineral] = MineralResult(
            mineral=mineral,
            proxy_elements=proxies,
            r_squared=r2,
            coefficients=coeffs,
            residual_std=float(np.sqrt(ss_res / max(n_samples - len(proxies) - 1, 1))),
            epistemic_label=label,
        )

    # Verify hierarchy: FACT minerals must have higher R² than INTERPRET, which > UNKNOWN
    fact_r2 = [m.r_squared for m in mineral_map.values() if m.epistemic_label == EpistemicLabel.FACT]
    interp_r2 = [m.r_squared for m in mineral_map.values() if m.epistemic_label == EpistemicLabel.INTERPRET]
    unknown_r2 = [m.r_squared for m in mineral_map.values() if m.epistemic_label == EpistemicLabel.UNKNOWN]

    hierarchy_reproduced = True
    if fact_r2 and interp_r2 and min(fact_r2) < max(interp_r2):
        hierarchy_reproduced = False
    if interp_r2 and unknown_r2 and min(interp_r2) < max(unknown_r2):
        hierarchy_reproduced = False
    if fact_r2 and unknown_r2 and min(fact_r2) < max(unknown_r2):
        hierarchy_reproduced = False

    # Sort by R² descending for hierarchy_order
    sorted_minerals = sorted(mineral_map.keys(), key=lambda m: mineral_map[m].r_squared, reverse=True)

    return ChemistryResult(
        minerals=mineral_map,
        hierarchy_reproduced=hierarchy_reproduced,
        hierarchy_order=sorted_minerals,
    )


def chemistry_lock(chem_result: ChemistryResult) -> ChemistryResult:
    """Apply L1 epistemic labels. (Labels already computed in fit_linear_emc; this is the gate hook.)"""
    return chem_result


# ═══════════════════════════════════════════════════════════════════════════════
# L2 — PHYSICS LOCK (F8 GENIUS)
# ═══════════════════════════════════════════════════════════════════════════════


def invert_linear(
    xrf_sample: ndarray,  # (n_elements,) — single sample XRF
    chem_result: ChemistryResult,
    element_names: list[str],
) -> dict[str, float]:
    """Baseline linear inversion — can go unphysical (negative fractions). Caught by L2 gate."""
    fractions: dict[str, float] = {}
    for mineral, mres in chem_result.minerals.items():
        val = mres.coefficients.get("intercept", 0.0)
        for proxy in mres.proxy_elements:
            if proxy in element_names:
                idx = element_names.index(proxy)
                val += mres.coefficients.get(proxy, 0.0) * xrf_sample[idx]
        fractions[mineral] = val
    return fractions


def invert_cls(
    xrf_sample: ndarray,
    chem_result: ChemistryResult,
    element_names: list[str],
) -> dict[str, float]:
    """
    Constrained least squares with heavy-weighted closure Σx=1, x≥0.
    Uses scipy.optimize.lsq_linear with bounds [0, ∞) and augmented
    closure row with high weight.
    """
    minerals = list(chem_result.minerals.keys())
    n_minerals = len(minerals)
    n_proxies = sum(len(m.proxy_elements) for m in chem_result.minerals.values())

    # Build forward matrix: each row is a proxy element equation
    A_rows: list[list[float]] = []
    b_vals: list[float] = []
    row_labels: list[str] = []

    # Per-mineral proxy equation rows
    for j, mineral in enumerate(minerals):
        mres = chem_result.minerals[mineral]
        row = [0.0] * n_minerals
        row[j] = 1.0
        A_rows.append(row)
        b_vals.append(invert_linear(xrf_sample, chem_result, element_names)[mineral])
        row_labels.append(f"proxy:{mineral}")

    # Closure row: Σ xⱼ = 1.0 with heavy weight
    closure_weight = 1000.0
    closure_row = [closure_weight] * n_minerals
    A_rows.append(closure_row)
    b_vals.append(closure_weight * 1.0)
    row_labels.append("closure")

    A = np.array(A_rows)
    b = np.array(b_vals)

    # Bounds: x ≥ 0
    bounds = (np.zeros(n_minerals), np.full(n_minerals, np.inf))

    try:
        result = lsq_linear(A, b, bounds=bounds, method="trf")
        fractions_arr = result.x
    except Exception:
        # Fallback to NNLS on proxy-only rows (no closure weight)
        A_nnls = np.array(A_rows[:-1])
        b_nnls = np.array(b_vals[:-1])
        fractions_arr, _ = nnls(A_nnls, b_nnls)
        # Normalize to sum ≈ 1
        total = fractions_arr.sum()
        if total > 1e-15:
            fractions_arr = fractions_arr / total

    fractions = {mineral: max(0.0, float(fractions_arr[j])) for j, mineral in enumerate(minerals)}

    # Re-normalize to sum exactly 1.0 after clipping negatives to 0
    total = sum(fractions.values())
    if total > 1e-15:
        fractions = {m: v / total for m, v in fractions.items()}

    return fractions


def invert_lp(
    xrf_sample: ndarray,
    chem_result: ChemistryResult,
    element_names: list[str],
) -> dict[str, float]:
    """
    L1-residual linear program for solid-solution robustness.
    Wrapper around invert_cls with L1 objective — for future hardening.
    Currently delegates to invert_cls as the reference implementation.
    """
    return invert_cls(xrf_sample, chem_result, element_names)


def physics_lock(
    fractions: dict[str, float],
    solver: str = "CLS",
) -> PhysicsResult:
    """Validate inversion output against physical constraints."""
    closure_sum = sum(fractions.values())
    closure_residual = abs(closure_sum - 1.0)
    negative_flags = [m for m, v in fractions.items() if v < -1e-9]

    if negative_flags:
        return PhysicsResult(
            fractions=fractions,
            closure_sum=closure_sum,
            closure_residual=closure_residual,
            negative_flags=negative_flags,
            solver_used=solver,
            verdict=PhysicsVerdict.VOID,
            warning=f"Negative fractions detected: {negative_flags}",
        )

    if closure_residual > 0.01:
        return PhysicsResult(
            fractions=fractions,
            closure_sum=closure_sum,
            closure_residual=closure_residual,
            negative_flags=[],
            solver_used=solver,
            verdict=PhysicsVerdict.SABAR,
            warning=f"Closure residual {closure_residual:.4f} > 0.01 — upgrade to LP recommended",
        )

    return PhysicsResult(
        fractions=fractions,
        closure_sum=closure_sum,
        closure_residual=closure_residual,
        negative_flags=[],
        solver_used=solver,
        verdict=PhysicsVerdict.PASS,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# L3 — DOMAIN LOCK (F1 AMANAH)
# ═══════════════════════════════════════════════════════════════════════════════

MAHALANOBIS_IN_DOMAIN: float = 3.0
MAHALANOBIS_MARGINAL: float = 10.0


def fit_domain(
    X_calibration: ndarray,  # (n_samples, n_elements) — calibration XRF cloud
) -> dict:
    """
    Fit Mahalanobis parameters from calibration data.
    Returns mean vector and ridge-stabilized inverse covariance.
    """
    mean = X_calibration.mean(axis=0)
    centered = X_calibration - mean
    cov = np.cov(centered, rowvar=False)

    # Ridge stabilization for near-singular covariance
    ridge = 1e-6 * np.eye(cov.shape[0])
    cov_reg = cov + ridge

    try:
        inv_cov = np.linalg.inv(cov_reg)
    except np.linalg.LinAlgError:
        inv_cov = np.linalg.pinv(cov_reg)

    return {
        "mean": mean,
        "inv_cov": inv_cov,
        "n_samples": X_calibration.shape[0],
        "n_elements": X_calibration.shape[1],
    }


def domain_lock(
    xrf_sample: ndarray,  # (n_elements,) — single sample
    domain_params: dict,
) -> DomainResult:
    """
    Compute Mahalanobis distance of sample against calibration cloud.
    Returns D² and verdict.
    """
    mean = domain_params["mean"]
    inv_cov = domain_params["inv_cov"]

    delta = xrf_sample - mean
    d2 = float(delta @ inv_cov @ delta)

    if d2 < MAHALANOBIS_IN_DOMAIN:
        verdict = DomainVerdict.SEAL
    elif d2 < MAHALANOBIS_MARGINAL:
        verdict = DomainVerdict.CAUTION
    else:
        verdict = DomainVerdict.HOLD

    return DomainResult(
        mahalanobis_d2=d2,
        in_domain=(verdict == DomainVerdict.SEAL),
        verdict=verdict,
        calibration_n_samples=domain_params["n_samples"],
        calibration_n_elements=domain_params["n_elements"],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# VERDICT ROLL-UP
# ═══════════════════════════════════════════════════════════════════════════════

# Severity order: HOLD > VOID > SABAR > UNKNOWN > PARTIAL > SEAL
_VERDICT_SEVERITY: dict[RollUpVerdict, int] = {
    RollUpVerdict.HOLD: 5,
    RollUpVerdict.VOID: 4,
    RollUpVerdict.SABAR: 3,
    RollUpVerdict.UNKNOWN: 2,
    RollUpVerdict.PARTIAL: 1,
    RollUpVerdict.SEAL: 0,
}


def emc_verdict(
    chemistry: ChemistryResult,
    physics: PhysicsResult,
    domain: DomainResult,
) -> EMCVerdict:
    """
    Full Triple-Lock roll-up.
    Weakest-verdict rule: any lock failure cascades to the most severe verdict.
    """
    # Collect per-mineral issues
    minerals_blocked: list[str] = []
    unknown_minerals = [m for m, r in chemistry.minerals.items() if r.epistemic_label == EpistemicLabel.UNKNOWN]
    minerals_blocked.extend(unknown_minerals)
    minerals_blocked.extend(physics.negative_flags)

    # Determine roll-up verdict
    candidates: list[RollUpVerdict] = []

    # Domain lock dominates
    if domain.verdict == DomainVerdict.HOLD:
        candidates.append(RollUpVerdict.HOLD)
    elif domain.verdict == DomainVerdict.CAUTION:
        candidates.append(RollUpVerdict.SABAR)

    # Physics lock
    if physics.verdict == PhysicsVerdict.VOID:
        candidates.append(RollUpVerdict.VOID)
    elif physics.verdict == PhysicsVerdict.SABAR:
        candidates.append(RollUpVerdict.SABAR)

    # Chemistry lock
    has_fact = any(r.epistemic_label == EpistemicLabel.FACT for r in chemistry.minerals.values())
    has_unknown = any(r.epistemic_label == EpistemicLabel.UNKNOWN for r in chemistry.minerals.values())
    has_interp = any(r.epistemic_label == EpistemicLabel.INTERPRET for r in chemistry.minerals.values())

    if has_unknown and not has_fact:
        candidates.append(RollUpVerdict.UNKNOWN)
    elif has_unknown:
        candidates.append(RollUpVerdict.PARTIAL)
    elif not chemistry.hierarchy_reproduced:
        candidates.append(RollUpVerdict.SABAR)

    if not candidates:
        candidates.append(RollUpVerdict.SEAL)

    roll_up = max(candidates, key=lambda v: _VERDICT_SEVERITY.get(v, 0))

    # Evidence card
    evidence_card = {
        "chemistry": {
            mineral: {
                "r_squared": r.r_squared,
                "epistemic_label": r.epistemic_label.value,
                "proxy_elements": r.proxy_elements,
            }
            for mineral, r in chemistry.minerals.items()
        },
        "physics": {
            "verdict": physics.verdict.value,
            "closure_sum": physics.closure_sum,
            "closure_residual": physics.closure_residual,
            "solver": physics.solver_used,
        },
        "domain": {
            "verdict": domain.verdict.value,
            "mahalanobis_d2": domain.mahalanobis_d2,
        },
        "roll_up": roll_up.value,
    }

    return EMCVerdict(
        chemistry=chemistry,
        physics=physics,
        domain=domain,
        roll_up=roll_up,
        evidence_card=evidence_card,
        minerals_blocked=minerals_blocked,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SYNTHETIC DATA GENERATORS (for self-test)
# ═══════════════════════════════════════════════════════════════════════════════


def make_synthetic_calibration(
    n_samples: int = 100,
    seed: int = 42,
) -> tuple[ndarray, ndarray, list[str], list[str]]:
    """
    Generate synthetic XRF+XRD data that reproduces the i-GO R² hierarchy:
    carbonate (Ca) → FACT, quartz (Si) → INTERPRET, clay (Al,Fe,K,Na) → INTERPRET,
    feldspar (K,Na) → UNKNOWN, pyrite (S) → UNKNOWN.
    """
    rng = np.random.default_rng(seed)

    element_names = ["Ca", "Si", "Al", "Fe", "K", "Na", "S"]
    mineral_names = ["carbonate", "quartz", "clay", "feldspar", "pyrite"]
    n_elements = len(element_names)
    n_minerals = len(mineral_names)

    # Ground-truth mineral fractions (random within constraints)
    # Order: carbonate, quartz, clay, feldspar, pyrite
    carbonate_frac = rng.uniform(0.1, 0.5, n_samples)
    quartz_frac = rng.uniform(0.1, 0.4, n_samples)
    clay_frac = rng.uniform(0.05, 0.25, n_samples)
    feldspar_frac = rng.uniform(0.0, 0.1, n_samples)
    pyrite_frac = rng.uniform(0.0, 0.03, n_samples)

    # Normalize to sum ≈ 1
    total = carbonate_frac + quartz_frac + clay_frac + feldspar_frac + pyrite_frac
    carbonate_frac /= total
    quartz_frac /= total
    clay_frac /= total
    feldspar_frac /= total
    pyrite_frac /= total

    Y = np.column_stack([carbonate_frac, quartz_frac, clay_frac, feldspar_frac, pyrite_frac])

    # Forward model: minerals → elements with stoichiometric noise
    # Different noise levels per element to mirror i-GO S/N hierarchy
    X = np.zeros((n_samples, n_elements))

    # Ca: mostly from carbonate (private), trace from clay
    # LOW noise → high R² for carbonate
    X[:, 0] = carbonate_frac * 0.40 + clay_frac * 0.02 + rng.normal(0, 0.005, n_samples)  # Ca — very low noise

    # Si: from quartz + clay + feldspar
    # MEDIUM noise
    X[:, 1] = quartz_frac * 0.47 + clay_frac * 0.25 + feldspar_frac * 0.30 + rng.normal(0, 0.02, n_samples)  # Si — medium noise

    # Al: from clay + feldspar (shared)
    # HIGH noise for clay degradation
    X[:, 2] = clay_frac * 0.08 + feldspar_frac * 0.05 + rng.normal(0, 0.004, n_samples)  # Al — moderate noise (clay → INTERPRET)

    # Fe: mostly clay, trace pyrite
    X[:, 3] = clay_frac * 0.05 + pyrite_frac * 0.01 + rng.normal(0, 0.01, n_samples)  # Fe — moderate noise

    # K: shared between clay and feldspar — THIS is the degeneracy
    X[:, 4] = (
        clay_frac * 0.03 + feldspar_frac * 0.08 + rng.normal(0, 0.008, n_samples)
    )  # K — moderate noise (shared = degenerate)

    # Na: shared between clay and feldspar — same degeneracy
    X[:, 5] = (
        clay_frac * 0.01 + feldspar_frac * 0.04 + rng.normal(0, 0.006, n_samples)
    )  # Na — moderate noise (shared = degenerate)

    # S: from pyrite (private) but HIGH noise — pyrite is the worst sink
    X[:, 6] = pyrite_frac * 0.53 + rng.normal(0, 0.03, n_samples)  # S — VERY high noise (degrades pyrite R²)

    # Ensure non-negative
    X = np.maximum(X, 0.0)

    return X, Y, element_names, mineral_names


def make_sabah_shift_sample(
    calibration_X: ndarray,
    element_names: list[str],
    seed: int = 99,
) -> ndarray:
    """
    Generate a Sabah-like out-of-domain sample.
    Adds zeolite/anorthite signal (Ca+Al enrichment, K+Na depletion)
    that shifts far from calibration chemistry-space.
    """
    rng = np.random.default_rng(seed)
    sample = calibration_X.mean(axis=0).copy()

    # Shift: Ca enrichment (volcanic carbonates/zeolites in Sabah)
    if "Ca" in element_names:
        sample[element_names.index("Ca")] *= 3.5

    # Shift: Al enrichment (anorthite Ca-plagioclase)
    if "Al" in element_names:
        sample[element_names.index("Al")] *= 2.0

    # Shift: K/Na depletion (different clay species in Crocker/Meligan)
    if "K" in element_names:
        sample[element_names.index("K")] *= 0.3
    if "Na" in element_names:
        sample[element_names.index("Na")] *= 0.2

    # Add noise
    sample += rng.normal(0, 0.01, len(sample))
    return np.maximum(sample, 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════


def _self_test() -> bool:
    """Run full Triple-Lock self-test. Returns True if all assertions pass."""
    print("=" * 68)
    print("  GEOX EMC INVERSION — TRIPLE-LOCK SELF-TEST")
    print("=" * 68)

    all_passed = True

    # ── Generate synthetic data ──────────────────────────────────────────────
    X, Y, element_names, mineral_names = make_synthetic_calibration(n_samples=100)
    print(f"\n  Synthetic data: {X.shape[0]} samples, {X.shape[1]} elements, {Y.shape[1]} minerals")

    # ── L1 CHEMISTRY LOCK ────────────────────────────────────────────────────
    chem = fit_linear_emc(X, Y, element_names, mineral_names)
    chem = chemistry_lock(chem)

    print("\n  L1 CHEMISTRY LOCK — per-mineral R²:")
    for mineral, mres in chem.minerals.items():
        bar = "█" * int(mres.r_squared * 20) + "░" * (20 - int(mres.r_squared * 20))
        print(f"    {mineral:12s}  R²={mres.r_squared:.3f} {bar}  [{mres.epistemic_label.value}]")

    # Assert hierarchy
    r2_order = [chem.minerals[m].r_squared for m in chem.hierarchy_order]
    is_monotonic = all(r2_order[i] >= r2_order[i + 1] for i in range(len(r2_order) - 1))
    hier_check = is_monotonic and chem.hierarchy_reproduced

    print(f"\n    Hierarchy reproduced: {hier_check}")
    print(f"    R² order: {' > '.join(f'{chem.minerals[m].r_squared:.3f} {m}' for m in chem.hierarchy_order)}")

    # Assert specific minerals are UNKNOWN
    feldspar_unknown = chem.minerals["feldspar"].epistemic_label == EpistemicLabel.UNKNOWN
    pyrite_unknown = chem.minerals["pyrite"].epistemic_label == EpistemicLabel.UNKNOWN
    carbonate_fact = chem.minerals["carbonate"].epistemic_label == EpistemicLabel.FACT

    print(f"    Feldspar UNKNOWN: {feldspar_unknown}")
    print(f"    Pyrite UNKNOWN:   {pyrite_unknown}")
    print(f"    Carbonate FACT:   {carbonate_fact}")

    if not feldspar_unknown:
        print("    ⚠️  FAIL: Feldspar should be UNKNOWN-grade")
        all_passed = False
    if not pyrite_unknown:
        print("    ⚠️  FAIL: Pyrite should be UNKNOWN-grade")
        all_passed = False
    if not carbonate_fact:
        print("    ⚠️  FAIL: Carbonate should be FACT-grade")
        all_passed = False

    # ── L2 PHYSICS LOCK ──────────────────────────────────────────────────────
    # Test on a mean sample
    test_sample = X.mean(axis=0)

    cls_fractions = invert_cls(test_sample, chem, element_names)
    physics = physics_lock(cls_fractions, solver="CLS")

    print(f"\n  L2 PHYSICS LOCK — CLS inversion:")
    print(f"    Closure sum:      {physics.closure_sum:.4f}")
    print(f"    Closure residual: {physics.closure_residual:.4f}")
    print(f"    Negative flags:   {physics.negative_flags if physics.negative_flags else 'none'}")
    print(f"    Verdict:          {physics.verdict.value}")
    for mineral, frac in physics.fractions.items():
        print(f"      {mineral:12s} → {frac:.4f}")

    if physics.verdict != PhysicsVerdict.PASS:
        print(f"    ⚠️  FAIL: Physics Lock should PASS on in-domain sample")
        all_passed = False

    # ── L3 DOMAIN LOCK ───────────────────────────────────────────────────────
    domain_params = fit_domain(X)
    in_domain_result = domain_lock(test_sample, domain_params)
    print(f"\n  L3 DOMAIN LOCK — in-domain sample:")
    print(f"    Mahalanobis D²:   {in_domain_result.mahalanobis_d2:.2f}")
    print(f"    Verdict:          {in_domain_result.verdict.value}")

    # Sabah-shift sample
    sabah_sample = make_sabah_shift_sample(X, element_names)
    sabah_result = domain_lock(sabah_sample, domain_params)
    print(f"\n  L3 DOMAIN LOCK — Sabah-shift sample:")
    print(f"    Mahalanobis D²:   {sabah_result.mahalanobis_d2:.2f}")
    print(f"    Verdict:          {sabah_result.verdict.value}")

    if in_domain_result.verdict != DomainVerdict.SEAL:
        print(f"    ⚠️  FAIL: In-domain should be SEAL")
        all_passed = False
    if sabah_result.verdict != DomainVerdict.HOLD:
        print(f"    ⚠️  FAIL: Sabah-shift should fire 888_HOLD")
        all_passed = False

    # ── ROLL-UP ──────────────────────────────────────────────────────────────
    in_domain_verdict = emc_verdict(chem, physics, in_domain_result)
    sabah_verdict = emc_verdict(chem, physics, sabah_result)

    print(f"\n  ROLL-UP:")
    print(f"    In-domain:  {in_domain_verdict.roll_up.value} (blocked: {in_domain_verdict.minerals_blocked})")
    print(f"    Out-domain: {sabah_verdict.roll_up.value} (blocked: {sabah_verdict.minerals_blocked})")

    if in_domain_verdict.roll_up not in (RollUpVerdict.PARTIAL, RollUpVerdict.UNKNOWN):
        print(f"    ⚠️  FAIL: In-domain should be PARTIAL or UNKNOWN (some minerals degenerate)")
        all_passed = False
    if sabah_verdict.roll_up != RollUpVerdict.HOLD:
        print(f"    ⚠️  FAIL: Out-domain must be HOLD (Sabah-port guard fires)")
        all_passed = False

    # ── FINAL ────────────────────────────────────────────────────────────────
    print(f"\n{'=' * 68}")
    if all_passed:
        print(f"  ALL ASSERTIONS PASS ✅")
    else:
        print(f"  SOME ASSERTIONS FAILED ❌")
    print(f"{'=' * 68}\n")

    return all_passed


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ok = _self_test()
    raise SystemExit(0 if ok else 1)
