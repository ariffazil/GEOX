#!/usr/bin/env python3
"""
m1_restore_surface.py — first real 2D restoration proof (pure-GEOX, self-contained).

Proves the GEOX restoration primitive end-to-end WITHOUT relying on LoopStructural's
surface-faulting (which smooths across the fault instead of producing a clean throw —
see LOOPSTRUCTURAL_REALITY_AUDIT.md). GEOX does BOTH directions:

    fault:    present  = restored + throw * field * slip   (forward)
    restore:  restored = present  - throw * field * slip   (backward)  == identity

Assertions:
  1. restore(fault(flat)) == flat (throw removed, reversible)
  2. restored length < faulted length (the vertical throw jump is removed)
  3. >=3 competing hypotheses
  4. preferred_model stays null

Run: cd /root/GEOX && PYTHONPATH=src .venv/bin/python3 scripts/m1_restore_surface.py
"""

from __future__ import annotations

import numpy as np

from geox_core.engines.structural_restoration.restore import (
    competing_restorations,
    line_length,
    max_throw,
    restore_surface,
)
from geox_core.schemas.restoration_bundle import RestorationBundle

THROW = 50.0
SLIP = np.array([0.0, 0.0, 1.0])  # vertical slip


def build_flat_surface(nx=61, xmin=-3.0, xmax=3.0, z=0.0) -> np.ndarray:
    """A continuous flat layer polyline (N,3) at z=const."""
    x = np.linspace(xmin, xmax, nx)
    return np.column_stack([x, np.zeros(nx), np.full(nx, z)])


def fault_surface(restored: np.ndarray, field: np.ndarray, throw: float, slip: np.ndarray) -> np.ndarray:
    """Forward model: apply a fault throw to a restored surface."""
    return restored + throw * field[:, None] * slip[None, :]


def main() -> int:
    flat = build_flat_surface()
    # geometric displacement field: footwall=0, hanging wall=1 (step at x=0)
    field = np.where(flat[:, 0] > 0.0, 1.0, 0.0)

    # 1. forward fault, then restore
    faulted = fault_surface(flat, field, THROW, SLIP)
    restored = restore_surface(faulted, field, THROW, SLIP)

    roundtrip = np.allclose(restored, flat, atol=1e-9)
    throw_faulted = max_throw(faulted[:, 2])
    throw_restored = max_throw(restored[:, 2])
    len_flat = line_length(flat)
    len_faulted = line_length(faulted)
    len_restored = line_length(restored)

    print(f"[1] faulted throw    = {throw_faulted:.1f}  (flat 0 -> hanging wall +{THROW:.0f})")
    print(f"[1] restored throw   = {throw_restored:.4f}  (round-trip returns flat: {roundtrip})")
    print(f"[2] length: flat={len_flat:.2f}  faulted={len_faulted:.2f}  restored={len_restored:.2f}")
    print(f"[2] throw jump removed: restored < faulted -> {len_restored < len_faulted}")

    # 3. >=3 competing hypotheses (perturbed throw)
    hyps = competing_restorations(faulted, field, THROW, SLIP)
    print(f"[3] hypotheses = {len(hyps)}: " + ", ".join(f"throw={h['throw']:.0f}" for h in hyps))

    # 4. RestorationBundle
    bundle = RestorationBundle(
        epistemic_class="HYPOTHESIS",
        lifecycle_state="DERIVED_CANDIDATE",
        explanation_class="UNCLASSIFIED",
        hypotheses=hyps,
        preferred_model=None,
        assumptions=["synthetic flat layer, vertical fault, pure dip-slip"],
        limitations=["synthetic geometry only — no geological validity claimed"],
        falsifiers=["restored != flat beyond 1e-9"],
        reversal_conditions=["fault_surface(restored, field, +throw, slip) recovers present-day"],
        provenance=["restore.py (pure GEOX)", "m1_restore_surface.py"],
        receipt_id=None,
        ui_resource_uri=None,
    )
    print(
        f"[4] RestorationBundle: hypotheses={len(bundle.hypotheses)}, preferred_null={bundle.preferred_model is None}, "
        f"epistemic={bundle.epistemic_class}, authority={bundle.authority_ceiling}"
    )

    ok = (
        roundtrip
        and (throw_restored < 1e-6)
        and (len_restored < len_faulted)
        and (len(hyps) == 3)
        and (bundle.preferred_model is None)
    )
    print(
        f"\nRESULT: {'PASS' if ok else 'FAIL'} — restoration primitive "
        f"{'proven reversible, balanced, Chamberlin-compliant' if ok else 'NOT proven'}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
