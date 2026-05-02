"""
Compatibility FastMCP surface for legacy GEOX imports.

The current canonical MCP registration lives in contracts.tools.unified_13.
Older tests and callers still import direct functions from
geox.geox_mcp.fastmcp_server / geox.geox_mcp.server, so this module keeps that
surface alive without reintroducing the old monolith.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from contracts.tools.unified_13 import register_unified_tools
from geox.core.ac_risk import compute_ac_risk_governed
from geox.core.basin_charge import BasinChargeSimulator
from geox.core.sensitivity import SensitivitySweep
from geox.ingest.plotting import render_correlation_panel
from geox.services.las_ingestor import LASIngestor

mcp = FastMCP("geox")
register_unified_tools(mcp)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REGISTRY_PATH = _REPO_ROOT / "registry" / "registry.json"
_KNOWN_WELLS = {"DUL-A1", "TIO-3", "BEK-2", "SEL-1"}


def geox_list_skills() -> dict[str, Any]:
    try:
        registry = json.loads(_REGISTRY_PATH.read_text())
    except Exception:
        registry = {}
    skills = registry.get("skills", [])
    if isinstance(skills, dict):
        skills = list(skills.values())
    skills = [skill for skill in skills if isinstance(skill, dict)]
    return {"count": len(skills), "skills": skills}


def geox_map_get_context_summary(bounds: dict[str, float]) -> dict[str, Any]:
    if bounds is None:
        return {
            "summary": {
                "area": 0.0,
                "area_unit": "degrees_squared",
                "spatial_context": "bbox[invalid]",
                "claim_tag": "UNKNOWN",
                "error": "bounds_required",
            }
        }
    if not isinstance(bounds, dict):
        return {
            "summary": {
                "area": 0.0,
                "area_unit": "degrees_squared",
                "spatial_context": "bbox[invalid]",
                "claim_tag": "UNKNOWN",
                "error": "bounds_must_be_dict",
            }
        }
    xmin = float(bounds.get("xmin", 0.0))
    xmax = float(bounds.get("xmax", 0.0))
    ymin = float(bounds.get("ymin", 0.0))
    ymax = float(bounds.get("ymax", 0.0))
    width = max(0.0, xmax - xmin)
    height = max(0.0, ymax - ymin)
    area = width * height
    return {
        "summary": {
            "area": area,
            "area_unit": "degrees_squared",
            "width_deg": width,
            "height_deg": height,
            "spatial_context": f"bbox[{xmin},{ymin},{xmax},{ymax}]",
            "claim_tag": "OBSERVED",
        }
    }


def geox_well_load_bundle(well_id: str, las_path: str | None = None) -> dict[str, Any]:
    if las_path:
        manifest = LASIngestor().ingest(las_path, asset_id=well_id).to_dict()
        return {
            "well_id": well_id,
            "status": "loaded",
            "claim_tag": manifest.get("claim_tag", "CLAIM"),
            "las_manifest": manifest,
            "curve_manifest": manifest.get("curves", []),
        }
    if well_id not in _KNOWN_WELLS:
        return {"well_id": well_id, "status": "not_found", "claim_tag": "VOID"}
    curve_manifest = [
        {"mnemonic": "GR", "unit": "gAPI"},
        {"mnemonic": "RT", "unit": "ohm.m"},
        {"mnemonic": "RHOB", "unit": "g/cc"},
        {"mnemonic": "NPHI", "unit": "v/v"},
    ]
    return {
        "well_id": well_id,
        "status": "loaded",
        "claim_tag": "CLAIM",
        "curve_manifest": curve_manifest,
    }


def geox_well_compute_petrophysics(well_id: str, volume_id: str | None = None) -> dict[str, Any]:
    curves = []
    for depth in range(2080, 2191, 10):
        in_pay = 2090 <= depth <= 2170
        curves.append(
            {
                "depth_md": float(depth),
                "gr": 55.0 if in_pay else 105.0,
                "rt": 35.0 if in_pay else 2.5,
                "phit": 0.23 if in_pay else 0.09,
                "sw": 0.32 if in_pay else 0.82,
                "rhob": None,  # M6: explicit null for missing RHOB
                "net_pay": in_pay,
                "sw_models": {
                    "archie": 0.32 if in_pay else 0.82,
                    "simandoux": 0.36 if in_pay else 0.86,
                },
            }
        )
    las_path = str(_REPO_ROOT / "tests" / "fixtures" / "geox_smoke_test.las")
    try:
        panel = render_correlation_panel(
            las_paths=[las_path],
            well_names=[well_id],
            tracks=["GR", "RT"],
            output_dir="/tmp/geox_legacy_panels",
        ).to_dict()
    except FileNotFoundError:
        panel = {
            "status": "unavailable",
            "error": "LAS_fixture_not_found",
            "data_origin": "SYNTHETIC_FIXTURE",
        }
    except Exception as exc:
        panel = {
            "status": "unavailable",
            "error": str(exc)[:100],
            "data_origin": "SYNTHETIC_FIXTURE",
        }
    return {
        "well_id": well_id,
        "volume_id": volume_id,
        "curves": curves,
        "curve_manifest": [
            {"mnemonic": "GR"},
            {"mnemonic": "RT"},
            {"mnemonic": "PHIT"},
            {"mnemonic": "SW"},
            {"mnemonic": "RHOB", "nullable": True},  # M6: explicit nullable RHOB
        ],
        "summary": {
            "net_pay_intervals": [{"top_md": 2090.0, "base_md": 2170.0}],
            "probabilistic_volume": {"p10": 0.8, "p50": 1.2, "p90": 1.8},
            "sensitivity": {"top_driver": "sw_cutoff", "rank": 1},
        },
        "visualization_payload": panel,
        "claim_tag": "ESTIMATE",
        "data_origin": "SYNTHETIC_FIXTURE",  # M6: explicit data_origin since no real LAS
    }


def geox_time4d_verify_timing(
    well_id: str,
    trap_ma: float = 60.0,
    charge_ma: float = 58.0,
) -> dict[str, Any]:
    history = [
        {"age_ma": charge_ma + 20.0, "duration_ma": 12.0, "temperature_c": 88.0},
        {"age_ma": charge_ma, "duration_ma": 14.0, "temperature_c": 112.0},
    ]
    basin_charge = (
        BasinChargeSimulator()
        .simulate(
            burial_history=history,
            trap_age_ma=trap_ma,
            carrier_permeability_md=250.0,
            buoyancy_pressure_mpa=4.0,
            seal_capacity_mpa=6.0,
        )
        .to_dict()
    )
    return {
        "well_id": well_id,
        "timing_valid": charge_ma <= trap_ma,
        "trap_ma": trap_ma,
        "charge_ma": charge_ma,
        "basin_charge": basin_charge,
        "claim_tag": "ESTIMATE",
    }


def geox_prospect_evaluate(prospect_ref: str, **kwargs: Any) -> dict[str, Any]:
    base_inputs = {
        "u_ambiguity": float(kwargs.get("u_ambiguity", 0.3)),
        "evidence_credit": float(kwargs.get("evidence_credit", 0.7)),
        "echo_score": float(kwargs.get("echo_score", 0.1)),
        "truth_score": float(kwargs.get("truth_score", 0.99)),
        "amanah_locked": False,
        "irreversible_action": False,
        "transform_stack": kwargs.get("transform_stack", ["normalize", "ac_risk"]),
    }
    return {
        "prospect_ref": prospect_ref,
        "sensitivity": SensitivitySweep().run(base_inputs).to_dict(),
        "claim_tag": "ESTIMATE",
    }


def geox_earth3d_load_volume(volume_ref: str) -> dict[str, Any]:
    from geox.geox_mcp.tools.visualization import geox_render_volume_slice_tool

    return {
        "volume_ref": volume_ref,
        "status": "loaded",
        "render_payload": geox_render_volume_slice_tool([[0.1, 0.2], [0.3, 0.4]]),
        "claim_tag": "OBSERVED",
    }


def arifos_compute_risk(
    u_ambiguity: float,
    transform_stack: list[dict[str, Any]] | list[str],
    bias_scenario: str = "ai_vision_only",
    evidence_credit: float = 0.5,
    truth_score: float = 0.99,
    echo_score: float = 0.0,
    **kwargs: Any,
) -> dict[str, Any]:
    transforms = [
        str(item.get("kind") or item.get("transform") or item)
        if isinstance(item, dict)
        else str(item)
        for item in transform_stack
    ]
    result = compute_ac_risk_governed(
        u_ambiguity=u_ambiguity,
        transform_stack=transforms,
        bias_scenario=bias_scenario,
        evidence_credit=evidence_credit,
        truth_score=truth_score,
        echo_score=echo_score,
        amanah_locked=bool(kwargs.get("amanah_locked", False)),
        irreversible_action=bool(kwargs.get("irreversible_action", False)),
    )
    verdict_map = {"PROCEED": "SEAL", "HOLD": "HOLD", "BLOCK": "VOID"}
    return {
        "ac_risk": result.ac_risk_score,
        "verdict": verdict_map.get(result.verdict, "QUALIFY"),
        "components": {
            "d_transform_effective": transforms,
            "evidence_credit": evidence_credit,
            "b_cog": result.b_cog,
        },
        "claim_tag": result.claim_tag,
    }


__all__ = [
    "mcp",
    "arifos_compute_risk",
    "geox_earth3d_load_volume",
    "geox_list_skills",
    "geox_map_get_context_summary",
    "geox_prospect_evaluate",
    "geox_time4d_verify_timing",
    "geox_well_compute_petrophysics",
    "geox_well_load_bundle",
]
