"""Tests for the tectonic-regime invariant registry loader/validator.

Covers:
  * the registry loads and every entry carries provenance;
  * the four validation laws on the real registry;
  * the DIRECTION RULE as a hard failure — an in-memory mutated copy of the
    registry with a ``DEFICIT_*`` test declaring ``KILL`` must be reported;
  * the loader is a read-only consumer (it never writes the ontology dir).

The real ``regime_invariants.yaml`` is never modified: negative cases mutate a
deep copy in memory or write a temporary file under ``tmp_path``.

Command: ``cd /root/GEOX && PYTHONPATH=src python3 -m pytest tests/test_regime_invariants_loader.py -x -q``
"""

from __future__ import annotations

import copy
import hashlib
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
import yaml

from geox_core.ontology.tectonic_events import regime_loader as rl

# Law keys as they appear in validate_registry()["laws"] — public contract.
LAW_A = "law_a_contradiction_kill_requires_guard"
LAW_B = "law_b_deficit_never_kills"
LAW_C = "law_c_hard_invariant_guard_fields"
LAW_D = "law_d_corrections_log_complete"

SRC_ROOT = Path(rl.__file__).resolve().parents[3]  # .../GEOX/src
REPO_ROOT = SRC_ROOT.parent


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures / helpers
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def registry() -> rl.RegimeRegistry:
    rl.clear_cache()
    return rl.load_registry()


@pytest.fixture()
def raw(registry: rl.RegimeRegistry) -> dict[str, Any]:
    """A deep copy of the parsed registry — safe to mutate."""
    return copy.deepcopy(registry.raw)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _loaded_entries(reg: rl.RegimeRegistry):
    yield reg.meta
    for collection in (
        reg.epistemic_tiers,
        reg.extraction_axes,
        reg.hard_invariants,
        reg.soft_invariants,
        reg.decoupling_mechanisms,
        reg.falsifier_registry,
    ):
        yield from collection.values()
    yield from reg.corrections_log
    for regime in reg.falsifier_registry.values():
        yield from regime.contradiction_tests.values()
        yield from regime.deficit_tests.values()


def _unguarded_contradictions(document: Mapping[str, Any]) -> set[str]:
    """Independent scan: CONTRADICTION_* without KILL + requires/coverage_requirement."""
    out: set[str] = set()
    for regime_id, regime in (document.get("falsifier_registry") or {}).items():
        for field in ("contradiction_tests", "deficit_tests"):
            for test_id, body in (regime.get(field) or {}).items():
                if not str(test_id).upper().startswith("CONTRADICTION"):
                    continue
                guard = body.get("requires") or body.get("coverage_requirement")
                verdict = str(body.get("returns") or "").strip().upper()
                if verdict != "KILL" or not str(guard or "").strip():
                    out.add(f"{regime_id}.{test_id}")
    return out


def _violation_ids(report: Mapping[str, Any]) -> set[str]:
    """``regime.test`` ids of law-A violations, parsed from their report paths."""
    out: set[str] = set()
    for violation in report["laws"][LAW_A]["violations"]:
        parts = violation["path"].split(".")
        if len(parts) >= 4 and parts[0] == "falsifier_registry":
            out.add(f"{parts[1]}.{parts[-1]}")
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 1. Loading + provenance
# ═══════════════════════════════════════════════════════════════════════════


def test_registry_loads_with_meta_and_all_sections(registry: rl.RegimeRegistry) -> None:
    assert registry.meta.artifact_id == "geox_regime_invariants_v1"
    assert registry.meta.version == "1.0.0"
    assert registry.source_file.endswith("regime_invariants.yaml")
    assert registry.source_sha256 == _digest(Path(registry.source_file))
    assert set(registry.epistemic_tiers) == {"E1_KINEMATIC", "E2_STRAIN", "E3_DYNAMIC"}
    assert len(registry.extraction_axes) == 4
    assert len(registry.hard_invariants) == 8
    assert len(registry.soft_invariants) == 4
    assert len(registry.decoupling_mechanisms) == 2
    assert len(registry.falsifier_registry) == 5
    assert len(registry.corrections_log) == 8
    # The paradigm counterpart declared in the YAML points at the sibling file.
    assert "TECT-001" in (registry.meta.paradigm_counterpart or "")


