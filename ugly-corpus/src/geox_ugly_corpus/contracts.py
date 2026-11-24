"""The contracts the Ugly Corpus measures.

Each contract is a falsifiable statement about the shipped GEOX code. The
corpus asserts *the contract*, not a happy path: a computed curve must not
count as measured, a missing source must not pass QC, an unphysical number
must be refused in the returned state.

Nothing here calls a network or reads a file it did not generate.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .generate import NULL_VALUE, Fixture, build_corpus, manifest_digest


@dataclass
class Result:
    contract: str
    ok: bool
    detail: str
    evidence: dict = field(default_factory=dict)


def _geox_imports():
    """Import GEOX late so the corpus can report a clear error when absent."""
    from geox_core.curve_origin import classify_curve_origin, measure_completeness
    from geox_mcp.tools.kernel._ingest import CANONICAL_ALIASES

    return classify_curve_origin, measure_completeness, CANONICAL_ALIASES


def parse_las(path: Path) -> tuple[dict[str, str], list[list[str]]]:
    """Return ({mnemonic: unit}, data rows) from a LAS 2.0 file."""
    text = path.read_text(encoding="ascii")
    lines = text.splitlines()
    curves: dict[str, str] = {}
    in_curve_section = False
    data_index: int | None = None
    for i, raw in enumerate(lines):
        line = raw.strip()
        upper = line.upper()
        if upper.startswith("~C"):
            in_curve_section = True
            continue
        if upper.startswith("~A"):
            data_index = i
            break
        if in_curve_section and line:
            token = line.split(":")[0].strip()
            mnemonic, _, unit = token.partition(".")
            curves[mnemonic.strip().upper()] = unit.strip()
    if data_index is None:
        raise ValueError(f"{path.name}: no ~A data section")
    rows = [line.split() for line in lines[data_index + 1 :] if line.strip()]
    return curves, rows


def _canonical_origins(mnemonics: set[str], classify_curve_origin, aliases) -> dict[str, str]:
    """Mirror geox_mcp.tools.qc's canonical resolution, one mnemonic per canonical curve."""
    upper = {m.upper() for m in mnemonics}
    origins: dict[str, str] = {}
    for canon, names in aliases.items():
        match = next((a for a in names if a in upper), None)
        if match is not None:
            origins[canon] = classify_curve_origin(match)["origin"]
    return origins


