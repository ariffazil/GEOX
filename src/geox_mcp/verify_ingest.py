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

# ── Identity + curve-set normalisation (F06/F07/F08, 2026-11-24) ─────────
# The verifier compared raw strings and raw list lengths, producing false
# DEGRADED verdicts on clean files:
#   F06 curve count: stored list excluded the depth curve, file included it.
#   F07 UWI: stored UWI was inferred from a permit token ("VOLVE", "Q15")
#       and then compared against the header UWI, manufacturing a mismatch.
#   F08 well name: "15/9-F-11A" != "15/9-F-11 A" under raw equality.
_DEPTH_MNEMONICS = frozenset({"DEPT", "DEPTH", "D", "MD", "TVD", "TVDSS", "TIME"})
_INFERRED_UWI_TOKENS = frozenset({"", "UNKNOWN", "VOLVE", "Q15", "N/A", "NA"})


def _norm_identity(value: Any) -> str:
    """Canonicalise an identifier: keep alphanumerics only, upper-case.

    "15/9-F-11A" and "15/9-F-11 A" both become "159F11A".
    """
    return "".join(ch for ch in str(value).upper() if ch.isalnum())


def _curve_set(curves: Any) -> set[str]:
    """Mnemonics present, excluding the depth/index curve."""
    out: set[str] = set()
    for c in curves or []:
        mnemonic = getattr(c, "mnemonic", c)
        m = str(mnemonic).strip().upper()
        if m and m not in _DEPTH_MNEMONICS:
            out.add(m)
    return out


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

        # F07: the UWI of record is the LAS header. An inferred permit token
        # ("VOLVE", "Q15") is provenance, not identity — comparing it to the
        # header manufactures a false mismatch. Header is authoritative; when
        # the header carries no UWI we report UNKNOWN instead of inventing one.
        stored_uwi_is_inferred = str(stored_uwi).strip().upper() in _INFERRED_UWI_TOKENS
        if header_uwi and stored_uwi and not stored_uwi_is_inferred and _norm_identity(stored_uwi) != _norm_identity(header_uwi):
            checks.append(
                {
                    "name": "uwi_match",
                    "passed": False,
                    "detail": f"UWI mismatch: stored='{stored_uwi}' file='{header_uwi}'",
                }
            )
            failed += 1
        elif header_uwi:
            checks.append(
                {
                    "name": "uwi_match",
                    "passed": True,
                    "detail": f"UWI={header_uwi}" + (" (stored UWI was inferred, not compared)" if stored_uwi_is_inferred and stored_uwi else ""),
                }
            )
            passed += 1
        else:
            checks.append(
                {
                    "name": "uwi_match",
                    "passed": True,
                    "detail": "UWI=UNKNOWN (header carries no UWI; nothing inferred)",
                }
            )
            passed += 1

        # F08: compare canonicalised well names, so spacing/punctuation variants
        # of the same well do not fail the check.
        if stored_well_id and header_well and _norm_identity(stored_well_id) != _norm_identity(header_well):
            checks.append(
                {
                    "name": "well_match",
                    "passed": False,
                    "detail": f"WELL mismatch: stored='{stored_well_id}' file='{header_well}' "
                    f"(canonical '{_norm_identity(stored_well_id)}' vs '{_norm_identity(header_well)}')",
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

        # ── Unit observation (G3): depth unit vs sonic unit ─────────────
        # Volve LAS ships DEPTH in metres and DT in microseconds/foot.
        # Nothing is converted silently; we record what we observed so a
        # downstream consumer cannot mistake ft/s for m/s.
        try:
            import numpy as _np

            dt_curve = None
            for _c in las.curves:
                if _c.mnemonic.strip().upper() in {"DT", "DTC", "AC"}:
                    dt_curve = _c
                    break
            if dt_curve is not None:
                _vals = _np.asarray(dt_curve.data, dtype=float)
                _vals = _vals[_np.isfinite(_vals)]
                if _vals.size:
                    _median = float(_np.median(_vals))
                    checks.append(
                        {
                            "name": "unit_observation",
                            "passed": True,
                            "detail": {
                                "depth_unit": str(header_depth_unit),
                                "sonic_curve": dt_curve.mnemonic,
                                "sonic_median": round(_median, 3),
                                "sonic_unit_inferred": "us/ft" if _median < 150 else "us/m",
                                "mixed_units": str(header_depth_unit).upper() == "M",
                            },
                        }
                    )
                    passed += 1
        except Exception:
            pass

        # F06: compare the curve SET with the depth curve excluded on both
        # sides. A set comparison also catches the wrong-curve case, which a
        # bare length comparison cannot.
        stored_curves = stored_metadata.get("curve_inventory") or stored_metadata.get("loaded_curves") or []
        stored_curve_set = _curve_set(stored_curves)
        file_curve_set = _curve_set(las.curves)
        if stored_curve_set and file_curve_set != stored_curve_set:
            checks.append(
                {
                    "name": "curve_count_match",
                    "passed": False,
                    "detail": (
                        f"curve set mismatch: stored={len(stored_curve_set)} file={len(file_curve_set)} "
                        f"only_stored={sorted(stored_curve_set - file_curve_set)} "
                        f"only_file={sorted(file_curve_set - stored_curve_set)}"
                    ),
                }
            )
            failed += 1
        elif stored_curve_set:
            checks.append(
                {
                    "name": "curve_count_match",
                    "passed": True,
                    "detail": f"{len(stored_curve_set)} curves (depth curve excluded)",
                }
            )
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
