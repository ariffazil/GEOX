"""Canonical noun family for seismic interpretation (FIX BRIEF v2 · P1).

Section · Calibration · Horizon · Fault · Hypothesis · GateResult · InterpretationBundle
CutoffPair (P2) — hanging-wall / footwall sense for polarity discrimination.

Legacy shapes enter only via adapters (geometry_adapt / calibration_derive).
Anonymous geometry is rejected — never defaulted to "unknown".

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class Calibration(StrictModel):
    """Earth-physics scale. Must be explicit — never silent workspace inherit."""

    bin_spacing_m: float | None = None
    sample_rate_ms: float | None = None
    vertical_exaggeration: float | None = None
    velocity_td: list[dict[str, Any]] | None = None
    velocity_linear_m_s: float | None = None
    section_azimuth_deg: float | None = None
    polarity_convention: Literal["SEG_NORMAL", "SEG_REVERSE", "UNKNOWN"] = "UNKNOWN"
    domain: Literal["time", "depth"] = "time"
    datum: str | None = None
    crs: str | None = None
    units: str | None = None
    well_tie: dict[str, Any] | None = None
    calibrated: bool = False
    input_class: Literal["image_only", "segy_slice", "segy_2d", "segy_3d", "unknown"] = "unknown"
    sha256: str | None = None
    calibration_hash: str | None = None
    # binding receipt — gates refuse if physics used without this when required
    bound: bool = False


# Physics keys that must NEVER silently inherit from workspace
PHYSICS_KEYS = frozenset(
    {
        "vertical_exaggeration",
        "ve",
        "polarity",
        "polarity_convention",
        "crs",
        "datum",
        "domain",
        "velocity",
        "velocity_td",
        "velocity_linear_m_s",
        "section_azimuth_deg",
        "azimuth",
        "units",
        "bin_spacing_m",
        "sample_rate_ms",
        "sample_interval_ms",
    }
)


class Point2D(FlexibleModel):
    x: float  # cmp / trace
    y: float  # twt_ms or depth_m


class Fault(FlexibleModel):
    fault_id: str
    points: list[dict[str, Any]] = Field(default_factory=list)
    regime_prior: str | None = None
    dip_deg_image: float | None = None
    dip_deg_subsurface: float | None = None
    throw_profile: list[Any] | None = None
    max_displacement: float | None = None
    length: float | None = None
    artifact: bool = False
    witness: str | None = None  # chatgpt | claude | classical_cv | human | geox


class Horizon(FlexibleModel):
    horizon_id: str
    points: list[dict[str, Any]] = Field(default_factory=list)
    order_index: int = 0
    witness: str | None = None


class CutoffPair(FlexibleModel):
    """Hanging-wall / footwall cutoff at Horizon × Fault (P2 discrimination)."""

    horizon_id: str
    fault_id: str
    hw_twt: float | None = None
    fw_twt: float | None = None
    hw_depth_m: float | None = None
    fw_depth_m: float | None = None
    sense: Literal["normal_slip", "reverse_slip", "ambiguous", "unmeasured"] = "unmeasured"
    throw_ms: float | None = None
    throw_m: float | None = None
    fault_cmp: float | None = None


class Hypothesis(FlexibleModel):
    hypothesis_id: str
    structural_style: str = "unknown"
    faults: list[Fault] = Field(default_factory=list)
    horizons: list[Horizon] = Field(default_factory=list)
    cutoffs: list[CutoffPair] = Field(default_factory=list)
    witness: str | None = None
    confidence: float = 0.0
    combined_gate_verdict: str | None = None


class GateResult(FlexibleModel):
    gate_id: str
    status: Literal["PASS", "WARN", "KILL", "UNMEASURED"]
    reason: str = ""
    receipt_hash: str = ""
    equation: str = ""


class Section(FlexibleModel):
    section_id: str | None = None
    image_path: str | None = None
    image_hash: str | None = None
    input_class: str = "image_only"
    domain: Literal["time", "depth"] = "time"


class InterpretationBundle(FlexibleModel):
    """Compact default; full physics behind detail_ref."""

    verdict: Literal["QUALIFIED_CANDIDATE"] = "QUALIFIED_CANDIDATE"
    seal_authority: Literal["arifOS_only"] = "arifOS_only"
    preferred_hypothesis: None = None
    input_class: str = "image_only"
    hypotheses: int = 0
    gate_summary: dict[str, int] = Field(default_factory=dict)
    render_ref: str | None = None
    detail_ref: str | None = None
    receipt_hash: str | None = None