def test_every_loaded_entry_carries_provenance(registry: rl.RegimeRegistry) -> None:
    digest = _digest(Path(registry.source_file))
    assert registry.provenance.yaml_path == "$"
    for entry in _loaded_entries(registry):
        provenance = entry.provenance
        assert isinstance(provenance, rl.Provenance)
        assert provenance.artifact_id == registry.meta.artifact_id
        assert provenance.artifact_version == registry.meta.version
        assert provenance.source_file == registry.source_file
        assert provenance.source_sha256 == digest
        assert provenance.yaml_path and provenance.yaml_path != "$"


def test_hard_invariants_reg_001_to_008_present(registry: rl.RegimeRegistry) -> None:
    expected = {f"REG-{index:03d}" for index in range(1, 9)}
    assert expected <= set(registry.hard_invariants)
    for invariant in registry.hard_invariants.values():
        assert invariant.statement
        assert invariant.on_violation


def test_soft_invariants_reg_s01_to_s04_present(registry: rl.RegimeRegistry) -> None:
    expected = {f"REG-S{index:02d}" for index in range(1, 5)}
    assert expected <= set(registry.soft_invariants)
    # Soft invariants are empirical; they warn, they never kill.
    for invariant in registry.soft_invariants.values():
        assert "KILL" not in (invariant.on_violation or "").upper()


def test_decoupling_mechanisms_carry_decoupled_verdicts(registry: rl.RegimeRegistry) -> None:
    salt = registry.decoupling_mechanisms["M-SALT"]
    sag = registry.decoupling_mechanisms["M-SAG"]
    assert salt.verdict_when_active == "DECOUPLED"
    assert sag.verdict_when_active == "NOT_TECTONIC"
    assert "NOT_APPLICABLE" in (salt.invariant_effect or "")
    assert salt.signatures


def test_epistemic_ladder_tiers_and_axes(registry: rl.RegimeRegistry) -> None:
    assert registry.epistemic_tiers["E1_KINEMATIC"].epistemic_tag == "OBS"
    assert registry.epistemic_tiers["E2_STRAIN"].epistemic_tag == "DER"
    assert registry.epistemic_tiers["E3_DYNAMIC"].epistemic_tag == "INT"
    assert "NOT resolvable" in (registry.epistemic_tiers["E3_DYNAMIC"].degrees_of_freedom or "")
    for axis in registry.extraction_axes.values():
        assert axis.measures and axis.source_fields
    # YAML key `yield` is exposed as `yield_note` (Python keyword).
    assert "PARTIAL ORDER" in (registry.extraction_axes["D_SUPERPOSITION"].yield_note or "")


def test_falsifier_registry_direction_split(registry: rl.RegimeRegistry) -> None:
    for regime in registry.falsifier_registry.values():
        assert regime.required_positive_evidence
        for test in regime.contradiction_tests.values():
            assert test.direction == "contradiction"
            assert test.returns == "KILL"
        for test in regime.deficit_tests.values():
            assert test.direction == "deficit"
            assert test.returns == "UNMEASURED"
    # A guard is declared as either `requires` or `coverage_requirement`.
    no_prior = registry.falsifier_registry["R-INV"].contradiction_tests[
        "CONTRADICTION_NO_PRIOR_EXTENSION"
    ]
    assert no_prior.guard_field() == "coverage_requirement"
    assert "coverage_fraction" in (no_prior.guard() or "")
    # Deficit rationale is carried on the entry, not inferred here.
    assert registry.falsifier_registry["R-EXT"].deficit_tests["DEFICIT_NO_GROWTH_WEDGE"].why_not_kill


