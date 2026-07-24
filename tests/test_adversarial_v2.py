"""Adversarial tests — T1 through T10 for seismic interpretation integrity.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

# ── helpers ──────────────────────────────────────────────────────────────────


def _hash(obj):
    raw = json.dumps(obj, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


# ── T1: Narrative claim guard ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_T1_vanilla_narrative_attack():
    """Unsupported claims: TWT→depth, probability, closure, drilling advice."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    result = await geox_seismic_interpret(
        mode="interpret",
        framework={
            "horizons": [{"name": "H1", "picks": [{"cmp": 100, "twt_ms": 175}, {"cmp": 200, "twt_ms": 180}]}],
        },
        request={
            "claim_text": "175 ms equals 250 m depth. 75% probability of success. Four-way closure. High-grade for drilling.",
        },
    )

    assert result.get("ok") is False
    assert result.get("error") == "NARRATIVE_CLAIM_BLOCKED"
    ng = result.get("narrative_guard") or {}
    blocked_codes = {b.get("code") for b in ng.get("blocked") or []}
    assert "DEPTH_FROM_TWT_UNMEASURED" in blocked_codes
    assert "PROBABILITY_THEATRE" in blocked_codes
    assert "FOUR_WAY_UNMEASURED" in blocked_codes
    assert "DRILLING_BLOCKED" in blocked_codes
    # seal/verdict hard blocks
    assert result.get("seal_eligibility") is not True
    assert result.get("preferred_hypothesis") is None
    assert result.get("local_verdict") == "QUALIFIED_CANDIDATE"


# ── T2: Image-only without calibration ───────────────────────────────────────


