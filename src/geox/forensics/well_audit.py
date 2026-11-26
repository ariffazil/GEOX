"""Deterministic 8-defect Well Forensic Engine (Phase D — src/geox/forensics/well_audit.py)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from geox.egs.models.entities import Well
from geox.egs.storage import load_or_seed_earthgraph, save_earthgraph
from geox.envelope import compact_envelope
from geox.obs import observed

MIXED_SENTINELS = (-999.25, -999.0, 9999.0, 98765.0, 1e37)


def _is_las2_text(text: str) -> bool:
    head = text[:2000].upper()
    return ("~W" in head or "~WELL" in head) and ("~C" in head or "~CURVE" in head) and ("~A" in head or "~ASCII" in head)


def _parse_las2(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not _is_las2_text(text):
        return {}
    section = ""
    well_meta: dict[str, str] = {}
    curves: list[tuple[str, str]] = []
    rows: list[list[float]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("~"):
            section = line[1:2].upper()
            continue
        if section == "W":
            m = re.match(r"^([A-Za-z0-9_]+)\s*\.[^\s]*\s+([^:]+):", line)
            if m:
                well_meta[m.group(1).upper()] = m.group(2).strip()
        elif section == "C":
            m = re.match(r"^([A-Za-z0-9_]+)\s*\.([^\s:]*)", line)
            if m:
                curves.append((m.group(1).upper(), m.group(2).strip().upper()))
        elif section == "A":
            parts = line.split()
            if len(parts) == len(curves):
                try:
                    rows.append([float(x) for x in parts])
                except ValueError:
                    continue
    arr = np.asarray(rows, dtype=float) if rows else np.empty((0, len(curves)))
    curve_data = {curves[i][0]: arr[:, i] for i in range(len(curves))} if arr.size else {c[0]: np.array([]) for c in curves}
    curve_units = {c[0]: c[1] for c in curves}
    return {
        "file": path.name,
        "ext": path.suffix.lower(),
        "well": well_meta.get("WELL", path.stem),
        "uwi": well_meta.get("UWI", ""),
        "n_samples": len(rows),
        "curve_units": curve_units,
        "curves": curve_data,
    }


def _cross_correlate_lag(depth: np.ndarray, a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    step = float(np.median(np.diff(depth)))
    a0, b0 = a - np.mean(a), b - np.mean(b)
    denom = float(np.linalg.norm(a0) * np.linalg.norm(b0))
    if denom == 0.0:
        return 0.0, 0.0
    max_lag = min(150, len(a) // 4)
    best_lag, best_r = 0, -1.0
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            x, y = a0[lag:], b0[: len(b0) - lag]
        else:
            x, y = a0[: len(a0) + lag], b0[-lag:]
        d = float(np.linalg.norm(x) * np.linalg.norm(y))
        r = float(np.dot(x, y) / d) if d > 0 else 0.0
        if r > best_r:
            best_r, best_lag = r, lag
    return round(best_lag * step, 2), round(best_r, 4)


def _is_sentinel_mask(vals: np.ndarray) -> np.ndarray:
    mask = ~np.isfinite(vals) | (np.abs(vals) >= 1e30)
    for s in MIXED_SENTINELS:
        mask |= np.isclose(vals, s, rtol=1e-6, atol=1e-3)
    return mask


@observed("Appraisal", tool_name="geox_well_forensic_audit")
def run_well_forensic_audit(pack_dir: str | Path, *, mode: str = "forensic_audit") -> dict[str, Any]:
    """Run deterministic 8-defect forensic audit over a well pack directory."""
    root = Path(pack_dir)
    parsed_las: list[dict[str, Any]] = []
    tdr_docs: list[dict[str, Any]] = []
    tops_docs: list[dict[str, Any]] = []

    for p in sorted(root.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() == ".json":
            doc = json.loads(p.read_text(encoding="utf-8"))
            if "CHECKSHOT_FLAG" in doc:
                tdr_docs.append(doc)
            if "tops" in doc:
                tops_docs.append(doc)
        else:
            las = _parse_las2(p)
            if las:
                parsed_las.append(las)

    faults: dict[str, dict[str, Any]] = {}
    quarantine_rows: list[dict[str, Any]] = []
    all_curves: dict[str, tuple[np.ndarray, str, str]] = {}
    depth_ref: np.ndarray | None = None
    uwis: set[str] = set()
    disguised_csv: list[str] = []
    stub_files: list[str] = []
    stub_sentinels: list[float] = []

    for las in parsed_las:
        fname = las["file"]
        if las["uwi"]:
            uwis.add(las["uwi"])
        if las["ext"] == ".csv":
            disguised_csv.append(fname)
        if las["n_samples"] <= 2:
            stub_files.append(fname)
            for cname, arr in las["curves"].items():
                if cname != "DEPT" and arr.size:
                    stub_sentinels.extend(float(x) for x in arr)
            quarantine_rows.append({"file": fname, "curve": "*", "status": "QUARANTINE", "fault": "SENTINEL_STUB_BLINDSPOT"})
            continue
        if "DEPT" in las["curves"] and (depth_ref is None or len(las["curves"]["DEPT"]) > len(depth_ref)):
            depth_ref = las["curves"]["DEPT"]
        for cname, arr in las["curves"].items():
            if cname != "DEPT":
                all_curves[cname] = (arr, las["curve_units"].get(cname, ""), fname)

    # 1. KB_DATUM_SHIFT
    if depth_ref is not None and "GR_R1" in all_curves and "GR_R2" in all_curves:
        a, _, fa = all_curves["GR_R1"]
        b, _, fb = all_curves["GR_R2"]
        if len(a) == len(b) == len(depth_ref):
            lag_m, r = _cross_correlate_lag(depth_ref, a, b)
            if abs(lag_m) >= 0.5 and r >= 0.85:
                faults["KB_DATUM_SHIFT"] = {"epistemic": "DER", "lag_m": lag_m, "pearson_r": r, "files": [fa, fb]}
                quarantine_rows.append({"file": fa, "curve": "GR_R1", "status": "QUARANTINE", "fault": "KB_DATUM_SHIFT"})

    # 2. UNIT_FACTOR_32808, 3. POROSITY_X100_MISMATCH, 4. SONIC_UNIT_HEADER_LIE, 5b. BLINDSPOT
    blindspots: list[dict[str, Any]] = []
    for cname, (arr, unit, fname) in all_curves.items():
        smask = _is_sentinel_mask(arr)
        valid = arr[~smask]
        cov_pct = round(100.0 * len(valid) / max(1, len(arr)), 2)
        if cov_pct < 95.0 and len(arr) > 10:
            blindspots.append({"file": fname, "curve": cname, "null_pct": round(100.0 - cov_pct, 2), "coverage_pct": cov_pct})
            quarantine_rows.append({"file": fname, "curve": cname, "status": "WARN", "fault": "SENTINEL_STUB_BLINDSPOT"})
        if valid.size == 0:
            continue
        med = float(np.median(valid))
        if "VPVS" in cname and (med > 4.5 or med < 1.0):
            faults["UNIT_FACTOR_32808"] = {
                "epistemic": "OBS", "curve": cname, "median": round(med, 3),
                "div_328084": round(med / 3.28084, 3), "file": fname,
            }
            quarantine_rows.append({"file": fname, "curve": cname, "status": "QUARANTINE", "fault": "UNIT_FACTOR_32808"})
        if ("NPHI" in cname or "PHIE" in cname) and unit in ("V/V", "FRAC", "DEC") and med > 1.0:
            faults["POROSITY_X100_MISMATCH"] = {"epistemic": "OBS", "curve": cname, "header_unit": unit, "median": round(med, 2), "file": fname}
            quarantine_rows.append({"file": fname, "curve": cname, "status": "QUARANTINE", "fault": "POROSITY_X100_MISMATCH"})
        if "DTCO" in cname and unit in ("US/M", "USEC/M") and 40.0 <= med <= 190.0:
            implied_vp_if_usm = round(1e6 / med, 1)
            implied_vp_if_usft = round(304800.0 / med, 1)
            faults["SONIC_UNIT_HEADER_LIE"] = {
                "epistemic": "DER", "curve": cname, "header_unit": unit, "median": round(med, 2),
                "implied_vp_if_usm_ms": implied_vp_if_usm, "implied_vp_if_usft_ms": implied_vp_if_usft, "file": fname,
            }
            quarantine_rows.append({"file": fname, "curve": cname, "status": "QUARANTINE", "fault": "SONIC_UNIT_HEADER_LIE"})

    if stub_files or blindspots:
        faults["SENTINEL_STUB_BLINDSPOT"] = {
            "epistemic": "OBS", "stub_files": stub_files, "stub_sentinels": stub_sentinels, "blindspots": blindspots,
        }

    # 6. IDENTITY_TDR_FORMAT_DRIFT
    bad_tdr = [d for d in tdr_docs if int(d.get("CHECKSHOT_FLAG", 1)) == 0]
    if len(uwis) > 1 or disguised_csv or bad_tdr:
        faults["IDENTITY_TDR_FORMAT_DRIFT"] = {
            "epistemic": "OBS", "uwi_conflicts": sorted(uwis),
            "disguised_las_csv": disguised_csv, "checkshot_flag_zero": len(bad_tdr),
        }
        for f in disguised_csv:
            quarantine_rows.append({"file": f, "curve": "*", "status": "WARN", "fault": "IDENTITY_TDR_FORMAT_DRIFT"})

    # 7. ROCK_PHYSICS_TRAP
    if depth_ref is not None and all(k in all_curves for k in ("VP", "VPVS", "RHOB", "NPHI", "PHIE_NMR", "RT")):
        vp = all_curves["VP"][0]
        vpvs = all_curves["VPVS"][0]
        rhob = all_curves["RHOB"][0]
        nphi = all_curves["NPHI"][0]
        nmr = all_curves["PHIE_NMR"][0]
        rt = all_curves["RT"][0]
        oh_sep = nphi - nmr
        trap = (oh_sep > 0.14) & (rhob < 2.15) & (vpvs < 2.3) & (rt < 3.0)
        if int(np.sum(trap)) >= 20:
            t_depths = depth_ref[trap]
            base_vp = float(np.median(vp[~trap])) if np.any(~trap) else 0.0
            trap_vp = float(np.median(vp[trap]))
            faults["ROCK_PHYSICS_TRAP"] = {
                "epistemic": "OBS+INT",
                "interval_m": [round(float(t_depths[0]), 1), round(float(t_depths[-1]), 1)],
                "vp_jump_ms": round(trap_vp - base_vp, 1),
                "median_rhob": round(float(np.median(rhob[trap])), 3),
                "nphi_nmr_sep_vv": round(float(np.median(oh_sep[trap])), 3),
                "median_rt_ohmm": round(float(np.median(rt[trap])), 2),
                "hypotheses": [
                    {"id": "H1", "epistemic": "INT", "claim": "Hydrated smectite/volcaniclastic buildup (water-wet)", "falsifier": "Core XRD >85% calcite & <5% clay."},
                    {"id": "H2", "epistemic": "INT", "claim": "Argillaceous carbonate / marl hard streak", "falsifier": "PEF <2.8 b/e and low Ca on elemental log."},
                    {"id": "H3", "epistemic": "SPEC", "claim": "Tight gas-charged sand/silt", "falsifier": "MDT/RT confirms Sw=1.00 water-wet."},
                ],
            }
            quarantine_rows.append({"file": all_curves["RHOB"][2], "curve": "RHOB/NPHI/NMR", "status": "QUARANTINE", "fault": "ROCK_PHYSICS_TRAP"})

    # 8. STRAT_AGE_INVERSION
    inversions: list[dict[str, Any]] = []
    for doc in tops_docs:
        tops = sorted(doc.get("tops", []), key=lambda t: float(t["depth_m"]))
        for a, b in zip(tops, tops[1:]):
            if float(a["age_ma"]) > float(b["age_ma"]):
                inversions.append({"shallower": a, "deeper": b})
    if inversions:
        faults["STRAT_AGE_INVERSION"] = {"epistemic": "OBS", "verdict": "HOLD", "inversions": inversions}
        quarantine_rows.append({"file": "tops.json", "curve": "BIOSTRAT", "status": "QUARANTINE", "fault": "STRAT_AGE_INVERSION"})

    # Persist summary node into ~/.geox/earthgraph.db
    well_name = parsed_las[0]["well"] if parsed_las else root.name
    try:
        g = load_or_seed_earthgraph()
        wid = f"well-audit-{well_name.lower()}"
        g.wells[wid] = Well(
            id=wid,
            name=well_name,
            uwi=",".join(sorted(uwis)),
            description=f"Forensic audit: {len(faults)} fault codes ({', '.join(sorted(faults)) or 'CLEAN'}).",
            log_curves=sorted(all_curves.keys()),
            tags=["forensic_audit", "quarantine" if faults else "pass"],
        )
        save_earthgraph(g)
    except Exception:
        pass

    fault_codes = sorted(faults.keys())
    quarantine_count = sum(1 for r in quarantine_rows if r["status"] == "QUARANTINE")
    verdict = "QUARANTINE" if quarantine_count > 0 else "PASS"

    if mode == "forensic_slice" and depth_ref is not None:
        stride = max(1, len(depth_ref) // 120)
        return compact_envelope(
            tool="geox_well",
            verdict=verdict,
            epistemic="OBS",
            summary=f"Forensic slice for {well_name}: {len(depth_ref[::stride])} decimated points.",
            data={
                "well": well_name,
                "depth_m": [round(float(x), 1) for x in depth_ref[::stride]],
                "gr_r1": [round(float(x), 1) for x in all_curves["GR_R1"][0][::stride]] if "GR_R1" in all_curves else [],
                "gr_r2": [round(float(x), 1) for x in all_curves["GR_R2"][0][::stride]] if "GR_R2" in all_curves else [],
                "quarantine_matrix": quarantine_rows,
                "faults": faults,
            },
            artifact_uri="ui://geox/well-forensic-desk.html",
        )

    return compact_envelope(
        tool="geox_well",
        verdict=verdict,
        epistemic="OBS",
        summary=f"{well_name} forensic audit: {len(fault_codes)} fault(s) [{', '.join(fault_codes) or 'NONE'}]; {quarantine_count} QUARANTINE.",
        defaults_applied=["lag_threshold_m=0.5", "min_pearson_r=0.85", "oh_sep_threshold_vv=0.14"],
        falsifiers=[
            "Calibrated multi-run tie + core XRD + SWC nannofossil ranges + checkshot_flag=1 clear QUARANTINE."
        ],
        data={
            "well": well_name,
            "fault_codes": fault_codes,
            "quarantine_count": quarantine_count,
            "quarantine_matrix": quarantine_rows,
            "faults": faults,
        },
        artifact_uri="ui://geox/well-forensic-desk.html",
    )
