"""
model_comparison.py — Bayesian Model Comparison for GEOX Falsification
======================================================================
Converts "INCONCLUSIVE" to a number: the Bayes factor between two models.

K = P(data | model_A) / P(data | model_B)

K > 3:   moderate evidence for A
K > 10:  strong evidence for A
K < 0.33: moderate evidence for B
K < 0.1:  strong evidence for B
0.33 < K < 3: INCONCLUSIVE (but now with a number)

GEOX-HARDEN-001 :: Fix 2.2
DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

from math import exp, log, sqrt, pi as π
from typing import Any


def bayes_factor_gaussian(
    observed: float,
    predicted_a: float,
    uncertainty_a: float,
    predicted_b: float,
    uncertainty_b: float,
) -> dict[str, Any]:
    """Compute Bayes factor between two Gaussian likelihoods.

    K_AB = P(obs|A) / P(obs|B)
    where P(obs|M) = Gaussian(obs; predicted_M, uncertainty_M)
    """

    def log_likelihood(obs: float, pred: float, sigma: float) -> float:
        if sigma <= 0:
            return float("-inf")
        z = (obs - pred) / sigma
        return -0.5 * (log(2 * π) + log(sigma**2) + z**2)

    ll_a = log_likelihood(observed, predicted_a, uncertainty_a)
    ll_b = log_likelihood(observed, predicted_b, uncertainty_b)

    log_k = ll_a - ll_b
    k = exp(log_k)

    abs_log_k = abs(log_k)
    if abs_log_k > 2.3:
        strength = "STRONG"
    elif abs_log_k > 1.1:
        strength = "MODERATE"
    elif abs_log_k > 0.5:
        strength = "WEAK"
    else:
        strength = "INCONCLUSIVE"

    return {
        "bayes_factor": round(k, 3),
        "log_bayes_factor": round(log_k, 3),
        "evidence_for": "A" if k > 1 else "B",
        "strength": strength,
        "likelihood_a": round(float(exp(ll_a)) if ll_a > float("-inf") else 0.0, 6),
        "likelihood_b": round(float(exp(ll_b)) if ll_b > float("-inf") else 0.0, 6),
    }
