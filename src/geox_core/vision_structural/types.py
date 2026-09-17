"""Frozen types for the GEOX deterministic structural-vision layer.

The Measurement envelope is the unit of exchange. It carries a NUMBER, its COVERAGE,
the METHOD that produced it, and declared UNCERTAINTY — never a probability, never a
verdict. UNMEASURED is a first-class state: it is not a pass and not a fail.

See CONTRACT.md §3–§4. Do not extend this module's public surface without a contract bump.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ExtractionStatus = Literal["MEASURED", "PARTIAL", "UNMEASURED"]

__all__ = [
    "ExtractionStatus",
    "Measurement",
    "unmeasured",
    "measured",
]

# Keys that must never appear in a vision-layer payload. A CV algorithm cannot emit a
# probability about geological truth; doing so fabricates confidence (F7 HUMILITY).
FORBIDDEN_PROBABILITY_KEYS: tuple[str, ...] = (
    "confidence",
    "reliability",
    "probability",
    "p_truth",
    "score",
    "certainty",
)


@dataclass(frozen=True)
class Measurement:
    """One measured quantity: value + coverage + method + uncertainty.

    Invariants:
      * MEASURED requires a value AND coverage (confidence without coverage is invalid).
      * UNMEASURED carries no value — it means "not tested", never "zero" and never "pass".
      * PARTIAL carries a value, and MUST declare what is missing in `notes`.
    """

    value: float | None
    unit: str
    status: ExtractionStatus
    n_samples: int = 0
    coverage: float | None = None
    method: str = ""
    uncertainty: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in ("MEASURED", "PARTIAL", "UNMEASURED"):
            raise ValueError(f"invalid status {self.status!r}")
        if self.status == "MEASURED":
            if self.value is None:
                raise ValueError("MEASURED requires a value")
            if self.coverage is None:
                raise ValueError(
                    "MEASURED requires coverage — confidence without coverage is invalid"
                )
        if self.status == "UNMEASURED":
            if self.value is not None:
                raise ValueError("UNMEASURED must not carry a value")
        if self.status == "PARTIAL" and not self.notes:
            raise ValueError("PARTIAL must declare what is missing in notes[]")
        if self.coverage is not None and not (0.0 <= self.coverage <= 1.0):
            raise ValueError(f"coverage must be 0..1, got {self.coverage}")
        if self.coverage is None and self.status == "PARTIAL":
            raise ValueError("PARTIAL requires coverage")

    # ── serialisation ────────────────────────────────────────────────────────

    def asdict(self) -> dict[str, Any]:
        return asdict(self)

    def to_framework(self) -> float | None:
        """Value for injection into a `run_regime_falsification` framework dict.

        UNMEASURED returns None so the downstream gate reads it as *not measured*
        rather than as a zero. A zero would be a fabricated kill.
        """
        return self.value if self.status in ("MEASURED", "PARTIAL") else None

    @property
    def is_usable(self) -> bool:
        return self.status in ("MEASURED", "PARTIAL") and self.value is not None


def unmeasured(unit: str, *, method: str = "", reason: str = "", **kw: Any) -> Measurement:
    """Construct an UNMEASURED Measurement with an explicit reason in notes."""
    notes = list(kw.pop("notes", []) or [])
    if reason:
        notes.append(reason)
    return Measurement(
        value=None, unit=unit, status="UNMEASURED", method=method, notes=notes, **kw
    )


def measured(
    value: float,
    unit: str,
    *,
    coverage: float,
    n_samples: int,
    method: str,
    uncertainty: dict[str, Any] | None = None,
    notes: list[str] | None = None,
) -> Measurement:
    """Construct a MEASURED Measurement. Coverage is mandatory by design."""
    return Measurement(
        value=float(value),
        unit=unit,
        status="MEASURED",
        n_samples=int(n_samples),
        coverage=float(coverage),
        method=method,
        uncertainty=uncertainty or {},
        notes=list(notes or []),
    )
