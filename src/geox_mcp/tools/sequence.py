"""
GEOX Sequence Interpret — Unified Stratigraphy Engine
═══════════════════════════════════════════════════════
Forged from the energy of 7 predecessor tools:
  geox_well_compute_gr_bins
  geox_well_build_packages
  geox_well_infer_seq_strat
  geox_well_analyze_sequence
  geox_stratigraphy_run_pipeline
  geox_stratigraphy_preview_config
  geox_section_interpret_correlation

One entry point. One clear contract. No phantom surface.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Literal

import numpy as np
import yaml

from geox_core.enums.statuses import (
    ArtifactStatus,
    ExecutionStatus,
    GovernanceStatus,
    get_standard_envelope,
    enrich_envelope_with_metabolic,
)
from geox_mcp.tools._helpers import (
    _get_artifact,
    _artifact_exists,
    _register_artifact,
    _classify_gr_motif,
    CANONICAL_ALIASES,
)

logger = logging.getLogger("geox.sequence")

TOOL_NAME = "geox_sequence_interpret"


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED HELPERS (forged from well.py + section.py energy)
# ═══════════════════════════════════════════════════════════════════════════════


def _source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_interval(*, zone_top: float, zone_base: float, bin_size_m: float | None = None) -> tuple[bool, str, str]:
    values = [zone_top, zone_base]
    if bin_size_m is not None:
        values.append(bin_size_m)
    if not all(np.isfinite(v) for v in values):
        return False, "NONFINITE_INPUT", "Depth interval and bin size must be finite numbers."
    if zone_top >= zone_base:
        return False, "INVALID_DEPTH_INTERVAL", "zone_top must be shallower than zone_base."
    if bin_size_m is not None:
        interval = zone_base - zone_top
        if bin_size_m <= 0:
            return False, "INVALID_BIN_SIZE", "bin_size_m must be greater than zero."
        if bin_size_m > interval:
            return False, "BIN_SIZE_EXCEEDS_INTERVAL", "bin_size_m cannot exceed interval thickness."
    return True, "", ""


def _gr_physics_guard(gr: np.ndarray, *, min_samples: int = 3) -> dict[str, Any]:
    valid = gr[np.isfinite(gr)]
    violations: list[str] = []
    if valid.size < min_samples:
        violations.append("INSUFFICIENT_VALID_GR_SAMPLES")
    if valid.size and float(np.nanmin(valid)) < 0:
        violations.append("GR_BELOW_PHYSICAL_RANGE")
    if valid.size and float(np.nanmax(valid)) > 300:
        violations.append("GR_ABOVE_EXPECTED_RANGE")
    return {
        "guard_passed": not violations,
        "physics_version": "geox-sequence-v2026.05.22",
        "checked": ["finite_samples", "GR_expected_range_0_300_gAPI"],
        "violations": violations,
        "valid_samples": int(valid.size),
    }


def _interpretation_limitations(source_kind: str, multi_curve: bool = False) -> list[str]:
    limitations = [
        "GR motif is a derived proxy, not direct lithology.",
        (
            "Depositional environment and sequence surfaces require calibration with core, "
            "cuttings, biostratigraphy, seismic, or field context before decision use."
        ),
    ]
    if source_kind.upper() in {"LAS", "CSV"}:
        limitations.append(
            "Tool used the GR curve only; density, neutron, resistivity, sonic, core, "
            "and pressure evidence were not consumed by this sequence tool."
            if not multi_curve
            else "Multi-curve mode enabled. GR primary; RHOB, RT, NPHI secondary."
        )
    return limitations


def _load_las_or_csv(source: str) -> tuple[np.ndarray, np.ndarray, dict]:
    """Load depth and GR from LAS or CSV. Returns (depth, gr, metadata)."""
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {source}")
    if not path.is_file():
        raise ValueError(f"Source is not a file: {source}")

    ext = path.suffix.lower()
    if ext in (".las", ".LAS"):
        try:
            import lasio
            las = lasio.read(str(path))
            depth = las.index
            if hasattr(depth, "values"):
                depth = depth.values
            depth = depth.astype(float)
            for alias in ["GR", "GRC", "SGR", "CGR", "GAPI", "GAMMA", "GAMMA_RAY"]:
                if alias in las.keys():
                    gr = las[alias]
                    if hasattr(gr, "values"):
                        gr = gr.values
                    gr = gr.astype(float)
                    break
            else:
                gr_name = list(las.keys())[0]
                gr = las[gr_name]
                if hasattr(gr, "values"):
                    gr = gr.values
                gr = gr.astype(float)
            meta = {
                "well": las.well.WELL.value if hasattr(las.well, "WELL") else path.stem,
                "source": str(path),
                "format": "LAS",
                "source_sha256": _source_hash(path),
                "n_samples": len(depth),
                "curves": list(las.keys()),
                "start_depth": float(depth[0]),
                "end_depth": float(depth[-1]),
            }
            finite = np.isfinite(depth) & np.isfinite(gr)
            depth = depth[finite]
            gr = gr[finite]
            if len(depth) < 3:
                raise ValueError("Source has fewer than 3 finite depth/GR samples.")
            diffs = np.diff(depth)
            if not (np.all(diffs > 0) or np.all(diffs < 0)):
                raise ValueError("Depth samples must be strictly monotonic before sequence analysis.")
            if np.all(diffs < 0):
                depth = depth[::-1]
                gr = gr[::-1]
            meta["valid_gr_samples"] = int(len(gr))
            return depth, gr, meta
        except ImportError as exc:
            raise ImportError("lasio is required for LAS files: pip install lasio") from exc

    elif ext in (".csv", ".CSV", ".txt"):
        import csv
        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            raise ValueError(f"Empty CSV: {source}")
        cols = list(rows[0].keys())
        depth_col = next((c for c in cols if c.lower() in ("depth", "dept", "md", "td")), cols[0])
        gr_col = next((c for c in cols if c.lower() in ("gr", "grc", "sgr", "gamma", "gamma_ray")), cols[1] if len(cols) > 1 else cols[0])
        depth = np.array([float(r[depth_col]) for r in rows], dtype=float)
        gr = np.array([float(r[gr_col]) for r in rows], dtype=float)
        meta = {
            "well": path.stem,
            "source": str(path),
            "format": "CSV",
            "source_sha256": _source_hash(path),
            "n_samples": len(depth),
            "columns": cols,
            "depth_column": depth_col,
            "gr_column": gr_col,
        }
        finite = np.isfinite(depth) & np.isfinite(gr)
        depth = depth[finite]
        gr = gr[finite]
        if len(depth) < 3:
            raise ValueError("Source has fewer than 3 finite depth/GR samples.")
        diffs = np.diff(depth)
        if not (np.all(diffs > 0) or np.all(diffs < 0)):
            raise ValueError("Depth samples must be strictly monotonic before sequence analysis.")
        if np.all(diffs < 0):
            depth = depth[::-1]
            gr = gr[::-1]
        meta["valid_gr_samples"] = int(len(gr))
        return depth, gr, meta
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _error_envelope(error_code: str, message: str, diagnostics: dict | None = None) -> dict[str, Any]:
    return get_standard_envelope(
        primary_artifact={"tool": TOOL_NAME, "error_code": error_code, "message": message, "recoverable": True},
        tool_class="compute",
        execution_status=ExecutionStatus.ERROR,
        governance_status=GovernanceStatus.HOLD,
        artifact_status=ArtifactStatus.REJECTED,
        claim_tag="HYPOTHESIS",
        claim_state="NO_VALID_EVIDENCE",
        uncertainty="High",
        diagnostics=diagnostics or {},
        physics_guard={"guard_passed": False, "physics_version": "geox-sequence-v2026.05.22", "violations": [error_code]},
        humility_score=1.0,
        perception_class="HYPOTHESIS",
        evidence_tag="SOURCE_UNRESOLVED",
        canon_9_touched=["GR"],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# WORKFLOW: single_well (absorbs well_compute_gr_bins + build_packages + infer_seq_strat + analyze_sequence)
# ═══════════════════════════════════════════════════════════════════════════════


async def _workflow_single_well(
    source: str,
    zone_top: float,
    zone_base: float,
    depo_env_code: str,
    bin_size_m: float,
    min_package_thickness_m: float,
    p50_shift_api: float,
    gr_cutoff_api: float,
    detail_level: Literal["bins", "packages", "full"],
) -> dict[str, Any]:
    ok, error_code, message = _validate_interval(zone_top=zone_top, zone_base=zone_base, bin_size_m=bin_size_m)
    if not ok:
        return _error_envelope(error_code, message)

    try:
        depth, gr, meta = _load_las_or_csv(source)
    except Exception as e:
        return _error_envelope("SOURCE_LOAD_FAILED", str(e), {"source": source})

    physics_guard = _gr_physics_guard(gr)
    if not physics_guard["guard_passed"]:
        return _error_envelope(
            "GR_PHYSICS_GUARD_FAILED",
            "GR samples failed finite/range checks. Run ingest + QC before interpretation.",
            {"source": source, "physics_guard": physics_guard},
        )

    from geox_core.well.tools.sensing import compute_gr_bins
    from geox_core.well.tools.packages import build_packages
    from geox_core.well.tools.seqstrat import infer_seq_strat, DEPO_ENV_SYSTEMS_TRACTS

    depo_env_code = str(depo_env_code or "").upper()
    if depo_env_code not in DEPO_ENV_SYSTEMS_TRACTS:
        return _error_envelope(
            "UNKNOWN_DEPOSITIONAL_ENVIRONMENT",
            "depo_env_code must be one of the supported GEOX sequence environments.",
            diagnostics={"allowed": sorted(DEPO_ENV_SYSTEMS_TRACTS.keys())},
        )

    # L1
    bins = compute_gr_bins(depth, gr, zone_top, zone_base, bin_size_m)
    usable_bins = [b for b in bins if b.get("p50") is not None]
    if not usable_bins:
        return _error_envelope(
            "NO_USABLE_BINS",
            "Requested interval produced no usable GR bins.",
            {"source_depth_range": [float(depth[0]), float(depth[-1])], "requested_interval": [zone_top, zone_base]},
        )

    if detail_level == "bins":
        return get_standard_envelope(
            primary_artifact={
                "tool": TOOL_NAME,
                "workflow": "single_well",
                "detail_level": "bins",
                "well": meta["well"],
                "source": source,
                "source_sha256": meta.get("source_sha256", ""),
                "zone_top": zone_top,
                "zone_base": zone_base,
                "bin_size_m": bin_size_m,
                "n_bins": len(bins),
                "n_usable_bins": len(usable_bins),
                "bins": bins,
                "metadata": meta,
                "limitations": _interpretation_limitations(meta.get("format", "unknown")),
            },
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="COMPUTED",
            claim_tag="CLAIM",
            claim_state="DERIVED_CANDIDATE",
            uncertainty="Moderate",
            evidence_refs=[meta.get("source_sha256", source)],
            physics_guard=physics_guard,
            humility_score=round(1.0 - min(1.0, len(usable_bins) / max(len(bins), 1)), 4),
            perception_class="DERIVED",
            evidence_tag="EVIDENCE_DIRECT",
            canon_9_touched=["GR"],
        )

    # L2
    packages = build_packages(bins, min_package_thickness_m, p50_shift_api)
    if not packages:
        return _error_envelope(
            "NO_PACKAGES_BUILT",
            "GR bins did not meet package thickness/coherence requirements.",
            {"n_bins": len(bins), "n_usable_bins": len(usable_bins)},
        )

    if detail_level == "packages":
        return get_standard_envelope(
            primary_artifact={
                "tool": TOOL_NAME,
                "workflow": "single_well",
                "detail_level": "packages",
                "well": meta["well"],
                "n_packages": len(packages),
                "packages": packages,
                "stacking_patterns": list(set(p.get("stacking_pattern", "MIXED") for p in packages)),
                "limitations": _interpretation_limitations(meta.get("format", "unknown")),
            },
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="COMPUTED",
            claim_tag="CLAIM",
            claim_state="DERIVED_CANDIDATE",
            uncertainty="Moderate",
            evidence_refs=[meta.get("source_sha256", source)],
            physics_guard=physics_guard,
            perception_class="DERIVED",
            evidence_tag="INTERPRET_FROM_LITHOLOGY",
            canon_9_touched=["GR"],
        )

    # L3
    seq_strat = infer_seq_strat(packages, depo_env_code, gr_cutoff_api)
    if not seq_strat.get("systems_tracts"):
        return _error_envelope("NO_SYSTEMS_TRACTS", "Package evidence was insufficient for sequence stratigraphy inference.")

    return get_standard_envelope(
        primary_artifact={
            "tool": TOOL_NAME,
            "workflow": "single_well",
            "detail_level": "full",
            "well": meta["well"],
            "source": source,
            "source_sha256": meta.get("source_sha256", ""),
            "metadata": meta,
            "n_bins": len(bins),
            "n_usable_bins": len(usable_bins),
            "n_packages": len(packages),
            "bins": bins,
            "packages": packages,
            "systems_tracts": seq_strat["systems_tracts"],
            "surfaces": seq_strat["surfaces"],
            "motif_summary": seq_strat.get("motif_summary", {}),
            "depo_env_code": depo_env_code,
            "depo_context": seq_strat.get("depo_context", "unknown"),
            "limitations": _interpretation_limitations(meta.get("format", "unknown")),
        },
        tool_class="compute",
        execution_status="SUCCESS",
        governance_status="QUALIFY",
        artifact_status="DRAFT",
        claim_tag="HYPOTHESIS",
        claim_state="INTERPRETED",
        uncertainty="High",
        evidence_refs=[meta.get("source_sha256", source)],
        physics_guard=physics_guard,
        humility_score=0.75,
        perception_class="HYPOTHESIS",
        evidence_tag="INTERPRET_FROM_LITHOLOGY",
        canon_9_touched=["GR"],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# WORKFLOW: project (absorbs stratigraphy_run_pipeline + stratigraphy_preview_config)
# ═══════════════════════════════════════════════════════════════════════════════


async def _workflow_project(project_yaml: str, output_dir: str | None) -> dict[str, Any]:
    try:
        config_dict = yaml.safe_load(project_yaml)
    except Exception as e:
        return _error_envelope("INVALID_YAML", f"Invalid YAML: {e}")

    try:
        from geox_core.well.stratigraphy.config import ProjectConfig, WellSource, ProjectInterval
        wells = [WellSource(**w) for w in config_dict.get("wells", [])]
        intervals = {}
        for well_id, ivls in config_dict.get("intervals", {}).items():
            intervals[well_id] = [ProjectInterval(**i) for i in ivls]

        config = ProjectConfig(
            project=config_dict.get("project", "Untitled"),
            bin_size_m=config_dict.get("bin_size_m", 10.0),
            min_package_thickness_m=config_dict.get("min_package_thickness_m", 20.0),
            p50_shift_thresh_gapi=config_dict.get("p50_shift_thresh_gapi", 15.0),
            gr_cut_api=config_dict.get("gr_cut_api", 75.0),
            gr_min_api=config_dict.get("gr_min_api", 0.0),
            gr_max_api=config_dict.get("gr_max_api", 150.0),
            gr_sand_api=config_dict.get("gr_sand_api", 35.0),
            gr_silt_api=config_dict.get("gr_silt_api", 65.0),
            gr_shaly_api=config_dict.get("gr_shaly_api", 90.0),
            well_order=config_dict.get("well_order", []),
            wells=wells,
            intervals=intervals,
            output_dir=output_dir or config_dict.get("output_dir", "/tmp/stratigraphy_output"),
            dpi=config_dict.get("dpi", 200),
            dpi_correlation=config_dict.get("dpi_correlation", 180),
        )
    except Exception as e:
        return _error_envelope("CONFIG_VALIDATION_ERROR", str(e))

    from geox_core.well.stratigraphy.pipeline import run_pipeline
    try:
        result = run_pipeline(config, output_dir=config.output_dir, dpi=config.dpi, dpi_corr=config.dpi_correlation)
        return get_standard_envelope(
            primary_artifact={**result, "tool": TOOL_NAME, "workflow": "project"},
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="COMPUTED",
            claim_tag="CLAIM",
            claim_state="INTERPRETED",
            uncertainty="Moderate",
            perception_class="DERIVED",
            canon_9_touched=["GR"],
        )
    except Exception as e:
        logger.exception("Pipeline execution failed")
        return _error_envelope("PIPELINE_EXECUTION_FAILED", str(e))


async def _workflow_preview(project_yaml: str) -> dict[str, Any]:
    try:
        config_dict = yaml.safe_load(project_yaml)
    except Exception as e:
        return {"ok": False, "error": f"Invalid YAML: {e}", "claim_state": "VOID"}

    wells = [{"name": w["name"], "path": w["path"], "format": w.get("format", "LAS")} for w in config_dict.get("wells", [])]
    interval_summary = {}
    for well_id, ivls in config_dict.get("intervals", {}).items():
        interval_summary[well_id] = [
            {"zone": i["zone"], "top": i["top"], "base": i["base"], "depo_env": i.get("depo_env", "?")}
            for i in ivls
        ]

    return {
        "ok": True,
        "tool": TOOL_NAME,
        "workflow": "preview",
        "project": config_dict.get("project", "Untitled"),
        "n_wells": len(wells),
        "n_intervals": sum(len(v) for v in interval_summary.values()),
        "wells": wells,
        "intervals": interval_summary,
        "parameters": {
            "bin_size_m": config_dict.get("bin_size_m", 10.0),
            "min_package_thickness_m": config_dict.get("min_package_thickness_m", 20.0),
            "p50_shift_thresh_gapi": config_dict.get("p50_shift_thresh_gapi", 15.0),
            "gr_cut_api": config_dict.get("gr_cut_api", 75.0),
        },
        "claim_state": "OBSERVED",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# WORKFLOW: section_correlation (absorbs section_interpret_correlation)
# ═══════════════════════════════════════════════════════════════════════════════


async def _workflow_section_correlation(
    section_ref: str,
    well_refs: list[str],
    mode: Literal["correlation", "gr_motif", "sequence_stratigraphy", "gde_trend", "well_tie"],
    well_las_paths: list[str] | None,
    tops: dict | None,
    zone_definitions: dict | None,
    strat_standard: dict | None,
    paleoenvironment_input: list[dict] | None,
    checkshot_ref: str | None,
    wavelet_mode: str,
    wavelet_freq_hz: list[float] | None,
    phase_degrees: float,
    polarity: str,
    synthetics_output: bool,
    tie_qc_report: bool,
    seismic_ref: str | None,
    sonic_curve: str,
    density_curve: str,
    matrix_density: float,
    fluid_density: float,
) -> dict[str, Any]:
    import sys
    sys.path.insert(0, "/root/geox")

    # well_tie mode
    if mode == "well_tie":
        if not well_refs:
            return _error_envelope("NO_WELL_REF", "well_tie mode requires at least one well_ref.")
        first_ref = well_refs[0]
        las_entry = _get_artifact(first_ref)
        las_path = None
        if las_entry and las_entry.get("las_path"):
            las_path = las_entry["las_path"]
        elif well_las_paths and len(well_las_paths) > 0:
            las_path = well_las_paths[0]
        if not las_path:
            return _error_envelope("NO_LAS_PATH", "well_tie mode requires a well_ref with a registered LAS path or a well_las_paths argument.")

        try:
            from geox_core.core.welltie import compute_welltie
            artifact = compute_welltie(
                las_path=las_path,
                checkshot_ref=checkshot_ref,
                wavelet_mode=wavelet_mode,
                wavelet_freq_hz=wavelet_freq_hz,
                phase_degrees=phase_degrees,
                polarity=polarity,
                seismic_ref=seismic_ref,
                sonic_curve=sonic_curve or "DT",
                density_curve=density_curve or "RHOB",
                matrix_density=matrix_density,
                fluid_density=fluid_density,
            )
        except ValueError as e:
            return _error_envelope("WELLTIE_COMPUTATION_ERROR", str(e))

        tie_verdict = artifact.get("tie_quality_verdict", "UNDETERMINED")
        claim_state = "DERIVED_CANDIDATE" if tie_verdict == "UNDETERMINED" else "INTERPRETED"
        exec_status = ExecutionStatus.SUCCESS
        gov_status = GovernanceStatus.HOLD if tie_verdict == "UNDETERMINED" else GovernanceStatus.QUALIFY
        art_status = ArtifactStatus.COMPUTED
        claim_tag = "HYPOTHESIS" if tie_verdict == "UNDETERMINED" else "PLAUSIBLE"

        return get_standard_envelope(
            {**artifact, "tool": TOOL_NAME, "workflow": "section_correlation", "mode": "well_tie"},
            tool_class="interpret",
            execution_status=exec_status,
            governance_status=gov_status,
            artifact_status=art_status,
            claim_tag=claim_tag,
            claim_state=claim_state,
            perception_class="DERIVED",
            uncertainty="Moderate" if tie_verdict == "UNDETERMINED" else "Low",
        )

    # correlation mode
    if mode == "correlation":
        artifact = {
            "section_ref": section_ref,
            "wells": well_refs,
            "markers": [],
            "tie_type_policy": (
                "Each marker tie must be tagged: observed (well log pick), "
                "derived (from seismic interpretation), or hypothesized (GR motif extrapolation). "
                "Untagged markers default to hypothesized."
            ),
        }
        return get_standard_envelope(
            artifact,
            tool_class="interpret",
            claim_tag="HYPOTHESIS",
            claim_state="INTERPRETED",
            perception_class="DERIVED",
            evidence_tag="EVIDENCE_DIRECT",
            strat_standard=strat_standard or {"scheme": "NN_zone", "reference_chart": ""},
        )

    # gde_trend mode
    if mode == "gde_trend":
        if not paleoenvironment_input:
            return _error_envelope("NO_GDE_INPUT", "gde_trend mode requires paleoenvironment_input")
        trend_results: dict[str, list[dict]] = {}
        for entry in paleoenvironment_input:
            wid = entry.get("well_id", "UNKNOWN")
            if wid not in trend_results:
                trend_results[wid] = []
            trend_results[wid].append(entry)
        for wid, gde_entries in trend_results.items():
            gde_entries.sort(key=lambda e: e.get("depth_m", 0))
            gde_indices = np.array([e.get("gde_index", -1) for e in gde_entries], dtype=float)
            for pos in range(len(gde_entries)):
                window_before = gde_indices[max(0, pos - 2) : pos + 1]
                window_after = gde_indices[pos : min(len(gde_entries), pos + 3)]
                shallow = np.nanmean(window_before[window_before >= 0]) if np.any(window_before >= 0) else np.nan
                deep = np.nanmean(window_after[window_after >= 0]) if np.any(window_after >= 0) else np.nan
                if np.isnan(shallow) or np.isnan(deep) or abs(shallow - deep) < 0.75:
                    trend = "STABLE_OR_AMBIGUOUS"
                elif shallow > deep:
                    trend = "DEEPENING_UPWARD"
                else:
                    trend = "SHALLOWING_UPWARD"
                gde_entries[pos]["vertical_trend"] = trend
        return get_standard_envelope(
            {
                "tool": TOOL_NAME,
                "workflow": "section_correlation",
                "mode": "gde_trend",
                "section_ref": section_ref,
                "trend_results": trend_results,
                "claim_state": "DERIVED_CANDIDATE",
            },
            tool_class="interpret",
            execution_status="SUCCESS",
            artifact_status="COMPUTED",
            claim_tag="PLAUSIBLE",
            perception_class="DERIVED",
        )

    # GR motif / sequence stratigraphy modes
    from geox_core.core.geox_1d import process_las_file
    well_sources: list[tuple[str, str]] = []
    for i, ref in enumerate(well_refs):
        entry = _get_artifact(ref)
        if entry and entry.get("las_path"):
            well_sources.append((ref, entry["las_path"]))
        elif well_las_paths and i < len(well_las_paths):
            well_sources.append((ref, well_las_paths[i]))
    if not well_sources and well_las_paths:
        for i, lp in enumerate(well_las_paths):
            wid = well_refs[i] if i < len(well_refs) else f"well_{i}"
            well_sources.append((wid, lp))
    if not well_sources:
        return _error_envelope("NO_LAS_SOURCES", "No LAS paths available. Provide well_refs with registered artifacts or well_las_paths.")

    motifs_by_well: dict[str, dict] = {}
    for well_id, las_path in well_sources:
        if not Path(las_path).exists():
            motifs_by_well[well_id] = {"error": "LAS_FILE_NOT_FOUND"}
            continue
        curves = process_las_file(las_path)
        if "ERROR" in curves:
            motifs_by_well[well_id] = {"error": "LAS_PARSE_FAILED"}
            continue
        gr = None
        for alias in CANONICAL_ALIASES.get("GR", ["GR"]):
            if alias in curves:
                gr = curves[alias]
                break
        depth = None
        for dk in ["DEPT", "DEPTH", "MD"]:
            if dk in curves:
                depth = curves[dk]
                break
        if gr is None or depth is None:
            motifs_by_well[well_id] = {"error": "GR_OR_DEPTH_NOT_FOUND"}
            continue
        if zone_definitions:
            for zone_name, zdef in zone_definitions.items():
                zt = zdef.get("top_m")
                zb = zdef.get("base_m")
                motif = _classify_gr_motif(gr, depth, zt, zb)
                motifs_by_well[well_id] = {**motif, "zone": zone_name}
        else:
            motif = _classify_gr_motif(gr, depth)
            motifs_by_well[well_id] = motif

    if mode == "gr_motif":
        return get_standard_envelope(
            {
                "tool": TOOL_NAME,
                "workflow": "section_correlation",
                "mode": "gr_motif",
                "section_ref": section_ref,
                "wells_processed": len(well_sources),
                "motifs_by_well": motifs_by_well,
                "claim_state": "DERIVED_CANDIDATE",
            },
            tool_class="interpret",
            execution_status="SUCCESS",
            artifact_status="COMPUTED",
            claim_tag="PLAUSIBLE",
        )

    # sequence_stratigraphy mode
    candidate_surfaces: list[dict] = []
    for well_id, motif in motifs_by_well.items():
        if "error" in motif:
            continue
        m = motif.get("motif", "UNKNOWN")
        depth_arr = None
        for _, las_path in well_sources:
            curves = process_las_file(las_path)
            for dk in ["DEPT", "DEPTH", "MD"]:
                if dk in curves:
                    depth_arr = curves[dk]
                    break
            if depth_arr is not None:
                break
        if m == "BELL":
            candidate_surfaces.append({
                "well_id": well_id,
                "surface_type": "TS_CANDIDATE",
                "evidence": "Bell motif — fining-upward suggests possible Transgressive Surface",
                "confidence": motif.get("confidence", 0.5),
                "depth_m": float(depth_arr[0]) if depth_arr is not None and len(depth_arr) > 0 else None,
                "claim_state": "DERIVED_CANDIDATE",
            })
        elif m == "FUNNEL":
            candidate_surfaces.append({
                "well_id": well_id,
                "surface_type": "MFS_CANDIDATE",
                "evidence": "Funnel motif — coarsening-upward suggests progradation below possible MFS",
                "confidence": motif.get("confidence", 0.5),
                "depth_m": float(depth_arr[0]) if depth_arr is not None and len(depth_arr) > 0 else None,
                "claim_state": "DERIVED_CANDIDATE",
            })
        if tops and well_id in tops:
            well_tops = tops[well_id]
            sorted_tops = sorted(well_tops.items(), key=lambda x: x[1])
            for i in range(len(sorted_tops) - 1):
                mk_a, dep_a = sorted_tops[i]
                mk_b, dep_b = sorted_tops[i + 1]
                gap = dep_b - dep_a
                if gap > 100:
                    candidate_surfaces.append({
                        "well_id": well_id,
                        "surface_type": "SB_CANDIDATE",
                        "evidence": f"Gap of {gap:.0f}m between {mk_a} and {mk_b} — possible erosional truncation / SB",
                        "confidence": 0.4,
                        "depth_m": dep_a,
                        "claim_state": "DERIVED_CANDIDATE",
                    })

    return get_standard_envelope(
        {
            "tool": TOOL_NAME,
            "workflow": "section_correlation",
            "mode": "sequence_stratigraphy",
            "section_ref": section_ref,
            "wells_processed": len(well_sources),
            "motifs_by_well": motifs_by_well,
            "candidate_surfaces": candidate_surfaces,
            "claim_state": "DERIVED_CANDIDATE",
        },
        tool_class="interpret",
        execution_status="SUCCESS",
        artifact_status="COMPUTED",
        claim_tag="PLAUSIBLE",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC TOOL
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_sequence_interpret(
    workflow: Literal["single_well", "project", "preview", "section_correlation"] = "single_well",
    # single_well
    source: str | None = None,
    zone_top: float | None = None,
    zone_base: float | None = None,
    depo_env_code: str = "FLUVIAL",
    bin_size_m: float = 10.0,
    min_package_thickness_m: float = 20.0,
    p50_shift_api: float = 15.0,
    gr_cutoff_api: float = 75.0,
    detail_level: Literal["bins", "packages", "full"] = "full",
    # project / preview
    project_yaml: str | None = None,
    output_dir: str | None = None,
    # section_correlation
    section_ref: str | None = None,
    well_refs: list[str] | None = None,
    mode: Literal["correlation", "gr_motif", "sequence_stratigraphy", "gde_trend", "well_tie"] = "correlation",
    well_las_paths: list[str] | None = None,
    tops: dict | None = None,
    zone_definitions: dict | None = None,
    strat_standard: dict | None = None,
    paleoenvironment_input: list[dict] | None = None,
    checkshot_ref: str | None = None,
    wavelet_mode: str = "ricker",
    wavelet_freq_hz: list[float] | None = None,
    phase_degrees: float = 0.0,
    polarity: str = "SEG_NORMAL",
    synthetics_output: bool = False,
    tie_qc_report: bool = True,
    seismic_ref: str | None = None,
    sonic_curve: str = "DT",
    density_curve: str = "RHOB",
    matrix_density: float = 2.65,
    fluid_density: float = 1.0,
) -> dict[str, Any]:
    """Unified sequence stratigraphy engine.

    Replaces: geox_well_compute_gr_bins, geox_well_build_packages,
    geox_well_infer_seq_strat, geox_well_analyze_sequence,
    geox_stratigraphy_run_pipeline, geox_stratigraphy_preview_config,
    geox_section_interpret_correlation.

    Parameters
    ----------
    workflow : str
        "single_well" — param-driven L1-L3 pipeline.
        "project" — YAML-driven multi-well with XLSX/PNG output.
        "preview" — validate project YAML without running.
        "section_correlation" — multi-well correlation panel.

    single_well params:
        source, zone_top, zone_base, depo_env_code, bin_size_m,
        min_package_thickness_m, p50_shift_api, gr_cutoff_api, detail_level

    project params:
        project_yaml, output_dir

    preview params:
        project_yaml

    section_correlation params:
        section_ref, well_refs, mode, well_las_paths, tops, zone_definitions,
        strat_standard, paleoenvironment_input, checkshot_ref, wavelet_mode,
        wavelet_freq_hz, phase_degrees, polarity, synthetics_output,
        tie_qc_report, seismic_ref, sonic_curve, density_curve,
        matrix_density, fluid_density

    Returns
    -------
    Standard GEOX envelope with bins / packages / systems_tracts / surfaces
    depending on workflow and detail_level.
    """
    if workflow == "single_well":
        if not source or zone_top is None or zone_base is None:
            return _error_envelope("MISSING_PARAMS", "single_well workflow requires source, zone_top, and zone_base.")
        return await _workflow_single_well(
            source=source,
            zone_top=zone_top,
            zone_base=zone_base,
            depo_env_code=depo_env_code,
            bin_size_m=bin_size_m,
            min_package_thickness_m=min_package_thickness_m,
            p50_shift_api=p50_shift_api,
            gr_cutoff_api=gr_cutoff_api,
            detail_level=detail_level,
        )

    if workflow == "project":
        if not project_yaml:
            return _error_envelope("MISSING_PARAMS", "project workflow requires project_yaml.")
        return await _workflow_project(project_yaml, output_dir)

    if workflow == "preview":
        if not project_yaml:
            return _error_envelope("MISSING_PARAMS", "preview workflow requires project_yaml.")
        return await _workflow_preview(project_yaml)

    if workflow == "section_correlation":
        if not section_ref or not well_refs:
            return _error_envelope("MISSING_PARAMS", "section_correlation workflow requires section_ref and well_refs.")
        return await _workflow_section_correlation(
            section_ref=section_ref,
            well_refs=well_refs,
            mode=mode,
            well_las_paths=well_las_paths,
            tops=tops,
            zone_definitions=zone_definitions,
            strat_standard=strat_standard,
            paleoenvironment_input=paleoenvironment_input,
            checkshot_ref=checkshot_ref,
            wavelet_mode=wavelet_mode,
            wavelet_freq_hz=wavelet_freq_hz,
            phase_degrees=phase_degrees,
            polarity=polarity,
            synthetics_output=synthetics_output,
            tie_qc_report=tie_qc_report,
            seismic_ref=seismic_ref,
            sonic_curve=sonic_curve,
            density_curve=density_curve,
            matrix_density=matrix_density,
            fluid_density=fluid_density,
        )

    return _error_envelope("UNKNOWN_WORKFLOW", f"Unknown workflow: {workflow}")
