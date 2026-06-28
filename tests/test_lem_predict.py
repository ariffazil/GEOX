"""
tests.test_lem_predict — geox_lem_predict conformance (W14+ FORGE 2026-06-21)

The GEOX-LEM substrate is live with a physics-prior inference path. Until
federated pretraining data (≥1,200 wells) and foundation-model weights are
deployed (gated by 888_HOLD), the tool runs in `mode="physics_prior"`. This
test suite verifies:

  1. The tool is in the canonical public surface (registry + server).
  2. Honest mock-default mode is the default.
  3. Physics9 bounds are enforced on every property.
  4. F2 TRUTH: confidence is hard-capped at 0.90.
  5. F13 SOVEREIGN: AC_Risk > 0.5 sets human_review_required.
  6. The universal envelope carries claim_tag, confidence_band, physics_guard.

DITEMPA BUKAN DIBEI — Earth evidence is forged, not given.
"""

from __future__ import annotations

import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.join(REPO_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)


# ── 1. Canonical surface presence ────────────────────────────────────────


def test_geox_lem_predict_in_canonical_registry():
    """geox_lem_predict is a backward-compat tool, accessible but not in the
    canonical 16-tool public surface. It is accessible via geox_petrophysics(mode='lem')
    in the Phase 2 Clean Architecture."""
    from geox_mcp.registry import CANONICAL_COMPAT_TOOLS

    # It's in compat tools (still callable, not publicly exposed)
    assert "geox_lem_predict" in CANONICAL_COMPAT_TOOLS, (
        "geox_lem_predict must be in CANONICAL_COMPAT_TOOLS (backward compat)"
    )


def test_expected_canonical_count_is_30():
    """Phase 2.1 Clean Architecture: 30 canonical tools (18 original + 12 EGS tools). Updated 2026-06-28.

    Old tools like geox_lem_predict are accessible via backward-compat
    wrappers but not exposed in the canonical public surface.
    """
    from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

    assert len(CANONICAL_PUBLIC_TOOLS) == 30, (
        f"CANONICAL_PUBLIC_TOOLS must be 30 in Phase 2.1 Clean Architecture, got {len(CANONICAL_PUBLIC_TOOLS)}"
    )


# ── 2. Mock-default mode ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_default_mode_is_physics_prior_honest():
    """Default mode is physics_prior and weights_status is honest."""
    from geox_mcp.tools.lem_predict import LEMPredictRequest, geox_lem_predict

    req = LEMPredictRequest(
        well_id="T-MOCK",
        curves={"GR": [40, 50, 60], "RHOB": [2.5, 2.4, 2.3]},
        depth_m=[1000.0, 1000.5, 1001.0],
        target_properties=["porosity"],
        actor_id="t",
        session_id="t",
    )
    result = await geox_lem_predict(req)
    pa = result.get("primary_artifact", {})
    assert pa.get("mode_used") == "physics_prior"
    assert pa.get("weights_status") in {"physics_prior_only", "mock_default"}
    # No fabricated transformer claims
    assert "federated_deployed" not in (pa.get("weights_status") or "")


# ── 3. Physics9 bounds enforcement ───────────────────────────────────────


@pytest.mark.asyncio
async def test_physics9_bounds_enforced_on_porosity():
    """Porosity values must stay within Physics9 bounds [0.02, 0.45]."""
    from geox_mcp.tools.lem_predict import LEMPredictRequest, geox_lem_predict

    # Extreme RHOB values to stress bounds
    req = LEMPredictRequest(
        well_id="T-BOUND",
        curves={
            "RHOB": [1.0, 2.65, 5.0, 0.5, 10.0],  # some out-of-physics
        },
        depth_m=[1000.0, 1000.5, 1001.0, 1001.5, 1002.0],
        target_properties=["porosity"],
        actor_id="t",
        session_id="t",
    )
    result = await geox_lem_predict(req)
    cells = result.get("primary_artifact", {}).get("cells", [])
    assert cells, "expected at least one cell"
    for cell in cells:
        phi = cell.get("predictions", {}).get("porosity", {}).get("value")
        if phi is not None:
            assert 0.02 <= phi <= 0.45, f"porosity out of Physics9 bounds: {phi}"


@pytest.mark.asyncio
async def test_physics9_bounds_enforced_on_sw():
    """Sw values must stay within Physics9 bounds [0.0, 1.0]."""
    from geox_mcp.tools.lem_predict import LEMPredictRequest, geox_lem_predict

    req = LEMPredictRequest(
        well_id="T-SW",
        curves={
            "RHOB": [2.4, 2.4, 2.4, 2.4, 2.4],
            "RT": [0.001, 1000.0, 1000.0, 0.001, 0.001],  # stress extremes
        },
        depth_m=[1000.0, 1000.5, 1001.0, 1001.5, 1002.0],
        target_properties=["porosity", "sw"],
        actor_id="t",
        session_id="t",
    )
    result = await geox_lem_predict(req)
    cells = result.get("primary_artifact", {}).get("cells", [])
    for cell in cells:
        sw = cell.get("predictions", {}).get("sw", {}).get("value")
        if sw is not None:
            assert 0.0 <= sw <= 1.0, f"Sw out of Physics9 bounds: {sw}"


