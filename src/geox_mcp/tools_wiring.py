# WARNING: Auto-generated from server.py to reduce monolith size.
# DITEMPA BUKAN DIBERI

import functools
import inspect
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, get_tool_domain
from geox_mcp.server import (
    _geox_annotations,
    _safe_forward,
)

logger = logging.getLogger("geox.mcp.tools_wiring")


def _parse_str_arguments(arguments: Any) -> Any:
    """F1 AMANAH: parse stringified JSON arguments into dicts.

    Some MCP transports serialize arguments as JSON strings instead of dicts.
    Pydantic rejects strings at the function signature level. This helper
    runs BEFORE Pydantic validation, converting str → dict.
    """
    if arguments is None:
        return None
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
            if isinstance(parsed, dict):
                logger.debug("ARG_PARSE: converted stringified JSON to dict")
                return parsed
            else:
                logger.warning(f"ARG_PARSE: JSON parsed but not a dict: {type(parsed)}")
                return arguments
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"ARG_PARSE: failed to parse string as JSON: {e}")
            return arguments
    return arguments


def _auto_construct_request(impl, args: dict) -> Any:
    """Auto-construct Pydantic request model from flat dict args.
    17 tools in earth_surface.py/earth_surface_2.py define functions with
    `request: SomePydanticModel` but the MCP wrapper passed flat kwargs via
    `**dict(arguments)`. This helper inspects the impl signature: if the
    first parameter is a BaseModel subclass, it constructs the model from
    flat args. Otherwise returns the raw dict for **kwargs impls.
    """
    if not args:
        return None
    try:
        sig = inspect.signature(impl)
        for _name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                try:
                    if issubclass(param.annotation, BaseModel):
                        return param.annotation(**args)
                except TypeError:
                    pass
    except Exception:
        pass
    return args  # fallback: return raw dict for **kwargs impls


async def _auto_call(impl, arguments: dict | None) -> dict[str, Any]:
    """Universal impl caller — auto-constructs Pydantic models + serializes response.

    Handles both model-based impls (`request: SomeModel`) and flat-kwargs impls.
    Serializes Pydantic response models to dict for FastMCP compatibility.
    """
    args = dict(arguments or {})
    req = _auto_construct_request(impl, args)
    if isinstance(req, BaseModel):
        result = await impl(req)
    else:
        result = await impl(**req)
    return result.model_dump() if isinstance(result, BaseModel) else result


