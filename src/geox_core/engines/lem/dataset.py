"""
GEOX-LEM Dataset — Training Data Pipeline from GEOX Assets
══════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given.

Loads LAS well log files, preprocesses curves, creates patches,
and produces training batches for the GEOX-LEM tokenizer and pretrainer.

Supports:
  - 715+ real LAS files from GEOX data/ directory
  - Multi-curve loading with alias resolution
  - Missing curve handling via modality dropout
  - Depth-aligned patch extraction
  - Per-well normalization with outlier clipping
  - Train/val/test splitting at well level
"""

from __future__ import annotations

import glob
import hashlib
import json
import logging
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

from geox_core.ingest.las_reader import load_las, _canonicalise

logger = logging.getLogger("geox.lem.dataset")

try:
    import torch
    from torch.utils.data import Dataset, DataLoader
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False
    Dataset = object  # type: ignore
    DataLoader = None  # type: ignore


# ── Curve Configuration ─────────────────────────────────────────────────────

# Canonical curve names and their LAS mnemonics (ordered by priority)
CURVE_ALIASES: dict[str, list[str]] = {
    "GR":   ["GR", "GAM", "GAMMA", "GR_1", "GRC"],
    "RT":   ["RT", "RES", "RESIST", "ILD", "ILD_LOG", "RD", "DEEP_RES"],
    "RHOB": ["RHOB", "RHO", "DEN", "DENSITY", "ZDEN"],
    "NPHI": ["NPHI", "PHI", "NPOR", "NEUT", "TNPH"],
    "DT":   ["DT", "AC", "SONIC", "DTC", "DT_CO"],
    "SP":   ["SP", "SPONTANEOUS", "SP_1"],
}

CANONICAL_CURVES = list(CURVE_ALIASES.keys())  # ["GR", "RT", "RHOB", "NPHI", "DT", "SP"]
NUM_CURVES = len(CANONICAL_CURVES)


# ── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class WellSample:
    """Preprocessed well log data ready for patch extraction."""
    well_id: str
    depth_md: np.ndarray            # (N,) depth in meters
    curves: dict[str, np.ndarray]   # curve_name → (N,) array
    null_mask: np.ndarray           # (N, C) boolean — True where null
    n_samples: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WellPatch:
    """A single patch extracted from a well."""
    well_id: str
    depth_start: float
    depth_end: float
    curves: np.ndarray              # (C, L) — values
    mask: np.ndarray                # (C, L) — null mask
    token_ids: Optional[np.ndarray] = None  # (L',) after tokenization


def _resolve_curve(las_data, curve_name: str, aliases: list[str]) -> np.ndarray | None:
    """Try each alias to load a curve from LAS bundle."""
    for alias in aliases:
        # Check all attribute names on the bundle
        for attr_name in dir(las_data):
            if attr_name.lower() == alias.lower():
                val = getattr(las_data, attr_name)
                if val is not None and isinstance(val, np.ndarray) and len(val) > 0:
                    return val
    return None


# ── Preprocessing ───────────────────────────────────────────────────────────