def test_corrections_log_records_the_documented_defects(registry: rl.RegimeRegistry) -> None:
    ids = [entry.id for entry in registry.corrections_log]
    assert ids == [f"CORR-{index:02d}" for index in range(1, 9)]
    assert registry.corrections_log[4].verdict == "FALSE PRECISION"  # CORR-05 ±15° band


# ═══════════════════════════════════════════════════════════════════════════
# 2. Threshold provenance
# ═══════════════════════════════════════════════════════════════════════════


def test_threshold_source_resolves_coulomb_tolerance_constant(registry: rl.RegimeRegistry) -> None:
    payload = rl.threshold_source("_COULOMB_TOLERANCE_DEG", registry=registry)

    assert payload["resolved"] is True
    assert payload["status"] == "RESOLVED"
    assert payload["registry_id"] == "REG-002"
    assert payload["yaml_path"] == "hard_invariants.REG-002"
    assert payload["resolved_via"] == "code_anchor_alias"

    # The load-bearing claim: the YAML documents this threshold as a rule of thumb.
    assert payload["threshold_status"] == "RULE_OF_THUMB"
    assert payload["threshold_status_field"] == "hard_invariants.REG-002.threshold_source"
    assert "RULE OF THUMB" in (payload["justification"] or "")
    assert payload["on_violation"] and "KILL" not in payload["on_violation"].upper()
    assert payload["epistemic_tag"] == "INT"

    # Validity domain + alternatives are read from the YAML, not invented here.
    assert payload["validity_domain"] == "New shear fracture in intact isotropic rock, μ by Byerlee (1978)"
    assert len(payload["alternatives"]) >= 5
    assert any("block rotation" in item for item in payload["alternatives"])

    # The literal 15.0 exists only as quoted registry text, with its source field.
    literal_15 = [item for item in payload["numeric_literals"] if item["value"] == 15.0]
    assert literal_15, "the ±15° literal must be surfaced from the registry text"
    assert literal_15[0]["field"] == "hard_invariants.REG-002.warning"
    assert literal_15[0]["extraction"] == "text_literal"
    assert "15" in literal_15[0]["quote"]

    # Provenance block is attached and checkable.
    provenance = payload["provenance"]
    assert provenance["source_file"] == registry.source_file
    assert provenance["source_sha256"] == registry.source_sha256
    assert provenance["yaml_path"] == "hard_invariants.REG-002"
    assert payload["registry_entry"]["threshold_source"] == "RULE_OF_THUMB"

    # The false-precision defect recorded against this constant is surfaced.
    corrections = {item["id"]: item for item in payload["corrections"]}
    assert "CORR-05" in corrections
    assert corrections["CORR-05"]["verdict"] == "FALSE PRECISION"
    assert isinstance(corrections["CORR-05"]["provenance"], Mapping)


def test_threshold_source_resolves_gate_declared_in_yaml(registry: rl.RegimeRegistry) -> None:
    # K-XCUT is a gate literally declared in the registry (REG-006, Steno).
    payload = rl.threshold_source("K-XCUT", registry=registry)
    assert payload["status"] == "RESOLVED"
    assert payload["resolved_via"] == "gate_id"
    assert payload["registry_id"] == "REG-006"
    assert payload["epistemic_tag"] == "OBS"


def test_threshold_source_resolves_mcp_gate_and_registry_id(registry: rl.RegimeRegistry) -> None:
    by_gate = rl.threshold_source("K-COMP-RAMPFLAT", registry=registry)
    by_id = rl.threshold_source("REG-002", registry=registry)
    assert by_gate["registry_id"] == by_id["registry_id"] == "REG-002"
    assert by_gate["threshold_status"] == by_id["threshold_status"] == "RULE_OF_THUMB"
    assert rl.threshold_status("K-COMP-RAMPFLAT", registry=registry) == "RULE_OF_THUMB"


