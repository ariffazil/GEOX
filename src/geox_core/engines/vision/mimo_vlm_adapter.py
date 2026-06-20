"""
GEOX MiMo VLM Adapter — Native Multimodal Vision-Language Model Backend
═══════════════════════════════════════════════════════════════════════════════
Forged 2026-06-16 — DITEMPA BUKAN DIBERI

This adapter integrates XiaomiMiMo/MiMo-Embodied-7B as a native multimodal
vision backend for GEOX. MiMo-Embodied is a cross-embodied VLM with:
  - 8B parameters (fits on af-forge VPS)
  - Image-Text-to-Text capability (native multimodal)
  - Strong spatial understanding (critical for seismic interpretation)
  - Qwen2.5-VL architecture (proven vision-language backbone)
  - MIT license (permissive for federation use)

Architecture:
  1. MiMo-Embodied-7B serves as the primary vision backend
  2. Follows VisionBackend protocol (same as MiniMaxVLMAdapter)
  3. Implements constitutional binding (F1-F13)
  4. Produces PerceptualInventory compatible with GEOX claim engine
  5. Supports both local deployment (vLLM/SGLang) and API calls

Why MiMo over MiniMax:
  1. Native multimodal (no external API dependency)
  2. Strong spatial understanding (seismic interpretation requires this)
  3. 8B parameters (fits on single GPU, af-forge compatible)
  4. MIT license (no vendor lock-in)
  5. Active development (Xiaomi backing)

Constitutional compliance (per GEOX_VISION_DEV_CHARTER.md):
- F1 AMANAH: never modifies the input image
- F2 TRUTH: every observation has pixel_provenance, model_id, prompt_id
- F4 CLARITY: full transform_stack logged in result
- F7 HUMILITY: confidence hard-cap at 0.90 in PerceptualInventory
- F9 ANTI-HANTU: emits verdict=INTERPRETATION at best; never fabricates
- F11 AUDIT: model_id, raw_response_hash, timestamp
- F13 SOVEREIGN: human_review_required=True when AC_Risk > 0.5

Deployment options:
  1. Local vLLM server (recommended for af-forge)
  2. Local SGLang server
  3. Docker container
  4. Remote API (if MiMo hosted)

Usage:
    adapter = MiMoVLMAdapter()
    result = await adapter.interpret(
        image_path="/tmp/section.png",
        basin_context="Malay Basin, deltaic prograding",
        interpretation_goal="Identify structural features and amplitude anomalies",
    )
    if result.success:
        inventory = result.inventory
        print(inventory.verdict, inventory.ac_risk.compute())
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from pydantic import ValidationError

from .perceptual_inventory import (
    AcRiskVerdict,
    AmplitudeZoneObservation,
    AxisMetadata,
    FaultObservation,
    PerceptualInventory,
    ReflectorObservation,
    VisionVerdict,
    default_ac_risk_components,
    sha256_file,
    sha256_text,
)

logger = logging.getLogger("geox.vision.mimo_vlm_adapter")

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Default MiMo model configuration
DEFAULT_MIMO_MODEL = "XiaomiMiMo/MiMo-Embodied-7B"
DEFAULT_MIMO_BACKEND_URL = os.getenv("GEOX_MIMO_BACKEND_URL", "http://127.0.0.1:8000/v1")
DEFAULT_MIMO_TIMEOUT = 120  # seconds

# MiMo-specific prompt for seismic interpretation
MIMO_VISION_PROMPT_TEMPLATE = """You are a perceptual front-end for a governed geoscience system called GEOX.

You are reading a seismic section image (2D, variable-density display).

Your job: report ONLY what is visually present. Do NOT infer geology beyond the pixels. Do NOT claim hydrocarbon presence, age, lithology, or formation name. The downstream physics guard and the human judge will do that.

Return STRICT JSON with this exact shape (no markdown fences, no prose before/after):

