"""Audit extraction — KL2 kinabalu_synth fixture → QC samples + summary.

F2 evidence builder for the 2026-09-07 penetration-chart audit.
Imports the fixture directly (no transcription), computes per-well T-D
physics, writes wells_summary.json + qc_samples.csv.
"""
import importlib.util
import json
import csv
import math

FIXTURE = "/root/GEOX/tests/fixtures/kinabalu_synth.py"
OUT = "/root/GEOX/outputs/kl2_kinabalu"

spec = importlib.util.spec_from_file_location("kinabalu_synth", FIXTURE)
ks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ks)

rows_csv = []
summary = {"wells": {}, "qc": {}}

for name in ks.list_wells():
    cfg = ks.get_well_config(name)
    cs = ks.get_synthetic_checkshot(name)
    v_ints, dv_dz_max, twt_mono, depth_mono = [], 0.0, True, True
    prev_z = prev_t = None
    for pt in cs:
        z, t = pt["depth_md"], pt["twt_ms"]
        rows_csv.append({
            "well": name, "depth_md": round(z, 2), "twt_ms": round(t, 2),
            "v_avg_ms": round(2 * z / (t / 1000.0), 1) if t > 0 else None,
        })
        if prev_z is not None:
            dz, dt = z - prev_z, t - prev_t
            if dt > 0:
                vi = 2 * dz / (dt / 1000.0)
                v_ints.append(vi)
                dv_dz_max = max(dv_dz_max, abs(vi - (v_ints[-2] if len(v_ints) > 1 else vi)) / dz if dz else 0)
            if t <= prev_t:
                twt_mono = False
            if z <= prev_z:
                depth_mono = False
        prev_z, prev_t = z, t
    td = cfg["z_range"][1]
    summary["wells"][name] = {
        "type": cfg["type"], "deviated": cfg["deviated"],
        "max_incl_deg": cfg.get("max_inclination_deg"),
        "td_tvdss_m": td, "twt_at_td_ms": cfg["twt_at_td"],
        "n_checkshot": len(cs),
        "v_int_range": [round(min(v_ints), 1), round(max(v_ints), 1)] if v_ints else None,
        "v_avg_at_td_ms": round(2 * td / (cfg["twt_at_td"] / 1000.0), 1),
    }
    summary["qc"][name] = {
        "depth_monotonic": depth_mono, "twt_monotonic": twt_mono,
        "v_int_within_1500_5000": bool(v_ints and min(v_ints) >= 1500 and max(v_ints) <= 5000),
        "v_avg_within_1800_3500": 1800 <= 2 * td / (cfg["twt_at_td"] / 1000.0) <= 3500,
    }

with open(f"{OUT}/wells_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
with open(f"{OUT}/qc_samples.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["well", "depth_md", "twt_ms", "v_avg_ms"])
    w.writeheader()
    w.writerows(rows_csv)

print(json.dumps(summary, indent=2))
print(f"\nrows={len(rows_csv)}")
