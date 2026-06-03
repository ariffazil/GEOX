"""
GEOX Well Stratigraphy — Generalized Pipeline Orchestrator
═══════════════════════════════════════════════════════════════════════════════

Runs L1 sensing -> L2 package builder -> L3 seq strat for any project config.
Outputs: XLSX (5 sheets) + per-well PNGs + correlation panel PNG.

Config-driven via ProjectConfig — no hardcoded wells, intervals, or depo envs.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
import os
from collections import Counter
from datetime import datetime
from typing import Any, Optional


from .config import (
    ProjectConfig,
    default_depo_eod,
    default_depo_rank,
    default_nn_ages,
)
from .loader import load_well_data
from .sensing import sense_bins
from .packages import build_packages
from .seqstrat import infer_seq_strat, geo_rule_check, litho_classify
from .plot import generate_well_panel, generate_correlation_panel
from .excel import export_excel, export_sensing

logger = logging.getLogger("geox.stratigraphy.pipeline")


def run_pipeline(
    config: ProjectConfig,
    output_dir: str = "output",
    dpi: int = 200,
    dpi_corr: int = 180,
) -> dict[str, Any]:
    """
    Run the full L1-L3 stratigraphy pipeline.

    Parameters
    ----------
    config : ProjectConfig
        Project configuration with wells, intervals, and parameters.
    output_dir : str, default "output"
        Output directory for generated files.
    dpi : int, default 200
        DPI for per-well PNGs.
    dpi_corr : int, default 180
        DPI for correlation panel PNG.

    Returns
    -------
    dict with keys: project, n_wells, n_bins, n_packages, n_gap_packages,
        tract_dist, motif_dist, outputs (list of generated file paths), status.
    """
    depo_eod = default_depo_eod()
    depo_rank = default_depo_rank()
    nn_ages = default_nn_ages()

    os.makedirs(output_dir, exist_ok=True)
    now_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # [1/4] Load well data
    logger.info(f"[1/4] Loading well data for {len(config.wells)} wells...")
    well_data = {}
    for ws in config.wells:
        try:
            data = load_well_data(ws.path)
            well_data[ws.name] = data
            logger.info(f"  OK {ws.name}: {len(data['depth'])} samples, GR={data['gr_col']}")
        except Exception as e:
            logger.warning(f"  FAIL {ws.name}: {e}")

    # [2/4] L1 -> L2 -> L3
    logger.info("[2/4] L1 sensing -> L2 packages -> L3 seq strat...")
    all_packages = []
    sensing_rows = []
    all_sensing_by_well = {}
    pkg_counter = {}

    for well_id in config.well_order or list(config.intervals.keys()):
        wdata = well_data.get(well_id)
        ivls = config.intervals.get(well_id, [])
        pkg_counter[well_id] = 0
        well_pkgs = []

        for ivl in ivls:
            zone = ivl.zone
            depo = ivl.depo_env
            top, base = float(ivl.top), float(ivl.base)
            age = _parse_zone_age(zone, nn_ages)

            if wdata is None or wdata.get("gr") is None:
                pkg_counter[well_id] += 1
                pkg = _make_no_data_package(well_id, pkg_counter[well_id], zone, depo, top, base, age)
                all_packages.append(pkg)
                well_pkgs.append(pkg)
                continue

            depth = wdata["depth"]
            gr = wdata["gr"]

            # L1: sensing
            bins = sense_bins(
                depth,
                gr,
                top,
                base,
                bin_size_m=config.bin_size_m,
                gr_cut_api=config.gr_cut_api,
            )
            for b in bins:
                sensing_rows.append({**b, "WELL": well_id, "ZONE": zone})
            all_sensing_by_well.setdefault(well_id, []).extend(bins)

            # L2: packages
            pkgs = build_packages(
                bins,
                min_pkg_m=config.min_package_thickness_m,
                shift_thresh_gapi=config.p50_shift_thresh_gapi,
            )

            for pi, pkg_raw in enumerate(pkgs, 1):
                pkg_counter[well_id] += 1
                tract, process = infer_seq_strat(pkg_raw, depo, depo_rank)
                flag = geo_rule_check(pkg_raw, depo, depo_rank)

                conf = (
                    "High"
                    if pkg_raw["VARIABILITY"] == "Low"
                    and pkg_raw["N_BINS"] >= 4
                    and pkg_raw["HUMAN_MOTIF"] not in ("Heterolithic", "Serrated / Irregular Pattern")
                    else "Low"
                    if pkg_raw["N_BINS"] < 3
                    else "Medium"
                )

                pkg = {
                    "WELL": well_id,
                    "PKG_ID": f"{well_id.replace(' ', '_').replace('-', '')}_P{pkg_counter[well_id]:02d}",
                    "PARENT_ZONE": zone,
                    "DEPO_ENV": depo,
                    "TOP": round(pkg_raw["TOP"], 2),
                    "BASE": round(pkg_raw["BASE"], 2),
                    "THICKNESS": pkg_raw["THICKNESS"],
                    "HUMAN_MOTIF": pkg_raw["HUMAN_MOTIF"],
                    "RIDER_MOTIF": pkg_raw["RIDER_MOTIF"],
                    "NET_TREND": pkg_raw["NET_TREND"],
                    "VARIABILITY": pkg_raw["VARIABILITY"],
                    "GR_BASELINE_SHIFT": pkg_raw["GR_BASELINE_SHIFT"],
                    "GR_MEAN": pkg_raw["GR_MEAN"],
                    "GR_P10": pkg_raw["GR_P10"],
                    "GR_P50": pkg_raw["GR_P50"],
                    "GR_P90": pkg_raw["GR_P90"],
                    "LITHO": litho_classify(pkg_raw["GR_MEAN"], config.gr_sand_api, config.gr_silt_api, config.gr_shaly_api),
                    "SEQ_STRAT": tract,
                    "INFERRED_PROCESS": process,
                    "ANOMALY_FLAG": flag,
                    "CONFIDENCE": conf,
                    "N_BINS": pkg_raw["N_BINS"],
                    "AGE_TOP_Ma": age[0] if age else None,
                    "AGE_BASE_Ma": age[1] if age else None,
                    "NN_ZONE": zone,
                    "QC": "PASS" if pkg_raw["GR_MEAN"] is not None else "NO_DATA",
                }
                all_packages.append(pkg)
                well_pkgs.append(pkg)

        # Extrapolate Heterolithic motifs in this well
        well_pkgs_sorted = sorted(well_pkgs, key=lambda p: p["TOP"])
        for pkg in well_pkgs_sorted:
            if pkg["HUMAN_MOTIF"] == "Heterolithic":
                em, ec, er = _extrapolate_motif(pkg, well_pkgs_sorted)
                if em:
                    pkg["EXTRAP_MOTIF"] = em
                    pkg["EXTRAP_CONF"] = ec
                    pkg["EXTRAP_REASON"] = er

    # [3/4] Generate PNGs
    logger.info(f"[3/4] Generating panels ({len(well_data)} wells + correlation)...")
    generated_files = []

    for well_id in config.well_order or list(config.intervals.keys()):
        wdata = well_data.get(well_id)
        pkgs = [p for p in all_packages if p["WELL"] == well_id]
        ivls = config.intervals.get(well_id, [])
        if not pkgs:
            logger.warning(f"  SKIP {well_id}: no packages")
            continue

        png_path = generate_well_panel(
            well_id,
            wdata,
            pkgs,
            ivls,
            sensing_bins=all_sensing_by_well.get(well_id, []),
            config=config,
            output_dir=output_dir,
            dpi=dpi,
            now_ts=now_ts,
        )
        if png_path:
            generated_files.append(png_path)

    corr_png = generate_correlation_panel(well_data, all_packages, config, output_dir, dpi_corr, now_ts)
    if corr_png:
        generated_files.append(corr_png)

    # [4/4] Export Excel
    logger.info("[4/4] Exporting XLSX...")
    xlsx_path = os.path.join(output_dir, f"{config.project}_SOT.xlsx")
    export_excel(all_packages, config, xlsx_path)
    generated_files.append(xlsx_path)

    # Export sensing CSV
    csv_path = os.path.join(output_dir, f"{config.project}_10M_SENSING.csv")
    export_sensing(sensing_rows, csv_path)
    generated_files.append(csv_path)

    # Summary
    tract_dist = Counter(p.get("SEQ_STRAT", "UNKNOWN") for p in all_packages)
    motif_dist = Counter(p["HUMAN_MOTIF"] for p in all_packages)

    return {
        "project": config.project,
        "n_wells": len(config.wells),
        "n_bins": len(sensing_rows),
        "n_packages": len(all_packages),
        "tract_distribution": dict(tract_dist.most_common()),
        "motif_distribution": dict(motif_dist.most_common()),
        "outputs": generated_files,
        "status": "SUCCESS",
        "timestamp": now_ts,
    }


def _parse_zone_age(zone: str, nn_ages: dict) -> Optional[tuple[float, float]]:
    """Parse NN zone age from zone string."""
    z = zone.upper().replace(" ", "_")
    if z in nn_ages:
        return nn_ages[z]
    for prefix in ["NN11_NN10", "NN10_NN11", "PRE_", "STAGE_", "LOWER_"]:
        if prefix in z:
            return None
    parts = [p for p in z.replace("-", "_").split("_") if p in nn_ages]
    if parts:
        return (
            min(nn_ages[p][0] for p in parts),
            max(nn_ages[p][1] for p in parts),
        )
    return None


def _make_no_data_package(
    well_id: str,
    counter: int,
    zone: str,
    depo: str,
    top: float,
    base: float,
    age: Optional[tuple],
) -> dict:
    """Create a package record for wells with no LAS data."""
    return {
        "WELL": well_id,
        "PKG_ID": f"{well_id.replace(' ', '_')}_P{counter:02d}",
        "PARENT_ZONE": zone,
        "DEPO_ENV": depo,
        "TOP": top,
        "BASE": base,
        "THICKNESS": round(base - top, 1),
        "HUMAN_MOTIF": "Heterolithic",
        "RIDER_MOTIF": "Serrated",
        "NET_TREND": "Heterolithic",
        "VARIABILITY": "No GR Data",
        "GR_BASELINE_SHIFT": None,
        "GR_MEAN": None,
        "GR_P10": None,
        "GR_P50": None,
        "GR_P90": None,
        "LITHO": "Heterolithic",
        "SEQ_STRAT": "UNCERTAIN",
        "INFERRED_PROCESS": "No LAS file — interval description only",
        "ANOMALY_FLAG": "NO_DATA",
        "CONFIDENCE": "—",
        "N_BINS": 0,
        "AGE_TOP_Ma": age[0] if age else None,
        "AGE_BASE_Ma": age[1] if age else None,
        "NN_ZONE": zone,
        "QC": "NO_DATA",
    }


def _extrapolate_motif(
    pkg: dict,
    sorted_pkgs: list[dict],
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extrapolate Heterolithic motif from nearest non-Heterolithic neighbours."""
    try:
        idx = sorted_pkgs.index(pkg)
    except ValueError:
        return None, None, None

    above = next(
        (sorted_pkgs[j]["HUMAN_MOTIF"] for j in range(idx - 1, -1, -1) if sorted_pkgs[j]["HUMAN_MOTIF"] != "Heterolithic"),
        None,
    )
    below = next(
        (
            sorted_pkgs[j]["HUMAN_MOTIF"]
            for j in range(idx + 1, len(sorted_pkgs))
            if sorted_pkgs[j]["HUMAN_MOTIF"] != "Heterolithic"
        ),
        None,
    )

    if above == below and above is not None:
        return above, "HIGH", f"Bracketed by {above} above and below"
    if above is not None and below is None:
        return above, "MEDIUM", "End of section — propagated downward"
    if below is not None and above is None:
        return below, "MEDIUM", "Start of section — propagated upward"
    return None, None, None
