"""
test_claim_explanation_class.py — explanatory-kind gate (claim_kernel/v1)
=========================================================================

Regression suite for the fourth axis of a GEOX claim:

  claim_state        WHERE the claim is in review      (9-state machine, unchanged)
  truth_class        HOW the claim was obtained        (FACT | INTERPRETATION | SPECULATION)
  claim_type         the geological category           (horizon | fault | trap | ...)
  explanation_class  WHAT KIND of explanation it is    (THIS FILE)

The rule under test — the one rule of ``claim_kernel``:

    A NARRATIVE claim may be true, valuable and worth reading and still carry
    zero explanatory power. It may be PUBLISHED; it may never be the SOLE
    JUSTIFICATION for a mutation. UNCLASSIFIED fails closed.

In GEOX terms: no claim may enter ``APPROVED_INTERPRETATION`` or ``SEALED``
unless its ``explanation_class`` is action-eligible (MEASURED | MECHANISM |
PATTERN).

Three layers are exercised, and they must agree:

  1. the contract  — contracts/claim_state_machine.yaml  (+ schemas/*.json)
  2. the guard     — geox_mcp/tools/claim_explanation_guard.py
  3. the live path — geox_mcp/tools/claims.py :: geox_claim_seal

NOTE ON ENVIRONMENT: this file deliberately imports nothing from
``geox_mcp.server`` / FastMCP, so it collects and runs even where the wider
suite hits the pre-existing FastMCP keyword defect.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from geox_mcp.tools import claim_explanation_guard as guard

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_YAML = REPO_ROOT / "contracts" / "claim_state_machine.yaml"
CONTRACT_JSON = REPO_ROOT / "contracts" / "schemas" / "claim_state_machine.json"
CLAIM_CARD_JSON = REPO_ROOT / "contracts" / "schemas" / "claim_card.json"

# Texts chosen so the kernel's own inference can be checked against the declared
# class: a real number with a source, a stated pathway, a named recurrence, and
# a destiny predicate with no mechanism, no measure and no falsifier.
TEXT_MEASURED = "Porosity at 2500 m is 22.5% measured from well A-1 logs, source: LAS run 3"
TEXT_MECHANISM = (
    "Fault seal breach occurs because the juxtaposed sand-sand contact at 1200 m "
    "allows cross-fault flow, pathway: capillary entry pressure exceeded"
)
TEXT_PATTERN = "The same overpressure pattern recurs across 5 wells in the Malay Basin; cause still contested"
TEXT_NARRATIVE = "The fairway is chosen ground and the best sands will always deliver"
TEXT_UNDECLARED = "Channel sand at 2.5s TWT, Malay Basin"


# ═══════════════════════════════════════════════════════════════════════════════
# 0. The kernel is really there and the vocabulary agrees
# ═══════════════════════════════════════════════════════════════════════════════


class TestKernelBinding:
    def test_claim_kernel_resolves(self):
        """The gate must be backed by a real module, not a name on a path."""
        assert guard.kernel_available(), f"claim_kernel did not resolve: {guard.kernel_error()}"

    def test_vocabulary_matches_kernel(self):
        """The guard's local fallback vocabulary must equal the kernel's."""
        assert guard.vocabulary_matches_kernel()

    def test_action_eligible_set_is_exactly_three(self):
        assert guard.ACTION_ELIGIBLE_EXPLANATION_CLASSES == (
            guard.MEASURED,
            guard.MECHANISM,
            guard.PATTERN,
        )
        assert guard.DEFAULT_EXPLANATION_CLASS == guard.UNCLASSIFIED

    def test_fail_closed_when_kernel_unavailable(self, monkeypatch):
        """An unverifiable gate is a closed gate — never a silently skipped one."""
        monkeypatch.setattr(guard, "_KERNEL", None)
        monkeypatch.setattr(guard, "_KERNEL_RESOLVED", True)
        monkeypatch.setattr(guard, "_KERNEL_ERROR", "simulated: claim_kernel absent")
        verdict = guard.evaluate_explanation_gate(TEXT_MEASURED, guard.MEASURED)
        assert verdict["allowed"] is False
        assert verdict["error_code"] == guard.ERROR_EXPLANATION_KERNEL_UNAVAILABLE


# ═══════════════════════════════════════════════════════════════════════════════
# 1. UNCLASSIFIED cannot be approved — it fails closed
# ═══════════════════════════════════════════════════════════════════════════════


class TestUnclassifiedCannotBeApproved:
    @pytest.mark.parametrize("target", ["APPROVED_INTERPRETATION", "SEALED"])
    def test_undeclared_class_is_refused(self, target):
        verdict = guard.guard_transition("REVIEW_PENDING", target, guard.UNCLASSIFIED, TEXT_UNDECLARED)
        assert verdict["allowed"] is False
        assert verdict["guarded"] is True
        assert verdict["error_code"] == guard.ERROR_EXPLANATION_NOT_ACTION_ELIGIBLE
        assert verdict["recommended_next_state"] is None, "unknown class holds; it is not rejected"

    def test_missing_field_on_legacy_record_reads_unclassified(self):
        """Records written before this axis existed carry no key. They fail closed."""
        legacy_payload = {"id": "clm_legacy", "claim_text": TEXT_MEASURED, "truth_class": "FACT"}
        assert guard.explanation_class_of(legacy_payload) == guard.UNCLASSIFIED
        assert guard.explanation_class_of(None) == guard.UNCLASSIFIED

    @pytest.mark.parametrize("junk", [None, "", "  ", "banana", "measured_ish", 7, {"a": 1}])
    def test_unknown_tokens_are_never_promoted(self, junk):
        assert guard.normalize_explanation_class(junk) == guard.UNCLASSIFIED


# ═══════════════════════════════════════════════════════════════════════════════
# 2. NARRATIVE cannot be approved — it is publishable, not actionable
# ═══════════════════════════════════════════════════════════════════════════════


class TestNarrativeCannotBeApproved:
    @pytest.mark.parametrize("target", ["APPROVED_INTERPRETATION", "SEALED"])
    def test_narrative_is_refused_with_clear_error_code(self, target):
        verdict = guard.guard_transition("REVIEW_PENDING", target, guard.NARRATIVE, TEXT_NARRATIVE)
        assert verdict["allowed"] is False
        assert verdict["error_code"] == guard.ERROR_EXPLANATION_NOT_ACTION_ELIGIBLE
        assert verdict["explanation_class"] == guard.NARRATIVE

    def test_narrative_contract_recommends_rejected(self):
        """It stays held AND the contract names the conformant exit: ANY → REJECTED."""
        verdict = guard.guard_transition("CHALLENGED", "APPROVED_INTERPRETATION", guard.NARRATIVE, TEXT_NARRATIVE)
        assert verdict["recommended_next_state"] == guard.NARRATIVE_FALLBACK_STATE == "REJECTED"
        assert "REJECTED" in verdict["required_action"]

    def test_narrative_declared_but_text_disagrees_is_still_refused(self):
        """Declaring MECHANISM on a story does not launder it past the kernel."""
        verdict = guard.evaluate_explanation_gate(TEXT_NARRATIVE, guard.MECHANISM)
        assert verdict["allowed"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MEASURED / MECHANISM / PATTERN can be approved
# ═══════════════════════════════════════════════════════════════════════════════


class TestActionEligibleClassesCanBeApproved:
    CASES = (
        (guard.MEASURED, TEXT_MEASURED),
        (guard.MECHANISM, TEXT_MECHANISM),
        (guard.PATTERN, TEXT_PATTERN),
    )

    @pytest.mark.parametrize("declared,text", CASES)
    @pytest.mark.parametrize("target", ["APPROVED_INTERPRETATION", "SEALED"])
    def test_action_eligible_class_passes(self, declared, text, target):
        verdict = guard.guard_transition("REVIEW_PENDING", target, declared, text)
        assert verdict["allowed"] is True, verdict.get("reasons")
        assert verdict["error_code"] is None
        assert verdict["action_eligible"] is True

    @pytest.mark.parametrize("declared,text", CASES)
    def test_gate_reports_kernel_verdicts(self, declared, text):
        verdict = guard.evaluate_explanation_gate(text, declared)
        assert verdict["allowed"] is True
        assert verdict["kernel"]["available"] is True
        assert verdict["kernel"]["schema"] == guard.CLAIM_KERNEL_SCHEMA
        assert verdict["class_verdict"]["declared"] == declared


# ═══════════════════════════════════════════════════════════════════════════════
# 4. The other transitions of the 9-state machine are untouched
# ═══════════════════════════════════════════════════════════════════════════════


class TestExistingMachineUnchanged:
    @pytest.mark.parametrize(
        "target",
        ["DRAFT", "AI_INFERRED", "REVIEW_PENDING", "NEEDS_EVIDENCE", "CHALLENGED", "REVOKED", "REJECTED"],
    )
    def test_unguarded_transitions_pass_for_any_class(self, target):
        for declared in (guard.UNCLASSIFIED, guard.NARRATIVE):
            verdict = guard.guard_transition("SOMEWHERE", target, declared, TEXT_UNDECLARED)
            assert verdict["allowed"] is True
            assert verdict["guarded"] is False
            assert verdict["error_code"] is None

    def test_guarded_targets_are_exactly_two(self):
        assert guard.guarded_transition_states() == ("APPROVED_INTERPRETATION", "SEALED")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. The YAML contract carries the same rule (contract == code)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def contract() -> dict:
    return yaml.safe_load(CONTRACT_YAML.read_text(encoding="utf-8"))


class TestContractDeclaresTheRule:
    def test_nine_states_preserved(self, contract):
        names = [s["name"] for s in contract["states"]]
        assert len(names) == 9, names
        assert set(names) == {
            "DRAFT", "AI_INFERRED", "REVIEW_PENDING", "NEEDS_EVIDENCE", "CHALLENGED",
            "APPROVED_INTERPRETATION", "SEALED", "REVOKED", "REJECTED",
        }

    def test_original_seven_error_codes_preserved(self, contract):
        codes = {c["code"] for c in contract["error_codes"]}
        original = {
            "HOLD_IDENTITY_REQUIRED", "HOLD_SCOPE_REQUIRED", "HOLD_EVIDENCE_REQUIRED",
            "HOLD_QC_FAILED", "HOLD_CRS_PROOF_REQUIRED", "HOLD_HUMAN_REVIEW_REQUIRED",
            "HOLD_SEAL_NOT_PERMITTED",
        }
        assert original.issubset(codes), original - codes
        assert guard.ERROR_EXPLANATION_NOT_ACTION_ELIGIBLE in codes
        assert guard.ERROR_EXPLANATION_KERNEL_UNAVAILABLE in codes
        assert all(c.get("severity") in {"critical", "high", "medium", "low"} for c in contract["error_codes"])

    def test_explanation_axis_declared(self, contract):
        axis = contract["explanation_axis"]
        assert axis["schema"] == guard.CLAIM_KERNEL_SCHEMA
        assert axis["field"] == "explanation_class"
        assert axis["default"] == "UNCLASSIFIED"
        assert axis["fail_closed"] is True
        assert axis["rewrite_of_preexisting_records"] == "none"

    def test_axis_classes_match_the_guard(self, contract):
        declared = {c["name"]: c["action_eligible"] for c in contract["explanation_axis"]["classes"]}
        assert set(declared) == set(guard.EXPLANATION_CLASSES)
        for name, eligible in declared.items():
            assert eligible is guard.is_action_eligible_class(name), name

    def test_guarded_transitions_match_the_code_guard(self, contract):
        targets = {t["to"] for t in contract["explanation_axis"]["guarded_transitions"]}
        assert targets == set(guard.guarded_transition_states())
        for t in contract["explanation_axis"]["guarded_transitions"]:
            assert t["error_code_on_fail"] == guard.ERROR_EXPLANATION_NOT_ACTION_ELIGIBLE

    def test_entry_conditions_state_the_gate(self, contract):
        by_name = {s["name"]: s for s in contract["states"]}
        for state in ("APPROVED_INTERPRETATION", "SEALED"):
            joined = " ".join(by_name[state]["entry_conditions"])
            assert "explanation_class must be action-eligible" in joined, state

    def test_default_block_names_the_blocked_states(self, contract):
        blocked = contract["default"]["blocked_if_explanation_not_action_eligible"]
        assert set(blocked) == set(guard.guarded_transition_states())
        assert contract["default"]["default_explanation_class"] == "UNCLASSIFIED"

    def test_json_schemas_carry_the_axis(self):
        sm = json.loads(CONTRACT_JSON.read_text(encoding="utf-8"))
        assert sm["properties"]["explanation_axis"]["properties"]["schema"]["const"] == "claim_kernel/v1"
        assert sm["required"] == ["spec_version", "states", "transitions", "error_codes", "default"]

        card = json.loads(CLAIM_CARD_JSON.read_text(encoding="utf-8"))
        prop = card["properties"]["explanation_class"]
        assert prop["enum"] == list(guard.EXPLANATION_CLASSES)
        assert prop["default"] == "UNCLASSIFIED"
        # additive: NOT required, so pre-existing claim records stay valid
        assert "explanation_class" not in card["required"]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. The claim model carries the field, defaulting to UNCLASSIFIED
# ═══════════════════════════════════════════════════════════════════════════════


class TestClaimModelField:
    def test_egs_claim_envelope_defaults_to_unclassified(self):
        from geox.egs.models.claims import ClaimEnvelope

        claim = ClaimEnvelope(title="Top reservoir at 2500 m TVDSS", statement="Top at 2500 m.")
        assert claim.explanation_class.value == guard.UNCLASSIFIED
        assert guard.explanation_class_of(claim) == guard.UNCLASSIFIED

    def test_egs_claim_envelope_accepts_a_declared_class(self):
        from geox.egs.models.claims import ClaimEnvelope

        claim = ClaimEnvelope(
            title="Top reservoir at 2500 m TVDSS",
            statement="Top at 2500 m.",
            explanation_class="MECHANISM",
        )
        assert guard.explanation_class_of(claim) == guard.MECHANISM

    def test_legacy_construction_is_unaffected(self):
        """Every field an existing caller passes keeps working."""
        from geox.egs.models.claims import ClaimDomain, ClaimEnvelope, ClaimStatus

        claim = ClaimEnvelope(
            title="Legacy claim",
            statement="Statement",
            domain=ClaimDomain.STRATIGRAPHY,
            status=ClaimStatus.ACCEPTED,
            author="Arif",
            confidence_score=0.85,
        )
        assert claim.status == ClaimStatus.ACCEPTED
        assert claim.domain == ClaimDomain.STRATIGRAPHY
        assert guard.explanation_class_of(claim) == guard.UNCLASSIFIED

    def test_payload_builder_writes_the_key(self):
        from geox_mcp.tools.claims import _build_claim_envelope

        payload = _build_claim_envelope(
            claim_id="clm_test",
            claim_type="porosity",
            claim_text=TEXT_MEASURED,
            truth_class="FACT",
            uncertainty=None,
            evidence_ids=[],
            alternatives=None,
            provenance="test",
            explanation_class="measured",  # case-insensitive on the way in
        )
        assert payload["explanation_class"] == guard.MEASURED
        assert guard.explanation_class_of(payload) == guard.MEASURED

    def test_payload_builder_default_is_unclassified(self):
        from geox_mcp.tools.claims import _build_claim_envelope

        payload = _build_claim_envelope(
            claim_id="clm_test2",
            claim_type="other",
            claim_text=TEXT_UNDECLARED,
            truth_class="INTERPRETATION",
            uncertainty=None,
            evidence_ids=[],
            alternatives=None,
            provenance="test",
        )
        assert payload["explanation_class"] == guard.UNCLASSIFIED
        assert guard.is_action_eligible_class(payload["explanation_class"]) is False


# ═══════════════════════════════════════════════════════════════════════════════
# 7. The live seal path enforces it (geox_claim_seal)
# ═══════════════════════════════════════════════════════════════════════════════


class _FakeCursor:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeConn:
    def __init__(self, row):
        self._row = row

    def execute(self, sql, params=()):  # noqa: ARG002
        return _FakeCursor(self._row)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeStore:
    """Minimal EarthMemoryStore stand-in: one row, (payload_json, approval_state)."""

    def __init__(self, payload: dict, approval_state: str = "VALIDATED"):
        self._row = (json.dumps(payload), approval_state)

    def _connect(self):
        return _FakeConn(self._row)


def _sealable_payload(claim_text: str, explanation_class: str | None) -> dict:
    """A claim that satisfies every PRE-EXISTING pre-seal gate, so the only
    thing left to fail is the explanatory-class gate."""
    payload = {
        "id": "clm_sealpath",
        "claim_type": "porosity",
        "claim_text": claim_text,
        "truth_class": "INTERPRETATION",
        "evidence_ids": ["ev_real_1"],
        "evidence_chain": [],
        "challenges": ["chl_1"],
        "authority": {"approval_state": "validated"},
    }
    if explanation_class is not None:
        payload["explanation_class"] = explanation_class
    return payload


@pytest.fixture
def seal_env(monkeypatch):
    """Wire a fake store + a dead arifOS into the live claim engine."""
    from geox_mcp.tools import claims as claims_mod

    holder = {}

    async def _no_arifos():
        return False

    def _wire(payload: dict, approval_state: str = "VALIDATED"):
        holder["store"] = _FakeStore(payload, approval_state)
        monkeypatch.setattr(claims_mod, "_get_memory_store", lambda: holder["store"])
        monkeypatch.setattr(claims_mod, "_get_arifOS_health", _no_arifos)
        return holder["store"]

    return _wire


class TestLiveSealPathEnforcesTheGate:
    async def test_narrative_cannot_seal(self, seal_env):
        from geox_mcp.tools.claims import geox_claim_seal

        seal_env(_sealable_payload(TEXT_NARRATIVE, guard.NARRATIVE))
        result = await geox_claim_seal(claim_id="clm_sealpath", ack_irreversible=True, seal_verdict="SEAL")
        assert result["status"] == "HOLD"
        assert result["error_code"] == guard.ERROR_EXPLANATION_NOT_ACTION_ELIGIBLE
        assert result["explanation_class"] == guard.NARRATIVE
        assert result["explanation_gate"]["recommended_next_state"] == "REJECTED"
        gates = [g["gate"] for g in result["failed_gates"]]
        assert "explanation_class_action_eligible" in gates

    async def test_unclassified_cannot_seal(self, seal_env):
        from geox_mcp.tools.claims import geox_claim_seal

        # no explanation_class key at all: a pre-existing record
        seal_env(_sealable_payload(TEXT_UNDECLARED, None))
        result = await geox_claim_seal(claim_id="clm_sealpath", ack_irreversible=True, seal_verdict="SEAL")
        assert result["status"] == "HOLD"
        assert result["error_code"] == guard.ERROR_EXPLANATION_NOT_ACTION_ELIGIBLE
        assert result["explanation_class"] == guard.UNCLASSIFIED

    @pytest.mark.parametrize(
        "declared,text",
        [
            (guard.MEASURED, TEXT_MEASURED),
            (guard.MECHANISM, TEXT_MECHANISM),
            (guard.PATTERN, TEXT_PATTERN),
        ],
    )
    async def test_action_eligible_class_seals(self, seal_env, declared, text):
        from geox_mcp.tools.claims import geox_claim_seal

        seal_env(_sealable_payload(text, declared))
        result = await geox_claim_seal(claim_id="clm_sealpath", ack_irreversible=True, seal_verdict="SEAL")
        assert result["status"] == "SEALED_LOCAL", result
        assert result["claim_state"] == "SEALED"

    async def test_legacy_error_code_still_wins_when_a_legacy_gate_fails(self, seal_env):
        """No evidence + no challenge + undeclared class → the OLD error code, unchanged."""
        from geox_mcp.tools.claims import geox_claim_seal

        payload = _sealable_payload(TEXT_UNDECLARED, None)
        payload["evidence_ids"] = []
        payload["challenges"] = []
        seal_env(payload)
        result = await geox_claim_seal(claim_id="clm_sealpath", ack_irreversible=True, seal_verdict="SEAL")
        assert result["status"] == "HOLD"
        assert result["error_code"] == "PRE_SEAL_CONTRADICTION_GATE"

    async def test_sabar_and_void_verdicts_are_untouched(self, seal_env):
        """Only the SEAL verdict path is gated; the machine's other verdicts are not."""
        from geox_mcp.tools.claims import geox_claim_seal

        seal_env(_sealable_payload(TEXT_NARRATIVE, guard.NARRATIVE))
        result = await geox_claim_seal(claim_id="clm_sealpath", ack_irreversible=True, seal_verdict="SABAR")
        assert result["status"] == "SEALED_LOCAL"
        assert result["verdict"] == "SABAR"

    async def test_guard_used_by_the_live_path_is_the_same_code(self):
        """The seal path calls guard_transition for the SEALED target — the same
        function that protects APPROVED_INTERPRETATION."""
        import inspect

        from geox_mcp.tools import claims as claims_mod

        src = inspect.getsource(claims_mod.geox_claim_seal)
        assert "guard_transition(" in src
        assert 'target_state="SEALED"' in src


# ═══════════════════════════════════════════════════════════════════════════════
# 8. The published MCP surface is reachable: geox_claim accepts the class
# ═══════════════════════════════════════════════════════════════════════════════


class TestMcpSurfaceExposesTheAxis:
    def test_geox_claim_schema_declares_explanation_class(self):
        """geox_claim is a mode-dispatched tool whose input schema comes from the
        wrapper signature in geox_mcp/tools_wiring.py. If the field is missing
        there, a real caller cannot declare a class at all and every claim would
        fail closed — the axis has to be reachable, not merely available."""
        import asyncio

        try:
            from geox_mcp.server import create_app, mcp
        except Exception as exc:  # pragma: no cover - environment dependent
            pytest.skip(f"MCP server surface unavailable here: {exc}")

        async def _probe() -> dict:
            create_app()
            tools = {t.name: t for t in await mcp.list_tools()}
            assert "geox_claim" in tools, "geox_claim missing from the canonical surface"
            return getattr(tools["geox_claim"], "parameters", None) or {}

        params = asyncio.run(_probe())
        assert "explanation_class" in (params.get("properties") or {})
