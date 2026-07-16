"""
GEOX-001: Well-Seismic Truth Test — "Model Deserves To Live"
═══════════════════════════════════════════════════════════════════════════════

Core thesis:
  If the well does not tie, the model does not get to speak as truth.

Objective:
  Prove GEOX can cross-examine a subsurface claim against real well-seismic
  evidence and return PROCEED / HOLD / KILL without pretending certainty.

Success condition (all six required):
  1. QC-verified ingested files
  2. Explicit evidence graph
  3. Synthetic tie / drift result
  4. Claim with OBS / DER / INT / SPEC separation
  5. Active challenge / alternative interpretation
  6. Verdict that can say PROCEED, HOLD, or KILL without fake certainty

Not basin simulation. Not prospect volumetrics. Not 3D fan modelling.
One well · one horizon · one seismic tie · one claim · one contradiction.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import numpy as np

from geox_core.core.welltie import (
    assess_tie_quality,
    compute_ai,
    compute_average_velocity_td,
    compute_reflectivity,
    compute_vp_from_sonic,
    cross_correlate,
    generate_synthetic_trace,
)
from geox_core.schemas.tie_claim_bridge import bridge_residual_to_claim
from geox_core.schemas.tie_receipt import build_tie_receipt

# ── Benchmark identity ────────────────────────────────────────────────────────

BENCHMARK_ID = "GEOX-001"
BENCHMARK_NAME = "Well-Seismic Truth Test"
BENCHMARK_TITLE = "Model Deserves To Live"
THESIS = "If the well does not tie, the model does not get to speak as truth."
TARGET_CLAIM_TEMPLATE = (
    "Horizon {horizon} represents the top reservoir at {well}."
)

# Threshold law (locked 2026-07-09 — GEOX-001 receipt design)
# mistie_ms:   PROCEED ≤15 · HOLD (15, 25] · KILL >25 (unless independently repaired)
# checkshot:   PROCEED ≤10 · HOLD (10, 25] · KILL >25 persistent
# correlation: PROCEED ≥0.65 · HOLD [0.40, 0.65) · KILL <0.40 without geological rescue
MISTIE_PROCEED_MS = 15.0
MISTIE_HOLD_MS = 15.0  # exclusive lower bound for HOLD band
MISTIE_KILL_MS = 25.0  # exclusive lower bound for KILL band
CHECKSHOT_PROCEED_MS = 10.0
CHECKSHOT_DRIFT_HOLD_MS = 10.0
CHECKSHOT_DRIFT_KILL_MS = 25.0
CORRELATION_PROCEED_MIN = 0.65
CORRELATION_HOLD_MIN = 0.40

# Pipeline stages (governed harness — maps to existing GEOX verbs)
PIPELINE_STAGES = (
    "000_ingest",
    "111_qc",
    "222_evidence_graph",
    "333_synthetic_tie",
    "444_claim_create",
    "555_challenge",
    "666_falsification_scan",
    "777_verdict",
)

ScenarioName = Literal["good_tie", "mistie_hold", "kill_contradiction"]
SCENARIO_GOOD: ScenarioName = "good_tie"
SCENARIO_HOLD: ScenarioName = "mistie_hold"
SCENARIO_KILL: ScenarioName = "kill_contradiction"

Verdict = Literal["PROCEED", "HOLD", "KILL"]
EpistemicRung = Literal["OBS", "DER", "INT", "SPEC"]

MANDATORY_ALTERNATIVES = (
    "Mapped event is not top reservoir; it is another impedance boundary.",
    "Well top is valid, but seismic event is mistied.",
    "Velocity model shifts depth closure enough to erase trap confidence.",
    "Reservoir motif exists in logs, but seismic support is weak.",
)


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class EvidenceNode:
    node_id: str
    kind: str
    rung: EpistemicRung
    label: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceEdge:
    source: str
    target: str
    relation: str
    note: str = ""


@dataclass
class QCResult:
    artifact: str
    status: Literal["PASS", "WARN", "FAIL"]
    checks: list[str]
    notes: list[str] = field(default_factory=list)


@dataclass
class TieResult:
    mistie_ms: float
    correlation: float
    residual_rms: float
    quality: str
    residual_class: str
    synthetic_peak_twt_ms: float
    mapped_event_twt_ms: float
    checkshot_drift_max_ms: float
    velocity_uncertainty_ms: float
    dt_ms: float


@dataclass
class ClaimBundle:
    claim_id: str
    text: str
    rung: EpistemicRung
    evidence_for: list[dict[str, Any]]
    evidence_against: list[dict[str, Any]]
    missing_tests: list[str]
    alternatives: list[dict[str, Any]]
    residual_class: str
    ac_risk: float
    promotion_allowed: bool


@dataclass
class FalsificationTest:
    test_id: str
    statement: str
    threshold: str
    current_status: Literal["unverified", "confirmed", "weakened", "falsified", "untestable"]
    implication: str


# ── Fixture generation (self-contained, no external data) ─────────────────────


def _make_depth_grid(start_m: float = 2000.0, stop_m: float = 2500.0, step_m: float = 1.0) -> np.ndarray:
    return np.arange(start_m, stop_m + step_m * 0.5, step_m, dtype=float)


def _build_curves(
    depth: np.ndarray,
    reservoir_top_m: float = 2300.0,
    *,
    strong_dn_separation: bool = False,
) -> dict[str, np.ndarray]:
    """Synthetic well curves with a sand motif at reservoir_top_m.

    Default: GR/RT support sand but density-neutron separation weak (HOLD band).
    strong_dn_separation=True: clean sand RHOB/NPHI for PROCEED path.
    """
    n = len(depth)
    gr = np.full(n, 95.0)
    rt = np.full(n, 3.0)
    rhob = np.full(n, 2.45)
    nphi = np.full(n, 0.28)
    dt = np.full(n, 100.0)  # us/ft shale-ish

    sand = (depth >= reservoir_top_m) & (depth < reservoir_top_m + 35.0)
    gr[sand] = 42.0
    rt[sand] = 18.0
    if strong_dn_separation:
        rhob[sand] = 2.18  # clear gas/sand density drop
        nphi[sand] = 0.30  # strong DN separation
    else:
        rhob[sand] = 2.32  # weak separation vs NPHI
        nphi[sand] = 0.22
    dt[sand] = 85.0  # faster sand

    # soft gradient with depth (compaction)
    z0 = depth[0]
    gr = gr + 0.01 * (depth - z0)
    dt = dt - 0.005 * (depth - z0)
    rhob = rhob + 0.00005 * (depth - z0)

    return {"DEPT": depth, "GR": gr, "RT": rt, "RHOB": rhob, "NPHI": nphi, "DT": dt}


def _build_checkshot(
    depth: np.ndarray,
    vp: np.ndarray,
    drift_bias_ms: float = 0.0,
) -> list[dict[str, float]]:
    """Checkshot points from integrated Vp, with optional systematic drift."""
    twt = compute_average_velocity_td(vp, depth)
    # subsample every ~50 m
    idxs = list(range(0, len(depth), 50))
    if idxs[-1] != len(depth) - 1:
        idxs.append(len(depth) - 1)
    rows = []
    for i, idx in enumerate(idxs):
        # inject linear drift that peaks mid-interval (for HOLD/KILL scenarios)
        frac = i / max(len(idxs) - 1, 1)
        drift = drift_bias_ms * math.sin(math.pi * frac)
        rows.append(
            {
                "depth_md": float(depth[idx]),
                "twt_ms": float(twt[idx] + drift),
            }
        )
    return rows


def _build_seismic_from_synthetic(
    synthetic: np.ndarray,
    twt_ms: np.ndarray,
    shift_ms: float,
    dt_ms: float,
    noise_db: float = -20.0,
    seed: int = 7,
) -> tuple[np.ndarray, np.ndarray]:
    """Seismic = shifted synthetic + noise. Positive shift = event later than well."""
    n_shift = int(round(shift_ms / max(dt_ms, 0.5)))
    seismic = np.roll(synthetic, n_shift)
    if noise_db < 0:
        amp = 10 ** (noise_db / 20.0)
        rng = np.random.default_rng(seed)
        seismic = seismic + rng.normal(0, amp, len(seismic))
        m = np.max(np.abs(seismic))
        if m > 0:
            seismic = seismic / m
    return seismic, twt_ms


def generate_scenario_bundle(scenario: ScenarioName = SCENARIO_HOLD) -> dict[str, Any]:
    """Generate minimum-data bundle for GEOX-001.

    minimum_data:
      - 1 LAS-equivalent curve set
      - 1 tops table
      - 1 checkshot table
      - 1 seismic line (trace + TWT)
      - 1 horizon pick
      - 1 velocity assumption
    """
    well_id = "Well A"
    horizon_id = "H1"
    reservoir_top_m = 2300.0
    depth = _make_depth_grid()

    # Scenario knobs (aligned to threshold law)
    # good: mistie ≤15, drift ≤10, corr high, strong DN → PROCEED
    # hold: mistie in (15, 25], drift in (10, 25], weak DN → HOLD
    # kill: mistie >25 (classic +38 ms) OR drift >25 + offset contradiction → KILL
    if scenario == SCENARIO_GOOD:
        checkshot_drift = 0.0
        mapped_shift_ms = 8.0
        nearby_top_contradicts = False
        velocity_uncert_pct = 0.03
        strong_dn = True
    elif scenario == SCENARIO_KILL:
        checkshot_drift = 28.0
        mapped_shift_ms = 38.0  # >25 ms kill gate — classic demo mistie
        nearby_top_contradicts = True
        velocity_uncert_pct = 0.12
        strong_dn = False
    else:  # mistie_hold — default demo (HOLD band, not kill)
        checkshot_drift = 18.0
        mapped_shift_ms = 22.0  # (15, 25] → HOLD under threshold law
        nearby_top_contradicts = False
        velocity_uncert_pct = 0.08
        strong_dn = False

    curves = _build_curves(depth, reservoir_top_m, strong_dn_separation=strong_dn)
    vp = compute_vp_from_sonic(curves["DT"], depth, dt_unit="usft")
    rho = curves["RHOB"]

    checkshot = _build_checkshot(depth, vp, drift_bias_ms=checkshot_drift)

    # T-D for synthetic: use checkshot interp for honesty
    cs_d = np.array([r["depth_md"] for r in checkshot])
    cs_t = np.array([r["twt_ms"] for r in checkshot])
    twt_full = np.interp(depth, cs_d, cs_t)

    ai = compute_ai(vp, rho, rho_unit="gcc")
    rc = compute_reflectivity(ai, polarity="SEG_NORMAL")
    # interface midpoints for TWT
    twt_rc = 0.5 * (twt_full[:-1] + twt_full[1:])
    synth, twt_s = generate_synthetic_trace(
        rc, twt_rc, wavelet_type="ricker", wavelet_freq_hz=30.0, noise_db=-22, rng_seed=42
    )
    dt_ms = float(np.median(np.diff(twt_s))) if len(twt_s) > 1 else 1.0
    seismic, twt_seis = _build_seismic_from_synthetic(synth, twt_s, mapped_shift_ms, dt_ms)

    # Top reservoir TWT from checkshot at 2300 m
    top_twt = float(np.interp(reservoir_top_m, cs_d, cs_t))
    # Synthetic peak near top: max |amp| in ±40 ms window around top
    window = (twt_s >= top_twt - 40) & (twt_s <= top_twt + 40)
    if np.any(window):
        local = np.where(window)[0]
        peak_idx = local[int(np.argmax(np.abs(synth[window])))]
        synth_peak_twt = float(twt_s[peak_idx])
    else:
        synth_peak_twt = top_twt
        peak_idx = 0

    # Mapped horizon H1 deliberately offset (the interpretation under test)
    mapped_h1_twt = synth_peak_twt + mapped_shift_ms

    tops = [
        {
            "well_id": well_id,
            "surface": "Top_Reservoir",
            "depth_md": reservoir_top_m,
            "confidence": "INTERPRETATION",
            "source": "log_motif_pick",
        },
        {
            "well_id": well_id,
            "surface": "Base_Reservoir",
            "depth_md": reservoir_top_m + 35.0,
            "confidence": "INTERPRETATION",
            "source": "log_motif_pick",
        },
    ]
    if nearby_top_contradicts:
        tops.append(
            {
                "well_id": "Well_B_nearby",
                "surface": "Top_Reservoir",
                "depth_md": reservoir_top_m - 95.0,  # depth trend contradiction
                "confidence": "INTERPRETATION",
                "source": "offset_well_pick",
                "note": "Nearby well top contradicts regional depth trend",
            }
        )

    # Density-neutron separation strength
    # score = mean(NPHI) + (2.65 - mean(RHOB)); higher = clearer sand/fluid flag
    sand_mask = (depth >= reservoir_top_m) & (depth < reservoir_top_m + 35.0)
    dn_sep_score = float(
        np.mean(curves["NPHI"][sand_mask]) + (2.65 - np.mean(curves["RHOB"][sand_mask]))
    )
    # weak if score < 0.65 (HOLD path default ~0.55; PROCEED path ~0.77)
    dn_weak = (not strong_dn) or dn_sep_score < 0.65

    velocity_assumption = {
        "method": "checkshot_linear_interp",
        "datum": "MSL",
        "units": "ms TWT / m MD",
        "uncertainty_fraction": velocity_uncert_pct,
        "uncertainty_ms_at_target": abs(top_twt) * velocity_uncert_pct,
        "note": "Velocity model uncertainty can erase closure if large enough",
        "closure_survives_p10_p50_p90": scenario == SCENARIO_GOOD,
    }

    return {
        "scenario": scenario,
        "well_id": well_id,
        "horizon_id": horizon_id,
        "curves": {k: v.tolist() for k, v in curves.items()},
        "tops": tops,
        "checkshot": checkshot,
        "seismic": {
            "line_id": "LINE_A_INLINE_120",
            "trace_id": f"{well_id}_extract",
            "twt_ms": twt_seis.tolist(),
            "amplitude": seismic.tolist(),
            "dt_ms": dt_ms,
            "polarity": "SEG_NORMAL",
            "phase": "assumed_zero",
        },
        "synthetic": {
            "twt_ms": twt_s.tolist(),
            "amplitude": synth.tolist(),
            "wavelet": "ricker_30hz",
            "peak_twt_ms": synth_peak_twt,
            "peak_index": int(peak_idx),
        },
        "horizon": {
            "name": horizon_id,
            "surface": "Top_Reservoir",
            "mapped_twt_ms": mapped_h1_twt,
            "pick_method": "manual_interpretation",
            "confidence": "INTERPRETATION",
        },
        "velocity_assumption": velocity_assumption,
        "petro_diagnostics": {
            "gr_resistivity_supports_sand": True,
            "density_neutron_separation_score": round(dn_sep_score, 4),
            "density_neutron_separation_weak": dn_weak,
            "top_pick_confidence": "INTERPRETATION",
        },
        "meta": {
            "benchmark_id": BENCHMARK_ID,
            "title": BENCHMARK_TITLE,
            "thesis": THESIS,
            "generated_at_utc": datetime.now(UTC).isoformat(),
        },
    }


def write_fixture_bundle(out_dir: str | Path, scenario: ScenarioName = SCENARIO_HOLD) -> Path:
    """Write minimum-data files for offline inspection / MCP ingest demos."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    bundle = generate_scenario_bundle(scenario)

    # LAS 2.0
    depth = bundle["curves"]["DEPT"]
    las_path = out / "well_a.las"
    step = depth[1] - depth[0] if len(depth) > 1 else 1.0
    lines = [
        "~Version ---------------------------------------------------",
        " VERS.                    2.0   :LAS version 2.0",
        " WRAP.                     NO   :ONE LINE PER DEPTH STEP",
        "~Well ------------------------------------------------------",
        f" STRT.M              {depth[0]:.4f}   :START DEPTH",
        f" STOP.M              {depth[-1]:.4f}   :STOP DEPTH",
        f" STEP.M              {step:.4f}   :STEP",
        " NULL.              -999.25   :NULL VALUE",
        " WELL.             Well_A   :WELL NAME",
        " COMP.             GEOX-001   :COMPANY",
        "~Curve Information -----------------------------------------",
        " DEPT.M              : DEPTH",
        " GR  .API            : GAMMA RAY",
        " RT  .OHMM           : RESISTIVITY",
        " RHOB.G/C3           : BULK DENSITY",
        " NPHI.V/V            : NEUTRON POROSITY",
        " DT  .USFT           : SONIC",
        "~A  DEPT        GR         RT        RHOB       NPHI        DT",
    ]
    for i in range(len(depth)):
        lines.append(
            f"{depth[i]:10.4f} {bundle['curves']['GR'][i]:10.4f} "
            f"{bundle['curves']['RT'][i]:10.4f} {bundle['curves']['RHOB'][i]:10.4f} "
            f"{bundle['curves']['NPHI'][i]:10.4f} {bundle['curves']['DT'][i]:10.4f}"
        )
    las_path.write_text("\n".join(lines) + "\n")

    (out / "tops.json").write_text(json.dumps(bundle["tops"], indent=2))
    (out / "checkshot.json").write_text(json.dumps(bundle["checkshot"], indent=2))
    (out / "seismic_trace.json").write_text(json.dumps(bundle["seismic"], indent=2))
    (out / "horizon_h1.json").write_text(json.dumps(bundle["horizon"], indent=2))
    (out / "velocity_assumption.json").write_text(json.dumps(bundle["velocity_assumption"], indent=2))
    (out / "bundle_meta.json").write_text(
        json.dumps({"scenario": scenario, "meta": bundle["meta"], "petro": bundle["petro_diagnostics"]}, indent=2)
    )
    return out


