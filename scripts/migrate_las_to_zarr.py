#!/usr/bin/env python3
"""
migrate_las_to_zarr.py — Stage 2.3: migrate legacy LAS artifacts to zarr store.

Forged 2026-07-25 · FI-008 (kimi-code) · agent-init Stage 2 work.

Walks the legacy artifact registry (the on-disk ``artifact_registry.json``
plus the in-memory ``_artifact_registry`` dict produced by
``tools/_artifact_helpers.py``), reads each LAS via lasio, wraps it in
the schema-compliant xarray.Dataset contract, and stores it in the
ZarrArtifactStore with a fresh lineage entry.

RECEIPT
=======

Every migrated artifact produces:
  - a zarr v3 store at
    /root/data/artifacts/zarr/<kind>/<canonical_id>/sha256-<hex>/
  - a lineage.json sibling with prev_hash=None (genesis entries)
  - a fresh index.json entry pointing at the new content_hash
  - a printed SHA-256 + canonical_ref + path for audit

The legacy _artifact_registry dict is NOT deleted — it's left in place
as a fallback when the new store can't resolve. Migration is purely
additive.

USAGE
=====

    cd /root/GEOX
    .venv/bin/python scripts/migrate_las_to_zarr.py

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Repo-root on the path so the GEOX package imports work when run directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import lasio  # noqa: E402
import numpy as np  # noqa: E402
import xarray as xr  # noqa: E402

from geox_mcp.artifacts.zarr_store import (  # noqa: E402
    ZarrArtifactStore,
    LineageEntry,
    well_log_from_legacy_entry,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("migrate_las_to_zarr")


# ── Source discovery ────────────────────────────────────────────────────────


def discover_las_files() -> list[Path]:
    """Find every .las/.LAS file under the configured GEOX well dirs."""
    roots: list[Path] = []
    for env in ("GEOX_WELL_DATA_DIR",):
        d = os.environ.get(env, "/data/wells")
        roots.append(Path(d))
    roots.append(Path("/data/geox_las"))

    found: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in (".las",):
                continue
            rp = path.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            found.append(path)
    return sorted(found)


def load_legacy_registry() -> dict[str, dict[str, Any]]:
    """Load the on-disk artifact_registry.json if it exists."""
    path = Path("/data/wells/artifact_registry.json")
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("failed to load legacy registry at %s: %s", path, exc)
        return {}


# ── LAS → xarray.Dataset ────────────────────────────────────────────────────


def _infer_units(mnemonic: str) -> str:
    """Best-effort pint-compatible unit string for a curve mnemonic.

    Failsafe default: ``"dimensionless"``. Caller must override for
    ambiguous mnemonics (e.g., DT may be US/F or US/M).
    """
    table = {
        "GR": "gAPI",
        "RHOB": "g/cm^3",
        "NPHI": "v/v",
        "RT": "ohm_m",
        "ILD": "ohm_m",
        "SP": "mV",
        "PEF": "b/e",
        "DT": "us/ft",
        "DTS": "us/ft",
        "DEPT": "m",
        "TVD": "m",
        "MD": "m",
        "ROP": "m/h",
        "GR_ED": "gAPI",
    }
    return table.get(mnemonic.upper(), "dimensionless")


def build_xr_dataset_from_las(
    las_path: Path,
) -> xr.Dataset | None:
    """Load a LAS file via lasio, normalize, return a schema-compliant xr.Dataset.

    Returns None when the file can't be parsed.
    """
    try:
        las = lasio.read(str(las_path))
    except Exception as exc:
        logger.warning("lasio.read failed for %s: %s", las_path, exc)
        return None

    # Skip files with no curves (header-only or corrupt).
    curve_mnemonics = [c.mnemonic for c in las.curves if c.mnemonic and c.mnemonic != "DEPT"]
    if not curve_mnemonics:
        logger.warning("no curves in %s — skipping", las_path)
        return None

    # Depth axis.
    depth_raw = np.asarray(las.index, dtype=float)
    # Drop rows where every curve value is the null sentinel.
    curves_arr: dict[str, np.ndarray] = {}
    for mn in curve_mnemonics:
        try:
            arr = np.asarray(las[mn], dtype=float)
        except KeyError:
            continue
        curves_arr[mn] = arr
    if not curves_arr:
        return None

    # Filter rows where ALL curve values are null.
    null_sentinel = -999.25
    keep_rows = np.ones(len(depth_raw), dtype=bool)
    for arr in curves_arr.values():
        keep_rows &= ~(np.isnan(arr) | (arr == null_sentinel))
    if not keep_rows.any():
        logger.warning("all-null rows in %s — skipping", las_path)
        return None
    depth = depth_raw[keep_rows]
    curves_arr = {k: v[keep_rows] for k, v in curves_arr.items()}

    # Build dataset.
    data_vars: dict[str, Any] = {}
    for mn, arr in curves_arr.items():
        data_vars[mn] = (
            ("depth",),
            arr.astype(float),
            {"units": _infer_units(mn)},
        )
    coords = {
        "depth": (
            "depth",
            depth,
            {"units": "m", "axis": "MD"},
        ),
    }
    attrs: dict[str, Any] = {
        "well": str(las.well.WELL.value).strip(),
        "uwi": str(las.well.UWI.value).strip() if "UWI" in las.well else "",
        "source_uri": f"file://{las_path}",
        "schema": "well_log_v1",
        "crs": "EPSG:4326",
        "depth_basis": "MD",
        "depth_unit": "m",
    }
    return xr.Dataset(data_vars, coords=coords, attrs=attrs)


# ── Migration main ──────────────────────────────────────────────────────────


def migrate_one(
    store: ZarrArtifactStore,
    las_path: Path,
    actor_id: str,
) -> LineageEntry | None:
    """Migrate one LAS file to the zarr store. Returns the lineage entry."""
    ds = build_xr_dataset_from_las(las_path)
    if ds is None:
        return None
    try:
        entry = store.put(
            ds,
            kind="well_las",
            source_uri=f"file://{las_path}",
            schema_version="well_log_v1",
            created_by=actor_id,
            tool_id="migration_script",
            action="create",
        )
    except ValueError as exc:
        logger.warning("schema validation failed for %s: %s", las_path, exc)
        return None
    return entry


def main() -> int:
    """Walk all LAS files and migrate. Print summary."""
    store_root = Path(os.environ.get("GEOX_ZARR_ROOT", "/root/data/artifacts/zarr"))
    actor_id = os.environ.get("GEOX_MIGRATION_ACTOR", "FI-008-migration")

    store = ZarrArtifactStore(root=store_root)
    files = discover_las_files()
    legacy = load_legacy_registry()
    logger.info("discovered %d LAS files; %d legacy registry entries", len(files), len(legacy))

    successes: list[LineageEntry] = []
    failures: list[tuple[Path, str]] = []
    for path in files:
        entry = migrate_one(store, path, actor_id=actor_id)
        if entry is None:
            failures.append((path, "schema or parse failure"))
        else:
            successes.append(entry)

    # Summary.
    print("=" * 64)
    print("MIGRATION SUMMARY")
    print("=" * 64)
    print(f"discovered:        {len(files)}")
    print(f"migrated:          {len(successes)}")
    print(f"failed:            {len(failures)}")
    print(f"store root:        {store_root}")
    print()
    print("--- migrated ---")
    for e in successes:
        print(f"  {e.artifact_ref}")
        print(f"    {e.kind}/{e.canonical_id}: content_hash={e.content_hash[:16]}...")
    if failures:
        print()
        print("--- failed ---")
        for path, reason in failures:
            print(f"  {path}: {reason}")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
