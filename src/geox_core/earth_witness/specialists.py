"""
GEOX Earth Witness — Bounded Single-Turn Specialist Observers
═══════════════════════════════════════════════════════════════════════════
Authority: ARIFOS::GEOX::EARTH_WITNESS_SLICE::v1
Phase 2.2: Specialists (single_turn, structured output, no transfer)

1. visual_inventory_observer     -> visible features + OCR + scale bar detection
2. rock_mineral_observer         -> lithological candidates & textures
3. seismic_display_observer      -> requests polarity, domain, gain/color map; flags display artifacts; enforces amplitude != hydrocarbon
4. fossil_morphology_observer    -> candidates only; then geox_paleobiodb_query for biozone ranges
5. physical_test_elicitor        -> emits INPUT_REQUIRED with exact tests to request
6. contradiction_auditor         -> checks cross-modal contradictions
"""

from __future__ import annotations

import logging
import re
from typing import Any

from geox_core.schemas.earth_observation import (
    VisibleFeature,
    OcrText,
    Measurement,
    Hypothesis,
    LimitationsBlock,
    HumanTestRequest,
)
from geox_core.earth_witness.field_tests import (
    FieldTestInput,
    evaluate_field_discriminators,
)

logger = logging.getLogger("geox.earth_witness.specialists")


# ── 1. Visual Inventory Specialist ──────────────────────────────────────────

def visual_inventory_observer(raw_payload: dict[str, Any]) -> tuple[list[VisibleFeature], list[OcrText], list[Measurement]]:
    """Extracts factual visible features, OCR labels, and scale measurements."""
    visible_features: list[VisibleFeature] = []
    ocr_items: list[OcrText] = []
    measurements: list[Measurement] = []

    for f in raw_payload.get("visible_features", []):
        visible_features.append(
            VisibleFeature(
                feature_id=f.get("feature_id", "f_auto"),
                label=f.get("label", "unnamed_feature"),
                category=f.get("category", "visible"),
                bounding_box=f.get("bounding_box"),
                description=f.get("description"),
                confidence=min(f.get("confidence", 0.70), 0.90),
            )
        )

    for o in raw_payload.get("ocr_text", []):
        ocr_items.append(
            OcrText(
                text=o.get("text", ""),
                confidence=o.get("confidence", 0.90),
                location=o.get("location"),
            )
        )

    for m in raw_payload.get("measurements", []):
        measurements.append(
            Measurement(
                metric=m.get("metric", "dimension"),
                value=float(m.get("value", 0.0)),
                unit=m.get("unit", "px"),
                method=m.get("method", "pixel_estimation"),
                uncertainty=float(m.get("uncertainty", 0.0)),
            )
        )

    return visible_features, ocr_items, measurements


# ── 2. Rock & Mineral Observer ──────────────────────────────────────────────

def rock_mineral_observer(
    raw_payload: dict[str, Any],
    field_tests: FieldTestInput | None = None,
) -> tuple[list[Hypothesis], list[str]]:
    """Generates competing rock/mineral hypotheses and applies field test elimination."""
    raw_hyps = raw_payload.get("hypotheses", [])
    candidate_names = [h.get("label", "") for h in raw_hyps if h.get("label")]
    limitations: list[str] = [
        "Mineral stoichiometry cannot be measured from photo pixels.",
        "Porosity percentage and fluid saturation cannot be measured from surface image.",
    ]

    if not candidate_names:
        candidate_names = ["Limestone", "Dolostone", "Sandstone", "Shale", "Chert"]

    if field_tests:
        # Run physical discriminator elimination
        report = evaluate_field_discriminators(candidate_names, field_tests)
        surviving = set(report.surviving_hypotheses)
    else:
        surviving = set(candidate_names)

    hypotheses: list[Hypothesis] = []
    for idx, h in enumerate(raw_hyps):
        label = h.get("label", f"Candidate {idx+1}")
        if label in surviving:
            hypotheses.append(
                Hypothesis(
                    hypothesis_id=h.get("hypothesis_id", f"hyp_{idx+1}"),
                    label=label,
                    supporting=h.get("supporting", []),
                    conflicting=h.get("conflicting", []),
                    falsifiers=h.get("falsifiers", []),
                    confidence=min(h.get("confidence", 0.70), 0.85),
                )
            )

    return hypotheses, limitations


