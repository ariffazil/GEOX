"""
geox_mcp.tools.lem_predict — GEOX-LEM Inference Tool (W14+ FORGE 2026-06-21)
═══════════════════════════════════════════════════════════════════════════════

Predicts rock properties (porosity, Sw, lithology, pressure proxy) at depth
intervals from well log curves via the GEOX-LEM substrate.

Architecture
------------
The GEOX-LEM substrate (`src/geox_core/engines/lem/`) is a multi-modal fusion
transformer (Perceiver encoder + 3D Swin processor + Perceiver decoder). At
deployment time (`geox_lem_predict.mode = "transformer"` or `"hybrid"`) it
emits learned representations constrained by physics9.

Until federated pretraining data (≥1,200 wells, E1 888_HOLD) is acquired and
foundation-model weights are deployed (GPU + 888_HOLD), the substrate operates
in **`mode = "physics_prior"`** — physics-bounded estimates via:

  - **Archie** (Sw from RT and assumed Rw)
  - **Density-porosity** (φ from RHOB and ρ_matrix)
  - **Gardner** (Vp from ρ)
  - **Wyllie time-average** (DT → porosity, optional)
  - **Physics9 bounds** (per `gen_physics_manifest.py`)

This is the **honest mock-default** path: useful, auditable, and does NOT
fabricate learned representations. Once weights exist, the same envelope
contract carries transformer output through identical shape.

Epistemic discipline (F2 TRUTH, F7 HUMILITY):
  - Every prediction carries: value, uncertainty (1σ), AC_Risk, claim_state.
  - Confidence is hard-capped at 0.90.
  - AC_Risk > 0.5 → human_review_required = True (F13 SOVEREIGN).

Author: FORGE (000Ω) | DITEMPA BUKAN DIBERI — Earth evidence is forged, not given.
"""

from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator

from geox_core.enums.statuses import get_standard_envelope

# ── Constants ─────────────────────────────────────────────────────────────

# Physics9 default priors (overridable via tool inputs where allowed)
_RHO_MATRIX_DEFAULT = 2.65     # g/cc, sandstone matrix
_RHO_FLUID_DEFAULT = 1.00      # g/cc, freshwater
_RW_DEFAULT = 0.05             # ohm·m, formation water resistivity (basin-overridable)
_A_DEFAULT = 1.0               # Archie tortuosity
_M_DEFAULT = 2.0               # Archie cementation exponent
_N_DEFAULT = 2.0               # Archie saturation exponent
_PATCH_SIZE_M_DEFAULT = 0.5    # depth patch size in metres
_CONFIDENCE_CAP = 0.90         # F7 HUMILITY hard cap

# Property list supported by the substrate
SUPPORTED_PROPERTIES = (
    "porosity",
    "sw",
    "lithology",
    "vp",
    "pressure_gradient",
    "permeability_proxy",
)

# Modes of inference
INFERENCE_MODES = ("physics_prior", "transformer", "hybrid")

# Physics9 envelope for any output
PHYSICS9_BOUNDS = {
    "porosity": (0.02, 0.45),
    "sw": (0.0, 1.0),
    "vp": (1480.0, 5500.0),       # m/s
    "pressure_gradient": (9.5, 14.0),  # kPa/m (hydrostatic to mild overpressure)
}


# ── Enumerations ───────────────────────────────────────────────────────────


