"""
contracts/tools/well_correlation.py — geox_well_correlation_panel MCP Tool
═══════════════════════════════════════════════════════════════════════════════

Thin MCP wrapper around geox.ingest.plotting.render_correlation_panel().
Geoscience logic lives in the engine; MCP tool is the delivery surface.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from fastmcp import FastMCP

logger = logging.getLogger("geox.well_correlation")


def register_well_correlation_tools(mcp: FastMCP) -> None:
    """
    Register geox_well_correlation_panel and supporting tools.
    """

    # ── geox_well_correlation_panel ──────────────────────────────────────────

    @mcp.tool(name="geox_well_correlation_panel")
    async def geox_well_correlation_panel(
        las_paths: list[str],
        well_names: Optional[list[str]] = None,
        tracks: Optional[list[str]] = None,
        depth_range: Optional[list[float]] = None,
        tops: Optional[dict[str, dict[str, float]]] = None,
        normalize: bool = True,
        basin_hint: Optional[str] = None,
        well_ids: Optional[list[str]] = None,
        output_dir: Optional[str] = None,
        output_png: Optional[str] = None,
        output_formats: Optional[list[str]] = None,
        plot_spec: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Generate a multi-well log correlation panel PNG.

        Accepts LAS file paths (absolute or relative to /data/ mount).
        Produces a PNG panel + CSV curve summary + QC warnings.

        GEOX Principle: produces visual evidence, not stratigraphic judgment.
        Every panel states: depth basis, datum correction status, claim state.

        Args:
            las_paths:   List of .las file paths.
                         Supports absolute paths or paths relative to /data/.
            well_names: Display names per well (optional, derived from filenames).
            tracks:     Curve tracks to display (default: ["GR", "RT"]).
                         Supported: GR, RT, RHOB, NPHI, DT, CAL, SP.
            depth_range: [min, max] depth filter in metres (optional).
            tops:       {well_id: {marker_name: depth_md}} for annotation lines.
            normalize:   Normalise tracks to 0–1 for display (default: True).
            basin_hint: Basin name for cross-basin guardrail.
                         If wells are from different basins, panel is labeled
                         EXPLORATORY_VISUALIZATION with appropriate warnings.
            well_ids:   Internal well IDs (optional, derived from filenames if None).
            output_dir: Directory for output files.
                         Default: /data/geox_panels (persistent, accessible on host).
            output_png: Exact PNG path to create. If provided, it wins over output_dir.
            output_formats: Static/audit outputs: png, svg, pdf, csv_summary, json_audit.
            plot_spec: Optional declarative PlotSpec. Executable/code fields are rejected.

        Returns:
            {
              "ok": true,
              "artifact": {"png_path": "...", "csv_summary_path": "..."},
              "wells_loaded": 4,
              "tracks_rendered": ["GR", "RT"],
              "curve_summary": [...],
              "qc_warnings": [...],
              "claim_state": "EXPLORATORY_VISUALIZATION",
              "vault_receipt": {...}
            }

            On failure:
            {
              "ok": false,
              "error_code": "NO_WELLS_LOADED | LAS_PARSE_FAILED | ...",
              "error_message": "...",
              "wells_failed": [...],
              "claim_state": "EXPLORATORY_VISUALIZATION"
            }
        """
        from geox.artifacts.writer import ArtifactValidationError, validate_output_path
        from geox.artifacts.las_sources import LASSourceError, materialize_las_source
        from geox.plot_specs.schemas import PlotSpecValidationError
        from geox.plot_specs.validators import build_well_panel_plot_spec
        from geox.renderers.base import RenderRequest
        from geox.renderers.matplotlib_logs import render_multiwell_correlation_panel

        # ── Input normalisation ─────────────────────────────────────────────
        if not las_paths:
            return _error_response(
                error_code="INVALID_INPUT",
                message="las_paths cannot be empty.",
                wells_failed=[],
            )

        # Resolve paths: accept absolute, /data/relative, or HTTPS URL
        resolved_paths: list[str] = []
        for index, p in enumerate(las_paths):
            try:
                resolved_paths.append(
                    materialize_las_source(p, artifact_id=f"panel_las_{index}")
                )
            except (FileNotFoundError, LASSourceError) as exc:
                logger.warning("Could not materialize LAS source %s: %s", p, exc)
                # Try as-is even if not found — let the engine report no wells loaded.
                resolved_paths.append(p)

        # Default output dir
        if output_png:
            try:
                output_png = validate_output_path(output_png, must_have_suffix=".png")
            except ArtifactValidationError as exc:
                return _error_response(
                    error_code="INVALID_OUTPUT_PATH",
                    message=str(exc),
                    wells_failed=[],
                )
            output_dir = os.path.dirname(output_png) or "."
        elif output_dir is None:
            output_dir = "/data/geox_panels"
        else:
            try:
                validate_output_path(
                    os.path.join(output_dir, "geox_probe.png"),
                    must_have_suffix=".png",
                )
            except ArtifactValidationError as exc:
                return _error_response(
                    error_code="INVALID_OUTPUT_PATH",
                    message=str(exc),
                    wells_failed=[],
                )

        try:
            spec = build_well_panel_plot_spec(
                las_paths=resolved_paths,
                tracks=tracks or ["GR", "RT"],
                depth_range=depth_range,
                output_formats=output_formats or ["png", "csv_summary", "json_audit"],
                raw_plot_spec=plot_spec,
            )
        except PlotSpecValidationError as exc:
            return _error_response(
                error_code="PLOTSPEC_REJECTED",
                message=str(exc),
                wells_failed=[],
            )

        # ── Render ───────────────────────────────────────────────────────────
        try:
            render_result = render_multiwell_correlation_panel(
                RenderRequest(
                    plot_spec=spec,
                    output_dir=output_dir,
                    output_png=output_png,
                    well_names=well_names,
                    tops=tops,
                    basin_hint=basin_hint,
                    well_ids=well_ids,
                    normalize=normalize,
                )
            )
            response = render_result.payload
            response["artifact"] = render_result.artifacts
            response["artifact_validation"] = render_result.validation
            response["plot_spec"] = spec.model_dump()
            response["facts"] = {
                "wells_loaded": response.get("wells_loaded", 0),
                "curves_rendered": len(response.get("tracks_rendered", [])),
                "depth_basis": spec.depth.basis,
                "renderer": spec.renderer.primary,
            }
            response["interpretation"] = (
                "Exploratory visualization. Human geologist review required."
            )
            response["unknown"] = [
                "Datum correction not applied unless source metadata explicitly supplies it.",
                "TVD/TVDSS unavailable unless supplied by source data.",
            ]
            response["parameters_used"] = {
                "renderer": spec.renderer.primary,
                "outputs": spec.outputs,
                "depth": spec.depth.model_dump(),
                "tracks": [track.model_dump() for track in spec.tracks],
            }
            response["telemetry"] = {
                "verdict": "SEAL" if render_result.ok else "PARTIAL",
                "confidence": "MED" if render_result.ok else "LOW",
                "claim_state": render_result.claim_state,
                "wells_loaded": response.get("wells_loaded", 0),
                "curves_rendered": len(response.get("tracks_rendered", [])),
                "renderer": spec.renderer.primary,
                "artifact_status": "VALID" if render_result.ok else "INVALID",
                "human_review_required": True,
            }
        except Exception as exc:
            logger.exception("geox_well_correlation_panel render failed")
            return _error_response(
                error_code="RENDER_FAILED",
                message=f"Panel render failed: {exc}",
                wells_failed=las_paths,
            )

        # Backward-compatible output_png relocation is handled by renderer.
        # FAIL-CLOSED: wells_loaded must be > 0 — blank panel is not an artifact
        wells_loaded = response.get("wells_loaded", 0)
        if wells_loaded == 0:
            return {
                "ok": False,
                "error_code": "NO_WELLS_LOADED",
                "error_message": (
                    "Correlation panel could not be generated because no LAS files were loaded."
                ),
                "wells_loaded": 0,
                "wells_failed": response.get("wells_failed", las_paths),
                "artifact": None,
                "warnings": response.get("qc_warnings", []),
                "claim_state": "NO_VALID_EVIDENCE",
            }

        if not render_result.ok:
            response["ok"] = False
            response["error_code"] = "ARTIFACT_VALIDATION_FAILED"
            response["error_message"] = "One or more required artifacts failed validation."

        # Vault receipt
        response["vault_receipt"] = _make_vault_receipt("geox_well_correlation_panel", response)

        return response

    # ── geox_las_curve_inventory ───────────────────────────────────────────

    @mcp.tool(name="geox_las_curve_inventory")
    async def geox_las_curve_inventory(
        las_path: str,
        well_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Inspect a LAS file and return its curve inventory.

        Does not load full curves — just reports what is present,
        null percentages, depth range, and unit information.
        Use this to verify LAS file structure before calling the panel tool.

        Args:
            las_path: Path to .las file (absolute or /data/-relative).
            well_id:  Optional well identifier.

        Returns:
            {
              "ok": true,
              "well_id": "...",
              "depth_curve": "DEPT",
              "depth_unit": "M",
              "depth_min": 102.0,
              "depth_max": 4638.5,
              "sample_count": 9074,
              "curves": {
                "GR": {"aliases": ["GR", "GAMMA"], "null_pct": 0.02, "unit": "gAPI"},
                "RT": {"aliases": ["RT", "ILD"], "null_pct": 0.15, "unit": "ohm.m"},
                ...
              },
              "qc_flags": ["RT: 15% null", "NPHI: not found"],
              "claim_state": "OBSERVED"
            }
        """
        from geox.artifacts.las_sources import LASSourceError, materialize_las_source
        from geox.ingest.plotting import CURVE_ALIASES, load_well_bundle

        # Resolve path
        try:
            resolved = materialize_las_source(las_path, artifact_id=well_id)
        except (FileNotFoundError, LASSourceError) as exc:
            return _error_response(
                error_code="FILE_NOT_FOUND",
                message=str(exc),
                wells_failed=[las_path],
            )

        try:
            bundle = load_well_bundle(resolved, well_id=well_id)
        except Exception as exc:
            return _error_response(
                error_code="LAS_PARSE_FAILED",
                message=f"Could not parse LAS file: {exc}",
                wells_failed=[las_path],
            )

        # Build alias map for found curves
        found_aliases: dict[str, list[str]] = {}
        for canon, aliases in CURVE_ALIASES.items():
            if canon in bundle.curves:
                found_aliases[canon] = aliases

        # QC flags
        qc_flags: list[str] = []
        for cname, np_pct in bundle.null_pct.items():
            if np_pct > 0.5:
                qc_flags.append(f"{cname}: {round(np_pct*100,1)}% null — low data quality.")
            elif np_pct > 0.1:
                qc_flags.append(f"{cname}: {round(np_pct*100,1)}% null.")

        # Unfound curves
        for canon in CURVE_ALIASES:
            if canon not in bundle.curves:
                qc_flags.append(f"{canon}: not found in LAS file.")

        return {
            "ok": True,
            "well_id": bundle.well_id,
            "source_path": bundle.source_path,
            "depth_curve": "DEPTH_MD",
            "depth_unit": bundle.depth_unit,
            "depth_min": bundle.depth_range[0],
            "depth_max": bundle.depth_range[1],
            "sample_count": bundle.n_samples,
            "curves": {
                canon: {
                    "aliases": found_aliases.get(canon, []),
                    "null_pct": bundle.null_pct.get(canon, 0.0),
                    "unit": _curve_unit(canon),
                }
                for canon in found_aliases
            },
            "qc_flags": qc_flags,
            "claim_state": bundle.claim_state,
            "vault_receipt": _make_vault_receipt("geox_las_curve_inventory", {
                "well_id": bundle.well_id,
                "n_curves": len(found_aliases),
            }),
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _error_response(error_code: str, message: str, wells_failed: list[str]) -> dict[str, Any]:
    return {
        "ok": False,
        "error_code": error_code,
        "error_message": message,
        "wells_failed": wells_failed,
        "wells_loaded": 0,
        "artifact": None,
        "claim_state": "NO_VALID_EVIDENCE",
    }


def _curve_unit(canon: str) -> str:
    return {
        "GR":   "gAPI",
        "RT":   "ohm.m",
        "RHOB": "g/cc",
        "NPHI": "v/v",
        "DT":   "us/ft",
        "CAL":  "in",
        "SP":   "mV",
    }.get(canon, "")


def _make_vault_receipt(tool_name: str, payload: dict) -> dict:
    try:
        payload_str = _json_deterministic(payload)
        digest = hashlib.sha256(payload_str.encode()).hexdigest()[:16]
        return {
            "vault": "VAULT999",
            "tool": tool_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hash": digest,
        }
    except Exception:
        return {
            "vault": "VAULT999",
            "tool": tool_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _json_deterministic(obj: dict) -> str:
    import json
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))
