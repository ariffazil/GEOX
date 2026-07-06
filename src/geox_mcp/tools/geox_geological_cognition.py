#!/usr/bin/env python3
"""
GEOX Geological Cognition Module
===================================
v1.0 — Forged 2026-07-06 under F13 SOVEREIGN.

Encodes the geologist's cognitive loop into GEOX:

    OBSERVE → HYPOTHESIZE → TEST → REVISE → MAP → INTEGRATE

Unlike geox_physical_reality.py (which detects pixel patterns),
this module REASONS about what those patterns mean geologically.

It separates:
    - Signal from illusion
    - Real structure from imaging artifact
    - Confirmed observation from testable hypothesis

The cognitive hierarchy:
    1. Basin-scale architecture (what kind of system?)
    2. Structural interpretation (how was it deformed?)
    3. Stratigraphic packages (how did sediment move through time?)
    4. Reservoir system (does the petroleum system work?)

Epistemic output per feature:
    - Ranked hypotheses (not single label)
    - Prior probability given basin context
    - Required tests to discriminate
    - Imaging artifact screening result

Hard law: The best interpreter knows when the image is lying.

DITEMPA BUKAN DIBERI.
"""

import numpy as np
from scipy import ndimage
from scipy.signal import hilbert
from scipy.stats import variation
from typing import Optional
import json


# ═══════════════════════════════════════════════════════════════════════════
# REFLECTOR PACKAGE CLASSIFIER
# Reads geometry across the full section — basin scale first
# ═══════════════════════════════════════════════════════════════════════════

def classify_reflector_packages(agc: np.ndarray, cp: np.ndarray,
                                 pc: np.ndarray, n_zones: int = 5) -> list:
    """Divide section into horizontal zones, classify each by reflector geometry.

    A geologist reads top-down: basin architecture first, then structural,
    then stratigraphic. This function replicates that first cognitive pass.

    Geometry classes (after Mitchum et al. 1977 seismic stratigraphy):
        PARALLEL       — continuous, even amplitude, flat or gently dipping
                         → laterally persistent bedding, marine, shelf
        SUBPARALLEL    — mostly continuous, minor irregularity
                         → coastal plain, proximal marine
        DIVERGENT      — reflectors thicken in one direction (wedge shape)
                         → growth fault, differential subsidence, margin
        SIGMOIDAL      — S-shaped, progradational clinoforms
                         → delta, shelf-margin, carbonate ramp
        OBLIQUE        — steep, no upper bounding surface
                         → high-energy progradation
        CHAOTIC        — discontinuous, high amplitude variation
                         → mass transport, fault damage, volcanics, basement
        TRANSPARENT    — low amplitude, uniform
                         → massive sandstone, salt, evaporite, shale
        HUMMOCKY       — irregular mounds
                         → carbonate build-up, reef, mud volcano, igneous
    """
    hc, wc = agc.shape
    zone_h = hc // n_zones
    packages = []

    for i in range(n_zones):
        r0 = i * zone_h
        r1 = min(hc, (i + 1) * zone_h)
        zone_agc = agc[r0:r1, :]
        zone_cp  = cp[r0:r1, :]
        zone_pc  = pc[r0:r1, :]

        # ── Continuity metrics ──────────────────────────────────────────
        # Mean phase coherence (how continuous are reflectors laterally?)
        mean_coherence = float(np.mean(zone_pc))

        # Row-to-row amplitude variation (high = chaotic, low = parallel)
        row_means = np.mean(np.abs(zone_agc), axis=1)
        row_cv = float(variation(row_means + 1e-10))  # coefficient of variation

        # Lateral gradient (measures dip change across zone)
        col_means = np.mean(np.abs(zone_agc), axis=0)
        col_gradient = float(np.polyfit(np.arange(wc), col_means, 1)[0])
        col_gradient_norm = abs(col_gradient) / (np.mean(np.abs(col_means)) + 1e-10)

        # Amplitude range (transparent zones have low variance)
        amp_std = float(np.std(zone_agc))
        amp_mean = float(np.mean(np.abs(zone_agc)))

        # ── Geometry classification ─────────────────────────────────────
        if mean_coherence < 0.25 and row_cv > 0.3:
            geometry = "CHAOTIC"
            geological_hint = [
                "Basement / pre-rift metamorphic or igneous",
                "Mass transport complex (MTC/MTD)",
                "Fault damage zone",
                "Salt or mud diapir",
                "Volcanic intrusive / extrusive",
                "Poor imaging zone (gas cloud, shallow gas, multiples)",
            ]
            scale = "BASIN"

        elif amp_std < 0.10 * amp_mean or amp_std < 0.05:
            geometry = "TRANSPARENT"
            geological_hint = [
                "Massive clean sandstone (no internal reflectors)",
                "Evaporite / salt (acoustic homogeneity)",
                "Thick shale package",
                "Carbonate platform interior",
                "Gas chimney wipeout (IMAGING ARTIFACT candidate)",
            ]
            scale = "STRATIGRAPHIC"

        elif col_gradient_norm > 0.05:
            # Significant lateral amplitude change → wedge or divergence
            if col_gradient > 0:
                geometry = "DIVERGENT_RIGHT"
            else:
                geometry = "DIVERGENT_LEFT"
            geological_hint = [
                "Growth fault: strata thicken into fault (syn-depositional)",
                "Half-graben fill: differential subsidence",
                "Margin wedge: basin-margin clinoforms",
                "Compaction differential",
            ]
            scale = "STRUCTURAL"

        elif mean_coherence > 0.55 and row_cv < 0.15:
            geometry = "PARALLEL"
            geological_hint = [
                "Post-rift thermal sag: laterally persistent marine bedding",
                "Shelf platform: tabular carbonate or marine shale",
                "Passive margin drift sequence",
                "Regional transgressive shale seal",
            ]
            scale = "BASIN"

        elif mean_coherence > 0.35:
            geometry = "SUBPARALLEL"
            geological_hint = [
                "Coastal plain to shallow marine transition",
                "Prodelta / distal fan sequence",
                "Channel-overbank alternation",
                "Compaction-modulated continental deposits",
            ]
            scale = "STRATIGRAPHIC"

        else:
            geometry = "IRREGULAR"
            geological_hint = [
                "Mixed reflector package: interbedded facies",
                "Deformed stratigraphy (folded, faulted at this scale)",
                "Onlap/downlap termination zone",
            ]
            scale = "STRATIGRAPHIC"

        packages.append({
            "zone_id": f"Z{i + 1}",
            "row_range": [int(r0), int(r1)],
            "depth_proxy": f"shallow-{'upper' if i < 2 else 'mid' if i < 4 else 'deep'}",
            "geometry": geometry,
            "scale_read": scale,
            "metrics": {
                "mean_coherence": round(mean_coherence, 3),
                "row_cv": round(row_cv, 3),
                "col_gradient_norm": round(col_gradient_norm, 4),
                "amp_std": round(amp_std, 4),
            },
            "geological_hypotheses": geological_hint,
            "epistemic": "DER_IMAGE_GEOMETRY",
            "note": "Geometry from pixel pattern analysis. Requires stratigraphic context + well tie to confirm.",
        })

    return packages