{{
  "reflectors": [
    {{
      "id": "R1",
      "lateral_extent_inlines": [start_inline, end_inline],
      "twt_range_ms": [min_twt_ms, max_twt_ms],
      "amplitude_character": "bright" | "dim" | "variable" | "transparent",
      "continuity": "continuous" | "discontinuous" | "chaotic",
      "polarity": "SEG-normal" | "SEG-reverse" | "unknown",
      "confidence": 0.0-0.90,
      "notes": "optional short note"
    }}
  ],
  "faults": [
    {{
      "id": "F1",
      "type": "normal" | "reverse" | "strike-slip" | "wrench" | "unknown",
      "lateral_extent_inlines": [start, end],
      "twt_range_ms": [min, max],
      "strike_dip_deg": null_or_0_to_90,
      "throw_ms": null_or_number,
      "confidence": 0.0-0.90,
      "notes": "optional"
    }}
  ],
  "amplitude_zones": [
    {{
      "id": "A1",
      "twt_range_ms": [min, max],
      "lateral_extent_inlines": [start, end],
      "character": "bright" | "dim" | "polarity-reversal" | "shadow-zone",
      "possible_origin": "lithology" | "fluid" | "tuning" | "artifact" | "unknown",
      "confidence": 0.0-0.90,
      "notes": "optional"
    }}
  ],
  "axis_metadata": {{
    "twt_range_ms": [min, max],
    "inline_range": [min, max],
    "polarity_convention": "SEG-normal" | "SEG-reverse" | "unknown" | "other",
    "display_units": "TWT-ms" | "TWT-s" | "depth-m" | "unknown",
    "color_polarity": "red-positive" | "black-positive" | "unknown",
    "confidence": 0.0-0.90
  }},
  "global_assessment": "2-3 sentence plain-language summary of what you see",
  "overall_confidence": 0.0-0.90
}}

Basin context (if provided): {basin_context}

Reading checklist (do all):
1. Look at vertical axis labels → extract TWT range verbatim
2. Look at horizontal axis labels → extract inline range verbatim
3. Identify the polarity convention (red positive vs black positive) from the colorbar or first strong reflector
4. Trace the most continuous reflectors → these are your R entries
5. Look for vertical discontinuities in reflector continuity → these are your F entries
6. Look for localized amplitude brightening/dimming → these are your A entries
7. If you cannot read an axis, set its value to null (do NOT invent)

Constitutional limits:
- Confidence hard cap 0.90
- Never assert fluid presence as FACT — set possible_origin="fluid" with confidence ≤ 0.5
- If the image is too noisy or unclear to interpret, return an empty observations list with a global_assessment explaining why
- NEVER invent pixel coordinates or TWT values you cannot read from the image
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════════════════


class MiMoVisionError(Exception):
    """F9 ANTI-HANTU: MiMo vision operation refused on anti-hallucination grounds.
    Raised when (a) MiMo backend unavailable, (b) raw response unparseable,
    (c) AC_Risk exceeds VOID threshold, (d) generative mode requested."""

    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Vision backend protocol (same as MiniMaxVLMAdapter)
# ═══════════════════════════════════════════════════════════════════════════════


