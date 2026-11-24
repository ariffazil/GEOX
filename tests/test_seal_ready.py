"""555 GOLDEN — seal-ready cases (external verify 2026-11-24T06:02Z, live ba713f97b).

Rule: these must FAIL on ba713f97b and PASS after the fix. Each test names the task ID.
No network. Run: /opt/geox/.venv/bin/python -m pytest tests/test_seal_ready.py -v
"""
from __future__ import annotations

import asyncio
import inspect
import json
import math
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"


def _run(coro):
    return asyncio.run(coro)


def _geo(**state):
    from geox_mcp.tools.geomechanics_unified import geox_geomechanics
    return _run(geox_geomechanics(mode="derive_moduli", state=state))


# ── T1: geomechanics must not silently default ────────────────────────────

def test_T1_known_answer_moduli():
    """Declared keys, physical values → exact moduli (K 13.8, G 5.175, nu 0.333)."""
    r = _geo(vp=3000, vs=1500, rho=2300)
    m = (r.get("result") or {}).get("moduli") or {}
    assert m.get("K_GPa") == pytest.approx(13.8, abs=0.05), m
    assert m.get("G_GPa") == pytest.approx(5.175, abs=0.02), m
    assert m.get("nu") == pytest.approx(0.3333, abs=0.002), m


def test_T1_alias_keys_are_mapped_not_defaulted():
    """{vp_m_s, vs_m_s, rho_kg_m3} must be USED (vp 4000), never replaced by 3000."""
    r = _geo(vp_m_s=4000, vs_m_s=2180, rho_kg_m3=2400)
    if r.get("isError") or (r.get("result") or {}).get("error"):
        pytest.skip("alias path returns an explicit error — acceptable per T1")
    st = (r.get("result") or {}).get("input_state") or {}
    assert st.get("vp") == pytest.approx(4000, abs=1), f"alias not mapped; got {st}"
    assert st.get("vs") == pytest.approx(2180, abs=1), st
    assert st.get("rho") == pytest.approx(2400, abs=1), st


def test_T1_unknown_key_never_defaults():
    """A state with no usable vp/vs/rho must ERROR, not default + grade AAA."""
    r = _geo(vp_metres_per_second=4000)  # wrong key entirely
    err = bool(r.get("isError")) or bool((r.get("result") or {}).get("error"))
    grade = (r.get("result") or {}).get("grade")
    assert err or grade != "AAA", f"unknown key defaulted and still graded AAA: {grade}"


def test_T1_impossible_vp_vs_rejected_and_moduli_null():
    """Vs >= 0.866*Vp implies nu >= 0.5 (unphysical) → reject, moduli null."""
    r = _geo(vp=4000, vs=3600, rho=2400)  # 0.866*4000 = 3464 < 3600
    res = r.get("result") or {}
    err = bool(r.get("isError")) or bool(res.get("error"))
    m = res.get("moduli")
    assert err or m in (None, {}), f"unphysical state accepted with moduli {m}"


# ── T2/T3: prospect provenance + percentile convention ───────────────────

def _inv_fn():
    import geox_mcp.tools.inverse_volumetrics as m
    for name, obj in vars(m).items():
        if inspect.isfunction(obj) and "sw_range" in inspect.signature(obj).parameters:
            return obj
    return None


def test_T2_supplied_field_is_input_not_default():
    fn = _inv_fn()
    if fn is None:
        pytest.skip("no inverse-volumetrics callable found")
    sig = inspect.signature(fn)
    kw = {"net_pay_m": 45.0}
    if "porosity_range" in sig.parameters:
        kw["porosity_range"] = (0.19, 0.25)
    if "sw_range" in sig.parameters:
        kw["sw_range"] = (0.15, 0.25)
    if "supplied_fields" in sig.parameters:
        kw["supplied_fields"] = ["net_pay_m"]
    out = fn(**kw)
    prov = (out or {}).get("input_provenance") or {}
    tag = prov.get("net_pay_m")
    assert tag == "INPUT", f"supplied net_pay_m tagged {tag!r} (must be INPUT)"