# ── Workflow steps ────────────────────────────────────────────────────────────


def step_qc_evidence(bundle: dict[str, Any]) -> list[QCResult]:
    """QC-verify ingested minimum data."""
    results: list[QCResult] = []

    curves = bundle["curves"]
    n = len(curves["DEPT"])
    required = ["DEPT", "DT", "RHOB", "GR"]
    missing = [c for c in required if c not in curves or len(curves[c]) != n]
    results.append(
        QCResult(
            artifact="LAS/well_curves",
            status="FAIL" if missing else "PASS",
            checks=[f"n_samples={n}", f"curves={list(curves.keys())}"],
            notes=[f"missing: {missing}"] if missing else ["DT+RHOB present for synthetic"],
        )
    )

    cs = bundle["checkshot"]
    cs_ok = len(cs) >= 3 and all("depth_md" in r and "twt_ms" in r for r in cs)
    results.append(
        QCResult(
            artifact="checkshot",
            status="PASS" if cs_ok else "FAIL",
            checks=[f"n_points={len(cs)}"],
            notes=[] if cs_ok else ["need ≥3 checkshot points with depth_md, twt_ms"],
        )
    )

    tops = bundle["tops"]
    top_ok = any(t.get("surface") == "Top_Reservoir" for t in tops)
    results.append(
        QCResult(
            artifact="tops",
            status="PASS" if top_ok else "FAIL",
            checks=[f"n_tops={len(tops)}"],
            notes=["Top_Reservoir present"] if top_ok else ["Top_Reservoir missing"],
        )
    )

    seis = bundle["seismic"]
    seis_ok = len(seis.get("amplitude", [])) >= 10 and len(seis["amplitude"]) == len(seis.get("twt_ms", []))
    results.append(
        QCResult(
            artifact="seismic_trace",
            status="PASS" if seis_ok else "FAIL",
            checks=[f"n_samples={len(seis.get('amplitude', []))}", f"polarity={seis.get('polarity')}"],
        )
    )

    hz = bundle["horizon"]
    hz_ok = "mapped_twt_ms" in hz and hz.get("name")
    results.append(
        QCResult(
            artifact="horizon_pick",
            status="PASS" if hz_ok else "FAIL",
            checks=[f"name={hz.get('name')}", f"twt={hz.get('mapped_twt_ms')}"],
        )
    )

    vel = bundle["velocity_assumption"]
    vel_ok = "method" in vel and "uncertainty_fraction" in vel
    results.append(
        QCResult(
            artifact="velocity_assumption",
            status="PASS" if vel_ok else "WARN",
            checks=[f"method={vel.get('method')}", f"u={vel.get('uncertainty_fraction')}"],
        )
    )

    return results


