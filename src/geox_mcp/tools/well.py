"""
GEOX Well Stratigraphy — MCP Tool Registration
═══════════════════════════════════════════════════════════════

Registers well stratigraphy tools (L1-L3) into the GEOX MCP surface.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import numpy as np
from fastmcp import FastMCP

from geox_core.enums.statuses import (
    ArtifactStatus,
    ExecutionStatus,
    GovernanceStatus,
    get_standard_envelope,
)
from geox_core.well.tools.seqstrat import DEPO_ENV_SYSTEMS_TRACTS

logger = logging.getLogger("geox.well.stratigraphy")

TOOL_PREFIX = "geox_well_"


def _well_tool_error(
    tool_name: str,
    error_code: str,
    message: str,
    *,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a governed fail-closed envelope for existing well tools."""
    return get_standard_envelope(
        primary_artifact={
            "tool": tool_name,
            "error_code": error_code,
            "message": message,
            "recoverable": True,
        },
        tool_class="compute",
        execution_status=ExecutionStatus.ERROR,
        governance_status=GovernanceStatus.HOLD,
        artifact_status=ArtifactStatus.REJECTED,
        claim_tag="HYPOTHESIS",
        claim_state="NO_VALID_EVIDENCE",
        uncertainty="High",
        diagnostics=diagnostics or {},
        physics_guard={
            "guard_passed": False,
            "physics_version": "geox-well-v2026.05.14",
            "violations": [error_code],
        },
        humility_score=1.0,
        perception_class="HYPOTHESIS",
        evidence_tag="SOURCE_UNRESOLVED",
        canon_9_touched=["phi"],
    )


def _validate_interval(
    *,
    zone_top: float,
    zone_base: float,
    bin_size_m: float | None = None,
) -> tuple[bool, str, str]:
    values = [zone_top, zone_base]
    if bin_size_m is not None:
        values.append(bin_size_m)
    if not all(np.isfinite(v) for v in values):
        return False, "NONFINITE_INPUT", "Depth interval and bin size must be finite numbers."
    if zone_top >= zone_base:
        return False, "INVALID_DEPTH_INTERVAL", "zone_top must be shallower than zone_base."
    if bin_size_m is not None:
        interval = zone_base - zone_top
        if bin_size_m <= 0:
            return False, "INVALID_BIN_SIZE", "bin_size_m must be greater than zero."
        if bin_size_m > interval:
            return (
                False,
                "BIN_SIZE_EXCEEDS_INTERVAL",
                "bin_size_m cannot exceed interval thickness.",
            )
    return True, "", ""


def _source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _gr_physics_guard(gr: np.ndarray, *, min_samples: int = 3) -> dict[str, Any]:
    valid = gr[np.isfinite(gr)]
    violations: list[str] = []
    if valid.size < min_samples:
        violations.append("INSUFFICIENT_VALID_GR_SAMPLES")
    if valid.size and float(np.nanmin(valid)) < 0:
        violations.append("GR_BELOW_PHYSICAL_RANGE")
    if valid.size and float(np.nanmax(valid)) > 300:
        violations.append("GR_ABOVE_EXPECTED_RANGE")
    return {
        "guard_passed": not violations,
        "physics_version": "geox-well-v2026.05.14",
        "checked": ["finite_samples", "GR_expected_range_0_300_gAPI"],
        "violations": violations,
        "valid_samples": int(valid.size),
    }


def _interpretation_limitations(source_kind: str) -> list[str]:
    limitations = [
        "GR motif is a derived proxy, not direct lithology.",
        (
            "Depositional environment and sequence surfaces require calibration with core, "
            "cuttings, biostratigraphy, seismic, or field context before decision use."
        ),
    ]
    if source_kind.upper() in {"LAS", "CSV"}:
        limitations.append(
            "Tool used the GR curve only; density, neutron, resistivity, sonic, core, "
            "and pressure evidence were not consumed by this sequence tool."
        )
    return limitations


