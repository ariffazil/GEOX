from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional

import numpy as np

from geox_core.enums.statuses import (
    get_standard_envelope,
    enrich_envelope_with_metabolic,
)
from geox_mcp.tools._helpers import (
    _get_artifact,
    _artifact_exists,
)
from geox_core.core.physics_guard import PhysicsGuard

logger = logging.getLogger("geox.canonical.anomalous_contrast")

# ═══════════════════════════════════════════════════════════════════════════════
# ANOMALOUS CONTRAST DETECTOR (LC#28)
# W → P → C → M → G → J  loop implementation for GEOX
# Witness → Perception → Contrast → Meaning → Guard → Judgment
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_anomalous_contrast_detector(
    evidence_refs: List[str],
    contrast_mode: Literal["seismic", "well_log", "cross_domain"] = "well_log",
    baseline_window: int = 10,
    z_score_threshold: float = 2.0,
    significance_filter: Literal["all", "major", "critical"] = "major",
) -> dict:
    """Detect anomalous contrast in earth evidence through the W→P→C→M→G→J loop.

    Applies statistical anomaly detection (z-score) against a rolling baseline,
    then interprets geological meaning and verifies against CANON-9 physics bounds.

    Args:
        evidence_refs: List of artifact references containing curve or trace data.
        contrast_mode: Type of evidence being analyzed.
        baseline_window: Samples for rolling baseline statistics.
        z_score_threshold: Standard-deviation threshold for anomaly flagging.
        significance_filter: Minimum severity to report (all / major / critical).

    Returns:
        LEM envelope with contrast detections, geological meanings, and physics guard.
    """

    # ── WITNESS: Attest evidence ───────────────────────────────────────────────
    if not evidence_refs:
        envelope = get_standard_envelope(
            {"tool": "geox_anomalous_contrast_detector", "error": "No evidence_refs provided."},
            tool_class="contrast",
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            perception_class="HYPOTHESIS",
        )
        return enrich_envelope_with_metabolic(envelope, "geox_anomalous_contrast_detector")

    missing = [ref for ref in evidence_refs if not _artifact_exists(ref)]
    if missing:
        envelope = get_standard_envelope(
            {"tool": "geox_anomalous_contrast_detector", "missing_refs": missing},
            tool_class="contrast",
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            perception_class="HYPOTHESIS",
        )
        return enrich_envelope_with_metabolic(envelope, "geox_anomalous_contrast_detector")

    # ── PERCEPTION: Decode raw signals ─────────────────────────────────────────
    all_values: List[float] = []
    ref_metadata: List[Dict[str, Any]] = []

    for ref in evidence_refs:
        artifact = _get_artifact(ref)
        if not artifact:
            continue
        data = artifact.get("data") or artifact.get("curve") or artifact.get("trace") or []
        if data:
            flat = [float(v) for v in np.asarray(data).flatten() if np.isfinite(float(v))]
            all_values.extend(flat)
            ref_metadata.append({
                "ref": ref,
                "n_samples": len(flat),
                "mean": float(np.mean(flat)) if flat else None,
                "std": float(np.std(flat)) if flat else None,
            })

    if len(all_values) < baseline_window * 2:
        envelope = get_standard_envelope(
            {
                "tool": "geox_anomalous_contrast_detector",
                "error": f"Insufficient samples ({len(all_values)}) for baseline window {baseline_window}.",
            },
            tool_class="contrast",
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
            perception_class="HYPOTHESIS",
        )
        return enrich_envelope_with_metabolic(envelope, "geox_anomalous_contrast_detector")

    arr = np.array(all_values, dtype=float)

    # ── CONTRAST: Rolling z-score anomaly detection ────────────────────────────
    # Equation: z_i = (x_i - μ_window) / σ_window
    anomalies: List[Dict[str, Any]] = []
    baseline_stats: List[Dict[str, Any]] = []

    for i in range(len(arr)):
        start = max(0, i - baseline_window)
        window = arr[start:i] if i > start else arr[start : start + baseline_window]
        if len(window) < 2:
            continue
        mu = float(np.mean(window))
        sigma = float(np.std(window)) + 1e-12
        z = float((arr[i] - mu) / sigma)
        baseline_stats.append({"index": i, "mu": mu, "sigma": sigma, "z": z})

        if abs(z) >= z_score_threshold:
            severity = "critical" if abs(z) >= 3.5 else "major" if abs(z) >= 2.5 else "minor"
            if significance_filter == "critical" and severity != "critical":
                continue
            if significance_filter == "major" and severity == "minor":
                continue
            anomalies.append({
                "index": i,
                "value": float(arr[i]),
                "z_score": round(z, 4),
                "severity": severity,
                "baseline_mu": round(mu, 4),
                "baseline_sigma": round(sigma, 4),
                "equation": "z = (x_i - μ_window) / σ_window",
            })

    # ── MEANING: Geological hypothesis inference ───────────────────────────────
    candidate_meanings: List[Dict[str, Any]] = []
    if anomalies:
        n_critical = sum(1 for a in anomalies if a["severity"] == "critical")
        n_major = sum(1 for a in anomalies if a["severity"] == "major")
        avg_z = float(np.mean([abs(a["z_score"]) for a in anomalies]))

        if contrast_mode == "seismic":
            if avg_z > 3.0:
                meaning = "High-amplitude anomaly — possible fluid contact, tuning, or fault shadow."
            elif avg_z > 2.5:
                meaning = "Moderate amplitude anomaly — possible lithology change or porosity effect."
            else:
                meaning = "Weak amplitude anomaly — noise or stratigraphic thinning."
        elif contrast_mode == "well_log":
            if avg_z > 3.0:
                meaning = "Extreme log contrast — possible fault, unconformity, or facies boundary."
            elif avg_z > 2.5:
                meaning = "Significant log contrast — possible fluid change or diagenetic front."
            else:
                meaning = "Mild log contrast — gradual facies transition or borehole effect."
        else:
            meaning = "Cross-domain anomaly — requires seismic-well tie for grounded interpretation."

        candidate_meanings.append({
            "meaning": meaning,
            "confidence": "low" if avg_z < 2.5 else "moderate" if avg_z < 3.5 else "high",
            "n_anomalies": len(anomalies),
            "n_critical": n_critical,
            "n_major": n_major,
            "avg_abs_z": round(avg_z, 4),
            "equation": "confidence = f(avg|z|, contrast_mode, n_critical)",
        })

    # ── GUARD: CANON-9 physics verification ────────────────────────────────────
    guard = PhysicsGuard()
    guard_result = guard.validate_velocity_sanity(
        np.array([float(v) for v in arr if v > 0]),
        np.linspace(0, len(arr), len(arr)),
    )
    constraints_checked = [
        {
            "constraint": "CANON-9_Vp_bounds",
            "check": "1500 <= Vp <= 6000 m/s",
            "passed": not guard_result.hold,
            "violation_count": int(guard_result.to_dict().get("violations", 0)) if hasattr(guard_result, "to_dict") else 0,
        },
        {
            "constraint": "statistical_significance",
            "check": f"|z| >= {z_score_threshold}",
            "passed": len(anomalies) > 0,
            "n_passed": len(anomalies),
        },
    ]

    # ── JUDGMENT: Verdict ──────────────────────────────────────────────────────
    if guard_result.hold:
        claim_state = "VOID"
        execution_status = "HOLD"
    elif len(anomalies) == 0:
        claim_state = "QC_VERIFIED"
        execution_status = "SUCCESS"
    else:
        claim_state = "DERIVED_CANDIDATE"
        execution_status = "SUCCESS"

    observed = {
        "n_samples": len(all_values),
        "n_refs": len(evidence_refs),
        "contrast_mode": contrast_mode,
        "baseline_window": baseline_window,
        "z_threshold": z_score_threshold,
        "n_anomalies": len(anomalies),
    }

    envelope = get_standard_envelope(
        observed,
        tool_class="contrast",
        claim_tag="HYPOTHESIS" if claim_state == "DERIVED_CANDIDATE" else claim_state,
        claim_state=claim_state,
        perception_class="DERIVED",
        evidence_refs=evidence_refs,
    )

    envelope["anomalies"] = anomalies
    envelope["ref_metadata"] = ref_metadata
    envelope["audit_receipt"] = {
        "deterministic_engine": "geox-contrast-v1",
        "equation": "z_i = (x_i - μ_window) / σ_window",
        "baseline_window": baseline_window,
        "z_threshold": z_score_threshold,
        "physics_guard_passed": not guard_result.hold,
    }

    return enrich_envelope_with_metabolic(
        envelope,
        "geox_anomalous_contrast_detector",
        anomalous_contrasts=anomalies,
        candidate_meanings=candidate_meanings,
        constraints_checked=constraints_checked,
    )
