"""
contracts/schemas/output_schemas.py — Canonical outputSchema for all 16 GEOX MCP tools.
MCP 2025-11-25 alignment: formal inputSchema + outputSchema per tool.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from typing import Any

# ── Shared schema fragments ────────────────────────────────────────────────────

PROVENANCE_BLOCK: dict[str, Any] = {
    "type": "object",
    "description": "Minimal provenance spine for audit and lineage.",
    "properties": {
        "tool_name": {"type": "string"},
        "tool_version": {"type": "string"},
        "artifact_hash": {"type": "string"},
        "claim_state": {"type": "string"},
        "depth_basis": {"type": "string", "enum": ["MD", "TVD", "TVDSS"]},
        "timestamp_utc": {"type": "string"},
        "evidence_refs": {"type": "array", "items": {"type": "string"}},
        "session_id": {"type": "string"},
    },
    "required": ["tool_name", "tool_version", "claim_state", "timestamp_utc"],
}

DEPTH_BASIS_BLOCK: dict[str, Any] = {
    "type": "object",
    "description": "Mandatory depth reference frame for all depth-valued outputs.",
    "properties": {
        "type": {"type": "string", "enum": ["MD", "TVD", "TVDSS"]},
        "datum": {"type": "string", "description": "e.g. KB, MSL, LAT"},
    },
}

CLAIM_STATE_ENUM: list[str] = [
    "NO_VALID_EVIDENCE",
    "INGESTED",
    "QC_VERIFIED",
    "INTERPRETED",
    "DERIVED_CANDIDATE",
    "SEALED",
    "JUDGE_PREVIEW",
    "888_HOLD",
    "VOID",
]

PERCEPTION_CLASS_ENUM: list[str] = [
    "MEASURED",
    "DERIVED",
    "DISPLAY",
    "CORROBORATED",
    "HYPOTHESIS",
]

EVIDENCE_TAG_ENUM: list[str] = [
    "EVIDENCE_DIRECT",
    "EVIDENCE_MULTI_ZONE",
    "INTERPRET_FROM_LITHOLOGY",
    "SOURCE_UNRESOLVED",
    "NN_NOT_PARSED",
    "NO_GDE_SOURCE",
    "GDE_NOT_MAPPED",
    "PROXY_FROM_CONTEXT",
    "UNKNOWN",
]

CANON9_ENUM: list[str] = [
    "rho",
    "Vp",
    "Vs",
    "rho_e",
    "chi",
    "k",
    "P",
    "T",
    "phi",
]

# ── Sprint 3a: Epistemic Ladder ───────────────────────────────────────────────
# Formal hierarchy that tags every piece of information with its distance from
# the physical earth. Lower rungs are closer to observation; higher rungs are
# further from verification. The iron law: the earth (Rung 1-2) outranks the
# interpreter (Rung 4-7). Every upward step adds assumptions and uncertainty.

EPISTEMIC_RUNG_ENUM: list[int] = [1, 2, 3, 4, 5, 6, 7]

EPISTEMIC_RUNG_LABELS: dict[int, str] = {
    1: "SIGNAL",  # Raw sensor output — unprocessed, uncalibrated
    2: "MEASUREMENT",  # Calibrated tool reading at specific depth/position
    3: "DERIVATION",  # Calculated from measurements + equations (e.g. Sw from RT)
    4: "INTERPRETATION",  # Abductive inference from multiple observations
    5: "MODEL",  # Computed from parameters + assumptions (e.g. P50 STOIIP)
    6: "JUDGMENT",  # Subjective evaluation against criteria
    7: "NARRATIVE",  # Story, rhetoric, recommendation
}

GROUNDING_TYPE_ENUM: list[str] = [
    "direct_measurement",  # Rung 1-2: raw sensor, calibrated reading
    "derived_calculation",  # Rung 3: derived via equation from measured
    "abductive_inference",  # Rung 4: best explanation given evidence
    "model_output",  # Rung 5: computed from assumptions
    "expert_judgment",  # Rung 6: subjective evaluation
    "narrative_framing",  # Rung 7: rhetorical construction
    "unknown",  # Cannot be determined
]

LADDER_DIRECTION_ENUM: list[str] = [
    "ascent",  # Evidence → Interpretation (normal reasoning path)
    "descent",  # Interpretation → Evidence (falsification path — verify_integrity)
    "lateral",  # Same rung (QC gate — neither adds nor removes epistemic distance)
    "mixed",  # Both directions in one tool (evidence_reason full phase)
]

ASSUMPTION_SENSITIVITY_ENUM: list[str] = [
    "CRITICAL",  # Changing this assumption collapses the entire interpretation
    "HIGH",  # Changes output significantly
    "MEDIUM",  # Changes output moderately
    "LOW",  # Minimal impact on output
]

MODALITY_ENUM: list[str] = [
    "well_log",
    "seismic",
    "core",
    "cuttings",
    "dst",
    "mud_log",
    "biostratigraphy",
    "geochemistry",
    "map",
    "report",
    "unknown",
]

# ── Schema fragments for Epistemic Ladder ─────────────────────────────────────

GROUNDING_ANCHOR_BLOCK: dict[str, Any] = {
    "type": "object",
    "description": "Modality-specific coordinate that grounds a claim to raw data.",
    "properties": {
        "modality": {"type": "string", "enum": MODALITY_ENUM},
        "well_id": {"type": "string"},
        "depth_range_m": {
            "type": "array",
            "items": {"type": "number"},
            "description": "[top, bottom] in metres MD",
            "minItems": 2,
            "maxItems": 2,
        },
        "cdp_range": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "[first_cdp, last_cdp] for seismic",
            "minItems": 2,
            "maxItems": 2,
        },
        "time_range_ms": {
            "type": "array",
            "items": {"type": "number"},
            "description": "[t_top, t_bottom] in milliseconds",
            "minItems": 2,
            "maxItems": 2,
        },
        "coordinate": {
            "type": "object",
            "properties": {
                "longitude": {"type": "number"},
                "latitude": {"type": "number"},
            },
        },
        "file_ref": {"type": "string", "description": "URI to source file, e.g. MAHA-1.las"},
        "raw_value": {"type": "string", "description": "The actual sensor reading as reported"},
    },
}

ASSUMPTION_RECORD_BLOCK: dict[str, Any] = {
    "type": "object",
    "description": "A single assumption added when climbing the epistemic ladder.",
    "properties": {
        "id": {"type": "string", "description": "Unique assumption ID, e.g. A1, A2"},
        "type": {
            "type": "string",
            "enum": ["cutoff", "model", "environment", "parameter", "analog", "threshold"],
        },
        "description": {"type": "string"},
        "source": {"type": "string", "description": "user_input, domain_knowledge, data_driven, convention"},
        "rung": {"type": "integer", "enum": EPISTEMIC_RUNG_ENUM},
        "value_used": {"type": "string"},
        "alternatives": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Reasonable alternative values that would change output",
        },
        "sensitivity": {"type": "string", "enum": ASSUMPTION_SENSITIVITY_ENUM},
    },
    "required": ["id", "type", "description", "rung", "sensitivity"],
}

EVIDENCE_LINK_BLOCK: dict[str, Any] = {
    "type": "object",
    "description": "A single claim in the evidence chain, grounded to a modality anchor.",
    "properties": {
        "claim": {"type": "string", "description": "Human-readable claim statement"},
        "rung": {"type": "integer", "enum": EPISTEMIC_RUNG_ENUM},
        "type": {
            "type": "string",
            "enum": ["OBSERVATION", "INTERPRETATION", "MODEL", "JUDGMENT", "NARRATIVE", "UNKNOWN"],
        },
        "grounding_type": {"type": "string", "enum": GROUNDING_TYPE_ENUM},
        "grounding_anchor": GROUNDING_ANCHOR_BLOCK,
        "falsifiable": {"type": "boolean"},
        "depends_on": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Assumption IDs this link depends on",
        },
        "counter_evidence": {
            "type": "string",
            "description": "Known contradicting evidence or alternative interpretations",
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Confidence in this specific claim, 0-1",
        },
    },
    "required": ["claim", "rung", "type", "grounding_type"],
}

UNCERTAINTY_BUDGET_BLOCK: dict[str, Any] = {
    "type": "object",
    "description": "Decomposition of total epistemic uncertainty into independent sources.",
    "properties": {
        "measurement_uncertainty": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "From tool accuracy, repeatability, environmental conditions",
        },
        "cutoff_uncertainty": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "From choice of threshold/cutoff values",
        },
        "model_uncertainty": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "From choice of physical/empirical model",
        },
        "assumption_uncertainty": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "From analog selection, parameter estimation",
        },
        "total_epistemic_uncertainty": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "RSS of above — assumes independence",
        },
        "dominant_source": {
            "type": "string",
            "enum": ["measurement_uncertainty", "cutoff_uncertainty", "model_uncertainty", "assumption_uncertainty"],
            "description": "Which source contributes most — tells geologist what to fix first",
        },
    },
    "required": ["total_epistemic_uncertainty"],
}

EPISTEMIC_PROVENANCE_BLOCK: dict[str, Any] = {
    "type": "object",
    "description": (
        "Sprint 3a: Epistemic Ladder provenance — tags every output with its distance "
        "from the physical earth. The iron law: Rung 1-2 (observation) outranks "
        "Rung 4-7 (interpretation). Every upward step declares its assumptions."
    ),
    "properties": {
        "output_rung": {
            "type": "integer",
            "enum": EPISTEMIC_RUNG_ENUM,
            "description": "Rung of the primary output claim",
        },
        "input_rungs": {
            "type": "array",
            "items": {"type": "integer", "enum": EPISTEMIC_RUNG_ENUM},
            "description": "Rungs of inputs consumed by this tool",
        },
        "ladder_direction": {
            "type": "string",
            "enum": LADDER_DIRECTION_ENUM,
            "description": (
                "ascent = interpretation (normal); descent = falsification (verify_integrity); "
                "lateral = QC gate (neither); mixed = both (evidence_reason full)"
            ),
        },
        "rung_delta": {
            "type": "integer",
            "description": "output_rung - min(input_rungs). Positive = ascent, negative = descent, zero = lateral",
        },
        "assumptions_added": {
            "type": "array",
            "items": ASSUMPTION_RECORD_BLOCK,
            "description": "Assumptions this tool introduced while climbing the ladder",
        },
        "assumptions_falsified": {
            "type": "array",
            "items": ASSUMPTION_RECORD_BLOCK,
            "description": "Assumptions rejected during descent (verify_integrity, evidence_reason contradict)",
        },
        "evidence_chain": {
            "type": "array",
            "items": EVIDENCE_LINK_BLOCK,
            "description": "Ordered chain from raw observation to final output claim",
        },
        "uncertainty_budget": UNCERTAINTY_BUDGET_BLOCK,
        "iron_law_violations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "higher_rung_claim": {"type": "string"},
                    "higher_rung": {"type": "integer"},
                    "contradicted_by_claim": {"type": "string"},
                    "contradicted_by_rung": {"type": "integer"},
                    "verdict": {"type": "string", "enum": ["VOID", "FLAG", "HOLD"]},
                },
            },
            "description": "Iron law violations detected: lower-rung observation beats higher-rung interpretation",
        },
    },
    "required": ["output_rung", "input_rungs", "ladder_direction", "rung_delta"],
}

# ── Canonical tool rung map ────────────────────────────────────────────────────
# Maps all 11 canonical MCP tools to their epistemic ladder position.
# ladder_direction: ascent (normal reasoning), descent (falsification), lateral (QC gate)
# For geox_evidence_reason: direction depends on phase (see phase_overrides)

TOOL_RUNG_MAP: dict[str, dict] = {
    # ── Rung 1→2: Signal ingestion ─────────────────────────────────────────
    "geox_data_ingest_bundle": {
        "input_rungs": [1],
        "output_rung": 2,
        "ladder_direction": "ascent",
        "assumptions_added": [
            {
                "id": "A1",
                "type": "parameter",
                "description": "Depth reference frame assumption (MD vs TVDSS)",
                "source": "user_input",
                "rung": 2,
                "value_used": "MD",
                "alternatives": ["TVDSS", "TVD"],
                "sensitivity": "MEDIUM",
            },
        ],
    },
    # ── Rung 2→2: QC gate — lateral ───────────────────────────────────────
    "geox_data_qc_bundle": {
        "input_rungs": [2],
        "output_rung": 2,
        "ladder_direction": "lateral",
        "assumptions_added": [],
    },
    # ── Rung 1-3→3: DST derivation ─────────────────────────────────────────
    "geox_dst_ingest_test": {
        "input_rungs": [1, 2],
        "output_rung": 3,
        "ladder_direction": "ascent",
        "assumptions_added": [
            {
                "id": "A1",
                "type": "model",
                "description": "Flow regime interpretation (stabilized vs transient)",
                "source": "domain_knowledge",
                "rung": 3,
                "value_used": "stabilized_flow",
                "alternatives": ["transient", "superposition"],
                "sensitivity": "HIGH",
            },
            {
                "id": "A2",
                "type": "parameter",
                "description": "Horner time assumption for pressure extrapolation",
                "source": "convention",
                "rung": 3,
                "value_used": "infinite_acting",
                "alternatives": ["finite_conductivity", "bounded"],
                "sensitivity": "MEDIUM",
            },
        ],
    },
    # ── Rung 2-3→5: Model computation ──────────────────────────────────────
    "geox_subsurface_generate_candidates": {
        "input_rungs": [2, 3],
        "output_rung": 5,
        "ladder_direction": "ascent",
        "assumptions_added": [
            {
                "id": "A1",
                "type": "cutoff",
                "description": "Porosity-cutoff for net pay",
                "source": "user_input",
                "rung": 3,
                "value_used": "0.08",
                "alternatives": ["0.06", "0.10", "0.12"],
                "sensitivity": "CRITICAL",
            },
            {
                "id": "A2",
                "type": "cutoff",
                "description": "Water saturation cutoff forHC pay",
                "source": "user_input",
                "rung": 3,
                "value_used": "0.50",
                "alternatives": ["0.45", "0.55", "0.60"],
                "sensitivity": "CRITICAL",
            },
            {
                "id": "A3",
                "type": "model",
                "description": "Spatial interpolation method",
                "source": "domain_knowledge",
                "rung": 5,
                "value_used": "ordinary_kriging",
                "alternatives": ["sequential_gaussian", "indicator_kriging"],
                "sensitivity": "HIGH",
            },
        ],
    },
    # ── Rung 5→2-5: Physics falsification (DESCENT) ────────────────────────
    # Only tool with negative rung_delta. Pushes Rung 5 models back to Rung 2
    # when Physics9 constraints are violated.
    "geox_subsurface_verify_integrity": {
        "input_rungs": [5],
        "output_rung": 2,  # Falls back to Rung 2 observations when model fails
        "ladder_direction": "descent",
        "assumptions_added": [],
        "assumptions_falsified": [
            {
                "id": "F1",
                "type": "model",
                "description": "Model prediction violated physics constraint",
                "source": "data_driven",
                "rung": 5,
                "value_used": "failed_model",
                "alternatives": [],
                "sensitivity": "CRITICAL",
            },
        ],
    },
    # ── Rung 2-3: Seismic compute (4 modes → different directions) ──────────
    # synthetic: Rung 2-3 → 3 (ascent)
    # well_tie: Rung 2+3 → 4 (ascent)
    # anomalous_contrast: Rung 2-3 → 4 (ascent)
    # gather_hydrophone: Rung 2 → 3 (ascent)
    "geox_seismic_compute": {
        "input_rungs": [2, 3],
        "output_rung": 3,
        "ladder_direction": "ascent",
        "assumptions_added": [
            {
                "id": "A1",
                "type": "parameter",
                "description": "Wavelet assumption (frequency, phase)",
                "source": "user_input",
                "rung": 3,
                "value_used": "ricker_25hz",
                "alternatives": ["ricker_30hz", "ormsby_20_40", "zero_phase"],
                "sensitivity": "HIGH",
            },
            {
                "id": "A2",
                "type": "model",
                "description": "Earth filter (convolution model)",
                "source": "domain_knowledge",
                "rung": 3,
                "value_used": "layered_acoustic",
                "alternatives": ["elastic", "viscoelastic"],
                "sensitivity": "MEDIUM",
            },
        ],
    },
    # ── Rung 2→4: Sequence stratigraphy (dramatic rung jump) ───────────────
    "geox_sequence_interpret": {
        "input_rungs": [2],
        "output_rung": 4,
        "ladder_direction": "ascent",
        "assumptions_added": [
            {
                "id": "A1",
                "type": "cutoff",
                "description": "GR clean/shale cutoff",
                "source": "user_input",
                "rung": 3,
                "value_used": "75 API",
                "alternatives": ["60 API", "80 API", "90 API"],
                "sensitivity": "HIGH",
            },
            {
                "id": "A2",
                "type": "model",
                "description": "Sequence stratigraphic framework",
                "source": "domain_knowledge",
                "rung": 4,
                "value_used": "Catuneanu_2006",
                "alternatives": ["Vail_1977", "Galloway_1989", "Embry_2009"],
                "sensitivity": "CRITICAL",
            },
            {
                "id": "A3",
                "type": "environment",
                "description": "Depositional environment",
                "source": "user_input",
                "rung": 4,
                "value_used": "deltaic",
                "alternatives": ["carbonate_shelf", "deep_marine", "fluvial"],
                "sensitivity": "CRITICAL",
            },
        ],
    },
    # ── Rung 2-5: Evidence synthesis (mixed — goes both directions) ─────────
    # synthesize/abduct: ascent 2-3 → 4-5
    # contradict: descent → 2 (falsification)
    # full: mixed (both)
    "geox_evidence_reason": {
        "input_rungs": [2, 3, 4, 5],
        "output_rung": 5,
        "ladder_direction": "mixed",
        "phase_overrides": {
            "synthesize": {"output_rung": 5, "ladder_direction": "ascent"},
            "abduct": {"output_rung": 4, "ladder_direction": "ascent"},
            "contradict": {"output_rung": 2, "ladder_direction": "descent"},
            "full": {"output_rung": 6, "ladder_direction": "mixed"},
        },
        "assumptions_added": [
            {
                "id": "A1",
                "type": "model",
                "description": "Cross-domain inference framework",
                "source": "domain_knowledge",
                "rung": 4,
                "value_used": "bayesian_network",
                "alternatives": ["dempster_shafer", "fuzzy_logic"],
                "sensitivity": "HIGH",
            },
        ],
    },
    # ── Rung 3-5→6-7: Prospect evaluation (highest rung outputs) ───────────
    "geox_prospect_evaluate": {
        "input_rungs": [3, 4, 5],
        "output_rung": 6,
        "ladder_direction": "ascent",
        "assumptions_added": [
            {
                "id": "A1",
                "type": "parameter",
                "description": "Discount rate for NPV",
                "source": "user_input",
                "rung": 6,
                "value_used": "0.10",
                "alternatives": ["0.08", "0.12", "0.15"],
                "sensitivity": "HIGH",
            },
            {
                "id": "A2",
                "type": "analog",
                "description": "Analog field selection",
                "source": "domain_knowledge",
                "rung": 6,
                "value_used": "regional_analogue",
                "alternatives": ["published_analogue", "proprietary_analogue"],
                "sensitivity": "CRITICAL",
            },
            {
                "id": "A3",
                "type": "threshold",
                "description": "Commercial门槛 (rate, porosity, thickness)",
                "source": "user_input",
                "rung": 6,
                "value_used": "custom",
                "alternatives": ["industry_standard"],
                "sensitivity": "CRITICAL",
            },
        ],
    },
    # ── Rung 2→2: Map rendering (lateral — no interpretation added) ────────
    "geox_map_context_scene": {
        "input_rungs": [2],
        "output_rung": 2,
        "ladder_direction": "lateral",
        "assumptions_added": [],
    },
    # ── Meta: no epistemic content ──────────────────────────────────────────
    "geox_system_registry_status": {
        "input_rungs": [],
        "output_rung": 0,  # Meta — no epistemic content
        "ladder_direction": "lateral",
        "assumptions_added": [],
    },
}


def validate_iron_law(evidence_chain: list[dict]) -> list[dict]:
    """
    Scan an evidence chain for iron law violations.

    Iron law: Rung 1-2 (observation) ALWAYS outranks Rung 4-7 (interpretation).
    If a higher-rung claim has counter_evidence tracing to a lower-rung observation,
    the lower-rung wins. The higher-rung claim must be VOID or flagged.

    Returns a list of violation records.
    """
    violations = []

    # Index claims by rung
    by_rung: dict[int, list[dict]] = {}
    for link in evidence_chain:
        rung = link.get("rung", 0)
        by_rung.setdefault(rung, []).append(link)

    # Check Rung 5+ claims against Rung 2 observations
    for claim_link in by_rung.get(5, []) + by_rung.get(6, []) + by_rung.get(7, []):
        counter = claim_link.get("counter_evidence", "")
        if not counter:
            continue

        # If there's a Rung 2 observation contradicting this Rung 5+ claim
        rung_2_claims = by_rung.get(2, [])
        if rung_2_claims:
            violations.append(
                {
                    "higher_rung_claim": claim_link.get("claim", ""),
                    "higher_rung": claim_link.get("rung", 0),
                    "contradicted_by_claim": rung_2_claims[0].get("claim", ""),
                    "contradicted_by_rung": 2,
                    "verdict": "VOID",
                }
            )

    # Check Rung 4 vs Rung 2 conflicts (e.g. interpretation contradicts measurement)
    for claim_link in by_rung.get(4, []):
        counter = claim_link.get("counter_evidence", "")
        if not counter:
            continue
        rung_2_claims = by_rung.get(2, [])
        if rung_2_claims:
            violations.append(
                {
                    "higher_rung_claim": claim_link.get("claim", ""),
                    "higher_rung": 4,
                    "contradicted_by_claim": rung_2_claims[0].get("claim", ""),
                    "contradicted_by_rung": 2,
                    "verdict": "FLAG",
                }
            )

    return violations


TOAC_PERCEPTION_BLOCK: dict[str, Any] = {
    "type": "object",
    "description": "ToAC v1 perception bridge: how this output relates to measured reality.",
    "properties": {
        "perception_class": {
            "type": "string",
            "enum": PERCEPTION_CLASS_ENUM,
            "description": "MEASURED=direct sensor, DERIVED=from measured, DISPLAY=visual artifact, CORROBORATED=multi-evidence, HYPOTHESIS=proxy without raw signal",
        },
        "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM, "description": "Per-field evidence provenance tag"},
        "canon_9_touched": {
            "type": "array",
            "items": {"type": "string", "enum": CANON9_ENUM},
            "description": "Which EARTH.CANON_9 quantities this output reads/writes/constrains",
        },
        "vertical_trend": {"type": "string", "enum": ["DEEPENING_UPWARD", "SHALLOWING_UPWARD", "STABLE_OR_AMBIGUOUS", "UNKNOWN"]},
        "litho_class": {
            "type": "string",
            "enum": [
                "CARBONATE",
                "HETEROLITHIC",
                "SAND_PRONE",
                "SILT_PRONE",
                "SHALE_PRONE",
                "COAL_CARBONACEOUS",
                "MIXED_OR_UNSPECIFIED",
                "UNKNOWN",
            ],
        },
        "strat_standard": {
            "type": "object",
            "properties": {
                "scheme": {"type": "string", "enum": ["NN_zone", "NP_zone", "Stage_Sabah", "Cycle_Sarawak", "custom"]},
                "reference_chart": {"type": "string", "description": "URI to governing chart, e.g. GPTS2020"},
            },
        },
    },
}

# ── Per-tool output schemas ───────────────────────────────────────────────────

TOOL_OUTPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    # ── 01 Ingest ──────────────────────────────────────────────────────────────
    "geox_data_ingest_bundle": {
        "description": (
            "Lazy ingestion for LAS, CSV, Parquet, SEG-Y, and structural payloads. "
            "claim_state=INGESTED on success. Returns depth_basis=MD unless TVDSS supplied."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "primary_artifact": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "tool": {"type": "string"},
                        "artifact_ref": {"type": "string"},
                        "well_id": {"type": "string"},
                        "loaded_curves": {"type": "array", "items": {"type": "string"}},
                        "depth_range_m": {"type": "array", "items": {"type": "number"}},
                        "depth_unit_normalized": {"type": "string"},
                        "sha256": {"type": "string"},
                        "canonical_curve_map": {"type": "object"},
                        "missing_canonical_curves": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "confidence_band": {"anyOf": [{"type": "object"}, {"type": "null"}]},
                "physics_guard": {"type": "object"},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "humility_score": {"type": "number"},
                "maruah_flag": {"type": "object"},
                "diagnostics": {"type": "object"},
                "provenance": PROVENANCE_BLOCK,
                "depth_basis": DEPTH_BASIS_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "epistemic_provenance": EPISTEMIC_PROVENANCE_BLOCK,
            },
            "required": ["claim_state", "provenance", "primary_artifact", "epistemic_provenance"],
        },
        "title": "Earth Data Ingestion Engine",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 02 QC ──────────────────────────────────────────────────────────────────
    "geox_data_qc_bundle": {
        "description": (
            "Real QC: depth monotonicity, null %, physical range checks. "
            "Sets claim_state=QC_VERIFIED only after actual data inspection. "
            "Fails closed: physics range breach → VOID."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "qc_passed": {"type": "boolean"},
                "qc_overall": {"type": "string"},
                "flags": {"type": "array", "items": {"type": "string"}},
                "limitations": {"type": "array", "items": {"type": "string"}},
                "depth_qc": {
                    "type": "object",
                    "properties": {
                        "monotonic": {"type": "boolean"},
                        "step_mean_m": {"type": "number"},
                        "depth_range_m": {"type": "array", "items": {"type": "number"}},
                    },
                },
                "curve_statistics": {"type": "object"},
                "depth_basis": DEPTH_BASIS_BLOCK,
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "epistemic_provenance": EPISTEMIC_PROVENANCE_BLOCK,
            },
            "required": ["claim_state", "qc_passed", "provenance", "epistemic_provenance"],
        },
        "title": "Earth Data QC Engine",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 03 Subsurface Generate ──────────────────────────────────────────────────
    "geox_subsurface_generate_candidates": {
        "description": (
            "Generates ensemble subsurface outputs (Vsh, porosity, Sw, net pay, permeability, "
            "lithology, GR motif). Fails closed: empty evidence_refs → NO_VALID_EVIDENCE/VOID. "
            "claim_state=DERIVED_CANDIDATE on success."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "primary_artifact": {"type": "object"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "confidence_band": {"anyOf": [{"type": "object"}, {"type": "null"}]},
                "physics_guard": {"type": "object"},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "humility_score": {"type": "number"},
                "ensemble": {"type": "array"},
                "residual": {"type": "object"},
                "evidence_density": {"type": "object"},
                "depth_basis": DEPTH_BASIS_BLOCK,
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "vertical_trend": {
                    "type": "string",
                    "enum": ["DEEPENING_UPWARD", "SHALLOWING_UPWARD", "STABLE_OR_AMBIGUOUS", "UNKNOWN"],
                },
                "litho_class": {
                    "type": "string",
                    "enum": [
                        "CARBONATE",
                        "HETEROLITHIC",
                        "SAND_PRONE",
                        "SILT_PRONE",
                        "SHALE_PRONE",
                        "COAL_CARBONACEOUS",
                        "MIXED_OR_UNSPECIFIED",
                        "UNKNOWN",
                    ],
                },
                "epistemic_provenance": EPISTEMIC_PROVENANCE_BLOCK,
            },
            "required": ["claim_state", "evidence_refs", "provenance", "epistemic_provenance"],
        },
        "title": "Subsurface Candidate Generator",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 04 Subsurface Verify ───────────────────────────────────────────────────
    "geox_subsurface_verify_integrity": {
        "description": (
            "Enforces Physics9 boundary limits and detects structural paradoxes. "
            "Never returns SEAL without verified evidence. "
            "claim_state=COMPUTED on success; NO_VALID_EVIDENCE if artifact not found."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "physics_guard": {"type": "object"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "epistemic_provenance": EPISTEMIC_PROVENANCE_BLOCK,
            },
            "required": ["claim_state", "governance_status", "provenance", "epistemic_provenance"],
        },
        "title": "Subsurface Integrity Verifier",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 05 Seismic ────────────────────────────────────────────────────────────
    "geox_seismic_analyze_volume": {
        "description": (
            "Seismic attribute computation, slice rendering, and interpretation support. "
            "ToAC: outputs are INTERPRETED by default (DISPLAY until well-tie confirms). "
            "claim_state=INTERPRETED on success."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "physics_guard": {"type": "object"},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "provenance": PROVENANCE_BLOCK,
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
            },
            "required": ["claim_state", "perception_class", "provenance"],
        },
        "title": "Seismic Volume Analyzer",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 06 Section ─────────────────────────────────────────────────────────────
    "geox_section_interpret_correlation": {
        "description": (
            "Multi-well stratigraphic correlation and marker interpretation. "
            "claim_state=INTERPRETED for correlation; DERIVED_CANDIDATE for motif/surfaces. "
            "Returns depth_basis=MD by default."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "motifs_by_well": {"type": "object"},
                "candidate_surfaces": {"type": "array"},
                "depth_basis": DEPTH_BASIS_BLOCK,
                "provenance": PROVENANCE_BLOCK,
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "vertical_trend": {
                    "type": "string",
                    "enum": ["DEEPENING_UPWARD", "SHALLOWING_UPWARD", "STABLE_OR_AMBIGUOUS", "UNKNOWN"],
                },
                "litho_class": {
                    "type": "string",
                    "enum": [
                        "CARBONATE",
                        "HETEROLITHIC",
                        "SAND_PRONE",
                        "SILT_PRONE",
                        "SHALE_PRONE",
                        "COAL_CARBONACEOUS",
                        "MIXED_OR_UNSPECIFIED",
                        "UNKNOWN",
                    ],
                },
                "strat_standard": {
                    "type": "object",
                    "properties": {
                        "scheme": {"type": "string", "enum": ["NN_zone", "NP_zone", "Stage_Sabah", "Cycle_Sarawak", "custom"]},
                        "reference_chart": {"type": "string"},
                    },
                },
                # ── well_tie fields ────────────────────────────────────────────
                "tie_quality_verdict": {
                    "type": "string",
                    "enum": ["EXCELLENT", "GOOD", "MODERATE", "POOR", "UNDETERMINED"],
                    "description": "Well-to-seismic tie quality assessment",
                },
                "correlation_coefficient": {
                    "type": "number",
                    "minimum": -1.0,
                    "maximum": 1.0,
                    "description": "Pearson correlation coefficient between synthetic and seismic trace",
                },
                "residual_rms": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Normalised RMS residual after optimal shift",
                },
                "phase_rotation_applied": {
                    "type": "number",
                    "description": "Phase rotation applied to synthetic trace (degrees)",
                },
                "time_shift_ms": {
                    "type": "number",
                    "description": "Optimal time shift applied to align synthetic with seismic (ms)",
                },
                "polarity_verdict": {
                    "type": "string",
                    "enum": ["MATCHED", "REVERSED", "UNDETERMINED"],
                },
                "wavelet": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["ricker", "ormsby", "klauder", "estimated"]},
                        "frequency_hz": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Frequency Hz — scalar for ricker/klauder, [f1,f2,f3,f4] for ormsby",
                        },
                        "phase_degrees": {"type": "number"},
                    },
                },
                "synthetic_ref": {
                    "type": ["string", "null"],
                    "description": "Artifact ref for registered synthetic trace (if synthetics_output=True)",
                },
                "correlation_traces": {
                    "type": ["object", "null"],
                    "description": "Correlation QC traces (if tie_qc_report=True)",
                },
                "depth_to_time": {
                    "type": "object",
                    "properties": {
                        "method": {"type": "string", "enum": ["checkshot", "average_velocity"]},
                        "coverage_pct": {"type": "number", "minimum": 0.0, "maximum": 100.0},
                    },
                },
                "ai_curve": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Acoustic impedance curve (Vp × rho) at each depth sample",
                },
                "reflectivity_series": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Zoeppritz reflectivity series at interface midpoints",
                },
                "physics_guard": {
                    "type": "object",
                    "description": "CANON-9 bounds verification for Vp and AI",
                },
                "humility_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Uncertainty load on this output (0=fully certain, 1=fully uncertain)",
                },
                "maruah_flag": {"type": "object"},
            },
            "required": ["claim_state", "perception_class", "provenance"],
        },
        "title": "Stratigraphic Section Interpreter",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 07 Map ─────────────────────────────────────────────────────────────────
    "geox_map_context_scene": {
        "description": (
            "Spatial bbox context, CRS checks, and causal scene rendering. "
            "ToAC: rendered scenes carry perception_class=DISPLAY. "
            "claim_state=INTERPRETED for rendered scenes."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "maruah_flag": {"type": "object"},
                "provenance": PROVENANCE_BLOCK,
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "vertical_trend": {
                    "type": "string",
                    "enum": ["DEEPENING_UPWARD", "SHALLOWING_UPWARD", "STABLE_OR_AMBIGUOUS", "UNKNOWN"],
                },
                "litho_class": {
                    "type": "string",
                    "enum": [
                        "CARBONATE",
                        "HETEROLITHIC",
                        "SAND_PRONE",
                        "SILT_PRONE",
                        "SHALE_PRONE",
                        "COAL_CARBONACEOUS",
                        "MIXED_OR_UNSPECIFIED",
                        "UNKNOWN",
                    ],
                },
                "epistemic_provenance": EPISTEMIC_PROVENANCE_BLOCK,
            },
            "required": ["claim_state", "perception_class", "provenance", "epistemic_provenance"],
        },
        "title": "Geospatial Scene Renderer",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 08 Time4D ──────────────────────────────────────────────────────────────
    "geox_time4d_analyze_system": {
        "description": (
            "Burial history, maturity modeling, and regime shift analysis. "
            "F2 Truth: without VRo/Tmax evidence, maturity is HYPOTHESIS not INTERPRETED. "
            "claim_state=INTERPRETED with evidence; NO_VALID_EVIDENCE without."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "depth_basis": DEPTH_BASIS_BLOCK,
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "strat_standard": {
                    "type": "object",
                    "properties": {
                        "scheme": {"type": "string", "enum": ["NN_zone", "NP_zone", "Stage_Sabah", "Cycle_Sarawak", "custom"]},
                        "reference_chart": {"type": "string"},
                    },
                },
            },
            "required": ["claim_state", "evidence_refs", "provenance"],
        },
        "title": "4D Time-System Analyzer",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 09 Prospect Evaluate ───────────────────────────────────────────────────
    "geox_prospect_evaluate": {
        "description": (
            "Integrated prospect evaluation (Volumetrics, POS, EVOI). "
            "claim_state=INTERPRETED on success; CANDIDATE if Monte Carlo converges. "
            "screen mode: claim_state=NO_VALID_EVIDENCE (qualitative only)."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "confidence_band": {"anyOf": [{"type": "object"}, {"type": "null"}]},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "humility_score": {"type": "number"},
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "vertical_trend": {
                    "type": "string",
                    "enum": ["DEEPENING_UPWARD", "SHALLOWING_UPWARD", "STABLE_OR_AMBIGUOUS", "UNKNOWN"],
                },
                "litho_class": {
                    "type": "string",
                    "enum": [
                        "CARBONATE",
                        "HETEROLITHIC",
                        "SAND_PRONE",
                        "SILT_PRONE",
                        "SHALE_PRONE",
                        "COAL_CARBONACEOUS",
                        "MIXED_OR_UNSPECIFIED",
                        "UNKNOWN",
                    ],
                },
                "epistemic_provenance": EPISTEMIC_PROVENANCE_BLOCK,
            },
            "required": ["claim_state", "evidence_refs", "provenance", "epistemic_provenance"],
        },
        "title": "Prospect Evaluator",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 10 Prospect Judge Preview ──────────────────────────────────────────────
    "geox_prospect_judge_preview": {
        "description": (
            "Reversible advisory verdict. Does NOT require ack_irreversible. claim_state=JUDGE_PREVIEW (non-binding preview)."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "f13_compliance": {"type": "object"},
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
            },
            "required": ["claim_state", "governance_status", "provenance"],
        },
        "title": "Prospect Judge Preview",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 11 Prospect Judge Seal ──────────────────────────────────────────────────
    "geox_prospect_judge_seal": {
        "description": (
            "888_JUDSEAL gateway: irreversible constitutional adjudication. "
            "F11 AUTH: constant-time PIN verification. F1 Amanah: requires ack_irreversible=True. "
            "claim_state=SEALED on success."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "f13_compliance": {"type": "object"},
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
            },
            "required": ["claim_state", "governance_status", "f13_compliance", "provenance"],
        },
        "title": "Prospect Judge Seal",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    },
    # ── 12 Evidence Summarize ───────────────────────────────────────────────────
    "geox_evidence_summarize_cross": {
        "description": (
            "Cross-domain synthesis into a causal evidence graph. "
            "claim_state=INTERPRETED (synthesis is always interpretation). "
            "Perception class: DERIVED (from measured) or DISPLAY (from rendered artifacts)."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "export_written": {"type": "boolean"},
                "provenance": PROVENANCE_BLOCK,
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "vertical_trend": {
                    "type": "string",
                    "enum": ["DEEPENING_UPWARD", "SHALLOWING_UPWARD", "STABLE_OR_AMBIGUOUS", "UNKNOWN"],
                },
                "strat_standard": {
                    "type": "object",
                    "properties": {
                        "scheme": {"type": "string", "enum": ["NN_zone", "NP_zone", "Stage_Sabah", "Cycle_Sarawak", "custom"]},
                        "reference_chart": {"type": "string"},
                    },
                },
            },
            "required": ["claim_state", "evidence_refs", "provenance"],
        },
        "title": "Cross-Domain Evidence Synthesizer",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 13 System Registry Status ──────────────────────────────────────────────
    "geox_system_registry_status": {
        "description": (
            "Discovery of canonical tools, health, and contract epoch. "
            "Reports the ACTUAL live MCP surface. Meta tool — no claim_state change."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "primary_artifact": {"type": "object"},
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "epistemic_provenance": EPISTEMIC_PROVENANCE_BLOCK,
            },
            "required": ["provenance", "epistemic_provenance"],
        },
        "title": "System Registry Status",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── Sprint 3a: Missing canonical tool schemas ──────────────────────────────────
    # These 3 canonical tools were referenced in TOOL_RUNG_MAP but had no
    # TOOL_OUTPUT_SCHEMAS entry. Added as part of Sprint 3a Epistemic Ladder.
    # ── 06b Seismic Compute ─────────────────────────────────────────────────────
    "geox_seismic_compute": {
        "description": (
            "Seismic forward modeling and attribute computation (synthetic, well-tie, "
            "anomalous contrast, gather QC). Fails closed: impossible physics → VOID. "
            "claim_state=INTERPRETED on success."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "mode": {"type": "string", "enum": ["synthetic", "well_tie", "anomalous_contrast", "gather_hydrophone"]},
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "physics_guard": {"type": "object"},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "primary_artifact": {"type": "object"},
                "provenance": PROVENANCE_BLOCK,
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "epistemic_provenance": EPISTEMIC_PROVENANCE_BLOCK,
            },
            "required": ["claim_state", "mode", "provenance", "epistemic_provenance"],
        },
        "title": "Seismic Compute Engine",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 07b Sequence Interpret ─────────────────────────────────────────────────
    "geox_sequence_interpret": {
        "description": (
            "Sequence stratigraphic interpretation from well log motifs and biostratigraphy. "
            "Returns systems tract, parasequence surfaces, and depositional interpretation. "
            "claim_state=INTERPRETED on success. "
            "This is the primary rung-jump tool: Rung 2 (GR log) → Rung 4 (sequence interpretation)."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "motifs_by_well": {"type": "object"},
                "candidate_surfaces": {"type": "array"},
                "depth_basis": DEPTH_BASIS_BLOCK,
                "provenance": PROVENANCE_BLOCK,
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "vertical_trend": {
                    "type": "string",
                    "enum": ["DEEPENING_UPWARD", "SHALLOWING_UPWARD", "STABLE_OR_AMBIGUOUS", "UNKNOWN"],
                },
                "litho_class": {
                    "type": "string",
                    "enum": [
                        "CARBONATE",
                        "HETEROLITHIC",
                        "SAND_PRONE",
                        "SILT_PRONE",
                        "SHALE_PRONE",
                        "COAL_CARBONACEOUS",
                        "MIXED_OR_UNSPECIFIED",
                        "UNKNOWN",
                    ],
                },
                "strat_standard": {
                    "type": "object",
                    "properties": {
                        "scheme": {"type": "string", "enum": ["NN_zone", "NP_zone", "Stage_Sabah", "Cycle_Sarawak", "custom"]},
                        "reference_chart": {"type": "string"},
                    },
                },
                "epistemic_provenance": EPISTEMIC_PROVENANCE_BLOCK,
            },
            "required": ["claim_state", "evidence_refs", "provenance", "epistemic_provenance"],
        },
        "title": "Sequence Stratigraphy Interpreter",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 08b Evidence Reason ────────────────────────────────────────────────────
    "geox_evidence_reason": {
        "description": (
            "Cross-domain evidence synthesis and contradiction detection. "
            "Phase 'synthesize': ascent Rung 2-3 → Rung 5. "
            "Phase 'abduct': abduction to Rung 4. "
            "Phase 'contradict': DESCENT to Rung 2 (falsification path). "
            "Phase 'full': mixed ascent/descent. "
            "claim_state=INTERPRETED on success; VOID if contradictions cannot be resolved."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "phase": {"type": "string", "enum": ["synthesize", "abduct", "contradict", "full"]},
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "primary_artifact": {"type": "object"},
                "provenance": PROVENANCE_BLOCK,
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "iron_law_violations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "higher_rung_claim": {"type": "string"},
                            "higher_rung": {"type": "integer"},
                            "contradicted_by_claim": {"type": "string"},
                            "contradicted_by_rung": {"type": "integer"},
                            "verdict": {"type": "string", "enum": ["VOID", "FLAG", "HOLD"]},
                        },
                    },
                },
                "epistemic_provenance": EPISTEMIC_PROVENANCE_BLOCK,
            },
            "required": ["claim_state", "phase", "evidence_refs", "provenance", "epistemic_provenance"],
        },
        "title": "Evidence Reasoning Engine",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 14 History Audit ───────────────────────────────────────────────────────
    "geox_history_audit": {
        "description": (
            "VAULT999 retrieval of past runs and decision lineage. "
            "Queries VAULT999 SEALED_EVENTS.jsonl + GEOX artifact store. "
            "Each record includes claim_state, verdict, actor_id, session_id, timestamp. "
            "Supports cursor-based pagination via nextCursor. Read-only — no state change."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "primary_artifact": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Sanitized search query"},
                        "records": {"type": "array", "description": "Matched decision lineage and artifact records"},
                        "record_count": {"type": "integer"},
                        "total_matching": {"type": "integer"},
                        "nextCursor": {"type": "string", "description": "Opaque cursor for pagination"},
                        "vault": {"type": "string"},
                        "sources_queried": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
            },
            "required": ["provenance", "primary_artifact"],
        },
        "title": "VAULT999 History Auditor",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── 15 Prospect Judge Verdict (internal governance gate) ─────────────────
    "geox_prospect_judge_verdict": {
        "description": (
            "[DEPRECATED] Internal 888_JUDGE gateway. "
            "Delegates to geox_prospect_judge_seal. "
            "Internal only — not in public canonical registry."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
            },
            "required": ["claim_state", "governance_status", "provenance"],
        },
        "title": "Prospect Judge Verdict (Internal)",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    },
    # ── 16 DST Ingest ───────────────────────────────────────────────────────────
    "geox_dst_ingest_test": {
        "description": (
            "Structured DST (Drill-Stem Test) ingestion with derived metrics and flags. "
            "F2 Truth: all outputs are OBSERVED from supplied parameters. "
            "claim_state=INGESTED on success. "
            "DST with impossible pressure gradient → VOID."
        ),
        "outputSchema": {
            "type": "object",
            "properties": {
                "execution_status": {"type": "string"},
                "tool_class": {"type": "string"},
                "governance_status": {"type": "string"},
                "artifact_status": {"type": "string"},
                "claim_tag": {"type": "string"},
                "claim_state": {"type": "string", "enum": CLAIM_STATE_ENUM},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "derived_metrics": {"type": "object"},
                "flags": {"type": "array", "items": {"type": "string"}},
                "depth_basis": DEPTH_BASIS_BLOCK,
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
            },
            "required": ["claim_state", "provenance"],
        },
        "title": "DST Data Ingestion",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
}


def get_tool_output_schema(tool_name: str) -> dict[str, Any] | None:
    """Return the outputSchema for a given tool name, or None if not found."""
    entry = TOOL_OUTPUT_SCHEMAS.get(tool_name)
    if entry:
        return entry.get("outputSchema")
    return None


def get_tool_metadata(tool_name: str) -> dict[str, Any] | None:
    """Return full metadata (title, annotations, outputSchema) for a given tool."""
    return TOOL_OUTPUT_SCHEMAS.get(tool_name)
