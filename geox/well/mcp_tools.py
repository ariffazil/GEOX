"""
GEOX Well Stratigraphy — MCP Tool Registration
═══════════════════════════════════════════════════════════════

Registers well stratigraphy tools (L1-L3) into the GEOX MCP surface.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
from fastmcp import FastMCP

from contracts.enums.statuses import get_standard_envelope

logger = logging.getLogger("geox.well.stratigraphy")

TOOL_PREFIX = "geox_well_"


def register_well_tools(mcp: FastMCP) -> None:
    """Register all well stratigraphy tools on the MCP instance."""

    # ── Helper: load LAS/CSV ─────────────────────────────────────────────
    def _load_las_or_csv(source: str) -> tuple[np.ndarray, np.ndarray, dict]:
        """Load depth and GR from LAS or CSV. Returns (depth, gr, metadata)."""
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        ext = path.suffix.lower()
        if ext in (".las", ".LAS"):
            try:
                import lasio
                las = lasio.read(str(path))
                depth = las.index.values.astype(float)
                # Find GR curve (try common mnemonics)
                for alias in ["GR", "GRC", "SGR", "CGR", "GAPI", "GAMMA", "GAMMA_RAY"]:
                    if alias in las.keys():
                        gr = las[alias].values.astype(float)
                        break
                else:
                    # Use first curve if no GR found
                    gr = list(las.keys())[0]
                    gr = las[gr].values.astype(float)
                meta = {
                    "well": las.well.WELL.value if hasattr(las.well, 'WELL') else path.stem,
                    "source": str(path),
                    "format": "LAS",
                    "n_samples": len(depth),
                    "curves": list(las.keys()),
                    "start_depth": float(depth[0]),
                    "end_depth": float(depth[-1]),
                }
                return depth, gr, meta
            except ImportError:
                raise ImportError("lasio is required for LAS files: pip install lasio")

        elif ext in (".csv", ".CSV", ".txt"):
            import csv
            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            if not rows:
                raise ValueError(f"Empty CSV: {source}")
            # Detect depth and GR columns
            cols = list(rows[0].keys())
            depth_col = next((c for c in cols if c.lower() in ("depth", "dept", "md", "td")), cols[0])
            gr_col = next((c for c in cols if c.lower() in ("gr", "grc", "sgr", "gamma", "gamma_ray")), cols[1] if len(cols) > 1 else cols[0])
            depth = np.array([float(r[depth_col]) for r in rows], dtype=float)
            gr = np.array([float(r[gr_col]) for r in rows], dtype=float)
            meta = {
                "well": path.stem,
                "source": str(path),
                "format": "CSV",
                "n_samples": len(depth),
                "columns": cols,
                "depth_column": depth_col,
                "gr_column": gr_col,
            }
            return depth, gr, meta

        else:
            raise ValueError(f"Unsupported file format: {ext}")

    # ── L1: 10 m GR Sensing ──────────────────────────────────────────────
    @mcp.tool()
    async def geox_well_compute_gr_bins(
        source: str,
        zone_top: float,
        zone_base: float,
        bin_size_m: float = 10.0,
    ) -> dict[str, Any]:
        """
        L1 Sensing: Compute 10 m GR statistics bins over a depth interval.

        Reads LAS or CSV file, bins GR by depth, returns per-bin statistics
        (P10, P50, P90, mean, std, n_samples) plus GR motif classification.

        Parameters
        ----------
        source : str
            Path to LAS or CSV file.
        zone_top : float
            Top of zone in metres.
        zone_base : float
            Base of zone in metres.
        bin_size_m : float, default 10.0
            Bin size in metres.

        Returns
        -------
        dict with bins, metadata, claim_state.
        """
        try:
            depth, gr, meta = _load_las_or_csv(source)
        except Exception as e:
            return {
                "ok": False,
                "tool": "geox_well_compute_gr_bins",
                "error": str(e),
                "claim_state": "VOID",
            }

        from geox.well.tools.sensing import compute_gr_bins
        bins = compute_gr_bins(depth, gr, zone_top, zone_base, bin_size_m)

        return get_standard_envelope(
            primary_artifact={
                "well": meta["well"],
                "source": source,
                "zone_top": zone_top,
                "zone_base": zone_base,
                "bin_size_m": bin_size_m,
                "n_bins": len(bins),
                "bins": bins,
                "metadata": meta,
            },
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="COMPUTED",
            claim_tag="CLAIM",
            claim_state="DERIVED_CANDIDATE",
            uncertainty="Moderate",
            perception_class="DERIVED",
            canon_9_touched=["GR"],
        )

    # ── L2: Geological Package Builder ────────────────────────────────────
    @mcp.tool()
    async def geox_well_build_packages(
        gr_bins: list[dict[str, Any]],
        min_package_thickness_m: float = 20.0,
        p50_shift_api: float = 15.0,
    ) -> dict[str, Any]:
        """
        L2 Package Builder: Aggregate 10 m GR bins into geological packages.

        Detects package boundaries by motif change and P50 shift thresholds.
        Returns packages with stacking pattern classification.

        Parameters
        ----------
        gr_bins : list[dict]
            10 m GR bins from geox_well_compute_gr_bins.
        min_package_thickness_m : float, default 20.0
            Minimum package thickness in metres.
        p50_shift_api : float, default 15.0
            P50 shift threshold for detecting package boundaries.

        Returns
        -------
        dict with packages, stacking_patterns, claim_state.
        """
        from geox.well.tools.packages import build_packages

        packages = build_packages(gr_bins, min_package_thickness_m, p50_shift_api)

        stacking_patterns = list(set(
            p.get("stacking_pattern", "MIXED") for p in packages
        ))

        return get_standard_envelope(
            primary_artifact={
                "n_packages": len(packages),
                "min_package_thickness_m": min_package_thickness_m,
                "p50_shift_api": p50_shift_api,
                "packages": packages,
                "stacking_patterns": stacking_patterns,
            },
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="COMPUTED",
            claim_tag="CLAIM",
            claim_state="DERIVED_CANDIDATE",
            uncertainty="Moderate",
            perception_class="DERIVED",
            canon_9_touched=["GR"],
        )

    # ── L3: Sequence Stratigraphy Inference ───────────────────────────────
    @mcp.tool()
    async def geox_well_infer_seq_strat(
        packages: list[dict[str, Any]],
        depo_env_code: str = "FLUVIAL",
        gr_cutoff_api: float = 75.0,
    ) -> dict[str, Any]:
        """
        L3 Sequence Stratigraphy: Infer systems tracts from packages.

        Assigns LST/TST/HST/FSST systems tracts and identifies key
        surfaces (SB, TS, MFS) based on stacking pattern changes.

        Parameters
        ----------
        packages : list[dict]
            Geological packages from geox_well_build_packages.
        depo_env_code : str, default "FLUVIAL"
            Depositional environment code.
            Valid: FLUVIAL, TIDAL, SHOREFACE, SHELF, DEEPWATER, CARBONATE.
        gr_cutoff_api : float, default 75.0
            GR cutoff for sand/shale discrimination.

        Returns
        -------
        dict with systems_tracts, surfaces, motif_summary, claim_state.
        """
        from geox.well.tools.seqstrat import infer_seq_strat

        result = infer_seq_strat(packages, depo_env_code, gr_cutoff_api)

        return get_standard_envelope(
            primary_artifact=result,
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="DRAFT",
            claim_tag="HYPOTHESIS",
            claim_state=result.get("claim_state", "INTERPRETED"),
            uncertainty="Moderate",
            perception_class="HYPOTHESIS",
            canon_9_touched=["GR"],
        )

    # ── Full pipeline: L1 + L2 + L3 ──────────────────────────────────────
    @mcp.tool()
    async def geox_well_analyze_sequence(
        source: str,
        zone_top: float,
        zone_base: float,
        depo_env_code: str = "FLUVIAL",
        bin_size_m: float = 10.0,
        min_package_thickness_m: float = 20.0,
        p50_shift_api: float = 15.0,
        gr_cutoff_api: float = 75.0,
    ) -> dict[str, Any]:
        """
        Full well sequence stratigraphy pipeline: L1 + L2 + L3.

        Reads LAS/CSV, computes 10 m GR bins, builds geological packages,
        infers systems tracts and key surfaces.

        This is the recommended entry point for most workflows.

        Parameters
        ----------
        source : str
            Path to LAS or CSV file.
        zone_top : float
            Top of zone in metres.
        zone_base : float
            Base of zone in metres.
        depo_env_code : str, default "FLUVIAL"
            Depositional environment code.
        bin_size_m : float, default 10.0
            Bin size for GR sensing.
        min_package_thickness_m : float, default 20.0
            Minimum package thickness.
        p50_shift_api : float, default 15.0
            P50 shift threshold for package boundaries.
        gr_cutoff_api : float, default 75.0
            GR cutoff for sand/shale.

        Returns
        -------
        dict with wells (containing bins, packages, seq_strat), surfaces, summary.
        """
        try:
            depth, gr, meta = _load_las_or_csv(source)
        except Exception as e:
            return {
                "ok": False,
                "tool": "geox_well_analyze_sequence",
                "error": str(e),
                "claim_state": "VOID",
            }

        from geox.well.tools.sensing import compute_gr_bins
        from geox.well.tools.packages import build_packages
        from geox.well.tools.seqstrat import infer_seq_strat

        # L1
        bins = compute_gr_bins(depth, gr, zone_top, zone_base, bin_size_m)

        # L2
        packages = build_packages(bins, min_package_thickness_m, p50_shift_api)

        # L3
        seq_strat = infer_seq_strat(packages, depo_env_code, gr_cutoff_api)

        return get_standard_envelope(
            primary_artifact={
                "well": meta["well"],
                "source": source,
                "metadata": meta,
                "n_bins": len(bins),
                "n_packages": len(packages),
                "bins": bins,
                "packages": packages,
                "systems_tracts": seq_strat["systems_tracts"],
                "surfaces": seq_strat["surfaces"],
                "motif_summary": seq_strat.get("motif_summary", {}),
                "depo_env_code": depo_env_code,
                "depo_context": seq_strat.get("depo_context", "unknown"),
            },
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="DRAFT",
            claim_tag="HYPOTHESIS",
            claim_state="INTERPRETED",
            uncertainty="Moderate",
            perception_class="DERIVED",
            canon_9_touched=["GR"],
        )

    # Register in FEDERATION_TOOLS for somatic boundary filtering
    _well_tool_names = [
        "geox_well_compute_gr_bins",
        "geox_well_build_packages",
        "geox_well_infer_seq_strat",
        "geox_well_analyze_sequence",
    ]
    try:
        from federation.tool_manifest import FEDERATION_TOOLS, ToolManifest, CognitiveAxis
        for _name in _well_tool_names:
            if _name not in FEDERATION_TOOLS:
                FEDERATION_TOOLS[_name] = ToolManifest(
                    name=_name,
                    description="",
                    expose=True,
                    cognitive_axis=CognitiveAxis.REASON,
                    organ="geox",
                )
    except Exception:
        pass  # FEDERATION_TOOLS may not be available

    logger.info(f"Well stratigraphy tools registered: {', '.join(_well_tool_names)}")