def register_tools_on(mcp):
    # ═══════════════════════════════════════════════════════════════════════════════
    # PHASE 2 UNIFIED TOOL WIRING — forge 2026-06-23
    # Wires the 14 mode-consolidated canonical tools that exist as _unified.py
    # implementations but were never registered with FastMCP. Each wrapper
    # delegates to the unified async function via a single 'arguments' dict
    # (FastMCP rejects **kwargs). Clients call as:
    #   {"name": "geox_basin", "arguments": {"arguments": {"mode": "...", "basin_name": "..."}}}
    @mcp.tool(name="geox_biostrat_calibrate", annotations=_geox_annotations("geox_biostrat_calibrate"))
    async def _biostrat_calibrate(
        taxon_name: str = "",
        zone_code: str = "",
        scheme: str = "",
        fossil_group: str = "",
        lithology: str = "",
        environment: str = "",
        run_falsify: bool = False,
        claim: str = "",
        region: str = "",
        sample_type: str = "",
    ) -> dict[str, Any]:
        """Calibrate relative biostratigraphy into age brackets with evidence and audit receipt."""
        from geox_mcp.tools.biostrat_calibrate import geox_biostrat_calibrate as _impl

        return await _impl(
            taxon_name=taxon_name,
            zone_code=zone_code,
            scheme=scheme,
            fossil_group=fossil_group,
            lithology=lithology,
            environment=environment,
            run_falsify=run_falsify,
            claim=claim,
            region=region,
            sample_type=sample_type,
        )

    @mcp.tool(name="geox_paleobiodb_query", annotations=_geox_annotations("geox_paleobiodb_query"))
    async def _paleobiodb_query(
        mode: str = "taxa",
        name: str = "",
        taxon: str = "",
        rank: str | None = None,
        interval: str | None = None,
        cc: str | None = None,
        fossil_group: str = "calcareous_nannofossil",
        limit: int = 50,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query the Paleobiology Database (PBDB v1.2) for taxa, occurrences, and biozones.

        Modes: taxa (resolve a taxon), occurrence (fossil occurrence records), zone (biozones),
        age_intervals (ICS chronostratigraphy). Read-only, public-domain fossil data, cached 24h
        to be a good PBDB citizen.
        """
        from geox_mcp.tools.geox_paleobiodb_query import geox_paleobiodb_query as _impl

        return await _impl(
            mode=mode,
            name=name,
            taxon=taxon,
            rank=rank,
            interval=interval,
            cc=cc,
            fossil_group=fossil_group,
            limit=limit,
        )

    @mcp.tool(name="geox_well_ingest", annotations=_geox_annotations("geox_well_ingest"))
    async def _well_ingest(
        mode: str = "auto",
        source_uri: str | None = None,
        source_type: str = "auto",
        well_id: str | None = None,
        standardize_curves: bool = True,
        normalize_units: bool = True,
        content_base64: str | None = None,
        filename: str | None = None,
        target_dir: str = "/data/wells",
        overwrite: bool = False,
        batch_mode: bool = False,
        artifact_refs: list[str] | None = None,
        qc_strict: bool = True,
        source_crs: str = "unknown",
        depth_datum: str | None = None,
        file_format: str | None = None,
        las_metadata: dict[str, Any] | None = None,
        las_curve_info: list[dict[str, Any]] | None = None,
        segy_metadata: dict[str, Any] | None = None,
        seismic_metadata: dict[str, Any] | None = None,
        deviation_metadata: dict[str, Any] | None = None,
        tops_metadata: dict[str, Any] | None = None,
        field: str | None = None,
        reservoir_name: str | None = None,
        test_name: str | None = None,
        test_duration_hr: float | None = None,
        main_flow_hr: float | None = None,
        main_buildup_hr: float | None = None,
        choke_size_64ths: float | None = None,
        bhp_psi: float | None = None,
        bht_c: float | None = None,
        whp_psi: float | None = None,
        wht_c: float | None = None,
        gas_rate_mmscfd: float | None = None,
        condensate_rate_stbd: float | None = None,
        water_rate_stbd: float | None = None,
        co2_mol_pct: float | None = None,
        h2s_ppm: float | None = None,
        bsw_pct: float | None = None,
        chloride_ppm: float | None = None,
        wgr_stb_per_mmscf: float | None = None,
        permeability_md_min: float | None = None,
        permeability_md_max: float | None = None,
        skin_min: float | None = None,
        skin_max: float | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Load well log data (LAS, SEG-Y, DST, deviation, tops)."""
        from geox_mcp.tools.well_ingest import geox_well_ingest as _impl

        try:
            args = _safe_forward(
                _impl,
                {
                    "mode": mode,
                    "source_uri": source_uri,
                    "source_type": source_type,
                    "well_id": well_id,
                    "standardize_curves": standardize_curves,
                    "normalize_units": normalize_units,
                    "content_base64": content_base64,
                    "filename": filename,
                    "target_dir": target_dir,
                    "overwrite": overwrite,
                    "batch_mode": batch_mode,
                    "artifact_refs": artifact_refs,
                    "qc_strict": qc_strict,
                    "source_crs": source_crs,
                    "depth_datum": depth_datum,
                    "file_format": file_format,
                    "las_metadata": las_metadata,
                    "las_curve_info": las_curve_info,
                    "segy_metadata": segy_metadata,
                    "seismic_metadata": seismic_metadata,
                    "deviation_metadata": deviation_metadata,
                    "tops_metadata": tops_metadata,
                    "field": field,
                    "reservoir_name": reservoir_name,
                    "test_name": test_name,
                    "test_duration_hr": test_duration_hr,
                    "main_flow_hr": main_flow_hr,
                    "main_buildup_hr": main_buildup_hr,
                    "choke_size_64ths": choke_size_64ths,
                    "bhp_psi": bhp_psi,
                    "bht_c": bht_c,
                    "whp_psi": whp_psi,
                    "wht_c": wht_c,
                    "gas_rate_mmscfd": gas_rate_mmscfd,
                    "condensate_rate_stbd": condensate_rate_stbd,
                    "water_rate_stbd": water_rate_stbd,
                    "co2_mol_pct": co2_mol_pct,
                    "h2s_ppm": h2s_ppm,
                    "bsw_pct": bsw_pct,
                    "chloride_ppm": chloride_ppm,
                    "wgr_stb_per_mmscf": wgr_stb_per_mmscf,
                    "permeability_md_min": permeability_md_min,
                    "permeability_md_max": permeability_md_max,
                    "skin_min": skin_min,
                    "skin_max": skin_max,
                },
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
            result = await _impl(**args)
            if isinstance(result, dict):
                from geox_mcp.result_truth import result_is_error as _result_is_error

                _is_err_ingest = _result_is_error(result)
                result = {
                    **result,
                    "_memory": "LIVE_PROBE",
                    "_epistemic": {
                        "evidence_layer": "UNKNOWN" if _is_err_ingest else "OBS",
                        "confidence": 0.10 if _is_err_ingest else 0.85,
                        "source": "geox_well_ingest",
                        "reversible": True,
                        "authority_claim": "ADVISORY" if _is_err_ingest else "EVIDENCE",
                    },
                }
            # PR2: 3-channel UI return so hosts open Well Witness after ingest
            from geox_mcp.tools.mcp_apps_bridge import wrap_as_ui_tool_result

            _wid = well_id
            if isinstance(result, dict):
                _wid = _wid or result.get("well_id")
            elif hasattr(result, "structured_content") and isinstance(result.structured_content, dict):
                _wid = _wid or result.structured_content.get("well_id")
            _is_err = (
                bool(getattr(result, "is_error", False))
                or (
                    isinstance(result, dict)
                    and (result.get("isError") or result.get("ok") is False or result.get("status") == "INVALID")
                )
                or (
                    hasattr(result, "structured_content")
                    and isinstance(result.structured_content, dict)
                    and (
                        result.structured_content.get("status") == "INVALID"
                        or result.structured_content.get("ok") is False
                        or result.structured_content.get("execution_status") in ("ERROR", "FAILED")
                        or (
                            isinstance(result.structured_content.get("primary_artifact"), dict)
                            and result.structured_content["primary_artifact"].get("status") == "ERROR"
                        )
                    )
                )
            )
            return wrap_as_ui_tool_result(
                result,
                app_id="well_desk",
                params={"well_id": _wid} if _wid else None,
                text=(None if _is_err else f"Well ingest complete for {_wid or 'unknown'}. Open Well Witness for tracks."),
            )
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_well_ingest", source_organ="geox")

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_well_view", annotations=_geox_annotations("geox_well_view"))
    # ZEN-CONSOLIDATED — async def _well_view(
        # ZEN-CONSOLIDATED — well_id: str | None = None,
        # ZEN-CONSOLIDATED — source_uri: str | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
        # ZEN-CONSOLIDATED — max_samples: int = 2000,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Well Witness View — hydrate LAS curves into interactive tracks.

        Prompt B (2026-07-25):
          1. Resolve well_id via demo registry / data/geox_las / ingest store
             (no longer requires source_uri for DEMO-* wells).
          2. Return curves+depths for WellDesk track hydrate.
          3. Seal a content-hash receipt (VAULT999 or PENDING) on success.

        F2: DEMO fixtures carry data_class + provenance_badge — never MEASURED.
        """
        import hashlib

        from geox_mcp.tools.mcp_apps_bridge import wrap_as_ui_tool_result

        _GEOX_ROOT = Path(__file__).resolve().parents[3]
        _curves: dict[str, list[float]] = {}
        _depths: list[float] = []
        _meta: dict[str, Any] = {}
        _is_err = False
        _text = ""
        _las_path: str | None = None
        _data_class = "UNKNOWN"
        _receipt: dict[str, Any] | None = None
        _max_n = max(100, min(int(max_samples or 2000), 20000))

        def _hydrate_from_path(path: Path, wid: str | None) -> tuple[bool, str]:
            nonlocal _curves, _depths, _meta, well_id, _las_path, _data_class
            try:
                import lasio

                _las = lasio.read(str(path), ignore_header_errors=True)
                raw_depths = [float(d) for d in _las.index]
                # Downsample for UI if huge
                step = max(1, len(raw_depths) // _max_n) if len(raw_depths) > _max_n else 1
                _depths = raw_depths[::step]
                null_v = -999.25
                try:
                    null_v = float(_las.well.NULL.value)
                except Exception:
                    pass
                for _mnemonic in ("GR", "RES", "RT", "ILD", "DT", "RHOB", "NPHI"):
                    if _mnemonic in _las.keys():
                        raw = [float(v) if v == v and float(v) != null_v else float("nan") for v in _las[_mnemonic]]
                        _curves[_mnemonic] = raw[::step]
                # Prefer RES alias over RT if both missing RES
                if "RES" not in _curves and "RT" in _curves:
                    _curves["RES"] = _curves["RT"]
                well_id = wid or (str(_las.well.WELL.value).strip() if hasattr(_las.well, "WELL") else path.stem) or path.stem
                _las_path = str(path)
                _meta = {
                    "well_id": well_id,
                    "start_md": _depths[0] if _depths else None,
                    "stop_md": _depths[-1] if _depths else None,
                    "null_value": null_v,
                    "curves_loaded": list(_curves.keys()),
                    "n_samples": len(_depths),
                    "las_path": _las_path,
                    "data_class": _data_class,
                }
                if not _curves or not _depths:
                    return False, f"LAS at {path} parsed but has no usable curves/depths."
                return True, (
                    f"Well View ready for {well_id}: {len(_depths)} depth points, "
                    f"curves={list(_curves.keys())}. Tracks hydrating."
                )
            except ImportError:
                return False, "LAS hydration unavailable: lasio not installed."
            except Exception as exc:
                logger.warning("LAS_HYDRATE_FAIL: %s", exc)
                return False, f"LAS read failed: {type(exc).__name__}: {exc}"

        # ── Path 1: explicit source_uri ─────────────────────────────────
        if source_uri:
            _path = Path(source_uri)
            if not _path.is_absolute():
                _path = _GEOX_ROOT / _path
            if _path.is_file() and _path.suffix.lower() in (".las", ".LAS"):
                _data_class = "FILE"
                ok_h, msg = _hydrate_from_path(_path, well_id)
                _is_err = not ok_h
                _text = msg
            else:
                _is_err = True
                _text = f"No LAS file found at {_path}. Use geox_well_ingest or DEMO-* well_id."

        # ── Path 2: resolve well_id via demo registry / geox_las / ingest ─
        elif well_id:
            from geox_mcp.tools.integration_well import _load_well_curves_for_ui

            loaded = _load_well_curves_for_ui(well_id, max_n=_max_n)
            if loaded.get("status") == "loaded" and loaded.get("curves"):
                _curves = {k: v for k, v in (loaded.get("curves") or {}).items() if v}
                _depths = list(loaded.get("depths") or [])
                _las_path = loaded.get("las_path")
                _data_class = loaded.get("data_class") or "DEMO"
                well_id = loaded.get("well_name") or well_id
                _meta = {
                    "well_id": well_id,
                    "start_md": _depths[0] if _depths else None,
                    "stop_md": _depths[-1] if _depths else None,
                    "curves_loaded": list(_curves.keys()),
                    "n_samples": len(_depths),
                    "las_path": _las_path,
                    "data_class": _data_class,
                    "geography": loaded.get("geography"),
                    "is_fixture_fallback": loaded.get("is_fixture_fallback"),
                    "provenance_badge": loaded.get("provenance_badge"),
                    "curves_available": loaded.get("curves_available"),
                }
                _text = (
                    f"Well View ready for {well_id}: {len(_depths)} depth points, "
                    f"curves={list(_curves.keys())} "
                    f"[{_data_class}]. Tracks hydrating."
                )
                _is_err = False
            else:
                _is_err = True
                _text = (
                    loaded.get("error")
                    or f"Well '{well_id}': NOT_FOUND — no LAS resolved. "
                    "Use DEMO-KINABALU / DEMO-VOLVE or geox_well_ingest + source_uri."
                )
        else:
            _is_err = True
            _text = "Well View requires well_id or source_uri."

        # ── Prompt C: canonical artifact spine + VAULT999 receipt ──────
        _canon_ref: str | None = None
        if not _is_err and _curves and _depths:
            try:
                from geox_mcp.artifact_identity import make_artifact_id, sha256_for_file
                from geox_mcp.tools._helpers import _register_artifact

                if _las_path and Path(_las_path).is_file():
                    sha = (
                        sha256_for_file(_las_path)
                        or hashlib.sha256(
                            json.dumps({"well_id": well_id, "n": len(_depths)}, sort_keys=True).encode()
                        ).hexdigest()
                    )
                else:
                    sha = hashlib.sha256(
                        json.dumps(
                            {
                                "well_id": well_id,
                                "n_samples": len(_depths),
                                "curves": sorted(_curves.keys()),
                            },
                            sort_keys=True,
                        ).encode()
                    ).hexdigest()
                _canon_ref = make_artifact_id("well_las", f"well:{well_id}", sha)
                try:
                    _register_artifact(
                        f"well_las:{well_id}",
                        las_path=_las_path,
                        curves=list(_curves.keys()),
                        claim_state="RAW_OBSERVATION",
                        source_uri=_las_path or source_uri,
                        artifact_type="well_log",
                    )
                    _register_artifact(
                        _canon_ref,
                        las_path=_las_path,
                        curves=list(_curves.keys()),
                        claim_state="RAW_OBSERVATION",
                        source_uri=_las_path or source_uri,
                        artifact_type="well_log",
                    )
                except Exception as _reg_exc:
                    logger.debug("WELL_VIEW_REGISTER: %s", _reg_exc)
                _meta["canonical_artifact_ref"] = _canon_ref
                _meta["artifact_sha256"] = sha

                from geox_mcp.seal_receipt import RiskClass, Reversibility, seal_receipt

                seal = seal_receipt(
                    tool="geox_well_view",
                    artifact_id=_canon_ref,
                    artifact_sha256=sha,
                    actor_id=actor_id,
                    session_id=session_id,
                    verdict="QUALIFY",
                    risk_class=RiskClass.LOW,
                    reversibility=Reversibility.FULL,
                )
                _receipt = {
                    "state": seal.state,
                    "ref": seal.ref,
                    "sha256": sha,
                    "canonical_artifact_ref": _canon_ref,
                    "vault_pending": getattr(seal, "vault_pending", seal.state != "SEALED"),
                    "error": getattr(seal, "error", None),
                }
                _meta["receipt"] = _receipt
                if seal.state == "SEALED":
                    _text += f" Artifact {_canon_ref[:48]}… Receipt {seal.ref}."
                else:
                    _text += f" Artifact registered; receipt {seal.state}."
            except Exception as _seal_exc:
                logger.warning("WELL_VIEW_RECEIPT: %s", _seal_exc)
                _receipt = {"state": "FAILED", "error": type(_seal_exc).__name__}
                _meta["receipt"] = _receipt

        _structured = {
            "ok": not _is_err,
            "isError": _is_err,
            "status": (
                "NOT_FOUND" if _is_err and ("NOT_FOUND" in _text or "No LAS" in _text) else ("ERROR" if _is_err else "OK")
            ),
            "well_id": well_id,
            "mode": "view",
            "data_mode": "view" if not _is_err else "unknown",
            "source_uri": source_uri or _las_path,
            "curves": _curves,
            "depths": _depths,
            "meta": _meta,
            "message": _text,
            "data_class": _data_class,
            "receipt": _receipt,
            "canonical_artifact_ref": _canon_ref,
            "artifact_ref": _canon_ref or (f"well_las:{well_id}" if well_id and not _is_err else None),
        }
        if _is_err:
            _structured["error"] = _text
        return wrap_as_ui_tool_result(
            {
                "well_id": well_id,
                "curves": _curves,
                "depths": _depths,
                "ok": not _is_err,
                "isError": _is_err,
                "status": _structured["status"],
                "receipt": _receipt,
            },
            app_id="well_desk",
            params={"well_id": well_id} if well_id else None,
            text=_text,
            structured_override=_structured,
        )

    @mcp.tool(name="geox_well_qc", annotations=_geox_annotations("geox_well_qc"))
    async def _well_qc(
        artifact_ref: str = "",
        artifact_type: str = "well_log",
        qc_mode: str = "full",
        samples: list[dict[str, Any]] | None = None,
        existing_features: list[str] | None = None,
        candidate_feature: str | None = None,
        target_key: str = "value",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """QC: depth, curves, completeness, FJIS."""
        from geox_mcp.tools.well_qc import geox_well_qc as _impl

        args = _safe_forward(
            _impl,
            {
                "artifact_ref": artifact_ref,
                "artifact_type": artifact_type,
                "qc_mode": qc_mode,
                "samples": samples,
                "existing_features": existing_features,
                "candidate_feature": candidate_feature,
                "target_key": target_key,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_well_desurvey", annotations=_geox_annotations("geox_well_desurvey"))
    async def _well_desurvey(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """3D wellbore geometry from deviation survey.

        Phase 2.1 (2026-06-28): evidence-only. Computes TVD/X/Y/TVDSS trajectory
        using industry-standard minimum curvature method (wellpathpy). Returns
        geox.desurvey.v1 envelope with claim-tagged uncertainty.
        See forge_work/GEOX-ADAPT-001-r1.md for spec + 12 golden tests.
        """
        from geox_mcp.tools.well_desurvey import geox_well_desurvey as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    @mcp.tool(name="geox_petrophysics", annotations=_geox_annotations("geox_petrophysics"))
    async def _petrophysics(
        mode: str = "generate",
        target_class: str | None = None,
        evidence_refs: list[str] | None = None,
        realizations: int = 3,
        gr_clean: float = 15,
        gr_shale: float = 150,
        vsh_method: str = "linear",
        matrix_density: float = 2.65,
        fluid_density: float = 1.0,
        sw_model: str = "archie",
        rw: float = 0.05,
        archie_a: float = 1,
        archie_m: float = 2,
        archie_n: float = 2,
        vsh_cutoff: float = 0.5,
        phi_cutoff: float = 0.1,
        sw_cutoff: float = 0.6,
        rt_cutoff: float = 2,
        zone_top_m: float | None = None,
        zone_base_m: float | None = None,
        basin_context: str | None = None,
        canon9_profile: str = "malay_basin",
        target_depth_m: float | None = None,
        cube_inline: dict[str, Any] | None = None,
        use_synth_cube: bool = True,
        lmr_inline: dict[str, Any] | None = None,
        candidate_ref: str | None = None,
        domain: str | None = None,
        well_id: str | None = None,
        curves: dict[str, Any] | None = None,
        depth_m: list[float] | None = None,
        depth_top_m: float | None = None,
        depth_bot_m: float | None = None,
        target_properties: list[str] | None = None,
        basin: str | None = None,
        rw_ohm_m: float | None = None,
        rho_matrix_g_cc: float | None = None,
        rho_fluid_g_cc: float | None = None,
        patch_size_m: float = 0.5,
        cell_states: list[dict[str, Any]] | None = None,
        areal_extent_m2: float = 1e6,
        pay_zone_thickness_m: float = 50.0,
        formation_volume_factor: float = 1.3,
        water_saturation: float = 0.30,
        oil_density_kg_m3: float = 850.0,
        recovery_factor: float = 0.30,
        # ── causal_closure + sv_integration params (Phase 3 bridges, 2026-07-30) ──
        stratigraphic_tops: list[dict[str, Any]] | None = None,
        predicted_lithology: str = "sandstone",
        rhob_curve_g_cm3: list[float] | None = None,
        water_depth_m: float = 0.0,
        water_density_kg_m3: float = 1025.0,
        # ── multi_mineral params (Chemistry9 X3) ──
        mineral_names: list[str] | None = None,
        gr_api_value: float | None = None,
        dt_value: float | None = None,
        nphi_value: float | None = None,
        rhob_value: float | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Vsh, porosity, Sw, perm, net pay, LEM."""
        # H2 P1: Auto-inject workspace context for empty well_id/basin
        if not well_id or not basin:
            try:
                from geox_mcp.state.workspace import get_workspace

                ws = get_workspace("default")
                if not well_id and ws.well_id:
                    well_id = ws.well_id
                if not basin and ws.basin:
                    basin = ws.basin
            except Exception:
                pass

        from geox_mcp.tools.petrophysics_unified import geox_petrophysics as _impl

        try:
            args = _safe_forward(
                _impl,
                {
                    "mode": mode,
                    "target_class": target_class,
                    "evidence_refs": evidence_refs,
                    "realizations": realizations,
                    "gr_clean": gr_clean,
                    "gr_shale": gr_shale,
                    "vsh_method": vsh_method,
                    "matrix_density": matrix_density,
                    "fluid_density": fluid_density,
                    "sw_model": sw_model,
                    "rw": rw,
                    "archie_a": archie_a,
                    "archie_m": archie_m,
                    "archie_n": archie_n,
                    "vsh_cutoff": vsh_cutoff,
                    "phi_cutoff": phi_cutoff,
                    "sw_cutoff": sw_cutoff,
                    "rt_cutoff": rt_cutoff,
                    "zone_top_m": zone_top_m,
                    "zone_base_m": zone_base_m,
                    "basin_context": basin_context,
                    "canon9_profile": canon9_profile,
                    "target_depth_m": target_depth_m,
                    "cube_inline": cube_inline,
                    "use_synth_cube": use_synth_cube,
                    "lmr_inline": lmr_inline,
                    "candidate_ref": candidate_ref,
                    "domain": domain,
                    "well_id": well_id,
                    "curves": curves,
                    "depth_m": depth_m,
                    "depth_top_m": depth_top_m,
                    "depth_bot_m": depth_bot_m,
                    "target_properties": target_properties,
                    "basin": basin,
                    "rw_ohm_m": rw_ohm_m,
                    "rho_matrix_g_cc": rho_matrix_g_cc,
                    "rho_fluid_g_cc": rho_fluid_g_cc,
                    "patch_size_m": patch_size_m,
                    "cell_states": cell_states,
                    "areal_extent_m2": areal_extent_m2,
                    "pay_zone_thickness_m": pay_zone_thickness_m,
                    "formation_volume_factor": formation_volume_factor,
                    "water_saturation": water_saturation,
                    "oil_density_kg_m3": oil_density_kg_m3,
                    "recovery_factor": recovery_factor,
                    # ── Phase 3 bridge params ──
                    "stratigraphic_tops": stratigraphic_tops,
                    "predicted_lithology": predicted_lithology,
                    "rhob_curve_g_cm3": rhob_curve_g_cm3,
                    "water_depth_m": water_depth_m,
                    "water_density_kg_m3": water_density_kg_m3,
                    # ── multi_mineral params ──
                    "mineral_names": mineral_names,
                    "gr_api_value": gr_api_value,
                    "dt_value": dt_value,
                    "nphi_value": nphi_value,
                    "rhob_value": rhob_value,
                },
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
            result = await _impl(**args)
            if isinstance(result, dict):
                # Determine if the result is genuinely errored (never empty error="")
                from geox_mcp.result_truth import result_is_error as _result_is_error

                _is_error = _result_is_error(result)
                # Stage 1 outputSchema enforcement: SUCCESS with null evidence is a false success.
                # An MCP tool must NEVER claim success when it computed nothing.
                _exec_ok = result.get("execution_status") in ("SUCCESS", None)
                _net_pay_null = result.get("net_pay") is None
                _curves_empty = not result.get("curves_available") and not result.get("curves")
                _empty_compute = result.get("curves_available") == [] or result.get("curves_available") is None
                if not _is_error and _exec_ok and _net_pay_null and _empty_compute:
                    _is_error = True
                    result["execution_status"] = "ERROR"
                    result["governance_status"] = "HOLD"
                    result["status"] = "INVALID"
                    result["error"] = (
                        "EVIDENCE_SCHEMA_VIOLATION: Petrophysics returned SUCCESS but produced "
                        "no net_pay and no curves. This is a false success — the tool computed "
                        "nothing. Expected: finite Vsh/φ/Sw arrays and deterministic net_pay. "
                        "Ingest a LAS file with well_id first."
                    )
                result = {
                    **result,
                    "_memory": "LIVE_PROBE",
                    "_epistemic": {
                        "evidence_layer": "UNKNOWN" if _is_error else "DER",
                        "confidence": 0.10 if _is_error else 0.80,
                        "source": "geox_petrophysics",
                        "reversible": True,
                        "authority_claim": "ADVISORY" if _is_error else "EVIDENCE",
                    },
                }
            # PR2: 3-channel UI return → Well Witness panel
            from geox_mcp.tools.mcp_apps_bridge import wrap_as_ui_tool_result

            _wid = well_id or (result.get("well_id") if isinstance(result, dict) else None)
            # Compact structured payload for iframe (drop dense arrays from model path)
            sc_override = None
            if isinstance(result, dict):
                from geox_mcp.result_truth import result_is_error as _result_is_error

                _sc_is_err = _result_is_error(result)
                sc_override = {
                    "ok": False if _sc_is_err else result.get("ok", True),
                    "tool": "geox_petrophysics",
                    "mode": mode,
                    "well_id": _wid,
                    "band": "DERIVED",
                    "summary": {
                        "well_id": _wid,
                        "mode": mode,
                        "band": "DERIVED",
                        "note": (
                            "Petrophysics incomplete — status INVALID; ingest LAS / supply curves first."
                            if _sc_is_err
                            else "Petrophysics complete — open Well Witness for tracks."
                        ),
                    },
                    "epistemic": result.get("_epistemic")
                    or ({"layer": "UNKNOWN", "confidence_cap": 0.10} if _sc_is_err else {"layer": "DER", "confidence_cap": 0.80}),
                    "net_pay": result.get("net_pay"),
                    "status": result.get("status", "INVALID" if _sc_is_err else "computed"),
                    # Pass through compact curve summaries if already small
                    "curves_available": list((result.get("curves") or {}).keys())
                    if isinstance(result.get("curves"), dict)
                    else result.get("curves_available"),
                    "message": result.get("message") or f"Petrophysics mode={mode} well_id={_wid}",
                }
            return wrap_as_ui_tool_result(
                result,
                app_id="well_desk",
                params={"well_id": _wid, "mode": "tracks"} if _wid else None,
                structured_override=sc_override,
                text=(f"Petrophysics ({mode}) for {_wid or 'workspace'}. UI: ui://geox/well-desk. DER layer — not a seal."),
            )
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_petrophysics", source_organ="geox")

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_sequence", annotations=_geox_annotations("geox_sequence"))
    # ZEN-CONSOLIDATED — async def _sequence(
        # ZEN-CONSOLIDATED — workflow: str = "single_well",
        # ZEN-CONSOLIDATED — source: str | None = None,
        # ZEN-CONSOLIDATED — zone_top: float | None = None,
        # ZEN-CONSOLIDATED — zone_base: float | None = None,
        # ZEN-CONSOLIDATED — depo_env_code: str = "FLUVIAL",
        # ZEN-CONSOLIDATED — bin_size_m: float = 10.0,
        # ZEN-CONSOLIDATED — min_package_thickness_m: float = 20.0,
        # ZEN-CONSOLIDATED — p50_shift_api: float = 15.0,
        # ZEN-CONSOLIDATED — gr_cutoff_api: float = 75.0,
        # ZEN-CONSOLIDATED — detail_level: str = "full",
        # ZEN-CONSOLIDATED — project_yaml: str | None = None,
        # ZEN-CONSOLIDATED — output_dir: str | None = None,
        # ZEN-CONSOLIDATED — section_ref: str | None = None,
        # ZEN-CONSOLIDATED — well_refs: list[str] | None = None,
        # ZEN-CONSOLIDATED — mode: str = "correlation",
        # ZEN-CONSOLIDATED — well_las_paths: list[str] | None = None,
        # ZEN-CONSOLIDATED — tops: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — zone_definitions: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — strat_standard: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — paleoenvironment_input: list[dict[str, Any]] | None = None,
        # ZEN-CONSOLIDATED — checkshot_ref: str | None = None,
        # ZEN-CONSOLIDATED — wavelet_mode: str = "ricker",
        # ZEN-CONSOLIDATED — wavelet_freq_hz: list[float] | None = None,
        # ZEN-CONSOLIDATED — phase_degrees: float = 0.0,
        # ZEN-CONSOLIDATED — polarity: str = "SEG_NORMAL",
        # ZEN-CONSOLIDATED — synthetics_output: bool = False,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Sequence stratigraphy, correlation. Pattern A wrapper — see sequence_unified.geox_sequence."""
        from geox_mcp.tools.sequence_unified import geox_sequence as _impl

        args = _safe_forward(
            _impl,
            {
                "workflow": workflow,
                "source": source,
                "zone_top": zone_top,
                "zone_base": zone_base,
                "depo_env_code": depo_env_code,
                "bin_size_m": bin_size_m,
                "min_package_thickness_m": min_package_thickness_m,
                "p50_shift_api": p50_shift_api,
                "gr_cutoff_api": gr_cutoff_api,
                "detail_level": detail_level,
                "project_yaml": project_yaml,
                "output_dir": output_dir,
                "section_ref": section_ref,
                "well_refs": well_refs,
                "mode": mode,
                "well_las_paths": well_las_paths,
                "tops": tops,
                "zone_definitions": zone_definitions,
                "strat_standard": strat_standard,
                "paleoenvironment_input": paleoenvironment_input,
                "checkshot_ref": checkshot_ref,
                "wavelet_mode": wavelet_mode,
                "wavelet_freq_hz": wavelet_freq_hz,
                "phase_degrees": phase_degrees,
                "polarity": polarity,
                "synthetics_output": synthetics_output,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    # ── SURFACE DISCOVERY — Federation Standard Registry Tool ────────────────────
    # GAP-1 FIX (2026-06-27): Every organ MUST expose <organ>_surface_status.
    # This is the non-judgment-lane discovery tool. Any MCP client can call it.
    # Returns canonical surface — 16 tools, not the 47 registered ghosts.
    # Mode registry: tool list + domains
    # Mode health: service status
    # DITEMPA BUKAN DIBERI.

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_surface_status", annotations=_geox_annotations("geox_surface_status"))
    # ZEN-CONSOLIDATED — async def geox_surface_status(  # noqa: PLR0915 — surface probe
        # ZEN-CONSOLIDATED — mode: str = "registry",
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Federation-standard registry probe for GEOX.

        Use this to discover what GEOX actually exposes.
        Not geox_system_registry_status (removed Phase 1).
        Not geox_doctrine (judgment lane, arifOS-only).

        Modes:
          registry  — canonical tool list + domains + affordance summary
          health    — service status, version, uptime

        This is the GAP-1 fix: one standard name across all organs.
        WEALTH has wealth_system_registry_status. GEOX now has geox_surface_status.
        arifOS has arifOS tools for the same purpose.
        """
        import datetime
        import subprocess

        try:
            git_version = (
                "geox-"
                + subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
            )
        except Exception:
            git_version = "geox-unknown"

        if mode == "health":
            return {
                "status": "healthy",
                "organ": "GEOX",
                "version": "v2026.06.22-phase2",
                "git_version": git_version,
                "canonical_tools": len(CANONICAL_PUBLIC_TOOLS),
                "mcp_transport": "http",
                "mcp_port": 8081,
                "registered_at": datetime.datetime.now(datetime.UTC).isoformat(),
            }

        # registry mode — WELL-style rich drift report
        # Domain sourced from GEOX_TOOL_MANIFEST via get_tool_domain() (registry.py).
        # Single source of truth — structured manifest replaces hardcoded inline dict.
        from geox_mcp.surface_manifest import manifest_tool_map

        canonical_set = set(CANONICAL_PUBLIC_TOOLS)
        all_manifest = manifest_tool_map()

        canonical_list = []
        phantom_list = []
        internal_list = []

        for tool_name, entry in sorted(all_manifest.items()):
            domain = entry.domain if hasattr(entry, "domain") else get_tool_domain(tool_name)
            if tool_name in canonical_set:
                canonical_list.append(
                    {
                        "name": tool_name,
                        "domain": domain,
                        "affordance": {
                            "action_class": "ANALYZE"
                            if tool_name.startswith("geox_")
                            and "claim" not in tool_name
                            and "doctrine" not in tool_name
                            and "evidence" not in tool_name
                            and "prospect" not in tool_name
                            else "OBSERVE",
                            "mutation": False,
                            "irreversible": False,
                            "requires_888_hold": tool_name in ("geox_claim", "geox_prospect"),
                            "final_authority": "ARIF",
                        },
                    }
                )
            elif entry.is_internal if hasattr(entry, "is_internal") else False:
                internal_list.append(tool_name)
            else:
                phantom_list.append(tool_name)

        # Multi-surface parity (manifest / runtime / plugin export / docs snapshot)
        from geox_mcp.surface_manifest import plugin_export_tool_names, surface_attestation
        from geox_mcp.tools.registry import (
            _load_generated_public_surface,
            _load_plugin_export_surface,
        )

        expected_app_export = set(plugin_export_tool_names())
        plugin_export_public = _load_plugin_export_surface() or expected_app_export
        generated_public = _load_generated_public_surface() or set(canonical_set)
        plugin_export_only = sorted(plugin_export_public - expected_app_export)
        missing_from_app_export = sorted(expected_app_export - plugin_export_public)
        generated_only = sorted(generated_public - set(canonical_set))
        missing_from_generated = sorted(set(canonical_set) - generated_public)

        attestation = surface_attestation()
        has_drift = bool(
            phantom_list
            or plugin_export_only
            or missing_from_app_export
            or generated_only
            or missing_from_generated
            or expected_app_export != set(canonical_set)
            or not attestation.get("ok")
            or attestation.get("public_count") != len(canonical_set)
        )
        # FAIL-CLOSED REGISTRY INVARIANT (KUTIP SAMPAH 2026-08-04):
        # The organ CANNOT report healthy while manifests diverge or
        # public_count exceeds public_count_target.
        public_count_target = attestation.get("public_count_target")
        over_target = public_count_target is not None and len(canonical_set) > public_count_target
        status = "degraded" if (has_drift or over_target) else "healthy"

        return {
            "status": status,
            "organ": "GEOX",
            "surface_version": attestation.get("surface_version") or "geox-zen15-2026.07.24",
            "surface_name": attestation.get("surface_name") or "ZEN-15",
            "surface_hash": attestation.get("surface_hash"),
            "surface_attestation": attestation,
            "canonical_callable": canonical_list,
            "canonical_tools": sorted(canonical_set),
            "intended_tools": len(all_manifest),
            "registered_tools": len(all_manifest),
            "callable_tools": len(canonical_list),
            "public_count": len(canonical_set),
            "public_count_target": attestation.get("public_count_target") or len(canonical_set),
            "phantom_tools": phantom_list,
            "internal_tools": internal_list,
            "plugin_export_public": sorted(plugin_export_public),
            "expected_app_export": sorted(expected_app_export),
            "plugin_export_only_tools": plugin_export_only,
            "missing_from_app_export": missing_from_app_export,
            "generated_public_only": generated_only,
            "missing_from_generated": missing_from_generated,
            "deprecated_callable": [],
            "alias_conflicts": [],
            "registry_truth": "DRIFT" if has_drift else "PASS",
            "verdict": "REGISTRY_DRIFT" if has_drift else "REGISTRY_PASS",
            "perception_class": "OBSERVED",
            "claim_state": "OBSERVED",
            "evidence_tag": "COMPUTED",
            "confidence_level": "HIGH",
            "humility_score": 0.05,
            "registered_at": __import__("datetime", fromlist=["datetime"])
            .datetime.now(__import__("datetime", fromlist=["datetime"]).timezone.utc)
            .isoformat(),
        }

    @mcp.tool(name="geox_seismic_ingest", annotations=_geox_annotations("geox_seismic_ingest"))
    async def _seismic_ingest(
        mode: str = "inspect_segy",
        volume_ref: str | None = None,
        output_path: str | None = None,
        sample_interval_ms: float = 4,
        textual_header: str = "",
        overwrite: bool = False,
        provenance: str = "fixture",
        segy_metadata: dict[str, Any] | None = None,
        seismic_metadata: dict[str, Any] | None = None,
        source_uri: str | None = None,
        source_type: str = "seismic",
        well_id: str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """SEG-Y I/O, header inspection."""
        from geox_mcp.tools.seismic_ingest import geox_seismic_ingest as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode,
                "volume_ref": volume_ref,
                "output_path": output_path,
                "sample_interval_ms": sample_interval_ms,
                "textual_header": textual_header,
                "overwrite": overwrite,
                "provenance": provenance,
                "segy_metadata": segy_metadata,
                "seismic_metadata": seismic_metadata,
                "source_uri": source_uri,
                "source_type": source_type,
                "well_id": well_id,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    @mcp.tool(name="geox_seismic_interpret", annotations=_geox_annotations("geox_seismic_interpret"))
    async def _seismic_interpret(
        mode: str = "horizon_contrast",
        # P0: public schema must accept horizon_contrast inputs (sovereign 2026-07-23)
        attribute_data: dict[str, list[float]] | None = None,
        depth: list[float] | None = None,
        geological_query: str = "sequence_boundary",
        well_ties: dict[str, float] | None = None,
        peak_threshold: float = 1.5,
        min_separation_m: float = 20.0,
        custom_query: dict[str, float] | None = None,
        source_uri: str = "",
        source_type: str = "csv",
        action: str = "get",
        volume_ref: str = "",
        frame_index: int = 0,
        orientation: str = "inline",
        provenance: str = "fixture",
        image_data: str | None = None,
        blend_mode: str = "alpha",
        horizon_query: str = "unconformity",
        threshold: float = 0.5,
        confidence_cap: float = 0.9,
        cube_ref: str | None = None,
        volume_inline: dict[str, Any] | None = None,
        # Phase C/A/D + B-final bundle
        image_path: str | None = None,
        artifact_ref: str | None = None,
        framework: dict[str, Any] | None = None,
        faults: list[dict[str, Any]] | None = None,
        horizons: list[dict[str, Any]] | None = None,
        measurement_context: dict[str, Any] | None = None,
        calibration: dict[str, Any] | None = None,
        earth_constraints: dict[str, Any] | None = None,
        request: dict[str, Any] | None = None,
        segy_path: str | None = None,
        max_faults: int = 20,
        max_horizons: int = 12,
        emit_bundle: bool = True,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """One semantic capability: propose geometry, physics-gate, compare hypotheses.

        Modes: horizon_contrast, fault_sticks, volume_frame, blend, structure_validate,
        interpret, interpret_section/rsi_pipeline, segy_slice.
        Local verdict QUALIFIED_CANDIDATE only. preferred_hypothesis always null from GEOX.
        """
        from geox_mcp.tools.seismic_interpret import geox_seismic_interpret as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode,
                "attribute_data": attribute_data,
                "depth": depth,
                "geological_query": geological_query,
                "well_ties": well_ties,
                "peak_threshold": peak_threshold,
                "min_separation_m": min_separation_m,
                "custom_query": custom_query,
                "source_uri": source_uri,
                "source_type": source_type,
                "action": action,
                "volume_ref": volume_ref,
                "frame_index": frame_index,
                "orientation": orientation,
                "provenance": provenance,
                "image_data": image_data,
                "blend_mode": blend_mode,
                "horizon_query": horizon_query,
                "threshold": threshold,
                "confidence_cap": confidence_cap,
                "cube_ref": cube_ref,
                "volume_inline": volume_inline,
                "image_path": image_path,
                "artifact_ref": artifact_ref,
                "framework": framework,
                "faults": faults,
                "horizons": horizons,
                "measurement_context": measurement_context,
                "calibration": calibration,
                "earth_constraints": earth_constraints,
                "request": request,
                "segy_path": segy_path,
                "max_faults": max_faults,
                "max_horizons": max_horizons,
                "emit_bundle": emit_bundle,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    # DEREGISTERED ZEN-15 — @mcp.tool(name="geox_vision", annotations=_geox_annotations("geox_vision"))
    async def _vision(
        mode: str = "infer_minimax",
        image_path: str = "",
        basin_context: str = "unknown",
        interpretation_goal: str = "Identify structural features",
        has_segy: bool = False,
        mimo_backend_url: str | None = None,
        mimo_model: str | None = None,
        mcp_url: str | None = None,
        model_id: str = "minimax-M3-vision",
        perceptual_inventory: dict[str, Any] | None = None,
        ground_truth_inventory: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """VLM inference, audit, calibration, perceptual."""
        from geox_mcp.tools.vision_unified import geox_vision as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode,
                "image_path": image_path,
                "basin_context": basin_context,
                "interpretation_goal": interpretation_goal,
                "has_segy": has_segy,
                "mimo_backend_url": mimo_backend_url,
                "mimo_model": mimo_model,
                "mcp_url": mcp_url,
                "model_id": model_id,
                "perceptual_inventory": perceptual_inventory,
                "ground_truth_inventory": ground_truth_inventory,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    # ── SEISMIC VISION AI — 4 modes (Phase 3.2, 2026-07-06) ────────────────────
    # Cognitive visual AI taxonomy: OBS_IMAGE / DER_RENDER_ENHANCEMENT / GEN_HYPOTHESIS / DER_COGNITIVE_RENDER

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_visual_understand", annotations=_geox_annotations("geox_visual_understand"))
    # ZEN-CONSOLIDATED — async def _visual_understand(
        # ZEN-CONSOLIDATED — image_path: str = "",
        # ZEN-CONSOLIDATED — mode: str = "full",
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """OBS_IMAGE perception assist. Without VLM backend returns HOLD (no fabricated structure).

        image_path: absolute path to seismic image on the host.
        Does NOT produce OBS_GEOLOGY. Max local verdict QUALIFIED_CANDIDATE.
        """
        from geox_mcp.tools.mcp_apps_bridge import wrap_as_ui_tool_result
        from geox_mcp.tools.seismic_vision_ai_async import geox_visual_understand_async as _impl

        result = await _impl(image_path=image_path or "", mode=mode or "full")
        is_hold = isinstance(result, dict) and (result.get("status") in ("HOLD", "VOID") or result.get("ok") is False)
        text = (
            f"Visual understand HOLD: {result.get('error') or result.get('reason') or 'no backend'}"
            if is_hold
            else "Visual understand complete (OBS_IMAGE only). UI: ui://geox/visual-hub."
        )
        # Preserve full result — do not compact away HOLD truth (F2)
        return wrap_as_ui_tool_result(
            result,
            app_id="visual_hub",
            structured_override=result if isinstance(result, dict) else {"data": result},
            text=text,
        )

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_visual_enhance", annotations=_geox_annotations("geox_visual_enhance"))
    async def _visual_enhance(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Enhance seismic readability. epistemic: DER_RENDER_ENHANCEMENT."""
        from geox_mcp.tools.seismic_vision_ai_async import geox_visual_enhance_async as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # KUTIP SAMPAH 2026-08-05 H1/W5 — deregistered public leak
    # @mcp.tool(name="geox_visual_generate_hypotheses", annotations=_geox_annotations("geox_visual_generate_hypotheses"))
    async def _visual_generate_hypotheses(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate visual alternatives across discontinuity gaps. epistemic: GEN_HYPOTHESIS."""
        from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui, wrap_as_ui_tool_result
        from geox_mcp.tools.seismic_vision_ai_async import geox_visual_generate_hypotheses_async as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        result = await _impl(**args)
        return wrap_as_ui_tool_result(
            result,
            app_id="visual_hub",
            structured_override=compact_structured_for_ui(
                result if isinstance(result, dict) else {"data": result},
                tool="geox_visual_generate_hypotheses",
                app_id="visual_hub",
            ),
            text="Visual hypotheses generated. UI: ui://geox/visual-hub.",
        )

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_panel_d_render", annotations=_geox_annotations("geox_panel_d_render"))
    async def _panel_d_render(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Render cognitive interpretation dashboard. epistemic: DER_COGNITIVE_RENDER."""
        from geox_mcp.tools.seismic_vision_ai_async import geox_panel_d_render_async as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # GEOX-ZEN 2026-08-04 — RE-REGISTERED (M2 — Stage 444 compare)
    @mcp.tool(name="geox_physical_reality_interpret", annotations=_geox_annotations("geox_physical_reality_interpret"))
    async def _physical_reality_interpret(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Multi-attribute physical reality gate + horizon/fault extraction. epistemic: OBS→DER→INT."""
        from geox_mcp.tools.geox_physical_reality_async import geox_physical_reality_interpret as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_cognitive_rank_hypotheses", annotations=_geox_annotations("geox_cognitive_rank_hypotheses"))
    async def _cognitive_rank_hypotheses(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Rank geological hypotheses by basin prior. epistemic: INT_SEISMIC."""
        from geox_mcp.tools.geox_geological_cognition_async import geox_cognitive_rank_hypotheses as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_segy_audit", annotations=_geox_annotations("geox_segy_audit"))
    async def _segy_audit(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Full SEG-Y trace reality pipeline. epistemic: OBS_SEGY_TRACE."""
        from geox_mcp.tools.geox_segy_trace_reality_async import geox_segy_audit as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_well_tie", annotations=_geox_annotations("geox_well_tie"))
    async def _well_tie(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Well-to-seismic tie via bruges. epistemic: DER_SYNTHETIC → INT_GEOLOGY_HORIZON."""
        from geox_mcp.tools.geox_well_tie_bruges_async import geox_well_tie as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_3d_model", annotations=_geox_annotations("geox_3d_model"))
    async def _3d_model(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """3D structural model via GemPy from 2D picks. epistemic: INT_3D_STRUCTURE."""
        from geox_mcp.tools.geox_3d_modeling_gempy_async import geox_3d_model as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_wealth_consequence", annotations=_geox_annotations("geox_wealth_consequence"))
    async def _wealth_consequence(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Capital consequence via WEALTH HarnessEngine. epistemic: CAPITAL_CONSEQUENCE."""
        from geox_mcp.tools.geox_wealth_bridge_async import geox_wealth_consequence as _impl

        args = _safe_forward(_impl, arguments or {}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_subsurface_model", annotations=_geox_annotations("geox_subsurface_model"))
    # ZEN-CONSOLIDATED — async def _subsurface_model(
        # ZEN-CONSOLIDATED — mode: str = "joint_inversion",
        # ZEN-CONSOLIDATED — survey_type: str = "gravity",
        # ZEN-CONSOLIDATED — easting_m: tuple[float, ...] | None = None,
        # ZEN-CONSOLIDATED — northing_m: tuple[float, ...] | None = None,
        # ZEN-CONSOLIDATED — prisms: list[dict[str, Any]] | None = None,
        # ZEN-CONSOLIDATED — magnetization_a_m: float = 0.0,
        # ZEN-CONSOLIDATED — field_declination_deg: float = 0.0,
        # ZEN-CONSOLIDATED — field_inclination_deg: float = 0.0,
        # ZEN-CONSOLIDATED — layers: list[dict[str, Any]] | None = None,
        # ZEN-CONSOLIDATED — frequencies_hz: list[float] | None = None,
        # ZEN-CONSOLIDATED — observations: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — prior: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — max_iter: int = 50,
        # ZEN-CONSOLIDATED — tolerance: float = 0.001,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Joint inversion, gravity/mag, MT forward."""
        from geox_mcp.tools.subsurface_model import geox_subsurface_model as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode,
                "survey_type": survey_type,
                "easting_m": easting_m,
                "northing_m": northing_m,
                "prisms": prisms,
                "magnetization_a_m": magnetization_a_m,
                "field_declination_deg": field_declination_deg,
                "field_inclination_deg": field_inclination_deg,
                "layers": layers,
                "frequencies_hz": frequencies_hz,
                "observations": observations,
                "prior": prior,
                "max_iter": max_iter,
                "tolerance": tolerance,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    @mcp.tool(name="geox_basin", annotations=_geox_annotations("geox_basin"))
    async def _basin(
        mode: str = "profile",
        name: str = "",
        basin_name: str = "",
        macrostrat_mode: str = "macrostrat_units",
        lat: float | None = None,
        lng: float | None = None,
        age_ma: float | None = None,
        age_top_ma: float | None = None,
        age_bot_ma: float | None = None,
        period: str | None = None,
        query: str | None = None,
        include_pending_datasets: bool = True,
        force: bool = False,
        intent: str = "general",
        bbox: list[float] | None = None,
        scene_mode: str = "bbox_context",
        crs: str = "EPSG:4326",
        vp_slice_inline: dict[str, Any] | None = None,
        profile_mode: str = "overview",
        claim_strictness: str = "screen",
        evidence_refs: list[str] | None = None,
        include_missing_evidence: bool = True,
        # P0+P1 tectonic kernel parameters (2026-07-03)
        reconstruct_mode: str = "position",
        model: str = "Merdith2021",
        models: list[str] | None = None,
        rift_mode: str = "full",
        beta: float | None = None,
        crust_initial_km: float | None = None,
        crust_current_km: float | None = None,
        time_since_rift_ma: float = 0.0,
        subsidence_rate_mm_yr: float | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Profile, resolve, macrostrat, deep_time, emag2, icgem, intake, scene.

        Pattern A (explicit params) — fastmcp 3.4.2 does not support **kwargs in tool
        signatures, so every parameter of basin_unified.geox_basin is declared here.
        Session metadata is forwarded only if the impl signature accepts it.
        """
        # H2 P1: Auto-inject workspace context for empty basin_name
        if not basin_name:
            try:
                from geox_mcp.state.workspace import get_workspace

                ws = get_workspace("default")
                if ws.basin:
                    basin_name = ws.basin
            except Exception:
                pass

        from geox_mcp.tools.basin_unified import geox_basin as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode,
                "name": name,
                "basin_name": basin_name,
                "macrostrat_mode": macrostrat_mode,
                "lat": lat,
                "lng": lng,
                "age_ma": age_ma,
                "age_top_ma": age_top_ma,
                "age_bot_ma": age_bot_ma,
                "period": period,
                "query": query,
                "include_pending_datasets": include_pending_datasets,
                "force": force,
                "intent": intent,
                "bbox": bbox,
                "scene_mode": scene_mode,
                "crs": crs,
                "vp_slice_inline": vp_slice_inline,
                "profile_mode": profile_mode,
                "claim_strictness": claim_strictness,
                "evidence_refs": evidence_refs,
                "include_missing_evidence": include_missing_evidence,
                # P0+P1
                "reconstruct_mode": reconstruct_mode,
                "model": model,
                "models": models,
                "rift_mode": rift_mode,
                "beta": beta,
                "crust_initial_km": crust_initial_km,
                "crust_current_km": crust_current_km,
                "time_since_rift_ma": time_since_rift_ma,
                "subsidence_rate_mm_yr": subsidence_rate_mm_yr,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        result = await _impl(**args)
        # PR3: 3-channel UI → basin-explorer
        from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui, wrap_as_ui_tool_result

        _bname = basin_name or name or (result.get("basin_name") if isinstance(result, dict) else "")
        return wrap_as_ui_tool_result(
            result,
            app_id="basin_explorer",
            params={"basin_name": _bname, "mode": mode} if _bname else {"mode": mode},
            structured_override=compact_structured_for_ui(
                result if isinstance(result, dict) else {"data": result},
                tool="geox_basin",
                app_id="basin_explorer",
            ),
            text=f"Basin {mode}: {_bname or 'unspecified'}. UI: ui://geox/basin-explorer.",
        )

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_claim", annotations=_geox_annotations("geox_claim"))
    # ZEN-CONSOLIDATED — async def _claim(
        # ZEN-CONSOLIDATED — mode: str = "create",
        # ZEN-CONSOLIDATED — claim_id: str = "",
        # ZEN-CONSOLIDATED — claim_text: str = "",
        # ZEN-CONSOLIDATED — claim_type: str = "other",
        # ZEN-CONSOLIDATED — truth_class: str = "INTERPRETATION",
        # ZEN-CONSOLIDATED — evidence_ids: list[str] | None = None,
        # ZEN-CONSOLIDATED — uncertainty_p10: float | None = None,
        # ZEN-CONSOLIDATED — uncertainty_p50: float | None = None,
        # ZEN-CONSOLIDATED — uncertainty_p90: float | None = None,
        # ZEN-CONSOLIDATED — uncertainty_distribution: str = "lognormal",
        # ZEN-CONSOLIDATED — alternatives: list[dict[str, Any]] | None = None,
        # ZEN-CONSOLIDATED — provenance: str = "GEOX Claim Engine",
        # ZEN-CONSOLIDATED — authority: str = "GEOX_CLAIM_WORKER",
        # ZEN-CONSOLIDATED — challenge_text: str = "",
        # ZEN-CONSOLIDATED — alternative_claim_text: str = "",
        # ZEN-CONSOLIDATED — alternative_evidence_ids: list[str] | None = None,
        # ZEN-CONSOLIDATED — challenge_evidence_ids: list[str] | None = None,
        # ZEN-CONSOLIDATED — alternative_uncertainty: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — challenger_provenance: str = "GEOX Claim Engine",
        # ZEN-CONSOLIDATED — ack_irreversible: bool = False,
        # ZEN-CONSOLIDATED — seal_verdict: str = "SEAL",
        # ZEN-CONSOLIDATED — voxel_state: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — evidence_id: str = "",
        # ZEN-CONSOLIDATED — evidence_type: str = "supporting",
        # ZEN-CONSOLIDATED — epistemic_label: str | None = None,
        # ZEN-CONSOLIDATED — forbidden_uses: list[str] | None = None,
        # ZEN-CONSOLIDATED — source_citation: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — category: str | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Create, validate, challenge, seal, attach."""
        from geox_mcp.tools.claim_unified import geox_claim as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode,
                "claim_id": claim_id,
                "claim_text": claim_text,
                "claim_type": claim_type,
                "truth_class": truth_class,
                "evidence_ids": evidence_ids,
                "uncertainty_p10": uncertainty_p10,
                "uncertainty_p50": uncertainty_p50,
                "uncertainty_p90": uncertainty_p90,
                "uncertainty_distribution": uncertainty_distribution,
                "alternatives": alternatives,
                "provenance": provenance,
                "authority": authority,
                "challenge_text": challenge_text,
                "alternative_claim_text": alternative_claim_text,
                "alternative_evidence_ids": alternative_evidence_ids,
                "challenge_evidence_ids": challenge_evidence_ids,
                "alternative_uncertainty": alternative_uncertainty,
                "challenger_provenance": challenger_provenance,
                "ack_irreversible": ack_irreversible,
                "seal_verdict": seal_verdict,
                "voxel_state": voxel_state,
                "evidence_id": evidence_id,
                "evidence_type": evidence_type,
                "epistemic_label": epistemic_label,
                "forbidden_uses": forbidden_uses,
                "source_citation": source_citation,
                "category": category,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
            ack_irreversible=ack_irreversible,
        )
        result = await _impl(**args)
        # PR3: 3-channel UI → risk-console
        from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui, wrap_as_ui_tool_result

        return wrap_as_ui_tool_result(
            result,
            app_id="risk_console",
            params={"mode": mode, "claim_id": claim_id} if claim_id else {"mode": mode},
            structured_override=compact_structured_for_ui(
                result if isinstance(result, dict) else {"data": result},
                tool="geox_claim",
                app_id="risk_console",
            ),
            text=f"Claim {mode}: {(claim_id or claim_text or '')[:80]}. UI: ui://geox/risk-console.",
        )

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_falsify", annotations=_geox_annotations("geox_falsify"))
    # ZEN-CONSOLIDATED — async def _falsify(
        # ZEN-CONSOLIDATED — claim_text: str = "",
        # ZEN-CONSOLIDATED — claim_type: str = "general",
        # ZEN-CONSOLIDATED — mode: str = "full",
        # ZEN-CONSOLIDATED — context: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — evidence: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Popperian falsification engine. Tests a geological claim against physical, stratigraphic, and logical constraints. Any check FALSIFIED → overall FALSIFIED. Science advances by eliminating what CANNOT be true. DITEMPA BUKAN DIBERI."""
        from geox_mcp.tools.claim_unified import geox_falsify as _impl

        args = _safe_forward(
            _impl,
            {
                "claim_text": claim_text,
                "claim_type": claim_type,
                "mode": mode,
                "context": context,
                "evidence": evidence,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        result = await _impl(**args)
        # PR3: 3-channel UI → judge-console
        from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui, wrap_as_ui_tool_result

        verdict = result.get("verdict") if isinstance(result, dict) else None
        return wrap_as_ui_tool_result(
            result,
            app_id="judge_console",
            params={"mode": mode},
            structured_override=compact_structured_for_ui(
                result if isinstance(result, dict) else {"data": result},
                tool="geox_falsify",
                app_id="judge_console",
            ),
            text=f"Falsify {mode}: verdict={verdict}. claim={(claim_text or '')[:60]}. UI: ui://geox/judge-console.",
        )

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_evidence_synthesize", annotations=_geox_annotations("geox_evidence_synthesize"))
    # ZEN-CONSOLIDATED — async def _evidence_synthesize(
        # ZEN-CONSOLIDATED — mode: str = "synthesize",
        # ZEN-CONSOLIDATED — query: str = "",
        # ZEN-CONSOLIDATED — scope: str = "all",
        # ZEN-CONSOLIDATED — permission_level: str = "authorized",
        # ZEN-CONSOLIDATED — file_path: str = "",
        # ZEN-CONSOLIDATED — basin_name: str | None = None,
        # ZEN-CONSOLIDATED — evidence_refs: list[str] | None = None,
        # ZEN-CONSOLIDATED — hypotheses: list[str] | None = None,
        # ZEN-CONSOLIDATED — scale: str = "parasequence",
        # ZEN-CONSOLIDATED — depo_context: str = "unknown",
        # ZEN-CONSOLIDATED — claim_strictness: str = "screen",
        # ZEN-CONSOLIDATED — reasoning_mode: str = "default",
        # ZEN-CONSOLIDATED — samples: list[dict[str, Any]] | None = None,
        # ZEN-CONSOLIDATED — block_size_km: float = 5.0,
        # ZEN-CONSOLIDATED — n_folds: int = 5,
        # ZEN-CONSOLIDATED — target_key: str = "value",
        # ZEN-CONSOLIDATED — feature_keys: list[str] | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Discover, synthesize, abduct, contradict, literature. Pattern A wrapper."""
        from geox_mcp.tools.evidence_unified import geox_evidence as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode,
                "query": query,
                "scope": scope,
                "permission_level": permission_level,
                "file_path": file_path,
                "basin_name": basin_name,
                "evidence_refs": evidence_refs,
                "hypotheses": hypotheses,
                "scale": scale,
                "depo_context": depo_context,
                "claim_strictness": claim_strictness,
                "reasoning_mode": reasoning_mode,
                "samples": samples,
                "block_size_km": block_size_km,
                "n_folds": n_folds,
                "target_key": target_key,
                "feature_keys": feature_keys,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    @mcp.tool(name="geox_prospect", annotations=_geox_annotations("geox_prospect"))
    async def _prospect(
        prospect_ref: str | None = None,
        mode: str = "screen",
        evidence_refs: list[str] | None = None,
        verdict: str = "compute",
        judge_pin: str | None = None,
        structural_map_inline: dict[str, Any] | None = None,
        power_params: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
        ack_irreversible: bool = False,
    ) -> dict[str, Any]:
        """Volumetrics, POS, EVOI, risk assessment. Pattern A wrapper."""
        # H2 P1: Auto-inject workspace context for empty prospect_ref
        if not prospect_ref:
            try:
                from geox_mcp.state.workspace import get_workspace

                ws = get_workspace("default")
                if ws.prospect_ref:
                    prospect_ref = ws.prospect_ref
            except Exception:
                pass

        from geox_mcp.tools.prospect_unified import geox_prospect as _impl

        args = _safe_forward(
            _impl,
            {
                "prospect_ref": prospect_ref,
                "mode": mode,
                "evidence_refs": evidence_refs,
                "verdict": verdict,
                "judge_pin": judge_pin,
                "structural_map_inline": structural_map_inline,
                "power_params": power_params,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
            ack_irreversible=ack_irreversible,
        )
        return await _impl(**args)

    # INTERNAL-ONLY 2026-06-27: judgment lane — removed from MCP facade
    # NOTE: by lane policy, geox_doctrine is in the judgment lane and cannot be
    # called directly from non-arifOS clients. Use arifOS judge → GEOX path.
    async def _doctrine(
        mode: str = "anti_beautiful_one",
        introduced_by: str = "",
        rung_origin: int = 0,
        description: str | None = None,
        parent_assumption_id: str | None = None,
        inherited_from: str | None = None,
        epistemic_label: str = "DER",
        claim_id: str = "",
        action: str = "review",
        void_reason: str | None = None,
        rung: int | None = None,
        depends_on_assumption_ids: list[str] | None = None,
        concept: str = "",
        query: str = "",
        state: dict[str, Any] | None = None,
        age_ma: float = 0,
        tile_id: str = "",
        task: str = "land_cover",
        bands: list[str] | None = None,
        time_range_start: str = "2024-01-01",
        time_range_end: str = "2024-12-31",
        cloud_cover_max: float = 0.2,
        source_uri: str | None = None,
        text: str = "",
        grounding_evidence_count: int = 0,
        grounding_evidence_rungs: list[int] | None = None,
        threshold: float = 1.5,
        include_decomposition: bool = True,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Anti-Beautiful-One, assumptions, Gödel, guards. Use mode='registry' for tool discovery.

        NOTE: by lane policy, geox_doctrine is in the judgment lane and cannot be
        called directly from non-arifOS clients. Use arifOS judge → GEOX path.
        Pattern A wrapper — every doctrine_unified.geox_doctrine param declared.
        """
        from geox_mcp.tools.doctrine_unified import geox_doctrine as _impl

        args: dict[str, Any] = {
            "mode": mode,
            "introduced_by": introduced_by,
            "rung_origin": rung_origin,
            "description": description,
            "parent_assumption_id": parent_assumption_id,
            "inherited_from": inherited_from,
            "epistemic_label": epistemic_label,
            "claim_id": claim_id,
            "action": action,
            "void_reason": void_reason,
            "rung": rung,
            "depends_on_assumption_ids": depends_on_assumption_ids,
            "concept": concept,
            "query": query,
            "state": state,
            "age_ma": age_ma,
            "tile_id": tile_id,
            "task": task,
            "bands": bands,
            "time_range_start": time_range_start,
            "time_range_end": time_range_end,
            "cloud_cover_max": cloud_cover_max,
            "source_uri": source_uri,
            "text": text,
            "grounding_evidence_count": grounding_evidence_count,
            "grounding_evidence_rungs": grounding_evidence_rungs,
            "threshold": threshold,
            "include_decomposition": include_decomposition,
        }
        args = _safe_forward(_impl, args, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # ── SURFACE EARTH DOMAIN — Physical Visible Earth (2026-06-25 FORGE) ────────

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_earthquake_catalog", annotations=_geox_annotations("geox_earthquake_catalog"))
    async def _earthquake_catalog(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query USGS Earthquake Catalog for seismic events. OBSERVED data — real seismic events from USGS FDSN API. Public Domain."""
        from geox_mcp.tools.earth_surface import geox_earthquake_catalog as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_relief_ingest", annotations=_geox_annotations("geox_relief_ingest"))
    async def _relief_ingest(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Ingest ETOPO 2022 global relief (topography + bathymetry). OBSERVED data — measured elevation from NOAA NCEI. Public Domain."""
        from geox_mcp.tools.earth_surface import geox_relief_ingest as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_bathymetry_ingest", annotations=_geox_annotations("geox_bathymetry_ingest"))
    async def _bathymetry_ingest(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Ingest GEBCO_2026 global bathymetry grid (ocean floor terrain). OBSERVED data — measured ocean depth from IHO/UNESCO. Public Domain."""
        from geox_mcp.tools.earth_surface import geox_bathymetry_ingest as _impl

        return await _auto_call(_impl, arguments)

    # ── EXTENDED EARTH DIMENSIONS — D4-D17 Open Data (2026-06-25 FORGE) ───────

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_heatflow_query", annotations=_geox_annotations("geox_heatflow_query"))
    async def _heatflow(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query IHFC Global Heat Flow Database. OBSERVED — ~91k measurements. GFZ/IHFC CC-BY-4.0."""
        from geox_mcp.tools.earth_surface_2 import geox_heatflow_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_stress_query", annotations=_geox_annotations("geox_stress_query"))
    async def _stress(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query World Stress Map 2025 (WSM). OBSERVED — ~100k stress orientations. GFZ CC-BY-4.0."""
        from geox_mcp.tools.earth_surface_2 import geox_stress_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_geochem_query", annotations=_geox_annotations("geox_geochem_query"))
    async def _geochem(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query EarthChem/PetDB for igneous geochemistry. OBSERVED — global rock analyses. CC-BY."""
        from geox_mcp.tools.earth_surface_2 import geox_geochem_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_plate_reconstruct", annotations=_geox_annotations("geox_plate_reconstruct"))
    async def _plate(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Reconstruct a point through deep time via GPlates. INTERPRETED — plate model dependent. GPL-2.0."""
        from geox_mcp.tools.earth_surface_2 import geox_plate_reconstruct as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_paleomag_query", annotations=_geox_annotations("geox_paleomag_query"))
    async def _paleomag(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query MagIC for paleomagnetic data. OBSERVED — rock magnetic measurements. CC-BY-4.0."""
        from geox_mcp.tools.earth_surface_2 import geox_paleomag_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_gravity_change_query", annotations=_geox_annotations("geox_gravity_change_query"))
    async def _grace(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query GRACE-FO for time-variable gravity (mass change). OBSERVED — NASA satellite gravimetry. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_gravity_change_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_ocean_query", annotations=_geox_annotations("geox_ocean_query"))
    async def _ocean(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query Copernicus Marine (CMEMS) for ocean physics/BGC. OBSERVED — satellite + model. EU Open Data."""
        from geox_mcp.tools.earth_surface_2 import geox_ocean_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_erddap_query", annotations=_geox_annotations("geox_erddap_query"))
    async def _erddap(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query NOAA ERDDAP for ocean/atmosphere data. OBSERVED — 10k+ datasets. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_erddap_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_climate_reanalysis", annotations=_geox_annotations("geox_climate_reanalysis"))
    async def _climate(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query ERA5 global reanalysis. OBSERVED — ECMWF hourly data from 1940. Copernicus License."""
        from geox_mcp.tools.earth_surface_2 import geox_climate_reanalysis as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_hydrology_query", annotations=_geox_annotations("geox_hydrology_query"))
    async def _hydrology(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query USGS Water Services for streamflow/groundwater. OBSERVED — US real-time. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_hydrology_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_satellite_catalog", annotations=_geox_annotations("geox_satellite_catalog"))
    async def _satellite(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Search STAC for Landsat/MODIS/Sentinel imagery. OBSERVED — satellite surface reflectance. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_satellite_catalog as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_uk_petroleum_query", annotations=_geox_annotations("geox_uk_petroleum_query"))
    async def _nsta(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query NSTA UK petroleum data (wells, fields, licences). OBSERVED — UKCS regulatory. OGL v3.0."""
        from geox_mcp.tools.earth_surface_2 import geox_uk_petroleum_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_geology_map_query", annotations=_geox_annotations("geox_geology_map_query"))
    async def _onegeology(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query OneGeology WMS for national geological maps. OBSERVED — aggregated survey data."""
        from geox_mcp.tools.earth_surface_2 import geox_geology_map_query as _impl

        return await _auto_call(_impl, arguments)

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_space_weather", annotations=_geox_annotations("geox_space_weather"))
    async def _spaceweather(
        arguments: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Query NOAA SWPC for space weather (Kp, Dst, solar wind). OBSERVED — real-time. Public Domain."""
        from geox_mcp.tools.earth_surface_2 import geox_space_weather as _impl

        return await _auto_call(_impl, arguments)

    # ── PHYSICS-FIRST STRATIGRAPHY ENGINES — Phase 3.0 (2026-07-03) ────────────
    # The extinction event: replaces LST/TST/HST taxonomy with physics simulation.
    # Sequences EMERGE from accommodation + eustasy + sediment, not from rules.
    # DITEMPA BUKAN DIBERI.

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_simulate_accommodation", annotations=_geox_annotations("geox_simulate_accommodation"))
    async def _simulate_accommodation(
        initial_subsidence_km: float = 2.0,
        thermal_subsidence_rate_mm_yr: float = 0.05,
        eustatic_rate_mm_yr: float = 0.0,
        sediment_supply_rate_m_myr: float = 50.0,
        initial_water_depth_m: float = 100.0,
        duration_ma: float = 10.0,
        time_step_myr: float = 0.5,
        dominant_lithology: str = "sandstone",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Simulate accommodation through time: tectonic subsidence + eustasy + sediment loading + compaction.

        Physics-first: this is the DRIVER of stratigraphy. Not cartoon sea-level curves.
        Surfaces and stacking patterns EMERGE from the simulation.
        Replaces the 'accommodation' concept that LST/TST/HST tries to name but never computes.

        Returns: accommodation steps with surface types and stacking patterns that emerged from physics.
        """
        from geox_core.engines.stratigraphy.accommodation import (
            AccommodationRequest,
        )
        from geox_core.engines.stratigraphy.accommodation import (
            simulate_accommodation as _impl,
        )

        try:
            req = AccommodationRequest(
                initial_subsidence_km=initial_subsidence_km,
                thermal_subsidence_rate_mm_yr=thermal_subsidence_rate_mm_yr,
                eustatic_rate_mm_yr=eustatic_rate_mm_yr,
                sediment_supply_rate_m_myr=sediment_supply_rate_m_myr,
                initial_water_depth_m=initial_water_depth_m,
                duration_ma=duration_ma,
                time_step_myr=time_step_myr,
                dominant_lithology=dominant_lithology,
            )
            result = _impl(req)
            return {"status": "success", "tool": "geox_simulate_accommodation", **result.model_dump()}
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_simulate_accommodation", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_simulate_surfaces", annotations=_geox_annotations("geox_simulate_surfaces"))
    async def _simulate_surfaces(
        initial_subsidence_km: float = 2.0,
        thermal_subsidence_rate_mm_yr: float = 0.05,
        eustatic_rate_mm_yr: float = 0.0,
        sediment_supply_rate_m_myr: float = 50.0,
        initial_water_depth_m: float = 100.0,
        duration_ma: float = 10.0,
        time_step_myr: float = 0.5,
        dominant_lithology: str = "sandstone",
        min_surface_magnitude_m: float = 0.5,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate stratigraphic surfaces from physics: erosion, flooding, MFS, truncation, ravinement.

        Surfaces are REAL, MAPPABLE, FALSIFIABLE — not taxonomic labels.
        This is Sloss's physics: base level → erosion → flooding → surfaces.
        A surface is a physical object. A systems tract is a cartoon.

        Returns: surfaces with type, age, geometry (onlap/downlap/truncation), and packages between them.
        """
        from geox_core.engines.stratigraphy.accommodation import (
            AccommodationRequest,
        )
        from geox_core.engines.stratigraphy.accommodation import (
            simulate_accommodation as _acc_impl,
        )
        from geox_core.engines.stratigraphy.surface_first import generate_surfaces as _surf_impl

        try:
            req = AccommodationRequest(
                initial_subsidence_km=initial_subsidence_km,
                thermal_subsidence_rate_mm_yr=thermal_subsidence_rate_mm_yr,
                eustatic_rate_mm_yr=eustatic_rate_mm_yr,
                sediment_supply_rate_m_myr=sediment_supply_rate_m_myr,
                initial_water_depth_m=initial_water_depth_m,
                duration_ma=duration_ma,
                time_step_myr=time_step_myr,
                dominant_lithology=dominant_lithology,
            )
            acc = _acc_impl(req)
            result = _surf_impl(acc, min_surface_magnitude_m=min_surface_magnitude_m)
            return {"status": "success", "tool": "geox_simulate_surfaces", **result.model_dump()}
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_simulate_surfaces", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_simulate_sequences", annotations=_geox_annotations("geox_simulate_sequences"))
    async def _simulate_sequences(
        initial_subsidence_km: float = 2.0,
        thermal_subsidence_rate_mm_yr: float = 0.05,
        eustatic_rate_mm_yr: float = 0.0,
        sediment_supply_rate_m_myr: float = 50.0,
        initial_water_depth_m: float = 100.0,
        duration_ma: float = 10.0,
        time_step_myr: float = 0.5,
        dominant_lithology: str = "sandstone",
        min_surface_magnitude_m: float = 0.5,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Let sequences EMERGE from physics: accommodation → surfaces → sequences.

        Sequences are NOT classified as LST/TST/HST. They EMERGE from:
        - erosion → sequence boundaries
        - flooding → flooding surfaces
        - maximum flooding → MFS
        - progradation/retrogradation → stacking patterns

        Scale (parasequence/depositional/Sloss) is determined by DURATION, not by rules.
        Resource potential (reservoir/seal/source) is inferred from stacking and surface types.

        Returns: emergent sequences with bounding surfaces, stacking patterns, resource potential, and resource graph.
        """
        from geox_core.engines.stratigraphy.accommodation import (
            AccommodationRequest,
        )
        from geox_core.engines.stratigraphy.accommodation import (
            simulate_accommodation as _acc_impl,
        )
        from geox_core.engines.stratigraphy.sequence_emergence import emerge_sequences as _seq_impl
        from geox_core.engines.stratigraphy.surface_first import generate_surfaces as _surf_impl

        try:
            req = AccommodationRequest(
                initial_subsidence_km=initial_subsidence_km,
                thermal_subsidence_rate_mm_yr=thermal_subsidence_rate_mm_yr,
                eustatic_rate_mm_yr=eustatic_rate_mm_yr,
                sediment_supply_rate_m_myr=sediment_supply_rate_m_myr,
                initial_water_depth_m=initial_water_depth_m,
                duration_ma=duration_ma,
                time_step_myr=time_step_myr,
                dominant_lithology=dominant_lithology,
            )
            acc = _acc_impl(req)
            surfaces = _surf_impl(acc, min_surface_magnitude_m=min_surface_magnitude_m)
            result = _seq_impl(surfaces, acc)
            return {"status": "success", "tool": "geox_simulate_sequences", **result.model_dump()}
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_simulate_sequences", source_organ="geox")

    # RE-REGISTERED 2026-07-13 — sediment routing for provenance-routing skill (earth-decode-7)
    @mcp.tool(name="geox_simulate_routing", annotations=_geox_annotations("geox_simulate_routing"))
    async def _simulate_routing(
        source_position_km: float = 0.0,
        source_sand_fraction: float = 0.6,
        source_supply_rate_m_myr: float = 100.0,
        source_discharge_m3_s: float = 2000.0,
        profile_length_km: float = 120.0,
        shelf_width_km: float = 50.0,
        shelf_gradient: float = 0.001,
        slope_gradient: float = 0.05,
        slope_start_km: float = 60.0,
        basin_floor_start_km: float = 80.0,
        accommodation_rate_m_myr: float = 50.0,
        duration_ma: float = 10.0,
        time_step_myr: float = 1.0,
        seed: int | None = 42,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Simulate sediment routing from source to sink: deltas, fans, bypass, deposition.

        Physics-first: generates depositional bodies from slope-driven transport,
        sand/mud partitioning, and autogenic lobe switching.
        Not facies modeling. Not geobody picking. Physics.

        Returns: depositional bodies (reservoirs, seals, sources), lobe events,
        mass balance, and emergent environments.
        """
        from geox_core.engines.stratigraphy.sediment_routing import (
            BasinGeometry,
            RoutingRequest,
            SedimentSource,
        )
        from geox_core.engines.stratigraphy.sediment_routing import (
            simulate_routing as _impl,
        )

        try:
            req = RoutingRequest(
                sources=[
                    SedimentSource(
                        source_id="SOURCE1",
                        position_km=source_position_km,
                        sand_fraction=source_sand_fraction,
                        supply_rate_m_myr=source_supply_rate_m_myr,
                        discharge_m3_s=source_discharge_m3_s,
                    )
                ],
                geometry=BasinGeometry(
                    profile_length_km=profile_length_km,
                    shelf_width_km=shelf_width_km,
                    shelf_gradient=shelf_gradient,
                    slope_gradient=slope_gradient,
                    slope_start_km=slope_start_km,
                    basin_floor_start_km=basin_floor_start_km,
                ),
                accommodation_rate_m_myr=accommodation_rate_m_myr,
                duration_ma=duration_ma,
                time_step_myr=time_step_myr,
                seed=seed,
            )
            result = _impl(req)
            return {"status": "success", "tool": "geox_simulate_routing", **result.model_dump()}
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_simulate_routing", source_organ="geox")

    # ── SEISMIC COGNITION ENGINE — Phase 3.1 (2026-07-06) ──────────────────────
    # 7-layer image-first pipeline for governed seismic interpretation.
    # IMAGE-FIRST COGNITION → SEG-Y VALIDATION → WELL-TIE GEOLOGY → GOVERNANCE
    # Constitutional: F7 humility (cap 0.90), F9 anti-hantu, non-uniqueness.
    # DITEMPA BUKAN DIBERI.

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_seismic_cognition", annotations=_geox_annotations("geox_seismic_cognition"))
    async def _seismic_cognition(
        mode: str = "full_pipeline",
        image_path: str | None = None,
        segy_path: str | None = None,
        well_data: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Seismic Cognition Engine — 7-layer image-first governed pipeline.

        Implements the constitutional doctrine:
          IMAGE-FIRST COGNITION → SEG-Y VALIDATION → WELL-TIE GEOLOGY → GOVERNANCE

        Modes:
          image_first  — Fast cognitive pass from rendered seismic image (Layers 1-3)
          validate     — SEG-Y physical audit (Layer 5)
          calibrate    — Well-tie calibration (Layer 6)
          full_pipeline — Complete chain: image → SEG-Y → well-tie → governance
          doctrine     — Returns the seismic cognition doctrine and layer definitions

        Constitutional invariants:
          - F7 HUMILITY: confidence hard-capped at 0.90
          - F9 ANTI-HANTU: no hallucinated geology
          - Non-uniqueness: every visual feature has multiple possible causes
          - OBS_IMAGE cannot claim geological meaning
          - INT_SEISMIC always keeps alternatives alive
          - DER_SYNTHETIC always labeled synthetic
          - No geology claim without physics validation
          - No economics without well tie
        """
        from geox_core.seismic_cognition import (
            CognitionResult,
            SeismicCognitionEngine,
            get_seismic_cognition_doctrine,
        )

        try:
            if mode == "doctrine":
                return {
                    "status": "success",
                    "tool": "geox_seismic_cognition",
                    "mode": "doctrine",
                    **get_seismic_cognition_doctrine(),
                }

            engine = SeismicCognitionEngine()

            if mode == "image_first":
                if not image_path:
                    return {
                        "status": "error",
                        "tool": "geox_seismic_cognition",
                        "error": "image_path required for image_first mode",
                    }
                result = await engine.process_image_first(image_path)
                return {
                    "status": "success",
                    "tool": "geox_seismic_cognition",
                    "mode": "image_first",
                    **result.to_dict(),
                }

            elif mode == "validate":
                if not segy_path:
                    return {
                        "status": "error",
                        "tool": "geox_seismic_cognition",
                        "error": "segy_path required for validate mode",
                    }
                # Build a prior result from image if provided
                if image_path:
                    prior = await engine.process_image_first(image_path)
                else:
                    prior = CognitionResult()
                result = await engine.validate_with_segy(segy_path, prior)
                return {
                    "status": "success",
                    "tool": "geox_seismic_cognition",
                    "mode": "validate",
                    **result.to_dict(),
                }

            elif mode == "calibrate":
                if not well_data:
                    return {
                        "status": "error",
                        "tool": "geox_seismic_cognition",
                        "error": "well_data required for calibrate mode",
                    }
                # Build prior chain
                if image_path:
                    prior = await engine.process_image_first(image_path)
                else:
                    prior = CognitionResult()
                if segy_path:
                    prior = await engine.validate_with_segy(segy_path, prior)
                result = await engine.calibrate_with_wells(well_data, prior)
                return {
                    "status": "success",
                    "tool": "geox_seismic_cognition",
                    "mode": "calibrate",
                    **result.to_dict(),
                }

            elif mode == "full_pipeline":
                verdict = await engine.full_pipeline(
                    image_path=image_path,
                    segy_path=segy_path,
                    well_data=well_data,
                )
                return {
                    "status": "success",
                    "tool": "geox_seismic_cognition",
                    "mode": "full_pipeline",
                    **verdict.to_dict(),
                }

            else:
                return {
                    "status": "error",
                    "tool": "geox_seismic_cognition",
                    "error": f"Unknown mode: {mode}. Valid: image_first, validate, calibrate, full_pipeline, doctrine",
                }

        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_seismic_cognition", source_organ="geox")

    # ═══════════════════════════════════════════════════════════════════════════════
    # SEISMIC PIPELINE TOOLS — Phase 3.0 RSI Cognition (2026-07-06)
    # Platform-agnostic seismic interpretation pipeline.
    # Implements IMAGE-FIRST COGNITION + NON-UNIQUENESS LAW doctrines.
    # OBS_IMAGE ≠ OBS_GEOLOGY. Pixels are observed. Geology requires calibration.
    # ═══════════════════════════════════════════════════════════════════════════════

    # GEOX-ZEN 2026-08-04 — RE-REGISTERED (M2 — Stage 444 compare)
    @mcp.tool(name="geox_physical_reality_interpret", annotations=_geox_annotations("geox_physical_reality_interpret"))
    async def _geox_physical_reality_interpret(
        image_path: str,
        output_dir: str | None = None,
        max_faults: int = 15,
        max_horizons: int = 8,
    ) -> dict[str, Any]:
        """Physical reality interpretation from seismic image pixels.

        Full RSI pipeline: reality gate → crop → AGC → phase → discontinuity →
        edge → fault probability → ant-track-lite → DP horizon tracking →
        epistemic governance → provenance manifest.

        OBS_IMAGE ≠ OBS_GEOLOGY: All outputs are pixel-derived.
        Every INT claim carries alternative interpretations.
        PETROPHYSICS = HOLD from image-only input.
        """
        try:
            from geox_core.seismic_pipeline.geox_physical_reality import GeoxPhysicalReality
            from geox_mcp.federation_safety import classify_error

            engine = GeoxPhysicalReality()
            result = engine.interpret(image_path, output_dir=output_dir)
            return {
                "status": "success",
                "tool": "geox_physical_reality_interpret",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_physical_reality_interpret", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_geological_cognition_run", annotations=_geox_annotations("geox_geological_cognition_run"))
    async def _geox_geological_cognition_run(
        image_path: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Geological cognition layer — translate pixel patterns into geological hypotheses.

        Runs after physical reality interpretation. Classifies reflector packages,
        detects terminations (onlap/downlap/truncation), screens imaging artifacts,
        ranks multiple hypotheses per feature, and builds a geologist-style report.

        Every INT claim carries alternatives. Non-uniqueness law enforced.
        """
        try:
            import sys

            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_geological_cognition import run_geological_cognition
            from geox_physical_reality import GeoxPhysicalReality

            # First run physical reality to get attributes
            engine = GeoxPhysicalReality()
            phys = engine.interpret(image_path, output_dir=output_dir)
            if phys.get("status") == "VOID":
                return {"status": "VOID", "reason": "Physical reality gate failed"}

            # Run geological cognition on the attributes
            # Use stored raw arrays from physical reality engine
            attrs = engine._last_attrs
            fp = engine._last_fp
            horizons = engine._last_horizons
            faults = engine._last_faults

            result = run_geological_cognition(attrs, fp, horizons, faults, output_dir)
            return {
                "status": "success",
                "tool": "geox_geological_cognition_run",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_geological_cognition_run", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_panel_d_render_mcp", annotations=_geox_annotations("geox_panel_d_render_mcp"))
    async def _geox_panel_d_render_mcp(
        image_path: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Panel D — Cognitive interpretation rendering.

        Renders what the geologist JUDGES, not what pixels show.
        Zone bands, termination symbols, fault labels, horizon labels,
        artifact boxes, epistemic rulers. The panel a senior geologist
        would show to justify a drilling decision.

        Requires prior physical reality + geological cognition runs.
        """
        try:
            import sys

            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_geological_cognition import run_geological_cognition
            from geox_panel_d import render_cognitive_panel
            from geox_physical_reality import GeoxPhysicalReality

            # Run full pipeline
            engine = GeoxPhysicalReality()
            phys = engine.interpret(image_path, output_dir=output_dir)
            if phys.get("status") == "VOID":
                return {"status": "VOID", "reason": "Physical reality gate failed"}

            # Use stored raw arrays from physical reality engine
            attrs = engine._last_attrs
            fp = engine._last_fp
            horizons = engine._last_horizons
            faults = engine._last_faults
            raw_arr = engine._last_raw_arr
            crop_bbox = engine._last_crop_bbox

            cogn = run_geological_cognition(attrs, fp, horizons, faults, output_dir)

            # Render Panel D
            result = render_cognitive_panel(
                attrs,
                fp,
                faults,
                horizons,
                cogn.get("packages", []),
                cogn.get("terminations", []),
                cogn.get("artifacts", []),
                cogn.get("hypotheses", {}),
                raw_arr,
                crop_bbox,
                phys.get("provenance", {}),
                output_dir or os.path.dirname(image_path),
            )
            return {
                "status": "success",
                "tool": "geox_panel_d_render_mcp",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_panel_d_render_mcp", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_segy_trace_audit", annotations=_geox_annotations("geox_segy_trace_audit"))
    async def _geox_segy_trace_audit(
        segy_path: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """SEG-Y trace reality audit — physical validation from raw traces.

        Ingests SEG-Y, audits trace headers, checks geometry,
        validates amplitude preservation, estimates wavelet phase,
        and computes trace-level attributes.

        This is the PHYSICS_VALIDATION layer — the evidential backbone
        that validates or falsifies image-based interpretations.
        """
        try:
            import sys

            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_segy_trace_reality import (
                audit_geometry,
                audit_trace_headers,
                check_amplitude_preservation,
                check_wavelet_phase,
                compute_trace_attributes,
                ingest_segy,
            )

            ingested = ingest_segy(segy_path)
            header_audit = audit_trace_headers(ingested)
            geom_audit = audit_geometry(ingested)
            amp_audit = check_amplitude_preservation(ingested)
            wavelet_info = check_wavelet_phase(ingested)
            trace_attrs = compute_trace_attributes(ingested, wavelet_info)

            return {
                "status": "success",
                "tool": "geox_segy_trace_audit",
                "header_audit": header_audit,
                "geometry_audit": geom_audit,
                "amplitude_audit": amp_audit,
                "wavelet_info": wavelet_info,
                "trace_attributes_summary": {
                    k: {"shape": v.shape, "dtype": str(v.dtype)} for k, v in trace_attrs.items() if hasattr(v, "shape")
                },
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_segy_trace_audit", source_organ="geox")

    # GEOX-ZEN 2026-08-04 — RE-REGISTERED (M1 — Stage 222 forward)
    @mcp.tool(name="geox_well_tie_compute", annotations=_geox_annotations("geox_well_tie_compute"))
    async def _geox_well_tie_compute(
        las_path: str,
        segy_path: str | None = None,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Well-tie calibration via bruges — synthetic seismogram generation.

        Loads well logs (LAS), computes synthetic seismogram via bruges,
        and ties to seismic if SEG-Y provided. This is the GEOLOGY layer
        that converts seismic interpretation into formation-calibrated picks.

        Without well tie, all interpretations remain INT_SEISMIC (not OBS_GEOLOGY).
        """
        try:
            import sys

            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_well_tie_bruges import run_well_tie

            result = run_well_tie(las_path, segy_audit_path=segy_path or "", output_dir=output_dir or "/tmp/geox_well_tie")
            return {
                "status": "success",
                "tool": "geox_well_tie_compute",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_well_tie_compute", source_organ="geox")

    # ── Phase 3.3: Tie Receipt + Preflight (2026-07-06) ─────────────────────────

    # ZEN 2026-07-11 G1: merged into geox_seismic_compute mode=tie_receipt
    async def _geox_tie_receipt(
        well_name: str,
        seismic_volume: str = "",
        polarity_convention: str = "",
        phase_convention: str = "",
        seismic_datum: str = "",
        well_datum: str = "",
        depth_basis: str = "MD",
        logs_used: str = "",
        time_depth_checkshot: bool = False,
        time_depth_vsp: bool = False,
        time_depth_confidence: str = "low",
        wavelet_source: str = "assumed",
        wavelet_phase_confidence: str = "low",
        correlation_score: float | None = None,
        residual_class: str = "unexplained",
        rock_lithology_sep: str = "low",
        rock_fluid_sep: str = "low",
        inversion_allowed: bool = False,
        decision_permission: str = "HOLD",
        decision_reason: str = "",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Seismic-to-well tie evidence envelope — metabolizer memory.

        Builds a structured receipt that tells the system what it is allowed to
        believe after a seismic-to-well tie. The receipt matters more than the
        image of the tie. It covers: data inputs, calibration quality, error
        classification, rock physics status, decision permission, and uncertainty.

        Anti-hantu: amplitude is not hydrocarbon. Impedance is not lithology.
        Inversion is not truth. Tie is not validation unless residuals are explained.
        """
        try:
            from geox_core.schemas.tie_receipt import build_tie_receipt

            logs_list = [l.strip() for l in logs_used.split(",") if l.strip()] if logs_used else []

            receipt = build_tie_receipt(
                well_name=well_name,
                seismic_volume=seismic_volume,
                session_id=session_id,
                polarity_convention=polarity_convention,
                phase_convention=phase_convention,
                seismic_datum=seismic_datum,
                well_datum=well_datum,
                depth_basis=depth_basis,
                logs_used=logs_list,
                time_depth_control={
                    "checkshot_present": time_depth_checkshot,
                    "vsp_present": time_depth_vsp,
                    "confidence": time_depth_confidence,
                },
                wavelet={
                    "source": wavelet_source,
                    "phase_confidence": wavelet_phase_confidence,
                },
                tie_quality={
                    "correlation_score": correlation_score,
                    "residual_class": residual_class,
                },
                rock_physics_status={
                    "lithology_separability": rock_lithology_sep,
                    "fluid_separability": rock_fluid_sep,
                },
                inversion_permission={
                    "allowed": inversion_allowed,
                },
                decision_permission=decision_permission,
                decision_reason=decision_reason,
            )

            return {
                "status": "success",
                "tool": "geox_tie_receipt",
                "receipt": receipt,
            }
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_tie_receipt", source_organ="geox")

    # ZEN 2026-07-11 G1: merged into geox_seismic_compute mode=tie_preflight
    async def _geox_tie_preflight(
        well_name: str,
        decision_context: str = "horizon_calibration",
        answers: str = "",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """25-point pre-interpretation gate for seismic-to-well tie.

        Before interpreting a tie, an agent must answer 25 questions covering:
        conventions, datum, calibration, data quality, signal, processing,
        geology, rock physics, resolution, analog, and decision context.

        Same data, different burden of proof: a tie for horizon calibration
        needs less than a tie for reserves booking.

        Returns GO / HOLD / VOID verdict with specific blockers.
        The checklist is not bureaucracy. It is the metabolizer's intake valve.
        """
        try:
            from geox_core.schemas.tie_preflight import run_tie_preflight

            # Parse answers: "1=YES,2=ZERO-PHASE,3=MSL,..."
            answers_dict: dict[int, str] = {}
            if answers:
                for pair in answers.split(","):
                    pair = pair.strip()
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        try:
                            answers_dict[int(k.strip())] = v.strip()
                        except ValueError:
                            pass

            result = run_tie_preflight(
                well_name=well_name,
                decision_context=decision_context,
                answers=answers_dict,
                session_id=session_id,
            )

            return {
                "status": "success",
                "tool": "geox_tie_preflight",
                **result,
            }
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_tie_preflight", source_organ="geox")

    # ── GEOX 1D MCP surface (Orthogonal Base) ─────────────────────────────

    # ZEN 2026-07-11 G1: merged into geox_seismic_compute mode — geox_well_time_depth_calibrate
    async def _geox_well_time_depth_calibrate(
        las_path: str,
        checkshot_path: str,
        method: str = "linear",
        velocity_bounds: list[float] | None = None,
        residual_threshold_pct: float = 10.0,
        well_id: str = "",
        actor_id: str = "geox_1d_mcp",
    ) -> dict[str, Any]:
        """Calibrate time–depth using LAS + checkshot with PhysicsGuard.

        Methods: linear | polynomial | vo_k | layer_cake.
        Returns JSON TDFitResult + geox:// resource URI (DRAFT_ONLY receipt).
        """
        try:
            from geox_mcp.tools.well_1d_surface import geox_well_time_depth_calibrate

            return await geox_well_time_depth_calibrate(
                las_path=las_path,
                checkshot_path=checkshot_path,
                method=method,  # type: ignore[arg-type]
                velocity_bounds=velocity_bounds,
                residual_threshold_pct=residual_threshold_pct,
                well_id=well_id,
                actor_id=actor_id,
            )
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_well_time_depth_calibrate", source_organ="geox")

    # GEOX-ZEN 2026-08-04 — RE-REGISTERED (M2 — Stage 444 compare)
    @mcp.tool(name="geox_well_seismic_mistie_rms", annotations=_geox_annotations("geox_well_seismic_mistie_rms"))
    async def _geox_well_seismic_mistie_rms(
        synthetic_trace: list[float],
        seismic_trace: list[float],
        dt_ms: float = 4.0,
        time_window_ms: list[float] | None = None,
        threshold_ms: float = 25.0,
        max_lag_ms: float = 50.0,
        well_id: str = "WELL",
        actor_id: str = "geox_1d_mcp",
    ) -> dict[str, Any]:
        """Phase 3 RMS mistie gate — synthetic vs seismic. Verdict SEAL|HOLD|VOID.

        Hard default threshold 25 ms. Absolute ms, not sample units.
        """
        try:
            from geox_mcp.tools.well_1d_surface import geox_well_seismic_mistie_rms

            return await geox_well_seismic_mistie_rms(
                synthetic_trace=synthetic_trace,
                seismic_trace=seismic_trace,
                dt_ms=dt_ms,
                time_window_ms=time_window_ms,
                threshold_ms=threshold_ms,
                max_lag_ms=max_lag_ms,
                well_id=well_id,
                actor_id=actor_id,
            )
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_well_seismic_mistie_rms", source_organ="geox")

    # GEOX-ZEN 2026-08-04 — RE-REGISTERED (M1 — Stage 222 forward)
    @mcp.tool(name="geox_wavelet_extract_least_squares", annotations=_geox_annotations("geox_wavelet_extract_least_squares"))
    async def _geox_wavelet_extract_least_squares(
        reflectivity_series: list[float],
        seismic_trace: list[float],
        wavelet_length_ms: float = 120.0,
        epsilon: float = 1e-3,
        dt_ms: float = 4.0,
        well_id: str = "WELL",
        actor_id: str = "geox_1d_mcp",
    ) -> dict[str, Any]:
        """Phase 4 Wiener least-squares wavelet extraction from r and seismic."""
        try:
            from geox_mcp.tools.well_1d_surface import geox_wavelet_extract_least_squares

            return await geox_wavelet_extract_least_squares(
                reflectivity_series=reflectivity_series,
                seismic_trace=seismic_trace,
                wavelet_length_ms=wavelet_length_ms,
                epsilon=epsilon,
                dt_ms=dt_ms,
                well_id=well_id,
                actor_id=actor_id,
            )
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_wavelet_extract_least_squares", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_benchmark_001", annotations=_geox_annotations("geox_benchmark_001"))
    async def _geox_benchmark_001(
        scenario: str = "mistie_hold",
        write_fixtures_dir: str = "",
        include_full_workflow: bool = True,
        enforce_orthogonal_base: bool = True,
        las_path: str = "",
        use_real_las: bool = False,
        checkshot_path: str = "",
        tops_path: str = "",
        seismic_path: str = "",
    ) -> dict[str, Any]:
        """GEOX-001: Well-Seismic Truth Test — Model Deserves To Live.

        Orthogonal Base first (GENESIS/013):
          well_ingest → well_qc → tie_preflight → well_tie → tie_receipt
        then Law plane verdict. Cognitive/Dimensional tools blocked until base.

        Thesis: If the well does not tie, the model does not get to speak as truth.
        """
        try:
            from geox_mcp.tools.benchmark_001 import geox_benchmark_001

            if scenario not in ("good_tie", "mistie_hold", "kill_contradiction"):
                return {
                    "status": "error",
                    "tool": "geox_benchmark_001",
                    "error": f"Unknown scenario '{scenario}'",
                }
            return await geox_benchmark_001(
                scenario=scenario,  # type: ignore[arg-type]
                write_fixtures_dir=write_fixtures_dir,
                include_full_workflow=include_full_workflow,
                enforce_orthogonal_base=enforce_orthogonal_base,
                las_path=las_path,
                use_real_las=use_real_las,
                checkshot_path=checkshot_path,
                tops_path=tops_path,
                seismic_path=seismic_path,
            )
        except Exception as e:
            from geox_mcp.federation_safety import classify_error

            return classify_error(e, source_tool="geox_benchmark_001", source_organ="geox")

    # ── WELL-TIE P2–P4: Time-Depth Calibrate · Mistie RMS · Wavelet Extract ────

    # DEREGISTERED 2026-07-10 — # ZEN 2026-07-11 G1: merged into geox_seismic_compute — geox_well_time_depth_calibrate
    async def _well_time_depth_calibrate(
        las_path: str,
        checkshot_path: str | None = None,
        checkshot_data: str | None = None,
        method: str = "linear",
        velocity_bounds: str | None = None,
        residual_threshold_pct: float = 10.0,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Calibrate time-depth using LAS + checkshot with PhysicsGuard.

        Accepts checkshot as a file path (JSON or CSV) or inline JSON string.
        Dispatches to 4 fitters: linear, polynomial, vo_k, layer_cake.
        Returns TDFitResult with equation, coefficients, residuals, extrapolation_risk.
        """
        try:
            import json

            from geox_core.core.welltie_mcp import compute_td_calibrate
            from geox_mcp.federation_safety import classify_error

            cs_data = None
            if checkshot_data:
                cs_data = json.loads(checkshot_data)
                if isinstance(cs_data, dict) and "checkshots" in cs_data:
                    cs_data = cs_data["checkshots"]
                if not isinstance(cs_data, list):
                    cs_data = [cs_data]

            vb = (1500.0, 6000.0)
            if velocity_bounds:
                parts = json.loads(velocity_bounds) if isinstance(velocity_bounds, str) else velocity_bounds
                if len(parts) >= 2:
                    vb = (float(parts[0]), float(parts[1]))

            result = compute_td_calibrate(
                las_path=las_path,
                checkshot_path=checkshot_path,
                checkshot_data=cs_data,
                method=method,
                velocity_bounds=vb,
                residual_threshold_pct=residual_threshold_pct,
            )
            return {"status": "success", "tool": "geox_well_time_depth_calibrate", **result}
        except Exception as e:
            return classify_error(e, source_tool="geox_well_time_depth_calibrate", source_organ="geox")

    # DEREGISTERED 2026-07-10 — # ZEN 2026-07-11 G1: merged into geox_seismic_compute — geox_well_seismic_mistie_rms
    async def _well_seismic_mistie_rms(
        well_name: str,
        synthetic_trace: list[float],
        seismic_trace: list[float],
        dt_ms: float,
        time_window_ms: list[float],
        threshold_ms: float = 25.0,
        max_lag_ms: float = 50.0,
        checkshot_ref: str | None = None,
        polarity: str = "SEG_NORMAL",
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Falsification gate: RMS mistie between synthetic and seismic.

        Computes cross-correlation, finds optimal lag, computes RMS after shift.
        Constitutional gate: RMS > threshold_ms → HOLD.
        25 ms threshold based on tuning thickness resolution limit.
        """
        try:
            from geox_core.schemas.mistie_rms import MistieRMSInput

            from geox_core.core.welltie_mcp import compute_mistie_rms
            from geox_mcp.federation_safety import classify_error

            inp = MistieRMSInput(
                well_name=well_name,
                synthetic_trace=synthetic_trace,
                seismic_trace=seismic_trace,
                dt_ms=dt_ms,
                time_window_ms=time_window_ms,
                threshold_ms=threshold_ms,
                max_lag_ms=max_lag_ms,
                checkshot_ref=checkshot_ref,
                polarity=polarity,
                session_id=session_id,
            )
            result = compute_mistie_rms(inp)
            return {"status": "success", "tool": "geox_well_seismic_mistie_rms", **result}
        except Exception as e:
            return classify_error(e, source_tool="geox_well_seismic_mistie_rms", source_organ="geox")

    # DEREGISTERED 2026-07-10 — # ZEN 2026-07-11 G1: merged into geox_seismic_compute — geox_wavelet_extract_least_squares
    async def _wavelet_extract_least_squares(
        well_name: str,
        reflectivity_series: list[float],
        seismic_trace: list[float],
        dt_ms: float,
        wavelet_length_ms: float = 100.0,
        epsilon: float = 0.01,
        max_condition_number: float = 100.0,
        min_correlation_after: float = 0.60,
        checkshot_ref: str | None = None,
        polarity: str = "SEG_NORMAL",
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Extract wavelet from earth — Wiener least-squares spectral division.

        Math: W(ω) = S(ω)·R*(ω)/(|R(ω)|²+ε).
        Physical constraints: compact support, causality, phase classification.
        Constitutional gate: condition_number > 10× threshold → VOID.
        """
        try:
            from geox_core.schemas.wavelet_extract import WaveletExtractInput

            from geox_core.core.welltie_mcp import extract_wavelet_least_squares
            from geox_mcp.federation_safety import classify_error

            inp = WaveletExtractInput(
                well_name=well_name,
                reflectivity_series=reflectivity_series,
                seismic_trace=seismic_trace,
                dt_ms=dt_ms,
                wavelet_length_ms=wavelet_length_ms,
                epsilon=epsilon,
                max_condition_number=max_condition_number,
                min_correlation_after=min_correlation_after,
                checkshot_ref=checkshot_ref,
                polarity=polarity,
                session_id=session_id,
            )
            result = extract_wavelet_least_squares(inp)
            return {"status": "success", "tool": "geox_wavelet_extract_least_squares", **result}
        except Exception as e:
            return classify_error(e, source_tool="geox_wavelet_extract_least_squares", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_3d_model_build", annotations=_geox_annotations("geox_3d_model_build"))
    async def _geox_3d_model_build(
        model_json_path: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """3D structural model via GemPy — implicit geological modeling.

        Builds a 3D geological model from 2D interpretation picks.
        Requires a JSON model definition with surfaces, orientations,
        and extent. Outputs 3D visualization and structural model.

        This is the STRUCTURAL_VALIDATION layer — converts 2D picks
        into 3D geological volumes for structural plausibility testing.
        """
        try:
            import sys

            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_3d_modeling_gempy import run_gempy_3d_model

            result = run_gempy_3d_model(model_json_path, output_dir)
            return {
                "status": "success",
                "tool": "geox_3d_model_build",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_3d_model_build", source_organ="geox")

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_wealth_bridge_run", annotations=_geox_annotations("geox_wealth_bridge_run"))
    async def _geox_wealth_bridge_run(
        gempy_manifest_path: str,
        well_data: dict[str, Any] | None = None,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """GEOX → WEALTH capital bridge — economic evaluation of geological models.

        Takes GemPy 3D model manifest and optional well data,
        computes prospect volumetrics, and routes to WEALTH organ
        for NPV/IRR/EMV evaluation.

        Sovereign authority required for capital decisions.
        WEALTH computes. arifOS judges. Arif decides.
        """
        try:
            import sys

            from geox_mcp.federation_safety import classify_error

            sys.path.insert(0, "/root/GEOX/src/geox_core/seismic_pipeline")
            from geox_wealth_bridge import run_wealth_bridge

            result = run_wealth_bridge(
                gempy_manifest_path, grid_path="", well_manifest_path="", output_dir=output_dir or "/tmp/geox_wealth"
            )
            return {
                "status": "success",
                "tool": "geox_wealth_bridge_run",
                **result,
            }
        except Exception as e:
            return classify_error(e, source_tool="geox_wealth_bridge_run", source_organ="geox")

    # ── GEOLOGICAL MAP PIPELINE — 4-Verb Chain (2026-07-02 FORGE) ────────────

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_map_layers_list", annotations=_geox_annotations("geox_map_layers_list"))
    # ZEN-CONSOLIDATED — async def _map_layers_list(
        # ZEN-CONSOLIDATED — bbox: list[float],
        # ZEN-CONSOLIDATED — theme: str | None = None,
        # ZEN-CONSOLIDATED — include_unavailable: bool = False,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """List available GEOX map layers for a bounding box. Returns layer catalogue with metadata, truth classes, and availability."""
        from geox_mcp.tools.earth_map import geox_map_layers_list as _impl

        return await _auto_call(_impl, {"bbox": bbox, "theme": theme, "include_unavailable": include_unavailable})

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_map_scene_plan", annotations=_geox_annotations("geox_map_scene_plan"))
    # ZEN-CONSOLIDATED — async def _map_scene_plan(
        # ZEN-CONSOLIDATED — bbox: list[float],
        # ZEN-CONSOLIDATED — layer_ids: list[str] | None = None,
        # ZEN-CONSOLIDATED — theme: str | None = None,
        # ZEN-CONSOLIDATED — map_purpose: str = "context",
        # ZEN-CONSOLIDATED — style_profile: str = "geox_regional_clean_v1",
        # ZEN-CONSOLIDATED — crs: str = "EPSG:4326",
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Create a deterministic visual recipe for a geological map scene. No image rendered yet — inspect this plan before rendering."""
        from geox_mcp.tools.earth_map import geox_map_scene_plan as _impl

        return await _auto_call(
            _impl,
            {
                "bbox": bbox,
                "layer_ids": layer_ids,
                "theme": theme,
                "map_purpose": map_purpose,
                "style_profile": style_profile,
                "crs": crs,
            },
        )

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_map_render_preview", annotations=_geox_annotations("geox_map_render_preview"))
    # ZEN-CONSOLIDATED — async def _map_render_preview(
        # ZEN-CONSOLIDATED — scene_id: str | None = None,
        # ZEN-CONSOLIDATED — bbox: list[float] | None = None,
        # ZEN-CONSOLIDATED — layer_ids: list[str] | None = None,
        # ZEN-CONSOLIDATED — theme: str | None = None,
        # ZEN-CONSOLIDATED — width_px: int = 1024,
        # ZEN-CONSOLIDATED — height_px: int = 768,
        # ZEN-CONSOLIDATED — style_profile: str = "geox_regional_clean_v1",
        # ZEN-CONSOLIDATED — format: str = "image/png",
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        # ZEN-CONSOLIDATED — """Render a static map preview from a scene plan or bbox. Images <300KB returned as inline base64."""
        # ZEN-CONSOLIDATED — from geox_mcp.tools.earth_map import geox_map_render_preview as _impl

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — return await _auto_call(
            # ZEN-CONSOLIDATED — _impl,
            # ZEN-CONSOLIDATED — {
                # ZEN-CONSOLIDATED — "scene_id": scene_id,
                # ZEN-CONSOLIDATED — "bbox": bbox,
                # ZEN-CONSOLIDATED — "layer_ids": layer_ids,
                # ZEN-CONSOLIDATED — "theme": theme,
                # ZEN-CONSOLIDATED — "width_px": width_px,
                # ZEN-CONSOLIDATED — "height_px": height_px,
                # ZEN-CONSOLIDATED — "style_profile": style_profile,
                # ZEN-CONSOLIDATED — "format": format,
            # ZEN-CONSOLIDATED — },
        # ZEN-CONSOLIDATED — )

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # KUTIP SAMPAH 2026-08-05 H1/W5 — deregistered public leak
    # ZEN-CONSOLIDATED — # @mcp.tool(name="geox_map_export_package", annotations=_geox_annotations("geox_map_export_package"))
    # ZEN-CONSOLIDATED — async def _map_export_package(
        # ZEN-CONSOLIDATED — scene_plan_id: str,
        # ZEN-CONSOLIDATED — formats: list[str] | None = None,
        # ZEN-CONSOLIDATED — include_sources: bool = False,
        # ZEN-CONSOLIDATED — include_provenance: bool = True,
        # ZEN-CONSOLIDATED — review_mode: str = "draft",
        # ZEN-CONSOLIDATED — output_dir: str | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        # ZEN-CONSOLIDATED — """Create a governed export package with map assets, metadata, and provenance sidecars. Final step of the map verb chain."""
        # ZEN-CONSOLIDATED — from geox_mcp.tools.earth_map import geox_map_export_package as _impl

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — return await _auto_call(
            # ZEN-CONSOLIDATED — _impl,
            # ZEN-CONSOLIDATED — {
                # ZEN-CONSOLIDATED — "scene_plan_id": scene_plan_id,
                # ZEN-CONSOLIDATED — "formats": formats,
                # ZEN-CONSOLIDATED — "include_sources": include_sources,
                # ZEN-CONSOLIDATED — "include_provenance": include_provenance,
                # ZEN-CONSOLIDATED — "review_mode": review_mode,
                # ZEN-CONSOLIDATED — "output_dir": output_dir,
            # ZEN-CONSOLIDATED — },
        # ZEN-CONSOLIDATED — )

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # ── BID ROUND SCREENER — MBR 2026 (2026-07-09) ─────────────────────────
    # ZEN-CONSOLIDATED — # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_bid_round_screener", annotations=_geox_annotations("geox_bid_round_screener"))
    # ZEN-CONSOLIDATED — async def _bid_round_screener(
        # ZEN-CONSOLIDATED — arguments: dict[str, Any] | str | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        # ZEN-CONSOLIDATED — """MBR 2026 Multi-Block Bid Round Screener — rank N blocks into BID/PARTNER/NO_BID matrix.

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Takes all block opportunities at once, scores each on geological risk,
        # ZEN-CONSOLIDATED — capital requirement, evidence strength, and fiscal attractiveness.
        # ZEN-CONSOLIDATED — F1-F13 floor compliance inline. Advisory only (F13 SOVEREIGN).
        # ZEN-CONSOLIDATED — """
        # ZEN-CONSOLIDATED — from geox_mcp.tools.bid_round_screener import geox_bid_round_screener as _impl

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — return await _auto_call(
            # ZEN-CONSOLIDATED — _impl,
            # ZEN-CONSOLIDATED — dict(_parse_str_arguments(arguments) or {}),
        # ZEN-CONSOLIDATED — )

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # ── COLLISION ZONE — Two Oceanics Physics (Phase Zen, 2026-07-10) ────────
    # ZEN-CONSOLIDATED — # Implements collision zone physics from Arif's Sabah Eureka Ledger v1.0.
    # ZEN-CONSOLIDATED — # Two blocks (accretionary + rifted), suture, accommodation ratio, loading ratio.
    # ZEN-CONSOLIDATED — # Detects 6 Eureka signatures. Margin Principle embedded.
    # ZEN-CONSOLIDATED — # DITEMPA BUKAN DIBERI.

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_collision_zone", annotations=_geox_annotations("geox_collision_zone"))
    # ZEN-CONSOLIDATED — async def _collision_zone(
        # ZEN-CONSOLIDATED — domain_a: dict[str, Any],
        # ZEN-CONSOLIDATED — domain_b: dict[str, Any],
        # ZEN-CONSOLIDATED — suture_name: str = "Suture",
        # ZEN-CONSOLIDATED — duration_ma: float = 15.0,
        # ZEN-CONSOLIDATED — bypass_fraction: float = 0.0,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        # ZEN-CONSOLIDATED — """Analyze a collision zone using Two Oceanics physics.

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Computes accommodation_ratio, loading_ratio, mass_deficit_pct from
        # ZEN-CONSOLIDATED — two lithospheric blocks with different subsidence physics.

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Detects Eureka signatures: TWO_OCEANICS, MFS_ASYMMETRY, LOADING_PULSE,
        # ZEN-CONSOLIDATED — MASS_DEFICIT, SUTURE_SINK, PROSPECT_BIFURCATION.

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Example (Sabah):
          # ZEN-CONSOLIDATED — domain_a = {"name": "Kinabalu", "initial_subsidence_km": 4.0,
                      # ZEN-CONSOLIDATED — "loading_rate_m_myr": 400.0, "has_mfs": true}
          # ZEN-CONSOLIDATED — domain_b = {"name": "Layang-Layang", "initial_subsidence_km": 2.0,
                      # ZEN-CONSOLIDATED — "thermal_rate_mm_yr": 0.20, "has_mfs": false}
          # ZEN-CONSOLIDATED — suture_name = "Sabah Trough"
        # ZEN-CONSOLIDATED — """
        # ZEN-CONSOLIDATED — from geox_mcp.tools.collision_zone import compute_collision

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — return compute_collision(
            # ZEN-CONSOLIDATED — domain_a=domain_a,
            # ZEN-CONSOLIDATED — domain_b=domain_b,
            # ZEN-CONSOLIDATED — suture_name=suture_name,
            # ZEN-CONSOLIDATED — duration_ma=duration_ma,
            # ZEN-CONSOLIDATED — bypass_fraction=bypass_fraction,
        # ZEN-CONSOLIDATED — )

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_collision_chronology", annotations=_geox_annotations("geox_collision_chronology"))
    # ZEN-CONSOLIDATED — async def _collision_chronology(
        # ZEN-CONSOLIDATED — events: list[dict[str, Any]],
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        # ZEN-CONSOLIDATED — """Compute collision chronology from a sequence of tectonic events.

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Takes a list of {age_ma, event_name, description} and computes
        # ZEN-CONSOLIDATED — collision duration, event ordering, and the key insight:
        # ZEN-CONSOLIDATED — "The collision is not an event. It is a 15 Myr sequence, still finishing."

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Example:
          # ZEN-CONSOLIDATED — events = [{"age_ma": 65, "event_name": "DG Rift", "description": "..."},
                    # ZEN-CONSOLIDATED — {"age_ma": 21, "event_name": "Collision", "description": "..."},
                    # ZEN-CONSOLIDATED — {"age_ma": 7,  "event_name": "Kinabalu Granite", "description": "..."}]
        # ZEN-CONSOLIDATED — """
        # ZEN-CONSOLIDATED — from geox_mcp.tools.collision_zone import compute_collision_chronology

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — return compute_collision_chronology(events)

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # ── DOMAIN EVIDENCE GATE — geox_diagnose (Phase Zen, 2026-07-10) ──────────
    # ZEN-CONSOLIDATED — # Pre-flight check: "Does GEOX have evidence for this question?"
    # ZEN-CONSOLIDATED — # Returns NO_DOMAIN_EVIDENCE / PARTIAL / READY.
    # ZEN-CONSOLIDATED — # When NO_DOMAIN_EVIDENCE: use ChatGPT, not GEOX.

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_diagnose", annotations=_geox_annotations("geox_diagnose"))
    # ZEN-CONSOLIDATED — async def _diagnose(
        # ZEN-CONSOLIDATED — query: str = "",
        # ZEN-CONSOLIDATED — domain: str = "",
        # ZEN-CONSOLIDATED — location: str = "",
        # ZEN-CONSOLIDATED — basin: str = "",
        # ZEN-CONSOLIDATED — required_evidence: list[str] | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        # ZEN-CONSOLIDATED — """Check if GEOX has domain evidence for a question.

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Routes questions to either GEOX (evidence analysis) or ChatGPT (general knowledge).

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Returns NO_DOMAIN_EVIDENCE when GEOX has no relevant basin profiles,
        # ZEN-CONSOLIDATED — literature, or well data — use ChatGPT for general knowledge questions.

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Returns READY when evidence is sufficient for geox_basin, geox_evidence,
        # ZEN-CONSOLIDATED — or geox_contrast_detect analysis.
        # ZEN-CONSOLIDATED — """
        # ZEN-CONSOLIDATED — from geox_mcp.tools.diagnose import diagnose

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — return diagnose(
            # ZEN-CONSOLIDATED — query=query,
            # ZEN-CONSOLIDATED — domain=domain,
            # ZEN-CONSOLIDATED — location=location,
            # ZEN-CONSOLIDATED — basin=basin,
            # ZEN-CONSOLIDATED — required_evidence=required_evidence,
        # ZEN-CONSOLIDATED — )

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # ── EARTH OBSERVE — 24-in-1 consolidated surface (Zen, 2026-07-10) ──────
    # ZEN-CONSOLIDATED — # One tool. 24 modes. Replaces 24 individual Earth data fetchers.
    # ZEN-CONSOLIDATED — # earthquake, relief, bathymetry, heatflow, stress, geochem,
    # ZEN-CONSOLIDATED — # plate_reconstruct, paleomag, gravity, ocean, erddap, climate,
    # ZEN-CONSOLIDATED — # hydrology, satellite, uk_petroleum, geology_map, space_weather,
    # ZEN-CONSOLIDATED — # nsta, context_at_location, isitwater, gravity_screen,
    # ZEN-CONSOLIDATED — # judgment_preflight, interpolate_grid, report_to_workflow

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_observe", annotations=_geox_annotations("geox_observe"))
    # ZEN-CONSOLIDATED — async def _observe(
        # ZEN-CONSOLIDATED — mode: str,
        # ZEN-CONSOLIDATED — query: str = "",
        # ZEN-CONSOLIDATED — lat: float | None = None,
        # ZEN-CONSOLIDATED — lng: float | None = None,
        # ZEN-CONSOLIDATED — bbox: list[float] | None = None,
        # ZEN-CONSOLIDATED — limit: int = 10,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        # ZEN-CONSOLIDATED — """Unified Earth observation — 24 data dimensions in one tool.

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Modes: earthquake, relief, bathymetry, heatflow, stress, geochem,
        # ZEN-CONSOLIDATED — plate_reconstruct, paleomag, gravity, ocean, erddap, climate,
        # ZEN-CONSOLIDATED — hydrology, satellite, uk_petroleum, geology_map, space_weather,
        # ZEN-CONSOLIDATED — nsta, context_at_location, isitwater, gravity_screen,
        # ZEN-CONSOLIDATED — judgment_preflight, interpolate_grid, report_to_workflow
        # ZEN-CONSOLIDATED — """
        # ZEN-CONSOLIDATED — from geox_mcp.tools.observe import geox_observe as _impl

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — return await _impl(
            # ZEN-CONSOLIDATED — mode=mode,
            # ZEN-CONSOLIDATED — query=query,
            # ZEN-CONSOLIDATED — lat=lat,
            # ZEN-CONSOLIDATED — lng=lng,
            # ZEN-CONSOLIDATED — bbox=bbox,
            # ZEN-CONSOLIDATED — limit=limit,
        # ZEN-CONSOLIDATED — )

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # ═══════════════════════════════════════════════════════════════════════════════
    # ZEN-CONSOLIDATED — # BASIN ANALYSIS ENGINES (4) — Phase 0 (2026-07-10)
    # ZEN-CONSOLIDATED — # Physics-first basin analysis: backstripping, mass balance, thermal maturity,
    # ZEN-CONSOLIDATED — # claim graph evaluation. Complements simulate_* with backward reconstruction.
    # ZEN-CONSOLIDATED — # ═══════════════════════════════════════════════════════════════════════════════

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # DEREGISTERED ZEN-15 — @mcp.tool(name="geox_basin_backstrip", annotations=_geox_annotations("geox_basin_backstrip"))
    # ZEN-CONSOLIDATED — async def _basin_backstrip(
        # ZEN-CONSOLIDATED — well_ref: str,
        # ZEN-CONSOLIDATED — stratigraphic_ages: list[dict[str, Any]],
        # ZEN-CONSOLIDATED — lithology_model: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — palaeobathymetry_model: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — sea_level_model_ref: str = "",
        # ZEN-CONSOLIDATED — water_density_kg_m3: float = 1030.0,
        # ZEN-CONSOLIDATED — mantle_density_kg_m3: float = 3300.0,
        # ZEN-CONSOLIDATED — uncertainty_realizations: int = 1000,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        # ZEN-CONSOLIDATED — """Reconstruct tectonic and total subsidence through time from validated well stratigraphy.

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Uses Steckler & Watts (1978) Airy isostasy + Sclater & Christie (1980) decompaction.
        # ZEN-CONSOLIDATED — """
        # ZEN-CONSOLIDATED — from geox_mcp.tools.basin_engines.backstrip_tool import geox_basin_backstrip as _impl

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — return await _impl(
            # ZEN-CONSOLIDATED — well_ref=well_ref,
            # ZEN-CONSOLIDATED — stratigraphic_ages=stratigraphic_ages,
            # ZEN-CONSOLIDATED — lithology_model=lithology_model or {},
            # ZEN-CONSOLIDATED — palaeobathymetry_model=palaeobathymetry_model or {},
            # ZEN-CONSOLIDATED — sea_level_model_ref=sea_level_model_ref,
            # ZEN-CONSOLIDATED — water_density_kg_m3=water_density_kg_m3,
            # ZEN-CONSOLIDATED — mantle_density_kg_m3=mantle_density_kg_m3,
            # ZEN-CONSOLIDATED — uncertainty_realizations=uncertainty_realizations,
        # ZEN-CONSOLIDATED — )

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # DEREGISTERED ZEN-15 — @mcp.tool(name="geox_sediment_mass_balance", annotations=_geox_annotations("geox_sediment_mass_balance"))
    # ZEN-CONSOLIDATED — async def _sediment_mass_balance(
        # ZEN-CONSOLIDATED — basin_name: str,
        # ZEN-CONSOLIDATED — source_eroded_km3: float,
        # ZEN-CONSOLIDATED — source_density_kg_m3: float = 2650.0,
        # ZEN-CONSOLIDATED — preserved_volumes: list[dict[str, Any]] | None = None,
        # ZEN-CONSOLIDATED — bypassed_km3: float = 0.0,
        # ZEN-CONSOLIDATED — dissolved_km3: float = 0.0,
        # ZEN-CONSOLIDATED — routing_efficiency: float | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        # ZEN-CONSOLIDATED — """Compute source-to-sink sediment mass balance with uncertainty.

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — Physics: Peters (2012) sediment cycling framework.
        # ZEN-CONSOLIDATED — """
        # ZEN-CONSOLIDATED — from geox_mcp.tools.basin_engines.mass_balance_tool import geox_sediment_mass_balance as _impl

# ZEN-CONSOLIDATED —         # ZEN-CONSOLIDATED — return await _impl(
            # ZEN-CONSOLIDATED — basin_name=basin_name,
            # ZEN-CONSOLIDATED — source_eroded_km3=source_eroded_km3,
            # ZEN-CONSOLIDATED — source_density_kg_m3=source_density_kg_m3,
            # ZEN-CONSOLIDATED — preserved_volumes=preserved_volumes,
            # ZEN-CONSOLIDATED — bypassed_km3=bypassed_km3,
            # ZEN-CONSOLIDATED — dissolved_km3=dissolved_km3,
            # ZEN-CONSOLIDATED — routing_efficiency=routing_efficiency,
        # ZEN-CONSOLIDATED — )

# ZEN-CONSOLIDATED —     # ZEN-CONSOLIDATED — # DEREGISTERED ZEN-15 — @mcp.tool(name="geox_thermal_maturity_history", annotations=_geox_annotations("geox_thermal_maturity_history"))
    # ZEN-CONSOLIDATED — async def _thermal_maturity_history(
        # ZEN-CONSOLIDATED — well_ref: str,
        # ZEN-CONSOLIDATED — burial_history: dict[str, Any],
        # ZEN-CONSOLIDATED — heat_flow_history: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — surface_temp_c: float = 20.0,
        # ZEN-CONSOLIDATED — geothermal_gradient_c_km: float = 30.0,
        # ZEN-CONSOLIDATED — time_step_myr: float = 1.0,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Model burial + heat flow + maturity through time.

        Uses EasyRo (Sweeney & Burnham 1990) + TTI (Lopatin 1971).
        """
        from geox_mcp.tools.basin_engines.thermal_tool import geox_thermal_maturity_history as _impl

        return await _impl(
            well_ref=well_ref,
            burial_history=burial_history,
            heat_flow_history=heat_flow_history,
            surface_temp_c=surface_temp_c,
            geothermal_gradient_c_km=geothermal_gradient_c_km,
            time_step_myr=time_step_myr,
        )

    # DEREGISTERED 2026-07-10 — @mcp.tool(name="geox_claim_graph_evaluate", annotations=_geox_annotations("geox_claim_graph_evaluate"))
    async def _claim_graph_evaluate(
        claims: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        initial_verdicts: dict[str, str] | None = None,
        failure_propagation: str = "cascade",
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate a claim dependency graph.

        Supports AND/OR/WEIGHTED dependency types and failure propagation.
        """
        from geox_mcp.tools.basin_engines.claim_graph_tool import geox_claim_graph_evaluate as _impl

        return await _impl(
            claims=claims,
            edges=edges,
            initial_verdicts=initial_verdicts,
            failure_propagation=failure_propagation,
        )

    # ═══════════════════════════════════════════════════════════════════════════════
    # MACROSTRAT UPSTREAM PROXY — geox_query_macrostrat
    # Canonical upstream proxy for Macrostrat geological database.
    # Registered as a dedicated tool (not a basin mode) per Option B blueprint.
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="geox_query_macrostrat",
        annotations=_geox_annotations("geox_query_macrostrat"),
    )
    async def _geox_query_macrostrat(
        arguments: dict[str, Any] | str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Query the Macrostrat geological database for regional stratigraphy, lithology, and age data.

        Macrostrat provides regional surface geology — lithology, age, and
        stratigraphic columns derived from published geological maps.
        Data is rung 2 (PROCESS_HYPOTHESIS), not subsurface truth.

        Modes: units, columns, sources, fossils, defs, measurements,
               lithologies, environments, intervals, strat_names, map_units

        Attribution: CC-BY-4.0 — Peters et al. (2018) doi:10.17605/OSF.IO/YNAXW

        Use when: the agent needs surface geology, lithology columns, or
        stratigraphic data from the Macrostrat database for a geographic region.
        """
        arguments = _parse_str_arguments(arguments) or {}
        if isinstance(arguments, dict):
            from geox_mcp.tools.macrostrat_unified import geox_query_macrostrat as _impl

            return await _impl(session_id=session_id, **arguments)
        return {
            "ok": False,
            "tool": "geox_query_macrostrat",
            "origin": "UPSTREAM_MACROSTRAT",
            "reason_code": "INVALID_ARGUMENTS",
            "error": f"Expected dict arguments, got {type(arguments).__name__}",
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # BIOSTRAT SUBSTRATE — Phase T1 hardening (2026-07-21, FORGE session SEAL-613335b1f5f34abe).
    # Thin MCP wrappers over existing library code. NO new zonation, NO new taxa,
    # NO schema changes, NO calibration edits. Surface only.
    # Library: src/geox_mcp/tools/biostrat/{taxonomy,schemas}.py + biostrat_falsify.py (~1,771 LOC)
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="geox_biostrat_resolve_taxon",
        annotations=_geox_annotations("geox_biostrat_resolve_taxon"),
    )
    async def _geox_biostrat_resolve_taxon(
        arguments: dict[str, Any] | str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a taxon name to a canonical TaxonRecord via PBDB + Mikrotax.

        Strategy: PBDB first (structured JSON, FAD/LAD ages), Mikrotax fallback
        (may return empty per GEOX code comment 2026-06-16).

        Attribution: PBDB data — CC-BY (paleobiodb.org); Mikrotax — Nannotax3
        citation (Young, Bown, Lees 2022).

        Use when: agent needs to canonicalize a fossil name and obtain FAD/LAD ages.
        Do not use when: regional calibration is required (use Mikrotax or local
        Sabah synthesis — not in scope of this wrapper).
        """
        arguments = _parse_str_arguments(arguments) or {}
        if not isinstance(arguments, dict):
            return {
                "ok": False,
                "tool": "geox_biostrat_resolve_taxon",
                "reason_code": "INVALID_ARGUMENTS",
                "error": f"Expected dict arguments, got {type(arguments).__name__}",
            }
        taxon_name = arguments.get("taxon_name")
        if not taxon_name:
            return {
                "ok": False,
                "tool": "geox_biostrat_resolve_taxon",
                "reason_code": "MISSING_TAXON_NAME",
                "error": "Required argument 'taxon_name' not provided.",
            }
        from geox_mcp.tools.biostrat.taxonomy import resolve_taxon as _impl

        record = await _impl(taxon_name=taxon_name)
        if record is None:
            return {
                "ok": False,
                "tool": "geox_biostrat_resolve_taxon",
                "reason_code": "TAXON_NOT_FOUND",
                "error": f"Taxon '{taxon_name}' not found in PBDB or Mikrotax.",
            }
        return {
            "ok": True,
            "tool": "geox_biostrat_resolve_taxon",
            "data": record.model_dump() if hasattr(record, "model_dump") else record.dict(),
            "attribution": {
                "license": "CC-BY",
                "sources": ["PBDB", "Mikrotax (Nannotax3)"],
                "provenance": getattr(record, "provenance", "PBDB/Mikrotax"),
            },
        }

    @mcp.tool(
        name="geox_biostrat_lookup_zone",
        annotations=_geox_annotations("geox_biostrat_lookup_zone"),
    )
    async def _geox_biostrat_lookup_zone(
        arguments: dict[str, Any] | str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Look up canonical zone metadata: scheme, age range, source.

        Uses PBDB intervals for nanno (scale=5) and foram (scale=24) zones.
        SE Asia-specific schemes (Lunt 2016 LBF, SSB 1995/2013, Morley 1991) are
        NOT in PBDB — returns SCHEME_NOT_IN_PBDB; use Mikrotax or local reference.

        Attribution: PBDB data — CC-BY (paleobiodb.org).

        Use when: agent needs zone age range for correlation or calibration.
        Do not use when: SE Asia regional calibration is needed (T3.16 HOLD).
        """
        arguments = _parse_str_arguments(arguments) or {}
        if not isinstance(arguments, dict):
            return {
                "ok": False,
                "tool": "geox_biostrat_lookup_zone",
                "reason_code": "INVALID_ARGUMENTS",
                "error": f"Expected dict arguments, got {type(arguments).__name__}",
            }
        zone_code = arguments.get("zone_code")
        scheme = arguments.get("scheme", "Martini_1971_NN")
        if not zone_code:
            return {
                "ok": False,
                "tool": "geox_biostrat_lookup_zone",
                "reason_code": "MISSING_ZONE_CODE",
                "error": "Required argument 'zone_code' not provided.",
            }

        # Scheme → PBDB scale mapping. ROUTING ONLY — no new zonation schemes.
        # nanno scales: NN/NP/CC/CN/CP/CNP/CNE/CNO → 5; foram scales: N/P/Wade → 24.
        # SE Asia schemes (LBF/SSB/Morley) intentionally absent → SCHEME_NOT_IN_PBDB.
        scheme_to_scale = {
            "Martini_1971_NN": 5,
            "Martini_1971_NP": 5,
            "Sissingh_1977_CC": 5,
            "Bukry_1973_CN": 5,
            "Okada_Bukry_1980_CP": 5,
            "Agnini_2014_CNP": 5,
            "Agnini_2014_CNE": 5,
            "Agnini_2014_CNO": 5,
            "Blow_1969_N": 24,
            "Blow_1969_P": 24,
            "Wade_2011": 24,
        }
        if scheme not in scheme_to_scale:
            return {
                "ok": False,
                "tool": "geox_biostrat_lookup_zone",
                "reason_code": "SCHEME_NOT_IN_PBDB",
                "error": (
                    f"Scheme '{scheme}' has no PBDB scale mapping. "
                    "SE Asia-specific schemes (Lunt 2016 LBF, SSB 1995/2013, "
                    "Morley 1991) require Mikrotax or local reference (out of scope)."
                ),
            }
        scale = scheme_to_scale[scheme]

        from geox_mcp.tools.biostrat.taxonomy import PBDBClient

        client = PBDBClient()
        try:
            intervals = await client.intervals_list(scale=scale, limit=200)
        finally:
            await client.close()

        zone_upper = str(zone_code).upper().strip()
        match = None
        for iv in intervals:
            name = str(iv.get("nam", "")).upper()
            if name == zone_upper or name.startswith(zone_upper):
                match = iv
                break

        if not match:
            return {
                "ok": False,
                "tool": "geox_biostrat_lookup_zone",
                "reason_code": "ZONE_NOT_FOUND",
                "error": f"Zone '{zone_code}' not found in PBDB scale={scale} (scheme={scheme}).",
                "data": {"scale": scale, "available_count": len(intervals)},
            }
        return {
            "ok": True,
            "tool": "geox_biostrat_lookup_zone",
            "data": {
                "zone_code": zone_code,
                "scheme": scheme,
                "name": match.get("nam"),
                "age_top_ma": match.get("ea"),
                "age_bottom_ma": match.get("la"),
                "pbdb_oid": match.get("oid"),
            },
            "source": "PBDB",
            "attribution": {
                "license": "CC-BY",
                "citation": "Paleobiology Database (paleobiodb.org)",
            },
        }

    @mcp.tool(
        name="geox_biostrat_falsify",
        annotations=_geox_annotations("geox_biostrat_falsify"),
    )
    async def _geox_biostrat_falsify(
        arguments: dict[str, Any] | str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Biostrat Falsification Engine — 8-gate Popperian test of any biostrat claim.

        Single FALSIFIED gate → overall verdict FALSIFIED. Science advances by
        elimination, not confirmation.

        Gates: G1 facies / G2 strat order / G3 taxonomy / G4 reworking /
               G5 diachroneity / G6 seismic / G7 sequence / G8 tectonic.

        Returns governed envelope with per-gate verdicts, evidence_for/evidence_against,
        falsified_gates list, and overall verdict (PASS / WEAK_PASS / FALSIFIED /
        UNFALSIFIABLE / HOLD).

        Use when: agent needs to verify a biostrat interpretation against physical,
        stratigraphic, taxonomic, and tectonic reality. The "jewel" of GEOX biostrat.

        Do not use when: building new zonations or taxonomies (T2.6 calibrate scope).
        """
        arguments = _parse_str_arguments(arguments) or {}
        if not isinstance(arguments, dict):
            return {
                "ok": False,
                "tool": "geox_biostrat_falsify",
                "reason_code": "INVALID_ARGUMENTS",
                "error": f"Expected dict arguments, got {type(arguments).__name__}",
            }
        from geox_mcp.tools.biostrat_falsify import geox_biostrat_falsify as _impl

        return await _impl(**arguments)

    # ═══════════════════════════════════════════════════════════════════════════════
    # BIOSTRAT CALIBRATE — Phase T2.6 (2026-07-21, FORGE session).
    # Conservative calibration layer. Converts biostrat evidence (zone + taxon +
    # optional context) into a defensible age bracket, with falsify integration.
    # NO new zones, NO new taxa, NO schema changes, NO bridge to Macrostrat.
    # Library: src/geox_mcp/tools/biostrat_calibrate.py
    # ═══════════════════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="geox_biostrat_calibrate",
        annotations=_geox_annotations("geox_biostrat_calibrate"),
    )
    async def _geox_biostrat_calibrate(
        arguments: dict[str, Any] | str | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Conservative biostrat calibration — defensible age bracket from zone + taxon.

        T2.6 — calibration only. Does NOT seal. Does NOT bridge to Macrostrat.

        Combines:
          - zone_to_biozone()   → canonical zone bracket (NN/NP/CC/CN/CP/N/P/LBF)
          - resolve_taxon()     → PBDB FAD/LAD with Mikrotax fallback
          - validate_zone_domain() → cross-era / cross-scheme guard
          - geox_biostrat_falsify() → optional 8-gate Popperian check

        Verdict grammar (T2.6): PARTIAL | SABAR | HOLD | VOID | UNKNOWN.
        T2.6 NEVER emits SEAL — that is for sovereign/judge path.

        Returns: ok, tool, data { calibrated_age_min_ma, calibrated_age_max_ma,
        best_age_label, input_basis, sources_used, evidence_for, evidence_against,
        uncertainty_notes, falsification_summary, confidence_tier, verdict,
        audit_receipt }.

        Use when: agent needs a defensible age bracket from biostrat inputs and
        accepts conservative uncertainty.
        Do not use when: bridging to Macrostrat (T2.7), sealing (T3.x), or
        claiming authoritative age (use arifOS arif_judge for sovereign verdicts).
        """
        arguments = _parse_str_arguments(arguments) or {}
        if not isinstance(arguments, dict):
            return {
                "ok": False,
                "tool": "geox_biostrat_calibrate",
                "reason_code": "INVALID_ARGUMENTS",
                "error": f"Expected dict arguments, got {type(arguments).__name__}",
            }
        from geox_mcp.tools.biostrat_calibrate import geox_biostrat_calibrate as _impl

        return await _impl(**arguments)

    # ═══════════════════════════════════════════════════════════════════════════════
    # MCP APP VISUAL TOOLS — Main server registration (Fix HOLD-2026-07-11)
    # These tools are also on the witness sub-server via mcp.mount(), but mount does
    # NOT composite annotations/AppConfig into the main server's tools/list.
    # Registering here ensures they appear in tools/list with ui.resourceUri bindings.
    # ═══════════════════════════════════════════════════════════════════════════════

    # PLAN-2026-07-12-GEOX-MCP-APP-SLICE-001 option A — well-desk open (P0)
    try:
        from fastmcp.apps import AppConfig as _AppConfig

        _well_desk_app = _AppConfig(
            resourceUri="ui://geox/well-desk",
            visibility=["app", "model"],
        )
    except Exception:  # pragma: no cover
        _well_desk_app = None

    # DEREGISTERED ZEN-15 — geox_well_desk_open (absorbed into geox_well_desk)
    # @mcp.tool(
    #     name="geox_well_desk_open",
    #     annotations={...},
    #     meta={...},
    # )
    async def _well_desk_open(
        well_id: str,
        mode: str = "summary",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """OBSERVE · Open GEOX well-desk interactive view (SEP-1865).

        Read-only operator summary. Hosts that support MCP Apps open
        ui://geox/well-desk (P0 single-file shell). Hosts without UI still
        receive structuredContent + text. No mutation. No secrets in UI.

        Use when: operator wants interactive well-desk / well summary view.
        Do not use when: ingesting new LAS (use geox_well_ingest) or deep QC
        (use geox_well_qc).
        """

        _mode = (mode or "summary").strip().lower()
        if _mode not in ("summary", "tracks"):
            _mode = "summary"
        _wid = (well_id or "").strip()
        if not _wid:
            return {
                "ok": False,
                "isError": True,
                "error_class": "MISSING_REQUIRED_FIELD",
                "message": "well_id is required",
                "tool": "geox_well_desk_open",
            }

        # Lightweight OBSERVE summary — no file IO required for P0 path proof.
        # Future: hydrate from geox_well_qc / artifact store when well_id resolves.
        summary = {
            "well_id": _wid,
            "mode": _mode,
            "band": "UNKNOWN",
            "note": ("P0 operator shell — interactive HTML via host iframe; full multi-track desk is GEOX_WELL_DESK_UI=full."),
            "views": (
                ["composite_log", "summary_card"] if _mode == "summary" else ["composite_log", "tracks", "crossplot_placeholder"]
            ),
            "patterns_stolen": [
                "instant well identity card",
                "mode switch summary|tracks",
                "host-mediated refresh only",
            ],
        }
        text = (
            f"Well-desk open: well_id={_wid} mode={_mode}. "
            f"UI resource: ui://geox/well-desk. "
            f"Band={summary['band']} (no vitals invented)."
        )
        return {
            "ok": True,
            "tool": "geox_well_desk_open",
            "well_id": _wid,
            "mode": _mode,
            "band": summary["band"],
            "summary": summary,
            "ui": {
                "resourceUri": "ui://geox/well-desk",
                "protocol": "SEP-1865",
                "p0_shell": True,
            },
            "session_id": session_id,
            "actor_id": actor_id,
            "trace_id": trace_id,
            "epistemic": {
                "layer": "OBS",
                "confidence_cap": 0.7,
                "note": "Identity card only until artifact hydrate is wired",
            },
            "ts": datetime.now(UTC).isoformat(),
            "content_text": text,
            "w0": "OPERATOR_VETO_INTACT",
            "final_authority": "ARIF",
        }

    @mcp.tool(
        name="geox_map_context_scene",
        annotations={
            "title": "Map Context Scene",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
            "ui": {"resourceUri": "ui://geox/workspace-v1.html"},
        },
    )
    async def _map_context_scene(
        bbox: list[float],
        mode: str = "bbox_context",
        crs: str = "EPSG:4326",
        vp_slice_inline: dict[str, Any] | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Spatial bbox context, CRS checks, and causal scene rendering.

        Modes:
            - bbox_context: Return bbox summary and scene metadata (default).
            - render_scene: Render causal scene map.
            - render_geojson: Return GeoJSON FeatureCollection with selectable geological features.
            - scene_summary: Summarize geological scene context.
            - crs_check: Validate and transform CRS.
            - coordinate_guardrail: Check coordinates against basin boundaries.
            - georeference_map: Georeference raster or vector data.

        When this tool is called, the MCP host opens the GEOX Workspace
        (ui://geox/workspace-v1.html) in a sandboxed iframe for read-only evidence review.

        Use when: the user provides a bounding box, coordinates, or asks for
        geological context of a region. Also used for rendering geological maps
        with selectable features.
        """
        # ── DEBUG (2026-07-11): verify identity propagation through bridge ──
        import logging

        from geox_mcp.tools.map_context import geox_map_context_scene as _impl

        _log = logging.getLogger("geox.canonical.map_context")
        _log.warning(f"IDENTITY_ARRIVAL: session_id={session_id!r} actor_id={actor_id!r} trace_id={trace_id!r}")

        return await _impl(
            bbox=bbox,
            mode=mode,
            crs=crs,
            vp_slice_inline=vp_slice_inline,
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    # DEREGISTERED ZEN-15 — geox_well_desk_publish (absorbed into geox_well_desk)
    # @mcp.tool(
    #     name="geox_well_desk_publish",
    #     annotations={...},
    # )
    async def _well_desk_publish(
        well_id: str,
        image_base64: str,
        metadata: dict[str, Any],
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """MUTATE · Publish a rendered well-desk image with embedded metadata.

        Accepts the base64-encoded PNG and its associated metadata, saves it
        to /root/GEOX/data/renders/, and seals the hash to the VAULT999
        seal chain.

        Use when: the user clicks 'Publish Image' inside the Well-Desk UI.
        """
        import base64
        import hashlib
        import json
        from pathlib import Path

        # 1. Clean input
        _wid = (well_id or "").strip()
        if not _wid:
            return {"ok": False, "isError": True, "message": "well_id is required"}

        # 2. Decode image
        try:
            img_bytes = base64.b64decode(image_base64)
        except Exception as e:
            return {"ok": False, "isError": True, "message": f"Failed to decode base64: {e}"}

        if not img_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return {"ok": False, "isError": True, "message": "Invalid PNG signature"}

        # 3. Save file
        renders_dir = Path(os.environ.get("GEOX_RENDERS_DIR", "/root/GEOX/data/renders"))
        renders_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"well-desk-{_wid}-{timestamp}.png"
        filepath = renders_dir / filename
        filepath.write_bytes(img_bytes)

        # 4. Hash and Seal to VAULT999
        image_sha = f"sha256:{hashlib.sha256(img_bytes).hexdigest()}"
        seal_token = f"SEAL-IMG-{hashlib.sha256(img_bytes).hexdigest()[:16].upper()}"

        seal_entry = {
            "entry_type": "IMAGE_SEAL",
            "token": seal_token,
            "well_id": _wid,
            "image_sha256": image_sha,
            "filename": filename,
            "filepath": str(filepath),
            "issued_at": datetime.now(UTC).isoformat() + "Z",
            "actor": actor_id or "ARIF",
            "session_id": session_id or "geox_session",
            "metadata": metadata,
            "epoch": datetime.now(UTC).isoformat() + "Z",
        }

        # IMAGE_SEAL is a side ledger — NEVER write seal_chain.jsonl / seal_chain_head.json
        # (those are the constitutional hash chain; IMAGE_SEAL pollution broke head 2026-07-12).
        vault_dir = Path(os.environ.get("GEOX_VAULT_IMAGE_DIR", "/root/.local/share/arifos/vault999"))
        vault_dir.mkdir(parents=True, exist_ok=True)
        chain_path = vault_dir / "image_seal_chain.jsonl"
        head_path = vault_dir / "image_seal_head.json"

        # Safe append with lock
        import fcntl

        lock_path = vault_dir / ".image_seal.lock"
        with open(lock_path, "a") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            try:
                # Append to image seal side-chain
                with open(chain_path, "a") as f:
                    f.write(json.dumps(seal_entry) + "\n")
                    f.flush()
                with open(head_path, "w") as f:
                    json.dump(seal_entry, f)
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)

        # 5. Vault witness - append IMAGE_SEAL to constitutional outcomes.jsonl
        try:
            outcomes_path = vault_dir / "outcomes.jsonl"
            vault_entry = {
                "ts": datetime.now(UTC).isoformat(),
                "event": "IMAGE_SEAL",
                "actor": actor_id or "ARIF",
                "session": session_id or "geox_session",
                "tool": "geox_well_desk_publish",
                "verdict": "SEAL",
                "elapsed_ms": 0,
                "image_sha256": image_sha,
                "well_id": _wid,
                "filename": filename,
                "seal_token": seal_token,
            }
            with open(lock_path, "a") as lockf:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
                try:
                    with open(outcomes_path, "a") as f:
                        f.write(json.dumps(vault_entry) + "\n")
                        f.flush()
                finally:
                    fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
        except Exception as vault_err:
            # Non-fatal - side ledger already written
            vault_note = f" (vault witness failed: {vault_err})"

        text = f"Image published successfully{vault_note}. Well: {_wid}. Path: {filepath}. Seal: {seal_token}"

        # Return to client/conversation
        return {
            "ok": True,
            "tool": "geox_well_desk_publish",
            "well_id": _wid,
            "seal_token": seal_token,
            "image_sha256": image_sha,
            "filepath": str(filepath),
            "metadata": metadata,
            "content_text": text,
        }

    # DEREGISTERED ZEN-15 — geox_render_well_panel (absorbed into geox_well_desk)
    # @mcp.tool(
    #     name="geox_render_well_panel",
    #     annotations={...},
    # )
    async def _render_well_panel(
        well_id: str,
        depth_top: float | None = None,
        depth_base: float | None = None,
        curves: list[str] | None = None,
        las_path: str | None = None,
        interpret: bool = True,
        rw: float = 0.03,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """OBSERVE · Render well-log panel with petrophysics + earth meaning.

        Default interpret=True: open LAS → Vsh/φe/Sw (DERIVED) + GR motif and
        reservoir/fluid read (INTERPRETED) on multi-track PNG with meaning panel.
        Resolves Equinor Volve 15/9-19 and Marmousi demo LAS by well_id or las_path.

        Use when: user wants a well panel, petrophysical interpretation, or earth
        meaning decoded from open-source or provided LAS.
        """
        if interpret:
            try:
                from geox_mcp.render_well_panel_petro import render_interpreted_panel

                return render_interpreted_panel(
                    well_id=well_id,
                    depth_top=depth_top,
                    depth_base=depth_base,
                    las_path=las_path,
                    rw=rw,
                    session_id=session_id,
                    actor_id=actor_id,
                )
            except Exception as e:
                return {
                    "ok": False,
                    "isError": True,
                    "message": f"interpreted panel failed: {type(e).__name__}: {e}",
                    "tool": "geox_render_well_panel",
                }

        # Minimal scaffold fallback when interpret=False and no LAS workflow
        import base64
        import hashlib
        import io
        import math

        import matplotlib

        matplotlib.use("Agg")
        from datetime import UTC, datetime
        from pathlib import Path

        import matplotlib.pyplot as plt
        from PIL import Image as PILImage
        from PIL.PngImagePlugin import PngInfo

        _wid = (well_id or "").strip() or "UNKNOWN"
        d0 = float(depth_top if depth_top is not None else 3000.0)
        d1 = float(depth_base if depth_base is not None else 4000.0)
        d = np.arange(d0, d1 + 0.5, 0.5)
        frac = (d - d0) / max(d1 - d0, 1e-9)
        fig, axes = plt.subplots(1, 3, figsize=(8, 7), sharey=True, facecolor="#0f0f1a")
        fig.suptitle(f"GEOX scaffold — {_wid}", color="white")
        for ax, v, col, title in zip(
            axes,
            (30 + 80 * np.sin(frac * math.pi * 3), 10 ** (0.5 + frac), 0.2 + 0.1 * np.sin(frac * math.pi)),
            ("#f1c40f", "#2ecc71", "#3498db"),
            ("GR syn", "RT syn", "φ syn"),
            strict=False,
        ):
            ax.plot(v, d, color=col)
            ax.set_title(title, color="white")
            ax.set_facecolor("#0f0f1a")
            ax.tick_params(colors="white")
            ax.invert_yaxis()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, facecolor="#0f0f1a")
        plt.close()
        renders = Path(os.environ.get("GEOX_RENDERS_DIR", "/root/GEOX/data/renders"))
        renders.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        fp = renders / f"well-panel-scaffold-{_wid}-{ts}.png"
        img = PILImage.open(io.BytesIO(buf.getvalue()))
        meta = PngInfo()
        meta.add_text("provenance", "scaffold")
        meta.add_text("well_id", _wid)
        img.save(fp, "PNG", pnginfo=meta)
        raw = fp.read_bytes()
        sha = f"sha256:{hashlib.sha256(raw).hexdigest()}"
        tok = f"SEAL-IMG-{hashlib.sha256(raw).hexdigest()[:16].upper()}"
        return {
            "ok": True,
            "tool": "geox_render_well_panel",
            "well_id": _wid,
            "seal_token": tok,
            "image_sha256": sha,
            "filepath": str(fp),
            "provenance": "scaffold",
            "content_text": f"Scaffold-only panel → {fp}",
            "metadata": {"provenance": "scaffold", "well_id": _wid},
            "image_base64_len": len(base64.b64encode(raw)),
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # ZEN-15 CANONICAL TOOLS (2026-07-13)
    # Unified tools absorbing multiple legacy tools into mode-based interfaces.
    # DITEMPA BUKAN DIBERI.
    # ═══════════════════════════════════════════════════════════════════════════════

    # KUTIP SAMPAH 2026-08-05 H1/W5 — deregistered public leak
    # @mcp.tool(name="geox_gravmag_studio", annotations=_geox_annotations("geox_gravmag_studio"))
    async def _gravmag_studio(
        mode: str = "open",
        survey_type: str = "gravity",
        easting_m: list[float] | None = None,
        northing_m: list[float] | None = None,
        observed_values: list[float] | None = None,
        prisms: list[dict[str, Any]] | None = None,
        magnetization_a_m: float = 0.0,
        field_declination_deg: float = 0.0,
        field_inclination_deg: float = 0.0,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Gravity/magnetic studio: forward modeling and screening. Modes: open, screen.

        open   — interactive GravMag Studio UI with forward modeling
        screen — screening analysis against observed data
        """
        if mode == "screen":
            from geox_mcp.tools.geophysics_studio_screen import geox_gravmag_studio_screen as _impl

            return await _impl(
                survey_type=survey_type,
                easting_m=easting_m or [],
                northing_m=northing_m or [],
                observed_values=observed_values or [],
                prisms=prisms or [],
                magnetization_a_m=magnetization_a_m,
                field_declination_deg=field_declination_deg,
                field_inclination_deg=field_inclination_deg,
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
        # Default: open
        from geox_mcp.tools.geophysics_studio import geox_gravmag_studio_open as _impl

        return await _impl(
            survey_type=survey_type,
            easting_m=easting_m or [],
            northing_m=northing_m or [],
            observed_values=observed_values or [],
            prisms=prisms or [],
            magnetization_a_m=magnetization_a_m,
            field_declination_deg=field_declination_deg,
            field_inclination_deg=field_inclination_deg,
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_well_desk", annotations=_geox_annotations("geox_well_desk"))
    # ZEN-CONSOLIDATED — async def _well_desk(
        # ZEN-CONSOLIDATED — mode: str = "open",
        # ZEN-CONSOLIDATED — well_id: str = "",
        # ZEN-CONSOLIDATED — depth_top: float | None = None,
        # ZEN-CONSOLIDATED — depth_base: float | None = None,
        # ZEN-CONSOLIDATED — curves: list[str] | None = None,
        # ZEN-CONSOLIDATED — las_path: str | None = None,
        # ZEN-CONSOLIDATED — interpret: bool = True,
        # ZEN-CONSOLIDATED — rw: float = 0.03,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Well desk: interactive view, publish, render. Modes: open, publish, render.

        open    — interactive well-desk view (MCP App)
        publish — render and publish well panel image
        render  — render well-log panel with petrophysics
        """
        from geox_mcp.tools.mcp_apps_bridge import wrap_as_ui_tool_result

        if mode == "publish":
            from geox_mcp.tools.integration_well import geox_well_desk_publish as _impl

            pub = await _impl(
                well_id=well_id,
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
            return wrap_as_ui_tool_result(
                pub,
                app_id="well_desk",
                params={"well_id": well_id, "mode": "publish"} if well_id else None,
            )
        if mode in ("petro", "lem_inference", "petrophysics"):
            from geox_mcp.tools.integration_well import geox_well_desk_petro as _impl

            petro = await _impl(
                well_id=well_id,
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
            return wrap_as_ui_tool_result(
                petro,
                app_id="well_desk",
                params={"well_id": well_id, "mode": "petro"} if well_id else None,
                text=(f"Well desk petro (lem_inference path) for {well_id or 'unknown'}. ADVISORY · NOT_SEALED."),
            )
        if mode == "render":
            from geox_mcp.render_well_panel_petro import render_interpreted_panel

            rendered = render_interpreted_panel(
                well_id=well_id,
                depth_top=depth_top,
                depth_base=depth_base,
                las_path=las_path,
                rw=rw,
                session_id=session_id,
                actor_id=actor_id,
            )
            # G3.4 epistemic: never SEAL language on demo
            if isinstance(rendered, dict):
                from geox_mcp.tools.integration_well import _is_demo_well_id

                if _is_demo_well_id(well_id or ""):
                    rendered = {
                        **rendered,
                        "authority_claim": "ADVISORY",
                        "seal_status": "NOT_SEALED",
                        "data_class": "DEMO",
                    }
            return wrap_as_ui_tool_result(
                rendered,
                app_id="well_desk",
                params={"well_id": well_id, "mode": "render"} if well_id else None,
                text=f"Well panel rendered for {well_id or 'unknown'} (ADVISORY).",
            )
        # Default: open — already returns 3-channel ToolResult
        from geox_mcp.tools.integration_well import geox_well_desk_open as _impl

        return await _impl(
            well_id=well_id,
            mode="summary" if mode in ("open", "summary", "") else mode,
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    # ═══════════════════════════════════════════════════════════════════════════════
    # POST-REGISTRATION ENRICHMENT — Binding 3 compliance (mcp-builder-doctrine v1.1.0)
    # Injects rich descriptions + "Use when..." trigger from tools_manifest.py
    # into the MCP surface. Without this, the model sees only minimal docstrings.
    @mcp.tool(name="geox_list_apps", annotations=_geox_annotations("geox_list_apps"))
    async def _list_apps(
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """List all registered GEOX MCP Apps (SEP-1865). Returns app_id, uri, title, description, and external_url for each discoverable app. MCP Apps Hosts use this to populate their app launcher."""
        from geox_mcp.tools.mcp_apps_bridge import list_apps as _impl

        apps = _impl()
        return {
            "content": [{"type": "text", "text": json.dumps(apps, indent=2)}],
            "apps": apps,
            "count": len(apps),
            "standard": "SEP-1865",
            "_meta": {
                "ui": {
                    "resourceUri": "ui://geox/catalog",
                    "title": "GEOX Skills Catalog",
                    "renderMode": "panel",
                }
            },
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # P0 REGISTRY DRIFT FIX — 8 manifest-only tools wired to callable surface
    # Forged 2026-07-20. These had implementations but no @mcp.tool decorators.
    # ═══════════════════════════════════════════════════════════════════════════════

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_basin_backstrip", annotations=_geox_annotations("geox_basin_backstrip"))
    # ZEN-CONSOLIDATED — async def _basin_backstrip(
        # ZEN-CONSOLIDATED — well_ref: str,
        # ZEN-CONSOLIDATED — stratigraphic_ages: list[dict[str, Any]],
        # ZEN-CONSOLIDATED — lithology_model: dict[str, Any],
        # ZEN-CONSOLIDATED — palaeobathymetry_model: dict[str, Any],
        # ZEN-CONSOLIDATED — sea_level_model_ref: str = "",
        # ZEN-CONSOLIDATED — water_density_kg_m3: float = 1030.0,
        # ZEN-CONSOLIDATED — mantle_density_kg_m3: float = 3300.0,
        # ZEN-CONSOLIDATED — uncertainty_realizations: int = 1000,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """1D basin backstripping: Steckler & Watts 1978 + Sclater & Christie 1980."""
        from geox_mcp.tools.basin_engines.backstrip_tool import geox_basin_backstrip as _impl

        args = _safe_forward(
            _impl,
            {
                "well_ref": well_ref,
                "stratigraphic_ages": stratigraphic_ages,
                "lithology_model": lithology_model,
                "palaeobathymetry_model": palaeobathymetry_model,
                "sea_level_model_ref": sea_level_model_ref,
                "water_density_kg_m3": water_density_kg_m3,
                "mantle_density_kg_m3": mantle_density_kg_m3,
                "uncertainty_realizations": uncertainty_realizations,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    # KUTIP SAMPAH 2026-08-05 H1/W5 — deregistered public leak
    # @mcp.tool(name="geox_claim_graph_evaluate", annotations=_geox_annotations("geox_claim_graph_evaluate"))
    async def _claim_graph_evaluate(
        claims: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        initial_verdicts: dict[str, str] | None = None,
        failure_propagation: str = "cascade",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate a claim dependency graph (AND/OR/WEIGHTED propagation)."""
        from geox_mcp.tools.basin_engines.claim_graph_tool import geox_claim_graph_evaluate as _impl

        args = _safe_forward(
            _impl,
            {
                "claims": claims,
                "edges": edges,
                "initial_verdicts": initial_verdicts,
                "failure_propagation": failure_propagation,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        result = await _impl(**args)
        from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui, wrap_as_ui_tool_result

        return wrap_as_ui_tool_result(
            result,
            app_id="risk_console",
            structured_override=compact_structured_for_ui(
                result if isinstance(result, dict) else {"data": result},
                tool="geox_claim_graph_evaluate",
                app_id="risk_console",
            ),
            text="Claim graph evaluate complete. UI: ui://geox/risk-console.",
        )

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_contradiction_scan", annotations=_geox_annotations("geox_contradiction_scan"))
    # ZEN-CONSOLIDATED — async def _contradiction_scan(
        # ZEN-CONSOLIDATED — claim_text: str = "",
        # ZEN-CONSOLIDATED — claim_type: str = "general",
        # ZEN-CONSOLIDATED — mode: str = "full",
        # ZEN-CONSOLIDATED — context: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — evidence: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Popperian falsification: scan claims for internal contradictions."""
        from geox_mcp.tools.contradiction_scan import geox_contradiction_scan as _impl

        args = _safe_forward(
            _impl,
            {
                "claim_text": claim_text,
                "claim_type": claim_type,
                "mode": mode,
                "context": context,
                "evidence": evidence,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        result = await _impl(**args)
        from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui, wrap_as_ui_tool_result

        return wrap_as_ui_tool_result(
            result,
            app_id="judge_console",
            params={"mode": mode},
            structured_override=compact_structured_for_ui(
                result if isinstance(result, dict) else {"data": result},
                tool="geox_contradiction_scan",
                app_id="judge_console",
            ),
            text=f"Contradiction scan {mode}: {(claim_text or '')[:60]}. UI: ui://geox/judge-console.",
        )

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_evidence", annotations=_geox_annotations("geox_evidence"))
    # ZEN-CONSOLIDATED — async def _evidence(
        # ZEN-CONSOLIDATED — mode: str = "synthesize",
        # ZEN-CONSOLIDATED — evidence_id: str = "",
        # ZEN-CONSOLIDATED — evidence_type: str = "supporting",
        # ZEN-CONSOLIDATED — claim_id: str = "",
        # ZEN-CONSOLIDATED — claim_text: str = "",
        # ZEN-CONSOLIDATED — query: str = "",
        # ZEN-CONSOLIDATED — scope: str = "all",
        # ZEN-CONSOLIDATED — file_path: str = "",
        # ZEN-CONSOLIDATED — basin_name: str | None = None,
        # ZEN-CONSOLIDATED — evidence_refs: list[str] | None = None,
        # ZEN-CONSOLIDATED — hypotheses: list[str] | None = None,
        # ZEN-CONSOLIDATED — epistemic_label: str | None = None,
        # ZEN-CONSOLIDATED — forbidden_uses: list[str] | None = None,
        # ZEN-CONSOLIDATED — source_citation: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — category: str | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Unified evidence — discover, synthesize, abduct, contradict, ingest_literature.

        Modes:
          discover          - Search SharePoint/OneDrive/local for geological evidence
          synthesize        - Cross-domain evidence graph synthesis
          abduct            - Generate competing geological process hypotheses
          contradict        - Attack hypotheses and surface contradictions
          spatial_block     - Spatial block-CV
          ingest_literature - PDF literature ingest with claim scaffold
        """
        from geox_mcp.tools.evidence_unified import geox_evidence as _impl

        args = _safe_forward(
            _impl,
            {
                "mode": mode,
                "evidence_id": evidence_id,
                "evidence_type": evidence_type,
                "claim_id": claim_id,
                "claim_text": claim_text,
                "query": query,
                "scope": scope,
                "file_path": file_path,
                "basin_name": basin_name,
                "evidence_refs": evidence_refs,
                "hypotheses": hypotheses,
                "epistemic_label": epistemic_label,
                "forbidden_uses": forbidden_uses,
                "source_citation": source_citation,
                "category": category,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        result = await _impl(**args)
        from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui, wrap_as_ui_tool_result

        return wrap_as_ui_tool_result(
            result,
            app_id="judge_console",
            params={"claim_id": claim_id} if claim_id else None,
            structured_override=compact_structured_for_ui(
                result if isinstance(result, dict) else {"data": result},
                tool="geox_evidence",
                app_id="judge_console",
            ),
            text=f"Evidence {evidence_type}: claim={claim_id or 'n/a'}. UI: ui://geox/judge-console.",
        )

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_lem_predict", annotations=_geox_annotations("geox_lem_predict"))
    # ZEN-CONSOLIDATED — async def _lem_predict(
        # ZEN-CONSOLIDATED — target_depth_m: float | None = None,
        # ZEN-CONSOLIDATED — basin_context: str | None = None,
        # ZEN-CONSOLIDATED — cube_inline: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — lmr_inline: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — use_synth_cube: bool = True,
        # ZEN-CONSOLIDATED — candidate_ref: str | None = None,
        # ZEN-CONSOLIDATED — domain: str | None = None,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Litho-Elastic prediction via LEM inference engine.

        Simplified surface: accepts target depth + basin context.
        Internally constructs LEMPredictRequest for the physics-prior engine.
        For full curve-based prediction, use the LEM engine directly via
        geox_petrophysics(mode='lem_inference') with well log data.
        """
        from geox_mcp.tools.lem_predict import LEMPredictRequest, geox_lem_predict as _impl

        # Construct a valid minimal request from surface params.
        # Full-curve prediction requires geox_petrophysics(mode='lem_inference').
        req = LEMPredictRequest(
            well_id=candidate_ref or "lem-synthetic",
            curves={"GR": [75.0], "RT": [5.0], "RHOB": [2.35]},
            depth_m=[target_depth_m] if target_depth_m else [1500.0],
            depth_top_m=target_depth_m,
            depth_bot_m=target_depth_m,
            basin=basin_context,
            session_id=session_id,
            actor_id=actor_id,
        )
        result = await _impl(req)
        payload = result if isinstance(result, dict) else result.model_dump(mode="json")
        from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui, wrap_as_ui_tool_result

        return wrap_as_ui_tool_result(
            payload,
            app_id="well_desk",
            params={"mode": "lem", "depth_m": target_depth_m},
            structured_override=compact_structured_for_ui(payload, tool="geox_lem_predict", app_id="well_desk"),
            text=(f"LEM predict depth={target_depth_m} basin={basin_context or 'n/a'}. UI: ui://geox/well-desk."),
        )

    # KUTIP SAMPAH 2026-08-05 H1/W5 — deregistered public leak
    # @mcp.tool(name="geox_sediment_mass_balance", annotations=_geox_annotations("geox_sediment_mass_balance"))
    async def _sediment_mass_balance(
        basin_name: str,
        source_eroded_km3: float,
        source_density_kg_m3: float = 2650.0,
        preserved_volumes: list[dict[str, Any]] | None = None,
        bypassed_km3: float = 0.0,
        dissolved_km3: float = 0.0,
        routing_efficiency: float | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Source-to-sink sediment mass balance with compaction correction."""
        from geox_mcp.tools.basin_engines.mass_balance_tool import geox_sediment_mass_balance as _impl

        args = _safe_forward(
            _impl,
            {
                "basin_name": basin_name,
                "source_eroded_km3": source_eroded_km3,
                "source_density_kg_m3": source_density_kg_m3,
                "preserved_volumes": preserved_volumes,
                "bypassed_km3": bypassed_km3,
                "dissolved_km3": dissolved_km3,
                "routing_efficiency": routing_efficiency,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    # ZEN-CONSOLIDATED — @mcp.tool(name="geox_thermal_maturity_history", annotations=_geox_annotations("geox_thermal_maturity_history"))
    # ZEN-CONSOLIDATED — async def _thermal_maturity_history(
        # ZEN-CONSOLIDATED — well_ref: str,
        # ZEN-CONSOLIDATED — burial_history: dict[str, Any],
        # ZEN-CONSOLIDATED — heat_flow_history: dict[str, Any] | None = None,
        # ZEN-CONSOLIDATED — surface_temp_c: float = 20.0,
        # ZEN-CONSOLIDATED — geothermal_gradient_c_km: float = 30.0,
        # ZEN-CONSOLIDATED — time_step_myr: float = 1.0,
        # ZEN-CONSOLIDATED — session_id: str | None = None,
        # ZEN-CONSOLIDATED — actor_id: str | None = None,
        # ZEN-CONSOLIDATED — trace_id: str | None = None,
    # ZEN-CONSOLIDATED — ) -> dict[str, Any]:
        """Burial + heat flow + maturity modelling (EasyRo + TTI)."""
        from geox_mcp.tools.basin_engines.thermal_tool import geox_thermal_maturity_history as _impl

        args = _safe_forward(
            _impl,
            {
                "well_ref": well_ref,
                "burial_history": burial_history,
                "heat_flow_history": heat_flow_history,
                "surface_temp_c": surface_temp_c,
                "geothermal_gradient_c_km": geothermal_gradient_c_km,
                "time_step_myr": time_step_myr,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    # KUTIP SAMPAH 2026-08-05 H1/W5 — deregistered public leak
    # @mcp.tool(name="geox_to_wealth_bridge", annotations=_geox_annotations("geox_to_wealth_bridge"))
    async def _to_wealth_bridge(
        prospect_ref: str,
        npv_usd: float | None = None,
        irr: float | None = None,
        breakeven_usd: float | None = None,
        discount_rate: float = 0.10,
        risk_geo: float = 0.0,
        sigma_market: float = 0.0,
        sigma_policy: float = 0.0,
        admissibility: str = "admitted",
        epistemic_source: str = "ESTIMATE",
        penalty_infinite: bool = False,
        carbon_cost_usd: float = 0.0,
        delay_risk: float = 0.0,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """GEOX→WEALTH governed handoff: prospect economics to capital model."""
        from geox_mcp.tools.wealth_bridge_tool import geox_to_wealth_bridge as _impl

        args = _safe_forward(
            _impl,
            {
                "prospect_id": prospect_ref,
                "npv_usd": npv_usd,
                "irr": irr,
                "breakeven_usd": breakeven_usd,
                "discount_rate": discount_rate,
                "risk_geo": risk_geo,
                "sigma_market": sigma_market,
                "sigma_policy": sigma_policy,
                "admissibility": admissibility,
                "epistemic_source": epistemic_source,
                "penalty_infinite": penalty_infinite,
                "carbon_cost_usd": carbon_cost_usd,
                "delay_risk": delay_risk,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    # ═══════════════════════════════════════════════════════════════════════════════
    # H2: GEOX Workspace Tool — persistent session context (P1)
    # ═══════════════════════════════════════════════════════════════════════════════
    try:
        from geox_mcp.tools.workspace_tool import geox_workspace

        @mcp.tool(name="geox_workspace", annotations=_geox_annotations("geox_workspace"))
        async def _workspace(
            mode: str = "view",
            basin: str | None = None,
            play: str | None = None,
            well_id: str | None = None,
            field: str | None = None,
            prospect_ref: str | None = None,
            session_id: str = "default",
            actor_id: str | None = None,
            trace_id: str | None = None,
        ):
            """GEOX Workspace — persistent geological context across all tools.

            Set your basin/play/well once and every subsequent tool
            (Earth Volume, Prospect Studio, Basin Explorer) inherits the context.

            Modes: set (set context), view (see current state), history (tool call log),
                   evidence (evidence stack), relations (knowledge graph), reset (clear).

            Governance: pass actor_id + valid session_id (from arif_init) — evidence lane.
            """
            return await geox_workspace(
                mode=mode,
                basin=basin,
                play=play,
                well_id=well_id,
                field=field,
                prospect_ref=prospect_ref,
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )

        logger.info("H2: geox_workspace tool registered")
    except Exception as e:
        logger.warning("H2: geox_workspace registration skipped: %s", e)

    # ═══════════════════════════════════════════════════════════════════
    # H3 — geox_contrast_metabolize (Eureka 2026-08-13)
    # Unified anomalous-contrast metabolic pipeline:
    #   ISOLATE → MEASURE → CLASSIFY (≥3 stratigraphic trap hypotheses)
    # substrate_class=INERT · authority_ceiling=COMPUTE_ONLY
    # local_verdict=QUALIFIED_CANDIDATE — arifOS seals only.
    # Closes the 1-tool surface gap kept /health in status=degraded.
    # ═══════════════════════════════════════════════════════════════════
    try:
        @mcp.tool(name="geox_contrast_metabolize", annotations=_geox_annotations("geox_contrast_metabolize"))
        async def _contrast_metabolize(
            arguments: dict[str, Any] | None = None,
            session_id: str | None = None,
            actor_id: str | None = None,
            trace_id: str | None = None,
        ) -> dict[str, Any]:
            """Unified anomalous contrast metabolic pipeline (Eureka 2026-08-13).

            Binds three stages into one call:
              1. ISOLATE — deterministic acoustic impedance contrast detection
              2. MEASURE — AVO gradient + LMR estimates at contrast points
              3. CLASSIFY — ≥3 stratigraphic trap hypotheses for LLM handoff

            substrate_class: INERT
            authority_ceiling: COMPUTE_ONLY
            local_verdict: QUALIFIED_CANDIDATE (arifOS seals)
            """
            from geox_mcp.tools.contrast_metabolize import geox_contrast_metabolize as _impl

            args = _safe_forward(
                _impl,
                arguments or {},
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
            return await _impl(**args)

        logger.info("H3: geox_contrast_metabolize tool registered")
    except Exception as e:
        logger.warning("H3: geox_contrast_metabolize registration skipped: %s", e)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1 — deterministic 2D geological model renderer
    # Arif directive 2026-07-29: F2 TRUTH — computed, not hallucinated.
    # Pure matplotlib rendering. Zero external I/O. Zero hallucination.
    # ═══════════════════════════════════════════════════════════════════
    from pydantic import BaseModel, Field

    class _StrataUnit(BaseModel):
        """A single stratigraphic unit in the cross-section."""

        name: str = Field(..., description="Unit name (e.g. Sandstone, Shale)")
        thickness_m: float = Field(..., gt=0, description="Unit thickness in metres")
        color: str = Field("#888888", description="Hex colour for fill (e.g. #E6A817)")

    class _GeologicalModelParams(BaseModel):
        """Input schema for geox_geological_model_generate.

        All parameters describe a 2D geological cross-section.
        Zero external data fetching — pure deterministic computation.
        """

        grid_width_m: float = Field(2000.0, gt=0, description="Cross-section width in metres")
        grid_depth_m: float = Field(1000.0, gt=0, description="Cross-section depth in metres")
        dip_angle_deg: float = Field(0.0, description="Structural dip in degrees (0 = horizontal)")
        fault_throw_m: float = Field(
            0.0, description="Vertical fault displacement in metres. Positive = normal, negative = reverse. 0 = no fault."
        )
        fault_x_position_m: float | None = Field(
            None,
            ge=0,
            description="X-coordinate of fault plane intersection with surface. Defaults to midpoint when fault_throw_m != 0.",
        )
        strata: list[_StrataUnit] = Field(
            default_factory=lambda: [
                _StrataUnit(name="Layer A", thickness_m=200, color="#d4a574"),
                _StrataUnit(name="Layer B", thickness_m=150, color="#b8c9a0"),
                _StrataUnit(name="Layer C", thickness_m=100, color="#8ab8d4"),
                _StrataUnit(name="Layer D", thickness_m=80, color="#c9a87c"),
                _StrataUnit(name="Layer E", thickness_m=60, color="#a0b8c9"),
                _StrataUnit(name="Layer F", thickness_m=40, color="#74695e"),
                _StrataUnit(name="Basement", thickness_m=20, color="#4a4a4a"),
            ],
            description="Ordered list of stratigraphic units from top to bottom",
        )
        title: str = Field("Geological Cross-Section", description="Plot title")

    # ZEN-CONSOLIDATED — @mcp.tool(
        # ZEN-CONSOLIDATED — name="geox_geological_model_generate",
        # ZEN-CONSOLIDATED — annotations=_geox_annotations("geox_geological_model_generate"),
    # ZEN-CONSOLIDATED — )
    async def _geological_model_generate(
        params: _GeologicalModelParams,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> str:
        """Generate a deterministic 2D geological cross-section using matplotlib.

        Computes layer geometry from structural parameters (dip, fault throw, strata
        thicknesses) using numpy trigonometry. Renders via matplotlib with Agg backend.
        NO diffusion models, NO API calls, NO hallucination — pure physics + geometry.

        Args:
            params: Structured geological model parameters (see _GeologicalModelParams).
            session_id: Governed session (SEAL-* or act_v1.*) — required by P0-2 authority gate.
            actor_id: Claiming actor (F11 non-repudiation).
            trace_id: Optional correlation id for audit chain.

        Returns:
            Absolute local path to the generated PNG file (/tmp/geox/geox_model_<uuid>.png).
        """
        # Identity consumed by geox_middleware authority gate; keep referenced for audit.
        _ = (session_id, actor_id, trace_id)
        import os
        import uuid
        from datetime import UTC, datetime

        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np

        # ── Extract parameters ───────────────────────────────────────────
        gw = params.grid_width_m
        gd = params.grid_depth_m
        dip_rad = params.dip_angle_deg * np.pi / 180.0
        throw = params.fault_throw_m
        depth_scale = gd / sum(u.thickness_m for u in params.strata)

        # Fault x position: default to centre when fault present
        fx = params.fault_x_position_m
        if fx is None and throw != 0:
            fx = gw / 2

        # ── Render figure ────────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(12, 6))
        y_offset = 0.0

        for unit in params.strata:
            thick = unit.thickness_m * depth_scale
            # Left edge at surface
            xl_top = dip_rad * y_offset
            xl_bot = dip_rad * (y_offset + thick)
            # Right edge at surface
            xr_top = gw + dip_rad * y_offset
            xr_bot = gw + dip_rad * (y_offset + thick)

            if fx is not None and throw != 0:
                tp = throw * depth_scale
                # Left polygon (unfaulted)
                ax.fill(
                    [xl_top, fx, fx, xl_bot],
                    [y_offset, y_offset, y_offset + thick, y_offset + thick],
                    color=unit.color,
                    edgecolor="black",
                    linewidth=0.5,
                )
                # Right polygon (offset by throw)
                ax.fill(
                    [fx, xr_top, xr_bot, fx],
                    [y_offset + tp, y_offset + tp, y_offset + thick + tp, y_offset + thick + tp],
                    color=unit.color,
                    edgecolor="black",
                    linewidth=0.5,
                )
                # Label both sides
                ax.text(
                    fx / 2,
                    y_offset + thick / 2,
                    unit.name,
                    fontsize=8,
                    ha="center",
                    va="center",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7),
                )
                ax.text(
                    (gw + fx) / 2,
                    y_offset + thick / 2 + tp / 2,
                    unit.name,
                    fontsize=8,
                    ha="center",
                    va="center",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7),
                )
            else:
                polygon = mpatches.Polygon(
                    [(xl_top, y_offset), (xr_top, y_offset), (xr_bot, y_offset + thick), (xl_bot, y_offset + thick)],
                    closed=True,
                    color=unit.color,
                    edgecolor="black",
                    linewidth=0.5,
                )
                ax.add_patch(polygon)
                ax.text(
                    gw * 0.25,
                    y_offset + thick / 2,
                    unit.name,
                    fontsize=8,
                    ha="center",
                    va="center",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7),
                )

            y_offset += thick

        # ── Fault annotation ─────────────────────────────────────────────
        if fx is not None and throw != 0:
            tp = throw * depth_scale
            ax.axvline(x=fx, color="red", linewidth=2, linestyle="--", label=f"Fault (throw={throw:.0f}m)")
            ax.annotate(
                "",
                xy=(fx + gw * 0.02, y_offset - tp),
                xytext=(fx + gw * 0.02, y_offset),
                arrowprops=dict(arrowstyle="<->", color="red", lw=1.5),
            )
            ax.text(fx + gw * 0.025, y_offset - tp / 2, f"Throw\n{throw:.0f}m", fontsize=7, color="red", va="center")

        # ── Dip annotation ───────────────────────────────────────────────
        if params.dip_angle_deg != 0:
            ax.annotate(
                "",
                xy=(gw * 0.1, 0),
                xytext=(gw * 0.1 + dip_rad * 200 * depth_scale, -dip_rad * 200 * depth_scale),
                arrowprops=dict(arrowstyle="->", color="blue", lw=1.5),
            )
            ax.text(
                gw * 0.1 + dip_rad * 100 * depth_scale,
                -dip_rad * 100 * depth_scale - 30,
                f"Dip {params.dip_angle_deg}°",
                fontsize=8,
                color="blue",
                ha="center",
            )

        # ── Axes ─────────────────────────────────────────────────────────
        ax.set_xlim(0, gw)
        ax.set_ylim(y_offset + 50, -50)
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Depth (m)")
        ax.set_title(params.title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.text(
            0.98,
            0.02,
            f"GEOX deterministic render | {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
            transform=ax.transAxes,
            fontsize=6,
            color="gray",
            ha="right",
            va="bottom",
            style="italic",
        )
        plt.tight_layout()

        # ── Save ─────────────────────────────────────────────────────────
        os.makedirs("/tmp/geox/", exist_ok=True)
        out_path = f"/tmp/geox/geox_model_{uuid.uuid4().hex[:8]}.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # F2: return only the absolute path — Hermes handles display
        return out_path

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2 — LEM Tools (E1-E5) — LEM Agentic Substrate
    # Forged 2026-07-29 by OpenCode under Arif F13 directive.
    # GemPy 3D + H3 Spatial Index + LanceDB + STAC + DDE/Macrostrat
    # ═══════════════════════════════════════════════════════════════════

    # E1 — GemPy Implicit 3D Structural Modeling
    try:
        from geox_mcp.tools.gempy_implicit_3d import geox_gempy_implicit_3d

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_gempy_implicit_3d",
            # ZEN-CONSOLIDATED — annotations=_geox_annotations("geox_gempy_implicit_3d"),
        # ZEN-CONSOLIDATED — )
        async def _gempy_implicit_3d(
            surface_points: list | str | None = None,
            orientations: list | str | None = None,
            grid_resolution: tuple | list | str | None = None,
            model_extent: tuple | list | str | None = None,
            compute_uncertainty: bool = True,
            uncertainty_realizations: int = 10,
            fault_groups: list | str | None = None,
            output_format: str = "json",
            session_id: str | None = None,
            actor_id: str | None = None,
            trace_id: str | None = None,
        ):
            """Implicit 3D structural modeling with GemPy.

            Builds a 3D geological volume from surface contact points and
            orientation measurements using universal cokriging scalar
            potential field interpolation. Returns lithology block,
            scalar field, section images, and uncertainty estimates.

            Use when: '3D model', 'GemPy', 'implicit modeling',
            'structural model', 'geological volume'.
            """
            return await geox_gempy_implicit_3d(
                surface_points=surface_points,
                orientations=orientations,
                grid_resolution=grid_resolution,
                model_extent=model_extent,
                compute_uncertainty=compute_uncertainty,
                uncertainty_realizations=uncertainty_realizations,
                fault_groups=fault_groups,
                output_format=output_format,
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )

        logger.info("LEM E1: geox_gempy_implicit_3d registered")
    except Exception as e:
        logger.warning("LEM E1: geox_gempy_implicit_3d skipped: %s", e)

    # E2 — H3 Hexagonal Spatial Index
    try:
        from geox_mcp.tools.h3_spatial_index import geox_h3_spatial_index

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_h3_spatial_index",
            # ZEN-CONSOLIDATED — annotations=_geox_annotations("geox_h3_spatial_index"),
        # ZEN-CONSOLIDATED — )
        async def _h3_spatial_index(
            mode: str = "latlng_to_cell",
            lat: float | None = None,
            lng: float | None = None,
            resolution: int = 7,
            h3_cell: str | None = None,
            points: list | str | None = None,
            k: int = 1,
            polygon: list | str | None = None,
            session_id: str | None = None,
            actor_id: str | None = None,
            trace_id: str | None = None,
        ):
            """H3 hexagonal spatial indexing for Earth intelligence.

            Convert lat/lng to H3 cells, aggregate points, query
            k-ring neighbours, fill polygons. Uniform-adjacency hex
            grid for O(1) spatial retrieval.

            Use when: 'H3 index', 'hexagon', 'spatial index',
            'latlng to h3', 'cell aggregate'.
            """
            return await geox_h3_spatial_index(
                mode=mode,
                lat=lat,
                lng=lng,
                resolution=resolution,
                h3_cell=h3_cell,
                points=points,
                k=k,
                polygon=polygon,
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )

        logger.info("LEM E2: geox_h3_spatial_index registered")
    except Exception as e:
        logger.warning("LEM E2: geox_h3_spatial_index skipped: %s", e)

    # E3 — LanceDB Embedded Vector Store
    try:
        from geox_mcp.tools.lancedb_embed_store import geox_lancedb_embed_store

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_lancedb_embed_store",
            # ZEN-CONSOLIDATED — annotations=_geox_annotations("geox_lancedb_embed_store"),
        # ZEN-CONSOLIDATED — )
        async def _lancedb_embed_store(
            mode: str = "search",
            table_name: str = "geo_embeddings",
            embeddings: list | str | None = None,
            metadata: list | str | None = None,
            k: int = 10,
            refine_factor: int | None = None,
            filter_expr: str | None = None,
            h3_cell: str | None = None,
            h3_radius: int = 1,
            create_if_missing: bool = True,
            drop_table: bool = False,
            session_id: str | None = None,
            actor_id: str | None = None,
            trace_id: str | None = None,
        ):
            """LanceDB embedded vector store for earth embeddings.

            Store and search AlphaEarth (64-dim), Clay (768-dim),
            or custom embeddings with H3 spatial cross-reference.
            PQ compression + refine_factor. Serverless, embedded.

            Use when: 'search embeddings', 'vector store', 'LanceDB',
            'store earth embeddings', 'similarity search'.
            """
            return await geox_lancedb_embed_store(
                mode=mode,
                table_name=table_name,
                embeddings=embeddings,
                metadata=metadata,
                k=k,
                refine_factor=refine_factor,
                filter_expr=filter_expr,
                h3_cell=h3_cell,
                h3_radius=h3_radius,
                create_if_missing=create_if_missing,
                drop_table=drop_table,
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )

        logger.info("LEM E3: geox_lancedb_embed_store registered")
    except Exception as e:
        logger.warning("LEM E3: geox_lancedb_embed_store skipped: %s", e)

    # E4 — STAC Catalog Discovery
    try:
        from geox_mcp.tools.stac_discover import geox_stac_discover

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_stac_discover",
            # ZEN-CONSOLIDATED — annotations=_geox_annotations("geox_stac_discover"),
        # ZEN-CONSOLIDATED — )
        async def _stac_discover(
            mode: str = "search",
            catalog: str = "earthsearch",
            bbox: list | str | None = None,
            datetime_range: str | None = None,
            collections: list | str | None = None,
            max_items: int = 20,
            item_id: str | None = None,
            collection_id: str | None = None,
            query_bands: list | str | None = None,
            limit: int = 1,
            session_id: str | None = None,
            actor_id: str | None = None,
            trace_id: str | None = None,
        ):
            """STAC Catalog query for cloud-native geospatial assets.

            Discover COG, GeoParquet, Zarr datasets by spatial,
            temporal, and band filters across federated STAC catalogs
            (Earth Search, Planetary Computer, Copernicus, USGS).

            Use when: 'STAC', 'satellite imagery', 'COG', 'GeoParquet',
            'cloud-native geospatial', 'discover data'.
            """
            return await geox_stac_discover(
                mode=mode,
                catalog=catalog,
                bbox=bbox,
                datetime_range=datetime_range,
                collections=collections,
                max_items=max_items,
                item_id=item_id,
                collection_id=collection_id,
                query_bands=query_bands,
                limit=limit,
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )

        logger.info("LEM E4: geox_stac_discover registered")
    except Exception as e:
        logger.warning("LEM E4: geox_stac_discover skipped: %s", e)

    # E5 — DDE/Macrostrat Neuro-Symbolic Reasoner
    try:
        from geox_mcp.tools.dde_reason import geox_dde_reason

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_dde_reason",
            # ZEN-CONSOLIDATED — annotations=_geox_annotations("geox_dde_reason"),
        # ZEN-CONSOLIDATED — )
        async def _dde_reason(
            mode: str = "query_stratigraphy",
            bbox: list | str | None = None,
            lat: float | None = None,
            lng: float | None = None,
            formation: str | None = None,
            known_units: list | str | None = None,
            ontology_term: str | None = None,
            section_params: dict | str | None = None,
            delta_age_ma: float | None = None,
            limit: int = 10,
            session_id: str | None = None,
            actor_id: str | None = None,
            trace_id: str | None = None,
        ):
            """DDE Ontology + Macrostrat neuro-symbolic reasoning.

            Query the Deep-time Digital Earth knowledge graph
            (62,610 physical rules) for stratigraphic reasoning,
            infer missing geology, validate cross-sections against
            physical laws, and explore tectonic context.

            Use when: 'stratigraphy', 'DDE', 'Macrostrat',
            'infer unit', 'age constraints', 'tectonic context'.
            """
            return await geox_dde_reason(
                mode=mode,
                bbox=bbox,
                lat=lat,
                lng=lng,
                formation=formation,
                known_units=known_units,
                ontology_term=ontology_term,
                section_params=section_params,
                delta_age_ma=delta_age_ma,
                limit=limit,
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )

        logger.info("LEM E5: geox_dde_reason registered")
    except Exception as e:
        logger.warning("LEM E5: geox_dde_reason skipped: %s", e)

    # ── EGS Temporal tools (geox_temporal_decline/rrr/basin_lifecycle/cadence) ──
    try:
        from geox.egs.tools.temporal import (
            temporal_basin_lifecycle,
            temporal_cadence,
            temporal_decline,
            temporal_rrr,
        )

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_temporal_decline",
            # ZEN-CONSOLIDATED — annotations=_geox_annotations("geox_temporal_decline"),
        # ZEN-CONSOLIDATED — )
        async def _temporal_decline(
            production_data: list[dict[str, Any]],
            forecast_years: int = 5,
            threshold_bpd: float = 250000.0,
            session_id: str | None = None,
            actor_id: str | None = None,
            trace_id: str | None = None,
        ) -> dict[str, Any]:
            """Fit exponential decline curve to production history and forecast future rates."""
            args = _safe_forward(
                temporal_decline,
                {
                    "production_data": production_data,
                    "forecast_years": forecast_years,
                    "threshold_bpd": threshold_bpd,
                },
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
            return await temporal_decline(**args)

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_temporal_rrr",
            # ZEN-CONSOLIDATED — annotations=_geox_annotations("geox_temporal_rrr"),
        # ZEN-CONSOLIDATED — )
        async def _temporal_rrr(
            reserves_start: float,
            additions: float,
            production: float,
            session_id: str | None = None,
            actor_id: str | None = None,
            trace_id: str | None = None,
        ) -> dict[str, Any]:
            """Compute Reserve Replacement Ratio (RRR = additions / production)."""
            args = _safe_forward(
                temporal_rrr,
                {
                    "reserves_start": reserves_start,
                    "additions": additions,
                    "production": production,
                },
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
            return await temporal_rrr(**args)

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_temporal_basin_lifecycle",
            # ZEN-CONSOLIDATED — annotations=_geox_annotations("geox_temporal_basin_lifecycle"),
        # ZEN-CONSOLIDATED — )
        async def _temporal_basin_lifecycle(
            basin_name: str,
            peak_production: float,
            current_production: float,
            discovery_year: int,
            peak_year: int,
            session_id: str | None = None,
            actor_id: str | None = None,
            trace_id: str | None = None,
        ) -> dict[str, Any]:
            """Classify basin lifecycle stage: growth, plateau, decline, or mature."""
            args = _safe_forward(
                temporal_basin_lifecycle,
                {
                    "basin_name": basin_name,
                    "peak_production": peak_production,
                    "current_production": current_production,
                    "discovery_year": discovery_year,
                    "peak_year": peak_year,
                },
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
            return await temporal_basin_lifecycle(**args)

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_temporal_cadence",
            # ZEN-CONSOLIDATED — annotations=_geox_annotations("geox_temporal_cadence"),
        # ZEN-CONSOLIDATED — )
        async def _temporal_cadence(
            blocks_offered: int,
            blocks_awarded: int,
            years_span: int,
            average_cycle_time_years: float,
            session_id: str | None = None,
            actor_id: str | None = None,
            trace_id: str | None = None,
        ) -> dict[str, Any]:
            """Analyse exploration licensing cadence: award rate, pipeline lag, and production impact."""
            args = _safe_forward(
                temporal_cadence,
                {
                    "blocks_offered": blocks_offered,
                    "blocks_awarded": blocks_awarded,
                    "years_span": years_span,
                    "average_cycle_time_years": average_cycle_time_years,
                },
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
            return await temporal_cadence(**args)

        logger.info("TEMPORAL: 4 geox_temporal_* tools registered")
    except Exception as e:
        logger.warning("TEMPORAL: geox_temporal_* tools skipped: %s", e)

    # ── Additional core tools (source_rock, avo, diagenesis) ──
    try:
        from geox_core.source_rock.parameters import (
            classify_toc, classify_kerogen, classify_maturity, estimate_toc_deltalogr,
        )

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_source_rock",
            # ZEN-CONSOLIDATED — description="Source rock evaluation: TOC classification (Peters-Cassa 1994), kerogen typing (van Krevelen), maturity windows, ΔlogR TOC estimation. Modes: toc, kerogen, maturity, delalogr, full.",
            # ZEN-CONSOLIDATED — annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
        # ZEN-CONSOLIDATED — )
        async def _source_rock(
            mode: str = "full",
            toc_wt_pct: float | None = None,
            hydrogen_index: float | None = None,
            oxygen_index: float | None = None,
            tmax_c: float | None = None,
            kerogen_type: str = "II",
            depth_m: float | None = None,
            resistivity_ohm_m: float | None = None,
            sonic_us_ft: float | None = None,
            density_gcc: float | None = None,
            lom: float = 7.0,
            baseline_resistivity: float = 2.0,
            baseline_sonic: float = 90.0,
        ) -> dict[str, Any]:
            results: dict[str, Any] = {"mode": mode}
            try:
                if mode in ("toc", "full") and toc_wt_pct is not None:
                    results["toc"] = classify_toc(toc_wt_pct)
                if mode in ("kerogen", "full") and hydrogen_index is not None:
                    results["kerogen"] = classify_kerogen(hydrogen_index, oxygen_index, tmax_c)
                if mode in ("maturity", "full") and tmax_c is not None:
                    results["maturity"] = classify_maturity(tmax_c, kerogen_type)
                if mode in ("deltalogr", "full") and depth_m is not None and resistivity_ohm_m is not None:
                    results["deltalogr"] = estimate_toc_deltalogr(
                        depth_m, resistivity_ohm_m, sonic_us_ft, density_gcc,
                        lom, baseline_resistivity, baseline_sonic,
                    )
                if len(results) == 1:
                    results["error"] = f"mode={mode} requires specific parameters (see description)"
                return results
            except Exception as e:
                return {"error": str(e), "mode": mode}

        logger.info("CORE: geox_source_rock registered")
    except Exception as e:
        logger.warning("CORE: geox_source_rock skipped: %s", e)

    try:
        from geox_core.avo.avo_forward import zoeppritz_rpp, shuey_avo, lmr_decompose
        from geox_core.avo.castagna import castagna_mudrock_vp_to_vs, castagna_mudrock_fallback

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_avo_forward",
            # ZEN-CONSOLIDATED — description="AVO forward modeling: Zoeppritz exact Rpp, Shuey 2-term, Lambda-Mu-Rho (Goodway 1997), Castagna mudrock. Modes: zoeppritz, shuey, lmr, castagna, full.",
            # ZEN-CONSOLIDATED — annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
        # ZEN-CONSOLIDATED — )
        async def _avo_forward(
            mode: str = "zoeppritz",
            vp1: float = 3.0,
            vs1: float = 1.5,
            rho1: float = 2.3,
            vp2: float = 2.5,
            vs2: float = 1.2,
            rho2: float = 2.1,
            theta_deg: list[float] | None = None,
            theta_max: float = 30.0,
            vp: float = 3.0,
            vs: float = 1.5,
            rho: float = 2.3,
            fluid_zone: str = "brine",
            unit: str = "m/s",
        ) -> dict[str, Any]:
            import numpy as np
            results: dict[str, Any] = {"mode": mode}
            try:
                thetas = np.array(theta_deg if theta_deg else [0, 5, 10, 15, 20, 25, 30])
                if mode in ("zoeppritz", "full"):
                    rpp = zoeppritz_rpp(vp1, vs1, rho1, vp2, vs2, rho2, thetas)
                    results["zoeppritz"] = {"theta_deg": thetas.tolist(), "rpp": rpp.tolist()}
                    results["reflectivity"] = rpp.tolist()
                if mode in ("shuey", "full"):
                    sh = shuey_avo(vp1, vs1, rho1, vp2, vs2, rho2, theta_max)
                    sd = sh.to_dict() if hasattr(sh, 'to_dict') else {}
                    results["shuey"] = {"intercept_R0": sd.get("intercept_R0"), "gradient_G": sd.get("gradient_G"), "avo_class": sd.get("avo_class")}
                    if sd.get("intercept_R0") is not None:
                        results["amplitude"] = [sd.get("intercept_R0")]
                if mode in ("lmr", "full"):
                    vpp = np.array([vp]) if isinstance(vp, (int, float)) else np.array(vp)
                    vss = np.array([vs]) if isinstance(vs, (int, float)) else np.array(vs)
                    rr = np.array([rho]) if isinstance(rho, (int, float)) else np.array(rho)
                    lmr = lmr_decompose(vpp, vss, rr)
                    results["lmr"] = {"lambda_rho": [float(x) for x in lmr.lambda_rho], "mu_rho": [float(x) for x in lmr.mu_rho], "fluid_indicator": getattr(lmr, 'fluid_indicator', None)}
                if mode in ("castagna", "full"):
                    vs_est = castagna_mudrock_vp_to_vs(vp, unit=unit)
                    fallback = castagna_mudrock_fallback(vp, fluid_zone=fluid_zone, unit=unit)
                    results["castagna"] = {"vp_to_vs": float(vs_est) if not hasattr(vs_est, '__len__') else vs_est.tolist(), "fallback": fallback}
                if len(results) == 1:
                    results["error"] = f"mode={mode} not recognized"
                return results
            except Exception as e:
                return {"error": str(e), "mode": mode}

        logger.info("CORE: geox_avo_forward registered")
    except Exception as e:
        logger.warning("CORE: geox_avo_forward skipped: %s", e)

    try:
        from geox_core.diagenesis.compaction import (
            athy_porosity, sclater_christie_porosity, compaction_correction,
        )

        # ZEN-CONSOLIDATED — @mcp.tool(
            # ZEN-CONSOLIDATED — name="geox_diagenesis",
            # ZEN-CONSOLIDATED — description="Diagenesis analysis: mechanical compaction models (Athy 1930, Sclater & Christie 1980), compaction correction, overpressure detection. Modes: compaction, full.",
            # ZEN-CONSOLIDATED — annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
        # ZEN-CONSOLIDATED — )
        async def _diagenesis(
            mode: str = "compaction",
            depth_m: float = 2000.0,
            measured_porosity: float | None = None,
            lithology: str = "sandstone",
            surface_porosity: float = 0.45,
            compaction_coeff: float = 0.0004,
        ) -> dict[str, Any]:
            results: dict[str, Any] = {"mode": mode, "depth_m": depth_m, "lithology": lithology}
            try:
                athy = athy_porosity(depth_m, surface_porosity, compaction_coeff)
                sc = sclater_christie_porosity(lithology, depth_m)
                results["athy_porosity"] = round(athy, 4)
                results["sclater_christie_porosity"] = round(sc, 4)
                if measured_porosity is not None:
                    results["correction"] = compaction_correction(measured_porosity, depth_m, lithology)
                return results
            except Exception as e:
                return {"error": str(e), "mode": mode}

        logger.info("CORE: geox_diagenesis registered")
    except Exception as e:
        logger.warning("CORE: geox_diagenesis skipped: %s", e)

    # ═══════════════════════════════════════════════════════════════════
    try:
        from geox_mcp.tools_manifest import CANONICAL_TOOLS as _manifest

        _enriched = 0
        _skipped = 0
        # Access tools via FastMCP's local provider component registry
        _components = getattr(getattr(mcp, "_local_provider", None), "_components", {})
        for tool_name, canonical in _manifest.items():
            # FastMCP stores tools as "tool:<name>@" keys in _components
            _key = f"tool:{tool_name}@"
            if _key in _components:
                existing = getattr(_components[_key], "description", "") or ""
                if "Use when" not in existing:
                    _components[_key].description = f"{canonical.description} Use when: {canonical.use_when}"
                    _enriched += 1
                else:
                    _skipped += 1
        logger.info(
            f"MANIFEST_ENRICH: enriched {_enriched}/{len(_manifest)} canonical tools, skipped {_skipped} (already enriched)"
        )
    except Exception as e:
        logger.warning(f"MANIFEST_ENRICH: skipped — {e}")

    # ═══════════════════════════════════════════════════════════════════════════════
    # ZEN CONSOLIDATION 2026-08-10 — Merged mode-dispatch tools + backwards-compat shims
    # Old @mcp.tool removed; implementations stay as plain async functions.
    # ═══════════════════════════════════════════════════════════════════════════════

    # ── GROUP 1: geox_temporal — absorbs temporal_decline/rrr/basin_lifecycle/cadence ──
    @mcp.tool(
        name="geox_temporal",
        description="Temporal analytics for petroleum basins. Modes: decline (decline curve analysis), rrr (reserve replacement ratio), basin_lifecycle (classify lifecycle stage), cadence (licensing cadence analysis).",
        annotations=_geox_annotations("geox_temporal"),
    )
    async def _temporal_unified(
        mode: str = "decline",
        production_data: list[dict[str, Any]] | None = None,
        forecast_years: int = 5,
        threshold_bpd: float = 250000.0,
        reserves_start: float | None = None,
        additions: float | None = None,
        production: float | None = None,
        basin_name: str = "",
        peak_production: float | None = None,
        current_production: float | None = None,
        discovery_year: int | None = None,
        peak_year: int | None = None,
        blocks_offered: int | None = None,
        blocks_awarded: int | None = None,
        years_span: int | None = None,
        average_cycle_time_years: float | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Temporal analytics for petroleum basins.

        Modes:
          decline         — Fit exponential decline curve to production history
          rrr             — Compute Reserve Replacement Ratio (additions / production)
          basin_lifecycle — Classify basin lifecycle stage: growth, plateau, decline, mature
          cadence         — Analyse exploration licensing cadence: award rate, pipeline lag
        """
        if mode == "decline":
            return await _temporal_decline(
                production_data=production_data or [],
                forecast_years=forecast_years,
                threshold_bpd=threshold_bpd,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode == "rrr":
            return await _temporal_rrr(
                reserves_start=reserves_start or 0.0,
                additions=additions or 0.0,
                production=production or 1.0,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode == "basin_lifecycle":
            return await _temporal_basin_lifecycle(
                basin_name=basin_name,
                peak_production=peak_production or 0.0,
                current_production=current_production or 0.0,
                discovery_year=discovery_year or 1970,
                peak_year=peak_year or 2000,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode == "cadence":
            return await _temporal_cadence(
                blocks_offered=blocks_offered or 0,
                blocks_awarded=blocks_awarded or 0,
                years_span=years_span or 1,
                average_cycle_time_years=average_cycle_time_years or 1.0,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        else:
            return {"error": f"Unknown mode: {mode}. Valid: decline, rrr, basin_lifecycle, cadence"}

    # GROUP 1 shims — backwards-compat: old names call new tool with right mode
    @mcp.tool(name="geox_temporal_decline", annotations=_geox_annotations("geox_temporal_decline"))
    async def _shim_temporal_decline(production_data, forecast_years=5, threshold_bpd=250000.0, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_temporal(mode=decline)]"""
        return await _temporal_unified(mode="decline", production_data=production_data, forecast_years=forecast_years, threshold_bpd=threshold_bpd, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_temporal_rrr", annotations=_geox_annotations("geox_temporal_rrr"))
    async def _shim_temporal_rrr(reserves_start, additions, production, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_temporal(mode=rrr)]"""
        return await _temporal_unified(mode="rrr", reserves_start=reserves_start, additions=additions, production=production, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_temporal_basin_lifecycle", annotations=_geox_annotations("geox_temporal_basin_lifecycle"))
    async def _shim_temporal_basin_lifecycle(basin_name, peak_production, current_production, discovery_year, peak_year, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_temporal(mode=basin_lifecycle)]"""
        return await _temporal_unified(mode="basin_lifecycle", basin_name=basin_name, peak_production=peak_production, current_production=current_production, discovery_year=discovery_year, peak_year=peak_year, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_temporal_cadence", annotations=_geox_annotations("geox_temporal_cadence"))
    async def _shim_temporal_cadence(blocks_offered, blocks_awarded, years_span, average_cycle_time_years, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_temporal(mode=cadence)]"""
        return await _temporal_unified(mode="cadence", blocks_offered=blocks_offered, blocks_awarded=blocks_awarded, years_span=years_span, average_cycle_time_years=average_cycle_time_years, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    # ── GROUP 2: geox_map — absorbs map_layers_list/scene_plan/render_preview ──
    @mcp.tool(
        name="geox_map",
        description="Geological map pipeline. Modes: layers_list (list available layers for bbox), scene_plan (create deterministic visual recipe), render_preview (render static map preview).",
        annotations=_geox_annotations("geox_map"),
    )
    async def _map_unified(
        mode: str = "layers_list",
        bbox: list[float] | None = None,
        theme: str | None = None,
        include_unavailable: bool = False,
        layer_ids: list[str] | None = None,
        map_purpose: str = "context",
        style_profile: str = "geox_regional_clean_v1",
        crs: str = "EPSG:4326",
        scene_id: str | None = None,
        width_px: int = 1024,
        height_px: int = 768,
        format: str = "image/png",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Geological map pipeline.

        Modes:
          layers_list   — List available GEOX map layers for a bounding box
          scene_plan    — Create a deterministic visual recipe for a geological map scene
          render_preview — Render a static map preview from a scene plan or bbox
        """
        # 2026-09-06: zen-consolidation commented out _map_layers_list /
        # _map_scene_plan / _map_render_preview but this unified wrapper still
        # called them → NameError. Call earth_map impls directly.
        if mode == "layers_list":
            if bbox is None:
                return {"ok": False, "error": "layers_list mode requires bbox parameter"}
            from geox_mcp.tools.earth_map import geox_map_layers_list as _impl

            return await _impl(bbox=bbox, theme=theme, include_unavailable=include_unavailable)
        elif mode == "scene_plan":
            if bbox is None:
                return {"ok": False, "error": "scene_plan mode requires bbox parameter"}
            from geox_mcp.tools.earth_map import geox_map_scene_plan as _impl

            return await _impl(
                bbox=bbox,
                layer_ids=layer_ids,
                theme=theme,
                map_purpose=map_purpose,
                style_profile=style_profile,
                crs=crs,
            )
        elif mode == "render_preview":
            from geox_mcp.tools.earth_map import geox_map_render_preview as _impl

            return await _impl(
                scene_id=scene_id,
                bbox=bbox,
                layer_ids=layer_ids,
                theme=theme,
                width_px=width_px,
                height_px=height_px,
                style_profile=style_profile,
                format=format,
            )
        else:
            return {"ok": False, "error": f"Unknown mode: {mode}. Valid: layers_list, scene_plan, render_preview"}

    @mcp.tool(name="geox_map_layers_list", annotations=_geox_annotations("geox_map_layers_list"))
    async def _shim_map_layers_list(bbox, theme=None, include_unavailable=False, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_map(mode=layers_list)]"""
        return await _map_unified(mode="layers_list", bbox=bbox, theme=theme, include_unavailable=include_unavailable, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_map_scene_plan", annotations=_geox_annotations("geox_map_scene_plan"))
    async def _shim_map_scene_plan(bbox, layer_ids=None, theme=None, map_purpose="context", style_profile="geox_regional_clean_v1", crs="EPSG:4326", session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_map(mode=scene_plan)]"""
        return await _map_unified(mode="scene_plan", bbox=bbox, layer_ids=layer_ids, theme=theme, map_purpose=map_purpose, style_profile=style_profile, crs=crs, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_map_render_preview", annotations=_geox_annotations("geox_map_render_preview"))
    async def _shim_map_render_preview(scene_id=None, bbox=None, layer_ids=None, theme=None, width_px=1024, height_px=768, style_profile="geox_regional_clean_v1", format="image/png", session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_map(mode=render_preview)]"""
        return await _map_unified(mode="render_preview", scene_id=scene_id, bbox=bbox, layer_ids=layer_ids, theme=theme, width_px=width_px, height_px=height_px, style_profile=style_profile, format=format, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    # ── GROUP 3: geox_source — absorbs source_rock/diagenesis ──
    @mcp.tool(
        name="geox_source",
        description="Source rock and diagenesis evaluation. Modes: source_rock (TOC, kerogen, maturity, ΔlogR), diagenesis (compaction models: Athy, Sclater & Christie).",
        annotations=_geox_annotations("geox_source"),
    )
    async def _source_unified(
        mode: str = "source_rock",
        # source_rock params
        toc_wt_pct: float | None = None,
        hydrogen_index: float | None = None,
        oxygen_index: float | None = None,
        tmax_c: float | None = None,
        kerogen_type: str = "II",
        depth_m: float | None = None,
        resistivity_ohm_m: float | None = None,
        sonic_us_ft: float | None = None,
        density_gcc: float | None = None,
        lom: float = 7.0,
        baseline_resistivity: float = 2.0,
        baseline_sonic: float = 90.0,
        # diagenesis params
        measured_porosity: float | None = None,
        lithology: str = "sandstone",
        surface_porosity: float = 0.45,
        compaction_coeff: float = 0.0004,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Source rock and diagenesis evaluation.

        Modes:
          source_rock — TOC classification, kerogen typing, maturity windows, ΔlogR
          diagenesis  — Mechanical compaction models (Athy 1930, Sclater & Christie 1980)
        """
        if mode == "source_rock":
            return await _source_rock(
                mode="full", toc_wt_pct=toc_wt_pct, hydrogen_index=hydrogen_index,
                oxygen_index=oxygen_index, tmax_c=tmax_c, kerogen_type=kerogen_type,
                depth_m=depth_m, resistivity_ohm_m=resistivity_ohm_m,
                sonic_us_ft=sonic_us_ft, density_gcc=density_gcc, lom=lom,
                baseline_resistivity=baseline_resistivity, baseline_sonic=baseline_sonic,
            )
        elif mode == "diagenesis":
            return await _diagenesis(
                mode="compaction", depth_m=depth_m or 2000.0,
                measured_porosity=measured_porosity, lithology=lithology,
                surface_porosity=surface_porosity, compaction_coeff=compaction_coeff,
            )
        else:
            return {"error": f"Unknown mode: {mode}. Valid: source_rock, diagenesis"}

    @mcp.tool(name="geox_source_rock", annotations=_geox_annotations("geox_source_rock"))
    async def _shim_source_rock(mode="full", toc_wt_pct=None, hydrogen_index=None, oxygen_index=None, tmax_c=None, kerogen_type="II", depth_m=None, resistivity_ohm_m=None, sonic_us_ft=None, density_gcc=None, lom=7.0, baseline_resistivity=2.0, baseline_sonic=90.0):
        """[SHIM→geox_source(mode=source_rock)]"""
        return await _source_unified(mode="source_rock", toc_wt_pct=toc_wt_pct, hydrogen_index=hydrogen_index, oxygen_index=oxygen_index, tmax_c=tmax_c, kerogen_type=kerogen_type, depth_m=depth_m, resistivity_ohm_m=resistivity_ohm_m, sonic_us_ft=sonic_us_ft, density_gcc=density_gcc, lom=lom, baseline_resistivity=baseline_resistivity, baseline_sonic=baseline_sonic)

    @mcp.tool(name="geox_diagenesis", annotations=_geox_annotations("geox_diagenesis"))
    async def _shim_diagenesis(mode="compaction", depth_m=2000.0, measured_porosity=None, lithology="sandstone", surface_porosity=0.45, compaction_coeff=0.0004):
        """[SHIM→geox_source(mode=diagenesis)]"""
        return await _source_unified(mode="diagenesis", depth_m=depth_m, measured_porosity=measured_porosity, lithology=lithology, surface_porosity=surface_porosity, compaction_coeff=compaction_coeff)

    # ── GROUP 4: geox_spatial — absorbs h3_spatial_index/lancedb_embed_store/stac_discover ──
    @mcp.tool(
        name="geox_spatial",
        description="Spatial indexing and discovery. Modes: h3_index (H3 hexagonal spatial indexing), lancedb_store (LanceDB embedded vector store for earth embeddings), stac_discover (STAC catalog query for cloud-native geospatial assets).",
        annotations=_geox_annotations("geox_spatial"),
    )
    async def _spatial_unified(
        mode: str = "h3_index",
        # h3 params
        lat: float | None = None,
        lng: float | None = None,
        resolution: int = 7,
        h3_cell: str | None = None,
        points: list | str | None = None,
        k: int = 1,
        polygon: list | str | None = None,
        # lancedb params
        table_name: str = "geo_embeddings",
        embeddings: list | str | None = None,
        metadata: list | str | None = None,
        refine_factor: int | None = None,
        filter_expr: str | None = None,
        h3_radius: int = 1,
        create_if_missing: bool = True,
        drop_table: bool = False,
        # stac params
        catalog: str = "earthsearch",
        bbox: list | str | None = None,
        datetime_range: str | None = None,
        collections: list | str | None = None,
        max_items: int = 20,
        item_id: str | None = None,
        collection_id: str | None = None,
        query_bands: list | str | None = None,
        limit: int = 1,
        # session
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Spatial indexing and discovery.

        Modes:
          h3_index      — H3 hexagonal spatial indexing (lat/lng to cell, aggregate, k-ring)
          lancedb_store — LanceDB embedded vector store (store/search earth embeddings)
          stac_discover — STAC catalog query for COG/GeoParquet/Zarr datasets
        """
        if mode == "h3_index":
            return await _h3_spatial_index(
                mode="latlng_to_cell", lat=lat, lng=lng, resolution=resolution,
                h3_cell=h3_cell, points=points, k=k, polygon=polygon,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode == "lancedb_store":
            return await _lancedb_embed_store(
                mode="search", table_name=table_name, embeddings=embeddings,
                metadata=metadata, k=k, refine_factor=refine_factor,
                filter_expr=filter_expr, h3_cell=h3_cell, h3_radius=h3_radius,
                create_if_missing=create_if_missing, drop_table=drop_table,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode == "stac_discover":
            return await _stac_discover(
                mode="search", catalog=catalog, bbox=bbox,
                datetime_range=datetime_range, collections=collections,
                max_items=max_items, item_id=item_id, collection_id=collection_id,
                query_bands=query_bands, limit=limit,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        else:
            return {"error": f"Unknown mode: {mode}. Valid: h3_index, lancedb_store, stac_discover"}

    @mcp.tool(name="geox_h3_spatial_index", annotations=_geox_annotations("geox_h3_spatial_index"))
    async def _shim_h3_spatial_index(mode="latlng_to_cell", lat=None, lng=None, resolution=7, h3_cell=None, points=None, k=1, polygon=None, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_spatial(mode=h3_index)]"""
        return await _spatial_unified(mode="h3_index", lat=lat, lng=lng, resolution=resolution, h3_cell=h3_cell, points=points, k=k, polygon=polygon, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_lancedb_embed_store", annotations=_geox_annotations("geox_lancedb_embed_store"))
    async def _shim_lancedb_embed_store(mode="search", table_name="geo_embeddings", embeddings=None, metadata=None, k=10, refine_factor=None, filter_expr=None, h3_cell=None, h3_radius=1, create_if_missing=True, drop_table=False, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_spatial(mode=lancedb_store)]"""
        return await _spatial_unified(mode="lancedb_store", table_name=table_name, embeddings=embeddings, metadata=metadata, k=k, refine_factor=refine_factor, filter_expr=filter_expr, h3_cell=h3_cell, h3_radius=h3_radius, create_if_missing=create_if_missing, drop_table=drop_table, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_stac_discover", annotations=_geox_annotations("geox_stac_discover"))
    async def _shim_stac_discover(mode="search", catalog="earthsearch", bbox=None, datetime_range=None, collections=None, max_items=20, item_id=None, collection_id=None, query_bands=None, limit=1, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_spatial(mode=stac_discover)]"""
        return await _spatial_unified(mode="stac_discover", catalog=catalog, bbox=bbox, datetime_range=datetime_range, collections=collections, max_items=max_items, item_id=item_id, collection_id=collection_id, query_bands=query_bands, limit=limit, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    # ── GROUP 5: geox_deep_time — absorbs dde_reason ──
    @mcp.tool(
        name="geox_deep_time",
        description="Deep-time Digital Earth reasoning. Modes: dde_reason (DDE Ontology + Macrostrat neuro-symbolic reasoning for stratigraphic queries, cross-section validation, tectonic context).",
        annotations=_geox_annotations("geox_deep_time"),
    )
    async def _deep_time_unified(
        mode: str = "dde_reason",
        bbox: list | str | None = None,
        lat: float | None = None,
        lng: float | None = None,
        formation: str | None = None,
        known_units: list | str | None = None,
        ontology_term: str | None = None,
        section_params: dict | str | None = None,
        delta_age_ma: float | None = None,
        limit: int = 10,
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Deep-time Digital Earth reasoning.

        Modes:
          dde_reason — Query DDE Ontology + Macrostrat for stratigraphic reasoning,
                       infer missing geology, validate cross-sections, tectonic context
        """
        # 2026-09-06: do not call nested _dde_reason (may be missing if LEM E5
        # import failed) and do not forward session envelope blindly
        # (unexpected keyword on older impls). Import + _safe_forward.
        from geox_mcp.tools.dde_reason import geox_dde_reason as _impl

        impl_mode = "query_stratigraphy"
        if mode in (
            "tectonic_context",
            "lithology_at_point",
            "age_constraints",
            "query_dde",
            "infer_missing",
            "validate_section",
            "query_stratigraphy",
        ):
            impl_mode = mode
        elif mode not in ("dde_reason", "query_stratigraphy"):
            return {
                "ok": False,
                "error": (
                    f"Unknown mode: {mode}. Valid: dde_reason, tectonic_context, "
                    "lithology_at_point, age_constraints, query_dde"
                ),
            }

        args = _safe_forward(
            _impl,
            {
                "mode": impl_mode,
                "bbox": bbox,
                "lat": lat,
                "lng": lng,
                "formation": formation,
                "known_units": known_units,
                "ontology_term": ontology_term,
                "section_params": section_params,
                "delta_age_ma": delta_age_ma,
                "limit": limit,
            },
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
        return await _impl(**args)

    @mcp.tool(name="geox_dde_reason", annotations=_geox_annotations("geox_dde_reason"))
    async def _shim_dde_reason(mode="query_stratigraphy", bbox=None, lat=None, lng=None, formation=None, known_units=None, ontology_term=None, section_params=None, delta_age_ma=None, limit=10, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_deep_time(mode=dde_reason)]"""
        return await _deep_time_unified(mode="dde_reason", bbox=bbox, lat=lat, lng=lng, formation=formation, known_units=known_units, ontology_term=ontology_term, section_params=section_params, delta_age_ma=delta_age_ma, limit=limit, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    # ── GROUP 6: geox_claim — absorbs evidence/evidence_synthesize/falsify/contradiction_scan ──
    @mcp.tool(
        name="geox_claim",
        description="Unified claim engine. Modes: create/validate/challenge/seal/attach (claim lifecycle), falsify (Popperian falsification), discover/synthesize/abduct/contradict/spatial_block/ingest_literature (evidence), scan (contradiction scan).",
        annotations=_geox_annotations("geox_claim"),
    )
    async def _claim_unified(
        mode: str = "create",
        # ── claim params ──
        claim_id: str = "",
        claim_text: str = "",
        claim_type: str = "other",
        truth_class: str = "INTERPRETATION",
        evidence_ids: list[str] | None = None,
        uncertainty_p10: float | None = None,
        uncertainty_p50: float | None = None,
        uncertainty_p90: float | None = None,
        uncertainty_distribution: str = "lognormal",
        alternatives: list[dict[str, Any]] | None = None,
        provenance: str = "GEOX Claim Engine",
        authority: str = "GEOX_CLAIM_WORKER",
        challenge_text: str = "",
        alternative_claim_text: str = "",
        alternative_evidence_ids: list[str] | None = None,
        challenge_evidence_ids: list[str] | None = None,
        alternative_uncertainty: dict[str, Any] | None = None,
        challenger_provenance: str = "GEOX Claim Engine",
        ack_irreversible: bool = False,
        seal_verdict: str = "SEAL",
        voxel_state: dict[str, Any] | None = None,
        # ── evidence params ──
        evidence_id: str = "",
        evidence_type: str = "supporting",
        epistemic_label: str | None = None,
        forbidden_uses: list[str] | None = None,
        source_citation: dict[str, Any] | None = None,
        category: str | None = None,
        # ── falsify/scan params ──
        context: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        # ── evidence_unified params ──
        query: str = "",
        scope: str = "all",
        permission_level: str = "authorized",
        file_path: str = "",
        basin_name: str | None = None,
        evidence_refs: list[str] | None = None,
        hypotheses: list[str] | None = None,
        scale: str = "parasequence",
        depo_context: str = "unknown",
        claim_strictness: str = "screen",
        reasoning_mode: str = "default",
        samples: list[dict[str, Any]] | None = None,
        block_size_km: float = 5.0,
        n_folds: int = 5,
        target_key: str = "value",
        feature_keys: list[str] | None = None,
        # ── session ──
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Unified claim engine — lifecycle, falsification, evidence, contradiction scanning.

        Modes:
          claim lifecycle: create, validate, challenge, seal, attach
          falsification:   falsify (Popperian falsification engine)
          evidence:        discover, synthesize, abduct, contradict, spatial_block, ingest_literature
          scanning:        scan (contradiction scan)
        """
        if mode in ("create", "validate", "challenge", "seal", "attach"):
            return await _claim(
                mode=mode, claim_id=claim_id, claim_text=claim_text,
                claim_type=claim_type, truth_class=truth_class,
                evidence_ids=evidence_ids, uncertainty_p10=uncertainty_p10,
                uncertainty_p50=uncertainty_p50, uncertainty_p90=uncertainty_p90,
                uncertainty_distribution=uncertainty_distribution,
                alternatives=alternatives, provenance=provenance, authority=authority,
                challenge_text=challenge_text,
                alternative_claim_text=alternative_claim_text,
                alternative_evidence_ids=alternative_evidence_ids,
                challenge_evidence_ids=challenge_evidence_ids,
                alternative_uncertainty=alternative_uncertainty,
                challenger_provenance=challenger_provenance,
                ack_irreversible=ack_irreversible, seal_verdict=seal_verdict,
                voxel_state=voxel_state, evidence_id=evidence_id,
                evidence_type=evidence_type, epistemic_label=epistemic_label,
                forbidden_uses=forbidden_uses, source_citation=source_citation,
                category=category,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode == "falsify":
            return await _falsify(
                claim_text=claim_text, claim_type=claim_type, mode="full",
                context=context, evidence=evidence,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode in ("discover", "synthesize", "abduct", "contradict", "spatial_block", "ingest_literature"):
            return await _evidence(
                mode=mode, evidence_id=evidence_id, evidence_type=evidence_type,
                claim_id=claim_id, claim_text=claim_text, query=query, scope=scope,
                file_path=file_path, basin_name=basin_name,
                evidence_refs=evidence_refs, hypotheses=hypotheses,
                epistemic_label=epistemic_label, forbidden_uses=forbidden_uses,
                source_citation=source_citation, category=category,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode == "scan":
            return await _contradiction_scan(
                claim_text=claim_text, claim_type=claim_type, mode="full",
                context=context, evidence=evidence,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        else:
            return {"error": f"Unknown mode: {mode}. Valid: create, validate, challenge, seal, attach, falsify, discover, synthesize, abduct, contradict, scan, spatial_block, ingest_literature"}

    # GROUP 6 shims
    @mcp.tool(name="geox_falsify", annotations=_geox_annotations("geox_falsify"))
    async def _shim_falsify(claim_text="", claim_type="general", mode="full", context=None, evidence=None, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_claim(mode=falsify)]"""
        return await _claim_unified(mode="falsify", claim_text=claim_text, claim_type=claim_type, context=context, evidence=evidence, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_evidence_synthesize", annotations=_geox_annotations("geox_evidence_synthesize"))
    async def _shim_evidence_synthesize(mode="synthesize", query="", scope="all", permission_level="authorized", file_path="", basin_name=None, evidence_refs=None, hypotheses=None, scale="parasequence", depo_context="unknown", claim_strictness="screen", reasoning_mode="default", samples=None, block_size_km=5.0, n_folds=5, target_key="value", feature_keys=None, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_claim(mode=synthesize)]"""
        return await _claim_unified(mode="synthesize", query=query, scope=scope, permission_level=permission_level, file_path=file_path, basin_name=basin_name, evidence_refs=evidence_refs, hypotheses=hypotheses, scale=scale, depo_context=depo_context, claim_strictness=claim_strictness, reasoning_mode=reasoning_mode, samples=samples, block_size_km=block_size_km, n_folds=n_folds, target_key=target_key, feature_keys=feature_keys, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_contradiction_scan", annotations=_geox_annotations("geox_contradiction_scan"))
    async def _shim_contradiction_scan(claim_text="", claim_type="general", mode="full", context=None, evidence=None, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_claim(mode=scan)]"""
        return await _claim_unified(mode="scan", claim_text=claim_text, claim_type=claim_type, context=context, evidence=evidence, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_evidence", annotations=_geox_annotations("geox_evidence"))
    async def _shim_evidence(mode="synthesize", evidence_id="", evidence_type="supporting", claim_id="", claim_text="", query="", scope="all", file_path="", basin_name=None, evidence_refs=None, hypotheses=None, epistemic_label=None, forbidden_uses=None, source_citation=None, category=None, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_claim(mode=evidence)]"""
        return await _claim_unified(mode=mode, evidence_id=evidence_id, evidence_type=evidence_type, claim_id=claim_id, claim_text=claim_text, query=query, scope=scope, file_path=file_path, basin_name=basin_name, evidence_refs=evidence_refs, hypotheses=hypotheses, epistemic_label=epistemic_label, forbidden_uses=forbidden_uses, source_citation=source_citation, category=category, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    # ── GROUP 7: geox_model — absorbs subsurface_model/geological_model_generate/gempy_implicit_3d ──
    @mcp.tool(
        name="geox_model",
        description="Subsurface and geological modeling. Modes: subsurface (joint inversion, gravity/mag, MT forward), geological_generate (deterministic 2D cross-section from strata), gempy_3d (GemPy implicit 3D structural modeling).",
        annotations=_geox_annotations("geox_model"),
    )
    async def _model_unified(
        mode: str = "subsurface",
        # ── subsurface params ──
        survey_type: str = "gravity",
        easting_m: tuple[float, ...] | None = None,
        northing_m: tuple[float, ...] | None = None,
        prisms: list[dict[str, Any]] | None = None,
        magnetization_a_m: float = 0.0,
        field_declination_deg: float = 0.0,
        field_inclination_deg: float = 0.0,
        layers: list[dict[str, Any]] | None = None,
        frequencies_hz: list[float] | None = None,
        observations: dict[str, Any] | None = None,
        prior: dict[str, Any] | None = None,
        max_iter: int = 50,
        tolerance: float = 0.001,
        # ── geological_generate params (Pydantic model passed through) ──
        geological_params: dict[str, Any] | None = None,
        # ── gempy_3d params ──
        surface_points: list | str | None = None,
        orientations: list | str | None = None,
        grid_resolution: tuple | list | str | None = None,
        model_extent: tuple | list | str | None = None,
        compute_uncertainty: bool = True,
        uncertainty_realizations: int = 10,
        fault_groups: list | str | None = None,
        output_format: str = "json",
        # ── session ──
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Subsurface and geological modeling.

        Modes:
          subsurface          — Joint inversion, gravity/mag, MT forward modeling
          geological_generate — Deterministic 2D geological cross-section from strata definition
          gempy_3d            — GemPy implicit 3D structural modeling from surface points
        """
        if mode == "subsurface":
            return await _subsurface_model(
                mode="joint_inversion", survey_type=survey_type,
                easting_m=easting_m, northing_m=northing_m, prisms=prisms,
                magnetization_a_m=magnetization_a_m,
                field_declination_deg=field_declination_deg,
                field_inclination_deg=field_inclination_deg, layers=layers,
                frequencies_hz=frequencies_hz, observations=observations,
                prior=prior, max_iter=max_iter, tolerance=tolerance,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode == "geological_generate":
            if geological_params is not None:
                params = _GeologicalModelParams(**geological_params)
            else:
                params = _GeologicalModelParams()
            return await _geological_model_generate(
                params=params, session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode == "gempy_3d":
            return await _gempy_implicit_3d(
                surface_points=surface_points, orientations=orientations,
                grid_resolution=grid_resolution, model_extent=model_extent,
                compute_uncertainty=compute_uncertainty,
                uncertainty_realizations=uncertainty_realizations,
                fault_groups=fault_groups, output_format=output_format,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        else:
            return {"error": f"Unknown mode: {mode}. Valid: subsurface, geological_generate, gempy_3d"}

    @mcp.tool(name="geox_subsurface_model", annotations=_geox_annotations("geox_subsurface_model"))
    async def _shim_subsurface_model(mode="joint_inversion", survey_type="gravity", easting_m=None, northing_m=None, prisms=None, magnetization_a_m=0.0, field_declination_deg=0.0, field_inclination_deg=0.0, layers=None, frequencies_hz=None, observations=None, prior=None, max_iter=50, tolerance=0.001, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_model(mode=subsurface)]"""
        return await _model_unified(mode="subsurface", survey_type=survey_type, easting_m=easting_m, northing_m=northing_m, prisms=prisms, magnetization_a_m=magnetization_a_m, field_declination_deg=field_declination_deg, field_inclination_deg=field_inclination_deg, layers=layers, frequencies_hz=frequencies_hz, observations=observations, prior=prior, max_iter=max_iter, tolerance=tolerance, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_geological_model_generate", annotations=_geox_annotations("geox_geological_model_generate"))
    async def _shim_geological_model_generate(geological_params=None, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_model(mode=geological_generate)]"""
        return await _model_unified(mode="geological_generate", geological_params=geological_params, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_gempy_implicit_3d", annotations=_geox_annotations("geox_gempy_implicit_3d"))
    async def _shim_gempy_implicit_3d(surface_points=None, orientations=None, grid_resolution=None, model_extent=None, compute_uncertainty=True, uncertainty_realizations=10, fault_groups=None, output_format="json", session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_model(mode=gempy_3d)]"""
        return await _model_unified(mode="gempy_3d", surface_points=surface_points, orientations=orientations, grid_resolution=grid_resolution, model_extent=model_extent, compute_uncertainty=compute_uncertainty, uncertainty_realizations=uncertainty_realizations, fault_groups=fault_groups, output_format=output_format, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    # ── GROUP 8: geox_well — absorbs well_view/well_desk ──
    @mcp.tool(
        name="geox_well",
        description="Well operations. Modes: view (hydrate LAS curves into interactive tracks for WellDesk), desk (interactive view, publish, render with petrophysics).",
        annotations=_geox_annotations("geox_well"),
    )
    async def _well_unified(
        mode: str = "view",
        well_id: str | None = None,
        source_uri: str | None = None,
        # desk params
        depth_top: float | None = None,
        depth_base: float | None = None,
        curves: list[str] | None = None,
        las_path: str | None = None,
        interpret: bool = True,
        rw: float = 0.03,
        # view params
        max_samples: int = 2000,
        # session
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Well operations.

        Modes:
          view — Hydrate LAS curves into interactive tracks for WellDesk UI
          desk — Interactive well-desk: open/publish/render with petrophysics
        """
        if mode == "view":
            return await _well_view(
                well_id=well_id, source_uri=source_uri, max_samples=max_samples,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        elif mode == "desk":
            return await _well_desk(
                mode="open", well_id=well_id, depth_top=depth_top,
                depth_base=depth_base, curves=curves, las_path=las_path,
                interpret=interpret, rw=rw,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        else:
            return await _well_desk(
                mode=mode, well_id=well_id, depth_top=depth_top,
                depth_base=depth_base, curves=curves, las_path=las_path,
                interpret=interpret, rw=rw,
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )

    @mcp.tool(name="geox_well_view", annotations=_geox_annotations("geox_well_view"))
    async def _shim_well_view(well_id=None, source_uri=None, session_id=None, actor_id=None, trace_id=None, max_samples=2000):
        """[SHIM→geox_well(mode=view)]"""
        return await _well_unified(mode="view", well_id=well_id, source_uri=source_uri, max_samples=max_samples, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    @mcp.tool(name="geox_well_desk", annotations=_geox_annotations("geox_well_desk"))
    async def _shim_well_desk(mode="open", well_id="", depth_top=None, depth_base=None, curves=None, las_path=None, interpret=True, rw=0.03, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_well(mode=desk)]"""
        return await _well_unified(mode=mode, well_id=well_id, depth_top=depth_top, depth_base=depth_base, curves=curves, las_path=las_path, interpret=interpret, rw=rw, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    # ── GROUP 9: geox_petrophysics absorbs sequence/lem_predict ──
    # (geox_petrophysics already exists with mode parameter — shims only)
    @mcp.tool(name="geox_sequence", annotations=_geox_annotations("geox_sequence"))
    async def _shim_sequence(workflow="single_well", source=None, zone_top=None, zone_base=None, depo_env_code="FLUVIAL", bin_size_m=10.0, min_package_thickness_m=20.0, p50_shift_api=15.0, gr_cutoff_api=75.0, detail_level="full", project_yaml=None, output_dir=None, section_ref=None, well_refs=None, mode="correlation", well_las_paths=None, tops=None, zone_definitions=None, strat_standard=None, paleoenvironment_input=None, checkshot_ref=None, wavelet_mode="ricker", wavelet_freq_hz=None, phase_degrees=0.0, polarity="SEG_NORMAL", synthetics_output=False, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_petrophysics] Sequence stratigraphy wrapper."""
        from geox_mcp.tools.sequence_unified import geox_sequence as _impl
        args = _safe_forward(_impl, {"workflow": workflow, "source": source, "zone_top": zone_top, "zone_base": zone_base, "depo_env_code": depo_env_code, "bin_size_m": bin_size_m, "min_package_thickness_m": min_package_thickness_m, "p50_shift_api": p50_shift_api, "gr_cutoff_api": gr_cutoff_api, "detail_level": detail_level, "project_yaml": project_yaml, "output_dir": output_dir, "section_ref": section_ref, "well_refs": well_refs, "mode": mode, "well_las_paths": well_las_paths, "tops": tops, "zone_definitions": zone_definitions, "strat_standard": strat_standard, "paleoenvironment_input": paleoenvironment_input, "checkshot_ref": checkshot_ref, "wavelet_mode": wavelet_mode, "wavelet_freq_hz": wavelet_freq_hz, "phase_degrees": phase_degrees, "polarity": polarity, "synthetics_output": synthetics_output}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    @mcp.tool(name="geox_lem_predict", annotations=_geox_annotations("geox_lem_predict"))
    async def _shim_lem_predict(target_depth_m=None, basin_context=None, cube_inline=None, lmr_inline=None, use_synth_cube=True, candidate_ref=None, domain=None, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_petrophysics] Litho-Elastic prediction wrapper."""
        from geox_mcp.tools.lem_predict import LEMPredictRequest, geox_lem_predict as _impl
        req = LEMPredictRequest(well_id=candidate_ref or "lem-synthetic", curves={"GR": [75.0], "RT": [5.0], "RHOB": [2.35]}, depth_m=[target_depth_m] if target_depth_m else [1500.0], depth_top_m=target_depth_m, depth_bot_m=target_depth_m, basin=basin_context, session_id=session_id, actor_id=actor_id)
        result = await _impl(req)
        payload = result if isinstance(result, dict) else result.model_dump(mode="json")
        from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui, wrap_as_ui_tool_result
        return wrap_as_ui_tool_result(payload, app_id="well_desk", params={"mode": "lem", "depth_m": target_depth_m}, structured_override=compact_structured_for_ui(payload, tool="geox_lem_predict", app_id="well_desk"), text=(f"LEM predict depth={target_depth_m} basin={basin_context or 'n/a'}. UI: ui://geox/well-desk."))

    # ── GROUP 10: geox_seismic_interpret absorbs visual_understand ──
    # (geox_seismic_interpret already exists with mode parameter — shim only)
    @mcp.tool(name="geox_visual_understand", annotations=_geox_annotations("geox_visual_understand"))
    async def _shim_visual_understand(image_path="", mode="full", session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_seismic_interpret] OBS_IMAGE perception assist."""
        from geox_mcp.tools.mcp_apps_bridge import wrap_as_ui_tool_result
        from geox_mcp.tools.seismic_vision_ai_async import geox_visual_understand_async as _impl
        result = await _impl(image_path=image_path or "", mode=mode or "full")
        is_hold = isinstance(result, dict) and (result.get("status") in ("HOLD", "VOID") or result.get("ok") is False)
        text = (f"Visual understand HOLD: {result.get('error') or result.get('reason') or 'no backend'}" if is_hold else "Visual understand complete (OBS_IMAGE only). UI: ui://geox/visual-hub.")
        return wrap_as_ui_tool_result(result, app_id="visual_hub", structured_override=result if isinstance(result, dict) else {"data": result}, text=text)

    # ── GROUP 11: geox_seismic_compute absorbs avo_forward ──
    @mcp.tool(
        name="geox_seismic_compute",
        description="Seismic computation. Modes: avo_forward (AVO forward modeling: Zoeppritz, Shuey, LMR, Castagna).",
        annotations=_geox_annotations("geox_seismic_compute"),
    )
    async def _seismic_compute_unified(
        mode: str = "avo_forward",
        # avo_forward params
        vp1: float = 3.0,
        vs1: float = 1.5,
        rho1: float = 2.3,
        vp2: float = 2.5,
        vs2: float = 1.2,
        rho2: float = 2.1,
        theta_deg: list[float] | None = None,
        theta_max: float = 30.0,
        vp: float = 3.0,
        vs: float = 1.5,
        rho: float = 2.3,
        fluid_zone: str = "brine",
        unit: str = "m/s",
        session_id: str | None = None,
        actor_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Seismic computation tools.

        Modes:
          avo_forward — AVO forward modeling: Zoeppritz exact Rpp, Shuey 2-term,
                        Lambda-Mu-Rho (Goodway 1997), Castagna mudrock
        """
        if mode == "avo_forward":
            return await _avo_forward(
                mode="zoeppritz", vp1=vp1, vs1=vs1, rho1=rho1, vp2=vp2, vs2=vs2, rho2=rho2,
                theta_deg=theta_deg, theta_max=theta_max, vp=vp, vs=vs, rho=rho,
                fluid_zone=fluid_zone, unit=unit,
            )
        else:
            return {"error": f"Unknown mode: {mode}. Valid: avo_forward"}

    @mcp.tool(name="geox_avo_forward", annotations=_geox_annotations("geox_avo_forward"))
    async def _shim_avo_forward(mode="zoeppritz", vp1=3.0, vs1=1.5, rho1=2.3, vp2=2.5, vs2=1.2, rho2=2.1, theta_deg=None, theta_max=30.0, vp=3.0, vs=1.5, rho=2.3, fluid_zone="brine", unit="m/s"):
        """[SHIM→geox_seismic_compute(mode=avo_forward)]"""
        return await _seismic_compute_unified(mode="avo_forward", vp1=vp1, vs1=vs1, rho1=rho1, vp2=vp2, vs2=vs2, rho2=rho2, theta_deg=theta_deg, theta_max=theta_max, vp=vp, vs=vs, rho=rho, fluid_zone=fluid_zone, unit=unit)

    # ── GROUP 12: geox_basin absorbs basin_backstrip/thermal_maturity_history ──
    # (geox_basin already exists with mode parameter — shims only)
    @mcp.tool(name="geox_basin_backstrip", annotations=_geox_annotations("geox_basin_backstrip"))
    async def _shim_basin_backstrip(well_ref, stratigraphic_ages, lithology_model, palaeobathymetry_model, sea_level_model_ref="", water_density_kg_m3=1030.0, mantle_density_kg_m3=3300.0, uncertainty_realizations=1000, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_basin] 1D basin backstripping."""
        from geox_mcp.tools.basin_engines.backstrip_tool import geox_basin_backstrip as _impl
        args = _safe_forward(_impl, {"well_ref": well_ref, "stratigraphic_ages": stratigraphic_ages, "lithology_model": lithology_model, "palaeobathymetry_model": palaeobathymetry_model, "sea_level_model_ref": sea_level_model_ref, "water_density_kg_m3": water_density_kg_m3, "mantle_density_kg_m3": mantle_density_kg_m3, "uncertainty_realizations": uncertainty_realizations}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    @mcp.tool(name="geox_thermal_maturity_history", annotations=_geox_annotations("geox_thermal_maturity_history"))
    async def _shim_thermal_maturity_history(well_ref, burial_history, heat_flow_history=None, surface_temp_c=20.0, geothermal_gradient_c_km=30.0, time_step_myr=1.0, session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_basin] Burial + heat flow + maturity modelling."""
        from geox_mcp.tools.basin_engines.thermal_tool import geox_thermal_maturity_history as _impl
        args = _safe_forward(_impl, {"well_ref": well_ref, "burial_history": burial_history, "heat_flow_history": heat_flow_history, "surface_temp_c": surface_temp_c, "geothermal_gradient_c_km": geothermal_gradient_c_km, "time_step_myr": time_step_myr}, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
        return await _impl(**args)

    # ── GROUP 13: geox_workspace absorbs surface_status ──
    # (geox_workspace already exists with mode parameter — shim only)
    @mcp.tool(name="geox_surface_status", annotations=_geox_annotations("geox_surface_status"))
    async def _shim_surface_status(mode="registry", session_id=None, actor_id=None, trace_id=None):
        """[SHIM→geox_workspace] Federation-standard registry probe for GEOX."""
        return await geox_workspace(mode=mode, session_id=session_id, actor_id=actor_id, trace_id=trace_id)

    logger.info("ZEN CONSOLIDATION: merged tools + shims registered")


    # ═══════════════════════════════════════════════════════════════════════════════
    # H1 P1.1: Evidence-Chain Enforcement — wraps every tool handler with
    # isError + empty-evidence detection + outputSchema injection.
    # Fixes the transport-success ≠ evidence-success defect (Roadmap §1).
    # ═══════════════════════════════════════════════════════════════════════════════
    _EVIDENCE_WRAPPED = 0
    _EVIDENCE_SKIPPED = 0
    for _comp_key, _comp in list(_components.items()):
        if not _comp_key.startswith("tool:geox_"):
            continue
        _tool_name = _comp_key.removeprefix("tool:").rstrip("@")
        _orig_fn = getattr(_comp, "fn", None)
        if _orig_fn is None:
            _EVIDENCE_SKIPPED += 1
            continue

        @functools.wraps(_orig_fn)
        async def _evidence_wrapper(*args, _tool=_tool_name, _orig=_orig_fn, **kwargs):
            try:
                result = await _orig(*args, **kwargs)
            except Exception as exc:
                from geox_mcp.federation_safety import classify_error

                return classify_error(exc, source_tool=_tool, source_organ="geox")

            # Detect error state in dict results (F2: empty error="" is NOT failure)
            _is_err = False
            if isinstance(result, dict):
                from geox_mcp.result_truth import result_is_error as _result_is_error

                _is_err = _result_is_error(result)
                # ENFORCE: empty evidence with ok: true → isError: true
                _meta_keys = {
                    "ok",
                    "isError",
                    "status",
                    "error",
                    "tool",
                    "mode",
                    "data_mode",
                    "ext_witness_ready",
                    "ext_witness_note",
                    "provenance",
                    "_memory",
                    "_epistemic",
                    "message",
                    "apex",
                    "geox_advisory",
                    "_meta",
                    "_evidence_receipt",
                }
                _has_evidence = any(k not in _meta_keys and result.get(k) is not None for k in result)
                if not _has_evidence and not _is_err and result.get("ok") is not False:
                    logger.warning(f"EVIDENCE_GAP: {_tool} returned ok but no evidence fields")
                    result["isError"] = True
                    result.setdefault(
                        "error",
                        "Tool returned no evidence — transport success ≠ evidence success",
                    )
                    _is_err = True
                elif _is_err:
                    result["isError"] = True
                    # Keep ok consistent with isError when ok claimed success
                    if result.get("ok") is True:
                        result["ok"] = False
                else:
                    result["isError"] = False
                    # Clear vacuous error keys so clients don't misread
                    if result.get("error") == "":
                        result.pop("error", None)

                # Inject outputSchema reference from canonical registry
                from geox_mcp.tools.mcp_apps_bridge import get_output_schema

                _schema = get_output_schema(_tool)
                if _schema:
                    result.setdefault("_meta", {})
                    if isinstance(result["_meta"], dict):
                        result["_meta"].setdefault("outputSchema", _schema)

                # P1.3: Content-hash evidence receipt (SHA-256)
                import hashlib

                _receipt_keys = [k for k in result if not k.startswith("_") and k not in ("content", "structuredContent")]
                _receipt_data = {k: result[k] for k in _receipt_keys if k in result}
                try:
                    _payload = json.dumps(_receipt_data, default=str, sort_keys=True).encode()
                    _hash = hashlib.sha256(_payload).hexdigest()
                    result["_evidence_receipt"] = {
                        "sha256": _hash,
                        "tool": _tool,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "isError": _is_err,
                    }
                except Exception:
                    pass

                # P1.4: False-success monitor — detect confident-but-empty outputs
                try:
                    from geox_mcp.monitoring.false_success_detector import FalseSuccessDetector, _FALSE_SUCCESS_SEED_CORPUS

                    _fs_detector = FalseSuccessDetector(corpus_documents=_FALSE_SUCCESS_SEED_CORPUS)
                    _text_content = json.dumps({k: v for k, v in result.items() if not k.startswith("_")}, default=str)[:2000]
                    _fs_report = _fs_detector.detect(_text_content, result, _tool)
                    if _fs_report.verdict != "CLEAN":
                        result.setdefault("_false_success", _fs_report.to_dict())
                        if not _is_err and _fs_report.verdict == "FALSE_SUCCESS":
                            logger.warning(
                                "FALSE_SUCCESS: %s score=%.3f — confident language with no evidence",
                                _tool,
                                _fs_report.score,
                            )
                except Exception:
                    pass

            elif hasattr(result, "is_error"):
                _is_err = bool(result.is_error)

            return result

        _comp.fn = _evidence_wrapper
        _EVIDENCE_WRAPPED += 1

    logger.info(
        "EVIDENCE_CHAIN: wrapped %d tools with isError + empty-evidence enforcement (%d skipped)",
        _EVIDENCE_WRAPPED,
        _EVIDENCE_SKIPPED,
    )