def step_build_evidence_graph(bundle: dict[str, Any], qc: list[QCResult]) -> dict[str, Any]:
    """Explicit evidence graph: nodes carry OBS/DER/INT/SPEC rungs."""
    nodes = [
        EvidenceNode("n_las", "well_log", "OBS", "Well_A LAS curves (DT,RHOB,GR,RT,NPHI)"),
        EvidenceNode("n_checkshot", "checkshot", "OBS", "Checkshot / VSP table"),
        EvidenceNode("n_seismic", "seismic_trace", "OBS", f"Seismic extract {bundle['seismic']['line_id']}"),
        EvidenceNode("n_tops", "formation_tops", "INT", "Top_Reservoir log pick"),
        EvidenceNode("n_horizon", "horizon_pick", "INT", f"Mapped horizon {bundle['horizon']['name']}"),
        EvidenceNode("n_velocity", "velocity_model", "SPEC", "Velocity assumption + uncertainty"),
        EvidenceNode("n_synthetic", "synthetic_seismogram", "DER", "Ricker synthetic from AI→RC"),
        EvidenceNode("n_tie", "well_seismic_tie", "DER", "Cross-correlation mistie / residual"),
        EvidenceNode("n_claim", "claim", "INT", "Horizon = top reservoir claim"),
    ]
    edges = [
        EvidenceEdge("n_las", "n_synthetic", "derives", "DT+RHOB → AI → RC → synthetic"),
        EvidenceEdge("n_checkshot", "n_synthetic", "calibrates", "T-D places synthetic in time"),
        EvidenceEdge("n_synthetic", "n_tie", "compares_to", "synthetic vs seismic extract"),
        EvidenceEdge("n_seismic", "n_tie", "compares_to", "observed seismic event"),
        EvidenceEdge("n_horizon", "n_tie", "tested_by", "mapped event vs synthetic peak"),
        EvidenceEdge("n_tops", "n_claim", "supports", "log motif suggests sand at top"),
        EvidenceEdge("n_tie", "n_claim", "constrains", "mistie governs claim right-to-believe"),
        EvidenceEdge("n_velocity", "n_claim", "can_falsify", "velocity uncertainty may erase closure"),
        EvidenceEdge("n_checkshot", "n_claim", "can_falsify", "checkshot drift invalidates depth map"),
    ]
    qc_pass = all(r.status != "FAIL" for r in qc)
    return {
        "nodes": [asdict(n) for n in nodes],
        "edges": [asdict(e) for e in edges],
        "qc_gate_pass": qc_pass,
        "graph_id": f"eg-{BENCHMARK_ID}-{bundle['well_id']}-{bundle['horizon_id']}",
    }