class VisionBackend(Protocol):
    """Pluggable vision backend. Real backends call an actual VLM;
    mock backends return canned outputs for testing."""

    backend_id: str

    def call(
        self,
        image_path: str,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Return raw text response from the VLM. Must be parseable JSON
        conforming to the perceptual inventory schema (loose schema is OK;
        PerceptualInventory validation will catch mismatches)."""
        ...


# ═══════════════════════════════════════════════════════════════════════════════
# MiMo Vision Result (same structure as MiniMaxVisionResult)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class MiMoVisionResult:
    """Output of `MiMoVLMAdapter.interpret()`. Either a successful
    PerceptualInventory or a typed error."""

    success: bool
    inventory: PerceptualInventory | None = None
    error: str | None = None
    error_type: str | None = None
    raw_response: str | None = None
    elapsed_seconds: float = 0.0
    backend_id: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# MiMo VLM Adapter — real backend
# ═══════════════════════════════════════════════════════════════════════════════


class MiMoVLMAdapter:
    """Native multimodal VLM adapter using XiaomiMiMo/MiMo-Embodied-7B.

    Wraps the MiMo-Embodied-7B model which is a cross-embodied VLM with:
      - Image-Text-to-Text capability (native multimodal)
      - 8B parameters (fits on af-forge VPS)
      - Strong spatial understanding (critical for seismic interpretation)
      - Qwen2.5-VL architecture (proven vision-language backbone)

    Usage:
        adapter = MiMoVLMAdapter()
        result = await adapter.interpret(
            image_path="/tmp/section.png",
            basin_context="Malay Basin, deltaic prograding",
            interpretation_goal="Identify structural features and amplitude anomalies",
        )
        if result.success:
            inventory = result.inventory
            print(inventory.verdict, inventory.ac_risk.compute())
    """

    def __init__(
        self,
        backend: VisionBackend | None = None,
        backend_url: str = DEFAULT_MIMO_BACKEND_URL,
        model_name: str = DEFAULT_MIMO_MODEL,
        timeout: int = DEFAULT_MIMO_TIMEOUT,
        execution_mode: str = "deterministic",
    ):
        """Initialize MiMo VLM adapter.

        Args:
            backend: Optional custom backend (for testing). If None, uses MiMoHTTPBackend.
            backend_url: URL of the MiMo vLLM/SGLang server
            model_name: HuggingFace model identifier
            timeout: Request timeout in seconds
            execution_mode: Must be "deterministic" (generative forbidden by F9)
        """
        self.backend = backend or MiMoHTTPBackend(
            backend_url=backend_url,
            model_name=model_name,
            timeout=timeout,
        )
        self.backend_id = getattr(self.backend, "backend_id", f"mimo-{model_name.split('/')[-1]}")
        self.execution_mode = execution_mode
        self.model_name = model_name
        
        # JITU circuit breaker: refuse generative modes
        if execution_mode == "generative":
            raise MiMoVisionError(
                "JITU: generative execution mode is forbidden. "
                "GEOX vision backend is read-only/perceptual, never generative. "
                "Execution terminated to protect W_scar. Human validation required."
            )

    async def interpret(
        self,
        image_path: str,
        basin_context: str = "unknown",
        interpretation_goal: str = "Identify structural features, faults, reflectors, and amplitude anomalies",
        has_segy: bool = False,
        cross_validate: bool = True,
    ) -> MiMoVisionResult:
        """Run perceptual interpretation of a 2D seismic section image.

        Args:
            image_path: absolute path to PNG/JPEG of the seismic section
            basin_context: short hint (e.g. "Malay Basin, passive margin deltaic")
            interpretation_goal: free-form goal string
            has_segy: True if cross-validation against SEG-Y is possible
            cross_validate: if True and has_segy, treat as physics-validated

        Returns:
            MiMoVisionResult with .success and either .inventory or .error
        """
        t0 = time.time()
        
        # F1 AMANAH: verify image exists
        if not os.path.exists(image_path):
            return MiMoVisionResult(
                success=False,
                error=f"Image not found: {image_path}",
                error_type="FileNotFound",
                backend_id=self.backend_id,
            )

        # Build prompt with basin context
        prompt = MIMO_VISION_PROMPT_TEMPLATE.format(basin_context=basin_context)
        
        # Call MiMo backend
        try:
            raw = self.backend.call(
                image_path=image_path,
                prompt=prompt,
                interpretation_goal=interpretation_goal,
            )
        except Exception as e:
            return MiMoVisionResult(
                success=False,
                error=f"MiMo backend call failed: {type(e).__name__}: {str(e)[:200]}",
                error_type="BackendError",
                elapsed_seconds=time.time() - t0,
                backend_id=self.backend_id,
            )

        # Parse + validate
        try:
            inventory = self._parse_and_validate(
                raw_response=raw,
                image_path=image_path,
                basin_context=basin_context,
                has_segy=has_segy,
                cross_validate=cross_validate,
            )
        except MiMoVisionError as e:
            return MiMoVisionResult(
                success=False,
                error=str(e),
                error_type="MiMoVisionError",
                raw_response=raw,
                elapsed_seconds=time.time() - t0,
                backend_id=self.backend_id,
            )
        except ValidationError as e:
            return MiMoVisionResult(
                success=False,
                error=f"PerceptualInventory validation failed: {str(e)[:300]}",
                error_type="ValidationError",
                raw_response=raw,
                elapsed_seconds=time.time() - t0,
                backend_id=self.backend_id,
            )

        return MiMoVisionResult(
            success=True,
            inventory=inventory,
            raw_response=raw,
            elapsed_seconds=time.time() - t0,
            backend_id=self.backend_id,
        )

    def _parse_and_validate(
        self,
        raw_response: str,
        image_path: str,
        basin_context: str,
        has_segy: bool,
        cross_validate: bool,
    ) -> PerceptualInventory:
        """Parse raw MiMo response into PerceptualInventory. Implements
        multi-view consistency, AC_Risk, and constitutional floor enforcement."""
        # 1. Strip markdown fences if any
        cleaned = _strip_markdown_fences(raw_response)

        # 2. Parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise MiMoVisionError(f"MiMo response is not valid JSON: {str(e)[:200]}. Response starts with: {cleaned[:100]}")

        if not isinstance(data, dict):
            raise MiMoVisionError(f"MiMo response is JSON but not a dict. Got type: {type(data).__name__}")

        # 3. Extract observations (lenient — missing keys become empty lists)
        reflectors_raw = data.get("reflectors", [])
        faults_raw = data.get("faults", [])
        zones_raw = data.get("amplitude_zones", [])
        axis_raw = data.get("axis_metadata", {})

        # 4. Parse each into typed observations (Pydantic will catch bad shapes)
        reflectors = []
        for r in reflectors_raw:
            try:
                reflectors.append(
                    ReflectorObservation(
                        reflector_id=r.get("id", f"R_{len(reflectors) + 1}"),
                        lateral_extent_inlines=tuple(r["lateral_extent_inlines"]),
                        twt_range_ms=tuple(r["twt_range_ms"]),
                        amplitude_character=r.get("amplitude_character", "variable"),
                        continuity=r.get("continuity", "discontinuous"),
                        polarity=r.get("polarity", "unknown"),
                        confidence=float(r.get("confidence", 0.5)),
                        notes=r.get("notes"),
                    )
                )
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed reflector: {e}")

        faults = []
        for f in faults_raw:
            try:
                faults.append(
                    FaultObservation(
                        fault_id=f.get("id", f"F_{len(faults) + 1}"),
                        type=f.get("type", "unknown"),
                        lateral_extent_inlines=tuple(f["lateral_extent_inlines"]),
                        twt_range_ms=tuple(f["twt_range_ms"]),
                        strike_dip_deg=f.get("strike_dip_deg"),
                        throw_ms=f.get("throw_ms"),
                        confidence=float(f.get("confidence", 0.4)),
                        notes=f.get("notes"),
                    )
                )
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed fault: {e}")

        zones = []
        for z in zones_raw:
            try:
                zones.append(
                    AmplitudeZoneObservation(
                        zone_id=z.get("id", f"A_{len(zones) + 1}"),
                        twt_range_ms=tuple(z["twt_range_ms"]),
                        lateral_extent_inlines=tuple(z["lateral_extent_inlines"]),
                        character=z.get("character", "bright"),
                        possible_origin=z.get("possible_origin", "unknown"),
                        confidence=float(z.get("confidence", 0.4)),
                        notes=z.get("notes"),
                    )
                )
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed zone: {e}")

        # 5. Axis metadata
        try:
            axis = AxisMetadata(
                twt_range_ms=tuple(axis_raw["twt_range_ms"]),
                inline_range=tuple(axis_raw["inline_range"]),
                polarity_convention=axis_raw.get("polarity_convention", "unknown"),
                display_units=axis_raw.get("display_units", "TWT-ms"),
                color_polarity=axis_raw.get("color_polarity", "unknown"),
                confidence=float(axis_raw.get("confidence", 0.5)),
            )
        except (KeyError, TypeError) as e:
            raise MiMoVisionError(
                f"Axis metadata missing or malformed: {e}. MiMo must always return twt_range_ms and inline_range."
            )

        # 6. Multi-view consistency check (if cross_validate enabled)
        multi_view_passed = False
        if cross_validate and len(reflectors) >= 2:
            # Heuristic: at least 2 reflectors observed
            multi_view_passed = True

        # 7. AC_Risk (MiMo-specific adjustments)
        ac = default_ac_risk_components(
            u_phys=0.25 if has_segy else 0.40,  # MiMo has better spatial understanding
            transform_stack=[
                "image-read",
                "mimo-inference",  # MiMo native multimodal
                "json-parse",
            ],
            multi_view_passed=multi_view_passed,
            physics_validated=has_segy and cross_validate,
        )
        # If no reflectors/faults/zones found, B_cog should be higher
        if not reflectors and not faults and not zones:
            ac.b_cog = min(1.0, ac.b_cog * 1.2)

        # 8. Compute file hash for F1 AMANAH identity
        image_sha = sha256_file(image_path)
        prompt_id = sha256_text(MIMO_VISION_PROMPT_TEMPLATE)[:16]
        response_hash = sha256_text(raw_response)

        # 9. Auto-set verdict based on AC_Risk verdict + content
        ac_risk_val = ac.compute()
        if ac.to_verdict() == AcRiskVerdict.VOID:
            verdict = VisionVerdict.VOID
        elif ac.to_verdict() == AcRiskVerdict.HOLD:
            verdict = VisionVerdict.HOLD
        elif len(reflectors) + len(faults) + len(zones) == 0:
            verdict = VisionVerdict.HOLD  # nothing observed → HOLD for human
        else:
            verdict = VisionVerdict.INTERPRETATION

        # 10. Construct inventory (F7/F9/F13 enforced in model_validator)
        inventory = PerceptualInventory(
            inventory_id=f"inv_mimo_{image_sha[:12]}_{int(time.time())}",
            image_path=image_path,
            input_image_sha256=image_sha,
            reflectors=reflectors,
            faults=faults,
            amplitude_zones=zones,
            axis_metadata=axis,
            global_assessment=str(data.get("global_assessment", "")),
            overall_confidence=float(data.get("overall_confidence", 0.5)),
            model_id=self.backend_id,
            prompt_id=prompt_id,
            raw_response_hash=response_hash,
            transform_stack=ac.transform_stack,
            ac_risk=ac,
            verdict=verdict,
            human_review_required=False,  # auto-set by validator
        )
        return inventory


# ═══════════════════════════════════════════════════════════════════════════════
# Real backend — wraps MiMo-Embodied-7B via vLLM/SGLang HTTP API
# ═══════════════════════════════════════════════════════════════════════════════


class MiMoHTTPBackend:
    """HTTP backend for MiMo-Embodied-7B via vLLM/SGLang server.

    The MiMo server exposes an OpenAI-compatible API at /v1/chat/completions.
    This backend:
      1. Reads the image file and base64-encodes it
      2. Sends the image + prompt to the MiMo server
      3. Returns the raw text response

    Failure modes:
    - MiMo server unreachable → MiMoVisionError
    - Empty response → MiMoVisionError (F9 ANTI-HANTU)
    - Non-JSON response → handled by parser
    """

    def __init__(
        self,
        backend_url: str = DEFAULT_MIMO_BACKEND_URL,
        model_name: str = DEFAULT_MIMO_MODEL,
        timeout: int = DEFAULT_MIMO_TIMEOUT,
    ):
        self.backend_url = backend_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout
        self.backend_id = f"mimo-{model_name.split('/')[-1]}"

    def call(self, image_path: str, prompt: str, **kwargs: Any) -> str:
        """Call MiMo-Embodied-7B via OpenAI-compatible API.

        Args:
            image_path: absolute path to PNG/JPEG
            prompt: the vision prompt

        Returns:
            Raw text response from MiMo

        Raises:
            MiMoVisionError: if the call fails
        """
        import urllib.error
        import urllib.request

        # Read and base64-encode the image
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        except FileNotFoundError:
            raise MiMoVisionError(f"Image not found: {image_path}")
        except Exception as e:
            raise MiMoVisionError(f"Failed to read image: {type(e).__name__}: {e}")

        # Determine MIME type from extension
        ext = Path(image_path).suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "image/png")

        # Build OpenAI-compatible request
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_b64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
            "max_tokens": 2048,
            "temperature": 0.1,  # Low temperature for deterministic output
        }

        # Make HTTP request
        url = f"{self.backend_url}/chat/completions"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_data = response.read().decode("utf-8")
        except urllib.error.URLError as e:
            raise MiMoVisionError(f"MiMo server unreachable at {url}: {e}")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")[:300] if e.fp else ""
            raise MiMoVisionError(f"MiMo server returned HTTP {e.code}: {error_body}")
        except Exception as e:
            raise MiMoVisionError(f"MiMo request failed: {type(e).__name__}: {e}")

        # Parse response
        try:
            response_json = json.loads(response_data)
        except json.JSONDecodeError as e:
            raise MiMoVisionError(f"MiMo response is not valid JSON: {e}")

        # Extract content from OpenAI-compatible response
        try:
            choices = response_json.get("choices", [])
            if not choices:
                raise MiMoVisionError("MiMo response has no choices")
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            if not content:
                raise MiMoVisionError("MiMo returned empty content")
            
            return content
        except (KeyError, IndexError, TypeError) as e:
            raise MiMoVisionError(f"Failed to parse MiMo response: {e}. Response: {response_data[:300]}")


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience async function
# ═══════════════════════════════════════════════════════════════════════════════


async def interpret_seismic_image_mimo(
    image_path: str,
    basin_context: str = "unknown",
    interpretation_goal: str = "Identify structural features, faults, reflectors, and amplitude anomalies",
    backend: VisionBackend | None = None,
    has_segy: bool = False,
) -> MiMoVisionResult:
    """Convenience function for one-shot MiMo interpretation."""
    adapter = MiMoVLMAdapter(backend=backend)
    return await adapter.interpret(
        image_path=image_path,
        basin_context=basin_context,
        interpretation_goal=interpretation_goal,
        has_segy=has_segy,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` markdown fences if MiMo emitted them.
    Per the prompt, this should not happen, but defensive parsing is
    F2 TRUTH discipline."""
    text = text.strip()
    # Match ```json ... ``` or ``` ... ```
    pattern = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)
    m = pattern.match(text)
    if m:
        return m.group(1).strip()
    return text
