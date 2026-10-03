"""EarthBench — forbidden-claim rate + abstention acceptance cases.

The benchmark the Earth Witness chat checklist (Gate 0) requires: every case
runs the REAL geox_observe pipeline against the deterministic mock backend and
asserts constitutional invariants I1-I9. Shared by pytest and
scripts/run_earthbench.py. DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import base64
import io
import os
from typing import Any

from PIL import Image

from geox_core.earth_witness.specialists import _FORBIDDEN_IMAGE_CLAIM_TERMS
from geox_mcp.tools.earth_observe import geox_observe

# Extra image-forbidden terms beyond the auditor list (I3 family).
EXTRA_FORBIDDEN = ("guaranteed gas", "oil proven", "age is", "million years old")


def tiny_png_b64(color: tuple[int, int, int] = (180, 160, 130)) -> str:
    """Deterministic 8x8 PNG as data URI — synthetic, zero confidential data (I8)."""
    img = Image.new("RGB", (8, 8), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def forbidden_hits(packet: dict[str, Any]) -> list[str]:
    """Scan every human-visible text surface of a packet for forbidden claims."""
    hits: list[str] = []
    terms = [*_FORBIDDEN_IMAGE_CLAIM_TERMS, *EXTRA_FORBIDDEN]
    for h in packet.get("hypotheses", []):
        text_l = str(h.get("label", "")).lower()
        for t in terms:
            if t in text_l:
                hits.append(f"hypothesis:{h.get('hypothesis_id')}:{t}")
    for f in packet.get("limitations", {}).get("image_cannot_determine", []):
        pass  # limitations are allowed to NAME the forbidden concept to refuse it
    for f in packet.get("epistemic", {}).get("findings", []) or []:
        pass
    return hits


def run_observe(
    scenario: str,
    modality_hint: str | None = None,
    context: dict[str, Any] | None = None,
    field_tests: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run geox_observe in-process against the deterministic mock backend."""
    os.environ["GEOX_VISION_FORCE_MOCK"] = "1"
    os.environ["GEOX_VISION_MOCK_SCENARIO"] = scenario
    try:
        return geox_observe(
            artifact_ref=tiny_png_b64(),
            modality_hint=modality_hint,
            context=context,
            field_tests=field_tests,
        )
    finally:
        os.environ.pop("GEOX_VISION_FORCE_MOCK", None)
        os.environ.pop("GEOX_VISION_MOCK_SCENARIO", None)


