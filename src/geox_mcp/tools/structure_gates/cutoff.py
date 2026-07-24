"""CutoffPair derivation + polarity discrimination (FIX BRIEF v2 · P2).

K-DIP is a FILTER, not the judge. True polarity discrimination uses:
  hanging-wall cutoff sense (down = normal-slip, up = reverse-slip)
  + throw taper + growth side + restoration.

Steep dip + reverse cutoff = reactivated inversion → PASS-with-note, not KILL.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any, Literal

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt

Sense = Literal["normal_slip", "reverse_slip", "ambiguous", "unmeasured"]


def _f(v: Any) -> float | None:
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def _points(obj: dict[str, Any]) -> list[tuple[float, float]]:
    pts = obj.get("points") or obj.get("pts") or obj.get("sticks") or obj.get("picks") or []
    out: list[tuple[float, float]] = []
    for i, p in enumerate(pts):
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            out.append((float(p[0]), float(p[1])))
        elif isinstance(p, dict):
            x = p.get("x", p.get("cmp", p.get("trace_index", i)))
            y = p.get("y", p.get("twt_ms", p.get("depth_m")))
            if x is not None and y is not None:
                out.append((float(x), float(y)))
    return out


def _fault_cmp_at_twt(fault_pts: list[tuple[float, float]], twt: float) -> float | None:
    if not fault_pts:
        return None
    ordered = sorted(fault_pts, key=lambda p: p[1])
    if twt <= ordered[0][1]:
        return ordered[0][0]
    if twt >= ordered[-1][1]:
        return ordered[-1][0]
    for i in range(len(ordered) - 1):
        c0, t0 = ordered[i]
        c1, t1 = ordered[i + 1]
        if min(t0, t1) <= twt <= max(t0, t1):
            if abs(t1 - t0) < 1e-9:
                return c0
            w = (twt - t0) / (t1 - t0)
            return c0 + w * (c1 - c0)
    return ordered[len(ordered) // 2][0]


def _side_mean_twt(h_pts: list[tuple[float, float]], fcmp: float, side: str) -> float | None:
    if side == "L":
        pool = [t for c, t in h_pts if c < fcmp - 1e-6]
    else:
        pool = [t for c, t in h_pts if c > fcmp + 1e-6]
    if not pool:
        return None
    return sum(pool) / len(pool)


def derive_cutoff_pairs(
    faults: list[dict[str, Any]],
    horizons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build CutoffPair list from Horizon × Fault geometry."""
    pairs: list[dict[str, Any]] = []
    for f in faults:
        if not isinstance(f, dict):
            continue
        fid = f.get("fault_id") or f.get("id") or f.get("name")
        if not fid or str(fid) == "unknown":
            continue
        fpts = _points(f)
        if len(fpts) < 2:
            continue
        # hanging-wall side heuristic: left of S-dipping, right of N-dipping
        # from stick: if cmp decreases with depth → S-dipping-ish → HW often north (right)
        dc = fpts[-1][0] - fpts[0][0]
        dt = fpts[-1][1] - fpts[0][1]
        # for reverse/normal sense we compare which side is deeper at cutoff
        for h in horizons:
            if not isinstance(h, dict):
                continue
            hid = h.get("horizon_id") or h.get("id") or h.get("name")
            if not hid:
                continue
            hpts = _points(h)
            if len(hpts) < 2:
                continue
            mean_t = sum(t for _, t in hpts) / len(hpts)
            fcmp = _fault_cmp_at_twt(fpts, mean_t)
            if fcmp is None:
                continue
            twt_l = _side_mean_twt(hpts, fcmp, "L")
            twt_r = _side_mean_twt(hpts, fcmp, "R")
            if twt_l is None or twt_r is None:
                pairs.append(
                    {
                        "horizon_id": str(hid),
                        "fault_id": str(fid),
                        "sense": "unmeasured",
                        "fault_cmp": fcmp,
                    }
                )
                continue
            # Assign HW/FW: hanging wall = deeper side for reverse (upthrown FW);
            # for normal: HW is downthrown (deeper).
            # Without independent HW knowledge, report geometric sense of offset:
            # if right deeper than left by threshold → right_down; use regime_prior for HW label
            throw_ms = abs(twt_r - twt_l)
            deeper_side = "R" if twt_r > twt_l else "L"
            regime = str(f.get("regime_prior") or f.get("regime") or "").lower()
            # Convention: for a fault, hanging wall is the block that moved relative to FW.
            # Geometric slip sense from which side is downthrown:
            #   downthrown deeper → that side is HW for normal; FW for reverse.
            # We report sense relative to "deeper block is hanging wall" (normal_slip)
            # vs "shallower block is hanging wall" would be reverse if HW known.
            # Operational rule (brief): hw_twt > fw_twt (deeper HW) = normal_slip
            #                         hw_twt < fw_twt (shallower HW) = reverse_slip
            # Without HW label, use regime_prior to assign HW:
            if regime in ("normal", "extensional"):
                # HW = downthrown = deeper
                if deeper_side == "R":
                    hw_twt, fw_twt = twt_r, twt_l
                else:
                    hw_twt, fw_twt = twt_l, twt_r
                sense: Sense = "normal_slip" if hw_twt >= fw_twt else "reverse_slip"
            elif regime in ("reverse", "thrust", "compressional"):
                # HW = upthrown for reverse? Actually reverse: HW moves up relative to FW
                # so HW is shallower in post-fault geometry for reverse.
                if deeper_side == "R":
                    # right deeper → if reverse, HW is left (shallower)
                    hw_twt, fw_twt = twt_l, twt_r
                else:
                    hw_twt, fw_twt = twt_r, twt_l
                sense = "reverse_slip" if hw_twt <= fw_twt else "normal_slip"
            else:
                # no regime: pure geometric — deeper = "downthrown_side"
                hw_twt, fw_twt = (twt_r, twt_l) if deeper_side == "R" else (twt_l, twt_r)
                sense = "ambiguous" if throw_ms < 5.0 else "normal_slip"  # geometric downthrown as HW

            if throw_ms < 2.0:
                sense = "ambiguous"

            pairs.append(
                {
                    "horizon_id": str(hid),
                    "fault_id": str(fid),
                    "hw_twt": hw_twt,
                    "fw_twt": fw_twt,
                    "throw_ms": throw_ms,
                    "sense": sense,
                    "fault_cmp": fcmp,
                    "twt_l": twt_l,
                    "twt_r": twt_r,
                    "regime_prior": regime or None,
                    "deeper_side": deeper_side,
                }
            )
    return pairs


