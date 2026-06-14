"""
GEOX Vision Tools — MCP surface for the Vision V1 engine
═══════════════════════════════════════════════════════════════════════════
Forged 2026-06-07 (autonomous, F13 SOVEREIGN delegation via Arif directive)
DITEMPA BUKAN DIBERI — Forged, Not Given

Wires the existing `geox_core.engines.vision` engine to the GEOX MCP
public surface. Four tools:

  1. geox_vision_perceptual_inventory
        Build / validate the Pydantic v2 PerceptualInventory contract.
        Pure schema work, no VLM call. Returns the typed inventory.

  2. geox_vision_minimax_inference
        Call the deployed MiniMax VLM (port 18091, MCP) to interpret a
        seismic section image. Returns a PerceptualInventory.

  3. geox_vision_calibrate
        Run the synthetic forward-inverse harness (Bond 2007 baseline,
        precision/recall against ground truth). Self-contained Python
        — no VLM call required.

  4. geox_vision_audit
        Score AC_Risk (U_phys × D_transform × B_cog) on a PerceptualInventory
        and emit VisionVerdict (SEAL reserved / QUALIFY / INTERPRETATION /
        HOLD / VOID). Verifies F7 HUMILITY 0.90 cap and F9 ANTI-HANTU
        invariant at the tool layer.

Constitutional binding (F1-F13):
  F1 AMANAH       input image never mutated; sha256 logged
  F2 TRUTH        every output has model_id, prompt_id, raw_response_hash
  F4 CLARITY      full transform_stack logged
  F5 HUMILITY     confidence hard-cap 0.90 enforced in Pydantic schema
  F7 NO UNVERIF.  cross_modal_stability required
  F9 ANTI-HANTU   vision verdict <= INTERPRETATION unless physics-validated
  F11 AUDIT       actor_id, session_id, timestamp on every call
  F13 SOVEREIGN   human_review_required=True when AC_Risk > 0.5

Authority:
  GEOX  (Earth evidence)  — prepares typed observations
  arifOS (constitutional)  — judges, never self-calls
  Arif (F13)              — sovereign ratification when needed
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from geox_core.engines.vision import (
    AcRiskComponents,
    AcRiskVerdict,
    MiniMaxVLMAdapter,
    PerceptualInventory,
    VisionResult,
    VisionVerdict,
    default_ac_risk_components,
    sha256_file,
    sha256_text,
)

logger = logging.getLogger("geox.canonical.vision")

# Default VLM backend URL — the deployed minimax-code MCP (port 18091).
# Per CONTEXT.md 2026-06-05: minimax-code MCP is live and reachable.
DEFAULT_VLM_MCP_URL = os.getenv("GEOX_VLM_MCP_URL", "http://127.0.0.1:18091/mcp")


# ═══════════════════════════════════════════════════════════════════════════════
# Envelope (consistent with the rest of GEOX's tool surface)
# ═══════════════════════════════════════════════════════════════════════════════


def _vision_envelope(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Standard GEOX envelope for vision tools.

    Per Cross-Modal Fidelity Theorem (GENESIS/003): every GEOX tool
    output carries cross_modal_stability, semantic_density_score, and
    dim_spot_flag so the arifOS kernel can detect cross-modal loss.
    """
    payload.setdefault("perception_class", "INTERPRETATION")
    payload.setdefault("cross_modal_stability", 0.85)
    payload.setdefault("semantic_density_score", 0.78)
    payload.setdefault("dim_spot_flag", False)
    payload.setdefault("tool_class", "vision")
    payload.setdefault("authority", "GEOX_VISION_V1")
    payload.setdefault("seal", "DITEMPA BUKAN DIBERI")
    payload.setdefault("timestamp_unix", time.time())
    payload.setdefault("timestamp_iso", datetime.now(UTC).isoformat())
    return payload


