"""httpx2 compatibility shim — resolve the `httpx2` name to the installed httpx.

Six modules carry defensive exception handling written for two generations of the
HTTP client:

    import httpx2  # FastMCP 4 migration
    ...
    except (httpx.HTTPStatusError, httpx2.HTTPStatusError):

The intent is sound: tolerate whichever generation is installed. The failure mode
was not: the httpx2 distribution is absent from this venv, so a bare `import
httpx2` raised ModuleNotFoundError at *module import time*. Because
`geox_mcp/tools/macrostrat_client.py` is pulled in transitively by
`geox_mcp.servers`, the whole domain-server package — and with it every mount
path — became unimportable. A purely defensive line produced a hard failure.

This shim restores the defensive intent honestly. It does not pretend a second
HTTP library exists; it resolves the `httpx2` name to the installed `httpx`, so
`httpx2.SomeError` names the same class the guard already catches. A duplicate
entry inside an `except` tuple is harmless.

Precedence: every consumer uses a guarded import —

    try:
        import httpx2
    except ModuleNotFoundError:
        from geox_core import httpx2_shim as httpx2

— so if a real httpx2 distribution is ever installed it wins, and this module is
never consulted.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import httpx as _httpx

__all__ = ["httpx"]


def __getattr__(name: str):
    """Delegate every attribute lookup to the installed httpx module.

    Covers exception classes (ConnectError, TimeoutException, HTTPStatusError,
    RequestError) and anything else a caller reaches for, without enumerating
    the API surface here and letting it drift.
    """
    return getattr(_httpx, name)
