"""
FLAME Client — governed HTTP bridge to FLAME free-loop inference mesh.

Architectural rules (Arif-ratified 2026-07-25):
  1. Strict timeout (8s) — never hang an organ waiting for FLAME
  2. Graceful degradation — return UNKNOWN/empty on failure, never crash the caller
  3. Stateless request — payloads are self-contained, FLAME has no context history
  4. ADVISORY authority — output tagged for F2 truth verification, never governs

Usage:
    from geox_mcp.tools.flame_client import flame_summarize, flame_classify

    result = flame_summarize("Analyze these claims: ...")
    # Returns: str | None  (None on failure)

    result = flame_classify(categories=["error", "warning"], text="...")
    # Returns: dict | None

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from typing import Any

logger = logging.getLogger("geox.flame_client")

# ── Config ───────────────────────────────────────────────────────────────
FLAME_API_BASE = "http://127.0.0.1:18901"
DEFAULT_TIMEOUT_S = 8  # Strict: never hang organ
MAX_BODY_CHARS = 8000  # Keep requests lean — FLAME is RM0, no giant contexts


def _flame_post(
    endpoint: str,
    payload: dict[str, Any],
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> dict[str, Any] | None:
    """POST to FLAME API with graceful degradation.

    Args:
        endpoint: Path like '/summarize' or '/classify'
        payload: JSON-serialisable dict — must be self-contained
        timeout_s: HTTP timeout in seconds (default 8)

    Returns:
        Parsed JSON response dict, or None on any failure.
    """
    url = f"{FLAME_API_BASE}{endpoint}"
    body = json.dumps(payload).encode("utf-8")

    if len(body) > MAX_BODY_CHARS * 4:  # rough UTF-8 byte check
        logger.warning("flame_client: payload too large (%d bytes), truncating", len(body))
        body = body[:MAX_BODY_CHARS * 4]

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Caller-Id": "geox",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            logger.debug(
                "flame_client: %s → %s (ok=%s, latency_ms=%s)",
                endpoint,
                result.get("model", "?"),
                result.get("ok", False),
                result.get("latency_ms", "?"),
            )
            return result
    except urllib.error.HTTPError as e:
        # FLAME returns 400 even when ok=True if "error" key exists in response
        # (even with empty string). Try to parse body for valid content.
        try:
            body = e.read().decode("utf-8")
            result = json.loads(body)
            if result.get("ok"):
                logger.debug(
                    "flame_client: %s → HTTP %d but ok=True — accepting",
                    endpoint, e.code,
                )
                return result
        except Exception:
            pass
        logger.warning("flame_client: HTTP %d on %s — %s", e.code, endpoint, str(e)[:200])
        return None
    except urllib.error.URLError as e:
        logger.warning("flame_client: connection failed to %s — %s", endpoint, str(e.reason)[:200])
        return None
    except TimeoutError:
        logger.warning("flame_client: timeout (%ds) on %s", timeout_s, endpoint)
        return None
    except json.JSONDecodeError:
        logger.warning("flame_client: non-JSON response from %s", endpoint)
        return None
    except Exception as e:
        logger.warning("flame_client: unexpected error on %s — %s", endpoint, str(e)[:200])
        return None


def flame_summarize(
    text: str,
    caller_id: str = "geox",
    timeout: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Send text to FLAME for summarization/synthesis.

    Graceful degradation: returns dict with 'ok'=False on failure.
    Caller must check result.get('ok') before using content.

    Args:
        text: Self-contained text to summarize
        caller_id: Optional caller identifier for audit
        timeout: HTTP timeout in seconds (default 8)

    Returns:
        Dict with keys: ok (bool), content (str), model, provider,
        latency_ms, authority. Never None.
    """
    result = _flame_post("/summarize", {
        "text": text[:MAX_BODY_CHARS],
        "caller_id": caller_id,
        "sensitivity": "PUBLIC",
        "task_class": "summarize",
    }, timeout_s=timeout)
    if result and result.get("ok"):
        return {
            "ok": True,
            "content": result.get("content", ""),
            "model": result.get("model", "unknown"),
            "provider": result.get("provider", "unknown"),
            "latency_ms": result.get("latency_ms", 0),
            "authority": "ADVISORY",
        }
    return {
        "ok": False,
        "content": "",
        "error": "FLAME unavailable or empty response",
        "authority": "ADVISORY",
    }


def flame_classify(
    text: str,
    categories: list[str] | None = None,
    caller_id: str = "geox",
    timeout: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Send text to FLAME for classification.

    Graceful degradation: returns dict with 'ok'=False on failure.

    Args:
        text: Self-contained text to classify
        categories: Optional list of category labels
        caller_id: Optional caller identifier for audit
        timeout: HTTP timeout in seconds (default 8)

    Returns:
        Dict with keys: ok (bool), content (str), authority. Never None.
    """
    payload = {
        "text": text[:MAX_BODY_CHARS],
        "caller_id": caller_id,
        "sensitivity": "PUBLIC",
        "task_class": "classify",
    }
    if categories:
        payload["categories"] = ",".join(categories)

    result = _flame_post("/classify", payload, timeout_s=timeout)
    if result and result.get("ok"):
        return {
            "ok": True,
            "content": result.get("content", ""),
            "model": result.get("model", "unknown"),
            "provider": result.get("provider", "unknown"),
            "authority": "ADVISORY",
        }
    return {"ok": False, "content": "", "authority": "ADVISORY"}


def flame_contradiction_analysis(
    claim_a_text: str,
    claim_b_text: str,
    caller_id: str = "geox",
) -> dict[str, Any] | None:
    """Analyse semantic contradiction between two claims via FLAME.

    Used as fallback when the 13-type rule-based classifier returns UNKNOWN.
    FLAME identifies contradiction type + severity + resolution path.

    Graceful degradation: returns None on failure.

    Args:
        claim_a_text: First claim text
        claim_b_text: Second claim text
        caller_id: Optional caller identifier

    Returns:
        Dict with 'type', 'severity', 'reason', 'resolution' keys,
        or None on failure.
    """
    prompt = (
        f"Analyse the contradiction between these two geological claims.\n\n"
        f"Claim A: {claim_a_text[:2000]}\n\n"
        f"Claim B: {claim_b_text[:2000]}\n\n"
        f"Identify: (1) contradiction type (MEASUREMENT_CONFLICT, DATUM_CONFLICT, "
        f"INTERPRETATION_OBSERVATION_MISMATCH, MODEL_PHYSICS_VIOLATION, "
        f"CROSS_MODAL_CONFLICT, MISSING_GROUNDING, NARRATIVE_OVERRUN, "
        f"BEAUTIFUL_ONE_DRIFT, CIRCULAR_REASONING, STRUCTURAL_COHERENCE_VIOLATION, UNKNOWN), "
        f"(2) severity (FATAL, HIGH, MEDIUM, LOW), "
        f"(3) explanation, (4) resolution path (VOID, HOLD, DEMOTE, ESCALATE)."
    )

    result = _flame_post("/summarize", {
        "text": prompt,
        "caller_id": caller_id,
        "sensitivity": "PUBLIC",
        "task_type": "classify",
    })

    if result and result.get("ok"):
        return {
            "source": "FLAME",
            "analysis": result.get("content", ""),
            "model": result.get("model", "unknown"),
            "provider": result.get("provider", "unknown"),
            "authority": "ADVISORY",
            "latency_ms": result.get("latency_ms", 0),
        }
    return None
