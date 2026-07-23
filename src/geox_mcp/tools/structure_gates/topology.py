"""G2 / K-XCUT — horizon topology hard veto.

Non-crossing (same section order), no negative thickness between ordered pairs.
Missing geometry → INCONCLUSIVE.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any


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


def _segments_cross(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> bool:
    """Simple polyline cross test in 2D (image/survey domain)."""
    def orient(p, q, r):
        return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

    def on_seg(p, q, r):
        return (
            min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
            and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])
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


def gate_g2_topology(framework: dict[str, Any]) -> dict[str, Any]:
    horizons = framework.get("horizons") or []
    findings: list[dict[str, Any]] = []

    if len(horizons) < 2:
        return {
            "gate": "G2",
            "verdict": "INCONCLUSIVE",
            "reason": "Need ≥2 horizons for topology",
            "findings": [],
            "type": "hard_veto",
        }

    # Explicit flags from caller
    if framework.get("topology_cross") is True or framework.get("horizons_cross") is True:
        return {
            "gate": "G2",
            "verdict": "KILL",
            "reason": "Caller flagged horizons_cross/topology_cross",
            "findings": [{"verdict": "KILL", "reason": "explicit cross flag"}],
            "type": "hard_veto",
        }

    # Pairwise cross
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

    # Negative thickness: ordered by order_index, mean y should be monotonic if depth-down
    ordered = sorted(
        horizons,
        key=lambda h: h.get("order_index", h.get("order", 0)),
    )
    means: list[tuple[str, float]] = []
    for h in ordered:
        ys = _ys(h)
        if ys:
            means.append((str(h.get("horizon_id") or h.get("id")), sum(ys) / len(ys)))

    if len(means) >= 2:
        # Assume increasing y = deeper (or TWT). order_index small = shallow.
        for k in range(len(means) - 1):
            if means[k][1] > means[k + 1][1] + 1e-6:
                # Possible inverted order / negative thickness if order claims shallow→deep
                if all("order_index" in h or "order" in h for h in ordered):
                    findings.append(
                        {
                            "verdict": "KILL",
                            "reason": (
                                f"Negative thickness / order inversion: "
                                f"{means[k][0]} mean_y={means[k][1]:.2f} > "
                                f"{means[k+1][0]} mean_y={means[k+1][1]:.2f}"
                            ),
                        }
                    )

    if any(f.get("verdict") == "KILL" for f in findings):
        return {
            "gate": "G2",
            "verdict": "KILL",
            "reason": "Topology hard veto",
            "findings": findings,
            "type": "hard_veto",
        }

    # All have geometry and no cross
    with_geom = sum(1 for h in horizons if _to_xy(h))
    if with_geom < 2:
        return {
            "gate": "G2",
            "verdict": "INCONCLUSIVE",
            "reason": "Insufficient polyline geometry",
            "findings": findings,
            "type": "hard_veto",
        }

    return {
        "gate": "G2",
        "verdict": "PASS",
        "reason": "No horizon cross / order inversion detected",
        "findings": findings,
        "type": "hard_veto",
    }