def run_contracts(fixtures: list[Fixture]) -> list[Result]:
    classify_curve_origin, measure_completeness, CANONICAL_ALIASES = _geox_imports()
    by_name = {f.name: f for f in fixtures}
    results: list[Result] = []

    # ── L5 / L10: raw vs computed ────────────────────────────────────────────
    curves, _rows = parse_las(by_name["01_clean.las"].path)
    origins = _canonical_origins(set(curves), classify_curve_origin, CANONICAL_ALIASES)
    comp = measure_completeness(origins, len(CANONICAL_ALIASES))
    results.append(
        Result(
            "L5-measured-baseline",
            comp["measured_count"] == len(CANONICAL_ALIASES) and comp["inventory_count"] == len(CANONICAL_ALIASES),
            f"clean fixture resolves {comp['measured_count']}/{len(CANONICAL_ALIASES)} canonical curves as measured",
            comp,
        )
    )

    curves, _rows = parse_las(by_name["02_computed.las"].path)
    origins = _canonical_origins(set(curves), classify_curve_origin, CANONICAL_ALIASES)
    comp = measure_completeness(origins, len(CANONICAL_ALIASES))
    forbidden = {"VSH", "PHIE", "TVDSS"}
    leaked = forbidden & set(comp["measured_curves"])
    unknown_aliases_counted = {"DT", "NPHI"} & set(comp["measured_curves"])
    results.append(
        Result(
            "L5-computed-not-measured",
            not leaked and not unknown_aliases_counted and comp["measured_count"] == 1,
            "computed VSH/PHIE/TVDSS and unknown-origin aliases SONIC/PHI must not count as measured "
            f"(measured={comp['measured_count']}, leaked={sorted(leaked)})",
            comp,
        )
    )

    interp = classify_curve_origin("RHOB_INTERP")
    interp_comp = measure_completeness({"RHOB": interp["origin"]}, len(CANONICAL_ALIASES))
    results.append(
        Result(
            "L5-token-outranks-name",
            interp["origin"] == "interpreted" and interp_comp["measured_count"] == 0,
            f"RHOB_INTERP → {interp['origin']} (basis={interp['origin_basis']}), measured_count={interp_comp['measured_count']}",
            {"classification": interp, "completeness": interp_comp},
        )
    )

    unknown = classify_curve_origin("ZZZ9")
    unknown_comp = measure_completeness({"GR": "measured", "ZZZ9": unknown["origin"]}, len(CANONICAL_ALIASES))
    results.append(
        Result(
            "L5-unknown-stays-in-inventory",
            unknown["origin"] == "unknown"
            and unknown_comp["inventory_count"] == 2
            and unknown_comp["measured_count"] == 1
            and unknown_comp["inventory_only_curves"] == ["ZZZ9"],
            f"ZZZ9 → {unknown['origin']}; inventory={unknown_comp['inventory_count']}, measured={unknown_comp['measured_count']}",
            unknown_comp,
        )
    )

    spliced = classify_curve_origin("GR_SPLICE")
    results.append(
        Result(
            "L5-spliced-not-measured",
            spliced["origin"] == "spliced",
            f"GR_SPLICE → {spliced['origin']} (basis={spliced['origin_basis']})",
            {"classification": spliced},
        )
    )

    # ── Fail-closed QC ───────────────────────────────────────────────────────
    from geox_mcp.tools.qc import geox_data_qc_bundle

    qc = asyncio.run(geox_data_qc_bundle(artifact_ref="ugly-corpus-unregistered-source"))
    qc_ok = (
        qc.get("execution_status") == "ERROR"
        and qc.get("governance_status") == "HOLD"
        and qc.get("claim_state") == "NO_VALID_EVIDENCE"
        and (qc.get("primary_artifact") or {}).get("qc_passed") is False
    )
    results.append(
        Result(
            "QC-missing-source-fails-closed",
            qc_ok,
            "an unregistered/missing source must return ERROR+HOLD+NO_VALID_EVIDENCE with qc_passed=False",
            {k: qc.get(k) for k in ("execution_status", "governance_status", "claim_state")},
        )
    )

    # ── G-1 physics refusal ──────────────────────────────────────────────────
    from geox_mcp.tools.petrophysics_unified import geox_petrophysics
    from geox_mcp.tools.seismic_compute import geox_seismic_compute

    inverted = asyncio.run(geox_petrophysics(mode="generate", target_class="reservoir", zone_top_m=3500.0, zone_base_m=1500.0))
    results.append(
        Result(
            "G1-inverted-interval-refused",
            inverted.get("status") == "INVALID",
            f"top>base must refuse, got status={inverted.get('status')!r}",
            {"status": inverted.get("status")},
        )
    )

    negative = asyncio.run(geox_petrophysics(mode="generate", target_class="reservoir", phi_cutoff=-0.15))
    results.append(
        Result(
            "G1-negative-porosity-refused",
            negative.get("status") == "INVALID",
            f"negative porosity cutoff must refuse, got status={negative.get('status')!r}",
            {"status": negative.get("status")},
        )
    )

    superluminal = asyncio.run(geox_seismic_compute(mode="synthetic", vp=[8000.0], rho=[2.5]))
    sl_ok = (
        superluminal.get("execution_status") == "ERROR"
        and superluminal.get("governance_status") == "HOLD"
        and superluminal.get("artifact_status") == "REJECTED"
        and superluminal.get("claim_state") == "NO_VALID_EVIDENCE"
    )
    results.append(
        Result(
            "G1-superluminal-velocity-refused",
            sl_ok,
            "8000 m/s in sedimentary rock must return ERROR/HOLD/REJECTED/NO_VALID_EVIDENCE",
            {k: superluminal.get(k) for k in ("execution_status", "governance_status", "artifact_status", "claim_state")},
        )
    )

    # ── Envelope honesty: an uncomputed guard must not attest a pass ─────────
    from geox_core.enums.statuses import get_standard_envelope

    env = get_standard_envelope({"probe": "ugly-corpus"})
    guard = env.get("physics_guard") or {}
    results.append(
        Result(
            "GUARD-uncomputed-is-not-pass",
            guard.get("guard_passed") is not True,
            f"a tool that runs no guard must not emit guard_passed=True (got {guard.get('guard_passed')!r})",
            {"physics_guard": guard},
        )
    )

    # ── Corpus self-checks: determinism, synthetic provenance, real ugliness ──
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        digest_a = manifest_digest(build_corpus(Path(first)))
        digest_b = manifest_digest(build_corpus(Path(second)))
    results.append(
        Result(
            "corpus-determinism",
            digest_a == digest_b,
            f"two builds share manifest digest {digest_a[:16]}…",
            {"manifest_digest": digest_a},
        )
    )

    provenance_ok = True
    provenance_detail = []
    for fixture in fixtures:
        text = fixture.path.read_text(encoding="ascii")
        stamped = "SYNTHETIC-UGLY-CORPUS" in text and "SEED 20261124" in text
        provenance_ok = provenance_ok and stamped
        provenance_detail.append(f"{fixture.name}:{'synthetic' if stamped else 'UNSTAMPED'}")
    results.append(
        Result(
            "corpus-synthetic-provenance",
            provenance_ok,
            "every fixture header names the generator and seed",
            {"fixtures": provenance_detail},
        )
    )

    curves, rows = parse_las(by_name["05_ugly_nan_dupes.las"].path)
    dept_index = list(curves).index("DEPT")
    gr_index = list(curves).index("GR")
    rhob_index = list(curves).index("RHOB")
    depths = [float(row[dept_index]) for row in rows]
    gr_values = [float(row[gr_index]) for row in rows]
    rhob_values = [float(row[rhob_index]) for row in rows]
    duplicate_depths = len(depths) - len(set(depths))
    # LAS nulls are written as NULL_VALUE (-999.25), not as Python NaN; both
    # are "not a measurement" and the fixture must not hide either.
    nan_fraction = sum(1 for v in gr_values if v != v or v == NULL_VALUE) / len(gr_values)
    max_rhob = max(v for v in rhob_values if not math.isnan(v))
    results.append(
        Result(
            "corpus-ugly-is-actually-ugly",
            duplicate_depths >= 1 and nan_fraction >= 0.5 and max_rhob > 3.2,
            f"duplicate_depths={duplicate_depths}, GR_nan_fraction={nan_fraction:.2f}, max_RHOB={max_rhob:.2f}",
            {
                "duplicate_depths": duplicate_depths,
                "gr_nan_fraction": round(nan_fraction, 3),
                "max_rhob": max_rhob,
            },
        )
    )

    return results


def budget_result(elapsed_s: float, budget_s: float = 60.0) -> Result:
    return Result(
        "budget-60s",
        elapsed_s <= budget_s,
        f"{elapsed_s:.2f}s of a {budget_s:.0f}s budget (includes imports and GEOX tool calls)",
        {"elapsed_s": round(elapsed_s, 3), "budget_s": budget_s},
    )
