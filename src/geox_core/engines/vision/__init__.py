"""
GEOX Vision V1 — Layer 1 (Vision Ingest) Engine
═══════════════════════════════════════════════════════════════════════════════
Forged 2026-06-07 — DITEMPA BUKAN DIBERI

This package implements the **Vision Ingest Layer** of the GEOX four-layer
vision architecture (per `GEOX_VISION_DEV_CHARTER.md` and
`VISION_INTELLIGENCE_IMPLEMENTATION.md`, Phase 3 Real VLM).

Working rule (per Charter §"Working Rule"):
    pixels → transforms → physics → decision

Three artifacts ship in this package:

1. `perceptual_inventory.py` — Pydantic v2 schemas for the Layer-1 output
   contract. This is the missing piece between VLM output and the GEOX
   claim engine.

2. `minimax_vlm_adapter.py` — Real VLM backend adapter that wraps the
   deployed `minimax-code_understand_image` MCP tool (port 18091) as a
   Python-callable vision backend. Replaces the mock backend that the
   2026-04-10 Implementation Summary flagged as "Real VLM adapters
   not yet wired".

3. `vision_test_harness.py` — Two test loops:
       a. Synthetic forward-inverse (ground truth, precision/recall)
       b. Public real seismic (candidate interpretation, no ground truth,
          emits INTERPRETATION + human_review_required=True)

Constitutional compliance (per GEOX_VISION_DEV_CHARTER.md):
- F1 AMANAH: never modifies the input image
- F2 TRUTH: every observation has `pixel_provenance` and `prompt_id`
- F4 CLARITY: full transform stack logged in result
- F7 HUMILITY: confidence hard-cap at 0.90, baseline uncertainty 0.15
- F9 ANTI-HANTU: emits verdict=INTERPRETATION not SEAL; never fabricates
- F11 AUDIT: model_id + raw_response_hash + timestamp on every call
- F13 SOVEREIGN: never self-authorizes; human_review_required=True when
                 AC_Risk > 0.5

Cross-Modal Fidelity Theorem (ratified 2026-06-05) constrains the
adapter's output to a Pydantic-typed grammar that survives round-trip
through PNG → JSON → MCP → claim engine without corruption.
"""

from __future__ import annotations

__version__ = "2026.06.07-v1"
__author__ = "arifOS Forge Agent Ω (autonomous, F13 SOVEREIGN delegation)"
__status__ = "EXPERIMENTAL — not registered as canonical tool, not in production"

# Public surface (re-exports for convenience)
from .mimo_vlm_adapter import (
    MiMoHTTPBackend,
    MiMoVisionError,
    MiMoVisionResult,
    MiMoVLMAdapter,
    interpret_seismic_image_mimo,
)
from .minimax_vlm_adapter import (
    AntiHantuError,
    MiniMaxVLMAdapter,
    VisionBackend,
    VisionResult,
    interpret_seismic_image,
)
from .perceptual_inventory import (
    AcRiskComponents,
    AcRiskVerdict,
    AmplitudeCharacter,
    AmplitudeZoneCharacter,
    AmplitudeZoneObservation,
    AmplitudeZoneOrigin,
    AxisMetadata,
    DisplayColorPolarity,
    DisplayUnits,
    FaultObservation,
    FaultType,
    PerceptualInventory,
    PolarityConvention,
    ReflectorContinuity,
    ReflectorObservation,
    VisionVerdict,
    default_ac_risk_components,
    sha256_file,
    sha256_text,
)

__all__ = [
    # Inventory schemas
    "PerceptualInventory",
    "ReflectorObservation",
    "FaultObservation",
    "AmplitudeZoneObservation",
    "AxisMetadata",
    "AcRiskComponents",
    "VisionVerdict",
    "AcRiskVerdict",
    # Enums
    "AmplitudeCharacter",
    "ReflectorContinuity",
    "PolarityConvention",
    "FaultType",
    "AmplitudeZoneCharacter",
    "AmplitudeZoneOrigin",
    "DisplayColorPolarity",
    "DisplayUnits",
    # Helpers
    "default_ac_risk_components",
    "sha256_file",
    "sha256_text",
    # MiniMax Adapter
    "MiniMaxVLMAdapter",
    "VisionBackend",
    "VisionResult",
    "AntiHantuError",
    "interpret_seismic_image",
    # MiMo Adapter
    "MiMoVLMAdapter",
    "MiMoVisionResult",
    "MiMoVisionError",
    "MiMoHTTPBackend",
    "interpret_seismic_image_mimo",
]
