"""GEOX --airgap mode: fail-closed outbound socket blocker for corporate/VDI offline execution."""
from __future__ import annotations

import os
import socket
from contextlib import contextmanager
from typing import Iterator

_ORIGINAL_CONNECT = socket.socket.connect
_ORIGINAL_CREATE_CONNECTION = socket.create_connection


class AirgapViolationError(RuntimeError):
    """Raised when code attempts an outbound network connection under --airgap."""


def is_airgap_enabled() -> bool:
    return os.getenv("GEOX_AIRGAP", "0").strip().lower() in ("1", "true", "yes", "on")


def enable_airgap_guard() -> None:
    """Install process-wide outbound socket block (allows AF_UNIX / loopback only if disabled)."""
    os.environ["GEOX_AIRGAP"] = "1"

    def _blocked_connect(self: socket.socket, address: object) -> None:
        raise AirgapViolationError(f"GEOX --airgap blocked outbound socket connect to {address!r}")

    def _blocked_create_connection(address: object, *args: object, **kwargs: object) -> socket.socket:
        raise AirgapViolationError(f"GEOX --airgap blocked create_connection to {address!r}")

    socket.socket.connect = _blocked_connect  # type: ignore[assignment]
    socket.create_connection = _blocked_create_connection  # type: ignore[assignment]


def disable_airgap_guard() -> None:
    socket.socket.connect = _ORIGINAL_CONNECT  # type: ignore[assignment]
    socket.create_connection = _ORIGINAL_CREATE_CONNECTION  # type: ignore[assignment]
    os.environ["GEOX_AIRGAP"] = "0"


@contextmanager
def airgap_context() -> Iterator[None]:
    enable_airgap_guard()
    try:
        yield
    finally:
        disable_airgap_guard()
