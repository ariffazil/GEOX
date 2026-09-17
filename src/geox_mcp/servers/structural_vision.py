"""
GEOX Structural Vision Domain Server — DETERMINISTIC structural-metric lane
══════════════════════════════════════════════════════════════════════════
Forged 2026-09-18 · Authority: F13 Arif · Contract: CONTRACT.md v1.0 (frozen)
DITEMPA BUKAN DIBERI — Forged, Not Given

THE RULE THIS SERVER EXISTS TO ENFORCE
--------------------------------------
    THE LLM NEVER READS GEOMETRY OFF AN IMAGE.

The tool runs deterministic computer vision and returns NUMBERS WITH COVERAGE.
The agent reasons over the returned numbers only — never over the pixels.

THIS LANE IS SEPARATE FROM, AND MUST NEVER BE MERGED INTO, THE VLM LANE IN
`geox_mcp/servers/vision.py`. A vision-language model reading spatial metrics
off a seismic image is EXACTLY the hallucination failure this lane exists to
prevent: a VLM has no depth sample interval, no trace spacing, no
vertical-exaggeration factor, but will nonetheless emit "the fault dips about
60 degrees" with a fluent confidence that no measurement supports. The VLM
lane is a PERCEPTION lane (`geox_vision_*`, model-capped at 0.90 by F7
HUMILITY, outputs never reaching SEAL without physics validation). This is a
DETERMINISTIC MEASUREMENT lane.

Therefore, and permanently:

  * DO NOT add the tools below to `servers/vision.py`.
  * DO NOT re-export `servers/vision.py`'s tools here.
  * DO NOT share an annotation table, a registration list, an engine or a
    code path between the two servers.
  * DO NOT let a perception-lane result be used as an input to a
    structural-metric claim, or vice versa.

Two tools:

  geox_structural_vision_extract
        section + horizon_masks + calibration -> CONTRACT section 5 bundle:
        axes A/B/C/D, MANDATORY aggregate coverage, calibration_state,
        decompaction_declared, method_receipt, status. preferred_hypothesis
        is always None. No confidence / reliability / probability / score /
        certainty key can survive the return path (sanitizer + assertion).

  geox_structural_regime_falsify
        a THIN ADAPTER onto the SINGLE existing falsifier engine
        (structure_gates.tectonic_regime.run_regime_falsification). It fills
        the `framework` dict that engine already consumes (CONTRACT section 6)
        and returns the engine's verdict plus the raw bundle and the exact
        framework used, for traceability. It does NOT reimplement the engine
        and must never grow a second one: one engine, one authority.

Constitutional binding:
  F1  AMANAH      inputs never mutated; call hash + session lineage recorded
  F2  TRUTH       every number carries method + n_samples + uncertainty
  F4  CLARITY     the bundle shape is pinned by the frozen contract
  F7  HUMILITY    no self-assigned probability anywhere; confidence comes from
                  coverage + n_samples and is capped at 0.90
  F9  ANTI-HANTU  no softening — UNMEASURED is reported as UNMEASURED
  F11 AUDIT       traceable to the algorithms that ran and their parameters
  F13 SOVEREIGN   GEOX proposes geometry; arifOS seals; Arif decides

Authority: GEOX (Earth evidence) prepares. arifOS judges. Arif (F13) decides.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from geox_mcp.tools._register import register_tools_on_server
from geox_mcp.tools.structural_vision import (
    geox_structural_regime_falsify,
    geox_structural_vision_extract,
)

# ── Tool surface ─────────────────────────────────────────────────────────────
# Deliberately DISJOINT from _VISION_TOOLS in servers/vision.py. The two sets
# must never intersect, and this server must never mount a `geox_vision_*` name.
_STRUCTURAL_VISION_TOOLS: list[tuple[str, Any]] = [
    ("geox_structural_vision_extract", geox_structural_vision_extract),
    ("geox_structural_regime_falsify", geox_structural_regime_falsify),
]

# ── MCP annotations ──────────────────────────────────────────────────────────
# Both tools are PURE READ + PURE COMPUTE: they read a section, run local CV,
# and return numbers. No external network, no file written, no state mutated.
# `idempotentHint: True` is load-bearing — the same section and the same
# parameters MUST yield the same numbers, which is only true because no
# stochastic model (and no VLM) is anywhere in this path. If a VLM were ever
# introduced here, this annotation would become a lie.
_STRUCTURAL_VISION_ANNOTATIONS: dict[str, dict] = {
    "geox_structural_vision_extract": {
        "title": "Structural Vision Extract (deterministic CV, not a VLM)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,   # deterministic CV: same input -> same numbers
        "openWorldHint": False,   # local compute only; no model, no network
    },
    "geox_structural_regime_falsify": {
        "title": "Structural Regime Falsify (thin adapter onto the one K-REGIME engine)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,   # falsification is a pure function of the framework
        "openWorldHint": False,
    },
}


def create_structural_vision_server() -> FastMCP:
    """Build the structural-vision domain sub-server.

    Mounts exactly two tools, both wired through `register_tools_on_server` so
    they inherit the canonical floor enforcement (F1/F7/F9/F11/F13) and the
    Evidence Contract envelope. The deterministic CV lives in
    `geox_core.vision_structural` (lazy-imported by the tools so this server
    boots even while the core is being built in parallel); the falsification
    lives in `geox_mcp.tools.structure_gates.tectonic_regime` and is REUSED,
    not reimplemented.

    The docstring above is the boundary contract: this lane stays separate from
    `servers/vision.py`. A VLM reading spatial metrics from pixels is the
    HALLUCINATION failure mode this server exists to prevent, so the two must
    never merge. Keep `_STRUCTURAL_VISION_TOOLS` disjoint from that lane's
    `_VISION_TOOLS`, and never route a perception-lane result into a
    structural-metric claim.
    """
    server = FastMCP("geox-structural-vision")
    register_tools_on_server(server, _STRUCTURAL_VISION_TOOLS, _STRUCTURAL_VISION_ANNOTATIONS)
    return server


__all__ = [
    "_STRUCTURAL_VISION_ANNOTATIONS",
    "_STRUCTURAL_VISION_TOOLS",
    "create_structural_vision_server",
]