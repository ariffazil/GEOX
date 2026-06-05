"""
GEOX Spatial Block Validation — Surrogate block-CV for small-sample honesty.

Article reference: Burlamaque (2026-06-04) — "Small Data, Big Maps"
  Step 3: "Spatial block validation (NOT random K-fold)"

Folds the article's 5-step recipe into GEOX as a callable module
(no new top-level tool — surfaces via geox_evidence_reason(phase='spatial_block')).

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np

logger = logging.getLogger("geox.spatial_block")

TOOL_NAME = "geox_spatial_block_validate"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _assign_blocks(
    coords: list[tuple[float, float]],
    block_size_km: float,
) -> list[int]:
    """Assign each (lat, lon) to a spatial block id (grid cell)."""
    if not coords:
        return []
    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    # 1 deg latitude ~ 111 km. Block size in deg-lat = block_size_km / 111.
    deg_per_block = max(block_size_km / 111.0, 1e-6)
    blocks: list[int] = []
    seen: dict[tuple[int, int], int] = {}
    next_id = 0
    for lat, lon in coords:
        ix = int((lat - lat_min) / deg_per_block)
        iy = int((lon - lon_min) / deg_per_block)
        key = (ix, iy)
        if key not in seen:
            seen[key] = next_id
            next_id += 1
        blocks.append(seen[key])
    return blocks


def _assign_folds(block_ids: list[int], n_folds: int) -> list[int]:
    """Round-robin assign blocks to folds (preserves spatial contiguity)."""
    if n_folds < 2:
        raise ValueError("n_folds must be >= 2")
    out: list[int] = []
    block_to_fold: dict[int, int] = {}
    fold_counter = 0
    # Sort blocks by id (stable, deterministic)
    for bid in sorted(set(block_ids)):
        block_to_fold[bid] = fold_counter % n_folds
        fold_counter += 1
    for bid in block_ids:
        out.append(block_to_fold[bid])
    return out


def _safe_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    n_estimators: int = 50,
    max_depth: int = 5,
    random_state: int = 42,
) -> tuple[np.ndarray, Any]:
    """Train a small RandomForest; fall back to mean predictor on failure."""
    try:
        from sklearn.ensemble import RandomForestRegressor

        # Guard: sklearn needs >= 2 samples
        if len(X_train) < 2 or len(set(y_train)) < 2:
            mean_pred = float(np.mean(y_train)) if len(y_train) else 0.0
            preds = np.full(len(X_test), mean_pred, dtype=float)
            return preds, None
        rf = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=1,
        )
        rf.fit(X_train, y_train)
        return rf.predict(X_test), rf
    except Exception as e:
        logger.debug(f"RandomForest fallback engaged: {e}")
        mean_pred = float(np.mean(y_train)) if len(y_train) else 0.0
        return np.full(len(X_test), mean_pred, dtype=float), None


def _percentiles(values: list[float]) -> dict[str, float]:
    """P10 / P50 / P90 via numpy (deterministic, no scipy dep)."""
    if not values:
        return {"p10": 0.0, "p50": 0.0, "p90": 0.0}
    arr = np.array(values, dtype=float)
    return {
        "p10": float(np.percentile(arr, 10)),
        "p50": float(np.percentile(arr, 50)),
        "p90": float(np.percentile(arr, 90)),
    }


def run_spatial_block_validate(
    samples: list[dict[str, Any]],
    block_size_km: float = 5.0,
    n_folds: int = 5,
    target_key: str = "value",
    feature_keys: list[str] | None = None,
    random_seed: int = 42,
    max_samples: int = 5000,
) -> dict[str, Any]:
    """Run surrogate spatial block cross-validation.

    Article Step 3 implementation: spatially-close blocks stay together.
    Returns the honest generalization gap and per-fold diagnostics.

    Args:
        samples: list of dicts with at least: {"lat": float, "lon": float,
            "value": float, "feature_1": float, ...}. Coordinates in WGS84.
        block_size_km: spatial block size in kilometres. Default 5km.
        n_folds: number of folds. Default 5.
        target_key: which sample key is the regression target.
        feature_keys: which sample keys to use as features. If None,
            uses all numeric keys except 'lat'/'lon'/'value'.
        random_seed: deterministic seed for the surrogate model.
        max_samples: cap to keep RF training fast on large data.

    Returns:
        dict with per-fold metrics, spatial gap, and verdict.
    """
    if not samples:
        return {
            "verdict": "VOID",
            "error": "No samples supplied",
            "n_samples": 0,
            "n_samples_total": 0,
            "n_blocks": 0,
        }

    # Capture total before downsampling for receipt transparency
    n_samples_total = len(samples)

    # Downsample if needed (deterministic — first N)
    if len(samples) > max_samples:
        import random as _rnd

        _rnd.seed(random_seed)
        samples = _rnd.sample(samples, max_samples)

    # Extract coords
    coords: list[tuple[float, float]] = []
    valid: list[dict[str, Any]] = []
    for s in samples:
        try:
            lat = float(s.get("lat"))
            lon = float(s.get("lon"))
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        coords.append((lat, lon))
        valid.append(s)

    if len(valid) < 4:
        return {
            "verdict": "VOID",
            "error": f"Too few valid samples after coordinate filter: {len(valid)}",
            "n_samples": len(samples),
            "n_blocks": 0,
        }

    # Determine features
    if feature_keys is None:
        exclude = {"lat", "lon", "value", target_key}
        all_keys: set[str] = set()
        for s in valid:
            all_keys.update(s.keys())
        feature_keys = sorted(all_keys - exclude)
    feature_keys = [k for k in feature_keys if k not in ("lat", "lon", target_key)]

    # Build matrix
    try:
        X = np.array(
            [[float(s.get(k, 0.0) or 0.0) for k in feature_keys] for s in valid],
            dtype=float,
        )
        y = np.array([float(s[target_key]) for s in valid], dtype=float)
    except (KeyError, TypeError, ValueError) as e:
        return {
            "verdict": "VOID",
            "error": f"Failed to build feature matrix: {e}",
            "n_samples": len(valid),
            "n_blocks": 0,
        }

    # Spatial block + fold assignment
    block_ids = _assign_blocks(coords, block_size_km)
    fold_ids = _assign_folds(block_ids, n_folds)
    n_blocks = len(set(block_ids))

    # Cross-validate
    per_fold_rmse: list[float] = []
    per_fold_r2: list[float] = []
    per_fold_n_test: list[int] = []
    per_fold_n_train: list[int] = []
    per_fold_baseline_rmse: list[float] = []  # random-CV-like baseline (no blocks)

    # Random baseline (no spatial awareness)
    rng = np.random.default_rng(random_seed)
    random_idx = rng.permutation(len(y))
    random_folds = [int(i % n_folds) for i in range(len(y))]

    for fold in range(n_folds):
        # Spatial CV
        test_mask = np.array([f == fold for f in fold_ids], dtype=bool)
        train_mask = ~test_mask
        if test_mask.sum() == 0 or train_mask.sum() < 2:
            continue
        X_tr, y_tr = X[train_mask], y[train_mask]
        X_te, y_te = X[test_mask], y[test_mask]
        preds, _ = _safe_random_forest(X_tr, y_tr, X_te, random_state=random_seed + fold)
        rmse = float(np.sqrt(np.mean((preds - y_te) ** 2)))
        ss_res = float(np.sum((y_te - preds) ** 2))
        ss_tot = float(np.sum((y_te - np.mean(y_te)) ** 2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        per_fold_rmse.append(rmse)
        per_fold_r2.append(r2)
        per_fold_n_test.append(int(test_mask.sum()))
        per_fold_n_train.append(int(train_mask.sum()))

        # Random CV (baseline) for the same fold index
        test_mask_r = np.array([f == fold for f in random_folds], dtype=bool)
        train_mask_r = ~test_mask_r
        if test_mask_r.sum() == 0 or train_mask_r.sum() < 2:
            per_fold_baseline_rmse.append(rmse)
            continue
        X_tr_r, y_tr_r = X[train_mask_r], y[train_mask_r]
        X_te_r, y_te_r = X[test_mask_r], y[test_mask_r]
        preds_r, _ = _safe_random_forest(X_tr_r, y_tr_r, X_te_r, random_state=random_seed + fold)
        rmse_r = float(np.sqrt(np.mean((preds_r - y_te_r) ** 2)))
        per_fold_baseline_rmse.append(rmse_r)

    if not per_fold_rmse:
        return {
            "verdict": "VOID",
            "error": "All folds empty after spatial split",
            "n_samples": len(valid),
            "n_blocks": n_blocks,
        }

    # Compute gap
    spatial_p = _percentiles(per_fold_rmse)
    baseline_p = _percentiles(per_fold_baseline_rmse) if per_fold_baseline_rmse else spatial_p
    gap = spatial_p["p50"] - baseline_p["p50"] if baseline_p["p50"] else 0.0
    gap_ratio = (spatial_p["p50"] / baseline_p["p50"]) if baseline_p["p50"] > 0 else 1.0

    # Verdict: per F1-AMANAH, never SEAL if spatial_gap > 2x random gap
    if gap_ratio > 2.0:
        verdict = "VOID"
        reason = f"spatial_gap_p50 = {gap_ratio:.2f}x random — block-CV is the honest number"
    elif gap_ratio > 1.5:
        verdict = "HOLD"
        reason = f"spatial_gap_p50 = {gap_ratio:.2f}x random — material overfitting risk"
    elif gap_ratio > 1.2:
        verdict = "QUALIFY"
        reason = f"spatial_gap_p50 = {gap_ratio:.2f}x random — minor overfit"
    else:
        verdict = "SEAL"
        reason = f"spatial_gap_p50 = {gap_ratio:.2f}x random — generalizes well"

    return {
        "verdict": verdict,
        "verdict_reason": reason,
        "n_samples": len(valid),
        "n_samples_total": n_samples_total,
        "n_blocks": n_blocks,
        "n_folds": n_folds,
        "block_size_km": block_size_km,
        "feature_keys": feature_keys,
        "per_fold_rmse": per_fold_rmse,
        "per_fold_r2": per_fold_r2,
        "per_fold_n_test": per_fold_n_test,
        "per_fold_n_train": per_fold_n_train,
        "per_fold_baseline_rmse_random_cv": per_fold_baseline_rmse,
        "spatial_cv_rmse": spatial_p,
        "random_cv_rmse": baseline_p,
        "spatial_gap_p10_p50_p90": {
            "p10": spatial_p["p10"] - baseline_p["p10"],
            "p50": gap,
            "p90": spatial_p["p90"] - baseline_p["p90"],
        },
        "spatial_gap_ratio": round(gap_ratio, 3),
        "block_reliability": [
            {
                "block_id": bid,
                "n_samples": sum(1 for b in block_ids if b == bid),
                "fold": fold_ids[block_ids.index(bid)],
            }
            for bid in sorted(set(block_ids))[:20]  # cap to first 20 for envelope size
        ],
    }