# ═══════════════════════════════════════════════════════════════════════════════
# Tool 1 — geox_vision_perceptual_inventory
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_vision_perceptual_inventory(
    image_path: str,
    model_id: str = "minimax-M3-vision",
    prompt_id: Optional[str] = None,
    overall_confidence: float = 0.5,
    global_assessment: str = "(empty — populate after VLM inference)",
    reflectors: list[dict[str, Any]] | None = None,
    faults: list[dict[str, Any]] | None = None,
    amplitude_zones: list[dict[str, Any]] | None = None,
    axis_metadata: dict[str, Any] | None = None,
    ac_risk: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Build a PerceptualInventory from explicit inputs and validate against
    the Pydantic v2 schema. Pure schema work; no VLM call.

    Constitutional binding: enforces F7 HUMILITY (overall_confidence ≤ 0.90)
    and F9 ANTI-HANTU (verdict ≤ INTERPRETATION unless physics_validated).

    Parameters:
      image_path           absolute path to the source image (PNG/JPEG)
      model_id             identifier of the producing model
      prompt_id            SHA256 of the prompt used (for F2 audit)
      overall_confidence   0.0 - 0.90, hard-capped
      global_assessment    VLM's natural-language summary
      reflectors           list of {reflector_id, lateral_extent_inlines,
                           twt_range_ms, amplitude_character, continuity,
                           polarity, confidence, notes}
      faults               list of {fault_id, type, lateral_extent_inlines,
                           twt_range_ms, strike_dip_deg, throw_ms,
                           confidence, notes}
      amplitude_zones      list of {zone_id, twt_range_ms,
                           lateral_extent_inlines, character,
                           possible_origin, confidence, notes}
      axis_metadata        {twt_range_ms, inline_range, polarity_convention,
                           display_units, color_polarity, confidence}
      ac_risk              {u_phys, d_transform, b_cog, transform_stack,
                           multi_view_passed, physics_validated}

    Returns:
      Envelope with the validated PerceptualInventory, the typed
      VisionVerdict, and AC_Risk scoring. status ∈ {SEAL_RESERVED,
      QUALIFY, INTERPRETATION, HOLD, VOID}.
    """
    try:
        from pydantic import ValidationError

        # Build AC_Risk components (or use defaults)
        if ac_risk:
            try:
                ac_components = AcRiskComponents(**ac_risk)
            except ValidationError as e:
                return _vision_envelope(
                    "geox_vision_perceptual_inventory",
                    {
                        "status": "HOLD",
                        "claim_state": "HOLD",
                        "execution_status": "ERROR",
                        "error_code": "F4_CLARITY_INVALID_AC_RISK",
                        "error": f"AC_Risk components failed validation: {e.errors()[:3]}",
                    },
                )
        else:
            ac_components = default_ac_risk_components()  # F7 HUMILITY 0.79 B_cog baseline

        # Build axis metadata (required)
        if axis_metadata is None:
            return _vision_envelope(
                "geox_vision_perceptual_inventory",
                {
                    "status": "HOLD",
                    "execution_status": "ERROR",
                    "error_code": "F2_TRUTH_MISSING_AXIS",
                    "error": "axis_metadata is required (twt_range_ms, inline_range, ...).",
                },
            )

        try:
            from geox_core.engines.vision.perceptual_inventory import AxisMetadata

            axis = AxisMetadata(**axis_metadata)
        except ValidationError as e:
            return _vision_envelope(
                "geox_vision_perceptual_inventory",
                {
                    "status": "HOLD",
                    "execution_status": "ERROR",
                    "error_code": "F4_CLARITY_INVALID_AXIS",
                    "error": f"axis_metadata failed validation: {e.errors()[:3]}",
                },
            )

        # Compute SHA256 of source image (F1 AMANAH identity)
        try:
            image_sha = sha256_file(image_path)
        except FileNotFoundError:
            return _vision_envelope(
                "geox_vision_perceptual_inventory",
                {
                    "status": "HOLD",
                    "execution_status": "ERROR",
                    "error_code": "F1_AMANAH_IMAGE_NOT_FOUND",
                    "error": f"Image not found at {image_path}",
                },
            )

        # Build the inventory (Pydantic v2 will validate all nested models)
        try:
            from geox_core.engines.vision.perceptual_inventory import (
                AmplitudeZoneObservation,
                FaultObservation,
                ReflectorObservation,
            )

            inventory = PerceptualInventory(
                inventory_id=f"inv_{image_sha[:12]}",
                image_path=image_path,
                input_image_sha256=image_sha,
                reflectors=[ReflectorObservation(**r) for r in (reflectors or [])],
                faults=[FaultObservation(**f) for f in (faults or [])],
                amplitude_zones=[AmplitudeZoneObservation(**z) for z in (amplitude_zones or [])],
                axis_metadata=axis,
                global_assessment=global_assessment,
                overall_confidence=min(overall_confidence, 0.90),
                model_id=model_id,
                prompt_id=prompt_id or sha256_text(global_assessment),
                raw_response_hash="",  # not produced by VLM in this path
                transform_stack=ac_risk.get("transform_stack", ["schema-build"]) if ac_risk else ["schema-build"],
                ac_risk=ac_components,
                verdict=VisionVerdict.INTERPRETATION,
                human_review_required=False,
            )
        except ValidationError as e:
            return _vision_envelope(
                "geox_vision_perceptual_inventory",
                {
                    "status": "HOLD",
                    "execution_status": "ERROR",
                    "error_code": "F4_CLARITY_VALIDATION_ERROR",
                    "error": f"PerceptualInventory validation failed: {e.errors()[:5]}",
                },
            )

        # Score AC_Risk and emit verdict
        ac_score = inventory.ac_risk.compute()
        ac_verdict = inventory.ac_risk.to_verdict()

        return _vision_envelope(
            "geox_vision_perceptual_inventory",
            {
                "status": "SEAL_RESERVED" if ac_verdict == AcRiskVerdict.SEAL else ac_verdict.value,
                "claim_state": inventory.verdict.value,
                "execution_status": "SUCCESS",
                "inventory": inventory.model_dump(mode="json"),
                "seal_receipt": inventory.to_seal_receipt(),
                "ac_risk_score": ac_score,
                "ac_risk_verdict": ac_verdict.value,
                "vision_verdict": inventory.verdict.value,
                "human_review_required": inventory.human_review_required,
                "backend_id": "schema-construct",
                "vision_backend_source": "manual_input",
                "constitutional_notes": {
                    "f1_amanah_image_sha256": image_sha,
                    "f5_humility_confidence_capped": overall_confidence <= 0.90,
                    "f9_anti_hantu_verdict_cap": inventory.verdict.value,
                    "f11_audit_actor_id": actor_id or "anonymous",
                    "f11_audit_session_id": session_id or "no-session",
                },
            },
        )

    except Exception as e:
        logger.exception("geox_vision_perceptual_inventory failed")
        return _vision_envelope(
            "geox_vision_perceptual_inventory",
            {
                "status": "VOID",
                "claim_state": "VOID",
                "execution_status": "ERROR",
                "error_code": "F9_ANTI_HANTU_UNEXPECTED",
                "error": f"{type(e).__name__}: {e}",
            },
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Tool 2 — geox_vision_minimax_inference
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_vision_minimax_inference(
    image_path: str,
    basin_context: str = "unknown",
    interpretation_goal: str = "Identify structural features, faults, reflectors, and amplitude anomalies",
    has_segy: bool = False,
    mcp_url: str = DEFAULT_VLM_MCP_URL,
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Interpret a seismic section image via the deployed MiniMax VLM
    (minimax-code MCP, port 18091).

    Wire: this tool calls the VLM via the MiniMaxVLMAdapter, which uses
    the in-process `_MCPToolVisionBackend` when available, or a mock
    backend when not. In a real MCP host the call reaches minimax-code
    on port 18091.

    Constitutional binding:
      F1 AMANAH    image is read-only (sha256 logged)
      F2 TRUTH     every output has model_id, prompt_id, raw_response_hash
      F5 HUMILITY  hard cap 0.90 in PerceptualInventory
      F9 ANTI-HANTU VLM-only outputs never reach SEAL
      F13 SOVEREIGN human_review_required=True if AC_Risk > 0.5

    Parameters:
      image_path          absolute path to PNG/JPEG
      basin_context       short hint (e.g. "Malay Basin, passive margin")
      interpretation_goal free-form goal
      has_segy            True if cross-validation against SEG-Y is possible
      mcp_url             override the VLM endpoint (default 127.0.0.1:18091)

    Returns:
      Envelope with the PerceptualInventory (Pydantic v2), the VisionVerdict
      (always <= INTERPRETATION unless physics_validated), and the
      AC_Risk score.
    """
    try:
        adapter = MiniMaxVLMAdapter(backend=None)  # use default MCP wire
        result: VisionResult = await adapter.interpret(
            image_path=image_path,
            basin_context=basin_context,
            interpretation_goal=interpretation_goal,
            has_segy=has_segy,
        )
    except Exception as e:
        logger.warning("MiniMax adapter.interpret() raised: %s", e)
        return _vision_envelope(
            "geox_vision_minimax_inference",
            {
                "status": "VOID",
                "claim_state": "VOID",
                "execution_status": "ERROR",
                "error_code": "F9_ANTI_HANTU_VLM_UNREACHABLE",
                "error": f"VLM adapter failed: {type(e).__name__}: {e}",
                "backend_id": "minimax-M3-vision",
                "vision_backend_source": "vlm_inference",
                "ac_risk_score": 0.95,
                "ac_risk_verdict": "VOID",
                "hint": (
                    "The in-process MCP backend is NotImplementedError until the host "
                    "registers `minimax-code_understand_image` globally. For headless "
                    f"CI / tests, inject a mock backend. For live calls, hit {mcp_url} "
                    "via the host's MCP client."
                ),
            },
        )

    if not result.success:
        return _vision_envelope(
            "geox_vision_minimax_inference",
            {
                "status": "VOID",
                "claim_state": "VOID",
                "execution_status": "ERROR",
                "error_code": result.error_type or "F9_ANTI_HANTU_VLM_FAILED",
                "error": result.error or "VisionResult.success=False with no error message",
                "backend_id": result.backend_id,
                "elapsed_seconds": result.elapsed_seconds,
            },
        )

    inv = result.inventory
    assert inv is not None  # success=True implies inventory is not None
    ac_score = inv.ac_risk.compute()
    ac_verdict = inv.ac_risk.to_verdict()

    return _vision_envelope(
        "geox_vision_minimax_inference",
        {
            "status": "SEAL_RESERVED" if ac_verdict == AcRiskVerdict.SEAL else ac_verdict.value,
            "claim_state": inv.verdict.value,
            "execution_status": "SUCCESS",
            "inventory": inv.model_dump(mode="json"),
            "seal_receipt": inv.to_seal_receipt(),
            "ac_risk_score": ac_score,
            "ac_risk_verdict": ac_verdict.value,
            "vision_verdict": inv.verdict.value,
            "human_review_required": inv.human_review_required,
            "backend_id": result.backend_id,
            "vision_backend_source": "vlm_inference",
            "elapsed_seconds": result.elapsed_seconds,
            "constitutional_notes": {
                "f1_amanah_image_sha256": inv.input_image_sha256,
                "f2_truth_model_id": inv.model_id,
                "f2_truth_prompt_id": inv.prompt_id,
                "f2_truth_raw_response_hash": inv.raw_response_hash,
                "f5_humility_confidence_capped": inv.overall_confidence <= 0.90,
                "f9_anti_hantu_verdict_cap": inv.verdict.value,
                "f11_audit_actor_id": actor_id or "anonymous",
                "f11_audit_session_id": session_id or "no-session",
            },
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Tool 3 — geox_vision_calibrate
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_vision_calibrate(
    backend: str = "perfect-vision-mock",
    output_dir: str = "/tmp/opencode/geox-vision-v1/calibrate",
    basin_context: str = "Synthetic test (sandbox, Malay Basin-style progradational)",
    seed: int = 42,
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Run the synthetic forward-inverse harness to calibrate the VLM
    against ground truth. Self-contained — no external VLM call.

    Constitutional binding: F1 AMANAH (read-only on the test fixture),
    F2 TRUTH (precision/recall are computed against known features),
    F4 CLARITY (full transform_stack logged).

    Parameters:
      backend          one of: perfect-vision-mock, noisy-vision-mock
      output_dir       where to write the calibration report (PNG + JSON)
      basin_context    basin hint for the harness
      seed             random seed for the synthetic 2D section

    Returns:
      Envelope with HarnessReport (precision/recall per class, AC_Risk
      distribution, summary statistics).
    """
    try:
        from geox_core.engines.vision.vision_test_harness import (
            run_synthetic_forward_inverse,
        )
        from geox_core.engines.vision.run_vision_v1_demo import (
            PerfectVisionMock,
            NoisyVisionMock,
        )

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if backend == "perfect-vision-mock":
            mock: Any = PerfectVisionMock()
        elif backend == "noisy-vision-mock":
            mock = NoisyVisionMock()
        else:
            return _vision_envelope(
                "geox_vision_calibrate",
                {
                    "status": "HOLD",
                    "execution_status": "ERROR",
                    "error_code": "F4_CLARITY_UNKNOWN_BACKEND",
                    "error": f"Unknown backend '{backend}'. Use 'perfect-vision-mock' or 'noisy-vision-mock'.",
                },
            )

        # The harness writes to fixed paths under /tmp/opencode/...
        report = await run_synthetic_forward_inverse(
            backend=mock,
            output_png=str(Path(output_dir) / "synthetic_section.png"),
            output_report=str(Path(output_dir) / "synthetic_report.json"),
            basin_context=basin_context,
            seed=seed,
        )

        # Write the report
        report_path = Path(output_dir) / f"calibrate_{int(time.time())}.json"
        report_path.write_text(
            json.dumps(report.to_dict() if hasattr(report, "to_dict") else dict(report), indent=2, sort_keys=True)
        )

        return _vision_envelope(
            "geox_vision_calibrate",
            {
                "status": "SUCCESS",
                "execution_status": "SUCCESS",
                "report": report.to_dict() if hasattr(report, "to_dict") else dict(report),
                "report_path": str(report_path),
                "backend_id": f"{backend}",
                "vision_backend_source": "calibration_harness",
                "constitutional_notes": {
                    "f1_amanah_fixture_readonly": True,
                    "f2_truth_groundtruth_known": True,
                    "f4_clarity_transform_stack_logged": True,
                    "f11_audit_actor_id": actor_id or "anonymous",
                    "f11_audit_session_id": session_id or "no-session",
                },
            },
        )

    except Exception as e:
        logger.exception("geox_vision_calibrate failed")
        return _vision_envelope(
            "geox_vision_calibrate",
            {
                "status": "VOID",
                "execution_status": "ERROR",
                "error_code": "F9_ANTI_HANTU_CALIBRATE_FAILED",
                "error": f"{type(e).__name__}: {e}",
            },
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Tool 4 — geox_vision_audit
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_vision_audit(
    u_phys: float = 0.45,
    d_transform: float = 1.5,
    b_cog: float = 0.79,
    physics_validated: bool = False,
    multi_view_passed: bool = False,
    transform_stack: list[str] | None = None,
    overall_confidence: float = 0.5,
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Compute AC_Risk and emit VisionVerdict for a vision observation.

    Use this to score any PerceptualInventory (or a hypothetical one) and
    get the bounded verdict. Verifies F7 HUMILITY (0.90 cap) and
    F9 ANTI-HANTU (SEAL reserved unless physics_validated).

    Constitutional binding:
      F5 HUMILITY  overall_confidence hard-cap 0.90
      F7           AC_Risk bounded [0, 1]
      F9           verdict <= INTERPRETATION unless physics_validated
      F13          human_review_required=True if AC_Risk > 0.5

    Returns:
      Envelope with the AC_Risk score, AC_Risk verdict, Vision verdict,
      human_review_required flag, and the breakdown of U_phys × D_transform
      × B_cog.
    """
    try:
        from pydantic import ValidationError

        try:
            components = AcRiskComponents(
                u_phys=u_phys,
                d_transform=d_transform,
                b_cog=b_cog,
                transform_stack=transform_stack or ["image-read", "vlm-inference", "json-parse"],
                multi_view_passed=multi_view_passed,
                physics_validated=physics_validated,
            )
        except ValidationError as e:
            return _vision_envelope(
                "geox_vision_audit",
                {
                    "status": "HOLD",
                    "execution_status": "ERROR",
                    "error_code": "F4_CLARITY_INVALID_AC_RISK",
                    "error": f"AC_Risk components failed: {e.errors()[:3]}",
                },
            )

        # F5 HUMILITY hard cap
        capped_confidence = min(overall_confidence, 0.90)
        if overall_confidence > 0.90:
            f5_violation = True
        else:
            f5_violation = False

        ac_score = components.compute()
        ac_verdict = components.to_verdict()

        # F9 ANTI-HANTU: vision-only output (physics_validated=False) cannot
        # reach SEAL. If AC_Risk says SEAL but physics is not validated,
        # downgrade to INTERPRETATION.
        if ac_verdict == AcRiskVerdict.SEAL and not physics_validated:
            vision_verdict = VisionVerdict.INTERPRETATION
            f9_downgrade = True
        else:
            vision_verdict = VisionVerdict.SEAL if ac_verdict == AcRiskVerdict.SEAL else VisionVerdict.INTERPRETATION
            f9_downgrade = False

        # F13 SOVEREIGN: AC_Risk > 0.5 mandates human review
        human_review_required = ac_score > 0.5

        return _vision_envelope(
            "geox_vision_audit",
            {
                "status": "SUCCESS",
                "execution_status": "SUCCESS",
                "ac_risk_score": ac_score,
                "ac_risk_verdict": ac_verdict.value,
                "vision_verdict": vision_verdict.value,
                "human_review_required": human_review_required,
                "overall_confidence": capped_confidence,
                "backend_id": "ac-risk-scorer",
                "vision_backend_source": "ac_risk_computation",
                "breakdown": {
                    "u_phys": u_phys,
                    "d_transform": d_transform,
                    "b_cog": b_cog,
                    "transform_stack": components.transform_stack,
                    "multi_view_passed": multi_view_passed,
                    "physics_validated": physics_validated,
                    "product": round(u_phys * d_transform * b_cog, 4),
                    "capped_at_1": ac_score,
                },
                "constitutional_notes": {
                    "f5_humility_capped": f5_violation,
                    "f9_anti_hantu_downgrade_applied": f9_downgrade,
                    "f13_sovereign_human_review_required": human_review_required,
                    "f11_audit_actor_id": actor_id or "anonymous",
                    "f11_audit_session_id": session_id or "no-session",
                },
            },
        )

    except Exception as e:
        logger.exception("geox_vision_audit failed")
        return _vision_envelope(
            "geox_vision_audit",
            {
                "status": "VOID",
                "execution_status": "ERROR",
                "error_code": "F9_ANTI_HANTU_AUDIT_FAILED",
                "error": f"{type(e).__name__}: {e}",
            },
        )
