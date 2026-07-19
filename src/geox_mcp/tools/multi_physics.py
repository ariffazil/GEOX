"""
multi_physics.py — MCP tool wrappers for Phase C (W13+) multi-physics forge.

W13+ forge: constitutional MCP surface for the joint Earth Witness:
- geox_joint_inversion: fuse N modalities → one Physics13State per cell
- geox_mt_forward: 1D CSEM/MT apparent resistivity + phase
- geox_biostrat_constraint: time-facies admissibility for a cell

DITEMPA BUKAN DIBEI — the cell is forged, not given; the witness testifies, not seals.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from geox_core.engines.geophysics.biostrat_constraint import (
    evaluate_biostrat_constraint,
)
from geox_core.engines.geophysics.mt_forward import (
    MTForwardRequest,
    MTLayer,
    mt_forward,
)
from geox_core.physics.joint_inversion import (
    InversionRequest,
    ModalityObservation,
    joint_inversion,
)
from geox_core.physics.state import Physics13State


# ───────────────────────────── JOINT INVERSION ─────────────────────────────────────
class ModalityObsSchema(BaseModel):
    modality: Literal[
        "seismic_impedance", "seismic_vpvs", "gravity",
        "magnetic", "mt_resistivity",
    ]
    value: float
    uncertainty: float = Field(default=0.05, gt=0)
    weight: float = Field(default=1.0, gt=0)
    depth_m: float = Field(default=0.0, ge=0)


class JointInversionRequest(BaseModel):
    observations: list[ModalityObsSchema] = Field(default_factory=list)
    prior: dict | None = Field(default=None, description="Optional Physics13State as dict")
    max_iter: int = Field(default=50, ge=1, le=500)
    tolerance: float = Field(default=1e-3, gt=0)


class JointInversionResponse(BaseModel):
    ok: bool
    tool: str = "geox_joint_inversion"
    state: dict | None = None
    grade: str | None = None
    residual_rms: float | None = None
    iterations: int | None = None
    modality_count: int | None = None
    per_modality: dict | None = None
    observation_hash: str | None = None
    epistemic_provenance: dict | None = None
    godel_wall: dict | None = None
    error: str | None = None


async def geox_joint_inversion(request: JointInversionRequest) -> JointInversionResponse:
    """Constitutional MCP tool: joint multi-physics inversion under Physics9 bounds.

    Fuses N modalities (seismic impedance, Vp/Vs, gravity, magnetic, MT resistivity)
    into one Physics13State per cell. Enforces Earth-bounds on every dial.
    """
    try:
        obs = [
            ModalityObservation(
                modality=o.modality, value=o.value,
                uncertainty=o.uncertainty, weight=o.weight,
                depth_m=o.depth_m,
            )
            for o in request.observations
        ]
        prior = None
        if request.prior:
            prior = Physics13State(**request.prior)
        req = InversionRequest(
            observations=obs, prior=prior,
            max_iter=request.max_iter, tolerance=request.tolerance,
        )
        result = joint_inversion(req)
        if not result["ok"]:
            return JointInversionResponse(
                ok=False, error=result.get("error", "inversion_failed"),
            )
        return JointInversionResponse(
            ok=True,
            state=result["state"].to_dict(),
            grade=result["grade"],
            residual_rms=result["residual_rms"],
            iterations=result["iterations"],
            modality_count=result["modality_count"],
            per_modality=result["per_modality"],
            observation_hash=result["observation_hash"],
            epistemic_provenance=result["epistemic_provenance"],
            godel_wall=result["godel_wall"],
        )
    except Exception as e:
        return JointInversionResponse(ok=False, error=str(e))


# ───────────────────────────── MT FORWARD ──────────────────────────────────────────
class MTLayerSchema(BaseModel):
    thickness_m: float
    resistivity_ohm_m: float = Field(gt=0)


class MTForwardRequestSchema(BaseModel):
    layers: list[MTLayerSchema]
    frequencies_hz: tuple[float, ...] = (0.001, 0.01, 0.1, 1.0, 10.0, 100.0)


class MTForwardResponse(BaseModel):
    ok: bool
    tool: str = "geox_mt_forward"
    result: dict | None = None
    error: str | None = None


async def geox_mt_forward(request: MTForwardRequestSchema) -> MTForwardResponse:
    """Constitutional MCP tool: 1D CSEM/MT forward response (apparent resistivity + phase)."""
    try:
        layers = [MTLayer(thickness_m=l.thickness_m, resistivity_ohm_m=l.resistivity_ohm_m) for l in request.layers]
        req = MTForwardRequest(layers=layers, frequencies_hz=request.frequencies_hz)
        r = mt_forward(req)
        if not r["ok"]:
            return MTForwardResponse(ok=False, error=r.get("error", "mt_forward_failed"))
        return MTForwardResponse(ok=True, result=r)
    except Exception as e:
        return MTForwardResponse(ok=False, error=str(e))


# ───────────────────────────── BIOSTRAT CONSTRAINT ────────────────────────────────
class BiostratRequest(BaseModel):
    state: dict = Field(..., description="Physics13State as dict")
    age_ma: float = Field(..., description="Age in Ma")


class BiostratResponse(BaseModel):
    ok: bool
    tool: str = "geox_biostrat_constraint"
    result: dict | None = None
    error: str | None = None


async def geox_biostrat_constraint(request: BiostratRequest) -> BiostratResponse:
    """Constitutional MCP tool: biostrat time-facies admissibility check."""
    try:
        state = Physics13State(**request.state)
        r = evaluate_biostrat_constraint(state, request.age_ma)
        return BiostratResponse(ok=True, result={
            "zone_name": r.zone_name,
            "zone_admissible_materials": list(r.zone_admissible_materials),
            "cell_material_match": r.cell_material_match,
            "is_material_admissible": r.is_material_admissible,
            "is_phi_in_range": r.is_phi_in_range,
            "is_vpvs_in_range": r.is_vpvs_in_range,
            "is_consistent": r.is_consistent,
            "notes": list(r.notes),
        })
    except Exception as e:
        return BiostratResponse(ok=False, error=str(e))


__all__ = [
    "JointInversionRequest",
    "JointInversionResponse",
    "geox_joint_inversion",
    "MTForwardRequestSchema",
    "MTForwardResponse",
    "geox_mt_forward",
    "BiostratRequest",
    "BiostratResponse",
    "geox_biostrat_constraint",
]
