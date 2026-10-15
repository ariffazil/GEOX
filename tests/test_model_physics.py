"""Known-answer tests for geox_model flexure + physics_section + critical_taper modes."""

import os

import pytest
from geox_mcp.tools.model_physics import compute_flexure, critical_taper_reference


class TestFlexure:
    """Validated against session-computed table (2026-10-06, Copilot+333-AGI)."""

    def test_te10_sediment_continuous(self):
        r = compute_flexure(te_km=10, infill="sediment", plate="continuous")
        row = r["results"][0]
        assert row["te_km"] == 10
        assert abs(row["forebulge_distance_km"] - 129) < 3  # 128.7

    def test_te10_sediment_broken(self):
        r = compute_flexure(te_km=10, infill="sediment", plate="broken")
        assert abs(r["results"][0]["forebulge_distance_km"] - 97) < 3  # 96.7

    def test_te5_water_continuous(self):
        r = compute_flexure(te_km=5, infill="water", plate="continuous")
        assert abs(r["results"][0]["forebulge_distance_km"] - 61) < 3  # 60.7

    def test_te5_water_broken(self):
        r = compute_flexure(te_km=5, infill="water", plate="broken")
        assert abs(r["results"][0]["forebulge_distance_km"] - 46) < 3  # 45.5

    def test_te15_sediment_continuous(self):
        r = compute_flexure(te_km=15, infill="sediment", plate="continuous")
        assert abs(r["results"][0]["forebulge_distance_km"] - 174) < 4  # 174.2

    def test_te30_sediment_continuous(self):
        r = compute_flexure(te_km=30, infill="sediment", plate="continuous")
        assert abs(r["results"][0]["forebulge_distance_km"] - 293) < 5  # 293.4

    def test_sweep_returns_table(self):
        r = compute_flexure(te_km=[5, 10, 15, 20, 30])
        assert len(r["results"]) == 5

    def test_default_sweep(self):
        r = compute_flexure()
        assert len(r["results"]) == 5

    def test_invalid_infill(self):
        with pytest.raises(ValueError):
            compute_flexure(infill="magma")

    def test_invalid_plate(self):
        with pytest.raises(ValueError):
            compute_flexure(plate="quantum")


class TestCriticalTaper:
    def test_reference_gated(self):
        r = critical_taper_reference()
        assert r["status"] == "REFERENCE_GATED"
        assert len(r["references"]) >= 3
        assert "known_answer_for_test" in r


# ── Confidentiality gate — semantic-surface scan ──────────────────────────────
# 2026-10-13 IRFANclaw-approved patch (binary: "YA, LULUSKAN PATCH REGEX GATE"):
# scan DOM text nodes + comments + external refs; exclude renderer-internal styling
# tokens (matplotlib glyph ids caused 532 false positives on asas_malam_xs.svg);
# fail CLOSED to raw scan when XML is unparseable. Forbidden-string wall unchanged.
from pathlib import Path as _Path  # noqa: E402

from geox_mcp.tools.model_physics import (  # noqa: E402
    _extract_svg_semantic_text,
    _scan_svg_confidential,
)

_NS = 'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'


def _svg(tmp_path, body, name="t.svg"):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


