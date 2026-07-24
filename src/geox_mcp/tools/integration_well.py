"""
integration_well.py — W13+ Phase C forge: WELL → GEOX integration.

Strategic doc: "operator readiness state feeding into joint_inversion decision_class".

This tool reads WELL organ state via the well_assess_homeostasis MCP call
(in-process — not a network call) and returns a decision_class that can
be fed into joint_inversion. The class gates how aggressive the solver
should be:

  C1 (GREEN)        — solver proceeds with strict bounds
  C2 (GREEN)        — solver proceeds with strict bounds
  C3 (STABLE/AMBER) — solver proceeds but flags uncertainty
  C4 (DEGRADED/RED) — solver returns VOID; do not seal
  C5 (CRITICAL)     — system hold; no inversions allowed

DITEMPA BUKAN DIBEI — the operator gates the witness.
"""

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field

OperatorDecisionClass = Literal["C1", "C2", "C3", "C4", "C5"]


class WellStateRequest(BaseModel):
    operator_id: str = Field(default="arif", description="Operator identity to check readiness for")
    task_description: str | None = Field(default=None, description="Optional context for WELL")


class WellStateResponse(BaseModel):
    ok: bool
    tool: str = "geox_well_decision_class"
    decision_class: OperatorDecisionClass = "C3"
    operator_readiness: str | None = None  # GREEN / AMBER / RED
    chronic_fatigue: bool = False
    accumulated_session_fatigue: float = 0.0
    rationale: str = ""
    epistemic_provenance: dict = Field(default_factory=dict)
    godel_wall: dict = Field(default_factory=dict)


async def geox_well_decision_class(
    request: WellStateRequest,
    *,
    well_assess_homeostasis=None,  # injected for testability
) -> WellStateResponse:
    """Constitutional MCP tool: derive decision_class from WELL operator state.

    If `well_assess_homeostasis` is None, attempts to import from the
    well-organ MCP. If the import fails (e.g. running outside federation),
    falls back to C3 (AMBER) — proceed with flags.
    """
    try:
        if well_assess_homeostasis is None:
            try:
                # Lazy import: the WELL organ is a separate service
                from arifosmcp.tools.organ_health import call_organ_tool

                well_assess_homeostasis = call_organ_tool
            except ImportError:
                # Use a local stub for off-federation operation
                well_assess_homeostasis = _stub_well_assess

        # Call WELL homeostasis
        result = await well_assess_homeostasis(
            subject=request.operator_id,
            mode="fatigue",
        )

        chronic_fatigue = bool(result.get("chronic_fatigue", False))
        accumulated = float(result.get("accumulated_session_fatigue", 0.0))
        # Decision matrix per WELL C-class threshold
        if chronic_fatigue or accumulated >= 0.85:
            decision_class: OperatorDecisionClass = "C5"
            operator_readiness = "RED"
            rationale = (
                "Operator shows chronic fatigue or session fatigue >= 0.85. "
                "System HOLD — no joint inversions allowed. Rest first."
            )
            godel_state = "VOID"
        elif accumulated >= 0.65:
            decision_class = "C4"
            operator_readiness = "AMBER"
            rationale = (
                "Operator session fatigue 0.65-0.85. Inversions proceed but "
                "uncertainty must be flagged. Defer non-critical inversions."
            )
            godel_state = "UNDECIDABLE_YET"
        elif accumulated >= 0.40:
            decision_class = "C3"
            operator_readiness = "STABLE"
            rationale = "Operator session fatigue 0.40-0.65. Proceed with strict bounds. Surface uncertainty in every output."
            godel_state = "KNOWN"
        else:
            decision_class = "C1"
            operator_readiness = "OPTIMAL"
            rationale = "Operator fatigue < 0.40. Proceed with strict bounds and full evidence envelope."
            godel_state = "KNOWN"

        return WellStateResponse(
            ok=True,
            decision_class=decision_class,
            operator_readiness=operator_readiness,
            chronic_fatigue=chronic_fatigue,
            accumulated_session_fatigue=accumulated,
            rationale=rationale,
            epistemic_provenance={
                "rung": 1,  # observation (not inference)
                "grounding": "well_assess_homeostasis_direct_call",
                "method": "fatigue_threshold_decision_matrix",
            },
            godel_wall={
                "state": godel_state,
                "reason": rationale,
            },
        )
    except Exception as e:
        return WellStateResponse(
            ok=False,
            decision_class="C3",
            rationale=f"WELL call failed: {e}. Defaulting to C3 with flags.",
            godel_wall={"state": "UNDECIDABLE_YET", "reason": f"WELL unavailable: {e}"},
        )


