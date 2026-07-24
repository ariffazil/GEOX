"""K-RESTORE / G5 — restoration balance numerics (PR-C3).

Build-not-buy (no mature OSS restore lib). Deterministic 2D methods:

  - line-length balance    hanging-wall / footwall polyline length ratio
  - area balance           area above fault vs. area below fault
  - residual               max(line-length_deviation, area_deviation)
  - hard veto when residual > tolerance (default 5%)

Gating rules (F13):
  - missing fault geometry  →  UNMEASURED (cannot measure balance)
  - residual > tolerance    →  KILL
  - residual ≤ tolerance    →  PASS
  - self_intersection=True  →  KILL (restoration is geometrically impossible)
  - closes=False            →  KILL (restoration does not close)
  - Caller-supplied residual/closes (offline trishear etc.) is also accepted.

Literature anchors:
  Dahlstrom 1969 — Balanced cross-sections
  Groshong ADS — Area-depth-strain analysis

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt

_DEFAULT_TOL = 0.05  # 5% line-length / area residual

_EQUATION = (
    "residual = max(|hw-fw|/max(hw,fw), |a_above-a_below|/max(a_above,a_below)) — line-length + area balance (Dahlstrom 1969)"
)


def _fault_lengths(fault: dict[str, Any]) -> tuple[float | None, float | None]:
    """Return (hw_length, fw_length). Looks for hanging_wall_segments /
    footwall_segments; falls back to throw_profile heuristic."""
    hw: float | None = None
    fw: float | None = None

    if isinstance(fault.get("hanging_wall_segments"), (list, tuple)) and fault["hanging_wall_segments"]:
        try:
            hw = float(sum(float(s) for s in fault["hanging_wall_segments"]))
        except (TypeError, ValueError):
            hw = None

    if isinstance(fault.get("footwall_segments"), (list, tuple)) and fault["footwall_segments"]:
        try:
            fw = float(sum(float(s) for s in fault["footwall_segments"]))
        except (TypeError, ValueError):
            fw = None

    if hw is None or fw is None:
        prof = fault.get("throw_profile")
        if isinstance(prof, (list, tuple)) and prof:
            try:
                throws = []
                for s in prof:
                    if isinstance(s, dict):
                        throws.append(abs(float(s.get("throw") or s.get("throw_m") or 0)))
                    else:
                        throws.append(abs(float(s)))
                half = sum(throws) / 2.0
                hw = hw if hw is not None else half
                fw = fw if fw is not None else half
            except (TypeError, ValueError):
                pass

    return hw, fw


def _fault_areas(fault: dict[str, Any]) -> tuple[float | None, float | None]:
    """Return (area_above, area_below). Caller-supplied from horizon polygons
    clipped by the fault trace."""
    if isinstance(fault.get("area_above_m2"), (int, float)) and isinstance(fault.get("area_below_m2"), (int, float)):
        return float(fault["area_above_m2"]), float(fault["area_below_m2"])
    return None, None


def _line_length_residual(hw: float, fw: float) -> float:
    if hw <= 0 or fw <= 0:
        return float("inf")
    return abs(hw - fw) / max(hw, fw)


def _area_residual(a_above: float, a_below: float) -> float:
    if a_above <= 0 or a_below <= 0:
        return float("inf")
    return abs(a_above - a_below) / max(a_above, a_below)


def gate_k_restore(framework: dict[str, Any]) -> dict[str, Any]:
    """K-RESTORE / G5 — restoration balance with real numerics."""
    faults = framework.get("faults") or []
    restore = framework.get("restore") or framework.get("restoration") or {}

    # Caller-supplied residuals win (offline trishear etc.)
    residual = restore.get("residual") if isinstance(restore, dict) else None
    if residual is None:
        residual = framework.get("restore_residual")
    closes = restore.get("closes") if isinstance(restore, dict) else framework.get("restore_closes")
    self_intersect = restore.get("self_intersection") if isinstance(restore, dict) else framework.get("restore_self_intersection")
    tol = float(
        (restore.get("tolerance") if isinstance(restore, dict) else None) or framework.get("restore_tolerance") or _DEFAULT_TOL
    )

    findings: list[dict[str, Any]] = []

    # Hard veto: self-intersection
    if self_intersect is True:
        findings.append({"verdict": "KILL", "reason": "Restore self-intersection"})

    # Hard veto: non-closure
    if closes is False:
        findings.append({"verdict": "KILL", "reason": "Restore does not close"})

    # Compute numerics from fault geometry when caller hasn't pre-computed
    per_fault_residuals: list[float] = []
    if residual is None and faults:
        for f in faults:
            fid = f.get("fault_id") or f.get("id") or "unknown"
            hw, fw = _fault_lengths(f)
            a_above, a_below = _fault_areas(f)

            ll_res = _line_length_residual(hw, fw) if hw is not None and fw is not None else None
            ar_res = _area_residual(a_above, a_below) if a_above is not None and a_below is not None else None

            if ll_res is None and ar_res is None:
                findings.append(
                    {
                        "fault_id": fid,
                        "verdict": "UNMEASURED",
                        "reason": ("Missing hanging_wall/footwall_segments or area_above/below_m2 — cannot compute balance"),
                    }
                )
                continue

            r_candidates = [r for r in (ll_res, ar_res) if r is not None and r != float("inf")]
            if not r_candidates:
                findings.append(
                    {
                        "fault_id": fid,
                        "verdict": "UNMEASURED",
                        "reason": "All measurements non-positive",
                    }
                )
                continue
            r = max(r_candidates)
            per_fault_residuals.append(r)

            if r > tol:
                findings.append(
                    {
                        "fault_id": fid,
                        "verdict": "KILL",
                        "reason": f"Restore residual {r:.3f} > tolerance {tol}",
                        "line_length_residual": ll_res,
                        "area_residual": ar_res,
                        "tolerance": tol,
                    }
                )
            else:
                findings.append(
                    {
                        "fault_id": fid,
                        "verdict": "PASS",
                        "reason": f"Restore residual {r:.3f} within {tol}",
                        "line_length_residual": ll_res,
                        "area_residual": ar_res,
                        "tolerance": tol,
                    }
                )

    # Resolve final verdict
    if any(f.get("verdict") == "KILL" for f in findings):
        status = "KILL"
        reason = "Restoration hard veto"
    elif any(f.get("verdict") == "PASS" for f in findings) and not any(f.get("verdict") == "UNMEASURED" for f in findings):
        status = "PASS"
        reason = f"All {sum(1 for f in findings if f.get('verdict') == 'PASS')} fault(s) balanced within {tol}"
    elif residual is not None:
        # Caller-supplied residual branch
        try:
            r = abs(float(residual))
            if r > tol:
                status = "KILL"
                reason = f"Restore residual {r} > tolerance {tol}"
            else:
                status = "PASS"
                reason = f"Restore residual {r} within {tol}"
            findings.append(
                {
                    "verdict": status,
                    "reason": reason,
                    "residual": r,
                    "tolerance": tol,
                }
            )
        except (TypeError, ValueError):
            status = "UNMEASURED"
            reason = "Non-numeric residual"
    else:
        # No faults AND no caller metrics → UNMEASURED
        status = "UNMEASURED"
        reason = "No restoration metrics provided (run balance offline or supply hanging/footwall segments)"

    return make_gate_receipt(
        "K-RESTORE",
        status,  # type: ignore[arg-type]
        inputs={"n_faults": len(faults), "caller_residual": residual, "tolerance": tol},
        equation=_EQUATION,
        thresholds={"default_tolerance": tol},
        calculated_result={
            "per_fault_residuals": per_fault_residuals,
            "max_residual": max(per_fault_residuals) if per_fault_residuals else None,
        },
        exceptions_considered=["offline trishear", "salt restoration (not supported)", "3D restoration (not supported)"],
        evidence_refs=[
            "Dahlstrom 1969 — Balanced cross-sections",
            "Groshong — Area-depth-strain (ADS)",
        ],
        reason=reason,
        findings=findings,
        gate_type="hard_veto",
    )
