"""Compact MCP response envelope (<400 tokens content + clean structuredContent)."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def compact_envelope(
    *,
    tool: str,
    verdict: str,
    summary: str,
    epistemic: str = "OBS",
    defaults_applied: list[str] | None = None,
    falsifiers: list[str] | None = None,
    data: dict[str, Any] | None = None,
    artifact_uri: str | None = None,
    max_summary_chars: int = 900,
) -> dict[str, Any]:
    """Build a token-disciplined (<400 est. tokens) MCP tool response."""
    clean_summary = summary.strip()[:max_summary_chars]
    payload = data or {}
    sha = hashlib.sha256(
        json.dumps(payload, default=str, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    structured: dict[str, Any] = {
        "tool": tool,
        "verdict": verdict,
        "epistemic": epistemic,
        "defaults_applied": list(defaults_applied or []),
        "falsifiers": list(falsifiers or []),
        "artifact_uri": artifact_uri or "",
        "sha256": sha,
        "data": payload,
    }
    return {
        "content": clean_summary,
        "verdict": verdict,
        "epistemic": epistemic,
        "defaults_applied": structured["defaults_applied"],
        "falsifiers": structured["falsifiers"],
        "sha256": sha,
        "structuredContent": structured,
        "isError": verdict in ("ERROR", "FAIL_CLOSED"),
    }