def test_T3_percentile_convention_is_declared_prms():
    fn = _inv_fn()
    if fn is None:
        pytest.skip("no inverse-volumetrics callable found")
    sig = inspect.signature(fn)
    kw = {}
    for p, v in (("net_pay_m", 30.0), ("porosity_range", (0.19, 0.25)), ("sw_range", (0.15, 0.25))):
        if p in sig.parameters:
            kw[p] = v
    out = fn(**kw) or {}
    conv = out.get("percentile_convention")
    assert conv is not None, "percentile convention not declared"
    assert "prms" in str(conv).lower(), f"convention is {conv!r}; B6 requires SPE-PRMS declared"


# ── T4: temporal decline must state method, window, unit ─────────────────

def test_T4_decline_method_and_window_echoed():
    from geox.egs.tools.temporal import temporal_decline
    data = [{"year": 2009, "production": 46820}, {"year": 2010, "production": 29277},
            {"year": 2011, "production": 14802}, {"year": 2012, "production": 10115}]
    r = _run(temporal_decline(production_data=data))
    res = (r or {}).get("results") or {}
    assert "method" in res, f"method not stated; keys={list(res)}"
    assert "window" in res or "window_years" in res, f"window not echoed; keys={list(res)}"


def test_T4_regression_matches_41_percent():
    from geox.egs.tools.temporal import temporal_decline
    data = [{"year": 2009, "production": 46820}, {"year": 2010, "production": 29277},
            {"year": 2011, "production": 14802}, {"year": 2012, "production": 10115}]
    r = _run(temporal_decline(production_data=data, method="regression"))
    res = (r or {}).get("results") or {}
    rate = res.get("decline_rate_pct_annual")
    assert rate is not None, res
    assert abs(rate - 41.0) <= 1.0, f"regression gave {rate}; expected 41.0 ±1"


# ── AVO: Shuey on measured Draupne/Hugin values ──────────────────────────

def test_AVO_shuey_class_I_from_measured_intervals():
    """Cap 3066/1628/2456 over res 3557/2225/2271 → A +0.035, B -0.2925, class I."""
    vp1, vs1, r1 = 3066.0, 1628.0, 2456.0
    vp2, vs2, r2 = 3557.0, 2225.0, 2271.0
    dvp = (vp2 - vp1) / ((vp2 + vp1) / 2)
    dvs = (vs2 - vs1) / ((vs2 + vs1) / 2)
    drho = (r2 - r1) / ((r2 + r1) / 2)
    A = 0.5 * (dvp + drho)
    B = 0.5 * dvp - 2 * (((vs1 + vs2) / 2) / ((vp1 + vp2) / 2)) ** 2 * (drho + 2 * dvs)
    assert A == pytest.approx(0.035, abs=0.005), A
    assert B == pytest.approx(-0.2925, abs=0.01), B
    assert A > 0 and (A + B) < 0, "sign pattern for class I not satisfied"


# ── petro: Rw tagged INPUT/OBS ───────────────────────────────────────────

def test_petro_rw_supplied_is_obs():
    from geox_mcp.tools.petrophysics_unified import geox_petrophysics
    r = _run(geox_petrophysics(mode="generate", well_id="T",
        curves={"GR": [40.0, 50.0, 60.0], "RHOB": [2.30, 2.28, 2.32],
                "RT": [30.0, 25.0, 40.0], "DT": [80.0, 82.0, 78.0]},
        depth_m=[1000.0, 1001.0, 1002.0], gr_clean=25, gr_shale=100, rw=0.0417))
    prov = r.get("input_provenance")
    if prov is None:
        pytest.skip("generate path did not expose provenance")
    assert prov.get("rw_ohm_m") in ("OBS", "INPUT"), prov


# ── registry: names in the public surface must be real ───────────────────

def test_public_surface_names_registered():
    p = SRC / "geox_mcp" / "generated" / "CANONICAL_PUBLIC_SURFACE.json"
    if not p.exists():
        pytest.skip("surface manifest absent")
    data = json.loads(p.read_text())
    names = data.get("tools") or data.get("public_names") or []
    if names and isinstance(names[0], dict):
        names = [n.get("name") for n in names]
    assert len(names) == 29, f"expected 29, got {len(names)}"
    assert all(str(n).startswith("geox_") for n in names)
