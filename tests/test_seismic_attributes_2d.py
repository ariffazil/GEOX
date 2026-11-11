"""
Seismic attribute catalog — 2D section lane
═══════════════════════════════════════════
Coverage of the common post-stack attribute variants (Sheriff 2002 / Chopra & Marfurt
2007 families) plus the known-answer behaviour of the artifact pre-pass.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import numpy as np
import pytest


# ─────────────────────────── helpers ───────────────────────────


def _ricker(n: int, amp: float) -> np.ndarray:
    t = np.arange(n) - n // 2
    a = (np.pi / (n / 6.0)) ** 2
    return amp * (1 - 2 * a * t**2) * np.exp(-a * t**2)


def _section(rows: int = 128, cols: int = 96, fault_row: int = 60, fault_slope: float = 0.4):
    """Bedding reflector stack + one cross-cutting reflector (ground truth known)."""
    sec = np.zeros((rows, cols))
    w = _ricker(11, 1.0)
    for k, row in enumerate(range(6, rows, 26)):
        n = min(11, rows - row)
        sec[row : row + n, :] += (0.45 * (-1) ** k) * w[:n, None]
    wf = _ricker(11, 1.0)
    truth = np.zeros(cols)
    for x in range(cols):
        y = int(fault_row + fault_slope * x)
        truth[x] = y + 5  # ricker centre
        n = min(11, rows - y)
        sec[y : y + n, x] += 1.35 * wf[:n]
    return sec, truth


# ─────────────────────────── catalog coverage ───────────────────────────


def test_catalog_covers_the_common_variants():
    from geox_mcp.tools.seismic_attributes_2d import ATTRIBUTE_SPECS

    families = {v["family"] for v in ATTRIBUTE_SPECS.values()}
    assert {"amplitude", "complex_trace", "frequency", "structure"} <= families

    # the common post-stack variants must all be present
    for name in (
        "amplitude",
        "envelope",
        "rms",
        "energy",
        "variance",
        "mean_amplitude",
        "max_magnitude",
        "sweetness",
        "instantaneous_phase",
        "cosine_phase",
        "instantaneous_frequency",
        "instantaneous_bandwidth",
        "apparent_polarity",
        "dominant_frequency",
        "centroid_frequency",
        "coherence",
        "discontinuity",
        "semblance",
        "dip",
        "azimuth",
        "curvature",
    ):
        assert name in ATTRIBUTE_SPECS, f"missing common variant: {name}"

    assert len(ATTRIBUTE_SPECS) >= 21, f"catalog too small: {len(ATTRIBUTE_SPECS)}"

    for name, spec in ATTRIBUTE_SPECS.items():
        assert spec.get("formula"), f"{name} has no formula"
        assert spec.get("units"), f"{name} has no units"
        assert spec.get("note"), f"{name} has no note"


def test_frequency_attributes_never_claim_hz():
    """F2: this lane owns no sample interval, so no attribute may be labelled Hz."""
    from geox_mcp.tools.seismic_attributes_2d import ATTRIBUTE_SPECS

    for name, spec in ATTRIBUTE_SPECS.items():
        if "frequency" in name:
            units = spec["units"].lower().replace("not hz", "")
            assert "hz" not in units, f"{name} claims Hz"


def test_out_of_scope_declares_reasons():
    from geox_mcp.tools.seismic_attributes_2d import OUT_OF_SCOPE

    assert len(OUT_OF_SCOPE) >= 4
    for row in OUT_OF_SCOPE:
        assert row.get("attribute") and row.get("reason") and row.get("where_it_lives")


def test_catalog_manifest_shape():
    from geox_mcp.tools.seismic_attributes_2d import catalog_manifest

    m = catalog_manifest()
    assert m["attribute_count"] >= 21
    assert set(m["families"]) == {"amplitude", "complex_trace", "frequency", "structure"}
    assert "Sheriff" in m["taxonomy_source"]
    assert "rows=TIME" in m["orientation"]


# ─────────────────────────── computation ───────────────────────────


def test_new_attributes_all_finite():
    from geox_mcp.tools.seismic_attributes_2d import compute_new_attributes

    sec, _ = _section()
    out = compute_new_attributes(sec, window=11)
    for name, arr in out.items():
        assert np.all(np.isfinite(arr)), f"{name} has non-finite values"
        assert arr.shape[0] == sec.shape[0], f"{name} shape drift"


def test_semblance_bounded_and_coherent():
    from geox_mcp.tools.seismic_attributes_2d import compute_new_attributes

    sec, _ = _section()
    out = compute_new_attributes(sec, window=11)
    sem = out["semblance"]
    assert sem.min() >= -1e-9
    assert sem.max() <= 1.0 + 1e-9


def test_apparent_polarity_is_sign_only():
    from geox_mcp.tools.seismic_attributes_2d import compute_new_attributes

    sec, _ = _section()
    out = compute_new_attributes(sec, window=11)
    pol = np.unique(out["apparent_polarity"])
    assert set(pol.tolist()) <= {-1.0, 0.0, 1.0}


def test_frequency_attributes_are_cycles_per_sample():
    from geox_mcp.tools.seismic_attributes_2d import compute_new_attributes

    sec, _ = _section()
    out = compute_new_attributes(sec, window=11)
    dom = out["dominant_frequency"]
    cen = out["centroid_frequency"]
    assert dom.min() >= 0.0
    assert dom.max() <= 0.5 + 1e-9  # Nyquist for d=1
    assert cen.min() >= 0.0
    assert cen.max() <= 0.5 + 1e-9


def test_envelope_finds_the_crosscutting_reflector():
    """Known-answer: envelope peak must sit on the reflector, not on a bedding peak."""
    from geox_mcp.tools.seismic_attributes_2d import compute_new_attributes

    sec, truth = _section()
    env = compute_new_attributes(sec, window=11)["envelope"]
    errs = np.array([abs(int(np.argmax(env[:, x])) - int(truth[x])) for x in range(sec.shape[1])])
    hit = float((errs <= 4).mean())
    assert hit >= 0.85, f"envelope reflector hit rate too low: {hit:.3f}"


# ─────────────────────────── artifact pre-pass ───────────────────────────


def _raster_with_decoys(rows: int = 128, cols: int = 160):
    sec, truth = _section(rows=rows, cols=cols, fault_row=50, fault_slope=0.35)
    a = np.clip((sec - sec.min()) / (sec.max() - sec.min()), 0, 1)
    signed = (a - 0.5) * 2
    i = np.abs(signed)
    pos = signed > 0
    rgb = np.empty((rows, cols, 3), float)
    rgb[..., 0] = np.where(pos, 255, 255 * (1 - i))
    rgb[..., 1] = np.where(pos, 255 * (1 - i), 255 * (1 - i))
    rgb[..., 2] = np.where(pos, 255 * (1 - i), 255)
    black = np.zeros((rows, cols), bool)
    black[10:18, 120:150] = True
    red = np.zeros((rows, cols), bool)
    red[40:50, 120:155] = True
    rgb[black] = (20, 20, 20)
    rgb[red] = (220, 30, 30)
    return rgb.astype(np.uint8), black, red, truth


def test_artifact_zones_detect_both_decoy_classes():
    from geox_mcp.tools.seismic_attributes_2d import detect_artifact_zones_rgb

    rgb, black, red, _ = _raster_with_decoys()
    art = detect_artifact_zones_rgb(rgb)
    assert art[black].mean() >= 0.95, "black-ink decoy missed"
    assert art[red].mean() >= 0.70, "colour-conforming flat label missed"


def test_artifact_scan_excludes_annotation_from_the_proxy():
    from geox_mcp.tools.seismic_attributes_2d import extract_seismic_convention

    rgb, black, red, _ = _raster_with_decoys()
    proxy, meta = extract_seismic_convention(rgb)
    assert meta["extraction"] == "rb_seismic_convention"
    assert meta["polarity"].startswith("PRESERVED")
    assert meta["artifact_fraction"] > 0.0
    # annotation pixels must not carry amplitude
    assert float(np.abs(proxy[black]).max()) == 0.0
    assert float(np.abs(proxy[red]).max()) == 0.0


# ─────────────────────────── tool surface ───────────────────────────


@pytest.mark.asyncio
async def test_attribute_mode_reachable_through_unified_impl():
    from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute

    sec, _ = _section()
    r = await geox_seismic_compute(
        mode="attribute",
        attribute="envelope",
        amplitude_grid=sec.tolist(),
        provenance="fixture",
    )
    assert r.get("ok") is True
    assert r.get("mode") == "attribute"
    assert "envelope" in r["summaries"]
    assert r.get("receipt_hash")
    assert r.get("preferred_hypothesis") is None


@pytest.mark.asyncio
async def test_attribute_mode_exposes_the_manifest_and_out_of_scope():
    from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute

    sec, _ = _section()
    r = await geox_seismic_compute(
        mode="attribute",
        attribute="all",
        amplitude_grid=sec.tolist(),
        provenance="fixture",
    )
    manifest = r.get("attribute_manifest") or {}
    assert manifest.get("attribute_count", 0) >= 21
    assert manifest.get("out_of_scope")
    for family in ("amplitude", "complex_trace", "frequency", "structure"):
        assert manifest["families"].get(family)


@pytest.mark.asyncio
async def test_raster_path_is_tagged_display_derived_proxy():
    import tempfile
    from pathlib import Path

    from PIL import Image

    from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute

    rgb, _black, _red, _truth = _raster_with_decoys()
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "section.png"
        Image.fromarray(rgb, "RGB").save(p)
        r = await geox_seismic_compute(
            mode="attribute",
            attribute="envelope",
            image_path=str(p),
            provenance="display_figure",
        )
    assert r.get("ok") is True
    assert r.get("truth_class") == "DISPLAY_DERIVED_PROXY"
    assert r.get("prohibited_uses")
    scan = r.get("artifact_scan") or {}
    assert scan.get("applied") is True
    assert scan.get("artifact_pixels", 0) > 0


@pytest.mark.asyncio
async def test_avo_forward_shape_unchanged():
    """Regression guard for af-fix #3/#6b (scar LOW 0.5)."""
    from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute

    r = await geox_seismic_compute(
        mode="avo_forward",
        vp1=3.0,
        vs1=1.5,
        rho1=2.3,
        vp2=2.5,
        vs2=1.2,
        rho2=2.1,
        theta_deg=[0.0, 10.0, 20.0],
    )
    assert r.get("mode") == "avo_forward"
    assert r.get("zoeppritz")
    assert "R_PP" in r["zoeppritz"]
    assert "reflectivity" in r


def test_unknown_attribute_lists_the_live_catalog():
    from geox_mcp.tools.seismic_zen_f1 import compute_attributes_2d

    sec, _ = _section()
    out = compute_attributes_2d(sec, attribute="not_an_attribute", window=11)
    assert out["ok"] is False
    assert out["error"] == "UNKNOWN_ATTRIBUTE"
    assert "envelope" in out["live_attributes"]
    assert "instantaneous_frequency" in out["live_attributes"]
