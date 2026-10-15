#!/usr/bin/env python3
"""
m1_restore_pipeline.py — end-to-end M1.2 restoration from a synthetic fixture.

Load SYNTHETIC_M1_2d_line.json (GATE C) -> build present-day faulted surface
-> restore_surface() (pure GEOX) -> verify throw removed + balance + >=3 hypotheses
-> RestorationBundle.

Run: cd /root/GEOX && PYTHONPATH=src .venv/bin/python3 scripts/m1_restore_pipeline.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from geox_core.engines.structural_restoration.restore import (
    competing_restorations,
    line_length,
    max_throw,
    restore_surface,
)
from geox_core.schemas.restoration_bundle import RestorationBundle

FIXTURE = Path("/root/GEOX/fixtures/SYNTHETIC_M1_2d_line.json")


def load_fixture(path: Path) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    doc = json.loads(path.read_text())
    fw = doc["horizon"]["footwall_points_xz"]
    hw = doc["horizon"]["hanging_wall_points_xz"]
    pts = np.array([[x, 0.0, z] for x, z in fw + hw])
    field = np.array([0.0] * len(fw) + [1.0] * len(hw))
    throw = float(doc["fault"]["throw"])
    slip = np.array(doc["fault"]["slip_vector"], dtype=float)
    return pts, field, throw, slip


def main() -> int:
    pts, field, throw, slip = load_fixture(FIXTURE)
    restored = restore_surface(pts, field, throw, slip)

    throw_faulted = max_throw(pts[:, 2])
    throw_restored = max_throw(restored[:, 2])
    len_faulted = line_length(pts)
    len_restored = line_length(restored)

    print(f"fixture: {FIXTURE.name} | pts={len(pts)} | throw={throw:.0f}")
    print(f"[1] faulted throw  = {throw_faulted:.1f}  ->  restored throw = {throw_restored:.3f}")
    print(f"[2] length: faulted={len_faulted:.2f}  restored={len_restored:.2f}  (jump removed: {len_restored < len_faulted})")

    hyps = competing_restorations(pts, field, throw, slip)
    bundle = RestorationBundle(
        epistemic_class="HYPOTHESIS",
        lifecycle_state="DERIVED_CANDIDATE",
        explanation_class="UNCLASSIFIED",
        hypotheses=hyps,
        preferred_model=None,
        assumptions=[f"synthetic faulted horizon from {FIXTURE.name}"],
        limitations=["synthetic geometry — no geological validity claimed"],
        falsifiers=["restored throw > 5% of fixture throw"],
        reversal_conditions=["re-apply throw via fault_surface recovers present-day"],
        provenance=["gen_synthetic_m1_fixture.py", "restore.py", "m1_restore_pipeline.py"],
        receipt_id=None,
        ui_resource_uri=None,
    )
    print(
        f"[3] RestorationBundle: hypotheses={len(bundle.hypotheses)}, preferred_null={bundle.preferred_model is None}, "
        f"lifecycle={bundle.lifecycle_state}"
    )

    ok = (
        (throw_faulted > 0.9 * throw)
        and (throw_restored < 0.05 * throw)
        and (len_restored < len_faulted)
        and (len(hyps) == 3)
        and (bundle.preferred_model is None)
    )
    print(
        f"\nRESULT: {'PASS' if ok else 'FAIL'} — end-to-end restoration from synthetic fixture {'proven' if ok else 'NOT proven'}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
