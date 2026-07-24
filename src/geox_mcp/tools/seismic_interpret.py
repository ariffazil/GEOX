"""
geox_seismic_interpret — Seismic Interpretation (Phase 2 + P0/C/A/D 2026-07-23)
════════════════════════════════════════════════════════════════════════════════
Live modes (public, callable):
  horizon_contrast   — 1D multi-attribute boundary detector (ToAC)
  fault_sticks       — Fault stick CSV/GeoJSON ingest (not auto-extract)
  volume_frame       — Volume frame read/write
  blend              — Alpha/RGB volume blending
  structure_validate — G2–G9 + K-* structural falsifier (+ interpretation_bundle)
  interpret          — propose→validate→compare bundle (framework and/or image)
  interpret_section  — RSI image-true propose (INT_SEISMIC, QUALIFIED_CANDIDATE)
  rsi_pipeline       — thin alias → geox_rsi_interpret
  section_image      — alias interpret_section
  segy_slice         — Phase D: SEG-Y → MeasurementContext + amplitude stats
  track_horizon      — F1 zen: 2D phase-aware DP track → horizon polylines
  measure_throw      — F1 zen: cutoffs → dmax_m/length_m/throw_profile_m + gates

Still HOLD (not public-executable):
  vision, extract_faults, build_structure, observe_image, falsify

Local engine verdicts are QUALIFIED_CANDIDATE at most — arifOS seals.
preferred_hypothesis always null from GEOX (human adjudicates).
DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import base64
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any

# Modes the handler can execute today
_LIVE_MODES = frozenset(
    {
        "horizon_contrast",
        "fault_sticks",
        "volume_frame",
        "blend",
        "structure_validate",
        "interpret",
        "classical_section",
        "interpret_section",
        "rsi_pipeline",
        "section_image",
        "segy_slice",
        "segy_2d",
        "track_horizon",  # F1 zen 2D phase track
        "measure_throw",  # F1 zen throw → structure gates
        "cutoff_throw",  # alias measure_throw
        "render",  # deterministic section overlay PNG (human loop)
    }
)

# Manifest-claimed but not public-executable — deliberate HOLD, not silent remaps
_NOT_YET_MODES: dict[str, str] = {
    "contrast": "Alias of horizon_contrast — pass mode=horizon_contrast with attribute_data+depth.",
    "vision": (
        "Vision modes (geox_visual_understand / geox_vision_*) are separate tools. "
        "geox_seismic_interpret does not run VLM. Call geox_visual_understand for OBS_IMAGE."
    ),
    "extract_faults": "Auto fault-plane extraction not proven. Use measure_throw + structure_validate.",
    "build_structure": "Use structure_validate on a proposed framework; full build_structure loop later.",
    "falsify": "Use geox_falsify (claim_type=structural_*) for claim physics checks.",
    "observe_image": "Use geox_visual_understand for OBS_IMAGE (HOLD without VLM).",
}


# Max raw decoded image bytes for chat base64 (~2 MiB). Downscale after if larger.
_MAX_IMAGE_BYTES = 2 * 1024 * 1024


def _json_safe(obj: Any) -> Any:
    """Make tool payloads JSON-serializable for MCP structuredContent.

    RSI/geometry paths leak numpy scalars (esp. numpy.bool_, float64). FastMCP
    then fails json.dumps → clients see 'outputSchema defined but no structured
    output returned' even though governance ALLOWED and the engine succeeded.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    # numpy scalars / arrays (and similar)
    item = getattr(obj, "item", None)
    if callable(item):
        try:
            return _json_safe(item())
        except Exception:
            pass
    tolist = getattr(obj, "tolist", None)
    if callable(tolist):
        try:
            return _json_safe(tolist())
        except Exception:
            pass
    if hasattr(obj, "__fspath__"):
        return str(obj)
    # last resort — keep transport alive over perfect fidelity
    return str(obj)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _resolve_image_input(
    *,
    image_path: str | None = None,
    image_data: str | None = None,
    artifact_ref: str | None = None,
    source_uri: str | None = None,
) -> dict[str, Any]:
    """Resolve server path and/or base64 chat image → local path + input_hash.

    Returns:
      {ok, path?, input_hash?, error?, message?, source?}
    """
    # 1) base64 / data-URL from chat clients
    if image_data and str(image_data).strip():
        raw = str(image_data).strip()
        if raw.startswith("data:") and "," in raw:
            raw = raw.split(",", 1)[1]
        try:
            blob = base64.b64decode(raw, validate=False)
        except Exception as exc:
            return {
                "ok": False,
                "error": "INVALID_IMAGE_DATA",
                "message": f"image_data is not valid base64: {exc}",
            }
        if not blob:
            return {"ok": False, "error": "EMPTY_IMAGE_DATA", "message": "image_data decoded empty"}
        input_hash = _sha256_bytes(blob)
        # size-cap: if too large, try server-side downscale
        if len(blob) > _MAX_IMAGE_BYTES:
            try:
                from io import BytesIO

                from PIL import Image

                im = Image.open(BytesIO(blob))
                im = im.convert("RGB")
                # iterative downscale until under cap
                w, h = im.size
                while True:
                    buf = BytesIO()
                    im.save(buf, format="JPEG", quality=85)
                    out = buf.getvalue()
                    if len(out) <= _MAX_IMAGE_BYTES or w < 256 or h < 256:
                        blob = out
                        break
                    w, h = max(256, int(w * 0.75)), max(256, int(h * 0.75))
                    im = im.resize((w, h))
                input_hash = _sha256_bytes(blob)  # hash of stored payload
            except Exception:
                return {
                    "ok": False,
                    "error": "IMAGE_TOO_LARGE",
                    "message": (
                        f"image_data {len(blob)} bytes exceeds {_MAX_IMAGE_BYTES} "
                        "and downscale failed — compress client-side"
                    ),
                }
        suffix = ".jpg"
        # sniff
        if blob[:8] == b"\x89PNG\r\n\x1a\n":
            suffix = ".png"
        elif blob[:2] == b"\xff\xd8":
            suffix = ".jpg"
        fd, tmp_path = tempfile.mkstemp(prefix="geox_img_", suffix=suffix)
        try:
            os.write(fd, blob)
        finally:
            os.close(fd)
        return {
            "ok": True,
            "path": tmp_path,
            "input_hash": input_hash,
            "source": "image_data",
            "bytes": len(blob),
            "ephemeral": True,
        }

    # 2) filesystem path
    path = (image_path or artifact_ref or source_uri or "").strip()
    if not path:
        return {
            "ok": False,
            "error": "MISSING_IMAGE",
            "message": "Provide image_path (host path) or image_data (base64, ≤2MB).",
        }
    p = Path(path)
    if not p.is_file():
        return {
            "ok": False,
            "error": "IMAGE_NOT_FOUND",
            "message": f"image_path not found on server: {path}",
            "path": path,
        }
    try:
        data = p.read_bytes()
        input_hash = _sha256_bytes(data)
    except Exception as exc:
        return {
            "ok": False,
            "error": "IMAGE_READ_FAILED",
            "message": str(exc),
            "path": path,
        }
    return {
        "ok": True,
        "path": str(p),
        "input_hash": input_hash,
        "source": "image_path",
        "bytes": len(data),
        "ephemeral": False,
    }