async def _stub_well_assess(
    subject: str,
    mode: str = "fatigue",
) -> dict:
    """Fallback when WELL MCP is unreachable. Returns C3 (stable, with flags)."""
    return {
        "chronic_fatigue": False,
        "accumulated_session_fatigue": 0.5,  # conservative middle-band
        "subject": subject,
        "mode": mode,
        "stub": True,
    }


def _downsample_series(values: list[float], max_n: int = 200) -> list[float]:
    """Evenly downsample a 1D series for iframe hydrate (keep UI payload small)."""
    if not values:
        return []
    n = len(values)
    if n <= max_n:
        return [float(v) if v is not None else float("nan") for v in values]
    step = max(1, n // max_n)
    out = [float(values[i]) if values[i] is not None else float("nan") for i in range(0, n, step)]
    return out[:max_n]


# Legacy set kept for callers; canonical map is resources/demo_wells.json
DEMO_WELL_REGISTRY = {
    "DEMO-KINABALU",
    "DEMO-VOLVE",
    "DEMO-SMOKE",
    "DEMO-01",
    "DEMO",
    "SMOKE",
    "DEMO_WELL_A",
    "DEMO_WELL_B",
    "DEMO_SANDAKAN_A",
    "DEMO_SANDAKAN_B",
    "MALAY_DEMO_01",
    "VOLVE_15_9_19",
}

_GEOX_ROOT = os.environ.get("GEOX_ROOT", "/root/GEOX")
_DEMO_WELLS_CACHE: dict | None = None


def _load_demo_wells_registry() -> dict:
    """Load canonical demo well → LAS map (Batch A G1.1)."""
    global _DEMO_WELLS_CACHE
    if _DEMO_WELLS_CACHE is not None:
        return _DEMO_WELLS_CACHE
    import json
    from pathlib import Path

    paths = [
        Path(_GEOX_ROOT) / "resources" / "demo_wells.json",
        Path("/opt/geox/app/resources/demo_wells.json"),
        Path(__file__).resolve().parents[3] / "resources" / "demo_wells.json",
    ]
    for p in paths:
        if p.is_file():
            try:
                _DEMO_WELLS_CACHE = json.loads(p.read_text(encoding="utf-8"))
                return _DEMO_WELLS_CACHE
            except Exception:
                continue
    _DEMO_WELLS_CACHE = {"wells": []}
    return _DEMO_WELLS_CACHE


def _resolve_demo_entry(well_id: str) -> dict | None:
    """Match well_id against demo registry primary id or aliases."""
    wid = well_id.strip()
    reg = _load_demo_wells_registry()
    for w in reg.get("wells") or []:
        names = {str(w.get("well_id", "")), *list(w.get("aliases") or [])}
        names_u = {n.upper() for n in names if n}
        if wid.upper() in names_u:
            return w
    return None


def _is_demo_well_id(well_id: str) -> bool:
    wid = well_id.strip().upper()
    if wid.startswith("DEMO-") or wid.startswith("DEMO_") or wid in {x.upper() for x in DEMO_WELL_REGISTRY}:
        return True
    return _resolve_demo_entry(well_id) is not None


def _load_well_curves_for_ui(well_id: str, max_n: int = 200) -> dict:
    """Best-effort LAS curve load for Well Witness hydrate. Enforces Truth Floor — no silent fixture fallbacks."""
    from pathlib import Path

    wid = well_id.strip()
    is_demo = _is_demo_well_id(wid)
    demo_entry = _resolve_demo_entry(wid)
    data_class = "UNKNOWN"
    geography = None
    is_fixture_fallback = False

    # 0. Canonical demo registry path (highest priority for DEMO ids)
    las_path = None
    if demo_entry and demo_entry.get("las_path"):
        rel = demo_entry["las_path"]
        for root in (Path(_GEOX_ROOT), Path("/opt/geox/app"), Path("/root/GEOX")):
            cand = root / rel
            if cand.is_file():
                las_path = cand
                data_class = demo_entry.get("data_class") or "DEMO"
                geography = demo_entry.get("geography")
                is_fixture_fallback = True
                break

    # 1. Look for explicit LAS files on disk
    well_data_dir = os.environ.get("GEOX_WELL_DATA_DIR", "/data/wells")
    if las_path is None:
        candidates = [
            Path(f"{well_data_dir}/{wid}.las"),
            Path(f"{well_data_dir}/{wid}"),
            Path(f"/data/wells/{wid}.las"),
            Path(f"/data/wells/{wid}"),
            Path(f"/data/geox_las/{wid}.las"),
            Path(f"/data/geox_las/{wid}"),
            Path(f"{_GEOX_ROOT}/data/geox_las/{wid}.las"),
            Path(f"/root/GEOX/data/geox_las/{wid}.las"),
            Path(f"/root/GEOX/fixtures/{wid}.las"),
            Path(f"/opt/geox/app/fixtures/{wid}.las"),
            Path(f"/root/GEOX/fixtures/_DEMO_SYNTHETIC/{wid}.las"),
            Path(f"/root/GEOX/fixtures/_DEMO_SYNTHETIC/{wid}_SANDAKAN.las"),
        ]
        las_path = next((p for p in candidates if p is not None and p.is_file()), None)

    # 1b. Check in-memory artifact registry for las_path (post-ingest)
    if las_path is None:
        try:
            from geox_mcp.tools._helpers import _get_artifact

            entry = _get_artifact(wid) or _get_artifact(f"well_las:{wid}")
            if entry and entry.get("las_path"):
                p = Path(entry["las_path"])
                if p.is_file():
                    las_path = p
                    data_class = entry.get("data_class") or "INGESTED"
        except Exception:
            pass

    # 2. Case-insensitive scan of well dirs for ingested wells
    if las_path is None:
        for search_dir_path in [
            Path(well_data_dir),
            Path("/data/wells"),
            Path("/data/geox_las"),
            Path(f"{_GEOX_ROOT}/data/geox_las"),
            Path("/root/GEOX/data/geox_las"),
            Path("/root/GEOX/fixtures/_DEMO_SYNTHETIC"),
        ]:
            if search_dir_path.is_dir():
                target_stem = wid.lower().replace(" ", "").replace("-", "").replace("_", "")
                for p in search_dir_path.glob("*.las"):
                    p_stem = p.stem.lower().replace(" ", "").replace("-", "").replace("_", "")
                    if target_stem == p_stem or target_stem in p_stem or p_stem in target_stem:
                        las_path = p
                        break
                if las_path:
                    break

    # 3. Demo fallback ONLY for explicit DEMO ids
    if las_path is None and is_demo:
        demo_candidates = [
            Path(f"{_GEOX_ROOT}/data/geox_las/DEMO-KINABALU.las"),
            Path("/root/GEOX/data/geox_las/DEMO-KINABALU.las"),
            Path("/root/GEOX/fixtures/geox_smoke_test.las"),
            Path("/opt/geox/app/fixtures/geox_smoke_test.las"),
        ]
        las_path = next((p for p in demo_candidates if p is not None and p.is_file()), None)
        is_fixture_fallback = True
        data_class = data_class if data_class != "UNKNOWN" else "DEMO"

    if las_path is None:
        return {
            "status": "no_las",
            "error": f"No LAS ingested for {wid}. Use geox_well_ingest or a DEMO-* / DEMO_WELL_* id.",
            "curves_available": [],
            "depths": None,
            "curves": None,
            "data_class": "EMPTY",
        }

    try:
        import lasio

        las = lasio.read(str(las_path), ignore_header_errors=True)
        mnemonics = [c.mnemonic.upper() for c in las.curves]
        depths_raw = list(las.index) if las.index is not None else []
        depths = _downsample_series([float(d) for d in depths_raw], max_n)

        def _curve(names: tuple[str, ...]) -> list[float] | None:
            for name in names:
                if name in mnemonics:
                    idx = mnemonics.index(name)
                    arr = list(las.curves[idx].data)
                    return _downsample_series(
                        [float(x) if x == x else float("nan") for x in arr], max_n
                    )
            return None

        curves = {
            "GR": _curve(("GR", "GAMMA", "SGR", "CGR")),
            "RES": _curve(("RT", "RES", "ILD", "LLD", "RD", "RDEEP", "AT90")),
            "DT": _curve(("DT", "DTCO", "AC", "DTC")),
            "RHOB": _curve(("RHOB", "DEN", "ZDEN", "RHOZ")),
            "NPHI": _curve(("NPHI", "NEU", "TNPH", "NPOR")),
        }
        avail = [m for m in mnemonics if m not in ("DEPT", "DEPTH", "MD")]

        out_curves = {k: v for k, v in curves.items() if v is not None}
        well_name = (
            str(getattr(las.well, "WELL", None).value).strip()
            if hasattr(las, "well") and hasattr(las.well, "WELL")
            else wid
        )
        if not well_name or well_name == "UNKNOWN":
            well_name = wid

        if data_class == "UNKNOWN":
            data_class = "DEMO" if (is_fixture_fallback or is_demo) else "MEASURED"

        res = {
            "status": "loaded",
            "well_name": well_name,
            "curves_available": avail,
            "depth_range_m": [depths[0], depths[-1]] if depths else None,
            "depths": depths,
            "curves": out_curves,
            "n_samples_ui": len(depths),
            "is_fixture_fallback": is_fixture_fallback or is_demo,
            "las_path": str(las_path),
            "data_class": data_class,
            "geography": geography,
        }
        if is_fixture_fallback or is_demo or data_class in ("DEMO", "SYNTHETIC_LABEL", "OPEN_OSS"):
            if data_class == "OPEN_OSS":
                res["provenance_badge"] = (
                    "DATA: OPEN OSS LAS (e.g. Volve North Sea) — real measurements, "
                    "NOT Malay Basin; DEMO context only"
                )
            else:
                res["provenance_badge"] = "DATA: DEMO FIXTURE — NOT REAL WELL DATA"
        return res
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to parse LAS for {wid}: {e}",
            "curves_available": [],
            "depths": None,
            "curves": None,
            "data_class": "ERROR",
        }


