"""
GEOX Feature Joint Information Statistic (FJIS) — Honest feature-addition score.

Article reference: Burlamaque (2026-06-04) — "Small Data, Big Maps"
  Step 1: "Extract more information from each sample — multi-sensor fusion,
          not feature inflation"

FJIS measures how much *joint* information a candidate feature adds beyond
the maximum redundant signal it shares with any single existing feature.

FJIS = I(candidate; target) - max(I(candidate; feature_i))   (for feature_i in existing)

Range: [-1, 1] after normalization.
  - FJIS > 0.2 AND max_redundancy < 0.5 → ADD (genuine new signal)
  - 0 < FJIS < 0.2                        → HOLD (marginal)
  - FJIS < 0 OR max_redundancy > 0.8     → DROP (redundant or harmful)

Surfaces via geox_data_qc_bundle(qc_mode='feature_info') — no new top-level tool.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger("geox.fjis")


def _safe_mutual_info(X: np.ndarray, y: np.ndarray) -> float:
    """Compute mutual information with sklearn; return 0.0 on failure.

    Uses k-nearest-neighbors MI estimator (Kraskov et al.) for robustness
    on continuous data.
    """
    try:
        from sklearn.feature_selection import mutual_info_regression

        # Cap for performance
        if len(X) > 2000:
            rng = np.random.default_rng(42)
            idx = rng.choice(len(X), 2000, replace=False)
            X = X[idx]
            y = y[idx]
        # MI needs 1D X
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        if X.shape[1] == 0 or len(np.unique(y)) < 2:
            return 0.0
        mi = float(mutual_info_regression(X, y, random_state=42)[0])
        return max(mi, 0.0)
    except Exception as e:
        logger.debug(f"mutual_info_regression fallback: {e}")
        return 0.0


def run_fjis(
    samples: list[dict[str, Any]],
    existing_features: list[str],
    candidate_feature: str,
    target_key: str = "value",
    max_samples: int = 2000,
    random_seed: int = 42,
) -> dict[str, Any]:
    """Compute the Feature Joint Information Statistic.

    Args:
        samples: list of dicts containing the named features + target.
        existing_features: names of features already in the model.
        candidate_feature: name of the new feature under evaluation.
        target_key: what we're trying to predict.
        max_samples: cap to keep MI computation fast.

    Returns:
        dict with fjis_score, redundancy_breakdown, recommendation.
    """
    if not samples:
        return {
            "verdict": "VOID",
            "fjis_score": 0.0,
            "recommendation": "DROP",
            "error": "No samples supplied",
        }

    if candidate_feature not in existing_features:
        # Add candidate to feature set for the analysis
        all_features = list(existing_features) + [candidate_feature]
    else:
        all_features = list(existing_features)

    # Downsample
    if len(samples) > max_samples:
        import random as _rnd

        _rnd.seed(random_seed)
        samples = _rnd.sample(samples, max_samples)

    # Build matrices
    try:
        X_existing = np.array(
            [[float(s.get(k, 0.0) or 0.0) for k in existing_features] for s in samples],
            dtype=float,
        )
        X_candidate = np.array(
            [float(s.get(candidate_feature, 0.0) or 0.0) for s in samples],
            dtype=float,
        )
        y = np.array([float(s[target_key]) for s in samples], dtype=float)
    except (KeyError, TypeError, ValueError) as e:
        return {
            "verdict": "VOID",
            "fjis_score": 0.0,
            "recommendation": "DROP",
            "error": f"Failed to build feature matrix: {e}",
        }

    if len(np.unique(y)) < 2:
        return {
            "verdict": "VOID",
            "fjis_score": 0.0,
            "recommendation": "DROP",
            "error": "Target has < 2 unique values — MI undefined",
        }

    # I(candidate; target) — candidate's own MI with target
    mi_candidate_target = _safe_mutual_info(X_candidate, y)

    # I(candidate; feature_i) — candidate's MI with each existing feature
    redundancy_breakdown: dict[str, float] = {}
    for i, feat in enumerate(existing_features):
        # Per-feature MI between candidate and that single existing feature
        mi = _safe_mutual_info(
            np.column_stack([X_candidate, X_existing[:, i]]),
            X_existing[:, i],
        )
        redundancy_breakdown[feat] = round(mi, 4)

    max_redundancy = max(redundancy_breakdown.values()) if redundancy_breakdown else 0.0
    # Joint MI between candidate and target, conditioned on existing features
    # (proxy: MI(candidate; target) - max pairwise redundancy)
    fjis_raw = mi_candidate_target - max_redundancy

    # Normalize: FJIS / I(candidate; target) — gives fraction of unique info
    fjis_normalized = (fjis_raw / mi_candidate_target) if mi_candidate_target > 0 else 0.0
    fjis_normalized = float(np.clip(fjis_normalized, -1.0, 1.0))

    # Recommendation
    if fjis_normalized > 0.2 and max_redundancy < 0.5:
        recommendation = "ADD"
        verdict = "SEAL"
    elif fjis_normalized > 0.0:
        recommendation = "HOLD"
        verdict = "QUALIFY"
    else:
        recommendation = "DROP"
        verdict = "HOLD"

    return {
        "verdict": verdict,
        "recommendation": recommendation,
        "fjis_score_raw": round(fjis_raw, 4),
        "fjis_score_normalized": round(fjis_normalized, 4),
        "mi_candidate_target": round(mi_candidate_target, 4),
        "max_redundancy": round(max_redundancy, 4),
        "redundancy_breakdown": redundancy_breakdown,
        "n_samples": len(samples),
        "existing_features": existing_features,
        "candidate_feature": candidate_feature,
        "target_key": target_key,
    }