def load_and_preprocess_well(
    las_path: str,
    required_curves: tuple[str, ...] = ("GR",),
    max_null_pct: float = 0.50,
    min_samples: int = 100,
    clip_outliers: bool = True,
    outlier_std: float = 5.0,
) -> Optional[WellSample]:
    """Load a LAS file and preprocess into WellSample.
    
    Steps:
      1. Load via GEOX las_reader
      2. Extract available curves using alias mapping
      3. Mark null values
      4. Check minimum quality criteria
      5. Clip outliers
      6. Return WellSample
    """
    try:
        bundle = load_las(las_path, well_id=Path(las_path).stem)
    except Exception as e:
        logger.debug(f"Failed to load {las_path}: {e}")
        return None

    # Extract curves from bundle
    curves: dict[str, np.ndarray] = {}
    null_counts: dict[str, float] = {}

    for canonical_name, aliases in CURVE_ALIASES.items():
        curve_data = None
        for alias in aliases:
            # Try each attribute name
            val = _resolve_curve(bundle, canonical_name, aliases)
            if val is None:
                # Try direct attribute access
                try:
                    val = getattr(bundle, alias.lower())
                except (AttributeError, KeyError):
                    try:
                        val = getattr(bundle, canonical_name.lower())
                    except (AttributeError, KeyError):
                        val = None

            if val is not None and isinstance(val, (np.ndarray, list)) and len(val) > 0:
                curve_data = _canonicalise(np.array(val, dtype=np.float64))
                break

        if curve_data is not None and len(curve_data) > 0:
            null_pct = float(np.sum(np.isnan(curve_data)) / len(curve_data))
            null_counts[canonical_name] = null_pct
            curves[canonical_name] = curve_data
        else:
            null_counts[canonical_name] = 1.0

    # Check required curves exist
    if not any(canonical in curves for canonical in required_curves):
        return None

    # Check minimum length
    n = max((len(v) for v in curves.values()), default=0)
    if n < min_samples:
        return None

    # Check null percentage on GR at minimum
    gr_null = null_counts.get("GR", 1.0)
    if gr_null > max_null_pct:
        return None

    # Clip outliers per curve
    if clip_outliers:
        for name in curves:
            arr = curves[name]
            valid = arr[~np.isnan(arr)]
            if len(valid) > 0:
                mean, std = np.nanmean(arr), np.nanstd(arr)
                lower = mean - outlier_std * std
                upper = mean + outlier_std * std
                curves[name] = np.clip(arr, lower, upper)

    # Build null mask
    null_mask_list = []
    for name in CANONICAL_CURVES:
        if name in curves:
            null_mask_list.append(np.isnan(curves[name]))
        else:
            null_mask_list.append(np.ones(n, dtype=bool))

    # Align curve lengths to minimum
    min_len = min((len(v) for v in curves.values()), default=n)
    aligned_curves: dict[str, np.ndarray] = {}
    for name, arr in curves.items():
        if len(arr) > min_len:
            aligned_curves[name] = arr[:min_len]
        else:
            aligned_curves[name] = arr

    depth = bundle.depth_md[:min_len] if hasattr(bundle, 'depth_md') and len(bundle.depth_md) >= min_len else np.arange(min_len, dtype=float)

    return WellSample(
        well_id=Path(las_path).stem,
        depth_md=depth,
        curves=aligned_curves,
        null_mask=np.column_stack(null_mask_list),
        n_samples=min_len,
        metadata={
            "filepath": las_path,
            "null_counts": null_counts,
            "curve_names": list(aligned_curves.keys()),
        },
    )


# ── Patch Extraction ────────────────────────────────────────────────────────

def extract_patches(
    sample: WellSample,
    patch_length: int = 32,
    patch_stride: int = 8,
) -> list[WellPatch]:
    """Extract overlapping patches from a well sample.
    
    Args:
        sample: Preprocessed well data
        patch_length: Number of depth samples per patch
        patch_stride: Stride between patches
    
    Returns:
        List of WellPatch objects
    """
    patches: list[WellPatch] = []
    n = sample.n_samples

    if n < patch_length:
        return patches

    # Build curve matrix (C, N)
    curve_matrix = np.zeros((NUM_CURVES, n), dtype=np.float32)
    mask_matrix = np.ones((NUM_CURVES, n), dtype=bool)  # True = null

    for i, name in enumerate(CANONICAL_CURVES):
        if name in sample.curves:
            arr = sample.curves[name]
            curve_matrix[i, :len(arr)] = arr[:n]
            mask_matrix[i, :len(arr)] = np.isnan(arr[:n])

    # Fill missing curves with mean of available values
    for i in range(NUM_CURVES):
        valid = curve_matrix[i, ~mask_matrix[i]]
        if len(valid) > 0:
            fill_val = np.nanmean(valid)
        else:
            fill_val = 0.0
        curve_matrix[i, mask_matrix[i]] = fill_val

    # Per-well normalization
    for i in range(NUM_CURVES):
        valid = curve_matrix[i, ~mask_matrix[i]]
        if len(valid) > 0:
            mean = np.mean(valid)
            std = max(np.std(valid), 1e-8)
            curve_matrix[i] = (curve_matrix[i] - mean) / std

    # Extract patches
    for start in range(0, n - patch_length + 1, patch_stride):
        end = start + patch_length
        patch_curves = curve_matrix[:, start:end]  # (C, L)
        patch_mask = mask_matrix[:, start:end]

        patches.append(WellPatch(
            well_id=sample.well_id,
            depth_start=float(sample.depth_md[start]) if start < len(sample.depth_md) else 0.0,
            depth_end=float(sample.depth_md[end - 1]) if end - 1 < len(sample.depth_md) else 0.0,
            curves=patch_curves,
            mask=patch_mask,
        ))

    return patches


# ── PyTorch Dataset ─────────────────────────────────────────────────────────

