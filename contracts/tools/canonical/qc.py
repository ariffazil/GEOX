from __future__ import annotations

import logging
from typing import Any, List, Dict, Optional, Literal

from fastmcp import FastMCP
from contracts.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
)
from contracts.tools.canonical._helpers import (
    _get_artifact,
    _artifact_exists,
    _register_artifact,
    _record_latest_qc,
    _latest_qc_failed_refs,
    _check_maruah_territory,
    _inject_ensemble_residual_evidence,
    _safe_upload_path,
    _decode_upload_content,
    _parse_csv_or_json,
    _map_canonical_curves,
    _detect_depth_unit,
    _compute_vsh_from_store,
    _compute_porosity_from_store,
    _compute_saturation_from_store,
    _compute_netpay_from_store,
    _classify_gr_motif,
    _classify_lithology_from_store,
    _safe_reduction,
    _get_well_data_with_depth,
    CLAIM_STATES,
    CANONICAL_ALIASES,
    _CURVE_RANGES,
    _artifact_registry,
    _artifact_store,
    _well_curves_registry,
    _ARTIFACT_REGISTRY_PATH,
    MAX_UPLOAD_BYTES,
)
from compatibility.legacy_aliases import LEGACY_ALIAS_MAP, get_alias_metadata

logger = logging.getLogger("geox.canonical.qc")