class TestConfidentialityGateSemanticScan:
    def test_glyph_id_false_positives_no_longer_block(self, tmp_path):
        """The production FP class: matplotlib path-mode ids matched the well-shape pattern."""
        p = _svg(
            tmp_path,
            f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg {_NS} width="100" height="100">
<defs>
  <path id="DejaVuSans-3" d="M1 2 L3 4"/>
  <path id="DejaVuSans-Oblique-3" d="M5 6"/>
  <path id="DejaVuSans-Bold-3" d="M7 8"/>
</defs>
<style>*{{stroke-linejoin: round}}</style>
<g><use xlink:href="#DejaVuSans-3"/><use xlink:href="#DejaVuSans-Bold-3"/></g>
</svg>""",
        )
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is True, gate
        assert gate["scan_surface"].startswith("svg_semantic")
        # old raw scan WOULD have blocked — advisory keeps that visible
        assert gate["raw_surface_advisory_matches"] >= 3

    def test_forbidden_string_in_text_node_blocks(self, tmp_path):
        p = _svg(tmp_path, f"<svg {_NS}><text>Rotan-2 well</text></svg>")
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is False
        assert "Rotan" in gate["scan_hits"]

    def test_well_shape_pattern_in_text_node_blocks(self, tmp_path):
        p = _svg(tmp_path, f"<svg {_NS}><text>Zampir-3</text></svg>")
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is False
        assert any("Zampir-3" in h for h in gate["scan_hits"])

    def test_reserve_figures_in_script_block(self, tmp_path):
        p = _svg(tmp_path, f'<svg {_NS}><script>var s = "500 MMbbl OOIP";</script></svg>')
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is False

    def test_comment_content_blocks(self, tmp_path):
        p = _svg(tmp_path, f"<svg {_NS}><!-- Nuri-4 draft --><text>public</text></svg>")
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is False
        assert "Nuri" in gate["scan_hits"]

    def test_external_href_scanned(self, tmp_path):
        p = _svg(tmp_path, f'<svg {_NS}><a href="https://x.example/Megah-1/r"><text>ok</text></a></svg>')
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is False

    def test_fragment_href_not_scanned(self, tmp_path):
        p = _svg(tmp_path, f'<svg {_NS}><use xlink:href="#DejaVuSans-3"/><text>ok</text></svg>')
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is True

    def test_allowlist_tepat_passes(self, tmp_path):
        p = _svg(tmp_path, f"<svg {_NS}><text>Tepat-1 discovery (public)</text></svg>")
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is True, gate

    def test_renderer_public_vocabulary_passes(self, tmp_path):
        """The real production labels: figure annotations must not block (IRFANclaw 2026-10-13)."""
        p = _svg(
            tmp_path,
            f"""<svg {_NS}>
<text>A · TRUE SCALE 1:1 — thin skin on ~30 km crust</text>
<text>BLOCK 1 · thinned continental lower plate</text>
<text>Block 2 · upper-plate crust + ophiolite</text>
<text>rifted passive MARGIN 1 (dead)</text>
<text>· Mt Kinabalu 4,095 m</text>
<text>Crocker Range</text>
<text>BUT 2.9 km of moat relief needs sediment load PLUS downdrag</text>
</svg>""",
        )
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is True, gate

    def test_allowlist_stays_specific_unknown_block_number_still_blocks(self, tmp_path):
        # "BLOCK 1/2" exempt ≠ every "Block N": a hypothetical Block 9 must still trip the net
        p = _svg(tmp_path, f"<svg {_NS}><text>Block 9</text></svg>")
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is False

    def test_allowlist_does_not_rescue_forbidden_strings(self, tmp_path):
        # the six partner strings block regardless of any allowlist entry nearby
        p = _svg(tmp_path, f"<svg {_NS}><text>Kinabalu trend near Rotan</text></svg>")
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is False
        assert "Rotan" in gate["scan_hits"]

    def test_style_css_excluded_by_design(self, tmp_path):
        # approved design: internal styling strings are not disclosure surface
        p = _svg(tmp_path, f"<svg {_NS}><style>.Rotan {{ color: red }}</style><text>ok</text></svg>")
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is True

    def test_malformed_svg_fails_closed_to_raw_scan(self, tmp_path):
        p = _svg(tmp_path, "not xml at all <<< Zoisit >>>")
        assert _extract_svg_semantic_text(p) is None
        gate = _scan_svg_confidential(p)
        assert gate["scan_surface"] == "raw_fallback_xml_parse_failed"
        assert gate["scan_clean"] is False
        assert "Zoisit" in gate["scan_hits"]

    @pytest.mark.skipif(
        not os.path.exists("/root/GEOX/geox/skills/subsurface/section/output/asas_malam_xs.svg"),
        reason="production artifact not present (CI)",
    )
    def test_production_artifact_passes_with_advisory(self):
        """Regression against the real 532-FP artifact (2026-10-13 incident)."""
        p = _Path("/root/GEOX/geox/skills/subsurface/section/output/asas_malam_xs.svg")
        gate = _scan_svg_confidential(p)
        assert gate["scan_clean"] is True, gate
        assert gate["raw_surface_advisory_matches"] >= 500  # old raw scan blocked on these