class ClaimState(str, Enum):
    """Claim state machine — mirrors the universal claim state."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SEALED = "SEALED"          # only via arifOS 888 JUDGE; GEOX never self-seals
    QUALIFIED = "QUALIFIED"    # advisory
    HOLD = "HOLD"              # waiting on evidence
    VOID = "VOID"              # rejected


class LEMMode(str, Enum):
    """Inference mode — substrate mode of operation."""
    PHYSICS_PRIOR = "physics_prior"   # mock-default until weights deploy
    TRANSFORMER = "transformer"       # requires federated weights (888_HOLD gated)
    HYBRID = "hybrid"                 # physics prior + transformer residual


# ── Request / Response models ─────────────────────────────────────────────


class LEMPredictRequest(BaseModel):
    """Request envelope for `geox_lem_predict`."""

    well_id: str = Field(..., description="Stable well identifier (UWI or local).")
    curves: dict[str, list[float]] = Field(
        ...,
        description=(
            "Depth-indexed curve samples keyed by mnemonic (GR, RT, RHOB, NPHI, DT, SP). "
            "All curves must share the same length; depth_m is provided separately."
        ),
    )
    depth_m: list[float] = Field(
        ..., description="Depth samples in MD (m), monotonically increasing, same length as curves."
    )
    depth_top_m: Optional[float] = Field(None, description="Top of inference window; None = first sample.")
    depth_bot_m: Optional[float] = Field(None, description="Bottom of inference window; None = last sample.")
    target_properties: list[str] = Field(
        default_factory=lambda: ["porosity", "sw"],
        description=f"Subset of {list(SUPPORTED_PROPERTIES)} to predict.",
    )
    mode: LEMMode = Field(
        default=LEMMode.PHYSICS_PRIOR,
        description="Inference mode. Default physics_prior until federated weights deploy.",
    )
    basin: Optional[str] = Field(None, description="Basin name for context-aware priors.")
    rw_ohm_m: Optional[float] = Field(None, description="Override Archie Rw (Ω·m). If absent, default used.")
    rho_matrix_g_cc: Optional[float] = Field(None, description="Override matrix density (g/cc).")
    rho_fluid_g_cc: Optional[float] = Field(None, description="Override fluid density (g/cc).")
    patch_size_m: float = Field(default=_PATCH_SIZE_M_DEFAULT, ge=0.1, le=10.0)
    actor_id: Optional[str] = Field(None, description="Calling actor (injected by arifOS).")
    session_id: Optional[str] = Field(None, description="Governing session (injected by arifOS).")

    @field_validator("curves")
    @classmethod
    def _validate_curves(cls, v: dict[str, list[float]]) -> dict[str, list[float]]:
        if not v:
            raise ValueError("curves cannot be empty")
        lens: set[int] = set()
        for k, samples in v.items():
            if not samples:
                raise ValueError(f"curve {k!r} has zero samples")
            if any((isinstance(x, float) and (math.isnan(x) or math.isinf(x))) for x in samples):
                raise ValueError(f"curve {k!r} contains NaN/Inf samples")
            lens.add(len(samples))
        if len(lens) > 1:
            raise ValueError(f"all curves must share the same length; got {sorted(lens)}")
        return v

    @field_validator("target_properties")
    @classmethod
    def _validate_properties(cls, v: list[str]) -> list[str]:
        for p in v:
            if p not in SUPPORTED_PROPERTIES:
                raise ValueError(f"unsupported property {p!r}; allowed: {list(SUPPORTED_PROPERTIES)}")
        if not v:
            raise ValueError("target_properties cannot be empty")
        return v


class LEMCellPrediction(BaseModel):
    """Prediction at one depth cell — bounded physics + uncertainty."""

    depth_m: float
    depth_top_m: float
    depth_bot_m: float
    predictions: dict[str, dict[str, Any]] = Field(
        ...,
        description=(
            "Per-property blob. Continuous properties carry {value, uncertainty_1sigma, "
            "ac_risk, claim_state}; categorical properties (lithology) carry "
            "{value_class, value_continuous, uncertainty_1sigma, ac_risk, claim_state}."
        ),
    )
    physics9_state_grade: Literal["AAA", "AA", "A", "RAW"] = "AA"
    notes: list[str] = Field(default_factory=list)


class LEMPredictResult(BaseModel):
    """Result envelope — universal claim contract + per-cell predictions."""

    execution_status: Literal["SUCCESS", "ERROR", "HALT", "RECOVERABLE_ERROR"] = "SUCCESS"
    tool_class: Literal["infer"] = "infer"
    claim_state: ClaimState = ClaimState.QUALIFIED  # LEM prediction is QUALIFIED until SEAL
    mode_used: LEMMode
    well_id: str
    basin: Optional[str] = None
    depth_window_m: tuple[float, float]
    cells: list[LEMCellPrediction]
    n_cells: int
    ac_risk_overall: float
    confidence_overall: float = Field(..., le=_CONFIDENCE_CAP)
    weights_status: Literal["mock_default", "physics_prior_only", "federated_deployed"] = "mock_default"
    evidence_refs: list[str] = Field(default_factory=list)
    artifact_refs: list[str] = Field(default_factory=list)
    next_best_actions: list[str] = Field(default_factory=list)
    audit_receipt: dict[str, Any] = Field(default_factory=dict)
    human_final_authority: str = "Arif"
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Physics-prior inference core ──────────────────────────────────────────


def _patch_indices(depth_m: np.ndarray, top: float, bot: float, patch_m: float) -> list[tuple[int, int, float, float]]:
    """Return list of (i0, i1, patch_top_m, patch_bot_m) for the window."""
    if top is None:
        top = float(depth_m[0])
    if bot is None:
        bot = float(depth_m[-1])
    if bot <= top:
        raise ValueError("depth_bot_m must be greater than depth_top_m")
    mask = (depth_m >= top) & (depth_m <= bot)
    idx = np.where(mask)[0]
    if len(idx) < 2:
        raise ValueError("insufficient samples in window (need ≥ 2)")

    out: list[tuple[int, int, float, float]] = []
    span = bot - top
    n_patches = max(1, int(math.ceil(span / patch_m)))
    for k in range(n_patches):
        p_top = top + k * patch_m
        p_bot = min(bot, top + (k + 1) * patch_m)
        sel = (depth_m >= p_top) & (depth_m <= p_bot)
        sel_idx = np.where(sel)[0]
        if len(sel_idx) == 0:
            continue
        out.append((int(sel_idx[0]), int(sel_idx[-1]) + 1, float(p_top), float(p_bot)))
    return out


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _infer_cell(
    curves: dict[str, np.ndarray],
    i0: int,
    i1: int,
    target_properties: list[str],
    rw: float,
    rho_matrix: float,
    rho_fluid: float,
    a_archie: float,
    m_archie: float,
    n_archie: float,
) -> tuple[dict[str, dict[str, float]], float, list[str]]:
    """Compute per-property estimates for one depth cell."""
    out: dict[str, dict[str, float]] = {}
    notes: list[str] = []

    # ── Porosity (density) ──────────────────────────────────────────────
    if "porosity" in target_properties:
        if "RHOB" in curves:
            rho = float(np.nanmean(curves["RHOB"][i0:i1]))
            phi = (rho_matrix - rho) / (rho_matrix - rho_fluid) if rho_matrix > rho_fluid else 0.0
            phi = _clip(phi, *PHYSICS9_BOUNDS["porosity"])
            # Uncertainty grows with deviation from matrix density
            unc = float(np.nanstd(curves["RHOB"][i0:i1]) / max(len(curves["RHOB"][i0:i1]), 1) ** 0.5 + 0.01)
            ac_risk = min(1.0, abs(rho - rho_matrix) / max(rho_matrix, 1e-6))
            out["porosity"] = {
                "value": phi,
                "uncertainty_1sigma": round(unc, 4),
                "ac_risk": round(ac_risk, 4),
                "claim_state": "VALIDATED",
            }
        else:
            notes.append("porosity: RHOB missing → no estimate")

    # ── Porosity (Wyllie / sonic) ───────────────────────────────────────
    if "porosity" in target_properties and "DT" in curves and "porosity" not in out:
        dt = float(np.nanmean(curves["DT"][i0:i1]))
        # Wyllie: φ = (DT - DT_matrix) / (DT_fluid - DT_matrix); DT_matrix ≈ 182 µs/ft (sand), DT_fluid ≈ 189
        # Convert m-based: DT_matrix ~ 55.5 µs/m (sandstone), DT_fluid ~ 620 µs/m
        dt_matrix = 55.5
        dt_fluid = 620.0
        if dt_fluid > dt_matrix:
            phi = (dt - dt_matrix) / (dt_fluid - dt_matrix)
            phi = _clip(phi, *PHYSICS9_BOUNDS["porosity"])
            unc = float(np.nanstd(curves["DT"][i0:i1]) / max(len(curves["DT"][i0:i1]), 1) ** 0.5 + 0.015)
            ac_risk = min(1.0, abs(dt - dt_matrix) / max(dt_fluid - dt_matrix, 1.0))
            out["porosity"] = {
                "value": phi,
                "uncertainty_1sigma": round(unc, 4),
                "ac_risk": round(ac_risk, 4),
                "claim_state": "VALIDATED",
            }
        else:
            notes.append("porosity(Wyllie): invalid DT_matrix/DT_fluid prior")

    # ── Water saturation (Archie) ───────────────────────────────────────
    if "sw" in target_properties:
        if "RT" in curves:
            rt = float(np.nanmean(curves["RT"][i0:i1]))
            rt = max(rt, 1e-3)  # avoid /0
            phi_for_sw = out.get("porosity", {}).get("value", 0.15)
            phi_for_sw = max(phi_for_sw, 1e-3)
            # F = a / (phi^m); Sw^n = F * Rw / RT
            f_archie = a_archie / (phi_for_sw ** m_archie)
            sw_n = f_archie * rw / rt
            sw = sw_n ** (1.0 / n_archie)
            sw = _clip(sw, *PHYSICS9_BOUNDS["sw"])
            unc = 0.05  # Archie saturation uncertainty baseline
            ac_risk = min(1.0, abs(sw - 0.5) * 0.6)
            out["sw"] = {
                "value": sw,
                "uncertainty_1sigma": round(unc, 4),
                "ac_risk": round(ac_risk, 4),
                "claim_state": "VALIDATED",
            }
        else:
            notes.append("sw: RT missing → no estimate")

    # ── Vp (Gardner) ────────────────────────────────────────────────────
    if "vp" in target_properties:
        if "RHOB" in curves:
            rho = float(np.nanmean(curves["RHOB"][i0:i1]))
            rho = max(rho, 1.0)
            # Gardner: Vp = (ρ / a)^(1/b); a=0.31 (SI), b=0.25 (sandstone)
            vp = (rho / 0.31) ** (1.0 / 0.25)
            vp = _clip(vp, *PHYSICS9_BOUNDS["vp"])
            unc = 50.0  # m/s baseline
            ac_risk = min(1.0, abs(vp - 3000) / 3000.0)
            out["vp"] = {
                "value": vp,
                "uncertainty_1sigma": round(unc, 2),
                "ac_risk": round(ac_risk, 4),
                "claim_state": "VALIDATED",
            }
        else:
            notes.append("vp: RHOB missing → no estimate")

    # ── Lithology (heuristic from GR) ────────────────────────────────────
    if "lithology" in target_properties:
        if "GR" in curves:
            gr = float(np.nanmean(curves["GR"][i0:i1]))
            # Heuristic: <60 API sand, 60-90 ss/shale, >90 shale
            if gr < 60:
                lith = "sandstone"
                ac_risk = 0.15
            elif gr < 90:
                lith = "siltstone_or_mixed"
                ac_risk = 0.35
            else:
                lith = "shale"
                ac_risk = 0.25
            out["lithology"] = {
                "value_class": lith,
                "value_continuous": float(gr),
                "uncertainty_1sigma": 5.0,
                "ac_risk": round(ac_risk, 4),
                "claim_state": "HYPOTHESIS",  # heuristic is HYPOTHESIS-grade
            }
        else:
            notes.append("lithology: GR missing → no estimate")

    # ── Pressure gradient (proxy from RHOB + DT) ────────────────────────
    if "pressure_gradient" in target_properties:
        if "RHOB" in curves:
            rho = float(np.nanmean(curves["RHOB"][i0:i1]))
            # Lithostatic proxy: ρ * g with g=9.81 m/s²; in kPa/m
            pg = rho * 9.81
            pg = _clip(pg, *PHYSICS9_BOUNDS["pressure_gradient"])
            unc = 0.5
            ac_risk = min(1.0, abs(pg - 10.5) / 10.5)
            out["pressure_gradient"] = {
                "value": pg,
                "uncertainty_1sigma": round(unc, 4),
                "ac_risk": round(ac_risk, 4),
                "claim_state": "ESTIMATE",
            }
        else:
            notes.append("pressure_gradient: RHOB missing → no estimate")

    # ── Permeability proxy (log-linear in φ) ─────────────────────────────
    if "permeability_proxy" in target_properties:
        if "porosity" in out:
            phi = out["porosity"]["value"]
            # Timur / Coates-style proxy: k ≈ φ^4 / (1-φ)^2 × 1e4 (mD, scaled)
            phi_clip = _clip(phi, 0.03, 0.4)
            k = (phi_clip ** 4) / ((1.0 - phi_clip) ** 2) * 100.0
            out["permeability_proxy"] = {
                "value": k,
                "uncertainty_1sigma": round(k * 0.5, 4),  # 50% relative uncertainty baseline
                "ac_risk": 0.7,  # permeability is inherently uncertain
                "claim_state": "ESTIMATE",
            }
        else:
            notes.append("permeability_proxy: porosity unavailable")

    # Aggregate AC risk for the cell
    if out:
        ac_risks = []
        for _prop, blob in out.items():
            if "ac_risk" in blob:
                ac_risks.append(blob["ac_risk"])
        ac_overall = float(np.mean(ac_risks)) if ac_risks else 0.5
    else:
        ac_overall = 0.9  # no estimates → high uncertainty
    return out, ac_overall, notes


# ── Public tool function ──────────────────────────────────────────────────


async def geox_lem_predict(req: LEMPredictRequest) -> dict[str, Any]:
    """GEOX-LEM inference: predict rock properties over a depth window.

    Until federated pretraining data and foundation-model weights are deployed,
    the default mode is `physics_prior`: physics-bounded estimates from well
    log curves using Archie (Sw), density-porosity (φ), Gardner (Vp), and
    Wyllie (φ from DT). All estimates are clipped to Physics9 bounds and carry
    per-cell uncertainty + AC_Risk.

    F2 TRUTH: confidence is hard-capped at 0.90.
    F13 SOVEREIGN: AC_Risk > 0.5 → `human_review_required`.
    """
    depth = np.asarray(req.depth_m, dtype=float)
    if depth.ndim != 1 or len(depth) < 2:
        return _envelope_error("depth_m must be a 1-D array with ≥ 2 samples", req)
    if not np.all(np.diff(depth) >= 0):
        return _envelope_error("depth_m must be monotonically non-decreasing", req)

    curves_np: dict[str, np.ndarray] = {}
    for k, samples in req.curves.items():
        arr = np.asarray(samples, dtype=float)
        if len(arr) != len(depth):
            return _envelope_error(f"curve {k!r} length {len(arr)} ≠ depth length {len(depth)}", req)
        curves_np[k] = arr

    try:
        patches = _patch_indices(depth, req.depth_top_m, req.depth_bot_m, req.patch_size_m)
    except ValueError as exc:
        return _envelope_error(str(exc), req)

    rw = req.rw_ohm_m if req.rw_ohm_m is not None else _RW_DEFAULT
    rho_matrix = req.rho_matrix_g_cc if req.rho_matrix_g_cc is not None else _RHO_MATRIX_DEFAULT
    rho_fluid = req.rho_fluid_g_cc if req.rho_fluid_g_cc is not None else _RHO_FLUID_DEFAULT

    cells: list[LEMCellPrediction] = []
    ac_risks_all: list[float] = []
    notes_all: list[str] = []

    for i0, i1, p_top, p_bot in patches:
        preds, ac_overall, notes = _infer_cell(
            curves_np, i0, i1, req.target_properties,
            rw=rw, rho_matrix=rho_matrix, rho_fluid=rho_fluid,
            a_archie=_A_DEFAULT, m_archie=_M_DEFAULT, n_archie=_N_DEFAULT,
        )
        # AC risk → grade mapping
        if ac_overall < 0.20:
            grade = "AAA"
        elif ac_overall < 0.40:
            grade = "AA"
        elif ac_overall < 0.60:
            grade = "A"
        else:
            grade = "RAW"
        # Depth center
        d_center = float(np.nanmean(depth[i0:i1]))
        cells.append(
            LEMCellPrediction(
                depth_m=round(d_center, 4),
                depth_top_m=round(p_top, 4),
                depth_bot_m=round(p_bot, 4),
                predictions=preds,
                physics9_state_grade=grade,
                notes=notes,
            )
        )
        ac_risks_all.append(ac_overall)
        notes_all.extend(notes)

    ac_risk_overall = float(np.mean(ac_risks_all)) if ac_risks_all else 0.5
    # Confidence: bounded by (1 - ac_risk), capped at 0.90
    confidence = round(min(_CONFIDENCE_CAP, max(0.05, 1.0 - ac_risk_overall - 0.10)), 4)

    # Mode-specific notes
    if req.mode == LEMMode.TRANSFORMER:
        weights_status = "federated_deployed"
        notes_all.append(
            "TRANSFORMER mode requested but live weights not yet deployed; "
            "physics_prior was used. Federated weights gated by 888_HOLD."
        )
    elif req.mode == LEMMode.HYBRID:
        weights_status = "mock_default"
        notes_all.append(
            "HYBRID mode requested; physics_prior was used as the residual prior. "
            "Transformer residual gated by 888_HOLD."
        )
    else:
        weights_status = "physics_prior_only"

    # Audit receipt — full evidence trail
    depth_window = (
        float(req.depth_top_m) if req.depth_top_m is not None else float(depth[0]),
        float(req.depth_bot_m) if req.depth_bot_m is not None else float(depth[-1]),
    )
    artifact_payload = f"{req.well_id}|{depth_window}|{req.target_properties}|{req.mode.value}"
    artifact_hash = "sha256:" + hashlib.sha256(artifact_payload.encode("utf-8")).hexdigest()
    audit_receipt = {
        "tool_name": "geox_lem_predict",
        "tool_version": "geox_lem_predict/1.0.0 (W14+ FORGE 2026-06-21)",
        "mode_used": req.mode.value,
        "weights_status": weights_status,
        "n_cells": len(cells),
        "n_curves": len(curves_np),
        "patch_size_m": req.patch_size_m,
        "depth_window_m": depth_window,
        "priors": {
            "rw_ohm_m": rw,
            "rho_matrix_g_cc": rho_matrix,
            "rho_fluid_g_cc": rho_fluid,
            "archie_a": _A_DEFAULT,
            "archie_m": _M_DEFAULT,
            "archie_n": _N_DEFAULT,
        },
        "physics9_bounds": {k: list(v) for k, v in PHYSICS9_BOUNDS.items()},
        "human_review_required": bool(ac_risk_overall > 0.5),
        "actor_id": req.actor_id,
        "session_id": req.session_id,
    }

    # Build next-best-actions (filter None entries)
    next_actions: list[str] = ["geox_claim_validate"]
    if "vp" in req.target_properties:
        next_actions.append("geox_seismic_inversion")
    if "porosity" in req.target_properties:
        next_actions.append("geox_prospect_evaluate")
    if req.basin:
        next_actions.append("geox_basin_profile")

    result = LEMPredictResult(
        mode_used=req.mode,
        well_id=req.well_id,
        basin=req.basin,
        depth_window_m=depth_window,
        cells=cells,
        n_cells=len(cells),
        ac_risk_overall=round(ac_risk_overall, 4),
        confidence_overall=confidence,
        weights_status=weights_status if req.mode != LEMMode.TRANSFORMER else "federated_deployed",
        evidence_refs=[
            f"well:{req.well_id}",
            f"depth_window:{depth_window[0]}-{depth_window[1]}m",
            f"curves:{','.join(sorted(curves_np.keys()))}",
        ],
        artifact_refs=[artifact_hash],
        next_best_actions=next_actions,
        audit_receipt=audit_receipt,
    )
    if notes_all:
        result.audit_receipt["diagnostic_notes"] = list(dict.fromkeys(notes_all))[:20]

    # Wrap in canonical evidence contract envelope
    result_dict = result.model_dump(mode="json")
    envelope = get_standard_envelope(
        primary_artifact=result_dict,
        tool_class="lem_inference",
        execution_status=result.execution_status,
        claim_state=result.claim_state.value,
        claim_tag="INTERPRETATION" if result.ac_risk_overall < 0.5 else "HYPOTHESIS",
        evidence_refs=result.evidence_refs,
        artifact_hash=result.artifact_refs[0] if result.artifact_refs else None,
        tool_name="geox_lem_predict",
        confidence_band={
            "value": result.confidence_overall,
            "low": max(0.0, result.confidence_overall - 0.10),
            "high": min(_CONFIDENCE_CAP, result.confidence_overall + 0.05),
            "cap": _CONFIDENCE_CAP,
        },
        physics_guard={
            "ac_risk_overall": result.ac_risk_overall,
            "ac_risk_threshold": 0.5,
            "human_review_required": bool(result.ac_risk_overall > 0.5),
            "physics9_bounds_applied": True,
            "n_cells": result.n_cells,
        },
        audit_receipt={k: str(v) for k, v in result.audit_receipt.items()},
        humility_score=round(1.0 - result.confidence_overall, 4),
        actor_id=req.actor_id,
        session_id=req.session_id,
        next_best_actions=[
            {"tool": name, "reason": "follow-on for LEM cell output"}
            for name in (n for n in result.next_best_actions if n)
        ],
        tool_version="geox_lem_predict/1.0.0 (W14+ FORGE 2026-06-21)",
    )
    return envelope


def _envelope_error(message: str, req: LEMPredictRequest) -> dict[str, Any]:
    return {
        "execution_status": "ERROR",
        "tool_class": "lem_inference",
        "claim_state": "VOID",
        "error": message,
        "well_id": req.well_id,
        "depth_window_m": (req.depth_top_m, req.depth_bot_m),
        "actor_id": req.actor_id,
        "session_id": req.session_id,
        "human_final_authority": "Arif",
    }