def _stamp_qualified(
    result: dict[str, Any],
    mode: str,
    transport: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result.setdefault("tool", "geox_seismic_interpret")
    result["mode"] = mode
    result["local_verdict"] = "QUALIFIED_CANDIDATE"
    result["seal_authority"] = "arifOS_only"
    gov = result.get("governance_status") or result.get("governance", {})
    if gov == "SEAL" or (isinstance(gov, dict) and gov.get("status") == "SEAL"):
        result["governance_status"] = "QUALIFY"
        result["governance_note"] = "Local SEAL remapped to QUALIFY — arifOS seals only"
    # RSI may return verdict PARTIAL — map transport language
    if result.get("verdict") == "SEAL":
        result["verdict"] = "PARTIAL"
    # Envelope fields that help outputSchema / clients without changing geology
    result.setdefault("status", "OK" if result.get("ok", True) else "HOLD")
    if result.get("preferred_hypothesis") is not False:
        result.setdefault("preferred_hypothesis", None)
    result.setdefault("claim_tag", "HYPOTHESIS")
    # Inject declared MCP transport metadata into provenance so callers can
    # correlate response → call. Only non-None fields are stamped (avoids
    # # stamping None and overwriting existing provenance).
    if transport:
        prov = result.setdefault("provenance", {})
        if isinstance(prov, dict):
            for k, v in transport.items():
                if v is not None:
                    prov.setdefault(k, v)
    return _json_safe(result)


async def geox_seismic_interpret(
    mode: str = "horizon_contrast",
    # ── horizon_contrast inputs ──
    attribute_data: dict[str, list[float]] | None = None,
    depth: list[float] | None = None,
    geological_query: str = "sequence_boundary",
    well_ties: dict[str, float] | None = None,
    stratigraphic_framework: str = "ABKSS",
    peak_threshold: float = 1.5,
    min_separation_m: float = 20.0,
    custom_query: dict[str, float] | None = None,
    closure_grid: list[dict[str, Any]] | None = None,
    # ── fault_sticks / volume / blend ──
    source_uri: str = "",
    source_type: str = "csv",
    action: str = "get",
    volume_ref: str = "",
    frame_index: int = 0,
    orientation: str = "inline",
    provenance: str = "fixture",
    image_data: str | None = None,
    blend_mode: str = "alpha",
    # ── section / RSI / structure / SEG-Y ──
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
    # ── MCP transport envelope (declared in TransportAwareRequest) ──
    # Must be explicit on the handler signature so they actually flow
    # through to provenance. FastMCP rejects **kwargs on tools, so each
    # transport field is declared by name. The schema layer (extra=forbid
    # + TransportAwareRequest) guarantees typos here trip loudly.
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
    source_sha256: str | None = None,
    # ── legacy ──
    horizon_query: str = "unconformity",
    threshold: float = 0.5,
    confidence_cap: float = 0.9,
    cube_ref: str | None = None,
    volume_inline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Unified seismic interpretation — public modes.

    Local engine verdicts are QUALIFIED_CANDIDATE at most — arifOS seals.
    preferred_hypothesis is never set by GEOX.

    Transport metadata (session_id, actor_id, trace_id, source_sha256) is
    declared on the schema (TransportAwareRequest) AND on this signature,
    so it survives both validation and dispatch.
    """
    # Inject transport into a single dict we propagate everywhere
    _transport: dict[str, Any] = {
        "session_id": session_id,
        "actor_id": actor_id,
        "trace_id": trace_id,
        "source_sha256": source_sha256,
    }
    mode_norm = (mode or "horizon_contrast").strip().lower()
    requested_mode = mode_norm

    if mode_norm == "contrast":
        mode_norm = "horizon_contrast"
    if mode_norm in ("section_image", "classical_section"):
        # classical_section / section_image → interpret_section (image-first propose)
        mode_norm = "interpret_section"
    if mode_norm == "segy_2d":
        mode_norm = "segy_slice"
    if mode_norm == "cutoff_throw":
        mode_norm = "measure_throw"

    # ── F1 zen: track_horizon ──
    if mode_norm == "track_horizon":
        from geox_mcp.tools.seismic_zen_f1 import zen_track_horizon

        result = await zen_track_horizon(
            image_path=image_path or artifact_ref or source_uri or None,
            amplitude_grid=(request or {}).get("amplitude_grid") if isinstance(request, dict) else None,
            volume_inline=volume_inline,
            max_horizons=max_horizons,
            seed_rows=(request or {}).get("seed_rows") if isinstance(request, dict) else None,
            provenance=provenance or "fixture",
            request=request,
        )
        return _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm, _transport)

    # ── F1 zen: measure_throw → optional structure_validate ──
    if mode_norm == "measure_throw":
        from geox_mcp.tools.seismic_zen_f1 import zen_measure_throw

        result = await zen_measure_throw(
            horizons=horizons,
            faults=faults,
            image_path=image_path or artifact_ref or source_uri or None,
            amplitude_grid=(request or {}).get("amplitude_grid") if isinstance(request, dict) else None,
            volume_inline=volume_inline,
            max_horizons=max_horizons,
            calibration=calibration,
            request=request,
            provenance=provenance or "fixture",
            run_gates=bool((request or {}).get("run_gates", True)) if isinstance(request, dict) else True,
        )
        return _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm, _transport)

    if mode_norm in _NOT_YET_MODES and mode_norm not in _LIVE_MODES:
        return {
            "ok": False,
            "tool": "geox_seismic_interpret",
            "mode": mode,
            "error": "MODE_NOT_PUBLIC",
            "message": _NOT_YET_MODES[mode_norm],
            "live_modes": sorted(_LIVE_MODES),
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
            "claim_tag": "HYPOTHESIS",
            "hint": "Use live_modes only.",
        }

    if mode_norm not in _LIVE_MODES:
        return {
            "ok": False,
            "tool": "geox_seismic_interpret",
            "mode": mode,
            "error": "UNKNOWN_MODE",
            "message": f"Unknown mode '{mode}'. Live: {sorted(_LIVE_MODES)}",
            "live_modes": sorted(_LIVE_MODES),
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
        }

    # ── render: deterministic section overlay (human loop) ──
    if mode_norm == "render":
        from geox_mcp.tools.section_render import geox_section_render as _render

        resolved_path = image_path or artifact_ref or source_uri or None
        if image_data and not resolved_path:
            ri = _resolve_image_input(image_data=image_data)
            if ri.get("ok"):
                resolved_path = ri.get("path")
        title = "GEOX section · QUALIFIED_CANDIDATE"
        hyp_id = None
        out_path = None
        if isinstance(request, dict):
            title = str(request.get("title") or title)
            hyp_id = request.get("hypothesis_id")
            out_path = request.get("output_path")
        result = await _render(
            image_path=resolved_path,
            faults=faults,
            horizons=horizons,
            framework=framework,
            annotations=(request or {}).get("annotations") if isinstance(request, dict) else None,
            title=title,
            receipt_hash=(request or {}).get("receipt_hash") if isinstance(request, dict) else None,
            hypothesis_id=hyp_id,
            output_path=out_path,
            calibration=calibration,
        )
        return _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm, transport=_transport)

    # ── structure_validate ──
    if mode_norm == "structure_validate":
        from geox_mcp.tools.structure_validate import geox_structure_validate as _impl
        from geox_mcp.tools.section_render import compact_gate_summary

        hyp_n = 3
        if isinstance(request, dict) and request.get("hypothesis_count"):
            hyp_n = int(request["hypothesis_count"])
        result = await _impl(
            framework=framework,
            faults=faults,
            horizons=horizons,
            measurement_context=measurement_context,
            calibration=calibration,
            earth_constraints=earth_constraints,
            emit_bundle=emit_bundle,
            hypothesis_count=hyp_n,
        )
        stamped = _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm, transport=_transport)
        stamped["preferred_hypothesis"] = None
        # Zen compact summary (full gates still available under "gates" unless detail=compact_only)
        if isinstance(stamped, dict) and stamped.get("gates"):
            stamped["gate_summary"] = compact_gate_summary(stamped["gates"])
            detail = "full"
            if isinstance(request, dict):
                detail = str(request.get("detail") or "full").lower()
            if detail in ("compact", "summary", "zen"):
                stamped["gates_detail"] = stamped.pop("gates")
                stamped["gates"] = stamped["gate_summary"]["gates"]
        return stamped

    # ── interpret_section (aliases: section_image, classical_section) ──
    # A1: must NEVER fall through to horizon_contrast default.
    if mode_norm == "interpret_section":
        resolved = _resolve_image_input(
            image_path=image_path,
            image_data=image_data,
            artifact_ref=artifact_ref,
            source_uri=source_uri,
        )
        if not resolved.get("ok"):
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "interpret_section",
                "requested_mode": requested_mode,
                "error": resolved.get("error") or "MISSING_IMAGE",
                "message": resolved.get("message")
                or "interpret_section requires image_path or image_data (base64).",
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "input_class": "image_only",
                "epistemic_label": "INT_SEISMIC",
            }
        path = resolved["path"]
        input_hash = resolved.get("input_hash")
        from geox_mcp.tools.classical_section_propose import geox_classical_section_propose as _cv

        cal = dict(calibration or {"input_class": "image_only", "calibrated": False})
        cal.setdefault("input_class", "image_only")
        if input_hash:
            cal["sha256"] = input_hash
        result = await _cv(
            image_path=path,
            max_faults=max_faults,
            max_horizons=max_horizons,
            run_gates=False,  # gates on mode=interpret / structure_validate only
            calibration=cal,
        )
        if not isinstance(result, dict):
            result = {"data": result}
        result["input_hash"] = input_hash
        result["image_source"] = resolved.get("source")
        if emit_bundle and result.get("framework") and not result.get("interpretation_bundle"):
            from geox_mcp.domain.seismic_interpret.bundle import build_interpretation_bundle

            result["interpretation_bundle"] = build_interpretation_bundle(
                frameworks_or_primary=result["framework"],
                observations=result.get("observations"),
                calibration=cal,
                request=request or {"hypothesis_count": 3},
                model_revision="classical_section_v1",
            )
            result["preferred_hypothesis"] = None
            # ensure provenance.input_hash
            ib = result.get("interpretation_bundle")
            if isinstance(ib, dict):
                prov = ib.setdefault("provenance", {})
                if isinstance(prov, dict) and input_hash:
                    prov["input_hash"] = input_hash
                    if cal.get("calibration_hash") or cal.get("sha256"):
                        prov.setdefault("calibration_hash", cal.get("calibration_hash") or cal.get("sha256"))
        # Preserve caller's mode name when alias (classical_section / section_image)
        stamp_mode = (
            requested_mode
            if requested_mode in ("interpret_section", "classical_section", "section_image")
            else "interpret_section"
        )
        stamped = _stamp_qualified(result, stamp_mode, transport=_transport)
        stamped["requested_mode"] = requested_mode
        stamped["resolved_mode"] = "interpret_section"
        return stamped

    # ── interpret: classical propose (if image) → validate → compare ──
    if mode_norm == "interpret":
        from geox_mcp.domain.seismic_interpret.bundle import build_interpretation_bundle
        from geox_mcp.tools.structure_validate import geox_structure_validate as _sv

        fw: dict[str, Any] = dict(framework or {})
        if faults is not None:
            fw["faults"] = faults
        if horizons is not None:
            fw["horizons"] = horizons
        propose_result = None
        input_hash = None
        has_image = bool(image_data or image_path or artifact_ref or source_uri)
        if has_image and not fw.get("faults") and not fw.get("horizons"):
            resolved = _resolve_image_input(
                image_path=image_path,
                image_data=image_data,
                artifact_ref=artifact_ref,
                source_uri=source_uri,
            )
            if not resolved.get("ok"):
                return {
                    "ok": False,
                    "tool": "geox_seismic_interpret",
                    "mode": "interpret",
                    "error": resolved.get("error"),
                    "message": resolved.get("message"),
                    "governance_status": "HOLD",
                    "local_verdict": "QUALIFIED_CANDIDATE",
                }
            path = resolved["path"]
            input_hash = resolved.get("input_hash")
            from geox_mcp.tools.classical_section_propose import (
                geox_classical_section_propose as _cv,
            )

            cal_prop = dict(calibration or {"input_class": "image_only", "calibrated": False})
            if input_hash:
                cal_prop["sha256"] = input_hash
            propose_result = await _cv(
                image_path=path,
                max_faults=max_faults,
                max_horizons=max_horizons,
                run_gates=False,
                calibration=cal_prop,
            )
            if isinstance(propose_result, dict) and propose_result.get("framework"):
                pf = propose_result["framework"]
                fw.setdefault("faults", pf.get("faults") or [])
                fw.setdefault("horizons", pf.get("horizons") or [])
                if pf.get("measurement_context"):
                    fw.setdefault("measurement_context", pf["measurement_context"])
        # Framework-only path: still run gates with calibration derive
        cal = dict(
            calibration
            or {
                "input_class": "image_only" if has_image else "unknown",
                "calibrated": bool(calibration and (
                    calibration.get("bin_spacing_m")
                    or calibration.get("vertical_exaggeration")
                    or calibration.get("velocity_td")
                    or calibration.get("velocity_linear_m_s")
                )),
            }
        )
        if input_hash:
            cal["sha256"] = input_hash
        if fw.get("faults") or fw.get("horizons") or fw.get("velocity"):
            from geox_mcp.tools.section_render import compact_gate_summary, geox_section_render

            sv = await _sv(
                framework=fw,
                measurement_context=measurement_context or fw.get("measurement_context"),
                calibration=cal,
                earth_constraints=earth_constraints,
                emit_bundle=True,
                hypothesis_count=int((request or {}).get("hypothesis_count") or 3),
            )
            bundle = sv.get("interpretation_bundle") or sv
            if isinstance(bundle, dict):
                prov = bundle.setdefault("provenance", {})
                if isinstance(prov, dict):
                    if input_hash:
                        prov["input_hash"] = input_hash
                    ch = cal.get("calibration_hash") or cal.get("sha256")
                    if ch:
                        prov.setdefault("calibration_hash", ch)

            gates = sv.get("gates") or {}
            gsum = compact_gate_summary(gates)

            # Auto-render primary hypothesis for human loop (skip if request.render=false)
            render_info = None
            do_render = True
            if isinstance(request, dict) and request.get("render") is False:
                do_render = False
            if do_render and (fw.get("faults") or fw.get("horizons")):
                try:
                    # Prefer image from propose / caller
                    rpath = image_path or artifact_ref or source_uri
                    if image_data and not rpath:
                        ri = _resolve_image_input(image_data=image_data)
                        if ri.get("ok"):
                            rpath = ri.get("path")
                            input_hash = input_hash or ri.get("input_hash")
                    # Also try classical propose path image
                    if not rpath and isinstance(propose_result, dict):
                        rpath = (propose_result.get("image_path") or propose_result.get("stages", {}).get("R0_reality_gate", {}).get("image_path"))
                    rh = None
                    if gates:
                        # first gate receipt as stamp seed
                        for g in gates.values():
                            if isinstance(g, dict) and g.get("receipt_hash"):
                                rh = g["receipt_hash"]
                                break
                    render_info = await geox_section_render(
                        image_path=rpath,
                        framework=fw,
                        title="GEOX interpret · HYP-001 · QUALIFIED_CANDIDATE",
                        receipt_hash=rh,
                        hypothesis_id="HYP-001",
                        calibration=cal,
                    )
                except Exception as exc:
                    render_info = {"ok": False, "error": "RENDER_FAILED", "message": str(exc)[:200]}

            from geox_mcp.tools.section_render import compact_interpret_envelope, store_detail_receipt

            verbosity = "compact"
            if isinstance(request, dict):
                verbosity = str(request.get("verbosity") or request.get("detail") or "compact").lower()

            n_hyps = len((bundle or {}).get("hypotheses") or []) if isinstance(bundle, dict) else 3
            render_ref = None
            if render_info and render_info.get("png_path"):
                render_ref = f"geox://artifacts/{Path(render_info['png_path']).name}"

            full_detail = {
                "interpretation_bundle": bundle if isinstance(bundle, dict) else {},
                "structure_validate": {
                    "combined_gate_verdict": sv.get("combined_gate_verdict"),
                    "kills": sv.get("kills"),
                    "passes": sv.get("passes"),
                    "warns": sv.get("warns"),
                    "unmeasured": sv.get("unmeasured"),
                    "gates": gates,
                    "cutoffs": sv.get("cutoffs"),
                },
                "propose": {
                    "ran": propose_result is not None,
                    "method": "classical_section",
                    "n_faults": (propose_result or {}).get("n_faults"),
                    "n_horizons": (propose_result or {}).get("n_horizons"),
                },
                "render": render_info,
                "input_hash": input_hash,
                "calibration": cal,
                "transport": _transport,
            }
            stored = store_detail_receipt(full_detail, prefix="interpret")
            receipt_hash = stored.get("detail_sha256", "")[:16]
            if render_info and render_info.get("receipt_hash"):
                receipt_hash = str(render_info["receipt_hash"])[:16]

            if verbosity in ("full", "verbose", "debug"):
                out_payload = {
                    **(bundle if isinstance(bundle, dict) else {}),
                    "ok": True,
                    "input_hash": input_hash,
                    "gate_summary": gsum,
                    "structure_validate": full_detail["structure_validate"],
                    "propose": full_detail["propose"],
                    "preferred_hypothesis": None,
                    "detail_ref": stored.get("detail_ref"),
                    "receipt_hash": receipt_hash,
                    "render": {
                        "ok": (render_info or {}).get("ok"),
                        "png_path": (render_info or {}).get("png_path"),
                        "png_sha256": (render_info or {}).get("png_sha256"),
                        "receipt_hash": (render_info or {}).get("receipt_hash"),
                        "render_ref": render_ref,
                    }
                    if render_info
                    else None,
                }
            else:
                # P4 progressive disclosure — default ≤2KB-class envelope
                out_payload = compact_interpret_envelope(
                    verdict="QUALIFIED_CANDIDATE",
                    input_class=str(cal.get("input_class") or "image_only"),
                    n_hypotheses=max(n_hyps, 3),
                    gate_summary={
                        "pass": len(gsum.get("passes") or []),
                        "warn": len(gsum.get("warns") or []),
                        "kill": len(gsum.get("kills") or []),
                        "unmeasured": len(gsum.get("unmeasured") or []),
                    },
                    render_ref=render_ref,
                    detail_ref=stored.get("detail_ref"),
                    receipt_hash=receipt_hash,
                    extras={
                        "ok": True,
                        "input_hash": input_hash,
                        "combined_gate_verdict": sv.get("combined_gate_verdict"),
                        "cutoffs_n": len(sv.get("cutoffs") or []),
                    },
                )
            return _stamp_qualified(out_payload, mode_norm, transport=_transport)
        bundle = build_interpretation_bundle(
            propose_result=propose_result if isinstance(propose_result, dict) else None,
            calibration=cal,
            earth_constraints=earth_constraints,
            request=request or {"hypothesis_count": 3},
        )
        if not has_image and not fw:
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "interpret",
                "error": "MISSING_INPUT",
                "message": (
                    "interpret requires framework faults/horizons and/or image_path/image_data."
                ),
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
            }
        if isinstance(bundle, dict) and input_hash:
            prov = bundle.setdefault("provenance", {})
            if isinstance(prov, dict):
                prov["input_hash"] = input_hash
        return _stamp_qualified(bundle, mode_norm, transport=_transport)

    # ── rsi_pipeline: legacy RSI-only (comparator, not primary product) ──
    if mode_norm == "rsi_pipeline":
        resolved = _resolve_image_input(
            image_path=image_path,
            image_data=image_data,
            artifact_ref=artifact_ref,
            source_uri=source_uri,
        )
        if not resolved.get("ok"):
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": mode_norm,
                "error": resolved.get("error") or "MISSING_IMAGE_PATH",
                "message": resolved.get("message")
                or "rsi_pipeline requires image_path or image_data.",
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "input_class": "image_only",
                "epistemic_label": "INT_SEISMIC",
            }
        path = resolved["path"]
        input_hash = resolved.get("input_hash")
        from geox_mcp.tools.seismic_rsi import geox_rsi_interpret as _rsi

        result = await _rsi(
            image_path=path,
            mode="horizon_fault_pick",
            max_faults=max_faults,
            max_horizons=max_horizons,
        )
        if not isinstance(result, dict):
            result = {"data": result}
        result["ok"] = result.get("verdict") not in ("VOID",)
        result["input_class"] = "image_only"
        result["epistemic_label"] = "INT_SEISMIC"
        result["input_hash"] = input_hash
        result["capability_note"] = (
            "Legacy RSI propose (comparator). Prefer mode=interpret_section for product path. "
            "Pixel domain ≠ subsurface. arifOS SEAL only."
        )
        alts = result.get("alternatives")
        if not alts:
            result["alternatives"] = [
                {"model_id": "through_going", "prior": "primary RSI pick set"},
                {"model_id": "relay_segmented", "prior": "faults as relays / hard-linked segments"},
                {"model_id": "artifact_dominant", "prior": "picks dominated by acquisition/processing artifacts"},
            ]
        if emit_bundle:
            from geox_mcp.domain.seismic_interpret.bundle import build_interpretation_bundle

            cal = dict(calibration or {"input_class": "image_only", "calibrated": False})
            if input_hash:
                cal["sha256"] = input_hash
            result["interpretation_bundle"] = build_interpretation_bundle(
                propose_result=result,
                calibration=cal,
                earth_constraints=earth_constraints,
                request=request or {"hypothesis_count": 3},
            )
            result["preferred_hypothesis"] = None
            ib = result.get("interpretation_bundle")
            if isinstance(ib, dict) and input_hash:
                prov = ib.setdefault("provenance", {})
                if isinstance(prov, dict):
                    prov["input_hash"] = input_hash
        return _stamp_qualified(result, mode_norm, transport=_transport)

    # ── segy_slice ──
    if mode_norm == "segy_slice":
        path = segy_path or source_uri or volume_ref or cube_ref or ""
        if not path:
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "segy_slice",
                "error": "MISSING_SEGY_PATH",
                "message": "segy_slice requires segy_path or source_uri to a SEG-Y file.",
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
            }
        from geox_mcp.tools.seismic_segy_slice import geox_segy_slice as _segy

        result = await _segy(
            segy_path=path,
            frame_index=frame_index or 0,
            orientation=orientation or "inline",
        )
        return _stamp_qualified(result if isinstance(result, dict) else {"data": result}, mode_norm, transport=_transport)

    if mode_norm == "fault_sticks":
        from geox_mcp.tools.paleoscan_forge import geox_fault_stick_ingest_tool as _impl

        return await _impl(source_uri=source_uri or "", source_type=source_type or "csv")

    if mode_norm == "volume_frame":
        from geox_mcp.tools.paleoscan_forge import geox_volume_frame_tool as _impl

        if not (volume_ref or "").strip():
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "volume_frame",
                "error": "MISSING_REQUIRED_FIELD",
                "message": "volume_frame requires volume_ref (ingested seismic volume artifact id).",
                "required_params": ["volume_ref"],
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "claim_tag": "VOID",
            }
        return await _impl(
            action=action or "get",
            volume_ref=volume_ref or "",
            frame_index=frame_index or 0,
            orientation=orientation or "inline",
            provenance=provenance or "fixture",
            image_data=image_data,
        )

    if mode_norm == "blend":
        from geox_mcp.tools.paleoscan_forge import geox_blend_volume_tool as _impl

        # Contract: alpha needs volume_ref_1+2; RGB needs red/green/blue refs.
        # Do not pass a single volume_ref (TypeError + silent mis-dispatch).
        if not volume_ref and not (request and isinstance(request, dict)):
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "blend",
                "error": "MISSING_REQUIRED_FIELD",
                "message": (
                    "blend requires volume refs: alpha → volume_ref_1+volume_ref_2 "
                    "(pass via request={...}); RGB → volume_ref_red/green/blue."
                ),
                "required_params": ["volume_ref_1", "volume_ref_2"],
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "claim_tag": "VOID",
            }
        blend_kwargs: dict[str, Any] = {"blend_mode": blend_mode or "alpha"}
        if isinstance(request, dict):
            for k in (
                "volume_ref_1",
                "volume_ref_2",
                "volume_ref_3",
                "volume_ref_red",
                "volume_ref_green",
                "volume_ref_blue",
                "alpha",
            ):
                if k in request:
                    blend_kwargs[k] = request[k]
        # legacy single volume_ref is insufficient — still declare contract
        if not any(blend_kwargs.get(k) for k in ("volume_ref_1", "volume_ref_red")):
            return {
                "ok": False,
                "tool": "geox_seismic_interpret",
                "mode": "blend",
                "error": "MISSING_REQUIRED_FIELD",
                "message": "blend missing volume_ref_1/volume_ref_2 (or RGB refs) in request.",
                "required_params": ["volume_ref_1", "volume_ref_2"],
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "claim_tag": "VOID",
            }
        return await _impl(**blend_kwargs)

    # ── horizon_contrast only — A1: never silent default for other live modes ──
    if mode_norm != "horizon_contrast":
        # Live mode declared but no handler branch above → hard fail (not remap)
        return {
            "ok": False,
            "tool": "geox_seismic_interpret",
            "mode": mode_norm,
            "requested_mode": requested_mode,
            "error": "MODE_HANDLER_MISSING",
            "message": (
                f"Mode '{mode_norm}' is live but no handler executed. "
                "This is a server bug — do not silently fall back to horizon_contrast."
            ),
            "live_modes": sorted(_LIVE_MODES),
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
        }

    attrs = attribute_data
    depths = depth
    if volume_inline and isinstance(volume_inline, dict):
        attrs = attrs or volume_inline.get("attribute_data")
        depths = depths or volume_inline.get("depth")
        if well_ties is None:
            well_ties = volume_inline.get("well_ties")
        if not geological_query or geological_query == "sequence_boundary":
            geological_query = volume_inline.get("geological_query") or geological_query

    if not attrs or not depths:
        return {
            "ok": False,
            "tool": "geox_seismic_interpret",
            "mode": "horizon_contrast",
            "error": "MISSING_REQUIRED_FIELD",
            "message": (
                "horizon_contrast requires attribute_data (dict attr→array) and depth (list[float]). "
                "This is a 1D multi-attribute boundary detector — not a 2D section picker."
            ),
            "required_params": ["attribute_data", "depth"],
            "live_modes": sorted(_LIVE_MODES),
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
            "hint": (
                "Use mode=interpret_section / interpret for 2D section images; "
                "mode=structure_validate for framework gates; "
                "or pass attribute_data+depth for 1D contrast."
            ),
        }

    attrs = dict(attrs)
    if "amplitude" in attrs and "seismic_amplitude" not in attrs and "acoustic_impedance" not in attrs:
        vals = attrs["amplitude"]
        try:
            mx = max(abs(float(v)) for v in vals if v is not None)
        except Exception:
            mx = 0.0
        if mx > 100.0:
            attrs["acoustic_impedance"] = attrs.pop("amplitude")
        else:
            attrs["seismic_amplitude"] = attrs.pop("amplitude")

    from geox_mcp.tools.horizon_contrast import geox_horizon_contrast_surface as _impl

    gq = geological_query or horizon_query or "sequence_boundary"
    if horizon_query and geological_query == "sequence_boundary" and horizon_query != "unconformity":
        gq = geological_query if geological_query != "sequence_boundary" else horizon_query

    result = await _impl(
        attribute_data=attrs,
        depth=list(depths),
        mode="full",
        geological_query=gq,
        well_ties=well_ties,
        stratigraphic_framework=stratigraphic_framework,
        peak_threshold=peak_threshold if peak_threshold else threshold,
        min_separation_m=min_separation_m,
        custom_query=custom_query,
        closure_grid=closure_grid,
    )

    if isinstance(result, dict):
        result = _stamp_qualified(result, "horizon_contrast", transport=_transport)
        result["capability_note"] = (
            "1D multi-attribute boundary detector. Not HorizonSurface3D. "
            "Not structural framework. Agent proposes; GEOX assists; Arif seals."
        )
    return result
