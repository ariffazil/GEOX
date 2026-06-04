"""
GEOX Well Stratigraphy — MCP Tool Registration
═══════════════════════════════════════════════════════════════════════════════

Registers the generalized L1-L3 sequence stratigraphy pipeline as GEOX MCP tools.

Config-driven: accepts a project.yaml with wells, intervals, and parameters.
No hardcoded wells, intervals, or depositional environments.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from typing import Any

import yaml
from fastmcp import FastMCP

from geox_core.enums.statuses import get_standard_envelope

logger = logging.getLogger("geox.stratigraphy.mcp")

TOOL_NAMES = [
    "geox_stratigraphy_run_pipeline",
    "geox_stratigraphy_preview_config",
]


def register_stratigraphy_tools(mcp: FastMCP) -> None:
    """Register stratigraphy pipeline tools on the MCP instance."""

    @mcp.tool()
    async def geox_stratigraphy_run_pipeline(
        project_yaml: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """
        Run the full L1-L3 sequence stratigraphy pipeline.

        Accepts a YAML project configuration defining wells, intervals,
        depositional environments, and pipeline parameters.

        Returns XLSX (5 sheets) + per-well PNG panels + correlation panel.

        Parameters
        ----------
        project_yaml : str
            YAML string defining the project configuration:
            ```yaml
            project: KL2
            bin_size_m: 10.0
            min_package_thickness_m: 20.0
            p50_shift_thresh_gapi: 15.0
            gr_cut_api: 75.0
            gr_min_api: 0.0
            gr_max_api: 150.0
            well_order:
              - WELL-1
              - WELL-2
            wells:
              - name: WELL-1
                path: /data/WELL-1.LAS
                format: LAS
              - name: WELL-2
                path: /data/WELL-2.csv
                format: CSV_LAS
            intervals:
              WELL-1:
                - zone: NN11
                  top: 1000
                  base: 2000
                  depo_env: UBT
              WELL-2:
                - zone: NN10
                  top: 500
                  base: 1500
                  depo_env: HIN
            ```
        output_dir : str, optional
            Output directory for generated files. Defaults to temp directory.

        Returns
        -------
        dict with summary: project, n_wells, n_bins, n_packages,
            tract_distribution, motif_distribution, outputs (file paths), status.
        """
        try:
            config_dict = yaml.safe_load(project_yaml)
        except Exception as e:
            return get_standard_envelope(
                primary_artifact={"error": f"Invalid YAML: {e}"},
                tool_class="compute",
                execution_status="ERROR",
                governance_status="VOID",
                artifact_status="REJECTED",
                claim_tag="VOID",
                claim_state="VOID",
            )

        from geox_core.well.stratigraphy.config import ProjectConfig, ProjectInterval, WellSource

        try:
            wells = [WellSource(**w) for w in config_dict.get("wells", [])]
            intervals = {}
            for well_id, ivls in config_dict.get("intervals", {}).items():
                intervals[well_id] = [ProjectInterval(**i) for i in ivls]

            config = ProjectConfig(
                project=config_dict.get("project", "Untitled"),
                bin_size_m=config_dict.get("bin_size_m", 10.0),
                min_package_thickness_m=config_dict.get("min_package_thickness_m", 20.0),
                p50_shift_thresh_gapi=config_dict.get("p50_shift_thresh_gapi", 15.0),
                gr_cut_api=config_dict.get("gr_cut_api", 75.0),
                gr_min_api=config_dict.get("gr_min_api", 0.0),
                gr_max_api=config_dict.get("gr_max_api", 150.0),
                gr_sand_api=config_dict.get("gr_sand_api", 35.0),
                gr_silt_api=config_dict.get("gr_silt_api", 65.0),
                gr_shaly_api=config_dict.get("gr_shaly_api", 90.0),
                well_order=config_dict.get("well_order", []),
                wells=wells,
                intervals=intervals,
                output_dir=output_dir or config_dict.get("output_dir", "/tmp/stratigraphy_output"),
                dpi=config_dict.get("dpi", 200),
                dpi_correlation=config_dict.get("dpi_correlation", 180),
            )
        except Exception as e:
            return get_standard_envelope(
                primary_artifact={"error": f"Config validation error: {e}"},
                tool_class="compute",
                execution_status="ERROR",
                governance_status="VOID",
                artifact_status="REJECTED",
                claim_tag="VOID",
                claim_state="VOID",
            )

        from geox_core.well.stratigraphy.pipeline import run_pipeline

        try:
            result = run_pipeline(
                config,
                output_dir=config.output_dir,
                dpi=config.dpi,
                dpi_corr=config.dpi_correlation,
            )
            return get_standard_envelope(
                primary_artifact=result,
                tool_class="compute",
                execution_status="SUCCESS",
                governance_status="QUALIFY",
                artifact_status="COMPUTED",
                claim_tag="CLAIM",
                claim_state="INTERPRETED",
                uncertainty="Moderate",
                perception_class="DERIVED",
                canon_9_touched=["GR"],
            )
        except Exception as e:
            logger.exception("Pipeline execution failed")
            return get_standard_envelope(
                primary_artifact={"error": str(e)},
                tool_class="compute",
                execution_status="ERROR",
                governance_status="VOID",
                artifact_status="REJECTED",
                claim_tag="VOID",
                claim_state="VOID",
            )

    @mcp.tool()
    async def geox_stratigraphy_preview_config(
        project_yaml: str,
    ) -> dict[str, Any]:
        """
        Validate and preview a stratigraphy project configuration.

        Parses the YAML, validates the schema, and returns a summary
        of wells, intervals, and parameters — without running the pipeline.

        Parameters
        ----------
        project_yaml : str
            YAML project configuration (same format as run_pipeline).

        Returns
        -------
        dict with validated config summary.
        """
        try:
            config_dict = yaml.safe_load(project_yaml)
        except Exception as e:
            return {
                "ok": False,
                "error": f"Invalid YAML: {e}",
                "claim_state": "VOID",
            }

        try:
            wells = [
                {"name": w["name"], "path": w["path"], "format": w.get("format", "LAS")} for w in config_dict.get("wells", [])
            ]
            interval_summary = {}
            for well_id, ivls in config_dict.get("intervals", {}).items():
                interval_summary[well_id] = [
                    {"zone": i["zone"], "top": i["top"], "base": i["base"], "depo_env": i.get("depo_env", "?")} for i in ivls
                ]
        except Exception as e:
            return {
                "ok": False,
                "error": f"Validation error: {e}",
                "claim_state": "VOID",
            }

        return {
            "ok": True,
            "project": config_dict.get("project", "Untitled"),
            "n_wells": len(wells),
            "n_intervals": sum(len(v) for v in interval_summary.values()),
            "wells": wells,
            "intervals": interval_summary,
            "parameters": {
                "bin_size_m": config_dict.get("bin_size_m", 10.0),
                "min_package_thickness_m": config_dict.get("min_package_thickness_m", 20.0),
                "p50_shift_thresh_gapi": config_dict.get("p50_shift_thresh_gapi", 15.0),
                "gr_cut_api": config_dict.get("gr_cut_api", 75.0),
            },
            "claim_state": "OBSERVED",
        }

    # Register in FEDERATION_TOOLS
    try:
        from federation.tool_manifest import FEDERATION_TOOLS, CognitiveAxis, ToolManifest

        for _name in TOOL_NAMES:
            if _name not in FEDERATION_TOOLS:
                FEDERATION_TOOLS[_name] = ToolManifest(
                    name=_name,
                    description="",
                    expose=True,
                    cognitive_axis=CognitiveAxis.REASON,
                    organ="geox",
                )
    except Exception:
        pass

    logger.info(f"Stratigraphy tools registered: {', '.join(TOOL_NAMES)}")
