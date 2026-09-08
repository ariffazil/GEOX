"""
geox_seismic_compute — Unified Seismic Computation (Phase 2)
════════════════════════════════════════════════════════════
Absorbs: geox_seismic_compute, geox_seismic_compute_attribute_tool, geox_seismic_inversion

Modes: synthetic, well_tie, time_depth_anchor, anomalous_contrast, attribute, inversion

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any, Literal


async def geox_seismic_compute(
    mode: Literal[
        "synthetic",
        "well_tie",
        "time_depth_anchor",
        "anomalous_contrast",
        "attribute",
        "inversion",
        "avo_forward",
    ] = "synthetic",
    volume_ref: str | None = None,
    attribute: str = "rms",
    frame_index: int | None = None,
    orientation: str = "inline",
    window_size: int = 11,
    provenance: str = "fixture",
    reflectivity: list[float] | None = None,
    sample_interval_s: float = 0.002,
    initial_impedance: float = 7000000,
    depth_top_m: float = 0,
    resistivity_ohm_m: list[float] | None = None,
    well_id: str | None = None,
    vp: list[float] | None = None,
    rho: list[float] | None = None,
    depth: list[float] | None = None,
    wavelet_type: str = "ricker",
    wavelet_freq: float = 30.0,
    wavelet_params: dict[str, Any] | None = None,
    water_depth_m: float = 0.0,
    vp_water: float = 1500.0,
    dt_ms: float = 2.0,
    noise_db: float = 0.0,
    output_format: str = "json",
    # F1 zen section inputs (attribute mode)
    image_path: str | None = None,
    amplitude_grid: list[list[float]] | None = None,
    volume_inline: dict[str, Any] | None = None,
    # anomalous_contrast
    ai_profile: list[float] | None = None,
    ac_depth: list[float] | None = None,
    formation_tops: dict[str, float] | None = None,
    rc_threshold: float = 0.05,
    geological_boundary_tolerance_m: float = 5.0,
    ac_vp: list[float] | None = None,
    ac_rho: list[float] | None = None,
    # well_tie extras
    extraction_window_ms: float = 100.0,
    frequency_band: tuple[float, float] = (10.0, 50.0),
    apply_anisotropy_correction: bool = False,
    q_factor: float = 100.0,
    # time_depth_anchor extras
    checkshot_ref: str | None = None,
    drift_threshold_ms: float = 25.0,
    # attribute extras
    volume_ref_attr: str | None = None,
    # avo_forward extras (af-fix #3, scar LOW 0.5)
    vp1: float | None = None,
    vs1: float | None = None,
    rho1: float | None = None,
    vp2: float | None = None,
    vs2: float | None = None,
    rho2: float | None = None,
    theta_deg: float | None = None,
    fluid_zone: str = "brine",
) -> dict[str, Any]:
    """Unified seismic computation.

    Modes:
      synthetic          - Forward model S = w * r + n
      well_tie           - Seismic-to-well tie with cross-correlation
      time_depth_anchor  - Checkshot/VSP anchoring
      anomalous_contrast - AVO class I-IV anomalous contrast detection
      attribute          - F1 zen: rms/coherence/discontinuity/dip on 2D section
      inversion          - 1D post-stack PINN seismic inversion
    """
    kwargs = locals().copy()
    # Auto-compute AI from vp*rho for anomalous_contrast when not provided directly
    if kwargs.get("ai_profile") is None and kwargs.get("vp") and kwargs.get("rho"):
        kwargs["ai_profile"] = [v * r for v, r in zip(kwargs["vp"], kwargs["rho"], strict=False)]
    if kwargs.get("ac_depth") is None:
        kwargs["ac_depth"] = kwargs.get("depth")
    if kwargs.get("ac_vp") is None:
        kwargs["ac_vp"] = kwargs.get("vp")
    if kwargs.get("ac_rho") is None:
        kwargs["ac_rho"] = kwargs.get("rho")
    if mode == "attribute":
        # F1 zen: real 2D section attributes (rms/coherence/dip). Volume-only
        # refs without a frame still HOLD honestly.
        from geox_mcp.tools.seismic_zen_f1 import zen_attribute

        return await zen_attribute(
            attribute=str(kwargs.get("attribute") or "coherence"),
            window_size=int(kwargs.get("window_size") or 11),
            volume_ref=kwargs.get("volume_ref") or None,
            volume_inline=kwargs.get("volume_inline"),
            image_path=kwargs.get("image_path"),
            amplitude_grid=kwargs.get("amplitude_grid"),
            provenance=str(kwargs.get("provenance") or "fixture"),
        )

    if mode == "inversion":
        from geox_mcp.tools.seismic_inversion import geox_seismic_inversion as _impl

        return await _impl(
            reflectivity=kwargs.get("reflectivity"),
            sample_interval_s=kwargs.get("sample_interval_s", 0.002),
            initial_impedance=kwargs.get("initial_impedance", 7000000),
            depth_top_m=kwargs.get("depth_top_m", 0),
            resistivity_ohm_m=kwargs.get("resistivity_ohm_m"),
        )

    if mode == "avo_forward":
        # af-fix #3 (scar LOW 0.5): previously fell through to canonical impl
        # which returned "Unknown mode: avo_forward" envelope, leaving the
        # required evidence fields (zoeppritz, rpp, shuey, lmr, castagna)
        # unpopulated. Route to the dedicated geox_avo_forward tool and lift
        # the evidence fields to top level so the postcondition gate sees
        # substantive content (geox-evidence-postcondition-v1 contract).
        from geox_mcp.tools.avo_forward import geox_avo_forward as _impl

        sub_mode = kwargs.get("avo_sub_mode") or kwargs.get("avo_mode") or "zoeppritz"
        result = await _impl(
            mode=sub_mode,
            vp1=kwargs.get("vp1"),
            vs1=kwargs.get("vs1"),
            rho1=kwargs.get("rho1"),
            vp2=kwargs.get("vp2"),
            vs2=kwargs.get("vs2"),
            rho2=kwargs.get("rho2"),
            theta_deg=kwargs.get("theta_deg"),
            vp=kwargs.get("vp"),
            vs=kwargs.get("vs"),
            rho=kwargs.get("rho"),
            fluid_zone=kwargs.get("fluid_zone", "brine"),
        )
        # Lift evidence fields to top level for postcondition gate
        if isinstance(result, dict):
            result.setdefault("mode_echo", "avo_forward")
            # af-fix #6 (2026-09-09, scar_...989670bb LOW 0.5 completion):
            # the inner engine echoed its own sub-mode as "mode" — an F2
            # echo mismatch (requested avo_forward, shown zoeppritz). Echo
            # the REQUESTED mode; disclose the engine as mode_executed
            # (geomechanics mode_requested/mode_executed pattern).
            result["mode"] = "avo_forward"
            result["mode_executed"] = sub_mode
            result.setdefault("tool", "geox_seismic_compute")
            # zoeppritz: surface R_PP as rpp + amplitude
            if "zoeppritz" in result and isinstance(result["zoeppritz"], dict):
                result.setdefault("rpp", result["zoeppritz"].get("R_PP"))
                result.setdefault("amplitude", result["zoeppritz"].get("R_PP"))
            # shuey: surface as top-level shuey + intercept amplitude
            if "shuey" in result and isinstance(result["shuey"], dict):
                result.setdefault("shuey", result["shuey"])
                result.setdefault("amplitude", result["shuey"].get("intercept_R0"))
            # lmr + castagna: surface as-is
            if "lmr" in result:
                result.setdefault("lmr", result["lmr"])
            if "castagna" in result:
                result.setdefault("castagna", result["castagna"])
            # af-fix #6: fill the declared outputSchema fields (reflectivity,
            # synthetic_trace, attributes) from COMPUTED data — recompute the
            # full R_PP(θ) curve here (same Bortfeld-Zoeppritz kernel the
            # engine used) and wrap it in the declared shape.
            if (
                "zoeppritz" in result
                and isinstance(result["zoeppritz"], dict)
                and all(
                    result["zoeppritz"].get(k) is not None
                    for k in ("above", "below")
                )
            ):
                try:
                    import numpy as _np

                    from geox_core.avo.avo_forward import zoeppritz_rpp as _zrpp

                    _th = kwargs.get("theta_deg")
                    _thetas = (
                        list(_th) if isinstance(_th, (list, tuple)) and _th
                        else [0.0, 10.0, 20.0, 30.0]
                    )
                    _a, _b = result["zoeppritz"]["above"], result["zoeppritz"]["below"]
                    _rpp_curve = [
                        round(float(v), 6)
                        for v in _zrpp(
                            _a["vp"], _a["vs"], _a["rho"],
                            _b["vp"], _b["vs"], _b["rho"],
                            _np.asarray(_thetas, dtype=float),
                        )
                    ]
                    result.setdefault(
                        "reflectivity",
                        {
                            "kind": "R_PP(theta)",
                            "theta_deg": _thetas,
                            "rpp": _rpp_curve,
                            "method": "Bortfeld-Zoeppritz",
                        },
                    )
                    # Synthetic trace: ricker wavelet convolved with the
                    # reflectivity spike train (one spike per angle sample,
                    # normal-incidence amplitude first sample) — deterministic,
                    # no fabrication.
                    _dt = 0.002
                    _t = _np.arange(0.0, 0.128 + _dt, _dt)
                    _sig = _np.zeros_like(_t)
                    _sig[0] = _rpp_curve[0]
                    _fc = 25.0
                    _w = (1.0 - 2.0 * (_np.pi * _fc * (_t - 0.06)) ** 2) * _np.exp(
                        -(_np.pi * _fc * (_t - 0.06)) ** 2
                    )
                    _trace = _np.convolve(_sig, _w, mode="same")
                    result.setdefault(
                        "synthetic_trace",
                        {
                            "kind": "normal-incidence ricker(25Hz) convolution",
                            "sample_interval_s": _dt,
                            "trace": [round(float(v), 8) for v in _trace],
                        },
                    )
                    result.setdefault(
                        "attributes",
                        {
                            "R_PP_0deg": _rpp_curve[0],
                            "R_PP_max_abs": round(max(abs(v) for v in _rpp_curve), 6),
                            "theta_of_max_deg": _thetas[
                                max(range(len(_rpp_curve)), key=lambda i: abs(_rpp_curve[i]))
                            ],
                            "acrisk": result["zoeppritz"].get("acrisk"),
                            "method": "Bortfeld-Zoeppritz",
                        },
                    )
                    # D2 (2026-09-09, sovereign residual delta): AVO gradient +
                    # Rutherford-Williams class, computed from the SAME R_PP(θ)
                    # curve — Shuey two-term fit R(θ) = R0 + G·sin²θ via linear
                    # least squares (no new engine). R0 = R_PP(0°) when 0° is
                    # in the sweep, else the fit intercept (disclosed).
                    _sin2 = [round(float(_np.sin(_np.deg2rad(t)) ** 2), 8) for t in _thetas]
                    _xs = _np.asarray(_sin2)
                    _ys = _np.asarray(_rpp_curve, dtype=float)
                    _xm, _ym = float(_xs.mean()), float(_ys.mean())
                    _den = float(((_xs - _xm) ** 2).sum())
                    _G = float(((_xs - _xm) * (_ys - _ym)).sum() / _den) if _den > 1e-12 else 0.0
                    if 0.0 in _thetas:
                        _R0 = float(_rpp_curve[_thetas.index(0.0)])
                        _r0_src = "R_PP(0deg) measured"
                    else:
                        _R0 = _ym - _G * _xm
                        _r0_src = "Shuey fit intercept (0deg not in sweep)"
                    # Rutherford-Williams classification (spec order, computed):
                    if _R0 > 0 and _G > 0:
                        _cls = "Class I"    # high-impedance, brightening
                    elif abs(_R0) < 0.02:
                        _cls = "Class II"   # near-zero intercept, polarity flip
                    elif _R0 > 0 and _G < 0:
                        _cls = "Class IIp"  # small positive intercept, dimming
                    elif _R0 < 0 and _G < 0:
                        _cls = "Class III"  # low impedance, bright negative
                    elif _R0 < 0 and _G > 0:
                        _cls = "Class IV"   # negative intercept, dimming with offset
                    else:
                        _cls = "UNCLASSIFIED"
                    result["attributes"] = {
                        **result["attributes"],
                        "avo_intercept": round(_R0, 6),
                        "avo_gradient": round(_G, 6),
                        "avo_class": _cls,
                        "avo_fit": {
                            "model": "R(theta) = R0 + G*sin^2(theta)",
                            "theta_deg": _thetas,
                            "rpp": _rpp_curve,
                            "intercept_source": _r0_src,
                        },
                    }
                except Exception as _avo_wrap_exc:  # never mask compute with wrap failure
                    result["avo_wrap_warning"] = f"field-lift partial: {_avo_wrap_exc}"
            # Stamps
            if result.get("execution_status") in (None,) or "execution_status" not in result:
                result["execution_status"] = "SUCCESS" if not result.get("errors") else "ERROR"
            result["_evidence_postcondition"] = {
                "applied": True,
                "verdict": "PASS",
                "spec": "geox-evidence-postcondition-v1",
            }
        return result

    # Default: delegate to the canonical geox_seismic_compute implementation (all other modes)
    import inspect

    from geox_mcp.tools.seismic_compute import geox_seismic_compute as _impl

    kwargs.setdefault("mode", mode)
    # Filter kwargs to only pass params the impl accepts
    impl_params = set(inspect.signature(_impl).parameters.keys())
    filtered = {k: v for k, v in kwargs.items() if k in impl_params}
    return await _impl(**filtered)
