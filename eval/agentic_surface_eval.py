"""
GEOX Agentic Surface Evaluation v2
=====================================
Three agent configurations on identical GEOX tasks.
Fixed: ZEN coverage uses domain-based routing, not name matching.

ZERO   — no tools, pure LLM reasoning
LEGACY — 89-tool flat surface (direct name match)
ZEN    — 7 unified dispatchers (domain-routed, mode-aware)
"""

from __future__ import annotations
import json, math, sys
from dataclasses import dataclass, field
from typing import Callable

# ─── Surface definitions ──────────────────────────────────────────────────────

LEGACY_89: list[str] = [
    "geox_well_ingest","geox_well_qc","geox_well_desurvey","geox_petrophysics",
    "geox_sequence","geox_surface_status","geox_seismic_ingest","geox_seismic_interpret",
    "geox_seismic_compute","geox_vision","geox_visual_understand","geox_visual_enhance",
    "geox_visual_generate_hypotheses","geox_rsi_interpret","geox_panel_d_render",
    "geox_physical_reality_interpret","geox_cognitive_rank_hypotheses","geox_segy_audit",
    "geox_well_tie","geox_3d_model","geox_basin","geox_claim","geox_evidence","geox_prospect",
    "geox_earthquake_catalog","geox_relief_ingest","geox_bathymetry_ingest","geox_heatflow_query",
    "geox_stress_query","geox_geochem_query","geox_plate_reconstruct","geox_paleomag_query",
    "geox_gravity_change_query","geox_ocean_query","geox_erddap_query","geox_climate_reanalysis",
    "geox_hydrology_query","geox_satellite_catalog","geox_uk_petroleum_query",
    "geox_geology_map_query","geox_space_weather","geox_simulate_accommodation",
    "geox_simulate_surfaces","geox_simulate_sequences","geox_simulate_routing",
    "geox_seismic_cognition","geox_geological_cognition_run","geox_well_tie_compute",
    "geox_tie_receipt","geox_tie_preflight","geox_3d_model_build","geox_wealth_bridge_run",
    "geox_spatial_intersection","geox_block_spec","geox_egs_query_entity",
    "geox_egs_query_claim","geox_egs_query_uncertainty","geox_egs_query_provenance",
    "geox_egs_claim_create","geox_egs_claim_challenge","geox_egs_evidence_attach",
    "geox_egs_evidence_reason","geox_egs_seismic_compute","geox_egs_rock_physics",
    "geox_egs_data_qc_bundle","geox_egs_scenario_audit","geox_geochem_kinetics",
    "geox_biostrat_parse","geox_biostrat_nn_age","geox_biostrat_ruling_check",
    "geox_biostrat_falsify","geox_macrostrat_calibrate","geox_geomechanics",
    "geox_gravity_screen","geox_judgment_preflight","geox_deep_time_state",
    "geox_atlas","geox_forbidden_claims_scan","geox_map_layers_list","geox_map_scene_plan",
    "geox_map_render_preview","geox_map_export_package","geox_contrast_detect",
    "geox_wealth_bridge","geox_subsurface_model","geox_render_audit","geox_wealth_consequence",
]
LEGACY_89 = list(dict.fromkeys(LEGACY_89))
while len(LEGACY_89) < 89:
    LEGACY_89.append(f"geox_legacy_tool_{len(LEGACY_89)+1}")
LEGACY_89 = LEGACY_89[:89]

ZEN_10: list[str] = [
    "geox_observe","geox_compute","geox_model","geox_interpret",
    "geox_spatial","geox_govern","geox_bridge",
    "geox_surface_status","geox_tie_receipt","geox_tie_preflight",
]

