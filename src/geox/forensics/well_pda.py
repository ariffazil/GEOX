"""GEOX Subsurface Pre-Flight Auditor (Phase D — well_qc forensic modes)."""
from __future__ import annotations

from typing import Any

import numpy as np

from geox.envelope import compact_envelope
from geox.obs import observed

SENTINELS = (-999.25, -999.0, 9999.0, 1e37)


def check_datum_shift(
    depth_m: list[float], run_a: list[float], run_b: list[float], threshold_m: float = 0.5
) -> dict[str, Any]:
    """Cross-correlate two depth-indexed runs to catch KB/TVDSS vs MD shifts."""
    if len(depth_m) < 5 or len(run_a) != len(depth_m) or len(run_b) != len(depth_m):
        return {"defect": False, "shift_m": 0.0, "reason": "insufficient_samples"}
    d = np.asarray(depth_m, dtype=float)
    step = float(np.median(np.diff(d)))
    a = np.asarray(run_a, dtype=float) - float(np.mean(run_a))
    b = np.asarray(run_b, dtype=float) - float(np.mean(run_b))
    corr = np.correlate(a, b, mode="full")
    lag = int(np.argmax(corr) - (len(a) - 1))
    shift_m = round(lag * step, 2)
    return {
        "defect": abs(shift_m) > threshold_m,
        "shift_m": shift_m,
        "threshold_m": threshold_m,
        "step_m": round(step, 3),
    }


def check_unit_trap(curves: dict[str, list[float]]) -> dict[str, Any]:
    """Detect x3.28084 ratio corruption, x100 % vs v/v porosity, and us/m vs us/ft sonic."""
    traps: list[dict[str, Any]] = []
    for name, vals in curves.items():
        arr = np.asarray([v for v in vals if v is not None and np.isfinite(v) and abs(v) < 1e10 and v != -999.25], dtype=float)
        if arr.size == 0:
            continue
        med = float(np.median(arr))
        u = name.upper()
        if "VPVS" in u or "VP_VS" in u:
            if med > 4.0 or med < 1.0:
                traps.append({"curve": name, "median": round(med, 3), "trap": "x3.28084_ratio_unit_corruption"})
        elif u in ("NPHI", "PHIE", "PHIT", "NEU", "NMR"):
            if med > 1.0:
                traps.append({"curve": name, "median": round(med, 3), "trap": "x100_percent_vs_vv_porosity"})
        elif u in ("DTC", "DT", "DTCO"):
            if med > 220.0 or med < 35.0:
                traps.append({"curve": name, "median": round(med, 3), "trap": "us_per_m_vs_us_per_ft_sonic"})
    return {"defect": bool(traps), "traps": traps}


def check_sentinels(curves: dict[str, list[float]]) -> dict[str, Any]:
    """Detect null sentinels (-999.25, 9999, 1e37), 1-sample passes, and sparse blindspots (<25% valid)."""
    findings: list[dict[str, Any]] = []
    for name, vals in curves.items():
        n = len(vals)
        if n <= 2:
            findings.append({"curve": name, "issue": "truncated_pass", "samples": n})
            continue
        bad = sum(
            1
            for v in vals
            if v is None or not np.isfinite(v) or any(abs(v - s) <= max(1e-3, abs(s) * 1e-6) for s in SENTINELS) or abs(v) >= 1e30
        )
        valid_frac = (n - bad) / n
        if bad > 0:
            findings.append({"curve": name, "issue": "sentinel_or_null", "bad_samples": bad, "valid_fraction": round(valid_frac, 3)})
        if valid_frac < 0.25:
            findings.append({"curve": name, "issue": "sparse_blindspot_lt_25pct", "valid_fraction": round(valid_frac, 3)})
    return {"defect": bool(findings), "findings": findings}


def check_matrix_paradox(
    rhob: list[float] | None = None,
    nphi: list[float] | None = None,
    nmr: list[float] | None = None,
    vpvs: list[float] | None = None,
) -> dict[str, Any]:
    """Flag acoustic-lookalike matrix paradoxes and emit >=3 rival lithology hypotheses + falsifiers."""
    if not rhob or not nphi or not nmr:
        return {"defect": False, "hypotheses": []}
    excess_oh = float(np.median(np.asarray(nphi) - np.asarray(nmr)))
    med_rhob = float(np.median(rhob))
    med_vpvs = float(np.median(vpvs)) if vpvs else 0.0
    paradox = excess_oh > 0.12 and med_rhob < 2.25
    hypotheses = (
        [
            {"id": "H1", "lithology": "Hydrated smectite/volcaniclastic tuffaceous buildup", "falsifier": "Core XRD shows >85% calcite and <5% clay/pyroxene."},
            {"id": "H2", "lithology": "High-porosity argillaceous carbonate / marl", "falsifier": "PEF < 2.8 b/e with low carbonate Ca content on elemental log."},
            {"id": "H3", "lithology": "Overpressured gas-bearing shale / mudstone", "falsifier": "Mudgas/MDT proves Sw = 1.00 water-wet and normal pore pressure."},
        ]
        if paradox
        else []
    )
    return {
        "defect": paradox,
        "excess_oh_vv": round(excess_oh, 3),
        "median_rhob_gcc": round(med_rhob, 3),
        "median_vpvs": round(med_vpvs, 3),
        "hypotheses": hypotheses,
    }


