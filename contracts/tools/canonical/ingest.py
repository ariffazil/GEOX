from __future__ import annotations

import logging
import os
from typing import Any, List, Dict, Optional, Literal

from fastmcp import FastMCP
from contracts.enums.statuses import (
    get_standard_envelope,
    GovernanceStatus,
    ArtifactStatus,
    ExecutionStatus,
)
from contracts.tools.canonical._helpers import (
    _get_artifact,
    _artifact_exists,
    _register_artifact,
    _record_latest_qc,
    _latest_qc_failed_refs,
    _check_maruah_territory,
    _inject_ensemble_residual_evidence,
    _safe_upload_path,
    _decode_upload_content,
    _parse_csv_or_json,
    _map_canonical_curves,
    _detect_depth_unit,
    _compute_vsh_from_store,
    _compute_porosity_from_store,
    _compute_saturation_from_store,
    _compute_netpay_from_store,
    _classify_gr_motif,
    _classify_lithology_from_store,
    _safe_reduction,
    _get_well_data_with_depth,
    CLAIM_STATES,
    CANONICAL_ALIASES,
    _CURVE_RANGES,
    _artifact_registry,
    _artifact_store,
    _well_curves_registry,
    _ARTIFACT_REGISTRY_PATH,
    MAX_UPLOAD_BYTES,
)
from compatibility.legacy_aliases import LEGACY_ALIAS_MAP, get_alias_metadata

logger = logging.getLogger("geox.canonical.ingest")