def register_well_tools(mcp: FastMCP) -> None:
    """Register all well stratigraphy tools on the MCP instance."""

    # ── Helper: load LAS/CSV ─────────────────────────────────────────────
    def _load_las_or_csv(source: str) -> tuple[np.ndarray, np.ndarray, dict]:
        """Load depth and GR from LAS or CSV. Returns (depth, gr, metadata)."""
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        if not path.is_file():
            raise ValueError(f"Source is not a file: {source}")

        ext = path.suffix.lower()
        if ext in (".las", ".LAS"):
            try:
                import lasio
                las = lasio.read(str(path))
                depth = las.index
                if hasattr(depth, 'values'):
                    depth = depth.values
                depth = depth.astype(float)
                # Find GR curve (try common mnemonics)
                for alias in ["GR", "GRC", "SGR", "CGR", "GAPI", "GAMMA", "GAMMA_RAY"]:
                    if alias in las.keys():
                        gr = las[alias]
                        if hasattr(gr, 'values'):
                            gr = gr.values
                        gr = gr.astype(float)
                        break
                else:
                    # Use first curve if no GR found
                    gr_name = list(las.keys())[0]
                    gr = las[gr_name]
                    if hasattr(gr, 'values'):
                        gr = gr.values
                    gr = gr.astype(float)
                meta = {
                    "well": las.well.WELL.value if hasattr(las.well, 'WELL') else path.stem,
                    "source": str(path),
                    "format": "LAS",
                    "source_sha256": _source_hash(path),
                    "n_samples": len(depth),
                    "curves": list(las.keys()),
                    "start_depth": float(depth[0]),
                    "end_depth": float(depth[-1]),
                }
                finite = np.isfinite(depth) & np.isfinite(gr)
                depth = depth[finite]
                gr = gr[finite]
                if len(depth) < 3:
                    raise ValueError("Source has fewer than 3 finite depth/GR samples.")
                diffs = np.diff(depth)
                if not (np.all(diffs > 0) or np.all(diffs < 0)):
                    raise ValueError(
                        "Depth samples must be strictly monotonic before sequence analysis."
                    )
                if np.all(diffs < 0):
                    depth = depth[::-1]
                    gr = gr[::-1]
                meta["valid_gr_samples"] = int(len(gr))
                return depth, gr, meta
            except ImportError as exc:
                raise ImportError("lasio is required for LAS files: pip install lasio") from exc

        elif ext in (".csv", ".CSV", ".txt"):
            import csv
            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            if not rows:
                raise ValueError(f"Empty CSV: {source}")
            # Detect depth and GR columns
            cols = list(rows[0].keys())
            depth_col = next(
                (c for c in cols if c.lower() in ("depth", "dept", "md", "td")),
                cols[0],
            )
            gr_col = next(
                (c for c in cols if c.lower() in ("gr", "grc", "sgr", "gamma", "gamma_ray")),
                cols[1] if len(cols) > 1 else cols[0],
            )
            depth = np.array([float(r[depth_col]) for r in rows], dtype=float)
            gr = np.array([float(r[gr_col]) for r in rows], dtype=float)
            meta = {
                "well": path.stem,
                "source": str(path),
                "format": "CSV",
                "source_sha256": _source_hash(path),
                "n_samples": len(depth),
                "columns": cols,
                "depth_column": depth_col,
                "gr_column": gr_col,
            }
            finite = np.isfinite(depth) & np.isfinite(gr)
            depth = depth[finite]
            gr = gr[finite]
            if len(depth) < 3:
                raise ValueError("Source has fewer than 3 finite depth/GR samples.")
            diffs = np.diff(depth)
            if not (np.all(diffs > 0) or np.all(diffs < 0)):
                raise ValueError(
                    "Depth samples must be strictly monotonic before sequence analysis."
                )
            if np.all(diffs < 0):
                depth = depth[::-1]
                gr = gr[::-1]
            meta["valid_gr_samples"] = int(len(gr))
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
        ok, error_code, message = _validate_interval(
            zone_top=zone_top,
            zone_base=zone_base,
            bin_size_m=bin_size_m,
        )
        if not ok:
            return _well_tool_error("geox_well_compute_gr_bins", error_code, message)

        try:
            depth, gr, meta = _load_las_or_csv(source)
        except Exception as e:
            return _well_tool_error(
                "geox_well_compute_gr_bins",
                "SOURCE_LOAD_FAILED",
                str(e),
                diagnostics={"source": source},
            )

        physics_guard = _gr_physics_guard(gr)
        if not physics_guard["guard_passed"]:
            return _well_tool_error(
                "geox_well_compute_gr_bins",
                "GR_PHYSICS_GUARD_FAILED",
                "GR samples failed finite/range checks. Run ingest + QC before interpretation.",
                diagnostics={"source": source, "physics_guard": physics_guard},
            )

        from geox_core.well.tools.sensing import compute_gr_bins
        bins = compute_gr_bins(depth, gr, zone_top, zone_base, bin_size_m)
        usable_bins = [b for b in bins if b.get("p50") is not None]
        if not usable_bins:
            return _well_tool_error(
                "geox_well_compute_gr_bins",
                "NO_USABLE_BINS",
                "Requested interval produced no usable GR bins.",
                diagnostics={
                    "source_depth_range": [float(depth[0]), float(depth[-1])],
                    "requested_interval": [zone_top, zone_base],
                    "bin_size_m": bin_size_m,
                },
            )

        return get_standard_envelope(
            primary_artifact={
                "tool": "geox_well_compute_gr_bins",
                "well": meta["well"],
                "source": source,
                "source_sha256": meta.get("source_sha256", ""),
                "zone_top": zone_top,
                "zone_base": zone_base,
                "bin_size_m": bin_size_m,
                "n_bins": len(bins),
                "n_usable_bins": len(usable_bins),
                "bins": bins,
                "metadata": meta,
                "limitations": _interpretation_limitations(meta.get("format", "unknown")),
            },
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="COMPUTED",
            claim_tag="CLAIM",
            claim_state="DERIVED_CANDIDATE",
            uncertainty="Moderate",
            evidence_refs=[meta.get("source_sha256", source)],
            diagnostics={
                "gr_physics_guard": physics_guard,
                "source_format": meta.get("format"),
            },
            physics_guard=physics_guard,
            humility_score=round(1.0 - min(1.0, len(usable_bins) / max(len(bins), 1)), 4),
            perception_class="DERIVED",
            evidence_tag="EVIDENCE_DIRECT",
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
        if min_package_thickness_m <= 0 or not np.isfinite(min_package_thickness_m):
            return _well_tool_error(
                "geox_well_build_packages",
                "INVALID_PACKAGE_THICKNESS",
                "min_package_thickness_m must be a finite positive number.",
            )
        if p50_shift_api < 0 or not np.isfinite(p50_shift_api):
            return _well_tool_error(
                "geox_well_build_packages",
                "INVALID_P50_SHIFT",
                "p50_shift_api must be a finite non-negative number.",
            )
        if not gr_bins:
            return _well_tool_error(
                "geox_well_build_packages",
                "NO_GR_BINS",
                "geox_well_build_packages requires bins from geox_well_compute_gr_bins.",
            )

        from geox_core.well.tools.packages import build_packages

        packages = build_packages(gr_bins, min_package_thickness_m, p50_shift_api)
        if not packages:
            return _well_tool_error(
                "geox_well_build_packages",
                "NO_PACKAGES_BUILT",
                "GR bins did not meet package thickness/coherence requirements.",
                diagnostics={
                    "n_input_bins": len(gr_bins),
                    "min_package_thickness_m": min_package_thickness_m,
                    "p50_shift_api": p50_shift_api,
                },
            )

        stacking_patterns = list(set(
            p.get("stacking_pattern", "MIXED") for p in packages
        ))

        return get_standard_envelope(
            primary_artifact={
                "tool": "geox_well_build_packages",
                "n_packages": len(packages),
                "min_package_thickness_m": min_package_thickness_m,
                "p50_shift_api": p50_shift_api,
                "packages": packages,
                "stacking_patterns": stacking_patterns,
                "limitations": _interpretation_limitations("GR_BINS"),
            },
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="COMPUTED",
            claim_tag="CLAIM",
            claim_state="DERIVED_CANDIDATE",
            uncertainty="Moderate",
            evidence_refs=["gr_bins"],
            diagnostics={"n_input_bins": len(gr_bins)},
            physics_guard={
                "guard_passed": True,
                "physics_version": "geox-well-v2026.05.14",
                "checked": ["non_empty_bins", "positive_package_thickness"],
            },
            perception_class="DERIVED",
            evidence_tag="INTERPRET_FROM_LITHOLOGY",
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
        if not packages:
            return _well_tool_error(
                "geox_well_infer_seq_strat",
                "NO_PACKAGES",
                "geox_well_infer_seq_strat requires packages from geox_well_build_packages.",
            )
        if not np.isfinite(gr_cutoff_api) or gr_cutoff_api < 0 or gr_cutoff_api > 300:
            return _well_tool_error(
                "geox_well_infer_seq_strat",
                "INVALID_GR_CUTOFF",
                "gr_cutoff_api must be within 0-300 gAPI.",
            )
        depo_env_code = str(depo_env_code or "").upper()
        if depo_env_code not in DEPO_ENV_SYSTEMS_TRACTS:
            return _well_tool_error(
                "geox_well_infer_seq_strat",
                "UNKNOWN_DEPOSITIONAL_ENVIRONMENT",
                "depo_env_code must be one of the supported GEOX sequence environments.",
                diagnostics={"allowed": sorted(DEPO_ENV_SYSTEMS_TRACTS.keys())},
            )

        from geox_core.well.tools.seqstrat import infer_seq_strat

        result = infer_seq_strat(packages, depo_env_code, gr_cutoff_api)
        if not result.get("systems_tracts"):
            return _well_tool_error(
                "geox_well_infer_seq_strat",
                "NO_SYSTEMS_TRACTS",
                "Package evidence was insufficient for sequence stratigraphy inference.",
            )
        result["tool"] = "geox_well_infer_seq_strat"
        result["limitations"] = _interpretation_limitations("GR_PACKAGES")

        return get_standard_envelope(
            primary_artifact=result,
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="DRAFT",
            claim_tag="HYPOTHESIS",
            claim_state=result.get("claim_state", "INTERPRETED"),
            uncertainty="High",
            evidence_refs=["geox_well_build_packages"],
            diagnostics={
                "allowed_depo_env_codes": sorted(DEPO_ENV_SYSTEMS_TRACTS.keys()),
                "basis": "GR motif and package stacking only",
            },
            physics_guard={
                "guard_passed": True,
                "physics_version": "geox-well-v2026.05.14",
                "checked": ["non_empty_packages", "supported_depo_env", "GR_cutoff_range"],
            },
            humility_score=0.75,
            perception_class="HYPOTHESIS",
            evidence_tag="INTERPRET_FROM_LITHOLOGY",
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
        ok, error_code, message = _validate_interval(
            zone_top=zone_top,
            zone_base=zone_base,
            bin_size_m=bin_size_m,
        )
        if not ok:
            return _well_tool_error("geox_well_analyze_sequence", error_code, message)
        if min_package_thickness_m <= 0 or not np.isfinite(min_package_thickness_m):
            return _well_tool_error(
                "geox_well_analyze_sequence",
                "INVALID_PACKAGE_THICKNESS",
                "min_package_thickness_m must be a finite positive number.",
            )
        if p50_shift_api < 0 or not np.isfinite(p50_shift_api):
            return _well_tool_error(
                "geox_well_analyze_sequence",
                "INVALID_P50_SHIFT",
                "p50_shift_api must be a finite non-negative number.",
            )
        if not np.isfinite(gr_cutoff_api) or gr_cutoff_api < 0 or gr_cutoff_api > 300:
            return _well_tool_error(
                "geox_well_analyze_sequence",
                "INVALID_GR_CUTOFF",
                "gr_cutoff_api must be within 0-300 gAPI.",
            )
        depo_env_code = str(depo_env_code or "").upper()
        if depo_env_code not in DEPO_ENV_SYSTEMS_TRACTS:
            return _well_tool_error(
                "geox_well_analyze_sequence",
                "UNKNOWN_DEPOSITIONAL_ENVIRONMENT",
                "depo_env_code must be one of the supported GEOX sequence environments.",
                diagnostics={"allowed": sorted(DEPO_ENV_SYSTEMS_TRACTS.keys())},
            )

        try:
            depth, gr, meta = _load_las_or_csv(source)
        except Exception as e:
            return _well_tool_error(
                "geox_well_analyze_sequence",
                "SOURCE_LOAD_FAILED",
                str(e),
                diagnostics={"source": source},
            )

        physics_guard = _gr_physics_guard(gr)
        if not physics_guard["guard_passed"]:
            return _well_tool_error(
                "geox_well_analyze_sequence",
                "GR_PHYSICS_GUARD_FAILED",
                "GR samples failed finite/range checks. Run ingest + QC before interpretation.",
                diagnostics={"source": source, "physics_guard": physics_guard},
            )

        from geox_core.well.tools.packages import build_packages
        from geox_core.well.tools.sensing import compute_gr_bins
        from geox_core.well.tools.seqstrat import infer_seq_strat

        # L1
        bins = compute_gr_bins(depth, gr, zone_top, zone_base, bin_size_m)
        usable_bins = [b for b in bins if b.get("p50") is not None]
        if not usable_bins:
            return _well_tool_error(
                "geox_well_analyze_sequence",
                "NO_USABLE_BINS",
                "Requested interval produced no usable GR bins.",
                diagnostics={
                    "source_depth_range": [float(depth[0]), float(depth[-1])],
                    "requested_interval": [zone_top, zone_base],
                    "bin_size_m": bin_size_m,
                },
            )

        # L2
        packages = build_packages(bins, min_package_thickness_m, p50_shift_api)
        if not packages:
            return _well_tool_error(
                "geox_well_analyze_sequence",
                "NO_PACKAGES_BUILT",
                "GR bins did not meet package thickness/coherence requirements.",
                diagnostics={
                    "n_bins": len(bins),
                    "n_usable_bins": len(usable_bins),
                    "min_package_thickness_m": min_package_thickness_m,
                },
            )

        # L3
        seq_strat = infer_seq_strat(packages, depo_env_code, gr_cutoff_api)
        if not seq_strat.get("systems_tracts"):
            return _well_tool_error(
                "geox_well_analyze_sequence",
                "NO_SYSTEMS_TRACTS",
                "Package evidence was insufficient for sequence stratigraphy inference.",
            )

        return get_standard_envelope(
            primary_artifact={
                "tool": "geox_well_analyze_sequence",
                "well": meta["well"],
                "source": source,
                "source_sha256": meta.get("source_sha256", ""),
                "metadata": meta,
                "n_bins": len(bins),
                "n_usable_bins": len(usable_bins),
                "n_packages": len(packages),
                "bins": bins,
                "packages": packages,
                "systems_tracts": seq_strat["systems_tracts"],
                "surfaces": seq_strat["surfaces"],
                "motif_summary": seq_strat.get("motif_summary", {}),
                "depo_env_code": depo_env_code,
                "depo_context": seq_strat.get("depo_context", "unknown"),
                "limitations": _interpretation_limitations(meta.get("format", "unknown")),
            },
            tool_class="compute",
            execution_status="SUCCESS",
            governance_status="QUALIFY",
            artifact_status="DRAFT",
            claim_tag="HYPOTHESIS",
            claim_state="INTERPRETED",
            uncertainty="High",
            evidence_refs=[meta.get("source_sha256", source)],
            diagnostics={
                "basis": "GR motif and package stacking only",
                "gr_physics_guard": physics_guard,
                "allowed_depo_env_codes": sorted(DEPO_ENV_SYSTEMS_TRACTS.keys()),
            },
            physics_guard=physics_guard,
            humility_score=0.75,
            perception_class="HYPOTHESIS",
            evidence_tag="INTERPRET_FROM_LITHOLOGY",
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
        from federation.tool_manifest import FEDERATION_TOOLS, CognitiveAxis, ToolManifest

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