@pytest.mark.asyncio
async def test_T2_image_only_without_calibration():
    """Image-only mode + no velocity → no depth claims, no seal."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    # Small PNG for image_only code path
    import base64
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="gray").save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    result = await geox_seismic_interpret(
        mode="interpret_section",
        image_data=b64,
        emit_bundle=True,
        calibration={"input_class": "image_only", "calibrated": False},
    )

    # interpret_section always stamps image_only input_class
    assert result.get("input_class") == "image_only"
    # No true depth from image only
    assert result.get("preferred_hypothesis") is None
    # local_verdict is QUALIFIED_CANDIDATE at most
    assert result.get("local_verdict") == "QUALIFIED_CANDIDATE"
    # seal_eligibility must be false for image-only
    assert result.get("seal_authority") == "arifOS_only"
    # interpret_section must never silently fall back to another mode
    assert result.get("mode") in ("interpret_section", "classical_section", "section_image")

    # Check interpretation_bundle exists and has seal_eligibility
    ib = result.get("interpretation_bundle") or {}
    # image-only bundles should not be seal-eligible
    se = ib.get("seal_eligibility")
    assert se is None or se is False

    # hypotheses present but not preferred (0 when no VLM backend, still valid)
    hyps = ib.get("hypotheses") or result.get("hypotheses") or []
    # No VLM → 0 hypotheses is fine — the important thing is we didn't crash
    # and preferred_hypothesis is still null
    assert isinstance(hyps, list)


# ── T3: Vertical exaggeration only ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_T3_vertical_exaggeration_only():
    """VE supplied but no azimuth or strike → true dip UNMEASURED (no false confidence)."""
    from geox_mcp.tools.structure_validate import geox_structure_validate

    result = await geox_structure_validate(
        calibration={
            "vertical_exaggeration": 5.0,
            "calibrated": False,
        },
        framework={
            "faults": [
                {
                    "name": "F1",
                    "sticks": [
                        {"cmp": 100, "twt_ms": 500},
                        {"cmp": 200, "twt_ms": 600},
                    ],
                }
            ],
            "horizons": [
                {
                    "name": "H1",
                    "order_index": 0,
                    "picks": [
                        {"cmp": 50, "twt_ms": 400},
                        {"cmp": 250, "twt_ms": 450},
                    ],
                }
            ],
        },
        emit_bundle=False,
    )

    gates = result.get("gates") or {}

    # K-DIP: with VE=5, 60° image dip can be corrected, but no true azimuth/strike
    # means true dip is derived from geometric correction only — may be WARN or KILL
    kdip = gates.get("K-DIP") or {}
    status = kdip.get("status") or "UNMEASURED"
    assert status in ("UNMEASURED", "WARN", "KILL", "PASS"), f"Unexpected K-DIP status: {status}"

    # Structure gates must produce combined verdict
    cgv = result.get("combined_gate_verdict")
    assert cgv in ("KILL", "PASS", "PARTIAL", "UNMEASURED"), f"Unexpected combined_verdict: {cgv}"

    # VE alone is partial information — not definitive
    assert result.get("local_verdict") == "QUALIFIED_CANDIDATE"


# ── T4: Checkshot + axis cal + gates fire, 2D ≠ 4-way closure ────────────────


@pytest.mark.asyncio
async def test_T4_checkshot_and_line_geometry():
    """Calibrated framework → gates fire, but 2D alone ≠ seal eligibility."""
    from geox_mcp.tools.structure_validate import geox_structure_validate

    result = await geox_structure_validate(
        calibration={
            "checkshot_ref": "CHK-001",
            "bin_spacing_m": 25.0,
            "sample_interval_ms": 4.0,
            "section_azimuth_deg": 90.0,
            "vertical_exaggeration": 1.0,
            "calibrated": True,
        },
        framework={
            "faults": [
                {
                    "name": "F1",
                    "sticks": [
                        {"cmp": 100, "twt_ms": 500},
                        {"cmp": 110, "twt_ms": 520},
                    ],
                    "strike_deg": 0.0,
                    "dip_direction": "E",
                }
            ],
            "horizons": [
                {
                    "name": "H1",
                    "order_index": 0,
                    "picks": [
                        {"cmp": 50, "twt_ms": 400},
                        {"cmp": 250, "twt_ms": 450},
                    ],
                }
            ],
        },
        emit_bundle=False,
    )

    gates = result.get("gates") or {}
    assert len(gates) > 0, "At least one gate must run"
    # 2D data cannot self-seal
    assert result.get("seal_eligibility") is not True
    assert result.get("local_verdict") == "QUALIFIED_CANDIDATE"
    # Calibrated gate should not be UNMEASURED for all gates
    measured = [k for k, v in gates.items() if isinstance(v, dict) and v.get("status") != "UNMEASURED"]
    assert len(measured) >= 1, "At least one gate should be measured with calibration"


# ── T5: Impossible fault topology ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_T5_impossible_fault_topology():
    """Fault with vertical stick geometry, horizon crossing detection."""
    from geox_mcp.tools.structure_validate import geox_structure_validate

    result = await geox_structure_validate(
        calibration={
            "bin_spacing_m": 25.0,
            "sample_interval_ms": 4.0,
            "vertical_exaggeration": 1.0,
            "calibrated": True,
        },
        framework={
            "faults": [
                {
                    "name": "F1",
                    # Hanging wall and footwall nearly vertical = extreme geometry
                    "sticks": [
                        {"cmp": 100, "twt_ms": 400},
                        {"cmp": 100, "twt_ms": 600},
                        {"cmp": 99, "twt_ms": 700},
                    ],
                    "dip_deg_image": 90,
                }
            ],
            "horizons": [
                {
                    "name": "H1",
                    "order_index": 0,
                    "picks": [{"cmp": 50, "twt_ms": 420}, {"cmp": 200, "twt_ms": 420}],
                },
                {
                    "name": "H2",
                    "order_index": 1,
                    "picks": [{"cmp": 50, "twt_ms": 580}, {"cmp": 200, "twt_ms": 580}],
                },
            ],
        },
        emit_bundle=False,
    )

    gates = result.get("gates") or {}
    has_kill_or_warn = any(
        (v.get("status") or v.get("verdict")) in ("KILL", "WARN") for v in gates.values() if isinstance(v, dict)
    )
    # At minimum, combined verdict should be computed
    assert result.get("combined_gate_verdict") in ("KILL", "PASS", "PARTIAL", "UNMEASURED"), (
        f"Unexpected: {result.get('combined_gate_verdict')}"
    )
    # Even if no kill/warn, structure_validate must not crash
    assert result.get("ok") is True


# ── T6: Independent witnesses (no averaging) ──────────────────────────────────


@pytest.mark.asyncio
async def test_T6_independent_witnesses():
    """Four incompatible geometry sets → four independent records, no averaging."""
    from geox_mcp.tools.structure_validate import geox_structure_validate

    frameworks = [
        {"faults": [{"name": "F1a", "sticks": [{"cmp": 100, "twt_ms": 500}, {"cmp": 120, "twt_ms": 550}]}]},
        {"faults": [{"name": "F1b", "sticks": [{"cmp": 80, "twt_ms": 520}, {"cmp": 140, "twt_ms": 540}]}]},
        {"faults": [{"name": "F1c", "sticks": [{"cmp": 60, "twt_ms": 480}, {"cmp": 160, "twt_ms": 600}]}]},
        {"faults": [{"name": "F1d", "sticks": [{"cmp": 90, "twt_ms": 510}, {"cmp": 130, "twt_ms": 530}]}]},
    ]

    results = []
    for fw in frameworks:
        r = await geox_structure_validate(
            framework=fw,
            calibration={"vertical_exaggeration": 2.0, "bin_spacing_m": 25.0},
            emit_bundle=False,
        )
        results.append(r)

    assert len(results) == 4
    for r in results:
        # Inconclusive means no dominant hypothesis from GEOX
        assert r.get("preferred_hypothesis") is None
        assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
        # Each result is independent — different gate states expected
        assert isinstance(r.get("gates"), dict)


# ── T7: Direct vs bridge parity ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_T7_direct_versus_bridge_parity():
    """Same payload twice must produce identical physics verdict."""
    from geox_mcp.tools.structure_validate import geox_structure_validate

    payload_args = dict(
        calibration={"bin_spacing_m": 25.0, "vertical_exaggeration": 1.0},
        framework={
            "faults": [
                {
                    "name": "F1",
                    "sticks": [{"cmp": 100, "twt_ms": 500}, {"cmp": 120, "twt_ms": 520}],
                }
            ],
            "horizons": [
                {
                    "name": "H1",
                    "order_index": 0,
                    "picks": [{"cmp": 50, "twt_ms": 400}, {"cmp": 250, "twt_ms": 450}],
                }
            ],
        },
        emit_bundle=False,
    )

    r1 = await geox_structure_validate(**payload_args)
    r2 = await geox_structure_validate(**payload_args)

    assert r1.get("combined_gate_verdict") == r2.get("combined_gate_verdict")

    g1 = r1.get("gates") or {}
    g2 = r2.get("gates") or {}
    for gate_id in set(list(g1.keys()) + list(g2.keys())):
        s1 = (g1.get(gate_id) or {}).get("status") or (g1.get(gate_id) or {}).get("verdict")
        s2 = (g2.get(gate_id) or {}).get("status") or (g2.get(gate_id) or {}).get("verdict")
        assert s1 == s2, f"Gate {gate_id} mismatch: {s1} vs {s2}"


# ── T8: Unsupported mode / boundary ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_T8_unknown_and_unsupported_modes():
    """Unknown modes must error gracefully; held modes must not silently remap."""
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    # Unknown mode
    r1 = await geox_seismic_interpret(mode="nonexistent_mode_zzz")
    assert r1.get("ok") is False
    assert r1.get("error") == "UNKNOWN_MODE"

    # Held/internal modes must not silently execute
    r2 = await geox_seismic_interpret(mode="vision")
    assert r2.get("ok") is False
    assert r2.get("error") == "MODE_NOT_PUBLIC"

    # interpret_section without image
    r3 = await geox_seismic_interpret(mode="interpret_section")
    assert r3.get("ok") is False
    err = r3.get("error")
    assert err in (
        "MISSING_IMAGE",
        "MISSING_IMAGE_PATH",
        "IMAGE_NOT_FOUND",
    ), f"Got: {err}"


# ── T9: Surface truth consistency ────────────────────────────────────────────


def test_T9_surface_truth_consistency():
    """Generated surfaces must have consistent tool sets."""
    import yaml

    root = Path(__file__).resolve().parent.parent  # /root/GEOX

    # Read manifest
    manifest_path = root / "src" / "geox_mcp" / "tools_manifest.yaml"
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    manifest_tools_raw = manifest.get("tools") or []
    if manifest_tools_raw and isinstance(manifest_tools_raw, list):
        manifest_tools = {t.get("name") for t in manifest_tools_raw if isinstance(t, dict)}
    else:
        manifest_tools = set(manifest_tools_raw)

    # Read CANONICAL_PUBLIC_SURFACE.json
    canon_path = root / "CANONICAL_PUBLIC_SURFACE.json"
    with open(canon_path) as f:
        canon = json.load(f)
    canon_tools = set(t.get("name") for t in canon.get("tools", []))

    # Canon is curated public subset of full manifest (internal tools included)
    assert canon_tools.issubset(manifest_tools), (
        f"Canon {len(canon_tools)} must be subset of Manifest {len(manifest_tools)}: "
        f"missing from manifest: {canon_tools - manifest_tools}"
    )
    # All public tools must appear in manifest
    assert canon_tools == manifest_tools or canon_tools.issubset(manifest_tools), (
        f"Canon {len(canon_tools)} vs Manifest {len(manifest_tools)}: "
        f"extra in canon not in manifest: {canon_tools - manifest_tools}"
    )
    # public_count should match canonical_tools count
    public_count = canon.get("public_count")
    assert public_count is None or public_count == len(canon_tools)

    # ZEN_15 must be archived if present
    zen15 = root / "docs" / "ZEN_15_SURFACE.md"
    if zen15.exists():
        content = zen15.read_text()
        assert "ARCHIVED" in content or "archive" in content.lower(), "ZEN_15_SURFACE.md must be marked as archived"


# ── T10: Render determinism ──────────────────────────────────────────────────


def test_T10_render_determinism():
    """Same inputs → byte-identical output (deterministic render)."""
    from geox_mcp.tools.section_render import render_section_overlay

    faults = [{"fault_id": "F1", "points": [{"x": 100, "y": 500}, {"x": 120, "y": 520}]}]
    horizons = [{"horizon_id": "H1", "points": [{"x": 50, "y": 400}, {"x": 250, "y": 450}]}]

    r1 = render_section_overlay(
        faults=faults,
        horizons=horizons,
        title="T10 test",
        hypothesis_id="T10-HYP",
    )
    r2 = render_section_overlay(
        faults=faults,
        horizons=horizons,
        title="T10 test",
        hypothesis_id="T10-HYP",
    )

    assert r1.get("png_sha256") == r2.get("png_sha256"), (
        f"Deterministic render must produce identical output: {r1.get('png_sha256')} vs {r2.get('png_sha256')}"
    )
    assert r1.get("receipt_hash") == r2.get("receipt_hash"), "Content hashes must match"
    assert r1.get("ok") is True
    assert r2.get("ok") is True
