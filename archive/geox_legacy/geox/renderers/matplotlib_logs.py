"""Matplotlib-backed well-log renderer adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from geox.artifacts.writer import validate_output_path, verify_artifact_pack, write_json_audit
from geox.ingest.plotting import render_correlation_panel
from geox.renderers.base import RenderRequest, RenderResult


def render_multiwell_correlation_panel(request: RenderRequest) -> RenderResult:
    spec = request.plot_spec
    output_png = (
        validate_output_path(request.output_png, must_have_suffix=".png")
        if request.output_png
        else None
    )
    output_dir = str(Path(output_png).parent) if output_png else request.output_dir

    panel_result = render_correlation_panel(
        las_paths=spec.las_paths,
        well_names=request.well_names,
        tracks=spec.canonical_tracks,
        output_dir=output_dir,
        depth_range=spec.depth.range,
        tops=request.tops,
        normalize=request.normalize,
        basin_hint=request.basin_hint,
        well_ids=request.well_ids,
        output_formats=spec.outputs,
    )
    payload = panel_result.to_dict()
    artifacts = dict(payload.get("artifact") or {})

    if output_png and panel_result.ok:
        produced_png = artifacts.get("png_path")
        if produced_png and Path(produced_png).resolve() != Path(output_png).resolve():
            Path(produced_png).replace(output_png)
            artifacts["png_path"] = output_png
            produced_csv = artifacts.get("csv_summary_path")
            if produced_csv and Path(produced_csv).exists():
                csv_target = str(Path(output_png).with_suffix(".csv"))
                Path(produced_csv).replace(csv_target)
                artifacts["csv_summary_path"] = csv_target
            for key, suffix in (("svg_path", ".svg"), ("pdf_path", ".pdf")):
                produced = artifacts.get(key)
                if produced and Path(produced).exists():
                    target = str(Path(output_png).with_suffix(suffix))
                    Path(produced).replace(target)
                    artifacts[key] = target

    validation = verify_artifact_pack(artifacts)
    audit_path = None
    if "json_audit" in spec.outputs and panel_result.ok:
        audit_path = write_json_audit(
            str(Path(artifacts["png_path"]).with_suffix(".json")),
            {
                "plot_spec": spec.model_dump(),
                "result": payload,
                "artifact_validation": validation,
                "facts": {
                    "wells_loaded": panel_result.wells_loaded,
                    "tracks_rendered": panel_result.tracks_rendered,
                },
                "interpretation": (
                    "Exploratory well-log visualization only; human geologist review required."
                ),
                "unknown": [
                    "Datum correction not applied",
                    "TVD/TVDSS unavailable unless explicitly supplied",
                ],
            },
        )
        artifacts["json_audit_path"] = audit_path
        validation = verify_artifact_pack(artifacts)

    return RenderResult(
        ok=panel_result.ok
        and _pack_is_valid(validation, required=("png_path", "csv_summary_path")),
        artifacts=artifacts,
        validation=validation,
        audit_path=audit_path,
        warnings=panel_result.qc_warnings,
        claim_state=panel_result.claim_state,
        payload=payload,
    )


def _pack_is_valid(validation: dict[str, dict[str, Any]], required: tuple[str, ...]) -> bool:
    for key in required:
        item = validation.get(key)
        if not item or item.get("status") != "VALID":
            return False
    return True
