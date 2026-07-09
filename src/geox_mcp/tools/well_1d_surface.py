"""
GEOX 1D MCP surface — Orthogonal Base calibration tools.

  geox_well_time_depth_calibrate
  geox_well_seismic_mistie_rms
  geox_wavelet_extract_least_squares

JSON-only boundary. EGS resource URIs under geox://well/...

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import csv
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np

from geox_core.schemas.geox_1d_mcp import (
    MistieResultMCP,
    TDFitResultMCP,
    VaultReceiptLite,
    WaveletResultMCP,
    as_float_list,
)

# Receipt store (filesystem EGS lite — not VAULT999 seal)
_EGS_DIR = Path("/root/geox/data/egs/receipts")
MethodArg = Literal["linear", "polynomial", "vo_k", "layer_cake"]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _persist_receipt(kind: str, well_id: str, payload: dict[str, Any]) -> str:
    """Write JSON receipt; return geox:// URI."""
    _EGS_DIR.mkdir(parents=True, exist_ok=True)
    rid = uuid.uuid4().hex[:12]
    safe_well = well_id.replace("/", "_").replace(" ", "_")
    fname = f"{safe_well}_{kind}_{rid}.json"
    path = _EGS_DIR / fname
    path.write_text(json.dumps(payload, indent=2, default=str))
    uri = f"geox://well/{safe_well}/{kind}/{rid}"
    # sidecar map for uri → path
    index = _EGS_DIR / "index.jsonl"
    with index.open("a") as f:
        f.write(json.dumps({"uri": uri, "path": str(path), "ts": _now()}) + "\n")
    return uri


def _load_checkshot(path: str | Path) -> list[dict[str, float]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"checkshot not found: {p}")
    if p.suffix.lower() == ".json":
        raw = json.loads(p.read_text())
        if not isinstance(raw, list):
            raise ValueError("checkshot JSON must be a list")
        out: list[dict[str, float]] = []
        for r in raw:
            if isinstance(r, dict):
                out.append(
                    {
                        "depth_md": float(r.get("depth_md", r.get("depth", 0))),
                        "twt_ms": float(r.get("twt_ms", r.get("twt", 0))),
                    }
                )
            elif isinstance(r, (list, tuple)) and len(r) >= 2:
                out.append({"depth_md": float(r[0]), "twt_ms": float(r[1])})
        return out
    # CSV
    rows: list[dict[str, float]] = []
    with p.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            # flexible headers
            d = row.get("depth_m") or row.get("depth_md") or row.get("depth") or row.get("DEPTH")
            t = row.get("twt_ms") or row.get("twt") or row.get("TWT")
            if d is None or t is None:
                continue
            rows.append({"depth_md": float(d), "twt_ms": float(t)})
    if len(rows) < 2:
        raise ValueError(f"checkshot has < 2 points: {p}")
    return rows


def _load_las_depth(path: str | Path) -> np.ndarray:
    """Minimal depth column from LAS ~A section."""
    lines = Path(path).read_text(errors="replace").splitlines()
    in_a = False
    depths: list[float] = []
    for line in lines:
        if line.startswith("~A"):
            in_a = True
            continue
        if not in_a or not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        try:
            depths.append(float(parts[0]))
        except (ValueError, IndexError):
            continue
    if len(depths) < 2:
        raise ValueError(f"LAS depth parse failed: {path}")
    return np.asarray(depths, dtype=float)


