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
            },
            "required": ["claim_state", "provenance", "primary_artifact"],
        },
        "title": "Earth Data Ingestion Engine",
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # ── MISSING 3 — Sprint 1 additions ─────────────────────────────────────────
    # geox_seismic_compute — oneOf 5-mode discriminated union
    "geox_seismic_compute": {
        "description": (
            "Unified seismic physics engine (5 modes). "
            "synthetic: forward model S=w*r+n. well_tie: cross-correlation tie. "
            "time_depth_anchor: checkshot/VSP anchoring. anomalous_contrast: AC mismatch detection. "
            "attribute: RMS/variance (honest stub). "
            "All modes return standard envelope with mode-specific primary_artifact."
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
                    "oneOf": [
                        # synthetic
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "mode": {"type": "string", "const": "synthetic"},
                                "synthetic_trace": {"type": "array", "items": {"type": "number"}},
                                "ai_profile": {"type": "array", "items": {"type": "number"}},
                                "rc_series": {"type": "array", "items": {"type": "number"}},
                                "twt_axis_ms": {"type": "array", "items": {"type": "number"}},
                                "depth_axis_m": {"type": "array", "items": {"type": "number"}},
                                "wavelet_signature": {"type": "array", "items": {"type": "number"}},
                                "wavelet_type": {"type": "string"},
                                "wavelet_freq_hz": {"type": "number"},
                                "depth_unit": {"type": "string"},
                                "time_unit": {"type": "string"},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "mode"],
                        },
                        # well_tie
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "mode": {"type": "string", "const": "well_tie"},
                                "cross_correlation": {"type": "array", "items": {"type": "number"}},
                                "shift_samples": {"type": "number"},
                                "quality_factor": {"type": "number"},
                                "wavelet_type": {"type": "string"},
                                "frequency_band_hz": {"type": "array", "items": {"type": "number"}},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "mode"],
                        },
                        # time_depth_anchor
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "mode": {"type": "string", "const": "time_depth_anchor"},
                                "td_curve": {"type": "array", "items": {"type": "number"}},
                                "depth_m": {"type": "array", "items": {"type": "number"}},
                                "drift_ms": {"type": "number"},
                                "method": {"type": "string"},
                                "checkshot_ref": {"type": "string"},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "mode"],
                        },
                        # anomalous_contrast
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "mode": {"type": "string", "const": "anomalous_contrast"},
                                "rc_profile": {"type": "array", "items": {"type": "number"}},
                                "depth_m": {"type": "array", "items": {"type": "number"}},
                                "anomalous_intervals": {"type": "array", "items": {"type": "object"}},
                                "formation_tops": {"type": "object"},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "mode"],
                        },
                        # attribute (honest stub)
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "mode": {"type": "string", "const": "attribute"},
                                "volume_ref": {"type": "string"},
                                "attribute": {"type": "string"},
                                "status": {"type": "string"},
                                "note": {"type": "string"},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "mode"],
                        },
                    ],
                },
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
                "equations_used": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["claim_state", "provenance", "primary_artifact"],
        },
        "title": "Unified Seismic Physics Engine",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # geox_sequence_interpret — oneOf 4-workflow discriminated union
    "geox_sequence_interpret": {
        "description": (
            "Unified sequence stratigraphy engine (4 workflows). "
            "single_well: param-driven L1-L3 pipeline (bins→packages→seq strat). "
            "project: YAML-driven multi-well with XLSX/PNG output. "
            "preview: validate project YAML without running. "
            "section_correlation: cross-well correlation panel. "
            "Returns standard envelope with workflow-specific artifacts."
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
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "workflow": {"type": "string", "const": "single_well"},
                                "zone_top_m": {"type": "number"},
                                "zone_base_m": {"type": "number"},
                                "gr_bins": {"type": "array", "items": {"type": "object"}},
                                "packages": {"type": "array", "items": {"type": "object"}},
                                "sequence_boundaries": {"type": "array", "items": {"type": "object"}},
                                "depo_environment": {"type": "string"},
                                "gr_cutoff_api": {"type": "number"},
                                "p50_shift_api": {"type": "number"},
                                "lithology_interpretation": {"type": "array", "items": {"type": "string"}},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "workflow"],
                        },
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "workflow": {"type": "string", "const": "project"},
                                "project_yaml": {"type": "string"},
                                "wells_processed": {"type": "array", "items": {"type": "string"}},
                                "output_dir": {"type": "string"},
                                "status": {"type": "string"},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "workflow"],
                        },
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "workflow": {"type": "string", "const": "preview"},
                                "project_yaml": {"type": "string"},
                                "validation_passed": {"type": "boolean"},
                                "errors": {"type": "array", "items": {"type": "string"}},
                                "warnings": {"type": "array", "items": {"type": "string"}},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "workflow"],
                        },
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "workflow": {"type": "string", "const": "section_correlation"},
                                "section_ref": {"type": "string"},
                                "well_refs": {"type": "array", "items": {"type": "string"}},
                                "correlation_panel": {"type": "array", "items": {"type": "object"}},
                                "sequence_boundaries": {"type": "array", "items": {"type": "object"}},
                                "mode": {"type": "string"},
                                "synthetics_output": {"type": "boolean"},
                                "tie_qc_report": {"type": "object"},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "workflow"],
                        },
                    ],
                },
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
                "vertical_trend": {
                    "type": "string",
                    "enum": ["DEEPENING_UPWARD", "SHALLOWING_UPWARD", "STABLE_OR_AMBIGUOUS", "UNKNOWN"],
                },
                "litho_class": {"type": "string"},
                "strat_standard": {"type": "object"},
                "equations_used": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["claim_state", "provenance", "primary_artifact"],
        },
        "title": "Unified Sequence Stratigraphy Engine",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    # geox_evidence_reason — oneOf 4-phase discriminated union
    "geox_evidence_reason": {
        "description": (
            "Unified evidence synthesis, abduction, and contradiction engine (4 phases). "
            "synthesize: cross-domain evidence graph. "
            "abduct: generate and rank competing geological hypotheses. "
            "contradict: attack hypotheses and surface contradictions. "
            "full: synthesize→abduct→contradict in one call. "
            "Returns standard envelope with phase-specific artifacts."
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
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "phase": {"type": "string", "const": "synthesize"},
                                "evidence_graph": {"type": "object"},
                                "export_path": {"type": "string"},
                                "node_count": {"type": "number"},
                                "edge_count": {"type": "number"},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "phase"],
                        },
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "phase": {"type": "string", "const": "abduct"},
                                "hypotheses": {"type": "array", "items": {"type": "object"}},
                                "hypothesis_count": {"type": "number"},
                                "scale": {"type": "string"},
                                "depo_context": {"type": "string"},
                                "top_ranked_hypothesis": {"type": "object"},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "phase"],
                        },
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "phase": {"type": "string", "const": "contradict"},
                                "contradictions": {"type": "array", "items": {"type": "object"}},
                                "contradiction_count": {"type": "number"},
                                "surviving_hypotheses": {"type": "array", "items": {"type": "string"}},
                                "weakest_hypothesis": {"type": "string"},
                                "decision_support": {"type": "object"},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "phase"],
                        },
                        {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "phase": {"type": "string", "const": "full"},
                                "evidence_graph": {"type": "object"},
                                "hypotheses": {"type": "array", "items": {"type": "object"}},
                                "contradictions": {"type": "array", "items": {"type": "object"}},
                                "decision_support": {"type": "object"},
                                "next_best_actions": {"type": "array", "items": {"type": "string"}},
                                "claim_limits": {"type": "array", "items": {"type": "string"}},
                                "error_code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["tool", "phase"],
                        },
                    ],
                },
                "confidence_band": {"anyOf": [{"type": "object"}, {"type": "null"}]},
                "physics_guard": {"type": "object"},
                "uncertainty": {"type": "string"},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "humility_score": {"type": "number"},
                "maruah_flag": {"type": "object"},
                "diagnostics": {"type": "object"},
                "provenance": PROVENANCE_BLOCK,
                "perception_class": {"type": "string", "enum": PERCEPTION_CLASS_ENUM},
                "evidence_tag": {"type": "string", "enum": EVIDENCE_TAG_ENUM},
                "canon_9_touched": {"type": "array", "items": {"type": "string", "enum": CANON9_ENUM}},
                "equations_used": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["claim_state", "provenance", "primary_artifact"],
        },
        "title": "Unified Evidence Reasoning Engine",
        "annotations": {
            "readOnlyHint": True,
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
            },
            "required": ["claim_state", "qc_passed", "provenance"],
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
            },
            "required": ["claim_state", "evidence_refs", "provenance"],
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
            },
            "required": ["claim_state", "governance_status", "provenance"],
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
            },
            "required": ["claim_state", "perception_class", "provenance"],
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
            },
            "required": ["claim_state", "evidence_refs", "provenance"],
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
            },
            "required": ["provenance"],
        },
        "title": "System Registry Status",
        "annotations": {
            "readOnlyHint": True,
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