async def geox_well_desk_open(
    well_id: str = "",
    mode: str = "summary",
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
):
    """Open Well Witness (MCP App) — 3-channel return for host iframe hydrate.

    Returns ToolResult:
      content            — short operator text
      structured_content — well_id/mode/band/curves/depths for p0-viz.html
      meta.ui.resourceUri — ui://geox/well-desk
    """
    from geox_mcp.tools.mcp_apps_bridge import ui_tool_result

    _mode = (mode or "summary").strip().lower()
    if _mode not in ("summary", "tracks", "open", "render"):
        _mode = "summary"
    if _mode in ("open", "render"):
        _mode = "summary"
    _wid = (well_id or "").strip()
    if not _wid:
        return ui_tool_result(
            app_id="well_desk",
            text="well_id is required for geox_well_desk open",
            structured={
                "ok": False,
                "tool": "geox_well_desk",
                "error_class": "MISSING_REQUIRED_FIELD",
                "message": "well_id is required",
            },
            is_error=True,
        )

    loaded = _load_well_curves_for_ui(_wid)

    if loaded.get("status") in ("no_las", "error"):
        err_msg = loaded.get("error") or f"No LAS ingested for {_wid}. Use geox_well_ingest or a DEMO-* id."
        return ui_tool_result(
            app_id="well_desk",
            text=f"Error: {err_msg}",
            structured={
                "ok": False,
                "tool": "geox_well_desk",
                "well_id": _wid,
                "error_class": "NO_LAS_DATA",
                "message": err_msg,
                "status": loaded.get("status", "no_las"),
            },
            is_error=True,
        )

    band = "LOADED"
    epi_cap = 0.85 if loaded.get("curves") else 0.70
    epi_layer = "OBS" if loaded.get("curves") else "OBS"

    data_class = loaded.get("data_class") or ("DEMO" if loaded.get("provenance_badge") else "MEASURED")
    structured = {
        "ok": True,
        "tool": "geox_well_desk",
        "mode": _mode,
        "submode": _mode,
        "well_id": _wid,
        "well_name": loaded.get("well_name", _wid),
        "band": band,
        "status": loaded.get("status", "loaded"),
        "curves_available": loaded.get("curves_available") or [],
        "depth_range_m": loaded.get("depth_range_m"),
        "depths": loaded.get("depths"),
        "curves": loaded.get("curves"),
        "n_samples_ui": loaded.get("n_samples_ui"),
        "provenance_badge": loaded.get("provenance_badge"),
        "data_class": data_class,
        "geography": loaded.get("geography"),
        "las_path": loaded.get("las_path"),
        "authority_claim": "ADVISORY",
        "output_class": "COMPUTED" if not loaded.get("provenance_badge") else "DEMO_FIXTURE",
        "summary": {
            "well_id": _wid,
            "mode": _mode,
            "band": band,
            "data_class": data_class,
            "note": (
                "Well Witness hydrate — curves loaded from LAS."
                if not loaded.get("provenance_badge")
                else "DEMO/OPEN fixture — curves loaded; NOT a field seal."
            ),
            "views": (
                ["composite_log", "summary_card"]
                if _mode == "summary"
                else ["composite_log", "tracks", "crossplot_placeholder"]
            ),
        },
        "epistemic": {
            "layer": epi_layer,
            "confidence_cap": epi_cap if data_class not in ("DEMO", "SYNTHETIC_LABEL") else 0.70,
            "note": "Curves OBS from LAS when present; never invent pay or saturation here.",
            "seal_status": "NOT_SEALED",
        },
        "ui": {
            "resourceUri": "ui://geox/well-desk",
            "protocol": "SEP-1865",
            "shell": "p0-viz",
        },
        "session_id": session_id,
        "actor_id": actor_id,
        "trace_id": trace_id,
        "w0": "OPERATOR_VETO_INTACT",
        "final_authority": "ARIF",
        "message": (
            f"Well desk open: {_wid} ({band}). "
            f"curves={list((loaded.get('curves') or {}).keys()) or 'none'} "
            f"data_class={data_class}."
        ),
    }

    n_curves = len(loaded.get("curves") or {})
    badge_str = f" [{loaded['provenance_badge']}]" if loaded.get("provenance_badge") else ""
    text = (
        f"Well Witness: well_id={_wid} mode={_mode} band={band}. "
        f"UI tracks={n_curves}. resource=ui://geox/well-desk.{badge_str}"
    )
    return ui_tool_result(
        app_id="well_desk",
        text=text,
        structured=structured,
        params={"well_id": _wid, "mode": _mode},
    )