# ── 3. Seismic Display Observer ─────────────────────────────────────────────

def seismic_display_observer(raw_payload: dict[str, Any]) -> tuple[list[Hypothesis], list[str], list[str]]:
    """Inspects seismic displays, strictly enforcing Amplitude != Hydrocarbon."""
    raw_hyps = raw_payload.get("hypotheses", [])
    limitations: list[str] = [
        "Fluid cannot be confirmed from image alone (Amplitude != Hydrocarbon). Low gas saturation produces identical bright spot.",
        "Velocity pull-up / push-down cannot be diagnosed without velocity calibration.",
    ]
    missing_metadata: list[str] = [
        "Polarity convention (SEG normal vs reverse) must be confirmed.",
        "Domain declaration (Time in ms vs Depth in m/ft) must be specified.",
    ]

    hypotheses: list[Hypothesis] = []
    for idx, h in enumerate(raw_hyps):
        label = h.get("label", f"Seismic Feature {idx+1}")
        # Enforce invariant I3: strip or sanitize direct hydrocarbon claims
        if any(term in label.lower() for term in ["gas pay", "oil leg", "commercial hydrocarbon"]):
            label = f"Acoustic Impedance Anomaly ({label})"
        hypotheses.append(
            Hypothesis(
                hypothesis_id=h.get("hypothesis_id", f"seis_hyp_{idx+1}"),
                label=label,
                supporting=h.get("supporting", []),
                conflicting=h.get("conflicting", []),
                falsifiers=h.get("falsifiers", ["well mistie", "low saturation gas"]),
                confidence=min(h.get("confidence", 0.65), 0.80),
            )
        )

    return hypotheses, limitations, missing_metadata


# ── 4. Fossil Morphology Observer ───────────────────────────────────────────

def fossil_morphology_observer(raw_payload: dict[str, Any]) -> tuple[list[Hypothesis], list[str]]:
    """Generates candidate taxa from morphology and bounds chronostratigraphic claims."""
    raw_hyps = raw_payload.get("hypotheses", [])
    limitations: list[str] = [
        "Chronostratigraphic age cannot be asserted from visual morphology alone.",
        "Requires PaleoBioDB biozone range validation and taxonomic verification.",
    ]

    hypotheses: list[Hypothesis] = []
    for idx, h in enumerate(raw_hyps):
        label = h.get("label", f"Taxon candidate {idx+1}")
        if not label.startswith("Candidate "):
            label = f"Candidate {label}"
        hypotheses.append(
            Hypothesis(
                hypothesis_id=h.get("hypothesis_id", f"fos_hyp_{idx+1}"),
                label=label,
                supporting=h.get("supporting", []),
                conflicting=h.get("conflicting", []),
                falsifiers=h.get("falsifiers", ["non-biogenic structure", "stratigraphic range mistie"]),
                confidence=min(h.get("confidence", 0.60), 0.75),
            )
        )

    return hypotheses, limitations


# ── 5. Physical Test Elicitor (The Sensory Clues Engine) ─────────────────────

def physical_test_elicitor(
    modality: str,
    field_tests: FieldTestInput | None = None,
    scale_present: bool = False,
) -> list[HumanTestRequest]:
    """Determines what physical diagnostic tests must be requested from the human/field."""
    requested: list[HumanTestRequest] = []

    if modality in ["rock", "outcrop", "core"]:
        if not field_tests or field_tests.hcl == "not_tested":
            requested.append(
                HumanTestRequest(
                    test_name="dilute_hcl",
                    purpose="Test 10% dilute HCl acid effervescence to determine carbonate mineralogy",
                    discriminates=["Calcite / Limestone (vigorous)", "Dolomite (powder only)", "Silicate / Sandstone / Shale (none)"],
                )
            )
        if not field_tests or field_tests.hardness == "not_tested":
            requested.append(
                HumanTestRequest(
                    test_name="scratch_hardness",
                    purpose="Test Mohs scratch hardness with copper coin (3.5) and pocket knife / steel nail (5.5)",
                    discriminates=["Soft minerals (Calcite Mohs 3)", "Hard silicates (Quartz/Chert Mohs 7)"],
                )
            )
        if not scale_present:
            requested.append(
                HumanTestRequest(
                    test_name="scale_reference",
                    purpose="Provide coin, hand, or ruler in photo for true millimeter/centimeter scale calibration",
                    discriminates=["Wentworth grain size classes", "Lamination thickness"],
                )
            )
    elif modality == "seismic_display":
        requested.append(
            HumanTestRequest(
                test_name="polarity_declaration",
                purpose="Declare whether seabed reflection is a peak (positive SEG normal) or trough",
                discriminates=["Hard kick vs Soft kick", "Class I vs Class III AVO"],
            )
        )

    return requested


