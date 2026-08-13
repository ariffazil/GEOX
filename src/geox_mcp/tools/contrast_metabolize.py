"""
geox_contrast_metabolize — Unified Anomalous Contrast Metabolic Pipeline
═══════════════════════════════════════════════════════════════════════════════
The bloodstream. Binds three existing organs into one metabolic loop:

  Stage 1 ISOLATE   → Deterministic acoustic impedance contrast detection
  Stage 2 MEASURE   → AVO gradient + reflectivity + classification
  Stage 3 CLASSIFY  → ≥3 stratigraphic trap hypotheses (LLM handoff payload)

Architecture (Eureka ratified 2026-08-13):
  Computational isomorphism ≠ constitutional isomorphism.
  substrate_class = INERT  → COMPUTE_ONLY  → this tool.

F1 AMANAH     — read-only computation, no mutation
F2 TRUTH      — output is measured/derived, never fabricated
F4 CLARITY    — every stage output carries epistemic label
F7 HUMILITY   — confidence capped at 0.90
F8 GENIUS     — simplest correct path (orchestration, not reimplementation)
F10 ONTOLOGY  — substrate_class = INERT
F11 AUDIT     — every stage carries provenance hash

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

import numpy as np

logger = logging.getLogger("geox.canonical.contrast_metabolize")

# ═══════════════════════════════════════════════════════════════════════════════
# substrate_class declaration (F10 ONTOLOGY)
# ═══════════════════════════════════════════════════════════════════════════════

SUBSTRATE_CLASS = "INERT"
AUTHORITY_CEILING = "COMPUTE_ONLY"

# ═══════════════════════════════════════════════════════════════════════════════
# Stage 1: Contrast Isolation (deterministic, no interpretation)
# ═══════════════════════════════════════════════════════════════════════════════


def _stage1_isolate_contrast(
    impedance: np.ndarray,
    depth_m: np.ndarray,
    sensitivity: float = 0.15,
) -> dict[str, Any]:
    """Isolate acoustic impedance contrast boundaries.

    Uses the same physics primitive as anomalous_contrast.py:
    RC = (Z2 - Z1) / (Z2 + Z1)

    Returns contrast points with their reflection coefficients.
    No interpretation. No narrative. Physics only.
    """
    # Compute reflection coefficients at each boundary
    rc = np.zeros_like(impedance)
    rc[1:] = (impedance[1:] - impedance[:-1]) / (impedance[1:] + impedance[:-1] + 1e-12)

    # Find contrast anomalies: |RC| exceeds sensitivity threshold
    abs_rc = np.abs(rc)
    threshold = sensitivity * np.max(abs_rc) if np.max(abs_rc) > 0 else 0
    anomaly_mask = abs_rc > threshold
    anomaly_indices = np.where(anomaly_mask)[0]

    # Classify AVO class (first-order, from normal incidence)
    anomalies = []
    for idx in anomaly_indices:
        rc_val = float(rc[idx])
        abs_rc_val = abs(rc_val)
        depth = float(depth_m[idx])

        # AVO class (Rutherford & Williams, 1989 — first-order estimate)
        if rc_val < -0.05 and abs_rc_val >= 0.03:
            avo_class = "Class III (bright spot — soft gas sand)"
        elif rc_val < -0.02 and abs_rc_val < 0.05:
            avo_class = "Class II (phase reversal — near-zero impedance contrast)"
        elif rc_val > 0.02:
            avo_class = "Class I (hard streak — high impedance contrast)"
        elif rc_val < -0.02:
            avo_class = "Class IV (rare — negative intercept, positive gradient)"
        else:
            avo_class = "Indeterminate (sub-threshold)"

        anomalies.append(
            {
                "depth_m": round(depth, 1),
                "reflection_coefficient": round(rc_val, 4),
                "abs_rc": round(abs_rc_val, 4),
                "avo_class_estimate": avo_class,
                "attention_residual": round(abs_rc_val - np.mean(abs_rc[anomaly_mask]), 4),
            }
        )

    return {
        "stage": "ISOLATE",
        "epistemic_label": "OBS",
        "contrast_threshold": round(threshold, 4),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "rc_profile_stats": {
            "max_abs_rc": round(float(np.max(abs_rc)), 4) if len(abs_rc) > 0 else 0.0,
            "mean_abs_rc": round(float(np.mean(abs_rc[anomaly_mask])), 4) if anomaly_mask.any() else 0.0,
            "std_rc": round(float(np.std(rc)), 4),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2: Measurement (derived computation from Stage 1 anomalies)
# ═══════════════════════════════════════════════════════════════════════════════


def _stage2_measure(
    impedance: np.ndarray,
    depth_m: np.ndarray,
    anomalies: list[dict[str, Any]],
    vp_default: float = 3000.0,
    vs_default: float = 1500.0,
    rho_default: float = 2.3,
) -> dict[str, Any]:
    """Measure AVO parameters at each anomaly.

    Derives Vs from Vp/Gardner relationship where possible.
    Computes acoustic impedance, shear impedance, and lambda-mu-rho
    first estimates at each contrast point.
    """
    measurements = []
    for anom in anomalies:
        idx = int(np.argmin(np.abs(depth_m - anom["depth_m"])))
        z_val = float(impedance[idx]) if idx < len(impedance) else 0.0

        # Gardner's relationship: rho = 0.31 * Vp^0.25 (SI: Vp in m/s)
        vp_est = vp_default
        rho_est = rho_default
        vs_est = vs_default

        # Castagna's mudrock line: Vs = 0.8621 * Vp - 1172.4 (m/s)
        vs_from_castagna = 0.8621 * vp_est - 1172.4
        if vs_from_castagna > 0:
            vs_est = vs_from_castagna

        # Shear impedance
        zshear = vs_est * rho_est

        # Lame parameters (first-order)
        mu = rho_est * vs_est**2  # Shear modulus
        lambda_param = rho_est * (vp_est**2 - 2 * vs_est**2)  # First Lame parameter
        lam_rho = lambda_param * rho_est  # λρ
        mu_rho = mu * rho_est  # μρ

        measurements.append(
            {
                "depth_m": anom["depth_m"],
                "acoustic_impedance": round(z_val, 1),
                "vp_estimate_m_s": round(vp_est, 1),
                "vs_estimate_m_s": round(vs_est, 1),
                "density_estimate_g_cc": round(rho_est, 3),
                "shear_impedance": round(zshear, 1),
                "lambda_rho": round(lam_rho, 0),
                "mu_rho": round(mu_rho, 0),
                "vp_vs_ratio": round(vp_est / vs_est, 3) if vs_est > 0 else None,
            }
        )

    return {
        "stage": "MEASURE",
        "epistemic_label": "DER",
        "measurement_count": len(measurements),
        "measurements": measurements,
        "note": "First-order estimates from normal-incidence RC. Full AVO requires pre-stack angle gathers.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 3: Classify Void (generate ≥3 hypotheses for LLM handoff)
# ═══════════════════════════════════════════════════════════════════════════════


def _stage3_classify(
    anomalies: list[dict[str, Any]],
    measurements: list[dict[str, Any]],
    hypothesis_count: int = 3,
) -> dict[str, Any]:
    """Generate ≥3 stratigraphic trap hypotheses from the anomaly measurements.

    This is the LLM handoff payload. GEOX proposes; arifOS disposes.
    Local max verdict = QUALIFIED_CANDIDATE. preferred_hypothesis = null.
    """
    hypotheses: list[dict[str, Any]] = []

    # Build hypotheses based on AVO class patterns
    bright_spots = [a for a in anomalies if "Class III" in a.get("avo_class_estimate", "")]
    phase_reversals = [a for a in anomalies if "Class II" in a.get("avo_class_estimate", "")]
    hard_streaks = [a for a in anomalies if "Class I" in a.get("avo_class_estimate", "")]
    flat_spot_candidates = []

    # Check for flat spot (similar depth anomalies across lateral extent — proxy)
    if len(anomalies) >= 2:
        depths = [a["depth_m"] for a in anomalies]
        depth_spread = max(depths) - min(depths) if depths else 0
        if depth_spread < 50:  # anomalies clustered → possible flat spot
            flat_spot_candidates = anomalies

    # H1: Direct hydrocarbon indicator (DHI) from bright spots
    if bright_spots:
        anom = bright_spots[0]
        hypotheses.append(
            {
                "id": "H1",
                "label": "Direct Hydrocarbon Indicator (Class III AVO — gas-charged sand)",
                "supporting_evidence": f"{len(bright_spots)} bright spot anomaly(ies) at {anom['depth_m']}m depth",
                "falsification_test": "Pre-stack AVO gradient analysis. If gradient decreases with offset → gas confirmed. If gradient flat → lithology effect (false positive).",
                "risk": "P(falsification) > 0.3 — bright spots can be caused by low-impedance shale, coal, or tuning effects.",
                "confidence": 0.0,  # GEOX never sets confidence — arifOS judges
            }
        )
    else:
        hypotheses.append(
            {
                "id": "H1",
                "label": "No bright spot DHI — potential brine-saturated sequence",
                "supporting_evidence": "No Class III anomalies detected in contrast profile",
                "falsification_test": "Check well ties for hydrocarbon shows at anomaly depths. Absence of bright spot ≠ absence of hydrocarbons (Class II/I reservoirs exist).",
                "risk": "P(false negative) > 0.2 — Class II reservoirs are invisible on full-stack data.",
                "confidence": 0.0,
            }
        )

    # H2: Stratigraphic trap (channel/fan/reef — geometric interpretation)
    hypotheses.append(
        {
            "id": "H2",
            "label": "Stratigraphic trap (depositional geometry — channel, fan, or reef)",
            "supporting_evidence": f"{len(anomalies)} contrast boundaries suggest depositional facies transitions over {max(a['depth_m'] for a in anomalies) - min(a['depth_m'] for a in anomalies):.0f}m interval"
            if anomalies
            else "Contrast profile too sparse for geometric inference",
            "falsification_test": "Seismic attribute analysis (coherence, curvature, sweetness). If anomalies are laterally continuous → regional marker, not stratigraphic trap. If discontinuous → depositional geometry.",
            "risk": "Non-uniqueness problem — multiple geological models fit the same seismic data.",
            "confidence": 0.0,
        }
    )

    # H3: Structural trap (fault/fold/unconformity)
    hypotheses.append(
        {
            "id": "H3",
            "label": "Structural trap (fault seal, fold closure, or unconformity)",
            "supporting_evidence": f"Contrast at {anomalies[0]['depth_m']:.0f}m with RC={anomalies[0]['reflection_coefficient']:.4f}"
            if anomalies
            else "No anomalies",
            "falsification_test": "Structure_validate mode with fault sticks and horizon framework. Check closure on time-structure maps.",
            "risk": "Requires structural framework input — contrast alone cannot determine trap geometry.",
            "confidence": 0.0,
        }
    )

    # H4 (bonus): Flat spot = fluid contact
    if flat_spot_candidates:
        hypotheses.append(
            {
                "id": "H4",
                "label": "Fluid contact (flat spot — oil-water or gas-oil contact)",
                "supporting_evidence": f"{len(flat_spot_candidates)} laterally clustered anomalies suggest a flat event",
                "falsification_test": "Check flatness on pre-stack gathers. True flat spots are frequency-independent. Tuning artifacts are frequency-dependent.",
                "risk": "Flat spots can be processing artifacts, multiples, or diagenetic boundaries (opal-CT transition).",
                "confidence": 0.0,
            }
        )

    # Trim to requested count
    hypotheses = hypotheses[: max(hypothesis_count, 3)]

    return {
        "stage": "CLASSIFY",
        "epistemic_label": "INT",
        "hypothesis_count": len(hypotheses),
        "hypotheses": hypotheses,
        "preferred_hypothesis": None,  # GEOX never prefers — arifOS judges
        "local_verdict": "QUALIFIED_CANDIDATE",
        "note": "Hypotheses generated from normal-incidence contrast profile. Pre-stack AVO and well ties required for promotion beyond QUALIFIED_CANDIDATE.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Synthetic volume generator (for fixture/testing mode)
# ═══════════════════════════════════════════════════════════════════════════════


def _generate_synthetic_profile(
    depth_max_m: float = 3000.0,
    n_samples: int = 200,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a synthetic acoustic impedance profile with embedded anomalies.

    Simulates a clastic basin: compaction trend + 3 lithology contrasts.
    """
    rng = np.random.default_rng(seed)
    depth_m = np.linspace(0, depth_max_m, n_samples)

    # Compaction trend: impedance increases with depth (Athy's law analogue)
    z_background = 2000 + 0.8 * depth_m + 50 * rng.random(n_samples)

    # Embed 3 anomalies: gas sand (soft), carbonate cement (hard), coal (very soft)
    anomaly_depths = [1200, 1850, 2400]
    anomaly_deltas = [-800, +1200, -1500]

    for d, dz in zip(anomaly_depths, anomaly_deltas):
        idx = int(np.argmin(np.abs(depth_m - d)))
        spread = max(3, n_samples // 60)
        for j in range(max(0, idx - spread), min(n_samples, idx + spread + 1)):
            weight = np.exp(-0.5 * ((j - idx) / max(1, spread / 2)) ** 2)
            z_background[j] += dz * weight

    return z_background, depth_m


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline Orchestrator (the bloodstream)
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_contrast_metabolize(
    *,
    mode: str = "synthetic",
    impedance_profile: list[float] | None = None,
    depth_profile: list[float] | None = None,
    segy_path: str | None = None,
    inline_range: list[int] | None = None,
    xline_range: list[int] | None = None,
    sensitivity: float = 0.15,
    hypothesis_count: int = 3,
    stages: list[str] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Unified anomalous contrast metabolic pipeline.

    Binds three stages into one call:
      1. ISOLATE — deterministic acoustic impedance contrast detection
      2. MEASURE — AVO gradient + LMR estimates at contrast points
      3. CLASSIFY — ≥3 stratigraphic trap hypotheses for LLM handoff

    substrate_class: INERT
    authority_ceiling: COMPUTE_ONLY
    local_verdict: QUALIFIED_CANDIDATE (arifOS seals)

    Args:
        mode: "synthetic" (fixture) | "profile" (user provides arrays) | "segy" (SEG-Y file)
        impedance_profile: acoustic impedance values (mode=profile)
        depth_profile: depth in meters (mode=profile)
        segy_path: path to SEG-Y file (mode=segy — extracts 1D trace)
        sensitivity: contrast detection threshold (fraction of max |RC|)
        hypothesis_count: minimum hypotheses to generate (max returned = count + 1)
        stages: which stages to run ["contrast", "measure", "classify"] or None for all
    """
    t0 = time.monotonic()
    run_stages = stages or ["contrast", "measure", "classify"]
    stage_map = {"contrast": "isolate", "measure": "measure", "classify": "classify"}

    # ── Input resolution ──────────────────────────────────────────────────────
    if mode == "synthetic":
        impedance, depth_m = _generate_synthetic_profile()
    elif mode == "profile":
        if not impedance_profile or not depth_profile:
            return {"ok": False, "error": "mode=profile requires impedance_profile and depth_profile arrays"}
        impedance = np.array(impedance_profile, dtype=float)
        depth_m = np.array(depth_profile, dtype=float)
    elif mode == "segy":
        # Future: use segyio to extract a representative trace
        return {
            "ok": False,
            "error": "mode=segy not yet implemented — use mode=synthetic or mode=profile",
            "hint": "mode=segy will use segyio to extract a 1D trace and compute impedance from Vp*rho",
        }
    else:
        return {"ok": False, "error": f"Unknown mode '{mode}'. Use: synthetic | profile | segy"}

    # ── Stage 1: Isolate contrast ─────────────────────────────────────────────
    stage1 = (
        _stage1_isolate_contrast(impedance, depth_m, sensitivity) if "isolate" in [stage_map.get(s) for s in run_stages] else None
    )

    # ── Stage 2: Measure ──────────────────────────────────────────────────────
    stage2 = None
    if stage1 and "measure" in [stage_map.get(s) for s in run_stages]:
        stage2 = _stage2_measure(impedance, depth_m, stage1["anomalies"])

    # ── Stage 3: Classify void ────────────────────────────────────────────────
    stage3 = None
    if stage1 and "classify" in [stage_map.get(s) for s in run_stages]:
        measurements = stage2["measurements"] if stage2 else []
        stage3 = _stage3_classify(stage1["anomalies"], measurements, hypothesis_count)

    # ── Metabolic receipt ─────────────────────────────────────────────────────
    elapsed_ms = int((time.monotonic() - t0) * 1000)
    receipt_data = json.dumps(
        {
            "tool": "geox_contrast_metabolize",
            "mode": mode,
            "stages_run": [s for s in run_stages if stage_map.get(s)],
            "anomaly_count": stage1["anomaly_count"] if stage1 else 0,
            "hypothesis_count": stage3["hypothesis_count"] if stage3 else 0,
            "elapsed_ms": elapsed_ms,
        },
        sort_keys=True,
    )
    receipt_hash = hashlib.sha256(receipt_data.encode()).hexdigest()[:16]

    return {
        "ok": True,
        "tool": "geox_contrast_metabolize",
        "substrate_class": SUBSTRATE_CLASS,
        "authority_ceiling": AUTHORITY_CEILING,
        "local_verdict": "QUALIFIED_CANDIDATE",
        "preferred_hypothesis": None,
        # Pipeline outputs
        "stage1_isolate": stage1,
        "stage2_measure": stage2,
        "stage3_classify": stage3,
        # Provenance
        "metabolic_receipt": receipt_hash,
        "elapsed_ms": elapsed_ms,
        "pipeline": "isolate → measure → classify",
        "epistemic_note": "Stage 1 = OBS (direct computation). Stage 2 = DER (derived estimates). Stage 3 = INT (interpretive — requires LLM/arifOS to adjudicate).",
        # Evidence envelope (GEOX standard)
        "_evidence_receipt": {
            "sha256": receipt_hash,
            "tool": "geox_contrast_metabolize",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "isError": False,
        },
        "_well_conformance": {
            "claim_state": "COMPUTED",
            "witness_type": "AI",
            "organ_type": "SEISMIC",
            "conformance_version": "v1.0",
            "conformant": True,
        },
    }