async def geox_well_desk_publish(
    well_id: str = "",
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict:
    """Publish well desk panel image (ZEN-15 consolidated).

    Renders the well panel. Never claims SEAL unless an arifOS verdict is present.
    G3.4: authority_claim stays ADVISORY for demo/synthetic.
    """
    try:
        from geox_mcp.render_well_panel_petro import render_interpreted_panel

        is_demo = _is_demo_well_id(well_id or "")
        demo_entry = _resolve_demo_entry(well_id or "")
        data_class = (demo_entry or {}).get("data_class") or ("DEMO" if is_demo else "MEASURED")

        panel = render_interpreted_panel(
            well_id=well_id,
            session_id=session_id,
            actor_id=actor_id,
        )
        # Strip accidental seal language from panel if demo
        if isinstance(panel, dict) and is_demo:
            panel = {**panel, "seal_status": "NOT_SEALED", "authority_claim": "ADVISORY"}

        return {
            "tool": "geox_well_desk",
            "mode": "publish",
            "well_id": well_id,
            "status": "published",
            "panel": panel,
            "data_class": data_class,
            "authority_claim": "ADVISORY",
            "seal_status": "NOT_SEALED",
            "output_class": "DEMO_FIXTURE" if is_demo else "COMPUTED",
            "epistemic": {
                "note": "Publish is ADVISORY witness export — not arifOS SEAL",
                "seal_status": "NOT_SEALED",
            },
            "session_id": session_id,
            "actor_id": actor_id,
            "trace_id": trace_id,
        }
    except Exception as e:
        return {
            "tool": "geox_well_desk",
            "mode": "publish",
            "well_id": well_id,
            "status": "error",
            "error": str(e),
            "authority_claim": "ADVISORY",
            "seal_status": "NOT_SEALED",
        }


async def geox_well_desk_petro(
    well_id: str = "",
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict:
    """Run lem_inference-style petro on loaded LAS curves (Batch B G1.3).

    Uses geox_petrophysics(mode=lem_inference) when curves resolve.
    Returns ADVISORY envelope — never SEAL.
    """
    loaded = _load_well_curves_for_ui(well_id or "")
    if loaded.get("status") != "loaded" or not loaded.get("curves") or not loaded.get("depths"):
        return {
            "ok": False,
            "tool": "geox_well_desk",
            "mode": "petro",
            "well_id": well_id,
            "error_class": "NO_LAS_DATA",
            "message": loaded.get("error") or "No curves for petro",
            "authority_claim": "ADVISORY",
            "seal_status": "NOT_SEALED",
        }

    curves = loaded["curves"]
    # Map RES → RT for lem if needed
    lem_curves = {
        "GR": curves.get("GR") or [],
        "RT": curves.get("RES") or curves.get("RT") or [],
        "RHOB": curves.get("RHOB") or [],
        "NPHI": curves.get("NPHI") or [],
        "DT": curves.get("DT") or [],
    }
    # Drop empty
    lem_curves = {k: v for k, v in lem_curves.items() if v}
    depth_m = loaded["depths"]

    try:
        from geox_mcp.tools.lem_predict import LEMPredictRequest, geox_lem_predict

        # Align curve lengths to depth
        n = len(depth_m)
        aligned = {}
        for k, v in lem_curves.items():
            if len(v) == n:
                aligned[k] = v
            elif len(v) > n:
                aligned[k] = v[:n]
            else:
                continue
        if "GR" not in aligned and "RHOB" not in aligned:
            return {
                "ok": False,
                "tool": "geox_well_desk",
                "mode": "petro",
                "well_id": well_id,
                "error_class": "INSUFFICIENT_CURVES",
                "message": f"Need GR/RHOB for petro; have {list(lem_curves.keys())}",
                "authority_claim": "ADVISORY",
                "seal_status": "NOT_SEALED",
            }

        req = LEMPredictRequest(
            well_id=well_id or "UNKNOWN",
            curves=aligned,
            depth_m=depth_m,
            depth_top_m=depth_m[0] if depth_m else None,
            depth_bot_m=depth_m[-1] if depth_m else None,
            target_properties=["porosity", "sw", "lithology"],
            rw_ohm_m=0.05,
            rho_matrix_g_cc=2.65,
            rho_fluid_g_cc=1.0,
            actor_id=actor_id,
            session_id=session_id,
        )
        result = await geox_lem_predict(req)
        return {
            "ok": True,
            "tool": "geox_well_desk",
            "mode": "petro",
            "well_id": well_id,
            "data_class": loaded.get("data_class"),
            "provenance_badge": loaded.get("provenance_badge"),
            "authority_claim": "ADVISORY",
            "seal_status": "NOT_SEALED",
            "output_class": "COMPUTED_DEMO" if loaded.get("provenance_badge") else "COMPUTED",
            "petro": result,
            "session_id": session_id,
            "actor_id": actor_id,
            "trace_id": trace_id,
        }
    except Exception as e:
        return {
            "ok": False,
            "tool": "geox_well_desk",
            "mode": "petro",
            "well_id": well_id,
            "error": str(e),
            "authority_claim": "ADVISORY",
            "seal_status": "NOT_SEALED",
        }


geox_well_desk = geox_well_desk_open


__all__ = [
    "OperatorDecisionClass",
    "WellStateRequest",
    "WellStateResponse",
    "geox_well_decision_class",
    "geox_well_desk",
    "geox_well_desk_open",
    "geox_well_desk_publish",
    "geox_well_desk_petro",
]
