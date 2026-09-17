"""K-REGIME wiring into the structure-gate matrix — additive proof.

The tectonic-regime falsification engine (``structure_gates/tectonic_regime.py``)
was imported by ``run_all_structure_gates`` but never invoked, so the doctrine
ran nowhere. This test file pins the wiring:

  (a) K-REGIME receipts now execute and are readable downstream
      (``gates["K-REGIME-*"]`` + top-level ``regime_falsification``);
  (b) the 9 core gates and the core ``combined_verdict`` / ``hypothesis_status``
      are byte-identical to the captured pre-wiring baseline;
  (c) a DEFICIT-only framework (expected signatures merely ABSENT) yields
      UNMEASURED — never KILL, never PASS;
  (d) a CONTRADICTION-bearing framework (positive counter-evidence measured)
      yields KILL where the engine says it should.

Iron rules exercised below: UNMEASURED is not a pass; no fabricated
confidence; every gate carries a receipt_hash; ``preferred_hypothesis`` is
always None from GEOX.

Two KNOWN GAPS in the engine are documented (not fixed, verdict semantics left
alone) as strict=False xfail markers — see the tests named ``test_gap_*``.
They are reported, not silently repaired.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest

from geox_mcp.domain.seismic_physics.receipts import receipt_hash
from geox_mcp.tools.structure_gates import (
    REGIME_FALSIFIERS,
    _merged_combined_verdict,
    run_all_structure_gates,
)
from geox_mcp.tools.structure_gates import tectonic_regime as tr

# ── Gate vocabulary / contract ───────────────────────────────────────────────

VALID_STATUS = {
    "PASS",
    "WARN",
    "KILL",
    "UNMEASURED",
    "NOT_APPLICABLE",
    "PARTIALLY_MEASURED",
    "COMPUTABLE",
}

CORE_GATES = (
    "K-DIP",
    "K-POLARITY",
    "K-THROW",
    "K-DL",
    "G2",
    "K-XCUT",
    "K-RESTORE",
    "K-VEL",
    "K-GROWTH",
)

UNIVERSAL_REGIME_GATES = (
    "K-REGIME-CEILING",
    "K-REGIME-DIFFERENTIAL",
    "K-REGIME-DECOMPACT",
    "K-REGIME-DISPLAY",
    "K-REGIME-RESOLUTION",
    "K-REGIME-XCUT",
    "K-REGIME-COVERAGE",
)

# One receipt per regime family — proves the driver reached every falsifier set.
FALSIFIER_RECEIPTS = (
    "K-EXT-GROWTH",       # extension
    "K-COMP-SHORTEN",     # compression
    "K-SS-FLOWER",        # strike_slip
    "K-INV-REVERSAL",     # inversion
    "K-SALT-BODY",        # salt_mobility
    "K-GRAV-LINKAGE",     # gravity_tectonics
    "K-NULL-COMPACTION",  # null_depositional (mandatory competitor)
)

# ── Frameworks ───────────────────────────────────────────────────────────────

FW_CLEAN = {
    "faults": [
        {
            "fault_id": "F_ok",
            "regime_prior": "normal",
            "dip_deg_subsurface": 62.0,
            "throw_profile": [
                {"station": 0, "throw": 5},
                {"station": 1, "throw": 45},
                {"station": 2, "throw": 8},
            ],
            "tip_taper": "ok",
            "max_displacement": 45,
            "length": 1000,
        }
    ],
    "horizons": [
        {"horizon_id": "H1", "order_index": 0,
         "points": [{"x": 0, "y": 100}, {"x": 10, "y": 105}, {"x": 20, "y": 110}]},
        {"horizon_id": "H2", "order_index": 1,
         "points": [{"x": 0, "y": 200}, {"x": 10, "y": 205}, {"x": 20, "y": 210}]},
    ],
}

# Geometry exists; NOT ONE expected signature is reported. Pure deficit.
FW_DEFICIT_ONLY = {
    "faults": [{"fault_id": "F1"}],
    "horizons": [
        {"horizon_id": "H1", "order_index": 0,
         "points": [{"x": 0, "y": 1000}, {"x": 10, "y": 1005}]},
    ],
}

# MEASURED contradiction: EI = 0.8 <= 1 kills the syn-tectonic growth claim.
FW_EXT_GROWTH_CONTRADICTION = {
    "faults": [
        {"fault_id": "F1", "regime_prior": "normal", "dip_deg_subsurface": 60.0,
         "throw_profile": [40, 40, 40], "max_displacement": 500, "length": 1000}
    ],
    "growth_claimed": True,
    "expansion_index": 0.8,
    "restore_residual": 0.2,
    "restore_tolerance": 0.05,
}

FW_MULTIKILL = {
    "faults": [
        {"fault_id": "F_imp", "regime_prior": "normal", "dip_deg_subsurface": 15.0,
         "max_displacement": 500, "length": 1000, "throw_profile": [40, 40, 40]}
    ],
    "throw_polarity_reversal": True,
    "relay_zone": False,
    "horizons": [
        {"horizon_id": "H1", "order_index": 0, "points": [{"x": 0, "y": 0}, {"x": 10, "y": 10}]},
        {"horizon_id": "H2", "order_index": 1, "points": [{"x": 0, "y": 10}, {"x": 10, "y": 0}]},
    ],
}

# Extension bare (no EI), but salt is in section and buoyancy-only is claimed
# with a measured density contrast far too small to initiate diapirism.
FW_SALT_CONTRADICTION = {**copy.deepcopy(FW_CLEAN),
                         "salt": {"present": True, "driver": "buoyancy",
                                  "density_contrast_kg_m3": 50}}

# A complete linked gravity system whose extension/shortening do not balance.
FW_GRAVITY_NULLPOINT = {
    "gravity": {
        "listric": True,
        "rollover": True,
        "toe_thrust": True,
        "same_decollement": True,
        "coeval": True,
        "total_extension_m": 1000.0,
        "total_shortening_m": 200.0,
    }
}

# ── Captured pre-wiring baseline (2026-09-18, before the K-REGIME block) ─────
# Recorded from the unmodified matrix. This is the regression contract: if any
# of these change, the wiring stopped being additive.
CORE_BASELINE = {
    "clean": {
        "gates": {
            "K-DIP": "PASS", "K-POLARITY": "UNMEASURED", "K-THROW": "PASS",
            "K-DL": "PASS", "G2": "PASS", "K-XCUT": "PASS",
            "K-RESTORE": "PASS", "K-VEL": "UNMEASURED", "K-GROWTH": "UNMEASURED",
        },
        "combined_verdict": "PARTIAL",
        "hypothesis_status": "SURVIVES_CURRENT_TESTS",
        "kills": [],
        "passes": ["K-DIP", "K-THROW", "K-DL", "G2", "K-XCUT", "K-RESTORE"],
        "warns": [],
        "unmeasured": ["K-POLARITY", "K-VEL", "K-GROWTH"],
    },
    "deficit_only": {
        "gates": {
            "K-DIP": "UNMEASURED", "K-POLARITY": "UNMEASURED", "K-THROW": "UNMEASURED",
            "K-DL": "UNMEASURED", "G2": "UNMEASURED", "K-XCUT": "UNMEASURED",
            "K-RESTORE": "UNMEASURED", "K-VEL": "UNMEASURED", "K-GROWTH": "UNMEASURED",
        },
        "combined_verdict": "UNMEASURED",
        "hypothesis_status": "UNTESTED",
        "kills": [],
        "passes": [],
        "warns": [],
        "unmeasured": list(CORE_GATES),
    },
    "ext_growth_contradiction": {
        "gates": {
            "K-DIP": "PASS", "K-POLARITY": "UNMEASURED", "K-THROW": "KILL",
            "K-DL": "KILL", "G2": "UNMEASURED", "K-XCUT": "UNMEASURED",
            "K-RESTORE": "KILL", "K-VEL": "UNMEASURED", "K-GROWTH": "KILL",
        },
        "combined_verdict": "KILL",
        "hypothesis_status": "REJECTED",
        "kills": ["K-THROW", "K-DL", "K-RESTORE", "K-GROWTH"],
        "passes": ["K-DIP"],
        "warns": [],
        "unmeasured": ["K-POLARITY", "G2", "K-XCUT", "K-VEL"],
    },
    "multikill": {
        "gates": {
            "K-DIP": "WARN", "K-POLARITY": "UNMEASURED", "K-THROW": "KILL",
            "K-DL": "KILL", "G2": "KILL", "K-XCUT": "KILL",
            "K-RESTORE": "PASS", "K-VEL": "UNMEASURED", "K-GROWTH": "UNMEASURED",
        },
        "combined_verdict": "KILL",
        "hypothesis_status": "REJECTED",
        "kills": ["K-THROW", "K-DL", "G2", "K-XCUT"],
        "passes": ["K-RESTORE"],
        "warns": ["K-DIP"],
        "unmeasured": ["K-POLARITY", "K-VEL", "K-GROWTH"],
    },
}

CASES = {
    "clean": FW_CLEAN,
    "deficit_only": FW_DEFICIT_ONLY,
    "ext_growth_contradiction": FW_EXT_GROWTH_CONTRADICTION,
    "multikill": FW_MULTIKILL,
}


# ── helpers ──────────────────────────────────────────────────────────────────


def _run(fw: dict) -> dict:
    """Deep-copy in, matrix out — no test can leak state between cases."""
    return run_all_structure_gates(copy.deepcopy(fw))


def _st(receipt: dict) -> str:
    return str(receipt.get("status") or receipt.get("verdict") or "UNMEASURED")


def _core_statuses(matrix: dict) -> dict:
    return {g: _st(matrix["gates"][g]) for g in CORE_GATES}


def _regime_receipts(matrix: dict) -> dict:
    return {
        k: v
        for k, v in matrix["gates"].items()
        if k.startswith(("K-REGIME-", "K-EXT-", "K-COMP-", "K-SS-", "K-INV-",
                         "K-SALT-", "K-GRAV-", "K-NULL-"))
    }


# ── (a) the regime gates now run ─────────────────────────────────────────────


def test_regime_gates_appear_in_matrix_output():
    """K-REGIME gates appear in run_all_structure_gates() output."""
    m = _run(FW_CLEAN)

    assert "regime_falsification" in m
    block = m["regime_falsification"]
    assert block["ok"] is True, block.get("message")
    assert block.get("error") is None

    # universal epistemic gates
    for gid in UNIVERSAL_REGIME_GATES:
        assert gid in m["gates"], f"{gid} missing from gates dict"
        assert _st(m["gates"][gid]) in VALID_STATUS

    # every regime family reached (per-regime falsifier receipts)
    for gid in FALSIFIER_RECEIPTS:
        assert gid in m["gates"], f"{gid} missing from gates dict"

    # the driver's own view is reachable
    assert block["n_hypotheses"] >= 3
    regimes = {h["regime"] for h in block["hypotheses"]}
    assert {"extension", "compression", "strike_slip", "inversion",
            "null_depositional"} <= regimes
    assert "null_depositional" in regimes, "mandatory null hypothesis was dropped"
    assert block["preferred_hypothesis"] is None
    assert block["seal_authority"] == "arifOS_only"

    # flat convenience views exist and agree with the receipts
    assert set(m["regime_kills"]) == {k for k, v in _regime_receipts(m).items()
                                      if _st(v) == "KILL"}
    assert set(m["regime_passes"]) == {k for k, v in _regime_receipts(m).items()
                                       if _st(v) == "PASS"}
    assert m["regime_status"] == block["overall"]


def test_every_regime_receipt_carries_valid_status_and_receipt_hash():
    """Gate contract: valid status vocabulary + verifiable receipt_hash."""
    m = _run(FW_EXT_GROWTH_CONTRADICTION)
    receipts = _regime_receipts(m)
    assert receipts, "no regime receipts produced"

    for gid, r in receipts.items():
        status = _st(r)
        assert status in VALID_STATUS, f"{gid} has illegal status {status!r}"
        h = r.get("receipt_hash")
        assert isinstance(h, str) and len(h) == 64, f"{gid} missing receipt_hash"
        # hash must be reproducible from the receipt body
        assert receipt_hash(r) == h, f"{gid} receipt_hash does not verify"
        assert r.get("epistemic_tier") in {"KINEMATIC", "STRAIN", "DYNAMIC"}


def test_regime_epistemic_tier_is_declared_never_invented():
    """KINEMATIC < STRAIN < DYNAMIC, and no DYNAMIC claim without slip data."""
    m = _run(FW_CLEAN)
    block = m["regime_falsification"]
    tiers = {h["regime"]: h["max_tier_name"] for h in block["hypotheses"]}
    assert set(tiers.values()) <= {"KINEMATIC", "STRAIN", "DYNAMIC"}
    # geometry-only bundle must NOT reach DYNAMIC anywhere
    assert "DYNAMIC" not in set(tiers.values())
    assert m["gates"]["K-REGIME-CEILING"]["status"] != "PASS"


# ── (b) existing behaviour unchanged ─────────────────────────────────────────


@pytest.mark.parametrize("case", sorted(CASES))
def test_core_gate_statuses_unchanged(case):
    """The 9 core gates keep their pre-wiring statuses, exactly."""
    base = CORE_BASELINE[case]
    m = _run(CASES[case])

    assert _core_statuses(m) == base["gates"]
    assert m["combined_verdict"] == base["combined_verdict"]
    assert m["hypothesis_status"] == base["hypothesis_status"]
    assert m["kills"] == base["kills"]
    assert m["passes"] == base["passes"]
    assert m["warns"] == base["warns"]
    assert m["unmeasured"] == base["unmeasured"]
    # core lists must never be polluted by regime gate ids
    regime_ids = set(_regime_receipts(m))
    assert not (regime_ids & set(m["kills"] + m["passes"] + m["warns"] + m["unmeasured"]))


@pytest.mark.parametrize("case", sorted(CASES))
def test_core_verdict_precedence_not_drifted(case):
    """The merged-verdict helper reproduces the core precedence exactly."""
    m = _run(CASES[case])
    assert _merged_combined_verdict(
        m["kills"], m["passes"], m["warns"], m["unmeasured"],
        m["partially_measured"], m["computable"],
    ) == m["combined_verdict"]


def test_include_regime_gates_false_keeps_legacy_output():
    """Escape hatch: skipping K-REGIME changes nothing and reports no pass."""
    m = run_all_structure_gates(copy.deepcopy(FW_CLEAN), include_regime_gates=False)
    base = CORE_BASELINE["clean"]

    assert _core_statuses(m) == base["gates"]
    assert m["combined_verdict"] == base["combined_verdict"]
    assert _regime_receipts(m) == {}
    assert m["regime_falsification"]["error"] == "REGIME_FALSIFICATION_SKIPPED"
    assert m["regime_status"] == "INSUFFICIENT_EVIDENCE"
    assert m["regime_governance_status"] == "HOLD"
    assert m["hypothesis_status_with_regime"] == m["hypothesis_status"]


# ── (c) deficit → UNMEASURED, never KILL, never PASS ─────────────────────────


def test_deficit_only_framework_yields_unmeasured_not_kill_not_pass():
    """Absent signatures may only produce UNMEASURED / NOT_APPLICABLE."""
    m = _run(FW_DEFICIT_ONLY)
    receipts = _regime_receipts(m)
    assert receipts, "regime gates did not run"

    statuses = {_st(r) for r in receipts.values()}
    assert statuses <= {"UNMEASURED", "NOT_APPLICABLE"}, statuses
    assert "KILL" not in statuses
    assert "PASS" not in statuses
    assert "WARN" not in statuses

    assert m["regime_kills"] == []
    assert m["regime_passes"] == []
    assert m["regime_warns"] == []
    # nothing anywhere in the matrix may kill on a deficit
    assert [k for k, v in m["gates"].items() if _st(v) == "KILL"] == []
    assert m["regime_status"] == "INSUFFICIENT_EVIDENCE"


def test_absent_growth_wedge_never_kills_extension_but_measured_ei_does():
    """Doctrine pair: absence of a wedge → UNMEASURED; EI<=1 measured → KILL."""
    # 1. bare fault with a dip, no growth signature at all
    deficit: dict[str, Any] = {
        "faults": [{"fault_id": "F1", "dip_deg": 60.0}],
        "horizons": [{"horizon_id": "H1", "order_index": 0, "points": [{"x": 0, "y": 0}]}],
    }
    m_deficit = _run(deficit)
    assert m_deficit["gates"]["K-EXT-GROWTH"]["status"] == "UNMEASURED"
    assert "K-EXT-GROWTH" not in m_deficit["regime_kills"]
    assert "extension" not in m_deficit["regime_rejected"]
    assert m_deficit["gates"]["K-EXT-GROWTH"]["missing_inputs"] == ["growth.expansion_index"]

    # 2. same framework + a MEASURED expansion index <= 1 → contradiction kills
    contradiction = copy.deepcopy(deficit)
    contradiction["expansion_index"] = 0.8
    m_contra = _run(contradiction)
    assert m_contra["gates"]["K-EXT-GROWTH"]["status"] == "KILL"
    assert "K-EXT-GROWTH" in m_contra["regime_kills"]
    assert "extension" in m_contra["regime_rejected"]


def test_unmeasured_regime_receipts_are_never_counted_as_passes():
    """Iron rule 3: UNMEASURED is not a pass, and is never averaged away."""
    m = _run(FW_DEFICIT_ONLY)
    for gid in m["regime_unmeasured"]:
        assert _st(m["gates"][gid]) in {"UNMEASURED", "NOT_APPLICABLE"}
        assert gid not in m["regime_passes"]
        assert gid not in m["regime_kills"]
        assert _st(m["gates"][gid]) != "PASS"


def test_epistemic_ceiling_kill_is_claim_gated_not_deficit_fired():
    """K-REGIME-CEILING may only KILL an asserted DYNAMIC claim.

    Documented judgement call: the ceiling fires on a POSITIVE claim
    ("this is a stress tensor") that the data class cannot support, not on an
    absent signature. A deficit-only bundle therefore returns UNMEASURED.
    Verdict semantics left untouched; reported, not silently changed.
    """
    assert _run({})["gates"]["K-REGIME-CEILING"]["status"] == "UNMEASURED"
    assert _run(FW_DEFICIT_ONLY)["gates"]["K-REGIME-CEILING"]["status"] == "UNMEASURED"

    claimed = _run({"claim": {"epistemic_tier": "DYNAMIC"},
                    "faults": [{"fault_id": "F1"}]})
    ceiling = claimed["gates"]["K-REGIME-CEILING"]
    assert ceiling["status"] == "KILL"
    assert ceiling["scope"] == "claim_only"
    assert claimed["regime_governance_status"] == "HOLD"


# ── (d) contradiction → KILL where the engine says it should ─────────────────


def test_contradiction_yields_kill_where_engine_says():
    m = _run(FW_EXT_GROWTH_CONTRADICTION)
    ext = m["gates"]["K-EXT-GROWTH"]

    assert ext["status"] == "KILL"
    assert ext["inputs"]["expansion_index"] == pytest.approx(0.8)
    assert ext["scope"] == "interval_syn_tectonic_claim"
    assert m["regime_kills"] == ["K-EXT-GROWTH"]
    assert m["regime_rejected"] == ["extension"]
    assert m["regime_status"] == "ALL_CANDIDATES_REJECTED"
    assert m["combined_verdict_with_regime"] == "KILL"
    assert m["hypothesis_status_with_regime"] == "REJECTED"


def test_measured_buoyancy_only_driver_with_weak_density_contrast_kills_salt():
    """Measured contradiction: buoyancy-only driver + Δρ 50 kg/m3 → KILL."""
    m = _run(FW_SALT_CONTRADICTION)
    salt = m["gates"]["K-SALT-DRIVER"]

    assert salt["status"] == "KILL"
    assert salt["inputs"]["density_contrast_kg_m3"] == pytest.approx(50.0)
    assert salt["scope"] == "mechanism_claim"
    assert "K-SALT-DRIVER" in m["regime_kills"]
    assert "salt_mobility" in m["regime_rejected"]


def test_regime_kill_is_never_hidden_behind_the_core_verdict():
    """A regime KILL must surface even when the 9 core gates do not kill."""
    m = _run(FW_SALT_CONTRADICTION)

    assert m["kills"] == [], "core gates should not kill this framework"
    assert m["combined_verdict"] == CORE_BASELINE["clean"]["combined_verdict"]
    assert m["regime_kills"] == ["K-SALT-DRIVER"]
    # the merged view carries the kill; GEOX still proposes nothing
    assert m["combined_verdict_with_regime"] == "KILL"
    assert m["hypothesis_status_with_regime"] == "REJECTED"
    assert m["regime_falsification"]["preferred_hypothesis"] is None


def test_linked_gravity_system_imbalance_kills_within_scope_only():
    """K-GRAV-NULLPOINT: measured ext/shortening mismatch → KILL, local scope."""
    m = _run(FW_GRAVITY_NULLPOINT)
    np = m["gates"]["K-GRAV-NULLPOINT"]

    assert np["status"] == "KILL"
    assert np["scope"] == "linked_system_only"
    assert np["calculated_result"]["generalise_basin_wide"] is False
    assert np["inputs"]["mismatch_fraction"] == pytest.approx(0.8, abs=1e-6)
    assert "gravity_tectonics" in m["regime_rejected"]


# ── SOURCE AUDIT: every KILL site in tectonic_regime.py (2026-09-18) ─────────
# Read at source before wiring. Every KILL emitter requires a POSITIVE MEASURED
# contradiction — none is reachable from an absent signature:
#   K-REGIME-CEILING  scope=claim_only — an ASSERTED DYNAMIC tier with no
#                     fault_slip_data (claim ceiling, not a data deficit;
#                     absence alone returns UNMEASURED — see dedicated test)
#   K-EXT-GROWTH      expansion index <= 1.0 MEASURED
#   K-COMP-SHORTEN    shortening MEASURED == 0
#   K-SALT-DRIVER     driver claims buoyancy AND density contrast MEASURED < 200
#   K-GRAV-NULLPOINT  ext + comp both MEASURED, mismatch > 25%, same decollement
#   (K-SS-THROW / K-SS-MARKER / K-SS-RIEDEL / K-SS-FLOWER / K-INV-* /
#    K-REGIME-DIFFERENTIAL / K-REGIME-DISPLAY / K-NULL-* emit no KILL at all —
#    K-REGIME-DIFFERENTIAL pins the negative direction as WARN by design)
# => no verdict-semantics change was needed in the engine. The sweeps below
# prove the property mechanically rather than trusting this reading.

# ── engine-level direction sweep (source-verified, not just sampled) ─────────


@pytest.mark.parametrize("regime", sorted(REGIME_FALSIFIERS))
def test_no_regime_falsifier_kills_on_absent_input(regime):
    """DEFICIT DIRECTION RULE at the kernel level.

    For every regime: an empty framework and a geometry-only framework with no
    reported signatures must produce ZERO KILLs. Absence fires on thin data as
    readily as on a true negative, so it may only ever return UNMEASURED
    (or NOT_APPLICABLE where a required input class is simply not in section).
    """
    for fw in ({}, copy.deepcopy(FW_DEFICIT_ONLY)):
        receipts = tr.REGIME_FALSIFIERS[regime](fw)
        assert receipts, f"{regime} returned no receipt"
        for r in receipts:
            assert _st(r) != "KILL", (
                f"{regime}/{r.get('gate_id')} killed on an ABSENT signature: {r.get('reason')}"
            )


def test_no_universal_regime_gate_kills_on_absent_input():
    """Same sweep for the 7 universal epistemic gates."""
    universal = (
        ("K-REGIME-CEILING", tr.gate_regime_ceiling),
        ("K-REGIME-DIFFERENTIAL", tr.gate_regime_differential),
        ("K-REGIME-DECOMPACT", tr.gate_regime_decompaction),
        ("K-REGIME-DISPLAY", tr.gate_regime_display),
        ("K-REGIME-RESOLUTION", tr.gate_regime_resolution),
        ("K-REGIME-XCUT", tr.gate_regime_xcut),
        ("K-REGIME-COVERAGE", tr.gate_regime_coverage),
    )
    for gid, fn in universal:
        for fw in ({}, copy.deepcopy(FW_DEFICIT_ONLY)):
            r = fn(fw)
            assert r["gate_id"] == gid
            assert _st(r) != "KILL", f"{gid} killed on absent input: {r.get('reason')}"


def test_no_regime_gate_kills_from_a_coverage_collapse():
    """Thin coverage must degrade to UNMEASURED, never sharpen into a KILL."""
    thin = {
        "faults": [{"fault_id": "F1", "dip_deg": 60.0}],
        "horizons": [{"horizon_id": "H1", "order_index": 0, "coverage_pct": 5,
                      "points": [{"x": 0, "y": 0}]}],
        "intervals": [{"name": "i1", "coverage_pct": 2}],
    }
    m = _run(thin)
    assert m["regime_kills"] == []
    assert m["gates"]["K-REGIME-COVERAGE"]["coverage"] == pytest.approx(0.035, abs=1e-6)
    assert m["gates"]["K-REGIME-COVERAGE"]["status"] == "WARN"


# ── iron rules ───────────────────────────────────────────────────────────────


def test_no_fabricated_confidence_anywhere_in_the_matrix():
    """Iron rule 1: no confidence/probability field may be emitted."""
    for case, fw in CASES.items():
        blob = json.dumps(_run(fw), default=str)
        assert "confidence" not in blob, f"{case} emitted a confidence token"
        assert "reliability" not in blob, f"{case} emitted a reliability token"

    m = _run(FW_CLEAN)
    assert m["seal_authority"] == "arifOS_only"
    assert m["local_verdict"] == "QUALIFIED_CANDIDATE"
    assert m["regime_falsification"]["local_verdict"] == "QUALIFIED_CANDIDATE"
    assert m["regime_falsification"]["seal_authority"] == "arifOS_only"


def test_regime_status_never_promotes_unmeasured_to_survival():
    """Discriminating power 0 → UNTESTED, whatever the gate mix."""
    m = _run(FW_DEFICIT_ONLY)
    for h in m["regime_falsification"]["hypotheses"]:
        if h["discriminating_power"] == 0.0:
            assert h["status"] == "UNTESTED", h
    assert m["regime_surviving"] == []


# ── KNOWN GAPS — documented, NOT silently fixed ──────────────────────────────
# Verdict semantics of the engine were left alone. Both gaps are direction
# errors (a deficit promoted / a low-coverage deficit not demoted), NOT
# KILL-from-deficit errors: no regime gate kills an absent signature.


@pytest.mark.xfail(
    strict=False,
    reason=(
        "GAP 1 (deficit promoted to PASS): K-SALT-DRIVER returns PASS when the "
        "driver is claimed as buoyancy but salt.density_contrast_kg_m3 is ABSENT. "
        "Iron rule 3 says an unmeasured quantity may not be promoted; doctrine-"
        "correct status is UNMEASURED with missing_inputs=['salt.density_contrast_kg_m3']."
    ),
)
def test_gap_salt_driver_deficit_should_be_unmeasured_not_pass():
    r = _run({"salt": {"present": True, "driver": "buoyancy"}})
    driver = r["gates"]["K-SALT-DRIVER"]
    assert driver["status"] == "UNMEASURED"
    assert "salt.density_contrast_kg_m3" in driver["missing_inputs"]


@pytest.mark.xfail(
    strict=False,
    reason=(
        "GAP 2 (no low-coverage demotion): deficit tests carry a coverage "
        "fraction but never downgrade to UNMEASURED when coverage < 0.7. "
        "K-REGIME-DIFFERENTIAL returns WARN at coverage 0.10."
    ),
)
def test_gap_deficit_with_low_coverage_should_downgrade_to_unmeasured():
    r = _run({
        "faults": [{"fault_id": "F1"}],
        "intervals": [{"name": "i1", "spatial_differential": False, "coverage_pct": 10}],
    })
    assert r["gates"]["K-REGIME-DIFFERENTIAL"]["status"] == "UNMEASURED"
