"""GEOX Observability — stdlib-only telemetry decorator & summary (Phase B)."""
from __future__ import annotations

import functools
import hashlib
import inspect
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

LIFECYCLE_STAGES: dict[str, str] = {
    "geox_basin": "Exploration", "geox_deep_time": "Exploration", "geox_map": "Exploration",
    "geox_spatial": "Exploration", "geox_seismic_ingest": "Exploration",
    "geox_seismic_interpret": "Exploration", "geox_seismic_compute": "Exploration",
    "geox_contrast_metabolize": "Exploration", "geox_source": "Exploration",
    "geox_observe": "Exploration", "geox_paleobiodb_query": "Exploration",
    "geox_prospect": "Exploration", "geox_glof": "Exploration",
    "geox_well_ingest": "Appraisal", "geox_well_qc": "Appraisal",
    "geox_petrophysics": "Appraisal", "geox_geomechanics": "Appraisal",
    "geox_grid": "Development", "geox_resqml_io": "Development",
    "geox_model": "Development", "geox_well": "Development",
    "geox_temporal": "Production",
    "geox_surface_status": "Cross-cutting", "geox_claim": "Cross-cutting",
    "geox_calibration_register_witness": "Cross-cutting",
    "geox_extract_display_proxy": "Cross-cutting",
    "geox_register_native_source": "Cross-cutting",
    "geox_extract_native_trace": "Cross-cutting",
    "geox_list_registered_sources": "Cross-cutting",
}

_GIT_SHA_CACHE: str | None = None


def telemetry_path() -> Path:
    return Path(os.getenv("GEOX_TELEMETRY_PATH") or (Path.home() / ".geox" / "telemetry.jsonl"))


def current_git_sha(repo_dir: Path | None = None) -> str:
    global _GIT_SHA_CACHE
    if _GIT_SHA_CACHE is not None and repo_dir is None:
        return _GIT_SHA_CACHE
    cwd = str(repo_dir or Path(__file__).resolve().parents[2])
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=cwd, timeout=3).decode().strip()
    except Exception:
        sha = "unknown"
    if repo_dir is None:
        _GIT_SHA_CACHE = sha
    return sha


def lifecycle_stage_for(tool: str, fallback: str = "unmapped") -> str:
    return LIFECYCLE_STAGES.get(tool, fallback)


def _sha256_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, default=str, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _emit(record: dict[str, Any]) -> None:
    try:
        p = telemetry_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _record(tool: str, stage: str, mode: str | None, sha_in: str, t0: float, res: Any, exc: BaseException | None) -> dict[str, Any]:
    raw = json.dumps(res if exc is None else {"error": str(exc)}, default=str, ensure_ascii=False).encode("utf-8")
    is_err = exc is not None or (isinstance(res, dict) and bool(res.get("isError")))
    verdict = "ERROR" if is_err else (str(res.get("verdict", "OK")) if isinstance(res, dict) else "OK")
    defaults = res.get("defaults_applied") if isinstance(res, dict) else None
    return {
        "ts": datetime.now(UTC).isoformat(), "tool": tool, "mode": mode or "",
        "lifecycle_stage": stage, "git_sha": current_git_sha(),
        "duration_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        "resp_tokens_est": max(1, len(raw) // 4), "resp_bytes": len(raw),
        "verdict": verdict, "defaults_applied_n": len(defaults) if isinstance(defaults, list) else 0,
        "sha256_in": sha_in, "sha256_out": hashlib.sha256(raw).hexdigest(), "is_error": is_err,
    }


def observed(stage: str | None = None, *, tool_name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator emitting one JSONL telemetry record per tool call."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        name, resolved = tool_name or getattr(fn, "__name__", "unknown"), stage or lifecycle_stage_for(tool_name or getattr(fn, "__name__", "unknown"))
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def _awrap(*args: Any, **kwargs: Any) -> Any:
                t0, sha_in = time.perf_counter(), _sha256_json({"args": args, "kwargs": kwargs})
                mode = str(kwargs["mode"]) if kwargs.get("mode") is not None else None
                try:
                    res = await fn(*args, **kwargs)
                    _emit(_record(name, resolved, mode, sha_in, t0, res, None))
                    return res
                except BaseException as exc:
                    _emit(_record(name, resolved, mode, sha_in, t0, None, exc))
                    raise
            return _awrap
        @functools.wraps(fn)
        def _swrap(*args: Any, **kwargs: Any) -> Any:
            t0, sha_in = time.perf_counter(), _sha256_json({"args": args, "kwargs": kwargs})
            mode = str(kwargs["mode"]) if kwargs.get("mode") is not None else None
            try:
                res = fn(*args, **kwargs)
                _emit(_record(name, resolved, mode, sha_in, t0, res, None))
                return res
            except BaseException as exc:
                _emit(_record(name, resolved, mode, sha_in, t0, None, exc))
                raise
        return _swrap
    return decorator


def summarize_telemetry(path: Path | None = None, window: int = 500) -> dict[str, Any]:
    """Compute p50/p95 latency, avg resp_tokens, and error rate per lifecycle stage."""
    p, rows = path or telemetry_path(), []
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines()[-window:]:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    if not rows:
        return {"count": 0, "p50_ms": 0.0, "p95_ms": 0.0, "avg_resp_tokens": 0.0, "error_rate_by_stage": {}}
    durs = sorted(float(r.get("duration_ms", 0.0)) for r in rows)
    toks = [float(r.get("resp_tokens_est", 0.0)) for r in rows]
    by_stage: dict[str, list[bool]] = {}
    for r in rows:
        by_stage.setdefault(str(r.get("lifecycle_stage", "unmapped")), []).append(bool(r.get("is_error")))
    n = len(durs)
    return {
        "count": n, "p50_ms": round(durs[int(0.50 * (n - 1))], 2), "p95_ms": round(durs[int(0.95 * (n - 1))], 2),
        "avg_resp_tokens": round(sum(toks) / n, 1),
        "error_rate_by_stage": {s: round(sum(v) / len(v), 4) for s, v in sorted(by_stage.items())},
    }