# ═══════════════════════════════════════════════════════════════════════════
# TERMINATION DETECTOR
# Where horizons terminate = most information-rich point in seismic
# ═══════════════════════════════════════════════════════════════════════════

def detect_terminations(horizons: list, agc: np.ndarray,
                        packages: list) -> list:
    """Detect reflector termination patterns at horizon endpoints.

    Termination types (after Vail et al. 1977):
        ONLAP      — reflector terminates upward against an inclined surface
                     → transgression, base-of-slope fill, lacustrine onlap
        DOWNLAP    — reflector terminates downward against lower surface
                     → progradation, delta front, turbidite fan
        TOPLAP     — reflector terminates at top, no upper surface
                     → sediment limit at highstand, bypass, erosional beveling
        TRUNCATION — reflector cut by overlying surface
                     → erosion by unconformity, fault cutoff, canyon erosion
        CONCORDANCE — reflector parallel, no termination
                     → continuous deposition, no time break

    Terminations define sequence boundaries — the most important
    chronostratigraphic surfaces in basin analysis.
    """
    hc, wc = agc.shape
    results = []

    for h in horizons:
        pts = np.array(h["pts"])  # [[col, row], ...]
        if len(pts) < 10:
            continue

        rows = pts[:, 1].astype(float)
        cols = pts[:, 0].astype(float)

        # ── Left termination (proximal / updip end) ──────────────────
        left_rows = rows[:max(5, len(rows) // 8)]
        left_trend = float(np.polyfit(np.arange(len(left_rows)), left_rows, 1)[0])

        # ── Right termination (distal / downdip end) ─────────────────
        right_rows = rows[-max(5, len(rows) // 8):]
        right_trend = float(np.polyfit(np.arange(len(right_rows)), right_rows, 1)[0])

        # ── Overall dip of horizon ────────────────────────────────────
        overall_dip = float(np.polyfit(cols, rows, 1)[0])

        # ── Amplitude at termination ──────────────────────────────────
        left_amp  = float(np.mean(np.abs(agc[int(rows[0]):int(rows[0])+3,  :wc//10])))
        right_amp = float(np.mean(np.abs(agc[int(rows[-1]):int(rows[-1])+3, -wc//10:])))

        # ── Classify terminations ─────────────────────────────────────
        def classify_end(trend, end_amp, side):
            """Classify one termination end."""
            if abs(trend) < 0.05:
                return {
                    "type": "CONCORDANCE",
                    "hypotheses": [
                        "Continuous parallel deposition — no time break",
                        "Section edge artifact (image boundary, not geology)",
                    ],
                    "sequence_significance": "LOW — no break implied",
                }
            elif trend > 0.15:  # dipping upward toward termination
                return {
                    "type": "ONLAP",
                    "hypotheses": [
                        "Transgressive systems tract: sea level rise, sediment lapping onto slope",
                        "Lacustrine onlap onto basin margin (syn-rift lake)",
                        "Compaction drape onto underlying structure",
                        f"Imaging artefact: migration smear at {side} edge",
                    ],
                    "sequence_significance": "HIGH — possible sequence boundary or MFS",
                }
            elif trend < -0.15:  # dipping downward toward termination
                return {
                    "type": "DOWNLAP",
                    "hypotheses": [
                        "Progradational systems tract: delta/fan building outward",
                        "Clinoform rollover: shelf-margin progradation",
                        "Turbidite lobe termination downdip",
                        f"Imaging artefact: differential NMO stretch at {side} edge",
                    ],
                    "sequence_significance": "HIGH — marks maximum flooding surface below",
                }
            else:
                return {
                    "type": "TRUNCATION_OR_TOPLAP",
                    "hypotheses": [
                        "Erosional truncation: unconformity surface cutting horizon",
                        "Toplap: sediment limit at depositional highstand",
                        "Fault cutoff at {side} margin",
                        "Acquisition/processing edge effect",
                    ],
                    "sequence_significance": "HIGH — possible unconformity surface",
                }

        left_term  = classify_end(left_trend,  left_amp,  "left/proximal")
        right_term = classify_end(right_trend, right_amp, "right/distal")

        # Which zone is this horizon in?
        zone_id = None
        for pkg in packages:
            if pkg["row_range"][0] <= int(rows[len(rows)//2]) < pkg["row_range"][1]:
                zone_id = pkg["zone_id"]
                break

        results.append({
            "horizon_id": h["id"],
            "overall_dip_px_per_px": round(overall_dip, 4),
            "zone": zone_id,
            "left_termination": left_term,
            "right_termination": right_term,
            "sequence_significance": (
                "HIGH" if "HIGH" in left_term["sequence_significance"]
                       or "HIGH" in right_term["sequence_significance"]
                else "LOW"
            ),
            "epistemic": "INT_SEISMIC_TERMINATION",
            "required_tests": [
                "Adjacent line correlation (does termination persist?)",
                "Well tie (does termination coincide with age break?)",
                "Attribute map at termination level (amplitude, coherence slice)",
                "Check termination is not section-edge processing artefact",
            ],
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════
# IMAGING ARTIFACT SCREEN
# The geologist's first question: "Is the image lying?"
# ═══════════════════════════════════════════════════════════════════════════

def screen_imaging_artifacts(agc: np.ndarray, cp: np.ndarray,
                              fp: np.ndarray, faults: list,
                              horizons: list) -> dict:
    """Screen for common seismic imaging artifacts.

    These are features that look geological but are acoustic/processing illusions:

    1. GAS WIPEOUT / CHIMNEY
       Cause: Gas-saturated sediment absorbs and scatters energy
       Pattern: Zone of chaotic/blank reflectors below a strong reflector,
                often with bright spot above
       Risk: Misinterpreted as fault damage or basement

    2. VELOCITY PULL-UP / SAG
       Cause: High-velocity body (carbonate, salt) focuses energy → apparent anticline
              Low-velocity body (gas, shallow channel) defocuses → apparent syncline
       Pattern: Structural feature that mirrors the shape of an overlying body
       Risk: Drilled as trap, found to be velocity artifact (costly!)

    3. SEISMIC MULTIPLES
       Cause: Energy bouncing multiple times between strong reflectors
       Pattern: Repetition of strong reflectors at regular TWT intervals
                (water-bottom multiple, peg-leg multiple)
       Risk: Misinterpreted as deep real geology

    4. MIGRATION SMILES / OPERATOR TRUNCATION
       Cause: Incomplete migration removes energy from wrong positions
       Pattern: Curved "smile" artefacts below fault tips or at section edges
       Risk: Misinterpreted as real folds or structures

    5. ACQUISITION FOOTPRINT
       Cause: Regular survey geometry imprints on data
       Pattern: Linear amplitude striping, usually in the inline or crossline direction
       Risk: Misinterpreted as subtle faults or stratigraphy

    6. NMO STRETCH
       Cause: Normal moveout correction stretches far-offset traces
       Pattern: Low-frequency, low-coherence shallow zone at far offsets
       Risk: Misinterpreted as unconformity or reflector absence

    Returns: Dict of flagged artifacts with locations and probability.
    """
    hc, wc = agc.shape
    artifacts = {}

    # ── 1. Gas wipeout / chimney detection ──────────────────────────────
    # Look for zones of very low coherence below a bright (high amplitude) row
    row_amp = np.mean(np.abs(agc), axis=1)
    row_amp_n = row_amp / (row_amp.max() + 1e-10)

    bright_rows = np.where(row_amp_n > 0.7)[0]
    wipeout_candidates = []

    for br in bright_rows:
        # Check coherence below bright row
        if br + 20 < hc:
            below_coh = np.mean(cp[br + 5:br + 25, :])
            if below_coh < 0.2:
                wipeout_candidates.append({
                    "bright_row": int(br),
                    "wipeout_rows": [int(br + 5), int(min(hc, br + 50))],
                    "coherence_below": round(float(below_coh), 3),
                    "artifact_type": "GAS_WIPEOUT_CHIMNEY",
                    "probability": "MODERATE",
                    "geological_alternative": [
                        "Real gas charge below bright spot (direct hydrocarbon indicator)",
                        "Fault damage zone (not gas)",
                        "Chaotic mass transport below unconformity",
                    ],
                    "required_test": "AVO analysis + rock physics forward model",
                })

    if wipeout_candidates:
        artifacts["gas_wipeout_chimney"] = {
            "n_candidates": len(wipeout_candidates),
            "candidates": wipeout_candidates[:5],
            "epistemic": "INT_IMAGING_ARTIFACT",
        }

    # ── 2. Velocity pull-up / sag ────────────────────────────────────────
    # Horizons that arch upward (pull-up) or downward (sag) beneath a body
    pullup_candidates = []
    for h in horizons:
        pts = np.array(h["pts"])
        rows = pts[:, 1].astype(float)
        mid_col = len(rows) // 2
        # Check if horizon is concave-up (pull-up) or concave-down (sag)
        # Fit a parabola — high curvature = velocity effect candidate
        if len(rows) > 20:
            x = np.arange(len(rows))
            coeffs = np.polyfit(x, rows, 2)
            curvature = float(abs(coeffs[0]))  # coefficient of x^2
            if curvature > 0.001:
                shape = "PULLUP" if coeffs[0] < 0 else "SAG"
                pullup_candidates.append({
                    "horizon_id": h["id"],
                    "parabolic_curvature": round(curvature, 6),
                    "shape": shape,
                    "artifact_type": f"VELOCITY_{shape}",
                    "probability": "LOW_TO_MODERATE",
                    "geological_alternative": [
                        f"Real structural {'anticline' if shape == 'PULLUP' else 'syncline'} (not velocity effect)",
                        f"Compaction drape over underlying {'high' if shape == 'PULLUP' else 'low'}",
                    ],
                    "required_test": "Depth conversion with interval velocity model",
                })

    if pullup_candidates:
        artifacts["velocity_pullup_sag"] = {
            "n_candidates": len(pullup_candidates),
            "candidates": pullup_candidates,
            "epistemic": "INT_IMAGING_ARTIFACT",
            "note": "All structural interpretations require depth conversion. Time domain structures ≠ depth domain structures.",
        }

    # ── 3. Multiple reflection detection ─────────────────────────────────
    # Look for near-periodic repetition of amplitude patterns
    row_amp_smooth = ndimage.gaussian_filter1d(row_amp_n, sigma=3)
    peaks = []
    for r in range(1, hc - 1):
        if row_amp_smooth[r] > row_amp_smooth[r-1] and row_amp_smooth[r] > row_amp_smooth[r+1]:
            if row_amp_smooth[r] > 0.5:
                peaks.append(r)

    multiple_candidates = []
    for i in range(len(peaks) - 1):
        for j in range(i + 1, len(peaks)):
            spacing = peaks[j] - peaks[i]
            # Multiples repeat at regular intervals — check if spacing divides evenly
            if spacing > 30:
                ratio = spacing / (peaks[i] + 1e-10)
                if abs(ratio - round(ratio)) < 0.1:
                    multiple_candidates.append({
                        "primary_row": int(peaks[i]),
                        "repeat_row": int(peaks[j]),
                        "spacing_px": int(spacing),
                        "artifact_type": "POSSIBLE_MULTIPLE",
                        "probability": "LOW",
                        "geological_alternative": [
                            "Two distinct real geological reflectors at this spacing",
                            "Interbedded hard layers (tuning effect)",
                        ],
                        "required_test": "Multiple prediction + subtraction processing, or Radon demultiple",
                    })
                    break
        if multiple_candidates:
            break

    if multiple_candidates:
        artifacts["multiples"] = {
            "n_candidates": len(multiple_candidates),
            "candidates": multiple_candidates[:3],
            "epistemic": "INT_IMAGING_ARTIFACT",
        }

    # ── 4. Acquisition footprint (regular striping) ──────────────────────
    # FFT on amplitude to check for regular lateral periodicities
    col_var = np.var(agc, axis=0)
    fft_col = np.abs(np.fft.rfft(col_var))
    dominant_freq = int(np.argmax(fft_col[1:]) + 1)  # exclude DC
    footprint_period = wc / dominant_freq if dominant_freq > 0 else None
    footprint_flag = (footprint_period is not None
                      and 10 < footprint_period < wc * 0.5
                      and fft_col[dominant_freq] > 3 * np.median(fft_col[1:]))

    if footprint_flag:
        artifacts["acquisition_footprint"] = {
            "dominant_period_px": round(float(footprint_period), 1),
            "amplitude": round(float(fft_col[dominant_freq]), 3),
            "artifact_type": "ACQUISITION_FOOTPRINT",
            "probability": "LOW_TO_MODERATE",
            "geological_alternative": [
                "Real stratigraphic periodicity (cyclothems, Milankovitch)",
                "Structural periodicity (fault spacing)",
            ],
            "required_test": "Compare with nominal survey line spacing; check perpendicular direction",
            "epistemic": "INT_IMAGING_ARTIFACT",
        }

    # ── Summary verdict ──────────────────────────────────────────────────
    n_flags = len(artifacts)
    if n_flags == 0:
        screen_verdict = "CLEAN — no major artifact indicators detected"
    elif n_flags == 1:
        screen_verdict = "CAUTION — 1 artifact type flagged, test before interpreting"
    else:
        screen_verdict = f"WARNING — {n_flags} artifact types flagged, interpretation may be compromised"

    return {
        "screen_verdict": screen_verdict,
        "n_artifact_types_flagged": n_flags,
        "artifacts": artifacts,
        "always_true": [
            "Section displayed in TWO-WAY TIME, not true depth",
            "All structures require depth conversion before drilling",
            "Amplitude is NOT direct lithology or fluid without AVO + rock physics",
            "Seismic resolution is bandwidth-limited (tuning thickness ≈ λ/4)",
            "Near-section edges may have edge-of-migration operator artefacts",
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════
# GEOLOGICAL HYPOTHESIS RANKER
# Per feature: ranked causes, basin prior, required tests
# ═══════════════════════════════════════════════════════════════════════════

# Malay Basin prior — what is geologically likely in this basin
# Based on: syn-rift → thermal sag → compressional inversion
MALAY_BASIN_PRIOR = {
    "fault_types": {
        "Normal (syn-rift, NW-trending)": 0.40,
        "Inverted (reactivated, transpressional)": 0.30,
        "Strike-slip (axial fault zone, dextral Late Miocene)": 0.20,
        "Reverse / thrust": 0.07,
        "Processing artifact": 0.03,
    },
    "horizon_types": {
        "Syn-rift lacustrine / fluvial": 0.20,
        "Post-rift thermal sag marine": 0.35,
        "Coastal plain / deltaic (Groups I-J)": 0.25,
        "Inversion-related unconformity": 0.10,
        "Multiple reflection": 0.05,
        "Processing artifact": 0.05,
    },
    "anomaly_types": {
        "Stratigraphic trap (channel/pinchout)": 0.35,
        "Structural trap (anticline/inversion)": 0.40,
        "Combination trap": 0.15,
        "Processing/velocity artifact": 0.10,
    },
}

GENERIC_BASIN_PRIOR = {
    "fault_types": {
        "Normal fault": 0.35,
        "Reverse / thrust fault": 0.20,
        "Strike-slip fault": 0.15,
        "Lithological contrast (not fault)": 0.15,
        "Processing artifact": 0.10,
        "Acquisition footprint": 0.05,
    },
    "horizon_types": {
        "Continuous geological reflector": 0.50,
        "Multiple reflection": 0.15,
        "Processing artifact": 0.15,
        "Noise train": 0.10,
        "Migration artefact": 0.10,
    },
}


def rank_hypotheses(faults: list, horizons: list, packages: list,
                    terminations: list, artifacts: dict,
                    basin_context: str = "malay_basin") -> dict:
    """Rank geological hypotheses per feature.

    This is the core of geologist-grade interpretation:
    Not "this IS a fault" but "this COULD BE a fault (0.40),
    or a lithological contrast (0.15), or an artifact (0.10)..."

    For each fault and horizon, output:
        - Ranked hypotheses with prior probability
        - Basin-specific adjustment
        - Tests required to discriminate
        - Confidence cap (F7 HUMILITY — never exceed 0.90)
    """
    prior = MALAY_BASIN_PRIOR if basin_context == "malay_basin" else GENERIC_BASIN_PRIOR
    results = {"basin_context": basin_context, "faults": [], "horizons": [], "summary": {}}

    # ── Fault hypothesis ranking ──────────────────────────────────────────
    for f in faults:
        dip = f.get("dip_est", "near-vertical")
        conf_proxy = f.get("conf_proxy", 0.5)
        row_span = f.get("row_span", 50)

        # Adjust prior by dip
        fault_prior = dict(prior["fault_types"])
        if dip == "near-vertical":
            # Near-vertical → more likely strike-slip or normal
            for k in fault_prior:
                if "strike-slip" in k.lower() or "normal" in k.lower():
                    fault_prior[k] *= 1.3
                elif "reverse" in k.lower() or "thrust" in k.lower():
                    fault_prior[k] *= 0.6

        elif dip == "low-angle":
            # Low-angle → more likely thrust or detachment
            for k in fault_prior:
                if "reverse" in k.lower() or "thrust" in k.lower():
                    fault_prior[k] *= 1.8
                elif "normal" in k.lower():
                    fault_prior[k] *= 0.7

        # Normalize to sum to 1
        total = sum(fault_prior.values())
        fault_prior = {k: round(v / total, 3) for k, v in fault_prior.items()}

        # Sort descending
        ranked = sorted(fault_prior.items(), key=lambda x: x[1], reverse=True)

        results["faults"].append({
            "fault_id": f["id"],
            "dip_class": dip,
            "conf_proxy": conf_proxy,
            "row_span_px": row_span,
            "hypotheses_ranked": [
                {"rank": i + 1, "hypothesis": h, "prior_prob": p,
                 "note": f"{'Highest prior in {}'.format(basin_context) if i == 0 else ''}"}
                for i, (h, p) in enumerate(ranked)
            ],
            "discrimination_tests": [
                "Check vertical displacement continuity with depth (does throw change?)",
                "Look for drag folds or growth strata adjacent to fault",
                "Correlate fault on adjacent seismic lines (is it real 3D feature?)",
                "Test dip direction (same as regional stress field?)",
                "Well calibration: look for fault in log character / missing section",
            ],
            "confidence_cap": min(0.90, conf_proxy * 0.85),
            "epistemic": "INT_SEISMIC_FAULT_RANKED",
        })

    # ── Horizon hypothesis ranking ────────────────────────────────────────
    horiz_prior = dict(prior["horizon_types"])

    for h in horizons:
        continuity = h.get("continuity", 0.5)
        seed_row = h.get("seed_row", 0)
        amp_proxy = h.get("mean_amplitude_proxy", 0.3)

        # Check if this horizon is flagged as artifact
        artifact_flags = []
        if "multiples" in artifacts.get("artifacts", {}):
            for mc in artifacts["artifacts"]["multiples"].get("candidates", []):
                if abs(seed_row - mc.get("primary_row", -999)) < 20:
                    artifact_flags.append("POSSIBLE_MULTIPLE — check TWT spacing")

        # Adjust prior by continuity
        adjusted = dict(horiz_prior)
        if continuity > 0.70:
            for k in adjusted:
                if "geological" in k.lower() or "marine" in k.lower() or "post-rift" in k.lower():
                    adjusted[k] *= 1.4
                elif "multiple" in k.lower() or "artifact" in k.lower():
                    adjusted[k] *= 0.6
        elif continuity < 0.30:
            for k in adjusted:
                if "multiple" in k.lower() or "artifact" in k.lower() or "noise" in k.lower():
                    adjusted[k] *= 1.5

        total = sum(adjusted.values())
        adjusted = {k: round(v / total, 3) for k, v in adjusted.items()}
        ranked = sorted(adjusted.items(), key=lambda x: x[1], reverse=True)

        # Find associated termination
        term = next((t for t in terminations if t["horizon_id"] == h["id"]), None)

        results["horizons"].append({
            "horizon_id": h["id"],
            "continuity": continuity,
            "seed_row": seed_row,
            "amplitude_proxy": amp_proxy,
            "artifact_flags": artifact_flags,
            "hypotheses_ranked": [
                {"rank": i + 1, "hypothesis": hy, "prior_prob": p}
                for i, (hy, p) in enumerate(ranked)
            ],
            "termination_context": {
                "left": term["left_termination"]["type"] if term else "NOT_ANALYSED",
                "right": term["right_termination"]["type"] if term else "NOT_ANALYSED",
                "sequence_significance": term["sequence_significance"] if term else "UNKNOWN",
            },
            "discrimination_tests": [
                "Synthetic seismogram well tie (bruges wavelet convolution)",
                "Check if horizon repeat interval matches water-bottom multiple TWT",
                "Correlate across multiple seismic lines",
                "Extract amplitude map at this level for geological pattern",
                "Test if horizon tracks known stratigraphic marker from wells",
            ],
            "confidence_cap": min(0.90, continuity * 0.85),
            "epistemic": "INT_SEISMIC_HORIZON_RANKED",
        })

    # ── Summary ───────────────────────────────────────────────────────────
    results["summary"] = {
        "n_faults_ranked": len(results["faults"]),
        "n_horizons_ranked": len(results["horizons"]),
        "top_fault_hypothesis": results["faults"][0]["hypotheses_ranked"][0]["hypothesis"] if results["faults"] else "none",
        "top_horizon_hypothesis": results["horizons"][0]["hypotheses_ranked"][0]["hypothesis"] if results["horizons"] else "none",
        "basin_context_applied": basin_context,
        "interpretation_law": [
            "Every feature has multiple causes — ranked, not single-labelled",
            "High confidence requires: well tie + multi-line correlation + attribute test",
            "F7 HUMILITY: confidence cap 0.90 — always carry non-zero doubt",
            "The best interpreter knows when the image is lying",
        ],
    }

    return results


# ═══════════════════════════════════════════════════════════════════════════
# GEOLOGIST'S REPORT — structured output a geologist can read
# ═══════════════════════════════════════════════════════════════════════════

def build_geologist_report(packages: list, terminations: list,
                            artifacts: dict, hypotheses: dict,
                            prov_short: str) -> str:
    """Build a structured plain-text report in the style of a geologist's
    interpretation memo. This is what GEOX presents to the human geologist.
    """
    lines = []
    lines.append("=" * 72)
    lines.append("  GEOX GEOLOGICAL INTERPRETATION REPORT")
    lines.append(f"  {prov_short}")
    lines.append("=" * 72)

    lines.append("\n§1 BASIN-SCALE ARCHITECTURE (first cognitive pass)")
    lines.append("-" * 48)
    for pkg in packages:
        lines.append(
            f"  {pkg['zone_id']} [{pkg['row_range'][0]:>3}–{pkg['row_range'][1]:>3}px]  "
            f"{pkg['geometry']:<22} coh={pkg['metrics']['mean_coherence']:.2f}"
        )
        lines.append(f"      → Top hypothesis: {pkg['geological_hypotheses'][0]}")
        if len(pkg["geological_hypotheses"]) > 1:
            lines.append(f"      → Alt:           {pkg['geological_hypotheses'][1]}")

    lines.append("\n§2 IMAGING ARTIFACT SCREEN")
    lines.append("-" * 48)
    lines.append(f"  Verdict: {artifacts['screen_verdict']}")
    for at_name, at_data in artifacts.get("artifacts", {}).items():
        lines.append(f"  ⚠  {at_name.upper()}: {at_data.get('n_candidates', 1)} candidate(s)")
    for always in artifacts["always_true"][:3]:
        lines.append(f"  !  {always}")

    lines.append("\n§3 FAULT INTERPRETATION (ranked hypotheses)")
    lines.append("-" * 48)
    for fh in hypotheses.get("faults", []):
        lines.append(
            f"  {fh['fault_id']}  dip={fh['dip_class']:<14}  "
            f"conf_cap={fh['confidence_cap']:.0%}"
        )
        for rh in fh["hypotheses_ranked"][:3]:
            lines.append(f"      #{rh['rank']} {rh['hypothesis']:<45}  P={rh['prior_prob']:.2f}")

    lines.append("\n§4 HORIZON INTERPRETATION (ranked hypotheses)")
    lines.append("-" * 48)
    for hh in hypotheses.get("horizons", []):
        term_l = hh["termination_context"]["left"]
        term_r = hh["termination_context"]["right"]
        seq_sig = hh["termination_context"]["sequence_significance"]
        lines.append(
            f"  {hh['horizon_id']}  cont={hh['continuity']:.0%}  "
            f"L-term={term_l}  R-term={term_r}  seq={seq_sig}"
        )
        for rh in hh["hypotheses_ranked"][:2]:
            lines.append(f"      #{rh['rank']} {rh['hypothesis']:<45}  P={rh['prior_prob']:.2f}")
        if hh["artifact_flags"]:
            for af in hh["artifact_flags"]:
                lines.append(f"      ⚠ ARTIFACT FLAG: {af}")

    lines.append("\n§5 TERMINATION ANALYSIS (sequence stratigraphy)")
    lines.append("-" * 48)
    for t in terminations:
        seq = t["sequence_significance"]
        marker = "▲" if seq == "HIGH" else "·"
        lines.append(
            f"  {marker} {t['horizon_id']}  "
            f"L:{t['left_termination']['type']:<20} "
            f"R:{t['right_termination']['type']:<20} "
            f"seq_sig={seq}"
        )

    lines.append("\n§6 WHAT THE SEISMIC CANNOT TELL YOU (HOLD)")
    lines.append("-" * 48)
    holds = [
        "True structural depth (requires velocity model + depth conversion)",
        "Lithology (requires well calibration + rock physics)",
        "Fluid type (requires AVO analysis + Zoeppritz/Shuey)",
        "Formation age (requires well tie + biostratigraphy)",
        "Reserves / commerciality (requires volumetrics + economic model)",
        "Fault seal capacity (requires fault rock analysis)",
    ]
    for h in holds:
        lines.append(f"  HOLD: {h}")

    lines.append("\n§7 NEXT REQUIRED STEPS")
    lines.append("-" * 48)
    steps = [
        "Tie synthetic seismogram to nearest well (bruges: Ricker + RC convolution)",
        "Multi-line correlation: does each feature persist on adjacent sections?",
        "Horizon amplitude extraction: what is the spatial pattern at each level?",
        "Depth conversion: velocity model → true structural depth",
        "AVO analysis on bright spots: fluid discrimination (Shuey two-term)",
        "Route geological risk to WEALTH: NPV/EMV under ranked uncertainty",
    ]
    for i, s in enumerate(steps, 1):
        lines.append(f"  {i}. {s}")

    lines.append("\n" + "=" * 72)
    lines.append("  EPISTEMIC STATUS: INT — all outputs are hypotheses, not facts")
    lines.append("  CONFIDENCE CAP: 0.90 (F7 HUMILITY)")
    lines.append("  OBS_IMAGE ≠ OBS_GEOLOGY")
    lines.append("=" * 72)

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API — integrate with GeoxPhysicalReality
# ═══════════════════════════════════════════════════════════════════════════

def run_geological_cognition(attrs: dict, fp: np.ndarray,
                              faults: list, horizons: list,
                              output_dir: str,
                              basin_context: str = "malay_basin",
                              prov_short: str = "",
                              raw_arr=None,
                              crop_bbox=None,
                              prov: dict = None) -> dict:
    """Run the full geological cognition pass.

    Takes outputs from geox_physical_reality.py and adds the reasoning layer:
        - Zone/package classification (basin architecture)
        - Termination detection (sequence stratigraphy)
        - Artifact screening (separate signal from illusion)
        - Hypothesis ranking (what does this MEAN, geologically?)
        - Geologist's report (human-readable interpretation memo)

    Returns enriched interpretation dict.
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    agc = attrs['agc']
    cp  = attrs['phase']
    pc  = attrs['coherence']

    print("  [COG-1] Basin-scale package classification...")
    packages = classify_reflector_packages(agc, cp, pc, n_zones=6)
    print(f"          {len(packages)} zones: {[p['geometry'] for p in packages]}")

    print("  [COG-2] Termination detection...")
    terminations = detect_terminations(horizons, agc, packages)
    high_sig = [t for t in terminations if t["sequence_significance"] == "HIGH"]
    print(f"          {len(terminations)} horizons analysed, {len(high_sig)} high-significance terminations")

    print("  [COG-3] Imaging artifact screen...")
    artifacts = screen_imaging_artifacts(agc, cp, fp, faults, horizons)
    print(f"          {artifacts['screen_verdict']}")

    print("  [COG-4] Hypothesis ranking...")
    hypotheses = rank_hypotheses(faults, horizons, packages, terminations, artifacts, basin_context)
    print(f"          Top fault hypothesis: {hypotheses['summary']['top_fault_hypothesis']}")
    print(f"          Top horizon hypothesis: {hypotheses['summary']['top_horizon_hypothesis']}")

    print("  [COG-5] Building geologist's report...")
    report_text = build_geologist_report(packages, terminations, artifacts, hypotheses, prov_short)
    report_path = os.path.join(output_dir, "D_geologist_report.txt")
    with open(report_path, "w") as f:
        f.write(report_text)
    print(f"  ✅ Report: {report_path}")

    # Save full cognition JSON
    cognition = {
        "packages": packages,
        "terminations": terminations,
        "artifacts": {k: v for k, v in artifacts.items() if k != "artifacts"}
                    | {"artifact_details": artifacts.get("artifacts", {})},
        "hypotheses": hypotheses,
        "basin_context": basin_context,
    }
    cog_path = os.path.join(output_dir, "cognition.json")
    with open(cog_path, "w") as f:
        json.dump(cognition, f, indent=2, default=str)
    print(f"  ✅ Cognition JSON: {cog_path}")

    print(report_text)

    # ── COG-6: Panel D — Cognitive Interpretation Render ────────────────
    print("  [COG-6] Rendering cognitive panel (Panel D)...")
    panel_d_path = None
    if raw_arr is not None:
        try:
            from geox_panel_d import render_cognitive_panel
            panel_d_path = render_cognitive_panel(
                attrs, fp, faults, horizons,
                packages, terminations, artifacts, hypotheses,
                raw_arr, crop_bbox, prov, output_dir)
        except Exception as e:
            print(f"  ⚠ Panel D failed: {e} (non-fatal)")

    outputs = [report_path, cog_path]
    if panel_d_path:
        outputs.append(panel_d_path)

    return {
        "packages": packages,
        "terminations": terminations,
        "artifacts": artifacts,
        "hypotheses": hypotheses,
        "outputs": outputs,
    }


# ═══════════════════════════════════════════════════════════════════════════
# CLI — run standalone or with geox_physical_reality output
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    from geox_physical_reality import GeoxPhysicalReality, _compute_attributes, _compute_fault_probability, _extract_amplitude, _crop_seismic_panel, _reality_gate
    from PIL import Image
    import numpy as np

    if len(sys.argv) < 2:
        print("Usage: python3 geox_geological_cognition.py <seismic_image> [output_dir] [basin]")
        print("       basin: malay_basin (default) | generic")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./geox_cognition_out"
    basin = sys.argv[3] if len(sys.argv) > 3 else "malay_basin"

    # Run physical reality pass first
    print("\n[PHASE 1] Physical Reality Pass...")
    pri = GeoxPhysicalReality()
    result = pri.interpret(image_path, output_dir=output_dir)

    if result.get("verdict") == "VOID":
        print(f"VOID: {result.get('reason')}")
        sys.exit(1)

    # Re-extract attrs + faults + horizons WITH full pts arrays
    # (the report dict strips pts for JSON size — cognition needs full geometry)
    from PIL import Image
    from geox_physical_reality import (
        _crop_seismic_panel, _extract_amplitude, _compute_attributes,
        _compute_fault_probability, _extract_faults, _extract_horizons,
    )
    raw = np.array(Image.open(image_path))
    cropped, crop_bbox = _crop_seismic_panel(raw)
    amp = _extract_amplitude(cropped)
    attrs = _compute_attributes(amp)
    fp = _compute_fault_probability(attrs)

    # Re-extract with full pts (needed by cognition module)
    faults   = _extract_faults(fp, min_pts=80, max_faults=15)
    horizons = _extract_horizons(attrs, faults, max_horizons=8)

    # Rebuild fault/horizon lists from report
    prov = result.get("input", {}).get("provenance", {})
    prov_short = f"img:{prov.get('image_sha256_short','?')} | {prov.get('run_tag','?')}"

    print("\n[PHASE 2] Geological Cognition Pass...")
    cog = run_geological_cognition(
        attrs, fp, faults, horizons,
        output_dir=output_dir,
        basin_context=basin,
        prov_short=prov_short,
        raw_arr=raw,
        crop_bbox=crop_bbox,
        prov=prov,
    )

    print(f"\nOutputs: {cog['outputs']}")