# ZEN domain routing table — which dispatcher handles which legacy name
ZEN_ROUTING: dict[str, str] = {
    # observe
    "geox_well_ingest":"geox_observe","geox_well_qc":"geox_observe",
    "geox_well_desurvey":"geox_observe","geox_seismic_ingest":"geox_observe",
    "geox_atlas":"geox_observe","geox_earthquake_catalog":"geox_observe",
    "geox_relief_ingest":"geox_observe","geox_bathymetry_ingest":"geox_observe",
    "geox_heatflow_query":"geox_observe","geox_stress_query":"geox_observe",
    "geox_geochem_query":"geox_observe","geox_plate_reconstruct":"geox_observe",
    "geox_paleomag_query":"geox_observe","geox_gravity_change_query":"geox_observe",
    "geox_ocean_query":"geox_observe","geox_erddap_query":"geox_observe",
    "geox_climate_reanalysis":"geox_observe","geox_hydrology_query":"geox_observe",
    "geox_satellite_catalog":"geox_observe","geox_uk_petroleum_query":"geox_observe",
    "geox_geology_map_query":"geox_observe","geox_space_weather":"geox_observe",
    "geox_deep_time_state":"geox_observe","geox_macrostrat_calibrate":"geox_observe",
    # compute
    "geox_petrophysics":"geox_compute","geox_geomechanics":"geox_compute",
    "geox_seismic_compute":"geox_compute","geox_egs_seismic_compute":"geox_compute",
    "geox_egs_rock_physics":"geox_compute","geox_geochem_kinetics":"geox_compute",
    "geox_gravity_screen":"geox_compute","geox_sequence":"geox_compute",
    # model
    "geox_basin":"geox_model","geox_simulate_accommodation":"geox_model",
    "geox_simulate_routing":"geox_model","geox_3d_model":"geox_model",
    "geox_3d_model_build":"geox_model","geox_simulate_sequences":"geox_model",
    "geox_simulate_surfaces":"geox_model","geox_subsurface_model":"geox_model",
    # interpret
    "geox_vision":"geox_interpret","geox_visual_understand":"geox_interpret",
    "geox_visual_enhance":"geox_interpret","geox_visual_generate_hypotheses":"geox_interpret",
    "geox_rsi_interpret":"geox_interpret","geox_panel_d_render":"geox_interpret",
    "geox_physical_reality_interpret":"geox_interpret",
    "geox_cognitive_rank_hypotheses":"geox_interpret",
    "geox_segy_audit":"geox_interpret","geox_well_tie":"geox_interpret",
    "geox_well_tie_compute":"geox_interpret","geox_seismic_interpret":"geox_interpret",
    "geox_seismic_cognition":"geox_interpret","geox_geological_cognition_run":"geox_interpret",
    "geox_biostrat_parse":"geox_interpret","geox_biostrat_nn_age":"geox_interpret",
    "geox_biostrat_ruling_check":"geox_interpret","geox_biostrat_falsify":"geox_interpret",
    "geox_contrast_detect":"geox_interpret",
    # spatial
    "geox_map_layers_list":"geox_spatial","geox_map_scene_plan":"geox_spatial",
    "geox_map_render_preview":"geox_spatial","geox_map_export_package":"geox_spatial",
    "geox_spatial_intersection":"geox_spatial","geox_block_spec":"geox_spatial",
    "geox_render_audit":"geox_spatial",
    # govern
    "geox_egs_query_entity":"geox_govern","geox_egs_query_claim":"geox_govern",
    "geox_egs_query_uncertainty":"geox_govern","geox_egs_query_provenance":"geox_govern",
    "geox_egs_claim_create":"geox_govern","geox_egs_claim_challenge":"geox_govern",
    "geox_egs_evidence_attach":"geox_govern","geox_egs_evidence_reason":"geox_govern",
    "geox_egs_data_qc_bundle":"geox_govern","geox_egs_scenario_audit":"geox_govern",
    "geox_judgment_preflight":"geox_govern","geox_forbidden_claims_scan":"geox_govern",
    "geox_claim":"geox_govern","geox_evidence":"geox_govern",
    # bridge
    "geox_wealth_bridge":"geox_bridge","geox_wealth_bridge_run":"geox_bridge",
    "geox_prospect":"geox_bridge","geox_wealth_consequence":"geox_bridge",
    # infra
    "geox_surface_status":"geox_surface_status",
    "geox_tie_receipt":"geox_tie_receipt","geox_tie_preflight":"geox_tie_preflight",
}

# ─── Task bank ────────────────────────────────────────────────────────────────

@dataclass
class Task:
    id: str
    domain: str
    intent: str
    legacy_correct: list[str]   # correct legacy tool names
    n_steps: int                # expected agentic steps (1 = single tool)
    complexity: int             # 1-3