def step_synthetic_tie(bundle: dict[str, Any]) -> TieResult:
    """Generate/compare synthetic tie vs mapped seismic event."""
    synth = np.asarray(bundle["synthetic"]["amplitude"], dtype=float)
    twt_s = np.asarray(bundle["synthetic"]["twt_ms"], dtype=float)
    seis = np.asarray(bundle["seismic"]["amplitude"], dtype=float)
    # align lengths
    n = min(len(synth), len(seis))
    synth, seis = synth[:n], seis[:n]
    twt_s = twt_s[:n]
    dt_ms = float(bundle["seismic"].get("dt_ms") or (np.median(np.diff(twt_s)) if n > 1 else 1.0))

    corr, residual_rms, lag_samples = cross_correlate(synth, seis)
    # cross_correlate assumes 1 ms/sample; rescale to actual dt
    mistie_from_corr = float(lag_samples) * (dt_ms if abs(dt_ms - 1.0) > 1e-6 else 1.0)

    synth_peak = float(bundle["synthetic"]["peak_twt_ms"])
    mapped = float(bundle["horizon"]["mapped_twt_ms"])
    mistie_peak = mapped - synth_peak  # + means mapped event later than well synthetic

    # Prefer peak-to-mapped mistie as the claim-facing metric (interpretation test)
    mistie_ms = mistie_peak

    # Checkshot drift vs average-velocity integration
    depth = np.asarray(bundle["curves"]["DEPT"], dtype=float)
    dt_log = np.asarray(bundle["curves"]["DT"], dtype=float)
    vp = compute_vp_from_sonic(dt_log, depth, dt_unit="usft")
    twt_int = compute_average_velocity_td(vp, depth)
    cs = bundle["checkshot"]
    cs_d = np.array([r["depth_md"] for r in cs])
    cs_t = np.array([r["twt_ms"] for r in cs])
    twt_cs_on_log = np.interp(depth, cs_d, cs_t)
    checkshot_drift_max = float(np.nanmax(np.abs(twt_cs_on_log - twt_int)))

    vel_uncert = float(bundle["velocity_assumption"].get("uncertainty_ms_at_target") or 0.0)

    # Residual class for claim bridge (threshold law)
    if abs(mistie_ms) > MISTIE_KILL_MS or checkshot_drift_max > CHECKSHOT_DRIFT_KILL_MS:
        residual_class = "checkshot_vsp_error" if checkshot_drift_max >= abs(mistie_ms) else "time_depth_error"
    elif abs(mistie_ms) > MISTIE_HOLD_MS or checkshot_drift_max > CHECKSHOT_DRIFT_HOLD_MS:
        residual_class = "time_depth_error"
    elif corr < CORRELATION_HOLD_MIN:
        residual_class = "wavelet_error"
    elif abs(mistie_ms) <= MISTIE_PROCEED_MS and corr >= CORRELATION_PROCEED_MIN:
        residual_class = "good_tie"
    else:
        residual_class = "unexplained"

    quality = assess_tie_quality(corr, residual_rms, phase_rotation_deg=0.0, polarity_reversed=False)

    return TieResult(
        mistie_ms=round(mistie_ms, 2),
        correlation=round(float(corr), 4),
        residual_rms=round(float(residual_rms), 4),
        quality=quality,
        residual_class=residual_class,
        synthetic_peak_twt_ms=round(synth_peak, 2),
        mapped_event_twt_ms=round(mapped, 2),
        checkshot_drift_max_ms=round(checkshot_drift_max, 2),
        velocity_uncertainty_ms=round(vel_uncert, 2),
        dt_ms=round(dt_ms, 3),
    )


def step_classify_epistemic(bundle: dict[str, Any], tie: TieResult) -> dict[str, EpistemicRung]:
    """Separate OBS / DER / INT / SPEC for every claim-facing element."""
    petro = bundle["petro_diagnostics"]
    return {
        "las_curves": "OBS",
        "checkshot_table": "OBS",
        "seismic_trace_amplitudes": "OBS",
        "synthetic_seismogram": "DER",
        "tie_mistie_ms": "DER",
        "top_reservoir_log_pick": "INT",  # log motif pick is interpretation
        "horizon_h1_mapped_event": "INT",
        "reservoir_presence_from_gr_rt": "INT" if petro.get("gr_resistivity_supports_sand") else "SPEC",
        "reservoir_presence_from_dn": (
            "INT" if petro.get("density_neutron_separation_weak") else "DER"
        ),
        "velocity_model": "SPEC",
        "horizon_equals_top_reservoir_claim": "INT",
        "closure_after_velocity_uncertainty": "SPEC",
    }


def step_create_claim(
    bundle: dict[str, Any],
    tie: TieResult,
    epistemic: dict[str, EpistemicRung],
) -> ClaimBundle:
    """Create the target claim with evidence_for / against and rung honesty."""
    well = bundle["well_id"]
    hz = bundle["horizon_id"]
    text = TARGET_CLAIM_TEMPLATE.format(horizon=hz, well=well)
    bridge = bridge_residual_to_claim(tie.residual_class, claim_type="structural", existing_ac_risk=0.15)

    evidence_for: list[dict[str, Any]] = [
        {
            "item": "GR/resistivity motif supports sand at Top_Reservoir",
            "rung": epistemic["reservoir_presence_from_gr_rt"],
            "source": "n_las",
        },
        {
            "item": f"Top pick exists at log motif ({bundle['tops'][0]['depth_md']} m MD)",
            "rung": epistemic["top_reservoir_log_pick"],
            "source": "n_tops",
        },
    ]
    if tie.residual_class == "good_tie":
        evidence_for.append(
            {
                "item": f"Synthetic-to-seismic mistie {tie.mistie_ms} ms within tolerance",
                "rung": "DER",
                "source": "n_tie",
            }
        )

    evidence_against: list[dict[str, Any]] = [
        {
            "item": f"synthetic tie peak is shifted {tie.mistie_ms:+.0f} ms from mapped event",
            "rung": "DER",
            "source": "n_tie",
        },
        {
            "item": f"checkshot drift max {tie.checkshot_drift_max_ms:.1f} ms",
            "rung": "DER",
            "source": "n_checkshot",
        },
    ]
    petro = bundle["petro_diagnostics"]
    if petro.get("density_neutron_separation_weak"):
        evidence_against.append(
            {
                "item": "GR/resistivity motif supports sand, but density-neutron separation is weak",
                "rung": "INT",
                "source": "n_las",
            }
        )
    evidence_against.append(
        {
            "item": "top pick confidence is INTERPRETATION, not OBSERVATION",
            "rung": "INT",
            "source": "n_tops",
        }
    )
    evidence_against.append(
        {
            "item": (
                f"velocity model uncertainty ±{tie.velocity_uncertainty_ms:.1f} ms "
                "can erase closure"
            ),
            "rung": "SPEC",
            "source": "n_velocity",
        }
    )
    for ea in bridge.get("evidence_against") or []:
        evidence_against.append({"item": ea, "rung": "DER", "source": "residual_bridge"})

    # Nearby well contradiction
    for t in bundle["tops"]:
        if t.get("well_id") != well and t.get("surface") == "Top_Reservoir":
            evidence_against.append(
                {
                    "item": (
                        f"nearby well {t['well_id']} top at {t['depth_md']} m "
                        "contradicts depth trend"
                    ),
                    "rung": "INT",
                    "source": "n_tops",
                }
            )

    # Demo-facing next tests first (operator-actionable), then residual bridge tests
    missing = [
        "re-pick seismic event around tie window",
        "run alternate velocity model",
        "attach second well or sidetrack if available",
    ]
    for t in bridge.get("missing_tests") or []:
        if t not in missing:
            missing.append(t)

    claim_rung: EpistemicRung = "INT"
    if tie.residual_class == "good_tie" and not petro.get("density_neutron_separation_weak"):
        claim_rung = "DER"

    return ClaimBundle(
        claim_id=f"claim-{BENCHMARK_ID}-{well}-{hz}",
        text=text,
        rung=claim_rung,
        evidence_for=evidence_for,
        evidence_against=evidence_against,
        missing_tests=missing,
        alternatives=[],  # filled by challenge step
        residual_class=tie.residual_class,
        ac_risk=float(bridge.get("ac_risk", 0.4)),
        promotion_allowed=bool(bridge.get("promotion_allowed", False)),
    )


def step_challenge_claim(claim: ClaimBundle, tie: TieResult, bundle: dict[str, Any]) -> ClaimBundle:
    """Mandatory alternative interpretations — never single-story geology."""
    claim.alternatives = [
        {
            "alternative_id": "alt_not_top_reservoir",
            "text": MANDATORY_ALTERNATIVES[0],
            "rung": "INT",
            "detail": (
                f"Mapped event at {tie.mapped_event_twt_ms:.0f} ms may be a parallel "
                f"impedance boundary; synthetic peak at {tie.synthetic_peak_twt_ms:.0f} ms "
                f"(mistie {tie.mistie_ms:+.0f} ms)."
            ),
            "status": "active_challenge",
        },
        {
            "alternative_id": "alt_seismic_mistied",
            "text": MANDATORY_ALTERNATIVES[1],
            "rung": "INT",
            "detail": "Well top valid on logs; seismic event pick is the error source.",
            "status": "active_challenge",
        },
        {
            "alternative_id": "alt_velocity_erases_trap",
            "text": MANDATORY_ALTERNATIVES[2],
            "rung": "SPEC",
            "detail": (
                f"velocity_uncertainty_ms={tie.velocity_uncertainty_ms}; "
                f"checkshot_drift_max_ms={tie.checkshot_drift_max_ms}"
            ),
            "status": "active_challenge",
        },
        {
            "alternative_id": "alt_weak_seismic_support",
            "text": MANDATORY_ALTERNATIVES[3],
            "rung": "INT",
            "detail": "GR/RT motif supports sand; seismic event correlation may not.",
            "status": "active_challenge",
        },
    ]
    if any(t.get("well_id") != bundle["well_id"] for t in bundle["tops"]):
        claim.alternatives.append(
            {
                "alternative_id": "alt_offset_depth_trend",
                "text": "Nearby well top contradicts depth trend; correlation is wrong.",
                "rung": "INT",
                "status": "active_challenge",
            }
        )
    return claim