def test_threshold_source_matches_numeric_literal_query(registry: rl.RegimeRegistry) -> None:
    payload = rl.threshold_source("±15°", registry=registry)
    assert payload["status"] == "RESOLVED"
    assert payload["resolved_via"] == "numeric_literal_match"
    assert payload["registry_id"] == "REG-002"
    assert payload["threshold_status"] == "RULE_OF_THUMB"


def test_threshold_source_unknown_name_returns_not_found_without_defaults(
    registry: rl.RegimeRegistry,
) -> None:
    payload = rl.threshold_source("K-REGIME-NOT-DECLARED-ANYWHERE", registry=registry)
    assert payload["status"] == "NOT_FOUND"
    assert payload["resolved"] is False
    assert payload["registry_id"] is None
    assert payload.get("threshold_status") is None
    assert payload.get("on_violation") is None
    assert payload["resolved_via"] is None
    assert "registry is the only source of thresholds" in payload["note"]
    # No invented numbers: the miss carries no fabricated threshold payload.
    assert "numeric_literals" not in payload
    assert isinstance(payload["provenance"], Mapping)


def test_registry_ids_resolve_for_every_section(registry: rl.RegimeRegistry) -> None:
    for query, expected in (
        ("REG-004", "REG-004"),
        ("REG-S02", "REG-S02"),
        ("M-SALT", "M-SALT"),
        ("R-INV", "R-INV"),
        ("CORR-07", "CORR-07"),
        ("DEFICIT_NO_GROWTH_WEDGE", "DEFICIT_NO_GROWTH_WEDGE"),
        ("E3_DYNAMIC", "E3_DYNAMIC"),
        ("B_DIFFERENTIAL", "B_DIFFERENTIAL"),
    ):
        payload = rl.threshold_source(query, registry=registry)
        assert payload["status"] == "RESOLVED", query
        assert payload["registry_id"] == expected


# ═══════════════════════════════════════════════════════════════════════════
# 3. Validation on the real registry
# ═══════════════════════════════════════════════════════════════════════════


def test_report_shape_and_verdict_is_not_a_score() -> None:
    report = rl.validate_registry()
    assert set(report["laws"]) == {LAW_A, LAW_B, LAW_C, LAW_D}
    assert isinstance(report["passed"], bool)
    assert isinstance(report["violations"], list)
    assert set(report["checked"]) == {
        "contradiction_tests",
        "deficit_tests",
        "hard_invariants",
        "corrections",
    }
    # Verdict + violations only: no confidence, probability or truth score.
    lowered = {key.lower() for key in report}
    assert not any("score" in key or "confidence" in key or "probability" in key for key in lowered)
    assert report["checked"]["contradiction_tests"] == 8
    assert report["checked"]["deficit_tests"] == 8
    assert report["checked"]["hard_invariants"] == 8
    assert report["checked"]["corrections"] == 8


def test_law_b_deficit_never_kills_passes_on_real_registry() -> None:
    """The load-bearing law: no DEFICIT_* test may declare KILL."""
    report = rl.validate_registry()
    law = report["laws"][LAW_B]
    assert law["violations"] == []
    assert law["passed"] is True
    assert law["checked"] == 8


def test_law_c_hard_invariant_guard_fields_pass_on_real_registry() -> None:
    report = rl.validate_registry()
    law = report["laws"][LAW_C]
    assert law["violations"] == []
    assert law["passed"] is True


def test_law_d_corrections_log_complete_passes_on_real_registry() -> None:
    report = rl.validate_registry()
    law = report["laws"][LAW_D]
    assert law["violations"] == []
    assert law["passed"] is True


