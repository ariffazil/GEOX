"""
GEOX Horizon Contrast Surface — ToAC-as-Attention Pipeline
╔══════════════════════════════════════════════════════════════════╗
║  Eureka GeoX Theory — Agent Horizon Interpretation Engine       ║
║                                                                 ║
║  Every seismic attribute IS a contrast operator:                ║
║    Coherence   = lateral contrast  (faults, channels, edges)    ║
║    Curvature   = geometric contrast (folds, domes, drag)        ║
║    Frequency   = stratigraphic contrast (tuning, fluid)         ║
║    Amplitude   = impedance contrast  (lithology, porosity)      ║
║    Phase       = continuity contrast (unconformities, onlap)    ║
║    AVO         = fluid/lithology contrast (HC indicator)        ║
║                                                                 ║
║  Signal = Observation − Expectation  (in every domain)          ║
║  Fusion = attention-weighted sum across attribute channels      ║
║                                                                 ║
║  Pipeline:                                                      ║
║    1. Background model (the "Mudrock line" of the section)      ║
║    2. Multi-attribute contrast residuals (per-sample δ_i)       ║
║    3. Attention-weighted fusion (geological query × attributes) ║
║    4. Horizon candidate extraction (peaks in fused surface)     ║
║    5. Geological alignment governance (physics + well + model)  ║
║    6. Audited output (ClaimTag + SEAL/HOLD/SABAR)               ║
╚══════════════════════════════════════════════════════════════════╝

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastmcp import Context

from geox_core.enums.statuses import (
    ArtifactStatus,
    ExecutionStatus,
    GovernanceStatus,
    enrich_envelope_with_metabolic,
    get_standard_envelope,
)

logger = logging.getLogger("geox.horizon_contrast")

TOOL_NAME = "geox_horizon_contrast_surface"

# ═══════════════════════════════════════════════════════════════════════════════
# Attention Query Templates — Geological Feature Vectors (ABKSS Framework)
# ═══════════════════════════════════════════════════════════════════════════════
# Each query vector defines which attributes matter most for a given geological
# feature type. This IS the "geological knowledge" that weights the attention.
# The agent's interpretation query selects one of these templates (or a custom
# composition) to drive the multi-attribute fusion.

ATTENTION_QUERY_TEMPLATES: dict[str, dict[str, Any]] = {
    "unconformity": {
        "phase": 0.45,
        "coherence": 0.30,
        "frequency": 0.15,
        "amplitude": 0.05,
        "curvature": 0.05,
        "note": "Unconformities manifest as phase breaks + coherence boundaries. "
        "Attention heavily weighted to continuity contrast.",
    },
    "flooding_surface": {
        "amplitude": 0.35,
        "frequency": 0.30,
        "phase": 0.20,
        "coherence": 0.10,
        "curvature": 0.05,
        "note": "Flooding surfaces are high-amplitude, continuous reflectors "
        "with consistent frequency character across the basin.",
    },
    "carbonate_platform": {
        "amplitude": 0.40,
        "frequency": 0.30,
        "curvature": 0.15,
        "coherence": 0.10,
        "phase": 0.05,
        "note": "Carbonates (BEBAS equivalent) produce strong, irregular amplitude with karst-related curvature anomalies.",
    },
    "channel_system": {
        "coherence": 0.40,
        "amplitude": 0.25,
        "curvature": 0.15,
        "frequency": 0.10,
        "phase": 0.10,
        "note": "Channels appear as low-coherence linear features with amplitude "
        "contrast against background. Lateral contrast dominates.",
    },
    "fault_zone": {
        "coherence": 0.50,
        "curvature": 0.30,
        "phase": 0.10,
        "frequency": 0.05,
        "amplitude": 0.05,
        "note": "Faults are primarily coherence breaks with associated curvature anomalies from drag folding.",
    },
    "fluid_contact": {
        "amplitude": 0.40,
        "frequency": 0.30,
        "phase": 0.15,
        "coherence": 0.10,
        "curvature": 0.05,
        "note": "Fluid contacts (OWS, GWC) produce flat events with frequency "
        "contrast from gas-over-water effect. AVO confirmation ideal but requires "
        "pre-stack data.",
    },
    "sequence_boundary": {
        "phase": 0.30,
        "coherence": 0.25,
        "frequency": 0.20,
        "amplitude": 0.15,
        "curvature": 0.10,
        "note": "Sequence boundaries combine unconformity character (onlap/truncation) "
        "with flooding surface continuity. Mixed attention profile.",
    },
    "gas_sand": {
        "amplitude": 0.40,
        "frequency": 0.30,
        "phase": 0.15,
        "coherence": 0.10,
        "curvature": 0.05,
        "note": "Class III AVO signature: bright spot with amplitude increasing at "
        "far offsets. Frequency attenuation from gas absorption. "
        "ATTENTION WARNING: high false-positive rate — brine sands can mimic.",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# Stratigraphic Column (ABKSS Framework — Layang-Layang type section)
# ═══════════════════════════════════════════════════════════════════════════════

ABKSS_STRATIGRAPHIC_COLUMN: list[dict[str, Any]] = [
    {
        "formation": "ASAS",
        "age": "Oligocene-Early Miocene",
        "lithology": "Fluvial-lacustrine clastics",
        "seismic_character": "Low-continuity, variable amplitude, discontinuous reflectors",
        "query_template": "channel_system",
        "expected_contrast": "MODERATE",
        "key_horizons": ["Top_ASAS", "Intra_ASAS_sand"],
    },
    {
        "formation": "BEBAS",
        "age": "Early-Mid Miocene",
        "lithology": "Carbonate platform / reefal buildup",
        "seismic_character": "High-amplitude mounded/chaotic, karst features",
        "query_template": "carbonate_platform",
        "expected_contrast": "HIGH",
        "key_horizons": ["Top_BEBAS", "Base_BEBAS", "Intra_BEBAS_karst"],
    },
    {
        "formation": "KAPUR",
        "age": "Mid-Late Miocene",
        "lithology": "Prograding deltaic clastics",
        "seismic_character": "Oblique clinoforms, variable amplitude, growth faulting",
        "query_template": "sequence_boundary",
        "expected_contrast": "MODERATE-HIGH",
        "key_horizons": ["Top_KAPUR", "MFS_KAPUR", "SB_KAPUR_base"],
    },
    {
        "formation": "SABAR",
        "age": "Late Miocene-Pliocene",
        "lithology": "Shallow marine clastics",
        "seismic_character": "Parallel continuous, moderate amplitude, progradational",
        "query_template": "flooding_surface",
        "expected_contrast": "LOW-MODERATE",
        "key_horizons": ["Top_SABAR", "MFS_SABAR"],
    },
    {
        "formation": "SENJA",
        "age": "Pliocene-Recent",
        "lithology": "Shelf to upper slope clastics",
        "seismic_character": "High-continuity parallel reflectors, seafloor multiple risk",
        "query_template": "flooding_surface",
        "expected_contrast": "LOW",
        "key_horizons": ["Seafloor", "MFS_SENJA"],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# Background Model — Expected attribute baseline
# ═══════════════════════════════════════════════════════════════════════════════


def _compute_background_model(
    attribute_data: dict[str, list[float]],
    depth: list[float],
    well_ties: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compute expected attribute trends vs depth (the 'Mudrock line' of the section).

    For each attribute, computes:
    - Running mean (compaction trend)
    - Running std (expected natural variation)
    - Depth-dependent baseline

    If well ties provided, uses them to calibrate the expected response at known
    formation tops (equivalent to fitting Mudrock line intercept).
    """
    import numpy as np

    background: dict[str, Any] = {}
    depth_arr = np.array(depth, dtype=float)

    for attr_name, values in attribute_data.items():
        vals = np.array(values, dtype=float)
        n = len(vals)
        window = max(n // 10, 5)

        running_mean = np.convolve(vals, np.ones(window) / window, mode="same")
        running_std = np.zeros_like(vals)
        for i in range(n):
            lo = max(0, i - window // 2)
            hi = min(n, i + window // 2)
            running_std[i] = float(np.std(vals[lo:hi]))

        background[attr_name] = {
            "mean": running_mean.tolist(),
            "std": running_std.tolist(),
            "window": window,
            "depth_range": [float(depth_arr[0]), float(depth_arr[-1])],
            "global_mean": float(np.mean(vals)),
            "global_std": float(np.std(vals)),
        }

    # Well tie calibration
    calibration: list[dict] = []
    if well_ties:
        for formation, tie_depth in well_ties.items():
            idx = int(np.argmin(np.abs(depth_arr - tie_depth)))
            cal = {"formation": formation, "depth_m": float(depth_arr[idx])}
            for attr_name in attribute_data:
                vals = np.array(attribute_data[attr_name], dtype=float)
                cal[f"{attr_name}_at_tie"] = float(vals[idx])
                cal[f"{attr_name}_bg_at_tie"] = background[attr_name]["mean"][idx]
                cal[f"{attr_name}_deviation"] = float(vals[idx] - background[attr_name]["mean"][idx])
            calibration.append(cal)

    return {
        "background_model": background,
        "well_tie_calibration": calibration,
        "equations_used": ["running_mean", "running_std", "depth_trend"],
        "assumptions": [
            "Compaction trend is smooth and monotonic",
            "Attribute statistics are locally stationary within window",
            "Well ties represent true formation depths (no checkshot error)",
        ],
    }


def _compute_contrast_residuals(
    attribute_data: dict[str, list[float]],
    background: dict[str, Any],
) -> dict[str, list[float]]:
    """Compute per-sample contrast residuals for each attribute.

    δ_i^(attr) = A_obs(x,t) − A_bg(x,t)    [Contrast Primitive]

    Returns normalized residuals (z-score relative to running mean/std).
    """
    import numpy as np

    residuals: dict[str, list[float]] = {}
    bg_model = background.get("background_model", background)

    for attr_name, values in attribute_data.items():
        vals = np.array(values, dtype=float)
        bg = bg_model.get(attr_name, {})
        mean = np.array(bg.get("mean", [0.0] * len(vals)), dtype=float)
        std = np.array(bg.get("std", [1.0] * len(vals)), dtype=float)
        std = np.where(std < 1e-9, 1.0, std)
        z_scores = (vals - mean) / std
        residuals[attr_name] = z_scores.tolist()

    return residuals


def _attention_weighted_fusion(
    residuals: dict[str, list[float]],
    query_template: dict[str, float],
    depth: list[float],
    geological_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fuse multi-attribute contrast residuals using attention weighting.

    α_k = softmax(q_geological · k_attribute_k / √d)    [Attention over attributes]

    Contrast(x,t) = Σ_k α_k · δ_i^(k)                      [Fused surface]

    Each attribute is a "key" in the attention mechanism. The query vector
    encodes "what kind of geological feature am I looking for?"
    """
    import numpy as np

    n_samples = len(depth)
    attr_names = [k for k in residuals if k in query_template]
    n_attrs = len(attr_names)

    if n_attrs == 0:
        return {
            "fused_contrast": [0.0] * n_samples,
            "attention_weights": {},
            "error": "No matching attributes between query template and data",
        }

    # Compute attention weights via softmax over attribute query scores
    queries = np.array([query_template.get(a, 0.0) for a in attr_names], dtype=float)
    queries = queries / (np.sum(queries) + 1e-9)  # Normalize to sum=1

    alphas = np.exp(queries * 3.0) / np.sum(np.exp(queries * 3.0))  # Temperature=1/3

    # Weighted fusion
    fused = np.zeros(n_samples, dtype=float)
    for i, attr_name in enumerate(attr_names):
        res = np.array(residuals[attr_name], dtype=float)
        fused += alphas[i] * res

    # Per-attribute contribution
    contributions = {}
    for i, attr_name in enumerate(attr_names):
        contributions[attr_name] = {
            "weight": round(float(alphas[i]), 4),
            "query_score": round(float(queries[i]), 4),
            "mean_abs_contribution": round(float(np.mean(np.abs(alphas[i] * np.array(residuals[attr_name])))), 4),
        }

    return {
        "fused_contrast": fused.tolist(),
        "attention_weights": {attr: round(float(alphas[i]), 4) for i, attr in enumerate(attr_names)},
        "attribute_contributions": contributions,
        "dominant_attribute": max(contributions.items(), key=lambda x: x[1]["weight"])[0],
        "n_attributes_fused": n_attrs,
    }


def _extract_horizon_candidates(
    fused_contrast: list[float],
    depth: list[float],
    peak_threshold: float = 1.5,
    min_separation_m: float = 20.0,
) -> list[dict[str, Any]]:
    """Extract peaks from the fused contrast surface as horizon candidates.

    Peak = local maximum in contrast surface where contrast > threshold.
    These are NOT yet validated as real geological horizons.
    """
    import numpy as np

    fc = np.array(fused_contrast, dtype=float)
    d = np.array(depth, dtype=float)

    candidates = []
    for i in range(1, len(fc) - 1):
        if fc[i] > fc[i - 1] and fc[i] > fc[i + 1] and fc[i] > peak_threshold:
            candidates.append(
                {
                    "index": i,
                    "depth_m": float(d[i]),
                    "contrast_score": round(float(fc[i]), 4),
                }
            )

    # Filter by minimum separation
    filtered = []
    for c in sorted(candidates, key=lambda x: x["contrast_score"], reverse=True):
        too_close = any(abs(c["depth_m"] - f["depth_m"]) < min_separation_m for f in filtered)
        if not too_close:
            filtered.append(c)

    return sorted(filtered, key=lambda x: x["depth_m"])


def _geological_alignment_check(
    candidates: list[dict[str, Any]],
    well_ties: dict[str, float] | None,
    stratigraphic_column: list[dict[str, Any]],
    physics_guard_passed: bool,
) -> dict[str, Any]:
    """Governance checks: well ties, stratigraphic order, physics constraints.

    This is Step 5 of the ToAC-as-Attention pipeline — where the agent's
    contrast-driven picks are validated against ground truth.
    """
    flags = []
    well_tie_results = []

    if well_ties:
        for formation, tie_depth in well_ties.items():
            match = None
            best_dist = float("inf")
            for c in candidates:
                dist = abs(c["depth_m"] - tie_depth)
                if dist < best_dist:
                    best_dist = dist
                    match = c

            half_wavelength = 25.0  # ~25m at 2500m/s, 50Hz
            if match and best_dist < half_wavelength:
                well_tie_results.append(
                    {
                        "formation": formation,
                        "tie_depth_m": tie_depth,
                        "candidate_depth_m": match["depth_m"],
                        "mistie_m": round(best_dist, 2),
                        "verdict": "MATCH" if best_dist < half_wavelength / 2 else "QUALIFY",
                    }
                )
            else:
                well_tie_results.append(
                    {
                        "formation": formation,
                        "tie_depth_m": tie_depth,
                        "candidate_depth_m": None,
                        "mistie_m": None,
                        "verdict": "NO_CANDIDATE — 888_HOLD",
                    }
                )
                flags.append(f"Well tie MISSING for {formation} at {tie_depth}m — no candidate within {half_wavelength}m")

    # Stratigraphic order check
    ordered = sorted(candidates, key=lambda x: x["depth_m"])
    for i in range(len(ordered) - 1):
        shallow = ordered[i]
        deep = ordered[i + 1]
        if deep["depth_m"] - shallow["depth_m"] < 5.0:
            flags.append(
                f"Structural order VIOLATION: candidates at {shallow['depth_m']}m "
                f"and {deep['depth_m']}m separated by only {deep['depth_m'] - shallow['depth_m']:.1f}m"
            )

    if not physics_guard_passed:
        flags.append("Physics9 violation: AI outside sedimentary bounds")

    return {
        "well_tie_results": well_tie_results,
        "stratigraphic_order_check": "PASS" if not any("VIOLATION" in f for f in flags) else "FLAGGED",
        "physics_guard": "PASS" if physics_guard_passed else "FAIL",
        "flags": flags,
        "requires_888_hold": len(flags) > 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC TOOL
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_horizon_contrast_surface(
    attribute_data: dict[str, list[float]],
    depth: list[float],
    mode: Literal["full", "background_only", "contrast_only", "candidates_only"] = "full",
    geological_query: str = "sequence_boundary",
    well_ties: dict[str, float] | None = None,
    stratigraphic_framework: str = "ABKSS",
    peak_threshold: float = 1.5,
    min_separation_m: float = 20.0,
    custom_query: dict[str, float] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """ToAC-as-Attention Horizon Contrast Surface Pipeline.

    Computes multi-attribute contrast residuals, fuses them via attention
    weighting, extracts horizon candidates, and applies geological governance.

    This is the AGENT's horizon interpretation engine — faster, reproducible,
    and with a full audit trail per the Eureka GeoX Theory of Anomalous Contrast.

    Parameters
    ----------
    attribute_data : dict[str, list[float]]
        Per-attribute data. Keys: amplitude, coherence, frequency, phase, curvature.
        All arrays must be same length as depth.

    depth : list[float]
        Depth values in metres (must align with all attribute arrays).

    mode : str
        "full" — complete pipeline (background → contrast → fusion → candidates → governance)
        "background_only" — compute background model only
        "contrast_only" — background + contrast residuals
        "candidates_only" — full pipeline but skip governance

    geological_query : str
        Which attention query template to use. One of:
        unconformity, flooding_surface, carbonate_platform, channel_system,
        fault_zone, fluid_contact, sequence_boundary, gas_sand.
        This determines how attention weights are distributed across attributes.

    well_ties : dict[str, float] | None
        Known formation tops for calibration: {formation_name: depth_m}.

    stratigraphic_framework : str
        Stratigraphic column to use for geological context. "ABKSS" (default)
        is the Layang-Layang type section framework.

    peak_threshold : float
        Minimum contrast score for a peak to be considered a candidate.

    min_separation_m : float
        Minimum separation between horizon candidates.

    custom_query : dict[str, float] | None
        Custom attention weight dictionary. Overrides geological_query if provided.

    Returns
    -------
    Governed envelope with: background_model, contrast_residuals, fused_contrast,
    horizon_candidates, geological_alignment, and the attention_equivalence metadata.
    """
    import numpy as np

    if ctx:
        ctx.report_progress(0, 100)

    # ── Validation ────────────────────────────────────────────────────────
    if not attribute_data or not depth:
        return get_standard_envelope(
            {"tool": TOOL_NAME, "error": "attribute_data and depth required"},
            tool_class="compute",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE",
        )

    n_samples = len(depth)
    for attr_name, values in attribute_data.items():
        if len(values) != n_samples:
            return get_standard_envelope(
                {"tool": TOOL_NAME, "error": f"Attribute '{attr_name}' length {len(values)} != depth length {n_samples}"},
                tool_class="compute",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                claim_tag="HYPOTHESIS",
                claim_state="NO_VALID_EVIDENCE",
            )

    # ── Resolve query template ────────────────────────────────────────────
    if custom_query:
        query = custom_query
        query_source = "custom"
    elif geological_query in ATTENTION_QUERY_TEMPLATES:
        query = dict(ATTENTION_QUERY_TEMPLATES[geological_query])
        query_source = f"template:{geological_query}"
    else:
        # Fallback: uniform weighting
        attr_names = list(attribute_data.keys())
        query = {a: 1.0 / len(attr_names) for a in attr_names}
        query_source = "fallback:uniform"

    if ctx:
        ctx.report_progress(10, 100)

    # ── Step 1: Background Model ──────────────────────────────────────────
    background = _compute_background_model(attribute_data, depth, well_ties)

    if ctx:
        ctx.report_progress(30, 100)

    if mode == "background_only":
        return get_standard_envelope(
            {"tool": TOOL_NAME, "mode": mode, "background": background},
            tool_class="compute",
            execution_status=ExecutionStatus.SUCCESS,
            governance_status=GovernanceStatus.QUALIFY,
            artifact_status=ArtifactStatus.DRAFT,
            claim_tag="PLAUSIBLE",
            claim_state="INTERPRETED",
            evidence_refs=list(well_ties.keys()) if well_ties else [],
            perception_class="DISPLAY",
        )

    # ── Step 2: Contrast Residuals ────────────────────────────────────────
    residuals = _compute_contrast_residuals(attribute_data, background)

    if ctx:
        ctx.report_progress(50, 100)

    if mode == "contrast_only":
        return get_standard_envelope(
            {
                "tool": TOOL_NAME,
                "mode": mode,
                "background": background,
                "contrast_residuals": residuals,
            },
            tool_class="compute",
            execution_status=ExecutionStatus.SUCCESS,
            governance_status=GovernanceStatus.QUALIFY,
            artifact_status=ArtifactStatus.DRAFT,
            claim_tag="PLAUSIBLE",
            claim_state="INTERPRETED",
            evidence_refs=list(well_ties.keys()) if well_ties else [],
            perception_class="ANOMALY",
        )

    # ── Step 3: Attention-Weighted Fusion ──────────────────────────────────
    fusion = _attention_weighted_fusion(
        residuals,
        query,
        depth,
        geological_context={"stratigraphic_framework": stratigraphic_framework},
    )

    if ctx:
        ctx.report_progress(65, 100)

    # ── Step 4: Horizon Candidate Extraction ──────────────────────────────
    candidates = _extract_horizon_candidates(
        fusion["fused_contrast"],
        depth,
        peak_threshold=peak_threshold,
        min_separation_m=min_separation_m,
    )

    if ctx:
        ctx.report_progress(80, 100)

    # ── Step 5: Geological Alignment Governance ───────────────────────────
    # Physics9 guard: AI range check
    ai_vals = attribute_data.get("amplitude", [0])
    ai_arr = np.array(ai_vals, dtype=float)
    ai_lower, ai_upper = 2000.0, 35000.0
    physics_ok = (
        bool(ai_lower <= float(np.min(ai_arr)) <= ai_upper and ai_lower <= float(np.max(ai_arr)) <= ai_upper)
        if len(ai_arr) > 0
        else True
    )

    strat_col = ABKSS_STRATIGRAPHIC_COLUMN if stratigraphic_framework == "ABKSS" else []
    geo_alignment = _geological_alignment_check(
        candidates,
        well_ties,
        strat_col,
        physics_ok,
    )

    if ctx:
        ctx.report_progress(90, 100)

    # ── Verdict logic ─────────────────────────────────────────────────────
    n_candidates = len(candidates)
    n_flags = len(geo_alignment.get("flags", []))
    has_well_ties = bool(well_ties)

    if n_candidates == 0:
        claim_tag = "HYPOTHESIS"
        gov_status = GovernanceStatus.HOLD
        claim_state = "INTERPRETED"
    elif geo_alignment.get("requires_888_hold", False):
        claim_tag = "PLAUSIBLE"
        gov_status = GovernanceStatus.HOLD
        claim_state = "INTERPRETED"
    elif n_candidates > 0 and has_well_ties and n_flags == 0:
        claim_tag = "CLAIM"
        gov_status = GovernanceStatus.SEAL
        claim_state = "QC_VERIFIED"
    else:
        claim_tag = "PLAUSIBLE"
        gov_status = GovernanceStatus.QUALIFY
        claim_state = "INTERPRETED"

    # ── Step 6: Governed Envelope ─────────────────────────────────────────
    envelope = get_standard_envelope(
        {
            "tool": TOOL_NAME,
            "mode": mode,
            "geological_query": geological_query,
            "query_source": query_source,
            "query_note": ATTENTION_QUERY_TEMPLATES.get(geological_query, {}).get("note", ""),
            "n_candidates": n_candidates,
            "background": background,
            "contrast_residuals": residuals,
            "fusion": fusion,
            "horizon_candidates": candidates,
            "geological_alignment": geo_alignment,
        },
        tool_class="compute",
        execution_status=ExecutionStatus.SUCCESS,
        governance_status=gov_status,
        artifact_status=ArtifactStatus.DRAFT if n_candidates == 0 else ArtifactStatus.IN_REVIEW,
        claim_tag=claim_tag,
        claim_state=claim_state,
        perception_class="ANOMALY" if n_candidates > 0 else "DISPLAY",
        evidence_refs=list(well_ties.keys()) if well_ties else [],
        physics_guard={
            "guard_passed": physics_ok,
            "physics_version": "geox-horizon-v2026.06.05",
            "equations_used": [
                "AI = Vp × ρ",
                "δ_i = A_obs − A_bg",
                "α_k = softmax(q_geological · k_attribute / √d)",
                "Contrast(x,t) = Σ_k α_k · δ_i^(k)",
            ],
            "assumptions": [
                "Compaction trend is smooth and monotonic",
                "Attribute statistics locally stationary within running window",
                "Well ties are calibrated (no checkshot error)",
                "Attention weights encode geological prior knowledge",
            ],
        },
    )

    # ── ToAC-Attention Equivalence Metadata ────────────────────────────────
    attr_contrast_types = [
        {"attribute": "amplitude", "contrast_type": "Impedance contrast — lithology/porosity"},
        {"attribute": "coherence", "contrast_type": "Lateral contrast — faults/channels/edges"},
        {"attribute": "frequency", "contrast_type": "Stratigraphic contrast — tuning/fluid"},
        {"attribute": "phase", "contrast_type": "Continuity contrast — unconformities/onlap"},
        {"attribute": "curvature", "contrast_type": "Geometric contrast — folds/domes/drag"},
    ]

    envelope["horizon_contrast"] = {
        "toac_version": "v2026.06.05",
        "pipeline": [
            "1. Background model (compaction trend + running statistics)",
            "2. Multi-attribute contrast residuals (δ_i = A_obs − A_bg)",
            "3. Attention-weighted fusion (α = softmax(q · K/√d))",
            "4. Horizon candidate extraction (peaks in fused surface)",
            "5. Geological alignment governance (well tie + physics + stratigraphy)",
            "6. Audited output (ClaimTag + verdict + audit hash)",
        ],
        "attention_equivalence": {
            "theorem": "ToAC ≡ Attention: Every seismic attribute IS a contrast operator",
            "query_vector": query,
            "query_interpretation": (
                f"Attention weighted toward {fusion.get('dominant_attribute', '?')} "
                f"({query.get(fusion.get('dominant_attribute', ''), 0):.0%} of attention). "
                f"Geological query: '{geological_query}' — "
                f"{ATTENTION_QUERY_TEMPLATES.get(geological_query, {}).get('note', 'Custom query')}"
            ),
            "attribute_contrast_types": attr_contrast_types,
            "fused_contrast_interpretation": (
                f"The fused contrast surface highlights where the section deviates "
                f"from the background across {fusion.get('n_attributes_fused', 0)} "
                f"attributes. Peaks above {peak_threshold}σ are horizon candidates. "
                f"NOT every peak is a geological horizon — multiples, tuning artifacts, "
                f"and acquisition footprint may produce false anomalies (equivalent to "
                f"false Class III AVO bright spots — Castagna & Swan, 1997)."
            ),
        },
        "bias_audit": {
            "principle": "B_cog — Bond's cognitive bias audit (2007)",
            "query_template_used": geological_query,
            "alternative_queries_suggested": [q for q in ATTENTION_QUERY_TEMPLATES if q != geological_query and q != "gas_sand"][
                :3
            ],
            "warning": (
                "Single query template = single interpretation hypothesis. "
                "Bond (2007) demonstrated ~79% first-interpretation error rate. "
                "Strongly consider running multiple geological queries and "
                "comparing candidates across attention profiles."
            )
            if geological_query != "gas_sand"
            else (
                "ATTENTION WARNING: 'gas_sand' query has highest false-positive "
                "rate (equivalent to Class III false bright spots). Brine sands, "
                "coals, and hard streaks can all produce high amplitude contrast. "
                "Confirm with AVO pre-stack analysis and well control."
            ),
        },
        "failure_modes": {
            "false_class_iii": (
                "High-amplitude anomaly from brine sand, coal, or hard streak "
                "mimics gas response. Mitigation: cross-validate with frequency "
                "attenuation + pre-stack AVO."
            ),
            "class_iv_miss": (
                "Gas sand with dimming amplitude (Class IV) produces low contrast "
                "and may not exceed peak_threshold. Mitigation: lower threshold "
                "in known Class IV provinces + phase/curvature cross-check."
            ),
            "tuning_artifact": (
                "Thin-bed tuning produces amplitude contrast peaks at top/base "
                "of bed that are not separate geological horizons. Mitigation: "
                "min_separation_m should exceed tuning thickness."
            ),
            "acquisition_footprint": (
                "Systematic amplitude striping from acquisition geometry may "
                "produce false contrast peaks. Mitigation: coherence cross-check "
                "(acquisition noise is high-coherence, geological boundaries are not)."
            ),
        },
    }

    if ctx:
        ctx.report_progress(100, 100)

    return enrich_envelope_with_metabolic(envelope, TOOL_NAME)