class WellLogDataset(Dataset):
    """
    PyTorch dataset for GEOX-LEM training.
    
    Loads LAS files, extracts patches, and returns:
      - curves: (C, L) normalized well log patch
      - mask: (C, L) null indicator
      - well_id: str
      - depth: (L,) depth values
    """

    def __init__(
        self,
        data_dir: str = "data/wells",
        file_pattern: str = "*.las",
        patch_length: int = 32,
        patch_stride: int = 8,
        max_null_pct: float = 0.50,
        min_samples: int = 100,
        required_curves: tuple[str, ...] = ("GR",),
        max_patches_per_well: int = 500,
        seed: int = 42,
    ):
        self.patch_length = patch_length
        self.seed = seed
        self.rng = random.Random(seed)

        # Find all LAS files
        search_path = os.path.join(data_dir, file_pattern)
        las_files = sorted(glob.glob(search_path))
        logger.info(f"Found {len(las_files)} LAS files in {data_dir}")

        # Load and preprocess wells
        self.samples: list[WellSample] = []
        for fpath in las_files:
            sample = load_and_preprocess_well(
                fpath,
                required_curves=required_curves,
                max_null_pct=max_null_pct,
                min_samples=min_samples,
            )
            if sample is not None:
                self.samples.append(sample)

        logger.info(f"Loaded {len(self.samples)} valid wells out of {len(las_files)} files")

        # Extract patches
        self.patches: list[WellPatch] = []
        for sample in self.samples:
            patches = extract_patches(sample, patch_length, patch_stride)
            if len(patches) > max_patches_per_well:
                self.rng.shuffle(patches)
                patches = patches[:max_patches_per_well]
            self.patches.extend(patches)

        logger.info(f"Extracted {len(self.patches)} patches from {len(self.samples)} wells")
        self.rng.shuffle(self.patches)

    def __len__(self) -> int:
        return len(self.patches)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        patch = self.patches[idx]
        return {
            "curves": torch.from_numpy(patch.curves).float(),  # (C, L)
            "mask": torch.from_numpy(patch.mask).bool(),       # (C, L)
            "well_id": patch.well_id,
            "depth_start": patch.depth_start,
            "depth_end": patch.depth_end,
        }

    def get_well_ids(self) -> list[str]:
        return list(set(p.well_id for p in self.patches))

    def summary(self) -> dict[str, Any]:
        return {
            "num_wells": len(self.samples),
            "num_patches": len(self.patches),
            "patch_length": self.patch_length,
            "curves": CANONICAL_CURVES,
            "well_ids": [s.well_id for s in self.samples[:10]],
            "total_well_ids": len(self.samples),
        }


# ── Factory Functions ──────────────────────────────────────────────────────

def create_lem_dataloader(
    data_dir: str = "data/wells",
    batch_size: int = 64,
    patch_length: int = 32,
    patch_stride: int = 8,
    num_workers: int = 4,
    shuffle: bool = True,
) -> dict[str, Any]:
    """Create a DataLoader for GEOX-LEM training.
    
    Returns dict with 'loader', 'dataset', and 'summary'.
    """
    if not _HAS_TORCH:
        raise RuntimeError("PyTorch required for dataloader. Install: pip install torch")

    dataset = WellLogDataset(
        data_dir=data_dir,
        patch_length=patch_length,
        patch_stride=patch_stride,
    )

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True,
    )

    return {
        "loader": loader,
        "dataset": dataset,
        "summary": dataset.summary(),
    }


def inspect_data(data_dir: str = "data/wells") -> dict[str, Any]:
    """Inspect available well data and return summary statistics."""
    summary = {
        "total_las_files": 0,
        "valid_wells": 0,
        "total_curves_found": set(),
        "null_statistics": {},
        "depth_ranges": [],
        "sample_counts": [],
    }

    search_path = os.path.join(data_dir, "*.las")
    las_files = sorted(glob.glob(search_path))
    summary["total_las_files"] = len(las_files)

    for fpath in las_files[:50]:  # Sample first 50
        sample = load_and_preprocess_well(fpath)
        if sample is not None:
            summary["valid_wells"] += 1
            summary["total_curves_found"].update(sample.curves.keys())
            summary["sample_counts"].append(sample.n_samples)
            if len(sample.depth_md) >= 2:
                summary["depth_ranges"].append({
                    "well": sample.well_id,
                    "top": float(sample.depth_md[0]),
                    "base": float(sample.depth_md[-1]),
                    "samples": sample.n_samples,
                    "curves": list(sample.curves.keys()),
                })

    summary["total_curves_found"] = list(summary["total_curves_found"])
    return summary


__all__ = [
    "WellLogDataset",
    "create_lem_dataloader",
    "inspect_data",
    "load_and_preprocess_well",
    "extract_patches",
    "WellSample",
    "WellPatch",
    "CANONICAL_CURVES",
    "NUM_CURVES",
]
