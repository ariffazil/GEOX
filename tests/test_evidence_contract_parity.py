"""Each public tool has one evidence contract. Each contract is public or internal.

A public gap is an explicit None. It is not an invented key list, and it is
not coverage. An empty list is rejected: that shape false-fails SUCCESS.
"""

from __future__ import annotations

from geox_mcp.evidence_postcondition import (
    EVIDENCE_CONTRACT_SCOPE,
    EVIDENCE_CONTRACTS,
    check_evidence_postcondition,
    compliance_matrix,
)
from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS


def test_each_public_tool_has_exactly_one_contract() -> None:
    public = list(CANONICAL_PUBLIC_TOOLS)
    assert len(public) == len(set(public))
    assert len(public) == 27
    for name in public:
        assert name in EVIDENCE_CONTRACTS, name
        assert EVIDENCE_CONTRACT_SCOPE[name] in ("public", "public_gap")
    assert len([name for name in EVIDENCE_CONTRACTS if name in set(public)]) == len(public)


def test_each_contract_is_public_or_explicitly_internal() -> None:
    public = set(CANONICAL_PUBLIC_TOOLS)
    assert EVIDENCE_CONTRACT_SCOPE
    for name, scope in EVIDENCE_CONTRACT_SCOPE.items():
        keys = EVIDENCE_CONTRACTS[name]
        if name in public:
            assert scope in ("public", "public_gap")
        else:
            assert scope == "internal", name
        if scope == "public_gap":
            assert keys is None
        elif scope == "public":
            assert isinstance(keys, list) and len(keys) > 0
        else:
            assert keys is None or (isinstance(keys, list) and len(keys) > 0)


def test_no_public_tool_is_both_enforced_and_gap() -> None:
    public = set(CANONICAL_PUBLIC_TOOLS)
    for name in public:
        scope = EVIDENCE_CONTRACT_SCOPE[name]
        keys = EVIDENCE_CONTRACTS[name]
        if scope == "public_gap":
            assert keys is None
        else:
            assert scope == "public"
            assert keys
        assert keys != []


def test_gap_contract_does_not_false_fail_success() -> None:
    result = {"ok": True, "status": "OK", "n_sources": 0}
    out = check_evidence_postcondition("geox_list_registered_sources", result)
    assert out["ok"] is True
    assert out["status"] == "OK"
    assert "isError" not in out


def test_compliance_pct_uses_the_public_27_not_internal_names() -> None:
    matrix = compliance_matrix()
    assert matrix["public_tools"] == 27
    assert matrix["enforced_count"] + matrix["gap_count"] == 27
    assert matrix["gap_count"] == 16
    assert matrix["internal_count"] == 23
    assert matrix["compliance_pct"] == round(matrix["enforced_count"] / 27 * 100)
    assert matrix["compliance_pct"] != 68
    assert "geox_gravmag_studio" in matrix["internal"]
    assert "geox_observe" in matrix["gaps"]
    assert "geox_prospect" in matrix["enforced"]
