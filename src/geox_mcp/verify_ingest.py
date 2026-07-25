"""
verify_ingest — P0-4 dual-control independent verification.

Every governed ingest MUST pass an independent read-back before
the result is returned. The verifier MUST NOT reuse the ingest
function's in-memory result — it opens the file independently.

Pipeline:
  write → close → independent reopen → SHA-256 → parse UWI/WELL
  → validate curves/depth → compare metadata → VERIFIED or HOLD

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any

logger = logging.getLogger("geox.verify_ingest")


def verify_ingest_independent(
    las_path: str,
    stored_metadata: dict[str, Any],
    artifact_ref: str = "",
) -> dict[str, Any]:
    """Independent dual-control verification of a just-ingested LAS file.

    Opens the file independently, recomputes hash, extracts headers,
    and cross-checks against the stored ingest metadata. Does NOT
    reuse any in-memory result from the ingest function.

    Returns a verification envelope for injection into the response.
    """
    checks: list[dict[str, Any]] = []
    passed = 0
    failed = 0

    # ── Check 1: Independent file open ──────────────────────────────
    if not os.path.exists(las_path):
        return {
            "verdict": "HOLD",
            "reason": "FILE_NOT_FOUND",
            "detail": f"LAS file not found at {las_path} after ingest",
            "checks": [{"name": "file_exists", "passed": False, "detail": las_path}],
            "passed": 0,
            "failed": 1,
        }

    checks.append({"name": "file_exists", "passed": True, "detail": las_path})
    passed += 1

    # ── Check 2: Independent SHA-256 recomputation ──────────────────
    file_sha = _sha256_file(las_path)
    stored_hash = stored_metadata.get("content_sha256") or stored_metadata.get("sha256")
    if not file_sha:
        checks.append({"name": "sha256_compute", "passed": False, "detail": "hash computation failed"})
        failed += 1
    else:
        checks.append({"name": "sha256_compute", "passed": True, "detail": f"sha256:{file_sha[:16]}..."})
        passed += 1
        if stored_hash:
            stored_clean = stored_hash.removeprefix("sha256:")
            if file_sha == stored_clean:
                checks.append({"name": "sha256_match", "passed": True, "detail": "hash matches stored metadata"})
                passed += 1
            else:
                checks.append(
                    {
                        "name": "sha256_match",
                        "passed": False,
                        "detail": f"hash mismatch: file={file_sha[:16]}... stored={stored_clean[:16]}...",
                    }
                )
                failed += 1

    # ── Check 3: LAS header parsing (UWI / WELL / depth) ────────────
    try:
        import lasio

        las = lasio.read(las_path, ignore_header_errors=True)
        well_info = las.well
        header_uwi = (well_info.UWI.value if hasattr(well_info, "UWI") else None) or ""
        header_well = (well_info.WELL.value if hasattr(well_info, "WELL") else None) or ""
        header_depth_unit = (well_info.DUNM.value if hasattr(well_info, "DUNM") else None) or "M"

        checks.append(
            {
                "name": "las_parse",
                "passed": True,
                "detail": {
                    "uwi": str(header_uwi)[:80],
                    "well": str(header_well)[:80],
                    "depth_unit": str(header_depth_unit),
                    "curve_count": len(las.curves) if las.curves else 0,
                },
            }
        )
        passed += 1

        # Check UWI/WELL against stored metadata
        stored_well_id = stored_metadata.get("well_id") or stored_metadata.get("asset_id") or ""
        stored_uwi = stored_metadata.get("uwi") or ""

        if stored_uwi and header_uwi and stored_uwi.strip() != header_uwi.strip():
            checks.append(
                {
                    "name": "uwi_match",
                    "passed": False,
                    "detail": f"UWI mismatch: stored='{stored_uwi}' file='{header_uwi}'",
                }
            )
            failed += 1
        elif stored_uwi and header_uwi:
            checks.append({"name": "uwi_match", "passed": True, "detail": f"UWI={header_uwi}"})
            passed += 1

        if stored_well_id and header_well and stored_well_id.strip() != header_well.strip():
            checks.append(
                {
                    "name": "well_match",
                    "passed": False,
                    "detail": f"WELL mismatch: stored='{stored_well_id}' file='{header_well}'",
                }
            )
            failed += 1
        elif stored_well_id and header_well:
            checks.append({"name": "well_match", "passed": True, "detail": f"WELL={header_well}"})
            passed += 1

        # Check depth unit
        stored_unit = stored_metadata.get("depth_unit_normalized") or stored_metadata.get("depth_unit_original") or "M"
        if header_depth_unit and stored_unit.upper() != header_depth_unit.upper():
            checks.append(
                {
                    "name": "depth_unit_match",
                    "passed": False,
                    "detail": f"depth unit mismatch: stored='{stored_unit}' file='{header_depth_unit}'",
                }
            )
            failed += 1
        elif header_depth_unit:
            checks.append({"name": "depth_unit_match", "passed": True, "detail": f"depth_unit={header_depth_unit}"})
            passed += 1

        # Check curve count
        stored_curves = stored_metadata.get("curve_inventory") or stored_metadata.get("loaded_curves") or []
        file_curve_count = len(las.curves) if las.curves else 0
        if stored_curves and file_curve_count != len(stored_curves):
            checks.append(
                {
                    "name": "curve_count_match",
                    "passed": False,
                    "detail": f"curve count mismatch: stored={len(stored_curves)} file={file_curve_count}",
                }
            )
            failed += 1
        elif stored_curves:
            checks.append({"name": "curve_count_match", "passed": True, "detail": f"{len(stored_curves)} curves"})
            passed += 1

    except ImportError:
        checks.append({"name": "las_parse", "passed": False, "detail": "lasio not available"})
        failed += 1
    except Exception as exc:
        checks.append({"name": "las_parse", "passed": False, "detail": str(exc)[:200]})
        failed += 1

    # ── Verdict ──────────────────────────────────────────────────────
    verdict = "VERIFIED" if failed == 0 else "DEGRADED" if failed <= 2 else "HOLD"

    return {
        "verdict": verdict,
        "passed": passed,
        "failed": failed,
        "artifact_ref": artifact_ref,
        "file_path": las_path,
        "file_sha256": f"sha256:{file_sha}" if file_sha else None,
        "checks": checks,
        "doctrine": "P0-4: Dual-control independent verification. Verifier does not reuse ingest memory.",
    }


def _sha256_file(path: str) -> str:
    """Stream-compute SHA-256 of a file. Empty string on read error."""
    sha = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()
    except OSError:
        return ""
