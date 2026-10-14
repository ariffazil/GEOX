"""GEOX-side weighted physics prior P (pointer target for arifOS LANE A item 2).

AX-0 (2026-10-14): the well/seismic/geology-weighted interpretation of P moved
here from arifOS apex_canonical.compute_P. The kernel now computes only
explicit measured values; this module owns the DOMAIN semantics.

Rules inherited from AX-0 (no invented values):
- An unmeasured dial contributes nothing; weights renormalise over measured
  dials only.
- All dials unmeasured -> None (UNMEASURED). Never a default prior.
- Contradiction rules require the winning dial to be measured, else None.
- Caller must pass explicit numeric values. If a domain default is genuinely
  justified, it must be passed explicitly by the caller — this module never
  fabricates one.
"""


def compute_p_weighted(
    p_well: float | None,
    p_seis: float | None,
    p_geo: float | None,
    w_well: float = 0.4,
    w_seis: float = 0.3,
    w_geo: float = 0.3,
    well_contradicts_seis: bool = False,
    seis_contradicts_geo: bool = False,
) -> float | None:
    """Domain-weighted physics prior. Returns None when UNMEASURED."""
    measured = {"well": p_well, "seis": p_seis, "geo": p_geo}
    if all(v is None or v <= 0 for v in measured.values()):
        return None
    if well_contradicts_seis:
        return round(min(1.0, max(0.0, p_well)), 4) if (p_well or 0) > 0 else None
    if seis_contradicts_geo:
        return round(min(1.0, max(0.0, p_seis)), 4) if (p_seis or 0) > 0 else None
    pairs = [
        (w_well, p_well),
        (w_seis, p_seis),
        (w_geo, p_geo),
    ]
    pairs = [(w, v) for w, v in pairs if v is not None and v > 0]
    w_total = sum(w for w, _ in pairs)
    if w_total == 0:
        return None
    return round(min(1.0, max(0.0, sum((w / w_total) * v for w, v in pairs))), 4)
