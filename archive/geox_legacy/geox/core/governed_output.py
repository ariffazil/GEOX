"""
Shared governed output helpers for Wave 2 GEOX tools.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from geox.core.ac_risk import ClaimTag


def classify_claim_tag(confidence: float, hold_enforced: bool = False) -> str:
    """Map a normalized confidence score to the canonical ClaimTag."""
    score = max(0.0, min(1.0, confidence))
    if hold_enforced:
        return ClaimTag.ESTIMATE.value
    if score >= 0.85:
        return ClaimTag.CLAIM.value
    if score >= 0.65:
        return ClaimTag.PLAUSIBLE.value
    if score >= 0.4:
        return ClaimTag.HYPOTHESIS.value
    if score > 0.0:
        return ClaimTag.ESTIMATE.value
    return ClaimTag.UNKNOWN.value


def make_vault_receipt(tool_name: str, payload: dict[str, Any], verdict: str = "SEAL") -> dict[str, Any]:
    """Create a lightweight VAULT999-style immutable receipt."""
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(f"{tool_name}:{canonical}".encode("utf-8")).hexdigest()
    return {
        "vault": "VAULT999",
        "tool_name": tool_name,
        "verdict": verdict,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hash": digest,
    }
