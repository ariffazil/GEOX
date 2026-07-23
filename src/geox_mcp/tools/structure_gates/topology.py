"""G2 / K-XCUT — horizon topology hard veto.

Missing geometry → UNMEASURED. Cross/order fail → KILL.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt

_EQUATION = "Horizons non-crossing; order_index shallow→deep implies mean y monotonic if depth-down"


def _ys(horizon: dict[str, Any]) -> list[float] | None:
    pts = horizon.get("points") or horizon.get("pts")
    if not pts:
        return None
    ys: list[float] = []
    for p in pts:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            ys.append(float(p[1]))
        elif isinstance(p, dict):
            for k in ("y", "twt_ms", "depth_m", "sample", "z"):
                if k in p and p[k] is not None:
                    ys.append(float(p[k]))
                    break
    return ys if ys else None


def _to_xy(horizon: dict[str, Any]) -> list[tuple[float, float]] | None:
    pts = horizon.get("points") or horizon.get("pts")
    if not pts:
        return None
    out: list[tuple[float, float]] = []
    for i, p in enumerate(pts):
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            out.append((float(p[0]), float(p[1])))
        elif isinstance(p, dict):
            x = p.get("x", p.get("trace_index", p.get("inline", i)))
            y = p.get("y", p.get("twt_ms", p.get("depth_m", p.get("sample"))))
            if x is None or y is None:
                continue
            out.append((float(x), float(y)))
    return out if len(out) >= 2 else None


def _segments_cross(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> bool:
    def orient(p, q, r):
        return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

    def on_seg(p, q, r):
        return min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and min(p[1], r[1]) <= q[1] <= max(
            p[1], r[1]
        )

    def intersects(p1, q1, p2, q2):
        o1, o2 = orient(p1, q1, p2), orient(p1, q1, q2)
        o3, o4 = orient(p2, q2, p1), orient(p2, q2, q1)
        if o1 * o2 < 0 and o3 * o4 < 0:
            return True
        if o1 == 0 and on_seg(p1, p2, q1):
            return True
        if o2 == 0 and on_seg(p1, q2, q1):
            return True
        if o3 == 0 and on_seg(p2, p1, q2):
            return True
        if o4 == 0 and on_seg(p2, q1, q2):
            return True
        return False

    for i in range(len(a) - 1):
        for j in range(len(b) - 1):
            if intersects(a[i], a[i + 1], b[j], b[j + 1]):
                return True
    return False


def gate_g2_topology(framework: dict[str, Any]) -> dict[str, Any]:
    horizons = framework.get("horizons") or []
    findings: list[dict[str, Any]] = []

    # Explicit polarity reverse without relay
    if framework.get("throw_polarity_reversal") and not framework.get("relay_zone"):
        return make_gate_receipt(
            "G2",
            "KILL",
            reason="Throw polarity reverse without relay",
            equation=_EQUATION,
            inputs={"throw_polarity_reversal": True, "relay_zone": False},
            thresholds={"polity_reversal_without_relay": "KILL"},
            calculated_result={"n_kill_findings": 1},
            evidence_refs=["Bond group SE 2019 — structural crosscut consistency"],
            findings=[{"verdict": "KILL", "reason": "polarity_reversal"}],
            gate_type="hard_veto",
        )

    if framework.get("topology_cross") is True or framework.get("horizons_cross") is True:
        return make_gate_receipt(
            "G2",
            "KILL",
            reason="Caller flagged horizons_cross",
            equation=_EQUATION,
            inputs={"explicit_flag": True},
            thresholds={"explicit_flag": "any_true"},
            calculated_result={"n_kill_findings": 1},
            evidence_refs=["Bond group SE 2019 — structural crosscut consistency"],
            findings=[{"verdict": "KILL", "reason": "explicit cross flag"}],
            gate_type="hard_veto",
        )

    if len(horizons) < 2:
        return make_gate_receipt(
            "G2",
            "UNMEASURED",
            reason="Need ≥2 horizons for topology",
            equation=_EQUATION,
            inputs={"n_horizons": len(horizons)},
            thresholds={"min_horizons": 2},
            calculated_result={"n_horizons": len(horizons), "min_required": 2},
            evidence_refs=["Bond group SE 2019 — structural crosscut consistency"],
            gate_type="hard_veto",
        )

    for i in range(len(horizons)):
        for j in range(i + 1, len(horizons)):
            hi, hj = horizons[i], horizons[j]
            a, b = _to_xy(hi), _to_xy(hj)
            if a and b and _segments_cross(a, b):
                findings.append(
                    {
                        "verdict": "KILL",
                        "reason": "Horizons cross in section",
                        "h_a": hi.get("horizon_id") or hi.get("id"),
                        "h_b": hj.get("horizon_id") or hj.get("id"),
                    }
                )

    ordered = sorted(horizons, key=lambda h: h.get("order_index", h.get("order", 0)))
    means: list[tuple[str, float]] = []
    for h in ordered:
        ys = _ys(h)
        if ys:
            means.append((str(h.get("horizon_id") or h.get("id")), sum(ys) / len(ys)))
    if len(means) >= 2 and all("order_index" in h or "order" in h for h in ordered):
        for k in range(len(means) - 1):
            if means[k][1] > means[k + 1][1] + 1e-6:
                findings.append(
                    {
                        "verdict": "KILL",
                        "reason": (
                            f"Negative thickness / order inversion: "
                            f"{means[k][0]} > {means[k+1][0]}"
                        ),
                    }
                )

    if any(f.get("verdict") == "KILL" for f in findings):
        return make_gate_receipt(
            "G2",
            "KILL",
            reason="Topology hard veto",
            equation=_EQUATION,
            inputs={"n_horizons": len(horizons)},
            thresholds={"min_horizons": 2, "monotonic": "increasing y = deeper"},
            evidence_refs=["Bond group SE 2019 — structural crosscut consistency"],
            findings=findings,
            calculated_result={"n_kill_findings": len(findings)},
            gate_type="hard_veto",
        )

    with_geom = sum(1 for h in horizons if _to_xy(h))
    if with_geom < 2:
        return make_gate_receipt(
            "G2",
            "UNMEASURED",
            reason="Insufficient polyline geometry",
            equation=_EQUATION,
            inputs={"n_horizons": len(horizons), "n_with_geometry": with_geom},
            thresholds={"min_horizons_with_geometry": 2},
            calculated_result={"n_horizons_with_geometry": with_geom, "n_kill_findings": 0},
            evidence_refs=["Bond group SE 2019 — structural crosscut consistency"],
            findings=findings,
            gate_type="hard_veto",
        )

    return make_gate_receipt(
        "G2",
        "PASS",
        reason="No horizon cross / order inversion detected",
        equation=_EQUATION,
        inputs={"n_horizons": len(horizons), "n_with_geometry": with_geom},
        thresholds={"min_horizons_with_geometry": 2},
        evidence_refs=["Bond group SE 2019 — structural crosscut consistency"],
        findings=findings,
        calculated_result={"cross_count": 0, "negative_thickness_count": 0},
        gate_type="hard_veto",
    )
