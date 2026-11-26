"""Deterministic synthetic corrupted-LAS well pack generator (SYNTH-DW-01, seed=42).

100% synthetic public test fixture — zero corporate/operator identifiers.
Injects all 8 forensic defect classes for Phase D verification.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


def _write_las2(
    path: Path,
    *,
    well: str,
    uwi: str,
    start_m: float,
    stop_m: float,
    step_m: float,
    null_val: float,
    kb_m: float,
    wd_m: float,
    curves: list[tuple[str, str, str]],
    data: np.ndarray,
) -> None:
    lines = [
        "~VERSION INFORMATION",
        " VERS.                          2.0 : CWLS LOG ASCII STANDARD - VERSION 2.0",
        " WRAP.                           NO : ONE LINE PER DEPTH STEP",
        "~WELL INFORMATION",
        f" STRT.M                {start_m:10.4f} : START DEPTH",
        f" STOP.M                {stop_m:10.4f} : STOP DEPTH",
        f" STEP.M                {step_m:10.4f} : STEP",
        f" NULL.                 {null_val:10.4f} : NULL VALUE",
        f" WELL.                 {well:<20} : WELL NAME",
        f" UWI .                 {uwi:<20} : UNIQUE WELL ID",
        f" KB  .M                {kb_m:10.2f} : KELLY BUSHING",
        f" WD  .M                {wd_m:10.2f} : WATER DEPTH",
        "~CURVE INFORMATION",
    ]
    for mnem, unit, desc in curves:
        lines.append(f" {mnem:<12}.{unit:<8}              : {desc}")
    lines.append("~ASCII")
    for row in data:
        lines.append(" " + " ".join(f"{v:12.4f}" for v in row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_synth_dw_01(out_dir: Path, seed: int = 42) -> Path:
    """Generate SYNTH-DW-01 multi-file pack with all 8 injected defects."""
    rng = np.random.default_rng(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Full well depth grid: 1500.0 to 3200.0 m MD at 0.5 m step (3401 samples)
    depth = np.arange(1500.0, 3200.0 + 0.25, 0.5)
    n = len(depth)

    # Base realistic GR signal with clear stratigraphic markers for cross-correlation
    gr_base = (
        65.0
        + 25.0 * np.sin((depth - 1500.0) / 45.0)
        + 18.0 * np.exp(-((depth - 2050.0) ** 2) / 180.0)
        - 28.0 * np.exp(-((depth - 2450.0) ** 2) / 220.0)
        + 22.0 * np.exp(-((depth - 2900.0) ** 2) / 160.0)
        + rng.normal(0.0, 1.2, size=n)
    )
    gr_base = np.clip(gr_base, 15.0, 140.0)

    # Defect 1: KB_DATUM_SHIFT — Run 1 GR_R1 shifted by exact +30.0 m (60 samples)
    shift_samples = 60  # 30.0 m / 0.5 m
    gr_r1 = np.empty_like(gr_base)
    gr_r1[shift_samples:] = gr_base[:-shift_samples]
    gr_r1[:shift_samples] = gr_base[0]
    gr_r2 = gr_base.copy()
    gr_spliced = gr_base.copy()

    # Defect 5b: 9.5% null blindspot inside GR_FULL
    gr_full = gr_base.copy()
    n_null = int(round(0.095 * n))
    gr_full[800 : 800 + n_null] = -999.25

    # Normal petrophysics + Defect 7 (ROCK_PHYSICS_TRAP at 2800-3100 m MD)
    trap_mask = (depth >= 2800.0) & (depth <= 3100.0)
    vp_ms = np.where(trap_mask, 2850.0, 2200.0) + rng.normal(0.0, 20.0, size=n)  # +650 m/s jump
    vpvs_true = np.where(trap_mask, 2.02, 2.95) + rng.normal(0.0, 0.03, size=n)
    rhob = np.where(trap_mask, rng.uniform(1.95, 2.10, size=n), rng.uniform(2.25, 2.42, size=n))
    phie_nmr = np.where(trap_mask, 0.16, 0.22) + rng.normal(0.0, 0.008, size=n)
    nphi_true = np.where(trap_mask, phie_nmr + 0.20, phie_nmr + 0.02)  # +0.20 v/v excess clay-bound water
    rt = np.where(trap_mask, rng.uniform(1.5, 2.4, size=n), rng.uniform(3.0, 8.0, size=n))
    sw = np.where(trap_mask, 1.0, 0.65)

    # Defect 2: UNIT_FACTOR_32808 — VPVS_CORRUPT = vpvs_true * 3.28084 (~6.6-10.2)
    vpvs_corrupt = vpvs_true * 3.28084

    # Defect 3: POROSITY_X100_MISMATCH — NPHI_BAD labeled v/v but numeric values in % (18-44)
    nphi_bad = np.clip(nphi_true * 100.0, 18.0, 44.0)

    # Defect 4: SONIC_UNIT_HEADER_LIE — DTCO_BAD labeled US/M but values in us/ft (70-135)
    dtco_bad = np.clip(304800.0 / vp_ms, 70.0, 135.0)

    # File 1: Run 1 LAS (UWI 99900001, shifted GR_R1 + corrupt curves)
    _write_las2(
        out_dir / "SYNTH-DW-01_run1.las",
        well="SYNTH-DW-01",
        uwi="99900001",
        start_m=1500.0,
        stop_m=3200.0,
        step_m=0.5,
        null_val=-999.25,
        kb_m=30.0,
        wd_m=1500.0,
        curves=[
            ("DEPT", "M", "MEASURED DEPTH"),
            ("GR_R1", "GAPI", "GAMMA RAY RUN 1 (SHIFTED +30M)"),
            ("VPVS_CORRUPT", "V/V", "VP/VS CORRUPTED BY 3.28084"),
            ("NPHI_BAD", "v/v", "NEUTRON POROSITY (PERCENT LABELED V/V)"),
            ("DTCO_BAD", "US/M", "COMPRESSIONAL SLOWNESS (US/FT LABELED US/M)"),
        ],
        data=np.column_stack([depth, gr_r1, vpvs_corrupt, nphi_bad, dtco_bad]),
    )

    # File 2: Run 2 LAS (UWI 99900002 -> Defect 6 UWI conflict, GR_R2, GR_SPLICED, GR_FULL, rock-physics trap curves)
    _write_las2(
        out_dir / "SYNTH-DW-01_run2.las",
        well="SYNTH-DW-01",
        uwi="99900002",
        start_m=1500.0,
        stop_m=3200.0,
        step_m=0.5,
        null_val=-999.25,
        kb_m=30.0,
        wd_m=1500.0,
        curves=[
            ("DEPT", "M", "MEASURED DEPTH"),
            ("GR_R2", "GAPI", "GAMMA RAY RUN 2"),
            ("GR_SPLICED", "GAPI", "GAMMA RAY SPLICED"),
            ("GR_FULL", "GAPI", "GAMMA RAY WITH 9.5% BLINDSPOT"),
            ("VP", "M/S", "P-WAVE VELOCITY"),
            ("VPVS", "V/V", "VP/VS RATIO"),
            ("RHOB", "G/C3", "BULK DENSITY"),
            ("NPHI", "v/v", "NEUTRON POROSITY"),
            ("PHIE_NMR", "v/v", "NMR EFFECTIVE POROSITY"),
            ("RT", "OHMM", "TRUE RESISTIVITY"),
            ("SW", "v/v", "WATER SATURATION"),
        ],
        data=np.column_stack([depth, gr_r2, gr_spliced, gr_full, vp_ms, vpvs_true, rhob, nphi_true, phie_nmr, rt, sw]),
    )

    # Defect 6b: Valid LAS 2.0 file intentionally named .csv
    _write_las2(
        out_dir / "SYNTH-DW-01_disguised_las.csv",
        well="SYNTH-DW-01",
        uwi="99900002",
        start_m=1500.0,
        stop_m=1510.0,
        step_m=0.5,
        null_val=-999.25,
        kb_m=30.0,
        wd_m=1500.0,
        curves=[("DEPT", "M", "MEASURED DEPTH"), ("GR_CHK", "GAPI", "CHECK GR")],
        data=np.column_stack([depth[:21], gr_r2[:21]]),
    )

    # Defect 5a: Three 1-sample stub LAS files with mixed sentinels (9999, 98765, -999.25)
    for idx, sent in enumerate((9999.0, 98765.0, -999.25), 1):
        _write_las2(
            out_dir / f"SYNTH-DW-01_stub{idx}.las",
            well="SYNTH-DW-01",
            uwi="99900001",
            start_m=2000.0,
            stop_m=2000.0,
            step_m=0.0,
            null_val=-999.25,
            kb_m=30.0,
            wd_m=1500.0,
            curves=[("DEPT", "M", "MEASURED DEPTH"), ("GR_STUB", "GAPI", "STUB CURVE")],
            data=np.array([[2000.0, sent]]),
        )

    # Defect 6c: Checkshot/TDR sidecar with CHECKSHOT_FLAG=0
    (out_dir / "SYNTH-DW-01_tdr.json").write_text(
        json.dumps(
            {
                "well": "SYNTH-DW-01",
                "CHECKSHOT_FLAG": 0,
                "source": "synthetic_sonic_integration_only",
                "points": [{"md_m": 1500.0, "twt_ms": 2000.0}, {"md_m": 3200.0, "twt_ms": 3450.0}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Defect 8: STRAT_AGE_INVERSION — 10.5 Ma marker deeper than 13.5 Ma marker
    (out_dir / "SYNTH-DW-01_tops.json").write_text(
        json.dumps(
            {
                "well": "SYNTH-DW-01",
                "tops": [
                    {"marker": "Top_Late_Miocene", "depth_m": 2100.0, "age_ma": 8.5, "zone": "NN11", "sample_type": "swc"},
                    {"marker": "Top_Mid_Miocene_A", "depth_m": 2550.0, "age_ma": 13.5, "zone": "NN6", "sample_type": "cuttings"},
                    {"marker": "Top_Mid_Miocene_B", "depth_m": 2850.0, "age_ma": 10.5, "zone": "NN9", "sample_type": "cuttings"},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return out_dir


def generate_clean_control(out_dir: Path, seed: int = 42) -> Path:
    """Generate clean SYNTH-CLEAN-01 control pack with 0 defects."""
    rng = np.random.default_rng(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    depth = np.arange(1500.0, 2100.0 + 0.25, 0.5)
    n = len(depth)
    gr = np.clip(60.0 + 20.0 * np.sin((depth - 1500.0) / 40.0) + rng.normal(0.0, 0.8, size=n), 20.0, 120.0)
    vp = np.full(n, 2400.0) + rng.normal(0.0, 15.0, size=n)
    vpvs = np.full(n, 2.15) + rng.normal(0.0, 0.02, size=n)
    rhob = np.full(n, 2.38) + rng.normal(0.0, 0.02, size=n)
    phie_nmr = np.full(n, 0.21) + rng.normal(0.0, 0.005, size=n)
    nphi = phie_nmr + 0.02
    dtco = 304800.0 / vp  # us/ft properly labeled US/F
    rt = np.full(n, 6.5) + rng.normal(0.0, 0.2, size=n)
    sw = np.full(n, 0.45)

    _write_las2(
        out_dir / "SYNTH-CLEAN-01.las",
        well="SYNTH-CLEAN-01",
        uwi="99999901",
        start_m=1500.0,
        stop_m=2100.0,
        step_m=0.5,
        null_val=-999.25,
        kb_m=25.0,
        wd_m=1000.0,
        curves=[
            ("DEPT", "M", "MEASURED DEPTH"),
            ("GR_R1", "GAPI", "GAMMA RAY RUN 1"),
            ("GR_R2", "GAPI", "GAMMA RAY RUN 2"),
            ("VP", "M/S", "P-WAVE VELOCITY"),
            ("VPVS", "V/V", "VP/VS RATIO"),
            ("RHOB", "G/C3", "BULK DENSITY"),
            ("NPHI", "v/v", "NEUTRON POROSITY"),
            ("PHIE_NMR", "v/v", "NMR EFFECTIVE POROSITY"),
            ("DTCO", "US/F", "COMPRESSIONAL SLOWNESS"),
            ("RT", "OHMM", "TRUE RESISTIVITY"),
            ("SW", "v/v", "WATER SATURATION"),
        ],
        data=np.column_stack([depth, gr, gr, vp, vpvs, rhob, nphi, phie_nmr, dtco, rt, sw]),
    )
    (out_dir / "SYNTH-CLEAN-01_tdr.json").write_text(
        json.dumps({"well": "SYNTH-CLEAN-01", "CHECKSHOT_FLAG": 1}, indent=2), encoding="utf-8"
    )
    (out_dir / "SYNTH-CLEAN-01_tops.json").write_text(
        json.dumps(
            {
                "well": "SYNTH-CLEAN-01",
                "tops": [
                    {"marker": "Top_A", "depth_m": 1650.0, "age_ma": 8.5, "zone": "NN11", "sample_type": "swc"},
                    {"marker": "Top_B", "depth_m": 1950.0, "age_ma": 12.5, "zone": "NN7", "sample_type": "swc"},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return out_dir


if __name__ == "__main__":
    p = generate_synth_dw_01(Path("/tmp/synth_dw_01"))
    print(f"Generated SYNTH-DW-01 pack at {p}")