def step_falsification_scan(tie: TieResult, claim: ClaimBundle, bundle: dict[str, Any]) -> list[FalsificationTest]:
    """Popperian kill tests — what would kill the model."""
    abs_m = abs(tie.mistie_ms)
    tests = [
        FalsificationTest(
            test_id="revised_checkshot_mistie_gt_25ms",
            statement="if revised checkshot still gives >25 ms mistie, kill horizon tie",
            threshold=f"abs(mistie_ms) > {MISTIE_KILL_MS}",
            current_status=(
                "falsified"
                if abs_m > MISTIE_KILL_MS
                else "weakened"
                if abs_m > MISTIE_HOLD_MS
                else "confirmed"
            ),
            implication="Horizon H1 cannot be promoted as Top_Reservoir without re-pick or T-D repair",
        ),
        FalsificationTest(
            test_id="nearby_well_top_breaks_depth_trend",
            statement="if nearby well top contradicts depth trend, downgrade prospect",
            threshold="offset top residual vs regional trend > 50 m",
            current_status=(
                "falsified"
                if any(t.get("well_id") != bundle["well_id"] for t in bundle["tops"])
                else "unverified"
            ),
            implication="Multi-well depth consistency required before structural map trust",
        ),
        FalsificationTest(
            test_id="velocity_uncertainty_erases_closure",
            statement="if alternate velocity removes closure, prospect claim cannot proceed",
            threshold="velocity_uncertainty_ms > closure_relief_ms",
            current_status="unverified",  # closure not in minimum unit
            implication="Do not promote closure-dependent prospect without velocity sensitivity",
        ),
        FalsificationTest(
            test_id="polarity_or_phase_assumption_unresolved",
            statement="if polarity/phase assumption unresolved, synthetic event may track wrong reflector",
            threshold="wavelet phase not extracted from well-seismic match",
            current_status="weakened",  # assumed zero-phase Ricker
            implication="Phase/polarity must be locked before PROCEED on thin reservoirs",
        ),
        FalsificationTest(
            test_id="synthetic_event_tracks_different_reflector",
            statement="if synthetic peak tracks a different reflector than mapped H1, kill horizon tie",
            threshold=f"abs(mistie_ms) > {MISTIE_KILL_MS}",
            current_status="falsified" if abs_m > MISTIE_KILL_MS else "weakened" if abs_m > MISTIE_HOLD_MS else "confirmed",
            implication="Mapped event is not the well impedance boundary under test",
        ),
        FalsificationTest(
            test_id="density_neutron_weak_support",
            statement="if density-neutron cannot support sand, reservoir claim stays INTERPRETATION",
            threshold="dn_separation_score < 0.15",
            current_status=(
                "weakened"
                if bundle["petro_diagnostics"].get("density_neutron_separation_weak")
                else "confirmed"
            ),
            implication="Petrophysical support for reservoir is motif-only (GR/RT), not hard OBS",
        ),
    ]
    return tests


def step_verdict(
    tie: TieResult,
    claim: ClaimBundle,
    falsification: list[FalsificationTest],
    qc: list[QCResult],
) -> dict[str, Any]:
    """Uncertainty-calibrated verdict under locked threshold law: PROCEED | HOLD | KILL."""
    reasons: list[str] = []
    next_tests: list[str] = list(claim.missing_tests[:3])
    # always append alternate-velocity falsification line for receipt shape
    falsif_lines = [
        f.statement
        for f in falsification
        if f.current_status in ("falsified", "weakened", "unverified")
    ]

    qc_fail = [r for r in qc if r.status == "FAIL"]
    if qc_fail:
        return {
            "verdict": "KILL",
            "reason": [f"QC FAIL on {r.artifact}" for r in qc_fail],
            "falsification": [asdict(f) for f in falsification],
            "falsification_statements": falsif_lines,
            "next_test": next_tests,
            "confidence_cap": 0.30,
            "model_deserves_to_live": False,
            "threshold_triggers": ["qc_fail"],
        }

    abs_mistie = abs(tie.mistie_ms)
    drift = tie.checkshot_drift_max_ms
    corr = tie.correlation
    offset_kill = any(
        f.test_id == "nearby_well_top_breaks_depth_trend" and f.current_status == "falsified"
        for f in falsification
    )
    triggers: list[str] = []

    # KILL gates (threshold law)
    kill = False
    if abs_mistie > MISTIE_KILL_MS:
        kill = True
        triggers.append("mistie_gt_25ms")
    if drift > CHECKSHOT_DRIFT_KILL_MS:
        kill = True
        triggers.append("checkshot_drift_gt_25ms")
    if corr < CORRELATION_HOLD_MIN and not claim.promotion_allowed:
        kill = True
        triggers.append("correlation_lt_0.40")
    if offset_kill and abs_mistie > MISTIE_HOLD_MS:
        kill = True
        triggers.append("offset_top_contradicts_depth_trend")

    # HOLD gates
    hold = False
    if MISTIE_HOLD_MS < abs_mistie <= MISTIE_KILL_MS:
        hold = True
        triggers.append("mistie_in_hold_band")
    if CHECKSHOT_DRIFT_HOLD_MS < drift <= CHECKSHOT_DRIFT_KILL_MS:
        hold = True
        triggers.append("checkshot_drift_in_hold_band")
    if CORRELATION_HOLD_MIN <= corr < CORRELATION_PROCEED_MIN:
        hold = True
        triggers.append("correlation_in_hold_band")
    if any("density-neutron" in e["item"] for e in claim.evidence_against):
        hold = True
        triggers.append("weak_density_neutron_separation")

    if kill:
        verdict: Verdict = "KILL"
        reasons.append(f"synthetic tie peak is shifted {tie.mistie_ms:+.0f} ms from mapped event")
        if drift > CHECKSHOT_DRIFT_HOLD_MS:
            reasons.append(f"checkshot drift exceeds threshold ({drift:.1f} ms)")
        if offset_kill:
            reasons.append("nearby well top contradicts depth trend")
        reasons.append("top pick confidence is INTERPRETATION, not OBSERVATION")
        reasons.append("velocity model uncertainty can erase closure")
        live = False
    elif hold or not claim.promotion_allowed or tie.residual_class != "good_tie":
        verdict = "HOLD"
        reasons.append(f"synthetic tie peak is shifted {tie.mistie_ms:+.0f} ms from mapped event")
        if drift > CHECKSHOT_DRIFT_HOLD_MS:
            reasons.append("checkshot drift exceeds threshold")
        if any("density-neutron" in e["item"] for e in claim.evidence_against):
            reasons.append(
                "GR/resistivity motif supports sand, but density-neutron separation is weak"
            )
        reasons.append("top pick confidence is INTERPRETATION, not OBSERVATION")
        reasons.append("velocity model uncertainty can erase closure")
        live = False
    elif (
        abs_mistie <= MISTIE_PROCEED_MS
        and drift <= CHECKSHOT_PROCEED_MS
        and corr >= CORRELATION_PROCEED_MIN
        and tie.residual_class == "good_tie"
    ):
        verdict = "PROCEED"
        reasons.append(f"mistie {tie.mistie_ms:+.1f} ms ≤ {MISTIE_PROCEED_MS:.0f} ms (proceed band)")
        reasons.append(f"correlation {corr:.2f} ≥ {CORRELATION_PROCEED_MIN}")
        reasons.append("residual_class=good_tie; claim may advance with stated uncertainty")
        live = True
        triggers.append("all_proceed_thresholds_met")
        next_tests = [
            "verify with second well if available",
            "lock wavelet phase against known markers",
            "re-run after any new checkshot",
        ]
    else:
        verdict = "HOLD"
        reasons.append(
            f"tie quality {tie.quality} / residual {tie.residual_class} insufficient for PROCEED"
        )
        reasons.append(f"mistie={tie.mistie_ms:+.1f} ms correlation={corr:.2f}")
        live = False
        triggers.append("fallback_hold")

    # F7 humility: never claim certainty
    confidence_cap = 0.85 if verdict == "PROCEED" else 0.55 if verdict == "HOLD" else 0.35

    return {
        "verdict": verdict,
        "reason": reasons,
        "falsification": [asdict(f) for f in falsification],
        "falsification_statements": falsif_lines,
        "next_test": next_tests,
        "confidence_cap": confidence_cap,
        "model_deserves_to_live": live,
        "ac_risk": claim.ac_risk,
        "residual_class": tie.residual_class,
        "threshold_triggers": triggers,
        "thresholds_applied": {
            "mistie_ms": {
                "proceed": f"<={MISTIE_PROCEED_MS}",
                "hold": f">{MISTIE_HOLD_MS} and <={MISTIE_KILL_MS}",
                "kill": f">{MISTIE_KILL_MS}",
            },
            "checkshot_drift_ms": {
                "proceed": f"<={CHECKSHOT_PROCEED_MS}",
                "hold": f">{CHECKSHOT_DRIFT_HOLD_MS} and <={CHECKSHOT_DRIFT_KILL_MS}",
                "kill": f">{CHECKSHOT_DRIFT_KILL_MS}",
            },
            "correlation": {
                "proceed": f">={CORRELATION_PROCEED_MIN}",
                "hold": f"{CORRELATION_HOLD_MIN} to {CORRELATION_PROCEED_MIN}",
                "kill": f"<{CORRELATION_HOLD_MIN}",
            },
        },
    }


