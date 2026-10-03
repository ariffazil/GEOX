"""In-process forbidden-claims scan for every outgoing chat reply.

Fast form of the audit-only geox_forbidden_claims_scan: same canonical rules
(prompts/GEOX_CONSTITUTIONAL_PROMPT_BLOCK.yaml `forbidden:` + I3 family) plus
the EarthBench term list. Any hit → the proxy replaces the reply with HOLD.
One scanner, one home: this module; the auditor list is imported, not copied.
"""

from __future__ import annotations

import re
from typing import Any

from geox_core.earth_witness.specialists import _FORBIDDEN_IMAGE_CLAIM_TERMS

CANONICAL_FORBIDDEN = (
    "horizon is true",  # without mistie advisory SEAL-grade gate
    "amplitude is hydrocarbon",
    "impedance is lithology",
)

_AGE_RE = re.compile(r"\b\d+(\.\d+)?\s*(ma|myr|million years)\b", re.IGNORECASE)


def scan_reply(packet: dict[str, Any]) -> dict[str, Any]:
    """Scan an EarthObservationPacket's reply surfaces. Returns {ok, hits}."""
    hits: list[str] = []
    terms = [*_FORBIDDEN_IMAGE_CLAIM_TERMS, *CANONICAL_FORBIDDEN]

    surfaces: list[tuple[str, str]] = []
    for h in packet.get("hypotheses", []):
        surfaces.append((f"hypothesis:{h.get('hypothesis_id')}", str(h.get("label", ""))))
    for a in packet.get("limitations", {}).get("annotations", []) or []:
        surfaces.append(("annotation", str(a)))

    for where, text in surfaces:
        low = text.lower()
        for t in terms:
            if t in low:
                hits.append(f"{where}:{t}")
        if where.startswith("hypothesis") and _AGE_RE.search(text):
            hits.append(f"{where}:age_from_image")

    return {"ok": not hits, "hits": hits}
