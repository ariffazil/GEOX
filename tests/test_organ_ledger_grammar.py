"""commit_ledger is the public organ-ledger grammar. seal stays gated.

The alias must not skip LIMITED_MUTATE, IRREVERSIBLE, or the RT3 ack.
Neither name is an arif_judge or VAULT999 verdict.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from geox_mcp.organ_governance import check_governance
from geox_mcp.registry import is_mutating_call, is_organ_ledger_commit
from geox_mcp.session_enforcement import ValidationResult

_ROOT = Path(__file__).resolve().parents[1]


def test_commit_ledger_and_seal_alias_both_mutate() -> None:
    assert is_organ_ledger_commit("commit_ledger")
    assert is_organ_ledger_commit("seal")
    assert is_organ_ledger_commit("SEAL")
    assert not is_organ_ledger_commit("compute")
    assert not is_organ_ledger_commit("create")
    assert not is_organ_ledger_commit("preview")
    for args in ({"mode": "seal"}, {"mode": "commit_ledger"}, {"mode": " SEAL "}):
        assert is_mutating_call("geox_claim", args)
    for args in ({"verdict": "seal"}, {"verdict": "commit_ledger"}):
        assert is_mutating_call("geox_prospect", args)
    assert not is_mutating_call("geox_claim", {"mode": "create"})
    assert not is_mutating_call("geox_prospect", {"verdict": "compute"})
    assert not is_mutating_call("geox_prospect", {"verdict": "preview"})


def test_public_copy_names_the_ledger_and_keeps_the_judge_key() -> None:
    wiring = (_ROOT / "src/geox_mcp/tools_wiring.py").read_text()
    prospect = (_ROOT / "src/geox_mcp/tools/prospect.py").read_text()
    claim = (_ROOT / "src/geox_mcp/tools/claim_unified.py").read_text()
    middleware = (_ROOT / "src/geox_mcp/geox_middleware.py").read_text()
    governance = (_ROOT / "src/geox_mcp/organ_governance.py").read_text()
    assert "commit_ledger" in wiring
    assert "not an arif_judge or VAULT999 verdict" in wiring
    assert "arif_judge or VAULT999 verdict" in claim
    assert 'tool_name="geox_prospect_evaluate[seal]"' in prospect
    assert "is_organ_ledger_commit(verdict)" in prospect
    assert "verdict='seal' is a constitutional adjudication" not in prospect
    for text in (middleware, governance):
        assert '== "seal"' not in text
        assert "is_organ_ledger_commit" in text


@pytest.mark.asyncio
async def test_alias_and_public_name_hold_on_observe_only() -> None:
    mock_auth = ValidationResult(
        ok=True,
        actor="test_agent",
        authority="OBSERVE_ONLY",
        session={"type": "session", "session_id": "SEAL-123456789012"},
    )
    cases = [
        ("geox_claim", {"mode": "seal"}),
        ("geox_claim", {"mode": "commit_ledger"}),
        ("geox_prospect", {"mode": "screen", "verdict": "seal"}),
        ("geox_prospect", {"mode": "screen", "verdict": "commit_ledger"}),
        ("geox_prospect", {"mode": "commit_ledger", "verdict": "compute"}),
    ]
    with patch("geox_mcp.organ_governance.validate_session", return_value=mock_auth):
        for tool, args in cases:
            verdict, err, _ = await check_governance(
                tool_name=tool,
                arguments=args,
                session_authority="OBSERVE_ONLY",
                actor_id="test_agent",
                session_id="SEAL-123456789012",
            )
            assert verdict == "HOLD", f"{tool} {args} must stay gated, got {verdict}: {err}"
