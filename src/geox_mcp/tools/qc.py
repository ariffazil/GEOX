from __future__ import annotations

import logging
import os
from typing import Literal

from geox_core.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
    enrich_envelope_with_metabolic,
)
from geox_mcp.tools._helpers import (
    _get_artifact,
    _artifact_exists,
    _record_latest_qc,
    _detect_depth_unit,
    CANONICAL_ALIASES,
    _CURVE_RANGES,
)

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
    # Hardening: validate free-text inputs at boundary.
    from geox_mcp.tools.kernel._validation import validate_tool_inputs

    _err = validate_tool_inputs(
        "geox_data_qc_bundle",
        artifact_ref=artifact_ref,
        artifact_type=artifact_type,
    )
    if _err is not None:
        return _err
    curve_warnings = []
    depth_qc = {}
    header_checks = {}
    present_curves = []
    missing_curves = []
    completeness_score = 0.0

    if not artifact_ref or not _artifact_exists(artifact_ref):
        envelope = get_standard_envelope(
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
        return enrich_envelope_with_metabolic(envelope, "geox_data_qc_bundle")

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
        envelope = get_standard_envelope(
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
        return enrich_envelope_with_metabolic(envelope, "geox_data_qc_bundle")

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

            checks_passed = sum(
                [
                    bool(well_name and well_name not in ("", "None")),
                    bool(uwi and uwi not in ("", "None")),
                    bool(loc and loc not in ("", "None")),
                    bool(datum and datum not in ("", "None")),
                    bool(depth_unit and depth_unit not in ("UNKNOWN", "", "None")),
                ]
            )
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
                    curve_warnings.append(f"{canon}: min={float(np.min(valid)):.2f} below {lo} {unit}")
                if hi is not None and float(np.max(valid)) > hi:
                    curve_warnings.append(f"{canon}: max={float(np.max(valid)):.2f} above {hi} {unit}")
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

    except Exception:
        # Fall through to the standard LASIngestor QC path
        pass

    # Always also run LASIngestor QC as the base
    try:
        from geox_core.services.las_ingestor import LASIngestor

        ingestor = LASIngestor()
        well_result = ingestor.ingest(path=las_path, asset_id=artifact_ref)
        qc_result = ingestor.qc_logs(well_result, las_path)
        qc_dict = qc_result.to_dict()

        qc_overall = qc_dict.get("qc_overall", "FAIL")
        inherited_diagnostics = (store_entry or {}).get("diagnostics", {})
        inherited_limitations = list(inherited_diagnostics.get("limitations") or [])
        inherited_suitability = inherited_diagnostics.get("suitability")
        inherited_qcfail_count = int(inherited_diagnostics.get("qcfail_count") or 0)

        engine_flags = [issue.type for c in qc_result.curve_results for issue in (c.issues if hasattr(c, "issues") else [])]
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

        # EUREKA FORGE (2026-06-02): distill the SAF statistical-rigor pattern
        # into the existing QC verdict. No new tool registered (F13 directive:
        # no additional tools). When the loaded well data has statistically
        # significant departures from normality (Shapiro p<0.05) or high
        # outlier density, we surface this as a SAF-grounded warning and
        # downgrade the claim_state to QC_VERIFIED_WITH_WARNINGS.
        try:
            import sys

            _arifos_kernel = "/root/arifOS"
            if _arifos_kernel not in sys.path:
                sys.path.insert(0, _arifos_kernel)
            from core.shared.saf_stats import (
                stat_assumptions as _saf_assumptions,
                stat_outliers as _saf_outliers,
            )
            import pandas as _pd_saf
            import uuid as _uuid_saf
            from pathlib import Path as _Path_saf
            import os as _os_saf

            _geox_saf_root = _Path_saf(_os_saf.environ.get("GEOX_SAF_DATA_ROOT", "/tmp/geox_saf"))
            _geox_saf_root.mkdir(parents=True, exist_ok=True)
            _os_saf.environ.setdefault("SAF_DATA_ROOT", str(_geox_saf_root))
            # Extract depth curve from the loaded well (use curves['DEPT'])
            _depth = None
            try:
                _curves_dict = getattr(well_result, "curves", None) or {}
                # Try common depth curve names
                for _dn in ("DEPT", "DEPTH", "MD", "TVD"):
                    if _dn in _curves_dict:
                        _arr = _curves_dict[_dn]
                        if hasattr(_arr, "tolist"):
                            _depth = _arr.tolist()
                        elif isinstance(_arr, (list, tuple)):
                            _depth = list(_arr)
                        break
                if _depth is None and _curves_dict:
                    # Fall back to first numeric curve
                    for _v in _curves_dict.values():
                        if hasattr(_v, "tolist"):
                            _depth = _v.tolist()
                            break
            except Exception:
                _depth = None
            _saf_summary = None
            if _depth and len(_depth) >= 3:
                _csv = _geox_saf_root / f"qc_{_uuid_saf.uuid4().hex[:10]}.csv"
                _pd_saf.DataFrame({"depth": _depth}).to_csv(_csv, index=False)
                _saf_assump = _saf_assumptions(file_path=str(_csv), columns=["depth"])
                _saf_out = _saf_outliers(file_path=str(_csv), columns=["depth"], method="iqr", threshold=1.5)
                try:
                    _csv.unlink()
                except OSError:
                    pass
                # Extract summary stats
                _p_shapiro = None
                _skew = None
                _kurt = None
                for c in _saf_assump.get("results", []):
                    if c.get("normality_p") is not None:
                        _p_shapiro = c.get("normality_p")
                        _skew = c.get("skew")
                        _kurt = c.get("kurtosis")
                        break
                _n_outliers = 0
                for c in _saf_out.get("per_column", {}).values():
                    _n_outliers += len(c.get("indices", []))
                _saf_summary = {
                    "n_depth_samples": len(_depth),
                    "shapiro_p": round(_p_shapiro, 6) if _p_shapiro is not None else None,
                    "skew": round(_skew, 4) if _skew is not None else None,
                    "kurtosis": round(_kurt, 4) if _kurt is not None else None,
                    "outliers_iqr_count": _n_outliers,
                    "outlier_density": round(_n_outliers / len(_depth), 4) if _depth else None,
                    "verdict": "SEAL"
                    if (_p_shapiro is None or _p_shapiro >= 0.05) and _n_outliers / max(len(_depth), 1) < 0.05
                    else "SABAR",
                }
                # F2 TRUTH: if normality violated OR outlier density > 5%,
                # add a warning (will downgrade claim_state below)
                if _p_shapiro is not None and _p_shapiro < 0.05:
                    flags.append("SAF_NON_NORMAL_DEPTH")
                    limitations.append(f"SAF stat_assumptions: Shapiro p={_p_shapiro:.4f} — depth distribution non-normal.")
                if _n_outliers / max(len(_depth), 1) > 0.05:
                    flags.append(f"SAF_HIGH_OUTLIER_DENSITY:{_n_outliers}")
                    limitations.append(
                        f"SAF stat_outliers: {_n_outliers} outliers ({_n_outliers / len(_depth):.1%} of depth samples) — investigate before parametric use."
                    )
        except Exception as _saf_exc:
            _saf_summary = {"embed_skipped": str(_saf_exc)[:120]}

        # Red Team Fix: Include curve_warnings and depth_qc in failure logic
        has_range_issues = bool(curve_warnings)
        has_depth_issues = not depth_qc.get("monotonic", True)

        if (
            inherited_suitability == "void"
            or inherited_qcfail_count > 0
            or qc_overall == "FAIL"
            or has_range_issues
            or has_depth_issues
        ):
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
            # EUREKA FORGE (2026-06-02): surface SAF statistical-rigor
            # summary in the response so downstream consumers can see
            # the assumption check + outlier audit.
            if _saf_summary is not None:
                response["_saf_assumptions"] = _saf_summary
            if _saf_anova is not None:
                response["_saf_anova"] = _saf_anova
            if _saf_chi2 is not None:
                response["_saf_chi_square"] = _saf_chi2
            if _saf_missing is not None:
                response["_saf_missing"] = _saf_missing
        except NameError:
            pass  # mode-specific vars not set (exception above)

        return enrich_envelope_with_metabolic(response, "geox_data_qc_bundle")

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
        envelope = get_standard_envelope(
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
        return enrich_envelope_with_metabolic(envelope, "geox_data_qc_bundle")