TASKS: list[Task] = [
    Task("T01","well",        "Load LAS file PETRA-1, QC gamma-ray curve",
         ["geox_well_ingest","geox_well_qc"], 2, 2),
    Task("T02","petrophysics","Compute Vshale, porosity, Sw for zone A",
         ["geox_petrophysics"], 1, 1),
    Task("T03","seismic",     "Ingest SEG-Y, audit headers, compute amplitude attribute",
         ["geox_seismic_ingest","geox_segy_audit","geox_seismic_compute"], 3, 3),
    Task("T04","basin",       "Run accommodation model for Malay Basin Miocene",
         ["geox_simulate_accommodation","geox_basin"], 2, 2),
    Task("T05","governance",  "Create claim: Baram top at 3200m TVDSS, conf=0.85",
         ["geox_egs_claim_create"], 1, 1),
    Task("T06","spatial",     "Render map: SB-1 block with wells and fault polygons",
         ["geox_map_layers_list","geox_map_scene_plan","geox_map_render_preview"], 3, 2),
    Task("T07","interpret",   "Interpret seismic vision image for channel bodies",
         ["geox_vision","geox_visual_understand"], 2, 1),
    Task("T08","cross-domain","Well tie PETRA-1, rank seismic attributes, create best-fit claim",
         ["geox_well_tie_compute","geox_cognitive_rank_hypotheses","geox_egs_claim_create"], 3, 3),
    Task("T09","earth-surface","Query heatflow and stress data for Sarawak",
         ["geox_heatflow_query","geox_stress_query"], 2, 2),
    Task("T10","bridge",      "Run wealth bridge NPV exposure for PETRA prospect",
         ["geox_wealth_bridge_run","geox_prospect"], 2, 2),
]

# ─── Surface evaluation models ────────────────────────────────────────────────

def eval_zero(tasks: list[Task]) -> dict:
    """No tools. Agent reasons in natural language only."""
    rows = []
    for t in tasks:
        # Can reason about domain, cannot execute.
        # Hallucination risk HIGH for numerical tasks, low for conceptual.
        hallu_risk = 0.7 if t.complexity >= 2 else 0.5
        qual_score = 0.25  # can describe intent, cannot produce artifact
        G = 0.0            # execution=0 collapses APEX multiplicatively
        C = 0.20 * (1 - qual_score)  # A=0.20, P=0, X=0
        rows.append({
            "task_id": t.id, "domain": t.domain, "complexity": t.complexity,
            # Qualitative
            "can_execute": False,
            "hallucination_risk": round(hallu_risk, 2),
            "qualitative_score": round(qual_score, 2),
            # Quantitative
            "tool_calls_needed": 0,
            "tool_calls_correct": 0,
            "selection_precision": 0.0,
            "disambiguation_cost_steps": None,  # N/A
            "coverage": 0.0,
            # Quantum / APEX
            "G": round(G, 4),
            "C_dark": round(C, 4),
            "phi": 0.85,  # clean context, no noise
            "H_surface": 0.0,
            "dS_task": round(-math.log2(t.n_steps + 1), 4),  # reasoning entropy only
            "verdict": "SESAT",
        })
    summary = {
        "avg_G": 0.0,
        "avg_C_dark": round(sum(r["C_dark"] for r in rows) / len(rows), 4),
        "avg_precision": 0.0,
        "avg_coverage": 0.0,
        "avg_hallu_risk": round(sum(r["hallucination_risk"] for r in rows)/len(rows), 4),
        "avg_qual_score": round(sum(r["qualitative_score"] for r in rows)/len(rows), 4),
        "avg_disambig": None,
        "avg_dS": round(sum(r["dS_task"] for r in rows)/len(rows), 4),
        "avg_phi": 0.85,
        "lurus": 0, "sesat": 10, "bangang": 0,
        "H_surface": 0.0,
        "entropy_reduction_vs_zero": 0.0,
    }
    return {"surface": "ZERO (no tools)", "n_tools": 0, "summary": summary, "tasks": rows}


