from __future__ import annotations

import logging
import os
from typing import Any, Literal

from geox_core.enums.statuses import (
    ArtifactStatus,
    ExecutionStatus,
    GovernanceStatus,
    enrich_envelope_with_metabolic,
    get_standard_envelope,
)
from geox_mcp.tools._helpers import (
    _CURVE_RANGES,
    CANONICAL_ALIASES,
    _artifact_exists,
    _detect_depth_unit,
    _get_artifact,
    _record_latest_qc,
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
            import os as _os_saf
            import uuid as _uuid_saf
            from pathlib import Path as _Path_saf

            import pandas as _pd_saf
            from core.shared.saf_stats import (
                stat_assumptions as _saf_assumptions,
            )
            from core.shared.saf_stats import (
                stat_outliers as _saf_outliers,
            )

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

        # EUREKA FORGE (2026-06-03): group-wise one-way ANOVA + Welch ANOVA.
        # When the artifact has a categorical grouping column (e.g. facies,
        # well_id, region) and >=2 numeric curves, run one-way ANOVA on
        # each numeric curve ~ group_col. The federated saf_stats.stat_anova
        # uses pingouin/scipy and returns F, p, eta^2, plus optional
        # Tukey HSD post-hoc. This complements the univariate (depth
        # distribution) and bivariate (cross-curve correlation) forges:
        # the third axis of petrophysical QC is "do these curves differ
        # by group?" — e.g. does GR differ across facies? Does RHOB
        # differ by well?
        _saf_anova = None
        try:
            import sys as _sys_aov

            _arifos_kernel_aov = "/root/arifOS"
            if _arifos_kernel_aov not in _sys_aov.path:
                _sys_aov.path.insert(0, _arifos_kernel_aov)
            from core.shared.saf_stats import stat_anova as _saf_anova_fn

            # Detect a categorical grouping column from the artifact.
            # Convention: caller passes group_col via the artifact's
            # "_saf_group_col" tag, or the function falls back to
            # a column named exactly one of: "facies", "well_id",
            # "region", "zone", "group".
            _group_col_aov = (
                raw_curves.get("_saf_group_col")  # caller hint
                if isinstance(raw_curves, dict)
                else None
            )
            if not _group_col_aov:
                for _candidate in ("facies", "well_id", "region", "zone", "group"):
                    if _candidate in (raw_curves or {}):
                        _group_col_aov = _candidate
                        break
            if _group_col_aov and _group_col_aov in (raw_curves or {}):
                _group_vals = raw_curves[_group_col_aov]
                if _group_vals is not None and len(_group_vals) >= 6:
                    import os as _os_aov
                    import uuid as _uuid_aov
                    from pathlib import Path as _Path_aov

                    import pandas as _pd_aov

                    _aov_root = _Path_aov(_os_aov.environ.get("GEOX_SAF_DATA_ROOT", "/tmp/geox_saf"))
                    _aov_root.mkdir(parents=True, exist_ok=True)
                    _os_aov.environ["SAF_DATA_ROOT"] = str(_aov_root)
                    _aov_csv = _aov_root / (f"anova_{_uuid_aov.uuid4().hex[:10]}.csv")
                    _aov_df: dict = {_group_col_aov: list(_group_vals)}
                    for k in raw_curves:
                        if k != _group_col_aov and k.upper() not in {"DEPT", "DEPTH", "MD"} and raw_curves.get(k) is not None:
                            _v = raw_curves[k]
                            if isinstance(_v, list) and len(_v) == len(_group_vals):
                                _aov_df[k] = _v
                    _pd_aov.DataFrame(_aov_df).to_csv(_aov_csv, index=False)
                    _aov_results: dict = {
                        "group_col": _group_col_aov,
                        "n_groups": None,
                        "per_curve": {},
                        "significant_curves": [],
                    }
                    _curves_tested = [
                        k
                        for k in _aov_df
                        if k != _group_col_aov and _pd_aov.api.types.is_numeric_dtype(_pd_aov.Series(_aov_df[k]).dtype)
                    ]
                    for _curve_aov in _curves_tested:
                        try:
                            _aov_raw = _saf_anova_fn(
                                str(_aov_csv),
                                value_col=_curve_aov,
                                group_col=_group_col_aov,
                                parametric=True,
                                welch=False,
                                post_hoc=True,
                            )
                            # Federated stat_anova returns the F stat nested
                            # under anova_table.F (as a dict mapping term
                            # names to F values), with p_value at the top
                            # level. Upstream saf_stats returns the F
                            # stat at result.F. Handle both.
                            _aov_p = _aov_raw.get("p_value") if isinstance(_aov_raw, dict) else None
                            _aov_F = None
                            _aov_eta2 = None
                            _aov_k = None
                            if isinstance(_aov_raw, dict):
                                _aov_inner = _aov_raw.get("result", _aov_raw)
                                if isinstance(_aov_inner, dict):
                                    _aov_F = _aov_inner.get("F")
                                    _aov_eta2 = _aov_inner.get("eta_squared")
                                    _aov_k = _aov_inner.get("k_groups")
                                if _aov_F is None:
                                    _aov_table = _aov_raw.get("anova_table", {}) or {}
                                    _F_map = _aov_table.get("F", {}) or {}
                                    # F values are keyed by term names
                                    # like "C(facies)"; pick the first.
                                    if isinstance(_F_map, dict) and _F_map:
                                        _aov_F = next(iter(_F_map.values()))
                                if _aov_eta2 is None:
                                    _aov_eta2 = _aov_raw.get("eta_sq")
                                if _aov_k is None:
                                    _k_val = _aov_raw.get("n_groups")
                                    if _k_val is None:
                                        # Count unique groups from the data.
                                        _k_val = len(set(str(x) for x in _group_vals))
                                    _aov_k = _k_val
                            _aov_results["n_groups"] = _aov_k
                            _aov_results["per_curve"][_curve_aov] = {
                                "F": _aov_F,
                                "p_value": _aov_p,
                                "eta_squared": _aov_eta2,
                                "k_groups": _aov_k,
                                "significant_at_0_05": (_aov_p is not None and float(_aov_p) < 0.05),
                            }
                            if _aov_p is not None and float(_aov_p) < 0.05:
                                _aov_results["significant_curves"].append(_curve_aov)
                        except Exception as _curve_aov_exc:
                            _aov_results["per_curve"][_curve_aov] = {"embed_skipped": str(_curve_aov_exc)[:120]}
                    try:
                        _aov_csv.unlink()
                    except OSError:
                        pass
                    if _aov_results["significant_curves"]:
                        limitaciones.append(
                            f"SAF stat_anova: {_aov_results['n_groups']}-group ANOVA found significant differences "
                            f"(p<0.05) in {len(_aov_results['significant_curves'])} curve(s) "
                            f"by {_group_col_aov}: {', '.join(_aov_results['significant_curves'])}."
                        )
                        flags.append("SAF_ANOVA_SIGNIFICANT_GROUPS")
                    _saf_anova = _aov_results
        except Exception as _saf_aov_exc:
            _saf_anova = {"embed_skipped": str(_saf_aov_exc)[:120]}

        # EUREKA FORGE (2026-06-03): data-quality MCAR audit via stat_missing.
        # Per-column missing counts + Little's MCAR chi-square test. A
        # non-random missingness pattern means downstream parametric
        # analysis is biased. Compatible with both federated (dict-format
        # per_column) and upstream (list-format) saf_stats.stat_missing.
        _saf_missing = None
        try:
            import sys as _sys_mis

            _arifos_kernel_mis = "/root/arifOS"
            if _arifos_kernel_mis not in _sys_mis.path:
                _sys_mis.path.insert(0, _arifos_kernel_mis)
            import os as _os_mis
            import uuid as _uuid_mis
            from pathlib import Path as _Path_mis

            import pandas as _pd_mis
            from core.shared.saf_stats import stat_missing as _saf_missing_fn

            _mis_root = _Path_mis(_os_mis.environ.get("GEOX_SAF_DATA_ROOT", "/tmp/geox_saf"))
            _mis_root.mkdir(parents=True, exist_ok=True)
            _os_mis.environ["SAF_DATA_ROOT"] = str(_mis_root)
            _mis_csv = _mis_root / (f"missing_{_uuid_mis.uuid4().hex[:10]}.csv")
            _mis_df: dict = {}
            for _k_mis, _v_mis in (raw_curves or {}).items():
                if _k_mis.upper() not in {"DEPT", "DEPTH", "MD"} and _v_mis is not None and isinstance(_v_mis, list):
                    _mis_df[_k_mis] = _v_mis
            if _mis_df:
                _pd_mis.DataFrame(_mis_df).to_csv(_mis_csv, index=False)
                _mis_raw = _saf_missing_fn(str(_mis_csv))
                try:
                    _mis_csv.unlink()
                except OSError:
                    pass
                _mis_per_col_raw = _mis_raw.get("per_column", {}) if isinstance(_mis_raw, dict) else {}
                _mis_mcar = _mis_raw.get("littles_mcar_approx", {}) if isinstance(_mis_raw, dict) else {}
                _mis_per_col_list = []
                _mis_high_missing = []
                if isinstance(_mis_per_col_raw, dict):
                    for _col_name_mis, _col_info_mis in _mis_per_col_raw.items():
                        if isinstance(_col_info_mis, dict):
                            _missing = _col_info_mis.get("missing", 0)
                            _pct = _col_info_mis.get("pct", 0.0)
                        else:
                            _missing, _pct = 0, 0.0
                        _mis_per_col_list.append(
                            {
                                "column": _col_name_mis,
                                "n_missing": _missing,
                                "pct_missing": _pct,
                            }
                        )
                        if _pct > 10.0:
                            _mis_high_missing.append(_col_name_mis)
                elif isinstance(_mis_per_col_raw, list):
                    _mis_per_col_list = _mis_per_col_raw
                    _mis_high_missing = [c.get("column") for c in _mis_per_col_raw if c.get("pct_missing", 0) > 10.0]
                _mcar_rejected = _mis_mcar.get("verdict_at_alpha_0_05", "") == "False"
                _saf_missing = {
                    "n_rows": (_mis_raw.get("n_rows") if isinstance(_mis_raw, dict) else None),
                    "total_missing": (_mis_raw.get("total_missing") if isinstance(_mis_raw, dict) else None),
                    "pct_missing_total": (_mis_raw.get("pct_missing_total") if isinstance(_mis_raw, dict) else None),
                    "per_column": _mis_per_col_list,
                    "littles_mcar_approx": _mis_mcar,
                    "high_missing_columns": _mis_high_missing,
                    "mcar_rejected": _mcar_rejected,
                    "interpretation": (
                        "missingness is NOT random (MCAR rejected) — downstream analysis may be biased"
                        if _mcar_rejected
                        else "missingness consistent with MCAR"
                    ),
                }
                if _mis_high_missing:
                    limitaciones.append(
                        f"SAF stat_missing: {len(_mis_high_missing)} curve(s) have >10% missing: {', '.join(_mis_high_missing)}"
                    )
                    flags.append("SAF_HIGH_MISSING")
                if _mcar_rejected:
                    limitaciones.append(
                        "SAF stat_missing: Little's MCAR test rejected "
                        f"(chi2={_mis_mcar.get('chi2_approx', '?')}, "
                        "p<0.05) — missingness is systematic, not random"
                    )
                    flags.append("SAF_MCAR_REJECTED")
        except Exception as _saf_mis_exc:
            _saf_missing = {"embed_skipped": str(_saf_mis_exc)[:120]}

        # EUREKA FORGE (2026-06-03): categorical independence via chi-square.

        # EUREKA FORGE (2026-06-03): categorical independence via chi-square.
        # When the artifact has TWO categorical columns (e.g. facies x
        # region, lithology x well_id), run chi-square test of
        # independence via saf_stats.stat_chi_square. Surfaces chi2,
        # p_value, dof, Cramér's V (effect size), and Fisher's exact
        # (for 2x2 tables). Answers: "is facies X independent of
        # region Y, or are they correlated?"
        _saf_chi2 = None
        try:
            import sys as _sys_chi

            _arifos_kernel_chi = "/root/arifOS"
            if _arifos_kernel_chi not in _sys_chi.path:
                _sys_chi.path.insert(0, _arifos_kernel_chi)
            from core.shared.saf_stats import stat_chi_square as _saf_chi2_fn

            # Find two categorical columns. Auto-detect from: facies,
            # lithology, region, zone, well_id, formation, group.
            _cat_candidates_chi = (
                "facies",
                "lithology",
                "region",
                "zone",
                "well_id",
                "formation",
                "group",
            )
            _cat_cols_chi = [
                c
                for c in _cat_candidates_chi
                if c in (raw_curves or {}) and raw_curves.get(c) is not None and len(raw_curves.get(c)) >= 6
            ]
            if len(_cat_cols_chi) >= 2:
                import os as _os_chi
                import uuid as _uuid_chi
                from pathlib import Path as _Path_chi

                import pandas as _pd_chi

                _chi2_root = _Path_chi(_os_chi.environ.get("GEOX_SAF_DATA_ROOT", "/tmp/geox_saf"))
                _chi2_root.mkdir(parents=True, exist_ok=True)
                _os_chi.environ["SAF_DATA_ROOT"] = str(_chi2_root)
                _chi2_csv = _chi2_root / (f"chi2_{_uuid_chi.uuid4().hex[:10]}.csv")
                _chi2_df_chi: dict = {c: list(raw_curves[c]) for c in _cat_cols_chi[:2]}
                _pd_chi.DataFrame(_chi2_df_chi).to_csv(_chi2_csv, index=False)
                _chi2_raw = _saf_chi2_fn(
                    str(_chi2_csv),
                    var_a=_cat_cols_chi[0],
                    var_b=_cat_cols_chi[1],
                    test="independence",
                )
                try:
                    _chi2_csv.unlink()
                except OSError:
                    pass
                # Federated saf_stats returns the F1-F13 envelope with
                # chi2, p_value, dof, cramers_v, fisher_exact at top
                # level. Upstream saf_stats nests under "result".
                _chi2_p = _chi2_raw.get("p_value") if isinstance(_chi2_raw, dict) else None
                _chi2_chi2 = _chi2_raw.get("chi2") if isinstance(_chi2_raw, dict) else None
                _chi2_dof = _chi2_raw.get("dof") if isinstance(_chi2_raw, dict) else None
                _chi2_v = _chi2_raw.get("cramers_v") if isinstance(_chi2_raw, dict) else None
                _chi2_fisher = _chi2_raw.get("fisher_exact") if isinstance(_chi2_raw, dict) else None
                _chi2_table_shape = (
                    _chi2_raw.get("n_rows"),
                    _chi2_raw.get("n_cols"),
                )
                _chi2_summary = {
                    "var_a": _cat_cols_chi[0],
                    "var_b": _cat_cols_chi[1],
                    "test": "chi_square_independence",
                    "chi2": _chi2_chi2,
                    "dof": _chi2_dof,
                    "p_value": _chi2_p,
                    "cramers_v": _chi2_v,
                    "fisher_exact": _chi2_fisher,
                    "table_shape": _chi2_table_shape,
                    "significant_at_0_05": (_chi2_p is not None and float(_chi2_p) < 0.05),
                }
                if _chi2_p is not None and float(_chi2_p) < 0.05:
                    _chi2_summary["interpretation"] = f"{_cat_cols_chi[0]} and {_cat_cols_chi[1]} are NOT independent"
                    limitaciones.append(
                        f"SAF stat_chi_square: {_cat_cols_chi[0]} and {_cat_cols_chi[1]} "
                        f"are not independent (chi2={_chi2_chi2}, p={_chi2_p}, "
                        f"Cramér's V={_chi2_v})."
                    )
                    flags.append("SAF_CHI_SQUARE_DEPENDENT")
                else:
                    _chi2_summary["interpretation"] = f"{_cat_cols_chi[0]} and {_cat_cols_chi[1]} are independent"
                _saf_chi2 = _chi2_summary
        except Exception as _saf_chi2_exc:
            _saf_chi2 = {"embed_skipped": str(_saf_chi2_exc)[:120]}
        except Exception as _saf_aov_exc:
            _saf_anova = {"embed_skipped": str(_saf_aov_exc)[:120]}

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

            # EUREKA FORGE (2026-06-03): cross-curve correlation QC.
            # When in 'full' or 'cross_curve' mode with >=2 numeric curves,
            # compute Pearson + Spearman pairwise correlations between
            # curves. Univariate QC (already done) checks each curve in
            # isolation; this adds bivariate coherence — the petrophysical
            # equivalent of asking "do GR and RHOB move together as
            # theory predicts?". Strong linear relationships are flagged
            # for redundancy; near-zero correlations between curves
            # that should be related (e.g. NPHI vs RHOB in clean sands)
            # are flagged for further review.
            try:
                import sys as _sys_xc

                _arifos_kernel_xc = "/root/arifOS"
                if _arifos_kernel_xc not in _sys_xc.path:
                    _sys_xc.path.insert(0, _arifos_kernel_xc)
                import os as _os_xc
                import uuid as _uuid_xc
                from pathlib import Path as _Path_xc

                import pandas as _pd_xc
                from core.shared.saf_stats import (
                    stat_correlate as _saf_correlate,
                )

                _geox_saf_root_xc = _Path_xc(_os_xc.environ.get("GEOX_SAF_DATA_ROOT", "/tmp/geox_saf"))
                _geox_saf_root_xc.mkdir(parents=True, exist_ok=True)
                _os_xc.environ.setdefault("SAF_DATA_ROOT", str(_geox_saf_root_xc))

                if qc_mode in ("full", "cross_curve"):
                    _numeric_curves: dict[str, Any] = {
                        k: np.asarray(v, dtype=float)
                        for k, v in raw_curves.items()
                        if k.upper() not in {"DEPT", "DEPTH", "MD"} and v is not None and len(v) >= 5
                    }
                    _numeric_curves = {k: v for k, v in _numeric_curves.items() if not np.all(np.isnan(v))}
                    if len(_numeric_curves) >= 2:
                        _curves_csv = _geox_saf_root_xc / (f"xcurve_{_uuid_xc.uuid4().hex[:10]}.csv")
                        _pd_xc.DataFrame(_numeric_curves).to_csv(_curves_csv, index=False)
                        _mnems = sorted(_numeric_curves.keys())
                        _pearson_matrix: dict[str, dict[str, float | None]] = {m1: {} for m1 in _mnems}
                        _spearman_matrix: dict[str, dict[str, float | None]] = {m1: {} for m1 in _mnems}
                        _pvalue_matrix: dict[str, dict[str, float | None]] = {m1: {} for m1 in _mnems}
                        _high_corr_pairs: list[dict[str, Any]] = []
                        for i, m1 in enumerate(_mnems):
                            for j, m2 in enumerate(_mnems):
                                if j <= i:
                                    continue
                                _r_p = _saf_correlate(str(_curves_csv), m1, m2, method="pearson")
                                _r_s = _saf_correlate(str(_curves_csv), m1, m2, method="spearman")

                                # Federated saf_stats returns a F1-F13 wrapped
                                # envelope with fields at the top level (no
                                # "result" nesting). Fall back to nested form
                                # for upstream-style callers.
                                def _pick_corr(d, key):
                                    if not isinstance(d, dict):
                                        return None
                                    if key in d:
                                        return d[key]
                                    inner = d.get("result")
                                    if isinstance(inner, dict) and key in inner:
                                        return inner[key]
                                    return None

                                _rp = _pick_corr(_r_p, "r")
                                _pp = _pick_corr(_r_p, "p_value")
                                _rs = _pick_corr(_r_s, "r")
                                _pearson_matrix[m1][m2] = round(float(_rp), 4) if _rp is not None else None
                                _spearman_matrix[m1][m2] = round(float(_rs), 4) if _rs is not None else None
                                _pvalue_matrix[m1][m2] = round(float(_pp), 6) if _pp is not None else None
                                if _rp is not None and abs(float(_rp)) >= 0.95:
                                    _high_corr_pairs.append(
                                        {
                                            "curve_a": m1,
                                            "curve_b": m2,
                                            "r_pearson": round(float(_rp), 4),
                                            "r_spearman": (round(float(_rs), 4) if _rs is not None else None),
                                            "p_value": _pp,
                                            "interpretation": ("redundant curves — consider dropping one"),
                                        }
                                    )
                                if _rp is not None and abs(_rp) >= 0.95:
                                    _high_corr_pairs.append(
                                        {
                                            "curve_a": m1,
                                            "curve_b": m2,
                                            "r_pearson": round(_rp, 4),
                                            "r_spearman": (round(_rs, 4) if _rs is not None else None),
                                            "p_value": _pp,
                                            "interpretation": ("redundant curves — consider dropping one"),
                                        }
                                    )
                        try:
                            _curves_csv.unlink()
                        except OSError:
                            pass
                        if _high_corr_pairs:
                            limitations.append(
                                f"SAF stat_correlate: {len(_high_corr_pairs)} "
                                "curve pair(s) with |r|>=0.95 (potential redundancy)."
                            )
                            flags.append("SAF_REDUNDANT_CURVES")
                        response["_saf_cross_curve"] = {
                            "n_curves": len(_mnems),
                            "curves": _mnems,
                            "pearson": _pearson_matrix,
                            "spearman": _spearman_matrix,
                            "p_value": _pvalue_matrix,
                            "high_correlation_pairs": _high_corr_pairs,
                            "redundancy_threshold": 0.95,
                        }
            except Exception as _saf_xc_exc:
                response["_saf_cross_curve_skipped"] = str(_saf_xc_exc)[:120]
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
