"""DEPRECATED package name (organ collision with WELL :18083).

Canonical import path: ``geox.welllog`` (well-log / stratigraphy domain).
This package re-exports welllog for backward compatibility until 2026-08-15.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "geox.well is deprecated; use geox.welllog (well-log stratigraphy, not WELL organ).",
    DeprecationWarning,
    stacklevel=2,
)

try:
    from geox.welllog import *  # noqa: F403
except Exception:
    pass

__all__ = []
