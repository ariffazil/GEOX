"""Per-call governed identity propagated from GEOX ingress to output envelopes."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

GEOX_IDENTITY_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar(
    "geox_identity_context",
    default=None,
)