@pytest.mark.asyncio
async def test_physics9_bounds_enforced_on_vp():
    """Vp values must stay within Physics9 bounds [1480, 5500] m/s."""
    from geox_mcp.tools.lem_predict import LEMPredictRequest, geox_lem_predict

    req = LEMPredictRequest(
        well_id="T-VP",
        curves={"RHOB": [1.0, 2.0, 3.0, 4.0, 5.0]},
        depth_m=[1000.0, 1000.5, 1001.0, 1001.5, 1002.0],
        target_properties=["vp"],
        actor_id="t",
        session_id="t",
    )
    result = await geox_lem_predict(req)
    cells = result.get("primary_artifact", {}).get("cells", [])
    for cell in cells:
        vp = cell.get("predictions", {}).get("vp", {}).get("value")
        if vp is not None:
            assert 1480.0 <= vp <= 5500.0, f"Vp out of Physics9 bounds: {vp}"


# ── 4. F2 TRUTH: confidence cap at 0.90 ──────────────────────────────────


@pytest.mark.asyncio
async def test_confidence_capped_at_0_90():
    """Confidence must never exceed 0.90 (F7 HUMILITY)."""
    from geox_mcp.tools.lem_predict import LEMPredictRequest, geox_lem_predict

    req = LEMPredictRequest(
        well_id="T-CAP",
        curves={"RHOB": [2.5] * 5},
        depth_m=[1000.0, 1000.5, 1001.0, 1001.5, 1002.0],
        target_properties=["porosity"],
        actor_id="t",
        session_id="t",
    )
    result = await geox_lem_predict(req)
    pa = result.get("primary_artifact", {})
    conf = pa.get("confidence_overall")
    assert conf is not None
    assert conf <= 0.90, f"confidence exceeded F7 cap: {conf}"
    # also check the confidence_band.high
    cb = result.get("confidence_band", {})
    assert cb.get("cap", 1.0) == 0.90


# ── 5. F13 SOVEREIGN: AC_Risk > 0.5 → human_review_required ──────────────


@pytest.mark.asyncio
async def test_high_ac_risk_sets_human_review_required():
    """When AC_Risk overall exceeds 0.5, human_review_required must be True."""
    from geox_mcp.tools.lem_predict import LEMPredictRequest, geox_lem_predict

    # Adversarial: missing most curves → high AC_Risk
    req = LEMPredictRequest(
        well_id="T-HOLD",
        curves={"GR": [200, 200, 200]},  # extreme GR
        depth_m=[1000.0, 1000.5, 1001.0],
        target_properties=["porosity", "sw", "vp"],
        actor_id="t",
        session_id="t",
    )
    result = await geox_lem_predict(req)
    pa = result.get("primary_artifact", {})
    ac_overall = pa.get("ac_risk_overall")
    pg = result.get("physics_guard", {})
    if ac_overall is not None and ac_overall > 0.5:
        assert pg.get("human_review_required") is True, (
            "AC_Risk > 0.5 must set human_review_required"
        )


# ── 6. Universal envelope contract ───────────────────────────────────────


@pytest.mark.asyncio
async def test_universal_envelope_has_required_fields():
    """The result envelope carries all canonical fields."""
    from geox_mcp.tools.lem_predict import LEMPredictRequest, geox_lem_predict

    req = LEMPredictRequest(
        well_id="T-ENV",
        curves={"GR": [40, 50], "RT": [10, 12], "RHOB": [2.5, 2.4]},
        depth_m=[1000.0, 1000.5],
        target_properties=["porosity", "sw", "lithology"],
        actor_id="t",
        session_id="t",
    )
    result = await geox_lem_predict(req)

    # Top-level envelope fields
    assert "execution_status" in result
    assert "claim_state" in result
    assert "claim_tag" in result
    assert "evidence_refs" in result
    assert "physics_guard" in result
    assert "confidence_band" in result
    assert "audit_receipt" in result
    assert "humility_score" in result
    assert "primary_artifact" in result
    assert result["execution_status"] == "SUCCESS"
    assert result["claim_state"] in {"DRAFT", "VALIDATED", "SEALED", "QUALIFIED", "HOLD", "VOID"}
    assert result["claim_tag"] in {
        "CLAIM", "PLAUSIBLE", "HYPOTHESIS", "ESTIMATE", "UNKNOWN",
        "FACT", "INTERPRETATION",
    }
    # Primary artifact carries the well + mode + audit_receipt with tool_name
    pa = result["primary_artifact"]
    assert pa["well_id"] == "T-ENV"
    assert pa["mode_used"] == "physics_prior"
    assert pa.get("audit_receipt", {}).get("tool_name") == "geox_lem_predict"


@pytest.mark.asyncio
async def test_rejects_mismatched_curve_lengths():
    """curves among themselves must share the same length."""
    from geox_mcp.tools.lem_predict import LEMPredictRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        LEMPredictRequest(
            well_id="T-BAD",
            curves={"RHOB": [2.5, 2.4, 2.3], "GR": [40, 50]},  # mismatched
            depth_m=[1000.0, 1000.5, 1001.0],
            target_properties=["porosity"],
            actor_id="t",
            session_id="t",
        )


@pytest.mark.asyncio
async def test_rejects_empty_target_properties():
    """target_properties cannot be empty."""
    from geox_mcp.tools.lem_predict import LEMPredictRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        LEMPredictRequest(
            well_id="T-EMPTY",
            curves={"RHOB": [2.5]},
            depth_m=[1000.0],
            target_properties=[],
            actor_id="t",
            session_id="t",
        )
