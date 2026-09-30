"""Arming module for the deterministic structural-vision lane — Status: PLANNED.

NOT ARMED. Nothing imports this module. The lane is built, tested, and verified
(224 tests across four files) but is deliberately **not reachable** from the live
MCP surface. Arming it changes the canonical public tool surface, which is a
governed mutation (see registry.GHOST_TOOLS: "Reactivation requires F13
SOVEREIGN ack"). It is therefore prepared here and left unarmed.

To arm, TWO changes are required — both, or neither:

  1. tools_manifest.yaml — add entries for:
         geox_structural_vision_extract
         geox_structural_regime_falsify
     (registry.SURFACE_TOOLS derives from surface_manifest.public_tool_names(),
      which reads this YAML. Without manifest entries the new tools exist but
      RT1_BLOCK rejects every call at geox_middleware.py ~line 704.)

  2. geox_mcp/server.py — inside the domain-server block (~line 636-666), add:
         from geox_mcp.servers import create_structural_vision_server
         structural_vision = create_structural_vision_server()
         mcp.mount(structural_vision, namespace=None)

DO NOT do step 1 on the OLD vision lane while arming this one. See HAZARD below.

═══════════════════════════════════════════════════════════════════════════════
HAZARD D1 — read before touching tools_manifest.yaml
═══════════════════════════════════════════════════════════════════════════════
The four existing `geox_vision_*` tools are MOUNTED (server.py ~650) but absent
from the manifest, so RT1 currently blocks them. That blockage is the only thing
preventing a governance hazard from going live:

  src/geox_core/engines/vision/minimax_vlm_adapter.py:139-140
  src/geox_core/engines/vision/mimo_vlm_adapter.py:121-122

both send a JSON schema to a vision-language model containing:

      "strike_dip_deg": null_or_0_to_90,
      "throw_ms": null_or_number,

and then read those values straight back into FaultObservation at
minimax_vlm_adapter.py:375-376 and mimo_vlm_adapter.py:428-429. Those are direct
inputs to the K-DIP / K-THROW / K-EXT-DIP gates.

So: adding `geox_vision_*` to the manifest to "make vision work" would arm a path
where a language model's guess at a dip in degrees, read off a picture, becomes a
physics-gated structural verdict. The ONLY current guard is
min(overall_confidence, 0.90) — a cap on self-reported certainty, which bounds
nothing about whether the number is physical.

The deterministic lane this module arms is the opposite design: a number is
computed by an algorithm from the data, and carries coverage and uncertainty
instead of a self-assigned confidence. Arming it is a net safety gain. Arming the
VLM lane on the same commit is a net safety loss. Keep them separate.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox.mcp.structural_vision_wiring")

# Tools this lane adds to the public surface. Kept here so the arm-note and the
# manifest entry have a single source of truth.
PLANNED_PUBLIC_TOOLS: tuple[str, ...] = (
    "geox_structural_vision_extract",
    "geox_structural_regime_falsify",
)

# Reverse-domain mapping is intentionally left unpopulated until arming, because
# writing it now would be a second partial activation path that bypasses the
# manifest review. Populate both places, or neither.
PLANNED_DOMAIN_MAP: dict[str, str] = {}


def describe_arming_plan() -> dict[str, Any]:
    """Return the two required changes and the hazard note, for review.

    This performs no mutation. It exists so that the arming decision can be made
    against an explicit, inspectable diff rather than from memory.
    """
    return {
        "status": "PLANNED_NOT_ARMED",
        "armed": False,
        "tools_to_add_to_public_surface": list(PLANNED_PUBLIC_TOOLS),
        "required_changes": [
            {
                "file": "src/geox_mcp/tools_manifest.yaml",
                "action": "add manifest entries for the two tools above",
                "why": "registry.SURFACE_TOOLS -> surface_manifest.public_tool_names() reads this file; "
                       "without it RT1_BLOCK rejects every call (geox_middleware.py ~line 704)",
            },
            {
                "file": "src/geox_mcp/server.py",
                "action": "import create_structural_vision_server, instantiate, mcp.mount(..., namespace=None)",
                "why": "the server exists but nothing mounts it",
            },
        ],
        "hazard": {
            "id": "D1",
            "do_not_co_arm": "geox_vision_* (perception/VLM lane)",
            "evidence": [
                "src/geox_core/engines/vision/minimax_vlm_adapter.py:139-140, 375-376",
                "src/geox_core/engines/vision/mimo_vlm_adapter.py:121-122, 428-429",
            ],
            "summary": (
                "The VLM lane asks a language model for strike_dip_deg and throw_ms and feeds the "
                "answers into K-DIP / K-THROW / K-EXT-DIP. It is inert only because RT1 blocks it. "
                "Manifest-adding it to 'fix vision' would arm that path."
            ),
        },
        "seal_authority": "F13_only",
        "note": (
            "Arming mutates the canonical public tool surface. Not done by an agent without "
            "explicit F13 acknowledgment."
        ),
    }


__all__ = ["PLANNED_PUBLIC_TOOLS", "PLANNED_DOMAIN_MAP", "describe_arming_plan"]
