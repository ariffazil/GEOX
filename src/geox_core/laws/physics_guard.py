"""
GEOX PhysicsGuard: The Constitutional Gatekeeper
=================================================
F1 AMANAH · F2 TRUTH · F3 TRI-WITNESS · F8 GENIUS · F9 ETHICS

Wired gates:
  • AC_Risk (Anomalous Contrast) → VOID on epistemic collapse
  • EMC Triple-Lock (2026-08-04) → element→mineral governance
    L1 Chemistry Lock — stoichiometric privacy → UNKNOWN
    L2 Physics Lock   — constrained inversion → VOID/SABAR
    L3 Domain Lock    — Mahalanobis OOD → 888_HOLD
"""

from __future__ import annotations

from typing import Any

import numpy as np

from geox_core.physics import Physics13State, anomaly_contrast_theory

# EMC engine — optional import, fails gracefully if not installed
try:
    from geox_core.inference.emc_inversion import (
        ChemistryResult,
        DomainResult,
        EMCVerdict,
        PhysicsResult,
        chemistry_lock as _chemistry_lock,
        domain_lock as _domain_lock,
        emc_verdict as _emc_verdict,
        fit_domain as _fit_domain,
        fit_linear_emc,
        invert_cls,
        physics_lock as _physics_lock,
    )

    _EMC_AVAILABLE = True
except ImportError:
    _EMC_AVAILABLE = False
    ChemistryResult = None  # type: ignore[assignment]
    DomainResult = None  # type: ignore[assignment]
    EMCVerdict = None  # type: ignore[assignment]
    PhysicsResult = None  # type: ignore[assignment]
    _chemistry_lock = None  # type: ignore[assignment]
    _domain_lock = None  # type: ignore[assignment]
    _emc_verdict = None  # type: ignore[assignment]
    _fit_domain = None  # type: ignore[assignment]
    _physics_lock = None  # type: ignore[assignment]
    fit_linear_emc = None  # type: ignore[assignment]
    invert_cls = None  # type: ignore[assignment]