def eval_legacy(tasks: list[Task]) -> dict:
    """89-tool flat surface. Agent sees all names at once."""
    N = len(LEGACY_89)
    tool_set = set(LEGACY_89)
    # Shannon entropy of flat surface
    H_surface = math.log2(N)  # ~6.47 bits — agent must search 89 names

    rows = []
    for t in tasks:
        correct_tools = [c for c in t.legacy_correct if c in tool_set]
        n_correct = len(correct_tools)
        coverage = n_correct / len(t.legacy_correct)
        # Precision: probability correct tool selected on first try (uniform random)
        precision = n_correct / N
        # Disambiguation: expected draws before first hit (geometric expectation)
        disambig = N / max(n_correct, 1)

        # Phi degrades with context pollution: 89 names in prompt/schema
        phi = max(0.50, 0.92 - (N - 10) * 0.0025)  # 0.92 - 0.2 = 0.72

        # Accuracy: tools exist, can be called
        accuracy = coverage  # all correct tools reachable
        execution = 0.90 if n_correct > 0 else 0.0
        xenial = 0.90

        G = accuracy * precision * execution * xenial * phi
        C = accuracy * (1 - precision) * (1 - execution)

        # Qualitative
        hallu_risk = 0.30 if n_correct > 0 else 0.70  # risk of picking wrong tool
        # tool choice ambiguity is the real problem: e.g. geox_well_tie vs geox_well_tie_compute
        ambiguity_penalty = 0.15 * (1 + len([x for x in LEGACY_89 if t.domain in x]) / N)
        qual_score = min(0.90, coverage * 0.85 - ambiguity_penalty)

        # Entropy: task search space within 89 names
        H_task = math.log2(max(N / max(n_correct, 1), 1))
        dS = -H_task  # negative = reduction from surface to correct tool

        rows.append({
            "task_id": t.id, "domain": t.domain, "complexity": t.complexity,
            "can_execute": n_correct > 0,
            "hallucination_risk": round(hallu_risk, 2),
            "qualitative_score": round(max(qual_score, 0), 2),
            "tool_calls_needed": t.n_steps,
            "tool_calls_correct": n_correct,
            "selection_precision": round(precision, 4),
            "disambiguation_cost_steps": round(disambig, 1),
            "coverage": round(coverage, 4),
            "G": round(G, 4),
            "C_dark": round(C, 4),
            "phi": round(phi, 3),
            "H_surface": round(H_surface, 4),
            "dS_task": round(dS, 4),
            "verdict": "LURUS" if G >= 0.80 and C < 0.30 else
                       "BANGANG" if C >= 0.30 else "SESAT",
        })

    def avg(key):
        vals = [r[key] for r in rows if r[key] is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    summary = {
        "avg_G": avg("G"),
        "avg_C_dark": avg("C_dark"),
        "avg_precision": avg("selection_precision"),
        "avg_coverage": avg("coverage"),
        "avg_hallu_risk": avg("hallucination_risk"),
        "avg_qual_score": avg("qualitative_score"),
        "avg_disambig": avg("disambiguation_cost_steps"),
        "avg_dS": avg("dS_task"),
        "avg_phi": avg("phi"),
        "lurus": sum(1 for r in rows if r["verdict"]=="LURUS"),
        "sesat": sum(1 for r in rows if r["verdict"]=="SESAT"),
        "bangang": sum(1 for r in rows if r["verdict"]=="BANGANG"),
        "H_surface": round(H_surface, 4),
        "entropy_reduction_vs_zero": round(H_surface, 4),
    }
    return {"surface": "LEGACY-89", "n_tools": N, "summary": summary, "tasks": rows}


def eval_zen(tasks: list[Task]) -> dict:
    """10-tool ZEN surface. Agent routes to dispatcher → specifies mode."""
    N = len(ZEN_10)
    dispatcher_set = set(ZEN_10)
    H_surface = math.log2(N)  # ~3.32 bits — 10 names only

    rows = []
    for t in tasks:
        # Correct ZEN dispatchers for this task
        correct_dispatchers = list(dict.fromkeys(
            ZEN_ROUTING.get(c) for c in t.legacy_correct
            if ZEN_ROUTING.get(c) in dispatcher_set
        ))
        n_correct_d = len(correct_dispatchers)
        # Coverage: fraction of required legacy tools that have ZEN routing
        routed = [c for c in t.legacy_correct if ZEN_ROUTING.get(c) in dispatcher_set]
        coverage = len(routed) / len(t.legacy_correct)

        # Precision: much higher — only 10 choices, correct one is semantically obvious
        precision = n_correct_d / N
        # Disambiguation: first pick correct dispatcher (N=10), then mode within it
        # Mode disambiguation is CHEAP — each dispatcher ~8-25 modes, well-named
        dispatcher_disambig = N / max(n_correct_d, 1)
        # Mode is described by intent, so mode selection is near-deterministic
        mode_disambig = 2.5  # expected ~2.5 reads of mode list to find correct
        total_disambig = dispatcher_disambig + mode_disambig

        phi = 0.92  # ZEN surface: minimal schema noise, high signal

        accuracy = coverage
        execution = 0.92 if n_correct_d > 0 else 0.0  # slight uplift: mode guides execution
        xenial = 0.90

        G = accuracy * precision * execution * xenial * phi
        C = accuracy * (1 - precision) * (1 - execution)

        # Qualitative: ZEN forces intent articulation (mode= param)
        # Agent must think "what kind of operation is this?" → reduces hallucination
        hallu_risk = 0.15 if n_correct_d > 0 else 0.50
        # Mode-based dispatch forces semantic clarity
        qual_score = min(0.95, coverage * 0.92 + 0.05)

        # Entropy: task search space within 10 tools, then mode within dispatcher
        H_task_dispatcher = math.log2(max(N / max(n_correct_d, 1), 1))
        H_task_mode = math.log2(15)  # avg modes per dispatcher ~15
        # But mode is guided by intent — effective mode entropy is much lower
        H_mode_effective = math.log2(3)  # agent typically considers ~3 candidate modes
        dS = -(H_task_dispatcher + H_mode_effective)  # total entropy reduction

        rows.append({
            "task_id": t.id, "domain": t.domain, "complexity": t.complexity,
            "can_execute": n_correct_d > 0,
            "hallucination_risk": round(hallu_risk, 2),
            "qualitative_score": round(qual_score, 2),
            "tool_calls_needed": t.n_steps,
            "tool_calls_correct": n_correct_d,
            "selection_precision": round(precision, 4),
            "disambiguation_cost_steps": round(total_disambig, 1),
            "coverage": round(coverage, 4),
            "G": round(G, 4),
            "C_dark": round(C, 4),
            "phi": phi,
            "H_surface": round(H_surface, 4),
            "dS_task": round(dS, 4),
            "verdict": "LURUS" if G >= 0.80 and C < 0.30 else
                       "BANGANG" if C >= 0.30 else "SESAT",
        })

    def avg(key):
        vals = [r[key] for r in rows if r[key] is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    summary = {
        "avg_G": avg("G"),
        "avg_C_dark": avg("C_dark"),
        "avg_precision": avg("selection_precision"),
        "avg_coverage": avg("coverage"),
        "avg_hallu_risk": avg("hallucination_risk"),
        "avg_qual_score": avg("qualitative_score"),
        "avg_disambig": avg("disambiguation_cost_steps"),
        "avg_dS": avg("dS_task"),
        "avg_phi": avg("phi"),
        "lurus": sum(1 for r in rows if r["verdict"]=="LURUS"),
        "sesat": sum(1 for r in rows if r["verdict"]=="SESAT"),
        "bangang": sum(1 for r in rows if r["verdict"]=="BANGANG"),
        "H_surface": round(H_surface, 4),
        "entropy_reduction_vs_zero": round(H_surface, 4),
    }
    return {"surface": "ZEN-7 (+3 infra = 10)", "n_tools": N, "summary": summary, "tasks": rows}


# ─── Run + report ─────────────────────────────────────────────────────────────

def run():
    z = eval_zero(TASKS)
    l = eval_legacy(TASKS)
    q = eval_zen(TASKS)

    # Comparative summary table
    comparison = {
        "metric": ["n_tools","H_surface (bits)","avg_G (APEX)","avg_C_dark",
                   "avg_precision","avg_coverage","avg_disambig_steps",
                   "avg_phi","avg_hallu_risk","avg_qual_score",
                   "LURUS / SESAT","avg_dS (entropy Δ)"],
        "ZERO": [
            z["n_tools"], z["summary"]["H_surface"],
            z["summary"]["avg_G"], z["summary"]["avg_C_dark"],
            z["summary"]["avg_precision"], z["summary"]["avg_coverage"],
            "N/A", z["summary"]["avg_phi"],
            z["summary"]["avg_hallu_risk"], z["summary"]["avg_qual_score"],
            f"0 / {z['summary']['sesat']}", z["summary"]["avg_dS"],
        ],
        "LEGACY-89": [
            l["n_tools"], l["summary"]["H_surface"],
            l["summary"]["avg_G"], l["summary"]["avg_C_dark"],
            l["summary"]["avg_precision"], l["summary"]["avg_coverage"],
            l["summary"]["avg_disambig"], l["summary"]["avg_phi"],
            l["summary"]["avg_hallu_risk"], l["summary"]["avg_qual_score"],
            f"{l['summary']['lurus']} / {l['summary']['sesat']}", l["summary"]["avg_dS"],
        ],
        "ZEN-10": [
            q["n_tools"], q["summary"]["H_surface"],
            q["summary"]["avg_G"], q["summary"]["avg_C_dark"],
            q["summary"]["avg_precision"], q["summary"]["avg_coverage"],
            q["summary"]["avg_disambig"], q["summary"]["avg_phi"],
            q["summary"]["avg_hallu_risk"], q["summary"]["avg_qual_score"],
            f"{q['summary']['lurus']} / {q['summary']['sesat']}", q["summary"]["avg_dS"],
        ],
    }

    return {
        "comparison": comparison,
        "zero": z["summary"],
        "legacy": l["summary"],
        "zen": q["summary"],
        "task_detail": {
            "zero_tasks": z["tasks"],
            "legacy_tasks": l["tasks"],
            "zen_tasks": q["tasks"],
        }
    }

if __name__ == "__main__":
    out = run()
    print(json.dumps(out, indent=2))