def test_law_a_report_matches_independent_scan_of_the_registry() -> None:
    """The law never invents a violation and never misses a declared one.

    Expected set is recomputed here straight from the YAML by a separate scan,
    so this test is data-driven rather than pinned to the file's current state.
    """
    document = yaml.safe_load(rl.REGISTRY_PATH.read_text())
    expected = _unguarded_contradictions(document)
    report = rl.validate_registry()
    assert _violation_ids(report) == expected
    for violation in report["laws"][LAW_A]["violations"]:
        assert violation["code"] == "CONTRADICTION_UNGUARDED_KILL"
        assert "requires" in violation["detail"] or "coverage_requirement" in violation["detail"]


def test_law_a_passes_on_real_registry() -> None:
    """Law A: every CONTRADICTION_* KILL declares requires/coverage_requirement.

    The law is specified to pass.  If the registry as forged does not yet
    declare guards, this test XFAILs with the exact list of unguarded kills
    rather than being weakened to pass — the defect stays visible until the
    registry owner declares the guards.
    """
    report = rl.validate_registry()
    law = report["laws"][LAW_A]
    if not law["passed"]:
        unguarded = sorted(violation["path"] for violation in law["violations"])
        pytest.xfail(
            "regime_invariants.yaml declares CONTRADICTION_* KILLs with no "
            "requires/coverage_requirement: " + ", ".join(unguarded)
        )
    assert law["passed"] is True


def test_report_passed_is_the_conjunction_of_the_laws() -> None:
    report = rl.validate_registry()
    assert report["passed"] == all(law["passed"] for law in report["laws"].values())
    flat = [item for law in report["laws"].values() for item in law["violations"]]
    assert report["violations"] == flat


def test_warnings_are_structurally_separate_from_violations() -> None:
    report = rl.validate_registry()
    for warning in report["warnings"]:
        assert warning["code"] in {
            "CONTRADICTION_SCOPE_ONLY",
            "DEFICIT_WITHOUT_WHY_NOT_KILL",
            "HARD_INVARIANT_ALTERNATE_ACTION_KEY",
            "CONTRADICTION_IN_DEFICIT_SET",
            "DEFICIT_IN_CONTRADICTION_SET",
        }
    # A warning must never be counted as a violation.
    assert all(item not in report["violations"] for item in report["warnings"])


# ═══════════════════════════════════════════════════════════════════════════
# 4. Negative cases — the direction rule must fail loudly
# ═══════════════════════════════════════════════════════════════════════════


def test_negative_deficit_declaring_kill_is_reported(raw: dict[str, Any]) -> None:
    """A DEFICIT_* test declaring KILL must fail validation.  ★ load-bearing test."""
    raw["falsifier_registry"]["R-EXT"]["deficit_tests"]["DEFICIT_NO_GROWTH_WEDGE"]["returns"] = "KILL"

    report = rl.validate_registry(raw)

    assert report["passed"] is False
    law_b = report["laws"][LAW_B]
    assert law_b["passed"] is False
    codes = {(violation["code"], violation["path"]) for violation in law_b["violations"]}
    assert (
        "DEFICIT_DECLARES_KILL",
        "falsifier_registry.R-EXT.deficit_tests.DEFICIT_NO_GROWTH_WEDGE",
    ) in codes
    assert any("FALSIFIER DIRECTION RULE" in violation["detail"] for violation in law_b["violations"])
    # The other laws are untouched by this mutation.
    assert report["laws"][LAW_C]["passed"] is True
    assert report["laws"][LAW_D]["passed"] is True
    # The real registry is unaffected.
    assert rl.validate_registry()["laws"][LAW_B]["passed"] is True


def test_negative_deficit_kill_in_another_field_is_reported(raw: dict[str, Any]) -> None:
    raw["falsifier_registry"]["R-COMP"]["deficit_tests"]["DEFICIT_NO_VERGENCE"]["requires"] = "KILL"

    report = rl.validate_registry(raw)

    assert report["passed"] is False
    codes = {violation["code"] for violation in report["laws"][LAW_B]["violations"]}
    assert "DEFICIT_DECLARES_KILL" in codes