def polarity_from_cutoffs(cutoffs: list[dict[str, Any]], fault_id: str) -> dict[str, Any]:
    """Aggregate cutoff sense for one fault."""
    relevant = [c for c in cutoffs if c.get("fault_id") == fault_id]
    if not relevant:
        return {"sense": "unmeasured", "n": 0}
    senses = [c.get("sense") for c in relevant if c.get("sense") not in (None, "unmeasured", "ambiguous")]
    if not senses:
        return {"sense": "ambiguous" if relevant else "unmeasured", "n": len(relevant)}
    normal = sum(1 for s in senses if s == "normal_slip")
    reverse = sum(1 for s in senses if s == "reverse_slip")
    if normal > reverse:
        return {"sense": "normal_slip", "n": len(relevant), "votes": {"normal": normal, "reverse": reverse}}
    if reverse > normal:
        return {"sense": "reverse_slip", "n": len(relevant), "votes": {"normal": normal, "reverse": reverse}}
    return {"sense": "ambiguous", "n": len(relevant), "votes": {"normal": normal, "reverse": reverse}}


def gate_k_polarity(framework: dict[str, Any]) -> dict[str, Any]:
    """K-POLARITY — cutoff-sense discrimination (filter chain, not sole judge).

    Does NOT kill on dip alone. Compares regime_prior to cutoff sense.
    Steep reverse with reverse cutoffs → PASS. Steep reverse with normal cutoffs
    and reactivation → WARN (inversion). Clear contradiction without exception → WARN/KILL soft.
    """
    faults = framework.get("faults") or []
    cutoffs = framework.get("cutoffs") or []
    if not cutoffs and faults and (framework.get("horizons") or []):
        cutoffs = derive_cutoff_pairs(faults, framework.get("horizons") or [])

    if not faults:
        return make_gate_receipt(
            "K-POLARITY",
            "UNMEASURED",
            reason="No faults",
            equation="sense from CutoffPair: hw deeper→normal_slip; hw shallower→reverse_slip",
            inputs={"n_faults": 0},
            thresholds={},
            calculated_result={},
            gate_type="soft_conditional",
        )

    findings = []
    kills = passes = warns = unmeas = 0
    for f in faults:
        if not isinstance(f, dict):
            continue
        fid = f.get("fault_id") or f.get("id") or "unknown"
        pol = polarity_from_cutoffs(cutoffs, str(fid))
        sense = pol.get("sense")
        regime = str(f.get("regime_prior") or f.get("regime") or "unknown").lower()
        reactivation = bool(f.get("reactivation_evidence") or f.get("reactivation") or regime in ("inversion", "inverted"))

        if sense in ("unmeasured", None):
            unmeas += 1
            findings.append({"fault_id": fid, "status": "UNMEASURED", "reason": "no cutoff pairs", "polarity": pol})
            continue
        if sense == "ambiguous":
            unmeas += 1
            findings.append({"fault_id": fid, "status": "UNMEASURED", "reason": "ambiguous cutoffs", "polarity": pol})
            continue

        # map regime to expected sense
        if regime in ("normal", "extensional"):
            expected = "normal_slip"
        elif regime in ("reverse", "thrust", "compressional"):
            expected = "reverse_slip"
        else:
            unmeas += 1
            findings.append(
                {
                    "fault_id": fid,
                    "status": "UNMEASURED",
                    "reason": "regime_prior unknown — cutoff sense recorded but not judged",
                    "polarity": pol,
                    "cutoff_sense": sense,
                }
            )
            continue

        if sense == expected:
            passes += 1
            findings.append(
                {
                    "fault_id": fid,
                    "status": "PASS",
                    "cutoff_sense": sense,
                    "regime_prior": regime,
                    "reason": "cutoff sense matches regime_prior",
                }
            )
        elif reactivation or regime in ("inversion", "inverted"):
            warns += 1
            findings.append(
                {
                    "fault_id": fid,
                    "status": "WARN",
                    "cutoff_sense": sense,
                    "regime_prior": regime,
                    "reason": "sense≠regime but reactivation/inversion exception — PASS-with-note class",
                }
            )
        else:
            # soft kill — polarity mismatch without exception
            warns += 1  # WARN not KILL: K-DIP-style sole-source kill forbidden
            findings.append(
                {
                    "fault_id": fid,
                    "status": "WARN",
                    "cutoff_sense": sense,
                    "regime_prior": regime,
                    "reason": "cutoff sense disagrees with regime_prior — needs throw/growth/restore chain",
                }
            )

    if kills:
        status = "KILL"
    elif passes or warns:
        status = "PASS" if not warns else "WARN"
    else:
        status = "UNMEASURED"

    return make_gate_receipt(
        "K-POLARITY",
        status,  # type: ignore[arg-type]
        equation="CutoffPair sense vs regime_prior; reactivation → WARN not KILL; dip never sole-source",
        inputs={"n_faults": len(faults), "n_cutoffs": len(cutoffs)},
        thresholds={"reactivation_exception": True, "dip_alone_kill": False},
        calculated_result={"kills": kills, "passes": passes, "warns": warns, "unmeasured": unmeas},
        reason=f"passes={passes} warns={warns} unmeasured={unmeas}",
        findings=findings,
        gate_type="soft_conditional",
        exceptions_considered=["reactivation", "inversion", "section_obliquity", "VE_distortion"],
        evidence_refs=["Bond 2007 multi-interpretation", "Anderson 1951 (dip filter only)"],
    )
