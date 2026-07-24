"""Mode-router contract regression — empty-input per-mode errors + propose leg.

Proves:
  - rsi_pipeline empty ≠ horizon_contrast MISSING_REQUIRED_FIELD text (no bleed)
  - classical_section aliases to interpret_section
  - interpret_section with real image emits horizon/fault candidates

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

IMG = Path("/root/GEOX/data/seismic_sections/marmousi_synthetic_section.png")
COLD = Path("/root/forge_work/2026-07-23/geox-coldstart/T3_adversarial_unlabeled_section.png")


@pytest.fixture
def image_path() -> str:
    if IMG.exists():
        return str(IMG)
    if COLD.exists():
        return str(COLD)
    pytest.skip("No seismic section PNG on host")


@pytest.mark.asyncio
async def test_empty_input_mode_contracts_are_distinct():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    cases = {
        "horizon_contrast": "MISSING_REQUIRED_FIELD",
        "rsi_pipeline": "MISSING_IMAGE_PATH",
        "interpret_section": "MISSING_IMAGE_PATH",
        "classical_section": "MISSING_IMAGE_PATH",
        "structure_validate": "EMPTY_FRAMEWORK",
        "segy_slice": "MISSING_SEGY_PATH",
        "blend": "MISSING_REQUIRED_FIELD",
        "volume_frame": "MISSING_REQUIRED_FIELD",
    }
    for mode, expected_err in cases.items():
        r = await geox_seismic_interpret(mode=mode)
        assert isinstance(r, dict), mode
        blob = json.dumps(r, default=str)
        # no TypeError crash
        assert "TypeError" not in blob
        err = r.get("error")
        # fault_sticks returns envelope VOID without error key — special case
        if mode == "fault_sticks":
            assert r.get("claim_tag") == "VOID" or r.get("claim_state") == "INGESTION_FAILED" or err
            continue
        assert err == expected_err, f"{mode}: got {err}, expected {expected_err}, body={blob[:400]}"
        # router bleed: non-horizon modes must not quote horizon_contrast contract
        if mode != "horizon_contrast":
            assert "horizon_contrast requires attribute_data" not in blob, f"bleed into {mode}"


@pytest.mark.asyncio
async def test_rsi_pipeline_empty_is_not_horizon_contrast_error():
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(mode="rsi_pipeline")
    assert r.get("error") == "MISSING_IMAGE_PATH"
    assert "attribute_data" not in (r.get("message") or "")
    assert "1D multi-attribute" not in (r.get("message") or "")


@pytest.mark.asyncio
async def test_propose_leg_interpret_section_emits_geometry(image_path: str):
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(
        mode="interpret_section",
        image_path=image_path,
        max_faults=5,
        max_horizons=4,
        emit_bundle=True,
    )
    assert r.get("ok") is True or r.get("verdict") in ("PARTIAL", "PASS", "QUALIFIED_CANDIDATE")
    horizons = r.get("horizons") or (r.get("geometry") or {}).get("horizons") or []
    faults = r.get("faults") or (r.get("geometry") or {}).get("faults") or []
    # Propose leg is alive if we get tagged geometry — faults may be 0 on
    # continuous sections (e.g. Marmousi smooth synthetic window).
    assert len(horizons) >= 1 or len(faults) >= 1, (
        f"propose leg must emit ≥1 candidate (H={len(horizons)} F={len(faults)})"
    )
    assert r.get("preferred_hypothesis") is None
    assert r.get("seal_authority") == "arifOS_only" or r.get("local_verdict") == "QUALIFIED_CANDIDATE"


@pytest.mark.asyncio
async def test_classical_section_aliases_to_propose(image_path: str):
    from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

    r = await geox_seismic_interpret(
        mode="classical_section",
        image_path=image_path,
        max_faults=3,
        max_horizons=3,
    )
    # alias must not UNKNOWN_MODE
    assert r.get("error") != "UNKNOWN_MODE", r
    horizons = r.get("horizons") or (r.get("geometry") or {}).get("horizons") or []
    assert len(horizons) >= 1
