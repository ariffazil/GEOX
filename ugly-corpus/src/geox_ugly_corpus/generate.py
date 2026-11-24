"""Deterministic synthetic LAS 2.0 fixture generation.

No network, no real data, no timestamps: the same seed produces the same bytes
on every machine, which is what makes the SHA-256 manifest meaningful.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from pathlib import Path

from . import SEED, __version__

NULL_VALUE = -999.25


@dataclass(frozen=True)
class Fixture:
    name: str
    path: Path
    sha256: str
    curves: tuple[str, ...]
    # What this fixture is for, kept beside the bytes so a reader never has to
    # guess why an ugly file exists.
    purpose: str
    synthetic: bool = True
    generator_seed: int = SEED


@dataclass
class _Series:
    unit: str
    values: list[float]
    special: list[str] = field(default_factory=lambda: [])


def _wave(n: int, base: float, amp: float, freq: float = 0.05, noise: float = 0.0) -> list[float]:
    """Deterministic pseudo-noise via two incommensurate sines.

    A real RNG is avoided so the byte stream cannot drift across Python
    versions; ``noise`` scales a sum of sines, not a random draw.
    """
    out: list[float] = []
    for i in range(n):
        v = base + amp * math.sin(freq * i) + noise * math.sin(1.7 * i + 0.3) * math.cos(0.23 * i)
        out.append(v)
    return out


def _nan_flood(values: list[float], every: int = 5, width: int = 3) -> list[float]:
    out = list(values)
    for i in range(0, len(out), every):
        for j in range(i, min(i + width, len(out))):
            out[j] = float("nan")
    return out


def write_las(
    path: Path,
    well: str,
    depth_unit: str,
    curves: dict[str, tuple[str, list[float]]],
    start: float,
    step: float,
) -> None:
    """Write a minimal LAS 2.0 file: enough structure to parse, nothing more."""
    n = len(next(iter(curves.values()))[1])
    lines = [
        "~VERSION INFORMATION",
        " VERS. 2.0 :",
        " WRAP. NO :",
        "~WELL INFORMATION",
        f" STRT.{depth_unit} {start:.4f} :",
        f" STOP.{depth_unit} {start + step * (n - 1):.4f} :",
        f" STEP.{depth_unit} {step:.4f} :",
        f" NULL. {NULL_VALUE} :",
        f" WELL. {well} :",
        f" SRC. SYNTHETIC-UGLY-CORPUS v{__version__} SEED {SEED} :",
        "~CURVE INFORMATION",
    ]
    for mnemonic, (unit, _values) in curves.items():
        lines.append(f" {mnemonic}.{unit} :")
    lines.append("~A")
    for i in range(n):
        row = []
        for _mnemonic, (_unit, values) in curves.items():
            v = values[i]
            row.append(f"{NULL_VALUE:.2f}" if v != v else f"{v:.4f}")
        lines.append(" " + " ".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def _depth(n: int, start: float, step: float, unit: str) -> tuple[str, list[float]]:
    return (unit, [start + step * i for i in range(n)])


def build_corpus(dest: Path) -> list[Fixture]:
    """Generate every fixture under ``dest`` and return the manifest."""
    dest.mkdir(parents=True, exist_ok=True)
    fixtures: list[tuple[str, str, dict[str, tuple[str, list[float]]], float, float, str]] = []

    # 1. Clean: the exact nine canonical measured mnemonics, in range.
    n = 120
    fixtures.append(
        (
            "01_clean.las",
            "UGLY-CLEAN",
            {
                "DEPT": _depth(n, 1000.0, 0.5, "M"),
                "GR": ("gAPI", _wave(n, 70, 25)),
                "RHOB": ("G/C3", _wave(n, 2.45, 0.08)),
                "NPHI": ("V/V", _wave(n, 0.22, 0.05)),
                "DT": ("US/F", _wave(n, 70, 8)),
                "RT": ("OHMM", _wave(n, 12.0, 3.0)),
                "PEF": ("B/E", _wave(n, 3.0, 0.3)),
                "CALI": ("IN", _wave(n, 8.6, 0.2)),
                "SP": ("MV", _wave(n, -20.0, 6.0)),
                "DTS": ("US/F", _wave(n, 130, 10)),
            },
            1000.0,
            0.5,
            "All nine canonical measured curves present and in range.",
        )
    )

    # 2. Computed: the L5 trap. Measured GR beside computed and unknown-name curves.
    n = 80
    fixtures.append(
        (
            "02_computed.las",
            "UGLY-COMPUTED",
            {
                "DEPT": _depth(n, 1500.0, 0.5, "M"),
                "GR": ("gAPI", _wave(n, 60, 18)),
                "VSH": ("V/V", _wave(n, 0.35, 0.1)),
                "PHIE": ("V/V", _wave(n, 0.18, 0.04)),
                "TVDSS": ("M", _wave(n, 1520, 12)),
                "SONIC": ("US/F", _wave(n, 75, 6)),
                "PHI": ("V/V", _wave(n, 0.2, 0.05)),
            },
            1500.0,
            0.5,
            "Computed/interpreted-value curves must never satisfy measured completeness; "
            "SONIC and PHI are canonical aliases whose origin is unknown and must fail closed.",
        )
    )

    # 3. Interpreted: a name that says it was interpreted.
    n = 60
    fixtures.append(
        (
            "03_interpreted.las",
            "UGLY-INTERPRETED",
            {
                "DEPT": _depth(n, 2000.0, 1.0, "M"),
                "GR": ("gAPI", _wave(n, 55, 15)),
                "RHOB_INTERP": ("G/C3", _wave(n, 2.4, 0.05)),
            },
            2000.0,
            1.0,
            "RHOB_INTERP is interpreted, not measured: the token rule must outrank the name.",
        )
    )

    # 4. Unknown: an unrecognised mnemonic must stay in inventory and out of measured.
    n = 40
    fixtures.append(
        (
            "04_unknown.las",
            "UGLY-UNKNOWN",
            {
                "DEPT": _depth(n, 2500.0, 1.0, "M"),
                "GR": ("gAPI", _wave(n, 65, 12)),
                "ZZZ9": ("X", _wave(n, 1.0, 0.1)),
            },
            2500.0,
            1.0,
            "An unknown curve must not vanish from the inventory and must not count as measured.",
        )
    )

    # 5. Ugly: duplicate depths, a NaN flood, out-of-range spikes.
    n = 100
    gr = _nan_flood(_wave(n, 80, 30), every=4, width=2)
    rhob = _wave(n, 2.5, 0.1)
    for i in range(0, n, 13):
        rhob[i] = 9.99  # impossible density: the range check exists to catch this
    dept = _depth(n, 3000.0, 0.5, "M")[1]
    for i in range(0, n, 17):
        dept[i] = dept[i - 1] if i else dept[i]  # duplicate depth row
    fixtures.append(
        (
            "05_ugly_nan_dupes.las",
            "UGLY-NAN",
            {
                "DEPT": ("M", dept),
                "GR": ("gAPI", gr),
                "RHOB": ("G/C3", rhob),
            },
            3000.0,
            0.5,
            "Deliberately broken: duplicate depths, >50% NaNs on GR, impossible RHOB spikes.",
        )
    )

    # 6. Spliced: a curve stitched from two vintages.
    n = 60
    fixtures.append(
        (
            "06_spliced.las",
            "UGLY-SPLICED",
            {
                "DEPT": _depth(n, 3500.0, 0.5, "M"),
                "GR_SPLICE": ("gAPI", _wave(n, 75, 20)),
                "RHOB": ("G/C3", _wave(n, 2.4, 0.06)),
            },
            3500.0,
            0.5,
            "GR_SPLICE must classify as spliced, never measured.",
        )
    )

    # 7. Units: a foot-denominated file. Kept for the unit-trap contract.
    n = 30
    fixtures.append(
        (
            "07_ft_units.las",
            "UGLY-FT",
            {
                "DEPT": _depth(n, 5000.0, 1.0, "FT"),
                "GR": ("gAPI", _wave(n, 45, 10)),
            },
            5000.0,
            1.0,
            "Depth in feet: a metric-only pipeline must not silently treat it as metres.",
        )
    )

    manifest: list[Fixture] = []
    for name, well, curves, start, step, purpose in fixtures:
        path = dest / name
        write_las(path, well, curves["DEPT"][0], curves, start, step)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.append(
            Fixture(
                name=name,
                path=path,
                sha256=digest,
                curves=tuple(curves),
                purpose=purpose,
            )
        )
    return manifest


def manifest_digest(fixtures: list[Fixture]) -> str:
    """SHA-256 over the sorted name:hash pairs — one number for the whole corpus."""
    payload = "\n".join(f"{f.name}:{f.sha256}" for f in sorted(fixtures, key=lambda x: x.name))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()
