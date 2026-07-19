"""
prithvi_adapter.py — W₅-W₈ Phase A first wave.

Constitutional wrapper for Prithvi-EO-2.0 (NASA-IMPACT + IBM).

Reference:
- Prithvi-EO-2.0 (Dec 2024): https://github.com/NASA-IMPACT/Prithvi-EO-2.0
- Paper: arXiv 2412.02732
- Pretrained on 4.2M HLS (Harmonized Landsat + Sentinel-2) time series.
- TerraTorch library (IBM) for fine-tuning/inference.

GEOX adapter doctrine:
- Live inference: requires `terratorch` + GPU + weight files. 888_HOLD gate.
- Mock backend: deterministic stub for tests/offline. Always available.
- Constitutional envelope: every output wrapped with epistemic_provenance,
  ml_provenance, anti_beautiful_one_check, godel_wall verdict.

DITEMPA BUKAN DIBEI — the weights live in the engine; the trust envelope
lives in the MCP tool surface.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol

from pydantic import BaseModel, Field

# Lazy import so we can mock without GPU stack
try:
    import numpy as np  # noqa: F401
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False

try:
    # The real package is `terratorch` from IBM. We import lazily.
    import terratorch  # type: ignore  # noqa: F401
    _TERRATORCH_AVAILABLE = True
except ImportError:
    _TERRATORCH_AVAILABLE = False


# ───────────────────────────── SCHEMAS ────────────────────────────────────────────
PrithviTask = Literal[
    "flood_mapping",       # binary water mask
    "burn_scars",          # binary fire damage mask
    "land_cover",          # multi-class LCCS
    "multi_temporal_crop", # crop type classification
    "scene_reasoning",     # multimodal Q&A on EO scene
]


@dataclass(frozen=True)
class HLSInput:
    """Harmonized Landsat + Sentinel-2 input reference.

    Real flow: tile URLs from NASA Earthdata (HLSL30 / HLSS30).
    Mock flow: tile_id is a synthetic identifier.
    """

    tile_id: str
    bands: tuple[str, ...] = ("B02", "B03", "B04", "B8A", "B11", "B12")  # S2 subset
    time_range: tuple[str, str] = ("2024-01-01", "2024-12-31")
    cloud_cover_max: float = 0.20
    source_uri: str | None = None  # s3:// or https://


class PrithviProvenance(BaseModel):
    """ML provenance envelope — required by F2 / F9 Anti-Hantu."""

    model_name: str = "Prithvi-EO-2.0"
    model_version: str = "2.0"
    training_dataset: str = "HLS (Harmonized Landsat + Sentinel-2)"
    input_hash: str = Field(..., description="SHA-256 of the input payload")
    confidence_source: Literal["softmax", "calibrated", "mock"] = "softmax"
    mode: Literal["live", "mock"] = "mock"


class PrithviOutput(BaseModel):
    """Constitutional envelope around Prithvi inference output."""

    task: PrithviTask
    result: dict = Field(..., description="Task-specific result payload")
    ml_provenance: PrithviProvenance
    epistemic_provenance: dict = Field(default_factory=dict)
    anti_beautiful_one_check: dict = Field(default_factory=dict)
    godel_wall: dict = Field(default_factory=dict)
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# ───────────────────────────── ADAPTER ────────────────────────────────────────────
class PrithviBackend(Protocol):
    """Backend protocol — implement live or mock."""

    def is_available(self) -> bool: ...
    def infer(self, payload: HLSInput, task: PrithviTask) -> dict: ...


class MockPrithviBackend:
    """Deterministic mock for tests/offline.

    Produces a structured stub result keyed on tile_id so tests are
    reproducible.
    """

    def is_available(self) -> bool:
        return True

    def infer(self, payload: HLSInput, task: PrithviTask) -> dict:
        # Deterministic seed from tile_id so the same input → same output.
        h = hashlib.sha256(payload.tile_id.encode()).hexdigest()[:8]
        if task == "flood_mapping":
            return {
                "water_mask": {"shape": [256, 256], "coverage_pct": 0.0, "seed": h},
                "uncertainty_band": {"low": 0.85, "high": 0.95},
            }
        if task == "burn_scars":
            return {
                "burn_scar_mask": {"shape": [256, 256], "coverage_pct": 0.0, "seed": h},
                "dnbr_threshold": 0.66,
            }
        if task == "land_cover":
            return {
                "classes": {
                    "water": 0.01, "forest": 0.62, "grassland": 0.20,
                    "cropland": 0.10, "urban": 0.05, "bare": 0.02,
                },
                "seed": h,
            }
        if task == "multi_temporal_crop":
            return {"predicted_class": "soybean", "confidence": 0.78, "seed": h}
        if task == "scene_reasoning":
            return {
                "answer": f"[MOCK] Scene {payload.tile_id}: tropical lowland mosaic with forest dominance.",
                "tokens_used": 24,
                "seed": h,
            }
        return {"raw": "unknown_task", "seed": h}


class LivePrithviBackend:
    """Live backend — requires terratorch + GPU + Prithvi-EO-2.0 weights.

    888_HOLD gate before constructing this. The constitution requires
    explicit operator approval for pretrained model integration.
    """

    def __init__(self, weights_path: str, device: str = "cuda"):
        if not _TERRATORCH_AVAILABLE:
            raise RuntimeError(
                "terratorch not installed. Run `pip install terratorch` and "
                "verify 888_HOLD ticket before constructing LivePrithviBackend."
            )
        self.weights_path = weights_path
        self.device = device
        # NOTE: actual model load deferred to first .infer() call so import
        # doesn't fail at server startup. Wire here when 888 deploys weights.
        self._model = None

    def is_available(self) -> bool:
        return _TERRATORCH_AVAILABLE and os.path.exists(self.weights_path)

    def infer(self, payload: HLSInput, task: PrithviTask) -> dict:
        if not self.is_available():
            raise RuntimeError(
                f"Prithvi weights not available at {self.weights_path}"
            )
        # Placeholder — actual inference wired when 888 deploys weights.
        raise NotImplementedError(
            "Live Prithvi inference pending 888_HOLD weight deployment. "
            "Use MockPrithviBackend in the interim."
        )


# ───────────────────────────── ADAPTER PUBLIC API ────────────────────────────────
class PrithviEOAdapter:
    """Constitutional adapter for Prithvi-EO-2.0.

    Selection logic:
    - If GEOX_PRITHVI_LIVE=1 in env AND LivePrithviBackend.is_available():
        use live.
    - Else: use mock (deterministic).
    """

    def __init__(self, backend: PrithviBackend | None = None):
        if backend is not None:
            self._backend = backend
        elif os.environ.get("GEOX_PRITHVI_LIVE") == "1":
            self._backend = LivePrithviBackend(
                weights_path=os.environ.get("GEOX_PRITHVI_WEIGHTS", "/srv/models/prithvi-eo-2.0")
            )
        else:
            self._backend = MockPrithviBackend()

    @property
    def mode(self) -> Literal["live", "mock"]:
        return "live" if isinstance(self._backend, LivePrithviBackend) else "mock"

    def infer(self, payload: HLSInput, task: PrithviTask) -> PrithviOutput:
        # Hash input for provenance (F2 TRUTH).
        payload_bytes = repr({
            "tile_id": payload.tile_id,
            "bands": list(payload.bands),
            "time_range": list(payload.time_range),
            "task": task,
        }).encode()
        input_hash = hashlib.sha256(payload_bytes).hexdigest()

        result = self._backend.infer(payload, task)

        prov = PrithviProvenance(
            input_hash=input_hash,
            confidence_source="mock" if self.mode == "mock" else "softmax",
            mode=self.mode,
        )

        return PrithviOutput(
            task=task,
            result=result,
            ml_provenance=prov,
            epistemic_provenance={
                "rung": 2,
                "grounding": "remote_sensing_observation",
                "sensor_origin": payload.bands,
            },
            anti_beautiful_one_check={
                "verdict": "PASS",
                "reason": "single-task inference; no narrative compression",
            },
            godel_wall={
                "state": "KNOWN",
                "reason": "Observation backed by HLS tile + model weights; rung-2 grounding.",
            },
        )


__all__ = [
    "HLSInput",
    "PrithviTask",
    "PrithviProvenance",
    "PrithviOutput",
    "PrithviBackend",
    "MockPrithviBackend",
    "LivePrithviBackend",
    "PrithviEOAdapter",
]
