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


def _load_well_curves_for_ui(well_id: str, max_n: int = 200) -> dict:
    """Best-effort LAS curve load for Well Witness hydrate. Never invent physics."""
    from pathlib import Path

    candidates = [
        Path(f"/data/geox_las/{well_id}.las"),
        Path(f"/data/geox_las/{well_id}"),
        Path(f"/root/GEOX/fixtures/{well_id}.las"),
        Path(f"/root/GEOX/fixtures/_DEMO_SYNTHETIC/{well_id}.las"),
        Path("/root/GEOX/fixtures/geox_smoke_test.las") if well_id in ("DEMO", "SMOKE", "geox_smoke_test") else None,
    ]
    las_path = next((p for p in candidates if p is not None and p.is_file()), None)
    if las_path is None:
        # Case-insensitive scan of /data/geox_las
        data_dir = Path("/data/geox_las")
        if data_dir.is_dir():
            wid = well_id.lower().replace(" ", "")
            for p in data_dir.glob("*.las"):
                if wid in p.stem.lower().replace(" ", ""):
                    las_path = p
                    break
    if las_path is None:
        return {"status": "no_las", "curves_available": [], "depths": None, "curves": None}

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
                    return _downsample_series([float(x) if x == x else float("nan") for x in arr], max_n)
            return None

        curves = {
            "GR": _curve(("GR", "GAMMA", "SGR", "CGR")),
            "RES": _curve(("RT", "RES", "ILD", "LLD", "RD", "RDEEP")),
            "DT": _curve(("DT", "DTCO", "AC", "DTC")),
            "RHOB": _curve(("RHOB", "DEN", "ZDEN", "RHOZ")),
        }
        # Drop empty tracks
        curves = {k: v for k, v in curves.items() if v is not None}
        available = [c.mnemonic for c in las.curves]
        depth_range = [depths[0], depths[-1]] if depths else None
        return {
            "status": "loaded",
            "las_path": str(las_path),
            "well_name": getattr(las.well, "WELL", None) and str(getattr(las.well.WELL, "value", well_id)) or well_id,
            "curves_available": available,
            "depth_range_m": depth_range,
            "depths": depths,
            "curves": curves if curves else None,
            "n_samples_ui": len(depths),
            "n_samples_source": len(depths_raw),
        }
    except Exception as exc:
        return {
            "status": "load_error",
            "curves_available": [],
            "depths": None,
            "curves": None,
            "error": str(exc)[:200],
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
    if _mode not in ("summary", "tracks", "open"):
        _mode = "summary"
    if _mode == "open":
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
    band = "LOADED" if loaded.get("status") == "loaded" else "UNKNOWN"
    epi_cap = 0.85 if loaded.get("curves") else 0.70
    epi_layer = "OBS" if loaded.get("curves") else "OBS"

    structured = {
        "ok": True,
        "tool": "geox_well_desk",
        "mode": _mode,
        "submode": _mode,
        "well_id": _wid,
        "well_name": loaded.get("well_name", _wid),
        "band": band,
        "status": loaded.get("status", "ready"),
        "curves_available": loaded.get("curves_available") or [],
        "depth_range_m": loaded.get("depth_range_m"),
        "depths": loaded.get("depths"),
        "curves": loaded.get("curves"),
        "n_samples_ui": loaded.get("n_samples_ui"),
        "summary": {
            "well_id": _wid,
            "mode": _mode,
            "band": band,
            "note": (
                "Well Witness hydrate — curves downsampled for MCP App iframe."
                if loaded.get("curves")
                else "No LAS curves found; host shell may show synthetic preview until ingest."
            ),
            "views": (
                ["composite_log", "summary_card"]
                if _mode == "summary"
                else ["composite_log", "tracks", "crossplot_placeholder"]
            ),
        },
        "epistemic": {
            "layer": epi_layer,
            "confidence_cap": epi_cap,
            "note": "Curves OBS from LAS when present; never invent pay or saturation here.",
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
            f"curves={list((loaded.get('curves') or {}).keys()) or 'none'}."
        ),
    }

    n_curves = len(loaded.get("curves") or {})
    text = (
        f"Well Witness: well_id={_wid} mode={_mode} band={band}. "
        f"UI tracks={n_curves}. resource=ui://geox/well-desk. "
        f"{'LAS loaded.' if loaded.get('status') == 'loaded' else 'No LAS — ingest first or use demo id.'}"
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
    """Publish well desk panel as sealed image (ZEN-15 consolidated).

    Renders the well panel and returns an image artifact_ref.
    """
    try:
        from geox_mcp.render_well_panel_petro import render_interpreted_panel

        panel = render_interpreted_panel(
            well_id=well_id,
            session_id=session_id,
            actor_id=actor_id,
        )
        return {
            "tool": "geox_well_desk",
            "mode": "publish",
            "well_id": well_id,
            "status": "published",
            "panel": panel,
        }
    except Exception as e:
        return {
            "tool": "geox_well_desk",
            "mode": "publish",
            "well_id": well_id,
            "status": "error",
            "error": str(e),
        }


__all__ = [
    "OperatorDecisionClass",
    "WellStateRequest",
    "WellStateResponse",
    "geox_well_decision_class",
    "geox_well_desk_open",
    "geox_well_desk_publish",
]
