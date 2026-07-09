#!/usr/bin/env python3
"""P1 — Monte Carlo STOIIP/EMV from Marmousi LAS-derived φ/NTG (GENESIS/014).

Uses compute_las_physics (DER from curves) → stoiip_monte_carlo → emv_from_stoiip_mc.
Not a 3D GRV grid. Volumes are factor MC; label honestly.

Usage:
  PYTHONPATH=src python scripts/marmousi2_stoiip_mc_p1.py
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geox_core.benchmarks.geox_001_las_physics import compute_las_physics
from geox_core.wealth.volumetric_mc import emv_from_stoiip_mc, stoiip_monte_carlo

DATA = ROOT / "data"
WELLS = {
    "MARMOUSI2-X1500": DATA / "marmousi-well-x1500.las",
    "MARMOUSI2-X5000": DATA / "marmousi-well-x5000.las",
    "MARMOUSI2-X10000": DATA / "marmousi-well-x10000.las",
}

# Synthetic prospect geometry for known-answer volume exercise (SPEC)
# Not Marmousi field size — fixed trap assumptions so MC stress-tests φ/NTG from logs.
TRAP_SPEC = {
    "area_km2": {"p10": 12.0, "p50": 8.0, "p90": 5.0},
    "h_m": {"p10": 80.0, "p50": 50.0, "p90": 30.0},
    "so": {"p10": 0.75, "p50": 0.65, "p90": 0.50},
    "bo": {"p10": 1.15, "p50": 1.25, "p90": 1.40},
    "pos": 0.30,
    "value_per_mmstb_usd_mm": 10.0,
    "dry_hole_cost_usd_mm": 40.0,
    "recovery_factor": 0.30,
}


def load_las_curves(path: Path) -> dict[str, np.ndarray]:
    lines = path.read_text().splitlines()
    in_a = False
    depth, vp, rhob = [], [], []
    for line in lines:
        if line.startswith("~A"):
            in_a = True
            continue
        if not in_a or not line.strip():
            continue
        p = line.split()
        if len(p) < 4:
            continue
        d, v, _s, r = map(float, p[:4])
        if v <= 0:
            continue
        depth.append(d)
        vp.append(v)
        rhob.append(r)
    d_a = np.asarray(depth, dtype=float)
    v_a = np.asarray(vp, dtype=float)
    r_a = np.asarray(rhob, dtype=float)
    # DT from Vp for Wyllie path: us/ft ≈ 1e6/Vp_ft_s; Vp m/s → us/ft = 304800/Vp
    dt = 304800.0 / np.clip(v_a, 100.0, 8000.0)
    return {"DEPT": d_a, "DT": dt, "RHOB": r_a, "VP": v_a}


def main() -> int:
    rows = []
    for well_id, path in WELLS.items():
        if not path.exists():
            print(f"SKIP missing {path}")
            continue
        curves = load_las_curves(path)
        phys = compute_las_physics(curves, dt_unit="usft")
        pe = phys["stats"]["phi_e"]
        ntg = float(phys["stats"]["net_to_gross"])
        # φ distributions from log percentiles; widen NTG slightly for MC
        phi_p50 = float(pe["p50"])
        phi_p10 = float(pe.get("p10") or phi_p50 * 1.15)
        phi_p90 = float(pe.get("p90") or phi_p50 * 0.85)
        # ensure p10 high / p90 low for volume convention
        phi_hi, phi_lo = max(phi_p10, phi_p50, phi_p90), min(phi_p10, phi_p50, phi_p90)
        phi_mid = float(np.median([phi_p10, phi_p50, phi_p90]))

        ntg_p50 = max(0.05, min(0.98, ntg))
        ntg_p10 = min(0.99, ntg_p50 * 1.05)
        ntg_p90 = max(0.05, ntg_p50 * 0.85)

        mc = stoiip_monte_carlo(
            area_km2_p10=TRAP_SPEC["area_km2"]["p10"],
            area_km2_p50=TRAP_SPEC["area_km2"]["p50"],
            area_km2_p90=TRAP_SPEC["area_km2"]["p90"],
            h_m_p10=TRAP_SPEC["h_m"]["p10"],
            h_m_p50=TRAP_SPEC["h_m"]["p50"],
            h_m_p90=TRAP_SPEC["h_m"]["p90"],
            ntg_p10=ntg_p10,
            ntg_p50=ntg_p50,
            ntg_p90=ntg_p90,
            phi_p10=phi_hi,
            phi_p50=phi_mid,
            phi_p90=phi_lo,
            so_p10=TRAP_SPEC["so"]["p10"],
            so_p50=TRAP_SPEC["so"]["p50"],
            so_p90=TRAP_SPEC["so"]["p90"],
            bo_p10=TRAP_SPEC["bo"]["p10"],
            bo_p50=TRAP_SPEC["bo"]["p50"],
            bo_p90=TRAP_SPEC["bo"]["p90"],
            n_sims=5000,
            seed=42 + hash(well_id) % 1000,
        )
        emv = emv_from_stoiip_mc(
            mc,
            pos=TRAP_SPEC["pos"],
            value_per_mmstb_usd_mm=TRAP_SPEC["value_per_mmstb_usd_mm"],
            dry_hole_cost_usd_mm=TRAP_SPEC["dry_hole_cost_usd_mm"],
            recovery_factor=TRAP_SPEC["recovery_factor"],
        )
        row = {
            "well_id": well_id,
            "las": path.name,
            "phi_e": {
                "p10": round(phi_hi, 4),
                "p50": round(phi_mid, 4),
                "p90": round(phi_lo, 4),
                "source": "DER_FROM_LAS_CURVES",
            },
            "ntg_log": round(ntg_p50, 4),
            "stoiip_mmstb": mc["stoiip_mmstb"],
            "recoverable_mmstb": emv["recoverable_mmstb"],
            "emv_usd_mm": emv["emv_usd_mm"],
            "pos": emv["pos"],
            "epistemic": {
                "phi_ntg": "DER",
                "trap_geometry": "SPEC",
                "pos": "INT",
                "emv": "DER",
            },
        }
        rows.append(row)
        print(
            f"{well_id}: φ_e P50={phi_mid:.3f} NTG={ntg_p50:.3f} "
            f"STOIIP P50={mc['stoiip_mmstb']['p50']:.2f} MMstb "
            f"EMV={emv['emv_usd_mm']:.1f} MMUSD"
        )

    summary = {
        "phase": "P1_MONTE_CARLO_STOIIP",
        "doctrine": "GENESIS/014 — after P0 LAS physics",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "trap_geometry_note": "SPEC fixed synthetic trap — volume factors stress-test φ/NTG from Marmousi logs, not a real prospect map",
        "anti_hantu": [
            "STOIIP is not grid GRV",
            "POS is INT assumption 0.30",
            "Marmousi is known-answer elastic model — φ high is model water+soft sediment, not Malay Basin reservoir",
        ],
        "wells": rows,
        "overall": "PASS" if len(rows) == 3 else "PARTIAL",
    }

    out_json = Path("/root/A-FORGE/forge_work/2026-07-09/MARMOUSI2-P1-STOIIP-MC.json")
    out_md = Path("/root/A-FORGE/forge_work/2026-07-09/MARMOUSI2-P1-STOIIP-MC.md")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2))

    lines = [
        "# Marmousi2 P1 — Monte Carlo STOIIP / EMV",
        "",
        f"**Status:** {summary['overall']} · {summary['timestamp_utc']}",
        "",
        "φ and NTG from `compute_las_physics` (DER). Trap geometry SPEC (fixed).",
        "",
        "| Well | φ_e P50 | NTG | STOIIP P90 | P50 | P10 | EMV (MMUSD) |",
        "|------|---------|-----|------------|-----|-----|-------------|",
    ]
    for r in rows:
        s = r["stoiip_mmstb"]
        lines.append(
            f"| {r['well_id']} | {r['phi_e']['p50']:.3f} | {r['ntg_log']:.3f} | "
            f"{s['p90']:.1f} | {s['p50']:.1f} | {s['p10']:.1f} | {r['emv_usd_mm']:.1f} |"
        )
    lines += [
        "",
        "## Epistemic",
        "- φ / NTG: **DER** from LAS curves",
        "- Area / thickness: **SPEC** (exercise only)",
        "- POS: **INT** 0.30",
        "- EMV: **DER** from MC volumes × POS",
        "",
        "Next (P2): spatial ToAC — prospect-local, not basin depocenter.",
        "",
        f"JSON: `{out_json}`",
        "",
        "*GENESIS/014 · DITEMPA BUKAN DIBERI*",
    ]
    out_md.write_text("\n".join(lines) + "\n")
    # also docs
    docs = ROOT / "docs" / "benchmarks" / "MARMOUSI2-P1-STOIIP-MC.md"
    docs.write_text(out_md.read_text())
    print("OVERALL", summary["overall"])
    print("→", out_json)
    print("→", out_md)
    return 0 if len(rows) == 3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
