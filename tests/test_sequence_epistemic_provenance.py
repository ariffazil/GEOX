from __future__ import annotations

from geox_mcp.tools.sequence import _epistemic_provenance_for_sequence


def test_full_sequence_provenance_declares_pick_uncertainty_axes():
    provenance = _epistemic_provenance_for_sequence(
        detail_level="full",
        source_sha256="sha256:test-sequence",
    )

    axes = provenance["pick_uncertainty_axes"]
    assert axes["framework_uncertainty"]["rgt_monotonicity_gate"].startswith("enforced")
    assert axes["pick_uncertainty"]["cycle_skip_policy"] == "QC down-weight — never a silent delete"
    assert axes["velocity_uncertainty"]["independent_from"] == ["framework", "picks"]
    assert axes["eureka_ref"] == "PICK_UNCERTAINTY_AXES_2026_06_10"