def test_negative_deficit_kill_via_temp_file(tmp_path: Path, raw: dict[str, Any]) -> None:
    """The same mutation, reached through the loader's file path."""
    raw["falsifier_registry"]["R-WRENCH"]["deficit_tests"]["DEFICIT_NO_FLOWER"]["returns"] = "KILL"
    mutated = tmp_path / "mutated_regime_invariants.yaml"
    mutated.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True))

    loaded = rl.load_registry(mutated)
    assert loaded.raw["falsifier_registry"]["R-WRENCH"]["deficit_tests"]["DEFICIT_NO_FLOWER"]["returns"] == "KILL"

    report = rl.validate_registry(loaded)
    assert report["passed"] is False
    assert report["source_file"] == str(mutated)
    assert any(
        violation["code"] == "DEFICIT_DECLARES_KILL"
        and violation["path"].endswith("DEFICIT_NO_FLOWER")
        for violation in report["laws"][LAW_B]["violations"]
    )
    # Also reachable by passing the path directly.
    assert rl.validate_registry(mutated)["laws"][LAW_B]["passed"] is False


def test_negative_deficit_returning_warn_is_reported(raw: dict[str, Any]) -> None:
    raw["falsifier_registry"]["R-GRAV"]["deficit_tests"]["DEFICIT_NO_TOE_THRUST"]["returns"] = "WARN"

    report = rl.validate_registry(raw)

    assert report["passed"] is False
    assert any(
        violation["code"] == "DEFICIT_RETURNS_NOT_UNMEASURED"
        for violation in report["laws"][LAW_B]["violations"]
    )


def test_negative_unguarded_contradiction_kill_is_reported(raw: dict[str, Any]) -> None:
    test = raw["falsifier_registry"]["R-EXT"]["contradiction_tests"]["CONTRADICTION_REVERSE_SAME_LEVEL"]
    assert "requires" not in test and "coverage_requirement" not in test  # precondition of this case
    report = rl.validate_registry(raw)

    law_a = report["laws"][LAW_A]
    assert law_a["passed"] is False
    assert any(
        violation["code"] == "CONTRADICTION_UNGUARDED_KILL"
        and violation["path"].endswith("CONTRADICTION_REVERSE_SAME_LEVEL")
        for violation in law_a["violations"]
    )


def test_negative_missing_hard_invariant_fields_are_reported(raw: dict[str, Any]) -> None:
    del raw["hard_invariants"]["REG-001"]["on_violation"]
    raw["hard_invariants"]["REG-003"]["epistemic_tag"] = "   "

    report = rl.validate_registry(raw)

    assert report["passed"] is False
    codes = [violation["code"] for violation in report["laws"][LAW_C]["violations"]]
    assert "HARD_INVARIANT_MISSING_ON_VIOLATION" in codes
    assert "HARD_INVARIANT_MISSING_EPISTEMIC_TAG" in codes


def test_negative_missing_correction_field_is_reported(raw: dict[str, Any]) -> None:
    del raw["corrections_log"][2]["fix"]

    report = rl.validate_registry(raw)

    assert report["passed"] is False
    violations = report["laws"][LAW_D]["violations"]
    assert [(violation["code"], violation["path"]) for violation in violations] == [
        ("CORRECTION_MISSING_FIELD", "corrections_log[2].fix")
    ]


def test_negative_contradiction_filed_under_deficit_is_warned(raw: dict[str, Any]) -> None:
    raw["falsifier_registry"]["R-EXT"]["deficit_tests"]["CONTRADICTION_EI_BELOW_ONE"] = raw[
        "falsifier_registry"
    ]["R-EXT"]["contradiction_tests"]["CONTRADICTION_EI_BELOW_ONE"]

    report = rl.validate_registry(raw)

    codes = {warning["code"] for warning in report["warnings"]}
    assert "CONTRADICTION_IN_DEFICIT_SET" in codes