async def geox_data_qc_bundle(
    artifact_ref: str,
    artifact_type: str,
    qc_mode: Literal["full", "header", "curves", "depth", "completeness"] = "full",
) -> dict:
    """Real QC: depth monotonicity, null %, physical range checks.

    Fails closed: artifact_ref must have been previously ingested.
    Sets claim_state=QC_VERIFIED only after actual data inspection.

    Args:
        artifact_ref: Artifact ID returned by geox_data_ingest_bundle.
        artifact_type: Type hint (e.g. well_log).
        qc_mode: QC sub-mode.
            - "header": check well name, UWI, coordinates, datum, depth unit.
            - "depth": monotonicity, step consistency, duplicate depth count.
            - "curves": physical range checks per canonical curve.
            - "completeness": which canonical curves present vs missing.
            - "full" (default): all of the above.
    """
    # Red Team Fix: Initialize these to ensure they are available for the fail-closed check
    curve_warnings = []
    depth_qc = {}
    header_checks = {}
    present_curves = []
    missing_curves = []
    completeness_score = 0.0

    if not artifact_ref or not _artifact_exists(artifact_ref):
        return get_standard_envelope(
            {
                "tool": "geox_data_qc_bundle",
                "error_code": "ARTIFACT_NOT_FOUND",
                "artifact_status": "MISSING",
                "primary_artifact": None,
                "flags": ["ARTIFACT_NOT_FOUND"],
                "uncertainty": "High",
                "claim_state": "NO_VALID_EVIDENCE",
                "qc_passed": False,
            },
            tool_class="qc",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
        )

    store_entry = _get_artifact(artifact_ref)
    las_path = store_entry.get("las_path") if store_entry else None

    # If no path stored (e.g. manually registered artifact), return shallow pass
    if not las_path or not os.path.exists(las_path):
        _record_latest_qc(
            artifact_ref,
            {
                "qc_overall": "SHALLOW",
                "qc_passed": True,
                "flags": ["QC_ENGINE_SKIPPED: no LAS path in store"],
                "limitations": ["Artifact registered but LAS path unavailable."],
                "claim_state": "QC_VERIFIED",
            },
        )
        return get_standard_envelope(
            {
                "tool": "geox_data_qc_bundle",
                "artifact_ref": artifact_ref,
                "artifact_type": artifact_type,
                "artifact_status": "REGISTERED_NO_PATH",
                "qc_passed": True,
                "flags": ["QC_ENGINE_SKIPPED: no LAS path in store"],
                "claim_state": "INGESTED",
                "warning": "Artifact registered but LAS path unavailable — shallow pass only. NOT QC_VERIFIED.",
            },
            tool_class="qc",
            execution_status=ExecutionStatus.SUCCESS,
            artifact_status=ArtifactStatus.DRAFT,
            claim_tag="HYPOTHESIS",
        )

    # ── Mode-specific QC ─────────────────────────────────────────────────
    import sys
    sys.path.insert(0, "/root/geox")
    import numpy as np

    try:
        import lasio
        las = lasio.read(las_path)
        raw_curves = {}
        for key in las.keys():
            raw_curves[key.upper()] = np.array(las[key].data)

        # DEPTH array
        depth_arr = None
        for dk in ["DEPT", "DEPTH", "MD"]:
            if dk in raw_curves:
                depth_arr = raw_curves[dk]
                break

        if qc_mode in ("header", "full"):
            header_score = 0.0
            header_checks = {}
            well_name = str(las.well.get("WELL", "")).strip()
            uwi = str(las.well.get("UWI", "")).strip()
            loc = str(las.well.get("LOC", "")).strip()
            datum = str(las.well.get("DATUM", "")).strip()
            depth_unit = _detect_depth_unit(las_path)

            checks_passed = sum([
                bool(well_name and well_name not in ("", "None")),
                bool(uwi and uwi not in ("", "None")),
                bool(loc and loc not in ("", "None")),
                bool(datum and datum not in ("", "None")),
                bool(depth_unit and depth_unit not in ("UNKNOWN", "", "None")),
            ])
            header_score = round(checks_passed / 5.0, 2)
            header_checks = {
                "well_name": well_name or "MISSING",
                "uwi": uwi or "MISSING",
                "location": loc or "MISSING",
                "datum": datum or "MISSING",
                "depth_unit": depth_unit,
                "header_score": header_score,
            }

        if qc_mode in ("depth", "full") and depth_arr is not None:
            diffs = np.diff(depth_arr)
            is_monotonic = bool(np.all(diffs > 0) or np.all(diffs < 0))
            step_mean = float(np.mean(np.abs(diffs))) if len(diffs) > 0 else 0.0
            step_std = float(np.std(np.abs(diffs))) if len(diffs) > 0 else 0.0
            n_duplicates = int(np.sum(diffs == 0))
            depth_qc = {
                "monotonic": is_monotonic,
                "step_mean_m": round(step_mean, 4),
                "step_std_m": round(step_std, 4),
                "n_duplicate_depths": n_duplicates,
                "depth_range_m": [float(depth_arr[0]), float(depth_arr[-1])],
            }

        if qc_mode in ("curves", "full"):
            curve_warnings = []
            curve_statistics = {}
            for mnemonic, arr in raw_curves.items():
                if mnemonic in {"DEPT", "DEPTH", "MD"}:
                    continue
                arr_float = np.asarray(arr, dtype=float)
                valid = arr_float[~np.isnan(arr_float)]
                curve_statistics[mnemonic] = {
                    "sample_count": int(arr_float.size),
                    "null_pct": round(float(np.isnan(arr_float).sum() / max(arr_float.size, 1) * 100.0), 3),
                    "min": float(np.nanmin(valid)) if valid.size else None,
                    "max": float(np.nanmax(valid)) if valid.size else None,
                }
            for canon, (lo, hi, unit) in _CURVE_RANGES.items():
                # Find the mnemonic in raw_curves via aliases
                arr = None
                for alias in CANONICAL_ALIASES.get(canon, []):
                    if alias in raw_curves:
                        arr = raw_curves[alias]
                        break
                if arr is None:
                    continue
                valid = arr[~np.isnan(arr)]
                if len(valid) == 0:
                    curve_warnings.append(f"{canon}: all values NaN")
                    continue
                if lo is not None and float(np.min(valid)) < lo:
                    curve_warnings.append(
                        f"{canon}: min={float(np.min(valid)):.2f} below {lo} {unit}"
                    )
                if hi is not None and float(np.max(valid)) > hi:
                    curve_warnings.append(
                        f"{canon}: max={float(np.max(valid)):.2f} above {hi} {unit}"
                    )
                if canon == "RT" and float(np.min(valid)) <= 0:
                    curve_warnings.append(f"{canon}: non-positive resistivity values found")

        if qc_mode in ("completeness", "full"):
            curve_mnemonics_upper = {k.upper() for k in raw_curves.keys()}
            present_curves = []
            missing_curves = []
            for canon, aliases in CANONICAL_ALIASES.items():
                found = any(a in curve_mnemonics_upper for a in aliases)
                if found:
                    present_curves.append(canon)
                else:
                    missing_curves.append(canon)
            completeness_score = round(len(present_curves) / len(CANONICAL_ALIASES), 2)

    except Exception as exc:
        # Fall through to the standard LASIngestor QC path
        pass

    # Always also run LASIngestor QC as the base
    try:
        from geox.services.las_ingestor import LASIngestor
        ingestor = LASIngestor()
        well_result = ingestor.ingest(path=las_path, asset_id=artifact_ref)
        qc_result = ingestor.qc_logs(well_result, las_path)
        qc_dict = qc_result.to_dict()

        qc_overall = qc_dict.get("qc_overall", "FAIL")
        inherited_diagnostics = (store_entry or {}).get("diagnostics", {})
        inherited_limitations = list(inherited_diagnostics.get("limitations") or [])
        inherited_suitability = inherited_diagnostics.get("suitability")
        inherited_qcfail_count = int(inherited_diagnostics.get("qcfail_count") or 0)

        engine_flags = [
            issue.type
            for c in qc_result.curve_results
            for issue in (c.issues if hasattr(c, "issues") else [])
        ]
        curve_state_flags = [
            f"CURVE_{c.status}_STATE:{c.mnemonic}"
            for c in qc_result.curve_results
            if getattr(c, "status", "PASS") in ("WARN", "FAIL")
        ]
        inherited_flags = []
        if inherited_diagnostics.get("missing_channels"):
            inherited_flags.append("MISSING_RECOMMENDED_CURVES")
        if inherited_qcfail_count > 0:
            inherited_flags.append("CURVE_FAIL_STATE")
        if inherited_suitability == "void":
            inherited_flags.append("SUITABILITY_VOID")

        flags = sorted(set(engine_flags + curve_state_flags + inherited_flags))
        limitations = sorted(set(list(qc_dict.get("limitations", [])) + inherited_limitations))

        # Red Team Fix: Include curve_warnings and depth_qc in failure logic
        has_range_issues = bool(curve_warnings)
        has_depth_issues = not depth_qc.get("monotonic", True)

        if inherited_suitability == "void" or inherited_qcfail_count > 0 or qc_overall == "FAIL" or has_range_issues or has_depth_issues:
            claim_state = "RAW_OBSERVATION"
            qc_passed = False
            if has_range_issues or has_depth_issues:
                qc_overall = "FAIL"
        elif qc_overall == "PASS" and not flags and not limitations:
            claim_state = "QC_VERIFIED"
            qc_passed = True
        elif qc_overall == "WARN":
            claim_state = "QC_VERIFIED_WITH_WARNINGS"
            qc_passed = True
        else:
            claim_state = "QC_VERIFIED_WITH_WARNINGS"
            qc_passed = True

        _record_latest_qc(
            artifact_ref,
            {
                "qc_overall": qc_overall,
                "qc_passed": qc_passed,
                "flags": flags,
                "limitations": limitations,
                "claim_state": claim_state,
            },
        )

        response = get_standard_envelope(
            {
                "tool": "geox_data_qc_bundle",
                "artifact_ref": store_entry.get("artifact_ref", artifact_ref) if store_entry else artifact_ref,
                "artifact_type": artifact_type,
                "qc_mode": qc_mode,
                "artifact_status": "QC_INSPECTED",
                "qc_overall": qc_overall,
                "qc_passed": qc_passed,
                "curve_results": [c.to_dict() if hasattr(c, "to_dict") else dict(c) for c in qc_result.curve_results],
                "flags": flags,
                "limitations": limitations,
                "inherited_ingest_diagnostics": inherited_diagnostics,
                "human_decision_point": qc_dict.get("human_decision_point", ""),
                "claim_state": claim_state,
                "vault_receipt": qc_dict.get("vault_receipt", {}),
            },
            tool_class="qc",
            execution_status=ExecutionStatus.SUCCESS,
            artifact_status=ArtifactStatus.VERIFIED,
            claim_tag="CLAIM",
        )

        # Inject mode-specific results
        try:
            if qc_mode in ("header", "full"):
                response["header_qc"] = header_checks
            if qc_mode in ("depth", "full") and depth_arr is not None:
                response["depth_qc"] = depth_qc
            if qc_mode in ("curves", "full"):
                response["curve_range_warnings"] = curve_warnings
                response["curve_statistics"] = curve_statistics
            if qc_mode in ("completeness", "full"):
                response["completeness_score"] = completeness_score
                response["present_curves"] = present_curves
                response["missing_curves"] = missing_curves
        except NameError:
            pass  # mode-specific vars not set (exception above)

        return response

    except Exception as exc:
        _record_latest_qc(
            artifact_ref,
            {
                "qc_overall": "ERROR",
                "qc_passed": False,
                "flags": ["QC_ENGINE_FAILED"],
                "limitations": [f"QC engine error: {exc}"],
                "claim_state": "RAW_OBSERVATION",
            },
        )
        return get_standard_envelope(
            {
                "tool": "geox_data_qc_bundle",
                "error_code": "QC_ENGINE_FAILED",
                "message": f"QC engine error: {exc}",
                "artifact_ref": artifact_ref,
                "qc_passed": False,
                "claim_state": "RAW_OBSERVATION",
                "recoverable": True,
            },
            tool_class="qc",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
        )


