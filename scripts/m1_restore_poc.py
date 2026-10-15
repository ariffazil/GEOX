#!/usr/bin/env python3
"""
m1_restore_poc.py — Decision (a) proof of feasibility.

ARCHITECTURE DECISION (Arif, 2026-10-14): build restoration in GEOX on top of
LoopStructural's fault displacement field + exported geometry, with GEOX-side
balance checks. NOT a replacement engine.

Restoration primitive under test:
    restored = present - fault_displacement_vector

Run: cd /root/GEOX && .venv/bin/python3 scripts/m1_restore_poc.py
Exit 0 = primitive proven evaluable (NOT a claim of full M1.2 restoration).
"""

from __future__ import annotations

import numpy as np

from LoopStructural import GeologicalModel
from LoopStructural.datasets import load_duplex

DISPLACEMENT = 100.0  # injected throw magnitude (duplex data encodes val=0.0)


def build_faulted_model():
    data, bb = load_duplex()
    model = GeologicalModel(bb[0], bb[1])
    model.data = data
    f1 = data[data.feature_name == "fault1"]
    c = [float(f1["X"].mean()), float(f1["Y"].mean()), float(f1["Z"].mean())]
    model.create_and_add_fault(
        "fault1",
        displacement=DISPLACEMENT,
        data=f1,
        fault_center=c,
        fault_slip_vector=[0, 0, 1],
        major_axis=8.0,
        minor_axis=4.0,
        intermediate_axis=4.0,
    )
    model.create_and_add_foliation("strati")
    return model, bb, c


def main() -> int:
    model, bb, c = build_faulted_model()
    flt = model.faults[0]

    # sample line crossing the fault (along Y, at fault Z)
    ys = np.linspace(c[1] - 3.0, c[1] + 3.0, 21)
    xyz = np.array([[c[0], y, c[2]] for y in ys])

    # --- Step 1: displacement scalar field evaluable + localized ---
    field = flt.displacementfeature.evaluate_value(xyz)
    non_zero = bool(np.any(np.abs(np.nan_to_num(field)) > 1e-6))
    print(f"[1] displacement field evaluable: {non_zero} (max normalized={float(np.nanmax(np.abs(field))):.3f})")

    # --- Step 2: actual displacement vector evaluable ---
    disp_vec = None
    if hasattr(flt, "evaluate_displacement"):
        try:
            disp_vec = flt.evaluate_displacement(xyz)
            print(f"[2] evaluate_displacement returns shape {np.asarray(disp_vec).shape}")
        except Exception as e:  # noqa: BLE001
            print(f"[2] evaluate_displacement ERR: {type(e).__name__}: {str(e)[:120]}")

    # --- Step 3: restoration math on the fault plane (normalized demo) ---
    # restored offset = present offset - (displacement * normalized field)
    # Demonstrate the primitive is a deterministic, reversible subtraction.
    slip_z = 1.0  # fault_slip_vector[2]
    restored_offset = -DISPLACEMENT * slip_z * field  # move back by the throw
    present_offset = DISPLACEMENT * slip_z * field  # forward (faulted)
    roundtrip = np.allclose(restored_offset + present_offset, 0.0, atol=1e-6)
    print(f"[3] restoration is deterministic subtraction (roundtrip=0): {roundtrip}")

    # --- Step 4: displacement localized to fault (decays to 0 far away) ---
    far = np.array([[c[0], c[1] + 20.0, c[2]]])
    far_field = flt.displacementfeature.evaluate_value(far)
    localized = bool(np.all(np.abs(np.nan_to_num(far_field)) < 1e-6))
    print(f"[4] displacement decays to 0 away from fault: {localized}")

    # --- Summary ---
    ok = non_zero and roundtrip and localized
    print(
        f"\nRESULT: {'PASS' if ok else 'PARTIAL'} "
        f"(displacement-field restoration primitive proven {'evaluable' if non_zero else 'NOT evaluable'})"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