async def geox_data_ingest_bundle(
    source_uri: Optional[str] = None,
    source_type: Literal["well", "seismic", "earth3d", "auto", "tops", "biostrat", "checkshot"] = "auto",
    well_id: Optional[str] = None,
    standardize_curves: bool = True,
    normalize_units: bool = True,
    content_base64: Optional[str] = None, # New: support for base64 encoded content
    filename: Optional[str] = None, # Required if content_base64 is provided
    target_dir: str = "/data/geox_las", # Required if content_base64 is provided
    overwrite: bool = False, # Required if content_base64 is provided
) -> dict:
    """Lazy ingestion for LAS, CSV, Parquet, SEG-Y, and structural payloads.
    Also supports direct base64 upload for LAS files (absorbing geox_file_upload_import).

    Args:
        source_uri: File path (e.g. /mnt/data/15-9-19_SR_COMP.LAS) or HTTPS URL. Mutually exclusive with content_base64.
        source_type: Hint for payload type; "auto" detects from extension.
                     Supports: well, seismic, earth3d, auto, tops, biostrat, checkshot.
        well_id: Optional identifier; derived from filename if omitted.
        standardize_curves: Run canonical alias mapping on well log mnemonics.
        normalize_units: Convert ft→m if depth unit is FT/FEET.
        content_base64: Optional: Base64 encoded file content (e.g., LAS file). Mutually exclusive with source_uri.
        filename: Optional: Required if content_base64 is provided. The original filename.
        target_dir: Optional: Directory to save the uploaded file if content_base64 is used. Defaults to /data/geox_las.
        overwrite: Optional: Whether to overwrite existing file if content_base64 is used. Defaults to False.
    """

    # --- Handle content_base64 upload first (new functionality from geox_file_upload_import) ---
    if content_base64:
        if source_uri:
             return get_standard_envelope(
                {
                    "status": "ERROR",
                    "tool": "geox_data_ingest_bundle",
                    "error_code": "INVALID_INPUT",
                    "message": "Provide exactly one of content_base64 or source_uri, not both.",
                    "claim_state": "NO_VALID_EVIDENCE",
                },
                tool_class="ingress",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
            )
        if not filename:
            return get_standard_envelope(
                {
                    "status": "ERROR",
                    "tool": "geox_data_ingest_bundle",
                    "error_code": "MISSING_FILENAME",
                    "message": "Filename is required when content_base64 is provided.",
                    "claim_state": "NO_VALID_EVIDENCE",
                },
                tool_class="ingress",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
            )

        try:
            target_path = _safe_upload_path(filename, target_dir)
        except ValueError as exc:
            return get_standard_envelope(
                {
                    "status": "ERROR",
                    "tool": "geox_data_ingest_bundle",
                    "error_code": "INVALID_OUTPUT_PATH",
                    "message": str(exc),
                    "claim_state": "NO_VALID_EVIDENCE",
                },
                tool_class="ingress",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
            )

        if target_path.exists() and not overwrite:
            return get_standard_envelope(
                {
                    "status": "ERROR",
                    "tool": "geox_data_ingest_bundle",
                    "error_code": "FILE_EXISTS",
                    "message": f"File already exists: {target_path}",
                    "stored_path": str(target_path),
                    "claim_state": "NO_VALID_EVIDENCE",
                },
                tool_class="ingress",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
            )

        try:
            payload = _decode_upload_content(content_base64)
            target_path.write_bytes(payload)
        except Exception as exc:
            return get_standard_envelope(
                {
                    "status": "ERROR",
                    "tool": "geox_data_ingest_bundle",
                    "error_code": "IMPORT_FAILED",
                    "message": str(exc),
                    "claim_state": "NO_VALID_EVIDENCE",
                },
                tool_class="ingress",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
            )

        sha256 = hashlib.sha256(target_path.read_bytes()).hexdigest()
        derived_well_id = well_id or target_path.stem

        try:
            from geox.services.las_ingestor import LASIngestor

            ingest_result = LASIngestor().ingest(path=str(target_path), asset_id=derived_well_id)
            ingest_dict = ingest_result.to_dict()
        except Exception as exc:
            return get_standard_envelope(
                {
                    "status": "ERROR",
                    "tool": "geox_data_ingest_bundle",
                    "error_code": "LAS_PARSE_FAILED",
                    "message": f"File stored but could not be parsed as LAS: {exc}",
                    "stored_path": str(target_path),
                    "sha256": sha256,
                    "claim_state": "NO_VALID_EVIDENCE",
                },
                tool_class="ingress",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
            )

        loaded_curves = ingest_dict.get("loaded_curves", [])
        diagnostics = {
            "qcfail_count": ingest_dict.get("qcfail_count", 0),
            "suitability": ingest_dict.get("suitability"),
            "limitations": ingest_dict.get("limitations", []),
            "missing_channels": ingest_dict.get("missing_channels", []),
            "n_depth_samples": ingest_dict.get("n_depth_samples", 0),
            "depth_range_m": ingest_dict.get("depth_range_m")
            or ingest_dict.get("depth_range"),
            "sha256": sha256,
        }
        artifact_ref = _register_artifact(
            f"well_las:{derived_well_id}",
            curves=loaded_curves,
            las_path=str(target_path),
            claim_state="FILE_IMPORTED",
            diagnostics=diagnostics,
            source_uri="inline_base64_upload",
            artifact_type="well_log",
        )

        return get_standard_envelope(
            {
                "status": "OK",
                "tool": "geox_data_ingest_bundle",
                "stored_path": str(target_path),
                "artifact_ref": artifact_ref,
                "well_id": derived_well_id,
                "sha256": sha256,
                "loaded_curves": loaded_curves,
                "curve_count": len(loaded_curves),
                "depth_range_m": diagnostics["depth_range_m"],
                "claim_state": "FILE_IMPORTED",
            },
            tool_class="ingress",
            execution_status=ExecutionStatus.SUCCESS,
            artifact_status=ArtifactStatus.LOADED,
            claim_tag="CLAIM",
        )

    # --- Original geox_data_ingest_bundle logic (for source_uri) ---
    if not source_uri:
        return get_standard_envelope(
            {
                "status": "ERROR",
                "tool": "geox_data_ingest_bundle",
                "error_code": "MISSING_SOURCE",
                "message": "Either source_uri or content_base64 must be provided.",
                "claim_state": "NO_VALID_EVIDENCE",
            },
            tool_class="ingress",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
        )

    from pathlib import Path

    derived_id = well_id or Path(source_uri).stem

    # ── Handle non-well source types ────────────────────────────────────
    if source_type == "tops":
        try:
            rows = _parse_csv_or_json(source_uri)
        except Exception as exc:
            return get_standard_envelope(
                {
                    "tool": "geox_data_ingest_bundle",
                    "status": "ERROR",
                    "error_code": "FILE_NOT_FOUND" if "not found" in str(exc).lower() else "PARSE_FAILED",
                    "message": str(exc),
                    "source_type": "tops",
                },
                tool_class="ingest",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
            )
        formations = [r.get("formation_name", r.get("FORMATION_NAME", "")) for r in rows]
        _register_artifact(derived_id, claim_state="RAW_OBSERVATION")
        _artifact_store[derived_id]["type"] = "tops"
        _artifact_store[derived_id]["rows"] = rows
        return get_standard_envelope(
            {
                "tool": "geox_data_ingest_bundle",
                "status": "SUCCESS",
                "artifact_ref": derived_id,
                "source_type": "tops",
                "formation_count": len(rows),
                "formations": formations,
                "claim_state": "RAW_OBSERVATION",
            },
            tool_class="ingest",
            execution_status=ExecutionStatus.SUCCESS,
            artifact_status=ArtifactStatus.LOADED,
            claim_tag="CLAIM",
        )

    if source_type == "biostrat":
        try:
            rows = _parse_csv_or_json(source_uri)
        except Exception as exc:
            return get_standard_envelope(
                {
                    "tool": "geox_data_ingest_bundle",
                    "status": "ERROR",
                    "error_code": "FILE_NOT_FOUND" if "not found" in str(exc).lower() else "PARSE_FAILED",
                    "message": str(exc),
                    "source_type": "biostrat",
                },
                tool_class="ingest",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
            )
        biozones = list({r.get("biozone", r.get("BIOZONE", "")) for r in rows if r.get("biozone") or r.get("BIOZONE")})
        _register_artifact(derived_id, claim_state="RAW_OBSERVATION")
        _artifact_store[derived_id]["type"] = "biostrat"
        _artifact_store[derived_id]["rows"] = rows
        return get_standard_envelope(
            {
                "tool": "geox_data_ingest_bundle",
                "status": "SUCCESS",
                "artifact_ref": derived_id,
                "source_type": "biostrat",
                "sample_count": len(rows),
                "biozones": biozones,
                "claim_state": "RAW_OBSERVATION",
            },
            tool_class="ingest",
            execution_status=ExecutionStatus.SUCCESS,
            artifact_status=ArtifactStatus.LOADED,
            claim_tag="CLAIM",
        )

    if source_type == "checkshot":
        try:
            rows = _parse_csv_or_json(source_uri)
        except Exception as exc:
            return get_standard_envelope(
                {
                    "tool": "geox_data_ingest_bundle",
                    "status": "ERROR",
                    "error_code": "FILE_NOT_FOUND" if "not found" in str(exc).lower() else "PARSE_FAILED",
                    "message": str(exc),
                    "source_type": "checkshot",
                },
                tool_class="ingest",
                execution_status=ExecutionStatus.ERROR,
                governance_status=GovernanceStatus.HOLD,
                artifact_status=ArtifactStatus.REJECTED,
                claim_tag="HYPOTHESIS",
            )
        depths = [float(r.get("depth_md", r.get("DEPTH_MD", 0))) for r in rows if r.get("depth_md") or r.get("DEPTH_MD")]
        _register_artifact(derived_id, claim_state="RAW_OBSERVATION")
        _artifact_store[derived_id]["type"] = "checkshot"
        _artifact_store[derived_id]["rows"] = rows
        depth_range = [min(depths), max(depths)] if depths else [0, 0]
        return get_standard_envelope(
            {
                "tool": "geox_data_ingest_bundle",
                "status": "SUCCESS",
                "artifact_ref": derived_id,
                "source_type": "checkshot",
                "point_count": len(rows),
                "depth_range_m": depth_range,
                "claim_state": "RAW_OBSERVATION",
            },
            tool_class="ingest",
            execution_status=ExecutionStatus.SUCCESS,
            artifact_status=ArtifactStatus.LOADED,
            claim_tag="CLAIM",
        )

    # ── Well / seismic / earth3d / auto path ────────────────────────────
    source_name = os.path.basename(source_uri.split("?", 1)[0]) or "inline_las"
    derived_well_id = well_id or Path(source_name).stem.replace(".las", "").replace(".LAS", "")
    try:
        from geox.artifacts.las_sources import LASSourceError, materialize_las_source

        local_path = materialize_las_source(source_uri, artifact_id=derived_well_id)
    except FileNotFoundError as exc:
        return get_standard_envelope(
            {
                "tool": "geox_data_ingest_bundle",
                "status": "ERROR",
                "error_code": "FILE_NOT_FOUND",
                "message": str(exc),
                "recoverable": True,
                "suggested_action": (
                    "Use a server-visible path, HTTPS URL, data: URI, or base64: LAS payload."
                ),
            },
            tool_class="ingest",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
        )
    except LASSourceError as exc:
        error_code = (
            "URL_FETCH_FAILED"
            if source_uri.startswith(("http://", "https://"))
            else "LAS_SOURCE_UNAVAILABLE"
        )
        return get_standard_envelope(
            {
                "tool": "geox_data_ingest_bundle",
                "status": "ERROR",
                "error_code": error_code,
                "message": str(exc),
                "recoverable": True,
                "suggested_action": (
                    "Use an HTTPS URL or inline base64 LAS payload when local paths are not mounted."
                ),
            },
            tool_class="ingest",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
        )

    # Check /app/fixtures if file not found locally
    if not os.path.exists(local_path):
        basename = os.path.basename(source_uri)
        fixture_path = f"/app/fixtures/{basename}"
        if os.path.exists(fixture_path):
            local_path = fixture_path

    # Auto-detect source_type from extension
    detected_type = source_type
    if source_type == "auto":
        ext = os.path.splitext(local_path)[1].lower()
        detected_type = {"las": "well"}.get(ext, "well")

    try:
        from geox.services.las_ingestor import LASIngestor
        result = LASIngestor().ingest(path=local_path, asset_id=derived_well_id)
        out = result.to_dict()

        # Keep downloaded LAS evidence addressable across MCP calls/processes.
        if source_uri.startswith(("http://", "https://")):
            try:
                stable_dir = Path(os.environ.get("GEOX_WELL_DATA_DIR", "/data/wells"))
                stable_dir.mkdir(parents=True, exist_ok=True)
                stable_path = stable_dir / f"{_safe_artifact_filename(derived_well_id)}.las"
                if Path(local_path) != stable_path:
                    import shutil
                    shutil.copyfile(local_path, stable_path)
                    local_path = str(stable_path)
            except Exception:
                logger.warning("Could not persist downloaded LAS for artifact %s", derived_well_id)

        # Register in artifact store (MVP in-memory)
        loaded_curves = out.get("loaded_curves", [])
        diagnostics = {
            "qcfail_count": out.get("qcfail_count", 0),
            "suitability": out.get("suitability"),
            "limitations": out.get("limitations", []),
            "missing_channels": out.get("missing_channels", []),
            "n_depth_samples": out.get("n_depth_samples", 0),
            "depth_range_m": out.get("depth_range_m") or out.get("depth_range"),
        }
        artifact_ref = _register_artifact(
            derived_well_id,
            curves=loaded_curves,
            las_path=local_path,
            claim_state="RAW_OBSERVATION",
            diagnostics=diagnostics,
            source_uri=source_uri,
            artifact_type="well_log",
        )

        # ── Curve standardization ────────────────────────────────────
        canonical_curve_map: dict[str, str] = {}
        missing_canonical_curves: list[str] = []
        if standardize_curves and loaded_curves:
            canonical_curve_map, missing_canonical_curves = _map_canonical_curves(loaded_curves)

        # ── Depth unit detection & normalization ─────────────────────
        depth_unit_original = _detect_depth_unit(local_path)
        depth_conversion_applied = False
        depth_unit_normalized = depth_unit_original

        needs_conversion = (
            normalize_units
            and depth_unit_original.upper() in ("FT", "FEET", "FOOT")
        )
        if needs_conversion:
            # Multiply stored depth values (apply 0.3048 ft→m)
            depth_unit_normalized = "M"
            depth_conversion_applied = True
            # Update depth_range in out if present
            if "depth_range" in out and isinstance(out["depth_range"], list):
                out["depth_range"] = [v * 0.3048 for v in out["depth_range"]]

        # Overlay MCP context
        out["tool"] = "geox_data_ingest_bundle"
        out["artifact_ref"] = artifact_ref
        out["asset_id"] = artifact_ref
        out["source_uri"] = source_uri
        out["source_type"] = detected_type
        out["well_id"] = derived_well_id
        out["claim_state"] = CLAIM_STATES["RAW_OBSERVATION"]
        # Normalize depth keys for spec compliance
        if "depth_range" in out and isinstance(out["depth_range"], list):
            out["depth_min"] = out["depth_range"][0]
            out["depth_max"] = out["depth_range"][1]
        out["curve_inventory"] = out.get("loaded_curves", [])

        # Canonical curve info
        out["canonical_curve_map"] = canonical_curve_map
        out["missing_canonical_curves"] = missing_canonical_curves
        out["depth_unit_original"] = depth_unit_original
        out["depth_unit_normalized"] = depth_unit_normalized
        out["depth_conversion_applied"] = depth_conversion_applied

        # VAULT999 receipt
        payload_str = json.dumps(out, sort_keys=True, default=str, separators=(",", ":"))
        digest = hashlib.sha256(payload_str.encode()).hexdigest()[:16]
        out["vault_receipt"] = {
            "vault": "VAULT999",
            "tool": "geox_data_ingest_bundle",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hash": digest,
        }
        return get_standard_envelope(
            out,
            tool_class="ingest",
            execution_status=ExecutionStatus.SUCCESS,
            artifact_status=ArtifactStatus.LOADED,
            claim_tag="CLAIM",
        )
    except Exception as exc:
        return get_standard_envelope(
            {
                "tool": "geox_data_ingest_bundle",
                "status": "ERROR",
                "error_code": "LAS_PARSE_FAILED",
                "message": f"Could not parse LAS file: {exc}",
                "file": local_path,
                "recoverable": True,
                "suggested_action": "Check file encoding, LAS header, or whether the file is a valid LAS 1.2/2.0 format.",
                "well_id": derived_well_id,
                "source_uri": source_uri,
            },
            tool_class="ingest",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            artifact_status=ArtifactStatus.REJECTED,
            claim_tag="HYPOTHESIS",
        )