# ── 6. Contradiction Auditor (runs BEFORE any final reply) ──────────────────

_FORBIDDEN_IMAGE_CLAIM_TERMS = (
    "gas pay",
    "oil leg",
    "commercial hydrocarbon",
    "proven gas",
    "hydrocarbon accumulation",
    "hydrocarbon discovery",
    "flowing oil",
)


def contradiction_auditor(
    hypotheses: list[Hypothesis],
    ocr_items: list[OcrText],
    modality: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Cross-modal contradiction check on a nearly-final observation bundle.

    Enforced invariants (IMAGE_METABOLIZER_DESIGN.md §10.1):
      I3 — no hydrocarbon/fluid claim from image alone.
      I4 — no fossil age from morphology alone.
      I6 — confidence ceiling 0.90.
      I7 — basin context must never appear as hypothesis support.
      OCR — text evidence is evidence of the TEXT, never of the Earth.

    Returns {ok, findings[], checked} — findings are structured dicts so the
    caller can surface them in limitations[] without schema drift.
    """
    context = context or {}
    findings: list[dict[str, Any]] = []
    ocr_terms = {w.lower() for o in ocr_items for w in o.text.split() if len(w) > 4}
    basin = str(context.get("basin_profile") or context.get("basin") or "").lower()

    for h in hypotheses:
        label_l = h.label.lower()

        # I3: hydrocarbon claims an image cannot make
        for term in _FORBIDDEN_IMAGE_CLAIM_TERMS:
            if term in label_l:
                findings.append(
                    {
                        "type": "FORBIDDEN_IMAGE_CLAIM",
                        "rule": "I3",
                        "target": h.hypothesis_id,
                        "detail": f"hyp_label_contains:{term}",
                    }
                )
                break

        # I6: confidence ceiling
        if h.confidence > 0.90:
            findings.append(
                {
                    "type": "CONFIDENCE_CEILING_BREACH",
                    "rule": "I6",
                    "target": h.hypothesis_id,
                    "detail": f"confidence={h.confidence}",
                }
            )

        # OCR text must never be the EARTH evidence behind a hypothesis
        for s in h.supporting:
            s_l = str(s).lower()
            if ocr_terms and (s_l in ocr_terms or any(t in s_l for t in ocr_terms)):
                findings.append(
                    {
                        "type": "OCR_AS_EARTH_EVIDENCE",
                        "rule": "OCR_TEXT_ONLY",
                        "target": h.hypothesis_id,
                        "detail": f"supporting_ref:{s}",
                    }
                )

        # I7: basin context presented as evidence inflates confidence
        if basin and basin in label_l:
            findings.append(
                {
                    "type": "BASIN_CONTEXT_INFLATION",
                    "rule": "I7",
                    "target": h.hypothesis_id,
                    "detail": f"basin_in_label:{basin}",
                }
            )

        # I4: fossil age asserted from morphology
        if modality == "fossil":
            if "age" in label_l or re.search(r"\b\d+(\.\d+)?\s*ma\b", label_l) or "million year" in label_l:
                findings.append(
                    {
                        "type": "FOSSIL_AGE_FROM_MORPHOLOGY",
                        "rule": "I4",
                        "target": h.hypothesis_id,
                        "detail": f"hyp_label:{h.label}",
                    }
                )

    return {
        "ok": not findings,
        "findings": findings,
        "checked": {
            "hypotheses": len(hypotheses),
            "ocr_items": len(ocr_items),
            "modality": modality,
            "basin_context": bool(basin),
        },
    }
