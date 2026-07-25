"""
artifact_resolve — Prompt C: resolve any well ref → LAS path + canonical id.

Accepts:
  - artifact://geox/<kind>/<id>/sha256-<hex>
  - well_las:<name> / WELL:<name>
  - bare DEMO-* / well display names
  - filesystem paths (*.las)

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from geox_mcp.artifact_identity import (
    make_artifact_id,
    parse_artifact_ref,
    sha256_for_file,
    storage_keys_for,
)


def _geox_root() -> Path:
    """…/GEOX/src/geox_mcp/artifact_resolve.py → GEOX root."""
    return Path(__file__).resolve().parents[2]


def resolve_well_las(ref: str) -> dict[str, Any]:
    """Resolve a well reference to a LAS path and identity metadata."""
    raw = (ref or "").strip()
    empty = {
        "ok": False,
        "ref_raw": ref,
        "las_path": None,
        "well_id": None,
        "canonical_artifact_ref": None,
        "kind": "well_las",
        "error": "empty_ref",
        "source": "none",
        "sha256": None,
    }
    if not raw:
        return empty

    root = _geox_root()

    # Direct filesystem path
    as_path = Path(raw)
    if not as_path.is_absolute():
        cand = root / raw
        if cand.is_file() and cand.suffix.lower() == ".las":
            as_path = cand
    if as_path.is_file() and as_path.suffix.lower() == ".las":
        sha = sha256_for_file(str(as_path)) or ("0" * 64)
        wid = as_path.stem
        canon = make_artifact_id("well_las", f"well:{wid}", sha)
        return {
            "ok": True,
            "ref_raw": raw,
            "las_path": str(as_path.resolve()),
            "well_id": wid,
            "canonical_artifact_ref": canon,
            "kind": "well_las",
            "error": None,
            "source": "path",
            "sha256": sha,
        }

    parsed = parse_artifact_ref(raw) or {}
    display = (
        parsed.get("display_name")
        or (parsed.get("canonical_id") or "").removeprefix("well:")
        or raw
    )
    kind = parsed.get("kind") or "well_las"

    # In-memory artifact store
    try:
        from geox_mcp.tools._helpers import _get_artifact

        for key in storage_keys_for(raw) + [raw, f"well_las:{display}", display]:
            entry = _get_artifact(key)
            if not entry:
                continue
            lp = entry.get("las_path")
            if not lp or not Path(lp).is_file():
                continue
            las = str(Path(lp).resolve())
            sha = str(entry.get("content_hash") or sha256_for_file(las) or ("0" * 64))
            sha = sha.removeprefix("sha256:")
            if len(sha) != 64:
                sha = sha256_for_file(las) or ("0" * 64)
            wid = entry.get("well_id") or display
            if isinstance(wid, str) and ":" in wid and not wid.startswith("well:"):
                # well_las:NAME → NAME
                wid = wid.split(":", 1)[-1]
            canon = make_artifact_id(
                "well_las" if not str(kind).startswith("well") else kind,
                f"well:{wid}" if not str(wid).startswith("well:") else wid,
                sha,
            )
            return {
                "ok": True,
                "ref_raw": raw,
                "las_path": las,
                "well_id": wid,
                "canonical_artifact_ref": canon,
                "kind": kind,
                "error": None,
                "source": "store",
                "sha256": sha,
            }
    except Exception:
        pass

    # Demo registry / disk scan
    try:
        from geox_mcp.tools.integration_well import _load_well_curves_for_ui
        from geox_mcp.tools._helpers import _register_artifact

        loaded = _load_well_curves_for_ui(display, max_n=50)
        if loaded.get("status") == "loaded" and loaded.get("las_path"):
            las = str(Path(loaded["las_path"]).resolve())
            sha = sha256_for_file(las) or ("0" * 64)
            wid = loaded.get("well_name") or display
            canon = make_artifact_id("well_las", f"well:{wid}", sha)
            curves = list((loaded.get("curves") or {}).keys())
            try:
                _register_artifact(
                    f"well_las:{wid}",
                    las_path=las,
                    curves=curves,
                    claim_state="RAW_OBSERVATION",
                    source_uri=las,
                    artifact_type="well_log",
                )
                _register_artifact(
                    canon,
                    las_path=las,
                    curves=curves,
                    claim_state="RAW_OBSERVATION",
                    source_uri=las,
                    artifact_type="well_log",
                )
            except Exception:
                pass
            return {
                "ok": True,
                "ref_raw": raw,
                "las_path": las,
                "well_id": wid,
                "canonical_artifact_ref": canon,
                "kind": "well_las",
                "error": None,
                "source": "demo",
                "sha256": sha,
                "data_class": loaded.get("data_class"),
            }
    except Exception as exc:
        return {
            **empty,
            "well_id": display,
            "kind": kind,
            "error": f"resolve_failed:{type(exc).__name__}",
        }

    return {
        **empty,
        "well_id": display,
        "kind": kind,
        "error": "LAS_NOT_FOUND",
    }


def resolve_many(refs: list[str]) -> list[dict[str, Any]]:
    return [resolve_well_las(r) for r in (refs or [])]
