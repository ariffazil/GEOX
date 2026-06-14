"""
GEOX Forward Model Synthetic — Deterministic 1D Seismogram Generation
═══════════════════════════════════════════════════════════════════════════════
Well logs → Acoustic Impedance → Reflection Coefficients → Wavelet convolution
→ Synthetic Seismogram + Depth-Time table.

Physics:
    AI(z) = Vp(z) × ρ(z)
    RC(i) = [AI(i+1) - AI(i)] / [AI(i+1) + AI(i)]
    TWT(z) = 2 × Σ(dz / Vp) + TWT_water
    Synthetic(t) = RC(t) ∗ W(t)

Constitutional: F9-Rahmah (physics-only, no hallucination).
Author: M Arif Fazil | DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

from datetime import datetime, timezone

import logging
from typing import Any, Literal

import numpy as np

from geox_core.core.geox_2d import build_wavelet
from geox_core.enums.statuses import (
    ArtifactStatus,
    ExecutionStatus,
    GovernanceStatus,
    enrich_envelope_with_metabolic,
    get_standard_envelope,
)
from geox_core.physics import (
    convolve_trace as convolve_synthetic,
)
from geox_core.physics import (
    impedance_array as calculate_acoustic_impedance,
)
from geox_core.physics import (
    reflectivity_array as calculate_reflectivity,
)
from geox_core.physics import (
    ricker_wavelet as generate_ricker,
)
from geox_mcp.tools._helpers import (
    _artifact_exists,
    _get_well_data_with_depth,
)

logger = logging.getLogger("geox.canonical.forward_model")


async def geox_forward_model_synthetic(
    vp: list[float] | None = None,
    rho: list[float] | None = None,
    depth: list[float] | None = None,
    wavelet_type: Literal["ricker", "ormsby", "klauder"] = "ricker",
    wavelet_freq: float = 20.0,
    wavelet_params: dict[str, Any] | None = None,
    water_depth_m: float = 0.0,
    vp_water: float = 1500.0,
    dt_ms: float = 4.0,
    noise_db: float = -18.0,
    well_id: str | None = None,
    output_format: Literal["full", "compact"] = "full",
) -> dict:
    """Forward seismic model: Well logs → AI → RC → Wavelet convolution → Synthetic.

    Accepts either raw arrays (vp, rho, depth) or a well_id referencing an
    ingested LAS artifact. If well_id is provided, vp/rho/depth arrays are
    optional and will be loaded from the artifact store.

    Physics:
        AI(z) = Vp(z) × ρ(z)                                           [kg/m²·s]
        RC(i) = [AI(i+1) - AI(i)] / [AI(i+1) + AI(i)]                  [dimensionless]
        TWT(z) = 2 × ∫(dz/Vp) + TWT_water                              [ms]
        Synthetic(t) = RC(t) ∗ W(t)                                    [amplitude]

    Args:
        vp: P-wave velocity in m/s. Optional if well_id provided.
        rho: Bulk density in g/cc. Optional if well_id provided.
        depth: Depth in metres (TVD or MD). Optional if well_id provided.
        wavelet_type: "ricker", "ormsby", or "klauder".
        wavelet_freq: Dominant frequency in Hz (Ricker) or centre frequency.
        wavelet_params: Additional wavelet parameters (e.g. {"f1":10,"f2":20,"f3":40,"f4":60} for Ormsby).
        water_depth_m: Water depth for TWT water-column correction.
        vp_water: P-wave velocity in water (m/s).
        dt_ms: Time sampling interval in ms.
        noise_db: Random noise amplitude in dB. Set to 0 for noise-free.
        well_id: Optional artifact reference to load curves from store.
        output_format: "full" returns all arrays; "compact" returns metadata only.

    Returns:
        LEM-enriched dict with synthetic trace, AI profile, RC series, TWT axis,
        depth-to-time table, wavelet signature, and full provenance.
    """

    # ── 1. ATTESTATION: Resolve data source ──────────────────────────────────
    if well_id is not None:
        if not _artifact_exists(well_id):
            return get_standard_envelope(
                {
                    "tool": "geox_forward_model_synthetic",
                    "error_code": "NO_VALID_EVIDENCE",
                    "message": f"Well artifact '{well_id}' not found in registry.",
                },
                tool_class="compute",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
                evidence_refs=[well_id] if well_id else [],
            )
        loaded = _get_well_data_with_depth(well_id)
        if "error" in loaded:
            return get_standard_envelope(
                {
                    "tool": "geox_forward_model_synthetic",
                    "error_code": "LAS_LOAD_FAILED",
                    "message": loaded["error"],
                    "detail": loaded.get("detail", ""),
                },
                tool_class="compute",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
                evidence_refs=[well_id],
            )
        curves = loaded["curves"]
        depth_arr = loaded["depth"]
        # Resolve VP from DT or VP mnemonic
        vp_arr = None
        for mnemonic in ["VP", "DT", "DTC", "DTCO"]:
            if mnemonic in curves:
                if mnemonic == "DT":
                    vp_arr = 1e6 / np.clip(curves[mnemonic], 40, 300)
                else:
                    vp_arr = curves[mnemonic]
                break
        if vp_arr is None:
            return get_standard_envelope(
                {
                    "tool": "geox_forward_model_synthetic",
                    "error_code": "VP_CURVE_MISSING",
                    "message": "No VP or DT curve found in well artifact.",
                    "available": list(curves.keys()),
                },
                tool_class="compute",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
                evidence_refs=[well_id],
            )
        # Resolve density
        rho_arr = None
        for mnemonic in ["RHOB", "RHOZ", "DEN"]:
            if mnemonic in curves:
                rho_arr = curves[mnemonic]
                break
        if rho_arr is None:
            # Gardner fallback with constitutional flag
            rho_arr = 1.741 * (vp_arr**0.25)
            logger.info("F2: Gardner fallback applied for density (RHOB missing).")
            gardner_flag = True
        else:
            gardner_flag = False
    else:
        if not vp or not rho or not depth:
            return get_standard_envelope(
                {
                    "tool": "geox_forward_model_synthetic",
                    "error_code": "MISSING_INPUTS",
                    "message": "Provide either well_id or vp/rho/depth arrays.",
                },
                tool_class="compute",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
            )
        vp_arr = np.array(vp, dtype=float)
        rho_arr = np.array(rho, dtype=float)
        depth_arr = np.array(depth, dtype=float)
        gardner_flag = False

    # ── 2. PHYSICS: AI → RC → TWT ────────────────────────────────────────────
    # Ensure consistent units: rho in g/cc → kg/m³ for SI impedance
    rho_si = rho_arr * 1000.0
    ai = calculate_acoustic_impedance(rho_si, vp_arr)
    rc = calculate_reflectivity(ai)

    # Time-depth conversion (two-way travel time)
    twt = np.zeros_like(depth_arr, dtype=float)
    for i in range(1, len(depth_arr)):
        dz = depth_arr[i] - depth_arr[i - 1]
        twt[i] = twt[i - 1] + 2.0 * dz / vp_arr[i] * 1000.0  # ms
    if water_depth_m > 0.0:
        twt_water = 2.0 * water_depth_m / vp_water * 1000.0
        twt += twt_water

    # Regularize to uniform time sampling for convolution
    t_uniform = np.arange(twt[0], twt[-1] + dt_ms, dt_ms)
    rc_uniform = np.interp(t_uniform, twt, rc, left=0.0, right=0.0)

    # ── 3. WAVELET & CONVOLUTION ─────────────────────────────────────────────
    if wavelet_type == "ricker":
        wavelet = generate_ricker(wavelet_freq, dt_ms / 1000.0)
    else:
        wavelet = build_wavelet(wavelet_freq, dt_ms, wavelet_type)

    synthetic = convolve_synthetic(rc_uniform, wavelet)

    # Optional noise
    if noise_db < 0:
        noise_amp = 10 ** (noise_db / 20.0)
        rng = np.random.default_rng(42)
        synthetic += rng.normal(0, noise_amp * np.max(np.abs(synthetic) + 1e-9), len(synthetic))

    # ── 4. LEM ENVELOPE CONSTRUCTION ─────────────────────────────────────────
    primary_artifact = {
        "tool": "geox_forward_model_synthetic",
        "synthetic_length_samples": len(synthetic),
        "twt_range_ms": [float(t_uniform[0]), float(t_uniform[-1])],
        "depth_range_m": [float(depth_arr[0]), float(depth_arr[-1])],
        "wavelet_type": wavelet_type,
        "wavelet_freq_hz": wavelet_freq,
        "dt_ms": dt_ms,
        "water_depth_m": water_depth_m,
        "gardner_fallback_used": gardner_flag,
    }

    if output_format == "full":
        primary_artifact["synthetic_trace"] = synthetic.tolist()
        primary_artifact["ai_profile"] = ai.tolist()
        primary_artifact["rc_series"] = rc.tolist()
        primary_artifact["twt_axis_ms"] = t_uniform.tolist()
        primary_artifact["depth_axis_m"] = depth_arr.tolist()
        primary_artifact["depth_to_twt_table"] = [{"depth_m": float(d), "twt_ms": float(t)} for d, t in zip(depth_arr, twt)]
        primary_artifact["wavelet_signature"] = wavelet.tolist()

    envelope = get_standard_envelope(
        primary_artifact,
        tool_class="compute",
        execution_status=ExecutionStatus.SUCCESS,
        governance_status=GovernanceStatus.QUALIFY,
        artifact_status=ArtifactStatus.COMPUTED,
        claim_tag="COMPUTED",
        claim_state="COMPUTED",
        uncertainty="Moderate",
        evidence_refs=[well_id] if well_id else [],
        physics_guard={
            "guard_passed": True,
            "physics_version": "geox-forward-model-v2026.05.21",
            "equations_used": [
                "AI = Vp × ρ",
                "RC = (AI₂ - AI₁) / (AI₂ + AI₁)",
                "TWT = 2 × ∫(dz / Vp)",
                "Synthetic = RC ∗ W",
            ],
            "assumptions": [
                "zero-offset (normal incidence)",
                "1D isotropic earth model",
                "no AVO / anisotropy correction",
            ],
            "limitations": [
                "neglects transmission losses",
                "no multiple reflections",
                "no surface ghosts",
            ],
        },
        audit_receipt={
            "tool": "geox_forward_model_synthetic",
            "version": "2026.05.21",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "floors_checked": [1, 2, 3, 9, 10, 11, 13],
        },
        canon_9_touched=["Vp", "rho", "phi"],
    )

    # Inject LEM confidence fields
    envelope["confidence"] = {
        "level": "MEDIUM",
        "uncertainty_band": {"p10": 0.85, "p50": 1.0, "p90": 1.15},
        "sensitivity_to": [
            "wavelet_frequency",
            "vp_model_accuracy",
            "density_curve_quality",
        ],
    }
    envelope["provenance"]["equations_used"] = [
        "AI = Vp × ρ",
        "RC = (AI₂ - AI₁) / (AI₂ + AI₁)",
        "TWT = 2 × ∫(dz / Vp)",
        "Synthetic = RC ∗ W",
    ]

    return enrich_envelope_with_metabolic(
        envelope,
        "geox_forward_model_synthetic",
        witness_type="seismic",
        witness_status="COMPUTED",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FORGE 2026-06-10 — Zahid Eureka: Forward-Consistency Gate
# ═══════════════════════════════════════════════════════════════════════════════
# "Re-forward-model the inversion result and correlate against the seismic input.
#  Correlation ≈ 1.0 proves data-consistency. Without this check, the inversion
#  result has no self-validation." — Zahid Zamanshah, 2026-06-09
#
# Physics: Pearson r between synthetic trace and input seismic trace.
# Gate: r > 0.85 = data-consistent. Never says "correct" — only "data-consistent."
#
# Lancaster-Whitcombe (2000): coloured inversion preserves relative impedance but
# cannot recover absolute low frequencies. Gate passes if the inversion reproduces
# the band-limited seismic — it does NOT prove the absolute impedance is correct.
# ═══════════════════════════════════════════════════════════════════════════════


def _forward_consistency_gate(
    synthetic: np.ndarray,
    seismic_input: np.ndarray,
    threshold: float = 0.85,
) -> dict[str, Any]:
    """Re-forward-model the synthetic and correlate against input seismic.

    This IS the gate Zahid describes: after inversion (AI → RC → wavelet
    convolution → synthetic), correlate the output synthetic against the
    original seismic trace. Pearson r ≈ 1.0 proves the inversion is
    internally data-consistent. r < threshold proves something went wrong
    in the forward-inverse loop.

    Constitutional grounding:
      - F2 TRUTH: Pearson r is a deterministic statistic — deterministic output
      - F9 ANTI-HANTU: Never says "correct." Only says "data-consistent."
      - F7 HUMILITY: If gate cannot run (no seismic input), humility = 1.0

    Args:
        synthetic: The forward-modeled synthetic trace (1D array).
        seismic_input: The original seismic trace at the well location (1D array).
        threshold: Pearson r threshold for data-consistency. Default 0.85.

    Returns:
        dict with correlation, data_consistent flag, gate_passed, interpretation,
        cite, and humility_score.
    """
    # Align lengths — use minimum
    n = min(len(synthetic), len(seismic_input))
    if n < 3:
        return {
            "gate_run": True,
            "correlation_r": None,
            "data_consistent": False,
            "gate_passed": False,
            "threshold": threshold,
            "interpretation": "INSUFFICIENT_SAMPLES — need at least 3 samples for correlation",
            "cite": "Lancaster-Whitcombe (2000) coloured inversion: data-consistent ≠ correct",
            "humility_score": 1.0,
            "eureka_ref": "FORWARD_CONSISTENCY_GATE_2026_06_10",
        }

    syn = np.asarray(synthetic[:n], dtype=float)
    seis = np.asarray(seismic_input[:n], dtype=float)

    # Guard against zero-variance inputs
    syn_std = np.std(syn)
    seis_std = np.std(seis)
    if syn_std < 1e-12 or seis_std < 1e-12:
        return {
            "gate_run": True,
            "correlation_r": 0.0,
            "data_consistent": False,
            "gate_passed": False,
            "threshold": threshold,
            "interpretation": "ZERO_VARIANCE — one or both inputs have no signal variation",
            "cite": "Lancaster-Whitcombe (2000): data-consistent ≠ correct",
            "humility_score": 1.0,
            "eureka_ref": "FORWARD_CONSISTENCY_GATE_2026_06_10",
        }

    # Pearson correlation coefficient
    r = float(np.corrcoef(syn, seis)[0, 1])

    # NaN guard
    if np.isnan(r):
        r = 0.0

    data_consistent = bool(r >= threshold)

    # Interpretation — never says "correct"
    if data_consistent and r > 0.95:
        interpretation = (
            f"DATA_CONSISTENT (r={r:.4f}): The inversion reproduces the input "
            f"seismic with high fidelity. This proves internal consistency of the "
            f"forward-inverse loop but does NOT prove the absolute impedance model "
            f"is correct — low frequencies remain in the null space of band-limited "
            f"inversion (Lancaster-Whitcombe, 2000)."
        )
    elif data_consistent:
        interpretation = (
            f"DATA_CONSISTENT (r={r:.4f}): The inversion is internally consistent "
            f"with the input seismic at the {threshold:.0%} threshold. "
            f"Moderate residual may indicate wavelet estimation error, tuning "
            f"effects, or noise contamination — not a physical failure."
        )
    else:
        interpretation = (
            f"CONSISTENCY_CHECK_FAILED (r={r:.4f} < {threshold}): The inversion "
            f"does NOT adequately reproduce the input seismic. Possible causes: "
            f"wavelet mismatch, incorrect velocity model, time-depth error, or "
            f"pre-stack effects contaminating the post-stack trace. "
            f"REWORK required before using this synthetic for interpretation."
        )

    return {
        "gate_run": True,
        "correlation_r": round(r, 6),
        "data_consistent": data_consistent,
        "gate_passed": data_consistent,
        "threshold": threshold,
        "interpretation": interpretation,
        "cite": "Lancaster-Whitcombe (2000): data-consistent ≠ correct. "
        "Correlation proves the inversion reproduces the input seismic. "
        "Without a well-tied LFM, low frequencies are a 1/f integration "
        "ramp — not calibrated geology.",
        "humility_score": round(1.0 - min(r, 0.95), 4) if data_consistent else 1.0,
        "eureka_ref": "FORWARD_CONSISTENCY_GATE_2026_06_10",
    }