async def geox_well_time_depth_calibrate(
    las_path: str,
    checkshot_path: str,
    method: MethodArg = "linear",
    velocity_bounds: list[float] | None = None,
    residual_threshold_pct: float = 10.0,
    well_id: str = "",
    actor_id: str = "geox_1d_mcp",
) -> dict[str, Any]:
    """Calibrate time–depth using LAS depth grid + checkshot (PhysicsGuard).

    Wraps geox_core.physics.td_methods.fit_td. Returns TDFitResultMCP JSON.
    """
    from geox_core.physics.td_methods import fit_td

    try:
        depth = _load_las_depth(las_path)
        checkshot = _load_checkshot(checkshot_path)
        method_map = {
            "linear": "linear",
            "polynomial": "polynomial",
            "vo_k": "vo_k",
            "vok": "vo_k",
            "layer_cake": "layer_cake",
            "layercake": "layer_cake",
        }
        m = method_map.get(str(method).lower(), str(method))
        result = fit_td(m, checkshot, depth)
        d = result.to_dict() if hasattr(result, "to_dict") else dict(result)

        # residual threshold check vs RMSE / mean |twt|
        twt = np.asarray(d.get("twt_ms") or [], dtype=float)
        rmse = float(d.get("rmse_ms") or 0.0)
        scale = float(np.nanmean(np.abs(twt))) if len(twt) else 1.0
        residual_pct = 100.0 * rmse / max(scale, 1e-6)
        residual_ok = residual_pct <= residual_threshold_pct

        # optional velocity bounds note (interval vel from checkshot)
        if velocity_bounds and len(velocity_bounds) == 2:
            d.setdefault("physics_guard", {})["velocity_bounds_requested"] = list(velocity_bounds)

        well = well_id or Path(las_path).stem
        rid = uuid.uuid4().hex[:12]
        uri = f"geox://well/{well}/tdfit/{m}_{rid}"
        receipt = VaultReceiptLite(
            receipt_id=rid,
            tool="geox_well_time_depth_calibrate",
            actor=actor_id,
            verdict="HOLD" if d.get("fail_closed") or not residual_ok else "SEAL",
            resource_uri=uri,
            timestamp_utc=_now(),
        )
        envelope = TDFitResultMCP(
            method=str(d.get("method", m)),
            equation=str(d.get("equation", "")),
            coefficients=as_float_list(d.get("coefficients")),
            twt_ms=as_float_list(d.get("twt_ms")),
            residuals_ms=as_float_list(d.get("residuals_ms")),
            rmse_ms=rmse,
            physics_guard=dict(d.get("physics_guard") or {}),
            extrapolation_risk=float(d.get("extrapolation_risk") or 0.0),
            fail_closed=bool(d.get("fail_closed")),
            residual_threshold_pct=residual_threshold_pct,
            residual_ok=residual_ok,
            vault_receipt=receipt,
            resource_uri=uri,
        )
        payload = envelope.model_dump()
        payload["resource_uri"] = _persist_receipt("tdfit", well, payload)
        if payload.get("vault_receipt"):
            payload["vault_receipt"]["resource_uri"] = payload["resource_uri"]
        return {
            "status": "success",
            "tool": "geox_well_time_depth_calibrate",
            "result": payload,
            "claim_state": "DERIVED",
            "perception_class": "DERIVED",
        }
    except Exception as e:
        return {
            "status": "error",
            "tool": "geox_well_time_depth_calibrate",
            "error": str(e),
            "result": None,
        }


