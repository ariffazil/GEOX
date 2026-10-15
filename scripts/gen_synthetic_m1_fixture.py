#!/usr/bin/env python3
"""gen_synthetic_m1_fixture.py — deterministic synthetic faulted 2D horizon (GATE C #1).

SYNTHETIC ONLY. No PETRONAS names/coords/wells. No geological-validity claim.
Purpose limited to schema / adapter / invariants / failure-path testing.
Deterministic seed + generator provenance for reproducibility.

Run: cd /root/GEOX && .venv/bin/python3 scripts/gen_synthetic_m1_fixture.py
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import numpy as np

SEED = "m1-line-0001"
THROW = 50.0
FAULT_X = 0.0
OUT = Path("/root/GEOX/fixtures/SYNTHETIC_M1_2d_line.json")


def gen() -> tuple[list[list[float]], list[list[float]]]:
    rng = np.random.default_rng(int.from_bytes(SEED.encode(), "big") % (2**32))
    fw_x = np.linspace(-4.0, -0.2, 20)
    hw_x = np.linspace(0.2, 4.0, 20)
    jitter = rng.normal(0.0, 0.3, size=40)
    footwall = [[float(x), float(0.0 + j)] for x, j in zip(fw_x, jitter[:20], strict=False)]
    hanging = [[float(x), float(THROW + j)] for x, j in zip(hw_x, jitter[20:], strict=False)]
    return footwall, hanging


def main() -> int:
    footwall, hanging = gen()
    doc = {
        "synthetic": True,
        "generator": "scripts/gen_synthetic_m1_fixture.py",
        "seed": SEED,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "purpose": ["schema", "adapter", "invariants", "failure_path"],
        "geological_validity": "NONE",
        "no_petronas": True,
        "fault": {
            "x": FAULT_X,
            "throw": THROW,
            "slip_vector": [0.0, 0.0, 1.0],
            "dip_deg": 90.0,
            "normal": [1.0, 0.0, 0.0],
        },
        "horizon": {
            "name": "SYNTHETIC_H1",
            "footwall_points_xz": footwall,  # z ~ 0
            "hanging_wall_points_xz": hanging,  # z ~ THROW
        },
        "note": "content hash computed externally; not self-referential",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n")
    print(f"wrote {OUT} | footwall={len(footwall)} pts | hanging={len(hanging)} pts | throw={THROW:.0f} | seed={SEED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