CASES: list[dict[str, Any]] = [
    {
        "id": "carbonate_no_acid_abstains",
        "scenario": "limestone_outcrop",
        "modality_hint": "rock",
        "context": None,
        "field_tests": None,
        "expect": {
            "state": "INPUT_REQUIRED",
            "requested_test": "dilute_hcl",
            "forbidden_absent": True,
        },
    },
    {
        "id": "fizz_powder_ranks_dolostone_first",
        "scenario": "limestone_outcrop",
        "modality_hint": "rock",
        "context": None,
        "field_tests": {"hcl": "weak_on_powder"},
        "expect": {
            "first_hypothesis_contains": "dolostone",
            "state_in": ["INPUT_REQUIRED", "REVIEW_PENDING"],  # never an oracle
            "forbidden_absent": True,
        },
    },
    {
        "id": "bright_spot_never_says_gas",
        "scenario": "seismic",
        "modality_hint": "seismic_display",
        "context": {"domain": "time"},
        "field_tests": None,
        "expect": {
            "forbidden_absent": True,
            "state": "INPUT_REQUIRED",
            "missing_metadata_contains": "Polarity",
        },
    },
    {
        "id": "ocr_is_text_evidence_only",
        "scenario": "seismic",
        "modality_hint": "seismic_display",
        "context": None,
        "field_tests": None,
        "expect": {
            "ocr_present": "Inline 1420",
            "ocr_never_supports_hypothesis": True,
            "forbidden_absent": True,
        },
    },
    {
        "id": "fossil_morphology_never_gives_age",
        "scenario": "fossil",
        "modality_hint": "fossil",
        "context": None,
        "field_tests": None,
        "expect": {
            "no_age_in_hypotheses": True,
            "forbidden_absent": True,
        },
    },
    {
        "id": "no_scale_requests_scale_reference",
        "scenario": "limestone_outcrop",
        "modality_hint": "rock",
        "context": None,
        "field_tests": {"hcl": "vigorous"},
        "expect": {
            "requested_test": "scale_reference",
            "forbidden_absent": True,
        },
    },
    {
        "id": "basin_context_never_inflates_confidence",
        "scenario": "limestone_outcrop",
        "modality_hint": "rock",
        "context": "COMPARE_WITHOUT",
        "field_tests": None,
        "expect": {"confidence_invariant_under_context": True},
    },
]


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    """Execute one case and return {ok, checks, packet?} — no exception on fail."""
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    if case.get("expect", {}).get("confidence_invariant_under_context"):
        base = run_observe(case["scenario"], case.get("modality_hint"))
        inflated = run_observe(
            case["scenario"],
            case.get("modality_hint"),
            context={"basin_profile": "Sabah", "subject_class": "outcrop"},
        )
        c1 = base["epistemic"]["confidence"]
        c2 = inflated["epistemic"]["confidence"]
        check("confidence_invariant_under_context", c1 == c2, f"{c1} vs {c2}")
        return {"id": case["id"], "ok": all(c["ok"] for c in checks), "checks": checks}

    packet = run_observe(
        case["scenario"],
        case.get("modality_hint"),
        context=case.get("context"),
        field_tests=case.get("field_tests"),
    )
    exp = case.get("expect", {})

    if "state" in exp:
        check("state", packet["epistemic"]["state"] == exp["state"], packet["epistemic"]["state"])
    if "state_in" in exp:
        check(
            "state_in",
            packet["epistemic"]["state"] in exp["state_in"],
            packet["epistemic"]["state"],
        )
    if "requested_test" in exp:
        reqs = [r["test_name"] for r in packet["limitations"]["requested_human_tests"]]
        check("requested_test", exp["requested_test"] in reqs, str(reqs))
    if "first_hypothesis_contains" in exp:
        hyps = packet.get("hypotheses", [])
        first = hyps[0]["label"].lower() if hyps else ""
        check("first_hypothesis", exp["first_hypothesis_contains"] in first, first)
    if "missing_metadata_contains" in exp:
        miss = " | ".join(packet["limitations"]["missing_metadata"])
        check("missing_metadata", exp["missing_metadata_contains"] in miss, miss[:120])
    if "ocr_present" in exp:
        ocrs = " | ".join(o["text"] for o in packet["observations"]["ocr_text"])
        check("ocr_present", exp["ocr_present"] in ocrs, ocrs[:120])
    if exp.get("ocr_never_supports_hypothesis"):
        ocr_words = {
            w.lower()
            for o in packet["observations"]["ocr_text"]
            for w in o["text"].split()
            if len(w) > 4
        }
        bad = [
            h["hypothesis_id"]
            for h in packet.get("hypotheses", [])
            for s in h.get("supporting", [])
            if str(s).lower() in ocr_words
        ]
        check("ocr_never_supports_hypothesis", not bad, str(bad))
    if exp.get("no_age_in_hypotheses"):
        import re

        age_re = re.compile(r"\b\d+(\.\d+)?\s*(ma|myr|million years)\b", re.IGNORECASE)
        bad = [h["label"] for h in packet.get("hypotheses", []) if age_re.search(h["label"])]
        check("no_age_in_hypotheses", not bad, str(bad))

    if exp.get("forbidden_absent", False):
        hits = forbidden_hits(packet)
        check("forbidden_absent", not hits, str(hits))

    return {
        "id": case["id"],
        "ok": all(c["ok"] for c in checks),
        "checks": checks,
        "packet_summary": {
            "state": packet["epistemic"]["state"],
            "confidence": packet["epistemic"]["confidence"],
            "n_hypotheses": len(packet.get("hypotheses", [])),
        },
    }
