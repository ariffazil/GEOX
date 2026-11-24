"""G-1 physics sanity — in-process, no MCP server required.

Replaces the three G-1 tests that lived in ``tests/alignment/test_align_geox.py``.
Those wrapped ``call_geox_tool`` — a stub that raised ``NotImplementedError``
unconditionally — inside ``pytest.raises((ValueError, RuntimeError,
NotImplementedError))``. Two of them therefore passed green without executing a
single line of GEOX; the third converted the same stub into a skip.

Contract as measured on 2026-11-24 (``/root/GEOX``, in-process):

    geox_petrophysics(...)        -> {"status": "INVALID"}          (refuses)
    geox_seismic_compute(...)     -> envelope: execution_status ERROR,
                                     governance_status HOLD,
                                     artifact_status REJECTED,
                                     claim_state NO_VALID_EVIDENCE   (refuses)

GEOX does not raise for unphysical input; it refuses in the returned state.
These tests pin that state, which is the thing a caller actually branches on.
"""

from __future__ import annotations

import asyncio

from geox_mcp.tools.petrophysics_unified import geox_petrophysics
from geox_mcp.tools.seismic_compute import geox_seismic_compute

SUPERLUMINAL = dict(mode="synthetic", vp=[8000.0], rho=[2.5])


def _run(coro):
    return asyncio.run(coro)


def test_g1_inverted_depth_refused():
    """Interval top below its base is unphysical — must refuse, not compute."""
    result = _run(
        geox_petrophysics(
            mode="generate",
            target_class="reservoir",
            zone_top_m=3500.0,
            zone_base_m=1500.0,
        )
    )
    assert result.get("status") == "INVALID", (
        f"inverted interval was not refused; status={result.get('status')!r}"
    )


def test_g1_negative_porosity_cutoff_refused():
    """A negative porosity cutoff is unphysical — must refuse."""
    result = _run(
        geox_petrophysics(mode="generate", target_class="reservoir", phi_cutoff=-0.15)
    )
    assert result.get("status") == "INVALID", (
        f"negative porosity cutoff was not refused; status={result.get('status')!r}"
    )


def test_g1_superluminal_velocity_refused():
    """8000 m/s in sedimentary rock is unphysical — must be rejected in the envelope."""
    result = _run(geox_seismic_compute(**SUPERLUMINAL))

    assert result.get("execution_status") == "ERROR"
    assert result.get("governance_status") == "HOLD"
    assert result.get("artifact_status") == "REJECTED"
    assert result.get("claim_state") == "NO_VALID_EVIDENCE"


def test_g1_rejected_output_must_not_attest_physics_pass():
    """A rejected output must never carry a passing physics attestation.

    Regression lock for GEOX-PHYS-GUARD-DEFAULT: get_standard_envelope() used to
    fall back to {"guard_passed": True} when a tool supplied no physics_guard, so
    an output the system had just REJECTED still attested that physics passed.
    An uncomputed guard is now null — "not evaluated", never "passed".
    """
    result = _run(geox_seismic_compute(**SUPERLUMINAL))

    guard = result.get("physics_guard") or {}
    assert guard.get("guard_passed") is None, (
        f"rejected output attests guard_passed={guard.get('guard_passed')!r}; "
        "an uncomputed guard must be null, never True"
    )


def test_supplied_physics_guard_is_preserved():
    """The fix must not over-correct: a tool that does supply a guard keeps it."""
    from geox_core.enums.statuses import get_standard_envelope

    envelope = get_standard_envelope(
        {"tool": "probe"},
        physics_guard={"guard_passed": True, "physics_version": "probe-v1"},
    )
    assert envelope["physics_guard"]["guard_passed"] is True

    envelope_fail = get_standard_envelope(
        {"tool": "probe"},
        physics_guard={"guard_passed": False, "violations": ["x"]},
    )
    assert envelope_fail["physics_guard"]["guard_passed"] is False
