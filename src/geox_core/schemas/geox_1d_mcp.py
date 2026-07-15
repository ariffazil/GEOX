"""
GEOX 1D MCP boundary models — JSON-native, no numpy at the wire.

Tools:
  geox_well_time_depth_calibrate
  geox_well_seismic_mistie_rms
  geox_wavelet_extract_least_squares

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


def as_float_list(x: Any) -> list[float]:
    """np.ndarray / list / scalar → list[float]."""
    if x is None:
        return []
    if hasattr(x, "tolist"):
        raw = x.tolist()
        if isinstance(raw, (int, float)):
            return [float(raw)]
        return [float(v) for v in raw]
    if isinstance(x, (list, tuple)):
        return [float(v) for v in x]
    return [float(x)]


class VaultReceiptLite(BaseModel):
    """Lightweight audit receipt (not VAULT999 seal — DRAFT_ONLY until arifOS)."""

    receipt_id: str
    tool: str
    actor: str = "geox_1d_mcp"
    threshold_ms: float | None = None
    verdict: str | None = None
    resource_uri: str | None = None
    timestamp_utc: str = ""
    vault999_status: Literal["DRAFT_ONLY"] = "DRAFT_ONLY"
    seal_allowed: bool = False


class TDFitResultMCP(BaseModel):
    """JSON envelope for T-D calibration (maps TDFitResult.to_dict)."""

    method: str
    equation: str
    coefficients: list[float] = Field(default_factory=list)
    twt_ms: list[float] = Field(default_factory=list)
    residuals_ms: list[float] = Field(default_factory=list)
    rmse_ms: float
    physics_guard: dict[str, Any] = Field(default_factory=dict)
    extrapolation_risk: float = 0.0
    fail_closed: bool = False
    residual_threshold_pct: float | None = None
    residual_ok: bool | None = None
    vault_receipt: VaultReceiptLite | None = None
    resource_uri: str | None = None


class MistieResultMCP(BaseModel):
    """Phase 3 falsification gate — hard 25 ms default."""

    optimal_lag_ms: float
    rms_mistie_ms: float
    correlation_coefficient: float
    residual_rms_normalized: float | None = None
    verdict: Literal["SEAL", "HOLD", "VOID"]
    threshold_used_ms: float
    verdict_reason: str = ""
    residual_class: str = ""
    residual_description: str = ""
    per_interval_mistie: list[dict[str, Any]] = Field(default_factory=list)
    physics_guard: dict[str, Any] = Field(default_factory=dict)
    anti_hantu_flags: list[str] = Field(default_factory=list)
    vault_receipt: VaultReceiptLite | None = None
    resource_uri: str | None = None


class WaveletResultMCP(BaseModel):
    """Phase 4 least-squares / Wiener wavelet extraction."""

    wavelet: list[float] = Field(default_factory=list)
    condition_number: float
    epsilon_used: float
    new_synthetic: list[float] = Field(default_factory=list)
    updated_mistie_ms: float | None = None
    updated_correlation: float | None = None
    phase_class: Literal["zero", "minimum", "mixed", "unknown"] = "unknown"
    wavelet_length_ms: float = 0.0
    dt_ms: float = 1.0
    physics_guard: dict[str, Any] = Field(default_factory=dict)
    vault_receipt: VaultReceiptLite | None = None
    resource_uri: str | None = None
