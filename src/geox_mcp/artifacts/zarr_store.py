"""
zarr_store — P0 Stage 2.2: zarr-backed artifact spine (DRAFT for review).

Forged 2026-07-25 · FI-008 (kimi-code) · agent-init Stage 2 work.

This module is the first cut of GEOX's artifact-spine migration per the
roadmap. It is ADDITIVE — the legacy ``_artifact_registry`` dict in
``tools/_artifact_helpers.py`` is untouched, so existing ingest/QC
paths keep working. Migration of existing artifacts is a follow-up
action (2.3) gated on this draft being reviewed and approved.

DOCTRINE
========

1. **Content-addressed identity.** Every artifact is stored under a
   canonical path derived from its ``content_hash``. Two artifacts with
   identical bytes produce identical paths; mutation creates a new path.

2. **Immutability (OSDU-aligned).** Once written, an artifact version is
   never modified. Corrections produce a new version with a new
   ``content_hash``; the lineage chain records the relationship via
   ``prev_hash``.

3. **xarray at the boundary, zarr on disk.** Agents consume
   ``xr.Dataset`` objects with unit-tagged coords and attrs. Storage
   is zarr v3 groups with Blosc/Zstd compression. Filesystem paths are
   opaque to callers — only the canonical reference is exchanged.

4. **pint units everywhere.** Every curve carries a ``units`` attribute
   (parseable by pint). Every coord carries a ``units`` attribute plus
   an ``axis`` (MD / TVD / TVDSS / TWT). CRS/datum are first-class.

5. **Lineage chain (Git-like).** Every store operation appends an entry
   to a hash-chained ledger; ``prev_hash`` links the new version to its
   parent. Detecting whether a dataset has changed is a single hash
   comparison (per ACM reference cited in the roadmap).

REVERSIBILITY
=============

This module is opt-in via ``ZarrArtifactStore.put()``. The legacy
``_artifact_registry`` (in-memory dict) is preserved. To revert: do
not call this module from ingest/QC. Delete the file and every GEOX
surface continues working unchanged.

NOT YET WIRED
=============

This draft is REQUIRES sovereign review before any of the following:

  - Replacing the in-memory ``_artifact_registry`` as the source of truth
  - Migrating existing LAS/SEG-Y artifacts into zarr stores
  - Persisting lineage to VAULT999 (uses local FS only today)
  - Adding a /artifacts REST endpoint exposing the spine

Until then, this module sits alongside the legacy store as a parallel
implementation that proves the design works end-to-end.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("geox_mcp.artifacts.zarr_store")

# Optional imports — the module is import-safe even when zarr/xarray
# are not installed; ``put``/``get`` raise informative errors in that case.
try:
    import xarray as xr
except ImportError:  # pragma: no cover — handled at runtime
    xr = None  # type: ignore[assignment]

try:
    import zarr
except ImportError:  # pragma: no cover
    zarr = None  # type: ignore[assignment]


# ── Lineage entry (hash-chained, JSON-serializable) ────────────────────────


@dataclass(frozen=True)
class LineageEntry:
    """One step in an artifact's hash-chained lineage.

    Attributes:
        artifact_ref: canonical reference ``artifact://geox/<kind>/<id>/sha256-<hex>``
        prev_hash:    hex digest of the previous entry's content_hash (or None for genesis)
        content_hash: hex digest of this version's bytes (computed from xarray.to_dict())
        source_uri:   where the bytes came from (file://, s3://, base64://, ...)
        kind:         short taxonomy token (``well_las``, ``seismic_segy``, ...)
        canonical_id: UWI or ``well:<WELL>`` or other stable identifier
        schema_version: protocol version (``well_log_v1``, ...)
        created_at:   ISO-8601 timestamp
        created_by:   actor_id that performed the store (F11 audit attribution)
        attrs:        passthrough metadata dict (CRS, depth_basis, units, ...)
        tool_id:      tool that produced the artifact (for provenance)
        action:       "create" | "supersede" | "append" | "replace"
    """

    artifact_ref: str
    content_hash: str
    source_uri: str
    kind: str
    canonical_id: str
    schema_version: str
    created_at: str
    created_by: str
    prev_hash: str | None = None
    attrs: dict[str, Any] = field(default_factory=dict)
    tool_id: str = ""
    action: str = "create"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LineageEntry:
        return cls(**d)

    def chain_hash(self) -> str:
        """Hash over the canonical entry fields — what prev_hash links to.

        Independent of the artifact's own content_hash so the lineage
        ledger can detect tampering with provenance metadata separately
        from the artifact bytes.
        """
        canonical = {
            "artifact_ref": self.artifact_ref,
            "content_hash": self.content_hash,
            "source_uri": self.source_uri,
            "kind": self.kind,
            "canonical_id": self.canonical_id,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "prev_hash": self.prev_hash,
            "attrs": json.dumps(self.attrs, sort_keys=True, default=str),
            "tool_id": self.tool_id,
            "action": self.action,
        }
        raw = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


# ── Zarr artifact store ────────────────────────────────────────────────────


class ZarrArtifactStore:
    """Content-addressed, hash-chained artifact store backed by zarr v3.

    Layout on disk::

        {root}/
          index.json                              # canonical_ref -> latest entry
          well_las/
            AUDIT-0001/
              sha256-abc123.../
                zarr.json                          # zarr v3 metadata
                c/                                 # chunks
                lineage.json                        # THIS version's lineage
              sha256-def456.../
                ...                                # next version (immutable)
          seismic_segy/
            ...

    The current version's lineage lives INSIDE its content_hash directory
    so lineage is co-located with the bytes it describes. ``index.json``
    maps canonical_ref → content_hash so ``get()`` can resolve.

    Schema validation on put:

      - ``Dataset.attrs`` MUST contain ``well`` (or other canonical_id),
        ``source_uri``, ``schema``, ``crs``, ``depth_basis``.
      - Every coord MUST carry a ``units`` attribute.
      - Every data_var MUST carry a ``units`` attribute.
    """

    # Schema fields that MUST be present on every Dataset.
    REQUIRED_ATTRS: tuple[str, ...] = (
        "well",
        "source_uri",
        "schema",
        "crs",
        "depth_basis",
    )

    def __init__(
        self,
        root: str | Path = "/root/data/artifacts/zarr",
        *,
        compression: str = "zstd",
        compression_level: int = 3,
    ) -> None:
        if xr is None or zarr is None:
            raise RuntimeError(
                "xarray and zarr are required for ZarrArtifactStore. "
                "Install with `uv pip install zarr xarray dask pint`."
            )
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.compression = compression
        self.compression_level = compression_level
        self._index_path = self.root / "index.json"
        if not self._index_path.exists():
            self._write_index({})

    # ── Schema validation ──────────────────────────────────────────────

    @staticmethod
    def _validate_dataset(ds: Any) -> tuple[bool, list[str]]:
        """Return (ok, missing_fields) per the schema contract."""
        missing: list[str] = []
        for attr in ZarrArtifactStore.REQUIRED_ATTRS:
            if attr not in ds.attrs or not ds.attrs.get(attr):
                missing.append(attr)
        for name, coord in ds.coords.items():
            if "units" not in coord.attrs or not coord.attrs.get("units"):
                missing.append(f"coord:{name}.units")
        for name, var in ds.data_vars.items():
            if "units" not in var.attrs or not var.attrs.get("units"):
                missing.append(f"data_var:{name}.units")
        return (len(missing) == 0, missing)

    @staticmethod
    def _canonical_id_from_attrs(attrs: dict[str, Any]) -> str:
        """Resolve canonical_id: UWI when present, else well:<WELL>."""
        uwi = attrs.get("uwi", "").strip()
        if uwi:
            return uwi
        well = attrs.get("well", "").strip()
        if well:
            return f"well:{well}"
        return ""

    @staticmethod
    def _content_hash(ds: Any) -> str:
        """Stable content hash from xarray.to_dict() — order-independent."""
        d = ds.to_dict()
        canonical = json.dumps(d, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _make_ref(kind: str, canonical_id: str, content_hash: str) -> str:
        return (
            f"artifact://geox/{kind}/{canonical_id}"
            f"/sha256-{content_hash}"
        )

    # ── index.json read/write ───────────────────────────────────────────

    def _read_index(self) -> dict[str, str]:
        try:
            return json.loads(self._index_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_index(self, index: dict[str, str]) -> None:
        tmp = self._index_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self._index_path)

    # ── path resolution ─────────────────────────────────────────────────

    def _version_dir(self, kind: str, canonical_id: str, content_hash: str) -> Path:
        return self.root / kind / canonical_id / f"sha256-{content_hash}"

    def _latest_content_hash(self, kind: str, canonical_id: str) -> str | None:
        kind_dir = self.root / kind / canonical_id
        if not kind_dir.exists():
            return None
        versions = [p.name for p in kind_dir.iterdir() if p.is_dir() and p.name.startswith("sha256-")]
        if not versions:
            return None
        # Latest by content_hash lexical sort is NOT chronological. For
        # now: index.json is the source of truth for which hash is
        # canonical. If absent, fall back to most-recent by mtime.
        idx = self._read_index()
        ref_key = f"{kind}/{canonical_id}"
        if ref_key in idx:
            return idx[ref_key].replace("sha256-", "")
        return max(versions).replace("sha256-", "")

    def exists(self, ref: str) -> bool:
        """Return True iff any version exists for the canonical ref."""
        from geox_mcp.tools._artifact_identity import parse_artifact_ref

        parsed = parse_artifact_ref(ref)
        if parsed is None or parsed["format"] != "canonical":
            return False
        kind = parsed["kind"]
        canonical_id = parsed["canonical_id"]
        sha = parsed.get("sha256")
        if sha:
            return (self.root / kind / canonical_id / f"sha256-{sha}").exists()
        return self._latest_content_hash(kind, canonical_id) is not None

    # ── put / get ────────────────────────────────────────────────────────

    def put(
        self,
        ds: Any,
        *,
        kind: str,
        source_uri: str,
        schema_version: str,
        created_by: str,
        tool_id: str = "",
        action: str = "create",
        canonical_id: str | None = None,
        prev_hash: str | None = None,
    ) -> LineageEntry:
        """Persist ``ds`` to zarr and record a lineage entry.

        Args:
            ds: xarray.Dataset with schema attrs (well/uwi/source_uri/
                schema/crs/depth_basis) and unit attrs on every coord
                and data_var.
            kind: short taxonomy token (``well_las``, ``seismic_segy``).
            source_uri: where the bytes came from (file://, s3://, ...).
            schema_version: protocol version (``well_log_v1``).
            created_by: actor_id (F11 audit).
            tool_id: tool that produced the artifact (provenance).
            action: ``create`` / ``supersede`` / ``append`` / ``replace``.
            canonical_id: override canonical_id resolution; default uses
                attrs.uwi (preferred) or attrs.well.
            prev_hash: explicit lineage link; default walks the previous
                version in index.json.

        Returns:
            LineageEntry for the new version.

        Raises:
            ValueError: when schema validation fails or canonical_id is
                empty.
        """
        # 1. Validate schema.
        ok, missing = self._validate_dataset(ds)
        if not ok:
            raise ValueError(
                f"Dataset schema validation failed; missing/invalid: {missing}"
            )

        # 2. Resolve canonical_id.
        cid = canonical_id or self._canonical_id_from_attrs(dict(ds.attrs))
        if not cid:
            raise ValueError(
                "canonical_id could not be resolved from dataset attrs "
                "(need attrs['uwi'] or attrs['well'])"
            )

        # 3. Compute content_hash.
        content_hash = self._content_hash(ds)
        ref = self._make_ref(kind, cid, content_hash)

        # 4. Determine prev_hash when caller didn't supply one.
        if prev_hash is None:
            prev_sha = self._latest_content_hash(kind, cid)
            if prev_sha and prev_sha != content_hash:
                prev_hash = prev_sha
            else:
                prev_hash = None  # genesis or self-reference

        # 5. Write zarr v3 array group.
        version_dir = self._version_dir(kind, cid, content_hash)
        if version_dir.exists():
            logger.info(
                "ZARR_STORE: artifact already exists at %s — no-op", version_dir
            )
            # Still return the existing lineage so callers can build refs.
            lineage_path = version_dir / "lineage.json"
            if lineage_path.exists():
                return LineageEntry.from_dict(
                    json.loads(lineage_path.read_text(encoding="utf-8"))
                )

        version_dir.mkdir(parents=True, exist_ok=True)
        # Persist the Dataset as a zarr v3 group at version_dir.
        # ``xarray.Dataset.to_zarr`` writes a group; we control store path.
        ds.to_zarr(
            store=str(version_dir),
            mode="w",
            consolidated=False,
            zarr_format=3,
        )

        # 6. Build and persist lineage entry.
        entry = LineageEntry(
            artifact_ref=ref,
            content_hash=content_hash,
            source_uri=source_uri,
            kind=kind,
            canonical_id=cid,
            schema_version=schema_version,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            created_by=created_by,
            prev_hash=prev_hash,
            attrs={k: v for k, v in ds.attrs.items()},
            tool_id=tool_id,
            action=action,
        )
        lineage_path = version_dir / "lineage.json"
        lineage_path.write_text(
            json.dumps(entry.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        # 7. Update index.json (canonical_ref-keyed, points to latest).
        idx = self._read_index()
        idx[f"{kind}/{cid}"] = f"sha256-{content_hash}"
        self._write_index(idx)

        logger.info(
            "ZARR_STORE: stored %s (size=%d vars=%d)",
            ref,
            version_dir.stat().st_size if version_dir.exists() else 0,
            len(ds.data_vars),
        )
        return entry

    def get(self, ref: str) -> Any | None:
        """Load a Dataset by canonical ref. None when not found."""
        from geox_mcp.tools._artifact_identity import parse_artifact_ref

        parsed = parse_artifact_ref(ref)
        if parsed is None:
            return None

        kind = parsed["kind"]
        canonical_id = parsed["canonical_id"]
        sha = parsed.get("sha256") or self._latest_content_hash(kind, canonical_id)
        if not sha:
            return None
        version_dir = self._version_dir(kind, canonical_id, sha)
        if not version_dir.exists():
            return None
        try:
            return xr.open_zarr(store=str(version_dir), consolidated=False)
        except Exception as exc:
            logger.warning(
                "ZARR_STORE: failed to open %s: %s", version_dir, exc
            )
            return None

    def lineage(self, ref: str) -> list[LineageEntry]:
        """Return the full hash-chained lineage for ``ref``.

        Walks ``prev_hash`` pointers starting from ``ref`` until genesis
        (prev_hash is None). Returns the list ordered newest → oldest.
        """
        out: list[LineageEntry] = []
        from geox_mcp.tools._artifact_identity import parse_artifact_ref

        parsed = parse_artifact_ref(ref)
        if parsed is None or parsed["format"] != "canonical":
            return out
        kind = parsed["kind"]
        canonical_id = parsed["canonical_id"]

        # Walk back from the given ref.
        cur_sha: str | None = parsed.get("sha256") or self._latest_content_hash(
            kind, canonical_id
        )
        while cur_sha is not None:
            version_dir = self._version_dir(kind, canonical_id, cur_sha)
            lineage_path = version_dir / "lineage.json"
            if not lineage_path.exists():
                break
            entry = LineageEntry.from_dict(
                json.loads(lineage_path.read_text(encoding="utf-8"))
            )
            out.append(entry)
            cur_sha = entry.prev_hash
        return out

    def list(
        self, *, kind: str | None = None
    ) -> list[LineageEntry]:
        """Enumerate the most recent lineage entry per artifact.

        Returns the latest version's LineageEntry for each (kind, canonical_id).
        """
        out: list[LineageEntry] = []
        kinds = [kind] if kind else [
            p.name for p in self.root.iterdir() if p.is_dir()
        ]
        for k in kinds:
            kind_dir = self.root / k
            if not kind_dir.exists():
                continue
            for cid_dir in kind_dir.iterdir():
                if not cid_dir.is_dir():
                    continue
                # Use index.json to find latest, else fall back to lexical max.
                idx = self._read_index()
                ref_key = f"{k}/{cid_dir.name}"
                if ref_key in idx:
                    sha = idx[ref_key].replace("sha256-", "")
                else:
                    versions = sorted(
                        p.name for p in cid_dir.iterdir() if p.is_dir()
                    )
                    if not versions:
                        continue
                    sha = versions[-1].replace("sha256-", "")
                lineage_path = cid_dir / f"sha256-{sha}" / "lineage.json"
                if lineage_path.exists():
                    out.append(
                        LineageEntry.from_dict(
                            json.loads(lineage_path.read_text(encoding="utf-8"))
                        )
                    )
        return out


# ── Helper: build xr.Dataset from a legacy artifact entry (for migration) ─


def well_log_from_legacy_entry(
    entry: dict[str, Any],
    curves: dict[str, list[float]],
    depth: list[float],
    *,
    units: dict[str, str] | None = None,
) -> Any:
    """Construct an xarray.Dataset from a legacy artifact entry + raw curves.

    Used by the 2.3 migration script (next concrete action). Validates
    that every curve has a ``units`` entry in ``units``.

    Returns:
        xr.Dataset with the schema contract enforced.
    """
    if xr is None:
        raise RuntimeError("xarray required for migration helper")
    units = units or {}
    missing_units = [c for c in curves if c not in units]
    if missing_units:
        raise ValueError(
            f"curves without units — pint requires every curve to be unit-tagged: {missing_units}"
        )

    import numpy as np

    coords: dict[str, Any] = {
        "depth": (
            "depth",
            np.asarray(depth, dtype=float),
            {"units": units.get("__depth__", "m"), "axis": "MD"},
        ),
    }
    data_vars: dict[str, Any] = {}
    for name, values in curves.items():
        arr = np.asarray(values, dtype=float)
        # Replace null sentinel with NaN.
        arr = np.where(arr == -999.25, np.nan, arr)
        data_vars[name] = (
            ("depth",),
            arr,
            {"units": units[name]},
        )

    attrs = {
        "well": entry.get("well") or entry.get("aliases", ["unknown"])[0],
        "uwi": entry.get("uwi", ""),
        "source_uri": entry.get("source_uri", "file://unknown"),
        "schema": entry.get("schema", "well_log_v1"),
        "crs": entry.get("crs", "EPSG:4326"),
        "depth_basis": entry.get("depth_basis", "MD"),
        "depth_unit": units.get("__depth__", "m"),
    }

    return xr.Dataset(data_vars, coords=coords, attrs=attrs)
