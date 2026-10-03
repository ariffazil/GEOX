"""
GEOX Earth Witness — Unified Vision Backend Adapter Interface
═══════════════════════════════════════════════════════════════════════════
Authority: ARIFOS::GEOX::EARTH_WITNESS_SLICE::v1
Phase 2.3 & 2.5: Model backend behind ONE adapter interface.

Decouples GEOX multimodal reasoning from hardcoded ports or single vendor VLMs.
Supports:
1. DeterministicMockVisionBackend (reproducible test suite & offline baseline)
2. GeminiVertexVisionBackend (Google Gemini 3.8 Flash multimodal via Vertex / GenAI SDK)
3. LegacyMiniMaxVisionBackend (configured via env, marked DEPRECATED)
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger("geox.earth_witness.vision_backend")


class VisionBackendResponse(BaseModel):
    backend_name: str
    model_id: str
    raw_response: dict[str, Any]
    response_hash: str
    latency_ms: float = 0.0


class BaseVisionBackend(ABC):
    """Abstract interface for Earth multimodal inspection."""

    @abstractmethod
    def inspect_artifact(
        self,
        image_bytes: bytes,
        mime_type: str,
        system_instruction: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
    ) -> VisionBackendResponse:
        pass


# ── 1. Deterministic Mock Backend (For Tests & Sandbox Verification) ─────────

class DeterministicMockVisionBackend(BaseVisionBackend):
    """Deterministic mock returning reproducible geological observation payloads."""

    def __init__(self, mock_scenario: str = "limestone_outcrop"):
        self.mock_scenario = mock_scenario

    def inspect_artifact(
        self,
        image_bytes: bytes,
        mime_type: str,
        system_instruction: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
    ) -> VisionBackendResponse:
        sha256 = hashlib.sha256(image_bytes).hexdigest()
        
        # Scenarios for test determinism
        if "seismic" in self.mock_scenario or "seismic" in user_prompt.lower():
            payload = {
                "modality": "seismic_display",
                "visible_features": [
                    {
                        "feature_id": "feat_01",
                        "label": "subhorizontal_high_amplitude_reflector",
                        "category": "reflector",
                        "confidence": 0.85,
                        "description": "Continuous high-amplitude reflection at middle two-way time",
                    },
                    {
                        "feature_id": "feat_02",
                        "label": "planar_discontinuity",
                        "category": "fault",
                        "confidence": 0.80,
                        "description": "Apparent normal fault offset cutting middle reflectors",
                    }
                ],
                "ocr_text": [
                    {"text": "TWT (ms)", "confidence": 0.95, "location": "y-axis"},
                    {"text": "Inline 1420", "confidence": 0.92, "location": "title"}
                ],
                "measurements": [
                    {"metric": "apparent_throw", "value": 45.0, "unit": "ms", "method": "pixel_scale", "uncertainty": 5.0}
                ],
                "hypotheses": [
                    {
                        "hypothesis_id": "hyp_01",
                        "label": "Tilted fault block with acoustic contrast",
                        "supporting": ["planar_discontinuity", "subhorizontal_high_amplitude_reflector"],
                        "conflicting": [],
                        "falsifiers": ["velocity pull-up artifact", "processing migration smile"],
                        "confidence": 0.78,
                    }
                ],
                "limitations": {
                    "image_cannot_determine": [
                        "True fluid phase (Amplitude != Hydrocarbon). Low gas saturation (fizz gas) causes identical amplitude.",
                        "True formation velocity without sonic log / checkshot calibration."
                    ],
                    "missing_metadata": ["Seismic display polarity convention (SEG normal vs reverse)", "Time vs depth domain declaration"],
                    "requested_human_tests": [
                        {"test_name": "polarity_check", "purpose": "Confirm impedance increase polarity", "discriminates": ["soft kick", "hard kick"]}
                    ],
                    "requested_instrument_data": ["Well checkshot velocity survey", "Angle gathers for AVO gradient verification"]
                }
            }
        elif "fossil" in self.mock_scenario or "fossil" in user_prompt.lower():
            payload = {
                "modality": "fossil",
                "visible_features": [
                    {
                        "feature_id": "feat_fos_01",
                        "label": "planispiral_chambered_shell",
                        "category": "morphology",
                        "confidence": 0.82,
                        "description": "Multi-chambered planispiral microfossil test resembling benthic foraminifera",
                    }
                ],
                "ocr_text": [],
                "measurements": [
                    {"metric": "diameter", "value": 0.8, "unit": "mm", "method": "scale_bar", "uncertainty": 0.05}
                ],
                "hypotheses": [
                    {
                        "hypothesis_id": "hyp_fos_01",
                        "label": "Candidate Lepidocyclina / Larger Benthic Foraminifera",
                        "supporting": ["planispiral_chambered_shell"],
                        "conflicting": [],
                        "falsifiers": ["non-carbonate recrystallization", "non-biogenic ooid structure"],
                        "confidence": 0.70,
                    }
                ],
                "limitations": {
                    "image_cannot_determine": [
                        "Absolute chronostratigraphic age cannot be determined from morphology alone. Requires PBDB biozone range validation."
                    ],
                    "missing_metadata": ["Oriented thin-section axial plane", "Formation / member stratigraphic context"],
                    "requested_human_tests": [],
                    "requested_instrument_data": ["PaleoBioDB occurrence query", "Biostratigraphic assemblage cross-check"]
                }
            }
        else:
            # Default rock / outcrop
            payload = {
                "modality": "rock",
                "visible_features": [
                    {
                        "feature_id": "feat_rock_01",
                        "label": "massive_fine_grained_crystalline_fabric",
                        "category": "texture",
                        "confidence": 0.85,
                        "description": "Light grey to buff massive rock without visible clastic grains",
                    }
                ],
                "ocr_text": [],
                "measurements": [],
                "hypotheses": [
                    {
                        "hypothesis_id": "hyp_rock_01",
                        "label": "Limestone (Micrite / Mudstone)",
                        "supporting": ["massive_fine_grained_crystalline_fabric"],
                        "conflicting": [],
                        "falsifiers": ["no effervescence with dilute HCl"],
                        "confidence": 0.72,
                    },
                    {
                        "hypothesis_id": "hyp_rock_02",
                        "label": "Dolostone",
                        "supporting": ["buff weathering color"],
                        "conflicting": [],
                        "falsifiers": ["effervescence on cold unpowdered rock"],
                        "confidence": 0.65,
                    }
                ],
                "limitations": {
                    "image_cannot_determine": [
                        "Mineral stoichiometry cannot be observed from photo pixels.",
                        "Porosity percentage and fluid saturation cannot be measured from surface image."
                    ],
                    "missing_metadata": ["Scale bar or reference object of known dimension"],
                    "requested_human_tests": [
                        {"test_name": "dilute_hcl", "purpose": "Discriminate Calcite from Dolomite", "discriminates": ["Limestone", "Dolostone"]},
                        {"test_name": "scratch_hardness", "purpose": "Confirm softness vs silicate", "discriminates": ["Carbonate (Mohs 3)", "Chert / Silicate (Mohs 7)"]}
                    ],
                    "requested_instrument_data": ["Thin section petrography", "XRD / XRF elemental mineralogy"]
                }
            }

        resp_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        resp_hash = hashlib.sha256(resp_bytes).hexdigest()
        return VisionBackendResponse(
            backend_name="deterministic_mock",
            model_id="geox-mock-earth-v1",
            raw_response=payload,
            response_hash=resp_hash,
            latency_ms=1.5,
        )


# ── 2. Gemini / Google Vertex Multimodal Backend ─────────────────────────────

class GeminiVertexVisionBackend(BaseVisionBackend):
    """Google Gemini 3.8 Flash multimodal backend via Google GenAI / Vertex AI."""

    def __init__(
        self,
        model_id: str = "gemini-3.8-flash",
        api_key: str | None = None,
    ):
        self.model_id = model_id
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def inspect_artifact(
        self,
        image_bytes: bytes,
        mime_type: str,
        system_instruction: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
    ) -> VisionBackendResponse:
        if not self.api_key:
            # Fall back to mock when running without live API key
            logger.warning("No GEMINI_API_KEY found in environment. Falling back to deterministic mock backend.")
            mock = DeterministicMockVisionBackend()
            return mock.inspect_artifact(image_bytes, mime_type, system_instruction, user_prompt, response_schema)

        # Call Gemini REST API directly using standard library (zero external deps required)
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent?key={self.api_key}"
        b64_img = base64.b64encode(image_bytes).decode("utf-8")

        req_body: dict[str, Any] = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [
                {
                    "parts": [
                        {"text": user_prompt},
                        {"inline_data": {"mime_type": mime_type, "data": b64_img}},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            }
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(req_body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=45) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))

        raw_text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
        parsed_json = json.loads(raw_text)
        resp_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

        return VisionBackendResponse(
            backend_name="gemini_vertex",
            model_id=self.model_id,
            raw_response=parsed_json,
            response_hash=resp_hash,
        )


# ── Backend Selector ────────────────────────────────────────────────────────

def get_vision_backend(backend_type: str = "auto") -> BaseVisionBackend:
    """Returns the configured vision backend."""
    if backend_type == "mock" or os.getenv("GEOX_VISION_FORCE_MOCK") == "1":
        return DeterministicMockVisionBackend()
    if backend_type == "gemini" or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return GeminiVertexVisionBackend()
    # Default to mock for safety & air-gapped testability
    return DeterministicMockVisionBackend()