async def geox_well_seismic_mistie_rms(
    synthetic_trace: list[float],
    seismic_trace: list[float],
    dt_ms: float = 4.0,
    time_window_ms: list[float] | None = None,
    threshold_ms: float = 25.0,
    max_lag_ms: float = 50.0,
    intervals: list[dict[str, Any]] | None = None,
    well_id: str = "WELL",
    actor_id: str = "geox_1d_mcp",
) -> dict[str, Any]:
    """Phase 3 falsification gate: RMS mistie synthetic vs seismic.

    Hard gate default 25 ms → SEAL | HOLD | VOID.
    """
    from geox_core.engines.seismic.mistie_engine import compute_mistie_rms

    try:
        window = None
        if time_window_ms and len(time_window_ms) >= 2:
            window = (float(time_window_ms[0]), float(time_window_ms[1]))
        raw = compute_mistie_rms(
            np.asarray(synthetic_trace, dtype=float),
            np.asarray(seismic_trace, dtype=float),
            dt_ms=float(dt_ms),
            time_window_ms=window,
            threshold_ms=float(threshold_ms),
            max_lag_ms=float(max_lag_ms),
            intervals=intervals,
        )
        verdict = str(raw.get("verdict", "VOID"))
        if verdict not in ("SEAL", "HOLD", "VOID"):
            verdict = "HOLD"
        rid = uuid.uuid4().hex[:12]
        uri = f"geox://well/{well_id}/mistie/{rid}"
        receipt = VaultReceiptLite(
            receipt_id=rid,
            tool="geox_well_seismic_mistie_rms",
            actor=actor_id,
            threshold_ms=float(threshold_ms),
            verdict=verdict,
            resource_uri=uri,
            timestamp_utc=_now(),
        )
        envelope = MistieResultMCP(
            optimal_lag_ms=float(raw.get("optimal_lag_ms") or 0.0),
            rms_mistie_ms=float(raw.get("rms_mistie_ms") or 0.0)
            if np.isfinite(float(raw.get("rms_mistie_ms") or 0))
            else 1e9,
            correlation_coefficient=float(raw.get("correlation_coefficient") or 0.0),
            residual_rms_normalized=raw.get("residual_rms_normalized"),
            verdict=verdict,  # type: ignore[arg-type]
            threshold_used_ms=float(raw.get("threshold_used_ms") or threshold_ms),
            verdict_reason=str(raw.get("verdict_reason") or ""),
            residual_class=str(raw.get("residual_class") or ""),
            residual_description=str(raw.get("residual_description") or ""),
            per_interval_mistie=list(raw.get("per_interval") or []),
            physics_guard=dict(raw.get("physics_guard") or {}),
            anti_hantu_flags=list(raw.get("anti_hantu_flags") or []),
            vault_receipt=receipt,
            resource_uri=uri,
        )
        payload = envelope.model_dump()
        # fix non-finite for JSON
        if not np.isfinite(payload["rms_mistie_ms"]):
            payload["rms_mistie_ms"] = 1e9
        payload["resource_uri"] = _persist_receipt("mistie", well_id, payload)
        return {
            "status": "success",
            "tool": "geox_well_seismic_mistie_rms",
            "result": payload,
            "governance_status": verdict,
            "claim_state": "DERIVED",
        }
    except Exception as e:
        return {
            "status": "error",
            "tool": "geox_well_seismic_mistie_rms",
            "error": str(e),
            "result": None,
        }


async def geox_wavelet_extract_least_squares(
    reflectivity_series: list[float],
    seismic_trace: list[float],
    wavelet_length_ms: float = 120.0,
    epsilon: float = 1e-3,
    dt_ms: float = 4.0,
    well_id: str = "WELL",
    actor_id: str = "geox_1d_mcp",
) -> dict[str, Any]:
    """Phase 4 Wiener least-squares wavelet extraction."""
    from geox_core.engines.seismic.wavelet_extract import extract_wavelet_least_squares

    try:
        raw = extract_wavelet_least_squares(
            reflectivity_series,
            seismic_trace,
            dt_ms=float(dt_ms),
            wavelet_length_ms=float(wavelet_length_ms),
            epsilon=float(epsilon),
        )
        rid = uuid.uuid4().hex[:12]
        uri = f"geox://well/{well_id}/wavelet/{rid}"
        receipt = VaultReceiptLite(
            receipt_id=rid,
            tool="geox_wavelet_extract_least_squares",
            actor=actor_id,
            resource_uri=uri,
            timestamp_utc=_now(),
        )
        envelope = WaveletResultMCP(
            wavelet=list(raw.get("wavelet") or []),
            condition_number=float(raw.get("condition_number") or 0.0),
            epsilon_used=float(raw.get("epsilon_used") or epsilon),
            new_synthetic=list(raw.get("new_synthetic") or []),
            updated_mistie_ms=raw.get("updated_mistie_ms"),
            updated_correlation=raw.get("updated_correlation"),
            phase_class=raw.get("phase_class") or "unknown",  # type: ignore[arg-type]
            wavelet_length_ms=float(raw.get("wavelet_length_ms") or wavelet_length_ms),
            dt_ms=float(raw.get("dt_ms") or dt_ms),
            physics_guard=dict(raw.get("physics_guard") or {}),
            vault_receipt=receipt,
            resource_uri=uri,
        )
        payload = envelope.model_dump()
        payload["resource_uri"] = _persist_receipt("wavelet", well_id, payload)
        return {
            "status": "success",
            "tool": "geox_wavelet_extract_least_squares",
            "result": payload,
            "claim_state": "DERIVED",
        }
    except Exception as e:
        return {
            "status": "error",
            "tool": "geox_wavelet_extract_least_squares",
            "error": str(e),
            "result": None,
        }
