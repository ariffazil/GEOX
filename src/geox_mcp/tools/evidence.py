from __future__ import annotations

import csv
import json
import logging
import os
from typing import List, Optional, Literal

from geox_core.enums.statuses import (
    get_standard_envelope,
)
from geox_mcp.tools._helpers import (
    _get_artifact,
)

logger = logging.getLogger("geox.canonical.evidence")


async def geox_evidence_summarize_cross(
    evidence_refs: List[str],
    export_format: Literal["json", "csv"] = "json",
    output_path: Optional[str] = None,
) -> dict:
    """Cross-domain synthesis into a causal evidence graph.

    Args:
        evidence_refs: List of artifact refs to synthesize.
        export_format: Output format if output_path is provided ("json" or "csv").
        output_path: If provided, write the evidence summary to this path.
    """
    artifact = {
        "refs": evidence_refs,
        "graph": "synthesized",
        "contradictions": [],
        "visual_artifact_policy": (
            "Visual artifacts (PNG, SVG, HTML) in the evidence graph are supporting "
            "evidence only — they do not constitute physical truth by themselves. "
            "Every visual artifact must be accompanied by its claim_state, depth_basis, "
            "and artifact validation status. Do not promote a visual artifact to "
            "physical evidence without explicit unit + depth + QC verification."
        ),
    }
    result = get_standard_envelope(
        artifact,
        tool_class="compute",
        claim_tag="DERIVED",
        claim_state="INTERPRETED",
        perception_class="DERIVED",
    )

    if output_path:
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            if export_format == "csv":
                with open(output_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["artifact_ref", "claim_state", "note"])
                    for ref in evidence_refs:
                        entry = _get_artifact(ref)
                        cs = entry.get("claim_state", "UNKNOWN") if entry else "NOT_REGISTERED"
                        writer.writerow([ref, cs, ""])
            else:
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2, default=str)
            result["export_written"] = True
            result["export_path"] = output_path
            result["export_format"] = export_format
        except Exception as exc:
            result["export_written"] = False
            result["export_error"] = str(exc)

    return result
