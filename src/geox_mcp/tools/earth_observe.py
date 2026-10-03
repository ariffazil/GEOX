"""
geox_observe.py — Canonical Multimodal Earth Observation Umbrella Tool
═══════════════════════════════════════════════════════════════════════════
Authority: ARIFOS::GEOX::EARTH_WITNESS_SLICE::v1
Phase 2.1: The 27th canonical tool bridging multimodal observation into GEOX.

Enforces:
I1 Image != Specimen != Measurement != Earth.
I2 Vision output is EVIDENCE only for visible features; interpretations are HYPOTHESIS.
I3 No hydrocarbon/fluid claim from image alone (Amplitude != Hydrocarbon).
I4 No fossil age from morphology alone.
I5 Missing diagnostic input -> INPUT_REQUIRED, never guessed.
I6 Every output carries claim_tag, confidence (<=0.90), provenance, limitations[].
I7 basin_profile = context only; never inflates confidence.
I8 Zero confidential PETRONAS data sent to external models.
I9 Max local verdict = QUALIFIED_CANDIDATE.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from geox_core.schemas.earth_observation import (
    EarthObservationPacket,
    ArtifactMetadata,
    ObservationContext,
    ObservationsBlock,
    LimitationsBlock,
    EpistemicBlock,
    ProvenanceRecord,
    ScaleMetadata,
    OrientationMetadata,
    DisplayTransformMetadata,
    ObservationModality,
)
from geox_core.earth_witness.field_tests import FieldTestInput
from geox_core.earth_witness.vision_backend import get_vision_backend
from geox_core.earth_witness.specialists import (
    visual_inventory_observer,
    rock_mineral_observer,
    seismic_display_observer,
    fossil_morphology_observer,
    physical_test_elicitor,
    contradiction_auditor,
    HumanTestRequest,
)

logger = logging.getLogger("geox.mcp.earth_observe")


def geox_observe(
    artifact_ref: str | dict[str, Any],
    modality_hint: str | None = None,
    context: dict[str, Any] | None = None,
    field_tests: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Inspects any Earth visual artifact and returns a governed EarthObservationPacket.

    Args:
        artifact_ref: File path, base64 data URI, or dict with {data, mime_type}.
        modality_hint: rock, outcrop, core, thin_section, fossil, seismic_display, map, section.
        context: Optional scale, orientation, domain, basin_profile.
        field_tests: Optional sensory tests (hcl, hardness, streak, magnetism, etc.).

    Returns:
        Canonical EarthObservationPacket dictionary.
    """
    context = context or {}
    field_tests_input = FieldTestInput(**(field_tests or {})) if field_tests else None

    # 1. Resolve Artifact Data & SHA256
    image_bytes = b""
    mime_type = "image/jpeg"
    artifact_id = "art_inline"
    original_uri: str | None = None

    if isinstance(artifact_ref, dict):
        if "data" in artifact_ref:
            raw_data = artifact_ref["data"]
            if "," in raw_data:
                raw_data = raw_data.split(",", 1)[1]
            image_bytes = base64.b64decode(raw_data)
        mime_type = artifact_ref.get("mime_type", "image/jpeg")
        original_uri = artifact_ref.get("uri")
        artifact_id = artifact_ref.get("id", f"art_{int(time.time())}")
    elif isinstance(artifact_ref, str):
        if artifact_ref.startswith("data:"):
            # Data URI
            header, encoded = artifact_ref.split(",", 1)
            mime_type = header.split(";")[0].replace("data:", "")
            image_bytes = base64.b64decode(encoded)
        elif os.path.exists(artifact_ref):
            # Local file path
            original_uri = artifact_ref
            artifact_id = os.path.basename(artifact_ref)
            with open(artifact_ref, "rb") as f:
                image_bytes = f.read()
            if artifact_ref.lower().endswith(".png"):
                mime_type = "image/png"
            elif artifact_ref.lower().endswith(".webp"):
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"
        else:
            # Treat as raw string or base64
            try:
                image_bytes = base64.b64decode(artifact_ref)
            except Exception:
                image_bytes = artifact_ref.encode("utf-8")

    art_sha256 = hashlib.sha256(image_bytes).hexdigest()

    # 2. Select Modality
    modality: ObservationModality = "unknown"
    if modality_hint in ["rock", "outcrop", "core", "thin_section", "fossil", "seismic_display", "map", "section"]:
        modality = modality_hint  # type: ignore
    elif "modality" in context:
        modality = context["modality"]

    # 3. Call Vision Backend
    backend = get_vision_backend()
    system_instruction = (
        "You are the GEOX Earth Observer. Observe visible features, OCR labels, scale bars, and lithological/structural markers. "
        "Strict Rule: You are a tri-witness, not a judge. Never assert fluid content (Amplitude != Hydrocarbon). "
        "Enumerate visible facts only; all geological classifications are hypotheses."
    )
    user_prompt = f"Analyze this Earth artifact (modality hint: {modality}). Extract visible features, text, and competing hypotheses."

    resp = backend.inspect_artifact(
        image_bytes=image_bytes,
        mime_type=mime_type,
        system_instruction=system_instruction,
        user_prompt=user_prompt,
    )
    raw_payload = resp.raw_response

    # Update modality if detected by backend and previously unknown
    if modality == "unknown":
        detected_mod = raw_payload.get("modality", "rock")
        if detected_mod in ["rock", "outcrop", "core", "thin_section", "fossil", "seismic_display", "map", "section"]:
            modality = detected_mod

    # 4. Specialist Orchestration (Single-Turn Execution)
    visible_features, ocr_items, measurements = visual_inventory_observer(raw_payload)

    hypotheses = []
    limitations_cannot_determine = []
    missing_metadata = []

    if modality in ["rock", "outcrop", "core", "thin_section"]:
        hyps, lims = rock_mineral_observer(raw_payload, field_tests=field_tests_input)
        hypotheses.extend(hyps)
        limitations_cannot_determine.extend(lims)
    elif modality == "seismic_display":
        hyps, lims, missing_meta = seismic_display_observer(raw_payload)
        hypotheses.extend(hyps)
        limitations_cannot_determine.extend(lims)
        missing_metadata.extend(missing_meta)
    elif modality == "fossil":
        hyps, lims = fossil_morphology_observer(raw_payload)
        hypotheses.extend(hyps)
        limitations_cannot_determine.extend(lims)
    else:
        hyps, lims = rock_mineral_observer(raw_payload, field_tests=field_tests_input)
        hypotheses.extend(hyps)
        limitations_cannot_determine.extend(lims)

    # Merge backend-declared missing metadata (the vision payload may know
    # display-processing gaps — gain/AGC, colormap symmetry — that the generic
    # per-modality observer does not). Dedupe, observers first.
    _seen_meta = set(missing_metadata)
    for bm in raw_payload.get("limitations", {}).get("missing_metadata", []) or []:
        if bm and bm not in _seen_meta:
            missing_metadata.append(bm)
            _seen_meta.add(bm)

    # 4.5 Contradiction audit (checklist §5: runs before every final reply).
    # Findings land in limitations[] (no schema drift) and force the packet
    # state DOWN — a contradicted bundle can never be QUALIFIED_CANDIDATE.
    audit = contradiction_auditor(
        hypotheses=hypotheses,
        ocr_items=ocr_items,
        modality=modality,
        context=context,
    )
    audit_forced_review = not audit["ok"]
    for f in audit["findings"]:
        limitations_cannot_determine.append(
            f"CONTRADICTION_AUDIT[{f['rule']}] {f['type']} on {f['target']}: {f['detail']}"
        )

    # 5. Physical Elicitor (Diagnostic Human Clues)
    scale_obj = None
    if "scale" in context and isinstance(context["scale"], dict):
        scale_obj = ScaleMetadata(**context["scale"])

    requested_tests = physical_test_elicitor(
        modality=modality,
        field_tests=field_tests_input,
        scale_present=(scale_obj is not None and scale_obj.is_calibrated),
    )
    # Merge backend-requested tests (vision payload may know display-/fossil-
    # specific diagnostics the generic elicitor does not). Dedupe by test_name;
    # elicitor entries win on conflicts (they are constitutionally generic).
    _seen = {t.test_name for t in requested_tests}
    for bt in raw_payload.get("limitations", {}).get("requested_human_tests", []) or []:
        if bt.get("test_name") and bt["test_name"] not in _seen:
            requested_tests.append(
                HumanTestRequest(
                    test_name=bt["test_name"],
                    purpose=bt.get("purpose", ""),
                    discriminates=bt.get("discriminates", []),
                )
            )
            _seen.add(bt["test_name"])

    # 6. Epistemic Posture & State
    state = "DRAFT"
    if requested_tests or missing_metadata:
        state = "INPUT_REQUIRED"
    elif hypotheses and len(hypotheses) == 1 and hypotheses[0].confidence > 0.75:
        state = "QUALIFIED_CANDIDATE"
    else:
        state = "REVIEW_PENDING"
    if audit_forced_review and state == "QUALIFIED_CANDIDATE":
        # A contradicted bundle never ships as QUALIFIED_CANDIDATE (I9 posture).
        state = "REVIEW_PENDING"

    epistemic_block = EpistemicBlock(
        claim_tag="INTERPRET",
        confidence=min(hypotheses[0].confidence if hypotheses else 0.50, 0.90),
        state=state,  # type: ignore
        provenance=[
            ProvenanceRecord(
                step="geox_observe_intake",
                agent_id="earth_observer_agent",
                model_id=resp.model_id,
                timestamp=datetime.now(UTC).isoformat(),
                hash=resp.response_hash,
            ),
            ProvenanceRecord(
                step="contradiction_auditor",
                agent_id="geox_earth_witness",
                model_id="rule_engine_v1",
                timestamp=datetime.now(UTC).isoformat(),
                hash=resp.response_hash,
            ),
        ],
        verdict="QUALIFIED_CANDIDATE" if state == "QUALIFIED_CANDIDATE" else "PARTIAL",
    )

    # 7. Assemble Root Packet
    packet = EarthObservationPacket(
        packet_id=f"eop_{hashlib.md5(f'{art_sha256}_{time.time()}'.encode()).hexdigest()[:12]}",
        artifact=ArtifactMetadata(
            id=artifact_id,
            sha256=art_sha256,
            media_type=mime_type,
            original_uri=original_uri,
            source_actor=context.get("source_actor", "anonymous_geologist"),
            captured_at=datetime.now(UTC).isoformat(),
        ),
        context=ObservationContext(
            modality=modality,
            subject_class=context.get("subject_class"),
            scale=scale_obj,
            orientation=OrientationMetadata(**context["orientation"]) if "orientation" in context else None,
            crs=context.get("crs"),
            domain=context.get("domain", "time" if modality == "seismic_display" else "na"),
            display_transform=DisplayTransformMetadata(**context["display_transform"]) if "display_transform" in context else None,
            acquisition_metadata=context.get("acquisition_metadata", {}),
        ),
        observations=ObservationsBlock(
            visible_features=visible_features,
            ocr_text=ocr_items,
            measurements=measurements,
            annotations=raw_payload.get("annotations", []),
        ),
        hypotheses=hypotheses,
        limitations=LimitationsBlock(
            image_cannot_determine=limitations_cannot_determine,
            missing_metadata=missing_metadata,
            requested_human_tests=requested_tests,
            requested_instrument_data=raw_payload.get("limitations", {}).get("requested_instrument_data", []),
        ),
        epistemic=epistemic_block,
    )

    return packet.model_dump()
