from typing import List, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX WITNESS CORE — v2026.05.22
# 10 tools. Physics-9 foundation. No interpretation. No narrative.
# ═══════════════════════════════════════════════════════════════════════════════

CANONICAL_PUBLIC_TOOLS: List[str] = [
    # Data witnessing
    "geox_data_ingest_bundle",
    "geox_data_qc_bundle",
    "geox_dst_ingest_test",
    # Physics-9 domain engines
    "geox_subsurface_generate_candidates",
    "geox_subsurface_verify_integrity",
    # Seismic physics
    "geox_seismic_well_tie_compute",
    "geox_time_depth_anchor",
    "geox_forward_model_synthetic",
    "geox_anomalous_contrast_detector",
    # Machine-checkable truth
    "geox_system_registry_status",
]

GEOX_TOOL_MANIFEST: List[Dict[str, Any]] = [
    {"name": "geox_data_ingest_bundle",             "axis": "observe",  "expose": True},
    {"name": "geox_data_qc_bundle",                 "axis": "verify",   "expose": True},
    {"name": "geox_dst_ingest_test",                "axis": "observe",  "expose": True},
    {"name": "geox_subsurface_generate_candidates", "axis": "reason",   "expose": True},
    {"name": "geox_subsurface_verify_integrity",    "axis": "verify",   "expose": True},
    {"name": "geox_seismic_well_tie_compute",       "axis": "reason",   "expose": True},
    {"name": "geox_time_depth_anchor",              "axis": "verify",   "expose": True},
    {"name": "geox_forward_model_synthetic",        "axis": "reason",   "expose": True},
    {"name": "geox_anomalous_contrast_detector",    "axis": "critique", "expose": True},
    {"name": "geox_system_registry_status",         "axis": "identity", "expose": True},
]

# Legacy aliases — hidden by default (GEOX_SHOW_LEGACY_ALIASES)
LEGACY_ALIAS_MAP: Dict[str, str] = {
    "geox_ingest_bundle": "geox_data_ingest_bundle",
    "geox_qc_bundle": "geox_data_qc_bundle",
    "geox_subsurface_candidates": "geox_subsurface_generate_candidates",
    "geox_petrophysics": "geox_subsurface_generate_candidates",
    "geox_seismic_tie": "geox_seismic_well_tie_compute",
    "geox_well_tie": "geox_seismic_well_tie_compute",
    "geox_td_anchor": "geox_time_depth_anchor",
    "geox_forward_model": "geox_forward_model_synthetic",
    "geox_anomalous_contrast": "geox_anomalous_contrast_detector",
    "geox_ac_detector": "geox_anomalous_contrast_detector",
    "geox_registry": "geox_system_registry_status",
}