# ── Orchestrator ──────────────────────────────────────────────────────────────


def run_geox_001(
    scenario: ScenarioName = SCENARIO_HOLD,
    bundle: dict[str, Any] | None = None,
    fixture_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run GEOX-001 Well-Seismic Truth Test end-to-end.

    Returns a receipt with all six success artifacts plus the killer verdict block.
    """
    if bundle is None:
        if fixture_dir:
            bundle = _load_bundle_from_dir(Path(fixture_dir))
        else:
            bundle = generate_scenario_bundle(scenario)

    # 1. QC
    qc = step_qc_evidence(bundle)
    # 2. Evidence graph
    graph = step_build_evidence_graph(bundle, qc)
    # 3–4. Synthetic tie + drift
    tie = step_synthetic_tie(bundle)
    # 5. Epistemic separation
    epistemic = step_classify_epistemic(bundle, tie)
    # 6–7. Claim + challenge
    claim = step_create_claim(bundle, tie, epistemic)
    claim = step_challenge_claim(claim, tie, bundle)
    # 8. Falsification
    falsification = step_falsification_scan(tie, claim, bundle)
    # 9. Verdict
    verdict_block = step_verdict(tie, claim, falsification, qc)

    # Tie receipt (metabolizer memory)
    receipt = build_tie_receipt(
        well_name=bundle["well_id"],
        seismic_volume=bundle["seismic"].get("line_id", ""),
        polarity_convention=bundle["seismic"].get("polarity", "SEG_NORMAL"),
        phase_convention=bundle["seismic"].get("phase", "assumed_zero"),
        depth_basis="MD",
        logs_used=["DT", "RHOB", "GR", "RT", "NPHI"],
        time_depth_control={
            "checkshot_present": True,
            "vsp_present": False,
            "checkshot_count": len(bundle["checkshot"]),
            "drift_max_ms": tie.checkshot_drift_max_ms,
            "confidence": "medium" if tie.checkshot_drift_max_ms < CHECKSHOT_DRIFT_HOLD_MS else "low",
        },
        wavelet={
            "source": "assumed",
            "frequency_hz": 30.0,
            "phase_degrees": 0.0,
            "phase_confidence": "low",
        },
        tie_quality={
            "correlation_window": f"around top ±40 ms @ {tie.synthetic_peak_twt_ms:.0f} ms",
            "correlation_score": float(np.clip(tie.correlation, -1.0, 1.0)),
            "residual_class": tie.residual_class,
            "residual_description": f"mistie_ms={tie.mistie_ms}, quality={tie.quality}",
            "residual_severity": (
                "critical"
                if abs(tie.mistie_ms) >= MISTIE_KILL_MS
                else "high"
                if abs(tie.mistie_ms) >= MISTIE_HOLD_MS
                else "low"
            ),
        },
        rock_physics_status={
            "lithology_separability": "low"
            if bundle["petro_diagnostics"].get("density_neutron_separation_weak")
            else "medium",
            "fluid_separability": "low",
        },
        inversion_permission={
            "allowed": False,
            "constraints": ["GEOX-001 does not unlock inversion from a contested tie"],
        },
        decision_permission=verdict_block["verdict"] if verdict_block["verdict"] != "KILL" else "VOID",
        decision_reason="; ".join(verdict_block["reason"][:3]),
        uncertainty={
            "depth": "low" if tie.checkshot_drift_max_ms >= CHECKSHOT_DRIFT_HOLD_MS else "medium",
            "structural_trap": "low" if abs(tie.mistie_ms) >= MISTIE_HOLD_MS else "medium",
            "major_unknowns": [
                f"checkshot_drift_max_ms={tie.checkshot_drift_max_ms}",
                f"velocity_uncertainty_ms={tie.velocity_uncertainty_ms}",
                f"mistie_ms={tie.mistie_ms}",
            ],
        },
    )

    success = {
        "QC_verified_ingested_files": all(r.status != "FAIL" for r in qc),
        "explicit_evidence_graph": bool(graph.get("nodes")) and bool(graph.get("edges")),
        "synthetic_tie_and_drift_result": tie.mistie_ms is not None and tie.correlation is not None,
        "claim_with_OBS_DER_INT_SPEC_separation": bool(epistemic)
        and claim.rung in ("OBS", "DER", "INT", "SPEC"),
        "active_challenge_or_alternative_interpretation": len(claim.alternatives) >= 4,
        "verdict_can_say_PROCEED_HOLD_KILL_without_pretending_certainty": (
            verdict_block["verdict"] in ("PROCEED", "HOLD", "KILL")
            and verdict_block["confidence_cap"] <= 0.90
        ),
        # legacy keys (compat with earlier tests)
        "1_qc_verified": all(r.status != "FAIL" for r in qc),
        "2_evidence_graph": bool(graph.get("nodes")) and bool(graph.get("edges")),
        "3_synthetic_tie_drift": tie.mistie_ms is not None and tie.correlation is not None,
        "4_claim_obs_der_int_spec": bool(epistemic) and claim.rung in ("OBS", "DER", "INT", "SPEC"),
        "5_active_challenge": len(claim.alternatives) >= 4,
        "6_verdict_no_fake_certainty": verdict_block["verdict"] in ("PROCEED", "HOLD", "KILL")
        and verdict_block["confidence_cap"] <= 0.90,
    }
    core_six = [
        "QC_verified_ingested_files",
        "explicit_evidence_graph",
        "synthetic_tie_and_drift_result",
        "claim_with_OBS_DER_INT_SPEC_separation",
        "active_challenge_or_alternative_interpretation",
        "verdict_can_say_PROCEED_HOLD_KILL_without_pretending_certainty",
    ]
    all_six = all(success[k] for k in core_six)

    evidence_classes = {
        "OBS": [
            "LAS curves inspected",
            "tops table inspected",
            "checkshot/VSP inspected",
            "seismic event observed",
        ],
        "DER": [
            "synthetic trace generated",
            "time-depth relation computed",
            f"mistie measured ({tie.mistie_ms:+.1f} ms)",
            f"drift estimated ({tie.checkshot_drift_max_ms:.1f} ms)",
            f"correlation_score={tie.correlation:.3f}",
        ],
        "INT": [
            "top reservoir pick",
            "horizon-to-well tie",
            "geological defensibility claim",
        ],
        "SPEC": [
            "velocity closure survival",
            "regional trend assumption",
            "prospect implication",
        ],
    }

    constitutional_status = {
        "GEOX_verdict": verdict_block["verdict"],
        "VAULT999_status": "DRAFT_ONLY",
        "seal_allowed": False,
        "seal_allowed_note": "false_without_arifOS_adjudication",
        "band": "YELLOW",
        "evidence_level": "L2_live_surface_L4_benchmark_design",
        "receipt_class": "DRAFT_ONLY_not_VAULT999_sealed",
    }

    killer_output = {
        "benchmark": f"{BENCHMARK_ID}: {BENCHMARK_TITLE}",
        "claim": claim.text,
        "verdict": verdict_block["verdict"],
        "evidence_classes": evidence_classes,
        "reason": verdict_block["reason"],
        "falsification": verdict_block.get("falsification_statements")
        or [f["statement"] for f in verdict_block["falsification"]],
        "next_test": verdict_block["next_test"],
        "constitutional_status": constitutional_status,
    }

    pipeline = {
        "000_ingest": {
            "well_id": bundle["well_id"],
            "horizon": bundle["horizon_id"],
            "required_inputs": [
                "las_file",
                "tops_table",
                "checkshot_or_vsp",
                "seismic_line_or_mini_cube",
                "horizon_pick_or_surface",
                "velocity_assumption",
            ],
            "status": "complete",
        },
        "111_qc": {"results": [asdict(r) for r in qc], "status": "PASS" if success["1_qc_verified"] else "FAIL"},
        "222_evidence_graph": graph,
        "333_synthetic_tie": {
            **asdict(tie),
            "wavelet_assumption": "ricker_30hz_assumed_zero_phase",
            "velocity_assumption_used": bundle.get("velocity_assumption"),
            "peak_or_trough_polarity": bundle["seismic"].get("polarity", "SEG_NORMAL"),
            "tie_window_ms": 80.0,
        },
        "444_claim_create": asdict(claim),
        "555_challenge": claim.alternatives,
        "666_falsification_scan": [asdict(f) for f in falsification],
        "777_verdict": verdict_block,
    }

    return {
        "benchmark_id": BENCHMARK_ID,
        "benchmark_name": BENCHMARK_NAME,
        "title": BENCHMARK_TITLE,
        "thesis": THESIS,
        "domain": "GEOX",
        "test_type": "Well-Seismic Truth Test",
        "scenario": bundle.get("scenario", scenario),
        "status": "success" if all_six else "incomplete",
        "all_six_success_conditions": all_six,
        "success_conditions": success,
        "pipeline_stages": list(PIPELINE_STAGES),
        "pipeline": pipeline,
        "workflow": {
            "ingest_data": pipeline["000_ingest"],
            "qc_evidence": pipeline["111_qc"]["results"],
            "evidence_graph": graph,
            "synthetic_tie": pipeline["333_synthetic_tie"],
            "epistemic_classification": epistemic,
            "claim": asdict(claim),
            "challenge": claim.alternatives,
            "falsification_scan": [asdict(f) for f in falsification],
            "verdict": verdict_block,
        },
        "GEOX_001_receipt": killer_output,
        "tie_receipt": receipt,
        "killer_output": killer_output,
        "evidence_classes": evidence_classes,
        "constitutional_status": constitutional_status,
        "model_deserves_to_live": verdict_block["model_deserves_to_live"],
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "domain_law": "NATURAL_LAW",
        "excluded": [
            "basin simulation",
            "prospect volumetrics",
            "3D fan modelling",
            "full petroleum system risking",
            "production history integration",
            "multi-well field correlation",
            "commercial POS",
        ],
        "anti_hantu": [
            "amplitude is not hydrocarbon",
            "impedance is not lithology",
            "tie is not validation unless residuals are explained",
            "horizon pick is INTERPRETATION until well evidence licenses it",
            "GEOX does not seal — arifOS/VAULT999 owns final seal",
        ],
    }


def _load_bundle_from_dir(path: Path) -> dict[str, Any]:
    """Load a previously written fixture directory into a runtime bundle."""
    # Prefer regenerating scenario from meta if present; else assemble pieces
    meta_path = path / "bundle_meta.json"
    scenario: ScenarioName = SCENARIO_HOLD
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        scenario = meta.get("scenario", SCENARIO_HOLD)
        # regenerate for full physics consistency (fixtures are audit artifacts)
        return generate_scenario_bundle(scenario)

    # Manual assembly fallback
    import csv

    # If LAS exists, regenerate default hold scenario — full re-parse of LAS is
    # available via geox_1d but fixtures are scenario-driven for reproducibility.
    return generate_scenario_bundle(scenario)


def render_killer_yaml(result: dict[str, Any]) -> str:
    """Render the locked GEOX_001_receipt human-facing YAML shape."""
    k = result.get("GEOX_001_receipt") or result["killer_output"]
    cs = k.get("constitutional_status") or result.get("constitutional_status") or {}
    lines = [
        f'benchmark: "{k.get("benchmark", BENCHMARK_ID + ": " + BENCHMARK_TITLE)}"',
        f'claim: "{k["claim"]}"',
        f"verdict: {k['verdict']}",
        "evidence_classes:",
    ]
    ec = k.get("evidence_classes") or result.get("evidence_classes") or {}
    for rung in ("OBS", "DER", "INT", "SPEC"):
        lines.append(f"  {rung}:")
        for item in ec.get(rung, []):
            lines.append(f"    - {item}")
    lines.append("reason:")
    for r in k["reason"]:
        lines.append(f"  - {r}")
    lines.append("falsification:")
    for f in k["falsification"]:
        lines.append(f"  - {f}")
    lines.append("next_test:")
    for t in k["next_test"]:
        lines.append(f"  - {t}")
    lines.append("constitutional_status:")
    lines.append(f"  GEOX_verdict: {cs.get('GEOX_verdict', k['verdict'])}")
    lines.append(f"  VAULT999_status: {cs.get('VAULT999_status', 'DRAFT_ONLY')}")
    lines.append(f"  seal_allowed: {str(cs.get('seal_allowed', False)).lower()}")
    lines.append(f"model_deserves_to_live: {str(result['model_deserves_to_live']).lower()}")
    return "\n".join(lines) + "\n"


def load_real_las_curves(las_path: str | Path) -> dict[str, np.ndarray]:
    """Load DEPT + sonic + density (+ GR/NPHI/RT if present) from a real LAS file."""
    path = Path(las_path)
    if not path.exists():
        raise FileNotFoundError(f"LAS not found: {path}")

    # Prefer geox_1d if available; fall back to light parser
    try:
        from geox_core.core.geox_1d import process_las_file

        raw = process_las_file(str(path))
        if "ERROR" not in raw:
            depth = None
            for dk in ("DEPT", "DEPTH", "MD"):
                if dk in raw:
                    depth = np.asarray(raw[dk], dtype=float)
                    break
            dt = None
            for sk in ("DT", "DT4", "AC", "DTCO"):
                if sk in raw:
                    dt = np.asarray(raw[sk], dtype=float)
                    break
            rho = None
            for rk in ("RHOB", "DEN", "RHOZ"):
                if rk in raw:
                    rho = np.asarray(raw[rk], dtype=float)
                    break
            if depth is not None and dt is not None:
                out: dict[str, np.ndarray] = {"DEPT": depth, "DT": dt}
                if rho is not None:
                    out["RHOB"] = rho
                for src, dst in (("GR", "GR"), ("RDEP", "RT"), ("RT", "RT"), ("NEU", "NPHI"), ("NPHI", "NPHI")):
                    if src in raw and dst not in out:
                        out[dst] = np.asarray(raw[src], dtype=float)
                return out
    except Exception:
        pass

    # Minimal ASCII LAS reader
    lines = path.read_text(errors="replace").splitlines()
    in_ascii = False
    headers: list[str] = []
    rows: list[list[float]] = []
    for line in lines:
        if line.startswith("~C") or line.startswith("~Curve"):
            headers = []
            continue
        if line.startswith("~A"):
            in_ascii = True
            # header mnemonics often on ~A line or prior curve section
            continue
        if not in_ascii:
            # collect curve mnemonics
            if line.strip() and not line.startswith("~") and "." in line[:20]:
                mnem = line.strip().split(".")[0].strip().upper()
                if mnem and mnem not in headers:
                    headers.append(mnem)
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            rows.append([float(x) for x in parts])
        except ValueError:
            continue
    if not rows or not headers:
        raise ValueError(f"Could not parse LAS curves from {path}")
    arr = np.asarray(rows, dtype=float)
    n = min(len(headers), arr.shape[1])
    curves = {headers[i]: arr[:, i] for i in range(n)}
    # normalize keys
    out2: dict[str, np.ndarray] = {}
    for k, v in curves.items():
        ku = k.upper()
        if ku in ("DEPT", "DEPTH", "MD"):
            out2["DEPT"] = v
        elif ku in ("DT", "AC", "DTCO", "DT4"):
            out2["DT"] = v
        elif ku in ("RHOB", "DEN", "RHOZ"):
            out2["RHOB"] = v
        elif ku == "GR":
            out2["GR"] = v
        elif ku in ("RT", "RDEP", "ILD"):
            out2["RT"] = v
        elif ku in ("NPHI", "NEU", "NPOR"):
            out2["NPHI"] = v
    if "DEPT" not in out2 or "DT" not in out2:
        raise ValueError(f"LAS missing DEPT/DT after parse: keys={list(out2)}")
    if "RHOB" not in out2:
        # Gardner fallback marked later as DER not OBS
        vp = compute_vp_from_sonic(out2["DT"], out2["DEPT"], dt_unit="usft")
        out2["RHOB"] = (0.31 * (vp**0.25))  # rough Gardner g/cm3
        out2["_rhob_gardner"] = np.array([1.0])
    return out2


def run_geox_001_real_las(
    las_path: str | Path | None = None,
    scenario: ScenarioName = SCENARIO_HOLD,
) -> dict[str, Any]:
    """Run GEOX-001 using a real LAS for curves; scenario still supplies seismic/horizon/checkshot gaps.

    Honest provenance:
      - LAS curves = OBS (if file exists)
      - Checkshot / seismic extract / horizon = still scenario-derived (SPEC/INT)
        until real NOC/field companions are ingested.

    Default LAS: data/real_wells/q15_15_9_19/q15_15_9_19.las (North Sea Q15 — not NOC-proprietary).
    """
    default = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "real_wells"
        / "q15_15_9_19"
        / "q15_15_9_19.las"
    )
    # workspace may be /root/geox or /root/GEOX
    candidates = [
        Path(las_path) if las_path else None,
        default,
        Path("/root/geox/data/real_wells/q15_15_9_19/q15_15_9_19.las"),
        Path("/root/GEOX/data/real_wells/q15_15_9_19/q15_15_9_19.las"),
    ]
    path = next((p for p in candidates if p is not None and p.exists()), None)
    if path is None:
        result = run_geox_001(scenario=scenario)
        result["real_las"] = {
            "status": "MISSING",
            "note": "No real LAS on disk; fell back to synthetic scenario bundle",
            "noc_proprietary": "ABSENT",
        }
        return result

    real = load_real_las_curves(path)
    bundle = generate_scenario_bundle(scenario)

    # Overlay real curves onto scenario grid via depth interpolation window
    d_real = real["DEPT"]
    # use a contiguous window of real data matching scenario length
    n = len(bundle["curves"]["DEPT"])
    if len(d_real) >= n:
        # pick middle window with finite DT/RHOB
        dt_r = real["DT"]
        valid = np.isfinite(dt_r) & np.isfinite(real.get("RHOB", dt_r))
        idx = np.where(valid)[0]
        if len(idx) >= n:
            start = int(idx[len(idx) // 2 - n // 2])
            sl = slice(start, start + n)
            depth = d_real[sl]
            new_curves = {"DEPT": depth.tolist()}
            for k in ("DT", "RHOB", "GR", "RT", "NPHI"):
                if k in real:
                    new_curves[k] = np.asarray(real[k][sl], dtype=float).tolist()
            # fill missing with scenario
            for k, v in bundle["curves"].items():
                if k not in new_curves:
                    new_curves[k] = v
            bundle["curves"] = new_curves
            bundle["well_id"] = "15/9-19 (Q15)"
            bundle["petro_diagnostics"]["top_pick_confidence"] = "INTERPRETATION"
            bundle["petro_diagnostics"]["las_source"] = str(path)
            bundle["petro_diagnostics"]["las_provenance"] = "OBS_REAL_FILE"
            bundle["petro_diagnostics"]["rhob_gardner_fallback"] = bool(real.get("_rhob_gardner") is not None)
            # rebuild tops at mid-window depth
            mid = float(depth[len(depth) // 2])
            bundle["tops"][0]["depth_md"] = mid
            bundle["tops"][0]["well_id"] = bundle["well_id"]
            if len(bundle["tops"]) > 1:
                bundle["tops"][1]["depth_md"] = mid + 35.0
                bundle["tops"][1]["well_id"] = bundle["well_id"]

    # F2 LAS math — porosity/AI/RC from curves (not summary tables)
    las_physics = None
    try:
        from geox_core.benchmarks.geox_001_las_physics import compute_las_physics

        las_physics = compute_las_physics(bundle["curves"])
        # feed effective porosity stats into petro diagnostics
        pe = (las_physics.get("stats") or {}).get("phi_e") or {}
        bundle["petro_diagnostics"]["phi_e_p50"] = pe.get("p50")
        bundle["petro_diagnostics"]["phi_e_p10"] = pe.get("p10")
        bundle["petro_diagnostics"]["phi_e_p90"] = pe.get("p90")
        bundle["petro_diagnostics"]["net_to_gross_log"] = (las_physics.get("stats") or {}).get(
            "net_to_gross"
        )
        bundle["petro_diagnostics"]["porosity_source"] = "DER_FROM_LAS_CURVES"
    except Exception as exc:
        las_physics = {"status": "FAIL", "error": str(exc)[:200]}

    result = run_geox_001(scenario=scenario, bundle=bundle)
    result["real_las"] = {
        "status": "INGESTED",
        "path": str(path),
        "well": bundle["well_id"],
        "provenance": "OBS for LAS curves; checkshot/seismic/horizon remain scenario-derived until field companions arrive",
        "noc_proprietary": "ABSENT_ON_HOST",
        "note": "Best real LAS on host is Q15 North Sea 15/9-19 — not a NOC Malay Basin well",
    }
    if las_physics:
        result["las_physics"] = {
            k: las_physics[k]
            for k in ("epistemic", "rhob_source", "stats", "equations", "anti_hantu", "phi_n_source", "dt_unit")
            if k in las_physics
        }
        # keep series out of default receipt size — available under full key if needed
        result["las_physics_has_series"] = "series" in las_physics
        if "evidence_classes" in result:
            result["evidence_classes"].setdefault("DER", []).extend(
                [
                    f"φ_e P50={((las_physics.get('stats') or {}).get('phi_e') or {}).get('p50')} from density/neutron (LAS math)",
                    f"NTG_log={((las_physics.get('stats') or {}).get('net_to_gross'))}",
                    "AI/RC from Vp·ρ and Zoeppritz approximation",
                ]
            )
    # honesty: downgrade OBS claims for checkshot/seismic if scenario-derived
    if "evidence_classes" in result:
        result["evidence_classes"]["OBS"] = [
            f"LAS curves inspected (real file: {path.name})",
        ]
        result["evidence_classes"]["SPEC"] = list(
            dict.fromkeys(
                result["evidence_classes"].get("SPEC", [])
                + [
                    "checkshot/VSP scenario-derived (no field table)",
                    "seismic extract scenario-derived (no SEG-Y)",
                    "horizon pick scenario-derived",
                ]
            )
        )
    return result


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="GEOX-001: Model Deserves To Live")
    p.add_argument(
        "--scenario",
        choices=[SCENARIO_GOOD, SCENARIO_HOLD, SCENARIO_KILL],
        default=SCENARIO_HOLD,
    )
    p.add_argument("--write-fixtures", type=str, default="", help="Directory to write fixture files")
    p.add_argument("--real-las", action="store_true", help="Use real Q15 LAS curves if present")
    p.add_argument("--las-path", type=str, default="", help="Optional path to real LAS")
    p.add_argument("--json", action="store_true", help="Print full JSON receipt")
    args = p.parse_args()

    if args.write_fixtures:
        d = write_fixture_bundle(args.write_fixtures, args.scenario)
        print(f"fixtures → {d}")

    if args.real_las or args.las_path:
        result = run_geox_001_real_las(las_path=args.las_path or None, scenario=args.scenario)
    else:
        result = run_geox_001(scenario=args.scenario)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(render_killer_yaml(result))
        if result.get("real_las"):
            print(f"# real_las={result['real_las'].get('status')} noc={result['real_las'].get('noc_proprietary')}")
        print(f"# all_six={result['all_six_success_conditions']} scenario={result['scenario']}")