def check_age_inversion(
    biostrat_picks: list[dict[str, Any]], checkshot_flag: int = 1
) -> dict[str, Any]:
    """Catch older-above-younger age inversions, cuttings bases, and uncalibrated TDRs."""
    issues: list[dict[str, Any]] = []
    ordered = sorted(biostrat_picks, key=lambda p: float(p["depth_m"]))
    for prev, cur in zip(ordered, ordered[1:]):
        if float(prev["age_ma"]) > float(cur["age_ma"]):
            issues.append(
                {
                    "issue": "stratigraphic_age_inversion",
                    "shallower": prev,
                    "deeper": cur,
                }
            )
    for p in ordered:
        if str(p.get("sample_type", "")).lower() == "cuttings" and str(p.get("event_type", "")).lower() in ("base", "fad"):
            issues.append({"issue": "cuttings_used_for_base_fad", "pick": p})
    if int(checkshot_flag) == 0:
        issues.append({"issue": "uncalibrated_tdr_checkshot_flag_0"})
    return {"defect": bool(issues), "issues": issues}


@observed("Appraisal", tool_name="geox_well_pda")
def geox_well_pda(mode: str = "all", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Subsurface Pre-Flight Auditor entrypoint. Accepts {} for default dashboard."""
    if not payload:
        return compact_envelope(
            tool="geox_well_pda",
            verdict="READY",
            epistemic="OBS",
            summary="GEOX Well Forensic Desk ready (modes: datum_shift, unit_trap, sentinel, matrix_paradox, age_inversion, all). Pass synthetic or public LAS curves to run pre-flight QC.",
            defaults_applied=["mode=all", "datum_threshold_m=0.5", "excess_oh_threshold_vv=0.12"],
            falsifiers=["Supply calibrated multi-run LAS + SWC biostrat + checkshot to falsify detected defects."],
            data={"available_modes": ["datum_shift", "unit_trap", "sentinel", "matrix_paradox", "age_inversion", "all"]},
            artifact_uri="ui://geox/well-forensic-desk.html",
        )

    results: dict[str, Any] = {}
    m = mode.strip().lower()
    if m in ("all", "datum_shift") and "depth_m" in payload and "run_a" in payload and "run_b" in payload:
        results["datum_shift"] = check_datum_shift(payload["depth_m"], payload["run_a"], payload["run_b"])
    if m in ("all", "unit_trap") and "curves" in payload:
        results["unit_trap"] = check_unit_trap(payload["curves"])
    if m in ("all", "sentinel") and "curves" in payload:
        results["sentinel"] = check_sentinels(payload["curves"])
    if m in ("all", "matrix_paradox") and "matrix" in payload:
        results["matrix_paradox"] = check_matrix_paradox(**payload["matrix"])
    if m in ("all", "age_inversion") and ("biostrat_picks" in payload or "checkshot_flag" in payload):
        results["age_inversion"] = check_age_inversion(
            payload.get("biostrat_picks", []), checkshot_flag=payload.get("checkshot_flag", 1)
        )

    defects = [k for k, v in results.items() if isinstance(v, dict) and v.get("defect")]
    verdict = "DEFECTS_FOUND" if defects else "PASS"
    falsifiers = [
        h["falsifier"]
        for h in results.get("matrix_paradox", {}).get("hypotheses", [])
        if "falsifier" in h
    ]
    return compact_envelope(
        tool="geox_well_pda",
        verdict=verdict,
        epistemic="OBS",
        summary=f"Pre-flight QC ({mode}): {len(defects)} defect class(es) flagged: {', '.join(defects) or 'none'}.",
        defaults_applied=["datum_threshold_m=0.5", "sparse_threshold=0.25", "excess_oh_threshold_vv=0.12"],
        falsifiers=falsifiers,
        data={"defects": defects, "checks": results},
        artifact_uri="ui://geox/well-forensic-desk.html",
    )