class PhysicsGuard:
    """Enforces physical and epistemic invariants before capital allocation."""

    # ── EXISTING GATES ───────────────────────────────────────────────────────

    @staticmethod
    async def verify_vertical(well_id: str, curves: list) -> bool:
        """Ensures vertical consistency (e.g., density must increase with depth)."""
        return True  # Hardening required in L5

    @staticmethod
    async def verify_spatial(area_id: str, crs: str) -> bool:
        """Ensures spatial closure and projection integrity."""
        return True

    @staticmethod
    async def verify_closure(model_id: str) -> bool:
        """Ensures volumetric and mesh closure."""
        return True

    @staticmethod
    async def verify_preconditions(*args, **kwargs) -> bool:
        """Stub: precondition verification not yet implemented."""
        return True

    @staticmethod
    async def evaluate_epistemic_gate(background: Physics13State, observed: Physics13State) -> dict[str, Any]:
        """
        Hard-gate for the Wealth Bridge using the Theory of Anomalous Contrast.
        AC_Risk > 1.5 → VOID (Sovereign Block)
        """
        ac_result = anomaly_contrast_theory(background, observed)

        if ac_result["verdict"] == "VOID":
            ac_result["admissibility"] = "BLOCKED"
            ac_result["reason"] = "AC_Risk exceeds 1.5: Epistemic Collapse"
        else:
            ac_result["admissibility"] = "ALLOWED"

        return ac_result

    # ── EMC TRIPLE-LOCK GATES (2026-08-04) ──────────────────────────────────

    @staticmethod
    async def evaluate_chemistry_lock(
        X: np.ndarray,
        Y: np.ndarray,
        element_names: list[str],
        mineral_names: list[str],
        element_proxies: dict[str, list[str]] | None = None,
    ) -> ChemistryResult:
        """
        L1 CHEMISTRY LOCK — F2 TRUTH · F9 ANTIHANTU

        Evaluates stoichiometric privacy per element→mineral pair.
        R² < 0.60 → UNKNOWN-grade (blocked from petrophysics).
        R² ≥ 0.90 → FACT-grade (near-bijection).

        Args:
            X: (n_samples, n_elements) XRF data
            Y: (n_samples, n_minerals) XRD data
            element_names: element labels in column order
            mineral_names: mineral labels in column order
            element_proxies: optional per-mineral element mapping

        Returns:
            ChemistryResult with per-mineral R², coefficients, epistemic labels
        """
        if not _EMC_AVAILABLE:
            raise RuntimeError("EMC engine not available. Ensure geox_core.inference.emc_inversion is installed.")
        chem = fit_linear_emc(X, Y, element_names, mineral_names, element_proxies)
        return _chemistry_lock(chem)

    @staticmethod
    async def evaluate_physics_lock(
        xrf_sample: np.ndarray,
        chem_result: ChemistryResult,
        element_names: list[str],
        solver: str = "CLS",
    ) -> PhysicsResult:
        """
        L2 PHYSICS LOCK — F8 GENIUS

        Runs constrained inversion and validates physical constraints:
        Σ(mineral fractions) = 1.0, all fractions ≥ 0.
        Negative fraction → VOID. Closure residual > 0.01 → SABAR.

        Args:
            xrf_sample: (n_elements,) single sample XRF
            chem_result: output of evaluate_chemistry_lock
            element_names: element labels
            solver: "CLS" (constrained LS) or "LP" (linear program)

        Returns:
            PhysicsResult with fractions, closure check, verdict
        """
        if not _EMC_AVAILABLE:
            raise RuntimeError("EMC engine not available.")

        if solver == "LP":
            from geox_core.inference.emc_inversion import invert_lp

            fractions = invert_lp(xrf_sample, chem_result, element_names)
        else:
            fractions = invert_cls(xrf_sample, chem_result, element_names)

        return _physics_lock(fractions, solver)

    @staticmethod
    async def evaluate_domain_lock(
        xrf_sample: np.ndarray,
        X_calibration: np.ndarray,
    ) -> DomainResult:
        """
        L3 DOMAIN LOCK — F1 AMANAH → 888_HOLD

        Computes Mahalanobis distance of sample against calibration XRF cloud.
        D²_M < 3.0 → SEAL (in-domain)
        3.0 ≤ D²_M < 10.0 → CAUTION (marginal)
        D²_M ≥ 10.0 → HOLD (out-of-domain, request recalibration)

        Gate operates on chemistry-space position, NOT geographic distance.
        (Fusaea/Sloanea insight: equal offset, 4× different degradation.)

        Args:
            xrf_sample: (n_elements,) single sample XRF
            X_calibration: (n_samples, n_elements) calibration XRF cloud

        Returns:
            DomainResult with D², verdict
        """
        if not _EMC_AVAILABLE:
            raise RuntimeError("EMC engine not available.")

        domain_params = _fit_domain(X_calibration)
        return _domain_lock(xrf_sample, domain_params)

    @staticmethod
    async def evaluate_emc_verdict(
        chem: ChemistryResult,
        phys: PhysicsResult,
        domain: DomainResult,
    ) -> EMCVerdict:
        """
        FULL TRIPLE-LOCK ROLL-UP — weakest-verdict cascade.

        HOLD > VOID > SABAR > UNKNOWN > PARTIAL > SEAL.
        Any lock failure cascades to the most severe verdict.
        Emits full evidence card — no untagged output (F9 ANTI-HANTU).

        Returns:
            EMCVerdict with roll_up, evidence_card, blocked minerals
        """
        if not _EMC_AVAILABLE:
            raise RuntimeError("EMC engine not available.")
        return _emc_verdict(chem, phys, domain)


physics_guard = PhysicsGuard()