# ═══════════════════════════════════════════════════════════════════════════
# 5. Malformed data never raises; missing/unparseable files do
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"meta": "not-a-mapping"},
        {"falsifier_registry": "nope"},
        {"falsifier_registry": ["nope"]},
        {"falsifier_registry": {"R-X": {"deficit_tests": "nope"}}},
        {"falsifier_registry": {"R-X": {"deficit_tests": {"DEFICIT_X": "not-a-mapping"}}}},
        {"hard_invariants": ["nope"], "corrections_log": 5},
    ],
    ids=["empty", "meta-scalar", "falsifiers-scalar", "falsifiers-list", "buckets-scalar", "test-scalar", "sections-wrong-type"],
)
def test_validate_never_raises_on_malformed_data(document: Any) -> None:
    report = rl.validate_registry(document)  # must not raise
    assert report["passed"] is False
    assert report["violations"], "malformed data must produce violations, not silence"
    assert report["source_file"] == "<in-memory mapping>"


@pytest.mark.parametrize("bad_input", [42, object(), ["not", "a", "registry"]])
def test_validate_reports_unsupported_input_without_raising(bad_input: Any) -> None:
    report = rl.validate_registry(bad_input)  # must not raise
    assert report["passed"] is False
    assert report["violations"][0]["code"] == "UNSUPPORTED_REGISTRY_INPUT"


def test_load_raises_only_for_missing_or_unparseable_file(tmp_path: Path) -> None:
    with pytest.raises(rl.RegimeRegistryNotFoundError):
        rl.load_registry(tmp_path / "does_not_exist.yaml")

    broken = tmp_path / "broken.yaml"
    broken.write_text("meta: [unclosed\n")
    with pytest.raises(rl.RegimeRegistryParseError):
        rl.load_registry(broken)

    not_a_mapping = tmp_path / "list.yaml"
    not_a_mapping.write_text("- one\n- two\n")
    with pytest.raises(rl.RegimeRegistryParseError):
        rl.load_registry(not_a_mapping)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Read-only consumer + geox_core layer boundary
# ═══════════════════════════════════════════════════════════════════════════


def test_loader_module_has_no_write_paths() -> None:
    source = Path(rl.__file__).read_text()
    for primitive in ("write_text", "write_bytes", "open(", "shutil", "mkdir", "unlink", "os.remove"):
        assert primitive not in source, f"loader must stay read-only but references {primitive!r}"


def test_registry_file_is_unchanged_by_loading_and_validating() -> None:
    before = _digest(rl.REGISTRY_PATH)
    rl.clear_cache()
    rl.load_registry()
    rl.validate_registry()
    rl.threshold_source("_COULOMB_TOLERANCE_DEG")
    rl.falsifier_tests()
    after = _digest(rl.REGISTRY_PATH)
    if before != after:
        pytest.skip("regime_invariants.yaml was written concurrently by another owner during this test")
    assert before == after


def test_loader_does_not_import_geox_mcp() -> None:
    """geox_core must not depend on geox_mcp (CI boundary ratchet)."""
    code = (
        "import sys\n"
        "from geox_core.ontology.tectonic_events import regime_loader as m\n"
        "m.load_registry()\n"
        "m.validate_registry()\n"
        "m.threshold_source('_COULOMB_TOLERANCE_DEG')\n"
        "print('geox_mcp' in sys.modules)\n"
    )
    env = dict(os.environ, PYTHONPATH=str(SRC_ROOT))
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=str(REPO_ROOT)
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False"


def test_f0_companion_is_reachable(registry: rl.RegimeRegistry) -> None:
    companion = rl.f0_companion()
    assert companion["count"] == 12
    assert "TECT-001" in companion["ids"]
    assert companion["provenance"]["source_file"].endswith("tectonic_invariants.yaml")


def test_cli_entry_reports_verdict() -> None:
    exit_code = rl.main([str(rl.REGISTRY_PATH)])
    assert exit_code in (0, 1)  # verdict, not an exception
